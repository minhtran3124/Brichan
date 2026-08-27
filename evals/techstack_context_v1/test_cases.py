"""The frozen 12-case techstack-context policy evaluation.

This module is test-only evidence for coordinator policy — the H3 planner
reread and the packet acknowledgement — and never production validation. It
drives the production resolver, ``verify_snapshot``, and the production digest
helpers over disposable copies of the Design section 15 fixture bytes; the
acceptance verdict it computes lives here, not in ``src/brichan``.

Every fixture byte and the whole corpus are frozen by digest. No expected
Snapshot digest is stored: root identity carries the real device and inode, so
digests are checked by relation — observed against acknowledged — and never by
literal.

Run it exactly as:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest evals.techstack_context_v1.test_cases -v
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


EVAL_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = EVAL_DIR.parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from brichan.techstacks import (  # noqa: E402 - the path insert precedes it
    DIAGNOSTIC_CODES,
    DeclaredConflict,
    ExceptionApproval,
    FailureTarget,
    ResolutionInput,
    Resolution,
    Verification,
    resolve_context,
    verify_snapshot,
)
from brichan.techstacks import model, resolver  # noqa: E402


# ---------------------------------------------------------------------------
# Frozen corpus surface
# ---------------------------------------------------------------------------

#: The only schema version this eval implements. Version 1 is superseded and is
#: deliberately unreachable from here.
SCHEMA_VERSION = 2

#: Design section 16's strict corpus cap.
CASES_BYTE_LIMIT = 32768

#: Design section 16's exact case count.
CASE_COUNT = 12

CASES_PATH = EVAL_DIR / "cases.json"
FIXTURES_DIR = EVAL_DIR / "fixtures"

#: The eight Design section 15 fixture files and their frozen SHA-256 digests.
FIXTURE_DIGESTS = {
    "base/techstacks/README.md": "799ff69696d64ff69712e468b04da56641b1d8e7d270a0558ed361c80e831aca",
    "base/techstacks/general.md": "e53c65b6e09b67e1939e1a66ef7d53ba4e160639f846434ec245831edfd5f2f8",
    "base/techstacks/frontend/README.md": "8d849e5e007460967078eecd61716466549feb649359b9b054ffeec66267924f",
    "base/techstacks/frontend/components/Button.md": "b7cfdca9ef58aac52964d2bdfe9e502fb7229e99a4142dfa0a8b487af0c4fb66",
    "base/evidence/button.txt": "23953a89e4ce120b5ca035b218fb3e88eef34600ea810c4943d4103df6e97188",
    "stale/techstacks/README.md": "501f16996156edc92a86bc5d3695039f045af2bbfb7248a15eb38e114095cc1f",
    "stale/techstacks/stale.md": "0b31142020b4884458040320aa8fdd29c2edeb955295fe8761f79c81afd4fcfa",
    "stale/evidence/stale.txt": "7748a85fb815d7b4d7e7c4bfae1e8cb8b9cadb966823ee76842a3745fbb0d3ca",
}

#: The frozen byte lengths of the same eight blocks.
FIXTURE_BYTE_COUNTS = {
    "base/techstacks/README.md": 295,
    "base/techstacks/general.md": 375,
    "base/techstacks/frontend/README.md": 289,
    "base/techstacks/frontend/components/Button.md": 394,
    "base/evidence/button.txt": 19,
    "stale/techstacks/README.md": 227,
    "stale/techstacks/stale.md": 394,
    "stale/evidence/stale.txt": 18,
}

#: The literal 8,629-byte corpus of Design section 16.
CASES_SHA256 = "250759f6a9e2aba7355621fa76777fd8d2712c8ba0f721f40b6e2155de286ba7"
CASES_BYTE_COUNT = 8629

#: The two fixture trees, by exact name.
FIXTURE_NAMES = ("base", "stale")

#: Design section 16's exact case IDs, in corpus order.
CASE_IDS = (
    "unchanged",
    "discovered-scope-reread",
    "discovered-scope-no-reread",
    "stale-snapshot",
    "missing-acknowledgement",
    "exception-needed",
    "root-disappeared",
    "handoff-drift",
    "discovered-conflict-no-reread",
    "discovered-conflict-reread",
    "discovered-exception-no-reread",
    "discovered-exception-approved-reread",
)

#: The four accepted mutations. Any other value is rejected.
MUTATIONS = ("none", "edit_selected_leaf", "remove_root", "make_selected_leaf_stale")

#: The three accepted acknowledgement targets.
ACKNOWLEDGEMENTS = ("none", "initial", "final")

#: The three accepted exception modes.
EXCEPTION_MODES = ("none", "needed_unapproved", "approved")

#: The nine accepted acceptance reasons. Any other value is rejected.
REASONS = (
    "unchanged",
    "planner_reread_required",
    "stale_snapshot",
    "missing_acknowledgement",
    "exception_needed",
    "observed_not_applicable",
    "handoff_drift",
    "conflict_unresolved",
    "approved_exception",
)

#: Eval-only verification status: ``not_run`` names "no applicable Snapshot to
#: verify", which the production enum has no reason to carry.
NOT_RUN = "not_run"
EVAL_VERIFICATION_STATUSES = model.VERIFICATION_STATUSES + (NOT_RUN,)

CASE_KEYS = (
    "acknowledged_snapshot",
    "case_id",
    "discovered",
    "expected",
    "fixture",
    "initial",
    "mutation",
    "planner_reread",
)
STATE_KEYS = ("context_chains", "declared_conflicts", "exception_mode", "scope_paths")
EXPECTED_KEYS = (
    "acceptance",
    "final_diagnostic_codes",
    "final_selected_files",
    "final_status",
    "initial_diagnostic_codes",
    "initial_selected_files",
    "initial_status",
    "reason",
    "verification_status",
)
CONFLICT_KEYS = ("detail", "source", "target")

#: The fixed identity every one of the 12 cases resolves under.
TASK_ID = "TECHSTACK-EVAL-001"
PLAN_ID = "TECHSTACK-EVAL-PLAN-001"
PLAN_VERSION = 1
ATTEMPT_ID = "attempt-1"
AS_OF = "2026-08-24"

#: The one synthesized approval the ``approved`` mode consumes. Its scope and
#: binding digests are produced by the production hash functions from the final
#: input, so neither is frozen here.
APPROVAL_ID = "eval-approval-1"
APPROVAL_AUTHORIZED_BY = "user"
APPROVAL_REFERENCE = "eval://techstack-context-v1/stale-rule-approved"
APPROVAL_DIGEST = "f872fe15b7ac69588e139fe78741c7ba0df6eefa37148f5504a4b00ddb146967"
APPROVAL_ISSUED_ON = "2026-08-24"
APPROVAL_EXPIRES_ON = "2026-09-23"
APPROVAL_REASON = "approved eval stale-rule exception"
APPROVAL_TARGET_CODE = "STALE_RULE"
APPROVAL_TARGET_CONTEXT_ID = "general"

#: The 64 ASCII zeroes the ``handoff-drift`` case substitutes for the packet's
#: acknowledged digest after a successful verification. It is built, never
#: written out, so the no-frozen-digest scan below stays exact.
DRIFTED_ACKNOWLEDGEMENT = "0" * 64

#: The placeholder one approval carries for the single field its own binding
#: digest excludes; the production hash replaces it immediately.
UNBOUND_BINDING = "0" * 64

#: The exact mutation literals, each with its terminal LF and its code-span
#: backticks, each occurring exactly once in the frozen ``general.md`` bytes.
EDIT_SELECTED_LEAF_LINES = (
    (
        "- `GENERAL-001`: Keep project context bounded.\n",
        "- `GENERAL-001`: Keep project context bounded and current.\n",
    ),
)
MAKE_SELECTED_LEAF_STALE_LINES = (
    ("- Reviewed on: `2026-08-01`\n", "- Reviewed on: `2025-01-01`\n"),
    ("- Review within days: `365`\n", "- Review within days: `30`\n"),
)

#: The one leaf both leaf mutations act on, and the one map ``remove_root``
#: unlinks, each relative to the disposable copy.
SELECTED_LEAF = "techstacks/general.md"
ROOT_MAP = model.SNAPSHOT_ROOT_MAP


class EvalCorpusError(ValueError):
    """One strict-loader rejection. The eval never proceeds on a bad corpus."""


# ---------------------------------------------------------------------------
# Strict schema-version-2 loader
# ---------------------------------------------------------------------------


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            raise EvalCorpusError(f"duplicate key: {key}")
        seen.add(key)
    return dict(pairs)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvalCorpusError(message)


def _exact_keys(value: Any, keys: tuple[str, ...], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label}: object required")
    _require(tuple(sorted(value)) == keys, f"{label}: keys must be exactly {list(keys)}")
    return value


def _bool(value: Any, label: str) -> bool:
    _require(type(value) is bool, f"{label}: boolean required")
    return value


def _enum(value: Any, allowed: tuple[str, ...], label: str) -> str:
    _require(value in allowed, f"{label}: {value!r} is not one of {list(allowed)}")
    return value


def _path_list(value: Any, maximum: int, label: str) -> list[str]:
    _require(isinstance(value, list), f"{label}: array required")
    _require(len(value) <= maximum, f"{label}: at most {maximum} entries")
    for index, item in enumerate(value):
        _require(
            model.is_normalized_relative_path(item),
            f"{label}[{index}]: normalized relative path required",
        )
    return value


def _validate_state(value: Any, label: str) -> dict[str, Any]:
    state = _exact_keys(value, STATE_KEYS, label)
    _path_list(state["scope_paths"], model.SCOPE_PATH_COUNT_MAX, f"{label}.scope_paths")

    chains = state["context_chains"]
    _require(isinstance(chains, list), f"{label}.context_chains: array required")
    _require(
        len(chains) <= model.CONTEXT_CHAIN_COUNT_MAX,
        f"{label}.context_chains: at most {model.CONTEXT_CHAIN_COUNT_MAX} chains",
    )
    for index, chain in enumerate(chains):
        pointer = f"{label}.context_chains[{index}]"
        _require(isinstance(chain, list), f"{pointer}: array required")
        _require(
            model.CONTEXT_CHAIN_LENGTH_MIN <= len(chain) <= model.CONTEXT_CHAIN_LENGTH_MAX,
            f"{pointer}: {model.CONTEXT_CHAIN_LENGTH_MIN}"
            f"-{model.CONTEXT_CHAIN_LENGTH_MAX} Context IDs",
        )
        for position, context_id in enumerate(chain):
            _require(
                model.is_context_id(context_id, allow_root=True),
                f"{pointer}[{position}]: Context ID required",
            )

    conflicts = state["declared_conflicts"]
    _require(isinstance(conflicts, list), f"{label}.declared_conflicts: array required")
    _require(
        len(conflicts) <= model.CONFLICT_COUNT_MAX,
        f"{label}.declared_conflicts: at most {model.CONFLICT_COUNT_MAX} records",
    )
    for index, conflict in enumerate(conflicts):
        pointer = f"{label}.declared_conflicts[{index}]"
        record = _exact_keys(conflict, CONFLICT_KEYS, pointer)
        _require(
            model.is_free_text(record["source"], maximum=256),
            f"{pointer}.source: bounded free text required",
        )
        _require(
            model.is_free_text(record["target"], maximum=256),
            f"{pointer}.target: bounded free text required",
        )
        _require(
            model.is_free_text(record["detail"]),
            f"{pointer}.detail: bounded free text required",
        )

    _enum(state["exception_mode"], EXCEPTION_MODES, f"{label}.exception_mode")
    return state


def _validate_expected(value: Any, label: str) -> dict[str, Any]:
    expected = _exact_keys(value, EXPECTED_KEYS, label)
    _enum(expected["initial_status"], model.RESOLUTION_STATUSES, f"{label}.initial_status")
    _enum(expected["final_status"], model.RESOLUTION_STATUSES, f"{label}.final_status")
    _enum(
        expected["verification_status"],
        EVAL_VERIFICATION_STATUSES,
        f"{label}.verification_status",
    )
    for prefix in ("initial", "final"):
        _path_list(
            expected[f"{prefix}_selected_files"],
            model.SELECTED_FILE_LIMIT,
            f"{label}.{prefix}_selected_files",
        )
        codes = expected[f"{prefix}_diagnostic_codes"]
        pointer = f"{label}.{prefix}_diagnostic_codes"
        _require(isinstance(codes, list), f"{pointer}: array required")
        _require(
            len(codes) <= model.DIAGNOSTIC_COUNT_LIMIT,
            f"{pointer}: at most {model.DIAGNOSTIC_COUNT_LIMIT} codes",
        )
        for index, code in enumerate(codes):
            _require(code in DIAGNOSTIC_CODES, f"{pointer}[{index}]: {code!r} is not registered")
    _bool(expected["acceptance"], f"{label}.acceptance")
    _enum(expected["reason"], REASONS, f"{label}.reason")
    return expected


def validate_fixed_constants() -> None:
    """Prove the fixed task/plan/version/attempt/as-of/approval constants.

    Design section 16 states them literally, so a silent drift in this module
    would otherwise resolve a different attempt than the frozen corpus expects.
    """

    _require(TASK_ID == "TECHSTACK-EVAL-001", "task_id constant drifted")
    _require(PLAN_ID == "TECHSTACK-EVAL-PLAN-001", "plan_id constant drifted")
    _require(PLAN_VERSION == 1, "plan_version constant drifted")
    _require(ATTEMPT_ID == "attempt-1", "attempt_id constant drifted")
    _require(AS_OF == "2026-08-24", "as_of constant drifted")
    _require(APPROVAL_ID == "eval-approval-1", "approval_id constant drifted")
    _require(APPROVAL_AUTHORIZED_BY == "user", "authorized_by constant drifted")
    _require(
        APPROVAL_REFERENCE == "eval://techstack-context-v1/stale-rule-approved",
        "authorization_reference constant drifted",
    )
    _require(
        APPROVAL_DIGEST
        == "f872fe15b7ac69588e139fe78741c7ba0df6eefa37148f5504a4b00ddb146967",
        "authorization_digest constant drifted",
    )
    _require(APPROVAL_ISSUED_ON == "2026-08-24", "issued_on constant drifted")
    _require(APPROVAL_EXPIRES_ON == "2026-09-23", "expires_on constant drifted")
    _require(
        APPROVAL_REASON == "approved eval stale-rule exception",
        "approval reason constant drifted",
    )
    _require(APPROVAL_TARGET_CODE == "STALE_RULE", "approval target code drifted")
    _require(
        APPROVAL_TARGET_CONTEXT_ID == "general", "approval target Context ID drifted"
    )
    issued = datetime.date.fromisoformat(APPROVAL_ISSUED_ON)
    expires = datetime.date.fromisoformat(APPROVAL_EXPIRES_ON)
    as_of = datetime.date.fromisoformat(AS_OF)
    _require(
        issued <= as_of <= expires <= issued + datetime.timedelta(days=30),
        "the approval window does not bracket the frozen as-of",
    )


def load_cases(raw: bytes) -> dict[str, Any]:
    """Load and fully validate one schema-version-2 corpus, or raise.

    Nothing here is lenient: an unknown key, an unknown enum value, a duplicate
    key, a wrong count, or an over-cap array stops the eval instead of silently
    reducing what it proves.
    """

    validate_fixed_constants()
    _require(
        len(raw) <= CASES_BYTE_LIMIT,
        f"cases.json: at most {CASES_BYTE_LIMIT} bytes, found {len(raw)}",
    )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise EvalCorpusError(f"cases.json: strict UTF-8 required: {error}") from error
    try:
        document = json.loads(text, object_pairs_hook=_no_duplicate_keys)
    except json.JSONDecodeError as error:
        raise EvalCorpusError(f"cases.json: {error}") from error

    document = _exact_keys(document, ("cases", "schema_version"), "cases.json")
    _require(
        type(document["schema_version"]) is int
        and document["schema_version"] == SCHEMA_VERSION,
        f"cases.json: schema_version must be exactly {SCHEMA_VERSION}",
    )
    cases = document["cases"]
    _require(isinstance(cases, list), "cases.json: cases must be an array")
    _require(
        len(cases) == CASE_COUNT,
        f"cases.json: exactly {CASE_COUNT} cases, found {len(cases)}",
    )

    for index, case in enumerate(cases):
        label = f"cases[{index}]"
        record = _exact_keys(case, CASE_KEYS, label)
        _require(
            model.is_context_id(record["case_id"]),
            f"{label}.case_id: Context-ID spelling required",
        )
        _enum(record["fixture"], FIXTURE_NAMES, f"{label}.fixture")
        _validate_state(record["initial"], f"{label}.initial")
        _validate_state(record["discovered"], f"{label}.discovered")
        _enum(record["mutation"], MUTATIONS, f"{label}.mutation")
        _enum(
            record["acknowledged_snapshot"],
            ACKNOWLEDGEMENTS,
            f"{label}.acknowledged_snapshot",
        )
        _bool(record["planner_reread"], f"{label}.planner_reread")
        _validate_expected(record["expected"], f"{label}.expected")

    identifiers = tuple(case["case_id"] for case in cases)
    _require(
        identifiers == CASE_IDS,
        f"cases.json: case IDs must be exactly {list(CASE_IDS)}",
    )
    return document


def load_corpus(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    """Load the repository corpus after freezing its bytes by digest.

    ``path`` defaults to the repository corpus; the digest guard is the same
    for any other location, so a copy whose bytes differ is refused too.
    """

    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CASES_SHA256:
        raise EvalCorpusError("cases.json: the frozen corpus bytes changed")
    return load_cases(raw)["cases"]


# ---------------------------------------------------------------------------
# Disposable copies and their mutations
# ---------------------------------------------------------------------------


def fixture_files(name: str) -> tuple[str, ...]:
    """Return the frozen member paths of one fixture tree, relative to it."""

    prefix = f"{name}/"
    return tuple(
        member.removeprefix(prefix)
        for member in sorted(FIXTURE_DIGESTS)
        if member.startswith(prefix)
    )


def materialize(fixture: str, destination: Path) -> Path:
    """Copy exactly the frozen fixture files into a fresh disposable root.

    Only the eight inventoried files are ever copied, so nothing else in the
    repository can leak into an observed project root. The empty ``.git``
    directory that makes the copy a project root is created here and nowhere
    else.
    """

    root = destination / "project"
    root.mkdir()
    (root / ".git").mkdir()
    for member in fixture_files(fixture):
        source = FIXTURES_DIR / fixture / member
        target = root / member
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return root


def _replace_lines(
    leaf: Path, pairs: tuple[tuple[str, str], ...], mutation: str
) -> tuple[bytes, bytes]:
    """Replace each exact line once, or fail loudly.

    A replacement that matches nothing would leave the copy pristine and let a
    stale-rule case resolve applicable, so a zero-match source line raises here
    rather than weakening the case downstream.
    """

    before = leaf.read_bytes()
    text = before.decode("utf-8")
    for source, replacement in pairs:
        occurrences = text.count(source)
        if occurrences != 1:
            raise EvalCorpusError(
                f"{mutation}: {source!r} occurs {occurrences} times, expected exactly 1"
            )
        text = text.replace(source, replacement)
    after = text.encode("utf-8")
    if after == before:
        raise EvalCorpusError(f"{mutation}: the copied bytes did not change")
    leaf.write_bytes(after)
    return before, after


def changed_line_count(before: bytes, after: bytes) -> int:
    """Count the differing lines between two copies of the same leaf."""

    old = before.decode("utf-8").splitlines()
    new = after.decode("utf-8").splitlines()
    if len(old) != len(new):
        raise EvalCorpusError("a line mutation changed the line count")
    return sum(1 for left, right in zip(old, new) if left != right)


def apply_mutation(root: Path, mutation: str) -> int:
    """Apply one declared mutation to the copy and return its changed lines.

    ``none`` changes no byte; ``remove_root`` unlinks only the copied root map;
    the two leaf mutations rewrite exactly their own lines of the copied leaf.
    """

    if mutation == "none":
        return 0
    if mutation == "remove_root":
        (root / ROOT_MAP).unlink()
        return 0
    pairs = (
        EDIT_SELECTED_LEAF_LINES
        if mutation == "edit_selected_leaf"
        else MAKE_SELECTED_LEAF_STALE_LINES
    )
    before, after = _replace_lines(root / SELECTED_LEAF, pairs, mutation)
    return changed_line_count(before, after)


# ---------------------------------------------------------------------------
# Production inputs
# ---------------------------------------------------------------------------


def _conflicts(records: list[dict[str, Any]]) -> tuple[DeclaredConflict, ...]:
    return tuple(
        DeclaredConflict(
            source=record["source"], target=record["target"], detail=record["detail"]
        )
        for record in records
    )


def _approval(scope_sha256: str) -> ExceptionApproval:
    """Synthesize the one frozen approval, binding it with production hashes."""

    approval = ExceptionApproval(
        approval_id=APPROVAL_ID,
        coordinator_attested=True,
        authorized_by=APPROVAL_AUTHORIZED_BY,
        authorization_reference=APPROVAL_REFERENCE,
        authorization_digest=APPROVAL_DIGEST,
        task_id=TASK_ID,
        plan_id=PLAN_ID,
        plan_version=PLAN_VERSION,
        attempt_id=ATTEMPT_ID,
        issued_on=APPROVAL_ISSUED_ON,
        expires_on=APPROVAL_EXPIRES_ON,
        target=FailureTarget(
            code=APPROVAL_TARGET_CODE,
            context_id=APPROVAL_TARGET_CONTEXT_ID,
            evidence_path=None,
        ),
        scope_sha256=scope_sha256,
        reason=APPROVAL_REASON,
        binding_sha256=UNBOUND_BINDING,
    )
    return ExceptionApproval(
        **{
            **approval.to_json_object(),
            "target": approval.target,
            "binding_sha256": resolver.binding_digest(approval),
        }
    )


def build_input(
    scope_paths: tuple[str, ...],
    context_chains: tuple[tuple[str, ...], ...],
    declared_conflicts: tuple[DeclaredConflict, ...],
    exception_mode: str,
) -> ResolutionInput:
    """Build one production ResolutionInput for the frozen eval identity.

    The scope digest excludes approvals, so the approval is bound to the
    unapproved shape of the very input it then joins.
    """

    fields = {
        "task_id": TASK_ID,
        "plan_id": PLAN_ID,
        "plan_version": PLAN_VERSION,
        "attempt_id": ATTEMPT_ID,
        "as_of": AS_OF,
        "scope_paths": scope_paths,
        "context_chains": context_chains,
        "declared_conflicts": declared_conflicts,
    }
    unapproved = ResolutionInput(exception_approvals=(), **fields)
    if exception_mode != "approved":
        # ``needed_unapproved`` carries no approval by definition: the need is
        # what the resolver must block on.
        return unapproved
    return ResolutionInput(
        exception_approvals=(_approval(resolver.scope_digest(unapproved)),), **fields
    )


def state_input(state: dict[str, Any]) -> ResolutionInput:
    """Build the initial input from one case's ``initial`` state."""

    return build_input(
        tuple(state["scope_paths"]),
        tuple(tuple(chain) for chain in state["context_chains"]),
        _conflicts(state["declared_conflicts"]),
        state["exception_mode"],
    )


