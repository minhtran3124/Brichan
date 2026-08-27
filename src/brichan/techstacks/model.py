"""Frozen techstack context records, registries, bounds, and canonical JSON.

This module is the single authority for every public techstack value: the two
ordered caller-error vectors, the closed 58-row Diagnostic registry, the
six-code Difference registry, the input/Snapshot/Verification/publication
records, canonical JSON, digests, byte caps, and the two replacement
overflow sentinels.

Nothing here touches the filesystem, a subprocess, a CLI, project memory, or an
evaluation corpus. Records validate themselves at construction, so an invalid
value never reaches a resolver, a digest, or an artifact.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence


# ---------------------------------------------------------------------------
# Schema versions, numeric caps, and fixed strings
# ---------------------------------------------------------------------------

#: Every public techstack document is schema version 1.
SCHEMA_VERSION = 1

#: The only Snapshot ``root_map`` value; it equals ``selected_files[0].path``.
SNAPSHOT_ROOT_MAP = "techstacks/README.md"

#: Design section 3 read and enumeration caps.
MAP_FILE_BYTE_LIMIT = 65536
LEAF_FILE_BYTE_LIMIT = 65536
SELECTED_FILE_LIMIT = 12
SELECTED_AGGREGATE_BYTE_LIMIT = 65536
MAP_DEPTH_LIMIT = 6
MAP_ROW_LIMIT = 32
MAP_ROW_SELECTOR_LIMIT = 16
EVIDENCE_FILE_BYTE_LIMIT = 1048576
EVIDENCE_FILE_COUNT_LIMIT = 64
EVIDENCE_AGGREGATE_BYTE_LIMIT = 8388608
MANAGED_SKILL_FILE_BYTE_LIMIT = 262144
EXPORTED_SKILL_FILE_BYTE_LIMIT = 262144
SKILL_ENTRY_LIMIT = 64
SKILL_DIRECTORY_LIMIT = 64
SKILL_DEPTH_LIMIT = 6
SKILL_AGGREGATE_BYTE_LIMIT = 4194304
CLI_JSON_BYTE_LIMIT = 131072

#: The one canonical Snapshot document cap, counting the terminal LF.
SNAPSHOT_DOCUMENT_BYTE_LIMIT = 131072

#: The separate canonical SnapshotPublication document cap, counting the
#: terminal LF. It is larger than the Snapshot cap because one publication
#: carries up to three attempt records plus the final Resolution.
PUBLICATION_DOCUMENT_BYTE_LIMIT = 262144

#: Replacement-sentinel thresholds. A 129th diagnostic or a 65th difference
#: discards the accumulated array instead of truncating it.
DIAGNOSTIC_COUNT_LIMIT = 128
DIFFERENCE_COUNT_LIMIT = 64
EFFECTIVE_RULE_COUNT_LIMIT = 384

#: Universal scalar bounds.
PROJECT_ROOT_BYTE_MIN = 1
PROJECT_ROOT_BYTE_MAX = 3072
PATH_COMPONENT_BYTE_MAX = 255
RELATIVE_PATH_BYTE_MAX = 1024
IDENTIFIER_BYTE_MAX = 64
FREE_TEXT_BYTE_MAX = 1024
ENUM_BYTE_MAX = 64
DETAIL_BYTE_MAX = 1024
PLAN_VERSION_MIN = 1
PLAN_VERSION_MAX = 9999
INTEGER_MAX = 9223372036854775807
MODE_MAX = 4294967295
SCOPE_PATH_COUNT_MAX = 64
CONTEXT_CHAIN_COUNT_MAX = 32
CONTEXT_CHAIN_LENGTH_MIN = 1
CONTEXT_CHAIN_LENGTH_MAX = 6
APPROVAL_COUNT_MAX = 64
CONFLICT_COUNT_MAX = 64
RECORD_CANONICAL_BYTE_MAX = 4096
INPUT_CANONICAL_BYTE_MAX = 131072
EVIDENCE_DECLARATION_MAX = 8
AUTHORIZED_BY_BYTE_MIN = 1
AUTHORIZED_BY_BYTE_MAX = 64
AUTHORIZATION_REFERENCE_BYTE_MIN = 0
AUTHORIZATION_REFERENCE_BYTE_MAX = 1024
PUBLICATION_ATTEMPT_MAX = 3

#: Closed enumerations.
RESOLUTION_STATUSES = ("applicable", "not_applicable", "blocked")
VERIFICATION_STATUSES = ("match", "drift", "blocked")
PUBLICATION_STATUSES = (
    "published",
    "not_applicable",
    "blocked",
    "observation_drift",
)
ATTEMPT_PUBLICATIONS = ("created", "identical_existing")
SELECTED_FILE_KINDS = ("map", "leaf")
SEVERITIES = ("error", "warning")
DIAGNOSTIC_FIELD_CLASSES = ("G", "P", "C", "T")

#: Selection-basis registry order; a stored basis is a unique subset in this
#: order, never an author-supplied order.
SELECTION_BASIS_ORDER = ("root", "dot", "scope", "context_chain")

#: The three waivable findings an exception approval may target.
WAIVABLE_CODES = ("STALE_RULE", "DEPRECATED_RULE", "MISSING_EVIDENCE")

#: The one waivable code whose approval requires an evidence path.
EVIDENCE_TARGET_CODE = "MISSING_EVIDENCE"


# ---------------------------------------------------------------------------
# Caller error classes and the two ordered code registries
# ---------------------------------------------------------------------------


class TechstackError(Exception):
    """Base class for the two closed caller-error registries.

    ``code``, ``field``, and ``detail`` are immutable strings. Caller errors are
    raised before a Resolution is constructed and never appear in diagnostics.
    """

    def __init__(self, code: str, field: str, detail: str) -> None:
        super().__init__(f"{code}: {field}: {detail}")
        object.__setattr__(self, "_code", str(code))
        object.__setattr__(self, "_field", str(field))
        object.__setattr__(self, "_detail", str(detail))

    @property
    def code(self) -> str:
        return self._code  # type: ignore[attr-defined]

    @property
    def field(self) -> str:
        return self._field  # type: ignore[attr-defined]

    @property
    def detail(self) -> str:
        return self._detail  # type: ignore[attr-defined]

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("TechstackError attributes are immutable")


class TechstackInputError(TechstackError):
    """Raised for a caller-supplied root or ResolutionInput violation."""


class TechstackSnapshotError(TechstackError):
    """Raised for a caller-supplied Snapshot, as-of, or publication violation."""


#: Design section 4 owns this ordering. It is exactly 23 codes; no section may
#: introduce a twenty-fourth.
INPUT_ERROR_CODES: tuple[str, ...] = (
    "PROJECT_ROOT_TYPE",
    "PROJECT_ROOT_BYTE_LIMIT",
    "PROJECT_ROOT_NOT_ABSOLUTE",
    "PROJECT_ROOT_NOT_CANONICAL",
    "PROJECT_ROOT_SYMLINK",
    "PROJECT_ROOT_NOT_DIRECTORY",
    "PROJECT_NOT_GIT_ROOT",
    "PROJECT_ROOT_UNREADABLE",
    "PROJECT_ROOT_IO_ERROR",
    "PROJECT_ROOT_RESOURCE_LIMIT",
    "PROJECT_ROOT_FILESYSTEM_ERROR",
    "PROJECT_ROOT_UNSUPPORTED_SAFE_OPEN",
    "PROJECT_ROOT_HELPER_TIMEOUT",
    "PROJECT_ROOT_HELPER_FAILED",
    "PROJECT_ROOT_HELPER_LEAK",
    "PROJECT_ROOT_HELPER_BUSY",
    "INPUT_UNKNOWN_KEY",
    "INPUT_MISSING_KEY",
    "INPUT_TYPE",
    "INPUT_VALUE",
    "INPUT_BYTE_LIMIT",
    "INPUT_COUNT_LIMIT",
    "INPUT_DUPLICATE",
)

#: Design section 4 owns this ordering. It is exactly 11 codes; no section may
#: introduce a twelfth.
SNAPSHOT_ERROR_CODES: tuple[str, ...] = (
    "SNAPSHOT_UNKNOWN_KEY",
    "SNAPSHOT_MISSING_KEY",
    "SNAPSHOT_TYPE",
    "SNAPSHOT_VALUE",
    "SNAPSHOT_BYTE_LIMIT",
    "SNAPSHOT_COUNT_LIMIT",
    "SNAPSHOT_DUPLICATE",
    "SNAPSHOT_DIGEST_MISMATCH",
    "SNAPSHOT_AS_OF_TYPE",
    "SNAPSHOT_AS_OF_MISMATCH",
    "PUBLICATION_BYTE_LIMIT",
)

#: Design section 14 fixed details for every model error not enumerated in the
#: root/API outcome table below.
FIXED_DETAILS: Mapping[str, str] = {
    "INPUT_UNKNOWN_KEY": "input contains an unknown key",
    "INPUT_MISSING_KEY": "input is missing a required key",
    "INPUT_TYPE": "input field has the wrong JSON type",
    "INPUT_VALUE": "input field has an invalid value",
    "INPUT_BYTE_LIMIT": "input field exceeds its byte limit",
    "INPUT_COUNT_LIMIT": "input collection exceeds its count limit",
    "INPUT_DUPLICATE": "input contains a duplicate record",
    "SNAPSHOT_UNKNOWN_KEY": "Snapshot contains an unknown key",
    "SNAPSHOT_MISSING_KEY": "Snapshot is missing a required key",
    "SNAPSHOT_TYPE": "Snapshot field has the wrong JSON type",
    "SNAPSHOT_VALUE": "Snapshot field has an invalid value",
    "SNAPSHOT_BYTE_LIMIT": (
        "Snapshot document exceeds 131072 bytes including terminal LF"
    ),
    "SNAPSHOT_COUNT_LIMIT": "Snapshot collection exceeds its count limit",
    "SNAPSHOT_DUPLICATE": "Snapshot contains a duplicate record",
    "SNAPSHOT_DIGEST_MISMATCH": "Snapshot digest does not match canonical content",
    "PUBLICATION_BYTE_LIMIT": "Snapshot publication exceeds 262144 bytes",
}


@dataclass(frozen=True)
class RootApiOutcome:
    """One Design section 14 root/API outcome row."""

    condition: str
    error_class: type
    code: str
    field: str
    detail: str


#: The Design section 14 root/API outcome table, in table order. Each row fixes
#: one exact class, code, field, and detail. ``PROJECT_ROOT_FILESYSTEM_ERROR``
#: carries the single bounded decimal-errno slot.
ROOT_API_OUTCOMES: tuple[RootApiOutcome, ...] = (
    RootApiOutcome(
        "resolve_context input is not ResolutionInput",
        TechstackInputError,
        "INPUT_TYPE",
        "",
        "input must be a ResolutionInput",
    ),
    RootApiOutcome(
        "project_root is not pathlib.Path or os.fspath is not str",
        TechstackInputError,
        "PROJECT_ROOT_TYPE",
        "project_root",
        "project_root must be a pathlib.Path",
    ),
    RootApiOutcome(
        "absolute root UTF-8 length outside 1-3072",
        TechstackInputError,
        "PROJECT_ROOT_BYTE_LIMIT",
        "project_root",
        "project_root must contain 1 to 3072 UTF-8 bytes",
    ),
    RootApiOutcome(
        "root is not absolute",
        TechstackInputError,
        "PROJECT_ROOT_NOT_ABSOLUTE",
        "project_root",
        "project_root must be absolute",
    ),
    RootApiOutcome(
        "non-NFC, NUL, ~, ., .., empty interior, terminal slash, component >255",
        TechstackInputError,
        "PROJECT_ROOT_NOT_CANONICAL",
        "project_root",
        "project_root must be canonical NFC without unsafe components",
    ),
    RootApiOutcome(
        "no-follow root/ancestor/.git reports link",
        TechstackInputError,
        "PROJECT_ROOT_SYMLINK",
        "project_root",
        "project_root and .git must not contain symlinks",
    ),
    RootApiOutcome(
        "root/ancestor is not a directory",
        TechstackInputError,
        "PROJECT_ROOT_NOT_DIRECTORY",
        "project_root",
        "project_root components must be directories",
    ),
    RootApiOutcome(
        "literal .git missing or neither regular file nor directory",
        TechstackInputError,
        "PROJECT_NOT_GIT_ROOT",
        "project_root",
        "project_root must be a top-level Git root",
    ),
    RootApiOutcome(
        "root walk/.git EACCES or EPERM",
        TechstackInputError,
        "PROJECT_ROOT_UNREADABLE",
        "project_root",
        "project_root could not be read",
    ),
    RootApiOutcome(
        "root walk/.git ESTALE or EIO",
        TechstackInputError,
        "PROJECT_ROOT_IO_ERROR",
        "project_root",
        "project_root filesystem I/O failed",
    ),
    RootApiOutcome(
        "root walk/.git EMFILE, ENFILE, or ENOMEM",
        TechstackInputError,
        "PROJECT_ROOT_RESOURCE_LIMIT",
        "project_root",
        "project_root inspection exceeded a process resource",
    ),
    RootApiOutcome(
        "root walk/.git rejects required no-follow/directory flags",
        TechstackInputError,
        "PROJECT_ROOT_UNSUPPORTED_SAFE_OPEN",
        "project_root",
        "project_root safe-open semantics are unavailable",
    ),
    RootApiOutcome(
        "regular .git helper times out",
        TechstackInputError,
        "PROJECT_ROOT_HELPER_TIMEOUT",
        "project_root",
        "project_root safe-open helper timed out",
    ),
    RootApiOutcome(
        "regular .git helper/protocol fails",
        TechstackInputError,
        "PROJECT_ROOT_HELPER_FAILED",
        "project_root",
        "project_root safe-open helper failed",
    ),
    RootApiOutcome(
        "regular .git helper remains unreaped",
        TechstackInputError,
        "PROJECT_ROOT_HELPER_LEAK",
        "project_root",
        "project_root safe-open helper could not be reaped",
    ),
    RootApiOutcome(
        "regular .git helper refused because the controller is reserved,"
        " active, terminating, or killing",
        TechstackInputError,
        "PROJECT_ROOT_HELPER_BUSY",
        "project_root",
        "project_root safe-open helper is busy",
    ),
    RootApiOutcome(
        "other root walk/.git OSError",
        TechstackInputError,
        "PROJECT_ROOT_FILESYSTEM_ERROR",
        "project_root",
        "project root filesystem operation failed with errno <decimal-or--1>",
    ),
    RootApiOutcome(
        "verify_snapshot snapshot is not Snapshot",
        TechstackSnapshotError,
        "SNAPSHOT_TYPE",
        "",
        "snapshot must be a Snapshot",
    ),
    RootApiOutcome(
        "as_of is not exact datetime.date",
        TechstackSnapshotError,
        "SNAPSHOT_AS_OF_TYPE",
        "/as_of",
        "as_of must be a datetime.date",
    ),
    RootApiOutcome(
        "supplied as_of differs from Snapshot date",
        TechstackSnapshotError,
        "SNAPSHOT_AS_OF_MISMATCH",
        "/as_of",
        "as_of must equal Snapshot as_of",
    ),
)

#: ``condition`` keyed view of the table above, for production call sites.
ROOT_API_OUTCOMES_BY_CONDITION: Mapping[str, RootApiOutcome] = {
    outcome.condition: outcome for outcome in ROOT_API_OUTCOMES
}


#: ``code`` keyed view of the same table; every root/API code is unique.
ROOT_API_OUTCOMES_BY_CODE: Mapping[str, RootApiOutcome] = {
    outcome.code: outcome for outcome in ROOT_API_OUTCOMES
}


def root_api_error_for_code(
    code: str, *, errno_value: int | None = None
) -> TechstackError:
    """Return the exact Design section 14 error for one root/API code."""

    outcome = ROOT_API_OUTCOMES_BY_CODE[code]
    detail = outcome.detail
    if code == "PROJECT_ROOT_FILESYSTEM_ERROR":
        detail = project_root_filesystem_error_detail(errno_value)
    return outcome.error_class(code, outcome.field, detail)


def root_api_error(condition: str, *, errno_value: int | None = None) -> TechstackError:
    """Return the exact Design section 14 error for one root/API condition."""

    outcome = ROOT_API_OUTCOMES_BY_CONDITION[condition]
    detail = outcome.detail
    if outcome.code == "PROJECT_ROOT_FILESYSTEM_ERROR":
        detail = project_root_filesystem_error_detail(errno_value)
    return outcome.error_class(outcome.code, outcome.field, detail)


def project_root_filesystem_error_detail(errno_value: int | None) -> str:
    """Fill the one bounded decimal-errno slot of the root filesystem detail."""

    decimal = "-1" if errno_value is None else str(int(errno_value))
    return f"project root filesystem operation failed with errno {decimal}"


# ---------------------------------------------------------------------------
# Closed Diagnostic registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiagnosticSpec:
    """One closed Diagnostic registry row; ``rank`` is the canonical sort rank."""

    rank: int
    code: str
    fields: str
    severity: str
    waivable: bool
    detail: str


DIAGNOSTIC_REGISTRY: tuple[DiagnosticSpec, ...] = (
    DiagnosticSpec(1, "UNSUPPORTED_PLATFORM", "G", "error", False, "techstacks is unsupported on this platform"),
    DiagnosticSpec(2, "UNSUPPORTED_SAFE_OPEN", "G", "error", False, "required safe-open semantics are unavailable"),
    DiagnosticSpec(3, "ROOT_CHANGED", "G", "error", False, "project root identity changed during resolution"),
    DiagnosticSpec(4, "PATH_COMPONENT_NOT_DIRECTORY", "P", "error", False, "an intermediate path component is not a directory"),
    DiagnosticSpec(5, "SYMLINK_REJECTED", "P", "error", False, "a symbolic link is not permitted"),
    DiagnosticSpec(6, "DIRECTORY_REJECTED", "P", "error", False, "a regular file was required but a directory was observed"),
    DiagnosticSpec(7, "FIFO_REJECTED", "P", "error", False, "a FIFO is not permitted"),
    DiagnosticSpec(8, "SOCKET_REJECTED", "P", "error", False, "a socket is not permitted"),
    DiagnosticSpec(9, "DEVICE_REJECTED", "P", "error", False, "a device is not permitted"),
    DiagnosticSpec(10, "NON_REGULAR_REJECTED", "P", "error", False, "an unsupported nonregular entry was observed"),
    DiagnosticSpec(11, "UNREADABLE_FILE", "P", "error", False, "a required file could not be read"),
    DiagnosticSpec(12, "SPECIAL_FILE_UNAVAILABLE", "P", "error", False, "a special entry could not be safely inspected"),
    DiagnosticSpec(13, "FILESYSTEM_IO_ERROR", "P", "error", False, "filesystem I/O failed"),
    DiagnosticSpec(14, "FILESYSTEM_ERROR", "P", "error", False, "filesystem operation failed with errno <decimal-or--1>"),
    DiagnosticSpec(15, "RESOURCE_LIMIT", "G", "error", False, "a process filesystem resource was exhausted"),
    DiagnosticSpec(16, "FILE_CHANGED", "P", "error", False, "file identity or content changed during observation"),
    DiagnosticSpec(17, "OS_METADATA_RANGE", "P", "error", False, "filesystem metadata is outside the supported integer range"),
    DiagnosticSpec(18, "MISSING_RULE_FILE", "P", "error", False, "a selected rule file is missing"),
    DiagnosticSpec(19, "MAP_BYTE_LIMIT", "P", "error", False, "map file exceeds 65536 bytes"),
    DiagnosticSpec(20, "LEAF_BYTE_LIMIT", "P", "error", False, "leaf file exceeds 65536 bytes"),
    DiagnosticSpec(21, "EVIDENCE_BYTE_LIMIT", "C", "error", False, "evidence file exceeds 1048576 bytes"),
    DiagnosticSpec(22, "EVIDENCE_FILE_LIMIT", "G", "error", False, "evidence file count exceeds 64"),
    DiagnosticSpec(23, "EVIDENCE_AGGREGATE_BYTE_LIMIT", "G", "error", False, "evidence bytes exceed 8388608"),
    DiagnosticSpec(24, "INVALID_MAP", "P", "error", False, "map bytes do not match the map grammar"),
    DiagnosticSpec(25, "INVALID_LEAF", "P", "error", False, "leaf bytes do not match the leaf grammar at line <decimal-or-0>: <leaf-rule>"),
    DiagnosticSpec(26, "MAP_ROW_LIMIT", "P", "error", False, "map row count exceeds 32"),
    DiagnosticSpec(27, "SELECTOR_LIMIT", "C", "error", False, "map row selector count exceeds 16"),
    DiagnosticSpec(28, "MAP_DEPTH_LIMIT", "G", "error", False, "selected map depth exceeds 6"),
    DiagnosticSpec(29, "SELECTED_FILE_LIMIT", "G", "error", False, "selected file count exceeds 12"),
    DiagnosticSpec(30, "SELECTED_BYTE_LIMIT", "G", "error", False, "selected map and leaf bytes exceed 65536"),
    DiagnosticSpec(31, "DUPLICATE_CONTEXT_ID", "C", "error", False, "a Context ID occurs more than once"),
    DiagnosticSpec(32, "ROW_CHILD_ID_MISMATCH", "C", "error", False, "map row and child Context IDs differ"),
    DiagnosticSpec(33, "DUPLICATE_RULE_PATH", "C", "error", False, "a selected rule path occurs more than once"),
    DiagnosticSpec(34, "CONTEXT_CYCLE", "C", "error", False, "selected map graph contains a cycle"),
    DiagnosticSpec(35, "UNREACHABLE_CONTEXT", "G", "error", False, "requested Context ID chain is not exactly reachable"),
    DiagnosticSpec(36, "EFFECTIVE_RULE_LIMIT", "G", "error", False, "effective rule count exceeds 384"),
    DiagnosticSpec(37, "PEER_RULE_CONFLICT", "C", "error", False, "overlapping peer rules use the same Rule ID"),
    DiagnosticSpec(38, "NON_NEAREST_OVERRIDE", "C", "error", False, "override does not name the nearest authority context"),
    DiagnosticSpec(39, "INVALID_OVERRIDE", "C", "error", False, "override target or Rule ID is invalid"),
    DiagnosticSpec(40, "DECLARED_AUTHORITY_CONFLICT", "G", "error", False, "declared conflict prevents deterministic authority"),
    DiagnosticSpec(41, "FUTURE_REVIEW_DATE", "C", "error", False, "rule review date is after as_of"),
    DiagnosticSpec(42, "STALE_RULE", "C", "error", True, "rule review interval has expired"),
    DiagnosticSpec(43, "DEPRECATED_RULE", "C", "error", True, "selected rule is deprecated"),
    DiagnosticSpec(44, "MISSING_EVIDENCE", "T", "error", True, "declared evidence is missing"),
    DiagnosticSpec(45, "UNATTESTED_EXCEPTION", "T", "error", False, "exception approval is not coordinator-attested"),
    DiagnosticSpec(46, "INVALID_EXCEPTION_PROVENANCE", "T", "error", False, "exception approval provenance is invalid"),
    DiagnosticSpec(47, "EXCEPTION_BINDING_MISMATCH", "T", "error", False, "exception approval binding does not match this attempt"),
    DiagnosticSpec(48, "EXCEPTION_EXPIRED", "T", "error", False, "exception approval is not valid on as_of"),
    DiagnosticSpec(49, "EXCEPTION_DIGEST_MISMATCH", "T", "error", False, "exception approval digest is invalid"),
    DiagnosticSpec(50, "UNUSED_EXCEPTION", "T", "error", False, "exception approval matched no finding"),
    DiagnosticSpec(51, "AMBIGUOUS_EXCEPTION", "T", "error", False, "exception approval matched multiple findings"),
    DiagnosticSpec(52, "UNUSED_INPUT_WITHOUT_ROOT", "G", "error", False, "conflict or exception input exists without root map"),
    DiagnosticSpec(53, "SNAPSHOT_BYTE_LIMIT", "G", "error", False, "Snapshot document exceeds 131072 bytes including terminal LF"),
    DiagnosticSpec(54, "DIAGNOSTIC_LIMIT", "G", "error", False, "diagnostic count exceeded 128; individual diagnostics suppressed"),
    DiagnosticSpec(55, "SAFE_OPEN_HELPER_TIMEOUT", "P", "error", False, "bounded safe-open helper timed out"),
    DiagnosticSpec(56, "SAFE_OPEN_HELPER_FAILED", "P", "error", False, "bounded safe-open helper failed"),
    DiagnosticSpec(57, "SAFE_OPEN_HELPER_LEAK", "P", "error", False, "bounded safe-open helper could not be reaped"),
    DiagnosticSpec(58, "SAFE_OPEN_HELPER_BUSY", "P", "error", False, "another bounded safe-open helper is active"),
)

DIAGNOSTIC_CODES: tuple[str, ...] = tuple(spec.code for spec in DIAGNOSTIC_REGISTRY)
DIAGNOSTIC_SPECS: Mapping[str, DiagnosticSpec] = {
    spec.code: spec for spec in DIAGNOSTIC_REGISTRY
}

#: The four bounded-helper codes emitted only by the section 3 helper branches.
HELPER_DIAGNOSTIC_CODES = (
    "SAFE_OPEN_HELPER_TIMEOUT",
    "SAFE_OPEN_HELPER_FAILED",
    "SAFE_OPEN_HELPER_LEAK",
    "SAFE_OPEN_HELPER_BUSY",
)


#: The closed leaf-grammar rule registry. One member names the violated rule
#: of every leaf-reachable failure site of :mod:`brichan.techstacks.markdown`,
#: which imports this tuple and spells its members as literals at those sites,
#: so the registry is single-sourced and a test asserts every site literal is
#: a member. Members are uppercase ASCII identifiers of at most 32 bytes.
LEAF_GRAMMAR_RULES: tuple[str, ...] = (
    "DOCUMENT_ENCODING",
    "DOCUMENT_LINE_ENDING",
    "DOCUMENT_TERMINAL_LF",
    "LINE_SHAPE",
    "TITLE",
    "SECTION_BOUNDARY",
    "TRAILING_CONTENT",
    "METADATA_CONTEXT_ID",
    "METADATA_REVIEWED_ON",
    "METADATA_REVIEW_WITHIN_DAYS",
    "METADATA_DEPRECATED",
    "METADATA_EVIDENCE",
    "SCOPE_BULLET",
    "RULE_BULLET",
    "OVERRIDE_BULLET",
    "VERIFICATION_BULLET",
    "EXCEPTION_BULLET",
    "EXAMPLES_LABEL",
    "EXAMPLES_FENCE",
    "EXAMPLES_PAYLOAD",
)

#: The one literal prefix of the two-slot ``INVALID_LEAF`` detail. The reported
#: line is 0 for a document-level failure and otherwise a 1-based index into
#: the normalized line array, whose length the leaf byte cap bounds, so the
#: largest reportable line is one past that cap's line count.
INVALID_LEAF_DETAIL_PREFIX = "leaf bytes do not match the leaf grammar at line "


def filesystem_error_detail(errno_value: int | None) -> str:
    """Fill the one bounded decimal-errno slot of ``FILESYSTEM_ERROR``."""

    decimal = "-1" if errno_value is None else str(int(errno_value))
    return f"filesystem operation failed with errno {decimal}"


def invalid_leaf_detail(line: int | None, rule: str | None) -> str:
    """Fill the bounded line and violated-rule slots of ``INVALID_LEAF``.

    Both slots are required: an unattributed leaf failure cannot be rendered,
    so a parser site that forgets its rule fails loudly here instead of
    producing a diagnostic that names no rule.
    """

    if line is None or rule is None:
        raise ValueError("INVALID_LEAF requires a line and a leaf grammar rule")
    if isinstance(line, bool) or not isinstance(line, int):
        raise ValueError("INVALID_LEAF line must be an integer")
    if not 0 <= line <= LEAF_FILE_BYTE_LIMIT + 1:
        raise ValueError("INVALID_LEAF line is outside its bounds")
    if rule not in LEAF_GRAMMAR_RULES:
        raise ValueError(f"unknown leaf grammar rule: {rule!r}")
    return f"{INVALID_LEAF_DETAIL_PREFIX}{line}: {rule}"


def diagnostic_detail(
    code: str,
    *,
    errno_value: int | None = None,
    line: int | None = None,
    rule: str | None = None,
) -> str:
    """Return the literal registry detail for one diagnostic code."""

    if code == "FILESYSTEM_ERROR":
        return filesystem_error_detail(errno_value)
    if code == "INVALID_LEAF":
        return invalid_leaf_detail(line, rule)
    return DIAGNOSTIC_SPECS[code].detail


# ---------------------------------------------------------------------------
# Closed Difference registry
# ---------------------------------------------------------------------------

#: The closed Difference code order; index is the canonical sort rank.
DIFFERENCE_CODES: tuple[str, ...] = (
    "OBSERVED_NOT_APPLICABLE",
    "OBSERVED_BLOCKED",
    "VALUE_MISMATCH",
    "MISSING_RECORD",
    "EXTRA_RECORD",
    "DIFFERENCE_LIMIT",
)
DIFFERENCE_RANKS: Mapping[str, int] = {
    code: index for index, code in enumerate(DIFFERENCE_CODES)
}

#: Representation cap for a Difference ``expected``/``actual`` value.
DIFFERENCE_REPRESENTATION_BYTE_MAX = 1024


# ---------------------------------------------------------------------------
# Canonical JSON and digests
# ---------------------------------------------------------------------------


def canonical_json_text(value: Any) -> str:
    """Return canonical JSON text without the terminal LF."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        separators=(",", ": "),
    )


