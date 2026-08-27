"""Verification, Snapshot publication, and the read-only techstacks CLI.

This is the only techstacks module that owns a command surface. It imports
``sys`` and writes to the process streams; every other module in the package
stays importable without loading a CLI. Nothing here re-implements resolution:
``verify_snapshot`` reconstructs the Snapshot's own ResolutionInput and calls
the production resolver, and ``publish_snapshot`` drives that same resolver
through the Design section 16 publish-then-verify protocol.

Every literal in this module — help bytes, exit-2 lines, the publication path
grammar, and the exit codes — is copied from Design sections 2, 10, and 16. No
untrusted token, path, or exception detail is ever echoed onto a stream.
"""

from __future__ import annotations

import datetime
import errno
import json
import os
import re
import stat
import sys
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any

from . import filesystem
from .model import (
    CLI_JSON_BYTE_LIMIT,
    PUBLICATION_ATTEMPT_MAX,
    RELATIVE_PATH_BYTE_MAX,
    ROOT_API_OUTCOMES_BY_CODE,
    SCHEMA_VERSION,
    SNAPSHOT_DOCUMENT_BYTE_LIMIT,
    Resolution,
    ResolutionInput,
    Snapshot,
    SnapshotAttempt,
    SnapshotPublication,
    TechstackError,
    Verification,
    build_snapshot_differences,
    canonical_json_document,
    is_normalized_relative_path,
    observed_blocked_difference,
    observed_not_applicable_difference,
    publication_document,
    resolution_input_from_json_object,
    root_api_error_for_code,
    snapshot_document,
    snapshot_from_json_object,
)
from .resolver import read_project_file, resolve_context


# ---------------------------------------------------------------------------
# Importable verification
# ---------------------------------------------------------------------------


def verify_snapshot(
    snapshot: Any,
    project_root: Any,
    as_of: Any,
) -> Verification:
    """Verify one Snapshot against its project on ``as_of``.

    Precedence is exactly Design section 14: Snapshot type/schema/digest, then
    ``as_of`` type and equality, then the platform predicate, then the root,
    then observation. The Snapshot's own schema validation already rejects a
    null, different, non-index-0, or root-SelectedFile-inconsistent
    ``root_map``, so that rejection happens before any project access.
    """

    if not isinstance(snapshot, Snapshot):
        raise root_api_error_for_code("SNAPSHOT_TYPE")
    # An exact ``datetime.date``; a ``datetime`` is a subclass and is rejected.
    if type(as_of) is not datetime.date:
        raise root_api_error_for_code("SNAPSHOT_AS_OF_TYPE")
    if as_of.isoformat() != snapshot.as_of:
        raise root_api_error_for_code("SNAPSHOT_AS_OF_MISMATCH")

    observed = resolve_context(_input_of_snapshot(snapshot), project_root)
    expected_digest = snapshot.snapshot_sha256
    if observed.status == "blocked":
        return Verification(
            schema_version=SCHEMA_VERSION,
            status="blocked",
            expected_snapshot_sha256=expected_digest,
            observed_snapshot_sha256=None,
            observed_resolution=observed,
            differences=(observed_blocked_difference(),),
        )
    if observed.status == "not_applicable":
        return Verification(
            schema_version=SCHEMA_VERSION,
            status="drift",
            expected_snapshot_sha256=expected_digest,
            observed_snapshot_sha256=None,
            observed_resolution=observed,
            differences=(observed_not_applicable_difference(),),
        )
    observed_digest = observed.snapshot.snapshot_sha256
    if observed_digest == expected_digest:
        return Verification(
            schema_version=SCHEMA_VERSION,
            status="match",
            expected_snapshot_sha256=expected_digest,
            observed_snapshot_sha256=observed_digest,
            observed_resolution=observed,
            differences=(),
        )
    return Verification(
        schema_version=SCHEMA_VERSION,
        status="drift",
        expected_snapshot_sha256=expected_digest,
        observed_snapshot_sha256=observed_digest,
        observed_resolution=observed,
        differences=build_snapshot_differences(snapshot, observed.snapshot),
    )


