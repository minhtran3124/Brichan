# Brida workflow evaluation results

Status: complete
Date: 2026-07-27

## EVAL-REV — Reviewer workflow

Verdict: **PASS**

| Metric | Result |
|---|---:|
| Seeded defects | 4 |
| Matched | 4 |
| Missed | 0 |
| Unsupported substantive findings | 1 |
| Recall | 1.00 |
| Precision | 0.80 |
| Critical seeded defects found | 3/3 |

The blind reviewer found all seeded defects. It also promoted failure atomicity
from a residual risk to a substantive finding even though atomicity was not in
the stated intent, lowering precision to 0.80. This is useful counter-evidence:
the workflow catches bugs well, but the reviewer prompt should more strongly
separate contract defects from defensible hardening suggestions.

### Post-remediation retest

Verdict: **PASS**

After tightening `reviewer.md`, a fresh blind reviewer and independent scorer
found exactly the four seeded defects:

| Metric | Baseline | Retest |
|---|---:|---:|
| Recall | 1.00 | 1.00 |
| Precision | 0.80 | 1.00 |
| Unsupported substantive findings | 1 | 0 |
| Critical seeded defects found | 3/3 | 3/3 |

Five hardening ideas were retained as residual risks rather than incorrectly
promoted to contract defects.

## EVAL-TOK — Token and coordinator-context comparison

Verdict: **PARTIAL**

Both paths returned all eight requested facts correctly.

| Metric | Direct | Delegated |
|---|---:|---:|
| Answer accuracy | 8/8 | 8/8 |
| Coordinator input tokens | 46,601 | 14,831 |
| Coordinator output tokens | 540 | 189 |
| Worker input tokens | — | 48,926 |
| Worker output tokens | — | 613 |
| Total observed tokens | 47,141 | 64,559 |
| Observed sequential wall time | 7.5s | 16.7s |

- Coordinator input reduction: `31,770` tokens, or `68.2%` — **PASS**.
- Total token delta: `+17,418` tokens, or `+36.9%` — **FAIL** for total-token
  savings on this bounded task.
- Cost: **unavailable** because verified provider pricing is not recorded.

Delegation isolated coordinator context successfully, but it cost more total
tokens and time for this small synthesis task. Brida should delegate to protect
long-running coordinator context or gain parallelism/independent judgment—not
claim that delegation is inherently cheaper.

## EVAL-MET — Metrics tracking

Verdict: **PASS**

- JSONL ledger: `metrics/runs.jsonl`.
- Validator and deterministic summary: `metrics/validate_metrics.py`.
- Tests: `metrics/test_validate_metrics.py`.
- Result: 10 positive/negative and cross-field semantic tests pass from both
  the `m2m` root and the `brida` directory.
- Unknown timing, tokens, and cost are represented as `null`, not estimates.

## EVAL-LONG — Long-horizontal dogfood

Verdict: **PASS**

- Four eval tracks executed under one durable project with independent review.
- Six named Herdr workers plus one isolated Codex measurement worker were used;
  all Brida-owned eval panes were closed after evidence was saved.
- Four orchestration/instrumentation blockers were recovered without user
  input: scorer start/run race, invalid `done` wait target, auto-closed JSON
  worker usage-tail loss, and a read-only inventory approval interruption.
- Project memory, exact token prompts/outputs, fixtures, hidden truth, scored
  reviewer outputs, audit receipts, ledger, validator, and tests persist
  outside chat history.
- `herdr agent list` after cleanup showed no live `brida-eval-*` agent.

This demonstrates durable orchestration and recovery for this evaluation
workflow. It does not yet establish performance on multi-day production work.
