# Task register

## Active

| ID | Task | Owner | Status |
|---|---|---|---|
| WFS-001 | Decision record and A/B protocol | Brichan | done 2026-09-25 |
| WFS-002 | Stage 1 fixtures + Opus 5 vs 5.5 benchmark | Brichan (Herdr workers) | done 2026-09-25: `opus-5-5` preferred (review 45 vs 41, hidden 36/36 both); `evals/workflow-simplification/stage1/results/results.md` |
| WFS-003 | Catalog entry for `claude-opus-5-5` | Brichan | done 2026-09-25 (routing unchanged) |
| WFS-004 | Stage 2 lifecycle A/B on real tasks | Brichan (Herdr workers) | done 2026-09-25: arm B met all pass criteria; `evals/workflow-simplification/stage2/results/results.md` |
| WFS-005 | Policy change, if the A/B passes | Brichan + independent review | done 2026-09-26: checkout-only, code review v2 PASS; PR #37 |
| WFS-006 | Close WFS-005 code-review Lows (level 1) | `brichan-wfs006-impl` (`w4J:p1D`, launch `590f4a46…`), reviewer `brichan-wfs006-cr` (`w4J:p1E`, launch `43a6d5ef…`) | done 2026-09-26: review PASS (4 Low); panes closed |
| WFS-008 | Worktree `.git` file breaks path-check (level 0, contract path) | `brichan-wfs008-impl` (`w4J:p1G`, launch `59dd8b1d…`), reviewer `brichan-wfs008-cr` (`w4J:p1H`, launch `28b35b16…`) | done 2026-09-26: review PASS (4 Low); panes closed; branch `fix/worktree-git-file` |
| WFS-007 | Route checkout `implement` to `claude-opus-5-5` (level 0, contract path) | coordinator; reviewer `brichan-wfs007-cr` (`w4J:p1F`, launch `72117df1…`) | done 2026-09-26: review PASS (2 Low); pane closed |

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

## Stage 2 workers (dispatched 2026-09-25T04:58:49Z, base `6fe3977`)

Stage 2 scope reduced by the user on 2026-09-25 to S2-1, S2-3, S2-4, all
reviewers on Claude (Codex blocked by a pending update).

| Agent | Pane | Model | Task | Worktree | Launch ID | Status |
|---|---|---|---|---|---|---|
| `brichan-wfs-a201-plan` | `w4J:p7` | claude `claude-fable-5` high (route plan) | WFS-A-201 plan | `../brichan-wfs-201a` | `4a0d8137-e98d-4c76-b34f-bb515a3a2443` | done; pane closed |
| `brichan-wfs-b201` | `w4J:p8` | claude `claude-opus-5-5` medium | WFS-B-201 | `../brichan-wfs-201b` | `37e31916-1a97-4a19-a3f8-4a1f3d5a0ce0` | done; pane closed |
| `brichan-wfs-a203-plan` | `w4J:p9` | claude `claude-fable-5` high (route plan) | WFS-A-203 plan | `../brichan-wfs-203a` | `835c6eea-58b4-4b4d-b9bb-715e847be131` | done; pane closed |
| `brichan-wfs-b203` | `w4J:pA` | claude `claude-opus-5-5` medium | WFS-B-203 | `../brichan-wfs-203b` | `c474d994-3f8d-4a7d-b065-8843a2b70bfe` | done; pane closed |
| `brichan-wfs-a204-plan` | `w4J:pB` | claude `claude-fable-5` high (route plan) | WFS-A-204 plan | `../brichan-wfs-204a` | `c096537e-e4d6-4cf8-b818-996832962684` | done; pane closed |
| `brichan-wfs-b204` | `w4J:pC` | claude `claude-opus-5-5` medium | WFS-B-204 | `../brichan-wfs-204b` | `4e2e3d63-6251-4142-ba1e-1bc5472f2d66` | done; pane closed |
| `brichan-wfs-b203-review` | `w4J:pD` | claude `claude-opus-5` high (route review, Codex blocked) | WFS-B-203 review | `../brichan-wfs-203b` | `0e5173bc-8d2e-4a4d-9ffe-15ed78189e42` | PASS; pane closed |
| `brichan-wfs-b204-review` | `w4J:pE` | claude `claude-opus-5` high (route review, Codex blocked) | WFS-B-204 review | `../brichan-wfs-204b` | `46fdf628-1ab1-43fe-be8d-56d58e24d765` | PASS; pane closed |
| `brichan-wfs-a{201,203,204}-pr` | `w4J:pF`,`pG`,`pH` | claude `claude-opus-5` high | WFS-A plan reviews v1 (09:03:55Z) | arm A worktrees | `278ced4e…`, `aa64cece…`, `e34aecf4…` | all CHANGES REQUIRED (201: 1H 1M 2L; 203: 1H 4M 3L; 204: 1M 2L); panes closed |
| `brichan-wfs-a{201,203,204}-planrev` | `w4J:pJ`,`pK`,`pM` | claude `claude-fable-5` high | WFS-A plan revisions (09:26:00Z) | arm A worktrees | `4e5b37fb…`, `616edd89…`, `a86251cd…` | done; panes closed |

Later arm A sessions (plan revisions v3/v4, plan reviews 2-4, implementers, code reviews) and the blind escape review (`brichan-wfs-escape`, `claude-fable-5` high) are recorded with launch IDs and finish attestations in `ledger/workers.jsonl`; every pane was closed after its evidence was saved to `evals/workflow-simplification/stage2/results/`.

## WFS-005 workers (Level 2, branch `feat/lifecycle-simplification`)

| Agent | Pane | Model | Task | Launch ID | Status |
|---|---|---|---|---|---|
| `brichan-wfs005-plan` | `w4J:p15` | claude `claude-fable-5` high (route plan) | WFS-005 plan v1, v2 (Snapshot reread) | `0ee67e67-eda3-44ba-a27d-98936b333b66` | done; pane closed |
| `brichan-wfs005-pr` | `w4J:p16` | claude `claude-opus-5` high | plan review v1 | `35f4e718-6648-497d-bcea-8903226d4922` | CHANGES REQUIRED; pane closed |
| `brichan-wfs005-plan3` | `w4J:p17` | claude `claude-fable-5` high | plan v3 | `8d0b46d4-2a82-420e-84dd-fa0f45dcdbda` | done; pane closed |
| `brichan-wfs005-pr2` | `w4J:p18` | claude `claude-opus-5` high | plan review v2 | `13473fe2-ef27-40ca-8fd3-bf1abe8bdb22` | PASS; pane closed |
| `brichan-wfs005-impl` | `w4J:p19` | claude `claude-opus-5-5` medium | implementation | `54da7a4c-2eb7-45a2-8787-17f5381b5b2d` | done; pane closed |
| `brichan-wfs005-cr` | `w4J:p1A` | claude `claude-opus-5` high | code review v1 | `10a0b370-f8f1-49e7-ab13-4e69df4ef247` | CHANGES REQUIRED (M1); pane closed |
| `brichan-wfs005-fix1` | `w4J:p1B` | claude `claude-opus-5-5` medium | Fix 1 (M1 test) | `98972747-a0b9-4c99-a1f6-75f95b6bcb89` | done; pane closed |
| `brichan-wfs005-cr2` | `w4J:p1C` | claude `claude-opus-5` high | code review v2 | `e60f482b-7a99-4552-bc7f-11d2aa13c486` | PASS; pane closed |
