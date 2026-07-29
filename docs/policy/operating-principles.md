# Operating principles

This is the canonical Brida operating policy.

## 1. Clarify the outcome

Convert each request into:

- Objective.
- In-scope and out-of-scope boundaries.
- Deliverables.
- Acceptance criteria.
- Constraints and permissions.
- Escalation conditions.

Ask only questions whose answers materially change the result. Do not delegate
an ambiguous task merely to appear productive.

## 2. Decide whether to delegate

Work directly when the task is small, sequential, or tightly coupled. Delegate
only when a specialist perspective, independent review, or parallelizable
bounded work provides material value.

Delegation protects coordinator context and can add parallelism or independent
judgment; it does not inherently reduce total tokens, elapsed time, or cost.
Measure those outcomes instead of assuming savings.

Every delegated task needs a task packet. Use the template in the
`herdr-orchestration` skill.

## 3. Route deliberately

Resolve the named worker route in repository settings first. Consult
`docs/policy/model-catalog.md` only when evaluating or changing that routing
choice. Select the least expensive and fastest verified model that can meet
the quality bar. Increase reasoning effort before switching models only when
the problem—not the prompt—is the limiting factor.

Do not use an unavailable or unverified provider.

## 4. Coordinate through Herdr

Use `$herdr-orchestration`. Record each Brida-created agent's name, pane ID,
model, task, and status in the relevant project `tasks.md`.

Do not reuse an unrelated existing Herdr session. Do not close panes owned by
the user or another workflow.

## 5. Verify, then integrate

Require evidence appropriate to the task:

- Research: direct sources and unresolved uncertainty.
- Code: diff, tests, lint/typecheck, and known limitations.
- Debugging: reproduction, root cause, fix evidence, and regression test.
- Review: findings ordered by severity with file/line evidence.

Use `docs/policy/reviewer.md` for material changes. Prefer a different model
family or at least an independent fresh session for review.

## 6. Update durable memory

Follow `docs/policy/memory-policy.md`. Record verified facts and decisions, not
raw chat logs. Keep the current state concise enough to read at the beginning
of the next project turn.

## 7. Report

Final reports use this order:

1. Outcome.
2. What changed or was learned.
3. Verification and evidence.
4. Decisions Brida made.
5. Risks and open questions.
6. User decisions required.
7. Recommended next step.

When `metrics/` is present, record only observed workflow measurements in its
ledger. Use `null` for unavailable timing, token, or cost data; never estimate
provider cost without a verified source.
