# Handoff receipt

This versioned planner-to-implementer/reviewer lifecycle envelope records a
bounded handoff and its receipt. Its section headings are contract-checked;
keep the headings unchanged and in this order. Use `null` when a value is
unknown or unavailable. Do not include personal or home paths.

## Identity

- Receipt schema version: `1`
- Task ID: `<task-id>`
- Project: `<project-slug>`
- Handoff timestamp (UTC): `<ISO-8601 timestamp or null>`
- Receipt role: `<child or parent or null>`
- Parent receipt path: `<repo-relative path or null>`

## Plan version

- Artifact or plan ID: `<artifact-id or null>`
- Version: `<version or null>`
- Status: `<draft or accepted or implemented or reviewed or null>`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `<provider or null>` | `<model or null>` | `<pane-id or null>` | `<session-id or null>` |
| Implementer | `<provider or null>` | `<model or null>` | `<pane-id or null>` | `<session-id or null>` |
| Reviewer | `<provider or null>` | `<model or null>` | `<pane-id or null>` | `<session-id or null>` |

## Scope

- In scope: `<bounded deliverables>`
- Authorized paths: `<paths or null>`
- Exclusive write ownership: `<paths or null>`
- Branch: `<branch or null>`
- Worktree: `<worktree identifier or null>`

## Non-goals

- Excluded work: `<items or null>`

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| `<criterion-id>` | `<pass or fail or pending or null>` | `<evidence or null>` |

## Verification

| Command | Result |
| --- | --- |
| `<command or null>` | `<pass or fail or unavailable or null>` |

## Implementation evidence

- Changed artifacts: `<paths or null>`
- Diff evidence: `<summary or command output or null>`
- Test evidence: `<summary or command output or null>`

## Review verdict

- Verdict: `<PASS or CHANGES REQUIRED or null>`
- Findings: `<findings or null>`

## Risks and open decisions

- Risks: `<risks or null>`
- Open decisions: `<decisions or null>`

## Cleanup status

- Brida-owned panes closed: `<yes or no or null>`
- Project memory updated: `<yes or no or null>`
