# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `WFS-005`
- Task level: `2`
- Artifact: `plan`
- Artifact version: `2`
- Origin: `wfs-005-plan-worker:2026-09-26:v2`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `plan-session-17f97686`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `WFS-005-PLAN-001`
- Plan status: `draft`

## Version history

- Version 1 raised one escalation (`CHANGELOG.md` outside the Techstack
  scope) and is archived byte-frozen at `versions/v1/plan.md` per the
  dossier contract; it is review evidence and is never edited.
- Version 2 (this document) incorporates the coordinator's resolution:
  `CHANGELOG.md` is now inside the re-resolved Snapshot scope
  (attempt `attempt-plan-2`, plan version 2). The step sequence,
  verification, and risks are otherwise unchanged from version 1.

## Techstack scope acknowledgement (attempt-plan-2)

- Snapshot pointer: `projects/brida-workflow-simplification/handoffs/WFS-005/snapshots/attempt-plan-2-912216e4b4070c6b23aa2a5a78cb73c38d15be3a73a93886d9056d2d716cbbfd.snapshot.json`
- Snapshot SHA-256: `912216e4b4070c6b23aa2a5a78cb73c38d15be3a73a93886d9056d2d716cbbfd`,
  verified `match` on 2026-09-26 before this version was written.
- Final scope paths (all files this plan touches are inside them):
  `.agents/skills/herdr-orchestration`, `CHANGELOG.md`, `docs/policy`,
  `docs/workflows`, `projects/brida-workflow-simplification/handoffs/WFS-005`,
  `scripts`, `src/brichan/contracts/task_dossier`, `tests/contract`,
  `tests/integration`, `tests/unit`.
- Acknowledged Context IDs: `root`, `general`, `policy`, `policy-canonical`,
  `policy-dossiers`, `policy-packaged`, `python`, `python-runtime`,
  `python-scripts`, `python-tests`.
- Selected rule files, each reread in full after the re-resolution:
  `techstacks/README.md`, `techstacks/general.md`,
  `techstacks/policy/README.md`, `techstacks/policy/canonical.md`,
  `techstacks/policy/packaged-resources.md`,
  `techstacks/policy/task-dossiers.md`, `techstacks/python/README.md`,
  `techstacks/python/runtime.md`, `techstacks/python/scripts.md`,
  `techstacks/python/tests.md`.
- Declared conflicts: none. Exception approvals: none.

## Step sequence

Each step lands its tests with its change (GENERAL-004, TEST-003: every
rejection test calls the production path and fails with the guard removed).
Design section 7 numbers the tests; steps below name which they land.

- S1 — Schema and template. Add `report` to `ARTIFACTS`, `ARTIFACT_TITLES`,
  `ARTIFACT_OWNERS`; add `REPORT_SECTIONS`, `LEVEL_REQUIRED_ARTIFACTS`,
  `CONTRACT_PATH_PREFIXES`, `CONTRACT_PATH_FILES` to
  `src/brichan/contracts/task_dossier/schema.py`; create
  `docs/workflows/task-dossier/templates/report.md`. Extend the template
  contract test to the twelve recognized artifacts. Lands tests 17 (pins,
  code side) and the template half of 12.
- S2 — Validator. Implement design section 4's `validation.py` changes:
  level-aware required-set loading, report structure and passed-phase
  concreteness, Level 1/2 mandatory code-review applicability, report-based
  review independence, null review targets without a plan, status-table
  required-union-present rule, completion narrowing. Lands tests 1-11
  (validator side), including the legacy-fixture no-migration guard (8) and
  the partial-adoption guard (9).
- S3 — Scaffold. Level-keyed iteration in `scaffold.py`; integration-test
  updates for level 0/1/2 scaffolding. Lands test 12.
- S4 — Record and generator. Monotone key rule, conditional cross-checks,
  report-aware independence, null review targets, record-keyed rendering and
  status table in `record.py` and `generate.py`. The frozen eleven-artifact
  Level 1 fixture is not edited. Lands tests 13-14.
- S5 — Summary. Roster and unreadable-row changes in `summary.py`. Lands
  test 15.
- S6 — Contract-path checker. New
  `src/brichan/contracts/task_dossier/contract_paths.py` and
  `scripts/check_contract_paths.py` wrapper (19-line pattern); new
  `tests/unit/test_contract_paths.py`. Lands test 16.