def final_input(initial: dict[str, Any], discovered: dict[str, Any]) -> ResolutionInput:
    """Build the final input as the canonical union of both states.

    Discovered exception mode ``none`` retains the initial mode; any other
    discovered mode replaces it.
    """

    scope_paths = model.canonical_scope_paths(
        tuple(initial["scope_paths"]) + tuple(discovered["scope_paths"])
    )
    chains = model.canonical_context_chains(
        tuple(tuple(chain) for chain in initial["context_chains"])
        + tuple(tuple(chain) for chain in discovered["context_chains"])
    )
    conflicts = _conflicts(initial["declared_conflicts"] + discovered["declared_conflicts"])
    mode = (
        initial["exception_mode"]
        if discovered["exception_mode"] == "none"
        else discovered["exception_mode"]
    )
    return build_input(scope_paths, chains, conflicts, mode)


def has_h3_trigger(discovered: dict[str, Any]) -> bool:
    """A H3 trigger exists iff discovery added any dimension at all."""

    return bool(
        discovered["scope_paths"]
        or discovered["context_chains"]
        or discovered["declared_conflicts"]
        or discovered["exception_mode"] != "none"
    )


# ---------------------------------------------------------------------------
# Test-only policy oracle
# ---------------------------------------------------------------------------


class Observation:
    """One case's complete production evidence plus the policy verdict.

    Every production field is read from the real Resolution and Verification
    objects. The two acceptance fields — ``reason`` and ``acceptance`` — are
    this eval's own coordinator-policy judgement and exist nowhere in
    ``src/brichan``.
    """

    def __init__(
        self,
        initial: Resolution,
        final: Resolution,
        verification: Verification | None,
        acknowledged_digest: str | None,
        reason: str,
    ) -> None:
        self.initial = initial
        self.final = final
        self.verification = verification
        self.acknowledged_digest = acknowledged_digest
        self.reason = reason
        self.acceptance = reason in ("unchanged", "approved_exception")

    @property
    def verification_status(self) -> str:
        return NOT_RUN if self.verification is None else self.verification.status

    @staticmethod
    def selected(resolution: Resolution) -> tuple[str, ...]:
        if resolution.snapshot is None:
            return ()
        return tuple(record.path for record in resolution.snapshot.selected_files)

    @staticmethod
    def codes(resolution: Resolution) -> tuple[str, ...]:
        return tuple(record.code for record in resolution.diagnostics)


