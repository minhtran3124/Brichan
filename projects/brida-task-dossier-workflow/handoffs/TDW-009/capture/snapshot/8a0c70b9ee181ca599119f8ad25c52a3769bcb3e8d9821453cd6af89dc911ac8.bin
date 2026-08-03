# Task dossier workflow

This is the canonical checkout-mode task-dossier contract. It applies to work
tracked in this repository checkout. It does not change the installed `.brichan`
schema, the packaged resources, or the model routing manifest.

Every tracked task owns one dossier directory holding the same eleven standard
artifacts plus its canonical handoff receipt. The task level changes required
evidence depth, reviewer strength, and authorization gates. It never changes
which artifacts exist. Document presence is not correctness evidence.

## Location and identity

A dossier lives at `projects/<project-slug>/handoffs/<task-id>/`, beside the
canonical receipt described in
[`handoff-receipt.md`](../../.agents/skills/herdr-orchestration/references/handoff-receipt.md).

The task ID is stable and branch-independent: uppercase prefix, then a numeric
suffix of at least three digits, such as `TDW-005`. Renaming a branch, moving to
a detached worktree, or reusing a checkout does not change task identity. The
directory name is authoritative; every artifact repeats it and must agree.

## Standard artifacts

| Artifact | Writer | Mutability |
|---|---|---|
| `index.md` | Coordinator | Mutable projection; links authorities, copies none |
| `request.md` | Coordinator | Immutable redacted origin |
| `requirements.md` | Planner | Versioned |
| `brief.md` | Planner | Versioned |
| `options.md` | Planner | Draft; the selected decision is promoted onward |
| `design.md` | Planner | Versioned or superseded, never silently rewritten |
| `client-follow-up-questions.md` | Coordinator | Versioned |
| `plan.md` | Planner, coordinator acceptance | Versioned; accepted version immutable |
| `plan-review.md` | Independent reviewer | Immutable findings for the reviewed version |
| `code-review.md` | Independent reviewer | Immutable findings for the reviewed version |
| `pr-desc.md` | Coordinator generator | Regenerable output |
| `receipt.md` | Coordinator | Canonical; mutates only per the receipt lifecycle |

Templates for all eleven artifacts are in
[`task-dossier/templates/`](task-dossier/templates/index.md).

## Authority

The handoff receipt remains canonical for delegated lifecycle evidence, and
project memory remains canonical for durable project state. The dossier index
links to both: `Canonical receipt path` must be exactly this task's
`projects/<project-slug>/handoffs/<task-id>/receipt.md`, and
`Project memory path` must name one canonical memory file directly inside
`projects/<project-slug>/`.

The index links and never restates. It may declare only its projection
sections — `Artifact metadata`, `Task identity`, `Artifact status`,
`Claim or decision`, `Evidence`, and `Uncertainty`. Any other section is
rejected, including a receipt-owned one such as `Review verdict` and a
project-memory-owned one such as `Current state`, `Overview`, `Tasks`,
`Decisions`, or `References`. The index must not repeat a receipt-owned field
such as `Verdict`, `Diff evidence`, or `Brida-owned panes closed`, and must
carry no table other than the artifact status table.

## Phase states

Each artifact declares one phase state:

- `pending`: not started.
- `active`: in progress.
- `passed`: complete with evidence at the level's required depth.
- `not-required`: no material work applies, with rationale and evidence.
- `blocked`: stopped with recorded unresolved uncertainty.

A phase with no material work is recorded as `not-required` with rationale and
evidence. It is never inferred from a missing or empty file. Empty placeholders
fail validation. `not-required` is a recorded decision, not an exemption from
the evidence contract: it still requires a concrete claim or decision, concrete
evidence, and a concrete uncertainty statement.

Uncertainty is checked for content, not for length. An unfilled template
bullet, `TBD`, `pending`, or a bare `null` is not a statement; "No unresolved
uncertainty remains." is. This holds for `passed`, `blocked`, and
`not-required` alike.

A handoff directory that predates this contract stays exempt: a plain
`plan.md` or `design.md` with no `## Artifact metadata` block is a pre-contract
note, not an artifact of this contract. Once a handoff carries a file that does
declare that block, the task has adopted the contract, and a missing `index.md`
is reported as partial adoption rather than silently exempting the task.