- S7 — Documents. Rewrite `docs/workflows/task-dossier.md` per design
  sections 1-3 (preserving the pinned needles named in design section 6);
  update `docs/policy/operating-principles.md` section 2 to reference the
  workflow document; add the reviewer rule and amended return item to
  `docs/policy/reviewer.md`; update
  `.agents/skills/herdr-orchestration/references/task-dossier.md` and
  `SKILL.md` wording without touching any parity marker or packet label.
  Update `tests/contract/test_task_dossier_contract.py` needles and add the
  document-side pins and the reviewer-rule needle. Lands tests 17-18 (doc
  side).
- S8 — Records. Add the `CHANGELOG.md` Unreleased entry (Changed): the
  level-keyed dossier contract and the reviewer rule. In scope as of
  Snapshot attempt `attempt-plan-2`; the version 1 escalation is resolved.
- S9 — End-to-end and full verification (below), then the worker report,
  diff, and evidence for the completion gate.

## Verification

- Per step: the step's own unit or contract tests via
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest <module>`.
- Full gate, both interpreters (TEST-001, GENERAL-001):
  - `PYTHONDONTWRITEBYTECODE=1 make check`
  - `PYTHONDONTWRITEBYTECODE=1 make check PYTHON=/opt/homebrew/bin/python3.14`
  - the techstack eval run directly under 3.14 as well, because its recipe
    does not follow `PYTHON=` (SCRIPT-003 note in the Makefile docs).
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py
  projects` must report no diagnostic for any pre-existing dossier
  (acceptance A3). While WFS-005 itself is in flight, `make dossiers` and
  `tests/integration/test_task_dossier_workflow.py`
  `test_repository_checkout_validates_clean` may be red only because of
  WFS-005's own pending coordinator or reviewer artifacts; any other red is
  a defect in the change.
- `git diff --stat` over the implementation shows nothing under
  `src/brichan/resources/`, `PRODUCT.md`, `config/`, or `techstacks/`
  (acceptance A5; installed mode and packaged resources byte-unchanged).
- `git status` confirms the unrelated `.codex/config.toml` modification and
  the untracked `.brichan` backup directories are untouched.
- No commit, push, or other remote action: the implementation stays in the
  working tree of branch `feat/lifecycle-simplification` for the coordinator
  to review and the user to land through a pull request.

## Risks and mitigations

- Doc-needle breakage: `test_task_dossier_contract.py` pins exact strings
  including a line wrap; design section 6 names each, and S7 runs that test
  file before the full gate.
- Parity regression: the `.agents/` edits are word-level and avoid every
  `PARITY_MARKERS` phrase; `make test-contract` in S7 is the guard.
- Legacy breakage: test 8 validates an unmodified existing-dossier fixture;
  additionally S2 ends with the projects-root validator run over the real
  `projects/` tree.
- Concurrent dossier state: WFS-005's own dossier is in flight during
  implementation, so completion-gate reds must be checked against the
  expected-red list above rather than silenced.
- Evidence-base thinness: three tasks, one run per arm. The protocol's
  stop-and-rollback rule (an escaped defect that the removed ceremony would
  have caught returns that level to the full lifecycle and supersedes the
  decision) stays in force and is restated in the workflow document.

## Claim or decision

Implementation proceeds in nine steps, tests landing with each change, gated
by `make check` on Python 3.10 and 3.14. The version 1 escalation is
resolved: `CHANGELOG.md` is inside the re-resolved attempt-plan-2 Snapshot
scope, so no path this plan touches is outside the declared scope and
nothing blocks acceptance of this plan version on scope grounds.

## Evidence

- The attempt-plan-2 verify command returned `match` with digest
  `912216e4b4070c6b23aa2a5a78cb73c38d15be3a73a93886d9056d2d716cbbfd` on
  2026-09-26, and its resolved scope paths include `CHANGELOG.md`; all ten
  selected rule files were reread after the re-resolution as required.
- `versions/v1/plan.md` holds the byte-frozen version 1 (identical SHA-256
  to the pre-archive `plan.md` v1, verified at archive time), preserving the
  escalation record per the dossier contract.
- `design.md` v1 sections 4, 6, and 7 enumerate every touched function,
  file, and test this plan sequences; the design was grounded in a full read
  of the six contract-package modules on 2026-09-26.
- `Makefile` targets `check`, `dossiers`, and the test tiers were read to
  confirm the verification commands and the SCRIPT-003 eval note.

## Uncertainty

- The contract-path list membership question recorded in `design.md`'s
  Uncertainty section remains open for plan review; it does not block the
  step sequence, which treats the list as one literal to fill. The version 1
  scope escalation is resolved and no scope uncertainty remains.