def _acknowledged_snapshot(case: dict[str, Any], initial: Resolution, final: Resolution):
    """Return the Snapshot the packet acknowledged, or None.

    ``none`` acknowledges nothing, so the eval still verifies the latest
    applicable Snapshot to prove the project itself is intact; the missing
    acknowledgement is a separate, policy-level failure.
    """

    if case["acknowledged_snapshot"] == "initial":
        return initial.snapshot
    return final.snapshot


def decide(
    case: dict[str, Any],
    final: Resolution,
    verification: Verification | None,
    acknowledged_digest: str | None,
) -> str:
    """Return the coordinator-policy reason for one case.

    Design section 16's precedence is exact: the planner-reread gate closes
    before any digest, verification, conflict, or exception check, so a case
    that skipped the reread reports that and nothing else even when the
    eventual resolution would have blocked anyway.
    """

    trigger = has_h3_trigger(case["discovered"])
    if trigger != case["planner_reread"]:
        return "planner_reread_required"
    if final.status == "not_applicable":
        return "observed_not_applicable"
    if final.status == "blocked":
        if any(record.code == "DECLARED_AUTHORITY_CONFLICT" for record in final.diagnostics):
            return "conflict_unresolved"
        return "exception_needed"
    if case["acknowledged_snapshot"] == "none":
        return "missing_acknowledgement"
    if verification is None or verification.status != "match":
        return "stale_snapshot"
    final_digest = final.snapshot.snapshot_sha256
    if acknowledged_digest != final_digest:
        return "handoff_drift"
    if any(record.waived_by is not None for record in final.diagnostics):
        return "approved_exception"
    return "unchanged"


