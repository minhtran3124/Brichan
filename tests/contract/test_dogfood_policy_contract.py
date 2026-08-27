"""The shipped dogfood policy must mandate the delegated worker lifecycle.

Regression guard for the coordinator-does-everything failure: with only a
soft "delegate when it helps" principle, the coordinator implemented, tested,
and installed dependencies inline and never spawned a worker. The policy now
has to state the delegation mandate and the coordinator's write boundary.
"""

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

POLICY = ROOT / "src/brichan/resources/dogfood_v1/policy"

PACKAGED_PRINCIPLES = POLICY / "operating-principles.md"
CHECKOUT_PRINCIPLES = ROOT / "docs/policy/operating-principles.md"
REVIEWER = ROOT / "docs/policy/reviewer.md"
PACKAGED_TECHSTACKS = POLICY / "techstacks.md"
CHECKOUT_TECHSTACKS = ROOT / "docs/policy/techstacks.md"

#: Testing-discipline norms both operating policies must state. Each entry
#: carries one requirement, not a topic heading, so removing the rule from
#: either surface fails the contract.
TESTING_DISCIPLINE_MARKERS = (
    # Owned behavior (R1).
    "application-owned observable behavior",
    # Test creation quality (R2).
    "distinct justification",
    "observed failure",
    "duplicate",
    "speculative",
    "implementation-coupled",
    # Focused-to-broad order and intentional specialized suites (R3).
    "smallest relevant checks",
    "sequentially by default",
    "E2E, race, load, and stress tests are used intentionally, for a specific "
    "identified risk, never by default",
    # Static checks only when configured (R4).
    "configures them",
    # Failure diagnosis and assertion preservation (R5).
    "before code or tests change",
    "meaningful assertion",
    # The completion gate stays the completion gate (R6).
    "never replace",
)


def normalized(path: Path) -> str:
    """Read a policy with whitespace runs collapsed.

    Both files are wrapped at 80 columns, so markers must assert wording
    rather than line breaks.
    """

    return " ".join(path.read_text(encoding="utf-8").split())


class DogfoodPolicyDelegationTest(unittest.TestCase):
    def setUp(self):
        self.principles = (POLICY / "operating-principles.md").read_text(
            encoding="utf-8"
        )
        self.bootstrap = (POLICY / "bootstrap.md").read_text(encoding="utf-8")

    def test_principles_mandate_the_worker_lifecycle_for_repository_changes(self):
        for phrase in (
            "plan",
            "implement",
            "review",
            "worker lifecycle",
        ):
            self.assertIn(phrase, self.principles, phrase)
        self.assertNotIn(
            "Delegate only when",
            self.principles,
            "the soft delegate-when-it-helps rule must not return",
        )

    def test_principles_mandate_all_three_phases_without_exception(self):
        """No bounded-edit escape hatch may reappear in the shipped policy.

        The exception let a coordinator declare a change "small" and skip the
        `plan` worker, which is how the lifecycle was bypassed in practice.
        """
        self.assertIn("All three phases are mandatory", self.principles)
        for phrase in ("Skip the", "bounded edit", "only for"):
            self.assertNotIn(
                phrase,
                self.principles,
                f"the skip-plan exception must not return via {phrase!r}",
            )

    def test_principles_gate_integration_on_the_independent_review_worker(self):
        self.assertIn(
            "integrates a change only after the",
            self.principles,
        )
        self.assertIn("independent `review` worker", self.principles)

    def test_principles_bound_coordinator_writes_to_project_memory(self):
        self.assertIn(".brichan/project-memory/", self.principles)
        self.assertIn("do not edit repository files", self.principles.lower())

    def test_bootstrap_states_that_workers_execute(self):
        self.assertIn("You are Brichan", self.bootstrap)
        self.assertIn("You coordinate; workers execute", self.bootstrap)
        for phrase in ("plan", "implement", "review"):
            self.assertIn(phrase, self.bootstrap, phrase)


class TestingDisciplineContractTest(unittest.TestCase):
    """Both operating policies must carry the risk-based testing discipline.

    The observed failure is generated coverage nobody uses: duplicate,
    speculative, or implementation-coupled cases, broad suites run by reflex,
    and assertions weakened to make a gate pass. Each marker below carries one
    norm, so deleting the rule from either policy surface fails here.
    """

    def setUp(self):
        self.checkout = normalized(CHECKOUT_PRINCIPLES)
        self.packaged = normalized(PACKAGED_PRINCIPLES)
        self.reviewer = normalized(REVIEWER)

    def test_both_policies_state_every_testing_discipline_norm(self):
        for text, label in ((self.checkout, "checkout"), (self.packaged, "packaged")):
            for marker in TESTING_DISCIPLINE_MARKERS:
                self.assertIn(marker, text, f"{label}: {marker}")

    def test_the_unconditional_static_check_demand_does_not_return(self):
        """R4: this repository configures no linter or type checker."""

        self.assertNotIn("tests, lint/typecheck", self.checkout)

    def test_reviewers_must_flag_more_than_missing_tests(self):
        for marker in ("redundant", "non-owned", "implementation-coupled"):
            self.assertIn(marker, self.reviewer, marker)


class ShippedTechstackPolicyTest(unittest.TestCase):
    """The techstack contract must ship, not only exist in the checkout.

    An installed coordinator reads `.brichan/policy/`, never `docs/policy/`.
    A packaged policy that silently loses the delivery contract would leave
    installed coordinators inventing packet and receipt shapes; each marker
    below carries one obligation rather than a topic heading.
    """

    def setUp(self):
        self.checkout = normalized(CHECKOUT_TECHSTACKS)
        self.packaged = normalized(PACKAGED_TECHSTACKS)

    def test_the_packaged_policy_ships_beside_the_other_managed_policies(self):
        self.assertTrue(PACKAGED_TECHSTACKS.is_file(), PACKAGED_TECHSTACKS)
        self.assertEqual(POLICY, PACKAGED_TECHSTACKS.parent)

    def test_both_surfaces_keep_techstacks_project_owned(self):
        for text, label in ((self.checkout, "checkout"), (self.packaged, "packaged")):
            self.assertIn("belongs to the target project", text, label)
            self.assertIn("`techstacks/README.md`", text, label)
            self.assertIn("map-only", text, label)

    def test_both_surfaces_forbid_rule_bodies_in_a_packet_or_receipt(self):
        for text, label in ((self.checkout, "checkout"), (self.packaged, "packaged")):
            self.assertIn("never", text, label)
            self.assertIn("rule bodies", text, label)
            self.assertIn("opens the pointers itself", text, label)

    def test_the_installed_surface_names_only_the_installed_directory(self):
        """A packaged policy must not send an installed coordinator to
        `projects/<slug>/handoffs/`, which does not exist there."""

        self.assertIn(
            ".brichan/project-memory/techstack-snapshots/<TASK-ID>",
            self.packaged,
        )
        self.assertNotIn(
            "projects/<project-slug>/handoffs/<TASK-ID>/snapshots",
            self.packaged,
        )

    def test_neither_surface_softens_the_delegated_acceptance_rule(self):
        for text, label in ((self.checkout, "checkout"), (self.packaged, "packaged")):
            self.assertNotIn("the worker may accept", text, label)
            self.assertNotIn("trust the worker", text, label)
            self.assertIn("is a claim, not evidence", text, label)


if __name__ == "__main__":
    unittest.main()
