"""Worker-ledger record, write, read, resolver, and ``finish`` behavior.

Every case below pins application-owned observable behavior. The write
mechanics are new filesystem code on a brand-new path, so the fail-closed
rules (`PY-004`) and the loss-free recovery rules are pinned as rejections
that must fail if their guard is removed (`TEST-003`).
"""

import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.orchestration import worker_ledger
from brichan.orchestration.worker_ledger import (
    LedgerLocation,
    LedgerPathError,
    build_finished_record,
    build_launched_record,
    finished_record,
    installed_location,
    parse_records,
    read_records,
    record_finish,
    record_launch,
    resolve_checkout_location,
)


class _Route:
    """The duck-typed shape ``ResolvedRoute`` presents to the ledger."""

    def __init__(self, runtime="claude", model="a-model", effort="high"):
        self.runtime = runtime
        self.model = model
        self.effort = effort


SPLIT_PAYLOAD = {
    "id": "cli:pane:split",
    "result": {
        "pane": {"pane_id": "p2", "tab_id": "t1", "workspace_id": "w1"},
        "type": "pane_info",
    },
}


class LedgerTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        # ``resolve`` matters on this platform: the default temporary root sits
        # under a symlinked ancestor, and the walk below opens its base with
        # ``O_NOFOLLOW``.
        self.base = Path(self.temporary.name).resolve()

    def location(self, *parts):
        return LedgerLocation(base=self.base, parts=parts or ("ledger", "workers.jsonl"))

    def ledger_path(self):
        return self.base / "ledger" / "workers.jsonl"

    def lines(self):
        return self.ledger_path().read_bytes().split(b"\n")


class RecordConstructionTest(LedgerTestCase):
    """The record schema is the product's durable contract (R4-R6, M7).

    Consumers join and report from these exact fields and null rules, so a
    silently renamed key or an inferred value is the regression.
    """

    def test_a_routed_record_carries_every_field_with_no_nulls(self):
        record = build_launched_record(
            launch_id="11111111-1111-4111-8111-111111111111",
            worker="brichan-worker",
            task_id="WLG-001",
            route_name="implement",
            route=_Route(),
            command=("claude", "--model", "a-model"),
            pane_id="p2",
            split_payload=SPLIT_PAYLOAD,
            launched_at="2026-09-23T01:02:03Z",
        )
        self.assertEqual(
            {
                "schema_version": 1,
                "event": "launched",
                "launch_id": "11111111-1111-4111-8111-111111111111",
                "worker": "brichan-worker",
                "task_id": "WLG-001",
                "route": "implement",
                "runtime": "claude",
                "model": "a-model",
                "effort": "high",
                "pane_id": "p2",
                "workspace_id": "w1",
                "tab_id": "t1",
                "launched_at": "2026-09-23T01:02:03Z",
                "source": "brichan-herdr-agent-start",
            },
            record,
        )

    def test_a_legacy_record_nulls_route_model_and_effort(self):
        record = build_launched_record(
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            route_name=None,
            route=None,
            command=("codex", "--model", "legacy-model"),
            pane_id="p2",
            split_payload=SPLIT_PAYLOAD,
            launched_at="2026-09-23T01:02:03Z",
        )
        self.assertIsNone(record["route"])
        self.assertIsNone(record["model"])
        self.assertIsNone(record["effort"])
        self.assertIsNone(record["task_id"])
        # The runtime comes from the validated legacy argv, never a guess.
        self.assertEqual("codex", record["runtime"])

    def test_a_missing_envelope_section_records_null_rather_than_raising(self):
        record = build_launched_record(
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            route_name=None,
            route=None,
            command=("codex",),
            pane_id="p2",
            split_payload={"id": "cli:pane:split", "result": {"type": "pane_info"}},
            launched_at="2026-09-23T01:02:03Z",
        )
        self.assertIsNone(record["workspace_id"])
        self.assertIsNone(record["tab_id"])

    def test_a_generated_launch_identifier_is_never_null(self):
        """R14: the identifier is generated at launch, never derived later."""

        location = self.location()
        self.assertIsNone(
            record_launch(
                location,
                launch_id="22222222-2222-4222-8222-222222222222",
                worker="brichan-worker",
                task_id=None,
                route_name="implement",
                route=_Route(),
                command=("claude",),
                pane_id="p2",
                split_payload=SPLIT_PAYLOAD,
            )
        )
        (record,) = read_records(location).records
        self.assertEqual("22222222-2222-4222-8222-222222222222", record["launch_id"])

    def test_a_finished_record_records_when_it_was_recorded_only(self):
        """R2: an actual finish time is unknowable here, so nothing is estimated."""

        record = build_finished_record(
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            pane_id=None,
            evidence=["projects/x/handoffs/T/implementation.md"],
            observed_at="2026-09-23T01:02:03Z",
        )
        self.assertEqual("2026-09-23T01:02:03Z", record["observed_at"])
        self.assertEqual("coordinator", record["source"])
        for absent in ("finished_at", "duration", "completed_at", "ended_at"):
            self.assertNotIn(absent, record)


