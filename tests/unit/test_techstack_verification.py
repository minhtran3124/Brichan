"""Verification, publication, and the importable techstacks API vectors.

Every observation runs through the production resolver against real disposable
files under a real no-symlink Git root. Two kinds of injection appear and each
names itself: a spy that mutates the project between a real publish and a real
verify (the only way to schedule an observation race deterministically), and a
lowered cap constant for the structurally unreachable publication byte limit.
Nothing else is stubbed.
"""

import datetime
import json
import os
import shutil
import stat
import subprocess
import sys
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.techstacks import cli, filesystem as fs, model, resolver

from tests.unit.test_techstack_model import (
    maximum_snapshot_object,
    snapshot_object,
)
from tests.unit.test_techstack_resolver import (
    AS_OF,
    ATTEMPT_ID,
    PLAN_ID,
    PLAN_VERSION,
    TASK_ID,
    canonical_temporary_directory,
    leaf_source,
    make_approval,
    make_input,
    map_source,
)


AS_OF_DATE = datetime.date(2026, 8, 24)

#: The one authorized checkout output directory for this task.
CHECKOUT_DIRECTORY = PurePosixPath(
    f"projects/brida-installable-tool/handoffs/{TASK_ID}/snapshots"
)
INSTALLED_DIRECTORY = PurePosixPath(
    f".brichan/project-memory/techstack-snapshots/{TASK_ID}"
)


class ProjectMixin:
    """One real disposable Git root observed through the production reader."""

    def setUp(self):
        super().setUp()
        fs.HELPER_CONTROLLER.reset_for_test()
        self.base = canonical_temporary_directory()
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.root = self.base / "project"
        self.root.mkdir()
        (self.root / ".git").mkdir()

    def write(self, relative, data):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            data = data.encode("utf-8")
        target.write_bytes(data)
        return target

    def write_fixture(self, statement="Keep project context bounded."):
        """Write the smallest opted-in tree: one root map and one leaf."""

        self.write(
            "techstacks/README.md",
            map_source(
                [("general", "techstacks/general.md", (".",))],
                title="Base techstack map",
            ),
        )
        self.write(
            "techstacks/general.md",
            leaf_source(
                "general",
                [("GENERAL-001", statement)],
                title="General rules",
            ),
        )

    def resolved_snapshot(self, **overrides):
        resolution = resolver.resolve_context(make_input(**overrides), self.root)
        self.assertEqual("applicable", resolution.status, resolution.diagnostics)
        return resolution.snapshot

    def verify(self, snapshot, as_of=AS_OF_DATE):
        return cli.verify_snapshot(snapshot, self.root, as_of)

    def artifact_bytes(self, relative):
        return (self.root / relative).read_bytes()


# ---------------------------------------------------------------------------
# Design section 8 verification matrix
# ---------------------------------------------------------------------------