def observe(case: dict[str, Any], workspace: Path) -> Observation:
    """Run one case end to end inside one disposable copy.

    Initial resolution always precedes discovery and mutation; final resolution
    always follows both.
    """

    root = materialize(case["fixture"], workspace)
    initial = resolve_context(state_input(case["initial"]), root)
    apply_mutation(root, case["mutation"])
    final = resolve_context(final_input(case["initial"], case["discovered"]), root)

    snapshot = _acknowledged_snapshot(case, initial, final)
    verification = (
        None
        if snapshot is None
        else verify_snapshot(snapshot, root, datetime.date.fromisoformat(AS_OF))
    )
    acknowledged_digest: str | None = None
    if case["acknowledged_snapshot"] != "none" and snapshot is not None:
        acknowledged_digest = snapshot.snapshot_sha256
    if case["case_id"] == "handoff-drift":
        # The one case where a successful verification is followed by a packet
        # whose acknowledgement names no Snapshot this attempt ever produced.
        acknowledged_digest = DRIFTED_ACKNOWLEDGEMENT
    reason = decide(case, final, verification, acknowledged_digest)
    return Observation(initial, final, verification, acknowledged_digest, reason)


def temporary_root() -> Path:
    """Return a disposable directory whose path contains no symlink."""

    return Path(os.path.realpath(tempfile.mkdtemp()))