def _input_of_snapshot(snapshot: Snapshot) -> ResolutionInput:
    """Reconstruct the exact ResolutionInput the Snapshot was resolved from."""

    return ResolutionInput(
        task_id=snapshot.task_id,
        plan_id=snapshot.plan_id,
        plan_version=snapshot.plan_version,
        attempt_id=snapshot.attempt_id,
        as_of=snapshot.as_of,
        scope_paths=snapshot.scope_paths,
        context_chains=snapshot.context_chains,
        exception_approvals=snapshot.exception_approvals,
        declared_conflicts=snapshot.declared_conflicts,
    )


# ---------------------------------------------------------------------------
# Snapshot publication
# ---------------------------------------------------------------------------

#: The refusal detail. Design section 2 defines ``SNAPSHOT_OUTPUT_REFUSED`` as
#: a CLI exit-2 surface condition rather than an API caller error, and Design
#: section 4 closes the ``TechstackError`` hierarchy at exactly
#: ``TechstackInputError`` and ``TechstackSnapshotError``, so the class below is
#: a module-private plain ``Exception`` exactly like ``_Usage`` and
#: ``_DuplicateKey``.
SNAPSHOT_OUTPUT_REFUSED_DETAIL = (
    "snapshot_directory must be an authorized Snapshot artifact directory"
)


class SnapshotOutputRefused(Exception):
    """Raised when a publication target is not an authorized artifact path."""

    def __init__(self) -> None:
        super().__init__(SNAPSHOT_OUTPUT_REFUSED_DETAIL)
        self.detail = SNAPSHOT_OUTPUT_REFUSED_DETAIL


#: The two mode-specific Design section 10 output-directory grammars. Group
#: ``task`` must equal the ResolutionInput task ID; ``slug`` is a lowercase
#: hyphenated project slug.
_CHECKOUT_DIRECTORY = re.compile(
    r"^projects/(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)/handoffs/(?P<task>[^/]+)/snapshots$"
)
_INSTALLED_DIRECTORY = re.compile(
    r"^\.brichan/project-memory/techstack-snapshots/(?P<task>[^/]+)$"
)

#: The one artifact suffix. The stem is ``<attempt-id>-<snapshot_sha256>``.
ARTIFACT_SUFFIX = ".snapshot.json"

#: Directory mode for a created artifact ancestor and file mode for the
#: artifact itself, exactly as Design section 10 states.
ARTIFACT_DIRECTORY_MODE = 0o700
ARTIFACT_FILE_MODE = 0o600

#: The errnos that genuinely mean "this path is not an authorizable Snapshot
#: artifact target", which is what Design section 2's path/authority/collision
#: row names. Every other ``OSError`` — ``ENOSPC`` on a full volume, ``EIO`` on
#: a failing one — is a filesystem failure rather than a directory-authority
#: failure and must not claim the ``--snapshot-directory`` value is
#: unauthorized, so it reaches the sanitized internal-error line instead.
ARTIFACT_REFUSAL_ERRNOS = frozenset(
    {
        errno.EACCES,
        errno.EPERM,
        errno.EROFS,
        errno.ELOOP,
        errno.ENOTDIR,
        errno.EISDIR,
        errno.ENAMETOOLONG,
        errno.ENOENT,
        errno.EEXIST,
    }
)


def _artifact_os_error(error: OSError) -> BaseException:
    """Return the refusal for an authority errno, or the original I/O fault."""

    if error.errno in ARTIFACT_REFUSAL_ERRNOS:
        return SnapshotOutputRefused()
    return error


#: The bounded-observation outcomes that are filesystem failures rather than
#: directory-authority failures, mirrored from ``filesystem._ERRNO_OUTCOMES``.
ARTIFACT_IO_OUTCOMES = frozenset({"FILESYSTEM_IO_ERROR", "RESOURCE_LIMIT"})


def _artifact_observation_error(observed: filesystem.Observation) -> BaseException:
    """Return the refusal, or the I/O fault an ancestor observation carries.

    ``open_directory`` reports outcomes, not errnos. An I/O or resource-limit
    outcome on an existing ancestor is the same class ``_artifact_os_error``
    passes through, so it is rebuilt as the ``OSError`` it came from and routed
    through the same mapping; every other outcome stays the refusal.
    """

    if observed.code in ARTIFACT_IO_OUTCOMES:
        value = observed.errno_value
        if value is None or value < 0:
            value = errno.EIO
        return _artifact_os_error(OSError(value, os.strerror(value)))
    return SnapshotOutputRefused()


