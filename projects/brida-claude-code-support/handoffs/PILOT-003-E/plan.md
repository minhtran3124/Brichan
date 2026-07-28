# PILOT-003-E execution plan

## Objective

Execute one isolated control run and one isolated treatment run of the approved
task-local tool-failure pilot.

## Scope

- Disposable detached worktree per run from commit `6f3793e`.
- Claude Sonnet worker per run; no worker writes to the repository.
- Treatment-only shim returns exit `42` once for `pilot-tool read receipt` then
  delegates to the local tool.
- Brida records evidence, validates receipts, and removes only the created
  worktrees/panes after capture.

## Acceptance

- Control succeeds exactly once.
- Treatment captures the fault marker/exit code then succeeds on one retry.
- No production files, authority, permissions, paths, or worker goals expand.
- Cleanup contract and canonical receipt validation pass.