class WorkspaceMixin:
    """One disposable workspace per test, removed however the test ends."""

    def setUp(self):
        super().setUp()
        self.workspace = temporary_root()
        self.addCleanup(shutil.rmtree, self.workspace, ignore_errors=True)


def repository_fixture_digests() -> dict[str, str]:
    """Hash every repository fixture file exactly as it stands right now."""

    return {
        member: hashlib.sha256((FIXTURES_DIR / member).read_bytes()).hexdigest()
        for member in sorted(FIXTURE_DIGESTS)
    }


# ---------------------------------------------------------------------------
# Frozen bytes
# ---------------------------------------------------------------------------


class FrozenBytesTest(unittest.TestCase):
    """The corpus and all eight fixture blocks are frozen by digest."""

    def test_the_corpus_matches_its_frozen_digest_and_byte_count(self):
        raw = CASES_PATH.read_bytes()
        self.assertEqual(CASES_BYTE_COUNT, len(raw))
        self.assertEqual(CASES_SHA256, hashlib.sha256(raw).hexdigest())
        self.assertLessEqual(len(raw), CASES_BYTE_LIMIT)

    def test_every_fixture_file_matches_its_frozen_digest_and_byte_count(self):
        for member, digest in sorted(FIXTURE_DIGESTS.items()):
            with self.subTest(member=member):
                raw = (FIXTURES_DIR / member).read_bytes()
                self.assertEqual(FIXTURE_BYTE_COUNTS[member], len(raw))
                self.assertEqual(digest, hashlib.sha256(raw).hexdigest())

    def test_the_fixture_tree_holds_exactly_the_eight_frozen_files(self):
        present = {
            path.relative_to(FIXTURES_DIR).as_posix()
            for path in FIXTURES_DIR.rglob("*")
            if path.is_file()
        }
        self.assertEqual(set(FIXTURE_DIGESTS), present)

    def test_no_fixture_carries_a_bom_a_cr_or_a_trailing_space(self):
        for member in sorted(FIXTURE_DIGESTS):
            with self.subTest(member=member):
                raw = (FIXTURES_DIR / member).read_bytes()
                self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
                self.assertNotIn(b"\r", raw)
                self.assertTrue(raw.endswith(b"\n"))
                for line in raw.decode("utf-8").splitlines():
                    self.assertEqual(line.rstrip(), line)

    def test_each_mutation_literal_occurs_exactly_once_in_the_frozen_leaf(self):
        """The version-6 literals matched nothing; these must match once each."""

        text = (FIXTURES_DIR / "base" / SELECTED_LEAF).read_text(encoding="utf-8")
        for source, _ in EDIT_SELECTED_LEAF_LINES + MAKE_SELECTED_LEAF_STALE_LINES:
            with self.subTest(source=source):
                self.assertEqual(1, text.count(source))
        for superseded in ("Reviewed on: 2026-08-01", "Review within days: 365"):
            with self.subTest(superseded=superseded):
                self.assertEqual(0, text.count(superseded))


# ---------------------------------------------------------------------------
# Strict loader
# ---------------------------------------------------------------------------