## Evidence contract

Every artifact records:

- the claim or decision it asserts;
- repository or source evidence;
- unresolved uncertainty, or a recorded statement that none remains;
- applicability status and, when `not-required`, its rationale;
- authorship, and for model authorship the session identity plus the effective
  route, model, and effort;
- reviewing session and verdict where review applies;
- artifact version and an immutable origin marker.

A self-reported confidence score is not proof.

`plan-review.md` evaluates requirements, options, design, and plan for every
task and names the exact reviewed plan version. `code-review.md` evaluates the
implementation or records, with evidence, why no implementation review applies.
Reviewers do not back-write planning artifacts: `requirements.md`, `design.md`,
and `plan.md` are never reviewer-owned. Neither the reviewing session nor the
authoring session of a review artifact may be the session that authored the
plan.

## Levels

All three levels produce the complete dossier. They differ in depth:

| Level | Minimum evidence items per passed artifact | Reviewer strength | Ship |
|---|---|---|---|
| 0 | 1 | Routine review route | Not requested |
| 1 | 2 | Routine review route | Not requested |
| 2 | 3 | Documented stronger one-off override | Requires recorded user authorization |

Raise to level 1 when explicit planning or delegation is requested, work spans
sessions or is expected to resume, multiple credible options exist, architecture
or compatibility is affected, or acceptance criteria require decomposition.

Raise to level 2 when reviewer policy makes review mandatory, security, privacy,
destructive, production, or public-contract risk exists, multiple writers are
used, a worker replacement or recovery lifecycle is needed, or the user accepts a
meaningful reliability, compatibility, cost, or permission trade-off.

## Routing neutrality

The workflow is routing-neutral. It adds no phase or level keys to
`config/model-routing.json` and does not change the four named routes. Default
phase mapping:

- Intake, close, and authorized ship: coordinator.
- Repository and evidence discovery: `scan`.
- Exploration, design, and planning: coordinator or `plan`.
- Execution: `implement`.
- Plan and implementation review: fresh `review` sessions.

Each model-authored or model-reviewed artifact records the route, model, and
effort that were actually effective. Level 2 records a stronger one-off review
override in `index.md`; levels 0 and 1 leave that override null.

## Authorization

`index.md` records ship authorization as `not-requested` or `user-authorized`.
Levels 0 and 1 do not gate a ship and must record `not-requested`. Only level 2
may record `user-authorized`, and it then requires recorded evidence of the
user's decision. Closing a task never implies remote action.

`pr-desc.md` describes a change built from verified evidence; it declares
`Remote action authorized: no` and must not contain remote-mutation
instructions.

## Request provenance

`request.md` is redacted before storage, read-only, and marked immutable. Later
changes to the request are recorded as a new artifact version with its own
origin marker; earlier recorded provenance is not rewritten. Raw conversation
history is not stored, and personal or home paths are forbidden anywhere in the
dossier.

## Tooling

```bash
python3 scripts/scaffold_task_dossier.py TDW-005 --level 1 --project example
python3 scripts/scaffold_task_dossier.py TDW-005 --level 1 --project example --apply
python3 scripts/validate_task_dossiers.py projects
python3 scripts/validate_task_dossiers.py projects --require-complete
make dossiers
```

Scaffolding writes nothing without `--apply` and never overwrites an existing
artifact. It rejects a project slug that is not a lowercase hyphenated name, a
dossier path that would leave the projects root, and any existing artifact
symlink — including a dangling one — before it writes anything.

Planning and writing are separate steps, so each artifact is created
exclusively and without following links. An artifact that appears in that
window is preserved and reported as `preserve`; if the entry that appeared is a
symlink the scaffold aborts. Either way nothing is overwritten and no write
follows a link.

The validator is read-only: it diagnoses invalid or ambiguous state and never
repairs it.

`--require-complete` additionally requires every artifact to be `passed` or
`not-required`, the plan to be `accepted`, `plan-review.md` to be applicable to
every task, and every applicable review to carry a `PASS` verdict. A review
recorded as `passed` while its verdict is `CHANGES REQUIRED` is not a complete
task.
