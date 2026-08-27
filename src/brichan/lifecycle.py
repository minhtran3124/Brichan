"""Schema-v1 project initialization and diagnostics."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from importlib.resources import files
from pathlib import Path
from typing import Any

from brichan import __version__
from brichan.orchestration.model_routing import RoutingError, load_settings

from .project import ProjectPaths


SCHEMA_VERSION = 1
LAYOUT_NAME = "brichan-project"
RESOURCE_PACKAGE = "brichan.resources.dogfood_v1"
IMMUTABLE_PATHS = (
    "config/model-routing.json",
    "policy/bootstrap.md",
    "policy/identity.md",
    "policy/memory-policy.md",
    "policy/operating-principles.md",
    "policy/techstacks.md",
    "skills/herdr-orchestration/SKILL.md",
    "skills/herdr-orchestration/references/commands.md",
    "skills/herdr-orchestration/references/handoff-receipt.md",
    "skills/herdr-orchestration/references/task-packet.md",
)
MUTABLE_PATHS = (
    "project-memory/index.md",
    "project-memory/main/current-state.md",
    "project-memory/main/decisions.md",
    "project-memory/main/overview.md",
    "project-memory/main/references.md",
    "project-memory/main/tasks.md",
)

#: Root-level agent entry files. `init` creates each one from the
#: `agent-entry/` resource only when the repository does not already have it
#: (a symlink counts as having it); after creation they belong to the
#: repository and are never inspected, hashed, or modified again.
AGENT_ENTRY_PATHS = ("AGENTS.md", "CLAUDE.md")
AGENT_ENTRY_RESOURCE_DIR = "agent-entry"

#: Codex skill-discovery export. `brichan run` injects the managed skill from
#: `.brichan/skills/` explicitly, but a `codex` session started directly in
#: the repository discovers skills only under `.agents/skills/`. `init`
#: always exports the skill there when this specific skill directory is absent.
#: Existing `.agents/` content is preserved, and an existing export remains
#: unmanaged and is never overwritten.
AGENT_SKILLS_DIR = ".agents/skills/herdr-orchestration"
_SKILL_RESOURCE_PREFIX = "skills/herdr-orchestration/"


#: Version of the `doctor --json` document. Independent of the `.brichan`
#: state schema: this describes the diagnostic report, not the installed
#: footprint.
DOCTOR_SCHEMA_VERSION = 2

STATUS_OK = "ok"
STATUS_MISSING = "missing"
STATUS_INVALID = "invalid"
STATUS_UNAVAILABLE = "unavailable"

#: Worse statuses win when a section aggregates its checks.
_STATUS_RANK = {
    STATUS_OK: 0,
    STATUS_UNAVAILABLE: 1,
    STATUS_MISSING: 2,
    STATUS_INVALID: 3,
}

#: Source-checkout contract, drawn from the `internal-policy`,
#: `runtime-config`, and `durable-state` entries of
#: `config/repository-paths.json`.
CHECKOUT_POLICY_PATHS = (
    ("docs/policy/identity.md", "file"),
    ("docs/policy/memory-policy.md", "file"),
    ("docs/policy/model-catalog.md", "file"),
    ("docs/policy/operating-principles.md", "file"),
    ("docs/policy/reviewer.md", "file"),
    ("docs/policy/techstacks.md", "file"),
)
CHECKOUT_MEMORY_PATHS = (
    ("projects", "directory"),
    ("projects/index.md", "file"),
)
ROUTING_RELATIVE_PATH = "config/model-routing.json"

#: Installed-project contract, taken from the managed footprint.
INSTALLED_POLICY_PATHS = tuple(
    (path, "file") for path in IMMUTABLE_PATHS if path.startswith("policy/")
)
INSTALLED_MEMORY_PATHS = tuple((path, "file") for path in MUTABLE_PATHS)


class StateKind(str, Enum):
    UNINITIALIZED = "uninitialized"
    HEALTHY = "healthy"
    MALFORMED = "malformed"
    INCOMPATIBLE = "incompatible"


EXIT_CODES = {
    StateKind.HEALTHY: 0,
    StateKind.UNINITIALIZED: 1,
    StateKind.MALFORMED: 2,
    StateKind.INCOMPATIBLE: 3,
}


@dataclass(frozen=True)
class Inspection:
    kind: StateKind
    detail: str
    manifest: dict[str, Any] | None = None

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.kind]


def _resource_bytes(relative_path: str) -> bytes:
    return files(RESOURCE_PACKAGE).joinpath(relative_path).read_bytes()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def intended_manifest() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "package_version": __version__,
        "layout": LAYOUT_NAME,
        "runtime": "codex",
        "resources": {
            path: _sha256(_resource_bytes(path)) for path in IMMUTABLE_PATHS
        },
        "mutable_paths": list(MUTABLE_PATHS),
    }


def manifest_bytes() -> bytes:
    return (
        json.dumps(intended_manifest(), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def documented_footprint() -> tuple[str, ...]:
    return ("manifest.json", *IMMUTABLE_PATHS, *MUTABLE_PATHS)


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"cannot read manifest: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"manifest contains malformed JSON at line {exc.lineno}, "
            f"column {exc.colno}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError("manifest root must be a JSON object")
    return payload


def _lstat(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def _regular_file_problem(state_root: Path, relative_path: str) -> str | None:
    current = state_root
    for component in Path(relative_path).parts[:-1]:
        current = current / component
        metadata = _lstat(current)
        if metadata is None:
            return f"required parent directory is missing: {current.relative_to(state_root)}"
        if stat.S_ISLNK(metadata.st_mode):
            return f"symlinked parent component is forbidden: {current.relative_to(state_root)}"
        if not stat.S_ISDIR(metadata.st_mode):
            return f"parent component is not a directory: {current.relative_to(state_root)}"

    path = state_root / relative_path
    metadata = _lstat(path)
    if metadata is None:
        return f"required file is missing: {relative_path}"
    if stat.S_ISLNK(metadata.st_mode):
        return f"symlinked file is forbidden: {relative_path}"
    if not stat.S_ISREG(metadata.st_mode):
        return f"required path is not a regular file: {relative_path}"
    return None


def _inspect_project(paths: ProjectPaths) -> Inspection:
    state_root = paths.state_root
    state_metadata = _lstat(state_root)
    if state_metadata is None:
        return Inspection(StateKind.UNINITIALIZED, "no .brichan state directory")
    if stat.S_ISLNK(state_metadata.st_mode):
        return Inspection(StateKind.MALFORMED, ".brichan must not be a symlink")
    if not stat.S_ISDIR(state_metadata.st_mode):
        return Inspection(StateKind.MALFORMED, ".brichan is not a directory")

    manifest_path = state_root / "manifest.json"
    manifest_problem = _regular_file_problem(state_root, "manifest.json")
    if manifest_problem:
        return Inspection(StateKind.MALFORMED, manifest_problem)
    try:
        manifest = _load_manifest(manifest_path)
    except ValueError as exc:
        return Inspection(StateKind.MALFORMED, str(exc))

    schema_version = manifest.get("schema_version")
    if type(schema_version) is not int:
        return Inspection(
            StateKind.MALFORMED,
            "manifest schema_version must be an integer",
            manifest,
        )
    if schema_version != SCHEMA_VERSION:
        return Inspection(
            StateKind.INCOMPATIBLE,
            f"schema_version {schema_version} is not supported "
            f"(expected {SCHEMA_VERSION})",
            manifest,
        )
    package_version = manifest.get("package_version")
    if package_version != __version__:
        return Inspection(
            StateKind.INCOMPATIBLE,
            f"package_version {package_version!r} is not supported "
            f"(expected {__version__!r})",
            manifest,
        )

    expected = intended_manifest()
    if set(manifest) != set(expected):
        return Inspection(
            StateKind.MALFORMED,
            "manifest keys do not match schema v1",
            manifest,
        )
    for key in ("layout", "runtime", "mutable_paths"):
        if manifest.get(key) != expected[key]:
            return Inspection(
                StateKind.MALFORMED,
                f"manifest {key} does not match schema v1",
                manifest,
            )
    resources = manifest.get("resources")
    if not isinstance(resources, dict) or resources != expected["resources"]:
        return Inspection(
            StateKind.MALFORMED,
            "manifest resource inventory does not match this package",
            manifest,
        )

    for relative_path, expected_hash in resources.items():
        resource_path = state_root / relative_path
        resource_problem = _regular_file_problem(state_root, relative_path)
        if resource_problem:
            return Inspection(
                StateKind.MALFORMED,
                resource_problem,
                manifest,
            )
        try:
            actual_hash = _sha256(resource_path.read_bytes())
        except OSError as exc:
            return Inspection(
                StateKind.MALFORMED,
                f"cannot read resource {relative_path}: {exc}",
                manifest,
            )
        if actual_hash != expected_hash:
            return Inspection(
                StateKind.MALFORMED,
                f"managed resource was modified: {relative_path}",
                manifest,
            )

    for relative_path in MUTABLE_PATHS:
        memory_problem = _regular_file_problem(state_root, relative_path)
        if memory_problem:
            return Inspection(
                StateKind.MALFORMED,
                memory_problem,
                manifest,
            )

    try:
        load_settings(state_root / "config" / "model-routing.json")
    except RoutingError as exc:
        return Inspection(
            StateKind.MALFORMED,
            f"routing config is invalid: {exc}",
            manifest,
        )
    return Inspection(
        StateKind.HEALTHY,
        f"schema {SCHEMA_VERSION}; {len(resources)} managed resources",
        manifest,
    )


def inspect_project(paths: ProjectPaths) -> Inspection:
    """Inspect target state without leaking filesystem access exceptions."""

    try:
        return _inspect_project(paths)
    except OSError as exc:
        problem_path = exc.filename or str(paths.state_root)
        detail = exc.strerror or str(exc) or "filesystem access failed"
        return Inspection(
            StateKind.MALFORMED,
            f"cannot inspect project state {problem_path}: "
            f"{exc.__class__.__name__}: {detail}",
        )


def _missing_agent_entries(
    paths: ProjectPaths,
) -> tuple[tuple[str, str], ...]:
    """Pending unmanaged files as (project-relative path, resource path)."""

    pending = [
        (name, f"{AGENT_ENTRY_RESOURCE_DIR}/{name}")
        for name in AGENT_ENTRY_PATHS
        if not os.path.lexists(paths.project_root / name)
    ]
    if not os.path.lexists(paths.project_root / AGENT_SKILLS_DIR):
        pending.extend(
            (f".agents/{resource}", resource)
            for resource in IMMUTABLE_PATHS
            if resource.startswith(_SKILL_RESOURCE_PREFIX)
        )
    return tuple(pending)


def _write_agent_entries(
    paths: ProjectPaths,
    pending: tuple[tuple[str, str], ...],
) -> str | None:
    for relative_path, resource in pending:
        destination = paths.project_root / relative_path
        directory_fd: int | None = None
        try:
            directory_fd = os.open(
                paths.project_root,
                os.O_RDONLY | os.O_DIRECTORY,
            )
            for component in Path(relative_path).parts[:-1]:
                try:
                    os.mkdir(component, dir_fd=directory_fd)
                except FileExistsError:
                    pass
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                )
                os.close(directory_fd)
                directory_fd = next_fd
            file_fd = os.open(
                Path(relative_path).name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o666,
                dir_fd=directory_fd,
            )
            with os.fdopen(file_fd, "wb") as stream:
                stream.write(_resource_bytes(resource))
        except FileExistsError:
            continue
        except OSError as exc:
            return (
                f"initialization failed: {destination}: "
                f"{exc.__class__.__name__}: {exc}"
            )
        finally:
            if directory_fd is not None:
                os.close(directory_fd)
    return None


def initialize_project(
    paths: ProjectPaths,
    *,
    apply: bool,
) -> tuple[int, list[str]]:
    inspection = inspect_project(paths)
    if inspection.kind is StateKind.HEALTHY:
        missing_entries = _missing_agent_entries(paths)
        if not missing_entries:
            return 0, [f"no changes: {paths.state_root} is already healthy"]
        entry_actions = [f"create {name}" for name, _ in missing_entries]
        if not apply:
            return 0, ["dry-run: zero writes", *entry_actions]
        problem = _write_agent_entries(paths, missing_entries)
        if problem:
            return 2, [problem]
        return 0, [
            f"no changes: {paths.state_root} is already healthy",
            *entry_actions,
        ]
    if inspection.kind is not StateKind.UNINITIALIZED:
        return inspection.exit_code, [
            f"{inspection.kind.value}: {paths.state_root}: {inspection.detail}"
        ]

    missing_entries = _missing_agent_entries(paths)
    actions = [f"create .brichan/{path}" for path in documented_footprint()]
    actions.extend(f"create {name}" for name, _ in missing_entries)
    if not apply:
        return 0, ["dry-run: zero writes", *actions]

    try:
        with tempfile.TemporaryDirectory(
            prefix=".brichan-stage-", dir=paths.project_root
        ) as temporary:
            staged_state = Path(temporary) / ".brichan"
            staged_state.mkdir()
            (staged_state / "manifest.json").write_bytes(manifest_bytes())
            for relative_path in (*IMMUTABLE_PATHS, *MUTABLE_PATHS):
                destination = staged_state / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(_resource_bytes(relative_path))
            os.replace(staged_state, paths.state_root)
    except OSError as exc:
        return 2, [
            f"initialization failed: {paths.state_root}: "
            f"{exc.__class__.__name__}: {exc}"
        ]
    problem = _write_agent_entries(paths, missing_entries)
    if problem:
        return 2, [problem]
    return 0, [f"initialized: {paths.state_root}", *actions]


def status_lines(paths: ProjectPaths) -> tuple[int, list[str]]:
    inspection = inspect_project(paths)
    return inspection.exit_code, [
        f"{inspection.kind.value}: {paths.project_root}: {inspection.detail}"
    ]


def doctor_lines(paths: ProjectPaths) -> tuple[int, list[str]]:
    inspection = inspect_project(paths)
    lines = [
        f"project: ok {paths.project_root}",
        f"state: {inspection.kind.value} {inspection.detail}",
    ]
    if inspection.kind is not StateKind.HEALTHY:
        return inspection.exit_code, lines

    codex = shutil.which("codex")
    herdr = shutil.which("herdr")
    lines.append(
        f"codex: {'ok ' + str(Path(codex).resolve()) if codex else 'missing'}"
    )
    lines.append(
        f"herdr: {'ok ' + str(Path(herdr).resolve()) if herdr else 'missing'}"
    )
    if codex is None or herdr is None:
        return 4, lines
    return 0, lines


def _worst_status(statuses: list[str]) -> str:
    return max(statuses, key=lambda status: _STATUS_RANK[status], default=STATUS_OK)


def _component_problem(path: Path, kind: str) -> tuple[str, str] | None:
    """Classify one path component with a no-follow check, or None if sound."""

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return STATUS_MISSING, f"required {kind} is missing"
    except OSError as exc:
        return STATUS_INVALID, (
            f"cannot inspect required {kind}: "
            f"{exc.__class__.__name__}: {exc.strerror or exc}"
        )
    if stat.S_ISLNK(metadata.st_mode):
        return STATUS_INVALID, f"required {kind} is a symbolic link"
    if kind == "directory" and not stat.S_ISDIR(metadata.st_mode):
        return STATUS_INVALID, "required directory is not a directory"
    if kind == "file" and not stat.S_ISREG(metadata.st_mode):
        return STATUS_INVALID, "required file is not a regular file"
    return None


def _path_check(root: Path, relative_path: str, kind: str) -> dict[str, Any]:
    """Check one required path without following symlinks or reading it.

    Every parent component is checked before the leaf, so a symlinked parent
    is reported rather than silently traversed into another tree.
    """

    entry = {"path": str(root / relative_path)}
    current = root
    for component in Path(relative_path).parts[:-1]:
        current = current / component
        problem = _component_problem(current, "directory")
        if problem is not None:
            status, detail = problem
            parent = current.relative_to(root).as_posix()
            return {**entry, "status": status, "detail": f"parent {parent}: {detail}"}

    problem = _component_problem(root / relative_path, kind)
    if problem is not None:
        status, detail = problem
        return {**entry, "status": status, "detail": detail}
    return {**entry, "status": STATUS_OK, "detail": f"required {kind} is present"}


def _blocked_section(
    root: Path,
    entries: tuple[tuple[str, str], ...],
    status: str,
    detail: str,
) -> dict[str, Any]:
    """Report a section without touching the filesystem beneath `root`.

    Used when the state root itself is unsafe: the paths are still named so the
    document keeps its exact shape, but nothing under them is stat'ed or read.
    """

    return {
        "status": status,
        "files": {
            relative_path: {
                "status": status,
                "path": str(root / relative_path),
                "detail": detail,
            }
            for relative_path, _ in entries
        },
        "detail": detail,
    }


def _paths_section(
    root: Path,
    entries: tuple[tuple[str, str], ...],
    label: str,
) -> dict[str, Any]:
    files = {
        relative_path: _path_check(root, relative_path, kind)
        for relative_path, kind in entries
    }
    unhealthy = sorted(
        relative_path
        for relative_path, check in files.items()
        if check["status"] != STATUS_OK
    )
    detail = (
        f"all {len(files)} required {label} paths are present"
        if not unhealthy
        else f"unhealthy {label} paths: {', '.join(unhealthy)}"
    )
    return {
        "status": _worst_status([check["status"] for check in files.values()]),
        "files": files,
        "detail": detail,
    }


def _routing_section(root: Path) -> dict[str, Any]:
    check = _path_check(root, ROUTING_RELATIVE_PATH, "file")
    section = {
        "status": check["status"],
        "path": check["path"],
        "schema_version": None,
        "detail": check["detail"],
    }
    if check["status"] != STATUS_OK:
        return section

    path = root / ROUTING_RELATIVE_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        section["status"] = STATUS_INVALID
        section["detail"] = f"cannot read routing config: {exc.strerror or exc}"
        return section
    except UnicodeDecodeError as exc:
        section["status"] = STATUS_INVALID
        section["detail"] = (
            f"routing config is not valid {exc.encoding}: {exc.reason} "
            f"at byte {exc.start}"
        )
        return section
    except json.JSONDecodeError as exc:
        section["status"] = STATUS_INVALID
        section["detail"] = (
            f"routing config contains malformed JSON at line {exc.lineno}, "
            f"column {exc.colno}"
        )
        return section
    if isinstance(payload, dict) and type(payload.get("schema_version")) is int:
        section["schema_version"] = payload["schema_version"]

    try:
        load_settings(path)
    except RoutingError as exc:
        section["status"] = STATUS_INVALID
        section["detail"] = f"routing config is invalid: {exc}"
        return section
    section["detail"] = "routing config is valid"
    return section


def _git_section(root: Path) -> dict[str, Any]:
    """Report Git state using read-only queries only.

    Every invocation carries `--no-optional-locks` so Git never writes an
    optional index refresh, and only `rev-parse`/`status` queries are used: no
    fetch, checkout, commit, or config command is ever run.
    """

    unknown = {"branch": None, "commit": None, "dirty": None, "untracked": None}
    git = shutil.which("git")
    if git is None:
        return {
            **unknown,
            "status": STATUS_UNAVAILABLE,
            "detail": "git executable is not on PATH",
        }

    def query(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [git, "--no-optional-locks", "-C", str(root), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

    try:
        head = query("rev-parse", "--abbrev-ref", "HEAD")
        revision = query("rev-parse", "HEAD")
        worktree = query("status", "--porcelain")
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            **unknown,
            "status": STATUS_UNAVAILABLE,
            "detail": f"cannot query git: {exc.__class__.__name__}: {exc}",
        }

    if worktree.returncode != 0:
        return {
            **unknown,
            "status": STATUS_INVALID,
            "detail": (
                "git status failed: "
                f"{worktree.stderr.strip() or f'exit {worktree.returncode}'}"
            ),
        }

    entries = [line for line in worktree.stdout.splitlines() if line]
    untracked = any(line.startswith("??") for line in entries)
    dirty = any(not line.startswith("??") for line in entries)
    branch = head.stdout.strip() if head.returncode == 0 else ""
    commit = revision.stdout.strip() if revision.returncode == 0 else ""
    # An unborn or detached HEAD reports no branch rather than a fake one.
    if branch == "HEAD":
        branch = ""
    return {
        "status": STATUS_OK,
        "branch": branch or None,
        "commit": commit or None,
        "dirty": dirty,
        "untracked": untracked,
        "detail": (
            f"{'dirty' if dirty else 'clean'} worktree; "
            f"{'untracked files present' if untracked else 'no untracked files'}"
        ),
    }


def _dependency_check(name: str, *, required: bool) -> dict[str, Any]:
    """Resolve one executable on PATH. Resolution only; nothing is executed."""

    resolved = shutil.which(name)
    if resolved is None:
        suffix = "" if required else " (optional)"
        return {
            "status": STATUS_MISSING,
            "path": None,
            "required": required,
            "detail": f"{name} is not on PATH{suffix}",
        }
    return {
        "status": STATUS_OK,
        "path": str(Path(resolved).resolve()),
        "required": required,
        "detail": f"{name} resolved on PATH",
    }


def _dependencies_section() -> dict[str, Any]:
    if sys.executable:
        python = {
            "status": STATUS_OK,
            "path": str(Path(sys.executable).resolve()),
            "required": True,
            "detail": "running interpreter",
        }
    else:
        python = {
            "status": STATUS_UNAVAILABLE,
            "path": None,
            "required": True,
            "detail": "running interpreter path is unknown",
        }
    dependencies = {
        "python": python,
        "git": _dependency_check("git", required=True),
        "codex": _dependency_check("codex", required=True),
        # Herdr is required for worker orchestration, but is only resolved
        # here and is never launched by doctor.
        "herdr": _dependency_check("herdr", required=True),
    }
    required = [
        check["status"] for check in dependencies.values() if check["required"]
    ]
    return {"status": _worst_status(required), **dependencies}


# ---------------------------------------------------------------------------
# Agent skill export comparison (doctor report schema v2)
# ---------------------------------------------------------------------------

#: The managed skill root, relative to `.brichan/`. Its exported twin is
#: `AGENT_SKILLS_DIR`, relative to the project root.
MANAGED_SKILL_DIR = "skills/herdr-orchestration"

#: Design section 3 caps. Both sides carry the same numbers.
SKILL_OUTPUT_PATH_BYTE_LIMIT = 4096
SKILL_RELATIVE_PATH_BYTE_LIMIT = 1024
SKILL_COMPONENT_BYTE_LIMIT = 255
SKILL_FILE_BYTE_LIMIT = 262144
SKILL_AGGREGATE_BYTE_LIMIT = 4194304
SKILL_ENTRY_COUNT_LIMIT = 64
SKILL_DIRECTORY_COUNT_LIMIT = 64
SKILL_MAX_DEPTH = 6
SKILL_FILE_ROW_LIMIT = 128

#: Design section 9's closed 27-row section registry, in the single precedence
#: order Design section 16's cross-product restates. The first applicable row
#: wins; `detail` is the exact sentence Design section 14 freezes.
AGENT_SKILL_EXPORT_DETAILS = (
    (
        "SOURCE_CHECKOUT_NOT_APPLICABLE",
        "skill export comparison is not applicable in source-checkout mode",
    ),
    ("OUTPUT_PATH_BYTE_LIMIT", "an absolute skill path exceeds 4096 UTF-8 bytes"),
    (
        "OUTPUT_PATH_NOT_CANONICAL",
        "an absolute skill path is not strict UTF-8 NFC",
    ),
    ("MANAGED_STATE_UNINITIALIZED", "managed state is not initialized"),
    ("MANAGED_STATE_MALFORMED", "managed state is malformed or unsafe"),
    (
        "MANAGED_STATE_INCOMPATIBLE",
        "managed state is incompatible with this package",
    ),
    ("UNSUPPORTED_SAFE_OPEN", "required safe-open primitives are unavailable"),
    ("RESOURCE_LIMIT", "a process filesystem resource was exhausted"),
    ("SAFE_OPEN_HELPER_BUSY", "another bounded safe-open helper is active"),
    ("SAFE_OPEN_HELPER_TIMEOUT", "the bounded safe-open helper timed out"),
    ("SAFE_OPEN_HELPER_FAILED", "the bounded safe-open helper failed"),
    ("SAFE_OPEN_HELPER_LEAK", "the bounded safe-open helper could not be reaped"),
    (
        "SKILL_ENTRY_NAME_BYTE_LIMIT",
        "a skill entry name exceeds 255 or a path exceeds 1024 bytes",
    ),
    ("SKILL_ENTRY_NAME_INVALID", "a skill entry name is not strict UTF-8 NFC"),
    ("SKILL_ENTRY_LIMIT", "skill file count exceeds 64"),
    ("SKILL_DIRECTORY_LIMIT", "skill directory count exceeds 64"),
    ("SKILL_DEPTH_LIMIT", "skill directory depth exceeds 6"),
    ("MANAGED_SKILL_AGGREGATE_BYTE_LIMIT", "managed skill bytes exceed 4194304"),
    ("EXPORTED_SKILL_AGGREGATE_BYTE_LIMIT", "exported skill bytes exceed 4194304"),
    ("MANAGED_SKILL_BYTE_LIMIT", "a managed skill file exceeds 262144 bytes"),
    ("EXPORTED_SKILL_BYTE_LIMIT", "an exported skill file exceeds 262144 bytes"),
    ("SKILL_UNSAFE", "a skill entry is not a safe regular file or directory"),
    ("SKILL_UNREADABLE", "a skill entry could not be read"),
    ("EXPORT_EXTRA", "the export contains paths absent from managed state"),
    ("EXPORT_STALE", "managed and exported skill bytes differ"),
    ("EXPORT_MISSING", "the export or an expected exported file is missing"),
    ("EXPORT_CURRENT", "managed and exported skill files are current"),
)

RELATION_NOT_APPLICABLE = "not_applicable"
RELATION_MANAGED_STATE_UNAVAILABLE = "managed_state_unavailable"
RELATION_CURRENT = "current"
RELATION_MISSING = "missing"
RELATION_STALE = "stale"
RELATION_EXTRA = "extra"
RELATION_COMPARISON_UNAVAILABLE = "comparison_unavailable"
RELATION_UNAVAILABLE = "unavailable"

#: Design section 16's authoritative cross-product: for each detail code, the
#: section `status`, `relation`, whether both absolute paths are nonnull, and
#: whether `files` carries the canonical union rather than being suppressed.
_UNAVAILABLE_EMPTY = (STATUS_UNAVAILABLE, RELATION_COMPARISON_UNAVAILABLE, True, False)
_UNAVAILABLE_COMPLETE = (
    STATUS_UNAVAILABLE,
    RELATION_COMPARISON_UNAVAILABLE,
    True,
    True,
)
AGENT_SKILL_EXPORT_ROWS = {
    "SOURCE_CHECKOUT_NOT_APPLICABLE": (
        STATUS_OK,
        RELATION_NOT_APPLICABLE,
        False,
        False,
    ),
    "OUTPUT_PATH_BYTE_LIMIT": (
        STATUS_UNAVAILABLE,
        RELATION_COMPARISON_UNAVAILABLE,
        False,
        False,
    ),
    "OUTPUT_PATH_NOT_CANONICAL": (
        STATUS_UNAVAILABLE,
        RELATION_COMPARISON_UNAVAILABLE,
        False,
        False,
    ),
    "MANAGED_STATE_UNINITIALIZED": (
        STATUS_MISSING,
        RELATION_MANAGED_STATE_UNAVAILABLE,
        True,
        False,
    ),
    "MANAGED_STATE_MALFORMED": (
        STATUS_INVALID,
        RELATION_MANAGED_STATE_UNAVAILABLE,
        True,
        False,
    ),
    "MANAGED_STATE_INCOMPATIBLE": (
        STATUS_INVALID,
        RELATION_MANAGED_STATE_UNAVAILABLE,
        True,
        False,
    ),
    "UNSUPPORTED_SAFE_OPEN": _UNAVAILABLE_EMPTY,
    "RESOURCE_LIMIT": _UNAVAILABLE_EMPTY,
    "SAFE_OPEN_HELPER_BUSY": _UNAVAILABLE_EMPTY,
    "SAFE_OPEN_HELPER_TIMEOUT": _UNAVAILABLE_EMPTY,
    "SAFE_OPEN_HELPER_FAILED": _UNAVAILABLE_EMPTY,
    "SAFE_OPEN_HELPER_LEAK": _UNAVAILABLE_EMPTY,
    "SKILL_ENTRY_NAME_BYTE_LIMIT": _UNAVAILABLE_EMPTY,
    "SKILL_ENTRY_NAME_INVALID": _UNAVAILABLE_EMPTY,
    "SKILL_ENTRY_LIMIT": _UNAVAILABLE_EMPTY,
    "SKILL_DIRECTORY_LIMIT": _UNAVAILABLE_EMPTY,
    "SKILL_DEPTH_LIMIT": _UNAVAILABLE_EMPTY,
    "MANAGED_SKILL_AGGREGATE_BYTE_LIMIT": _UNAVAILABLE_EMPTY,
    "EXPORTED_SKILL_AGGREGATE_BYTE_LIMIT": _UNAVAILABLE_EMPTY,
    "MANAGED_SKILL_BYTE_LIMIT": _UNAVAILABLE_COMPLETE,
    "EXPORTED_SKILL_BYTE_LIMIT": _UNAVAILABLE_COMPLETE,
    "SKILL_UNSAFE": _UNAVAILABLE_COMPLETE,
    "SKILL_UNREADABLE": _UNAVAILABLE_COMPLETE,
    "EXPORT_EXTRA": (STATUS_INVALID, RELATION_EXTRA, True, True),
    "EXPORT_STALE": (STATUS_INVALID, RELATION_STALE, True, True),
    "EXPORT_MISSING": (STATUS_MISSING, RELATION_MISSING, True, True),
    "EXPORT_CURRENT": (STATUS_OK, RELATION_CURRENT, True, True),
}

SIDE_REGULAR = "regular"
SIDE_ABSENT = "absent"
SIDE_UNSAFE = "unsafe"
SIDE_UNREADABLE = "unreadable"
SIDE_OVER_LIMIT = "over_limit"
SIDE_NOT_CHECKED = "not_checked"

#: Design section 9's row detail registry, in its first-match order. Each entry
#: is `(detail_code, relation, exact detail)`.
AGENT_SKILL_EXPORT_FILE_DETAILS = (
    ("FILE_MANAGED_UNSAFE", RELATION_UNAVAILABLE, "managed entry is unsafe"),
    ("FILE_EXPORTED_UNSAFE", RELATION_UNAVAILABLE, "exported entry is unsafe"),
    (
        "FILE_MANAGED_UNREADABLE",
        RELATION_UNAVAILABLE,
        "managed entry is unreadable",
    ),
    (
        "FILE_EXPORTED_UNREADABLE",
        RELATION_UNAVAILABLE,
        "exported entry is unreadable",
    ),
    (
        "FILE_MANAGED_OVER_LIMIT",
        RELATION_UNAVAILABLE,
        "managed file exceeds 262144 bytes",
    ),
    (
        "FILE_EXPORTED_OVER_LIMIT",
        RELATION_UNAVAILABLE,
        "exported file exceeds 262144 bytes",
    ),
    (
        "FILE_CURRENT",
        RELATION_CURRENT,
        "managed and exported files are byte-identical",
    ),
    ("FILE_MISSING", RELATION_MISSING, "exported file is missing"),
    (
        "FILE_STALE",
        RELATION_STALE,
        "managed and exported file bytes differ",
    ),
    (
        "FILE_EXTRA",
        RELATION_EXTRA,
        "exported file has no managed counterpart",
    ),
)

#: Design section 3's errno table over packet-1 observation codes: what one
#: observed skill entry becomes on its own side.
_SKILL_SIDE_OUTCOMES = {
    "OK": SIDE_REGULAR,
    "NOT_FOUND": SIDE_ABSENT,
    "BYTE_LIMIT": SIDE_OVER_LIMIT,
    "SYMLINK_REJECTED": SIDE_UNSAFE,
    "PATH_COMPONENT_NOT_DIRECTORY": SIDE_UNSAFE,
    "DIRECTORY_REJECTED": SIDE_UNSAFE,
    "FIFO_REJECTED": SIDE_UNSAFE,
    "SOCKET_REJECTED": SIDE_UNSAFE,
    "DEVICE_REJECTED": SIDE_UNSAFE,
    "NON_REGULAR_REJECTED": SIDE_UNSAFE,
    "SPECIAL_FILE_UNAVAILABLE": SIDE_UNSAFE,
    "UNREADABLE_FILE": SIDE_UNREADABLE,
    "FILESYSTEM_IO_ERROR": SIDE_UNREADABLE,
    "FILESYSTEM_ERROR": SIDE_UNREADABLE,
    "FILE_CHANGED": SIDE_UNREADABLE,
    "OS_METADATA_RANGE": SIDE_UNREADABLE,
}

#: Observation codes that make the whole section unavailable rather than one
#: side of one row. Every one keeps its own name, so a transient descriptor or
#: memory exhaustion is never reported as a permanent platform gap.
_SKILL_SECTION_OUTCOMES = {
    "UNSUPPORTED_SAFE_OPEN": "UNSUPPORTED_SAFE_OPEN",
    "RESOURCE_LIMIT": "RESOURCE_LIMIT",
    "SAFE_OPEN_HELPER_BUSY": "SAFE_OPEN_HELPER_BUSY",
    "SAFE_OPEN_HELPER_TIMEOUT": "SAFE_OPEN_HELPER_TIMEOUT",
    "SAFE_OPEN_HELPER_FAILED": "SAFE_OPEN_HELPER_FAILED",
    "SAFE_OPEN_HELPER_LEAK": "SAFE_OPEN_HELPER_LEAK",
}

#: Installed state that is not healthy fixes the section before any comparison.
_MANAGED_STATE_CODES = {
    StateKind.UNINITIALIZED: "MANAGED_STATE_UNINITIALIZED",
    StateKind.MALFORMED: "MANAGED_STATE_MALFORMED",
    StateKind.INCOMPATIBLE: "MANAGED_STATE_INCOMPATIBLE",
}


@dataclass
class _SkillEntry:
    """One enumerated row-bearing entry on one side."""

    status: str
    size: int = 0


@dataclass
class _SkillScan:
    """One bounded side enumeration."""

    #: `present`, `absent`, `unsafe`, or `unreadable`; a non-present root gives
    #: every peer row that side's status without descending anything.
    root_state: str = "present"
    entries: dict[str, _SkillEntry] = field(default_factory=dict)
    directories: set[str] = field(default_factory=set)
    aggregate: int = 0
    failures: set[str] = field(default_factory=set)
    #: Some enumeration abort has tripped — a cap, the aggregate bound, or a
    #: section row raised while classifying an entry or opening a directory.
    #: `_abort_scan` is the only thing that sets it, and it is the only thing
    #: that stops the walk: descend nothing further, but keep observing the
    #: levels already listed so every co-occurring condition — the other caps
    #: and every condition classification or a refused open raises — is
    #: available to Design section 9's registry ranking.
    bounded: bool = False


def _safe_open() -> Any:
    """Import the bounded reader lazily.

    `brichan.cli.runtime` must stay free of the techstacks package until a
    techstacks command or an installed export comparison actually needs it.
    """

    from brichan.techstacks import filesystem

    return filesystem


def _skill_component(raw: bytes) -> str | None:
    """Decode one enumerated name, or None when no row can represent it.

    Names arrive as bytes, decode as strict UTF-8, and must already be NFC.
    The remaining checks are the closed `relative_path` grammar: a component is
    1-255 bytes and carries no separator or control character.
    """

    if not raw or len(raw) > SKILL_COMPONENT_BYTE_LIMIT:
        return None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if unicodedata.normalize("NFC", text) != text:
        return None
    if text in (".", "..") or "/" in text or "\\" in text:
        return None
    if any(ord(character) < 32 or ord(character) == 127 for character in text):
        return None
    return text


def _open_skill_root(
    project_root: Path,
    relative_root: str,
) -> tuple[int | None, str, str | None]:
    """Open one project-relative directory with no-follow descent only."""

    try:
        directory_fd = os.open(project_root, os.O_RDONLY | os.O_DIRECTORY)
    except OSError:
        return None, SIDE_UNREADABLE, None
    for component in relative_root.split("/"):
        child_fd, observed = _safe_open().open_directory(directory_fd, component)
        os.close(directory_fd)
        if child_fd is None:
            section = _SKILL_SECTION_OUTCOMES.get(observed.code)
            if section is not None:
                return None, SIDE_UNREADABLE, section
            return (
                None,
                _SKILL_SIDE_OUTCOMES.get(observed.code, SIDE_UNREADABLE),
                None,
            )
        directory_fd = child_fd
    return directory_fd, "present", None


def _abort_scan(scan: _SkillScan, code: str) -> None:
    """Record one enumeration-abort row and refuse every further descent.

    Every abort inside `_scan_skill_directory`'s enumeration loop is routed
    through this one helper, which is why that loop holds no `return`: an
    abort records its row and sets `scan.bounded`, and `scan.bounded` alone
    refuses descent. Design section 16 requires the level at which any abort
    condition trips to finish being listed, so a row observed later on that
    same level is still ranked by section 9's registry order rather than by
    whichever entry name sorted first.
    """

    scan.failures.add(code)
    scan.bounded = True


def _scan_skill_directory(
    directory_fd: int,
    prefix: str,
    depth: int,
    scan: _SkillScan,
    aggregate_code: str,
) -> None:
    """Enumerate one bounded directory level, depth-first in path-byte order.

    Design section 16 ranks an enumeration-abort condition only where this
    bounded enumeration actually observed it, and section 9 then ranks the
    *applicable* conditions by registry order, not the observed failures by
    entry name. So no abort stops the side mid-level: every abort in the loop
    below goes through `_abort_scan`, no `return` appears inside that loop,
    and the function returns exactly once, after it. Each abort only stops
    descent, and enumeration finishes listing the levels already listed, whose
    remaining names are still measured, decoded, and classified. That is what
    brings every condition observable at those levels — rows 13 and 14 from
    the names alone, rows 7 and 8 both from classifying an entry and from a
    refused directory open, the count, directory, and depth caps, and the
    aggregate row — under one registry order regardless of entry name. A
    condition whose evidence lies only inside a directory an abort prevented
    descending is never observed and is not applicable. Rows 13 and 14 outrank
    every row classifying an entry can raise, so a level is measured and
    decoded in full before any of its entries is classified. A section code
    raised while classifying an entry, or while opening a directory the level
    listed, is recorded the same way: the level finishes, so two section rows
    observed on it are ranked by registry order rather than by entry name, and
    only then does the side stop.

    Only the entry counter stops one past its cap: once its row is recorded
    and `files` is suppressed, no further entry can change the answer. The
    directory set must not stop there. Every directory it holds was observed
    at an already-listed level, which section 16 makes applicable, and the
    unexpected-directory accounting reads the whole set, so capping it would
    silently move a reported row.

    Finishing is bounded in kind rather than in count: it costs one metadata
    call per remaining name on the aborting level **and on every already-listed
    ancestor level**, at most `SKILL_MAX_DEPTH` + 1 levels in all (depths 0
    through `SKILL_MAX_DEPTH`), because section
    16 makes every condition observable at any level already listed applicable
    and each of those levels must therefore finish too. No file content is
    read, no descent occurs once an abort has set `bounded`, and the number of
    directory opens never exceeds the healthy baseline.
    """

    try:
        names = os.listdir(directory_fd)
    except OSError:
        if prefix:
            scan.entries[prefix.rstrip("/")] = _SkillEntry(SIDE_UNREADABLE)
        else:
            scan.root_state = SIDE_UNREADABLE
        # A level that could not be listed contributes no name to either pass
        # below, which is how the unreadable case leaves without a `return`.
        names = []
    listed: list[tuple[str, str]] = []
    for name in sorted(names, key=os.fsencode):
        raw = os.fsencode(name)
        # Design section 9 measures a name before it decodes it, so a name
        # that violates both a bound and the encoding is reported by its
        # length and the encoding row keeps only in-bounds names. Both rows
        # rank above every row classifying an entry can raise, so the level's
        # names are all recorded here and the name that raised one is simply
        # left out of the classified pass below.
        if len(raw) > SKILL_COMPONENT_BYTE_LIMIT:
            scan.failures.add("SKILL_ENTRY_NAME_BYTE_LIMIT")
            continue
        component = _skill_component(raw)
        if component is None:
            scan.failures.add("SKILL_ENTRY_NAME_INVALID")
            continue
        relative = f"{prefix}{component}"
        if len(relative.encode("utf-8")) > SKILL_RELATIVE_PATH_BYTE_LIMIT:
            scan.failures.add("SKILL_ENTRY_NAME_BYTE_LIMIT")
            continue
        listed.append((name, relative))
    for name, relative in listed:
        observed = _safe_open().classify_entry(directory_fd, name)
        section = _SKILL_SECTION_OUTCOMES.get(observed.code)
        if section is not None:
            # Section rows outrank every other row enumeration can raise, but
            # they do not outrank each other by entry name: record the row,
            # refuse every further descent, and finish the level so a peer
            # section row on it is ranked by section 9's registry order.
            _abort_scan(scan, section)
            continue
        if observed.code == "NOT_FOUND":
            continue
        if observed.code == "DIRECTORY_REJECTED":
            scan.directories.add(relative)
            if len(scan.directories) > SKILL_DIRECTORY_COUNT_LIMIT:
                _abort_scan(scan, "SKILL_DIRECTORY_LIMIT")
            if depth + 1 > SKILL_MAX_DEPTH:
                _abort_scan(scan, "SKILL_DEPTH_LIMIT")
            elif not scan.bounded:
                child_fd, opened = _safe_open().open_directory(directory_fd, name)
                if child_fd is None:
                    section = _SKILL_SECTION_OUTCOMES.get(opened.code)
                    if section is not None:
                        # The same shape as the classification branch above.
                        # `EMFILE` surfaces here and only here, and losing it
                        # to a lower-ranked row on a later name of this level
                        # is exactly what section 16 forbids.
                        _abort_scan(scan, section)
                    else:
                        scan.entries[relative] = _SkillEntry(
                            _SKILL_SIDE_OUTCOMES.get(opened.code, SIDE_UNREADABLE)
                        )
                else:
                    try:
                        _scan_skill_directory(
                            child_fd, f"{relative}/", depth + 1, scan, aggregate_code
                        )
                    finally:
                        os.close(child_fd)
                    continue
        else:
            status = _SKILL_SIDE_OUTCOMES.get(observed.code, SIDE_UNREADABLE)
            size = observed.identity.size if observed.identity is not None else 0
            # The entry counter stops one past its cap: the row that names it
            # is already recorded, `files` is already suppressed, and nothing
            # a further entry could add to either can change the answer.
            if len(scan.entries) <= SKILL_ENTRY_COUNT_LIMIT:
                scan.entries[relative] = _SkillEntry(status, size)
                if status == SIDE_REGULAR:
                    scan.aggregate += size
                    if (
                        scan.aggregate > SKILL_AGGREGATE_BYTE_LIMIT
                        and not scan.bounded
                    ):
                        _abort_scan(scan, aggregate_code)
        if len(scan.entries) > SKILL_ENTRY_COUNT_LIMIT:
            _abort_scan(scan, "SKILL_ENTRY_LIMIT")


def _scan_skill_side(
    project_root: Path,
    relative_root: str,
    aggregate_code: str,
) -> _SkillScan:
    scan = _SkillScan()
    directory_fd, state, failure = _open_skill_root(project_root, relative_root)
    scan.root_state = state
    if failure is not None:
        scan.failures.add(failure)
    if directory_fd is None:
        return scan
    try:
        _scan_skill_directory(directory_fd, "", 0, scan, aggregate_code)
    finally:
        os.close(directory_fd)
    return scan


def _read_skill_file(
    project_root: Path,
    relative_root: str,
    relative_path: str,
) -> Any:
    """Read one skill file through the packet-1 bounded reader."""

    components = f"{relative_root}/{relative_path}".split("/")
    directory_fd, state, failure = _open_skill_root(
        project_root, "/".join(components[:-1])
    )
    if directory_fd is None:
        if failure is not None:
            return _safe_open().Observation(code=failure)
        return _safe_open().Observation(
            code="UNREADABLE_FILE" if state != SIDE_ABSENT else "NOT_FOUND"
        )
    try:
        return _safe_open().read_bounded_regular(
            directory_fd, components[-1], SKILL_FILE_BYTE_LIMIT
        )
    finally:
        os.close(directory_fd)


def _side_status(scan: _SkillScan, relative_path: str) -> str:
    """The stat-level status of one path on one side."""

    if scan.root_state != "present":
        return scan.root_state
    entry = scan.entries.get(relative_path)
    if entry is not None:
        return entry.status
    if relative_path in scan.directories:
        # An unexpected directory where the peer side has a row entry.
        return SIDE_UNSAFE
    return SIDE_ABSENT


def _skill_row(
    relative_path: str,
    managed_status: str,
    managed_hash: str | None,
    exported_status: str,
    exported_hash: str | None,
) -> dict[str, Any]:
    if managed_status == SIDE_UNSAFE:
        code, relation, detail = AGENT_SKILL_EXPORT_FILE_DETAILS[0]
    elif exported_status == SIDE_UNSAFE:
        code, relation, detail = AGENT_SKILL_EXPORT_FILE_DETAILS[1]
    elif managed_status == SIDE_UNREADABLE:
        code, relation, detail = AGENT_SKILL_EXPORT_FILE_DETAILS[2]
    elif exported_status == SIDE_UNREADABLE:
        code, relation, detail = AGENT_SKILL_EXPORT_FILE_DETAILS[3]
    elif managed_status == SIDE_OVER_LIMIT:
        code, relation, detail = AGENT_SKILL_EXPORT_FILE_DETAILS[4]
    elif exported_status == SIDE_OVER_LIMIT:
        code, relation, detail = AGENT_SKILL_EXPORT_FILE_DETAILS[5]
    elif (
        managed_status == SIDE_REGULAR
        and exported_status == SIDE_REGULAR
        and managed_hash == exported_hash
    ):
        code, relation, detail = AGENT_SKILL_EXPORT_FILE_DETAILS[6]
    elif managed_status == SIDE_REGULAR and exported_status == SIDE_ABSENT:
        code, relation, detail = AGENT_SKILL_EXPORT_FILE_DETAILS[7]
    elif managed_status == SIDE_REGULAR and exported_status == SIDE_REGULAR:
        code, relation, detail = AGENT_SKILL_EXPORT_FILE_DETAILS[8]
    else:
        code, relation, detail = AGENT_SKILL_EXPORT_FILE_DETAILS[9]
    return {
        "relative_path": relative_path,
        "managed_status": managed_status,
        "managed_sha256": managed_hash,
        "exported_status": exported_status,
        "exported_sha256": exported_hash,
        "relation": relation,
        "detail_code": code,
        "detail": detail,
    }


def _compare_skill_row(
    project_root: Path,
    managed_relative: str,
    relative_path: str,
    managed: _SkillScan,
    exported: _SkillScan,
    failures: set[str],
) -> dict[str, Any]:
    """Classify one union path, reading no more than the relation needs.

    A side is read only while every earlier side is sound, so a side left
    unvisited after an earlier side failure reports `not_checked` and a null
    hash rather than a status it never observed.
    """

    managed_status = _side_status(managed, relative_path)
    exported_status = _side_status(exported, relative_path)

    def unvisited(status: str) -> str:
        return SIDE_NOT_CHECKED if status == SIDE_REGULAR else status

    if SIDE_UNSAFE in (managed_status, exported_status) or SIDE_UNREADABLE in (
        managed_status,
        exported_status,
    ):
        return _skill_row(
            relative_path,
            unvisited(managed_status),
            None,
            unvisited(exported_status),
            None,
        )

    managed_hash: str | None = None
    if managed_status == SIDE_REGULAR:
        managed_status, managed_hash = _observed_side(
            _read_skill_file(project_root, managed_relative, relative_path),
            failures,
        )
    if managed_status in (SIDE_UNSAFE, SIDE_UNREADABLE, SIDE_OVER_LIMIT):
        # An absent managed side is not a failure, so the exported side is
        # still visited; a failed one stops every remaining read.
        return _skill_row(
            relative_path,
            managed_status,
            managed_hash,
            unvisited(exported_status),
            None,
        )

    exported_hash: str | None = None
    if exported_status == SIDE_REGULAR:
        exported_status, exported_hash = _observed_side(
            _read_skill_file(project_root, AGENT_SKILLS_DIR, relative_path),
            failures,
        )
    return _skill_row(
        relative_path,
        managed_status,
        managed_hash,
        exported_status,
        exported_hash,
    )


def _observed_side(observed: Any, failures: set[str]) -> tuple[str, str | None]:
    """Turn one bounded read into a side status, hash, and section failure."""

    section = _SKILL_SECTION_OUTCOMES.get(observed.code)
    if section is not None:
        failures.add(section)
        return SIDE_UNREADABLE, None
    status = _SKILL_SIDE_OUTCOMES.get(observed.code, SIDE_UNREADABLE)
    if status != SIDE_REGULAR:
        return status, None
    return SIDE_REGULAR, _sha256(observed.data or b"")


def _export_section(
    detail_code: str,
    *,
    mode: str,
    managed_path: str | None,
    path: str | None,
    files: list[dict[str, Any]],
) -> dict[str, Any]:
    status, relation, paths_nonnull, files_complete = AGENT_SKILL_EXPORT_ROWS[
        detail_code
    ]
    detail = dict(AGENT_SKILL_EXPORT_DETAILS)[detail_code]
    return {
        "status": status,
        "mode": mode,
        "relation": relation,
        "path": path if paths_nonnull else None,
        "managed_path": managed_path if paths_nonnull else None,
        "files": files if files_complete else [],
        "detail_code": detail_code,
        "detail": detail,
    }


def _first_export_code(candidates: set[str]) -> str | None:
    for code, _ in AGENT_SKILL_EXPORT_DETAILS:
        if code in candidates:
            return code
    return None


def agent_skill_export_section(
    paths: ProjectPaths,
    *,
    source_mode: bool,
    inspection: Inspection | None,
) -> dict[str, Any]:
    """Compare the managed skill tree with its `.agents/` export, read-only.

    Source-checkout mode never inspects `.brichan` or `.agents` for this
    section, and installed state that is not healthy is answered before any
    comparison work descends anything.
    """

    if source_mode:
        return _export_section(
            "SOURCE_CHECKOUT_NOT_APPLICABLE",
            mode="source_checkout",
            managed_path=None,
            path=None,
            files=[],
        )

    try:
        state_relative = paths.state_root.relative_to(paths.project_root).as_posix()
    except ValueError:  # pragma: no cover - project_paths always nests the two
        state_relative = ".brichan"
    managed_relative = f"{state_relative}/{MANAGED_SKILL_DIR}"
    managed_path = str(paths.state_root / MANAGED_SKILL_DIR)
    export_path = str(paths.project_root / AGENT_SKILLS_DIR)
    # Both absolute strings are checked against Design section 9's
    # absolute-output-path grammar before any state is inspected, and every
    # condition either string raises is collected before one is chosen, so the
    # answer is the registry-ordered row rather than whichever string was
    # tested first.
    output_failures: set[str] = set()
    for candidate in (managed_path, export_path):
        try:
            encoded = len(candidate.encode("utf-8"))
        except UnicodeEncodeError:
            # Surrogate-escaped bytes are not strict UTF-8 at all, so no
            # length is representable and the grammar row is the only answer.
            output_failures.add("OUTPUT_PATH_NOT_CANONICAL")
            continue
        if encoded < 1 or encoded > SKILL_OUTPUT_PATH_BYTE_LIMIT:
            output_failures.add("OUTPUT_PATH_BYTE_LIMIT")
        if unicodedata.normalize("NFC", candidate) != candidate:
            output_failures.add("OUTPUT_PATH_NOT_CANONICAL")
    output_code = _first_export_code(output_failures)
    if output_code is not None:
        return _export_section(
            output_code,
            mode="installed",
            managed_path=None,
            path=None,
            files=[],
        )

    assert inspection is not None
    state_code = _MANAGED_STATE_CODES.get(inspection.kind)
    if state_code is not None:
        return _export_section(
            state_code,
            mode="installed",
            managed_path=managed_path,
            path=export_path,
            files=[],
        )

    if not _safe_open().is_supported_platform():
        return _export_section(
            "UNSUPPORTED_SAFE_OPEN",
            mode="installed",
            managed_path=managed_path,
            path=export_path,
            files=[],
        )

    managed = _scan_skill_side(
        paths.project_root,
        managed_relative,
        "MANAGED_SKILL_AGGREGATE_BYTE_LIMIT",
    )
    exported = _scan_skill_side(
        paths.project_root,
        AGENT_SKILLS_DIR,
        "EXPORTED_SKILL_AGGREGATE_BYTE_LIMIT",
    )
    failures = set(managed.failures) | set(exported.failures)

    union = sorted(
        set(managed.entries) | set(exported.entries),
        key=lambda value: value.encode("utf-8"),
    )
    for scan in (managed, exported):
        unexpected = sum(
            1
            for relative in union
            if relative not in scan.entries and relative in scan.directories
        )
        if len(scan.entries) + unexpected > SKILL_ENTRY_COUNT_LIMIT:
            failures.add("SKILL_ENTRY_LIMIT")
    if len(union) > SKILL_FILE_ROW_LIMIT:
        failures.add("SKILL_ENTRY_LIMIT")

    files: list[dict[str, Any]] = []
    if not failures:
        for relative in union:
            files.append(
                _compare_skill_row(
                    paths.project_root,
                    managed_relative,
                    relative,
                    managed,
                    exported,
                    failures,
                )
            )

    for row in files:
        if row["managed_status"] == SIDE_OVER_LIMIT:
            failures.add("MANAGED_SKILL_BYTE_LIMIT")
        if row["exported_status"] == SIDE_OVER_LIMIT:
            failures.add("EXPORTED_SKILL_BYTE_LIMIT")
        if SIDE_UNSAFE in (row["managed_status"], row["exported_status"]):
            failures.add("SKILL_UNSAFE")
        if SIDE_UNREADABLE in (row["managed_status"], row["exported_status"]):
            failures.add("SKILL_UNREADABLE")
        if row["relation"] == RELATION_EXTRA:
            failures.add("EXPORT_EXTRA")
        if row["relation"] == RELATION_STALE:
            failures.add("EXPORT_STALE")
        if row["relation"] == RELATION_MISSING:
            failures.add("EXPORT_MISSING")
    if exported.root_state == SIDE_ABSENT:
        failures.add("EXPORT_MISSING")

    detail_code = _first_export_code(failures) or "EXPORT_CURRENT"
    return _export_section(
        detail_code,
        mode="installed",
        managed_path=managed_path,
        path=export_path,
        files=files,
    )


_INSTALLED_REPOSITORY_STATUS = {
    StateKind.HEALTHY: STATUS_OK,
    StateKind.UNINITIALIZED: STATUS_MISSING,
    StateKind.MALFORMED: STATUS_INVALID,
    StateKind.INCOMPATIBLE: STATUS_INVALID,
}


def doctor_report(
    paths: ProjectPaths,
    *,
    checkout_root: Path | None = None,
) -> tuple[int, dict[str, Any]]:
    """Collect the read-only `doctor --json` report and its exit code.

    Source-checkout mode applies only when the resolved target *is* the running
    Brichan checkout; every other target is diagnosed as an installed project,
    whose state verdict and exit class stay owned by `inspect_project`.
    """

    source_mode = checkout_root is not None and checkout_root == paths.project_root
    inspection: Inspection | None = None
    blocked: tuple[str, str] | None = None
    if source_mode:
        repository = {
            "status": STATUS_OK,
            "root": str(paths.project_root),
            "kind": "source_checkout",
            "detail": "brichan source checkout",
        }
        contract_root = paths.project_root
        policy_paths = CHECKOUT_POLICY_PATHS
        memory_paths = CHECKOUT_MEMORY_PATHS
    else:
        inspection = inspect_project(paths)
        repository = {
            "status": _INSTALLED_REPOSITORY_STATUS[inspection.kind],
            "root": str(paths.project_root),
            "kind": "installed_project",
            "detail": f"{inspection.kind.value}: {inspection.detail}",
        }
        contract_root = paths.state_root
        policy_paths = INSTALLED_POLICY_PATHS
        memory_paths = INSTALLED_MEMORY_PATHS
        # A `.brichan` that is absent, symlinked, or not a directory must not
        # be traversed: descending through it would stat and read files in
        # whatever tree the link points at, outside the target repository.
        problem = _component_problem(paths.state_root, "directory")
        if problem is not None:
            status, reason = problem
            blocked = (status, f".brichan state directory: {reason}")

    if blocked is None:
        policies = _paths_section(contract_root, policy_paths, "policy")
        project_memory = _paths_section(contract_root, memory_paths, "project-memory")
        model_routing = _routing_section(contract_root)
    else:
        status, reason = blocked
        policies = _blocked_section(contract_root, policy_paths, status, reason)
        project_memory = _blocked_section(contract_root, memory_paths, status, reason)
        model_routing = {
            "status": status,
            "path": str(contract_root / ROUTING_RELATIVE_PATH),
            "schema_version": None,
            "detail": reason,
        }
    git = _git_section(paths.project_root)
    dependencies = _dependencies_section()
    agent_skill_export = agent_skill_export_section(
        paths,
        source_mode=source_mode,
        inspection=inspection,
    )

    codex_status = dependencies["codex"]["status"]
    other_required = [
        repository["status"],
        git["status"],
        policies["status"],
        model_routing["status"],
        project_memory["status"],
        dependencies["python"]["status"],
        dependencies["git"]["status"],
        dependencies["herdr"]["status"],
    ]
    # The export section contributes to `ok` but never to an exit class: the
    # state and codex owners below are unchanged.
    ok = (
        codex_status == STATUS_OK
        and agent_skill_export["status"] == STATUS_OK
        and all(status == STATUS_OK for status in other_required)
    )

    if source_mode:
        if all(status == STATUS_OK for status in other_required) and (
            codex_status == STATUS_OK
        ):
            code = 0
        elif all(status == STATUS_OK for status in other_required):
            code = 4
        else:
            code = 2
    else:
        assert inspection is not None
        # Installed exits stay owned by state plus codex, so a missing git
        # executable reports `ok: false` without changing the exit class.
        if inspection.kind is not StateKind.HEALTHY:
            code = inspection.exit_code
        else:
            code = 0 if codex_status == STATUS_OK else 4

    return code, {
        "schema_version": DOCTOR_SCHEMA_VERSION,
        "ok": ok,
        "agent_skill_export": agent_skill_export,
        "repository": repository,
        "git": git,
        "policies": policies,
        "model_routing": model_routing,
        "project_memory": project_memory,
        "dependencies": dependencies,
    }
