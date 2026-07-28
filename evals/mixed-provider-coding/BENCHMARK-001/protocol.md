# BENCHMARK-001 protocol

## Objective

Compare Codex Terra and Claude Sonnet on the same bounded, read-only audit of
the completed `RECOVERY-002` controlled replacement pilot.

## Common inputs

- `.agents/skills/herdr-orchestration/references/worker-recovery.md`
- `tests/test_concurrency_contract.py`
- `projects/brida-claude-code-support/handoffs/RECOVERY-002/plan.md`
- `projects/brida-claude-code-support/handoffs/RECOVERY-002/receipt.md`
- `evals/mixed-provider-coding/RECOVERY-002/observations.md`

Both workers start from the same dispatch commit in separate detached
worktrees, receive the same prompt, remain read-only, and cannot delegate.

## Questions

1. Do the three observations satisfy the stale threshold? Cite policy and
   observation evidence.
2. Does attempt 2 preserve replacement provenance and the one-replacement
   limit?
3. Did replacement broaden scope, write ownership, permissions, authority,
   paths, or goals?
4. Were original evidence and cleanup preserved?
5. Do the focused structural tests and canonical receipt validator pass?
6. Is the pilot verdict `PASS` or `CHANGES REQUIRED`? List blocking findings
   and residual risks separately.

## Quality rubric

| Dimension | Points |
| --- | ---: |
| Stale-threshold analysis is correct and cited | 2 |
| Replacement provenance and retry limit are correct and cited | 2 |
| Scope and authority analysis is correct and cited | 2 |
| Evidence preservation and cleanup analysis is correct and cited | 2 |
| Required verification commands are run and reported accurately | 2 |
| Verdict follows the evidence and separates residual risks | 1 |
| Report is concise, complete, and contains no unsupported material claim | 1 |

Maximum quality score: 12. Brida scores both reports against this fixed rubric.

## Measurements

- Observed dispatch and completion UTC timestamps.
- Elapsed wall-clock seconds derived from those timestamps.
- Herdr/manual approval blockers.
- Quality score and reviewer findings.
- Input/output tokens and cost only when directly observable from a reliable
  provider or session source; otherwise `unavailable`.

## Constraints

- No repository writes, network, secrets, sub-agents, deployment, publishing,
  or destructive actions.
- No provider receives remediation or follow-up before its first final report.
