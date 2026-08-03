# Adaptive task dossier implementation plan

- Plan ID: `TDW-PLAN-001`
- Version: `1`
- Status: direction accepted; implementation pending
- Scope: checkout-mode pilot first
- Installed schema change: excluded

## Objective

Add a full-document task workflow that improves resumption, traceability, and
review quality for every task without duplicating project memory or receipts.
Task level controls evidence depth, reviewer strength, and authorization gates,
not artifact presence.

## Non-goals

- Changing `.brichan` schema v1.
- Automatic branch creation or branch-derived identity.
- Automatic PR creation, publishing, deployment, or remote mutation.
- Replacing Herdr, task packets, receipts, reviewer policy, or project memory.
- Storing raw conversation history.

## Proposed operating model

```text
Intake
  ├─ Level 0 → Full concise docs → Plan review → Execute → Code review → Close
  ├─ Level 1 → Full material docs → Plan review → Execute → Code review → Close
  └─ Level 2 → Full deep docs → Strong plan review → Execute → Strong code review → Authorized Ship
```

Transitions are evidence-gated. All artifacts exist. A phase with no material
work is recorded as `not-required` with rationale and evidence, never inferred
from a missing or empty file.

## Routing compatibility constraint

The workflow state machine is routing-neutral. It does not add phase or level
keys to `config/model-routing.json`.

Default mapping:

- Intake, Close, and authorized Ship: coordinator.
- Repository/evidence discovery: `scan`.
- Exploration, design, and planning: coordinator or `plan`.
- Execution: `implement`.
- Plan/design and implementation review: fresh `review` sessions.

The effective runtime, model, and effort must be recorded for every
model-authored or model-reviewed artifact. Level 0 may use the routine review
route; Level 2 must use a documented stronger one-off override when the active
route is intended for routine work. Route schema changes are deferred until
pilot evidence demonstrates a repeated need.

## Phase 1 — Contract and templates

Deliverables:

- Document the Level 0/1/2 classifier and escalation triggers.
- Define stable task-ID syntax independent of branch/worktree.
- Define phase states: `pending`, `active`, `passed`, `not-required`, `blocked`.
- Define artifact ownership and source-of-truth rules.
- Add the complete standard template set for `index.md`, redacted `request.md`,
  `requirements.md`, `brief.md`, `options.md`, `design.md`,
  `client-follow-up-questions.md`, versioned `plan.md`, `plan-review.md`,
  `code-review.md`, and `pr-desc.md`.
- Require status, ownership, evidence, uncertainty, applicability, and version
  metadata in every artifact.
- Define request amendment and redaction rules.
- Define that receipt status remains canonical for delegated lifecycle evidence.
- Define phase-to-route mapping without adding routing manifest keys.
- Define how effective route overrides are recorded and reviewed.

Acceptance criteria:

- Every field has one authoritative owner.
- Every task level creates a complete dossier.
- A task can resume by reading project memory, its index, accepted plan, and
  receipt without loading raw chat.
- Branch rename or detached worktree does not change task identity.
- No policy implies remote action from `Close/Ship`.
- Both checkout and installed manifests continue to resolve unchanged.
- Empty placeholders fail validation; `not-required` requires rationale and
  evidence.

Verification:

- Documentation contract tests.
- Repository path/link validation.
- Independent operating-contract review.

## Phase 2 — Checkout-mode manual pilot

Deliverables:

- Run three real tasks: one Level 0, one Level 1, and one Level 2 or simulated
  high-risk/multi-writer task.
- Reuse `projects/<slug>/handoffs/<task-id>/` for every tracked task.
- Record observed creation time, files read on resume, drift defects, merge
  conflicts, missing context, and skipped phases.
- Test one interrupted/resumed task and one plan amendment.

Acceptance criteria:

- Level 0 produces the full concise dossier and passes plan/design review.
- A fresh coordinator can recover Level 1 context from durable artifacts.
- The Level 2 review references the exact accepted plan version.
- No artifact disagrees with project memory or receipt status.
- All measurements are observed; unavailable metrics are `null`.