class VerificationMatrixTest(ProjectMixin, unittest.TestCase):
    def test_an_unchanged_project_is_an_exact_match(self):
        self.write_fixture()
        snapshot = self.resolved_snapshot()
        verification = self.verify(snapshot)
        self.assertEqual(
            {
                "schema_version": 1,
                "status": "match",
                "expected_snapshot_sha256": snapshot.snapshot_sha256,
                "observed_snapshot_sha256": snapshot.snapshot_sha256,
                "differences": [],
            },
            {
                key: value
                for key, value in verification.to_json_object().items()
                if key != "observed_resolution"
            },
        )
        observed = verification.observed_resolution
        self.assertEqual("applicable", observed.status)
        self.assertEqual((), observed.diagnostics)
        self.assertEqual(snapshot.to_json_object(), observed.snapshot.to_json_object())

    def test_applicable_drift_carries_the_observed_digest_and_the_changed_leaves(self):
        self.write_fixture()
        snapshot = self.resolved_snapshot()
        self.write_fixture(statement="Keep project context tightly bounded.")
        verification = self.verify(snapshot)
        observed = verification.observed_resolution.snapshot
        self.assertEqual("drift", verification.status)
        self.assertEqual(snapshot.snapshot_sha256, verification.expected_snapshot_sha256)
        self.assertEqual(observed.snapshot_sha256, verification.observed_snapshot_sha256)
        self.assertNotEqual(snapshot.snapshot_sha256, observed.snapshot_sha256)
        codes = {item.code for item in verification.differences}
        self.assertEqual({"VALUE_MISMATCH"}, codes)
        leaf_key = self.difference_field(verification, "statement_sha256")
        self.assertTrue(leaf_key.startswith("/effective_rules/@sha256="), leaf_key)
        self.assertEqual(
            model.difference_representation(snapshot.effective_rules[0].statement_sha256),
            self.difference_at(verification, leaf_key).expected,
        )

    def test_a_blocked_observation_is_exactly_one_observed_blocked(self):
        self.write_fixture()
        snapshot = self.resolved_snapshot()
        # A leaf whose bytes no longer match the grammar blocks resolution.
        self.write("techstacks/general.md", "# Not a leaf\n")
        verification = self.verify(snapshot)
        self.assertEqual("blocked", verification.status)
        self.assertIsNone(verification.observed_snapshot_sha256)
        self.assertEqual("blocked", verification.observed_resolution.status)
        self.assertEqual(
            [
                {
                    "code": "OBSERVED_BLOCKED",
                    "field": "/observed_resolution/status",
                    "expected": '"applicable"',
                    "actual": '"blocked"',
                }
            ],
            [item.to_json_object() for item in verification.differences],
        )

    def test_root_map_disappearance_is_exactly_one_observed_not_applicable(self):
        self.write_fixture()
        snapshot = self.resolved_snapshot()
        shutil.rmtree(self.root / "techstacks")
        verification = self.verify(snapshot)
        self.assertEqual("drift", verification.status)
        self.assertIsNone(verification.observed_snapshot_sha256)
        self.assertEqual("not_applicable", verification.observed_resolution.status)
        self.assertIsNone(verification.observed_resolution.snapshot)
        self.assertEqual((), verification.observed_resolution.diagnostics)
        self.assertEqual(
            [
                {
                    "code": "OBSERVED_NOT_APPLICABLE",
                    "field": "/observed_resolution/status",
                    "expected": '"applicable"',
                    "actual": '"not_applicable"',
                }
            ],
            [item.to_json_object() for item in verification.differences],
        )

    def test_a_root_copy_is_ordinary_identity_drift_and_never_matches(self):
        self.write_fixture()
        snapshot = self.resolved_snapshot()
        copy = self.base / "copy"
        shutil.copytree(self.root, copy, symlinks=True)
        verification = cli.verify_snapshot(snapshot, copy, AS_OF_DATE)
        self.assertEqual("drift", verification.status)
        self.assertIsNotNone(verification.observed_snapshot_sha256)
        fields = {item.field for item in verification.differences}
        self.assertIn("/root_identity/inode", fields)
        # Identity drift is a plain VALUE_MISMATCH, so nothing about it is
        # waivable: the difference registry carries no severity at all.
        self.assertEqual({"VALUE_MISMATCH"}, {item.code for item in verification.differences})

    def test_every_first_class_snapshot_field_change_becomes_one_difference(self):
        self.write_fixture()
        snapshot = self.resolved_snapshot()
        observed = snapshot.to_json_object()
        for field, mutation in (
            ("as_of", "2026-08-23"),
            ("attempt_id", "attempt-2"),
            ("plan_version", 7),
            ("task_id", "TECHSTACK-002"),
            ("plan_id", "TECHSTACK-PLAN-002"),
        ):
            mutated = dict(observed)
            mutated[field] = mutation
            mutated["snapshot_sha256"] = model.snapshot_digest(mutated)
            differences = model.build_snapshot_differences(
                snapshot, model.snapshot_from_json_object(mutated)
            )
            self.assertEqual(
                [
                    {
                        "code": "VALUE_MISMATCH",
                        "field": f"/{field}",
                        "expected": model.difference_representation(observed[field]),
                        "actual": model.difference_representation(mutation),
                    }
                ],
                [item.to_json_object() for item in differences],
                field,
            )

    def test_every_comparable_array_snapshot_field_change_becomes_one_record(self):
        """The four input-carried arrays each difference as one array record.

        ``totals`` has no case here: it is recomputed from ``selected_files``
        and ``effective_rules``, so the Snapshot schema rejects any independent
        mutation of it. Its rows are owned by the verify-driven test below,
        where a real leaf change moves the counts and the arrays together.
        """

        self.write_fixture()
        snapshot = self.resolved_snapshot()
        observed = snapshot.to_json_object()
        approval = make_approval(make_input()).to_json_object()
        for field, element in (
            ("scope_paths", "docs"),
            ("context_chains", ["general"]),
            ("exception_approvals", approval),
            (
                "declared_conflicts",
                {"source": "general", "target": "root", "detail": "conflicting authority"},
            ),
        ):
            mutated = dict(observed)
            mutated[field] = [element]
            mutated["snapshot_sha256"] = model.snapshot_digest(mutated)
            differences = model.build_snapshot_differences(
                snapshot, model.snapshot_from_json_object(mutated)
            )
            self.assertEqual(
                [
                    {
                        "code": "EXTRA_RECORD",
                        "field": f"/{field}/{self.element_pointer(field, element)}",
                        "expected": None,
                        "actual": model.difference_representation(element),
                    }
                ],
                [item.to_json_object() for item in differences],
                field,
            )

    def test_an_array_record_change_reaches_the_api_with_the_totals_it_moved(self):
        """`MISSING_RECORD`/`EXTRA_RECORD` and `/totals` through `verify_snapshot`."""

        rules = [
            ("GENERAL-001", "Keep project context bounded."),
            ("GENERAL-002", "Prefer the smallest change."),
        ]
        self.write(
            "techstacks/README.md",
            map_source(
                [("general", "techstacks/general.md", (".",))],
                title="Base techstack map",
            ),
        )
        self.write_rules(rules)
        expected = self.resolved_snapshot()
        # Dropping the second rule leaves the observed array one record short.
        self.write_rules(rules[:1])
        self.assert_rule_record_drift(expected, "MISSING_RECORD", rules[1])
        # Restoring it and taking the Snapshot the other way round makes the
        # same record an extra one, so both array codes have a step-5 owner.
        expected = self.resolved_snapshot()
        self.write_rules(rules)
        self.assert_rule_record_drift(expected, "EXTRA_RECORD", rules[1])

    def write_rules(self, rules):
        self.write(
            "techstacks/general.md",
            leaf_source("general", list(rules), title="General rules"),
        )

    def assert_rule_record_drift(self, expected, code, rule):
        """Assert the complete Verification object for one leaf-rule change."""

        verification = self.verify(expected)
        observed = verification.observed_resolution.snapshot
        missing = code == "MISSING_RECORD"
        rule_object = self.rule_object(expected if missing else observed, rule[0])
        leaf = f"/selected_files/{self.element_pointer('selected_files', 'techstacks/general.md')}"
        expected_leaf = self.selected_file(expected, "techstacks/general.md")
        observed_leaf = self.selected_file(observed, "techstacks/general.md")
        self.assertEqual(
            {
                "schema_version": 1,
                "status": "drift",
                "expected_snapshot_sha256": expected.snapshot_sha256,
                "observed_snapshot_sha256": observed.snapshot_sha256,
                "differences": [
                    self.mismatch(f"{leaf}/bytes", expected_leaf["bytes"], observed_leaf["bytes"]),
                    self.mismatch(
                        f"{leaf}/identity/ctime_ns",
                        expected_leaf["identity"]["ctime_ns"],
                        observed_leaf["identity"]["ctime_ns"],
                    ),
                    self.mismatch(
                        f"{leaf}/identity/mtime_ns",
                        expected_leaf["identity"]["mtime_ns"],
                        observed_leaf["identity"]["mtime_ns"],
                    ),
                    self.mismatch(
                        f"{leaf}/identity/size",
                        expected_leaf["identity"]["size"],
                        observed_leaf["identity"]["size"],
                    ),
                    self.mismatch(
                        f"{leaf}/sha256", expected_leaf["sha256"], observed_leaf["sha256"]
                    ),
                    self.mismatch(
                        "/totals/bytes",
                        expected.totals.bytes,
                        observed.totals.bytes,
                    ),
                    self.mismatch(
                        "/totals/rule_count",
                        expected.totals.rule_count,
                        observed.totals.rule_count,
                    ),
                    {
                        "code": code,
                        "field": f"/effective_rules/{self.element_pointer('effective_rules', rule_object)}",
                        "expected": (
                            model.difference_representation(rule_object) if missing else None
                        ),
                        "actual": (
                            None if missing else model.difference_representation(rule_object)
                        ),
                    },
                ],
            },
            {
                key: value
                for key, value in verification.to_json_object().items()
                if key != "observed_resolution"
            },
            code,
        )

    def mismatch(self, field, expected, actual):
        return {
            "code": "VALUE_MISMATCH",
            "field": field,
            "expected": model.difference_representation(expected),
            "actual": model.difference_representation(actual),
        }

    def element_pointer(self, segment, element):
        """Re-derive the Design section 8 array-element pointer segment."""

        keys = {
            "exception_approvals": lambda item: item["approval_id"],
            "declared_conflicts": lambda item: [
                item["source"],
                item["target"],
                item["detail"],
            ],
            "selected_files": lambda item: item,
            "effective_rules": lambda item: [
                item["rule_id"],
                item["source_path"],
                item["context_id"],
                item["authority_map"],
                item["applies_to"],
                item["overrides_context_id"],
            ],
        }
        key = keys.get(segment, lambda item: item)(element)
        return f"@sha256={model.sha256_hex(model.canonical_json_bytes(key))}"

    def selected_file(self, snapshot, path):
        for item in snapshot.to_json_object()["selected_files"]:
            if item["path"] == path:
                return item
        raise AssertionError(f"no selected file at {path}")

    def rule_object(self, snapshot, rule_id):
        for item in snapshot.to_json_object()["effective_rules"]:
            if item["rule_id"] == rule_id:
                return item
        raise AssertionError(f"no effective rule {rule_id}")

    def test_more_than_sixty_four_differences_collapse_to_one_limit_record(self):
        rows = [
            (f"leaf{index}", f"techstacks/leaf{index}.md", (".",))
            for index in range(3)
        ]
        self.write("techstacks/README.md", map_source(rows, title="Wide map"))
        for index in range(3):
            self.write(
                f"techstacks/leaf{index}.md",
                leaf_source(
                    f"leaf{index}",
                    [(f"L{index}-{number:03d}", "First statement.") for number in range(32)],
                    title=f"Leaf {index}",
                ),
            )
        snapshot = self.resolved_snapshot()
        self.assertEqual(96, len(snapshot.effective_rules))
        for index in range(3):
            self.write(
                f"techstacks/leaf{index}.md",
                leaf_source(
                    f"leaf{index}",
                    [(f"L{index}-{number:03d}", "Second statement.") for number in range(32)],
                    title=f"Leaf {index}",
                ),
            )
        verification = self.verify(snapshot)
        observed = verification.observed_resolution.snapshot
        self.assertEqual("drift", verification.status)
        self.assertEqual(
            [
                {
                    "code": "DIFFERENCE_LIMIT",
                    "field": "/",
                    "expected": f"snapshot-sha256:{snapshot.snapshot_sha256}",
                    "actual": f"snapshot-sha256:{observed.snapshot_sha256}",
                }
            ],
            [item.to_json_object() for item in verification.differences],
        )

    def difference_at(self, verification, field):
        for item in verification.differences:
            if item.field == field:
                return item
        raise AssertionError(f"no difference at {field}")

    def difference_field(self, verification, suffix):
        for item in verification.differences:
            if item.field.endswith("/" + suffix):
                return item.field
        raise AssertionError(f"no difference ending in {suffix}")


