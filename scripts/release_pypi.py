#!/usr/bin/env python3
"""Release `brichan` to PyPI from a local checkout.

A PyPI upload cannot be undone: a version number is consumed permanently, and
a broken artifact cannot be replaced, only yanked and superseded. So this
script verifies first and uploads last, previews by default, and refuses to
start when anything about the release is inconsistent.

The token is read from .env (PYPI_TOKEN) and handed to twine through the
environment, never through argv, which is world-readable via ps. It is never
printed, including in error paths.

    scripts/release_pypi.py                     # preview the current version
    scripts/release_pypi.py --version 0.6.0     # bump, then preview
    scripts/release_pypi.py --publish           # actually upload
    scripts/release_pypi.py --repository testpypi --publish

Note that .github/workflows/publish.yml publishes the same distribution when a
vX.Y.Z tag is pushed. Both paths uploading one version is a conflict; see
--help for how this script leaves tagging alone.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DISTRIBUTION = "brichan"
TOKEN_VARIABLE = "PYPI_TOKEN"

REPOSITORIES = {
    "pypi": "https://upload.pypi.org/legacy/",
    "testpypi": "https://test.pypi.org/legacy/",
}

VERSION_SOURCES = {
    "pyproject.toml": re.compile(r'^(version = ")([^"]+)(")$', re.MULTILINE),
    "VERSION": re.compile(r"\A()(\d[^\s]*)(\s*)\Z"),
    "src/brida/__init__.py": re.compile(r'^(__version__ = ")([^"]+)(")$', re.MULTILINE),
}

SEMVER = re.compile(r"\A\d+\.\d+\.\d+([.-]?[0-9A-Za-z.]+)?\Z")


class ReleaseError(RuntimeError):
    """A condition that must stop the release before anything is uploaded."""


def log(message: str) -> None:
    print(f"release: {message}")


def read_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines. Values are secrets and are never logged."""
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def resolve_token(environment: dict[str, str]) -> str:
    """Prefer a real environment variable; fall back to .env."""
    token = environment.get(TOKEN_VARIABLE) or read_env_file(ROOT / ".env").get(
        TOKEN_VARIABLE
    )
    if not token:
        raise ReleaseError(
            f"{TOKEN_VARIABLE} is not set in the environment or in .env"
        )
    if not token.startswith("pypi-"):
        raise ReleaseError(
            f"{TOKEN_VARIABLE} does not look like a PyPI API token "
            "(expected it to start with 'pypi-')"
        )
    return token


def current_versions() -> dict[str, str]:
    found: dict[str, str] = {}
    for relative, pattern in VERSION_SOURCES.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        match = pattern.search(text)
        if match is None:
            raise ReleaseError(f"cannot find a version in {relative}")
        found[relative] = match.group(2)
    return found


def require_consistent_version() -> str:
    found = current_versions()
    distinct = set(found.values())
    if len(distinct) != 1:
        detail = ", ".join(f"{name}={value}" for name, value in found.items())
        raise ReleaseError(f"version sources disagree: {detail}")
    return distinct.pop()


def set_version(version: str) -> None:
    """Rewrite every version source, leaving CHANGELOG.md to the author."""
    for relative, pattern in VERSION_SOURCES.items():
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        updated, count = pattern.subn(
            lambda match: f"{match.group(1)}{version}{match.group(3)}", text
        )
        if count != 1:
            raise ReleaseError(f"cannot rewrite the version in {relative}")
        path.write_text(updated, encoding="utf-8")
    log(f"set version to {version} in {', '.join(VERSION_SOURCES)}")


def require_changelog_entry(version: str) -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{version}]" not in changelog:
        raise ReleaseError(
            f"CHANGELOG.md has no '## [{version}]' section; "
            "describe the release before publishing it"
        )


def require_clean_worktree() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        raise ReleaseError(
            "the working tree has uncommitted changes; commit or stash them "
            "so the upload matches a recorded commit"
        )


