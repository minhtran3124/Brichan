## Identity

- Receipt schema version: `2`
- Task ID: `DOGFOOD-005`
- Project: `brida-installable-tool`
- Handoff timestamp (UTC): `2026-07-29T15:25:00Z`
- Receipt role: `standalone`
- Parent receipt path: `null`
- Attempt: `1`
- Replaces session: `null`
- Attempt origin: `initial`
- Attempt lifecycle state: `complete`
- Prior attempt state: `null`
- Replacement evidence path: `null`

## Plan version

- Artifact or plan ID: `installer-pip-hardening`
- Version: `1`
- Status: `reviewed`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `null` | `null` | `null` | `null` |
| Implementer | `claude` | `sonnet` | `w1X:p3E` | `8bfb1356-15cb-4146-b01f-60491434ea41` |
| Reviewer | `claude` | `opus` | `w1X:p3D` | `a2c8068d-6f5b-4a4d-b34c-443c814babc7` |

## Scope

- In scope: Require build-interpreter `pip`, validate `pip` in a reused dedicated environment, align prerequisite docs, add focused regression coverage, and keep repository contract scans independent of a gitignored local `.venv`.
- Authorized paths: `scripts/install-brida`, `tests/integration/test_installed_dogfood.py`, `tests/contract/test_repository_contract.py`, `README.md`, `docs/guides/installable-dogfood.md`
- Exclusive write ownership: `scripts/install-brida`, `tests/integration/test_installed_dogfood.py`, `tests/contract/test_repository_contract.py`, `README.md`, `docs/guides/installable-dogfood.md`
- Branch: `cli`
- Worktree: `primary`

## Non-goals

- Excluded work: Other review findings, packaging architecture changes, commits, pushes, publishing, deployment, and writes outside disposable temporary directories.

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| AC-1 | `pass` | Focused integration test hides only `pip`; installer exits 2 with its own prerequisite message and no traceback. |
| AC-2 | `pass` | Focused integration test reuses a pip-less environment; installer exits 2 with the resolved path and non-destructive recovery guidance. |
| AC-3 | `pass` | Help, README, and dogfood guide name `pip`, `setuptools`, `venv`, and `wheel`; outside-checkout/no-activation test passes. |

## Verification

| Command | Result |
| --- | --- |
| `sh -n scripts/install-brida` | `pass` |
| focused integration tests | `pass` |
| `PYTHONDONTWRITEBYTECODE=1 make check` | `pass` |

## Implementation evidence

- Changed artifacts: `scripts/install-brida`, `tests/integration/test_installed_dogfood.py`, `tests/contract/test_repository_contract.py`, `README.md`, `docs/guides/installable-dogfood.md`
- Diff evidence: Build and reused-environment pip guards, two regression tests, prerequisite docs, and `.venv` exclusion in the repository-wide source scan.
- Test evidence: Three focused installer tests pass; repository contract module passes 16/16; full `make check` passes.

## Review verdict

- Verdict: `PASS`
- Findings: `F1 and F2 are remediated; M1 and M2 consistency follow-ups are closed; final independent re-review returned PASS.`

## Risks and open decisions

- Risks: Gitignored checkout `.venv/` provenance remains unexplained; it is outside the diff and cannot enter the wheel snapshot.
- Open decisions: Resolve local `.venv/` provenance before any future package publishing step.

## Cleanup status

- Brida-owned panes closed: `yes`
- Project memory updated: `yes`