class VerificationPrecedenceTest(ProjectMixin, unittest.TestCase):
    """Design section 14: Snapshot, then as-of, then platform, then root."""

    def test_a_nonsnapshot_argument_is_snapshot_type(self):
        with self.assertRaises(model.TechstackSnapshotError) as error:
            cli.verify_snapshot({}, self.root, AS_OF_DATE)
        self.assertEqual("SNAPSHOT_TYPE", error.exception.code)
        self.assertEqual("", error.exception.field)
        self.assertEqual("snapshot must be a Snapshot", error.exception.detail)

    def test_a_missing_root_argument_is_a_python_type_error(self):
        self.write_fixture()
        snapshot = self.resolved_snapshot()
        with self.assertRaises(TypeError):
            cli.verify_snapshot(snapshot)

    def test_a_datetime_is_not_an_exact_date(self):
        self.write_fixture()
        snapshot = self.resolved_snapshot()
        with self.assertRaises(model.TechstackSnapshotError) as error:
            cli.verify_snapshot(
                snapshot, self.root, datetime.datetime(2026, 8, 24, 12, 0, 0)
            )
        self.assertEqual("SNAPSHOT_AS_OF_TYPE", error.exception.code)
        self.assertEqual("/as_of", error.exception.field)
        self.assertEqual("as_of must be a datetime.date", error.exception.detail)

    def test_an_unequal_date_is_rejected_before_any_project_access(self):
        self.write_fixture()
        snapshot = self.resolved_snapshot()
        with mock.patch.object(cli, "resolve_context") as never:
            with self.assertRaises(model.TechstackSnapshotError) as error:
                cli.verify_snapshot(snapshot, self.root, datetime.date(2026, 8, 25))
        self.assertEqual("SNAPSHOT_AS_OF_MISMATCH", error.exception.code)
        self.assertEqual("/as_of", error.exception.field)
        self.assertEqual("as_of must equal Snapshot as_of", error.exception.detail)
        never.assert_not_called()

    def test_a_root_map_inconsistent_snapshot_is_rejected_before_project_access(self):
        payload = snapshot_object()
        payload["root_map"] = "techstacks/other.md"
        with self.assertRaises(model.TechstackSnapshotError) as error:
            model.snapshot_from_json_object(payload)
        self.assertEqual("SNAPSHOT_VALUE", error.exception.code)
        self.assertEqual("/root_map", error.exception.field)
        payload = snapshot_object()
        payload["root_map"] = None
        with self.assertRaises(model.TechstackSnapshotError) as error:
            model.snapshot_from_json_object(payload)
        self.assertEqual("SNAPSHOT_TYPE", error.exception.code)
        # A Snapshot cannot even be constructed with a divergent root row, so
        # verification can never reach the project with one.
        payload = snapshot_object()
        payload["selected_files"][0]["path"] = "techstacks/elsewhere.md"
        with self.assertRaises(model.TechstackSnapshotError):
            model.snapshot_from_json_object(payload)

    def test_an_unsupported_platform_returns_blocked_in_memory(self):
        self.write_fixture()
        snapshot = self.resolved_snapshot()
        with mock.patch.object(fs, "is_supported_platform", return_value=False):
            verification = self.verify(snapshot)
        self.assertEqual("blocked", verification.status)
        self.assertIsNone(verification.observed_snapshot_sha256)
        self.assertEqual(
            ("UNSUPPORTED_PLATFORM",),
            tuple(item.code for item in verification.observed_resolution.diagnostics),
        )
        self.assertEqual(
            "techstacks is unsupported on this platform",
            verification.observed_resolution.diagnostics[0].detail,
        )

    def test_a_root_defect_raises_the_exact_caller_error(self):
        self.write_fixture()
        snapshot = self.resolved_snapshot()
        with self.assertRaises(model.TechstackInputError) as error:
            cli.verify_snapshot(snapshot, Path("relative/root"), AS_OF_DATE)
        self.assertEqual("PROJECT_ROOT_NOT_ABSOLUTE", error.exception.code)


