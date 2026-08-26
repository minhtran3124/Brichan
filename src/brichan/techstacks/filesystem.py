"""Supported-platform predicate, no-symlink root anchor, and bounded reader.

Every project observation in this module is a bounded sequential observation,
never a transaction. Nothing here calls ``src/brichan/project.py``: that
resolver uses ``Path.resolve()`` and follows path symlinks, which the techstack
anchor must not do. There is no capability probe, no temporary side effect, no
thread timeout, no ``getattr(flag, 0)``, and no pathname fallback.

The one content-open path is the bounded standard-library helper child in
``safe_open_helper.py``. It is launched only by the frozen isolated argv below,
resolved from this module's own package file location, and governed by one
process-wide synchronized controller that retains the exact ``Popen`` object
through every active, cleanup, and unreaped state.
"""

from __future__ import annotations

import errno as errno_module
import os
import stat
import subprocess
import sys
import threading
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .model import (
    INTEGER_MAX,
    MODE_MAX,
    PATH_COMPONENT_BYTE_MAX,
    PROJECT_ROOT_BYTE_MAX,
    PROJECT_ROOT_BYTE_MIN,
    FileIdentity,
    RootIdentity,
    TechstackInputError,
    root_api_error_for_code,
)


# ---------------------------------------------------------------------------
# Frozen isolated helper launch contract
# ---------------------------------------------------------------------------

#: The child is resolved from this package's own file location and never from a
#: module search path. ``os.path.abspath`` is deliberately not used, because it
#: would fall back to the process working directory for a relative ``__file__``;
#: platform predicate 8 requires an absolute ``_HELPER_PATH`` instead, so a
#: relative module path fails closed as ``UNSUPPORTED_PLATFORM``.
_HELPER_DIR = os.path.dirname(__file__)
_HELPER_PATH = os.path.join(_HELPER_DIR, "safe_open_helper.py")

#: Frame protocol marker; it must equal the helper's own marker.
FRAME_MARKER = "brichan-safe-open-1"

#: Accepted helper modes. ``validate`` always pairs with limit 0.
HELPER_MODE_READ = "read"
HELPER_MODE_VALIDATE = "validate"

#: The accepted post-launch deadline is 2.000 + 0.250 + 0.250 seconds.
HELPER_FIRST_TIMEOUT = 2.000
HELPER_TERM_TIMEOUT = 0.250
HELPER_KILL_TIMEOUT = 0.250

#: Combined protocol bytes are bounded to the surface limit plus this overhead.
HELPER_PROTOCOL_OVERHEAD_BYTES = 4096

#: The bounded-helper outcome codes, plus the three context-free codes the
#: caller maps by surface.
OUTCOME_OK = "OK"
OUTCOME_NOT_FOUND = "NOT_FOUND"
OUTCOME_BYTE_LIMIT = "BYTE_LIMIT"

#: Every other outcome code is the identically named Diagnostic registry code.
_CHILD_STATUS_OUTCOMES = {
    "ok": OUTCOME_OK,
    "byte_limit": OUTCOME_BYTE_LIMIT,
    "file_changed": "FILE_CHANGED",
    "not_found": OUTCOME_NOT_FOUND,
    "symlink": "SYMLINK_REJECTED",
    "directory": "DIRECTORY_REJECTED",
    "fifo": "FIFO_REJECTED",
    "socket": "SOCKET_REJECTED",
    "device": "DEVICE_REJECTED",
    "non_regular": "NON_REGULAR_REJECTED",
    "path_component_not_directory": "PATH_COMPONENT_NOT_DIRECTORY",
    "unreadable": "UNREADABLE_FILE",
    "special_unavailable": "SPECIAL_FILE_UNAVAILABLE",
    "io_error": "FILESYSTEM_IO_ERROR",
    "resource_limit": "RESOURCE_LIMIT",
    "unsupported_safe_open": "UNSUPPORTED_SAFE_OPEN",
    "filesystem_error": "FILESYSTEM_ERROR",
    "metadata_range": "OS_METADATA_RANGE",
}

