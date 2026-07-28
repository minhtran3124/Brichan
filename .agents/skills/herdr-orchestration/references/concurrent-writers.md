# Concurrent writers

Use this policy when a task has more than one writer.

## Exclusive file ownership

Authorized path sets must not overlap. Assign each writer an exclusive set of
paths before work starts. Shared files are integrator-owned.

## Worktree isolation

One branch and one worktree per writer. Keep each writer's changes isolated
until integration.

## Receipt requirements

A handoff receipt is mandatory for every multi-writer task. Create one child
receipt per writer and one parent receipt per task.

## Integration

The integrator combines writer changes and owns any shared files. Final review
covers integrated state.
