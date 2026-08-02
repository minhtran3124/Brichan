# Handoff receipt

## Identity

- Receipt schema version: `2`
- Task ID: `SYNTH-011`
- Project: `synthetic-level1`
- Handoff timestamp (UTC): `2026-08-02T00:00:00Z`
- Receipt role: `parent`
- Parent receipt path: `null`
- Attempt: `1`
- Replaces session: `null`
- Attempt origin: `initial`
- Attempt lifecycle state: `complete`
- Prior attempt state: `null`
- Replacement evidence path: `null`

## Plan version

- Artifact or plan ID: `SYNTH-011-P1`
- Version: `1`
- Status: `accepted`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `synthetic` | `synthetic-fixture-model` | `w0:p0` | `synthetic-fixture-planner-0002` |
| Reviewer | `synthetic` | `synthetic-fixture-model` | `w0:p1` | `synthetic-fixture-reviewer-0002` |

## Scope

- In scope: `synthetic non-authoritative fixture dossier for the TDW-009 concise evaluation`
- Authorized paths: `evals/task-dossier-pilots/concise/projects/synthetic-level1/handoffs/SYNTH-011`
- Exclusive write ownership: `the TDW-009 evaluation only`
- Branch: `feat/full-doc-task-workflow`
- Worktree: `primary checkout`

## Non-goals

- Excluded work: `any real implementation, review, routing, or remote action`

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| `SYNTH-011-AC1` | `pass` | `eleven generated artifacts validate under the complete gate` |

## Verification

| Command | Result |
| --- | --- |
| `python3 scripts/validate_task_dossiers.py evals/task-dossier-pilots/concise/projects --require-complete` | `pass` |

## Implementation evidence

- Changed artifacts: `eleven generated dossier artifacts for SYNTH-011`
- Diff evidence: `evals/task-dossier-pilots/concise/records/SYNTH-011.record.json`
- Test evidence: `evals/task-dossier-pilots/concise/results.md`

## Review verdict

- Verdict: `null`
- Findings: `null; this synthetic fixture records no review verdict, and none of its identifiers is evidence of a real independent review`

## Risks and open decisions

- Risks: `a reader could mistake this synthetic fixture for real review evidence`
- Open decisions: `none; this receipt is fixture data`

## Cleanup status

- Brida-owned panes closed: `yes`
- Project memory updated: `yes`
