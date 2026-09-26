# Current state

Last updated: 2026-09-25 (stage 2 closed 15:05Z)

## Summary

Both stages are complete. Stage 1 preferred `claude-opus-5-5`. In stage 2
(three tasks, all reviewers on Claude), the simplified lifecycle (arm B) met
every protocol pass criterion: blind escape score 42 vs 42, one escaped
Medium per arm, no High. It used 5 vs 24 worker sessions, 56 vs 348 minutes
of active worker time, and 1,343 vs 12,699 artifact lines. No policy,
routing, or packaged-resource change has been made; adoption (WFS-005) waits
for the user's sign-off and an independent review.

## Completed recently

- 2026-09-25: analysis of run metrics and dossier pilots; decision record
  (proposed); A/B protocol; `claude-opus-5-5` answered a `claude -p` probe.
- 2026-09-25: stage 1 benchmark (`evals/workflow-simplification/stage1/`),
  catalog entry for `claude-opus-5-5`.

## In progress

None. Stage 2 evidence: `evals/workflow-simplification/stage2/results/`
(`results.md`, per-worker pane captures, final patches, both arms' dossiers,
blind escape review). All stage 2 worktrees and panes are removed or closed.

## Blockers

None.

## Risks

- Thin evidence base; the pilots with 0 findings were synthetic.
- Arm B changes both the lifecycle and the model; the protocol isolates the
  model effect in stage 1.
- Token and time data are mostly `null` today, so savings may stay
  unmeasurable unless stage runs capture them.

## Next actions

1. User decides on WFS-005: adopt the Level 0/1 simplification in policy
   (`docs/policy/operating-principles.md`, the packaged copy,
   `docs/workflows/task-dossier.md`, the `herdr-orchestration` skill), with the
   one addition stage 2 suggests: a missing regression test for a behavior
   change is a review defect, not a test gap. This is a durable-contract
   change and needs an independent review (preferably Codex once updated).
2. User decides whether to route `implement` to `claude-opus-5-5` in
   `config/model-routing.json`.
3. Follow-ups: `test_repository_paths` and `path-check` fail in any detached
   worktree (`.git` is a file); Codex has a pending update (0.155.0 ->
   0.157.0).

## Unverified assumptions

- `claude-opus-5-5` is stronger than `claude-opus-5` in general (stage 1 is
  three tasks, one sample, same-provider reviewer).
- Level 0/1 review would find nothing on real (not synthetic) tasks.