def _directory_text(snapshot_directory: Any) -> str:
    """Return the lexically valid normalized directory text, or refuse."""

    if not isinstance(snapshot_directory, PurePosixPath):
        raise SnapshotOutputRefused()
    value = str(snapshot_directory)
    if not is_normalized_relative_path(value):
        raise SnapshotOutputRefused()
    return value


def _validate_directory_authority(value: str, task_id: str) -> None:
    """Require one of the two mode-specific grammars with this task's ID."""

    match = _CHECKOUT_DIRECTORY.match(value) or _INSTALLED_DIRECTORY.match(value)
    if match is None or match.group("task") != task_id:
        raise SnapshotOutputRefused()


def _artifact_path(directory: str, snapshot: Snapshot) -> str:
    """Derive the one artifact path this Snapshot may occupy."""

    path = f"{directory}/{snapshot.attempt_id}-{snapshot.snapshot_sha256}{ARTIFACT_SUFFIX}"
    if unicodedata.normalize("NFC", path) != path:
        raise SnapshotOutputRefused()
    if len(path.encode("utf-8")) > RELATIVE_PATH_BYTE_MAX:
        raise SnapshotOutputRefused()
    if not is_normalized_relative_path(path):
        raise SnapshotOutputRefused()
    return path


def _open_artifact_parent(root_fd: int, directory: str) -> tuple[int, list[int]]:
    """Open every existing ancestor no-follow, creating only missing ones.

    Returns the parent descriptor and every descriptor the caller must close.
    Creation uses mode 0700 and is missing-only: an existing ancestor is opened
    and identity-checked, never replaced.
    """

    opened: list[int] = []
    parent = root_fd
    try:
        for component in directory.split("/"):
            descriptor, observed = filesystem.open_directory(parent, component)
            if descriptor is None:
                if observed.code != filesystem.OUTCOME_NOT_FOUND:
                    raise _artifact_observation_error(observed)
                try:
                    os.mkdir(component, ARTIFACT_DIRECTORY_MODE, dir_fd=parent)
                except OSError as error:
                    raise _artifact_os_error(error) from None
                descriptor, observed = filesystem.open_directory(parent, component)
                if descriptor is None:
                    raise _artifact_observation_error(observed)
            opened.append(descriptor)
            parent = descriptor
    except BaseException:
        for descriptor in reversed(opened):
            os.close(descriptor)
        raise
    return parent, opened


def _publish_document(parent_fd: int, name: str, document: str) -> str:
    """Create the one artifact entry, or accept identical existing bytes.

    Returns ``created`` or ``identical_existing``. No overwrite, truncate,
    rename, temporary file, or unlink is ever performed.
    """

    payload = document.encode("utf-8")
    if len(payload) > SNAPSHOT_DOCUMENT_BYTE_LIMIT:
        raise SnapshotOutputRefused()
    try:
        descriptor = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            ARTIFACT_FILE_MODE,
            dir_fd=parent_fd,
        )
    except FileExistsError:
        return _accept_identical_existing(parent_fd, name, payload)
    except OSError as error:
        raise _artifact_os_error(error) from None
    try:
        written = os.write(descriptor, payload)
        if written != len(payload):
            # A short write is a full or failing volume, never an authority
            # failure, so it carries the same errno the kernel would have.
            raise OSError(errno.EIO, "artifact write was short")
        os.fsync(descriptor)
    except OSError as error:
        raise _artifact_os_error(error) from None
    finally:
        os.close(descriptor)
    _require_identical_readback(parent_fd, name, payload)
    return "created"


def _accept_identical_existing(parent_fd: int, name: str, payload: bytes) -> str:
    """Accept an existing safe regular entry only when its bytes are identical."""

    _require_identical_readback(parent_fd, name, payload)
    return "identical_existing"


def _require_identical_readback(parent_fd: int, name: str, payload: bytes) -> None:
    """Reopen through the held parent and require identical bytes and type."""

    observation = filesystem.read_bounded_regular(
        parent_fd, name, SNAPSHOT_DOCUMENT_BYTE_LIMIT
    )
    if not observation.ok or observation.data != payload:
        raise SnapshotOutputRefused()
    if observation.identity is None or not stat.S_ISREG(observation.identity.mode):
        raise SnapshotOutputRefused()


