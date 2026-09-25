# Task register

## Active

| ID | Task | Owner | Status |
|---|---|---|---|
| WFS-001 | Decision record and A/B protocol | Brichan | done 2026-09-25 |
| WFS-002 | Stage 1 fixtures + Opus 5 vs 5.5 benchmark | Brichan (Herdr workers) | done 2026-09-25: `opus-5-5` preferred (review 45 vs 41, hidden 36/36 both); `evals/workflow-simplification/stage1/results/results.md` |
| WFS-003 | Catalog entry for `claude-opus-5-5` | Brichan | done 2026-09-25 (routing unchanged) |
| WFS-004 | Stage 2 lifecycle A/B on real tasks | Brichan (Herdr workers) | tasks selected (below); not started |
| WFS-005 | Policy change, if the A/B passes | Brichan + independent review | blocked on WFS-002/004 and user sign-off |

## Workers

| Agent | Pane | Model | Task | Worktree | Launch ID | Status |
|---|---|---|---|---|---|---|
| `brichan-wfs-s1-opus5` | `w4J:p2` | claude `claude-opus-5` medium | WFS-002 arm A | `../brichan-wfs-s1-a` @ `40f46d8` | `b7103851-13f7-47d7-a1e9-8e41b96bcd6c` | done 04:39:55Z (6m30s); pane closed; ledger finished |
| `brichan-wfs-s1-opus55` | `w4J:p3` | claude `claude-opus-5-5` medium | WFS-002 arm B | `../brichan-wfs-s1-b` @ `40f46d8` | `df555457-9a02-4a3c-a49e-5cc705a906e5` | done by 04:39:55Z (2m47s); pane closed; ledger finished |
| `brichan-wfs-s1-review` | `w4J:p6` | claude `claude-fable-5` high (Codex blocked by a pending update dialog) | WFS-002 blind review | `../brichan-wfs-s1-review` @ `40f46d8` | `bd3b12c1-f5c4-496e-9fd1-6f4fbdf7b643` | done 04:47:50Z; pane closed; ledger finished |

## Stage 2 task selection (WFS-004)

Chosen by Brichan on 2026-09-25 under the user's "do all three" instruction,
from recorded non-gating follow-ups. WLG-001-CR-L1 was dropped: already fixed
(`worker_launch.py:472` uses `is not None`).

| ID | Level | Task | Source | Contract path (arm B review trigger) |
|---|---|---|---|---|
| S2-1 | 0 | Rename `test_prose_rejects_control_and_markup_characters` to match what it now tests | TECHSTACK-002 stage-2 `L3` | no |
| S2-2 | 0 | Make the `DESIGN_DIAGNOSTIC_DETAILS` comment describe what the table holds | TECHSTACK-002 final `L1-fr-1` | no |
| S2-3 | 1 | `diagnostic_detail` must not silently ignore `line`/`rule` for codes that do not take them | TECHSTACK-002 stage-2 `L4` | no |
| S2-4 | 1 | Packaged `herdr-orchestration` skill: add `--task` and installed `finish --project` ledger guidance | WLG-001 residual | yes (`src/brichan/resources/`) |
| S2-5 | 0 | Memory-policy note on the worker ledger | worker-ledger next actions | yes (`docs/policy/`) |
