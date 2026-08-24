"""The packaged dogfood skill must carry the checkout skill's safeguards.

Regression guard for the observed drift: the packaged
`herdr-orchestration` skill shipped without the done/idle-is-not-proof
invariant, the bounded-wait rule, the truncation and evidence-file fallback,
the no-automatic-input rule, the paste-swallowed-Enter guidance, and the
no-progress evidence rule, while the checkout skill carried them. Parity is
now asserted here, so future drift fails `make check`.
"""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKOUT_SKILL = ROOT / ".agents/skills/herdr-orchestration"
PACKAGED_SKILL = ROOT / "src/brichan/resources/dogfood_v1/skills/herdr-orchestration"

#: Marker phrases that must appear in both skill trees. Each one carries a
#: safeguard, not merely a topic heading.
PARITY_MARKERS = (
    # Scheduling state is never completion evidence (requirements R1).
    "is not proof",
    "scheduling signal only",
    # Bounded waits (requirements R8).
    "at most 30 seconds",
    # Truncation and the evidence-file fallback (requirements R2, R11).
    "truncation risk",
    "possible",
    "confirmed",
    "the normal healthy outcome",
    "evidence-file fallback",
    "never acceptance evidence",
    # No automatic input (requirements R13).
    "Never send input to a worker automatically",
    "blocked",
    # Paste-swallowed-Enter recovery stays manual, and names the actual action
    # plus its observation precondition (requirements R13, R14).
    "[Pasted text #1]",
    "manual coordinator step",
    "herdr pane send-keys <pane-id> Enter",
    "herdr agent get",
    "herdr agent read",
    # No-progress evidence rule from references/worker-recovery.md.
    "three timestamped no-progress",
    "one bounded replacement",
    "escalate",
    # The monitoring surface both trees route observation through.
    "brichan-herdr-agent-observe",
)


def tree_text(root: Path) -> str:
    """Concatenate a skill tree's Markdown with whitespace normalized.

    Normalizing lets the markers assert wording rather than line wrapping, so
    a reflow of either tree does not produce a false parity failure.
    """

    joined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*.md"))
        if path.is_file()
    )
    return " ".join(joined.split())


class SkillParityContractTest(unittest.TestCase):
    def setUp(self):
        self.checkout = tree_text(CHECKOUT_SKILL)
        self.packaged = tree_text(PACKAGED_SKILL)

    def test_both_skill_trees_exist(self):
        self.assertTrue((CHECKOUT_SKILL / "SKILL.md").is_file())
        self.assertTrue((PACKAGED_SKILL / "SKILL.md").is_file())
        self.assertTrue((CHECKOUT_SKILL / "references/commands.md").is_file())
        self.assertTrue((PACKAGED_SKILL / "references/commands.md").is_file())

    def test_the_checkout_skill_states_every_safeguard(self):
        for marker in PARITY_MARKERS:
            self.assertIn(marker, self.checkout, marker)

    def test_the_packaged_skill_states_every_safeguard(self):
        for marker in PARITY_MARKERS:
            self.assertIn(marker, self.packaged, marker)

    def test_the_done_is_not_proof_invariant_is_stated_verbatim_in_both(self):
        phrase = (
            "A worker's `done` or `idle` state is not proof that acceptance "
            "criteria passed."
        )
        self.assertIn(phrase, self.checkout)
        self.assertIn(phrase, self.packaged)

    def test_neither_tree_promises_a_reachable_truncation_none_on_0_7_3(self):
        for text in (self.checkout, self.packaged):
            self.assertIn("0.7.3", text)
            self.assertIn("`possible` is the normal healthy outcome", text)

    def test_neither_tree_authorises_automatic_worker_input(self):
        for text in (self.checkout, self.packaged):
            self.assertNotIn("automatically send", text)
            self.assertNotIn("auto-answer", text)
            self.assertIn("Never send input to a worker automatically", text)

    def test_both_trees_state_the_actual_paste_recovery_action(self):
        """Code review v2, finding L1.

        A sentence saying recovery exists is not guidance. Both trees must name
        the command that sends the swallowed Enter, so the packaged skill can
        no longer satisfy parity by describing the topic alone.
        """

        for text in (self.checkout, self.packaged):
            self.assertIn("herdr pane send-keys <pane-id> Enter", text)

    def test_both_trees_gate_the_paste_recovery_on_a_fresh_observation(self):
        """The action must never appear without its precondition."""

        for text in (self.checkout, self.packaged):
            self.assertIn("[Pasted text #1]", text)
            self.assertIn("herdr agent get", text)
            self.assertIn("herdr agent read", text)
            self.assertIn("idle", text)
            # The Enter is conditional on the agent still being idle with an
            # unsubmitted prompt, never sent on elapsed time alone.
            action = text.index("herdr pane send-keys <pane-id> Enter")
            window = text[max(0, action - 900) : action + 900]
            self.assertIn("idle", window)
            self.assertIn("unsubmitted", window)
            self.assertIn("herdr agent read", window)

    def test_neither_tree_permits_unobserved_or_automated_enter(self):
        for text in (self.checkout, self.packaged):
            self.assertNotIn("always send Enter", text)
            self.assertNotIn("send Enter automatically", text)
            self.assertIn("Never send input to a worker automatically", text)

    def test_the_recovery_note_stays_scoped_to_the_recovery_flow(self):
        """Code review v3, finding L1-v3.

        The recovered Enter is the only manual keypress *in this recovery
        flow*. Saying it is the only input a coordinator ever sends to a worker
        contradicts ordinary task-packet dispatch through `herdr pane run`, and
        could mislead an installed coordinator into treating normal dispatch as
        prohibited. This negative assertion keeps the overbroad wording out.
        """

        overbroad = (
            "the only input a coordinator ever sends",
            "only input a coordinator ever sends to a worker",
            "the only input ever sent to a worker",
            "never send any other input to a worker",
        )
        for text in (self.checkout, self.packaged):
            for phrase in overbroad:
                self.assertNotIn(phrase, text, phrase)
        # The scoped wording and the ordinary dispatch path both stay stated.
        self.assertIn(
            "this is the only manual keypress in this recovery flow", self.packaged
        )
        for text in (self.checkout, self.packaged):
            self.assertIn("herdr pane run", text)

    def test_both_task_packet_templates_point_to_their_operating_policy(self):
        """Plan review v1, finding H1.

        Workers receive no managed instruction injection, so the task packet
        is the delivery mechanism for the operating policy. Each template
        must direct the worker to the policy path its surface can read.
        """

        checkout = (CHECKOUT_SKILL / "references/task-packet.md").read_text(
            encoding="utf-8"
        )
        packaged = (PACKAGED_SKILL / "references/task-packet.md").read_text(
            encoding="utf-8"
        )
        for text in (checkout, packaged):
            normalized = " ".join(text.split())
            self.assertIn("Applicable operating policy", normalized)
            self.assertIn(
                "including its testing discipline, before running "
                "Required verification",
                normalized,
            )
        self.assertIn("docs/policy/operating-principles.md", checkout)
        self.assertIn(".brichan/policy/operating-principles.md", packaged)

    def test_both_trees_route_observation_through_the_read_only_helper(self):
        for text in (self.checkout, self.packaged):
            self.assertIn("brichan-herdr-agent-observe preflight", text)
            self.assertIn("brichan-herdr-agent-observe observe", text)


if __name__ == "__main__":
    unittest.main()
