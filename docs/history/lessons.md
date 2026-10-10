# Lessons

This document is historical evidence, not normative policy.

One entry per escaped defect: a defect that reached `main` or a release before
it was caught. Each entry names the regression test or check that now catches
it. Promotion of a repeated lesson follows the rule under `Known mistakes` in
`AGENTS.md`.

| Date | Escaped defect | How it was found | Now caught by |
|---|---|---|---|
| 2026-10-10 | Claude launches disallowed only `Task`. After Claude Code renamed it `Agent` (still matched through the alias) and added `Workflow`, the native multi-agent `Workflow` tool stayed available, contrary to the no-native-delegation non-goal. | Comparison against Anthropic's AI-native SDLC playbook, then a live tool-list check (`CLAUDE-007`, PR #43) | Exact-flag assertions in `tests/unit/test_model_routing.py` and `tests/contract/test_repository_contract.py`, which fail if `Agent` or `Workflow` is dropped |
