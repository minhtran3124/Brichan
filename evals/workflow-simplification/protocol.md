# Workflow simplification A/B protocol

Decision under test: `projects/brida-workflow-simplification/decisions.md`
(2026-09-25, proposed).

## Objective

Show whether a risk-proportional lifecycle keeps quality at Levels 0 and 1
while using fewer workers, handoffs, and dossier lines. Separately, show
whether `claude-opus-5-5` improves on `claude-opus-5` for Brichan-shaped work.

The two questions run as separate stages so a lifecycle effect is not confused
with a model effect.

## Stage 1: model benchmark (`claude-opus-5` vs `claude-opus-5-5`)

Earlier benchmarks (`evals/mixed-provider-coding/BENCHMARK-001`, `-002`) hit
the ceiling, so stage 1 uses seeded tasks with hidden acceptance tests.

- Fixtures: 3 tasks under `evals/workflow-simplification/stage1/<task>/`:
  one implementation, one debugging with a seeded defect, and one
  contract-sensitive edit with a subtle trap (for example a documented
  invariant that a naive fix breaks).
- Hidden tests are stored outside every worker worktree until scoring, and
  are committed only after both arms finish.
- Arms: identical packet, same dispatch commit, separate detached worktrees,
  route `implement` effort `medium`, model differing only. Each worker plans
  its own work (this is also the arm-B shape for stage 2).
- Metrics per task: hidden tests passed / total, visible tests passed,
  independent review findings (fresh `review` route session, blind to the
  model), user interventions, dispatch/completion UTC, tokens and cost only if
  observed (otherwise `null`).
- Result: `opus-5-5` is preferred only if it is no worse on hidden tests on
  every task and better on at least one of: hidden tests, review findings,
  elapsed time.

## Stage 2: lifecycle A/B on real tasks

- Tasks: 5-8 real Level 0/1 backlog tasks chosen with the user before
  dispatch. Each task is run twice from the same base commit in separate
  worktrees; only one arm's result is integrated (arm A by default).
- Arm A (current): `plan` -> plan-review -> `implement` -> code review, full
  eleven-artifact dossier.
- Arm B (simplified):
  - Level 0: one `implement` worker writes a short plan in its receipt, runs
    `make check`; code review only if the diff touches a contract path
    (`docs/policy/`, `src/brichan/resources/`, `config/`, launcher, or
    `.brichan/` handling). Artifacts: request, receipt, evidence.
  - Level 1: one worker plans and implements; no plan-review; fresh
    independent code review (different provider) kept.
- Both arms use the stage 1 winning model for `implement` so stage 2 measures
  the lifecycle only.
- Escape check: after both arms finish, one extra blind review session
  (different provider from both arms' reviewers) reviews each arm's final diff
  against the task's acceptance criteria. A finding it rates medium or higher
  that the arm itself did not catch counts as an escaped defect.

### Metrics per arm and task

| Metric | Source |
|---|---|
| `make check` pass | command output saved as evidence |
| Acceptance criteria passed / total | coordinator check against evidence |
| Escaped defects (medium+) | blind escape review |
| Worker count, handoff blockers, user interventions | worker ledger, tasks.md |
| Dossier lines | `wc -l` over the task's dossier files |
| Elapsed seconds, tokens, cost | observed only; `null` otherwise |

Record each arm as one line in `metrics/runs.jsonl` with track
`workflow-simplification-a` or `workflow-simplification-b`.

### Pass criteria (all required)

1. Arm B passes `make check` and every acceptance criterion on every task.
2. Arm B has no more escaped medium+ defects than arm A in total, and zero
   escaped high or critical defects.
3. Arm B uses fewer workers and fewer dossier lines per task on average.

### Stop and rollback

- Any escaped high or critical defect in arm B stops stage 2 for that level;
  that level keeps the current lifecycle.
- If the policy is changed and a later real task shows an escaped defect that
  plan-review or code review would have caught, the affected level returns to
  the current lifecycle and the decision record is superseded.

## Authorization and scope

- No policy, routing, or packaged-resource change is made by running this
  protocol. Adopting the result is a separate task needing user sign-off and
  independent review.
- Workers stay inside their worktree and the stated fixture or task scope;
  no remote actions.
