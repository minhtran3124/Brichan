#!/usr/bin/env python3
"""Append-only durable record of Brichan worker launches and finishes.

Ledger schema version 1. One JSON object per line (JSONL), UTF-8, keys sorted,
exactly one ``\\n`` terminator per record. The ledger carries its own
``schema_version``, versioned separately from the installed ``.brichan`` state
schema, so a ledger revision never migrates managed state (``PACKAGED-003``).

Two event kinds exist. A ``launched`` record is machine-written by
``brichan-herdr-agent-start`` once a pane is confirmed started. A ``finished``
record is a coordinator **attestation** written only by this module's ``finish``
command; nothing here can observe a worker finishing, so nothing is inferred
from scheduling state and the absence of a ``finished`` record means "unknown",
never "still running" or "failed".

Consumer rules
--------------

- A ``finished`` record pairs with the ``launched`` record carrying the same
  ``launch_id``. ``worker`` and ``pane_id`` are informational and are never
  used for joining: worker names may be reused across launches and Herdr pane
  IDs outlive neither the server nor pane reuse.
- **The first ``finished`` record for a ``launch_id`` in file order wins**, and
  any later one is reported as a duplicate. ``finish`` refuses to write a
  second attestation for a ``launch_id``, but that refusal reads the ledger and
  then appends, so "at most one ``finished`` record per launch" is a
  **one-at-a-time guarantee**: two overlapping ``finish`` runs for the same
  ``launch_id`` can both pass the check. The file-order rule is what makes a
  consumer deterministic when they do.
- Readers ignore unknown keys, ignore empty and whitespace-only lines *without
  counting them* (two writers repairing the same crash fragment each prepend a
  newline, which is benign), and skip **every** undecodable non-empty line
  wherever it sits while counting it and surfacing the count.

Records are append-only and are never amended in version 1.

Safety
------

Every write walks its directory chain descriptor-relative with ``O_NOFOLLOW``,
creates at most the file's immediate parent directory, never creates a
``.brichan`` directory, and never writes inside one that lacks a regular
``manifest.json`` — a partial ``.brichan`` is diagnosed ``malformed`` and would
break the target project. The ledger file is opened
``O_RDWR | O_APPEND | O_CREAT | O_NOFOLLOW | O_NONBLOCK`` and type-checked with
``fstat`` before any read or write, so a FIFO, directory, or device is refused
without blocking.

Records hold no filesystem paths at all — only Herdr IDs, names, the launch
identifier, and routing strings — so no personal path can enter the ledger.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import stat
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


#: Ledger record schema, versioned independently of installed state (R6).
LEDGER_SCHEMA_VERSION = 1

#: Managed-state directory name and the manifest that proves it is healthy.
STATE_DIRECTORY = ".brichan"
STATE_MANIFEST = "manifest.json"

#: Fixed installed-mode ledger location under the state root.
LEDGER_DIRECTORY = "ledger"
LEDGER_FILE = "workers.jsonl"

#: The only final-component suffix ``--ledger-file`` accepts. No managed
#: resource ends in it, so no accepted value can name managed state.
LEDGER_SUFFIX = ".jsonl"

#: Record ``source`` values.
LAUNCH_SOURCE = "brichan-herdr-agent-start"
FINISH_SOURCE = "coordinator"

#: Every Brichan-owned worker name begins with this prefix.
WORKER_NAME_PREFIX = "brichan-"

#: Creation mode before umask. The ledger is data, never a secret.
LEDGER_FILE_MODE = 0o644

#: Read chunk for the tolerant reader.
_READ_CHUNK_BYTES = 65536

#: The one stderr note a launch prints when no ledger location resolves.
NO_LOCATION_NOTE = "ledger: no ledger location for this launch; not recorded"

#: Installed console-script and checkout wrapper program name.
PROGRAM = "brichan-herdr-worker-ledger"


class LedgerError(RuntimeError):
    """Raised when a ledger location cannot be used or written safely."""


class LedgerPathError(ValueError):
    """Raised when a ``--ledger-file`` value is refused at argument-parse time.

    This is a usage error: it is raised before any Herdr call, so an invalid
    value can never affect a launch that has already started.
    """


@dataclass(frozen=True)
class LedgerLocation:
    """A ledger file named as a base directory plus relative components."""

    base: Path
    parts: tuple[str, ...]

    @property
    def path(self) -> Path:
        return self.base.joinpath(*self.parts)


@dataclass(frozen=True)
class LedgerRead:
    """Records recovered from a ledger, with the count of damaged lines."""

    records: tuple[dict[str, Any], ...]
    skipped: int


# ---------------------------------------------------------------------------
# Location resolution
# ---------------------------------------------------------------------------


def installed_location(project_root: Path) -> LedgerLocation:
    """The fixed installed-mode ledger under a target's state root.

    This is the only path inside a ``.brichan`` directory any ledger code path
    may ever name.
    """

    return LedgerLocation(
        base=project_root,
        parts=(STATE_DIRECTORY, LEDGER_DIRECTORY, LEDGER_FILE),
    )


def resolve_checkout_location(checkout_root: Path, value: str) -> LedgerLocation:
    """Resolve a ``--ledger-file`` value against one checkout root.

    This is the single shared resolver (R15): the launcher and ``finish`` call
    it with the same base, so the same flag value always names the same file in
    both entry points. The accepted surface is deliberately small — relative,
    already normalized, no ``.``/``..`` component, no component named
    ``.brichan`` under case folding, and a ``.jsonl`` final name — so managed
    state is unreachable through the flag by construction rather than by an
    added rule. Refusing absolute paths also removes any need to walk an
    absolute chain, so the ``O_NOFOLLOW`` walk always starts at one defined
    base.
    """

    if not value:
        raise LedgerPathError("--ledger-file must not be empty")
    if os.path.isabs(value):
        raise LedgerPathError(f"--ledger-file must be a relative path: {value}")
    if value != os.path.normpath(value):
        raise LedgerPathError(
            f"--ledger-file must already be normalized: {value}"
        )
    parts = tuple(value.split("/"))
    for component in parts:
        if component in ("", ".", ".."):
            raise LedgerPathError(
                f"--ledger-file must not contain a {component!r} component: "
                f"{value}"
            )
        # Compared with ``casefold`` because the development platform's default
        # filesystem is case-insensitive, where a case-sensitive check would
        # let ``.BRICHAN/...`` reach managed state.
        if component.casefold() == STATE_DIRECTORY:
            raise LedgerPathError(
                f"--ledger-file must not name managed state: {value}"
            )
    if not parts[-1].endswith(LEDGER_SUFFIX):
        raise LedgerPathError(
            f"--ledger-file must name a {LEDGER_SUFFIX} file: {value}"
        )
    return LedgerLocation(base=checkout_root, parts=parts)


def _state_manifest_is_regular(project_root: Path) -> bool:
    try:
        info = os.lstat(project_root / STATE_DIRECTORY / STATE_MANIFEST)
    except OSError:
        return False
    return stat.S_ISREG(info.st_mode)


def resolve_installed_location(project: str | Path | None = None) -> LedgerLocation:
    """The installed ledger for an explicit or discovered target root.

    The target root is ``--project`` when given, else the Git root discovered
    upward from the process working directory — the same upward walk the legacy
    launcher path uses, so a launch recorded from a subdirectory ``--cwd`` and a
    later ``finish`` run in that repository resolve the same file.
    """

    from ..project import find_git_root

    if project is None:
        root = find_git_root()
    else:
        root = find_git_root(explicit=Path(project))
    if not _state_manifest_is_regular(root):
        raise LedgerError(f"no ledger for this target: {root}")
    return installed_location(root)


def legacy_launch_location(cwd: str | Path) -> LedgerLocation | None:
    """Resolve a legacy launch's ledger, or ``None``. Never raises (M4).

    A legacy launch takes an explicit command after ``--`` and touches no
    project state today. Resolution here must therefore never fail the launch:
    a non-Git ``--cwd``, a missing ``.brichan``, or unreadable state all
    degrade to "no location", which the caller reports as a one-line note.
    """

    from ..project import find_git_root

    try:
        # ``start=`` walks upward, unlike the ``explicit=`` form ``--project``
        # uses: a legacy ``--cwd`` is often a subdirectory, and requiring it to
        # be the Git root itself is exactly what used to fail the launch.
        root = find_git_root(start=Path(cwd).expanduser())
        if not _state_manifest_is_regular(root):
            return None
        return installed_location(root)
    except Exception:  # noqa: BLE001 - resolution never fails a launch (R7)
        return None


# ---------------------------------------------------------------------------
# Open discipline
# ---------------------------------------------------------------------------


def _open_directory(name: str | Path, *, dir_fd: int | None = None) -> int:
    return os.open(
        name,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        dir_fd=dir_fd,
    )


def _check_state_guard(directory_fd: int, component: str) -> None:
    """R9: never write inside a ``.brichan`` lacking a regular manifest.

    A partial ``.brichan`` without ``manifest.json`` is diagnosed ``malformed``
    by project inspection, so writing into one would break the target project.
    """

    if component.casefold() != STATE_DIRECTORY:
        return
    try:
        info = os.stat(STATE_MANIFEST, dir_fd=directory_fd, follow_symlinks=False)
    except OSError as exc:
        raise LedgerError(
            f"no ledger for this target: {STATE_DIRECTORY}/{STATE_MANIFEST} "
            f"is unreadable"
        ) from exc
    if not stat.S_ISREG(info.st_mode):
        raise LedgerError(
            f"no ledger for this target: {STATE_DIRECTORY}/{STATE_MANIFEST} "
            f"is not a regular file"
        )


@contextlib.contextmanager
def _ledger_directory(
    location: LedgerLocation, *, create: bool
) -> Iterator[int]:
    """Walk the ledger's directory chain descriptor-relative with O_NOFOLLOW.

    Every component below the base is opened ``O_NOFOLLOW``, so a symlinked
    component anywhere in the chain is a refusal and the relative path cannot
    be redirected into managed state or out of its base. At most the file's
    immediate parent is created, and never when that parent is a ``.brichan``.
    """

    descriptors: list[int] = []
    try:
        descriptors.append(_open_directory(location.base))
        directories = location.parts[:-1]
        for index, component in enumerate(directories):
            is_parent = index == len(directories) - 1
            if (
                is_parent
                and create
                and component.casefold() != STATE_DIRECTORY
            ):
                try:
                    os.mkdir(component, dir_fd=descriptors[-1])
                except FileExistsError:
                    pass
            opened = _open_directory(component, dir_fd=descriptors[-1])
            descriptors.append(opened)
            _check_state_guard(opened, component)
        yield descriptors[-1]
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _open_ledger_file(directory_fd: int, name: str, *, create: bool) -> int:
    """Open the ledger file and refuse anything that is not a regular file.

    ``O_RDWR`` is load-bearing twice: a FIFO opened read-write never blocks in
    ``open``, and the newline repair needs ``os.pread``. ``O_NONBLOCK`` is
    defense in depth for shapes where the open itself could block. The
    descriptor is type-checked before any read or write (``PY-004``, R11).
    """

    flags = os.O_RDWR | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK
    if create:
        flags |= os.O_CREAT
    descriptor = os.open(name, flags, LEDGER_FILE_MODE, dir_fd=directory_fd)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise LedgerError(
                f"ledger is not a regular file: mode 0o{info.st_mode:o}"
            )
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def append_record(location: LedgerLocation, record: dict[str, Any]) -> None:
    """Append exactly one record. Raises on any refusal or failure."""

    payload = (
        json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    with _ledger_directory(location, create=True) as directory_fd:
        descriptor = _open_ledger_file(
            directory_fd, location.parts[-1], create=True
        )
        try:
            size = os.fstat(descriptor).st_size
            # Newline repair: a crash or short write can leave a fragment with
            # no terminator. Prefixing one newline confines the fragment to its
            # own line instead of letting it swallow this record.
            if size > 0 and os.pread(descriptor, 1, size - 1) != b"\n":
                payload = b"\n" + payload
            written = os.write(descriptor, payload)
            if written != len(payload):
                raise LedgerError(
                    f"short ledger write: {written} of {len(payload)} bytes"
                )
        finally:
            os.close(descriptor)


def _failure_reason(exc: BaseException) -> str:
    reason = str(exc) or exc.__class__.__name__
    if isinstance(exc, LedgerError):
        return reason
    return f"{exc.__class__.__name__}: {reason}"


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


def parse_records(data: bytes) -> LedgerRead:
    """Decode a ledger's bytes tolerantly.

    Empty and whitespace-only lines are ignored *without* being counted; every
    undecodable non-empty line is skipped and counted, wherever it sits.
    """

    records: list[dict[str, Any]] = []
    skipped = 0
    for line in data.decode("utf-8", errors="replace").split("\n"):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            skipped += 1
            continue
        if not isinstance(record, dict):
            skipped += 1
            continue
        records.append(record)
    return LedgerRead(tuple(records), skipped)


def read_records(location: LedgerLocation) -> LedgerRead:
    """Read a ledger through the same walk and type check the writer uses."""

    with _ledger_directory(location, create=False) as directory_fd:
        descriptor = _open_ledger_file(
            directory_fd, location.parts[-1], create=False
        )
        chunks: list[bytes] = []
        try:
            while True:
                chunk = os.pread(
                    descriptor, _READ_CHUNK_BYTES, sum(len(c) for c in chunks)
                )
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(descriptor)
    return parse_records(b"".join(chunks))


def launched_record(
    records: Iterable[dict[str, Any]], launch_id: str
) -> dict[str, Any] | None:
    """The first ``launched`` record for ``launch_id`` in file order."""

    for record in records:
        if (
            record.get("event") == "launched"
            and record.get("launch_id") == launch_id
        ):
            return record
    return None


def finished_record(
    records: Iterable[dict[str, Any]], launch_id: str
) -> dict[str, Any] | None:
    """The winning ``finished`` record for ``launch_id``.

    The first ``finished`` record for a ``launch_id`` in file order wins; any
    later one is a duplicate. This is the tie-break consumers apply when two
    overlapping ``finish`` runs both pass the duplicate check.
    """

    for record in records:
        if (
            record.get("event") == "finished"
            and record.get("launch_id") == launch_id
        ):
            return record
    return None


# ---------------------------------------------------------------------------
# Record construction
# ---------------------------------------------------------------------------


def utc_timestamp() -> str:
    """UTC ``YYYY-MM-DDTHH:MM:SSZ``, seconds precision, literal ``Z``."""

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pane_field(split_payload: Any, key: str) -> str | None:
    """Read ``result.pane.<key>`` out of a ``pane split`` envelope.

    Herdr can exit 0 with an envelope that omits the section, so the read is
    defensive and a gap records ``null`` rather than raising.
    """

    result = split_payload.get("result") if isinstance(split_payload, dict) else None
    pane = result.get("pane") if isinstance(result, dict) else None
    value = pane.get(key) if isinstance(pane, dict) else None
    return value if isinstance(value, str) and value else None


def build_launched_record(
    *,
    launch_id: str,
    worker: str,
    task_id: str | None,
    route_name: str | None,
    route: Any,
    command: Sequence[str],
    pane_id: str,
    split_payload: Any,
    launched_at: str,
) -> dict[str, Any]:
    """Build one ``launched`` record with the schema's declared null rules.

    A routed launch records the resolved route's runtime, model, and effort. A
    legacy launch records ``route``, ``model``, and ``effort`` as ``null`` — the
    model is never parsed out of a legacy argv — and takes ``runtime`` from the
    validated legacy command, whose executable the provider guard already
    restricts to exactly ``codex`` or ``claude``.
    """

    if route is None:
        runtime = command[0]
        model: str | None = None
        effort: str | None = None
        route_value: str | None = None
    else:
        runtime = route.runtime
        model = route.model
        effort = route.effort
        route_value = route_name
    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "event": "launched",
        "launch_id": launch_id,
        "worker": worker,
        "task_id": task_id,
        "route": route_value,
        "runtime": runtime,
        "model": model,
        "effort": effort,
        "pane_id": pane_id,
        "workspace_id": _pane_field(split_payload, "workspace_id"),
        "tab_id": _pane_field(split_payload, "tab_id"),
        "launched_at": launched_at,
        "source": LAUNCH_SOURCE,
    }


def build_finished_record(
    *,
    launch_id: str,
    worker: str,
    task_id: str | None,
    pane_id: str | None,
    evidence: Sequence[str],
    observed_at: str,
) -> dict[str, Any]:
    """Build one ``finished`` attestation.

    ``observed_at`` is the time the finish was *recorded*. An actual finish time
    is unknowable here and is deliberately not a field, so nothing is estimated.
    """

    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "event": "finished",
        "launch_id": launch_id,
        "worker": worker,
        "task_id": task_id,
        "pane_id": pane_id,
        "observed_at": observed_at,
        "evidence": list(evidence),
        "source": FINISH_SOURCE,
    }


# ---------------------------------------------------------------------------
# Never-raise entry points (M3, R7)
# ---------------------------------------------------------------------------


def record_launch(
    location: LedgerLocation,
    *,
    launch_id: str,
    worker: str,
    task_id: str | None,
    route_name: str | None,
    route: Any,
    command: Sequence[str],
    pane_id: str,
    split_payload: Any,
) -> str | None:
    """Append one ``launched`` record. Returns a warning reason, never raises.

    ``Exception`` is caught here — not ``BaseException`` — because no exception
    from ledger code may change the launcher's exit status or suppress the
    ``agent_started`` envelope: the launcher's outer handler would otherwise
    turn a ``KeyError`` into exit 1 or let a ``TypeError`` escape as a
    traceback. ``KeyboardInterrupt`` and ``SystemExit`` are deliberately not
    caught: interrupting the process is the operator's prerogative and is not a
    ledger defect.
    """

    try:
        record = build_launched_record(
            launch_id=launch_id,
            worker=worker,
            task_id=task_id,
            route_name=route_name,
            route=route,
            command=command,
            pane_id=pane_id,
            split_payload=split_payload,
            launched_at=utc_timestamp(),
        )
        append_record(location, record)
    except Exception as exc:  # noqa: BLE001 - R7: a ledger defect never fails a launch
        return _failure_reason(exc)
    return None


def record_finish(
    location: LedgerLocation,
    *,
    launch_id: str,
    worker: str,
    task_id: str | None,
    pane_id: str | None,
    evidence: Sequence[str],
) -> str | None:
    """Append one ``finished`` attestation. Returns a refusal reason or ``None``.

    Refuses an unmatched ``launch_id`` and a ``launch_id`` that already carries
    a ``finished`` record, writing nothing in either case.
    """

    try:
        try:
            existing = read_records(location)
        except FileNotFoundError:
            # A target whose ledger does not exist yet holds no launched
            # record, so this is the unmatched-identifier refusal rather than
            # an I/O failure. Nothing is created: the append below is never
            # reached.
            existing = LedgerRead((), 0)
        if launched_record(existing.records, launch_id) is None:
            return f"no launched record for launch_id {launch_id}"
        if finished_record(existing.records, launch_id) is not None:
            return f"launch_id {launch_id} already has a finished record"
        append_record(
            location,
            build_finished_record(
                launch_id=launch_id,
                worker=worker,
                task_id=task_id,
                pane_id=pane_id,
                evidence=evidence,
                observed_at=utc_timestamp(),
            ),
        )
    except Exception as exc:  # noqa: BLE001 - one guard for every ledger path
        return _failure_reason(exc)
    return None


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def _build_parser(*, checkout: bool) -> argparse.ArgumentParser:
    """Build the ``finish`` parser for exactly one mode.

    The two entry points differ only in how the ledger is located: checkout
    mode requires ``--ledger-file`` and resolves it against the checkout root,
    while installed mode does not define the flag at all — passing it there is
    an ordinary usage error — and always uses the fixed state-root path.
    Neither inspects ``BRICHAN_ROOT`` (``SCRIPT-002``).
    """

    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Record coordinator-attested Brichan worker lifecycle events.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    finish = subparsers.add_parser(
        "finish",
        help="record a coordinator-attested worker finish",
    )
    finish.add_argument("--worker", required=True)
    finish.add_argument("--launch-id", required=True)
    finish.add_argument(
        "--evidence",
        action="append",
        required=True,
        help="repeatable; a repository-relative path or a command citation",
    )
    finish.add_argument("--task")
    finish.add_argument("--pane")
    if checkout:
        finish.add_argument("--ledger-file", required=True)
    else:
        finish.add_argument("--project")
    return parser


def _finish_command(
    args: argparse.Namespace, *, checkout_root: Path | None
) -> int:
    # A ``finished`` record is an attestation, not a machine observation: this
    # command cannot verify completion, it records that the coordinator, holding
    # the named evidence, attests the worker's lifecycle end. The refusals below
    # bound fabrication and typos.
    if not args.worker.startswith(WORKER_NAME_PREFIX):
        print(
            f"{PROGRAM}: worker name must begin with {WORKER_NAME_PREFIX}: "
            f"{args.worker}",
            file=sys.stderr,
        )
        return 1
    for item in args.evidence:
        if not item.strip():
            print(
                f"{PROGRAM}: every --evidence item must be non-empty",
                file=sys.stderr,
            )
            return 1

    if checkout_root is not None:
        try:
            location = resolve_checkout_location(checkout_root, args.ledger_file)
        except LedgerPathError as exc:
            print(f"{PROGRAM}: {exc}", file=sys.stderr)
            return 2
    else:
        try:
            location = resolve_installed_location(args.project)
        except (LedgerError, ValueError, OSError) as exc:
            print(f"{PROGRAM}: {exc}", file=sys.stderr)
            return 1

    reason = record_finish(
        location,
        launch_id=args.launch_id,
        worker=args.worker,
        task_id=args.task,
        pane_id=args.pane,
        evidence=args.evidence,
    )
    if reason is not None:
        print(f"{PROGRAM}: {reason}", file=sys.stderr)
        return 1
    return 0


def _run(argv: Sequence[str] | None, *, checkout_root: Path | None) -> int:
    parser = _build_parser(checkout=checkout_root is not None)
    try:
        args = parser.parse_args(
            sys.argv[1:] if argv is None else list(argv)
        )
    except SystemExit as exc:  # argparse usage errors and --help
        return int(exc.code or 0)
    return _finish_command(args, checkout_root=checkout_root)


def checkout_main(
    checkout_root: Path | str, argv: Sequence[str] | None = None
) -> int:
    """Source-checkout entrypoint, reached only from the repository wrapper.

    The wrapper derives the root from its own location, so checkout routing is
    a property of the launch rather than of the environment.
    """

    try:
        root = Path(checkout_root).expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        print(
            f"{PROGRAM}: unusable checkout root {checkout_root}: {exc}",
            file=sys.stderr,
        )
        return 2
    return _run(argv, checkout_root=root)


def main(argv: Sequence[str] | None = None) -> int:
    """Installed console-script entrypoint; always the fixed managed path.

    Exit ``0`` recorded, ``1`` refused or failed, ``2`` usage. Unlike the
    launcher, ``finish`` may fail loudly: it wraps no running agent, so
    fail-closed is the correct posture.
    """

    return _run(argv, checkout_root=None)


if __name__ == "__main__":
    raise SystemExit(main())
