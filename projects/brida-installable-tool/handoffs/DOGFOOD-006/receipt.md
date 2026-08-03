## Identity

- Receipt schema version: `2`
- Task ID: `DOGFOOD-006`
- Project: `brida-installable-tool`
- Handoff timestamp (UTC): `2026-08-03T05:05:30Z`
- Receipt role: `standalone`
- Parent receipt path: `null`
- Attempt: `1`
- Replaces session: `null`
- Attempt origin: `initial`
- Attempt lifecycle state: `complete`
- Prior attempt state: `null`
- Replacement evidence path: `null`

## Plan version

- Artifact or plan ID: `DOGFOOD-006-P1`
- Version: `3`
- Status: `reviewed`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `claude` | `claude-fable-5` | `w2D:pF` | `98e27c66-74a6-4fdc-bbc6-614ebf8a225e` |
| Implementer | `claude` | `claude-opus-5` | `w2D:pH` | `64ee8850-4eee-48d3-9689-3b7305ce32d1` |
| Reviewer | `codex` | `gpt-5.6-sol` | `w2D:pJ` | `019fc5f3-766d-74a2-8848-fce011562f93` |

## Scope

- In scope: Read-only `doctor --json` diagnostics for source checkouts and
  installed projects, exact JSON schema, exit compatibility, unit/integration
  tests, documentation, and adversarial safety coverage.
- Authorized paths: `src/brichan/lifecycle.py`, `src/brichan/cli/runtime.py`,
  `src/brichan/cli/render.py`, the authorized lifecycle/CLI integration and
  unit tests, and `docs/guides/installable-dogfood.md`.
- Exclusive write ownership: implementation worker owned source/test/docs paths;
  coordinator owned dossier and project-memory paths.
- Branch: `feat/full-doc-task-workflow`
- Worktree: `primary`

## Non-goals

- Excluded work: Routing-manifest changes, packaged resources, installed schema
  changes, Herdr invocation, credentials, deployment, push, PR, or remote state.

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| AC-1 | `pass` | Source checkout emits exact eight-key deterministic JSON report covering repository, Git, policies, routing, memory, and dependencies. |
| AC-2 | `pass` | Installed-project JSON preserves state exits 0/1/2/3/4 and no-follow state semantics. |
| AC-3 | `pass` | Git argv spy, Herdr non-execution checks, worktree/index snapshots, symlink probes, and invalid-UTF-8 probe pass. |
| AC-4 | `pass` | Unit/CLI/integration tests and installable-dogfood documentation updated; independent remediation review returns PASS. |

## Verification

| Command | Result |
| --- | --- |
| `git diff --check` | `pass` |
| Focused lifecycle/CLI/integration tests | `pass` |
| Symlink and invalid-UTF-8 adversarial probes | `pass` |
| `make check` | `pass` |

The full check was run from a clean generated-artifact state; the pre-existing
ignored `src/brichan.egg-info` was moved aside temporarily and restored after
the command.

## Implementation evidence

- Changed artifacts: `src/brichan/lifecycle.py`, `src/brichan/cli/runtime.py`,
  `src/brichan/cli/render.py`, lifecycle/CLI integration and unit tests, and
  `docs/guides/installable-dogfood.md`.
- Diff evidence: Structured source/installed report collector, deterministic
  JSON renderer, read-only Git queries, optional Herdr resolution, exact exit
  mapping, and no-follow/UTF-8 remediation.
- Test evidence: Focused report/render/CLI tests pass; direct checkout command
  exits 0 with valid JSON; remediation probes return exit 2 without traceback.

## Review verdict

- Verdict: `PASS`
- Findings: Initial review found H1 symlink traversal and M1 invalid-UTF-8
  traceback; both were remediated and independent version-2 re-review passed.

## Risks and open decisions

- Risks: The checkout contains a pre-existing/generated ignored
  `src/brichan.egg-info`; validation is sensitive to its presence, so the
  final check used a reversible temporary move. The dossier itself is
  coordinator-owned state.
- Open decisions: None. Push and PR remain unauthorized.

## Cleanup status

- Brida-owned panes closed: `yes`
- Project memory updated: `yes`