#: Closed errno mapping for parent-side metadata and directory operations.
_ERRNO_OUTCOMES = {
    errno_module.ENOENT: OUTCOME_NOT_FOUND,
    errno_module.ELOOP: "SYMLINK_REJECTED",
    errno_module.EMLINK: "SYMLINK_REJECTED",
    errno_module.ENOTDIR: "PATH_COMPONENT_NOT_DIRECTORY",
    errno_module.EISDIR: "DIRECTORY_REJECTED",
    errno_module.EACCES: "UNREADABLE_FILE",
    errno_module.EPERM: "UNREADABLE_FILE",
    errno_module.ENXIO: "SPECIAL_FILE_UNAVAILABLE",
    errno_module.ENODEV: "SPECIAL_FILE_UNAVAILABLE",
    errno_module.EINVAL: "UNSUPPORTED_SAFE_OPEN",
    errno_module.ENOTSUP: "UNSUPPORTED_SAFE_OPEN",
    errno_module.EOPNOTSUPP: "UNSUPPORTED_SAFE_OPEN",
    errno_module.ESTALE: "FILESYSTEM_IO_ERROR",
    errno_module.EIO: "FILESYSTEM_IO_ERROR",
    errno_module.EMFILE: "RESOURCE_LIMIT",
    errno_module.ENFILE: "RESOURCE_LIMIT",
    errno_module.ENOMEM: "RESOURCE_LIMIT",
}

#: Root-context caller codes for the same closed errno classes.
_ERRNO_ROOT_CODES = {
    errno_module.ENOENT: "PROJECT_NOT_GIT_ROOT",
    errno_module.ELOOP: "PROJECT_ROOT_SYMLINK",
    errno_module.EMLINK: "PROJECT_ROOT_SYMLINK",
    errno_module.ENOTDIR: "PROJECT_ROOT_NOT_DIRECTORY",
    errno_module.EACCES: "PROJECT_ROOT_UNREADABLE",
    errno_module.EPERM: "PROJECT_ROOT_UNREADABLE",
    errno_module.ESTALE: "PROJECT_ROOT_IO_ERROR",
    errno_module.EIO: "PROJECT_ROOT_IO_ERROR",
    errno_module.EMFILE: "PROJECT_ROOT_RESOURCE_LIMIT",
    errno_module.ENFILE: "PROJECT_ROOT_RESOURCE_LIMIT",
    errno_module.ENOMEM: "PROJECT_ROOT_RESOURCE_LIMIT",
    errno_module.EINVAL: "PROJECT_ROOT_UNSUPPORTED_SAFE_OPEN",
    errno_module.ENOTSUP: "PROJECT_ROOT_UNSUPPORTED_SAFE_OPEN",
    errno_module.EOPNOTSUPP: "PROJECT_ROOT_UNSUPPORTED_SAFE_OPEN",
}

#: Root-context caller codes for the four bounded-helper outcomes.
_HELPER_ROOT_CODES = {
    "SAFE_OPEN_HELPER_TIMEOUT": "PROJECT_ROOT_HELPER_TIMEOUT",
    "SAFE_OPEN_HELPER_FAILED": "PROJECT_ROOT_HELPER_FAILED",
    "SAFE_OPEN_HELPER_LEAK": "PROJECT_ROOT_HELPER_LEAK",
    "SAFE_OPEN_HELPER_BUSY": "PROJECT_ROOT_HELPER_BUSY",
}


# ---------------------------------------------------------------------------
# Supported-platform predicate
# ---------------------------------------------------------------------------


def _predicate_1() -> bool:
    return os.name == "posix"


def _predicate_2() -> bool:
    return sys.platform == "linux" or sys.platform.startswith("darwin")


def _predicate_3() -> bool:
    for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK"):
        flag = getattr(os, name, None)
        if not isinstance(flag, int) or isinstance(flag, bool) or flag == 0:
            return False
    return True


def _predicate_4() -> bool:
    return (
        os.open in os.supports_dir_fd
        and os.stat in os.supports_dir_fd
        and os.stat in os.supports_follow_symlinks
    )


def _predicate_5() -> bool:
    for callable_object in (os.stat, os.fstat, os.read, os.close, subprocess.Popen):
        if not callable(callable_object):
            return False
    for name in ("communicate", "terminate", "kill", "wait"):
        if not callable(getattr(subprocess.Popen, name, None)):
            return False
    if not hasattr(subprocess, "TimeoutExpired"):
        return False
    return "pass_fds" in subprocess.Popen.__init__.__code__.co_varnames


def _predicate_6() -> bool:
    return sys.version_info >= (3, 10)


def _predicate_7() -> bool:
    executable = sys.executable
    if not isinstance(executable, str) or not executable or not os.path.isabs(executable):
        return False
    try:
        info = os.stat(executable)
    except OSError:
        return False
    return stat.S_ISREG(info.st_mode)


def _predicate_8() -> bool:
    if sys.getfilesystemencoding() != "utf-8":
        return False
    if not os.path.isabs(_HELPER_PATH):
        return False
    try:
        info = os.stat(_HELPER_PATH, follow_symlinks=False)
    except OSError:
        return False
    return stat.S_ISREG(info.st_mode)


