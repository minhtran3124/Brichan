import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / ".agents/skills/herdr-orchestration/SKILL.md"
TASK_PACKET_PATH = (
    ROOT / ".agents/skills/herdr-orchestration/references/task-packet.md"
)
RECEIPT_PATH = (
    ROOT / ".agents/skills/herdr-orchestration/references/handoff-receipt.md"
)
CONCURRENT_WRITERS_PATH = (
    ROOT / ".agents/skills/herdr-orchestration/references/concurrent-writers.md"
)
WORKER_RECOVERY_PATH = (
    ROOT / ".agents/skills/herdr-orchestration/references/worker-recovery.md"
)


def normalize_markdown_prose(text):
    return re.sub(r"\s+", " ", text).strip()


class ConcurrencyContractTest(unittest.TestCase):
    def assert_policy(self, policy, text, message):
        self.assertIn(
            normalize_markdown_prose(policy),
            normalize_markdown_prose(text),
            message,
        )

    def test_mandatory_receipt_policy_is_explicit(self):
        skill = SKILL_PATH.read_text(encoding="utf-8")
        policies = (
            "A handoff receipt is mandatory for an accepted-plan handoff and "
            "for any multi-writer task.",
            "One child receipt per writer and one parent receipt per task.",
        )
        for policy in policies:
            self.assert_policy(
                policy,
                skill,
                f"Herdr orchestration policy must include policy anchor: {policy}",
            )

    def test_task_packet_declares_receipt_requirement(self):
        template = TASK_PACKET_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "Receipt requirement: <mandatory or not-required>",
            template,
            "Task packet template must declare whether a receipt is mandatory.",
        )

    def test_handoff_receipt_template_captures_concurrent_writer_identity(self):
        template = RECEIPT_PATH.read_text(encoding="utf-8")
        required_labels = (
            "Receipt role:",
            "Parent receipt path:",
            "Exclusive write ownership:",
            "Branch:",
            "Worktree:",
        )
        for label in required_labels:
            self.assertIn(
                label,
                template,
                f"Handoff receipt template must include the {label!r} field.",
            )

    def test_concurrent_writer_reference_has_required_structure_and_policy(self):
        self.assertTrue(
            CONCURRENT_WRITERS_PATH.is_file(),
            "Concurrent-writer policy reference must exist at "
            "references/concurrent-writers.md.",
        )
        reference = CONCURRENT_WRITERS_PATH.read_text(encoding="utf-8")
        headings = re.findall(r"^## (.+)$", reference, re.MULTILINE)
        self.assertEqual(
            (
                "Exclusive file ownership",
                "Worktree isolation",
                "Receipt requirements",
                "Integration",
            ),
            tuple(headings),
            "Concurrent-writer reference must contain exactly the required H2 "
            "headings in order.",
        )
        for policy in (
            "Authorized path sets must not overlap.",
            "One branch and one worktree per writer.",
        ):
            self.assertIn(
                policy,
                reference,
                f"Concurrent-writer reference must include policy anchor: {policy}",
            )

    def test_concurrent_writer_policy_is_linked_from_skill(self):
        skill = SKILL_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "references/concurrent-writers.md",
            skill,
            "Herdr orchestration skill must link to the concurrent-writer policy.",
        )

    def test_optional_upstream_plan_guidance_remains_compatible(self):
        template = TASK_PACKET_PATH.read_text(encoding="utf-8")
        skill = SKILL_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "Upstream plan and receipt (optional):",
            template,
            "Task packet template must retain its optional upstream-plan block.",
        )
        self.assert_policy(
            "omit the block or use `null` for every value",
            template,
            "Task packet template must preserve all-null guidance for optional "
            "upstream-plan data.",
        )
        self.assert_policy(
            "omit the block or use `null` values",
            skill,
            "Herdr orchestration skill must preserve optional upstream-plan "
            "guidance.",
        )

    def test_normalized_policy_checks_tolerate_only_cosmetic_reflow(self):
        recovery = WORKER_RECOVERY_PATH.read_text(encoding="utf-8")
        policy = (
            "Replacement does not grant broader permissions, authority, paths, "
            "or goals."
        )
        harmless_reflow = policy.replace("authority, paths", "authority,\npaths")
        semantic_mutation = policy.replace("does not grant broader", "grants broader")
        self.assert_policy(
            policy,
            recovery,
            "The shipped worker-recovery policy must include the real anchor.",
        )
        self.assert_policy(policy, harmless_reflow, "Wrapping must be harmless.")
        self.assertNotIn(
            normalize_markdown_prose(policy),
            normalize_markdown_prose(semantic_mutation),
            "Broadening replacement authority must fail its contract.",
        )

    def test_canonical_receipt_storage_policy_is_structural(self):
        skill = SKILL_PATH.read_text(encoding="utf-8")
        receipt = RECEIPT_PATH.read_text(encoding="utf-8")
        task_packet = TASK_PACKET_PATH.read_text(encoding="utf-8")
        policy = (
            "Store operational receipts at "
            "`projects/<slug>/handoffs/<task-id>/receipt.md`"
        )
        self.assert_policy(policy, skill, "Skill must define canonical storage.")
        self.assert_policy(
            "Historical receipts under `evals/` remain evidence; "
            "do not migrate them",
            receipt,
            "Historical evaluation evidence must remain outside migration.",
        )
        self.assert_policy(
            "When a receipt is mandatory, use its canonical repo-relative path",
            task_packet,
            "Task packets must point mandatory receipts to canonical storage.",
        )

    def test_worker_recovery_policy_is_linked_and_bounded(self):
        self.assertTrue(
            WORKER_RECOVERY_PATH.is_file(),
            "Worker-recovery policy reference must exist.",
        )
        skill = SKILL_PATH.read_text(encoding="utf-8")
        recovery = WORKER_RECOVERY_PATH.read_text(encoding="utf-8")
        self.assertIn("references/worker-recovery.md", skill)
        policies = (
            "Elapsed time alone never makes a worker stale.",
            "Record three consecutive no-progress observations before "
            "assigning stale status.",
            "The default retry limit is one replacement attempt.",
            "The replacement must reuse the accepted plan, canonical receipt, "
            "authorized scope, and write ownership.",
            "Replacement does not grant broader permissions, authority, paths, "
            "or goals.",
            "Escalate after the one-replacement limit is exhausted.",
            "Preserve the original session and pane evidence before replacement.",
            "Do not rewrite or discard evidence from the original session.",
            "Close only panes that Brida created and recorded.",
        )
        for policy in policies:
            self.assert_policy(
                policy,
                recovery,
                f"Worker recovery must preserve policy anchor: {policy}",
            )
        for state in ("`stale`", "`abandoned`", "`replaced`"):
            self.assertIn(state, recovery)

    def test_concurrent_writer_reference_has_no_path_or_code_span_hygiene_issues(self):
        self.assertTrue(
            CONCURRENT_WRITERS_PATH.is_file(),
            "Concurrent-writer policy reference must exist before hygiene can be "
            "checked.",
        )
        reference = CONCURRENT_WRITERS_PATH.read_text(encoding="utf-8")
        self.assertNotIn(
            "/Users/",
            reference,
            "Concurrent-writer reference must not contain a personal macOS home path.",
        )
        self.assertNotIn(
            "/home/",
            reference,
            "Concurrent-writer reference must not contain a personal Unix home path.",
        )
        code_spans = re.findall(r"`([^`\n]*)`", reference)
        self.assertFalse(
            any("|" in span for span in code_spans),
            "Concurrent-writer reference must not contain raw pipes inside inline "
            "code spans.",
        )


if __name__ == "__main__":
    unittest.main()