class LoaderTest(unittest.TestCase):
    """The loader accepts exactly Design section 16's corpus and nothing else."""

    def setUp(self):
        super().setUp()
        self.raw = CASES_PATH.read_bytes()
        self.document = json.loads(self.raw.decode("utf-8"))

    def encode(self, document: Any) -> bytes:
        return json.dumps(document).encode("utf-8")

    def rejects(self, raw: bytes, needle: str) -> None:
        with self.assertRaises(EvalCorpusError) as caught:
            load_cases(raw)
        self.assertIn(needle, str(caught.exception))

    def test_the_frozen_corpus_loads(self):
        document = load_cases(self.raw)
        self.assertEqual(SCHEMA_VERSION, document["schema_version"])
        self.assertEqual(CASE_COUNT, len(document["cases"]))
        self.assertEqual(CASE_IDS, tuple(case["case_id"] for case in document["cases"]))

    def test_the_fixed_constants_are_the_frozen_ones(self):
        validate_fixed_constants()
        self.assertEqual(
            (TASK_ID, PLAN_ID, PLAN_VERSION, ATTEMPT_ID, AS_OF),
            ("TECHSTACK-EVAL-001", "TECHSTACK-EVAL-PLAN-001", 1, "attempt-1", "2026-08-24"),
        )

    def test_an_over_cap_document_is_rejected_before_it_is_parsed(self):
        padded = b" " * (CASES_BYTE_LIMIT + 1)
        self.rejects(padded, "at most 32768 bytes")

    def test_invalid_utf8_is_rejected(self):
        self.rejects(b"\xff\xfe{}", "strict UTF-8 required")

    def test_a_duplicate_key_is_rejected(self):
        self.rejects(
            b'{"schema_version": 2, "schema_version": 2, "cases": []}',
            "duplicate key: schema_version",
        )

    def test_a_duplicate_key_inside_one_case_is_rejected(self):
        text = self.raw.decode("utf-8").replace(
            '"case_id":"unchanged"', '"case_id":"unchanged","case_id":"unchanged"', 1
        )
        self.rejects(text.encode("utf-8"), "duplicate key: case_id")

    def test_schema_version_one_is_rejected(self):
        document = dict(self.document, schema_version=1)
        self.rejects(self.encode(document), "schema_version must be exactly 2")

    def test_a_boolean_schema_version_is_rejected(self):
        document = dict(self.document, schema_version=True)
        self.rejects(self.encode(document), "schema_version must be exactly 2")

    def test_an_extra_top_level_key_is_rejected(self):
        document = dict(self.document, notes="extra")
        self.rejects(self.encode(document), "keys must be exactly")

    def test_eleven_and_thirteen_cases_are_both_rejected(self):
        short = dict(self.document, cases=self.document["cases"][:-1])
        self.rejects(self.encode(short), "exactly 12 cases, found 11")
        long = dict(self.document, cases=self.document["cases"] + [self.document["cases"][0]])
        self.rejects(self.encode(long), "exactly 12 cases, found 13")

    def test_an_unknown_mutation_is_rejected(self):
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["mutation"] = "delete_everything"
        self.rejects(self.encode(document), "is not one of")

    def test_every_accepted_mutation_is_exactly_the_four(self):
        self.assertEqual(
            ("none", "edit_selected_leaf", "remove_root", "make_selected_leaf_stale"),
            MUTATIONS,
        )
        for mutation in MUTATIONS:
            with self.subTest(mutation=mutation):
                document = json.loads(self.raw.decode("utf-8"))
                document["cases"][0]["mutation"] = mutation
                load_cases(self.encode(document))

    def test_an_unknown_reason_is_rejected(self):
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["expected"]["reason"] = "looked_fine"
        self.rejects(self.encode(document), "is not one of")

    def test_every_accepted_reason_is_exactly_the_nine(self):
        self.assertEqual(9, len(REASONS))
        for reason in REASONS:
            with self.subTest(reason=reason):
                document = json.loads(self.raw.decode("utf-8"))
                document["cases"][0]["expected"]["reason"] = reason
                load_cases(self.encode(document))

    def test_an_unknown_acknowledgement_or_exception_mode_is_rejected(self):
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["acknowledged_snapshot"] = "latest"
        self.rejects(self.encode(document), "is not one of")
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["discovered"]["exception_mode"] = "maybe"
        self.rejects(self.encode(document), "is not one of")

    def test_an_unknown_status_or_diagnostic_code_is_rejected(self):
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["expected"]["final_status"] = "fine"
        self.rejects(self.encode(document), "is not one of")
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["expected"]["final_diagnostic_codes"] = ["NOT_A_CODE"]
        self.rejects(self.encode(document), "is not registered")

    def test_the_eval_only_not_run_verification_status_is_accepted(self):
        self.assertIn(NOT_RUN, EVAL_VERIFICATION_STATUSES)
        self.assertNotIn(NOT_RUN, model.VERIFICATION_STATUSES)

    def test_a_missing_or_extra_case_key_is_rejected(self):
        document = json.loads(self.raw.decode("utf-8"))
        del document["cases"][0]["fixture"]
        self.rejects(self.encode(document), "keys must be exactly")
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["note"] = "extra"
        self.rejects(self.encode(document), "keys must be exactly")

    def test_the_initial_and_discovered_states_are_separately_validated(self):
        for side in ("initial", "discovered"):
            with self.subTest(side=side):
                document = json.loads(self.raw.decode("utf-8"))
                del document["cases"][0][side]["declared_conflicts"]
                self.rejects(self.encode(document), f"cases[0].{side}: keys must be exactly")

    def test_an_expected_key_may_not_be_missing(self):
        document = json.loads(self.raw.decode("utf-8"))
        del document["cases"][0]["expected"]["acceptance"]
        self.rejects(self.encode(document), "cases[0].expected: keys must be exactly")

    def test_the_scope_chain_conflict_and_selected_file_caps_are_enforced(self):
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["initial"]["scope_paths"] = [
            f"file-{index}.md" for index in range(model.SCOPE_PATH_COUNT_MAX + 1)
        ]
        self.rejects(self.encode(document), "at most 64 entries")

        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["initial"]["context_chains"] = [
            ["general"] for _ in range(model.CONTEXT_CHAIN_COUNT_MAX + 1)
        ]
        self.rejects(self.encode(document), "at most 32 chains")

        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["initial"]["context_chains"] = [
            ["general"] * (model.CONTEXT_CHAIN_LENGTH_MAX + 1)
        ]
        self.rejects(self.encode(document), "1-6 Context IDs")

        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["initial"]["context_chains"] = [[]]
        self.rejects(self.encode(document), "1-6 Context IDs")

        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["expected"]["final_selected_files"] = [
            f"techstacks/leaf-{index}.md" for index in range(model.SELECTED_FILE_LIMIT + 1)
        ]
        self.rejects(self.encode(document), "at most 12 entries")

        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["expected"]["final_diagnostic_codes"] = [
            "STALE_RULE"
        ] * (model.DIAGNOSTIC_COUNT_LIMIT + 1)
        self.rejects(self.encode(document), "at most 128 codes")

    def test_an_unnormalized_path_is_rejected(self):
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["initial"]["scope_paths"] = ["../escape.md"]
        self.rejects(self.encode(document), "normalized relative path required")

    def test_a_declared_conflict_needs_exactly_its_three_fields(self):
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["discovered"]["declared_conflicts"] = [
            {"source": "GENERAL-001", "target": "GENERAL-002"}
        ]
        self.rejects(self.encode(document), "keys must be exactly")

    def test_a_non_boolean_planner_reread_or_acceptance_is_rejected(self):
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["planner_reread"] = "true"
        self.rejects(self.encode(document), "boolean required")
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["expected"]["acceptance"] = 1
        self.rejects(self.encode(document), "boolean required")

    def test_an_unknown_fixture_name_is_rejected(self):
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["fixture"] = "other"
        self.rejects(self.encode(document), "is not one of")

    def test_a_reordered_or_renamed_case_id_set_is_rejected(self):
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0]["case_id"] = "renamed"
        self.rejects(self.encode(document), "case IDs must be exactly")
        document = json.loads(self.raw.decode("utf-8"))
        document["cases"][0], document["cases"][1] = (
            document["cases"][1],
            document["cases"][0],
        )
        self.rejects(self.encode(document), "case IDs must be exactly")

    def test_a_changed_repository_corpus_stops_the_eval(self):
        """A corpus whose bytes differ is refused by the digest rule itself.

        The padded copy is still valid JSON that ``load_cases`` would accept,
        so only the digest guard in ``load_corpus`` can reject it.
        """

        self.assertEqual(CASE_COUNT, len(load_corpus()))
        workspace = temporary_root()
        self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
        padded = workspace / "cases.json"
        padded.write_bytes(self.raw + b"\n")
        self.assertNotEqual(self.raw, padded.read_bytes())
        load_cases(padded.read_bytes())
        with self.assertRaises(
            EvalCorpusError, msg="the digest rule did not refuse a changed corpus"
        ) as caught:
            load_corpus(padded)
        self.assertIn("the frozen corpus bytes changed", str(caught.exception))


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