# ---------------------------------------------------------------------------
# Design section 16 publication protocol
# ---------------------------------------------------------------------------


class PublicationTest(ProjectMixin, unittest.TestCase):
    def publish(self, directory=CHECKOUT_DIRECTORY, **overrides):
        return cli.publish_snapshot(make_input(**overrides), self.root, directory)

    def drifting_verify(self, drifts):
        """Mutate the project before the first ``drifts`` real verifications.

        The publish and the verify are both production calls against real
        bytes; only the moment of the change is scheduled here, because a real
        racing writer cannot be made deterministic on this host.
        """

        real = cli.verify_snapshot
        self.observations = []

        def spy(snapshot, project_root, as_of):
            self.observations.append(snapshot.snapshot_sha256)
            if len(self.observations) <= drifts:
                self.write_fixture(
                    statement=f"Revision {len(self.observations)} of the rule."
                )
            return real(snapshot, project_root, as_of)

        return mock.patch.object(cli, "verify_snapshot", spy)

    def test_a_first_publication_creates_exactly_one_immutable_artifact(self):
        self.write_fixture()
        publication = self.publish()
        expected = self.resolved_snapshot()
        artifact = (
            f"{CHECKOUT_DIRECTORY}/{ATTEMPT_ID}-{expected.snapshot_sha256}"
            ".snapshot.json"
        )
        self.assertEqual(
            {
                "schema_version": 1,
                "status": "published",
                "attempts": [
                    {
                        "ordinal": 1,
                        "artifact_path": artifact,
                        "snapshot_sha256": expected.snapshot_sha256,
                        "publication": "created",
                        "verification_status": "match",
                    }
                ],
                "selected_artifact": artifact,
                "selected_snapshot_sha256": expected.snapshot_sha256,
            },
            {
                key: value
                for key, value in publication.to_json_object().items()
                if key != "resolution"
            },
        )
        self.assertEqual("applicable", publication.resolution.status)
        self.assertEqual(
            model.snapshot_document(expected).encode("utf-8"),
            self.artifact_bytes(artifact),
        )
        mode = stat.S_IMODE((self.root / artifact).stat().st_mode)
        self.assertEqual(0o600, mode)

    def test_republishing_identical_bytes_is_a_zero_write_success(self):
        self.write_fixture()
        first = self.publish()
        target = self.root / first.selected_artifact
        before = (target.stat().st_ino, target.stat().st_mtime_ns, target.read_bytes())
        second = self.publish()
        after = (target.stat().st_ino, target.stat().st_mtime_ns, target.read_bytes())
        self.assertEqual("published", second.status)
        self.assertEqual("identical_existing", second.attempts[0].publication)
        self.assertEqual(first.selected_artifact, second.selected_artifact)
        self.assertEqual(before, after)

    def test_drift_then_match_keeps_the_first_artifact_and_selects_the_second(self):
        self.write_fixture()
        with self.drifting_verify(drifts=1):
            publication = self.publish()
        self.assertEqual("published", publication.status)
        self.assertEqual(2, len(publication.attempts))
        self.assertEqual(
            ["drift", "match"],
            [attempt.verification_status for attempt in publication.attempts],
        )
        self.assertEqual(
            ["created", "created"],
            [attempt.publication for attempt in publication.attempts],
        )
        self.assertEqual(
            publication.attempts[1].artifact_path, publication.selected_artifact
        )
        # The drifted artifact is an immutable leftover: still present, still
        # its original bytes, never renamed, truncated, or deleted.
        leftover = publication.attempts[0]
        self.assertTrue((self.root / leftover.artifact_path).is_file())
        self.assertIn(
            leftover.snapshot_sha256.encode("ascii"),
            self.artifact_bytes(leftover.artifact_path),
        )

    def test_three_drifts_are_observation_drift_with_three_leftovers(self):
        self.write_fixture()
        with self.drifting_verify(drifts=3):
            publication = self.publish()
        self.assertEqual("observation_drift", publication.status)
        self.assertIsNone(publication.selected_artifact)
        self.assertIsNone(publication.selected_snapshot_sha256)
        self.assertEqual([1, 2, 3], [item.ordinal for item in publication.attempts])
        self.assertEqual(
            ["drift", "drift", "drift"],
            [item.verification_status for item in publication.attempts],
        )
        paths = [item.artifact_path for item in publication.attempts]
        self.assertEqual(3, len(set(paths)))
        for attempt in publication.attempts:
            self.assertEqual(
                model.canonical_json_document(
                    model.snapshot_from_json_object(
                        json.loads(
                            self.artifact_bytes(attempt.artifact_path)
                        )
                    ).to_json_object()
                ).encode("utf-8"),
                self.artifact_bytes(attempt.artifact_path),
            )

    def test_drift_then_blocked_stops_with_the_leftover_in_place(self):
        self.write_fixture()
        real = cli.verify_snapshot
        seen = []

        def spy(snapshot, project_root, as_of):
            seen.append(snapshot.snapshot_sha256)
            # The project stops parsing between publish and verify, so the
            # observation is blocked and the next resolve is blocked too.
            self.write("techstacks/general.md", "# Not a leaf\n")
            return real(snapshot, project_root, as_of)

        with mock.patch.object(cli, "verify_snapshot", spy):
            publication = self.publish()
        self.assertEqual("blocked", publication.status)
        self.assertEqual(1, len(publication.attempts))
        self.assertEqual("blocked", publication.attempts[0].verification_status)
        self.assertIsNone(publication.selected_artifact)
        self.assertEqual("blocked", publication.resolution.status)
        self.assertTrue((self.root / publication.attempts[0].artifact_path).is_file())

    def test_a_not_applicable_project_publishes_nothing(self):
        publication = self.publish()
        self.assertEqual(
            {
                "schema_version": 1,
                "status": "not_applicable",
                "attempts": [],
                "selected_artifact": None,
                "selected_snapshot_sha256": None,
            },
            {
                key: value
                for key, value in publication.to_json_object().items()
                if key != "resolution"
            },
        )
        self.assertEqual("not_applicable", publication.resolution.status)
        self.assertFalse((self.root / "projects").exists())

    def test_a_blocked_project_publishes_nothing(self):
        self.write_fixture()
        self.write("techstacks/general.md", "# Not a leaf\n")
        publication = self.publish()
        self.assertEqual("blocked", publication.status)
        self.assertEqual((), publication.attempts)
        self.assertFalse((self.root / "projects").exists())

    def test_the_installed_directory_grammar_is_also_authorized(self):
        self.write_fixture()
        publication = self.publish(directory=INSTALLED_DIRECTORY)
        self.assertEqual("published", publication.status)
        self.assertTrue(
            publication.selected_artifact.startswith(
                f".brichan/project-memory/techstack-snapshots/{TASK_ID}/"
            ),
            publication.selected_artifact,
        )

    def test_an_unauthorized_directory_is_refused_before_any_resolution(self):
        self.write_fixture()
        for directory in (
            PurePosixPath("snapshots"),
            PurePosixPath("projects/Bad_Slug/handoffs/TECHSTACK-001/snapshots"),
            PurePosixPath("projects/p/handoffs/TECHSTACK-002/snapshots"),
            PurePosixPath(".brichan/project-memory/techstack-snapshots/OTHER-1"),
            PurePosixPath("projects/p/handoffs/TECHSTACK-001/snapshots/nested"),
        ):
            with mock.patch.object(cli, "resolve_context") as never:
                with self.assertRaises(cli.SnapshotOutputRefused) as error:
                    self.publish(directory=directory)
            never.assert_not_called()
            # The refusal is a CLI surface condition, not a registry caller
            # error, so it carries the frozen detail rather than a code.
            self.assertEqual(
                cli.SNAPSHOT_OUTPUT_REFUSED_DETAIL, error.exception.detail, directory
            )
        with self.assertRaises(cli.SnapshotOutputRefused):
            self.publish(directory=str(CHECKOUT_DIRECTORY))

    def test_a_nonresolutioninput_argument_is_input_type(self):
        with self.assertRaises(model.TechstackInputError) as error:
            cli.publish_snapshot({}, self.root, CHECKOUT_DIRECTORY)
        self.assertEqual("INPUT_TYPE", error.exception.code)

    def test_a_differing_existing_artifact_is_refused_and_never_overwritten(self):
        self.write_fixture()
        expected = self.resolved_snapshot()
        artifact = (
            f"{CHECKOUT_DIRECTORY}/{ATTEMPT_ID}-{expected.snapshot_sha256}"
            ".snapshot.json"
        )
        self.write(artifact, "{}\n")
        with self.assertRaises(cli.SnapshotOutputRefused):
            self.publish()
        self.assertEqual(b"{}\n", self.artifact_bytes(artifact))

    def test_a_symlinked_artifact_entry_is_refused_without_following_it(self):
        self.write_fixture()
        expected = self.resolved_snapshot()
        artifact = (
            f"{CHECKOUT_DIRECTORY}/{ATTEMPT_ID}-{expected.snapshot_sha256}"
            ".snapshot.json"
        )
        (self.root / CHECKOUT_DIRECTORY).mkdir(parents=True)
        target = self.base / "outside.json"
        target.write_text("{}\n", encoding="utf-8")
        (self.root / artifact).symlink_to(target)
        with self.assertRaises(cli.SnapshotOutputRefused):
            self.publish()
        self.assertEqual("{}\n", target.read_text(encoding="utf-8"))


