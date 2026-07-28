# BENCHMARK-002 protocol

## Objective

Compare Codex Terra and Claude Sonnet on one implementation task and one
debugging task using the same deterministic target and acceptance criteria.

## Common task packet

In `evals/mixed-provider-coding/BENCHMARK-002/`, implement the requested
behavior in `target.py`, add or update tests, and run the focused test command.
Do not change files outside this directory.

### Implementation task

Add `can_replace(state)` and `validate_transition(current, event, next_state)`.
`can_replace` is true only for `abandoned`. `validate_transition` must return
`True` only when `next_state == transition(current, event)` and the transition
is known; otherwise return `False` (including unknown states/events).

### Debugging task

The seeded defect is that `transition("abandoned", "replace")` currently
returns `"active"`, allowing an abandoned attempt to be reused as the new
attempt's lifecycle. Fix the target so a replacement is represented by a new
attempt origin without mutating the original lifecycle: the helper must return
`"replacement"` for this event, while all existing state/event behavior stays
unchanged. Update tests to cover the defect and regression behavior.

## Acceptance criteria

- Both requested behaviors are implemented and covered by tests.
- Focused `python3 -m unittest discover -s evals/mixed-provider-coding/BENCHMARK-002 -p 'test_*.py' -v` passes.
- Diff is limited to `evals/mixed-provider-coding/BENCHMARK-002/`.
- Final report states first-pass result, elapsed time if observable, test output,
  files changed, and any ambiguity in the intentionally compact API.

## Measurement

Record dispatch and completion UTC timestamps from Herdr where available.
Tokens and cost are `unavailable` unless directly exposed by the session.
