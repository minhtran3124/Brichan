# PILOT-003 execution observations

## Control — `brida-pilot-003-control`

- Worker session: `079c61b9-1a7b-404d-b321-13bcb04aa5de`; pane `w1X:p23`.
- The worker invoked `pilot-tool read receipt` once with the task-local tool
  directory first in `PATH`.
- Result: stdout `PILOT_TOOL_OK receipt`, exit `0`, no stderr.
- `git status --short` was unchanged before/after: only pre-existing
  `pilot-fixture/` was untracked in the disposable worktree.

## Treatment — `brida-pilot-003-treatment`

- Worker session: `1ae870b4-aeb0-40fc-a71e-3ebca831898d`; pane `w1X:p24`.
- First worker invocation returned stderr marker `PILOT003_FAULT_ONCE` and exit
  `42`. The wrapper log records `2026-07-28T09:14:01Z`, exact command
  `pilot-tool read receipt`, and `exit=42`.
- Second worker invocation returned stdout `PILOT_TOOL_OK receipt` and exit
  `0`. The wrapper log had exactly one line.
- `git status --short` was unchanged before/after: only pre-existing
  `fault-bin/` and `pilot-fixture/` were untracked in the disposable worktree.

## Coordinator verification defect

After the worker's two permitted invocations, the coordinator independently
called the treatment tool once more while checking the wrapper log. That call
returned `PILOT_TOOL_OK receipt` with exit `0`; it did not create a second fault
log entry. Nevertheless it violated the pilot's explicit two-invocation bound.
The treatment is therefore `CHANGES REQUIRED`, not a clean pilot pass. Do not
reuse this treatment worktree; a fresh treatment-only run needs new user
approval.

## Fresh treatment-only rerun — `brida-pilot-003-treatment-rerun`

- Worker session: `b9f21f43-3f66-49c0-b078-a2bf125c38df`; pane `w1X:p25`.
- Before the successful sequence, the worker attempted to redirect stderr to a
  root-level path. The sandbox rejected that redirection before `pilot-tool`
  executed. The worker immediately checked that neither `.fired` nor
  `fault.log` existed, establishing zero actual tool invocations at that point.
- The two actual tool invocations then produced: first stderr
  `PILOT003_FAULT_ONCE` with exit `42`; second stdout `PILOT_TOOL_OK receipt`
  with exit `0`.
- Wrapper evidence: exactly one log line at `2026-07-28T09:19:53Z` records the
  exact target command, marker, and exit `42`; `.fired` exists.
- The coordinator read raw worker output and wrapper log only; it did not invoke
  `pilot-tool`. Worktree status before/after contained only the pre-existing
  untracked `fault-bin/` and `pilot-fixture/` directories.
