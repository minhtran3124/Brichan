# Handoff receipt

This standalone receipt records the `RECOVERY-002` controlled recovery pilot.

## Identity

- Receipt schema version: `1`
- Receipt role: `standalone`
- Parent receipt path: `null`
- Task ID: `RECOVERY-002`
- Project: `brida-claude-code-support`
- Handoff timestamp (UTC): `2026-07-28T06:30:26Z`
- Attempt: `1`
- Replaces session: `null`

## Plan version

- Artifact or plan ID: `RECOVERY-002-P1`
- Version: `1`
- Status: `accepted`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `Brida` | `Codex coordinator` | `w1X:pA` | `019fa6ba-dd94-7681-be71-1950f999a02f` |
| Implementer | `Codex` | `gpt-5.6-luna` | `null` | `null` |
| Reviewer | `null` | `null` | `null` | `null` |

## Scope

- In scope: controlled stall observations, bounded replacement, and read-only
  recovery-policy evidence.
- Authorized paths: `read-only repository inspection; no writes`
- Exclusive write ownership: `read-only`
- Branch: `feat/recovery-pilot-benchmark`
- Worktree: `repository root`

## Non-goals

- Excluded work: repository edits by workers, automatic termination, a second
  replacement, broader authority, secrets, network, deployment, and publishing.

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| `R2-1` | `pending` | `pending` |
| `R2-2` | `pending` | `pending` |
| `R2-3` | `pending` | `pending` |
| `R2-4` | `pending` | `pending` |
| `R2-5` | `pending` | `pending` |

## Verification

| Command | Result |
| --- | --- |
| `herdr agent get <original>` | `pending` |
| `herdr agent read <original> --lines 40` | `pending` |
| `herdr agent read <replacement> --lines 120` | `pending` |
| `git status --short` | `pending` |

## Implementation evidence

- Changed artifacts: `none by workers; coordinator evidence pending`
- Diff evidence: `pending`
- Test evidence: `pending`

## Review verdict

- Verdict: `null`
- Findings: `null`

## Risks and open decisions

- Risks: this is a deliberate stall simulation, not an uncontrolled provider
  or process failure.
- Open decisions: whether a later pilot should inject a real tool or provider
  failure under the same bounded policy.

## Cleanup status

- Brida-owned panes closed: `no`
- Project memory updated: `yes`
