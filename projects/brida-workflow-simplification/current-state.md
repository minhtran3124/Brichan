# Current state

Last updated: 2026-10-08

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
- 2026-10-08: WFS-009 (level 1) routes checkout `scan` to
  `claude-sonnet-5-5` and the packaged installed-mode Claude coordinator to
  `claude-opus-5-5` (effort unchanged); catalog re-probed (aliases now
  `sonnet`/`opus`/`fable` -> `claude-sonnet-5-5`/`claude-opus-5-5`/
  `claude-fable-5-1`). First `claude-sonnet-5-5` Herdr worker matched the
  coordinator's inventory 29/29. Review PASS (2 Lows fixed). In PR #41;
  release not authorized.
- 2026-10-08: WFS-010 side-by-side `claude-sonnet-5` vs `claude-sonnet-5-5`
  (stage 1 coding tasks at `40f46d8` plus a seeded scan audit): `sonnet-5-5`
  preferred. Blind review 42 vs 36; `sonnet-5` shipped 2 functional defects
  the hidden tests miss; hidden 36/36 and scan 6/6 with 0 decoys for both;
  `sonnet-5-5` about 3.5x faster. `evals/workflow-simplification/sonnet55/`.

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
- Codex is not installed on this machine (2026-10-08), so `review` route
  work falls back to a same-provider stronger Claude model.
- Techstack receipt contract wants an absolute `--project-root` in the
  verify row, but receipt path hygiene forbids home paths; WFS-009 recorded
  `--project-root .`. Needs a policy decision.

## Next actions

1. User merges PR #36, then PR #37 (WFS-005, WFS-006, WFS-007).
2. Done 2026-09-26: WFS-006 (level 1) closed WFS-005 Lows L1-L5, L8, L9
   (L6 kept as design, L7 fixed in place); WFS-007 (level 0) routes the
   checkout `implement` worker to `claude-opus-5-5`. Both reviewed PASS and are
   on the same branch as WFS-005 (PR #37).
4. Done 2026-09-26: WFS-008 fixed the worktree-only `.git` failures (branch
   `fix/worktree-git-file`, stacked on PR #37). Codex update pending and
   Codex usage-limited; reviews run on Claude meanwhile.
6. Dogfood count toward the adoption check: WFS-006 (L1), WFS-007 (L0),
   WFS-008 (L0), WFS-009 (L1) -- no escaped defect so far.
7. User reviews and merges PR #41 (WFS-009 and WFS-010, branch
   `feat/sonnet-opus-5-5-routing`).
5. Revisit installed-mode adoption after external dogfood.

## Unverified assumptions

- `claude-sonnet-5-5` is better than `claude-sonnet-5` in general (WFS-010
  is four tasks, one sample, same-provider reviewer; the scan fixture hit
  the ceiling).
- `claude-opus-5-5` is stronger than `claude-opus-5` in general (stage 1 is
  three tasks, one sample, same-provider reviewer).
- Level 0/1 review would find nothing on real (not synthetic) tasks.
