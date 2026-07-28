# Handoff receipt

## Identity

- Receipt schema version: `2`
- Receipt role: `parent`
- Parent receipt path: `null`
- Task ID: `PILOT-003-E`
- Project: `brida-claude-code-support`
- Handoff timestamp (UTC): `2026-07-28T09:14:59Z`
- Attempt: `1`
- Replaces session: `null`
- Attempt origin: `initial`
- Attempt lifecycle state: `complete`
- Prior attempt state: `null`
- Replacement evidence path: `null`

## Plan version

- Artifact or plan ID: `PILOT-003-E1`
- Version: `1`
- Status: `reviewed`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Coordinator/reviewer | `Brida` | `Codex coordinator` | `w1X:pA` | `019fa7eb-ba3f-7ee3-bf45-b6834847f03c` |
| Control worker | `Claude` | `Sonnet 5` | `w1X:p23` | `079c61b9-1a7b-404d-b321-13bcb04aa5de` |
| Treatment worker | `Claude` | `Sonnet 5` | `w1X:p24` | `1ae870b4-aeb0-40fc-a71e-3ebca831898d` |

## Scope

- In scope: one control and one treatment run in dedicated disposable worktrees.
- Authorized paths: task-local `pilot-fixture/` and treatment `fault-bin/` only.
- Exclusive write ownership: one worker per worktree; coordinator owns receipts/evidence.
- Branch: `main` at dispatch commit `6f3793e`
- Worktree: two Brida-created detached disposable worktrees

## Non-goals

- Excluded work: production changes, provider-outage simulation, process kills,
  additional retries, remote actions, secrets, deployment, and publishing.

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| `P3E-1` | `pass` | Control tool returned exact success output and exit 0 once. |
| `P3E-2` | `pass` | Treatment worker observed one exit-42 marker then one successful retry. |
| `P3E-3` | `fail` | Coordinator verification made a prohibited third treatment invocation. |
| `P3E-4` | `pass` | No production scope, permission, or authority expansion occurred. |

## Verification

| Command | Result |
| --- | --- |
| Control worker command and report | `pass; exact output and exit 0` |
| Treatment worker command/log/report | `pass; marker, exit 42, retry exit 0, one log line` |
| Coordinator post-run check | `fail; made third treatment invocation` |

## Implementation evidence

- Changed artifacts: task-local fixture tools, treatment wrapper state/log, and
  `evals/mixed-provider-coding/PILOT-003/observations.md`.
- Diff evidence: worker worktrees only contained task-local untracked fixture
  directories; main repository changes are durable pilot artifacts.
- Test evidence: worker reports and wrapper log are preserved in observations.

## Review verdict

- Verdict: `CHANGES REQUIRED`
- Findings: treatment cannot be accepted because the coordinator violated the
  two-invocation bound after the worker completed.

## Risks and open decisions

- Risks: this is a command-level fault, not a provider outage.
- Open decisions: approve one fresh treatment-only rerun; do not reuse this run.

## Cleanup status

- Brida-owned panes closed: `yes`
- Project memory updated: `yes`