def publish_snapshot(
    input: Any,  # noqa: A002 - frozen public parameter name
    project_root: Any,
    snapshot_directory: Any,
) -> SnapshotPublication:
    """Resolve, publish, and verify up to three times; never overwrite.

    Each attempt resolves once. A blocked or not-applicable resolution stops
    with no new artifact. An applicable resolution publishes its exact bytes by
    the missing-only no-follow protocol and then calls the production
    ``verify_snapshot`` on that same object. ``match`` selects the artifact and
    stops; ``drift`` or ``blocked`` leaves the immutable artifact in place and
    starts a fresh resolve. After three non-matching attempts the status is
    ``observation_drift`` and no artifact is packetable.
    """

    if not isinstance(input, ResolutionInput):
        raise root_api_error_for_code("INPUT_TYPE")
    directory = _directory_text(snapshot_directory)
    _validate_directory_authority(directory, input.task_id)

    attempts: list[SnapshotAttempt] = []
    resolution: Resolution | None = None
    for ordinal in range(1, PUBLICATION_ATTEMPT_MAX + 1):
        resolution = resolve_context(input, project_root)
        if resolution.status != "applicable":
            return _finished(
                "not_applicable" if resolution.status == "not_applicable" else "blocked",
                resolution,
                attempts,
            )
        snapshot = resolution.snapshot
        document = snapshot_document(snapshot)
        artifact_path = _artifact_path(directory, snapshot)
        # The publication cap is measured before any byte is published, so an
        # over-cap outcome writes no artifact at all.
        _require_publication_within_cap(resolution, attempts, ordinal, artifact_path, snapshot)
        publication = _publish_artifact(project_root, directory, artifact_path, document)
        verification = verify_snapshot(
            snapshot, project_root, datetime.date.fromisoformat(snapshot.as_of)
        )
        attempts.append(
            SnapshotAttempt(
                ordinal=ordinal,
                artifact_path=artifact_path,
                snapshot_sha256=snapshot.snapshot_sha256,
                publication=publication,
                verification_status=verification.status,
            )
        )
        if verification.status == "match":
            return _finished("published", resolution, attempts)
    return _finished("observation_drift", resolution, attempts)


def _publish_artifact(
    project_root: Any,
    directory: str,
    artifact_path: str,
    document: str,
) -> str:
    """Anchor the root again and publish the one artifact entry beneath it."""

    handle = filesystem.validate_and_open_git_root(project_root)
    opened: list[int] = []
    try:
        parent, opened = _open_artifact_parent(handle.fd, directory)
        return _publish_document(parent, artifact_path.rsplit("/", 1)[1], document)
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)
        handle.close()


def _require_publication_within_cap(
    resolution: Resolution,
    attempts: list[SnapshotAttempt],
    ordinal: int,
    artifact_path: str,
    snapshot: Snapshot,
) -> None:
    """Raise ``PUBLICATION_BYTE_LIMIT`` before this attempt writes anything."""

    prospective = SnapshotAttempt(
        ordinal=ordinal,
        artifact_path=artifact_path,
        snapshot_sha256=snapshot.snapshot_sha256,
        publication="created",
        verification_status="match",
    )
    publication_document(
        SnapshotPublication(
            schema_version=SCHEMA_VERSION,
            status="published",
            resolution=resolution,
            attempts=(*attempts, prospective),
            selected_artifact=artifact_path,
            selected_snapshot_sha256=snapshot.snapshot_sha256,
        )
    )


def _finished(
    status: str,
    resolution: Resolution,
    attempts: list[SnapshotAttempt],
) -> SnapshotPublication:
    """Build and byte-check the final publication."""

    selected = (None, None)
    if status == "published":
        selected = (attempts[-1].artifact_path, attempts[-1].snapshot_sha256)
    publication = SnapshotPublication(
        schema_version=SCHEMA_VERSION,
        status=status,
        resolution=resolution,
        attempts=tuple(attempts),
        selected_artifact=selected[0],
        selected_snapshot_sha256=selected[1],
    )
    publication_document(publication)
    return publication


# ---------------------------------------------------------------------------
# Exact CLI surface
# ---------------------------------------------------------------------------

PROGRAM = "brichan techstacks"

