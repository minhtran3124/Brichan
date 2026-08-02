# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `TDW-008`
- Task level: `2`
- Artifact: `options`
- Artifact version: `1`
- Origin: `packet:projects/brida-task-dossier-workflow/handoffs/TDW-008/task-packet.md@TDW-008-P1-v1`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `8aa41de8-a3f3-48ce-8d47-9aed67a452c6`
- Effective route: `plan`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Claim or decision

Option A — a pure function evaluating four fixed guards in declaration order and
returning a `tuple[str, ...]` of stable violation codes, with fail-closed value
handling — is selected. Fail-closed is the decisive property: a guard that only
rejects the literal `True` would pass the string `"true"`, and in the real system
this simulation stands in for, that gap is the difference between blocking a
publish and permitting one.

## Options considered

- Option A (selected): fixed guard order, `tuple` return, fail-closed value
  handling. A boolean guard is satisfied only by `False` or an absent key; any
  other value, including `"false"`, `0`, and `None`, is a violation. Deterministic
  by construction, no configuration surface.
- Option B: `mapping.get("remote_publish") is True` for the boolean guards and
  truthiness elsewhere. It is the most literal reading of `task-packet.md:17`, but
  it is fail-open: `{"remote_publish": "true"}` returns no violation. Rejected —
  a policy evaluator that fails open is worse than no evaluator, because it
  produces a clean report.
- Option C: a rule registry mapping field names to predicate callables, iterated
  to build the result. More extensible, and attractive if more guards arrive
  later. Rejected for now: iteration order becomes a property of the registry
  rather than of the source text, which weakens `TDW-008-R7` determinism for four
  fixed rules, and the packet at `task-packet.md:24-30` authorizes exactly one
  fixture, not a framework.
- Option D: raise on the first violation instead of returning a collection.
  Rejected: it reports one problem per run, so a caller fixing four violations
  needs four runs, and `task-packet.md:16-17` asks for violations in the plural.

## Decided semantics

- Return type is `tuple[str, ...]`; empty means compliant. A tuple is immutable,
  so a caller cannot mutate a returned report, and its order is the source order
  rather than a set's hash order.
- Violation codes, always emitted in this order:
  `remote-publish-forbidden`, `secret-access-forbidden`,
  `environment-not-sandbox`, `rollback-plan-missing`.
- `environment` must be exactly the string `sandbox`; no case folding, no
  whitespace tolerance, no alias. Anything else, including `"Sandbox"` and
  `None`, is `environment-not-sandbox`.
- `rollback_plan` must be a `str` that is non-empty after `strip()`. A non-string
  value is `rollback-plan-missing` rather than a `TypeError`, so a malformed
  policy still produces a report instead of a crash.
- Unknown keys in the mapping are ignored, not rejected. Rejecting them would
  make the evaluator refuse policies it does not understand; the packet's four
  guards are the whole contract.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-008/task-packet.md:15-20`
  requires deterministic violations from a read-only function covering exactly
  four guards, which is what fixes the code list and its order.
- `src/brichan/contracts/task_dossier/schema.py:89-98` shows the repository's
  existing habit of naming closed value vocabularies as module-level constants
  and validating against them, which is the precedent the fixed violation-code
  list follows.
- `src/brichan/contracts/task_dossier/validation.py:688-711` is a worked example
  of the fail-closed pattern in this repository: an unrecognized ship
  authorization value is diagnosed rather than treated as permissive, exactly as
  Option A treats an unrecognized boolean value.
- `docs/policy/identity.md:33-40` requires explicit authorization before touching
  deployment or credentials, which is the real-world rule Option B's fail-open
  reading would quietly undercut.

## Uncertainty

- Fail-closed handling means a policy written with string booleans, such as
  `{"remote_publish": "false"}`, is reported as violating rather than as
  malformed. That is a deliberate trade of precision for safety; a future version
  could add a distinct `policy-value-invalid` code, and that would be a new
  artifact version rather than a silent edit to this one.
