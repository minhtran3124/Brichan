#!/usr/bin/env python3
"""Generate a complete task dossier from one structured record.

Generation is dry-run by default and runs in four ordered phases:

``A`` load, validate, and render all eleven artifacts in memory. Nothing
touches the filesystem, so a refused record leaves the tree untouched.

``B`` walk the dossier chain from the projects root, opening every component
with ``O_RDONLY | O_DIRECTORY | O_NOFOLLOW`` relative to its already-open
parent. A descriptor names an inode, not a path, so an ancestor swapped after
its descriptor exists cannot redirect a write; one swapped before the open is
refused. ``ELOOP`` and ``ENOTDIR`` are both refusals because darwin reports
``ENOTDIR`` where Linux reports ``ELOOP``. Missing components are created with
``os.mkdir(..., dir_fd=parent)`` from single validated names, which is safe
before the lock exists: it creates only an empty directory.

``C`` take ``flock(dossier_fd, LOCK_EX | LOCK_NB)`` immediately after the
dossier descriptor is opened and before any temporary or artifact mutation. The
lock is refused, never awaited.

``D`` publish each artifact through a private ``O_EXCL`` temporary that is
written in full, ``fsync``-ed, identity-checked, and then hard-linked into
place with ``follow_symlinks=False``. ``os.rename`` and ``os.replace`` are
forbidden: rename overwrites, and replace accepts no ``dir_fd``. Publication
never overwrites, so ``EEXIST`` preserves the existing file.

**Threat-model boundary.** A non-cooperating process running under the same OS
identity that mutates directory entries while this generator holds the dossier
lock is out of scope. The post-publication check is a point-in-time observation,
not a compare-and-swap: neither prevention nor detection is claimed against
that process.

This module is routing-neutral. It never reads or names a routing manifest; the
effective route, model, and effort it renders are copied from the record.
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import os
import stat
import sys
from pathlib import Path
from typing import Sequence

from .record import (
    ArtifactRecord,
    RecordError,
    RecordFileError,
    TaskRecord,
    load_record,
)
from .scaffold import ScaffoldAction, dossier_path
from .schema import (
    ARTIFACTS,
    ARTIFACT_EXTRA_SECTIONS,
    ARTIFACT_OWNERS,
    ARTIFACT_TITLES,
    BODY_SECTIONS,
    INDEX_IDENTITY_FIELDS,
    INDEX_IDENTITY_SECTION,
    INDEX_STATUS_HEADER,
    INDEX_STATUS_SECTION,
    METADATA_FIELDS,
    METADATA_SECTION,
    TASK_LEVELS,
)


# Bounded temporary-name attempts. Exhaustion is a refusal, never a fallback to
# an unbounded or predictable name.
TEMPORARY_ATTEMPTS = 64

DOSSIER_COMPONENTS = ("handoffs",)


class GenerationError(Exception):
    """A refusal. Nothing is repaired and no partial artifact is published."""


class RecordScopeError(Exception):
    """The requested scope cannot be evaluated: no record file, no root."""


# --------------------------------------------------------------------------
# Phase A: rendering
# --------------------------------------------------------------------------


def _code(value: object) -> str:
    """Render one backtick-wrapped metadata value; JSON null renders `null`."""
    return "`null`" if value is None else f"`{value}`"


def _metadata_value(record: TaskRecord, name: str, label: str) -> object:
    artifact = record.artifacts[name]
    if label == "Task ID":
        return record.task_id
    if label == "Task level":
        return record.level
    if label == "Artifact":
        return name
    if label == "Artifact version":
        return artifact.version
    if label == "Origin":
        return record.effective_origin(name)
    if label == "Owner":
        return ARTIFACT_OWNERS[name]
    if label == "Phase state":
        return artifact.phase_state
    if label == "Applicability":
        return artifact.applicability
    if label == "Applicability rationale":
        return artifact.applicability_rationale
    if label == "Authorship":
        return artifact.authorship
    if label == "Authoring session":
        return artifact.authoring_session
    if label == "Effective route":
        return artifact.effective_route
    if label == "Effective model":
        return artifact.effective_model
    if label == "Effective effort":
        return artifact.effective_effort
    if label == "Reviewing session":
        return artifact.reviewing_session
    if label == "Review verdict":
        return artifact.review_verdict
    raise GenerationError(f"unknown metadata field {label!r}")


def _index_identity_value(
    record: TaskRecord, projects_root_name: str, label: str
) -> object:
    if label == "Task ID":
        return record.task_id
    if label == "Task level":
        return record.level
    if label == "Project":
        return record.project
    if label == "Canonical receipt path":
        return "/".join(
            (projects_root_name, record.project, "handoffs", record.task_id, "receipt.md")
        )
    return record.index_identity[label]


def _status_table(record: TaskRecord) -> list[str]:
    lines = [
        "| " + " | ".join(INDEX_STATUS_HEADER) + " |",
        "| " + " | ".join("---" for _ in INDEX_STATUS_HEADER) + " |",
    ]
    for name in ARTIFACTS:
        artifact = record.artifacts[name]
        cells = (
            _code(name),
            _code(artifact.applicability),
            _code(artifact.phase_state),
            _code(f"{name}.md"),
        )
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def render_artifact(
    record: TaskRecord, name: str, *, projects_root_name: str = "projects"
) -> str:
    """Return the complete Markdown body of one artifact.

    Rendering is deterministic: no timestamp, hostname, process ID, or absolute
    path reaches artifact content.
    """
    if name not in ARTIFACTS:
        raise GenerationError(f"unknown task-dossier artifact {name!r}")
    artifact: ArtifactRecord = record.artifacts[name]

    lines: list[str] = [f"# {ARTIFACT_TITLES[name]}", "", f"## {METADATA_SECTION}", ""]
    for label in METADATA_FIELDS:
        lines.append(f"- {label}: {_code(_metadata_value(record, name, label))}")

    if name == "index":
        lines.extend(["", f"## {INDEX_IDENTITY_SECTION}", ""])
        for label in INDEX_IDENTITY_FIELDS:
            value = _index_identity_value(record, projects_root_name, label)
            lines.append(f"- {label}: {_code(value)}")
        lines.extend(["", f"## {INDEX_STATUS_SECTION}", ""])
        lines.extend(_status_table(record))
    else:
        for section, labels in ARTIFACT_EXTRA_SECTIONS.get(name, ()):
            lines.extend(["", f"## {section}", ""])
            for label in labels:
                lines.append(f"- {label}: {_code(artifact.fields[label])}")

    for section in artifact.sections:
        lines.extend(["", f"## {section.title}", ""])
        lines.extend(section.body)

    claim, evidence, uncertainty = BODY_SECTIONS
    lines.extend(["", f"## {claim}", ""])
    lines.extend(artifact.claim.split("\n"))
    lines.extend(["", f"## {evidence}", ""])
    lines.extend(f"- {item}" for item in artifact.evidence)
    lines.extend(["", f"## {uncertainty}", ""])
    lines.extend(f"- {item}" for item in artifact.uncertainty)
    return "\n".join(lines) + "\n"


def render_dossier(
    record: TaskRecord, *, projects_root_name: str = "projects"
) -> dict[str, str]:
    """Render all eleven artifacts before anything is written."""
    return {
        name: render_artifact(record, name, projects_root_name=projects_root_name)
        for name in ARTIFACTS
    }


# --------------------------------------------------------------------------
# Phase B: descriptor walk
# --------------------------------------------------------------------------


def _open_directory(name: str, parent: int) -> int:
    return os.open(
        name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent
    )


def _identity(descriptor: int) -> tuple[int, int]:
    info = os.fstat(descriptor)
    return (info.st_dev, info.st_ino)


def _walk(
    projects_root: Path,
    components: Sequence[str],
    *,
    apply: bool,
    actions: list[ScaffoldAction],
) -> tuple[int, list[tuple[int, int]]] | None:
    """Open the dossier chain, creating missing components when applying.

    Returns the dossier descriptor and the per-level identities, or ``None``
    when a dry run stops at the first component that does not yet exist.
    """
    try:
        root_fd = os.open(
            projects_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
    except OSError as error:
        raise GenerationError(
            f"cannot open projects root {projects_root}: {error}"
        ) from None

    expected = os.stat(projects_root, follow_symlinks=False)
    if _identity(root_fd) != (expected.st_dev, expected.st_ino):
        os.close(root_fd)
        raise GenerationError("projects root changed identity during the walk")

    identities: list[tuple[int, int]] = [_identity(root_fd)]
    parent = root_fd
    walked: list[str] = []
    for component in components:
        walked.append(component)
        try:
            child = _open_directory(component, parent)
        except FileNotFoundError:
            if not apply:
                os.close(parent)
                actions.append(
                    ScaffoldAction(
                        projects_root.joinpath(*walked),
                        "would create",
                        "dossier directory does not exist yet",
                    )
                )
                return None
            try:
                os.mkdir(component, 0o755, dir_fd=parent)
            except FileExistsError:
                # A cooperating invocation won the mkdir race. Both converge on
                # the same inode; the lock in Phase C admits exactly one.
                pass
            except OSError as error:
                os.close(parent)
                raise GenerationError(
                    f"cannot create dossier component {component!r}: {error}"
                ) from None
            try:
                child = _open_directory(component, parent)
            except OSError as error:
                os.close(parent)
                raise GenerationError(
                    f"cannot open dossier component {component!r}: {error}"
                ) from None
        except OSError as error:
            os.close(parent)
            if error.errno in {errno.ELOOP, errno.ENOTDIR}:
                raise GenerationError(
                    f"dossier component {component!r} is a symlink or not a "
                    f"directory; refusing to write through it: {error}"
                ) from None
            raise GenerationError(
                f"cannot open dossier component {component!r}: {error}"
            ) from None
        os.close(parent)
        parent = child
        identities.append(_identity(parent))
    return parent, identities


def _rewalk(
    projects_root: Path, components: Sequence[str], identities: Sequence[tuple[int, int]]
) -> None:
    """Re-walk the canonical chain and refuse to report a detached success."""
    try:
        parent = os.open(
            projects_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
    except OSError as error:
        raise GenerationError(
            f"final canonical re-walk cannot open the projects root: {error}"
        ) from None
    try:
        if _identity(parent) != identities[0]:
            raise GenerationError(
                "namespace drift: the projects root moved during generation"
            )
        for position, component in enumerate(components, start=1):
            try:
                child = _open_directory(component, parent)
            except OSError as error:
                raise GenerationError(
                    f"namespace drift: cannot re-open {component!r}: {error}"
                ) from None
            os.close(parent)
            parent = child
            if _identity(parent) != identities[position]:
                raise GenerationError(
                    f"namespace drift: {component!r} no longer names the "
                    "directory this run wrote into"
                )
    finally:
        os.close(parent)


# --------------------------------------------------------------------------
# Phase D: publication
# --------------------------------------------------------------------------


def _write_all(descriptor: int, payload: bytes) -> None:
    written = 0
    while written < len(payload):
        count = os.write(descriptor, payload[written:])
        if count <= 0:
            raise GenerationError("short write while staging an artifact")
        written += count


def _create_temporary(dossier_fd: int, task_id: str, name: str) -> tuple[str, int]:
    for attempt in range(TEMPORARY_ATTEMPTS):
        candidate = f".tdgen.{task_id}.{name}.{os.getpid()}.{attempt}.tmp"
        try:
            descriptor = os.open(
                candidate,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                0o644,
                dir_fd=dossier_fd,
            )
        except FileExistsError:
            continue
        except OSError as error:
            raise GenerationError(
                f"cannot stage {name}.md: {error}"
            ) from None
        return candidate, descriptor
    raise GenerationError(
        f"exhausted {TEMPORARY_ATTEMPTS} private temporary names for {name}.md"
    )


def _cleanup_temporary(
    dossier_fd: int,
    candidate: str,
    identity: tuple[int, int],
    *,
    strict: bool = False,
) -> None:
    """Unlink the temporary only when it is still the file this run created.

    ``strict`` is used on the success path, where a cleanup failure must force
    a nonzero outcome rather than leave an unreported orphan. On an error path
    the original fault is the more useful diagnostic, so cleanup stays quiet.
    """
    try:
        info = os.lstat(candidate, dir_fd=dossier_fd)
    except FileNotFoundError:
        return
    except OSError as error:
        if strict:
            raise GenerationError(f"cannot inspect {candidate}: {error}") from None
        return
    if (info.st_dev, info.st_ino) != identity:
        # Something else now owns the name. Never unlink a foreign file.
        return
    try:
        os.unlink(candidate, dir_fd=dossier_fd)
    except OSError as error:
        if strict:
            raise GenerationError(
                f"cannot remove the private temporary {candidate}: {error}"
            ) from None
        return


def _publish(
    dossier_fd: int, task_id: str, name: str, body: str
) -> ScaffoldAction | None:
    """Publish one artifact atomically, or report why it was not published."""
    target = f"{name}.md"
    candidate, descriptor = _create_temporary(dossier_fd, task_id, name)
    # The identity is captured before the first byte is written so that every
    # failure path below can still verify what it is about to unlink.
    identity: tuple[int, int] | None = _identity(descriptor)
    payload = body.encode("utf-8")
    try:
        _write_all(descriptor, payload)
        os.fsync(descriptor)
        staged = os.fstat(descriptor)
        identity = (staged.st_dev, staged.st_ino)
        # A write that reports progress it did not make would otherwise publish
        # a truncated artifact. The size is checked against the rendered body,
        # not against the return values that produced it.
        if staged.st_size != len(payload):
            raise GenerationError(
                f"staged {target} holds {staged.st_size} byte(s) but the "
                f"rendered artifact is {len(payload)}"
            )
        info = os.lstat(candidate, dir_fd=dossier_fd)
        if (info.st_dev, info.st_ino) != identity:
            raise GenerationError(
                f"staged {target} no longer names the file this run wrote"
            )
    except GenerationError:
        os.close(descriptor)
        if identity is not None:
            _cleanup_temporary(dossier_fd, candidate, identity)
        raise
    except OSError as error:
        os.close(descriptor)
        if identity is not None:
            _cleanup_temporary(dossier_fd, candidate, identity)
        raise GenerationError(f"cannot stage {target}: {error}") from None
    else:
        try:
            os.close(descriptor)
        except OSError as error:
            _cleanup_temporary(dossier_fd, candidate, identity)
            raise GenerationError(f"cannot close staged {target}: {error}") from None

    try:
        os.link(
            candidate,
            target,
            src_dir_fd=dossier_fd,
            dst_dir_fd=dossier_fd,
            follow_symlinks=False,
        )
    except FileExistsError:
        _cleanup_temporary(dossier_fd, candidate, identity)
        return ScaffoldAction(
            Path(target), "preserve", "existing artifact is untouched"
        )
    except OSError as error:
        _cleanup_temporary(dossier_fd, candidate, identity)
        raise GenerationError(f"cannot publish {target}: {error}") from None

    # Point-in-time observation only. It is not a compare-and-swap and claims
    # neither prevention nor detection against the excluded process.
    #
    # Both failure branches still run the identity-checked cleanup: this run's
    # own private temporary is not evidence and must not be left behind, while
    # the identity check means a name now held by a foreign entry is preserved.
    # The final entry is never unlinked, whatever the observation reports.
    try:
        published = os.lstat(target, dir_fd=dossier_fd)
    except OSError as error:
        _cleanup_temporary(dossier_fd, candidate, identity)
        raise GenerationError(
            f"cannot observe published {target}: {error}"
        ) from None
    if not stat.S_ISREG(published.st_mode) or (
        published.st_dev,
        published.st_ino,
    ) != identity:
        _cleanup_temporary(dossier_fd, candidate, identity)
        raise GenerationError(
            f"publication integrity: {target} does not name the file this run "
            "published; the entry is left in place for inspection"
        )

    _cleanup_temporary(dossier_fd, candidate, identity, strict=True)
    return ScaffoldAction(Path(target), "create", f"generated {name} artifact")


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


def plan_generation(
    record: TaskRecord, projects_root: Path
) -> list[ScaffoldAction]:
    """Return the writes a generation would perform, performing none of them."""
    return _generate(record, projects_root, apply=False)


def apply_generation(
    record: TaskRecord, projects_root: Path
) -> list[ScaffoldAction]:
    """Publish every missing artifact, never overwriting or following a link."""
    return _generate(record, projects_root, apply=True)


def _generate(
    record: TaskRecord, projects_root: Path, *, apply: bool
) -> list[ScaffoldAction]:
    if not projects_root.is_dir():
        raise RecordScopeError(f"projects root does not exist: {projects_root}")

    # Phase A: nothing below this line runs if rendering refuses.
    bodies = render_dossier(record, projects_root_name=projects_root.resolve().name)
    dossier = dossier_path(projects_root, record.project, record.task_id)

    actions: list[ScaffoldAction] = []
    components = (record.project, *DOSSIER_COMPONENTS, record.task_id)

    # Phase B.
    walked = _walk(projects_root, components, apply=apply, actions=actions)
    if walked is None:
        for name in ARTIFACTS:
            actions.append(
                ScaffoldAction(
                    dossier / f"{name}.md", "create", f"generated {name} artifact"
                )
            )
        actions.append(
            ScaffoldAction(
                dossier / "receipt.md",
                "manual",
                "the canonical receipt stays coordinator-owned",
            )
        )
        return actions

    dossier_fd, identities = walked
    try:
        if not apply:
            for name in ARTIFACTS:
                target = f"{name}.md"
                try:
                    os.lstat(target, dir_fd=dossier_fd)
                except FileNotFoundError:
                    actions.append(
                        ScaffoldAction(
                            dossier / target, "create", f"generated {name} artifact"
                        )
                    )
                    continue
                actions.append(
                    ScaffoldAction(
                        dossier / target, "preserve", "existing artifact is untouched"
                    )
                )
            actions.append(
                ScaffoldAction(
                    dossier / "receipt.md",
                    "manual",
                    "the canonical receipt stays coordinator-owned",
                )
            )
            return actions

        # Phase C: refused, never awaited, and taken before any mutation.
        try:
            fcntl.flock(dossier_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise GenerationError(
                f"another generation holds the dossier lock: {error}"
            ) from None

        # Phase D.
        published: list[str] = []
        failure: GenerationError | None = None
        for name in ARTIFACTS:
            try:
                action = _publish(dossier_fd, record.task_id, name, bodies[name])
            except GenerationError as error:
                failure = error
                break
            actions.append(
                ScaffoldAction(dossier / f"{name}.md", action.action, action.reason)
            )
            if action.action == "create":
                published.append(name)

        try:
            os.fsync(dossier_fd)
        except OSError as error:
            raise GenerationError(
                f"cannot fsync the dossier directory: {error}"
            ) from None

        preserved = [
            action.path.name
            for action in actions
            if action.action == "preserve"
        ]
        if failure is not None or preserved:
            unpublished = [
                f"{name}.md" for name in ARTIFACTS if name not in published
            ]
            detail = "; ".join(
                part
                for part in (
                    str(failure) if failure is not None else "",
                    f"published={[f'{name}.md' for name in published]}",
                    f"unpublished={unpublished}",
                )
                if part
            )
            raise GenerationError(f"partial adoption: {detail}")
    finally:
        os.close(dossier_fd)

    _rewalk(projects_root, components, identities)
    actions.append(
        ScaffoldAction(
            dossier / "receipt.md",
            "manual",
            "the canonical receipt stays coordinator-owned",
        )
    )
    return actions


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the complete standard task dossier from one structured "
            "record (dry run by default)."
        )
    )
    parser.add_argument("task_id", help="stable branch-independent task ID")
    parser.add_argument("--level", required=True, choices=sorted(TASK_LEVELS))
    parser.add_argument("--project", required=True, help="project slug")
    parser.add_argument(
        "--record", required=True, type=Path, help="structured task record JSON"
    )
    parser.add_argument(
        "--projects-root",
        default=Path("projects"),
        type=Path,
        help="projects root that owns <slug>/handoffs/<task-id>",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="publish missing artifacts; without it nothing is written",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        record = load_record(
            args.record,
            task_id=args.task_id,
            level=args.level,
            project=args.project,
        )
    except RecordFileError as error:
        print(f"task-dossier generation failed: {error}", file=sys.stderr)
        return 2
    except RecordError as error:
        for diagnostic in error.diagnostics:
            print(f"record: {diagnostic}", file=sys.stderr)
        print(
            f"task-dossier generation refused: {len(error.diagnostics)} record "
            "diagnostic(s).",
            file=sys.stderr,
        )
        return 1

    try:
        if args.apply:
            actions = apply_generation(record, args.projects_root)
        else:
            actions = plan_generation(record, args.projects_root)
    except RecordScopeError as error:
        print(f"task-dossier generation failed: {error}", file=sys.stderr)
        return 2
    except (GenerationError, ValueError) as error:
        print(f"task-dossier generation failed: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"task-dossier generation failed: {error}", file=sys.stderr)
        return 1

    for action in actions:
        print(action.format())
    created = sum(1 for action in actions if action.action == "create")
    mode = "wrote" if args.apply else "planned"
    print(f"{mode} {created} task-dossier artifact(s) for {record.task_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