def _ssl_context() -> ssl.SSLContext | None:
    """Return a verifying context, falling back to certifi's CA bundle.

    Python installed from python.org on macOS ships without usable root
    certificates until a separate installer is run, so the default context
    cannot verify pypi.org. certifi is normally present alongside pip.
    """
    try:
        import certifi
    except ImportError:
        return None
    return ssl.create_default_context(cafile=certifi.where())


def released_versions(repository: str) -> set[str]:
    """Ask the index which versions exist. An unreachable index is fatal.

    Never assume "not published" on failure: that assumption turns a network
    blip into an upload attempt against a version that may already exist.
    """
    host = "test.pypi.org" if repository == "testpypi" else "pypi.org"
    url = f"https://{host}/pypi/{DISTRIBUTION}/json"
    attempts = [None, _ssl_context()]
    last: Exception | None = None
    for context in attempts:
        try:
            with urllib.request.urlopen(url, timeout=30, context=context) as response:
                return set(json.load(response).get("releases", {}))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return set()
            raise ReleaseError(f"cannot query {host}: HTTP {exc.code}") from exc
        except ssl.SSLError as exc:
            last = exc
            continue
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if isinstance(getattr(exc, "reason", None), ssl.SSLError):
                last = exc
                continue
            raise ReleaseError(f"cannot query {host}: {exc}") from exc
    raise ReleaseError(
        f"cannot verify TLS when querying {host}: {last}. "
        "Install certificates for this interpreter "
        "(on macOS: run 'Install Certificates.command' for your Python), "
        f"or pip install certifi for {sys.executable}"
    )


def require_unpublished(version: str, repository: str) -> None:
    if version in released_versions(repository):
        raise ReleaseError(
            f"{DISTRIBUTION} {version} is already on {repository}; "
            "a version cannot be replaced, so bump to a new one"
        )


def run(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, env=env, check=False)
    if result.returncode != 0:
        raise ReleaseError(f"command failed: {' '.join(command)}")


def require_tool(module: str) -> None:
    probe = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        check=False,
        capture_output=True,
    )
    if probe.returncode != 0:
        raise ReleaseError(
            f"{module} is not installed for {sys.executable}; "
            f"install it with: {sys.executable} -m pip install build twine"
        )


def clean_build_outputs() -> None:
    """Remove build residue before verifying and before building.

    A previous build leaves dist/ and src/*.egg-info behind. Both are ignored
    by Git but not by `make check`, whose repository contract walks the
    filesystem and fails on the binary artifacts and the stray egg-info
    directory -- so a second release run would trip over the first one.
    """
    for path in [DIST, ROOT / "build", *(ROOT / "src").glob("*.egg-info")]:
        if path.is_dir():
            shutil.rmtree(path)


def build_distributions() -> list[Path]:
    clean_build_outputs()
    run([sys.executable, "-m", "build", "--outdir", str(DIST), str(ROOT)])
    artifacts = sorted(DIST.iterdir())
    if not artifacts:
        raise ReleaseError("the build produced no artifacts")
    return artifacts


def isolated_environment() -> dict[str, str]:
    """os.environ without the variables that leak the source tree in.

    A developer shell often has PYTHONPATH pointing at src/. Inheriting it
    makes pip treat the checkout's egg-info as an existing installation and
    skip installing the wheel entirely, and makes the entry point import the
    source tree instead of the artifact -- so the smoke test would report on
    code that is not what was built.
    """
    environment = dict(os.environ)
    for variable in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"):
        environment.pop(variable, None)
    return environment


def smoke_install(wheel: Path, version: str) -> None:
    """Install the built wheel somewhere disposable and run its entry point."""
    clean = isolated_environment()
    with tempfile.TemporaryDirectory(prefix="brichan-release-") as temporary:
        environment = Path(temporary) / "venv"
        venv.create(environment, with_pip=True, clear=True)
        binaries = environment / ("Scripts" if os.name == "nt" else "bin")
        run(
            [str(binaries / "python"), "-m", "pip", "install", "--quiet", str(wheel)],
            env=clean,
        )
        entry_point = binaries / "brida"
        if not entry_point.exists():
            raise ReleaseError(
                f"the wheel installed without its console scripts: {entry_point} "
                "is missing"
            )
        result = subprocess.run(
            [str(entry_point), "--version"],
            check=False,
            capture_output=True,
            text=True,
            cwd=temporary,
            env=clean,
        )
        if result.returncode != 0 or version not in result.stdout:
            raise ReleaseError(
                "the built wheel does not report the released version: "
                f"{result.stdout.strip() or result.stderr.strip()}"
            )
    log(f"smoke test passed: brida --version reports {version}")


