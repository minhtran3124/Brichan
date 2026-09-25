# Decision log

### 2026-09-24 — Jev is a decision layer, not a route

- Status: accepted
- Context: Jev is marketed as up to 400x cheaper than LLMs; the obvious move is
  to route work to it.
- Decision: Never assign Jev to `plan`, `implement`, `review`, or `scan`. Use
  it only for bounded typed judgments beside the frontier workers, and only
  alongside deterministic checks.
- Rationale: It cannot generate text or code; independent evals put
  difficulty prediction at 51.3% and trajectory failure attribution at random
  (AUROC 0.56); injection in the state moves verdicts.
- Trade-offs: Savings are confined to the long tail of small judgments, not
  the frontier-worker spend that dominates Brichan's cost.
- Owner: Brichan
- Evidence: `projects/brida-jev-decision-layer/references.md`
- Supersedes: none

### 2026-09-24 — Start with a shadow-mode pilot

- Status: proposed
- Context: Thresholds published by others (deny at risk >= 2.5, auto-approve
  only at confidence == 1.000) come from other people's data.
- Decision: Log verdicts without acting on them first; set thresholds from
  Brichan's own worker tool calls and pane observations.
- Rationale: Every independent evaluator recommends it; a full pilot costs
  under $1 at vendor pricing.
- Trade-offs: Delays any safety benefit by one pilot cycle.
- Owner: Brichan
- Evidence: `projects/brida-jev-decision-layer/references.md`
- Supersedes: none
