# Handoff receipt

This versioned planner-to-implementer/reviewer lifecycle envelope records a
bounded handoff and its receipt. Its section headings are contract-checked;
keep the headings unchanged and in this order. Use `null` when a value is
unknown or unavailable. Do not include personal or home paths.

Store each operational receipt at
`projects/<slug>/handoffs/<task-id>/receipt.md`. Add that repo-relative path to
the project's `references.md` so progressive memory can discover it.
Historical receipts under `evals/` remain evidence; do not migrate them, and
the canonical validator does not discover them by default.

Use `standalone` for a single-writer task, `parent` for the coordinating receipt
of a multi-writer task, and `child` for each writer receipt. A child names its
canonical parent receipt using a repo-relative path. Parent and standalone
receipts use `null`.

Attempt numbering starts at `1`, with `Replaces session` set to `null`. A later
attempt names the prior session it replaces.

An `accepted` receipt may keep implementation, verification, and review values
pending. An `implemented` receipt requires passing criteria and verification
plus concrete implementation evidence. A reviewed `PASS` additionally requires
cleanup and project memory to be complete. `CHANGES REQUIRED` remains valid
with actionable findings while remediation is active.

## Identity

- Receipt schema version: `1`
- Task ID: `<task-id>`
- Project: `<project-slug>`
- Handoff timestamp (UTC): `<ISO-8601 timestamp or null>`
- Receipt role: `<standalone, child, or parent>`
- Parent receipt path: `<repo-relative path or null>`
- Attempt: `<positive integer>`
- Replaces session: `<prior session identifier or null>`

## Plan version

- Artifact or plan ID: `<artifact-id or null>`
- Version: `<version or null>`
- Status: `<accepted, implemented, or reviewed>`

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
| `<command or null>` | `<pass, fail, pending, unavailable, or null>` |

## Implementation evidence

- Changed artifacts: `<paths, pending, or null>`
- Diff evidence: `<summary, command output, pending, or null>`
- Test evidence: `<summary, command output, pending, or null>`

## Review verdict

- Verdict: `<PASS, CHANGES REQUIRED, pending, or null>`
- Findings: `<findings, pending, or null>`

## Risks and open decisions

- Risks: `<risks or null>`
- Open decisions: `<decisions or null>`

## Cleanup status

- Brida-owned panes closed: `<yes or no or null>`
- Project memory updated: `<yes or no or null>`