#: The eight ordered V1 platform predicates. Each reads already loaded
#: interpreter state or performs one metadata call on a Brichan-owned file.
PLATFORM_PREDICATES = (
    _predicate_1,
    _predicate_2,
    _predicate_3,
    _predicate_4,
    _predicate_5,
    _predicate_6,
    _predicate_7,
    _predicate_8,
)


def failing_platform_predicates() -> tuple[int, ...]:
    """Return the one-based ordinals of every failing platform predicate."""

    return tuple(
        ordinal
        for ordinal, predicate in enumerate(PLATFORM_PREDICATES, start=1)
        if not predicate()
    )


def is_supported_platform() -> bool:
    """Return True when every V1 platform predicate holds."""

    return not failing_platform_predicates()


# ---------------------------------------------------------------------------
# Observation results
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Observation:
    """One bounded observation outcome.

    ``code`` is ``OK``, ``NOT_FOUND``, ``BYTE_LIMIT``, or an identically named
    Diagnostic registry code. ``identity`` and ``data`` are present only for an
    ``OK`` regular read; ``validate`` returns ``OK`` with empty data.
    """

    code: str
    errno_value: int | None = None
    identity: FileIdentity | None = None
    data: bytes | None = None

    @property
    def ok(self) -> bool:
        return self.code == OUTCOME_OK


def _identity_from_stat(info: os.stat_result) -> FileIdentity | None:
    """Return the six-field identity, or None when a field is out of range."""

    fields = (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )
    for value in (fields[0], fields[1], fields[3], fields[4], fields[5]):
        if not isinstance(value, int) or not 0 <= value <= INTEGER_MAX:
            return None
    if not 0 <= fields[2] <= MODE_MAX:
        return None
    return FileIdentity(
        device=fields[0],
        inode=fields[1],
        mode=fields[2],
        size=fields[3],
        mtime_ns=fields[4],
        ctime_ns=fields[5],
    )


def _nonregular_outcome(mode: int) -> str:
    if stat.S_ISDIR(mode):
        return "DIRECTORY_REJECTED"
    if stat.S_ISFIFO(mode):
        return "FIFO_REJECTED"
    if stat.S_ISSOCK(mode):
        return "SOCKET_REJECTED"
    if stat.S_ISCHR(mode) or stat.S_ISBLK(mode):
        return "DEVICE_REJECTED"
    if stat.S_ISLNK(mode):
        return "SYMLINK_REJECTED"
    return "NON_REGULAR_REJECTED"


def _errno_outcome(error: OSError) -> Observation:
    code = _ERRNO_OUTCOMES.get(error.errno, "FILESYSTEM_ERROR")
    return Observation(code=code, errno_value=_decimal_errno(error))


def _decimal_errno(error: OSError) -> int:
    return -1 if error.errno is None else int(error.errno)


def classify_entry(parent_fd: int, name: str) -> Observation:
    """Metadata-classify one entry no-follow, before any content open.

    This metadata call is the type authority. A directory, FIFO, socket,
    character or block device, symlink, or unknown nonregular mode returns its
    exact type outcome here, so no content open is ever attempted for it.
    """

    try:
        info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError as error:
        return _errno_outcome(error)
    # Metadata type is the authority and precedes every other classification,
    # so a nonregular entry reports its exact type outcome even when its
    # device or time fields fall outside the supported integer range.
    if not stat.S_ISREG(info.st_mode):
        return Observation(code=_nonregular_outcome(info.st_mode))
    identity = _identity_from_stat(info)
    if identity is None:
        return Observation(code="OS_METADATA_RANGE")
    return Observation(code=OUTCOME_OK, identity=identity)


def open_directory(parent_fd: int | None, name: str) -> tuple[int | None, Observation]:
    """Metadata-classify then open one directory no-follow and identity-check."""

    try:
        info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError as error:
        return None, _errno_outcome(error)
    if not stat.S_ISDIR(info.st_mode):
        if stat.S_ISLNK(info.st_mode):
            return None, Observation(code="SYMLINK_REJECTED")
        return None, Observation(code="PATH_COMPONENT_NOT_DIRECTORY")
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=parent_fd,
        )
    except OSError as error:
        return None, _errno_outcome(error)
    try:
        opened = os.fstat(descriptor)
    except OSError as error:
        os.close(descriptor)
        return None, _errno_outcome(error)
    if (
        not stat.S_ISDIR(opened.st_mode)
        or opened.st_dev != info.st_dev
        or opened.st_ino != info.st_ino
    ):
        os.close(descriptor)
        return None, Observation(code="FILE_CHANGED")
    return descriptor, Observation(code=OUTCOME_OK)


