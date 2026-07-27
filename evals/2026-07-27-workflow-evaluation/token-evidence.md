# EVAL-TOK raw evidence

## Task

Both paths had to return the same eight source-grounded fields from
`AGENTS.md`, `operating-principles.md`, `model-catalog.md`, and `reviewer.md`:

`small_task_policy`, `delegation_trigger`, `default_worker`,
`forbidden_effort`, `mandatory_review_surface`, `reviewer_independence`,
`worker_transport`, and `pane_cleanup`.

Expected facts were taken directly from those four files. Accuracy was one
point per field whose meaning matched the source.

## Direct coordinator

Model: `gpt-5.6-terra`, medium

Exact prompt:

```text
EVAL-TOK direct path. Do this task yourself; do not delegate, use Herdr, or spawn agents. Read only AGENTS.md, operating-principles.md, model-catalog.md, and reviewer.md. Return one compact JSON object with exactly these keys and source-grounded string values: small_task_policy, delegation_trigger, default_worker, forbidden_effort, mandatory_review_surface, reviewer_independence, worker_transport, pane_cleanup. No commentary and no file changes.
```

```json
{
  "small_task_policy": "Work directly when small, sequential, or tightly coupled.",
  "delegation_trigger": "Delegate only when specialist perspective, independent review, or parallelizable bounded work provides material value.",
  "default_worker": "gpt-5.6-terra at medium effort.",
  "forbidden_effort": "ultra",
  "mandatory_review_surface": "Authentication, authorization, secrets, payments, personal data, destructive migrations, production behavior, public APIs, database schemas, cross-service contracts, large cross-cutting changes, or repeated worker failures.",
  "reviewer_independence": "Use a fresh reviewer session that did not implement the change; prefer a different verified provider.",
  "worker_transport": "Independent main-agent sessions created through Herdr.",
  "pane_cleanup": "Close Brida-owned idle or done worker panes before reporting delegated work complete."
}
```

Observed `turn.completed` usage:

```json
{"input_tokens":46601,"output_tokens":540}
```

Accuracy: `8/8`.

## Isolated worker

Model: `gpt-5.6-luna`, medium

Exact prompt:

```text
EVAL-TOK isolated worker path. Do not delegate or spawn agents. Read only AGENTS.md, operating-principles.md, model-catalog.md, and reviewer.md. Use targeted reads and do not print full source documents. Return one compact JSON object with exactly these keys and source-grounded string values: small_task_policy, delegation_trigger, default_worker, forbidden_effort, mandatory_review_surface, reviewer_independence, worker_transport, pane_cleanup. No commentary and no file changes.
```

```json
{
  "small_task_policy": "Work directly when the task is small, sequential, or tightly coupled.",
  "delegation_trigger": "Delegate only when specialist perspective, independent review, or parallelizable bounded work provides material value.",
  "default_worker": "gpt-5.6-terra at medium effort.",
  "forbidden_effort": "Do not use ultra for workers.",
  "mandatory_review_surface": "Authentication, authorization, secrets, payments, personal data, destructive migrations, irreversible transformations, production/deployment behavior, public APIs, database schemas, cross-service contracts, large cross-cutting changes, or repeatedly failed worker tasks.",
  "reviewer_independence": "Prefer a different verified provider; otherwise use a fresh main-agent session without implementation context and, when practical, a stronger model.",
  "worker_transport": "Independent main-agent sessions created and coordinated through Herdr.",
  "pane_cleanup": "Close Brida-owned idle/done worker panes; never close panes owned by the user or another workflow."
}
```

Observed `turn.completed` usage:

```json
{"input_tokens":48926,"output_tokens":613}
```

Accuracy: `8/8`.

## Delegated coordinator

The fresh coordinator received only the worker JSON above and was explicitly
forbidden from reading source files or using tools.

Exact prompt:

```text
EVAL-TOK delegated coordinator path. Do not read files, run tools, use Herdr, or delegate. Normalize the worker evidence below into one compact JSON object with exactly the same eight keys. Preserve the meaning; no commentary.

Worker evidence:
{"small_task_policy":"Work directly when the task is small, sequential, or tightly coupled.","delegation_trigger":"Delegate only when specialist perspective, independent review, or parallelizable bounded work provides material value.","default_worker":"gpt-5.6-terra at medium effort.","forbidden_effort":"Do not use ultra for workers.","mandatory_review_surface":"Authentication, authorization, secrets, payments, personal data, destructive migrations, irreversible transformations, production/deployment behavior, public APIs, database schemas, cross-service contracts, large cross-cutting changes, or repeatedly failed worker tasks.","reviewer_independence":"Prefer a different verified provider; otherwise use a fresh main-agent session without implementation context and, when practical, a stronger model.","worker_transport":"Independent main-agent sessions created and coordinated through Herdr.","pane_cleanup":"Close Brida-owned idle/done worker panes; never close panes owned by the user or another workflow."}
```

Exact output:

```json
{
  "small_task_policy": "Work directly when the task is small, sequential, or tightly coupled.",
  "delegation_trigger": "Delegate only when specialist perspective, independent review, or parallelizable bounded work provides material value.",
  "default_worker": "gpt-5.6-terra at medium effort.",
  "forbidden_effort": "Do not use ultra for workers.",
  "mandatory_review_surface": "Authentication, authorization, secrets, payments, personal data, destructive migrations, irreversible transformations, production/deployment behavior, public APIs, database schemas, cross-service contracts, large cross-cutting changes, or repeatedly failed worker tasks.",
  "reviewer_independence": "Prefer a different verified provider; otherwise use a fresh main-agent session without implementation context and, when practical, a stronger model.",
  "worker_transport": "Independent main-agent sessions created and coordinated through Herdr.",
  "pane_cleanup": "Close Brida-owned idle/done worker panes; never close panes owned by the user or another workflow."
}
```

Observed `turn.completed` usage:

```json
{"input_tokens":14831,"output_tokens":189}
```

Accuracy: `8/8`.

The exact prompts, outputs, and final usage records needed to reproduce the
comparison are persisted above. Host-local Codex session paths are deliberately
excluded from the repository.

## Recomputed comparison

| Metric | Direct | Delegated |
|---|---:|---:|
| Coordinator input | 46,601 | 14,831 |
| Coordinator output | 540 | 189 |
| Worker input | — | 48,926 |
| Worker output | — | 613 |
| Total | 47,141 | 64,559 |

- Coordinator input reduction: `(46601 - 14831) / 46601 = 68.1745%`.
- Total-token increase: `(64559 - 47141) / 47141 = 36.9496%`.

The first Herdr JSON-mode attempt finished and auto-closed its pane before the
usage tail could be retained. Exact token measurement was therefore repeated
with an isolated Codex worker using the same model, prompt, and disabled-native-
agent settings. The Herdr reviewer/scorer tracks independently validate worker
lifecycle behavior; this token track validates context accounting.
