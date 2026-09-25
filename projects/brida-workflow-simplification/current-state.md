# Current state

Last updated: 2026-09-25

## Summary

Stage 1 is complete: `claude-opus-5-5` beat `claude-opus-5` on the blind
review (45 vs 41, no functional defects vs one High) at equal hidden-test
results and in less wall time. It has a catalog entry; routing is unchanged.
Stage 2 tasks are selected and not yet started.

## Completed recently

- 2026-09-25: analysis of run metrics and dossier pilots; decision record
  (proposed); A/B protocol; `claude-opus-5-5` answered a `claude -p` probe.
- 2026-09-25: stage 1 benchmark (`evals/workflow-simplification/stage1/`),
  catalog entry for `claude-opus-5-5`.

## In progress

None.

## Blockers

None.

## Risks

- Thin evidence base; the pilots with 0 findings were synthetic.
- Arm B changes both the lifecycle and the model; the protocol isolates the
  model effect in stage 1.
- Token and time data are mostly `null` today, so savings may stay
  unmeasurable unless stage runs capture them.

## Next actions

1. Stage 2: run the A/B on S2-1..S2-5 (`tasks.md`), with `claude-opus-5-5`
   as the `implement` model in both arms (one-off override).
2. Follow-up: `tests/contract/test_repository_paths.py` fails inside a git
   worktree because `.git` is a file there (seen by a stage 1 worker).
3. Codex has a pending update dialog (0.155.0 -> 0.157.0) that blocks worker
   startup; the user decides whether to update.

## Unverified assumptions

- `claude-opus-5-5` is stronger than `claude-opus-5` in general (stage 1 is
  three tasks, one sample, same-provider reviewer).
- Level 0/1 review would find nothing on real (not synthetic) tasks.
