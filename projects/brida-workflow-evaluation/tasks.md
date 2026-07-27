# Task register

## Active

None.

## Blocked

| ID | Blocker | Decision needed from | Next check |
|---|---|---|---|

## Completed

| ID | Outcome | Evidence | Completed |
|---|---|---|---|
| EVAL-REV | Blind review PASS: recall 1.00, precision 0.80, all critical defects found | `evals/2026-07-27-workflow-evaluation/scoring/` | 2026-07-27 |
| EVAL-TOK | Context isolation PASS; total-token savings FAIL on the bounded synthesis task | `evals/2026-07-27-workflow-evaluation/RESULTS.md` | 2026-07-27 |
| EVAL-MET | JSONL schema, validator, summary, and 10 tests pass from root and Brida cwd | `metrics/`; `python3 -m unittest brida/metrics/test_validate_metrics.py`; `python3 -m unittest metrics/test_validate_metrics.py` | 2026-07-27 |
| EVAL-REV2 | Retest PASS: recall 1.00, precision 1.00, no unsupported findings | `evals/2026-07-27-workflow-evaluation/scoring/reviewer-score-v2.md` | 2026-07-27 |
| EVAL-LONG | PASS: durable four-track workflow, independent audit, recovery, and complete eval-pane cleanup | `evals/2026-07-27-workflow-evaluation/FINAL-AUDIT.md`; `metrics/runs.jsonl` | 2026-07-27 |

## Worker lifecycle

| Worker | Pane | Model | Purpose | State |
|---|---|---|---|---|
| `brida-eval-reviewer-20260727` | `w1R:p2` | `gpt-5.6-sol`, high | Blind baseline review | closed |
| `brida-eval-review-scorer-20260727` | `w1X:p3` | `gpt-5.6-terra`, medium | Baseline scoring | closed |
| `brida-eval-token-worker-20260727` | `w1X:p4` | `gpt-5.6-luna`, medium | Token instrumentation attempt | auto-closed |
| `brida-eval-final-auditor-20260727` | `w1X:p5` | `gpt-5.6-sol`, high | Independent final audit | closed |
| `brida-eval-reviewer-v2-20260727` | `w1X:p6` | `gpt-5.6-sol`, high | Blind remediation retest | closed |
| `brida-eval-review-scorer-v2-20260727` | `w1X:p7` | `gpt-5.6-terra`, medium | Retest scoring | closed |
