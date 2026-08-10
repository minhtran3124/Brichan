## Identity

- Receipt schema version: `2`
- Task ID: `MEMORY-001`
- Project: `brida-installable-tool`
- Handoff timestamp (UTC): `2026-08-09T16:22:39Z`
- Receipt role: `standalone`
- Parent receipt path: `null`
- Attempt: `2`
- Replaces session: `49c52563-1557-4351-ae69-8c36c8594bf6`
- Attempt origin: `replacement`
- Attempt lifecycle state: `complete`
- Prior attempt state: `abandoned`
- Replacement evidence path: `projects/brida-installable-tool/tasks.md`

## Plan version

- Artifact or plan ID: `MEMORY-001-PLAN`
- Version: `6`
- Status: `reviewed`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `claude` | `claude-opus-5[1m]` | `w34:p2` | `65f9eedd-94f2-489d-ad67-4e0edf5caf30` |
| Implementer | `codex` | `gpt-5.6-sol` | `w34:pA` | `019fe761-ed12-7560-bbdb-c388ba100c0d` |
| Plan reviewer | `codex` | `gpt-5.6-sol` | `w34:p8` | `019fe74e-6797-7313-b931-8e9794621cc6` |
| Code reviewer | `codex` | `gpt-5.6-sol` | `w34:pB` | `019fe769-cbd8-7bc3-b4fc-ec4604200b56` |

## Scope

- In scope: Durable product/project-memory repair, packaged installed-policy consistency, VERSION-derived wheel guide, release-memory checklist, read-only project-memory checker, tests, Makefile gate, and repository-path inventory.
- Authorized paths: The exact paths listed in `projects/brida-installable-tool/handoffs/MEMORY-001/plan.md` version 6.
- Exclusive write ownership: One implementation worker owns implementation paths; coordinator/reviewers own dossier and task-memory artifacts.
- Branch: `fix/durable-memory-consistency`
- Worktree: `primary`

## Non-goals

- Excluded work: VERSION bump, changelog rewrite, tag, push, pull request, publishing, external dogfood, network access, secrets, deployment, permission broadening, generated-artifact deletion, or unrelated history edits.

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| AC-1 | `pass` | Product, packaged policy, project memory, guide, and release checklist match plan version 6. |
| AC-2 | `pass` | The six checker invariants, deterministic diagnostics, exit 0/1, read-only/offline behavior, and 26 focused regression tests pass. |
| AC-3 | `pass` | Makefile/path-manifest wiring and the checked-in repository contract pass; `make check` is green. |
| AC-4 | `pass` | Independent code review version 2 returns PASS and the full local gate passes. |

## Verification

| Command | Result |
| --- | --- |
| `python3 scripts/check_project_memory.py` | `pass` |
| Focused unit and contract tests | `pass` |
| `python3 scripts/validate_task_dossiers.py projects --require-complete` | `pass` |
| `python3 scripts/validate_handoff_receipts.py projects` | `pass` |
| `make check` | `pass` |

## Implementation evidence

- Changed artifacts: Attempt 2 audited and completed the preserved partial diff, adding the checker tests, Makefile gate, and repository-path manifest entries while retaining the authorized product, memory, guide, release-checklist, and installed-policy repairs.
- Diff evidence: The implementation worker reported 19 non-dossier paths, all authorized by plan version 6; excluded-path drift was empty and `git diff --check` passed.
- Test evidence: Focused 27-test coverage, 400 unit tests, 79 contract tests, 90 integration tests, `memory-check`, `path-check`, dossier/receipt validation, and full `make check` passed. Independent code review version 2 returned PASS.

## Review verdict

- Verdict: `PASS`
- Findings: Review version 1 found two medium and one low issue; the replacement implementer remediated all three in the authorized checker/unit-test paths, and review version 2 verified every finding closed with no new issue.

## Risks and open decisions

- Risks: Attempt 1 was abandoned after three recorded no-progress observations in `projects/brida-installable-tool/tasks.md`. The packaged policy correction is unreleased without a version bump; deliberate re-init will observe the resource hash change. Path validation is point-in-time and does not defend against same-identity concurrent replacement.
- Open decisions: No implementation decision is open. Remote and release actions remain unauthorized.

## Cleanup status

- Brida-owned panes closed: `yes`
- Project memory updated: `yes`
