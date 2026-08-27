#!/usr/bin/env python3
"""Local macOS evidence for the bounded techstack safe-open contract.

This script is executable only by explicit owner or reviewer choice. It is not
part of CI and performs no network, repository, managed-state, export, release,
or remote action. It creates FIFO, socket, directory, and regular fixtures only
inside a `TemporaryDirectory`, inspects an already present character device and
any already present block device under `/dev`, and runs the production reader.

Usage:

    PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_techstack_safe_open_macos.py

It exits 2 with `unsupported evidence platform` on any other platform, 0 after
printing its single PASS line, and 1 on any failed assertion or on the
five-second outer deadline.
"""

import os
import signal
import socket
import stat
import sys
import tempfile
import threading
from pathlib import Path


PLATFORM_NAME = "macos"
DEADLINE_SECONDS = 5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class EvidenceError(Exception):
    """Raised when an evidence assertion fails."""


def named_platform() -> bool:
    return sys.platform.startswith("darwin")


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def _deadline_expired(signum, frame):
    sys.stderr.write("evidence deadline expired\n")
    raise SystemExit(1)


def make_root(base):
    root = Path(base) / "project"
    root.mkdir()
    (root / ".git").mkdir()
    return root


def check_metadata_classification(fs, root, root_fd, observed):
    """Every metadata-observed nonregular entry must skip the content open."""

    os.mkfifo(root / "pipe")
    (root / "package").mkdir()
    (root / "target.md").write_bytes(b"real bytes\n")
    os.symlink(root / "target.md", root / "link.md")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(str(root / "endpoint"))
        expected = {
            "pipe": "FIFO_REJECTED",
            "package": "DIRECTORY_REJECTED",
            "link.md": "SYMLINK_REJECTED",
            "endpoint": "SOCKET_REJECTED",
            "absent.md": "NOT_FOUND",
        }
        for name, code in expected.items():
            before = len(observed)
            outcome = fs.read_bounded_regular(root_fd, name, 4096)
            require(outcome.code == code, f"{name} returned {outcome.code}, expected {code}")
            require(len(observed) == before, f"{name} reached a content open")
    finally:
        server.close()