class PublicationCapTest(ProjectMixin, unittest.TestCase):
    def test_the_publication_cap_literal_and_its_exact_boundary(self):
        self.assertEqual(262144, model.PUBLICATION_DOCUMENT_BYTE_LIMIT)
        self.assertEqual(
            "Snapshot publication exceeds 262144 bytes",
            model.FIXED_DETAILS["PUBLICATION_BYTE_LIMIT"],
        )
        self.assertEqual("PUBLICATION_BYTE_LIMIT", model.SNAPSHOT_ERROR_CODES[10])

    def test_an_over_cap_publication_emits_nothing_and_publishes_no_artifact(self):
        self.write_fixture()
        exact = len(
            model.publication_document(
                cli.publish_snapshot(
                    make_input(), self.root, INSTALLED_DIRECTORY
                )
            ).encode("utf-8")
        )
        # A field-valid publication cannot reach 262,144 bytes (its largest
        # member is a Snapshot capped at 131,072), so the boundary is exercised
        # by lowering the production constant around this document's own size.
        fresh = self.base / "fresh"
        fresh.mkdir()
        (fresh / ".git").mkdir()
        for relative in ("techstacks/README.md", "techstacks/general.md"):
            target = fresh / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((self.root / relative).read_bytes())
        with mock.patch.object(model, "PUBLICATION_DOCUMENT_BYTE_LIMIT", exact - 1):
            with self.assertRaises(model.TechstackSnapshotError) as error:
                cli.publish_snapshot(make_input(), fresh, INSTALLED_DIRECTORY)
        self.assertEqual("PUBLICATION_BYTE_LIMIT", error.exception.code)
        self.assertEqual("", error.exception.field)
        self.assertEqual(
            "Snapshot publication exceeds 262144 bytes", error.exception.detail
        )
        self.assertFalse((fresh / ".brichan").exists())
        with mock.patch.object(model, "PUBLICATION_DOCUMENT_BYTE_LIMIT", exact):
            publication = cli.publish_snapshot(
                make_input(), fresh, INSTALLED_DIRECTORY
            )
        self.assertEqual("published", publication.status)
        self.assertTrue((fresh / publication.selected_artifact).is_file())


