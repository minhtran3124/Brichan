import json
import sys
import tempfile
import unittest
from pathlib import Path

BRIDA_ROOT = Path(__file__).resolve().parent.parent
if str(BRIDA_ROOT) not in sys.path:
    sys.path.insert(0, str(BRIDA_ROOT))

from metrics.validate_metrics import load_rows, render_summary


def valid_row():
    return {
        "schema_version": 1,
        "run_id": "eval-1",
        "task_id": "EVAL-1",
        "track": "reviewer",
        "started_at": "2026-07-27T00:00:00Z",
        "completed_at": "2026-07-27T00:00:01Z",
        "elapsed_seconds": 1,
        "verdict": "PASS",
        "acceptance_passed": 2,
        "acceptance_total": 2,
        "worker_count": 1,
        "blocker_count": 0,
        "user_intervention_count": 0,
        "reviewer_finding_count": 4,
        "coordinator_input_tokens": None,
        "coordinator_output_tokens": None,
        "worker_input_tokens": 100,
        "worker_output_tokens": 20,
        "cost_usd": None,
        "cost_source": None,
        "evidence": ["command"],
        "notes": "fixture",
    }


class MetricsValidationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.ledger_index = 0

    def write_ledger(self, rows):
        self.ledger_index += 1
        path = Path(self.temp_dir.name) / f"ledger-{self.ledger_index}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
        return path

    def test_valid_row_passes(self):
        rows, errors = load_rows(self.write_ledger([valid_row()]))
        self.assertEqual(1, len(rows))
        self.assertEqual([], errors)

    def test_missing_required_field_fails(self):
        row = valid_row()
        del row["verdict"]
        _, errors = load_rows(self.write_ledger([row]))
        self.assertTrue(any("missing fields: verdict" in error for error in errors))

    def test_invalid_verdict_fails(self):
        row = valid_row()
        row["verdict"] = "GOOD"
        _, errors = load_rows(self.write_ledger([row]))
        self.assertTrue(any("verdict must be" in error for error in errors))

    def test_negative_tokens_fail(self):
        row = valid_row()
        row["worker_input_tokens"] = -1
        _, errors = load_rows(self.write_ledger([row]))
        self.assertTrue(any("worker_input_tokens" in error for error in errors))

    def test_unavailable_timing_is_explicitly_allowed(self):
        row = valid_row()
        row["started_at"] = None
        row["completed_at"] = None
        row["elapsed_seconds"] = None
        _, errors = load_rows(self.write_ledger([row]))
        self.assertEqual([], errors)

    def test_partial_timing_fails(self):
        row = valid_row()
        row["completed_at"] = None
        _, errors = load_rows(self.write_ledger([row]))
        self.assertTrue(any("both be observed" in error for error in errors))

    def test_timestamp_order_is_enforced(self):
        row = valid_row()
        row["completed_at"] = "2026-07-26T23:59:59Z"
        _, errors = load_rows(self.write_ledger([row]))
        self.assertTrue(any("cannot precede" in error for error in errors))

    def test_pass_requires_all_acceptance_checks(self):
        row = valid_row()
        row["acceptance_passed"] = 1
        _, errors = load_rows(self.write_ledger([row]))
        self.assertTrue(any("PASS requires" in error for error in errors))

    def test_worker_tokens_require_a_worker(self):
        row = valid_row()
        row["worker_count"] = 0
        _, errors = load_rows(self.write_ledger([row]))
        self.assertTrue(any("worker token fields" in error for error in errors))

    def test_summary_is_deterministic(self):
        summary = render_summary([valid_row()])
        self.assertEqual(
            "\n".join(
                [
                    "runs=1",
                    "verdicts=PASS:1,PARTIAL:0,FAIL:0",
                    "workers=1",
                    "blockers=0",
                    "acceptance=2/2",
                    "tokens=coordinator_input_tokens:0/0obs,"
                    "coordinator_output_tokens:0/0obs,"
                    "worker_input_tokens:100/1obs,"
                    "worker_output_tokens:20/1obs",
                    "unknown_token_rows=1",
                    "cost_observed_rows=0",
                ]
            ),
            summary,
        )


if __name__ == "__main__":
    unittest.main()