class OpenDisciplineTest(LedgerTestCase):
    def test_a_fifo_at_the_ledger_path_is_refused_without_blocking(self):
        """M1, `PY-004`: a non-regular file must never hang a started launch.

        The FIFO is created by path, never with ``dir_fd``, which macOS Python
        3.10 does not support.
        """

        (self.base / "ledger").mkdir()
        os.mkfifo(self.ledger_path())

        reason = record_launch(
            self.location(),
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            route_name="implement",
            route=_Route(),
            command=("claude",),
            pane_id="p2",
            split_payload=SPLIT_PAYLOAD,
        )
        self.assertIsNotNone(reason)
        self.assertIn("not a regular file", reason)
        self.assertTrue(stat.S_ISFIFO(os.lstat(self.ledger_path()).st_mode))

    def test_a_directory_at_the_ledger_path_is_refused(self):
        (self.base / "ledger" / "workers.jsonl").mkdir(parents=True)

        reason = record_launch(
            self.location(),
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            route_name="implement",
            route=_Route(),
            command=("claude",),
            pane_id="p2",
            split_payload=SPLIT_PAYLOAD,
        )
        self.assertIsNotNone(reason)
        self.assertTrue(self.ledger_path().is_dir())

    def test_a_symlinked_ledger_directory_is_refused_without_following_it(self):
        """`PY-004`/R11: no symlink is followed for the directory or the file."""

        (self.base / "elsewhere").mkdir()
        os.symlink(self.base / "elsewhere", self.base / "ledger")

        reason = record_launch(
            self.location(),
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            route_name="implement",
            route=_Route(),
            command=("claude",),
            pane_id="p2",
            split_payload=SPLIT_PAYLOAD,
        )
        self.assertIsNotNone(reason)
        self.assertEqual([], list((self.base / "elsewhere").iterdir()))

    def test_a_symlinked_ledger_file_is_refused_without_following_it(self):
        (self.base / "ledger").mkdir()
        target = self.base / "outside.jsonl"
        target.write_bytes(b"")
        os.symlink(target, self.ledger_path())

        reason = record_launch(
            self.location(),
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            route_name="implement",
            route=_Route(),
            command=("claude",),
            pane_id="p2",
            split_payload=SPLIT_PAYLOAD,
        )
        self.assertIsNotNone(reason)
        self.assertEqual(b"", target.read_bytes())

    def test_a_symlinked_component_inside_the_relative_path_is_refused(self):
        """PR2-M1: the ``O_NOFOLLOW`` walk starts at the one defined base.

        The link is created inside the test tree, because the platform's own
        temporary root already sits under a symlinked ancestor.
        """

        (self.base / "real").mkdir()
        os.symlink(self.base / "real", self.base / "link")

        reason = record_launch(
            self.location("link", "ledger", "workers.jsonl"),
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            route_name="implement",
            route=_Route(),
            command=("claude",),
            pane_id="p2",
            split_payload=SPLIT_PAYLOAD,
        )
        self.assertIsNotNone(reason)
        self.assertEqual([], list((self.base / "real").iterdir()))

    def test_only_the_files_own_parent_directory_is_ever_created(self):
        """A missing ancestor is a write failure, never a ``makedirs``."""

        reason = record_launch(
            self.location("missing", "ledger", "workers.jsonl"),
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            route_name="implement",
            route=_Route(),
            command=("claude",),
            pane_id="p2",
            split_payload=SPLIT_PAYLOAD,
        )
        self.assertIsNotNone(reason)
        self.assertFalse((self.base / "missing").exists())


