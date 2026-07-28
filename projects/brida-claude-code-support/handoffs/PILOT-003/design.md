# PILOT-003 — real tool-failure recovery pilot

## Decision

Use a disposable worktree containing a task-local `pilot-tool` executable. The
treatment run prepends a temporary directory to `PATH`; its wrapper fails once
for the exact command `pilot-tool read receipt`, returning exit code `42` and a
stable marker, then delegates every later invocation to the original executable.
The control run uses the unwrapped executable. This is a real command/tool
failure at a bounded tool boundary, not a simulated idle worker or a process
kill.

No production launcher, Herdr server, credentials, or real repository files are
modified. The injected wrapper and worktree are disposable and local.

## Run protocol

1. Record UTC time, repo commit, Herdr workspace/tab/pane IDs, current worker
   status, `git status --short`, and the absolute disposable worktree path.
2. Create two equivalent disposable worktrees from the same commit: control and
   treatment. Give each a read-only task packet that requires one
   `pilot-tool read receipt` call and a bounded recovery response.
3. Run control once and save the raw worker output plus tool exit status.
4. Install the treatment-only wrapper with mode `0700`, verify its hash and
   exact target command, then run treatment once. Capture the injected marker,
   exit `42`, recovery attempt, final receipt, and worker lifecycle states.
5. Stop the run if the worker requests broader permissions, accesses a path
   outside its worktree, invokes a non-task-local command, or needs a second
   replacement. Preserve evidence and escalate; do not improvise recovery.
6. Before cleanup, verify the treatment reaches the bounded expected outcome
   (one tool failure, at most one retry/replacement, no scope expansion) and
   write the parent/child receipts.

## Fault and evidence contract

The injected wrapper must prove: exact command match; one failure only; exit
code `42`; UTC timestamp; and delegation to the original tool thereafter.
Capture wrapper log, raw Herdr output, task packet, commit IDs, status snapshots,
receipt paths, and focused test/validator output. Do not record account IDs,
tokens, or secrets.

## Cleanup contract (acceptance gate)

Cleanup is successful only if every item is checked and recorded:

- `git status --short` is clean in both disposable worktrees, or all remaining
  files are the expected evidence copied to the canonical receipt location.
- The temporary `PATH` directory, wrapper, and wrapper log are removed after
  evidence is copied; wrapper hash and target path are retained in the receipt.
- Every Brida-created worker pane is idle/done, its final output is saved, and
  only the recorded pane IDs are closed. `herdr agent list` shows no orphan
  `brida-pilot-003-*` worker.
- No process started by the pilot remains: record a scoped process check before
  and after cleanup. Do not use a broad kill; escalate if a process cannot be
  identified and stopped safely.
- The original attempt evidence and any replacement provenance remain
  readable, and the canonical receipt validator passes.
- Worktree paths are removed only after the preceding evidence checks pass; if
  cleanup fails, preserve the worktree and escalate rather than retrying with
  broader authority.

## Acceptance tests

- Control: one successful tool call and complete receipt.
- Treatment: one exit-42 injected failure, one bounded retry/replacement at
  most, complete receipt, and explicit `replacement` origin plus current
  lifecycle state.
- Both runs pass the focused structural tests and canonical receipt validation.
- Diff/scope audit shows no production or remote changes.
- Cleanup checklist is fully signed by Brida; any unverified item is marked
  `Unverified`, not inferred from a worker's assertion.

## Risks and user decisions

This tests command-level failure handling, not Claude/provider outage behavior.
The user must approve the one-time pilot execution and the exact disposable
worktree root before running it. A later provider-failure experiment would need
separate authorization and must not be inferred from this result.
