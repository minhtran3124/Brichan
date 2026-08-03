"""Focused unit tests for the TDW-008 pilot fixture."""

import unittest

from release_policy import (
    ENVIRONMENT_NOT_SANDBOX,
    REMOTE_PUBLISH_FORBIDDEN,
    ROLLBACK_PLAN_MISSING,
    SECRET_ACCESS_FORBIDDEN,
    evaluate_release_policy,
)


def safe_policy(**overrides):
    """Return a compliant policy mapping, with optional field overrides."""
    policy = {
        "remote_publish": False,
        "secret_access": False,
        "environment": "sandbox",
        "rollback_plan": "delete the fixture directory",
    }
    policy.update(overrides)
    return policy


class EvaluateReleasePolicyTests(unittest.TestCase):
    def test_safe_policy_has_no_violations(self):
        self.assertEqual(evaluate_release_policy(safe_policy()), ())

    def test_remote_publish_enabled_is_rejected(self):
        self.assertEqual(
            evaluate_release_policy(safe_policy(remote_publish=True)),
            (REMOTE_PUBLISH_FORBIDDEN,),
        )

    def test_secret_access_enabled_is_rejected(self):
        self.assertEqual(
            evaluate_release_policy(safe_policy(secret_access=True)),
            (SECRET_ACCESS_FORBIDDEN,),
        )

    def test_non_sandbox_environment_is_rejected(self):
        self.assertEqual(
            evaluate_release_policy(safe_policy(environment="production")),
            (ENVIRONMENT_NOT_SANDBOX,),
        )

    def test_missing_rollback_plan_is_rejected(self):
        policy = safe_policy()
        del policy["rollback_plan"]
        self.assertEqual(evaluate_release_policy(policy), (ROLLBACK_PLAN_MISSING,))

    def test_blank_rollback_plan_is_rejected(self):
        self.assertEqual(
            evaluate_release_policy(safe_policy(rollback_plan="   ")),
            (ROLLBACK_PLAN_MISSING,),
        )

    def test_ambiguous_boolean_value_fails_closed(self):
        self.assertEqual(
            evaluate_release_policy(safe_policy(remote_publish="false")),
            (REMOTE_PUBLISH_FORBIDDEN,),
        )

    def test_all_violations_are_reported_in_fixed_order(self):
        policy = {
            "remote_publish": True,
            "secret_access": True,
            "environment": "production",
        }
        self.assertEqual(
            evaluate_release_policy(policy),
            (
                REMOTE_PUBLISH_FORBIDDEN,
                SECRET_ACCESS_FORBIDDEN,
                ENVIRONMENT_NOT_SANDBOX,
                ROLLBACK_PLAN_MISSING,
            ),
        )

    def test_evaluation_is_deterministic(self):
        policy = safe_policy(remote_publish=True, environment="production")
        self.assertEqual(
            evaluate_release_policy(policy), evaluate_release_policy(policy)
        )

    def test_input_mapping_is_not_mutated(self):
        policy = safe_policy(secret_access=True)
        expected = dict(policy)
        evaluate_release_policy(policy)
        self.assertEqual(policy, expected)


if __name__ == "__main__":
    unittest.main()