class MutationTest(WorkspaceMixin, unittest.TestCase):
    """Every mutation provably changes the copy, and only the copy."""

    def test_none_changes_no_byte_of_the_copy(self):
        root = materialize("base", self.workspace)
        before = (root / SELECTED_LEAF).read_bytes()
        self.assertEqual(0, apply_mutation(root, "none"))
        self.assertEqual(before, (root / SELECTED_LEAF).read_bytes())

    def test_edit_selected_leaf_changes_exactly_one_line(self):
        root = materialize("base", self.workspace)
        fixture = (FIXTURES_DIR / "base" / SELECTED_LEAF).read_bytes()
        self.assertEqual(1, apply_mutation(root, "edit_selected_leaf"))
        mutated = (root / SELECTED_LEAF).read_bytes()
        self.assertNotEqual(fixture, mutated)
        self.assertIn(b"bounded and current.", mutated)

    def test_make_selected_leaf_stale_changes_exactly_two_lines(self):
        root = materialize("base", self.workspace)
        fixture = (FIXTURES_DIR / "base" / SELECTED_LEAF).read_bytes()
        self.assertEqual(2, apply_mutation(root, "make_selected_leaf_stale"))
        mutated = (root / SELECTED_LEAF).read_bytes()
        self.assertNotEqual(fixture, mutated)
        self.assertIn(b"- Reviewed on: `2025-01-01`\n", mutated)
        self.assertIn(b"- Review within days: `30`\n", mutated)

    def test_a_replacement_that_matches_nothing_fails_loudly(self):
        root = materialize("base", self.workspace)
        leaf = root / SELECTED_LEAF
        before = leaf.read_bytes()
        with self.assertRaises(EvalCorpusError) as caught:
            _replace_lines(leaf, (("- Reviewed on: 2026-08-01\n", "x\n"),), "version_6")
        self.assertIn("occurs 0 times", str(caught.exception))
        self.assertEqual(before, leaf.read_bytes())

    def test_the_stale_leaf_yields_stale_rule_and_no_future_review_date(self):
        root = materialize("base", self.workspace)
        apply_mutation(root, "make_selected_leaf_stale")
        resolution = resolve_context(build_input(("README.md",), (), (), "none"), root)
        self.assertEqual("blocked", resolution.status)
        codes = tuple(record.code for record in resolution.diagnostics)
        self.assertEqual(("STALE_RULE",), codes)
        self.assertNotIn("FUTURE_REVIEW_DATE", codes)
        self.assertEqual(
            APPROVAL_TARGET_CONTEXT_ID, resolution.diagnostics[0].context_id
        )

    def test_remove_root_unlinks_only_the_copied_root_map(self):
        root = materialize("base", self.workspace)
        apply_mutation(root, "remove_root")
        self.assertFalse((root / ROOT_MAP).exists())
        self.assertTrue((root / SELECTED_LEAF).is_file())
        self.assertTrue((root / "evidence" / "button.txt").is_file())

    def test_a_mutated_copy_leaves_the_repository_fixtures_untouched(self):
        before = repository_fixture_digests()
        for mutation in MUTATIONS:
            with self.subTest(mutation=mutation):
                workspace = temporary_root()
                self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
                apply_mutation(materialize("base", workspace), mutation)
        self.assertEqual(before, repository_fixture_digests())
        self.assertEqual(
            FIXTURE_DIGESTS, {member: digest for member, digest in before.items()}
        )


class DisposableCopyTest(WorkspaceMixin, unittest.TestCase):
    """The copy holds the fixture files plus ``.git``, and nothing else."""

    def test_the_copy_holds_only_the_frozen_files_and_an_empty_git_directory(self):
        root = materialize("base", self.workspace)
        self.assertTrue((root / ".git").is_dir())
        self.assertEqual([], list((root / ".git").iterdir()))
        copied = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(set(fixture_files("base")), copied)

    def test_the_copy_is_outside_the_repository(self):
        root = materialize("stale", self.workspace)
        self.assertNotIn(REPOSITORY_ROOT, root.parents)


# ---------------------------------------------------------------------------
# The 12 frozen cases
# ---------------------------------------------------------------------------


