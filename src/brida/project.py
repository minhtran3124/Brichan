"""Target-project discovery for installed Brida workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ProjectError(ValueError):
    """Raised when a target Git project cannot be resolved safely."""


@dataclass(frozen=True)
class ProjectPaths:
    """The three roots used by the installed-package vertical slice."""

    tool_root: Path
    project_root: Path
    state_root: Path


def package_root() -> Path:
    """Return the installed package root, never a target-repository path."""

    return Path(__file__).resolve().parent


def find_git_root(
    start: Path | None = None,
    *,
    explicit: Path | None = None,
) -> Path:
    """Resolve a narrow, top-level Git repository without invoking Git."""

    if explicit is not None:
        candidate = explicit.expanduser().resolve()
        if not candidate.is_dir():
            raise ProjectError(f"target project is not a directory: {candidate}")
        if not (candidate / ".git").exists():
            raise ProjectError(
                f"target project is not a Git repository root: {candidate}"
            )
        return candidate

    current = (Path.cwd() if start is None else start).expanduser().resolve()
    if not current.is_dir():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise ProjectError(f"cannot find a Git repository from: {current}")


def project_paths(
    start: Path | None = None,
    *,
    explicit: Path | None = None,
) -> ProjectPaths:
    project_root = find_git_root(start, explicit=explicit)
    return ProjectPaths(
        tool_root=package_root(),
        project_root=project_root,
        state_root=project_root / ".brida",
    )
