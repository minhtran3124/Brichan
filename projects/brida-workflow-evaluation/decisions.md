# Decision log

### 2026-07-27 — Separate coordinator-context savings from total-token savings

- Status: accepted
- Context: Delegation may reduce coordinator context while increasing total tokens.
- Decision: Report coordinator input, worker input, combined total, and quality separately.
- Rationale: Prevents claiming total savings from context isolation alone.
- Trade-offs: Requires multiple controlled model runs.
- Owner: Brida
- Evidence: `evals/2026-07-27-workflow-evaluation/README.md`
- Supersedes:
