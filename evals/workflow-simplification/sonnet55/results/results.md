# WFS-010 results: `claude-sonnet-5` vs `claude-sonnet-5-5`

Date: 2026-10-08. Protocol: `../README.md`. Base commit `40f46d8`.

## Setup

- Four workers through Herdr, dispatched together at 08:40:31Z: one coding
  and one scan worker per arm, effort `medium`, model the only difference.
  Arm A = `claude-sonnet-5`, arm B = `claude-sonnet-5-5`.
- Blind coding review: one fresh `claude-fable-5` session at `high` effort
  saw the submissions as X and Y. Mapping (revealed after scoring): X = arm A
  (`claude-sonnet-5`), Y = arm B (`claude-sonnet-5-5`). The protocol prefers
  a different provider; Codex is not installed on this machine, so the
  reviewer is same-provider but a different model from both arms, as in
  stage 1.
- Every worker returned a techstack verification acknowledgement matching
  its packet's Snapshot digest. Both arms changed only their authorized
  paths.

## Coding (stage 1 tasks)

| Measure | `claude-sonnet-5` (A / X) | `claude-sonnet-5-5` (B / Y) |
|---|---|---|
| Hidden tests (15 + 12 + 9) | 36/36 | 36/36 |
| Visible and own tests | all pass (17 + 11 + 15) | all pass (6 + 11 + 4) |
| Blind review score (3 tasks x 3 criteria x 5) | 36/45 | **42/45** |
| Functional defects found by review | 1 High (T1 `RecursionError` on deeply nested JSON), 1 Medium (T2 accepts `"1.0.0\n"` and non-ASCII digits) | 0 |
| Worker wall time shown by the CLI | 4m 52s | **1m 20s** |

The coordinator reproduced both arm A defects independently and confirmed
arm B rejects or counts the same four inputs correctly. The hidden tests do
not cover either input class, so only the review separated the arms on
correctness.

## Scan (seeded policy audit)

Answer key: `../s1-policy-audit/answer-key.md` (six seeded defects, three
decoys).

| Measure | `claude-sonnet-5` (A) | `claude-sonnet-5-5` (B) |
|---|---|---|
| Seeded defects found | 6/6 | 6/6 |
| Decoys flagged (false positives) | 0/3 | 0/3 |
| Other findings | none (D6 reported as two entries) | none |
| Minor slips in "not a defect" notes | none | one line number off by one; a speculative "skips T-006" remark |
| Worker wall time shown by the CLI | 3m 26s | **59s** |

## Tokens and cost

The CLI showed no session token totals in these captures. Tokens and cost
are `null`; per-token prices are equal for the two models, per the
Anthropic model list as of 2026-10-08 (not verified as billed cost).

## Verdict

Under the preference rule in `../README.md`, `claude-sonnet-5-5` is
preferred: no worse on hidden tests on every coding task, no worse on scan
recall, and better on review findings (0 functional defects vs 1 High and
1 Medium), blind review score (42 vs 36), and wall time (about 3.6x faster on
coding and 3.5x on scan).

Limits: four tasks, one sample per arm, and a same-provider reviewer. The
scan fixture was easy enough that both arms scored perfectly, so it
separated the models on speed only. This is directional evidence that
supports keeping `claude-sonnet-5-5` on the `scan` route; it is not proof of
a general advantage.

## Notes

- Arm A's two defects are the same classes stage 1 found for
  `claude-opus-5` (T1 nested JSON) and that both Opus arms fixed (T2 parser).
- The reviewer reported the known `make check` worktree failure
  (`test_repository_paths` seeing `.git` as a file); `40f46d8` predates the
  WFS-008 fix.
