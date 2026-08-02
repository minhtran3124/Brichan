# TDW-005 implementation task packet

You are a worker agent coordinated by Brichan, an AI Chief of Staff acting on
the user's behalf.

## Task ID

`TDW-005`

## Objective

Implement the checkout-only full-document task-dossier contract, templates,
validation, and tests needed to run Level 0/1/2 workflow pilots.

## Context

The accepted direction is in
`projects/brida-task-dossier-workflow/plan.md`, with supporting research,
routing impact, and the user decision in the same project. Every tracked task
must have the same complete document set. Level changes evidence depth,
reviewer strength, and authorization gates—not artifact presence. File
presence alone is not evidence.

The baseline commit is `3df2ad29fc96d8b092f596e51934c02e50474946`.
`config/model-routing.json` contains a pre-existing user change and must remain
byte-identical.

## Upstream plan and receipt

- Accepted plan ID: `TDW-PLAN-001`
- Plan version: `1`
- Plan status: `accepted`
- Handoff receipt path:
  `projects/brida-task-dossier-workflow/handoffs/TDW-005/receipt.md`
- Receipt requirement: `mandatory`

## In scope

- Canonical checkout-mode workflow contract and full template set for
  `index.md`, `request.md`, `requirements.md`, `brief.md`, `options.md`,
  `design.md`, `client-follow-up-questions.md`, `plan.md`, `plan-review.md`,
  `code-review.md`, and `pr-desc.md`.
- Integration with canonical operating/reviewer policy and the checkout Herdr
  skill without duplicating active defaults.
- A dependency-free validator and, if needed for repeatable pilots, a
  dry-run-first scaffolding helper.
- Validation of task identity, level, phase/applicability state, version,
  evidence/uncertainty, model/session provenance, review verdicts, canonical
  receipt linkage, and complete artifact presence.
- Regression, contract, integration, repository-path, and documentation tests.
- Documentation explaining Level 0/1/2 depth and routing-neutral behavior.

## Authorized paths

- `docs/policy/operating-principles.md`
- `docs/policy/reviewer.md`
- `docs/workflows/**`
- `.agents/skills/herdr-orchestration/**`
- `src/brichan/contracts/**`
- `scripts/**task*dossier*`
- `tests/unit/**task*dossier*`
- `tests/contract/**task*dossier*`
- `tests/integration/**task*dossier*`
- `config/repository-paths.json`
- `Makefile`
- `CONTRIBUTING.md`
- `docs/index.md`

## Out of scope

- Installed `.brichan` schema or packaged `dogfood_v1` resources.
- `config/model-routing.json`.
- Project memory, handoff task packet, or receipt files.
- Sample Level 0/1/2 pilot dossiers; the coordinator creates those after
  implementation review.
- Publishing, deployment, remote state, secrets, or permission changes.
- Native delegation or non-Herdr workers.

## Deliverables

- Implementation diff confined to authorized paths.
- Tests demonstrating the full-doc and evidence contract.
- Final report with changed paths, commands/results, limitations, and any
  product decisions that remain unresolved.

## Acceptance criteria

- `TDW-005-AC1`: Every tracked task requires all eleven standard artifacts and
  a canonical receipt; missing or empty placeholders fail validation.
- `TDW-005-AC2`: `not-required` is accepted only with rationale and evidence.
- `TDW-005-AC3`: Model-authored/reviewed artifacts record session identity,
  effective route/model/effort, uncertainty, applicability, and version/origin.
- `TDW-005-AC4`: Level 0/1/2 share artifact presence while differing in evidence
  depth, reviewer strength, and authorization gates.
- `TDW-005-AC5`: The workflow remains routing-neutral and does not change the
  four-route routing schema or the dirty checkout routing file.
- `TDW-005-AC6`: Request provenance is read-only/redacted, accepted plans are
  versioned, reviewers do not back-write plans, and PR text never authorizes
  remote action.
- `TDW-005-AC7`: Existing receipt/project-memory authorities remain canonical;
  the dossier index links rather than duplicates them.
- `TDW-005-AC8`: Focused tests and full `make check` pass.
- `TDW-005-AC9`: Installed schema/resources remain unchanged.

## Required verification

- Focused unit/contract/integration tests for the new behavior.
- Negative tests for missing artifacts, empty placeholders, unsupported status,
  missing evidence, stale plan version, missing/failing review, unsafe request
  provenance, and unauthorized ship state.
- `python3 scripts/validate_handoff_receipts.py projects`
- `make path-check`
- `make check`
- `git diff --check`
- Diff confirming `config/model-routing.json` and
  `src/brichan/resources/dogfood_v1/` are untouched by the implementation.

## Constraints

- Do not spawn sub-agents or delegate this task.
- Do not broaden permissions or access secrets.
- Do not modify files outside the authorized scope.
- Do not commit, publish, deploy, or modify remote state.
- Do not modify Brichan project memory or handoff artifacts.
- Preserve existing unrelated working-tree changes.

## Escalate when

- The accepted full-doc contract conflicts with a canonical invariant that
  cannot be preserved.
- The smallest correct implementation requires installed schema changes.
- Acceptance criteria conflict or require a user-level compatibility,
  authority, security, or cost decision.

## Final response

1. Outcome.
2. Files/artifacts changed.
3. Verification and evidence.
4. Risks, assumptions, and unresolved issues.
