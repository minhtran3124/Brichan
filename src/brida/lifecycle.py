"""Schema-v1 project initialization and diagnostics."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
from dataclasses import dataclass
from enum import Enum
from importlib.resources import files
from pathlib import Path
from typing import Any

from brida import __version__
from brida.orchestration.model_routing import RoutingError, load_settings

from .project import ProjectPaths


SCHEMA_VERSION = 1
LAYOUT_NAME = "brida-project"
RESOURCE_PACKAGE = "brida.resources.dogfood_v1"
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
        return Inspection(StateKind.UNINITIALIZED, "no .brida state directory")
    if stat.S_ISLNK(state_metadata.st_mode):
        return Inspection(StateKind.MALFORMED, ".brida must not be a symlink")
    if not stat.S_ISDIR(state_metadata.st_mode):
        return Inspection(StateKind.MALFORMED, ".brida is not a directory")

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

    actions = [f"create .brida/{path}" for path in documented_footprint()]
    if not apply:
        return 0, ["dry-run: zero writes", *actions]

    try:
        with tempfile.TemporaryDirectory(
            prefix=".brida-stage-", dir=paths.project_root
        ) as temporary:
            staged_state = Path(temporary) / ".brida"
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
        f"herdr: {'ok ' + str(Path(herdr).resolve()) if herdr else 'optional-missing'}"
    )
    if codex is None:
        return 4, lines
    return 0, lines
