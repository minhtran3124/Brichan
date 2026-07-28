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


class ConcurrencyContractTest(unittest.TestCase):
    def test_mandatory_receipt_policy_is_explicit(self):
        skill = SKILL_PATH.read_text(encoding="utf-8")
        policies = (
            "A handoff receipt is mandatory for an accepted-plan handoff and "
            "for any multi-writer task.",
            "One child receipt per writer and one parent receipt per task.",
        )
        for policy in policies:
            self.assertIn(
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
        self.assertIn(
            "omit the block or use `null` for every value",
            template,
            "Task packet template must preserve all-null guidance for optional "
            "upstream-plan data.",
        )
        self.assertIn(
            "omit the block or use `null` values",
            skill,
            "Herdr orchestration skill must preserve optional upstream-plan "
            "guidance.",
        )

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
