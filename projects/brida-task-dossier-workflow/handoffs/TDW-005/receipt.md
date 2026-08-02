# Handoff receipt

This standalone receipt records implementation of the checkout-only full-doc
task-dossier contract.

## Identity

- Receipt schema version: `2`
- Task ID: `TDW-005`
- Project: `brida-task-dossier-workflow`
- Handoff timestamp (UTC): `2026-08-02T03:47:12Z`
- Receipt role: `standalone`
- Parent receipt path: `null`
- Attempt: `1`
- Replaces session: `null`
- Attempt origin: `initial`
- Attempt lifecycle state: `complete`
- Prior attempt state: `null`
- Replacement evidence path: `null`

## Plan version

- Artifact or plan ID: `TDW-PLAN-001`
- Version: `1`
- Status: `reviewed`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `codex` | `gpt-5.6-sol` | `w2D:p1` | `019fbffa-7c8c-7eb1-b03a-fe86208bd015` |
| Implementer | `claude` | `claude-opus-5` | `w2D:p5` | `429445d9-3f2a-4d3c-9c87-63f51755a9a7` |
| Reviewer | `codex` | `gpt-5.6-sol` | `w2D:p6` | `019fc0a4-188e-7e91-91b1-22436b4fd951` |

## Scope

- In scope: `checkout full-doc workflow contract, templates, validator/helper, policy integration, and tests`
- Authorized paths: `docs/policy/operating-principles.md; docs/policy/reviewer.md; docs/workflows/**; .agents/skills/herdr-orchestration/**; src/brichan/contracts/**; scripts/**task*dossier*; tests/**task*dossier*; config/repository-paths.json; Makefile; CONTRIBUTING.md; docs/index.md`
- Exclusive write ownership: `implementation worker owns authorized implementation paths; coordinator owns project memory and handoff files`
- Branch: `feat/full-doc-task-workflow`
- Worktree: `primary checkout`

## Non-goals

- Excluded work: `installed schema/resources; routing config; pilot dossiers; publishing; deployment; remote state`

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| `TDW-005-AC1` | `pass` | `eleven templates plus receipt linkage; missing, empty, placeholder, and symlink tests pass` |
| `TDW-005-AC2` | `pass` | `not-required rationale and concrete-evidence tests pass` |
| `TDW-005-AC3` | `pass` | `model/session/route/model/effort provenance tests pass` |
| `TDW-005-AC4` | `pass` | `all levels share eleven artifacts; evidence thresholds 1/2/3 are tested` |
| `TDW-005-AC5` | `pass` | `routing-neutral contract tests pass; pre-existing routing diff remains excluded` |
| `TDW-005-AC6` | `pass` | `request immutability, plan version, independent review, and remote-action guard tests pass` |
| `TDW-005-AC7` | `pass` | `index links canonical receipt and cannot duplicate receipt-owned authority` |
| `TDW-005-AC8` | `pass` | `96 focused tests and full make check pass` |
| `TDW-005-AC9` | `pass` | `installed resource diff is empty and installed-resource contract test passes` |

## Verification

| Command | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.unit.test_task_dossier_validator tests.contract.test_task_dossier_contract tests.integration.test_task_dossier_workflow` | `PASS; 96 tests` |
| `python3 scripts/validate_handoff_receipts.py projects` | `PASS; 36 canonical receipts` |
| `make path-check` | `PASS; 71 entries and 64 references` |
| `make check` | `PASS; unit, contract, integration, metrics, receipt, dossier, path, packaging, and shell gates` |
| `git diff --check` | `PASS` |

## Implementation evidence

- Changed artifacts: `checkout workflow policy and docs; eleven templates; task-dossier schema/parser/validator/scaffolder; wrappers; repository manifest; Makefile integration; unit/contract/integration tests`
- Diff evidence: `implementation is confined to the receipt-authorized paths; config/model-routing.json remains a pre-existing user diff and src/brichan/resources/dogfood_v1 has no diff`
- Test evidence: `96 focused tests pass; make check passes with 234 unit, 61 contract, and 53 integration tests; receipt and repository path validation pass`

## Review verdict

- Verdict: `PASS`
- Findings: `initial and residual findings were remediated; final independent probes passed for traversal, symlinks and write races, completion/review/authorization gates, partial adoption, exact authority links, placeholder evidence, and closed index projection`

## Risks and open decisions

- Risks: `full-doc ceremony; duplicate truth; checkout and installed policy divergence`
- Open decisions: `adoption is gated by index.md so 36 historical receipt-only handoffs remain valid; checkout-only templates remain intentionally unpackaged`

## Cleanup status

- Brida-owned panes closed: `yes`
- Project memory updated: `yes`
