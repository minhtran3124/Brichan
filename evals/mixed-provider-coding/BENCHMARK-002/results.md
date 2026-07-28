# BENCHMARK-002 results

Both providers received the same packet and seeded fixture at dispatch commit
`6f3793e` in separate detached worktrees. The coordinator independently
inspected both final diffs and reran the baseline fixture tests in the main
worktree.

| Dimension | Codex Terra | Claude Sonnet |
| --- | ---: | ---: |
| Implementation behavior | pass | pass |
| Seeded debugging fix | pass | pass |
| Focused tests | 4 passed | 6 passed |
| Scope/diff check | pass | pass |
| **First-pass verdict** | **PASS** | **PASS** |

Tokens, provider cost, and independent end-to-end elapsed time were not
observable from the available CLI/session surfaces and remain `unavailable`.
The different test counts reflect independent test design, not unequal input.
This two-task sample is directional only; it does not justify changing global
routing or declaring a provider winner.
