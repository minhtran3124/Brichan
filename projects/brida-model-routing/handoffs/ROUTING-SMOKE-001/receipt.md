## Identity

- Receipt schema version: `2`
- Task ID: `ROUTING-SMOKE-001`
- Project: `brida-model-routing`
- Handoff timestamp (UTC): `2026-07-29T06:06:14Z`
- Receipt role: `standalone`
- Parent receipt path: `null`
- Attempt: `1`
- Replaces session: `null`
- Attempt origin: `initial`
- Attempt lifecycle state: `complete`
- Prior attempt state: `null`
- Replacement evidence path: `null`

## Plan version

- Artifact or plan ID: `MODEL-ROUTING-P1`
- Version: `1`
- Status: `implemented`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `OpenAI` | `Codex coordinator` | `w1X:pA` | `019fac3c-177b-7061-9506-957ed48ccdd8` |
| Implementer | `OpenAI` | `gpt-5.6-luna, medium` | `w1X:p2W` | `019fac78-beb2-74d2-b175-e83949385819` |
| Reviewer | `OpenAI` | `Codex coordinator` | `w1X:pA` | `019fac3c-177b-7061-9506-957ed48ccdd8` |

## Scope

- In scope: read-only live Herdr route and route-resolution verification
- Authorized paths: repository root, read-only inspection only
- Exclusive write ownership: no writes authorized
- Branch: `feat/settings-driven-model-routing`
- Worktree: `main repository worktree`

## Non-goals

- Excluded work: implementation, file edits, delegation, remote actions, and
  permission changes

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| `SMOKE1` | `pass` | Herdr-managed pane `w1X:p2W`, session `019fac78-beb2-74d2-b175-e83949385819` |
| `SMOKE2` | `pass` | live TUI and process argv show `gpt-5.6-luna`, `model_reasoning_effort=medium` |
| `SMOKE3` | `pass` | plan=Claude/opus/high, implement=Codex/Terra/medium, review=Claude/opus/high, scan=Codex/Luna/medium |
| `SMOKE4` | `pass` | before/after `git status --short` identical at 24 entries |

## Verification

| Command | Result |
| --- | --- |
| four route JSON dry-runs | `pass; all exit 0 and report dry_run=true` |
| before/after `git status --short` | `pass; identical` |

## Implementation evidence

- Changed artifacts: `none authorized`
- Diff evidence: worker caused no repository changes
- Test evidence: Herdr session metadata, process argv, four route JSON outputs,
  and status comparison captured from `w1X:p2W`

## Review verdict

- Verdict: `pending`
- Findings: live smoke evidence is complete; independent review is recorded
  separately

## Risks and open decisions

- Risks: real installed Herdr/provider integration may differ from parser-only
  validation
- Open decisions: `null`

## Cleanup status

- Brida-owned panes closed: `yes`
- Project memory updated: `yes`
