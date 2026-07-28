import contextlib
import io
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import validate_handoff_receipts


class HandoffReceiptValidatorTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.projects = self.root / "projects"
        self.projects.mkdir()

    def receipt(
        self,
        *,
        task_id="TASK-001",
        project="example",
        role="standalone",
        parent="null",
        attempt="1",
        replaces="null",
        status="accepted",
        criterion_status="pending",
        verification_result="pending",
        changed_artifacts="pending",
        diff_evidence="pending",
        test_evidence="pending",
        verdict="null",
        findings="null",
        panes_closed="no",
        memory_updated="yes",
        scope="bounded validator implementation",
    ):
        return textwrap.dedent(
            f"""\
            # Handoff receipt

            Fixture receipt.

            ## Identity

            - Receipt schema version: `1`
            - Receipt role: `{role}`
            - Parent receipt path: `{parent}`
            - Task ID: `{task_id}`
            - Project: `{project}`
            - Handoff timestamp (UTC): `2026-07-28T05:23:11Z`
            - Attempt: `{attempt}`
            - Replaces session: `{replaces}`

            ## Plan version

            - Artifact or plan ID: `{task_id}-P1`
            - Version: `1`
            - Status: `{status}`

            ## Sessions

            | Role | Provider | Model | Brida-owned pane | Session |
            | --- | --- | --- | --- | --- |
            | Implementer | `Codex` | `test-model` | `pane-1` | `session-1` |

            ## Scope

            - In scope: {scope}
            - Authorized paths: `scripts/example.py`
            - Exclusive write ownership: `single writer`
            - Branch: `test-branch`
            - Worktree: `test-worktree`

            ## Non-goals

            - Excluded work: deployment and remote actions

            ## Acceptance criteria

            | Criterion ID | Status | Evidence |
            | --- | --- | --- |
            | `C1` | `{criterion_status}` | `fixture criterion evidence` |

            ## Verification

            | Command | Result |
            | --- | --- |
            | `python3 -m unittest` | `{verification_result}` |

            ## Implementation evidence

            - Changed artifacts: `{changed_artifacts}`
            - Diff evidence: `{diff_evidence}`
            - Test evidence: `{test_evidence}`

            ## Review verdict

            - Verdict: `{verdict}`
            - Findings: `{findings}`

            ## Risks and open decisions

            - Risks: `fixture risk`
            - Open decisions: `null`

            ## Cleanup status

            - Brida-owned panes closed: `{panes_closed}`
            - Project memory updated: `{memory_updated}`
            """
        )

    def write_receipt(self, content, project="example", task_id="TASK-001"):
        path = self.projects / project / "handoffs" / task_id / "receipt.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_validator(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = validate_handoff_receipts.main([str(self.projects)])
        return result, stdout.getvalue(), stderr.getvalue()

    def assert_invalid(self, diagnostic):
        result, _, stderr = self.run_validator()
        self.assertNotEqual(0, result)
        self.assertIn("receipt.md", stderr)
        self.assertIn(diagnostic, stderr)

    def implemented_receipt(self, **overrides):
        values = {
            "status": "implemented",
            "criterion_status": "pass",
            "verification_result": "pass; fixture tests",
            "changed_artifacts": "scripts/example.py",
            "diff_evidence": "commit abc123",
            "test_evidence": "fixture tests pass",
            "panes_closed": "no",
            "memory_updated": "no",
        }
        values.update(overrides)
        return self.receipt(**values)

    def reviewed_receipt(self, **overrides):
        values = {
            "status": "reviewed",
            "criterion_status": "pass",
            "verification_result": "pass; fixture tests",
            "changed_artifacts": "scripts/example.py",
            "diff_evidence": "commit abc123",
            "test_evidence": "fixture tests pass",
            "verdict": "PASS",
            "findings": "null",
            "panes_closed": "yes",
            "memory_updated": "yes",
        }
        values.update(overrides)
        return self.receipt(**values)

    def test_valid_accepted_receipt_is_not_mutated(self):
        content = self.receipt()
        path = self.write_receipt(content)

        result, stdout, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)
        self.assertIn("Validated 1 canonical handoff receipt", stdout)
        self.assertEqual(content, path.read_text(encoding="utf-8"))

    def test_valid_implemented_receipt(self):
        self.write_receipt(self.implemented_receipt())

        result, _, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)

    def test_valid_reviewed_pass_receipt(self):
        self.write_receipt(self.reviewed_receipt())

        result, _, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)

    def test_valid_changes_required_receipt_during_remediation(self):
        content = self.reviewed_receipt(
            criterion_status="fail",
            verification_result="fail; reviewer mutation",
            verdict="CHANGES REQUIRED",
            findings="C1 must reject the reviewer mutation",
            panes_closed="no",
            memory_updated="no",
        )
        self.write_receipt(content)

        result, _, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)

    def test_valid_parent_and_child_topology(self):
        parent = self.receipt(task_id="PARENT", role="parent")
        child = self.receipt(
            task_id="CHILD",
            role="child",
            parent="projects/example/handoffs/PARENT/receipt.md",
        )
        self.write_receipt(parent, task_id="PARENT")
        self.write_receipt(child, task_id="CHILD")

        result, stdout, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)
        self.assertIn("Validated 2 canonical handoff receipt", stdout)

    def test_missing_required_field_reports_file_and_field(self):
        content = self.receipt().replace("- Project: `example`\n", "")
        self.write_receipt(content)

        self.assert_invalid("Identity.Project")

    def test_bad_path_identity_reports_expected_task(self):
        self.write_receipt(self.receipt(task_id="OTHER"))

        self.assert_invalid("expected 'TASK-001' from canonical path")

    def test_bad_role_parent_topology_is_rejected(self):
        content = self.receipt(role="child", parent="null")
        self.write_receipt(content)

        self.assert_invalid("child receipts require a repo-relative canonical")

    def test_incomplete_reviewed_pass_is_rejected(self):
        content = self.reviewed_receipt(criterion_status="pending")
        self.write_receipt(content)

        self.assert_invalid("reviewed PASS requires every criterion to pass")

    def test_reviewed_pass_requires_implementation_evidence(self):
        content = self.reviewed_receipt(changed_artifacts="TBD")
        self.write_receipt(content)

        self.assert_invalid("Implementation evidence.Changed artifacts")

    def test_reviewed_pass_cleanup_failure_is_rejected(self):
        content = self.reviewed_receipt(panes_closed="no")
        self.write_receipt(content)

        self.assert_invalid("Cleanup status.Brida-owned panes closed")

    def test_replacement_attempt_requires_provenance(self):
        content = self.receipt(attempt="2", replaces="null")
        self.write_receipt(content)

        self.assert_invalid("later attempts require concrete replacement")

    def test_attempt_one_cannot_claim_replacement(self):
        content = self.receipt(attempt="1", replaces="prior-session")
        self.write_receipt(content)

        self.assert_invalid("attempt 1 must not replace a prior session")

    def test_personal_and_home_paths_are_rejected(self):
        for index, unsafe_path in enumerate(
            ("/Users/alice/repo", "/home/alice/repo", "~/repo"),
            start=1,
        ):
            with self.subTest(unsafe_path=unsafe_path):
                task_id = f"TASK-{index:03d}"
                content = self.receipt(task_id=task_id, scope=unsafe_path)
                self.write_receipt(content, task_id=task_id)

        result, _, stderr = self.run_validator()

        self.assertNotEqual(0, result)
        self.assertEqual(3, stderr.count("path hygiene"))

    def test_historical_evaluation_receipts_are_not_discovered(self):
        historical = (
            self.root / "evals" / "mixed-provider-coding" / "receipt.md"
        )
        historical.parent.mkdir(parents=True)
        historical.write_text("not a canonical receipt", encoding="utf-8")

        result, stdout, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)
        self.assertIn("Validated 0 canonical handoff receipt", stdout)


if __name__ == "__main__":
    unittest.main()
