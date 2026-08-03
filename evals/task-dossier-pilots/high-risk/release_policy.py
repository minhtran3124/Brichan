"""Pilot fixture for TDW-008: a pure, fail-closed release-policy evaluator.

This module is an isolated evaluation fixture with no enforcement authority. It
inspects a mapping of policy fields and reports violation codes. It never
performs, simulates, or documents a real release: "release" names a data field
here, never an operation this module can carry out.

The module uses the standard library only. It performs no I/O, opens no network
connection, spawns no process, reads no environment variable or secret, and does
not mutate its input.
"""

# Violation codes, always emitted in this order.
REMOTE_PUBLISH_FORBIDDEN = "remote-publish-forbidden"
SECRET_ACCESS_FORBIDDEN = "secret-access-forbidden"
ENVIRONMENT_NOT_SANDBOX = "environment-not-sandbox"
ROLLBACK_PLAN_MISSING = "rollback-plan-missing"

SANDBOX_ENVIRONMENT = "sandbox"

# Distinguishes an absent key from a key present with the value ``None``.
_ABSENT = object()


def _is_disabled(value) -> bool:
    """Return ``True`` only when a boolean policy flag is explicitly safe.

    Safe means the key is absent or its value is the literal ``False``. Every
    other value — including ``"false"``, ``0``, and ``None`` — is treated as
    enabled, so an ambiguous or malformed policy fails closed. Identity, not
    equality, is used so that ``0`` is not mistaken for ``False``.
    """
    return value is _ABSENT or value is False


def evaluate_release_policy(mapping) -> tuple[str, ...]:
    """Return the violation codes for ``mapping`` in fixed order.

    An empty tuple means the policy is compliant. The same input always yields
    the same output: the codes are appended in source order, with no set
    iteration, sorting, clock, randomness, or ambient state involved. The input
    mapping is only read, never modified.
    """
    violations = []

    if not _is_disabled(mapping.get("remote_publish", _ABSENT)):
        violations.append(REMOTE_PUBLISH_FORBIDDEN)

    if not _is_disabled(mapping.get("secret_access", _ABSENT)):
        violations.append(SECRET_ACCESS_FORBIDDEN)

    if mapping.get("environment", _ABSENT) != SANDBOX_ENVIRONMENT:
        violations.append(ENVIRONMENT_NOT_SANDBOX)

    rollback_plan = mapping.get("rollback_plan", _ABSENT)
    if not isinstance(rollback_plan, str) or not rollback_plan.strip():
        violations.append(ROLLBACK_PLAN_MISSING)

    return tuple(violations)
