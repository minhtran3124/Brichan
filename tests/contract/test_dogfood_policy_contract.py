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

    def test_principles_bound_coordinator_writes_to_project_memory(self):
        self.assertIn(".brichan/project-memory/", self.principles)
        self.assertIn("do not edit repository files", self.principles.lower())

    def test_bootstrap_states_that_workers_execute(self):
        self.assertIn("You are Brichan", self.bootstrap)
        self.assertIn("You coordinate; workers execute", self.bootstrap)
        for phrase in ("plan", "implement", "review"):
            self.assertIn(phrase, self.bootstrap, phrase)


if __name__ == "__main__":
    unittest.main()