def upload(artifacts: list[Path], repository: str, token: str) -> None:
    environment = dict(os.environ)
    # Credentials go through the environment: argv is visible to every user
    # on the machine via ps.
    environment.update(
        {
            "TWINE_USERNAME": "__token__",
            "TWINE_PASSWORD": token,
            "TWINE_REPOSITORY_URL": REPOSITORIES[repository],
        }
    )
    run(
        [sys.executable, "-m", "twine", "upload", *[str(path) for path in artifacts]],
        env=environment,
    )


def confirm(version: str, repository: str) -> None:
    if not sys.stdin.isatty():
        raise ReleaseError(
            "refusing to publish without a terminal to confirm at; "
            "re-run interactively or pass --yes"
        )
    prompt = f"Publish {DISTRIBUTION} {version} to {repository}? This cannot be undone. "
    if input(f"{prompt}Type the version to confirm: ").strip() != version:
        raise ReleaseError("confirmation did not match; nothing was uploaded")


def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scripts/release_pypi.py",
        description=(
            "Verify, build, and optionally upload a brichan release. Previews "
            "by default: without --publish nothing leaves this machine. The "
            "PyPI token is read from PYPI_TOKEN in the environment or .env."
        ),
        epilog=(
            "This script never creates or pushes a Git tag. "
            ".github/workflows/publish.yml publishes on a vX.Y.Z tag, so "
            "pushing one after uploading here would make that workflow try to "
            "upload the same version again and fail. Pick one release path."
        ),
    )
    parser.add_argument(
        "--version",
        help="bump every version source to this value before releasing",
    )
    parser.add_argument(
        "--repository",
        choices=sorted(REPOSITORIES),
        default="pypi",
        help="index to publish to (default: pypi)",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="actually upload; without it the run stops after verification",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="skip the interactive confirmation (for automation)",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="permit uncommitted changes (the upload will not match a commit)",
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="skip 'make check' when it has already been run in this tree",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_arguments(argv)
    try:
        if args.version:
            if not SEMVER.match(args.version):
                raise ReleaseError(f"not a valid version: {args.version}")
            # Validate before writing, so a rejected release does not leave
            # the tree half-bumped.
            require_changelog_entry(args.version)
            set_version(args.version)

        version = require_consistent_version()
        log(f"releasing {DISTRIBUTION} {version} to {args.repository}")

        # Cheapest and most likely stoppers first: there is no point making
        # someone install packaging tools for a version the index will reject.
        require_changelog_entry(version)
        if not args.allow_dirty:
            require_clean_worktree()
        token = resolve_token(dict(os.environ)) if args.publish else ""
        require_unpublished(version, args.repository)
        require_tool("build")
        require_tool("twine")

        clean_build_outputs()
        if not args.skip_checks:
            run(["make", "check"])

        artifacts = build_distributions()
        run([sys.executable, "-m", "twine", "check", *[str(p) for p in artifacts]])
        wheels = [path for path in artifacts if path.suffix == ".whl"]
        if not wheels:
            raise ReleaseError("the build produced no wheel to smoke test")
        smoke_install(wheels[0], version)

        if not args.publish:
            log("verified. Artifacts ready in dist/:")
            for path in artifacts:
                log(f"  {path.name}")
            log("re-run with --publish to upload them")
            return 0

        if not args.yes:
            confirm(version, args.repository)
        upload(artifacts, args.repository, token)
        log(f"published {DISTRIBUTION} {version} to {args.repository}")
        log(f"tag the release commit if you keep tags: git tag v{version}")
        return 0
    except ReleaseError as exc:
        print(f"release failed: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("release cancelled", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
