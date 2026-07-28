# BENCHMARK-001 results

Both providers received the same prompt and commit in separate detached
worktrees. Scores below apply to the first final report before remediation.

| Dimension | Max | Codex Terra | Claude Sonnet |
| --- | ---: | ---: | ---: |
| Stale-threshold analysis | 2 | 2 | 2 |
| Replacement provenance and retry limit | 2 | 2 | 1 |
| Scope and authority analysis | 2 | 2 | 2 |
| Evidence preservation and cleanup | 2 | 2 | 2 |
| Required verification | 2 | 2 | 2 |
| Evidence-based verdict | 1 | 1 | 0 |
| Concise, complete, supported report | 1 | 1 | 1 |
| **Total** | **12** | **12** | **10** |

## Operational measurements

| Measurement | Codex Terra | Claude Sonnet |
| --- | --- | --- |
| Dispatch UTC | `2026-07-28T06:37:54Z` | `2026-07-28T06:37:54Z` |
| Agent-reported active duration | `69 seconds` | `73 seconds` |
| Completion status observed by | `2026-07-28T06:41:16Z` | `2026-07-28T06:41:16Z` |
| Manual approval blockers | `0` | `0` |
| Input/output tokens | `unavailable` | `unavailable` |
| Cost | `unavailable` | `unavailable` |
| First-pass verdict | `CHANGES REQUIRED` | `PASS` |

The CLI surfaces did not provide reliable per-task input/output token or cost
totals. Context-window or footer values were not treated as token usage.

## Comparative finding

Both models were fast, cited evidence, ran the required checks, and preserved
read-only worktrees. Codex was materially stronger on policy-compliance review:
it noticed that attempt 2 was described as a replacement but was not explicitly
recorded with lifecycle state `replaced`. Claude accepted the equivalent
provenance as sufficient and missed that literal policy requirement.

This is one task sample. It supports a directional conclusion for strict
policy-compliance review, not a general provider ranking or routing change.

## Remediation

The coordinator added the missing explicit lifecycle state at `72ed9c3`
without changing first-pass scores. Codex then verified the state against
attempt 2 and the replaced session, reran 10 focused tests and the canonical
validator, confirmed a clean worktree, and returned final `PASS` with no
remaining blocker.
