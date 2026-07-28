# BENCHMARK-002 plan

## Objective

Run an equivalent Codex Terra versus Claude Sonnet benchmark covering one
implementation task and one debugging task on a deterministic lifecycle helper.

## Scope

- Shared fixture and protocol under `evals/mixed-provider-coding/BENCHMARK-002/`.
- One isolated detached worktree per provider.
- First-pass diffs, focused tests, elapsed time, and rubric-based comparison.

## Exclusions

- No production code changes, remote actions, secrets, delegation, or routing
  change based on this sample.

## Acceptance

- Both providers receive the same packet and dispatch commit.
- Each first-pass result is scored on behavior, tests, scope, and evidence.
- Tokens and cost remain `unavailable` unless directly observable.
- Results and limitations are recorded in a canonical receipt and references.
