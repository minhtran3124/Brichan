# Claude Sonnet first-pass report

- Model: `Claude Sonnet 5`
- Pane: `w1X:p1W`
- Session: `96f593e5-457c-4d9a-ac88-78b8f6516e76`
- Dispatch commit: `323d546`
- Dispatch UTC: `2026-07-28T06:37:54Z`
- Agent-reported active duration: `73 seconds`
- Manual approval blockers: `0`
- Input/output tokens: `unavailable`
- Cost: `unavailable`

## Verdict

`PASS`

## Answers

1. The three timestamped observations satisfy the stale threshold.
2. Attempt 2 preserves prior-session provenance and the one-replacement limit.
3. No scope, ownership, permission, authority, path, or goal broadening is
   evidenced.
4. Original evidence and pane cleanup are preserved.
5. Ten focused structural tests and the canonical receipt validator passed.
6. No blocking finding was reported.

The report did not identify that the policy requires explicitly recording the
new attempt's lifecycle state as `replaced`.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_concurrency_contract -v`
  — 10 tests, `OK`.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_handoff_receipts.py projects`
  — three canonical receipts validated.
- `git status --short` — clean.

## Residual risks

- The three observations span 39 seconds; the policy defines no minimum
  interval, but realistic stale timing remains untested.
- This was a disclosed simulated stall rather than a live provider failure.
- The receipt had not yet recorded a review verdict at dispatch.
