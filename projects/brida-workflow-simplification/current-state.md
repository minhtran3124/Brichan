# Current state

Last updated: 2026-09-25

## Summary

The user accepted the direction; the decision record and A/B protocol are
written. No policy, routing, or code change has been made.

## Completed recently

- 2026-09-25: analysis of run metrics and dossier pilots; decision record
  (proposed); A/B protocol; `claude-opus-5-5` answered a `claude -p` probe.

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

1. Stage 1: build the seeded fixtures (hidden tests kept outside worker
   worktrees), then run the `claude-opus-5` vs `claude-opus-5-5` benchmark.
2. Add `claude-opus-5-5` to `docs/policy/model-catalog.md` with its
   verification date (together with the stage 1 results).
3. Stage 2: choose 5-8 real Level 0/1 backlog tasks with the user and run the
   A/B.

## Unverified assumptions

- `claude-opus-5-5` is stronger than `claude-opus-5` on Brichan-shaped tasks.
- Level 0/1 review would find nothing on real (not synthetic) tasks.
