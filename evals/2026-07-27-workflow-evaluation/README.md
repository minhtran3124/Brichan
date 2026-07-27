# Brida workflow evaluation — 2026-07-27

## Objective

Evaluate four claims independently and report counter-evidence:

1. Reviewer workflow works end to end.
2. Delegation reduces coordinator context and/or total tokens.
3. Metrics can be recorded and summarized reproducibly.
4. Brida can sustain a multi-phase, multi-worker horizontal task.

## Verdict scale

- **PASS** — acceptance threshold met with rerunnable evidence.
- **PARTIAL** — useful behavior observed, but the full claim is not established.
- **FAIL** — threshold missed or evidence contradicts the claim.

## EVAL-REV — Blind reviewer

- Input: `reviewer-input/intent.md` and `reviewer-input/transfer_service.py`.
- Hidden truth: `scoring/reviewer-truth.md`.
- Reviewer must not read the scoring directory.
- Scorer receives reviewer output and hidden truth after the review completes.
- Metrics: matched defects, missed defects, unsupported findings, recall, precision.
- Pass: recall >= 0.75, precision >= 0.75, and all critical defects found.

## EVAL-TOK — Coordinator context versus total tokens

Both paths answer the same eight-fact synthesis task over the same four Brida
documents.

- Direct: one coordinator reads source documents and answers.
- Delegated: one worker reads source documents and writes a bounded evidence
  summary; a fresh coordinator receives only that summary and answers.
- Metrics: answer accuracy, coordinator input/output tokens, worker
  input/output tokens, combined tokens, wall time.
- Pass for coordinator-context claim: delegated coordinator input tokens are
  lower than direct coordinator input tokens with equal answer accuracy.
- Pass for total-token claim: combined delegated tokens are lower than direct
  tokens with equal answer accuracy.
- Cost: unavailable unless verified pricing data is supplied.

## EVAL-MET — Metrics tracking

- Add a JSONL run ledger, schema documentation, validator, and summary command.
- Positive fixture must pass.
- Missing required field, invalid verdict, and negative token counts must fail.
- Summary output must be deterministic.

## EVAL-LONG — Horizontal dogfood

The full evaluation is the workload:

- Four tracks.
- Multiple isolated worker contexts.
- Hidden-answer review.
- A/B token measurement.
- Local implementation and independent final audit.

Metrics: elapsed time, planned/completed tasks, worker count, blocker count,
user intervention count, acceptance pass count, cleanup completeness, and
coordinator durable-memory updates.

Pass: all four tracks reach a verdict, every worker has bounded scope and
evidence, no Brida-owned pane remains, and the final report lists limitations.
