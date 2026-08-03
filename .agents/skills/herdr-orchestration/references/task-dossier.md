# Task dossier

The canonical contract is
[`docs/workflows/task-dossier.md`](../../../../docs/workflows/task-dossier.md).
This reference is the operating summary; the contract wins any conflict.

## Scope

Checkout mode only. The dossier does not change the installed `.brichan` schema,
the packaged resources, or `config/model-routing.json`.

## Location

`projects/<slug>/handoffs/<task-id>/`, beside the canonical receipt. The task ID
is stable and branch-independent; branch rename or a detached worktree does not
change task identity.

## Before starting a tracked task

1. Choose the task level: 0, 1, or 2. All levels produce the same eleven
   standard artifacts.
2. Dry-run the scaffold, then apply it:

   ```bash
   python3 scripts/scaffold_task_dossier.py TASK-000 --level 1 --project slug
   python3 scripts/scaffold_task_dossier.py TASK-000 --level 1 --project slug --apply
   ```

   The scaffold writes nothing without `--apply` and never overwrites an
   existing artifact, including one that appears while it is running.
3. Fill real evidence. A scaffolded dossier fails validation until it holds
   evidence, which is intended.

## While working

- Record phase state per artifact: `pending`, `active`, `passed`,
  `not-required`, or `blocked`.
- Record `not-required` with rationale, evidence, a concrete claim, and a
  concrete uncertainty statement; an unfilled template bullet, `TBD`, or `null`
  is not a statement. Never leave a file empty to imply that a phase did not
  apply. A handoff that carries any dossier artifact without `index.md` is
  reported as partial adoption.
- Record the effective route, model, effort, and session for every
  model-authored or model-reviewed artifact.
- Keep the receipt canonical for delegated lifecycle evidence and project
  memory canonical for durable state. The index links both — the exact task
  receipt and one canonical project-memory file — and copies neither. It may
  declare only its own projection sections.

## Review

Plan review and code review come from independent sessions and name the exact
reviewed plan ID and version. Neither the reviewing session nor the authoring
session of a review may be the plan author's session. Reviewers write only the
two review artifacts.
Level 2 requires a documented stronger one-off review override recorded in the
index.

## Closing

- `python3 scripts/validate_task_dossiers.py projects`
- `python3 scripts/validate_task_dossiers.py projects --require-complete`

`--require-complete` also requires an accepted plan, an applicable
`plan-review.md`, and a `PASS` verdict on every applicable review.

Closing a task never implies remote action. `pr-desc.md` declares
`Remote action authorized: no` and carries no remote-mutation instructions.
Levels 0 and 1 record ship authorization `not-requested`; only level 2 may
record `user-authorized`, and only with recorded evidence.