# ---------------------------------------------------------------------------
# Process-wide synchronized helper lifecycle
# ---------------------------------------------------------------------------

#: The six controller states. At most one launched or unreaped child can exist
#: process-wide, because the controller owns exactly one slot.
STATE_IDLE = "idle"
STATE_RESERVED = "reserved"
STATE_ACTIVE = "active"
STATE_TERMINATING = "terminating"
STATE_KILLING = "killing"
STATE_UNREAPED = "unreaped"

#: Bounded transition log length; tests assert exact transition sequences.
_TRANSITION_LOG_LIMIT = 512


class _HelperController:
    """One process-wide reservation and retained-``Popen`` lifecycle.

    Every state and object comparison uses ``(generation, object identity)``
    while holding the lock, so a stale caller can never clear a newer
    reservation. A PID is observational only and is never lifecycle authority:
    an unreaped process retains its ``Popen``, and the operating system cannot
    reuse its PID before that object reaps it.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._generation = 0
        self._state = STATE_IDLE
        self._process: subprocess.Popen[bytes] | None = None
        self._process_generation: int | None = None
        self._stdout_closed = True
        self._stderr_closed = True
        self.transitions: list[str] = []

    # -- observation ------------------------------------------------------

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def retained_process(self) -> subprocess.Popen[bytes] | None:
        with self._lock:
            return self._process

    def _log(self, message: str) -> None:
        if len(self.transitions) < _TRANSITION_LOG_LIMIT:
            self.transitions.append(message)

    def reset_for_test(self) -> None:
        """Clear controller state; owned by tests and never by production."""

        with self._lock:
            self._generation = 0
            self._state = STATE_IDLE
            self._process = None
            self._process_generation = None
            self._stdout_closed = True
            self._stderr_closed = True
            self.transitions = []

    # -- transitions ------------------------------------------------------

    def reserve(self) -> tuple[str, int]:
        """Reserve the single slot, or refuse with ``busy`` or ``leak``."""

        with self._lock:
            if self._state == STATE_UNREAPED:
                process = self._process
                try:
                    status = None if process is None else process.poll()
                except Exception:
                    self._log("unreaped/poll-raised")
                    return "leak", 0
                if status is None:
                    self._log("unreaped/poll-null")
                    return "leak", 0
                self._log("unreaped/reaped")
                self._close_pipes_locked()
                self._process = None
                self._process_generation = None
                self._state = STATE_IDLE
            if self._state != STATE_IDLE:
                self._log(f"{self._state}/busy")
                return "busy", 0
            self._generation += 1
            self._state = STATE_RESERVED
            self._log(f"reserved:{self._generation}")
            return "reserved", self._generation

    def attach(self, generation: int, process: subprocess.Popen[bytes]) -> None:
        """Store the exact launched object and become active."""

        with self._lock:
            self._require_reservation_locked(generation)
            self._process = process
            self._process_generation = generation
            self._stdout_closed = process.stdout is None
            self._stderr_closed = process.stderr is None
            self._state = STATE_ACTIVE
            self._log(f"active:{generation}")

    def launch_failed(self, generation: int) -> None:
        """Release the reservation when ``Popen`` raised before returning."""

        with self._lock:
            self._require_reservation_locked(generation)
            self._state = STATE_IDLE
            self._process = None
            self._process_generation = None
            self._log(f"launch-failed:{generation}")

    def mark(self, generation: int, state: str) -> None:
        """Record the terminating or killing cleanup stage."""

        with self._lock:
            self._require_owner_locked(generation)
            self._state = state
            self._log(f"{state}:{generation}")

    def finish(self, generation: int) -> None:
        """Close both pipes exactly once and return the slot to ``idle``."""

        with self._lock:
            self._require_owner_locked(generation)
            self._close_pipes_locked()
            self._process = None
            self._process_generation = None
            self._state = STATE_IDLE
            self._log(f"idle:{generation}")

    def abandon(self, generation: int) -> None:
        """Retain the same object as ``unreaped`` after the KILL window."""

        with self._lock:
            self._require_owner_locked(generation)
            self._close_pipes_locked()
            self._state = STATE_UNREAPED
            self._log(f"unreaped:{generation}")

    # -- internals --------------------------------------------------------

    def _require_reservation_locked(self, generation: int) -> None:
        if self._state != STATE_RESERVED or self._generation != generation:
            raise RuntimeError("stale helper reservation")

    def _require_owner_locked(self, generation: int) -> None:
        if self._process_generation != generation or self._generation != generation:
            raise RuntimeError("stale helper generation")

    def _close_pipes_locked(self) -> None:
        """Close stdout and stderr exactly once, guarded by two booleans."""

        process = self._process
        if process is None:
            return
        if not self._stdout_closed:
            self._stdout_closed = True
            try:
                if process.stdout is not None:
                    process.stdout.close()
            except Exception:
                self._log("stdout-close-raised")
        if not self._stderr_closed:
            self._stderr_closed = True
            try:
                if process.stderr is not None:
                    process.stderr.close()
            except Exception:
                self._log("stderr-close-raised")


#: The one module-global controller. Concurrent API and doctor calls share it,
#: so process-wide states permit zero or one launched or unreaped helper.
HELPER_CONTROLLER = _HelperController()


def helper_argv(parent_fd: int, name: str, mode: str, limit: int) -> list[str]:
    """Return the frozen isolated child argv for every surface and both modes."""

    return [
        sys.executable,
        "-I",
        "-S",
        "-B",
        "-X",
        "utf8=1",
        _HELPER_PATH,
        "--dir-fd",
        str(parent_fd),
        "--name",
        name,
        "--mode",
        mode,
        "--limit",
        str(limit),
    ]


def helper_popen_keywords(parent_fd: int) -> dict[str, Any]:
    """Return the exact ``Popen`` keywords, and no others."""

    return {
        "shell": False,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "close_fds": True,
        "pass_fds": (parent_fd,),
        "cwd": _HELPER_DIR,
        "env": {},
    }


def _parse_frame(
    stdout: bytes,
    stderr: bytes,
    returncode: int | None,
    limit: int,
) -> Observation:
    """Validate one bounded result frame, or report a helper failure."""

    if stderr:
        return Observation(code="SAFE_OPEN_HELPER_FAILED")
    if returncode != 0:
        return Observation(code="SAFE_OPEN_HELPER_FAILED")
    if len(stdout) > limit + HELPER_PROTOCOL_OVERHEAD_BYTES:
        return Observation(code="SAFE_OPEN_HELPER_FAILED")
    newline = stdout.find(b"\n")
    if newline < 0:
        return Observation(code="SAFE_OPEN_HELPER_FAILED")
    try:
        header = stdout[:newline].decode("utf-8")
    except UnicodeDecodeError:
        return Observation(code="SAFE_OPEN_HELPER_FAILED")
    parts = header.split(" ")
    if len(parts) != 10 or parts[0] != FRAME_MARKER:
        return Observation(code="SAFE_OPEN_HELPER_FAILED")
    status = parts[1]
    if status not in _CHILD_STATUS_OUTCOMES:
        return Observation(code="SAFE_OPEN_HELPER_FAILED")
    try:
        numbers = [int(part) for part in parts[2:]]
    except ValueError:
        return Observation(code="SAFE_OPEN_HELPER_FAILED")
    payload = stdout[newline + 1 :]
    declared = numbers[7]
    if declared != len(payload) or declared > limit:
        return Observation(code="SAFE_OPEN_HELPER_FAILED")
    errno_value = numbers[0]
    identity_fields = numbers[1:7]
    identity: FileIdentity | None = None
    if status not in ("filesystem_error", "metadata_range") and any(identity_fields):
        device, inode, mode, size, mtime_ns, ctime_ns = identity_fields
        if (
            min(device, inode, size, mtime_ns, ctime_ns) < 0
            or max(device, inode, size, mtime_ns, ctime_ns) > INTEGER_MAX
            or not 0 <= mode <= MODE_MAX
        ):
            return Observation(code="SAFE_OPEN_HELPER_FAILED")
        identity = FileIdentity(
            device=device,
            inode=inode,
            mode=mode,
            size=size,
            mtime_ns=mtime_ns,
            ctime_ns=ctime_ns,
        )
    return Observation(
        code=_CHILD_STATUS_OUTCOMES[status],
        errno_value=errno_value if errno_value >= 0 else -1,
        identity=identity,
        data=payload if status == "ok" else None,
    )


def _launch_bounded_helper(parent_fd: int, name: str, mode: str, limit: int) -> Observation:
    """Launch and drive exactly one bounded helper child.

    This is the only content-open path in production. Tests and the two local
    platform evidence scripts instrument this function to prove that no
    metadata-observed nonregular entry ever reaches a content open.
    """

    status, generation = HELPER_CONTROLLER.reserve()
    if status == "busy":
        return Observation(code="SAFE_OPEN_HELPER_BUSY")
    if status == "leak":
        return Observation(code="SAFE_OPEN_HELPER_LEAK")
    try:
        process = subprocess.Popen(
            helper_argv(parent_fd, name, mode, limit),
            **helper_popen_keywords(parent_fd),
        )
    except Exception:
        HELPER_CONTROLLER.launch_failed(generation)
        return Observation(code="SAFE_OPEN_HELPER_FAILED")
    except BaseException:
        # KeyboardInterrupt and SystemExit release the reservation exactly as
        # Design section 16 requires, then continue to unwind.
        HELPER_CONTROLLER.launch_failed(generation)
        raise
    HELPER_CONTROLLER.attach(generation, process)
    return _drive_helper(process, generation, limit)


def _reaped(process: subprocess.Popen[bytes]) -> bool:
    """Report whether the child has been reaped, treating a raising ``poll``
    as "not reaped".

    ``reserve()`` already guards its own ``poll()`` this way, so a raising
    ``poll`` in the cleanup sequence falls through to ``abandon()`` and the
    closed ``SAFE_OPEN_HELPER_LEAK`` outcome instead of escaping the API and
    stranding the controller in a cleanup state.
    """

    try:
        return process.poll() is not None
    except Exception:
        return False


def _drive_helper(
    process: subprocess.Popen[bytes],
    generation: int,
    limit: int,
) -> Observation:
    """Run the bounded communicate, TERM, and KILL windows in order."""

    try:
        stdout, stderr = process.communicate(timeout=HELPER_FIRST_TIMEOUT)
    except subprocess.TimeoutExpired:
        return _cleanup_helper(process, generation)
    except Exception:
        return _fail_helper(process, generation)
    if not _reaped(process):
        return _cleanup_helper(process, generation)
    HELPER_CONTROLLER.finish(generation)
    return _parse_frame(stdout or b"", stderr or b"", process.returncode, limit)


def _cleanup_helper(process: subprocess.Popen[bytes], generation: int) -> Observation:
    """Execute the TERM and KILL windows, then reap, retain, or fail."""

    try:
        HELPER_CONTROLLER.mark(generation, STATE_TERMINATING)
        failed = False
        try:
            process.terminate()
        except Exception:
            failed = True
        try:
            process.communicate(timeout=HELPER_TERM_TIMEOUT)
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            failed = True
        if _reaped(process):
            HELPER_CONTROLLER.finish(generation)
            return Observation(
                code="SAFE_OPEN_HELPER_FAILED" if failed else "SAFE_OPEN_HELPER_TIMEOUT"
            )
        HELPER_CONTROLLER.mark(generation, STATE_KILLING)
        try:
            process.kill()
        except Exception:
            failed = True
        try:
            process.communicate(timeout=HELPER_KILL_TIMEOUT)
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            failed = True
        if _reaped(process):
            HELPER_CONTROLLER.finish(generation)
            return Observation(
                code="SAFE_OPEN_HELPER_FAILED" if failed else "SAFE_OPEN_HELPER_TIMEOUT"
            )
        HELPER_CONTROLLER.abandon(generation)
        return Observation(code="SAFE_OPEN_HELPER_LEAK")
    except BaseException:
        # A KeyboardInterrupt or SystemExit inside the TERM/KILL window keeps
        # propagating, exactly as L2-i1-4 requires, but must not strand the
        # slot in ``terminating`` or ``killing``, which ``reserve()`` never
        # self-heals. Retain the same object as ``unreaped`` and unwind.
        if HELPER_CONTROLLER.state in (STATE_TERMINATING, STATE_KILLING):
            HELPER_CONTROLLER.abandon(generation)
        raise


def _fail_helper(process: subprocess.Popen[bytes], generation: int) -> Observation:
    """Handle a raising communicate through the remaining bounded stages."""

    outcome = _cleanup_helper(process, generation)
    if outcome.code == "SAFE_OPEN_HELPER_LEAK":
        return outcome
    return Observation(code="SAFE_OPEN_HELPER_FAILED")


# ---------------------------------------------------------------------------
# Bounded regular reads
# ---------------------------------------------------------------------------


def read_bounded_regular(parent_fd: int, name: str, limit: int) -> Observation:
    """Read one metadata-regular entry through the bounded helper.

    A metadata-observed nonregular entry returns its exact type outcome without
    any content open. Only a metadata-regular candidate reaches the helper.
    """

    classified = classify_entry(parent_fd, name)
    if not classified.ok:
        return classified
    observed = _launch_bounded_helper(parent_fd, name, HELPER_MODE_READ, limit)
    if not observed.ok:
        if observed.code == OUTCOME_BYTE_LIMIT:
            return Observation(code=OUTCOME_BYTE_LIMIT, identity=classified.identity)
        return observed
    if observed.identity != classified.identity:
        return Observation(code="FILE_CHANGED", identity=classified.identity)
    data = observed.data or b""
    if len(data) != classified.identity.size:  # type: ignore[union-attr]
        return Observation(code="FILE_CHANGED", identity=classified.identity)
    return Observation(code=OUTCOME_OK, identity=classified.identity, data=data)


def validate_bounded_regular(parent_fd: int, name: str) -> Observation:
    """Identity-check one metadata-regular entry without reading its content."""

    classified = classify_entry(parent_fd, name)
    if not classified.ok:
        return classified
    observed = _launch_bounded_helper(parent_fd, name, HELPER_MODE_VALIDATE, 0)
    if not observed.ok:
        return observed
    if observed.identity != classified.identity:
        return Observation(code="FILE_CHANGED", identity=classified.identity)
    return Observation(code=OUTCOME_OK, identity=classified.identity, data=b"")


# ---------------------------------------------------------------------------
# No-symlink top-level Git-root anchor
# ---------------------------------------------------------------------------

#: The literal Git marker validated relative to the held root descriptor.
GIT_MARKER_NAME = ".git"


@dataclass
class RootHandle:
    """One anchored project root and its held no-symlink descriptor."""

    path: str
    fd: int
    identity: RootIdentity

    def close(self) -> None:
        """Close the held root descriptor exactly once."""

        if self.fd >= 0:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = -1


def _root_error(error: OSError) -> TechstackInputError:
    """Map one root-walk OSError to its exact caller error."""

    code = _ERRNO_ROOT_CODES.get(error.errno, "PROJECT_ROOT_FILESYSTEM_ERROR")
    return root_api_error_for_code(code, errno_value=_decimal_errno(error))


def _root_code_error(code: str, *, errno_value: int | None = None) -> TechstackInputError:
    return root_api_error_for_code(code, errno_value=errno_value)


def validate_root_argument(project_root: Any) -> str:
    """Validate the lexical root contract and return its ``os.fspath`` value.

    No ``expanduser()``, ``Path.resolve()``, ``realpath()``, or implicit
    current-directory discovery participates.
    """

    if not isinstance(project_root, Path):
        raise _root_code_error("PROJECT_ROOT_TYPE")
    value = os.fspath(project_root)
    if not isinstance(value, str):
        raise _root_code_error("PROJECT_ROOT_TYPE")
    length = len(value.encode("utf-8", "surrogatepass"))
    if not PROJECT_ROOT_BYTE_MIN <= length <= PROJECT_ROOT_BYTE_MAX:
        raise _root_code_error("PROJECT_ROOT_BYTE_LIMIT")
    if not value.startswith("/"):
        raise _root_code_error("PROJECT_ROOT_NOT_ABSOLUTE")
    if unicodedata.normalize("NFC", value) != value:
        raise _root_code_error("PROJECT_ROOT_NOT_CANONICAL")
    if "\x00" in value or "~" in value or value.endswith("/"):
        raise _root_code_error("PROJECT_ROOT_NOT_CANONICAL")
    for component in value.split("/")[1:]:
        if not component or component in (".", ".."):
            raise _root_code_error("PROJECT_ROOT_NOT_CANONICAL")
        if len(component.encode("utf-8", "surrogatepass")) > PATH_COMPONENT_BYTE_MAX:
            raise _root_code_error("PROJECT_ROOT_NOT_CANONICAL")
    return value


def _open_root_descriptor(value: str) -> tuple[int, os.stat_result]:
    """Walk from ``/`` with no-follow metadata classification and identity."""

    try:
        descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as error:
        raise _root_error(error) from None
    info: os.stat_result
    try:
        info = os.fstat(descriptor)
    except OSError as error:
        os.close(descriptor)
        raise _root_error(error) from None
    for component in value.split("/")[1:]:
        try:
            metadata = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
        except OSError as error:
            os.close(descriptor)
            raise _root_error(error) from None
        if stat.S_ISLNK(metadata.st_mode):
            os.close(descriptor)
            raise _root_code_error("PROJECT_ROOT_SYMLINK")
        if not stat.S_ISDIR(metadata.st_mode):
            os.close(descriptor)
            raise _root_code_error("PROJECT_ROOT_NOT_DIRECTORY")
        try:
            child = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
        except OSError as error:
            os.close(descriptor)
            raise _root_error(error) from None
        os.close(descriptor)
        descriptor = child
        try:
            info = os.fstat(descriptor)
        except OSError as error:
            os.close(descriptor)
            raise _root_error(error) from None
        # The held descriptor must be the exact entry the metadata call
        # classified; a replacement between stat and open is not a root.
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_dev != metadata.st_dev
            or info.st_ino != metadata.st_ino
        ):
            os.close(descriptor)
            raise _root_code_error("PROJECT_NOT_GIT_ROOT")
    return descriptor, info


def _root_observation_error(observation: Observation) -> TechstackInputError:
    """Map one ``.git`` observation code to its exact root caller error.

    Both ``.git`` branches share this translation, so a directory ``.git`` and
    a regular worktree file report the same Design section 14 root code for the
    same observed class.
    """

    helper_code = _HELPER_ROOT_CODES.get(observation.code)
    if helper_code is not None:
        return _root_code_error(helper_code)
    if observation.code == "UNREADABLE_FILE":
        return _root_code_error("PROJECT_ROOT_UNREADABLE")
    if observation.code == "FILESYSTEM_IO_ERROR":
        return _root_code_error("PROJECT_ROOT_IO_ERROR")
    if observation.code == "RESOURCE_LIMIT":
        return _root_code_error("PROJECT_ROOT_RESOURCE_LIMIT")
    if observation.code == "UNSUPPORTED_SAFE_OPEN":
        return _root_code_error("PROJECT_ROOT_UNSUPPORTED_SAFE_OPEN")
    if observation.code == "SYMLINK_REJECTED":
        return _root_code_error("PROJECT_ROOT_SYMLINK")
    if observation.code == "FILESYSTEM_ERROR":
        return _root_code_error(
            "PROJECT_ROOT_FILESYSTEM_ERROR", errno_value=observation.errno_value
        )
    return _root_code_error("PROJECT_NOT_GIT_ROOT")


def _validate_git_marker(root_fd: int) -> None:
    """Metadata-classify literal ``.git`` and validate it without a path read."""

    try:
        metadata = os.stat(GIT_MARKER_NAME, dir_fd=root_fd, follow_symlinks=False)
    except OSError as error:
        raise _root_error(error) from None
    if stat.S_ISLNK(metadata.st_mode):
        raise _root_code_error("PROJECT_ROOT_SYMLINK")
    if stat.S_ISDIR(metadata.st_mode):
        descriptor, classified = open_directory(root_fd, GIT_MARKER_NAME)
        if descriptor is None:
            raise _root_observation_error(classified)
        os.close(descriptor)
        return
    if not stat.S_ISREG(metadata.st_mode):
        raise _root_code_error("PROJECT_NOT_GIT_ROOT")
    observation = validate_bounded_regular(root_fd, GIT_MARKER_NAME)
    if observation.ok:
        return
    raise _root_observation_error(observation)


def validate_and_open_git_root(project_root: Any) -> RootHandle:
    """Anchor one absolute no-symlink top-level Git root and hold it open.

    Both public APIs call this one implementation before project discovery. No
    ancestor search occurs, and no content open happens for a directory
    ``.git``; a regular worktree file is identity-checked through the bounded
    helper in validate-only mode.
    """

    value = validate_root_argument(project_root)
    descriptor, info = _open_root_descriptor(value)
    try:
        _validate_git_marker(descriptor)
    except BaseException:
        # The held root descriptor is closed on every exception, not only on
        # the caller errors this function raises itself.
        os.close(descriptor)
        raise
    identity_fields = (info.st_dev, info.st_ino)
    for number in identity_fields:
        if not 0 <= number <= INTEGER_MAX:
            os.close(descriptor)
            raise _root_code_error("PROJECT_ROOT_FILESYSTEM_ERROR", errno_value=None)
    return RootHandle(
        path=value,
        fd=descriptor,
        identity=RootIdentity(device=info.st_dev, inode=info.st_ino),
    )


def root_identity_unchanged(handle: RootHandle) -> bool:
    """Recheck root identity by textual no-follow reopen after selected reads."""

    try:
        metadata = os.stat(handle.path, follow_symlinks=False)
    except OSError:
        return False
    if not stat.S_ISDIR(metadata.st_mode):
        return False
    return (
        metadata.st_dev == handle.identity.device
        and metadata.st_ino == handle.identity.inode
    )