class CorpusTest(WorkspaceMixin, unittest.TestCase):
    """All 12 cases reproduce the frozen production evidence and verdicts."""

    def setUp(self):
        super().setUp()
        self.cases = load_corpus()
        self.before = repository_fixture_digests()
        self.addCleanup(
            lambda: self.assertEqual(self.before, repository_fixture_digests())
        )

    def observe(self, case: dict[str, Any]) -> Observation:
        workspace = temporary_root()
        self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
        return observe(case, workspace)

    def test_every_case_matches_its_frozen_production_evidence(self):
        for case in self.cases:
            with self.subTest(case=case["case_id"]):
                observation = self.observe(case)
                expected = case["expected"]
                self.assertEqual(expected["initial_status"], observation.initial.status)
                self.assertEqual(expected["final_status"], observation.final.status)
                self.assertEqual(
                    tuple(expected["initial_selected_files"]),
                    Observation.selected(observation.initial),
                )
                self.assertEqual(
                    tuple(expected["final_selected_files"]),
                    Observation.selected(observation.final),
                )
                self.assertEqual(
                    tuple(expected["initial_diagnostic_codes"]),
                    Observation.codes(observation.initial),
                )
                self.assertEqual(
                    tuple(expected["final_diagnostic_codes"]),
                    Observation.codes(observation.final),
                )
                self.assertEqual(
                    expected["verification_status"], observation.verification_status
                )

    def test_every_case_matches_its_frozen_acceptance_and_reason(self):
        for case in self.cases:
            with self.subTest(case=case["case_id"]):
                observation = self.observe(case)
                self.assertEqual(case["expected"]["reason"], observation.reason)
                self.assertEqual(case["expected"]["acceptance"], observation.acceptance)

    def test_the_corpus_freezes_exactly_three_accepted_cases(self):
        """A corpus-shape assertion: the observed verdicts are proven above."""

        accepted = [
            case["case_id"] for case in self.cases if case["expected"]["acceptance"]
        ]
        self.assertEqual(3, len(accepted))
        self.assertEqual(
            [
                "unchanged",
                "discovered-scope-reread",
                "discovered-exception-approved-reread",
            ],
            accepted,
        )

    def test_no_expected_snapshot_digest_is_stored_anywhere(self):
        """Root identity varies, so every digest check is relational."""

        source = Path(__file__).read_bytes() + CASES_PATH.read_bytes()
        digests = set(re.findall(rb"\b[0-9a-f]{64}\b", source))
        self.assertEqual(
            {APPROVAL_DIGEST.encode("ascii"), CASES_SHA256.encode("ascii")}
            | {digest.encode("ascii") for digest in FIXTURE_DIGESTS.values()},
            digests,
        )
        # The two all-zero digests are built, not written out, so no literal
        # Snapshot digest can hide behind them either.
        self.assertNotIn(DRIFTED_ACKNOWLEDGEMENT.encode("ascii"), source)
        self.assertNotIn(UNBOUND_BINDING.encode("ascii"), source)


class OracleTest(WorkspaceMixin, unittest.TestCase):
    """The policy oracle's own precedence and its three positive proofs."""

    def setUp(self):
        super().setUp()
        self.cases = {case["case_id"]: case for case in load_corpus()}

    def observe(self, case_id: str) -> Observation:
        workspace = temporary_root()
        self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
        return observe(self.cases[case_id], workspace)

    def test_a_h3_trigger_exists_for_every_discovered_dimension(self):
        empty = {
            "scope_paths": [],
            "context_chains": [],
            "declared_conflicts": [],
            "exception_mode": "none",
        }
        self.assertFalse(has_h3_trigger(empty))
        for key, value in (
            ("scope_paths", ["src/frontend/components/Button.tsx"]),
            ("context_chains", [["general"]]),
            (
                "declared_conflicts",
                [{"source": "A", "target": "B", "detail": "conflict"}],
            ),
            ("exception_mode", "needed_unapproved"),
            ("exception_mode", "approved"),
        ):
            with self.subTest(key=key, value=value):
                self.assertTrue(has_h3_trigger({**empty, key: value}))

    def test_the_reread_gate_closes_before_the_conflict_and_exception_checks(self):
        """Both no-reread cases block downstream, and both report the gate."""

        for case_id in (
            "discovered-conflict-no-reread",
            "discovered-exception-no-reread",
        ):
            with self.subTest(case=case_id):
                observation = self.observe(case_id)
                self.assertEqual("blocked", observation.final.status)
                self.assertEqual("planner_reread_required", observation.reason)
                self.assertFalse(observation.acceptance)

    def test_the_same_cases_with_the_reread_report_their_real_outcome(self):
        conflict = self.observe("discovered-conflict-reread")
        self.assertEqual("conflict_unresolved", conflict.reason)
        self.assertFalse(conflict.acceptance)
        self.assertIn(
            "DECLARED_AUTHORITY_CONFLICT", Observation.codes(conflict.final)
        )

    def test_a_scope_discovery_without_the_reread_is_rejected_though_it_resolves(self):
        observation = self.observe("discovered-scope-no-reread")
        self.assertEqual("applicable", observation.final.status)
        self.assertEqual("match", observation.verification_status)
        self.assertEqual("planner_reread_required", observation.reason)
        self.assertFalse(observation.acceptance)

    def test_the_approved_exception_is_consumed_acknowledged_and_verified(self):
        observation = self.observe("discovered-exception-approved-reread")
        self.assertEqual("applicable", observation.final.status)
        waivers = tuple(record.waived_by for record in observation.final.diagnostics)
        self.assertEqual((APPROVAL_ID,), waivers)
        self.assertEqual(
            ("warning",),
            tuple(record.severity for record in observation.final.diagnostics),
        )
        self.assertEqual("match", observation.verification_status)
        self.assertEqual(
            observation.final.snapshot.snapshot_sha256, observation.acknowledged_digest
        )
        self.assertEqual("approved_exception", observation.reason)
        self.assertTrue(observation.acceptance)

    def test_the_unapproved_need_blocks_before_any_approval_is_synthesized(self):
        observation = self.observe("exception-needed")
        self.assertEqual("blocked", observation.final.status)
        self.assertEqual(("STALE_RULE",), Observation.codes(observation.final))
        self.assertEqual(NOT_RUN, observation.verification_status)
        self.assertEqual("exception_needed", observation.reason)

    def test_a_missing_acknowledgement_is_rejected_though_the_project_verifies(self):
        observation = self.observe("missing-acknowledgement")
        self.assertEqual("match", observation.verification_status)
        self.assertIsNone(observation.acknowledged_digest)
        self.assertEqual("missing_acknowledgement", observation.reason)

    def test_an_acknowledged_superseded_snapshot_is_stale_not_drift(self):
        observation = self.observe("stale-snapshot")
        self.assertEqual("drift", observation.verification_status)
        self.assertNotEqual(
            observation.final.snapshot.snapshot_sha256, observation.acknowledged_digest
        )
        self.assertEqual("stale_snapshot", observation.reason)

    def test_a_foreign_acknowledgement_after_a_match_is_handoff_drift(self):
        observation = self.observe("handoff-drift")
        self.assertEqual("match", observation.verification_status)
        self.assertEqual(DRIFTED_ACKNOWLEDGEMENT, observation.acknowledged_digest)
        self.assertNotEqual(
            observation.final.snapshot.snapshot_sha256, observation.acknowledged_digest
        )
        self.assertEqual("handoff_drift", observation.reason)

    def test_a_disappeared_root_is_observed_not_applicable(self):
        observation = self.observe("root-disappeared")
        self.assertEqual("applicable", observation.initial.status)
        self.assertEqual("not_applicable", observation.final.status)
        self.assertEqual("drift", observation.verification_status)
        self.assertEqual("observed_not_applicable", observation.reason)

    def test_the_oracle_is_the_evals_own_judgement_and_not_production(self):
        """No production module exposes an acceptance verdict for this eval."""

        import brichan.techstacks as techstacks

        for name in ("decide", "observe", "has_h3_trigger", "Observation"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(techstacks, name))


if __name__ == "__main__":
    unittest.main()
