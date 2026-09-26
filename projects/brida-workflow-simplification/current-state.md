# Current state

Last updated: 2026-09-26

## Summary

WFS-005 is implemented and independently reviewed on branch
`feat/lifecycle-simplification`, stacked on PR #36. In checkout mode, Level 0
and Level 1 tasks now run the lighter lifecycle with a reduced artifact set
(`report.md` carries the plan), and Level 0 is reviewed only on a contract
path (`scripts/check_contract_paths.py`). The reviewer policy now treats a
behavior change without a committed regression test as a defect. Level 2 and
installed mode are unchanged. Code review v2 is PASS, with nine non-blocking
Lows recorded in `handoffs/WFS-005/code-review.md` (local).

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

1. User merges PR #36, then the WFS-005 PR.
2. Optional follow-up: close the nine non-blocking code-review Lows (test
   gaps L1-L4, the L5 empty-input contract-path rule, L6 legacy-rule
   restriction, L9 fail-open `.get` default).
3. User decides whether to route `implement` to `claude-opus-5-5`.
4. Follow-ups: worktree-only `.git` failures in `test_repository_paths` and
   `path-check`; Codex update pending (0.155.0 -> 0.157.1).
5. Revisit installed-mode adoption after external dogfood.

## Unverified assumptions

- `claude-opus-5-5` is stronger than `claude-opus-5` in general (stage 1 is
  three tasks, one sample, same-provider reviewer).
- Level 0/1 review would find nothing on real (not synthetic) tasks.
