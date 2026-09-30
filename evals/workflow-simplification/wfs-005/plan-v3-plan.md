# Plan

Versioned execution plan. An accepted version is immutable; changes create a
new version.

## Artifact metadata

- Task ID: `WFS-005`
- Task level: `2`
- Artifact: `plan`
- Artifact version: `3`
- Origin: `wfs-005-plan-worker:2026-09-26:v3`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `plan-session-8ec2b29b`
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
  scope) and is archived byte-frozen at `versions/v1/plan.md`.
- Version 2 incorporated the coordinator's scope resolution and was reviewed
  by an independent plan review with verdict `CHANGES REQUIRED`
  (`versions/v2/plan-review.md`, also the live `plan-review.md`). Version 2
  and the version 1 planning artifacts it rested on are archived byte-frozen
  at `versions/v2/` (`plan.md`, `design.md`, `options.md`,
  `requirements.md`, `brief.md`); archived versions are review evidence and
  are never edited (DOSSIER-003).
- Version 3 (this document) closes every review finding. `requirements.md`,
  `brief.md`, `options.md`, and `design.md` are revised to version 2 in the
  same pass; the closure table below maps each finding to its resolution.

## Findings closure (plan review of version 2, verdict CHANGES REQUIRED)

| Finding | Severity | Resolution in version 3 | Where |
| --- | --- | --- | --- |
| C1 | Critical, blocking | Adopted the review's shape (a): at Levels 0/1 `report` is required only when the dossier has no `plan.md`, so all six existing Level 0/1 dossiers satisfy their level through `plan` with no edits and no exemption list; presence fails closed on a symlinked/unreadable plan. Committed regression tests cover the real legacy shapes at both levels (test 8a/8b), not one fixture. | `design.md` §3; `options.md` Decision 2; `requirements.md` R8; tests 8a, 8b |
| C2 | Critical, blocking | Adopted the review's recommended alternative: `ARTIFACTS` stays the frozen eleven; a new literal `RECOGNIZED_ARTIFACTS` (the eleven plus `report`, after `plan`) is what the validator, scaffold, generator, summary, and partial-adoption scan iterate. All four named assertions keep their meaning; nothing under `projects/brida-task-dossier-workflow` or `evals` changes; the index template keeps its eleven rows. The three template/constant assertions that must re-key are enumerated as edits. | `design.md` §3, §6; `options.md` Decision 6; test 18 |
| C3 | High, blocking | The fixture is correctly identified as the Level 0 record `SYNTH-010`; under the effective-required key rule (required set evaluated over the record's keys, so a record with `plan` needs no `report`), the frozen eleven-key fixture loads with no edit. The design states this rather than restating version 2's claim. | `design.md` §4 (generator), §8 item 4; test 14 |
| H1 | High, blocking | Resolved the template/status-table contradiction: the index template is not edited and its contract test stays keyed to `ARTIFACTS`; the scaffold generates status rows for exactly the artifacts it scaffolds per level (Level 2 output byte-identical to today's). A scaffold-fill-validate round trip at every level becomes a committed test. | `design.md` §4 (scaffold); `options.md` Decision 7; tests 12, 13 |
| M1 | Medium | Level resolution now fails closed: an unparseable level falls back to `"2"` (largest required set, deepest evidence floor) instead of `"0"`, with a committed test. No existing dossier declares an invalid level. | `design.md` §4; test 19 |
| M2 | Medium | Recorded mitigation as recommended: the canonical statement requires the index to record the level-fixing trigger or the recorded absence of every trigger, and `docs/policy/reviewer.md` names level mis-declaration a review finding. Stays documentary — the review agrees nothing mechanical can close it. | `design.md` §1, §5; `requirements.md` R13 |
| M3 | Medium | Adopted the recommended membership: prefixes `src/brichan/` and `scripts/` replace the narrower `src/brichan/contracts/` and `src/brichan/lifecycle.py` entries; `tests/` stays off. Recorded as a user-reversible judgment. | `design.md` §2; `options.md` Decision 3; test 17 |
| M4 | Medium | Committed fixtures per distinct legacy shape: the contract test validates the two committed full dossiers under `evals/task-dossier-pilots/concise` (`SYNTH-010` Level 0, `SYNTH-011` Level 1) expecting zero diagnostics, and `build_dossier`'s full-eleven shape is exercised at both reduced levels. The manual `projects` run is named a check, not the regression guard (TEST-004). | `design.md` §7 test 8; `requirements.md` R10, A2 |
| L1 | Low | The stale `schema.py` comment ("It never changes which artifacts must exist.") is on the S1 file list to correct. | `design.md` §6; step S1 |
| L2 | Low | Dissolved by the C1+C2 shapes: the concise samples stay contract-valid with no edit (re-verified: the validator over `evals/task-dossier-pilots/concise/projects` exits 0 today), and test 8b pins them so a regression cannot land unnoticed. Nothing under `evals/` changes. | `design.md` §6, §7 test 8b |
| L3 | Low | Self-corrected by C2's resolution: every path this plan touches is inside the declared scope, and the claim below is now true as written. | This document, Claim |
| L4 | Low | The parity claim is restated at the strength the evidence supports: the guard is running `make test-contract` after S7 (the parity check compares whole trees), not a claim that the edited wording avoids every marker word. | `design.md` §6, Uncertainty |

The review's test-gap notes are also addressed: the round trip (tests 12-13)
closes the unvalidated-scaffold gap, test 8b pins the concise samples, and
the Level 0 review decision's trust boundary is named in the workflow
document (`design.md` §1).

## Techstack scope acknowledgement (attempt-plan-3)

- Snapshot pointer: `projects/brida-workflow-simplification/handoffs/WFS-005/snapshots/attempt-plan-3-07d0a9aa66386b05d94d37a06d4f414b7c83be1bbeee24f5c9647ce2a61079f6.snapshot.json`
- Snapshot SHA-256: `07d0a9aa66386b05d94d37a06d4f414b7c83be1bbeee24f5c9647ce2a61079f6`,
  verified `match` on 2026-09-26 before this version was written.
- Final scope paths (all files this plan touches are inside them):
  `.agents/skills/herdr-orchestration`, `CHANGELOG.md`, `docs/policy`,
  `docs/workflows`, `projects/brida-workflow-simplification/handoffs/WFS-005`,
  `scripts`, `src/brichan/contracts/task_dossier`, `tests/contract`,
  `tests/integration`, `tests/unit`.
- Acknowledged Context IDs: `root`, `general`, `policy`, `policy-canonical`,
  `policy-dossiers`, `policy-packaged`, `python`, `python-runtime`,
  `python-scripts`, `python-tests`.
- Selected rule files, each read in full under this attempt:
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

- S1 — Schema and template. Add `RECOGNIZED_ARTIFACTS`,
  `LEVEL_REQUIRED_ARTIFACTS`, `REPORT_SECTIONS`, `CONTRACT_PATH_PREFIXES`,
  `CONTRACT_PATH_FILES`, and the `report` entries of `ARTIFACT_TITLES` and
  `ARTIFACT_OWNERS` to `src/brichan/contracts/task_dossier/schema.py`,
  leaving `ARTIFACTS` byte-unchanged and correcting the stale
  level-never-changes-presence comment (L1); create
  `docs/workflows/task-dossier/templates/report.md`. Re-key the three
  template/constant contract assertions to `RECOGNIZED_ARTIFACTS` and land
  the tuple pin. The index template is not touched. Lands test 18 (code
  side) and the template halves of tests 12 and 18.
- S2 — Validator. Implement design section 4's `validation.py` changes:
  recognized-set loading, effective required set with the legacy
  `plan`-satisfies rule, fail-closed `"2"` level fallback, report structure
  and passed-phase concreteness, Level 1/2 mandatory code-review
  applicability, report-based review independence, null review targets
  without a plan, status-table required-union-present rule, completion
  narrowing. Lands tests 1-11 and 19, including both legacy no-migration
  guards (8a in the unit suite, 8b in the contract suite) and the
  partial-adoption guard (9).
- S3 — Scaffold. Level-keyed iteration plus generated status rows in
  `scaffold.py`; integration-test updates for level 0/1/2 scaffolding and
  the scaffold-fill-validate round trip at every level. Lands tests 12-13.
- S4 — Record and generator. Effective-required key rule against
  `RECOGNIZED_ARTIFACTS`, conditional cross-checks, report-aware
  independence, null review targets, record-keyed rendering and status table
  in `record.py` and `generate.py`. The frozen eleven-artifact Level 0
  fixture is not edited and must keep loading. Lands tests 14-15.
- S5 — Summary. Roster and unreadable-row changes in `summary.py`. Lands
  test 16.
- S6 — Contract-path checker. New
  `src/brichan/contracts/task_dossier/contract_paths.py` and
  `scripts/check_contract_paths.py` wrapper (19-line pattern); new
  `tests/unit/test_contract_paths.py`. Lands test 17.
- S7 — Documents. Rewrite `docs/workflows/task-dossier.md` per design
  sections 1-4 (preserving the pinned needles named in design section 6,
  adding the legacy rule, the level-determination evidence obligation, and
  the named contract-path trust boundary); update
  `docs/policy/operating-principles.md` section 2 to reference the workflow
  document; add the reviewer rule, amended return item, and the
  level-mis-declaration and contract-path sentences to
  `docs/policy/reviewer.md`; update
  `.agents/skills/herdr-orchestration/references/task-dossier.md` and
  `SKILL.md` wording without editing any parity marker or packet label.
  Update `tests/contract/test_task_dossier_contract.py` needles and add the
  document-side pins and the reviewer-rule needle, then run `make
  test-contract` (the parity guard, L4). Lands tests 18 (doc side) and 20.
- S8 — Records. Add the `CHANGELOG.md` Unreleased entry (Changed): the
  level-keyed dossier contract and the reviewer rule. In scope since
  Snapshot attempt `attempt-plan-2`, unchanged in `attempt-plan-3`.
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
  (acceptance A3). This run is a check; the committed regression guards for
  the same guarantee are tests 8a and 8b (TEST-004: the `projects/` dossiers
  are gitignored and never the sole owner of a gate assertion). While
  WFS-005 itself is in flight, `make dossiers` and
  `tests/integration/test_task_dossier_workflow.py`
  `test_repository_checkout_validates_clean` may be red only because of
  WFS-005's own pending coordinator or reviewer artifacts; any other red is
  a defect in the change.
- `git diff --stat` over the implementation shows nothing under
  `src/brichan/resources/`, `PRODUCT.md`, `config/`, `techstacks/`,
  `evals/`, or `projects/` outside this task's dossier (acceptance A5;
  installed mode and packaged resources byte-unchanged; C2's no-edit
  guarantee for other tasks' artifacts and the eval fixtures).
- `git status` confirms the unrelated `.codex/config.toml` modification and
  the untracked `.brichan` backup directories are untouched.
- No commit, push, or other remote action: the implementation stays in the
  working tree of branch `feat/lifecycle-simplification` for the coordinator
  to review and the user to land through a pull request.

## Risks and mitigations

- Doc-needle breakage: `test_task_dossier_contract.py` pins exact strings
  including a line wrap; design section 6 names each, and S7 runs that test
  file before the full gate.
- Parity regression: the `.agents/` edits are word-level; because
  `PARITY_MARKERS` contains bare generic words, the guard is `make
  test-contract` in S7 over the whole concatenated trees, not any
  word-avoidance claim (L4).
- Legacy breakage: tests 8a and 8b validate committed full-dossier shapes at
  both reduced levels; additionally S2 ends with the projects-root validator
  run over the real `projects/` tree as a check.
- Scaffold/validator drift: the two now share the level-keyed sets and the
  round trip (test 13) fails if their status-table or required-set rules
  ever disagree (H1's class of defect).
- Concurrent dossier state: WFS-005's own dossier is in flight during
  implementation, so completion-gate reds must be checked against the
  expected-red list above rather than silenced.
- Evidence-base thinness: three tasks, one run per arm. The protocol's
  stop-and-rollback rule (an escaped defect that the removed ceremony would
  have caught returns that level to the full lifecycle and supersedes the
  decision) stays in force and is restated in the workflow document.

## Claim or decision

Implementation proceeds in nine steps, tests landing with each change, gated
by `make check` on Python 3.10 and 3.14. Every blocking finding (C1, C2, C3,
H1) is resolved with the plan review's preferred shapes; M1-M4 are adopted
as recommended and L1-L4 are corrected or dissolved, per the closure table.
No path this plan touches is outside the declared attempt-plan-3 scope —
in particular, nothing under `projects/brida-task-dossier-workflow`,
`evals/`, or the index template changes — and no escalation is open.

## Evidence

- The attempt-plan-3 verify command returned `match` with digest
  `07d0a9aa66386b05d94d37a06d4f414b7c83be1bbeee24f5c9647ce2a61079f6` on
  2026-09-26 before any artifact was revised, and all ten selected rule
  files were read in full under this attempt.
- `versions/v2/plan-review.md` (identical to the live `plan-review.md`,
  reviewed plan version 2, verdict `CHANGES REQUIRED`) states findings
  C1-C3, H1, M1-M4, and L1-L4 with the recommended shapes this version
  adopts; the coordinator's plan-version-3 packet names those shapes as
  preferred.
- `versions/v2/` holds the byte-frozen superseded planning artifacts
  (SHA-256 of each archived file verified identical to its pre-revision
  live copy at archive time on 2026-09-26), and `versions/v1/plan.md`
  remains the frozen version 1 escalation record (DOSSIER-003).
- The claims the closure table rests on were re-verified against the tree by
  this session on 2026-09-26: the six Level 0/1 dossiers and their `plan.md`
  and `required` reviews; the fixture load site
  (`tests/unit/test_task_dossier_generator.py:76-82`, `level="0"`); the four
  `ARTIFACTS`-pinned assertions and the three to re-key in
  `tests/contract/test_task_dossier_contract.py`; the clean validator run
  over `evals/task-dossier-pilots/concise/projects` (exit 0, "Validated 2
  task dossier(s)"); and `_resolve_level`'s current `"0"` fallback
  (`src/brichan/contracts/task_dossier/validation.py:1035-1048`).
- `design.md` v2 sections 4, 6, and 7 enumerate every touched function,
  file, and test this plan sequences; `Makefile` targets `check`,
  `dossiers`, and the test tiers were previously read to confirm the
  verification commands and the SCRIPT-003 eval note, and the plan review
  independently verified both.

## Uncertainty

- The contract-path membership adopts the review's M3 recommendation; the
  user may prefer the narrower list, and swapping membership is a one-line
  document change, one tuple entry, and one pinned test (recorded in
  `design.md` Uncertainty as the remaining open judgment).
- Level self-declaration (M2) remains a documented, reviewer-checked
  exposure; no mechanical closure exists and none is claimed.
- No scope uncertainty remains: the version 1 escalation stays resolved and
  version 3 touches no path outside the declared scope.