class SnapshotDocumentCapTest(ProjectMixin, unittest.TestCase):
    """One 131,072-byte cap across model, file, artifact, pointer, and adapter."""

    def test_the_model_and_api_adapter_share_the_one_cap(self):
        self.assertEqual(131072, model.SNAPSHOT_DOCUMENT_BYTE_LIMIT)
        exact, reason_length = maximum_snapshot_object()
        self.assertEqual(
            131072, len(model.canonical_json_document(exact).encode("utf-8"))
        )
        snapshot = model.snapshot_from_json_object(exact)
        self.assertEqual(131072, len(model.snapshot_document(snapshot).encode("utf-8")))
        over = maximum_snapshot_object(reason_length + 1)
        over["snapshot_sha256"] = model.snapshot_digest(over)
        self.assertEqual(
            131073, len(model.canonical_json_document(over).encode("utf-8"))
        )
        with self.assertRaises(model.TechstackSnapshotError) as error:
            model.snapshot_from_json_object(over)
        self.assertEqual("SNAPSHOT_BYTE_LIMIT", error.exception.code)
        self.assertEqual(
            "Snapshot document exceeds 131072 bytes including terminal LF",
            error.exception.detail,
        )

    def test_the_output_artifact_writer_refuses_one_byte_past_the_cap(self):
        handle = fs.validate_and_open_git_root(self.root)
        self.addCleanup(handle.close)
        exact = "x" * (model.SNAPSHOT_DOCUMENT_BYTE_LIMIT - 1) + "\n"
        self.assertEqual("created", cli._publish_document(handle.fd, "exact.json", exact))
        self.assertEqual(
            model.SNAPSHOT_DOCUMENT_BYTE_LIMIT,
            (self.root / "exact.json").stat().st_size,
        )
        with self.assertRaises(cli.SnapshotOutputRefused):
            cli._publish_document(handle.fd, "over.json", exact + "y")
        self.assertFalse((self.root / "over.json").exists())

    def test_the_packet_pointer_is_only_the_matched_final_artifact(self):
        self.write_fixture()
        published = cli.publish_snapshot(make_input(), self.root, CHECKOUT_DIRECTORY)
        pointer = published.selected_artifact
        self.assertEqual(published.attempts[-1].artifact_path, pointer)
        self.assertLessEqual(
            (self.root / pointer).stat().st_size, model.SNAPSHOT_DOCUMENT_BYTE_LIMIT
        )
        self.assertEqual(
            published.selected_snapshot_sha256,
            model.snapshot_from_json_object(
                json.loads(self.artifact_bytes(pointer))
            ).snapshot_sha256,
        )