Go/no-go gate:

- Continue only if context recovery improves without recurring duplicate-truth
  defects or disproportionate documentation overhead.

## Phase 3 — Validator and helper commands

Deliverables:

- Add a dependency-free validator for task indexes and authority links.
- Validate task ID, class, phase state, accepted plan version, canonical receipt
  link, and required evidence by level.
- Add dry-run-first scaffolding for the complete Level 0/1/2 dossier.
- Add a resume summary that reads progressively and reports missing/stale links.
- Generate PR text from verified evidence only when explicitly requested.

Acceptance criteria:

- Helper commands make zero writes without an explicit apply flag.
- Existing user files are preserved.
- All standard artifacts exist; evidence depth varies by task level.
- Invalid or ambiguous state is diagnosed, never silently repaired.
- Regression, contract, integration, path, and documentation tests pass.

Verification:

- Unit tests for classifier and state transitions.
- Contract tests for templates and canonical links.
- Integration tests in a disposable checkout.
- Adversarial tests for symlinks, duplicate task IDs, missing receipts, stale
  plan versions, branch rename, and sensitive-path leakage.
- `make check`.
- Independent review.

## Phase 4 — Installed-mode decision

This is a decision phase, not an automatic continuation.

Required evidence:

- Checkout pilot results.
- Frequency of resumed material tasks.
- Measured ceremony and context-recovery benefit.
- State-size and retention behavior.
- Compatibility and reinitialization impact.

If accepted:

- Design a versioned managed task-artifact contract.
- Update packaged resources and lifecycle inventory.
- Define explicit incompatibility and backup/reinitialization behavior.
- Add disposable-wheel and real owner-repository dogfood.

If rejected:

- Keep the feature checkout-only and preserve installed schema v1.

## Proposed artifact ownership

| Artifact | Writer | Mutability |
|---|---|---|
| `index.md` | Coordinator | Mutable projection; no copied truth |
| `request.md` | Coordinator | Immutable redacted origin |
| `options.md` | Planner/coordinator | Draft; selected decision promoted elsewhere |
| `design.md` | Planner | Versioned or superseded, never silently rewritten |
| `plan.md` | Planner/coordinator acceptance | Versioned; accepted version immutable |
| review reports | Independent reviewer | Immutable findings for reviewed version |
| `receipt.md` | Coordinator | Mutates only according to receipt lifecycle contract |
| `pr-desc.md` | Coordinator generator | Regenerable output |

## Full-doc evidence contract

Document presence is not correctness evidence. Each artifact must include:

- claim or decision;
- repository/source evidence;
- unresolved uncertainty;
- applicability status;
- authoring session and effective route/model/effort when model-authored;
- reviewing session and verdict where review applies;
- version or immutable origin marker.

`plan-review.md` evaluates requirements, options, design, and plan for every
task. `code-review.md` evaluates implementation or records, with evidence, why
no implementation review is applicable. A self-reported confidence score is
not accepted as proof.

## Materiality triggers

Increase to Level 1 evidence depth when any is true:

- explicit planning or delegation is requested;
- work spans sessions or is expected to resume;
- multiple credible implementation options exist;
- architecture or compatibility is affected;
- acceptance criteria require decomposition.

Increase to Level 2 evidence depth and reviewer strength when any is true:

- reviewer policy makes review mandatory;
- security, privacy, destructive, production, or public-contract risk exists;
- multiple writers are used;
- a worker replacement/recovery lifecycle is needed;
- the user accepts a meaningful reliability, compatibility, cost, or permission
  trade-off.

## Rollout decision requested

The recommended user decision is:

> Accept `TDW-PLAN-001` as a checkout-only full-docs manual pilot, with one
> standard dossier for every task, adaptive evidence depth, and no installed
> schema change.

The user accepted this direction on 2026-08-02. Implementation remains a
separate bounded task because it changes the repository's operating contract
and task-artifact conventions.
