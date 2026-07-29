import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.check_compatibility_retirement import (
    REQUIRED_GATES,
    is_eligible,
    validate_config,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/compatibility-retirement.json"


class CompatibilityRetirementContractTest(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_current_gate_is_eligible_and_retired(self):
        self.assertEqual([], validate_config(self.config))
        self.assertTrue(self.config["retired"])
        self.assertTrue(is_eligible(self.config))
        self.assertEqual(
            "pass",
            self.config["gates"]["release_window"]["status"],
        )
        self.assertEqual(
            "pass",
            self.config["gates"]["full_ci"]["status"],
        )
        self.assertEqual(
            "pass",
            self.config["gates"]["claude_startup"]["status"],
        )
        self.assertEqual(
            "projects/brida-repository-structure-refactor/handoffs/"
            "RSR-011-L/receipt.md#RSR-011-L-1",
            self.config["gates"]["claude_startup"]["evidence"],
        )

    def test_require_eligible_accepts_current_gate(self):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/check_compatibility_retirement.py",
                "--require-eligible",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("eligible: yes", result.stdout)

    def test_all_gates_need_dated_repository_evidence(self):
        eligible = copy.deepcopy(self.config)
        for gate in REQUIRED_GATES:
            eligible["gates"][gate] = {
                "status": "pass",
                "checked_at": "2026-07-28T12:00:00Z",
                "evidence": "CHANGELOG.md#Changelog",
            }
        eligible["gates"]["release_window"]["evidence"] = (
            "CHANGELOG.md#[0.2.0]"
        )
        self.assertEqual([], validate_config(eligible))
        self.assertTrue(is_eligible(eligible))

        eligible["gates"]["full_ci"]["evidence"] = None
        errors = validate_config(eligible)
        self.assertIn(
            "gates.full_ci.evidence must be a repository file plus #fragment",
            errors,
        )
        self.assertFalse(is_eligible(eligible))

        eligible["gates"]["full_ci"] = {
            "status": "pass",
            "checked_at": "2026-07-28",
            "evidence": "CHANGELOG.md#Changelog",
        }
        self.assertIn(
            "gates.full_ci: pass requires a timezone-aware ISO-8601 checked_at",
            validate_config(eligible),
        )
        self.assertFalse(is_eligible(eligible))

        eligible["gates"]["full_ci"] = {
            "status": "pass",
            "checked_at": True,
            "evidence": ".#Changelog",
        }
        errors = validate_config(eligible)
        self.assertIn(
            "gates.full_ci: pass requires a timezone-aware ISO-8601 checked_at",
            errors,
        )
        self.assertIn(
            "gates.full_ci.evidence file missing: .",
            errors,
        )
        self.assertFalse(is_eligible(eligible))

    def test_release_window_rejects_partial_unreleased_fragment(self):
        config = copy.deepcopy(self.config)
        for gate in REQUIRED_GATES:
            config["gates"][gate] = {
                "status": "pass",
                "checked_at": "2026-07-28T12:00:00Z",
                "evidence": "CHANGELOG.md#Changelog",
            }
        config["gates"]["release_window"]["evidence"] = (
            "CHANGELOG.md#[Unreleased"
        )
        self.assertIn(
            "gates.release_window.evidence must reference a versioned "
            "CHANGELOG section",
            validate_config(config),
        )
        self.assertFalse(is_eligible(config))

    def test_protected_pointer_mapping_cannot_be_narrowed(self):
        narrowed = copy.deepcopy(self.config)
        narrowed["temporary_paths"] = narrowed["temporary_paths"][:1]
        self.assertIn(
            "temporary_paths must exactly match the protected policy-docs-v1 "
            "pointer mapping",
            validate_config(narrowed),
        )

    def test_retired_state_requires_changelog_evidence(self):
        retired = copy.deepcopy(self.config)
        retired["retirement_evidence"]["changelog"] = {
            "status": "pending",
            "checked_at": None,
            "evidence": None,
        }
        errors = validate_config(retired)
        self.assertIn(
            "retired migration requires passing changelog evidence",
            errors,
        )
        self.assertIn(
            "retired migration requires dated changelog evidence",
            errors,
        )
        self.assertIn(
            "retirement_evidence.changelog.evidence must be a repository "
            "file plus #fragment",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