class ApiBoundaryTest(unittest.TestCase):
    """The package keeps its command surface in exactly one module."""

    def test_cli_is_the_only_techstacks_module_touching_the_process_streams(self):
        package = ROOT / "src" / "brichan" / "techstacks"
        offenders = []
        for path in sorted(package.glob("*.py")):
            # ``safe_open_helper.py`` is the isolated child's own ``__main__``,
            # not a command surface: it is never imported by the package and
            # its streams carry the frame protocol, not user-facing bytes.
            if path.name in ("cli.py", "safe_open_helper.py"):
                continue
            text = path.read_text(encoding="utf-8")
            for token in ("sys.argv", "sys.stdout", "sys.stderr", "sys.exit"):
                if token in text:
                    offenders.append((path.name, token))
        self.assertEqual([], offenders)

    def test_the_public_package_import_loads_no_cli_or_project_module(self):
        # A fresh interpreter, because this process has already imported the
        # command surface in order to test it.
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT / "src")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import brichan.techstacks; import sys; "
                "assert 'brichan.techstacks.cli' not in sys.modules; "
                "assert not any(name == 'brichan.cli' or name.startswith('brichan.cli.') "
                "or name in ('brichan.lifecycle', 'brichan.project') "
                "or name == 'evals' or name.startswith('evals.') "
                "for name in sys.modules)",
            ],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
