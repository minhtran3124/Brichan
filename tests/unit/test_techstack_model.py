"""Frozen techstack model, registry, bound, and overflow vectors.

Every literal in this module is copied from the accepted design: the two
ordered caller-error vectors, the 58-row Diagnostic registry, the six-code
Difference registry, and every fixed detail string. Nothing here reconstructs
an order or a message from prose.
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.techstacks import model


#: Design section 4, copied literally. The order is normative.
DESIGN_INPUT_ERROR_CODES = (
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

#: Design section 4, copied literally. The order is normative.
DESIGN_SNAPSHOT_ERROR_CODES = (
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

#: Design section 4 registry rows: (rank, code, fields, severity, waivable).
DESIGN_DIAGNOSTIC_ROWS = (
    (1, "UNSUPPORTED_PLATFORM", "G", "error", False),
    (2, "UNSUPPORTED_SAFE_OPEN", "G", "error", False),
    (3, "ROOT_CHANGED", "G", "error", False),
    (4, "PATH_COMPONENT_NOT_DIRECTORY", "P", "error", False),
    (5, "SYMLINK_REJECTED", "P", "error", False),
    (6, "DIRECTORY_REJECTED", "P", "error", False),
    (7, "FIFO_REJECTED", "P", "error", False),
    (8, "SOCKET_REJECTED", "P", "error", False),
    (9, "DEVICE_REJECTED", "P", "error", False),
    (10, "NON_REGULAR_REJECTED", "P", "error", False),
    (11, "UNREADABLE_FILE", "P", "error", False),
    (12, "SPECIAL_FILE_UNAVAILABLE", "P", "error", False),
    (13, "FILESYSTEM_IO_ERROR", "P", "error", False),
    (14, "FILESYSTEM_ERROR", "P", "error", False),
    (15, "RESOURCE_LIMIT", "G", "error", False),
    (16, "FILE_CHANGED", "P", "error", False),
    (17, "OS_METADATA_RANGE", "P", "error", False),
    (18, "MISSING_RULE_FILE", "P", "error", False),
    (19, "MAP_BYTE_LIMIT", "P", "error", False),
    (20, "LEAF_BYTE_LIMIT", "P", "error", False),
    (21, "EVIDENCE_BYTE_LIMIT", "C", "error", False),
    (22, "EVIDENCE_FILE_LIMIT", "G", "error", False),
    (23, "EVIDENCE_AGGREGATE_BYTE_LIMIT", "G", "error", False),
    (24, "INVALID_MAP", "P", "error", False),
    (25, "INVALID_LEAF", "P", "error", False),
    (26, "MAP_ROW_LIMIT", "P", "error", False),
    (27, "SELECTOR_LIMIT", "C", "error", False),
    (28, "MAP_DEPTH_LIMIT", "G", "error", False),
    (29, "SELECTED_FILE_LIMIT", "G", "error", False),
    (30, "SELECTED_BYTE_LIMIT", "G", "error", False),
    (31, "DUPLICATE_CONTEXT_ID", "C", "error", False),
    (32, "ROW_CHILD_ID_MISMATCH", "C", "error", False),
    (33, "DUPLICATE_RULE_PATH", "C", "error", False),
    (34, "CONTEXT_CYCLE", "C", "error", False),
    (35, "UNREACHABLE_CONTEXT", "G", "error", False),
    (36, "EFFECTIVE_RULE_LIMIT", "G", "error", False),
    (37, "PEER_RULE_CONFLICT", "C", "error", False),
    (38, "NON_NEAREST_OVERRIDE", "C", "error", False),
    (39, "INVALID_OVERRIDE", "C", "error", False),
    (40, "DECLARED_AUTHORITY_CONFLICT", "G", "error", False),
    (41, "FUTURE_REVIEW_DATE", "C", "error", False),
    (42, "STALE_RULE", "C", "error", True),
    (43, "DEPRECATED_RULE", "C", "error", True),
    (44, "MISSING_EVIDENCE", "T", "error", True),
    (45, "UNATTESTED_EXCEPTION", "T", "error", False),
    (46, "INVALID_EXCEPTION_PROVENANCE", "T", "error", False),
    (47, "EXCEPTION_BINDING_MISMATCH", "T", "error", False),
    (48, "EXCEPTION_EXPIRED", "T", "error", False),
    (49, "EXCEPTION_DIGEST_MISMATCH", "T", "error", False),
    (50, "UNUSED_EXCEPTION", "T", "error", False),
    (51, "AMBIGUOUS_EXCEPTION", "T", "error", False),
    (52, "UNUSED_INPUT_WITHOUT_ROOT", "G", "error", False),
    (53, "SNAPSHOT_BYTE_LIMIT", "G", "error", False),
    (54, "DIAGNOSTIC_LIMIT", "G", "error", False),
    (55, "SAFE_OPEN_HELPER_TIMEOUT", "P", "error", False),
    (56, "SAFE_OPEN_HELPER_FAILED", "P", "error", False),
    (57, "SAFE_OPEN_HELPER_LEAK", "P", "error", False),
    (58, "SAFE_OPEN_HELPER_BUSY", "P", "error", False),
)

#: Design section 14 exact diagnostic details, copied literally.
DESIGN_DIAGNOSTIC_DETAILS = {
    "UNSUPPORTED_PLATFORM": "techstacks is unsupported on this platform",
    "UNSUPPORTED_SAFE_OPEN": "required safe-open semantics are unavailable",
    "ROOT_CHANGED": "project root identity changed during resolution",
    "PATH_COMPONENT_NOT_DIRECTORY": "an intermediate path component is not a directory",
    "SYMLINK_REJECTED": "a symbolic link is not permitted",
    "DIRECTORY_REJECTED": "a regular file was required but a directory was observed",
    "FIFO_REJECTED": "a FIFO is not permitted",
    "SOCKET_REJECTED": "a socket is not permitted",
    "DEVICE_REJECTED": "a device is not permitted",
    "NON_REGULAR_REJECTED": "an unsupported nonregular entry was observed",
    "UNREADABLE_FILE": "a required file could not be read",
    "SPECIAL_FILE_UNAVAILABLE": "a special entry could not be safely inspected",
    "FILESYSTEM_IO_ERROR": "filesystem I/O failed",
    "FILESYSTEM_ERROR": "filesystem operation failed with errno <decimal-or--1>",
    "RESOURCE_LIMIT": "a process filesystem resource was exhausted",
    "FILE_CHANGED": "file identity or content changed during observation",
    "OS_METADATA_RANGE": "filesystem metadata is outside the supported integer range",
    "MISSING_RULE_FILE": "a selected rule file is missing",
    "MAP_BYTE_LIMIT": "map file exceeds 65536 bytes",
    "LEAF_BYTE_LIMIT": "leaf file exceeds 65536 bytes",
    "EVIDENCE_BYTE_LIMIT": "evidence file exceeds 1048576 bytes",
    "EVIDENCE_FILE_LIMIT": "evidence file count exceeds 64",
    "EVIDENCE_AGGREGATE_BYTE_LIMIT": "evidence bytes exceed 8388608",
    "INVALID_MAP": "map bytes do not match the map grammar",
    "INVALID_LEAF": "leaf bytes do not match the leaf grammar at line <decimal-or-0>: <leaf-rule>",
    "MAP_ROW_LIMIT": "map row count exceeds 32",
    "SELECTOR_LIMIT": "map row selector count exceeds 16",
    "MAP_DEPTH_LIMIT": "selected map depth exceeds 6",
    "SELECTED_FILE_LIMIT": "selected file count exceeds 12",
    "SELECTED_BYTE_LIMIT": "selected map and leaf bytes exceed 65536",
    "DUPLICATE_CONTEXT_ID": "a Context ID occurs more than once",
    "ROW_CHILD_ID_MISMATCH": "map row and child Context IDs differ",
    "DUPLICATE_RULE_PATH": "a selected rule path occurs more than once",
    "CONTEXT_CYCLE": "selected map graph contains a cycle",
    "UNREACHABLE_CONTEXT": "requested Context ID chain is not exactly reachable",
    "EFFECTIVE_RULE_LIMIT": "effective rule count exceeds 384",
    "PEER_RULE_CONFLICT": "overlapping peer rules use the same Rule ID",
    "NON_NEAREST_OVERRIDE": "override does not name the nearest authority context",
    "INVALID_OVERRIDE": "override target or Rule ID is invalid",
    "DECLARED_AUTHORITY_CONFLICT": "declared conflict prevents deterministic authority",
    "FUTURE_REVIEW_DATE": "rule review date is after as_of",
    "STALE_RULE": "rule review interval has expired",
    "DEPRECATED_RULE": "selected rule is deprecated",
    "MISSING_EVIDENCE": "declared evidence is missing",
    "UNATTESTED_EXCEPTION": "exception approval is not coordinator-attested",
    "INVALID_EXCEPTION_PROVENANCE": "exception approval provenance is invalid",
    "EXCEPTION_BINDING_MISMATCH": "exception approval binding does not match this attempt",
    "EXCEPTION_EXPIRED": "exception approval is not valid on as_of",
    "EXCEPTION_DIGEST_MISMATCH": "exception approval digest is invalid",
    "UNUSED_EXCEPTION": "exception approval matched no finding",
    "AMBIGUOUS_EXCEPTION": "exception approval matched multiple findings",
    "UNUSED_INPUT_WITHOUT_ROOT": "conflict or exception input exists without root map",
    "SNAPSHOT_BYTE_LIMIT": "Snapshot document exceeds 131072 bytes including terminal LF",
    "DIAGNOSTIC_LIMIT": "diagnostic count exceeded 128; individual diagnostics suppressed",
    "SAFE_OPEN_HELPER_TIMEOUT": "bounded safe-open helper timed out",
    "SAFE_OPEN_HELPER_FAILED": "bounded safe-open helper failed",
    "SAFE_OPEN_HELPER_LEAK": "bounded safe-open helper could not be reaped",
    "SAFE_OPEN_HELPER_BUSY": "another bounded safe-open helper is active",
}

#: Design section 14 fixed details for model errors, copied literally.
DESIGN_FIXED_DETAILS = {
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
    "SNAPSHOT_BYTE_LIMIT": "Snapshot document exceeds 131072 bytes including terminal LF",
    "SNAPSHOT_COUNT_LIMIT": "Snapshot collection exceeds its count limit",
    "SNAPSHOT_DUPLICATE": "Snapshot contains a duplicate record",
    "SNAPSHOT_DIGEST_MISMATCH": "Snapshot digest does not match canonical content",
    "PUBLICATION_BYTE_LIMIT": "Snapshot publication exceeds 262144 bytes",
}

#: Design section 4 closed Difference code order, copied literally.
DESIGN_DIFFERENCE_CODES = (
    "OBSERVED_NOT_APPLICABLE",
    "OBSERVED_BLOCKED",
    "VALUE_MISMATCH",
    "MISSING_RECORD",
    "EXTRA_RECORD",
    "DIFFERENCE_LIMIT",
)

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def identity_object(size=10, **overrides):
    base = {
        "device": 1,
        "inode": 2,
        "mode": 33188,
        "size": size,
        "mtime_ns": 3,
        "ctime_ns": 4,
    }
    base.update(overrides)
    return base


def root_file_object(**overrides):
    base = {
        "path": "techstacks/README.md",
        "context_id": "root",
        "kind": "map",
        "referrer_map": None,
        "map_chain": [],
        "applies_to": ["."],
        "selection_basis": ["root"],
        "identity": identity_object(10),
        "bytes": 10,
        "sha256": DIGEST_A,
        "reviewed_on": None,
        "review_within_days": None,
        "deprecated": None,
        "evidence": [],
    }
    base.update(overrides)
    return base


def leaf_file_object(**overrides):
    base = {
        "path": "techstacks/frontend/components/Button.md",
        "context_id": "components",
        "kind": "leaf",
        "referrer_map": "techstacks/frontend/README.md",
        "map_chain": ["frontend", "components"],
        "applies_to": ["src/components"],
        "selection_basis": ["scope"],
        "identity": identity_object(20),
        "bytes": 20,
        "sha256": DIGEST_B,
        "reviewed_on": "2026-08-01",
        "review_within_days": 90,
        "deprecated": False,
        "evidence": [{"path": "docs/evidence.md", "bytes": 5, "sha256": DIGEST_C}],
    }
    base.update(overrides)
    return base


def effective_rule_object(**overrides):
    base = {
        "rule_id": "BTN-1",
        "statement_sha256": DIGEST_D,
        "source_path": "techstacks/frontend/components/Button.md",
        "context_id": "components",
        "authority_map": "techstacks/frontend/README.md",
        "applies_to": ["src/components"],
        "overrides_context_id": None,
    }
    base.update(overrides)
    return base


def failure_target_object(**overrides):
    base = {"code": "STALE_RULE", "context_id": "components", "evidence_path": None}
    base.update(overrides)
    return base


def approval_object(**overrides):
    base = {
        "approval_id": "approval-1",
        "coordinator_attested": True,
        "authorized_by": "user",
        "authorization_reference": "decision recorded in the task dossier",
        "authorization_digest": DIGEST_A,
        "task_id": "TECHSTACK-001",
        "plan_id": "TECHSTACK-PLAN-001",
        "plan_version": 8,
        "attempt_id": "attempt-1",
        "issued_on": "2026-08-20",
        "expires_on": "2026-09-01",
        "target": failure_target_object(),
        "scope_sha256": DIGEST_B,
        "reason": "the component rule review is pending a scheduled refresh",
        "binding_sha256": DIGEST_C,
    }
    base.update(overrides)
    return base


def conflict_object(**overrides):
    base = {
        "source": "techstacks/frontend/README.md",
        "target": "techstacks/README.md",
        "detail": "both maps claim the same component selector",
    }
    base.update(overrides)
    return base


def input_object(**overrides):
    base = {
        "task_id": "TECHSTACK-001",
        "plan_id": "TECHSTACK-PLAN-001",
        "plan_version": 8,
        "attempt_id": "attempt-1",
        "as_of": "2026-08-24",
        "scope_paths": ["src/components"],
        "context_chains": [["frontend", "components"]],
        "exception_approvals": [],
        "declared_conflicts": [],
    }
    base.update(overrides)
    return base


def snapshot_object(**overrides):
    """Build a complete Snapshot object with a recomputed digest."""

    selected = overrides.pop("selected_files", [root_file_object(), leaf_file_object()])
    rules = overrides.pop("effective_rules", [effective_rule_object()])
    base = {
        "schema_version": 1,
        "task_id": "TECHSTACK-001",
        "plan_id": "TECHSTACK-PLAN-001",
        "plan_version": 8,
        "attempt_id": "attempt-1",
        "as_of": "2026-08-24",
        "root_identity": {"device": 1, "inode": 1},
        "root_map": "techstacks/README.md",
        "scope_paths": ["src/components"],
        "context_chains": [["frontend", "components"]],
        "exception_approvals": [],
        "declared_conflicts": [],
        "selected_files": selected,
        "effective_rules": rules,
        "totals": {
            "file_count": len(selected),
            "bytes": sum(item["bytes"] for item in selected),
            "evidence_file_count": sum(len(item["evidence"]) for item in selected),
            "evidence_bytes": sum(
                observation["bytes"]
                for item in selected
                for observation in item["evidence"]
            ),
            "rule_count": len(rules),
        },
        "snapshot_sha256": model.DIGEST_PLACEHOLDER,
    }
    recompute = overrides.pop("recompute_digest", True)
    base.update(overrides)
    if recompute:
        base["snapshot_sha256"] = model.snapshot_digest(base)
    return base


class CallerErrorRegistryTest(unittest.TestCase):
    def test_input_error_code_vector_is_the_exact_ordered_design_list(self):
        self.assertEqual(DESIGN_INPUT_ERROR_CODES, model.INPUT_ERROR_CODES)
        self.assertEqual(23, len(model.INPUT_ERROR_CODES))
        self.assertEqual(
            "PROJECT_ROOT_HELPER_BUSY", model.INPUT_ERROR_CODES[15]
        )
        self.assertEqual("PROJECT_ROOT_HELPER_LEAK", model.INPUT_ERROR_CODES[14])
        self.assertEqual("INPUT_UNKNOWN_KEY", model.INPUT_ERROR_CODES[16])

    def test_snapshot_error_code_vector_is_the_exact_ordered_design_list(self):
        self.assertEqual(DESIGN_SNAPSHOT_ERROR_CODES, model.SNAPSHOT_ERROR_CODES)
        self.assertEqual(11, len(model.SNAPSHOT_ERROR_CODES))
        self.assertEqual("PUBLICATION_BYTE_LIMIT", model.SNAPSHOT_ERROR_CODES[10])

    def test_every_code_resolves_to_one_field_and_one_fixed_detail(self):
        covered = set(model.FIXED_DETAILS) | {
            outcome.code for outcome in model.ROOT_API_OUTCOMES
        }
        self.assertEqual(
            set(DESIGN_INPUT_ERROR_CODES) | set(DESIGN_SNAPSHOT_ERROR_CODES), covered
        )
        for outcome in model.ROOT_API_OUTCOMES:
            self.assertTrue(outcome.detail)
            self.assertIn(
                outcome.code,
                set(DESIGN_INPUT_ERROR_CODES) | set(DESIGN_SNAPSHOT_ERROR_CODES),
            )
        self.assertEqual(DESIGN_FIXED_DETAILS, dict(model.FIXED_DETAILS))

    def test_root_api_outcomes_carry_the_exact_class_field_and_detail(self):
        expected = {
            "PROJECT_ROOT_TYPE": (
                model.TechstackInputError,
                "project_root",
                "project_root must be a pathlib.Path",
            ),
            "PROJECT_ROOT_HELPER_BUSY": (
                model.TechstackInputError,
                "project_root",
                "project_root safe-open helper is busy",
            ),
            "SNAPSHOT_AS_OF_MISMATCH": (
                model.TechstackSnapshotError,
                "/as_of",
                "as_of must equal Snapshot as_of",
            ),
            "INPUT_TYPE": (
                model.TechstackInputError,
                "",
                "input must be a ResolutionInput",
            ),
        }
        for code, (error_class, field, detail) in expected.items():
            error = model.root_api_error_for_code(code)
            self.assertIsInstance(error, error_class)
            self.assertEqual(code, error.code)
            self.assertEqual(field, error.field)
            self.assertEqual(detail, error.detail)

    def test_filesystem_error_detail_carries_only_a_decimal_errno(self):
        self.assertEqual(
            "project root filesystem operation failed with errno 13",
            model.root_api_error_for_code(
                "PROJECT_ROOT_FILESYSTEM_ERROR", errno_value=13
            ).detail,
        )
        self.assertEqual(
            "project root filesystem operation failed with errno -1",
            model.root_api_error_for_code("PROJECT_ROOT_FILESYSTEM_ERROR").detail,
        )
        self.assertEqual(
            "filesystem operation failed with errno -1", model.filesystem_error_detail(None)
        )

    def test_caller_error_attributes_are_immutable(self):
        error = model.TechstackInputError("INPUT_VALUE", "/as_of", "input field has an invalid value")
        with self.assertRaises(AttributeError):
            error.code = "INPUT_TYPE"


class LeafGrammarRuleRegistryTest(unittest.TestCase):
    """The closed leaf-grammar rule registry and its two detail slots."""

    def test_registry_is_a_closed_ordered_tuple_of_twenty_identifiers(self):
        rules = model.LEAF_GRAMMAR_RULES
        self.assertIsInstance(rules, tuple)
        self.assertEqual(20, len(rules))
        self.assertEqual(len(set(rules)), len(rules))
        for rule in rules:
            with self.subTest(rule=rule):
                self.assertTrue(rule.replace("_", "").isalpha())
                self.assertEqual(rule, rule.upper())
                self.assertTrue(rule.isascii())
                self.assertLessEqual(len(rule.encode("utf-8")), 32)

    def test_invalid_leaf_detail_renders_both_slots(self):
        self.assertEqual(
            "leaf bytes do not match the leaf grammar at line 34: TRAILING_CONTENT",
            model.invalid_leaf_detail(34, "TRAILING_CONTENT"),
        )
        self.assertEqual(
            "leaf bytes do not match the leaf grammar at line 0: DOCUMENT_ENCODING",
            model.invalid_leaf_detail(0, "DOCUMENT_ENCODING"),
        )

    def test_invalid_leaf_detail_accepts_only_a_line_in_bounds_and_a_member(self):
        # 0 is the document-level case and 65537 is one past the largest line
        # array the leaf byte cap admits.
        self.assertTrue(model.invalid_leaf_detail(0, "LINE_SHAPE"))
        self.assertTrue(model.invalid_leaf_detail(65537, "LINE_SHAPE"))
        for line in (-1, 65538):
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    model.invalid_leaf_detail(line, "LINE_SHAPE")
        with self.assertRaises(ValueError):
            model.invalid_leaf_detail(None, "LINE_SHAPE")
        with self.assertRaises(ValueError):
            model.invalid_leaf_detail(1, None)
        with self.assertRaises(ValueError):
            model.invalid_leaf_detail(1, "NOT_A_RULE")

    def test_the_rendered_detail_stays_inside_its_bounds(self):
        widest = max(model.LEAF_GRAMMAR_RULES, key=len)
        detail = model.invalid_leaf_detail(65537, widest)
        self.assertLessEqual(len(detail.encode("utf-8")), 88)
        self.assertLessEqual(len(detail.encode("utf-8")), model.DETAIL_BYTE_MAX)

    def test_diagnostic_round_trips_both_slots(self):
        for line in (0, 65537):
            with self.subTest(line=line):
                built = model.diagnostic(
                    "INVALID_LEAF",
                    path="techstacks/general.md",
                    line=line,
                    rule="SECTION_BOUNDARY",
                )
                self.assertEqual(
                    model.invalid_leaf_detail(line, "SECTION_BOUNDARY"), built.detail
                )
                self.assertEqual(built, model.Diagnostic(**built.to_json_object()))

    def test_diagnostic_rejects_an_unattributed_or_malformed_detail(self):
        for detail in (
            "leaf bytes do not match the leaf grammar",
            "leaf bytes do not match the leaf grammar at line 1: NOT_A_RULE",
            "leaf bytes do not match the leaf grammar at line 65538: LINE_SHAPE",
            "leaf bytes do not match the leaf grammar at line -1: LINE_SHAPE",
            "leaf bytes do not match the leaf grammar at line 01: LINE_SHAPE",
            "leaf bytes do not match the leaf grammar at line  1: LINE_SHAPE",
        ):
            with self.subTest(detail=detail):
                with self.assertRaises(ValueError):
                    model.Diagnostic(
                        code="INVALID_LEAF",
                        severity="error",
                        path="techstacks/general.md",
                        context_id=None,
                        detail=detail,
                        waivable=False,
                        waived_by=None,
                    )
        with self.assertRaises(ValueError):
            model.diagnostic("INVALID_LEAF", path="techstacks/general.md")


class DiagnosticRegistryTest(unittest.TestCase):
    def test_registry_is_the_exact_58_row_table(self):
        rows = tuple(
            (spec.rank, spec.code, spec.fields, spec.severity, spec.waivable)
            for spec in model.DIAGNOSTIC_REGISTRY
        )
        self.assertEqual(DESIGN_DIAGNOSTIC_ROWS, rows)
        self.assertEqual(58, len(model.DIAGNOSTIC_REGISTRY))

    def test_every_detail_is_the_literal_registry_message(self):
        self.assertEqual(
            DESIGN_DIAGNOSTIC_DETAILS,
            {spec.code: spec.detail for spec in model.DIAGNOSTIC_REGISTRY},
        )
        for spec in model.DIAGNOSTIC_REGISTRY:
            self.assertLessEqual(len(spec.detail.encode("utf-8")), 128)

    def test_field_classes_are_enforced(self):
        general = model.diagnostic("UNSUPPORTED_PLATFORM")
        self.assertIsNone(general.path)
        self.assertIsNone(general.context_id)
        with self.assertRaises(ValueError):
            model.diagnostic("UNSUPPORTED_PLATFORM", path="techstacks/README.md")
        with self.assertRaises(ValueError):
            model.diagnostic("SYMLINK_REJECTED")
        with self.assertRaises(ValueError):
            model.diagnostic("SYMLINK_REJECTED", path="techstacks/README.md", context_id="root")
        with self.assertRaises(ValueError):
            model.diagnostic("STALE_RULE", path="techstacks/a.md")
        model.diagnostic("STALE_RULE", path="techstacks/a.md", context_id="components")
        model.diagnostic("UNUSED_EXCEPTION", context_id="components")
        with self.assertRaises(ValueError):
            model.diagnostic("UNUSED_EXCEPTION", path="techstacks/a.md", context_id="components")
        model.diagnostic(
            "MISSING_EVIDENCE", path="docs/evidence.md", context_id="components"
        )

    def test_only_the_three_waivable_codes_become_consumed_warnings(self):
        consumed = model.diagnostic(
            "STALE_RULE",
            path="techstacks/a.md",
            context_id="components",
            waived_by="approval-1",
        )
        self.assertEqual("warning", consumed.severity)
        self.assertTrue(consumed.waivable)
        self.assertEqual("approval-1", consumed.waived_by)
        with self.assertRaises(ValueError):
            model.diagnostic(
                "SYMLINK_REJECTED", path="techstacks/a.md", waived_by="approval-1"
            )
        for code in ("STALE_RULE", "DEPRECATED_RULE", "MISSING_EVIDENCE"):
            self.assertTrue(model.DIAGNOSTIC_SPECS[code].waivable)
        waivable = {spec.code for spec in model.DIAGNOSTIC_REGISTRY if spec.waivable}
        self.assertEqual({"STALE_RULE", "DEPRECATED_RULE", "MISSING_EVIDENCE"}, waivable)

    def test_unknown_code_and_wrong_detail_reject(self):
        with self.assertRaises(ValueError):
            model.Diagnostic(
                code="NO_SUCH_CODE",
                severity="error",
                path=None,
                context_id=None,
                detail="x",
                waivable=False,
                waived_by=None,
            )
        with self.assertRaises(ValueError):
            model.Diagnostic(
                code="UNSUPPORTED_PLATFORM",
                severity="error",
                path=None,
                context_id=None,
                detail="paraphrased detail",
                waivable=False,
                waived_by=None,
            )

    def test_diagnostics_sort_by_rank_path_context_detail_and_waiver(self):
        unsorted = [
            model.diagnostic("SYMLINK_REJECTED", path="techstacks/b.md"),
            model.diagnostic("UNSUPPORTED_PLATFORM"),
            model.diagnostic("SYMLINK_REJECTED", path="techstacks/a.md"),
        ]
        ordered = model.sort_diagnostics(unsorted)
        self.assertEqual(
            ["UNSUPPORTED_PLATFORM", "SYMLINK_REJECTED", "SYMLINK_REJECTED"],
            [item.code for item in ordered],
        )
        self.assertEqual("techstacks/a.md", ordered[1].path)

    def test_helper_codes_are_the_four_bounded_reader_branches(self):
        self.assertEqual(
            (
                "SAFE_OPEN_HELPER_TIMEOUT",
                "SAFE_OPEN_HELPER_FAILED",
                "SAFE_OPEN_HELPER_LEAK",
                "SAFE_OPEN_HELPER_BUSY",
            ),
            model.HELPER_DIAGNOSTIC_CODES,
        )
        for code in model.HELPER_DIAGNOSTIC_CODES:
            spec = model.DIAGNOSTIC_SPECS[code]
            self.assertEqual("P", spec.fields)
            self.assertFalse(spec.waivable)


class OverflowSentinelTest(unittest.TestCase):
    def test_a_129th_diagnostic_replaces_the_entire_array(self):
        diagnostics = [
            model.diagnostic("SYMLINK_REJECTED", path=f"techstacks/f{index}.md")
            for index in range(128)
        ]
        self.assertEqual(128, len(model.apply_diagnostic_limit(diagnostics)))
        diagnostics.append(model.diagnostic("SYMLINK_REJECTED", path="techstacks/x.md"))
        overflow = model.apply_diagnostic_limit(diagnostics)
        self.assertEqual(1, len(overflow))
        self.assertEqual("DIAGNOSTIC_LIMIT", overflow[0].code)
        self.assertEqual(
            "diagnostic count exceeded 128; individual diagnostics suppressed",
            overflow[0].detail,
        )

    def test_a_65th_difference_replaces_the_entire_array(self):
        differences = [
            model.Difference(
                code="VALUE_MISMATCH", field=f"/scope_paths/{index:02d}", expected="1", actual="2"
            )
            for index in range(64)
        ]
        self.assertEqual(64, len(model.apply_difference_limit(differences, DIGEST_A, DIGEST_B)))
        differences.append(
            model.Difference(code="VALUE_MISMATCH", field="/as_of", expected="1", actual="2")
        )
        overflow = model.apply_difference_limit(differences, DIGEST_A, DIGEST_B)
        self.assertEqual(1, len(overflow))
        self.assertEqual("DIFFERENCE_LIMIT", overflow[0].code)
        self.assertEqual("/", overflow[0].field)
        self.assertEqual(f"snapshot-sha256:{DIGEST_A}", overflow[0].expected)
        self.assertEqual(f"snapshot-sha256:{DIGEST_B}", overflow[0].actual)

    def test_snapshot_comparison_overflow_uses_the_digest_sentinel(self):
        expected = model.snapshot_from_json_object(
            snapshot_object(scope_paths=[f"src/a{index:02d}" for index in range(64)])
        )
        observed = model.snapshot_from_json_object(
            snapshot_object(scope_paths=[f"src/b{index:02d}" for index in range(64)])
        )
        differences = model.build_snapshot_differences(expected, observed)
        self.assertEqual(1, len(differences))
        self.assertEqual("DIFFERENCE_LIMIT", differences[0].code)
        self.assertEqual(
            f"snapshot-sha256:{expected.snapshot_sha256}", differences[0].expected
        )


class DifferenceRegistryTest(unittest.TestCase):
    def test_difference_code_order_is_exact(self):
        self.assertEqual(DESIGN_DIFFERENCE_CODES, model.DIFFERENCE_CODES)
        self.assertEqual(
            {code: index for index, code in enumerate(DESIGN_DIFFERENCE_CODES)},
            dict(model.DIFFERENCE_RANKS),
        )

    def test_value_mismatch_uses_the_leaf_pointer(self):
        expected = model.snapshot_from_json_object(snapshot_object())
        observed = model.snapshot_from_json_object(snapshot_object(as_of="2026-08-25"))
        differences = model.build_snapshot_differences(expected, observed)
        self.assertEqual(1, len(differences))
        self.assertEqual("VALUE_MISMATCH", differences[0].code)
        self.assertEqual("/as_of", differences[0].field)
        self.assertEqual('"2026-08-24"', differences[0].expected)
        self.assertEqual('"2026-08-25"', differences[0].actual)

    def test_missing_and_extra_records_use_the_sha256_pointer_segment(self):
        expected = model.snapshot_from_json_object(
            snapshot_object(declared_conflicts=[conflict_object()])
        )
        observed = model.snapshot_from_json_object(snapshot_object())
        differences = model.build_snapshot_differences(expected, observed)
        self.assertEqual(1, len(differences))
        self.assertEqual("MISSING_RECORD", differences[0].code)
        self.assertTrue(differences[0].field.startswith("/declared_conflicts/@sha256="))
        self.assertIsNone(differences[0].actual)
        reversed_differences = model.build_snapshot_differences(observed, expected)
        self.assertEqual("EXTRA_RECORD", reversed_differences[0].code)
        self.assertIsNone(reversed_differences[0].expected)

    def test_matched_records_recurse_into_their_fields(self):
        expected = model.snapshot_from_json_object(snapshot_object())
        observed = model.snapshot_from_json_object(
            snapshot_object(
                selected_files=[
                    root_file_object(),
                    leaf_file_object(deprecated=True),
                ]
            )
        )
        differences = model.build_snapshot_differences(expected, observed)
        self.assertEqual(1, len(differences))
        self.assertEqual("VALUE_MISMATCH", differences[0].code)
        self.assertTrue(differences[0].field.endswith("/deprecated"))
        self.assertEqual("false", differences[0].expected)
        self.assertEqual("true", differences[0].actual)

    def test_oversize_representation_uses_the_exact_hash_marker(self):
        oversize = ["x" * 200] * 20
        representation = model.difference_representation(oversize)
        self.assertTrue(representation.startswith("canonical-json-sha256:"))
        self.assertEqual(22 + 64, len(representation))

    def test_observed_status_rows_carry_quoted_json_text(self):
        not_applicable = model.observed_not_applicable_difference()
        self.assertEqual("/observed_resolution/status", not_applicable.field)
        self.assertEqual('"applicable"', not_applicable.expected)
        self.assertEqual('"not_applicable"', not_applicable.actual)
        blocked = model.observed_blocked_difference()
        self.assertEqual('"blocked"', blocked.actual)

    def test_differences_sort_by_rank_field_expected_and_actual(self):
        unsorted = [
            model.Difference(code="EXTRA_RECORD", field="/a", expected=None, actual="1"),
            model.Difference(code="VALUE_MISMATCH", field="/b", expected="1", actual="2"),
            model.Difference(code="VALUE_MISMATCH", field="/a", expected="1", actual="2"),
        ]
        ordered = model.sort_differences(unsorted)
        self.assertEqual(
            [("VALUE_MISMATCH", "/a"), ("VALUE_MISMATCH", "/b"), ("EXTRA_RECORD", "/a")],
            [(item.code, item.field) for item in ordered],
        )


class CanonicalJsonTest(unittest.TestCase):
    def test_canonical_form_is_sorted_two_space_utf8_with_one_terminal_lf(self):
        document = model.canonical_json_document({"b": 1, "a": {"d": "é", "c": [1, 2]}})
        self.assertEqual(
            '{\n  "a": {\n    "c": [\n      1,\n      2\n    ],\n    "d": "é"\n  },\n  "b": 1\n}\n',
            document,
        )
        self.assertTrue(document.endswith("}\n"))
        self.assertFalse(document.endswith("\n\n"))

    def test_snapshot_digest_zeroes_the_digest_field(self):
        payload = snapshot_object()
        digest = model.snapshot_digest(payload)
        zeroed = dict(payload)
        zeroed["snapshot_sha256"] = model.DIGEST_PLACEHOLDER
        self.assertEqual(
            model.sha256_hex(model.canonical_json_bytes(zeroed)), digest
        )
        self.assertEqual(digest, payload["snapshot_sha256"])
        self.assertNotIn(b"\n", model.canonical_json_bytes(zeroed)[-1:])


class RecordSchemaTest(unittest.TestCase):
    def test_key_vectors_are_exact(self):
        self.assertEqual(
            (
                "task_id",
                "plan_id",
                "plan_version",
                "attempt_id",
                "as_of",
                "scope_paths",
                "context_chains",
                "exception_approvals",
                "declared_conflicts",
            ),
            model.RESOLUTION_INPUT_KEYS,
        )
        self.assertEqual(("source", "target", "detail"), model.DECLARED_CONFLICT_KEYS)
        self.assertEqual(("code", "context_id", "evidence_path"), model.FAILURE_TARGET_KEYS)
        self.assertEqual(
            (
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
            ),
            model.EXCEPTION_APPROVAL_KEYS,
        )
        self.assertEqual(("device", "inode"), model.ROOT_IDENTITY_KEYS)
        self.assertEqual(
            ("device", "inode", "mode", "size", "mtime_ns", "ctime_ns"),
            model.FILE_IDENTITY_KEYS,
        )
        self.assertEqual(("path", "bytes", "sha256"), model.EVIDENCE_OBSERVATION_KEYS)
        self.assertEqual(
            (
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
            ),
            model.SELECTED_FILE_KEYS,
        )
        self.assertEqual(
            (
                "rule_id",
                "statement_sha256",
                "source_path",
                "context_id",
                "authority_map",
                "applies_to",
                "overrides_context_id",
            ),
            model.EFFECTIVE_RULE_KEYS,
        )
        self.assertEqual(
            ("file_count", "bytes", "evidence_file_count", "evidence_bytes", "rule_count"),
            model.TOTALS_KEYS,
        )
        self.assertEqual(
            (
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
            ),
            model.SNAPSHOT_KEYS,
        )
        self.assertEqual(
            ("code", "severity", "path", "context_id", "detail", "waivable", "waived_by"),
            model.DIAGNOSTIC_KEYS,
        )
        self.assertEqual(
            ("schema_version", "status", "snapshot", "diagnostics"), model.RESOLUTION_KEYS
        )
        self.assertEqual(("code", "field", "expected", "actual"), model.DIFFERENCE_KEYS)
        self.assertEqual(
            (
                "schema_version",
                "status",
                "expected_snapshot_sha256",
                "observed_snapshot_sha256",
                "observed_resolution",
                "differences",
            ),
            model.VERIFICATION_KEYS,
        )
        self.assertEqual(
            ("ordinal", "artifact_path", "snapshot_sha256", "publication", "verification_status"),
            model.SNAPSHOT_ATTEMPT_KEYS,
        )
        self.assertEqual(
            (
                "schema_version",
                "status",
                "resolution",
                "attempts",
                "selected_artifact",
                "selected_snapshot_sha256",
            ),
            model.SNAPSHOT_PUBLICATION_KEYS,
        )

    def test_status_enumerations_are_closed(self):
        self.assertEqual(("applicable", "not_applicable", "blocked"), model.RESOLUTION_STATUSES)
        self.assertEqual(("match", "drift", "blocked"), model.VERIFICATION_STATUSES)
        self.assertEqual(
            ("published", "not_applicable", "blocked", "observation_drift"),
            model.PUBLICATION_STATUSES,
        )
        self.assertEqual(("created", "identical_existing"), model.ATTEMPT_PUBLICATIONS)
        self.assertEqual(("map", "leaf"), model.SELECTED_FILE_KINDS)
        self.assertEqual(
            ("root", "dot", "scope", "context_chain"), model.SELECTION_BASIS_ORDER
        )

    def test_unknown_and_missing_keys_reject_with_their_own_codes(self):
        payload = input_object()
        payload["extra"] = 1
        with self.assertRaises(model.TechstackInputError) as unknown:
            model.resolution_input_from_json_object(payload)
        self.assertEqual("INPUT_UNKNOWN_KEY", unknown.exception.code)
        self.assertEqual("/extra", unknown.exception.field)
        payload = input_object()
        del payload["as_of"]
        with self.assertRaises(model.TechstackInputError) as missing:
            model.resolution_input_from_json_object(payload)
        self.assertEqual("INPUT_MISSING_KEY", missing.exception.code)
        snapshot = snapshot_object()
        snapshot["extra"] = 1
        with self.assertRaises(model.TechstackSnapshotError) as snapshot_unknown:
            model.snapshot_from_json_object(snapshot)
        self.assertEqual("SNAPSHOT_UNKNOWN_KEY", snapshot_unknown.exception.code)
        snapshot = snapshot_object()
        del snapshot["totals"]
        with self.assertRaises(model.TechstackSnapshotError) as snapshot_missing:
            model.snapshot_from_json_object(snapshot)
        self.assertEqual("SNAPSHOT_MISSING_KEY", snapshot_missing.exception.code)

    def test_no_input_field_accepts_null(self):
        for key in model.RESOLUTION_INPUT_KEYS:
            with self.subTest(key=key):
                with self.assertRaises(model.TechstackInputError):
                    model.resolution_input_from_json_object(input_object(**{key: None}))

    def test_input_canonicalizes_duplicates_and_order(self):
        parsed = model.resolution_input_from_json_object(
            input_object(
                scope_paths=["src/b", "src/a", "src/a"],
                context_chains=[["frontend"], ["frontend"], ["backend"]],
            )
        )
        self.assertEqual(("src/a", "src/b"), parsed.scope_paths)
        self.assertEqual((("backend",), ("frontend",)), parsed.context_chains)

    def test_duplicate_records_reject(self):
        with self.assertRaises(model.TechstackInputError) as duplicate_conflict:
            model.resolution_input_from_json_object(
                input_object(declared_conflicts=[conflict_object(), conflict_object()])
            )
        self.assertEqual("INPUT_DUPLICATE", duplicate_conflict.exception.code)
        with self.assertRaises(model.TechstackInputError) as duplicate_approval:
            model.resolution_input_from_json_object(
                input_object(
                    exception_approvals=[
                        approval_object(),
                        approval_object(approval_id="approval-2"),
                    ]
                )
            )
        self.assertEqual("INPUT_DUPLICATE", duplicate_approval.exception.code)

    def test_failure_target_evidence_path_rule(self):
        with self.assertRaises(model.TechstackInputError):
            model.resolution_input_from_json_object(
                input_object(
                    exception_approvals=[
                        approval_object(
                            target=failure_target_object(evidence_path="docs/e.md")
                        )
                    ]
                )
            )
        model.resolution_input_from_json_object(
            input_object(
                exception_approvals=[
                    approval_object(
                        target=failure_target_object(
                            code="MISSING_EVIDENCE", evidence_path="docs/e.md"
                        )
                    )
                ]
            )
        )
        with self.assertRaises(model.TechstackInputError):
            model.resolution_input_from_json_object(
                input_object(
                    exception_approvals=[
                        approval_object(
                            target=failure_target_object(code="PEER_RULE_CONFLICT")
                        )
                    ]
                )
            )

    def test_root_selected_file_is_index_zero_and_unique(self):
        snapshot = model.snapshot_from_json_object(snapshot_object())
        self.assertEqual("techstacks/README.md", snapshot.root_map)
        self.assertEqual(snapshot.root_map, snapshot.selected_files[0].path)
        self.assertEqual("root", snapshot.selected_files[0].context_id)
        swapped = snapshot_object(
            selected_files=[leaf_file_object(), root_file_object()]
        )
        with self.assertRaises(model.TechstackSnapshotError):
            model.snapshot_from_json_object(swapped)
        duplicate_root = snapshot_object(
            selected_files=[
                root_file_object(),
                leaf_file_object(context_id="root"),
            ]
        )
        with self.assertRaises(model.TechstackSnapshotError):
            model.snapshot_from_json_object(duplicate_root)

    def test_root_row_fields_are_exact(self):
        for override in (
            {"kind": "leaf"},
            {"referrer_map": "techstacks/README.md"},
            {"map_chain": ["root"]},
            {"applies_to": ["src"]},
            {"selection_basis": ["scope"]},
            {"reviewed_on": "2026-08-01"},
            {"evidence": [{"path": "docs/e.md", "bytes": 1, "sha256": DIGEST_C}]},
        ):
            with self.subTest(override=override):
                with self.assertRaises(model.TechstackSnapshotError):
                    model.snapshot_from_json_object(
                        snapshot_object(
                            selected_files=[
                                root_file_object(**override),
                                leaf_file_object(),
                            ]
                        )
                    )

    def test_map_review_fields_are_null_and_leaf_review_fields_are_not(self):
        with self.assertRaises(model.TechstackSnapshotError):
            model.snapshot_from_json_object(
                snapshot_object(
                    selected_files=[root_file_object(), leaf_file_object(reviewed_on=None)]
                )
            )
        with self.assertRaises(model.TechstackSnapshotError):
            model.snapshot_from_json_object(
                snapshot_object(
                    selected_files=[
                        root_file_object(),
                        leaf_file_object(
                            kind="map",
                            referrer_map="techstacks/README.md",
                            reviewed_on=None,
                            review_within_days=None,
                            deprecated=None,
                            evidence=[{"path": "d.md", "bytes": 1, "sha256": DIGEST_C}],
                        ),
                    ]
                )
            )

    def test_selection_basis_is_a_unique_registry_ordered_subset(self):
        accepted = snapshot_object(
            selected_files=[
                root_file_object(),
                leaf_file_object(selection_basis=["dot", "scope"]),
            ]
        )
        model.snapshot_from_json_object(accepted)
        for basis in (["scope", "dot"], ["scope", "scope"], [], ["root"]):
            with self.subTest(basis=basis):
                with self.assertRaises(model.TechstackSnapshotError):
                    model.snapshot_from_json_object(
                        snapshot_object(
                            selected_files=[
                                root_file_object(),
                                leaf_file_object(selection_basis=basis),
                            ]
                        )
                    )

    def test_file_identity_size_equals_bytes_and_observed_length(self):
        with self.assertRaises(model.TechstackSnapshotError) as mismatch:
            model.snapshot_from_json_object(
                snapshot_object(
                    selected_files=[
                        root_file_object(),
                        leaf_file_object(identity=identity_object(21)),
                    ]
                )
            )
        self.assertEqual("SNAPSHOT_VALUE", mismatch.exception.code)
        self.assertEqual("/selected_files/1/identity/size", mismatch.exception.field)

    def test_evidence_records_sort_and_reject_duplicates(self):
        with self.assertRaises(model.TechstackSnapshotError):
            model.snapshot_from_json_object(
                snapshot_object(
                    selected_files=[
                        root_file_object(),
                        leaf_file_object(
                            evidence=[
                                {"path": "docs/b.md", "bytes": 1, "sha256": DIGEST_C},
                                {"path": "docs/a.md", "bytes": 1, "sha256": DIGEST_C},
                            ]
                        ),
                    ]
                )
            )
        with self.assertRaises(model.TechstackSnapshotError):
            model.snapshot_from_json_object(
                snapshot_object(
                    selected_files=[
                        root_file_object(),
                        leaf_file_object(
                            evidence=[
                                {"path": "docs/a.md", "bytes": 1, "sha256": DIGEST_C},
                                {"path": "docs/a.md", "bytes": 2, "sha256": DIGEST_C},
                            ]
                        ),
                    ]
                )
            )

    def test_effective_rule_equals_its_selected_leaf_and_referring_row(self):
        for override in (
            {"source_path": "techstacks/README.md"},
            {"context_id": "frontend"},
            {"authority_map": "techstacks/README.md"},
            {"applies_to": ["src/other"]},
        ):
            with self.subTest(override=override):
                with self.assertRaises(model.TechstackSnapshotError):
                    model.snapshot_from_json_object(
                        snapshot_object(effective_rules=[effective_rule_object(**override)])
                    )

    def test_totals_recompute_exactly(self):
        for key in model.TOTALS_KEYS:
            with self.subTest(key=key):
                payload = snapshot_object()
                payload["totals"][key] = payload["totals"][key] + 1
                payload["snapshot_sha256"] = model.snapshot_digest(payload)
                with self.assertRaises(model.TechstackSnapshotError) as error:
                    model.snapshot_from_json_object(payload)
                self.assertEqual("SNAPSHOT_VALUE", error.exception.code)
                self.assertEqual(f"/totals/{key}", error.exception.field)

    def test_digest_mismatch_rejects(self):
        payload = snapshot_object()
        payload["snapshot_sha256"] = DIGEST_A
        with self.assertRaises(model.TechstackSnapshotError) as error:
            model.snapshot_from_json_object(payload)
        self.assertEqual("SNAPSHOT_DIGEST_MISMATCH", error.exception.code)
        self.assertEqual("/snapshot_sha256", error.exception.field)


class ResolutionAndVerificationStateTest(unittest.TestCase):
    def _snapshot(self):
        return model.snapshot_from_json_object(snapshot_object())

    def test_snapshot_is_nonnull_exactly_for_applicable(self):
        snapshot = self._snapshot()
        model.Resolution(schema_version=1, status="applicable", snapshot=snapshot, diagnostics=())
        model.Resolution(schema_version=1, status="not_applicable", snapshot=None, diagnostics=())
        with self.assertRaises(ValueError):
            model.Resolution(
                schema_version=1, status="not_applicable", snapshot=snapshot, diagnostics=()
            )
        with self.assertRaises(ValueError):
            model.Resolution(
                schema_version=1, status="applicable", snapshot=None, diagnostics=()
            )
        with self.assertRaises(ValueError):
            model.Resolution(schema_version=2, status="applicable", snapshot=snapshot, diagnostics=())

    def test_diagnostic_rules_by_status(self):
        snapshot = self._snapshot()
        with self.assertRaises(ValueError):
            model.Resolution(
                schema_version=1,
                status="not_applicable",
                snapshot=None,
                diagnostics=(model.diagnostic("UNSUPPORTED_PLATFORM"),),
            )
        with self.assertRaises(ValueError):
            model.Resolution(
                schema_version=1,
                status="applicable",
                snapshot=snapshot,
                diagnostics=(model.diagnostic("UNSUPPORTED_PLATFORM"),),
            )
        model.Resolution(
            schema_version=1,
            status="applicable",
            snapshot=snapshot,
            diagnostics=(
                model.diagnostic(
                    "STALE_RULE",
                    path="techstacks/a.md",
                    context_id="components",
                    waived_by="approval-1",
                ),
            ),
        )
        with self.assertRaises(ValueError):
            model.Resolution(
                schema_version=1, status="blocked", snapshot=None, diagnostics=()
            )
        model.Resolution(
            schema_version=1,
            status="blocked",
            snapshot=None,
            diagnostics=(model.diagnostic("UNSUPPORTED_PLATFORM"),),
        )

    def test_verification_state_matrix(self):
        snapshot = self._snapshot()
        applicable = model.Resolution(
            schema_version=1, status="applicable", snapshot=snapshot, diagnostics=()
        )
        match = model.Verification(
            schema_version=1,
            status="match",
            expected_snapshot_sha256=snapshot.snapshot_sha256,
            observed_snapshot_sha256=snapshot.snapshot_sha256,
            observed_resolution=applicable,
            differences=(),
        )
        self.assertEqual("match", match.status)
        with self.assertRaises(ValueError):
            model.Verification(
                schema_version=1,
                status="match",
                expected_snapshot_sha256=snapshot.snapshot_sha256,
                observed_snapshot_sha256=None,
                observed_resolution=applicable,
                differences=(),
            )
        not_applicable = model.Resolution(
            schema_version=1, status="not_applicable", snapshot=None, diagnostics=()
        )
        opt_out = model.Verification(
            schema_version=1,
            status="drift",
            expected_snapshot_sha256=snapshot.snapshot_sha256,
            observed_snapshot_sha256=None,
            observed_resolution=not_applicable,
            differences=(model.observed_not_applicable_difference(),),
        )
        self.assertEqual("drift", opt_out.status)
        with self.assertRaises(ValueError):
            model.Verification(
                schema_version=1,
                status="drift",
                expected_snapshot_sha256=snapshot.snapshot_sha256,
                observed_snapshot_sha256=snapshot.snapshot_sha256,
                observed_resolution=not_applicable,
                differences=(model.observed_not_applicable_difference(),),
            )
        blocked = model.Resolution(
            schema_version=1,
            status="blocked",
            snapshot=None,
            diagnostics=(model.diagnostic("UNSUPPORTED_PLATFORM"),),
        )
        blocked_verification = model.Verification(
            schema_version=1,
            status="blocked",
            expected_snapshot_sha256=snapshot.snapshot_sha256,
            observed_snapshot_sha256=None,
            observed_resolution=blocked,
            differences=(model.observed_blocked_difference(),),
        )
        self.assertEqual("blocked", blocked_verification.status)
        drift = model.Verification(
            schema_version=1,
            status="drift",
            expected_snapshot_sha256=DIGEST_A,
            observed_snapshot_sha256=snapshot.snapshot_sha256,
            observed_resolution=applicable,
            differences=(
                model.Difference(
                    code="VALUE_MISMATCH", field="/as_of", expected="1", actual="2"
                ),
            ),
        )
        self.assertEqual(1, len(drift.differences))


def maximum_snapshot_object(reason_length=None):
    """Build a Snapshot object whose canonical document is exactly the cap.

    The tunable is one approval ``reason``; the surrounding filler is at its
    own field maxima, so the document size is linear in that one length.
    """

    def build(length):
        conflicts = [
            {
                "source": f"src/conflict{index:02d}",
                "target": "techstacks/README.md",
                "detail": "d" * 1024,
            }
            for index in range(64)
        ]
        scope = [
            f"src/s{index:02d}/" + "/".join(["p" * 200 for _ in range(4)])
            for index in range(64)
        ]
        scope[0] = scope[0] + "/" + "q" * 150
        approvals = [
            approval_object(
                approval_id="approval-1",
                reason="r" * 1024,
                target=failure_target_object(context_id="ca"),
            ),
            approval_object(
                approval_id="approval-2",
                reason="r" * length,
                target=failure_target_object(context_id="cb"),
            ),
        ]
        return snapshot_object(
            scope_paths=scope,
            declared_conflicts=conflicts,
            exception_approvals=approvals,
        )

    if reason_length is not None:
        return build(reason_length)
    probe = len(model.canonical_json_document(build(500)).encode("utf-8"))
    solved = 500 + (model.SNAPSHOT_DOCUMENT_BYTE_LIMIT - probe)
    assert 1 <= solved <= model.FREE_TEXT_BYTE_MAX, solved
    return build(solved), solved


class PaddedPublication:
    """A publication-shaped document used only to pin the byte cap.

    A field-valid ``SnapshotPublication`` cannot reach 262,144 bytes, because
    its largest member is a Snapshot capped at 131,072 bytes. The cap is still
    a production behavior, so it is pinned here through the production
    ``publication_document`` byte accounting.
    """

    def __init__(self, filler):
        self._filler = filler

    def to_json_object(self):
        return {"filler": self._filler}


def publication_of_document_size(target):
    probe = len(
        model.canonical_json_document(PaddedPublication("x" * 100).to_json_object()).encode(
            "utf-8"
        )
    )
    return PaddedPublication("x" * (100 + target - probe))


class BoundsTest(unittest.TestCase):
    def assert_input_code(self, payload, code):
        with self.assertRaises(model.TechstackInputError) as error:
            model.resolution_input_from_json_object(payload)
        self.assertEqual(code, error.exception.code)
        return error.exception

    def test_identifier_and_date_bounds(self):
        model.resolution_input_from_json_object(input_object(task_id="A" + "-B" * 31))
        self.assert_input_code(input_object(task_id="A" + "-B" * 32), "INPUT_BYTE_LIMIT")
        self.assert_input_code(input_object(task_id="TECHSTACK"), "INPUT_VALUE")
        self.assert_input_code(input_object(task_id="techstack-001"), "INPUT_VALUE")
        self.assert_input_code(input_object(attempt_id="-attempt"), "INPUT_VALUE")
        model.resolution_input_from_json_object(input_object(attempt_id="a" * 64))
        self.assert_input_code(input_object(attempt_id="a" * 65), "INPUT_BYTE_LIMIT")
        self.assert_input_code(input_object(as_of="2026-02-30"), "INPUT_VALUE")
        self.assert_input_code(input_object(as_of="2026-8-24"), "INPUT_VALUE")
        model.resolution_input_from_json_object(input_object(as_of="2024-02-29"))

    def test_is_date_accepts_ascii_digits_only(self):
        """Design section 4's date grammar is ASCII ``YYYY-MM-DD``.

        Python's Unicode ``\\d`` also matches Arabic-Indic and every other
        decimal digit script, and ``datetime.date.fromisoformat`` — every
        consumer of an accepted date — rejects those, so the validator must
        too.
        """

        self.assertTrue(model.is_date("2026-08-01"))
        self.assertFalse(model.is_date("\u0662\u0660\u0662\u0666-\u0660\u0668-\u0660\u0661"))
        self.assertFalse(model.is_date("2026-08-0\u0661"))
        self.assertFalse(model.is_date("\uff12\uff10\uff12\uff16-\uff10\uff18-\uff10\uff11"))
        self.assert_input_code(
            input_object(as_of="\u0662\u0660\u0662\u0666-\u0660\u0668-\u0660\u0661"),
            "INPUT_VALUE",
        )

    def test_plan_version_bounds_and_bool_rejection(self):
        model.resolution_input_from_json_object(input_object(plan_version=1))
        model.resolution_input_from_json_object(input_object(plan_version=9999))
        self.assert_input_code(input_object(plan_version=0), "INPUT_VALUE")
        self.assert_input_code(input_object(plan_version=10000), "INPUT_VALUE")
        self.assert_input_code(input_object(plan_version=True), "INPUT_TYPE")
        self.assert_input_code(input_object(plan_version="8"), "INPUT_TYPE")

    def test_path_and_component_bounds(self):
        component = "c" * 255
        long_path = "/".join([component] * 4)
        self.assertEqual(1023, len(long_path))
        model.resolution_input_from_json_object(input_object(scope_paths=[long_path]))
        exact = "/".join([component, component, component, "c" * 254, "c"])
        self.assertEqual(1024, len(exact))
        model.resolution_input_from_json_object(input_object(scope_paths=[exact]))
        self.assert_input_code(input_object(scope_paths=[exact + "c"]), "INPUT_BYTE_LIMIT")
        self.assert_input_code(
            input_object(scope_paths=[long_path + "x" * 2]), "INPUT_BYTE_LIMIT"
        )
        self.assert_input_code(input_object(scope_paths=["c" * 256]), "INPUT_VALUE")
        for invalid in ("/abs", "rel/", "a//b", "./a", "../a", "~/a", "a\\b", "a\x00b", ""):
            with self.subTest(path=invalid):
                self.assert_input_code(input_object(scope_paths=[invalid]), "INPUT_VALUE")

    def test_selector_accepts_dot_exact_and_prefix_forms(self):
        """Design section 6 retains the version-3 prefix selector unchanged.

        The frozen Design section 15 fixture row uses ``src/frontend/``, so a
        selector is dot, an exact normalized path, or a normalized path plus
        exactly one terminal slash. ``is_normalized_relative_path`` stays
        strict, because the canonical ``project_root`` rule depends on it.
        """

        for accepted in (".", "p", "p/", "src/frontend/", "src/frontend/Button.tsx"):
            with self.subTest(selector=accepted):
                self.assertTrue(model.is_selector(accepted))
        for rejected in ("p//", "/p/", "./", "", "/", "../p/", "~/p/", "a\\b/", "a\x00b/"):
            with self.subTest(selector=rejected):
                self.assertFalse(model.is_selector(rejected))
        self.assertFalse(model.is_normalized_relative_path("p/"))
        component = "c" * 255
        long_path = "/".join([component] * 4)
        self.assertEqual(1023, len(long_path))
        # The terminal slash counts toward the 1,024-byte selector bound.
        self.assertTrue(model.is_selector(long_path + "/"))
        self.assertFalse(model.is_selector(long_path + "x/"))
        # A prefix selector must survive to a SelectedFile and its rule row,
        # because applies-to equals the normalized referring map row.
        model.snapshot_from_json_object(
            snapshot_object(
                selected_files=[
                    root_file_object(),
                    leaf_file_object(applies_to=["src/frontend/"]),
                ],
                effective_rules=[effective_rule_object(applies_to=["src/frontend/"])],
            )
        )

    def test_collection_count_bounds(self):
        model.resolution_input_from_json_object(
            input_object(scope_paths=[f"src/p{index:02d}" for index in range(64)])
        )
        self.assert_input_code(
            input_object(scope_paths=[f"src/p{index:02d}" for index in range(65)]),
            "INPUT_COUNT_LIMIT",
        )
        model.resolution_input_from_json_object(
            input_object(context_chains=[[f"c{index:02d}"] for index in range(32)])
        )
        self.assert_input_code(
            input_object(context_chains=[[f"c{index:02d}"] for index in range(33)]),
            "INPUT_COUNT_LIMIT",
        )
        model.resolution_input_from_json_object(
            input_object(context_chains=[[f"c{index}" for index in range(6)]])
        )
        self.assert_input_code(
            input_object(context_chains=[[f"c{index}" for index in range(7)]]),
            "INPUT_COUNT_LIMIT",
        )
        self.assert_input_code(input_object(context_chains=[[]]), "INPUT_COUNT_LIMIT")
        approvals = [
            approval_object(
                approval_id=f"approval-{index:02d}",
                target=failure_target_object(context_id=f"c{index:02d}"),
            )
            for index in range(64)
        ]
        model.resolution_input_from_json_object(input_object(exception_approvals=approvals))
        approvals.append(
            approval_object(
                approval_id="approval-64", target=failure_target_object(context_id="c64")
            )
        )
        self.assert_input_code(
            input_object(exception_approvals=approvals), "INPUT_COUNT_LIMIT"
        )
        conflicts = [
            conflict_object(source=f"src/c{index:02d}") for index in range(64)
        ]
        model.resolution_input_from_json_object(input_object(declared_conflicts=conflicts))
        conflicts.append(conflict_object(source="src/c64"))
        self.assert_input_code(input_object(declared_conflicts=conflicts), "INPUT_COUNT_LIMIT")

    def test_free_text_and_opaque_reference_bounds(self):
        model.resolution_input_from_json_object(
            input_object(
                exception_approvals=[
                    approval_object(authorization_reference="", reason="r" * 1024)
                ]
            )
        )
        self.assert_input_code(
            input_object(
                exception_approvals=[approval_object(authorization_reference="x" * 1025)]
            ),
            "INPUT_BYTE_LIMIT",
        )
        self.assert_input_code(
            input_object(exception_approvals=[approval_object(reason="")]), "INPUT_VALUE"
        )
        self.assert_input_code(
            input_object(exception_approvals=[approval_object(authorized_by="u" * 65)]),
            "INPUT_BYTE_LIMIT",
        )
        self.assert_input_code(
            input_object(exception_approvals=[approval_object(authorization_digest="A" * 64)]),
            "INPUT_VALUE",
        )

    def test_every_record_at_its_field_maxima_stays_inside_the_record_cap(self):
        payload = approval_object(
            authorized_by="u" * 64,
            authorization_reference="x" * 1024,
            reason="r" * 1024,
            target=failure_target_object(
                code="MISSING_EVIDENCE",
                context_id="c" * 64,
                evidence_path="/".join(["e" * 255] * 4),
            ),
        )
        model.resolution_input_from_json_object(input_object(exception_approvals=[payload]))
        canonical = len(model.canonical_json_text(payload).encode("utf-8"))
        self.assertLessEqual(canonical, model.RECORD_CANONICAL_BYTE_MAX)

    def test_canonical_input_document_cap(self):
        self.assertEqual(131072, model.INPUT_CANONICAL_BYTE_MAX)
        conflicts = [
            {
                "source": f"src/conflict{index:02d}",
                "target": "techstacks/README.md",
                "detail": "d" * 1024,
            }
            for index in range(64)
        ]
        approvals = [
            approval_object(
                approval_id=f"approval-{index:02d}",
                authorization_reference="x" * 1024,
                reason="r" * 1024,
                target=failure_target_object(context_id=f"c{index:02d}"),
            )
            for index in range(64)
        ]
        payload = input_object(declared_conflicts=conflicts, exception_approvals=approvals)
        self.assertGreater(
            len(model.canonical_json_text(payload).encode("utf-8")),
            model.INPUT_CANONICAL_BYTE_MAX,
        )
        error = self.assert_input_code(payload, "INPUT_BYTE_LIMIT")
        self.assertEqual("", error.field)

    def test_snapshot_document_cap_is_exact(self):
        payload, solved = maximum_snapshot_object()
        document = model.canonical_json_document(payload)
        self.assertEqual(131072, len(document.encode("utf-8")))
        snapshot = model.snapshot_from_json_object(payload)
        self.assertEqual(131072, len(model.snapshot_document(snapshot).encode("utf-8")))
        over = maximum_snapshot_object(solved + 1)
        self.assertEqual(131073, len(model.canonical_json_document(over).encode("utf-8")))
        with self.assertRaises(model.TechstackSnapshotError) as error:
            model.snapshot_from_json_object(over)
        self.assertEqual("SNAPSHOT_BYTE_LIMIT", error.exception.code)
        self.assertEqual("", error.exception.field)
        self.assertEqual(
            "Snapshot document exceeds 131072 bytes including terminal LF",
            error.exception.detail,
        )

    def test_integer_and_mode_ranges(self):
        payload = snapshot_object(
            selected_files=[
                root_file_object(),
                leaf_file_object(identity=identity_object(20, mode=4294967295)),
            ]
        )
        model.snapshot_from_json_object(payload)
        for override in (
            {"mode": 4294967296},
            {"device": -1},
            {"mtime_ns": model.INTEGER_MAX + 1},
            {"inode": True},
        ):
            with self.subTest(override=override):
                with self.assertRaises(model.TechstackSnapshotError):
                    model.snapshot_from_json_object(
                        snapshot_object(
                            selected_files=[
                                root_file_object(),
                                leaf_file_object(identity=identity_object(20, **override)),
                            ]
                        )
                    )

    def test_evidence_and_selected_byte_caps(self):
        payload = snapshot_object(
            selected_files=[
                root_file_object(),
                leaf_file_object(
                    identity=identity_object(1),
                    bytes=1,
                    evidence=[{"path": "docs/e.md", "bytes": 1048576, "sha256": DIGEST_C}],
                ),
            ]
        )
        model.snapshot_from_json_object(payload)
        with self.assertRaises(model.TechstackSnapshotError):
            model.snapshot_from_json_object(
                snapshot_object(
                    selected_files=[
                        root_file_object(),
                        leaf_file_object(
                            identity=identity_object(1),
                            bytes=1,
                            evidence=[
                                {"path": "docs/e.md", "bytes": 1048577, "sha256": DIGEST_C}
                            ],
                        ),
                    ]
                )
            )
        model.snapshot_from_json_object(
            snapshot_object(
                selected_files=[
                    root_file_object(identity=identity_object(65536), bytes=65536)
                ],
                effective_rules=[],
            )
        )
        with self.assertRaises(model.TechstackSnapshotError):
            model.snapshot_from_json_object(
                snapshot_object(
                    selected_files=[
                        root_file_object(identity=identity_object(65537), bytes=65537)
                    ],
                    effective_rules=[],
                )
            )

    def test_selected_file_count_cap(self):
        files = [root_file_object()] + [
            leaf_file_object(
                path=f"techstacks/frontend/components/B{index:02d}.md",
                context_id=f"c{index:02d}",
                identity=identity_object(1),
                bytes=1,
                evidence=[],
            )
            for index in range(11)
        ]
        model.snapshot_from_json_object(
            snapshot_object(selected_files=files, effective_rules=[])
        )
        files.append(
            leaf_file_object(
                path="techstacks/frontend/components/B99.md",
                context_id="c99",
                identity=identity_object(1),
                bytes=1,
                evidence=[],
            )
        )
        with self.assertRaises(model.TechstackSnapshotError):
            model.snapshot_from_json_object(
                snapshot_object(selected_files=files, effective_rules=[])
            )

    def test_publication_document_cap_is_exact(self):
        self.assertEqual(262144, model.PUBLICATION_DOCUMENT_BYTE_LIMIT)
        exact = publication_of_document_size(262144)
        self.assertEqual(262144, len(model.publication_document(exact).encode("utf-8")))
        over = publication_of_document_size(262145)
        with self.assertRaises(model.TechstackSnapshotError) as error:
            model.publication_document(over)
        self.assertEqual("PUBLICATION_BYTE_LIMIT", error.exception.code)
        self.assertEqual("", error.exception.field)
        self.assertEqual(
            "Snapshot publication exceeds 262144 bytes", error.exception.detail
        )

    def test_publication_records_and_selected_fields(self):
        snapshot = model.snapshot_from_json_object(snapshot_object())
        resolution = model.Resolution(
            schema_version=1, status="applicable", snapshot=snapshot, diagnostics=()
        )
        attempt = model.SnapshotAttempt(
            ordinal=1,
            artifact_path=f"projects/p/handoffs/T/snapshots/attempt-1-{snapshot.snapshot_sha256}.snapshot.json",
            snapshot_sha256=snapshot.snapshot_sha256,
            publication="created",
            verification_status="match",
        )
        published = model.SnapshotPublication(
            schema_version=1,
            status="published",
            resolution=resolution,
            attempts=(attempt,),
            selected_artifact=attempt.artifact_path,
            selected_snapshot_sha256=attempt.snapshot_sha256,
        )
        self.assertLess(
            len(model.publication_document(published).encode("utf-8")),
            model.PUBLICATION_DOCUMENT_BYTE_LIMIT,
        )
        with self.assertRaises(ValueError):
            model.SnapshotPublication(
                schema_version=1,
                status="published",
                resolution=resolution,
                attempts=(attempt,),
                selected_artifact=None,
                selected_snapshot_sha256=None,
            )
        drifted = model.SnapshotAttempt(
            ordinal=1,
            artifact_path=attempt.artifact_path,
            snapshot_sha256=snapshot.snapshot_sha256,
            publication="identical_existing",
            verification_status="drift",
        )
        model.SnapshotPublication(
            schema_version=1,
            status="observation_drift",
            resolution=resolution,
            attempts=(drifted,),
            selected_artifact=None,
            selected_snapshot_sha256=None,
        )
        with self.assertRaises(ValueError):
            model.SnapshotPublication(
                schema_version=1,
                status="observation_drift",
                resolution=resolution,
                attempts=(drifted,),
                selected_artifact=attempt.artifact_path,
                selected_snapshot_sha256=attempt.snapshot_sha256,
            )
        with self.assertRaises(ValueError):
            model.SnapshotAttempt(
                ordinal=4,
                artifact_path=attempt.artifact_path,
                snapshot_sha256=snapshot.snapshot_sha256,
                publication="created",
                verification_status="match",
            )

    def test_numeric_constants_match_the_design(self):
        self.assertEqual(65536, model.MAP_FILE_BYTE_LIMIT)
        self.assertEqual(65536, model.LEAF_FILE_BYTE_LIMIT)
        self.assertEqual(12, model.SELECTED_FILE_LIMIT)
        self.assertEqual(65536, model.SELECTED_AGGREGATE_BYTE_LIMIT)
        self.assertEqual(6, model.MAP_DEPTH_LIMIT)
        self.assertEqual(32, model.MAP_ROW_LIMIT)
        self.assertEqual(16, model.MAP_ROW_SELECTOR_LIMIT)
        self.assertEqual(1048576, model.EVIDENCE_FILE_BYTE_LIMIT)
        self.assertEqual(64, model.EVIDENCE_FILE_COUNT_LIMIT)
        self.assertEqual(8388608, model.EVIDENCE_AGGREGATE_BYTE_LIMIT)
        self.assertEqual(262144, model.MANAGED_SKILL_FILE_BYTE_LIMIT)
        self.assertEqual(262144, model.EXPORTED_SKILL_FILE_BYTE_LIMIT)
        self.assertEqual(64, model.SKILL_ENTRY_LIMIT)
        self.assertEqual(64, model.SKILL_DIRECTORY_LIMIT)
        self.assertEqual(6, model.SKILL_DEPTH_LIMIT)
        self.assertEqual(4194304, model.SKILL_AGGREGATE_BYTE_LIMIT)
        self.assertEqual(131072, model.CLI_JSON_BYTE_LIMIT)
        self.assertEqual(131072, model.SNAPSHOT_DOCUMENT_BYTE_LIMIT)
        self.assertEqual(262144, model.PUBLICATION_DOCUMENT_BYTE_LIMIT)
        self.assertEqual(128, model.DIAGNOSTIC_COUNT_LIMIT)
        self.assertEqual(64, model.DIFFERENCE_COUNT_LIMIT)
        self.assertEqual(384, model.EFFECTIVE_RULE_COUNT_LIMIT)
        self.assertEqual(3072, model.PROJECT_ROOT_BYTE_MAX)
        self.assertEqual(255, model.PATH_COMPONENT_BYTE_MAX)
        self.assertEqual(1024, model.RELATIVE_PATH_BYTE_MAX)
        self.assertEqual(9223372036854775807, model.INTEGER_MAX)
        self.assertEqual(4294967295, model.MODE_MAX)


class ImportBoundaryTest(unittest.TestCase):
    def _fresh_python(self, code):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_public_import_loads_no_cli_project_or_eval_module(self):
        result = self._fresh_python(
            "import brichan.techstacks; import sys; "
            "forbidden = [name for name in sys.modules if name == 'brichan.cli' "
            "or name.startswith('brichan.cli.') or name == 'brichan.lifecycle' "
            "or name == 'brichan.project' or name == 'evals' "
            "or name.startswith('evals.')]; "
            "assert not forbidden, forbidden"
        )
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
