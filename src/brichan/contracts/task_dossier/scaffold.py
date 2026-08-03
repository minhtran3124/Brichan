#!/usr/bin/env python3
"""Dry-run-first scaffolding for the complete task dossier.

Scaffolding writes nothing without an explicit apply flag, never overwrites an
existing artifact, and never fills evidence. A scaffolded dossier is expected to
fail validation until a human or a recorded session supplies real evidence.
"""

from __future__ import annotations

import argparse
import errno
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .schema import (
    ARTIFACTS,
    PROJECT_SLUG_PATTERN,
    TASK_ID_PATTERN,
    TASK_LEVELS,
)


TEMPLATE_RELATIVE_ROOT = Path("docs/workflows/task-dossier/templates")


@dataclass(frozen=True)
class ScaffoldAction:
    path: Path
    action: str
    reason: str

    def format(self) -> str:
        return f"{self.action}: {self.path}: {self.reason}"


def template_root(repository_root: Path | None = None) -> Path:
    """Return the checkout-mode template directory."""
    if repository_root is None:
        repository_root = Path(__file__).resolve().parents[4]
    return repository_root / TEMPLATE_RELATIVE_ROOT


def template_path(artifact: str, repository_root: Path | None = None) -> Path:
    if artifact not in ARTIFACTS:
        raise ValueError(f"unknown task-dossier artifact: {artifact}")
    return template_root(repository_root) / f"{artifact}.md"


def template_text(artifact: str, repository_root: Path | None = None) -> str:
    path = template_path(artifact, repository_root)
    if not path.is_file():
        raise FileNotFoundError(
            "checkout-mode task-dossier templates are unavailable at "
            f"{path}; this workflow is checkout-only"
        )
    return path.read_text(encoding="utf-8")


def _render(text: str, task_id: str, level: str, project: str) -> str:
    return (
        text.replace("<TASK-000>", task_id)
        .replace("<0, 1, or 2>", level)
        .replace("<project-slug>", project)
    )


def dossier_path(projects_root: Path, project: str, task_id: str) -> Path:
    """Return the dossier directory for a task, refusing to leave the root.

    Scaffolding is the only writing entry point, so identity is validated here
    before any path is built from user input.
    """
    if not PROJECT_SLUG_PATTERN.fullmatch(project):
        raise ValueError(
            "project must be a lowercase hyphenated slug, found "
            f"{project!r}"
        )
    if not TASK_ID_PATTERN.fullmatch(task_id):
        raise ValueError(
            f"task ID must be stable and branch-independent, found {task_id!r}"
        )

    root = projects_root.resolve()
    candidate = root / project / "handoffs" / task_id
    try:
        candidate.resolve().relative_to(root)
    except (OSError, ValueError):
        raise ValueError(
            f"dossier path must stay inside {projects_root}"
        ) from None
    return candidate


def plan_scaffold(
    dossier: Path,
    task_id: str,
    level: str,
    project: str,
    *,
    repository_root: Path | None = None,
) -> list[ScaffoldAction]:
    """Return the writes a scaffold would perform, without performing them."""
    if not PROJECT_SLUG_PATTERN.fullmatch(project):
        raise ValueError(
            f"project must be a lowercase hyphenated slug, found {project!r}"
        )
    if not TASK_ID_PATTERN.fullmatch(task_id):
        raise ValueError(
            f"task ID must be stable and branch-independent, found {task_id!r}"
        )
    if level not in TASK_LEVELS:
        raise ValueError(f"task level must be one of {sorted(TASK_LEVELS)}")
    if dossier.is_symlink():
        raise ValueError(f"dossier directory must not be a symlink: {dossier}")

    actions: list[ScaffoldAction] = []
    for artifact in ARTIFACTS:
        target = dossier / f"{artifact}.md"
        # is_symlink() is checked first and separately: a dangling symlink is
        # invisible to exists(), so a plain existence check would classify it
        # as creatable and then write through the link to its target.
        if target.is_symlink():
            raise ValueError(
                f"refusing to scaffold over a symlinked artifact: {target}"
            )
        if target.exists():
            actions.append(
                ScaffoldAction(target, "preserve", "existing artifact is untouched")
            )
            continue
        template_text(artifact, repository_root)
        actions.append(
            ScaffoldAction(target, "create", f"standard {artifact} template")
        )

    receipt = dossier / "receipt.md"
    actions.append(
        ScaffoldAction(
            receipt,
            "preserve" if receipt.exists() else "manual",
            "the canonical receipt stays coordinator-owned",
        )
    )
    return actions


def _create_exclusively(path: Path, text: str) -> bool:
    """Create ``path`` with ``text``, or report that it already existed.

    Planning and writing are separate steps, so a file can appear in between.
    ``O_EXCL`` makes creation atomic, and ``O_NOFOLLOW`` refuses a symlink that
    appears in the same window, so neither race can overwrite existing content
    or write through a link. Returns False when the file already existed.
    """
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o644)
    except FileExistsError:
        return False
    except OSError as error:
        if error.errno in {errno.ELOOP, errno.EMLINK}:
            return False
        raise
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(text)
    return True


def apply_scaffold(
    dossier: Path,
    task_id: str,
    level: str,
    project: str,
    *,
    repository_root: Path | None = None,
) -> list[ScaffoldAction]:
    """Write every missing artifact, never overwriting or following a link.

    On collision the artifact is preserved and reported as ``preserve``. If the
    colliding entry is a symlink the scaffold aborts, exactly as the pre-write
    guard does; artifacts already created stay, because nothing is overwritten.
    """
    planned = plan_scaffold(
        dossier, task_id, level, project, repository_root=repository_root
    )
    dossier.mkdir(parents=True, exist_ok=True)

    actions: list[ScaffoldAction] = []
    for action in planned:
        if action.action != "create":
            actions.append(action)
            continue
        artifact = action.path.stem
        rendered = _render(
            template_text(artifact, repository_root), task_id, level, project
        )
        if _create_exclusively(action.path, rendered):
            actions.append(action)
            continue
        if action.path.is_symlink():
            raise ValueError(
                "refusing to scaffold over a symlinked artifact: "
                f"{action.path}"
            )
        actions.append(
            ScaffoldAction(
                action.path,
                "preserve",
                "artifact appeared after planning and is untouched",
            )
        )
    return actions


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scaffold the complete standard task dossier (dry run by default)."
    )
    parser.add_argument("task_id", help="stable branch-independent task ID")
    parser.add_argument("--level", required=True, choices=sorted(TASK_LEVELS))
    parser.add_argument("--project", required=True, help="project slug")
    parser.add_argument(
        "--projects-root",
        default=Path("projects"),
        type=Path,
        help="projects root that owns <slug>/handoffs/<task-id>",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write missing artifacts; without it nothing is written",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        dossier = dossier_path(args.projects_root, args.project, args.task_id)
    except ValueError as error:
        print(f"task-dossier scaffold failed: {error}", file=sys.stderr)
        return 1

    try:
        if args.apply:
            actions = apply_scaffold(
                dossier, args.task_id, args.level, args.project
            )
        else:
            actions = plan_scaffold(
                dossier, args.task_id, args.level, args.project
            )
    except (FileNotFoundError, OSError, ValueError) as error:
        print(f"task-dossier scaffold failed: {error}", file=sys.stderr)
        return 1

    for action in actions:
        print(action.format())
    created = sum(1 for action in actions if action.action == "create")
    mode = "wrote" if args.apply else "planned"
    print(f"{mode} {created} task-dossier artifact(s) for {args.task_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
