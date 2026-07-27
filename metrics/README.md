# Brida workflow metrics

`runs.jsonl` is the append-only ledger for completed workflow evaluations and
delegated tasks. Each line is one JSON object.

## Required fields

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | integer | Currently `1` |
| `run_id` | string | Unique stable run identifier |
| `task_id` | string | Task or eval identifier |
| `track` | string | Workflow category |
| `started_at` | UTC timestamp or `null` | ISO 8601 ending in `Z` when observed |
| `completed_at` | UTC timestamp or `null` | ISO 8601 ending in `Z` when observed |
| `elapsed_seconds` | number >= 0 or `null` | Observed wall time |
| `verdict` | `PASS`, `PARTIAL`, or `FAIL` | Evidence-based outcome |
| `acceptance_passed` | integer >= 0 | Acceptance checks passed |
| `acceptance_total` | integer >= 0 | Total acceptance checks |
| `worker_count` | integer >= 0 | Independent worker sessions used |
| `blocker_count` | integer >= 0 | Observed blockers |
| `user_intervention_count` | integer >= 0 | Material user interventions |
| `reviewer_finding_count` | integer >= 0 | Substantive reviewer findings |
| `coordinator_input_tokens` | integer >= 0 or `null` | Observed coordinator input |
| `coordinator_output_tokens` | integer >= 0 or `null` | Observed coordinator output |
| `worker_input_tokens` | integer >= 0 or `null` | Sum across workers |
| `worker_output_tokens` | integer >= 0 or `null` | Sum across workers |
| `cost_usd` | number >= 0 or `null` | Only verified observed cost |
| `cost_source` | string or `null` | Source supporting `cost_usd` |
| `evidence` | array of strings | Rerunnable commands or artifact paths |
| `notes` | string | Limitations and counter-evidence |

Timestamp, duration, token, and cost values must be `null` when unavailable. Do
not estimate them.

## Validate and summarize

```bash
python3 metrics/validate_metrics.py metrics/runs.jsonl
python3 metrics/validate_metrics.py metrics/runs.jsonl --summary
python3 -m unittest metrics/test_validate_metrics.py
```
