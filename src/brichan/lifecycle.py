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
from dataclasses import dataclass
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
    "skills/herdr-orchestration/SKILL.md",
    "skills/herdr-orchestration/references/commands.md",
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


#: Version of the `doctor --json` document. Independent of the `.brichan`
#: state schema: this describes the diagnostic report, not the installed
#: footprint.
DOCTOR_SCHEMA_VERSION = 1

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


def initialize_project(paths: ProjectPaths, *, apply: bool) -> tuple[int, list[str]]:
    inspection = inspect_project(paths)
    if inspection.kind is StateKind.HEALTHY:
        return 0, [f"no changes: {paths.state_root} is already healthy"]
    if inspection.kind is not StateKind.UNINITIALIZED:
        return inspection.exit_code, [
            f"{inspection.kind.value}: {paths.state_root}: {inspection.detail}"
        ]

    actions = [f"create .brichan/{path}" for path in documented_footprint()]
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
    ok = codex_status == STATUS_OK and all(
        status == STATUS_OK for status in other_required
    )

    if source_mode:
        if ok:
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
        "repository": repository,
        "git": git,
        "policies": policies,
        "model_routing": model_routing,
        "project_memory": project_memory,
        "dependencies": dependencies,
    }