#: Every exit-2 stderr line, byte for byte from Design section 2. Nothing in
#: this table interpolates a token, a path, or an exception detail.
MISSING_SUBCOMMAND_LINE = (
    "brichan techstacks: MISSING_SUBCOMMAND: expected resolve or verify\n"
)
UNKNOWN_ARGUMENT_LINE = (
    "brichan techstacks: UNKNOWN_ARGUMENT: expected resolve or verify with "
    "named flags only\n"
)
UNKNOWN_FLAG_LINE = "brichan techstacks: UNKNOWN_ARGUMENT: unsupported option\n"
DUPLICATE_FLAG_LINE = (
    "brichan techstacks: DUPLICATE_ARGUMENT: each option may appear once\n"
)
MISSING_VALUE_LINE = "brichan techstacks: MISSING_VALUE: option requires one value\n"
RESOLVE_MISSING_ARGUMENT_LINE = (
    "brichan techstacks resolve: MISSING_ARGUMENT: --project-root and "
    "--input-json are required\n"
)
VERIFY_MISSING_ARGUMENT_LINE = (
    "brichan techstacks verify: MISSING_ARGUMENT: --project-root, "
    "--snapshot-json, and --as-of are required\n"
)
UNSUPPORTED_PLATFORM_LINE = (
    "brichan techstacks: UNSUPPORTED_PLATFORM: techstacks requires Linux or "
    "macOS POSIX safe-open primitives\n"
)
PROJECT_ROOT_INVALID_LINE = (
    "brichan techstacks: PROJECT_ROOT_INVALID: --project-root must name an "
    "absolute no-symlink top-level Git root\n"
)
INPUT_JSON_UNAVAILABLE_LINE = (
    "brichan techstacks resolve: INPUT_JSON_UNAVAILABLE: --input-json must "
    "name one stable regular project-relative file\n"
)
INPUT_JSON_BYTE_LIMIT_LINE = (
    "brichan techstacks resolve: INPUT_JSON_BYTE_LIMIT: input JSON exceeds "
    "131072 bytes\n"
)
INPUT_JSON_ENCODING_LINE = (
    "brichan techstacks resolve: INPUT_JSON_ENCODING: input JSON must be "
    "strict UTF-8 without BOM or NUL\n"
)
INPUT_JSON_SYNTAX_LINE = (
    "brichan techstacks resolve: INPUT_JSON_SYNTAX: input JSON must contain "
    "exactly one JSON object\n"
)
INPUT_JSON_DUPLICATE_KEY_LINE = (
    "brichan techstacks resolve: INPUT_JSON_DUPLICATE_KEY: duplicate JSON "
    "object key\n"
)
INVALID_INPUT_LINE = (
    "brichan techstacks resolve: INVALID_INPUT: input JSON violates "
    "ResolutionInput schema v1\n"
)
SNAPSHOT_OUTPUT_REFUSED_LINE = (
    "brichan techstacks resolve: SNAPSHOT_OUTPUT_REFUSED: "
    "--snapshot-directory must be an authorized Snapshot artifact directory\n"
)
SNAPSHOT_JSON_UNAVAILABLE_LINE = (
    "brichan techstacks verify: SNAPSHOT_JSON_UNAVAILABLE: --snapshot-json "
    "must name one stable regular project-relative file\n"
)
SNAPSHOT_JSON_BYTE_LIMIT_LINE = (
    "brichan techstacks verify: SNAPSHOT_JSON_BYTE_LIMIT: Snapshot JSON "
    "exceeds 131072 bytes\n"
)
SNAPSHOT_JSON_ENCODING_LINE = (
    "brichan techstacks verify: SNAPSHOT_JSON_ENCODING: Snapshot JSON must be "
    "strict UTF-8 without BOM or NUL\n"
)
SNAPSHOT_JSON_SYNTAX_LINE = (
    "brichan techstacks verify: SNAPSHOT_JSON_SYNTAX: Snapshot JSON must "
    "contain exactly one JSON object\n"
)
SNAPSHOT_JSON_DUPLICATE_KEY_LINE = (
    "brichan techstacks verify: SNAPSHOT_JSON_DUPLICATE_KEY: duplicate JSON "
    "object key\n"
)
INVALID_SNAPSHOT_LINE = (
    "brichan techstacks verify: INVALID_SNAPSHOT: Snapshot JSON violates "
    "schema v1 or its digest\n"
)
INVALID_AS_OF_LINE = (
    "brichan techstacks verify: INVALID_AS_OF: --as-of must equal Snapshot "
    "as_of in YYYY-MM-DD form\n"
)
INTERNAL_ERROR_LINE = "brichan techstacks: INTERNAL_ERROR: resolution failed\n"