class WriteIntegrityTest(LedgerTestCase):
    def _append(self, **overrides):
        payload = {
            "launch_id": "id",
            "worker": "brichan-worker",
            "task_id": None,
            "route_name": "implement",
            "route": _Route(),
            "command": ("claude",),
            "pane_id": "p2",
            "split_payload": SPLIT_PAYLOAD,
        }
        payload.update(overrides)
        return record_launch(self.location(), **payload)

    def test_a_short_write_is_reported_as_a_failure(self):
        """M2: a write that lands fewer bytes than the record must not pass.

        Reported as observable output rather than by counting calls (L4).
        """

        real_write = os.write

        def short_write(descriptor, data):
            return real_write(descriptor, data[: len(data) // 2])

        with mock.patch("os.write", short_write):
            reason = self._append()
        self.assertIsNotNone(reason)
        self.assertIn("short ledger write", reason)

    def test_a_crash_fragment_costs_no_later_record_and_counts_one_skip(self):
        """M2: the defect the reviewer reproduced — a fragment swallowing a record."""

        self.assertIsNone(self._append(launch_id="first"))
        with self.ledger_path().open("ab") as handle:
            handle.write(b'{"event": "launched", "laun')
        self.assertIsNone(self._append(launch_id="second"))

        read = read_records(self.location())
        self.assertEqual(
            ["first", "second"], [record["launch_id"] for record in read.records]
        )
        self.assertEqual(1, read.skipped)

    def test_a_double_repaired_fragment_reports_no_phantom_corruption(self):
        """PR2-L1: two writers repairing one fragment leave a benign blank line.

        Counting it would overstate damage that never occurred, so consumers
        would report corruption on a ledger that lost nothing.
        """

        data = (
            b'{"event": "launched", "launch_id": "first"}\n'
            b'{"event": "launched", "laun'
            b'\n{"event": "launched", "launch_id": "second"}\n'
            b'\n{"event": "launched", "launch_id": "third"}\n'
        )
        read = parse_records(data)
        self.assertEqual(
            ["first", "second", "third"],
            [record["launch_id"] for record in read.records],
        )
        self.assertEqual(1, read.skipped)

    def test_two_separately_opened_descriptors_yield_two_decodable_lines(self):
        """R10 as observable output rather than as a race test (L4)."""

        self.assertIsNone(self._append(launch_id="first"))
        self.assertIsNone(self._append(launch_id="second"))

        read = read_records(self.location())
        self.assertEqual(
            ["first", "second"], [record["launch_id"] for record in read.records]
        )
        self.assertEqual(0, read.skipped)
        self.assertEqual(b"", self.lines()[-1])

    def test_each_record_is_one_sorted_key_json_line(self):
        self.assertIsNone(self._append())
        (line,) = [item for item in self.lines() if item]
        keys = list(json.loads(line).keys())
        self.assertEqual(sorted(keys), keys)
        self.assertFalse(line.endswith(b" "))


class NeverRaiseTest(LedgerTestCase):
    def test_a_non_oserror_defect_returns_a_reason_and_never_raises(self):
        """M3: no exception class from ledger code may reach the launcher.

        The launcher's outer handler would otherwise turn a ``KeyError`` into
        exit 1 or let a ``TypeError`` escape as a traceback, which is exactly
        what R7 forbids. Narrowing ``except Exception`` must fail this test.
        """

        reason = record_launch(
            self.location(),
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            route_name=None,
            route=None,
            command=None,
            pane_id="p2",
            split_payload=SPLIT_PAYLOAD,
        )
        self.assertIsNotNone(reason)
        self.assertIn("TypeError", reason)
        self.assertFalse(self.ledger_path().exists())


class CheckoutResolverTest(LedgerTestCase):
    """PR2-M1/PR2-M2: the flag's accepted surface is the whole guard.

    Each refusal below must fail if its rule is removed: one mistaken flag
    value must never reach managed state or leave the checkout.
    """

    def test_a_conventional_relative_jsonl_path_is_accepted(self):
        location = resolve_checkout_location(
            self.base, "projects/slug/ledger/workers.jsonl"
        )
        self.assertEqual(self.base, location.base)
        self.assertEqual(
            ("projects", "slug", "ledger", "workers.jsonl"), location.parts
        )

    def test_every_refused_value_is_refused_and_touches_nothing(self):
        refused = (
            # The exact reproduction that flipped a healthy project to malformed.
            ".brichan/manifest.json",
            ".brichan/ledger/workers.jsonl",
            # The case variant: this platform's default filesystem is
            # case-insensitive, so a case-sensitive check would let it through.
            ".BRICHAN/ledger/workers.jsonl",
            ".Brichan/stray.jsonl",
            "projects/.BriChan/workers.jsonl",
            "../outside/workers.jsonl",
            "projects/../.brichan/workers.jsonl",
            "./projects/slug/workers.jsonl",
            "/absolute/workers.jsonl",
            "projects/slug/ledger/notes.txt",
            "projects//slug/workers.jsonl",
            "projects/slug/ledger/",
            "",
        )
        before = sorted(path.name for path in self.base.iterdir())
        for value in refused:
            with self.subTest(value=value):
                with self.assertRaises(LedgerPathError):
                    resolve_checkout_location(self.base, value)
        self.assertEqual(before, sorted(path.name for path in self.base.iterdir()))

    def test_the_launcher_and_finish_resolve_one_identical_path(self):
        """R15/PR2-L2: the same inputs named two different files before this.

        Both entry points call this one resolver against one checkout root, so
        a launch and its later ``finish`` can never disagree.
        """

        value = "projects/slug/ledger/workers.jsonl"
        launcher_side = resolve_checkout_location(self.base, value)
        finish_side = resolve_checkout_location(self.base, value)
        self.assertEqual(launcher_side, finish_side)
        self.assertEqual(launcher_side.path, finish_side.path)

    def test_the_installed_path_is_identical_for_both_entry_points(self):
        self.assertEqual(
            installed_location(self.base).path,
            self.base / ".brichan" / "ledger" / "workers.jsonl",
        )


class StateGuardTest(LedgerTestCase):
    """R9: a partial ``.brichan`` is diagnosed ``malformed``.

    Writing into one, or creating one, would break the target project. The
    flag can no longer name a ``.brichan`` path at all, so the fixed installed
    path is the guard's remaining reachable surface.
    """

    def test_an_uninitialized_state_directory_is_never_created(self):
        reason = record_launch(
            installed_location(self.base),
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            route_name="implement",
            route=_Route(),
            command=("claude",),
            pane_id="p2",
            split_payload=SPLIT_PAYLOAD,
        )
        self.assertIsNotNone(reason)
        self.assertFalse((self.base / ".brichan").exists())

    def test_a_state_directory_without_a_manifest_is_never_written_into(self):
        (self.base / ".brichan").mkdir()

        reason = record_launch(
            installed_location(self.base),
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            route_name="implement",
            route=_Route(),
            command=("claude",),
            pane_id="p2",
            split_payload=SPLIT_PAYLOAD,
        )
        self.assertIsNotNone(reason)
        self.assertIn("no ledger for this target", reason)
        self.assertEqual([], list((self.base / ".brichan").iterdir()))

    def test_a_manifest_that_is_not_a_regular_file_is_refused(self):
        (self.base / ".brichan").mkdir()
        (self.base / ".brichan" / "manifest.json").mkdir()

        reason = record_launch(
            installed_location(self.base),
            launch_id="id",
            worker="brichan-worker",
            task_id=None,
            route_name="implement",
            route=_Route(),
            command=("claude",),
            pane_id="p2",
            split_payload=SPLIT_PAYLOAD,
        )
        self.assertIsNotNone(reason)
        self.assertFalse((self.base / ".brichan" / "ledger").exists())

    def test_an_initialized_state_directory_accepts_the_fixed_ledger(self):
        (self.base / ".brichan").mkdir()
        (self.base / ".brichan" / "manifest.json").write_text("{}", encoding="utf-8")

        self.assertIsNone(
            record_launch(
                installed_location(self.base),
                launch_id="id",
                worker="brichan-worker",
                task_id=None,
                route_name="implement",
                route=_Route(),
                command=("claude",),
                pane_id="p2",
                split_payload=SPLIT_PAYLOAD,
            )
        )
        self.assertTrue(
            (self.base / ".brichan" / "ledger" / "workers.jsonl").is_file()
        )


class FinishRefusalTest(LedgerTestCase):
    def setUp(self):
        super().setUp()
        self.ledger = self.location()
        self.assertIsNone(
            record_launch(
                self.ledger,
                launch_id="launch-1",
                worker="brichan-worker",
                task_id=None,
                route_name="implement",
                route=_Route(),
                command=("claude",),
                pane_id="p2",
                split_payload=SPLIT_PAYLOAD,
            )
        )
        self.baseline = self.ledger_path().read_bytes()

    def finish(self, **overrides):
        payload = {
            "launch_id": "launch-1",
            "worker": "brichan-worker",
            "task_id": None,
            "pane_id": None,
            "evidence": ["projects/x/handoffs/T/implementation.md"],
        }
        payload.update(overrides)
        return record_finish(self.ledger, **payload)

    def test_a_matched_launch_identifier_records_one_attestation(self):
        self.assertIsNone(self.finish())
        records = read_records(self.ledger).records
        self.assertEqual(["launched", "finished"], [r["event"] for r in records])
        self.assertEqual("launch-1", records[1]["launch_id"])

    def test_an_unmatched_launch_identifier_is_refused_and_writes_nothing(self):
        """M7: a finish that names no launch is refused, never flagged."""

        reason = self.finish(launch_id="launch-unknown")
        self.assertIsNotNone(reason)
        self.assertIn("no launched record", reason)
        self.assertEqual(self.baseline, self.ledger_path().read_bytes())

    def test_a_second_finish_for_one_launch_is_refused_and_writes_nothing(self):
        """PR2-L3: each launch takes at most one attestation.

        Without the refusal, consumers promised one attestation would have to
        choose between competing ones.
        """

        self.assertIsNone(self.finish())
        after_first = self.ledger_path().read_bytes()

        reason = self.finish()
        self.assertIsNotNone(reason)
        self.assertIn("already has a finished record", reason)
        self.assertEqual(after_first, self.ledger_path().read_bytes())

    def test_the_first_finished_record_in_file_order_wins(self):
        """The consumer tie-break when two overlapping runs both pass the check.

        The refusal is a check-then-append with no lock, so "at most one" is a
        one-at-a-time guarantee; this rule is what keeps consumers
        deterministic when the calls overlap.
        """

        records = (
            {"event": "launched", "launch_id": "launch-1"},
            {"event": "finished", "launch_id": "launch-1", "evidence": ["first"]},
            {"event": "finished", "launch_id": "launch-1", "evidence": ["second"]},
        )
        self.assertEqual(["first"], finished_record(records, "launch-1")["evidence"])
        self.assertIsNone(finished_record(records, "launch-2"))


class FinishCommandTest(LedgerTestCase):
    """L1: the attestation refusals bound fabrication and typos.

    The CLI cannot verify completion, so the guards on who and what it records
    are the only thing between an attestation and a guess.
    """

    def setUp(self):
        super().setUp()
        self.project = self.base / "target"
        (self.project / ".brichan").mkdir(parents=True)
        (self.project / ".brichan" / "manifest.json").write_text(
            "{}", encoding="utf-8"
        )
        self.checkout_ledger = "projects/slug/ledger/workers.jsonl"
        (self.base / "projects" / "slug").mkdir(parents=True)
        self.checkout_path = self.base / self.checkout_ledger
        self.assertIsNone(
            record_launch(
                resolve_checkout_location(self.base, self.checkout_ledger),
                launch_id="launch-1",
                worker="brichan-worker",
                task_id=None,
                route_name="implement",
                route=_Route(),
                command=("claude",),
                pane_id="p2",
                split_payload=SPLIT_PAYLOAD,
            )
        )

    def checkout_finish(self, *arguments):
        return worker_ledger.checkout_main(self.base, list(arguments))

    def test_a_checkout_finish_records_through_the_shared_resolver(self):
        self.assertEqual(
            0,
            self.checkout_finish(
                "finish",
                "--worker",
                "brichan-worker",
                "--launch-id",
                "launch-1",
                "--evidence",
                "projects/x/handoffs/T/implementation.md",
                "--task",
                "WLG-001",
                "--pane",
                "p2",
                "--ledger-file",
                self.checkout_ledger,
            ),
        )
        records = parse_records(self.checkout_path.read_bytes()).records
        self.assertEqual("finished", records[-1]["event"])
        self.assertEqual("WLG-001", records[-1]["task_id"])
        self.assertEqual("p2", records[-1]["pane_id"])

    def test_a_worker_name_without_the_prefix_is_refused(self):
        before = self.checkout_path.read_bytes()
        self.assertEqual(
            1,
            self.checkout_finish(
                "finish",
                "--worker",
                "not-a-brichan-worker",
                "--launch-id",
                "launch-1",
                "--evidence",
                "projects/x/handoffs/T/implementation.md",
                "--ledger-file",
                self.checkout_ledger,
            ),
        )
        self.assertEqual(before, self.checkout_path.read_bytes())

    def test_an_empty_or_whitespace_evidence_item_is_refused(self):
        before = self.checkout_path.read_bytes()
        for item in ("", "   ", "\t\n"):
            with self.subTest(item=item):
                self.assertEqual(
                    1,
                    self.checkout_finish(
                        "finish",
                        "--worker",
                        "brichan-worker",
                        "--launch-id",
                        "launch-1",
                        "--evidence",
                        "projects/x/handoffs/T/implementation.md",
                        "--evidence",
                        item,
                        "--ledger-file",
                        self.checkout_ledger,
                    ),
                )
        self.assertEqual(before, self.checkout_path.read_bytes())

    def test_a_checkout_finish_without_a_ledger_file_is_a_usage_error(self):
        with mock.patch("sys.stderr"):
            self.assertEqual(
                2,
                self.checkout_finish(
                    "finish",
                    "--worker",
                    "brichan-worker",
                    "--launch-id",
                    "launch-1",
                    "--evidence",
                    "e",
                ),
            )

    def test_a_refused_ledger_file_value_is_a_usage_error(self):
        with mock.patch("sys.stderr"):
            self.assertEqual(
                2,
                self.checkout_finish(
                    "finish",
                    "--worker",
                    "brichan-worker",
                    "--launch-id",
                    "launch-1",
                    "--evidence",
                    "e",
                    "--ledger-file",
                    ".brichan/ledger/workers.jsonl",
                ),
            )

    def test_the_installed_entrypoint_rejects_a_ledger_file_flag(self):
        """The installed ledger has exactly one path, so the flag cannot exist.

        Accepting it there would give installed mode a second ledger location
        and reopen the managed-state surface the narrowing closed.
        """

        with mock.patch("sys.stderr"):
            self.assertEqual(
                2,
                worker_ledger.main(
                    [
                        "finish",
                        "--worker",
                        "brichan-worker",
                        "--launch-id",
                        "launch-1",
                        "--evidence",
                        "e",
                        "--ledger-file",
                        "projects/slug/ledger/workers.jsonl",
                    ]
                ),
            )

    def test_an_installed_finish_against_a_target_without_state_creates_nothing(self):
        bare = self.base / "bare"
        bare.mkdir()
        (bare / ".git").mkdir()

        with mock.patch("sys.stderr"):
            self.assertEqual(
                1,
                worker_ledger.main(
                    [
                        "finish",
                        "--worker",
                        "brichan-worker",
                        "--launch-id",
                        "launch-1",
                        "--evidence",
                        "e",
                        "--project",
                        str(bare),
                    ]
                ),
            )
        self.assertFalse((bare / ".brichan").exists())

    def test_a_target_whose_ledger_does_not_exist_yet_is_an_unmatched_finish(self):
        """A healthy target with no ledger holds no launched record.

        Reporting that as an I/O failure would tell a coordinator the
        filesystem broke when the real answer is that the identifier matches
        nothing; nothing is created either way.
        """

        (self.project / ".git").mkdir()
        with mock.patch("sys.stderr"):
            self.assertEqual(
                1,
                worker_ledger.main(
                    [
                        "finish",
                        "--worker",
                        "brichan-worker",
                        "--launch-id",
                        "launch-1",
                        "--evidence",
                        "e",
                        "--project",
                        str(self.project),
                    ]
                ),
            )
        self.assertFalse((self.project / ".brichan/ledger").exists())

    def test_an_installed_finish_uses_the_fixed_state_root_ledger(self):
        (self.project / ".git").mkdir()
        self.assertIsNone(
            record_launch(
                installed_location(self.project),
                launch_id="launch-2",
                worker="brichan-worker",
                task_id=None,
                route_name="implement",
                route=_Route(),
                command=("claude",),
                pane_id="p2",
                split_payload=SPLIT_PAYLOAD,
            )
        )
        self.assertEqual(
            0,
            worker_ledger.main(
                [
                    "finish",
                    "--worker",
                    "brichan-worker",
                    "--launch-id",
                    "launch-2",
                    "--evidence",
                    "projects/x/handoffs/T/implementation.md",
                    "--project",
                    str(self.project),
                ]
            ),
        )
        records = parse_records(
            (self.project / ".brichan/ledger/workers.jsonl").read_bytes()
        ).records
        self.assertEqual(["launched", "finished"], [r["event"] for r in records])


if __name__ == "__main__":
    unittest.main()