def check_devices(fs, observed):
    """Inspect one real character device and any available block device."""

    descriptor = os.open("/dev", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        before = len(observed)
        outcome = fs.read_bounded_regular(descriptor, "null", 4096)
        require(
            outcome.code == "DEVICE_REJECTED",
            f"/dev/null returned {outcome.code}, expected DEVICE_REJECTED",
        )
        require(len(observed) == before, "/dev/null reached a content open")
        block_name = None
        with os.scandir("/dev") as entries:
            for entry in entries:
                try:
                    if stat.S_ISBLK(entry.stat(follow_symlinks=False).st_mode):
                        block_name = entry.name
                        break
                except OSError:
                    continue
        if block_name is None:
            sys.stdout.write("NOT OBSERVED: no block device available\n")
            return
        before = len(observed)
        outcome = fs.read_bounded_regular(descriptor, block_name, 4096)
        require(
            outcome.code == "DEVICE_REJECTED",
            f"/dev/{block_name} returned {outcome.code}, expected DEVICE_REJECTED",
        )
        require(len(observed) == before, f"/dev/{block_name} reached a content open")
    finally:
        os.close(descriptor)


def check_regular_read(fs, root_fd):
    outcome = fs.read_bounded_regular(root_fd, "target.md", 4096)
    require(outcome.ok, f"regular read returned {outcome.code}")
    require(outcome.data == b"real bytes\n", "regular read returned unexpected bytes")
    over = fs.read_bounded_regular(root_fd, "target.md", 4)
    require(over.code == "BYTE_LIMIT", f"over-limit read returned {over.code}")


def check_injected_race(fs, model, root_fd):
    """A stale parent identity must terminate as an exact FILE_CHANGED."""

    real_classify = fs.classify_entry

    def stale(parent_fd, name):
        observation = real_classify(parent_fd, name)
        identity = observation.identity
        if identity is None:
            return observation
        return fs.Observation(
            code=observation.code,
            identity=model.FileIdentity(
                device=identity.device,
                inode=identity.inode,
                mode=identity.mode,
                size=identity.size + 1,
                mtime_ns=identity.mtime_ns,
                ctime_ns=identity.ctime_ns,
            ),
        )

    fs.classify_entry = stale
    try:
        outcome = fs.read_bounded_regular(root_fd, "target.md", 4096)
    finally:
        fs.classify_entry = real_classify
    require(outcome.code == "FILE_CHANGED", f"injected race returned {outcome.code}")


def check_real_timeout_cleanup(fs, root_fd):
    """Drive one real child through the TERM and KILL windows."""

    first, term, kill = (
        fs.HELPER_FIRST_TIMEOUT,
        fs.HELPER_TERM_TIMEOUT,
        fs.HELPER_KILL_TIMEOUT,
    )
    fs.HELPER_FIRST_TIMEOUT = 0.001
    fs.HELPER_TERM_TIMEOUT = 0.001
    fs.HELPER_KILL_TIMEOUT = 1.000
    try:
        outcome = fs.read_bounded_regular(root_fd, "target.md", 4096)
    finally:
        fs.HELPER_FIRST_TIMEOUT = first
        fs.HELPER_TERM_TIMEOUT = term
        fs.HELPER_KILL_TIMEOUT = kill
    require(
        outcome.code == "SAFE_OPEN_HELPER_TIMEOUT",
        f"real timeout case returned {outcome.code}",
    )
    require(
        any(entry.startswith("terminating:") for entry in fs.HELPER_CONTROLLER.transitions),
        "the real timeout case did not enter the TERM window",
    )
    require(
        fs.HELPER_CONTROLLER.state == fs.STATE_IDLE,
        f"controller state is {fs.HELPER_CONTROLLER.state} after the timeout case",
    )
    require(
        fs.HELPER_CONTROLLER.retained_process is None,
        "a reapable child survived the timeout case",
    )


def check_real_concurrency(fs, root_fd):
    """Concurrent real callers must never launch a second child."""

    results = []
    lock = threading.Lock()

    def call():
        outcome = fs.read_bounded_regular(root_fd, "target.md", 4096)
        with lock:
            results.append(outcome.code)

    threads = [threading.Thread(target=call) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(3)
    require(len(results) == 8, "a concurrent caller did not return")
    for code in results:
        require(
            code in ("OK", "SAFE_OPEN_HELPER_BUSY"),
            f"concurrent caller returned {code}",
        )
    require("OK" in results, "no concurrent caller completed a real read")
    require(
        fs.HELPER_CONTROLLER.state == fs.STATE_IDLE,
        "the controller did not return to idle after concurrent calls",
    )


def check_shadow_package(fs, base):
    """A hostile `brichan` package in the working directory must not execute."""

    hostile = Path(base) / "hostile"
    package = hostile / "brichan" / "techstacks"
    package.mkdir(parents=True)
    marker = hostile / "hostile-marker"
    source = (
        "import os\n"
        f"open({str(marker)!r}, 'a').write('x')\n"
        "print('HOSTILE')\n"
    )
    for path in (
        hostile / "brichan" / "__init__.py",
        package / "__init__.py",
        package / "safe_open_helper.py",
    ):
        path.write_text(source, encoding="utf-8")
    data = hostile / "data"
    data.mkdir()
    (data / "target.md").write_bytes(b"shadow-free\n")
    descriptor = os.open(data, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    previous = os.getcwd()
    try:
        os.chdir(hostile)
        outcome = fs.read_bounded_regular(descriptor, "target.md", 4096)
    finally:
        os.chdir(previous)
        os.close(descriptor)
    require(outcome.ok, f"shadow-package read returned {outcome.code}")
    require(outcome.data == b"shadow-free\n", "shadow-package read returned wrong bytes")
    require(not marker.exists(), "the planted package executed inside the bounded reader")


def run_evidence():
    from brichan.techstacks import filesystem as fs
    from brichan.techstacks import model

    require(fs.is_supported_platform(), "the platform predicate rejected this host")
    observed = []
    real_launch = fs._launch_bounded_helper

    def counting_launch(parent_fd, name, mode, limit):
        observed.append(name)
        return real_launch(parent_fd, name, mode, limit)

    fs._launch_bounded_helper = counting_launch
    try:
        with tempfile.TemporaryDirectory() as temporary:
            base = os.path.realpath(temporary)
            root = make_root(base)
            handle = fs.validate_and_open_git_root(root)
            try:
                check_metadata_classification(fs, root, handle.fd, observed)
                check_devices(fs, observed)
                before = (root / "target.md").read_bytes()
                check_regular_read(fs, handle.fd)
                check_injected_race(fs, model, handle.fd)
                check_real_timeout_cleanup(fs, handle.fd)
                check_real_concurrency(fs, handle.fd)
                check_shadow_package(fs, base)
                require(
                    (root / "target.md").read_bytes() == before,
                    "a fixture file changed during observation",
                )
                require(
                    fs.root_identity_unchanged(handle),
                    "the root identity changed during observation",
                )
            finally:
                handle.close()
    finally:
        fs._launch_bounded_helper = real_launch
    require(
        fs.HELPER_CONTROLLER.retained_process is None,
        "a reapable child survived the evidence run",
    )
    require(
        fs.HELPER_CONTROLLER.state == fs.STATE_IDLE,
        "the controller did not return to idle",
    )


def main():
    if not named_platform():
        sys.stderr.write("unsupported evidence platform\n")
        return 2
    signal.signal(signal.SIGALRM, _deadline_expired)
    signal.alarm(DEADLINE_SECONDS)
    try:
        run_evidence()
    except EvidenceError as error:
        sys.stderr.write(f"FAIL: {error}\n")
        return 1
    finally:
        signal.alarm(0)
    sys.stdout.write(f"PASS: techstack safe-open evidence ({PLATFORM_NAME})\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