def canonical_json_document(value: Any) -> str:
    """Return canonical JSON text with exactly one terminal LF."""

    return canonical_json_text(value) + "\n"


def canonical_json_bytes(value: Any) -> bytes:
    """Return canonical JSON bytes without the terminal LF."""

    return canonical_json_text(value).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Return the lowercase hex SHA-256 of ``data``."""

    return hashlib.sha256(data).hexdigest()


#: The digest placeholder that replaces ``snapshot_sha256`` while hashing.
DIGEST_PLACEHOLDER = "0" * 64


def snapshot_digest(snapshot_object: Mapping[str, Any]) -> str:
    """Hash canonical Snapshot bytes with ``snapshot_sha256`` zeroed."""

    hashable = dict(snapshot_object)
    hashable["snapshot_sha256"] = DIGEST_PLACEHOLDER
    return sha256_hex(canonical_json_bytes(hashable))


# ---------------------------------------------------------------------------
# Scalar grammar
# ---------------------------------------------------------------------------

_CONTEXT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_TASK_OR_PLAN_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
_ATTEMPT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_RULE_ID_PATTERN = _TASK_OR_PLAN_ID_PATTERN
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$", re.ASCII)

#: The reserved Context ID of the root map row.
ROOT_CONTEXT_ID = "root"


def _is_int(value: Any) -> bool:
    """Return True for a real integer; a bool is never an integer here."""

    return isinstance(value, int) and not isinstance(value, bool)


def _byte_length(value: str) -> int:
    return len(value.encode("utf-8"))


def is_nfc(value: str) -> bool:
    return unicodedata.normalize("NFC", value) == value


def is_context_id(value: Any, *, allow_root: bool = False) -> bool:
    if not isinstance(value, str) or not value.isascii():
        return False
    if not 1 <= len(value) <= IDENTIFIER_BYTE_MAX:
        return False
    if value == ROOT_CONTEXT_ID:
        return allow_root
    return bool(_CONTEXT_ID_PATTERN.match(value))


def is_task_or_plan_id(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.isascii()
        and 1 <= len(value) <= IDENTIFIER_BYTE_MAX
        and bool(_TASK_OR_PLAN_ID_PATTERN.match(value))
    )


def is_attempt_id(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.isascii()
        and 1 <= len(value) <= IDENTIFIER_BYTE_MAX
        and bool(_ATTEMPT_ID_PATTERN.match(value))
    )


def is_rule_id(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.isascii()
        and 1 <= len(value) <= IDENTIFIER_BYTE_MAX
        and bool(_RULE_ID_PATTERN.match(value))
    )


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_PATTERN.match(value))


def is_date(value: Any) -> bool:
    """Return True for a real Gregorian ``YYYY-MM-DD`` calendar date."""

    if not isinstance(value, str) or not _DATE_PATTERN.match(value):
        return False
    try:
        datetime.date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
    except ValueError:
        return False
    return True


def is_normalized_relative_path(value: Any) -> bool:
    """Return True for a normalized project-relative POSIX path."""

    if not isinstance(value, str) or not value:
        return False
    if _byte_length(value) > RELATIVE_PATH_BYTE_MAX or not is_nfc(value):
        return False
    if "\x00" in value or "\\" in value or "~" in value:
        return False
    if value.startswith("/") or value.endswith("/") or "//" in value:
        return False
    for component in value.split("/"):
        if not component or component in (".", ".."):
            return False
        if _byte_length(component) > PATH_COMPONENT_BYTE_MAX:
            return False
    return True


def is_selector(value: Any) -> bool:
    """Return True for dot, an exact normalized path, or a prefix selector.

    A prefix selector is a normalized relative path plus exactly one terminal
    slash, exactly as the retained version-3 selector algebra states. The
    terminal slash counts toward the 1,024-byte bound.
    ``is_normalized_relative_path`` itself stays strict, because Design
    section 14's canonical ``project_root`` rule relies on it rejecting a
    terminal slash.
    """

    if value == ".":
        return True
    if isinstance(value, str) and value.endswith("/"):
        return (
            _byte_length(value) <= RELATIVE_PATH_BYTE_MAX
            and is_normalized_relative_path(value[:-1])
        )
    return is_normalized_relative_path(value)


def is_free_text(value: Any, *, minimum: int = 1, maximum: int = FREE_TEXT_BYTE_MAX) -> bool:
    if not isinstance(value, str) or not is_nfc(value):
        return False
    if "\x00" in value:
        return False
    return minimum <= _byte_length(value) <= maximum


def is_general_integer(value: Any) -> bool:
    return _is_int(value) and 0 <= value <= INTEGER_MAX


# ---------------------------------------------------------------------------
# Validation plumbing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Context:
    """Error class and code prefix for one validation surface."""

    error_class: type
    prefix: str


_INPUT_CONTEXT = _Context(TechstackInputError, "INPUT")
_SNAPSHOT_CONTEXT = _Context(TechstackSnapshotError, "SNAPSHOT")


class _Problems:
    """Collect ``(pointer, code suffix)`` violations for one validation run."""

    def __init__(self, context: _Context) -> None:
        self._context = context
        self._items: list[tuple[str, str]] = []

    def add(self, pointer: str, suffix: str) -> None:
        self._items.append((pointer, suffix))

    def __bool__(self) -> bool:
        return bool(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def raise_first(self) -> None:
        """Raise the violation whose pointer sorts first in UTF-8 byte order."""

        if not self._items:
            return
        pointer, suffix = min(self._items, key=lambda item: item[0].encode("utf-8"))
        code = f"{self._context.prefix}_{suffix}"
        raise self._context.error_class(code, pointer, FIXED_DETAILS[code])


def _pointer(prefix: str, segment: str | int) -> str:
    if isinstance(segment, int):
        return f"{prefix}/{segment}"
    escaped = str(segment).replace("~", "~0").replace("/", "~1")
    return f"{prefix}/{escaped}"


def _as_json(value: Any) -> Any:
    """Return the JSON view of a record, sequence, or scalar."""

    to_json = getattr(value, "to_json_object", None)
    if callable(to_json):
        return to_json()
    if isinstance(value, (list, tuple)):
        return [_as_json(item) for item in value]
    return value


def _check_keys(
    value: Any,
    pointer: str,
    keys: Sequence[str],
    problems: _Problems,
) -> bool:
    """Check that ``value`` is an object with exactly ``keys``."""

    if not isinstance(value, Mapping):
        problems.add(pointer, "TYPE")
        return False
    unknown = sorted(set(value) - set(keys))
    missing = sorted(set(keys) - set(value))
    for key in unknown:
        problems.add(_pointer(pointer, key), "UNKNOWN_KEY")
    for key in missing:
        problems.add(_pointer(pointer, key), "MISSING_KEY")
    return not unknown and not missing


def _check_string(
    value: Any,
    pointer: str,
    predicate: Callable[[Any], bool],
    problems: _Problems,
    *,
    byte_maximum: int | None = None,
) -> bool:
    if not isinstance(value, str):
        problems.add(pointer, "TYPE")
        return False
    if byte_maximum is not None and _byte_length(value) > byte_maximum:
        problems.add(pointer, "BYTE_LIMIT")
        return False
    if not predicate(value):
        problems.add(pointer, "VALUE")
        return False
    return True


def _check_list(
    value: Any,
    pointer: str,
    problems: _Problems,
    *,
    maximum: int,
    minimum: int = 0,
) -> bool:
    if not isinstance(value, list):
        problems.add(pointer, "TYPE")
        return False
    if len(value) > maximum or len(value) < minimum:
        problems.add(pointer, "COUNT_LIMIT")
        return False
    return True


def _check_integer(
    value: Any,
    pointer: str,
    problems: _Problems,
    *,
    minimum: int,
    maximum: int,
) -> bool:
    if not _is_int(value):
        problems.add(pointer, "TYPE")
        return False
    if not minimum <= value <= maximum:
        problems.add(pointer, "VALUE")
        return False
    return True


def _check_bool(value: Any, pointer: str, problems: _Problems) -> bool:
    if not isinstance(value, bool):
        problems.add(pointer, "TYPE")
        return False
    return True


def _check_enum(
    value: Any,
    pointer: str,
    allowed: Sequence[str],
    problems: _Problems,
) -> bool:
    if not isinstance(value, str):
        problems.add(pointer, "TYPE")
        return False
    if _byte_length(value) > ENUM_BYTE_MAX:
        problems.add(pointer, "BYTE_LIMIT")
        return False
    if value not in allowed:
        problems.add(pointer, "VALUE")
        return False
    return True


# ---------------------------------------------------------------------------
# Canonical ordering helpers
# ---------------------------------------------------------------------------


def _utf8(value: str) -> bytes:
    return value.encode("utf-8")


def canonical_scope_paths(paths: Sequence[str]) -> tuple[str, ...]:
    """Deduplicate then sort scope paths by UTF-8 bytes."""

    return tuple(sorted(set(paths), key=_utf8))


def canonical_context_chains(
    chains: Sequence[Sequence[str]],
) -> tuple[tuple[str, ...], ...]:
    """Deduplicate then sort context chains by their UTF-8 element bytes."""

    unique = {tuple(chain) for chain in chains}
    return tuple(sorted(unique, key=lambda chain: [_utf8(item) for item in chain]))


def approval_sort_key(approval_object: Mapping[str, Any]) -> tuple[bytes, ...]:
    """Return the canonical ``(code, context, evidence, id)`` approval key."""

    target = approval_object["target"]
    evidence = target.get("evidence_path") or ""
    return (
        _utf8(target["code"]),
        _utf8(target["context_id"]),
        _utf8(evidence),
        _utf8(approval_object["approval_id"]),
    )


def conflict_sort_key(conflict_object: Mapping[str, Any]) -> tuple[bytes, ...]:
    """Return the canonical ``(source, target, detail)`` conflict key."""

    return (
        _utf8(conflict_object["source"]),
        _utf8(conflict_object["target"]),
        _utf8(conflict_object["detail"]),
    )


def effective_rule_sort_key(rule_object: Mapping[str, Any]) -> tuple[bytes, ...]:
    """Return the canonical six-part EffectiveRule sort key."""

    return (
        _utf8(rule_object["rule_id"]),
        _utf8(rule_object["source_path"]),
        _utf8(rule_object["context_id"]),
        _utf8(rule_object["authority_map"]),
        _utf8(canonical_json_text(rule_object["applies_to"])),
        _utf8(rule_object["overrides_context_id"] or ""),
    )


def diagnostic_sort_key(diagnostic_object: Mapping[str, Any]) -> tuple[Any, ...]:
    """Return the canonical ``(rank, path, context, detail, waiver)`` key."""

    return (
        DIAGNOSTIC_SPECS[diagnostic_object["code"]].rank,
        _utf8(diagnostic_object["path"] or ""),
        _utf8(diagnostic_object["context_id"] or ""),
        _utf8(diagnostic_object["detail"]),
        _utf8(diagnostic_object["waived_by"] or ""),
    )


def difference_sort_key(difference_object: Mapping[str, Any]) -> tuple[Any, ...]:
    """Return the canonical ``(rank, field, expected, actual)`` key."""

    return (
        DIFFERENCE_RANKS[difference_object["code"]],
        _utf8(difference_object["field"]),
        _utf8(difference_object["expected"] or ""),
        _utf8(difference_object["actual"] or ""),
    )


def _is_sorted(values: Sequence[Any], key: Callable[[Any], Any]) -> bool:
    keys = [key(value) for value in values]
    return all(keys[index] < keys[index + 1] for index in range(len(keys) - 1))


# ---------------------------------------------------------------------------
# Input records
# ---------------------------------------------------------------------------

DECLARED_CONFLICT_KEYS = ("source", "target", "detail")
FAILURE_TARGET_KEYS = ("code", "context_id", "evidence_path")
EXCEPTION_APPROVAL_KEYS = (
    "approval_id",
    "coordinator_attested",
    "authorized_by",
    "authorization_reference",
    "authorization_digest",
    "task_id",
    "plan_id",
    "plan_version",
    "attempt_id",
    "issued_on",
    "expires_on",
    "target",
    "scope_sha256",
    "reason",
    "binding_sha256",
)
RESOLUTION_INPUT_KEYS = (
    "task_id",
    "plan_id",
    "plan_version",
    "attempt_id",
    "as_of",
    "scope_paths",
    "context_chains",
    "exception_approvals",
    "declared_conflicts",
)


def _validate_declared_conflict(
    value: Any,
    pointer: str,
    problems: _Problems,
) -> None:
    if not _check_keys(value, pointer, DECLARED_CONFLICT_KEYS, problems):
        return
    _check_string(
        value["source"],
        _pointer(pointer, "source"),
        lambda item: is_free_text(item, maximum=256),
        problems,
        byte_maximum=256,
    )
    _check_string(
        value["target"],
        _pointer(pointer, "target"),
        lambda item: is_free_text(item, maximum=256),
        problems,
        byte_maximum=256,
    )
    _check_string(
        value["detail"],
        _pointer(pointer, "detail"),
        is_free_text,
        problems,
        byte_maximum=FREE_TEXT_BYTE_MAX,
    )


def _validate_failure_target(value: Any, pointer: str, problems: _Problems) -> None:
    if not _check_keys(value, pointer, FAILURE_TARGET_KEYS, problems):
        return
    code_ok = _check_enum(value["code"], _pointer(pointer, "code"), WAIVABLE_CODES, problems)
    _check_string(
        value["context_id"],
        _pointer(pointer, "context_id"),
        lambda item: is_context_id(item, allow_root=True),
        problems,
        byte_maximum=IDENTIFIER_BYTE_MAX,
    )
    evidence_pointer = _pointer(pointer, "evidence_path")
    evidence = value["evidence_path"]
    if code_ok and value["code"] == EVIDENCE_TARGET_CODE:
        _check_string(
            evidence,
            evidence_pointer,
            is_normalized_relative_path,
            problems,
            byte_maximum=RELATIVE_PATH_BYTE_MAX,
        )
    elif evidence is not None:
        problems.add(evidence_pointer, "VALUE")


def _validate_exception_approval(
    value: Any,
    pointer: str,
    problems: _Problems,
) -> None:
    if not _check_keys(value, pointer, EXCEPTION_APPROVAL_KEYS, problems):
        return
    _check_string(
        value["approval_id"],
        _pointer(pointer, "approval_id"),
        is_attempt_id,
        problems,
        byte_maximum=IDENTIFIER_BYTE_MAX,
    )
    _check_bool(value["coordinator_attested"], _pointer(pointer, "coordinator_attested"), problems)
    _check_string(
        value["authorized_by"],
        _pointer(pointer, "authorized_by"),
        lambda item: is_free_text(
            item,
            minimum=AUTHORIZED_BY_BYTE_MIN,
            maximum=AUTHORIZED_BY_BYTE_MAX,
        ),
        problems,
        byte_maximum=AUTHORIZED_BY_BYTE_MAX,
    )
    _check_string(
        value["authorization_reference"],
        _pointer(pointer, "authorization_reference"),
        lambda item: is_free_text(
            item,
            minimum=AUTHORIZATION_REFERENCE_BYTE_MIN,
            maximum=AUTHORIZATION_REFERENCE_BYTE_MAX,
        ),
        problems,
        byte_maximum=AUTHORIZATION_REFERENCE_BYTE_MAX,
    )
    for key in ("authorization_digest", "scope_sha256", "binding_sha256"):
        _check_string(value[key], _pointer(pointer, key), is_sha256, problems)
    for key in ("task_id", "plan_id"):
        _check_string(
            value[key],
            _pointer(pointer, key),
            is_task_or_plan_id,
            problems,
            byte_maximum=IDENTIFIER_BYTE_MAX,
        )
    _check_integer(
        value["plan_version"],
        _pointer(pointer, "plan_version"),
        problems,
        minimum=PLAN_VERSION_MIN,
        maximum=PLAN_VERSION_MAX,
    )
    _check_string(
        value["attempt_id"],
        _pointer(pointer, "attempt_id"),
        is_attempt_id,
        problems,
        byte_maximum=IDENTIFIER_BYTE_MAX,
    )
    for key in ("issued_on", "expires_on"):
        _check_string(value[key], _pointer(pointer, key), is_date, problems)
    _check_string(
        value["reason"],
        _pointer(pointer, "reason"),
        is_free_text,
        problems,
        byte_maximum=FREE_TEXT_BYTE_MAX,
    )
    _validate_failure_target(value["target"], _pointer(pointer, "target"), problems)


def _validate_record_list(
    value: Any,
    pointer: str,
    problems: _Problems,
    *,
    maximum: int,
    validator: Callable[[Any, str, _Problems], None],
    key: Callable[[Mapping[str, Any]], Any] | None,
) -> None:
    """Validate a bounded list of records, its record caps, and duplicates."""

    if not _check_list(value, pointer, problems, maximum=maximum):
        return
    seen: dict[Any, int] = {}
    for index, record in enumerate(value):
        record_pointer = _pointer(pointer, index)
        before = len(problems)
        validator(record, record_pointer, problems)
        if len(problems) != before:
            continue
        if _byte_length(canonical_json_text(record)) > RECORD_CANONICAL_BYTE_MAX:
            problems.add(record_pointer, "BYTE_LIMIT")
            continue
        if key is None:
            continue
        for identity in key(record):
            if identity in seen:
                problems.add(record_pointer, "DUPLICATE")
            else:
                seen[identity] = index


def _approval_identities(record: Mapping[str, Any]) -> tuple[Any, ...]:
    """Approval duplicates are by approval ID and by exact failure target."""

    return (
        ("approval_id", record["approval_id"]),
        ("target", canonical_json_text(record["target"])),
    )


def _conflict_identities(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return (("conflict", canonical_json_text(record)),)


def validate_resolution_input_object(value: Any) -> None:
    """Validate a serialized ResolutionInput object; raise the first violation."""

    problems = _Problems(_INPUT_CONTEXT)
    if not _check_keys(value, "", RESOLUTION_INPUT_KEYS, problems):
        problems.raise_first()
        return
    for key in ("task_id", "plan_id"):
        _check_string(
            value[key],
            _pointer("", key),
            is_task_or_plan_id,
            problems,
            byte_maximum=IDENTIFIER_BYTE_MAX,
        )
    _check_integer(
        value["plan_version"],
        "/plan_version",
        problems,
        minimum=PLAN_VERSION_MIN,
        maximum=PLAN_VERSION_MAX,
    )
    _check_string(
        value["attempt_id"],
        "/attempt_id",
        is_attempt_id,
        problems,
        byte_maximum=IDENTIFIER_BYTE_MAX,
    )
    _check_string(value["as_of"], "/as_of", is_date, problems)
    if _check_list(value["scope_paths"], "/scope_paths", problems, maximum=SCOPE_PATH_COUNT_MAX):
        for index, path in enumerate(value["scope_paths"]):
            _check_string(
                path,
                _pointer("/scope_paths", index),
                is_normalized_relative_path,
                problems,
                byte_maximum=RELATIVE_PATH_BYTE_MAX,
            )
    if _check_list(
        value["context_chains"],
        "/context_chains",
        problems,
        maximum=CONTEXT_CHAIN_COUNT_MAX,
    ):
        for index, chain in enumerate(value["context_chains"]):
            chain_pointer = _pointer("/context_chains", index)
            if not _check_list(
                chain,
                chain_pointer,
                problems,
                maximum=CONTEXT_CHAIN_LENGTH_MAX,
                minimum=CONTEXT_CHAIN_LENGTH_MIN,
            ):
                continue
            for position, context_id in enumerate(chain):
                _check_string(
                    context_id,
                    _pointer(chain_pointer, position),
                    lambda item: is_context_id(item, allow_root=True),
                    problems,
                    byte_maximum=IDENTIFIER_BYTE_MAX,
                )
    _validate_record_list(
        value["exception_approvals"],
        "/exception_approvals",
        problems,
        maximum=APPROVAL_COUNT_MAX,
        validator=_validate_exception_approval,
        key=_approval_identities,
    )
    _validate_record_list(
        value["declared_conflicts"],
        "/declared_conflicts",
        problems,
        maximum=CONFLICT_COUNT_MAX,
        validator=_validate_declared_conflict,
        key=_conflict_identities,
    )
    if not problems and _byte_length(canonical_json_text(value)) > INPUT_CANONICAL_BYTE_MAX:
        problems.add("", "BYTE_LIMIT")
    problems.raise_first()


@dataclass(frozen=True)
class DeclaredConflict:
    """One coordinator-declared authority conflict."""

    source: str
    target: str
    detail: str

    def to_json_object(self) -> dict[str, Any]:
        return {"source": self.source, "target": self.target, "detail": self.detail}


@dataclass(frozen=True)
class FailureTarget:
    """The exact waivable finding one approval targets."""

    code: str
    context_id: str
    evidence_path: str | None

    def to_json_object(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "context_id": self.context_id,
            "evidence_path": self.evidence_path,
        }


@dataclass(frozen=True)
class ExceptionApproval:
    """One coordinator-attested approval with opaque provenance."""

    approval_id: str
    coordinator_attested: bool
    authorized_by: str
    authorization_reference: str
    authorization_digest: str
    task_id: str
    plan_id: str
    plan_version: int
    attempt_id: str
    issued_on: str
    expires_on: str
    target: FailureTarget
    scope_sha256: str
    reason: str
    binding_sha256: str

    def to_json_object(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "coordinator_attested": self.coordinator_attested,
            "authorized_by": self.authorized_by,
            "authorization_reference": self.authorization_reference,
            "authorization_digest": self.authorization_digest,
            "task_id": self.task_id,
            "plan_id": self.plan_id,
            "plan_version": self.plan_version,
            "attempt_id": self.attempt_id,
            "issued_on": self.issued_on,
            "expires_on": self.expires_on,
            "target": _as_json(self.target),
            "scope_sha256": self.scope_sha256,
            "reason": self.reason,
            "binding_sha256": self.binding_sha256,
        }


@dataclass(frozen=True)
class ResolutionInput:
    """The exact serialized resolver input; it never carries ``project_root``."""

    task_id: str
    plan_id: str
    plan_version: int
    attempt_id: str
    as_of: str
    scope_paths: tuple[str, ...]
    context_chains: tuple[tuple[str, ...], ...]
    exception_approvals: tuple[ExceptionApproval, ...]
    declared_conflicts: tuple[DeclaredConflict, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "scope_paths", tuple(self.scope_paths))
        object.__setattr__(
            self,
            "context_chains",
            tuple(tuple(chain) if isinstance(chain, (list, tuple)) else chain for chain in self.context_chains),
        )
        object.__setattr__(self, "exception_approvals", tuple(self.exception_approvals))
        object.__setattr__(self, "declared_conflicts", tuple(self.declared_conflicts))
        validate_resolution_input_object(self.to_json_object())
        # Canonicalization follows validation: scope paths and chains
        # deduplicate then sort, and record arrays take their canonical order.
        object.__setattr__(self, "scope_paths", canonical_scope_paths(self.scope_paths))
        object.__setattr__(
            self, "context_chains", canonical_context_chains(self.context_chains)
        )
        object.__setattr__(
            self,
            "exception_approvals",
            tuple(
                sorted(
                    self.exception_approvals,
                    key=lambda approval: approval_sort_key(_as_json(approval)),
                )
            ),
        )
        object.__setattr__(
            self,
            "declared_conflicts",
            tuple(
                sorted(
                    self.declared_conflicts,
                    key=lambda conflict: conflict_sort_key(_as_json(conflict)),
                )
            ),
        )

    def to_json_object(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "plan_id": self.plan_id,
            "plan_version": self.plan_version,
            "attempt_id": self.attempt_id,
            "as_of": self.as_of,
            "scope_paths": list(self.scope_paths),
            "context_chains": [list(chain) for chain in self.context_chains],
            "exception_approvals": [_as_json(item) for item in self.exception_approvals],
            "declared_conflicts": [_as_json(item) for item in self.declared_conflicts],
        }


# ---------------------------------------------------------------------------
# Snapshot records
# ---------------------------------------------------------------------------

ROOT_IDENTITY_KEYS = ("device", "inode")
FILE_IDENTITY_KEYS = ("device", "inode", "mode", "size", "mtime_ns", "ctime_ns")
EVIDENCE_OBSERVATION_KEYS = ("path", "bytes", "sha256")
SELECTED_FILE_KEYS = (
    "path",
    "context_id",
    "kind",
    "referrer_map",
    "map_chain",
    "applies_to",
    "selection_basis",
    "identity",
    "bytes",
    "sha256",
    "reviewed_on",
    "review_within_days",
    "deprecated",
    "evidence",
)
EFFECTIVE_RULE_KEYS = (
    "rule_id",
    "statement_sha256",
    "source_path",
    "context_id",
    "authority_map",
    "applies_to",
    "overrides_context_id",
)
TOTALS_KEYS = ("file_count", "bytes", "evidence_file_count", "evidence_bytes", "rule_count")
SNAPSHOT_KEYS = (
    "schema_version",
    "task_id",
    "plan_id",
    "plan_version",
    "attempt_id",
    "as_of",
    "root_identity",
    "root_map",
    "scope_paths",
    "context_chains",
    "exception_approvals",
    "declared_conflicts",
    "selected_files",
    "effective_rules",
    "totals",
    "snapshot_sha256",
)

#: The exact root SelectedFile constants of Design section 4.
ROOT_SELECTED_FILE_CONTEXT_ID = ROOT_CONTEXT_ID
ROOT_SELECTED_FILE_KIND = "map"
ROOT_SELECTED_FILE_APPLIES_TO = (".",)
ROOT_SELECTED_FILE_SELECTION_BASIS = ("root",)


def _validate_root_identity(value: Any, pointer: str, problems: _Problems) -> None:
    if not _check_keys(value, pointer, ROOT_IDENTITY_KEYS, problems):
        return
    for key in ROOT_IDENTITY_KEYS:
        _check_integer(
            value[key], _pointer(pointer, key), problems, minimum=0, maximum=INTEGER_MAX
        )


def _validate_file_identity(value: Any, pointer: str, problems: _Problems) -> None:
    if not _check_keys(value, pointer, FILE_IDENTITY_KEYS, problems):
        return
    for key in ("device", "inode", "size", "mtime_ns", "ctime_ns"):
        _check_integer(
            value[key], _pointer(pointer, key), problems, minimum=0, maximum=INTEGER_MAX
        )
    _check_integer(value["mode"], _pointer(pointer, "mode"), problems, minimum=0, maximum=MODE_MAX)


def _validate_evidence_observation(value: Any, pointer: str, problems: _Problems) -> None:
    if not _check_keys(value, pointer, EVIDENCE_OBSERVATION_KEYS, problems):
        return
    _check_string(
        value["path"],
        _pointer(pointer, "path"),
        is_normalized_relative_path,
        problems,
        byte_maximum=RELATIVE_PATH_BYTE_MAX,
    )
    _check_integer(
        value["bytes"],
        _pointer(pointer, "bytes"),
        problems,
        minimum=0,
        maximum=EVIDENCE_FILE_BYTE_LIMIT,
    )
    _check_string(value["sha256"], _pointer(pointer, "sha256"), is_sha256, problems)


def _validate_selection_basis(value: Any, pointer: str, problems: _Problems) -> None:
    if not _check_list(
        value, pointer, problems, maximum=len(SELECTION_BASIS_ORDER), minimum=1
    ):
        return
    for index, basis in enumerate(value):
        _check_enum(basis, _pointer(pointer, index), SELECTION_BASIS_ORDER, problems)
    if len(set(value)) != len(value):
        problems.add(pointer, "DUPLICATE")
        return
    if ROOT_CONTEXT_ID in value:
        # The ``root`` basis belongs only to the root row at index 0.
        problems.add(pointer, "VALUE")
        return
    expected = [item for item in SELECTION_BASIS_ORDER if item in set(value)]
    if list(value) != expected:
        problems.add(pointer, "VALUE")


def _validate_applies_to(value: Any, pointer: str, problems: _Problems) -> None:
    if not _check_list(value, pointer, problems, maximum=MAP_ROW_SELECTOR_LIMIT, minimum=1):
        return
    for index, selector in enumerate(value):
        _check_string(
            selector,
            _pointer(pointer, index),
            is_selector,
            problems,
            byte_maximum=RELATIVE_PATH_BYTE_MAX,
        )


def _validate_selected_file(value: Any, pointer: str, problems: _Problems, *, index: int) -> None:
    if not _check_keys(value, pointer, SELECTED_FILE_KEYS, problems):
        return
    _check_string(
        value["path"],
        _pointer(pointer, "path"),
        is_normalized_relative_path,
        problems,
        byte_maximum=RELATIVE_PATH_BYTE_MAX,
    )
    is_root = index == 0
    _check_string(
        value["context_id"],
        _pointer(pointer, "context_id"),
        lambda item: is_context_id(item, allow_root=is_root),
        problems,
        byte_maximum=IDENTIFIER_BYTE_MAX,
    )
    kind_ok = _check_enum(value["kind"], _pointer(pointer, "kind"), SELECTED_FILE_KINDS, problems)
    referrer_pointer = _pointer(pointer, "referrer_map")
    chain_pointer = _pointer(pointer, "map_chain")
    if is_root:
        if value["path"] != SNAPSHOT_ROOT_MAP:
            problems.add(_pointer(pointer, "path"), "VALUE")
        if value["context_id"] != ROOT_CONTEXT_ID:
            problems.add(_pointer(pointer, "context_id"), "VALUE")
        if value["kind"] != ROOT_SELECTED_FILE_KIND:
            problems.add(_pointer(pointer, "kind"), "VALUE")
        if value["referrer_map"] is not None:
            problems.add(referrer_pointer, "VALUE")
        if value["map_chain"] != []:
            problems.add(chain_pointer, "VALUE")
        if value["applies_to"] != ["."]:
            problems.add(_pointer(pointer, "applies_to"), "VALUE")
        if value["selection_basis"] != ["root"]:
            problems.add(_pointer(pointer, "selection_basis"), "VALUE")
    else:
        if value["context_id"] == ROOT_CONTEXT_ID:
            problems.add(_pointer(pointer, "context_id"), "VALUE")
        _check_string(
            value["referrer_map"],
            referrer_pointer,
            is_normalized_relative_path,
            problems,
            byte_maximum=RELATIVE_PATH_BYTE_MAX,
        )
        if _check_list(
            value["map_chain"],
            chain_pointer,
            problems,
            maximum=MAP_DEPTH_LIMIT,
            minimum=1,
        ):
            for position, context_id in enumerate(value["map_chain"]):
                _check_string(
                    context_id,
                    _pointer(chain_pointer, position),
                    lambda item: is_context_id(item, allow_root=True),
                    problems,
                    byte_maximum=IDENTIFIER_BYTE_MAX,
                )
        _validate_applies_to(value["applies_to"], _pointer(pointer, "applies_to"), problems)
        _validate_selection_basis(
            value["selection_basis"], _pointer(pointer, "selection_basis"), problems
        )
    _validate_file_identity(value["identity"], _pointer(pointer, "identity"), problems)
    bytes_ok = _check_integer(
        value["bytes"],
        _pointer(pointer, "bytes"),
        problems,
        minimum=0,
        maximum=MAP_FILE_BYTE_LIMIT,
    )
    _check_string(value["sha256"], _pointer(pointer, "sha256"), is_sha256, problems)
    identity = value["identity"]
    if bytes_ok and isinstance(identity, Mapping) and _is_int(identity.get("size")):
        if identity["size"] != value["bytes"]:
            problems.add(_pointer(_pointer(pointer, "identity"), "size"), "VALUE")
    reviewed_pointer = _pointer(pointer, "reviewed_on")
    within_pointer = _pointer(pointer, "review_within_days")
    deprecated_pointer = _pointer(pointer, "deprecated")
    evidence_pointer = _pointer(pointer, "evidence")
    is_map = kind_ok and value["kind"] == "map"
    if is_map:
        for review_pointer, review_value in (
            (reviewed_pointer, value["reviewed_on"]),
            (within_pointer, value["review_within_days"]),
            (deprecated_pointer, value["deprecated"]),
        ):
            if review_value is not None:
                problems.add(review_pointer, "VALUE")
        if value["evidence"] != []:
            problems.add(evidence_pointer, "VALUE")
        return
    _check_string(value["reviewed_on"], reviewed_pointer, is_date, problems)
    _check_integer(
        value["review_within_days"], within_pointer, problems, minimum=0, maximum=INTEGER_MAX
    )
    _check_bool(value["deprecated"], deprecated_pointer, problems)
    if not _check_list(
        value["evidence"], evidence_pointer, problems, maximum=EVIDENCE_DECLARATION_MAX
    ):
        return
    for position, observation in enumerate(value["evidence"]):
        _validate_evidence_observation(
            observation, _pointer(evidence_pointer, position), problems
        )
    paths = [
        item["path"]
        for item in value["evidence"]
        if isinstance(item, Mapping) and isinstance(item.get("path"), str)
    ]
    if len(set(paths)) != len(paths):
        problems.add(evidence_pointer, "DUPLICATE")
    elif paths != sorted(paths, key=_utf8):
        problems.add(evidence_pointer, "VALUE")


def _validate_effective_rule(value: Any, pointer: str, problems: _Problems) -> None:
    if not _check_keys(value, pointer, EFFECTIVE_RULE_KEYS, problems):
        return
    _check_string(
        value["rule_id"],
        _pointer(pointer, "rule_id"),
        is_rule_id,
        problems,
        byte_maximum=IDENTIFIER_BYTE_MAX,
    )
    _check_string(
        value["statement_sha256"], _pointer(pointer, "statement_sha256"), is_sha256, problems
    )
    for key in ("source_path", "authority_map"):
        _check_string(
            value[key],
            _pointer(pointer, key),
            is_normalized_relative_path,
            problems,
            byte_maximum=RELATIVE_PATH_BYTE_MAX,
        )
    _check_string(
        value["context_id"],
        _pointer(pointer, "context_id"),
        is_context_id,
        problems,
        byte_maximum=IDENTIFIER_BYTE_MAX,
    )
    _validate_applies_to(value["applies_to"], _pointer(pointer, "applies_to"), problems)
    override_pointer = _pointer(pointer, "overrides_context_id")
    if value["overrides_context_id"] is not None:
        _check_string(
            value["overrides_context_id"],
            override_pointer,
            is_context_id,
            problems,
            byte_maximum=IDENTIFIER_BYTE_MAX,
        )


def _validate_totals(value: Any, pointer: str, problems: _Problems) -> None:
    if not _check_keys(value, pointer, TOTALS_KEYS, problems):
        return
    caps = {
        "file_count": SELECTED_FILE_LIMIT,
        "bytes": SELECTED_AGGREGATE_BYTE_LIMIT,
        "evidence_file_count": EVIDENCE_FILE_COUNT_LIMIT,
        "evidence_bytes": EVIDENCE_AGGREGATE_BYTE_LIMIT,
        "rule_count": EFFECTIVE_RULE_COUNT_LIMIT,
    }
    for key, cap in caps.items():
        _check_integer(value[key], _pointer(pointer, key), problems, minimum=0, maximum=cap)


def validate_snapshot_object(value: Any) -> None:
    """Validate a serialized Snapshot object; raise the first violation."""

    problems = _Problems(_SNAPSHOT_CONTEXT)
    if not _check_keys(value, "", SNAPSHOT_KEYS, problems):
        problems.raise_first()
        return
    _check_integer(
        value["schema_version"],
        "/schema_version",
        problems,
        minimum=SCHEMA_VERSION,
        maximum=SCHEMA_VERSION,
    )
    for key in ("task_id", "plan_id"):
        _check_string(
            value[key],
            _pointer("", key),
            is_task_or_plan_id,
            problems,
            byte_maximum=IDENTIFIER_BYTE_MAX,
        )
    _check_integer(
        value["plan_version"],
        "/plan_version",
        problems,
        minimum=PLAN_VERSION_MIN,
        maximum=PLAN_VERSION_MAX,
    )
    _check_string(
        value["attempt_id"],
        "/attempt_id",
        is_attempt_id,
        problems,
        byte_maximum=IDENTIFIER_BYTE_MAX,
    )
    _check_string(value["as_of"], "/as_of", is_date, problems)
    _validate_root_identity(value["root_identity"], "/root_identity", problems)
    if value["root_map"] != SNAPSHOT_ROOT_MAP:
        problems.add("/root_map", "TYPE" if not isinstance(value["root_map"], str) else "VALUE")
    if _check_list(value["scope_paths"], "/scope_paths", problems, maximum=SCOPE_PATH_COUNT_MAX):
        for index, path in enumerate(value["scope_paths"]):
            _check_string(
                path,
                _pointer("/scope_paths", index),
                is_normalized_relative_path,
                problems,
                byte_maximum=RELATIVE_PATH_BYTE_MAX,
            )
        if list(value["scope_paths"]) != list(canonical_scope_paths(
            [item for item in value["scope_paths"] if isinstance(item, str)]
        )):
            problems.add("/scope_paths", "VALUE")
    if _check_list(
        value["context_chains"], "/context_chains", problems, maximum=CONTEXT_CHAIN_COUNT_MAX
    ):
        chains_ok = True
        for index, chain in enumerate(value["context_chains"]):
            chain_pointer = _pointer("/context_chains", index)
            if not _check_list(
                chain,
                chain_pointer,
                problems,
                maximum=CONTEXT_CHAIN_LENGTH_MAX,
                minimum=CONTEXT_CHAIN_LENGTH_MIN,
            ):
                chains_ok = False
                continue
            for position, context_id in enumerate(chain):
                if not _check_string(
                    context_id,
                    _pointer(chain_pointer, position),
                    lambda item: is_context_id(item, allow_root=True),
                    problems,
                    byte_maximum=IDENTIFIER_BYTE_MAX,
                ):
                    chains_ok = False
        if chains_ok and [tuple(chain) for chain in value["context_chains"]] != list(
            canonical_context_chains(value["context_chains"])
        ):
            problems.add("/context_chains", "VALUE")
    _validate_record_list(
        value["exception_approvals"],
        "/exception_approvals",
        problems,
        maximum=APPROVAL_COUNT_MAX,
        validator=_validate_exception_approval,
        key=_approval_identities,
    )
    _validate_record_list(
        value["declared_conflicts"],
        "/declared_conflicts",
        problems,
        maximum=CONFLICT_COUNT_MAX,
        validator=_validate_declared_conflict,
        key=_conflict_identities,
    )
    if not problems:
        if not _is_sorted(value["exception_approvals"], approval_sort_key):
            problems.add("/exception_approvals", "VALUE")
        if not _is_sorted(value["declared_conflicts"], conflict_sort_key):
            problems.add("/declared_conflicts", "VALUE")
    _validate_selected_files(value, problems)
    _validate_effective_rules(value, problems)
    _validate_totals(value["totals"], "/totals", problems)
    _check_string(value["snapshot_sha256"], "/snapshot_sha256", is_sha256, problems)
    problems.raise_first()
    _validate_snapshot_equalities(value)


def _validate_selected_files(value: Mapping[str, Any], problems: _Problems) -> None:
    files = value["selected_files"]
    if not _check_list(
        files, "/selected_files", problems, maximum=SELECTED_FILE_LIMIT, minimum=1
    ):
        return
    for index, selected in enumerate(files):
        _validate_selected_file(
            selected, _pointer("/selected_files", index), problems, index=index
        )
    if problems:
        return
    paths = [selected["path"] for selected in files]
    if len(set(paths)) != len(paths):
        problems.add("/selected_files", "DUPLICATE")
        return
    if paths[1:] != sorted(paths[1:], key=_utf8):
        problems.add("/selected_files", "VALUE")
    roots = [selected for selected in files if selected["context_id"] == ROOT_CONTEXT_ID]
    if len(roots) != 1:
        problems.add("/selected_files", "VALUE")
    total_bytes = sum(selected["bytes"] for selected in files)
    if total_bytes > SELECTED_AGGREGATE_BYTE_LIMIT:
        problems.add("/selected_files", "COUNT_LIMIT")
    evidence_count = sum(len(selected["evidence"]) for selected in files)
    evidence_bytes = sum(
        observation["bytes"] for selected in files for observation in selected["evidence"]
    )
    evidence_paths = [
        observation["path"] for selected in files for observation in selected["evidence"]
    ]
    if len(set(evidence_paths)) != len(evidence_paths):
        problems.add("/selected_files", "DUPLICATE")
    if evidence_count > EVIDENCE_FILE_COUNT_LIMIT or evidence_bytes > EVIDENCE_AGGREGATE_BYTE_LIMIT:
        problems.add("/selected_files", "COUNT_LIMIT")


def _validate_effective_rules(value: Mapping[str, Any], problems: _Problems) -> None:
    rules = value["effective_rules"]
    if not _check_list(
        rules, "/effective_rules", problems, maximum=EFFECTIVE_RULE_COUNT_LIMIT
    ):
        return
    for index, rule in enumerate(rules):
        _validate_effective_rule(rule, _pointer("/effective_rules", index), problems)
    if problems:
        return
    if not _is_sorted(rules, effective_rule_sort_key):
        problems.add("/effective_rules", "VALUE")


def _validate_snapshot_equalities(value: Mapping[str, Any]) -> None:
    """Check the cross-record equalities, digest, and document cap."""

    problems = _Problems(_SNAPSHOT_CONTEXT)
    files = value["selected_files"]
    by_path = {selected["path"]: selected for selected in files}
    if value["root_map"] != files[0]["path"]:
        problems.add("/root_map", "VALUE")
    for index, rule in enumerate(value["effective_rules"]):
        pointer = _pointer("/effective_rules", index)
        source = by_path.get(rule["source_path"])
        if source is None or source["kind"] != "leaf":
            problems.add(_pointer(pointer, "source_path"), "VALUE")
            continue
        if rule["context_id"] != source["context_id"]:
            problems.add(_pointer(pointer, "context_id"), "VALUE")
        if rule["authority_map"] != source["referrer_map"]:
            problems.add(_pointer(pointer, "authority_map"), "VALUE")
        if rule["applies_to"] != source["applies_to"]:
            problems.add(_pointer(pointer, "applies_to"), "VALUE")
    totals = value["totals"]
    expected_totals = {
        "file_count": len(files),
        "bytes": sum(selected["bytes"] for selected in files),
        "evidence_file_count": sum(len(selected["evidence"]) for selected in files),
        "evidence_bytes": sum(
            observation["bytes"] for selected in files for observation in selected["evidence"]
        ),
        "rule_count": len(value["effective_rules"]),
    }
    for key, expected in expected_totals.items():
        if totals[key] != expected:
            problems.add(_pointer("/totals", key), "VALUE")
    problems.raise_first()
    if value["snapshot_sha256"] != snapshot_digest(value):
        raise TechstackSnapshotError(
            "SNAPSHOT_DIGEST_MISMATCH",
            "/snapshot_sha256",
            FIXED_DETAILS["SNAPSHOT_DIGEST_MISMATCH"],
        )
    document = canonical_json_document(value)
    if len(document.encode("utf-8")) > SNAPSHOT_DOCUMENT_BYTE_LIMIT:
        raise TechstackSnapshotError(
            "SNAPSHOT_BYTE_LIMIT", "", FIXED_DETAILS["SNAPSHOT_BYTE_LIMIT"]
        )


@dataclass(frozen=True)
class RootIdentity:
    """The anchored project-root device and inode."""

    device: int
    inode: int

    def to_json_object(self) -> dict[str, Any]:
        return {"device": self.device, "inode": self.inode}


@dataclass(frozen=True)
class FileIdentity:
    """The six-field observed identity of one selected file."""

    device: int
    inode: int
    mode: int
    size: int
    mtime_ns: int
    ctime_ns: int

    def to_json_object(self) -> dict[str, Any]:
        return {
            "device": self.device,
            "inode": self.inode,
            "mode": self.mode,
            "size": self.size,
            "mtime_ns": self.mtime_ns,
            "ctime_ns": self.ctime_ns,
        }


@dataclass(frozen=True)
class EvidenceObservation:
    """One observed declared-evidence file."""

    path: str
    bytes: int
    sha256: str

    def to_json_object(self) -> dict[str, Any]:
        return {"path": self.path, "bytes": self.bytes, "sha256": self.sha256}


@dataclass(frozen=True)
class SelectedFile:
    """One selected map or leaf and its complete selection provenance."""

    path: str
    context_id: str
    kind: str
    referrer_map: str | None
    map_chain: tuple[str, ...]
    applies_to: tuple[str, ...]
    selection_basis: tuple[str, ...]
    identity: FileIdentity
    bytes: int
    sha256: str
    reviewed_on: str | None
    review_within_days: int | None
    deprecated: bool | None
    evidence: tuple[EvidenceObservation, ...]

    def to_json_object(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "context_id": self.context_id,
            "kind": self.kind,
            "referrer_map": self.referrer_map,
            "map_chain": list(self.map_chain),
            "applies_to": list(self.applies_to),
            "selection_basis": list(self.selection_basis),
            "identity": _as_json(self.identity),
            "bytes": self.bytes,
            "sha256": self.sha256,
            "reviewed_on": self.reviewed_on,
            "review_within_days": self.review_within_days,
            "deprecated": self.deprecated,
            "evidence": [_as_json(item) for item in self.evidence],
        }


@dataclass(frozen=True)
class EffectiveRule:
    """One normalized rule statement and the authority that carries it."""

    rule_id: str
    statement_sha256: str
    source_path: str
    context_id: str
    authority_map: str
    applies_to: tuple[str, ...]
    overrides_context_id: str | None

    def to_json_object(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "statement_sha256": self.statement_sha256,
            "source_path": self.source_path,
            "context_id": self.context_id,
            "authority_map": self.authority_map,
            "applies_to": list(self.applies_to),
            "overrides_context_id": self.overrides_context_id,
        }


@dataclass(frozen=True)
class Totals:
    """Recomputed counts and byte sums for one Snapshot."""

    file_count: int
    bytes: int
    evidence_file_count: int
    evidence_bytes: int
    rule_count: int

    def to_json_object(self) -> dict[str, Any]:
        return {
            "file_count": self.file_count,
            "bytes": self.bytes,
            "evidence_file_count": self.evidence_file_count,
            "evidence_bytes": self.evidence_bytes,
            "rule_count": self.rule_count,
        }


@dataclass(frozen=True)
class Snapshot:
    """The exact applicable-resolution artifact; it carries no absolute path."""

    schema_version: int
    task_id: str
    plan_id: str
    plan_version: int
    attempt_id: str
    as_of: str
    root_identity: RootIdentity
    root_map: str
    scope_paths: tuple[str, ...]
    context_chains: tuple[tuple[str, ...], ...]
    exception_approvals: tuple[ExceptionApproval, ...]
    declared_conflicts: tuple[DeclaredConflict, ...]
    selected_files: tuple[SelectedFile, ...]
    effective_rules: tuple[EffectiveRule, ...]
    totals: Totals
    snapshot_sha256: str

    def __post_init__(self) -> None:
        for name in (
            "scope_paths",
            "exception_approvals",
            "declared_conflicts",
            "selected_files",
            "effective_rules",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(
            self,
            "context_chains",
            tuple(
                tuple(chain) if isinstance(chain, (list, tuple)) else chain
                for chain in self.context_chains
            ),
        )
        validate_snapshot_object(self.to_json_object())

    @classmethod
    def build(cls, **fields: Any) -> "Snapshot":
        """Construct a Snapshot, computing ``snapshot_sha256`` from its content."""

        draft = dict(fields)
        draft["snapshot_sha256"] = DIGEST_PLACEHOLDER
        provisional = {
            key: _as_json(value)
            for key, value in draft.items()
        }
        provisional["context_chains"] = [list(chain) for chain in draft["context_chains"]]
        provisional["scope_paths"] = list(draft["scope_paths"])
        draft["snapshot_sha256"] = snapshot_digest(provisional)
        return cls(**draft)

    def to_json_object(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "plan_id": self.plan_id,
            "plan_version": self.plan_version,
            "attempt_id": self.attempt_id,
            "as_of": self.as_of,
            "root_identity": _as_json(self.root_identity),
            "root_map": self.root_map,
            "scope_paths": list(self.scope_paths),
            "context_chains": [list(chain) for chain in self.context_chains],
            "exception_approvals": [_as_json(item) for item in self.exception_approvals],
            "declared_conflicts": [_as_json(item) for item in self.declared_conflicts],
            "selected_files": [_as_json(item) for item in self.selected_files],
            "effective_rules": [_as_json(item) for item in self.effective_rules],
            "totals": _as_json(self.totals),
            "snapshot_sha256": self.snapshot_sha256,
        }


def snapshot_document(snapshot: "Snapshot") -> str:
    """Return the canonical Snapshot document, terminal LF included."""

    document = canonical_json_document(snapshot.to_json_object())
    if len(document.encode("utf-8")) > SNAPSHOT_DOCUMENT_BYTE_LIMIT:
        raise TechstackSnapshotError(
            "SNAPSHOT_BYTE_LIMIT", "", FIXED_DETAILS["SNAPSHOT_BYTE_LIMIT"]
        )
    return document


# ---------------------------------------------------------------------------
# Diagnostics, Resolution, Differences, and Verification
# ---------------------------------------------------------------------------

DIAGNOSTIC_KEYS = ("code", "severity", "path", "context_id", "detail", "waivable", "waived_by")
RESOLUTION_KEYS = ("schema_version", "status", "snapshot", "diagnostics")
DIFFERENCE_KEYS = ("code", "field", "expected", "actual")
VERIFICATION_KEYS = (
    "schema_version",
    "status",
    "expected_snapshot_sha256",
    "observed_snapshot_sha256",
    "observed_resolution",
    "differences",
)


@dataclass(frozen=True)
class Diagnostic:
    """One closed registry finding. Location lives in fields, never in detail."""

    code: str
    severity: str
    path: str | None
    context_id: str | None
    detail: str
    waivable: bool
    waived_by: str | None

    def __post_init__(self) -> None:
        spec = DIAGNOSTIC_SPECS.get(self.code)
        if spec is None:
            raise ValueError(f"unknown diagnostic code: {self.code!r}")
        if self.waivable is not spec.waivable:
            raise ValueError(f"{self.code} waivability is fixed by the registry")
        if self.waived_by is None:
            if self.severity != "error":
                raise ValueError(f"{self.code} is an error unless it is consumed")
        else:
            if not spec.waivable:
                raise ValueError(f"{self.code} is not waivable")
            if self.severity != "warning":
                raise ValueError(f"a consumed {self.code} is a warning")
            if not is_attempt_id(self.waived_by):
                raise ValueError("waived_by must be an approval ID")
        line, rule = self._leaf_slots()
        if self.code == "INVALID_LEAF" and (line is None or rule is None):
            raise ValueError(f"{self.code} detail is fixed by the registry")
        if self.detail != diagnostic_detail(
            self.code, errno_value=self._errno_value(), line=line, rule=rule
        ):
            raise ValueError(f"{self.code} detail is fixed by the registry")
        if not 1 <= _byte_length(self.detail) <= DETAIL_BYTE_MAX:
            raise ValueError("diagnostic detail exceeds its byte bounds")
        self._check_location(spec)

    def _errno_value(self) -> int | None:
        if self.code != "FILESYSTEM_ERROR":
            return None
        suffix = self.detail.rsplit(" ", 1)[-1]
        try:
            return int(suffix)
        except ValueError:
            return None

    def _leaf_slots(self) -> tuple[int | None, str | None]:
        """Parse the two ``INVALID_LEAF`` slots back out of ``detail``.

        The accepted form is the literal prefix, one canonical decimal with no
        sign, leading zero, or whitespace and inside the reportable line
        bounds, then ``": "``, then one registry member. Any other form yields
        ``(None, None)``, which the caller rejects.
        """

        if self.code != "INVALID_LEAF":
            return (None, None)
        if not self.detail.startswith(INVALID_LEAF_DETAIL_PREFIX):
            return (None, None)
        remainder = self.detail[len(INVALID_LEAF_DETAIL_PREFIX) :]
        decimal, separator, rule = remainder.partition(": ")
        if not separator or rule not in LEAF_GRAMMAR_RULES:
            return (None, None)
        if not decimal or not all(character in "0123456789" for character in decimal):
            return (None, None)
        if len(decimal) > 1 and decimal.startswith("0"):
            return (None, None)
        line = int(decimal)
        if not 0 <= line <= LEAF_FILE_BYTE_LIMIT + 1:
            return (None, None)
        return (line, rule)

    def _check_location(self, spec: DiagnosticSpec) -> None:
        path_required = spec.fields in ("P", "C") or (
            spec.fields == "T" and self.code == "MISSING_EVIDENCE"
        )
        context_required = spec.fields in ("C", "T")
        if path_required:
            if not is_normalized_relative_path(self.path):
                raise ValueError(f"{self.code} requires a normalized path")
        elif self.path is not None:
            raise ValueError(f"{self.code} must not carry a path")
        if context_required:
            if not is_context_id(self.context_id, allow_root=True):
                raise ValueError(f"{self.code} requires a Context ID")
        elif self.context_id is not None:
            raise ValueError(f"{self.code} must not carry a Context ID")

    def to_json_object(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "context_id": self.context_id,
            "detail": self.detail,
            "waivable": self.waivable,
            "waived_by": self.waived_by,
        }


def diagnostic(
    code: str,
    *,
    path: str | None = None,
    context_id: str | None = None,
    errno_value: int | None = None,
    line: int | None = None,
    rule: str | None = None,
    waived_by: str | None = None,
) -> Diagnostic:
    """Build one registry-exact Diagnostic."""

    spec = DIAGNOSTIC_SPECS[code]
    severity = "warning" if waived_by is not None else "error"
    return Diagnostic(
        code=code,
        severity=severity,
        path=path,
        context_id=context_id,
        detail=diagnostic_detail(code, errno_value=errno_value, line=line, rule=rule),
        waivable=spec.waivable,
        waived_by=waived_by,
    )


def sort_diagnostics(diagnostics: Sequence[Diagnostic]) -> tuple[Diagnostic, ...]:
    """Sort diagnostics by ``(rank, path, context, detail, waived_by)``."""

    return tuple(
        sorted(diagnostics, key=lambda item: diagnostic_sort_key(item.to_json_object()))
    )


def apply_diagnostic_limit(
    diagnostics: Sequence[Diagnostic],
) -> tuple[Diagnostic, ...]:
    """Return sorted diagnostics, or the single replacement overflow sentinel.

    A 129th diagnostic discards the entire accumulated array; the first 128 are
    never returned as if the array were complete.
    """

    if len(diagnostics) > DIAGNOSTIC_COUNT_LIMIT:
        return (diagnostic("DIAGNOSTIC_LIMIT"),)
    return sort_diagnostics(diagnostics)


@dataclass(frozen=True)
class Resolution:
    """The complete resolver outcome for one attempt."""

    schema_version: int
    status: str
    snapshot: Snapshot | None
    diagnostics: tuple[Diagnostic, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("Resolution schema_version is 1")
        if self.status not in RESOLUTION_STATUSES:
            raise ValueError(f"unknown Resolution status: {self.status!r}")
        if (self.snapshot is not None) != (self.status == "applicable"):
            raise ValueError("Snapshot is nonnull exactly for an applicable Resolution")
        if self.status == "not_applicable" and self.diagnostics:
            raise ValueError("a not-applicable Resolution carries no diagnostics")
        if self.status == "applicable" and any(
            item.severity != "warning" or item.waived_by is None
            for item in self.diagnostics
        ):
            raise ValueError(
                "an applicable Resolution carries only consumed-waiver warnings"
            )
        if self.status == "blocked" and not any(
            item.severity == "error" for item in self.diagnostics
        ):
            raise ValueError("a blocked Resolution carries at least one error")

    def to_json_object(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "snapshot": None if self.snapshot is None else _as_json(self.snapshot),
            "diagnostics": [_as_json(item) for item in self.diagnostics],
        }


@dataclass(frozen=True)
class Difference:
    """One closed verification difference record."""

    code: str
    field: str
    expected: str | None
    actual: str | None

    def __post_init__(self) -> None:
        if self.code not in DIFFERENCE_RANKS:
            raise ValueError(f"unknown Difference code: {self.code!r}")
        if not isinstance(self.field, str) or not 1 <= _byte_length(
            self.field
        ) <= RELATIVE_PATH_BYTE_MAX:
            raise ValueError("Difference field is a 1-1024 byte JSON Pointer")
        if not self.field.startswith("/"):
            raise ValueError("Difference field is a JSON Pointer")
        for representation in (self.expected, self.actual):
            if representation is None:
                continue
            if not isinstance(representation, str):
                raise ValueError("Difference representations are strings or null")
            if _byte_length(representation) > DIFFERENCE_REPRESENTATION_BYTE_MAX:
                raise ValueError("Difference representation exceeds 1024 bytes")

    def to_json_object(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass(frozen=True)
class Verification:
    """The complete verification outcome for one Snapshot."""

    schema_version: int
    status: str
    expected_snapshot_sha256: str
    observed_snapshot_sha256: str | None
    observed_resolution: Resolution
    differences: tuple[Difference, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "differences", tuple(self.differences))
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("Verification schema_version is 1")
        if self.status not in VERIFICATION_STATUSES:
            raise ValueError(f"unknown Verification status: {self.status!r}")
        if not is_sha256(self.expected_snapshot_sha256):
            raise ValueError("expected_snapshot_sha256 must be a SHA-256 digest")
        if self.observed_snapshot_sha256 is not None and not is_sha256(
            self.observed_snapshot_sha256
        ):
            raise ValueError("observed_snapshot_sha256 must be null or a SHA-256 digest")
        if not isinstance(self.observed_resolution, Resolution):
            raise ValueError("observed_resolution is always present")
        observed = self.observed_resolution.status
        if observed == "blocked":
            self._require(
                self.status == "blocked"
                and self.observed_snapshot_sha256 is None
                and len(self.differences) == 1
                and self.differences[0].code == "OBSERVED_BLOCKED",
                "a blocked observation carries exactly one OBSERVED_BLOCKED",
            )
        elif observed == "not_applicable":
            self._require(
                self.status == "drift"
                and self.observed_snapshot_sha256 is None
                and len(self.differences) == 1
                and self.differences[0].code == "OBSERVED_NOT_APPLICABLE",
                "an observed opt-out carries exactly one OBSERVED_NOT_APPLICABLE",
            )
        elif self.status == "match":
            self._require(
                self.observed_snapshot_sha256 == self.expected_snapshot_sha256
                and not self.differences,
                "a match carries the expected digest and no differences",
            )
        else:
            self._require(
                self.status == "drift"
                and self.observed_snapshot_sha256 is not None
                and 1 <= len(self.differences) <= DIFFERENCE_COUNT_LIMIT,
                "applicable drift carries an observed digest and bounded differences",
            )

    @staticmethod
    def _require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)

    def to_json_object(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "expected_snapshot_sha256": self.expected_snapshot_sha256,
            "observed_snapshot_sha256": self.observed_snapshot_sha256,
            "observed_resolution": _as_json(self.observed_resolution),
            "differences": [_as_json(item) for item in self.differences],
        }


# ---------------------------------------------------------------------------
# Difference construction
# ---------------------------------------------------------------------------

#: Canonical array keys; every other array matches on its complete element.
_ARRAY_KEY_FUNCTIONS: Mapping[str, Callable[[Any], Any]] = {
    "exception_approvals": lambda element: element["approval_id"],
    "declared_conflicts": lambda element: [
        element["source"],
        element["target"],
        element["detail"],
    ],
    "selected_files": lambda element: element["path"],
    "effective_rules": lambda element: [
        element["rule_id"],
        element["source_path"],
        element["context_id"],
        element["authority_map"],
        element["applies_to"],
        element["overrides_context_id"],
    ],
    "evidence": lambda element: element["path"],
}

#: Snapshot key excluded from comparison because it is derived.
_DERIVED_SNAPSHOT_KEY = "snapshot_sha256"


def _element_identity(segment: str, element: Any) -> tuple[str, Any]:
    """Return the ``(pointer segment, canonical key)`` of one array element."""

    key_function = _ARRAY_KEY_FUNCTIONS.get(segment)
    key = key_function(element) if key_function is not None else element
    return f"@sha256={sha256_hex(canonical_json_bytes(key))}", key


def difference_representation(value: Any) -> str:
    """Return canonical JSON text, or the exact oversize hash marker."""

    text = canonical_json_text(value)
    if _byte_length(text) <= DIFFERENCE_REPRESENTATION_BYTE_MAX:
        return text
    return f"canonical-json-sha256:{sha256_hex(canonical_json_bytes(value))}"


def _compare_values(
    expected: Any,
    observed: Any,
    pointer: str,
    segment: str,
    found: list[Difference],
) -> None:
    if isinstance(expected, Mapping) and isinstance(observed, Mapping):
        for key in sorted(set(expected) | set(observed), key=_utf8):
            child = _pointer(pointer, key)
            if key not in expected or key not in observed:
                found.append(
                    Difference(
                        code="VALUE_MISMATCH",
                        field=child,
                        expected=None if key not in expected else difference_representation(expected[key]),
                        actual=None if key not in observed else difference_representation(observed[key]),
                    )
                )
                continue
            _compare_values(expected[key], observed[key], child, key, found)
        return
    if isinstance(expected, list) and isinstance(observed, list):
        expected_elements: dict[str, Any] = {}
        for element in expected:
            expected_elements[_element_identity(segment, element)[0]] = element
        observed_elements: dict[str, Any] = {}
        for element in observed:
            observed_elements[_element_identity(segment, element)[0]] = element
        for identity in sorted(set(expected_elements) | set(observed_elements)):
            child = f"{pointer}/{identity}"
            if identity not in observed_elements:
                found.append(
                    Difference(
                        code="MISSING_RECORD",
                        field=child,
                        expected=difference_representation(expected_elements[identity]),
                        actual=None,
                    )
                )
                continue
            if identity not in expected_elements:
                found.append(
                    Difference(
                        code="EXTRA_RECORD",
                        field=child,
                        expected=None,
                        actual=difference_representation(observed_elements[identity]),
                    )
                )
                continue
            _compare_values(
                expected_elements[identity], observed_elements[identity], child, segment, found
            )
        return
    if canonical_json_text(expected) != canonical_json_text(observed):
        found.append(
            Difference(
                code="VALUE_MISMATCH",
                field=pointer,
                expected=difference_representation(expected),
                actual=difference_representation(observed),
            )
        )


def sort_differences(differences: Sequence[Difference]) -> tuple[Difference, ...]:
    """Sort differences by ``(code rank, field, expected, actual)``."""

    return tuple(
        sorted(differences, key=lambda item: difference_sort_key(item.to_json_object()))
    )


def difference_limit_record(expected_digest: str, observed_digest: str) -> Difference:
    """Return the single replacement difference sentinel."""

    return Difference(
        code="DIFFERENCE_LIMIT",
        field="/",
        expected=f"snapshot-sha256:{expected_digest}",
        actual=f"snapshot-sha256:{observed_digest}",
    )


def apply_difference_limit(
    differences: Sequence[Difference],
    expected_digest: str,
    observed_digest: str,
) -> tuple[Difference, ...]:
    """Return sorted differences, or the single replacement overflow sentinel."""

    if len(differences) > DIFFERENCE_COUNT_LIMIT:
        return (difference_limit_record(expected_digest, observed_digest),)
    return sort_differences(differences)


def build_snapshot_differences(
    expected: "Snapshot",
    observed: "Snapshot",
) -> tuple[Difference, ...]:
    """Compare two validated Snapshots into closed, sorted Difference records."""

    expected_object = expected.to_json_object()
    observed_object = observed.to_json_object()
    del expected_object[_DERIVED_SNAPSHOT_KEY]
    del observed_object[_DERIVED_SNAPSHOT_KEY]
    found: list[Difference] = []
    _compare_values(expected_object, observed_object, "", "", found)
    return apply_difference_limit(
        found, expected.snapshot_sha256, observed.snapshot_sha256
    )


#: The two observed-status singleton rows of Design section 8.
OBSERVED_STATUS_FIELD = "/observed_resolution/status"


def observed_not_applicable_difference() -> Difference:
    """Return the exact observed opt-out difference."""

    return Difference(
        code="OBSERVED_NOT_APPLICABLE",
        field=OBSERVED_STATUS_FIELD,
        expected='"applicable"',
        actual='"not_applicable"',
    )


def observed_blocked_difference() -> Difference:
    """Return the exact observed blocked difference."""

    return Difference(
        code="OBSERVED_BLOCKED",
        field=OBSERVED_STATUS_FIELD,
        expected='"applicable"',
        actual='"blocked"',
    )


# ---------------------------------------------------------------------------
# Snapshot publication
# ---------------------------------------------------------------------------

SNAPSHOT_ATTEMPT_KEYS = (
    "ordinal",
    "artifact_path",
    "snapshot_sha256",
    "publication",
    "verification_status",
)
SNAPSHOT_PUBLICATION_KEYS = (
    "schema_version",
    "status",
    "resolution",
    "attempts",
    "selected_artifact",
    "selected_snapshot_sha256",
)


@dataclass(frozen=True)
class SnapshotAttempt:
    """One publish-then-verify attempt of the publication protocol."""

    ordinal: int
    artifact_path: str
    snapshot_sha256: str
    publication: str
    verification_status: str

    def __post_init__(self) -> None:
        if not _is_int(self.ordinal) or not 1 <= self.ordinal <= PUBLICATION_ATTEMPT_MAX:
            raise ValueError("attempt ordinal is 1 to 3")
        if not is_normalized_relative_path(self.artifact_path):
            raise ValueError("attempt artifact_path must be a normalized relative path")
        if not is_sha256(self.snapshot_sha256):
            raise ValueError("attempt snapshot_sha256 must be a SHA-256 digest")
        if self.publication not in ATTEMPT_PUBLICATIONS:
            raise ValueError(f"unknown attempt publication: {self.publication!r}")
        if self.verification_status not in VERIFICATION_STATUSES:
            raise ValueError(
                f"unknown attempt verification status: {self.verification_status!r}"
            )

    def to_json_object(self) -> dict[str, Any]:
        return {
            "ordinal": self.ordinal,
            "artifact_path": self.artifact_path,
            "snapshot_sha256": self.snapshot_sha256,
            "publication": self.publication,
            "verification_status": self.verification_status,
        }


@dataclass(frozen=True)
class SnapshotPublication:
    """The non-circular publish-then-verify outcome."""

    schema_version: int
    status: str
    resolution: Resolution
    attempts: tuple[SnapshotAttempt, ...]
    selected_artifact: str | None
    selected_snapshot_sha256: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempts", tuple(self.attempts))
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("SnapshotPublication schema_version is 1")
        if self.status not in PUBLICATION_STATUSES:
            raise ValueError(f"unknown publication status: {self.status!r}")
        if not isinstance(self.resolution, Resolution):
            raise ValueError("publication resolution is the final exact Resolution")
        if len(self.attempts) > PUBLICATION_ATTEMPT_MAX:
            raise ValueError("a publication carries at most three attempts")
        ordinals = [attempt.ordinal for attempt in self.attempts]
        if ordinals != list(range(1, len(self.attempts) + 1)):
            raise ValueError("attempt ordinals are sequential from one")
        selected = (self.selected_artifact, self.selected_snapshot_sha256)
        if self.status == "published":
            matching = [
                attempt
                for attempt in self.attempts
                if attempt.verification_status == "match"
            ]
            if len(matching) != 1:
                raise ValueError("a published publication has exactly one match attempt")
            if selected != (matching[0].artifact_path, matching[0].snapshot_sha256):
                raise ValueError("selected fields equal the matching attempt")
        elif selected != (None, None):
            raise ValueError("selected fields are nonnull only for a published status")

    def to_json_object(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "resolution": _as_json(self.resolution),
            "attempts": [_as_json(item) for item in self.attempts],
            "selected_artifact": self.selected_artifact,
            "selected_snapshot_sha256": self.selected_snapshot_sha256,
        }


def publication_document(publication: "SnapshotPublication") -> str:
    """Return the canonical publication document, terminal LF included.

    The 262,144-byte cap is measured on the complete document, so exactly
    262,144 bytes succeeds and 262,145 raises before any byte is emitted.
    """

    document = canonical_json_document(publication.to_json_object())
    if len(document.encode("utf-8")) > PUBLICATION_DOCUMENT_BYTE_LIMIT:
        raise TechstackSnapshotError(
            "PUBLICATION_BYTE_LIMIT", "", FIXED_DETAILS["PUBLICATION_BYTE_LIMIT"]
        )
    return document


# ---------------------------------------------------------------------------
# JSON object constructors
# ---------------------------------------------------------------------------


def _build_failure_target(value: Mapping[str, Any]) -> FailureTarget:
    return FailureTarget(
        code=value["code"],
        context_id=value["context_id"],
        evidence_path=value["evidence_path"],
    )


def _build_exception_approval(value: Mapping[str, Any]) -> ExceptionApproval:
    return ExceptionApproval(
        approval_id=value["approval_id"],
        coordinator_attested=value["coordinator_attested"],
        authorized_by=value["authorized_by"],
        authorization_reference=value["authorization_reference"],
        authorization_digest=value["authorization_digest"],
        task_id=value["task_id"],
        plan_id=value["plan_id"],
        plan_version=value["plan_version"],
        attempt_id=value["attempt_id"],
        issued_on=value["issued_on"],
        expires_on=value["expires_on"],
        target=_build_failure_target(value["target"]),
        scope_sha256=value["scope_sha256"],
        reason=value["reason"],
        binding_sha256=value["binding_sha256"],
    )


def _build_declared_conflict(value: Mapping[str, Any]) -> DeclaredConflict:
    return DeclaredConflict(
        source=value["source"], target=value["target"], detail=value["detail"]
    )


def _build_selected_file(value: Mapping[str, Any]) -> SelectedFile:
    identity = value["identity"]
    return SelectedFile(
        path=value["path"],
        context_id=value["context_id"],
        kind=value["kind"],
        referrer_map=value["referrer_map"],
        map_chain=tuple(value["map_chain"]),
        applies_to=tuple(value["applies_to"]),
        selection_basis=tuple(value["selection_basis"]),
        identity=FileIdentity(
            device=identity["device"],
            inode=identity["inode"],
            mode=identity["mode"],
            size=identity["size"],
            mtime_ns=identity["mtime_ns"],
            ctime_ns=identity["ctime_ns"],
        ),
        bytes=value["bytes"],
        sha256=value["sha256"],
        reviewed_on=value["reviewed_on"],
        review_within_days=value["review_within_days"],
        deprecated=value["deprecated"],
        evidence=tuple(
            EvidenceObservation(
                path=item["path"], bytes=item["bytes"], sha256=item["sha256"]
            )
            for item in value["evidence"]
        ),
    )


def _build_effective_rule(value: Mapping[str, Any]) -> EffectiveRule:
    return EffectiveRule(
        rule_id=value["rule_id"],
        statement_sha256=value["statement_sha256"],
        source_path=value["source_path"],
        context_id=value["context_id"],
        authority_map=value["authority_map"],
        applies_to=tuple(value["applies_to"]),
        overrides_context_id=value["overrides_context_id"],
    )


def resolution_input_from_json_object(value: Any) -> ResolutionInput:
    """Validate and build a ResolutionInput from a parsed JSON object."""

    validate_resolution_input_object(value)
    return ResolutionInput(
        task_id=value["task_id"],
        plan_id=value["plan_id"],
        plan_version=value["plan_version"],
        attempt_id=value["attempt_id"],
        as_of=value["as_of"],
        scope_paths=tuple(value["scope_paths"]),
        context_chains=tuple(tuple(chain) for chain in value["context_chains"]),
        exception_approvals=tuple(
            _build_exception_approval(item) for item in value["exception_approvals"]
        ),
        declared_conflicts=tuple(
            _build_declared_conflict(item) for item in value["declared_conflicts"]
        ),
    )


def snapshot_from_json_object(value: Any) -> Snapshot:
    """Validate and build a Snapshot from a parsed JSON object."""

    validate_snapshot_object(value)
    identity = value["root_identity"]
    return Snapshot(
        schema_version=value["schema_version"],
        task_id=value["task_id"],
        plan_id=value["plan_id"],
        plan_version=value["plan_version"],
        attempt_id=value["attempt_id"],
        as_of=value["as_of"],
        root_identity=RootIdentity(device=identity["device"], inode=identity["inode"]),
        root_map=value["root_map"],
        scope_paths=tuple(value["scope_paths"]),
        context_chains=tuple(tuple(chain) for chain in value["context_chains"]),
        exception_approvals=tuple(
            _build_exception_approval(item) for item in value["exception_approvals"]
        ),
        declared_conflicts=tuple(
            _build_declared_conflict(item) for item in value["declared_conflicts"]
        ),
        selected_files=tuple(_build_selected_file(item) for item in value["selected_files"]),
        effective_rules=tuple(_build_effective_rule(item) for item in value["effective_rules"]),
        totals=Totals(
            file_count=value["totals"]["file_count"],
            bytes=value["totals"]["bytes"],
            evidence_file_count=value["totals"]["evidence_file_count"],
            evidence_bytes=value["totals"]["evidence_bytes"],
            rule_count=value["totals"]["rule_count"],
        ),
        snapshot_sha256=value["snapshot_sha256"],
    )
