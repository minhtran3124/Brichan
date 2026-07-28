# PILOT-003-T-R1 execution plan

## Objective

Rerun the treatment in a new disposable worktree after the prior coordinator
verification made a prohibited third invocation.

## Scope and guard

- One Claude Sonnet worker invokes the task-local tool exactly twice.
- First call must return the injected exit-42 marker; second must succeed.
- Brida must not invoke `pilot-tool`; post-run verification is limited to raw
  worker output, wrapper-log reading, status inspection, and cleanup.

## Acceptance

- One fault log line, exact target command, marker, and exit 42.
- Worker reports exactly two calls: 42 then 0 with exact output.
- No scope/authority expansion or worker-caused repository change.
- Pane/worktree cleanup and canonical receipt validation pass.
