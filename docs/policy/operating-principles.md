# Operating principles

This is the canonical Brichan operating policy.

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

Every tracked task also owns one task dossier. Follow
`docs/workflows/task-dossier.md`. All task levels produce the same standard
artifact set; the level changes evidence depth, reviewer strength, and
authorization gates, never artifact presence.

## 3. Route deliberately

Resolve the named worker route in repository settings first. Consult
`docs/policy/model-catalog.md` only when evaluating or changing that routing
choice. Select the least expensive and fastest verified model that can meet
the quality bar. Increase reasoning effort before switching models only when
the problem—not the prompt—is the limiting factor.

Do not use an unavailable or unverified provider.

## 4. Coordinate through Herdr

Use `$herdr-orchestration`. Record each Brichan-created agent's name, pane ID,
model, task, and status in the relevant project `tasks.md`.

Do not reuse an unrelated existing Herdr session. Do not close panes owned by
the user or another workflow.

## 5. Verify, then integrate

Require evidence appropriate to the task:

- Research: direct sources and unresolved uncertainty.
- Code: diff, tests of application-owned observable behavior, static checks
  when the project configures them, and known limitations.
- Debugging: reproduction, root cause, fix evidence, and regression test.
- Review: findings ordered by severity with file/line evidence.

Use `docs/policy/reviewer.md` for material changes. Prefer a different model
family or at least an independent fresh session for review.

Record that evidence in the task dossier as well as the receipt. Document
presence is not evidence, and an artifact with no material work is recorded as
`not-required` with rationale and evidence.

### Testing discipline

- Test application-owned observable behavior, not third-party internals or
  framework guarantees the project does not own.
- Every new test needs a distinct justification: the owned behavior or
  observed failure it covers. Do not add duplicate, speculative, or
  implementation-coupled cases; coverage that restates the implementation is
  cost, not evidence.
- Run the smallest relevant checks first and broaden intentionally,
  sequentially by default. E2E, race, load, and stress tests are used
  intentionally, for a specific identified risk, never by default.
- Run lint and type checks when the project configures them; never add
  tooling merely to satisfy verification.
- Diagnose a failure — new defect, wrong assumption, or pre-existing issue —
  before code or tests change. Never weaken, skip, or delete a meaningful
  assertion merely to make a gate pass.
- Focused runs are fast implementation feedback; they never replace the
  project-defined completion, CI, or release gate. In this repository that
  gate is `make check`.

## 6. Update durable memory

Follow `docs/policy/memory-policy.md`. Record verified facts and decisions, not
raw chat logs. Keep the current state concise enough to read at the beginning
of the next project turn.

## 7. Report

Final reports use this order:

1. Outcome.
2. What changed or was learned.
3. Verification and evidence.
4. Decisions Brichan made.
5. Risks and open questions.
6. User decisions required.
7. Recommended next step.

When `metrics/` is present, record only observed workflow measurements in its
ledger. Use `null` for unavailable timing, token, or cost data; never estimate
provider cost without a verified source.