#: The three frozen help documents, each ending in exactly one LF.
TOP_LEVEL_HELP = """usage: brichan techstacks {resolve,verify} ...

Resolve or verify bounded project-owned techstack context.

subcommands:
  resolve  resolve context and optionally publish a Snapshot artifact
  verify   verify a Snapshot artifact against the project
"""

RESOLVE_HELP = """usage: brichan techstacks resolve --project-root ABSOLUTE --input-json PROJECT_RELATIVE [--snapshot-directory PROJECT_RELATIVE]

options:
  --project-root ABSOLUTE
  --input-json PROJECT_RELATIVE
  --snapshot-directory PROJECT_RELATIVE
  -h, --help
"""

VERIFY_HELP = """usage: brichan techstacks verify --project-root ABSOLUTE --snapshot-json PROJECT_RELATIVE --as-of YYYY-MM-DD

options:
  --project-root ABSOLUTE
  --snapshot-json PROJECT_RELATIVE
  --as-of YYYY-MM-DD
  -h, --help
"""

SUBCOMMANDS = ("resolve", "verify")
HELP_VECTORS = (["--help"], ["-h"])
RESOLVE_FLAGS = ("--project-root", "--input-json", "--snapshot-directory")
VERIFY_FLAGS = ("--project-root", "--snapshot-json", "--as-of")
SUBCOMMAND_FLAGS = {"resolve": RESOLVE_FLAGS, "verify": VERIFY_FLAGS}
SUBCOMMAND_HELP = {"resolve": RESOLVE_HELP, "verify": VERIFY_HELP}
SUBCOMMAND_MISSING_ARGUMENT = {
    "resolve": RESOLVE_MISSING_ARGUMENT_LINE,
    "verify": VERIFY_MISSING_ARGUMENT_LINE,
}
REQUIRED_FLAGS = {
    "resolve": ("--project-root", "--input-json"),
    "verify": ("--project-root", "--snapshot-json", "--as-of"),
}

#: Exit codes. Design section 2 freezes 0/5 for valid outcomes, 2 for every
#: caller error, and 70 for an unexpected internal failure.
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NOT_MATCHED = 5
EXIT_INTERNAL = 70

#: JSON whitespace, the only bytes permitted after the one document.
JSON_WHITESPACE = " \t\n\r"

_AS_OF_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


class _Usage(Exception):
    """One exit-2 outcome carrying its already frozen stderr line."""

    def __init__(self, line: str) -> None:
        super().__init__(line)
        self.line = line


class _DuplicateKey(Exception):
    """Raised by the object-pairs hook for a duplicate key at any nesting level."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise _DuplicateKey(key)
        seen[key] = value
    return seen


def _parse_flags(subcommand: str, tokens: list[str]) -> dict[str, str]:
    """Apply the frozen argument precedence and return the named values.

    Positions are frozen: a known flag always consumes the next token as its
    value, so a value that begins with a dash is a value and never an option.
    """

    known = SUBCOMMAND_FLAGS[subcommand]
    values: dict[str, str] = {}
    positional = unknown = duplicate = missing_value = False
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if not token.startswith("-"):
            positional = True
            index += 1
            continue
        if token not in known:
            unknown = True
            index += 1
            continue
        if token in values:
            duplicate = True
        if index + 1 >= len(tokens):
            missing_value = True
            index += 1
            continue
        values[token] = tokens[index + 1]
        index += 2
    if positional:
        raise _Usage(UNKNOWN_ARGUMENT_LINE)
    if unknown:
        raise _Usage(UNKNOWN_FLAG_LINE)
    if duplicate:
        raise _Usage(DUPLICATE_FLAG_LINE)
    if missing_value:
        raise _Usage(MISSING_VALUE_LINE)
    if any(flag not in values for flag in REQUIRED_FLAGS[subcommand]):
        raise _Usage(SUBCOMMAND_MISSING_ARGUMENT[subcommand])
    return values


def _lexical_root(value: str) -> Path:
    """Validate the lexical root contract without touching the filesystem."""

    root = Path(value)
    try:
        filesystem.validate_root_argument(root)
    except TechstackError:
        raise _Usage(PROJECT_ROOT_INVALID_LINE) from None
    return root


def _lexical_relative(value: str, line: str) -> str:
    """Require a normalized project-relative POSIX path of 1-1,024 bytes."""

    if not is_normalized_relative_path(value):
        raise _Usage(line)
    return value


def _lexical_as_of(value: str) -> datetime.date:
    """Accept only an ASCII ten-byte ``YYYY-MM-DD`` that constructs a date."""

    if len(value) != 10 or not value.isascii() or not _AS_OF_PATTERN.match(value):
        raise _Usage(INVALID_AS_OF_LINE)
    try:
        return datetime.date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
    except ValueError:
        raise _Usage(INVALID_AS_OF_LINE) from None


def _lexical_output_directory(value: str) -> PurePosixPath:
    """Require one lexically normalized directory of a mode-specific shape."""

    if not is_normalized_relative_path(value):
        raise _Usage(SNAPSHOT_OUTPUT_REFUSED_LINE)
    if not (_CHECKOUT_DIRECTORY.match(value) or _INSTALLED_DIRECTORY.match(value)):
        raise _Usage(SNAPSHOT_OUTPUT_REFUSED_LINE)
    return PurePosixPath(value)


def _require_platform() -> None:
    """A complete model cannot be safely read on an unsupported platform."""

    if not filesystem.is_supported_platform():
        raise _Usage(UNSUPPORTED_PLATFORM_LINE)


def _anchor(root: Path) -> filesystem.RootHandle:
    try:
        return filesystem.validate_and_open_git_root(root)
    except TechstackError:
        raise _Usage(PROJECT_ROOT_INVALID_LINE) from None


def _root_api_usage(error: TechstackError) -> BaseException:
    """Return the frozen root line for a root-table row, or the original error.

    Each importable API anchors the root for itself, so a root that changes
    between the CLI's own anchor and the API's re-anchor raises there rather
    than in ``_anchor``. Design section 14 maps every row of the root/API
    outcome table to the already frozen sanitized line for the surface, so
    those rows become the same exit-2 line here. Anything outside that table —
    the publication byte cap, for one — stays an unexpected internal failure.
    """

    if error.code in ROOT_API_OUTCOMES_BY_CODE:
        return _Usage(PROJECT_ROOT_INVALID_LINE)
    return error


class _JsonLines:
    """The five frozen per-surface JSON failure lines."""

    def __init__(self, unavailable, byte_limit, encoding, syntax, duplicate_key, model_line):
        self.unavailable = unavailable
        self.byte_limit = byte_limit
        self.encoding = encoding
        self.syntax = syntax
        self.duplicate_key = duplicate_key
        self.model = model_line


INPUT_JSON_LINES = _JsonLines(
    INPUT_JSON_UNAVAILABLE_LINE,
    INPUT_JSON_BYTE_LIMIT_LINE,
    INPUT_JSON_ENCODING_LINE,
    INPUT_JSON_SYNTAX_LINE,
    INPUT_JSON_DUPLICATE_KEY_LINE,
    INVALID_INPUT_LINE,
)
SNAPSHOT_JSON_LINES = _JsonLines(
    SNAPSHOT_JSON_UNAVAILABLE_LINE,
    SNAPSHOT_JSON_BYTE_LIMIT_LINE,
    SNAPSHOT_JSON_ENCODING_LINE,
    SNAPSHOT_JSON_SYNTAX_LINE,
    SNAPSHOT_JSON_DUPLICATE_KEY_LINE,
    INVALID_SNAPSHOT_LINE,
)


def _read_anchored_json(root_fd: int, relative_path: str, lines: _JsonLines) -> dict:
    """Read, decode, and parse one anchored JSON document.

    The bounded reader accepts at most 131,073 bytes and reports the raw cap
    without parsing. The document must be exactly one JSON object with only
    JSON whitespace after it, and no duplicate key at any nesting level.
    """

    observation = read_project_file(root_fd, relative_path, CLI_JSON_BYTE_LIMIT)
    if observation.code == filesystem.OUTCOME_BYTE_LIMIT:
        raise _Usage(lines.byte_limit)
    if not observation.ok or observation.data is None:
        raise _Usage(lines.unavailable)
    payload = observation.data
    if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload:
        raise _Usage(lines.encoding)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        raise _Usage(lines.encoding) from None
    decoder = json.JSONDecoder(object_pairs_hook=_reject_duplicate_keys)
    try:
        value, end = decoder.raw_decode(text.lstrip(JSON_WHITESPACE))
    except _DuplicateKey:
        raise _Usage(lines.duplicate_key) from None
    except ValueError:
        raise _Usage(lines.syntax) from None
    remainder = text.lstrip(JSON_WHITESPACE)[end:]
    if not isinstance(value, dict) or remainder.strip(JSON_WHITESPACE):
        raise _Usage(lines.syntax)
    return value


def _resolve_command(values: dict[str, str]) -> tuple[str, int]:
    """Run one ``resolve`` invocation and return its stdout and exit code."""

    root = _lexical_root(values["--project-root"])
    relative = _lexical_relative(values["--input-json"], INPUT_JSON_UNAVAILABLE_LINE)
    directory = None
    if "--snapshot-directory" in values:
        directory = _lexical_output_directory(values["--snapshot-directory"])
    _require_platform()
    handle = _anchor(root)
    try:
        payload = _read_anchored_json(handle.fd, relative, INPUT_JSON_LINES)
    finally:
        handle.close()
    try:
        resolution_input = resolution_input_from_json_object(payload)
    except TechstackError:
        raise _Usage(INVALID_INPUT_LINE) from None

    if directory is None:
        try:
            resolution = resolve_context(resolution_input, root)
        except TechstackError as error:
            raise _root_api_usage(error) from None
        code = EXIT_NOT_MATCHED if resolution.status == "blocked" else EXIT_OK
        return canonical_json_document(resolution.to_json_object()), code
    try:
        publication = publish_snapshot(resolution_input, root, directory)
    except SnapshotOutputRefused:
        raise _Usage(SNAPSHOT_OUTPUT_REFUSED_LINE) from None
    except TechstackError as error:
        raise _root_api_usage(error) from None
    code = (
        EXIT_NOT_MATCHED
        if publication.status in ("blocked", "observation_drift")
        else EXIT_OK
    )
    return publication_document(publication), code


def _verify_command(values: dict[str, str]) -> tuple[str, int]:
    """Run one ``verify`` invocation and return its stdout and exit code."""

    root = _lexical_root(values["--project-root"])
    relative = _lexical_relative(values["--snapshot-json"], SNAPSHOT_JSON_UNAVAILABLE_LINE)
    as_of = _lexical_as_of(values["--as-of"])
    _require_platform()
    handle = _anchor(root)
    try:
        payload = _read_anchored_json(handle.fd, relative, SNAPSHOT_JSON_LINES)
    finally:
        handle.close()
    try:
        snapshot = snapshot_from_json_object(payload)
    except TechstackError:
        raise _Usage(INVALID_SNAPSHOT_LINE) from None
    if as_of.isoformat() != snapshot.as_of:
        raise _Usage(INVALID_AS_OF_LINE)
    try:
        verification = verify_snapshot(snapshot, root, as_of)
    except TechstackError as error:
        raise _root_api_usage(error) from None
    code = EXIT_OK if verification.status == "match" else EXIT_NOT_MATCHED
    return canonical_json_document(verification.to_json_object()), code


def _dispatch(argv: list[str]) -> tuple[str, int]:
    """Apply the frozen precedence and return the stdout bytes and exit code."""

    if argv in HELP_VECTORS:
        return TOP_LEVEL_HELP, EXIT_OK
    if not argv:
        raise _Usage(MISSING_SUBCOMMAND_LINE)
    subcommand = argv[0]
    if subcommand not in SUBCOMMANDS:
        raise _Usage(UNKNOWN_ARGUMENT_LINE)
    rest = argv[1:]
    if rest in HELP_VECTORS:
        return SUBCOMMAND_HELP[subcommand], EXIT_OK
    values = _parse_flags(subcommand, rest)
    if subcommand == "resolve":
        return _resolve_command(values)
    return _verify_command(values)


def main(argv: list[str] | None = None) -> int:
    """Run one ``brichan techstacks`` invocation over the process streams.

    Stdout is written only once the complete document exists, so no failure
    can leave a partial document behind. Nothing untrusted reaches a stream:
    every failure line is a frozen literal, and an unexpected exception
    becomes the one sanitized internal-error line. A user interrupt and an
    explicit exit are neither unexpected nor a failure of the resolution, so
    they propagate to the caller unchanged.
    """

    arguments = sys.argv[1:] if argv is None else list(argv)
    try:
        document, code = _dispatch(arguments)
    except _Usage as usage:
        sys.stderr.write(usage.line)
        return EXIT_USAGE
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        sys.stderr.write(INTERNAL_ERROR_LINE)
        return EXIT_INTERNAL
    sys.stdout.write(document)
    return code
