# WFS-005 implementation report

Implementation of accepted plan `WFS-005-PLAN-001` version 3, plus coordinator
conditions M1 and M2 from the passing plan review (artifact version 2).
Written by the implementation worker (attempt `attempt-implement-1`) on
2026-09-26. All changes are uncommitted in the working tree of branch
`feat/lifecycle-simplification`.

## Outcome

Implemented. Every plan step S1-S9 and both coordinator conditions are met.
The full gate passes on Python 3.10 and 3.14 except for the reds the packet
sanctions (WFS-005's own pending dossier artifacts). There is one extra
pre-existing red at the time, not caused by this change: coordinator-owned untracked
pane captures under `evals/workflow-simplification/wfs-005/` embedded home paths
(see Risks, item 1). Corrected in place by the coordinator on 2026-09-26: the
captures were redacted, and the red no longer occurs.

## Techstack verification

- `bin/brichan techstacks verify --project-root <repo> --snapshot-json projects/brida-workflow-simplification/handoffs/WFS-005/snapshots/attempt-implement-1-97f413cb4b5634b3711b55c78848fd84145079ff1bb831d00c0da86b0934a3a6.snapshot.json --as-of 2026-09-26`
  returned `"status": "match"` with snapshot SHA-256
  `97f413cb4b5634b3711b55c78848fd84145079ff1bb831d00c0da86b0934a3a6`. It ran
  before any other work.
- All ten required selected rule files were read in full:
  `techstacks/README.md`, `techstacks/general.md`,
  `techstacks/policy/README.md`, `techstacks/policy/canonical.md`,
  `techstacks/policy/packaged-resources.md`,
  `techstacks/policy/task-dossiers.md`, `techstacks/python/README.md`,
  `techstacks/python/runtime.md`, `techstacks/python/scripts.md`,
  `techstacks/python/tests.md`. `docs/policy/operating-principles.md`
  (including its testing discipline) was also read.

## Changed files

Every path is inside the declared Techstack scope.

Code (`src/brichan/contracts/task_dossier/`, stdlib only):

- `schema.py`: adds `RECOGNIZED_ARTIFACTS` (the frozen eleven plus `report`
  after `plan`), `LEVEL_REQUIRED_ARTIFACTS`, `FALLBACK_TASK_LEVEL = "2"`,
  `REPORT_SECTIONS`, `CONTRACT_PATH_PREFIXES`, `CONTRACT_PATH_FILES`, the
  `report` entries of `ARTIFACT_TITLES`/`ARTIFACT_OWNERS`, and two shared
  helpers: `resolve_task_level` (the single fail-closed level rule) and
  `required_artifacts` (the level set minus `report` when `plan` is really
  present). `ARTIFACTS` is byte-unchanged. The stale "never changes which
  artifacts must exist" comment is corrected (L1).
- `validation.py`: recognized-set loading with real-presence tracking; a
  missing-file check against the effective required set; `"2"` fallback via
  `resolve_task_level`; report structure and passed-phase concreteness;
  `report` added to the reviewer back-write guard (M2); report-author
  independence for `code-review`; code review cannot be `not-required` at
  levels 1 and 2; review targets must be null without `plan.md`; the status
  table requires exactly (required ∪ present); completion's plan-review
  refusal narrowed to level 2; partial-adoption scan over recognized names.
- `scaffold.py`: level-keyed artifact set; `template_path` accepts every
  recognized name; generated index status rows (level 2 output is
  byte-identical to the templates).
- `record.py`: the effective-required key rule (⊆ `RECOGNIZED_ARTIFACTS`)
  through the shared helpers; JSON-null review targets exactly when `plan` is
  absent; `_cross_record` plan checks only when `plan` is present, plus
  report-author independence; report sections present and in order, and
  concrete when passed; evidence floor through `resolve_task_level`.
- `generate.py`: renders, plans, and publishes exactly the record's
  artifacts in `RECOGNIZED_ARTIFACTS` order, including the status table.
- `summary.py`: roster = (required ∪ present); "artifact is missing" only
  for required names; level and floor through `resolve_task_level` (M1);
  a report-author independence arm (`ReviewIndependence.against`).
- `contract_paths.py` (new): classification over path names plus a stdin
  CLI (exit 0 / 3 / 2); never runs Git or opens a repository file.

Scripts, templates, and documents:

- `scripts/check_contract_paths.py` (new): 19-line wrapper, same pattern
  and file mode as `scripts/validate_task_dossiers.py`.
- `docs/workflows/task-dossier/templates/report.md` (new). The index
  template is unchanged.
- `docs/workflows/task-dossier.md`: the single normative statement. It covers
  the intro presence rule, the `report.md` row, the level table with a
  required-artifacts column (level and minimum-evidence columns stay
  adjacent), the level-determination evidence obligation, the fail-closed
  rule, "Lifecycles by level", the report structure, the legacy
  `plan`-satisfies rule, the stop-and-rollback rule, "Contract paths" with the
  checker and the named trust boundary, and level-aware tooling text. Every
  pinned needle is preserved, including the wrapped "task level changes
  required" / "evidence depth" line.
- `docs/policy/operating-principles.md` section 2: now a reference to the
  workflow document.
- `docs/policy/reviewer.md`: the regression-test rule inside the prompt's
  `Rules:` list, the amended return item 4, the report back-write sentence,
  null targets without a plan, the contract-path reference, and the
  level-mis-declaration finding.
- `.agents/skills/herdr-orchestration/references/task-dossier.md` and
  `SKILL.md`: the level-keyed references. No parity marker or packet label
  was edited.
- `CHANGELOG.md`: Unreleased "Changed" entry.

Tests:

- `tests/unit/test_task_dossier_validator.py`, `tests/unit/test_task_dossier_generator.py`,
  `tests/unit/test_task_dossier_summary.py`, `tests/unit/test_contract_paths.py` (new),
  `tests/contract/test_task_dossier_contract.py`,
  `tests/integration/test_task_dossier_workflow.py`.

## Plan steps

- S1: schema constants, the template, the three re-keyed contract
  assertions, and the tuple pin (`RegistryPinTest`).
- S2: validator. Design tests 1-11 and 19 landed.
- S3: scaffold. Design tests 12 and 13 landed.
- S4: record and generator. Design tests 14 and 15 landed. The frozen
  eleven-artifact Level 0 fixture loads unedited
  (`test_worked_record_loads`, `test_the_literal_record_renders_and_validates_clean`).
- S5: summary. Design test 16 landed.
- S6: checker, wrapper, and tests. Design test 17 landed.
- S7: documents and contract pins. Design tests 18 and 20 landed; `make
  test-contract` was run as the parity guard (L4).
- S8: CHANGELOG entry.
- S9: full verification (below).

## Coordinator conditions

- M1 (fail-closed level resolution in all four tools). One helper,
  `schema.resolve_task_level`, is the only level rule. The validator, the
  summary, and the record loader call it, and the loader's required-key rule
  and evidence floor go through it too. None of them keeps a
  `.get(level, 1)`-style fail-open lookup. The scaffold and the generator CLI
  refuse an invalid level outright (`level_artifacts` raises; argparse
  `choices`). Tests that fail if a tool fails open:
  - validator: `test_an_invalid_level_fails_closed_to_level_2`,
    `test_a_missing_index_fails_closed_to_level_2`
  - summary: `test_an_unresolvable_level_fails_closed_to_level_2`
  - generator/record: `test_an_unresolvable_level_requires_the_largest_set`
  - scaffold: `test_scaffold_refuses_an_unresolvable_level`
  - pin: `test_the_fallback_level_is_the_largest_set_and_deepest_floor`
- M2 (back-write guard covers `report.md`). `report` joins the
  `_validate_ownership` tuple. The test is
  `test_reviewer_must_not_author_the_report`.

## Design test map

| # | Test |
| --- | --- |
| 1 | `test_reduced_level_0_dossier_with_a_waived_code_review_is_valid` |
| 2 | `test_reduced_level_1_dossier_with_an_independent_review_is_valid` |
| 3 | `test_reduced_dossier_without_a_report_is_rejected`; `test_a_symlinked_plan_does_not_excuse_the_report` |
| 4 | `test_levels_1_and_2_may_not_waive_code_review` |
| 5 | `test_a_passed_report_requires_concrete_report_sections`; `test_the_report_sections_are_structurally_required` |
| 6 | `test_code_review_must_be_independent_of_the_report_author` (validator and record) |
| 7 | `test_level_2_requires_every_standard_artifact` |
| 8a | `test_full_legacy_dossier_stays_valid_at_every_level` |
| 8b | `test_the_committed_legacy_samples_validate_under_the_level_rules` |
| 9 | `test_a_report_alone_without_an_index_is_partial_adoption` |
| 10 | `test_status_table_lists_exactly_required_and_present_artifacts` |
| 11 | `test_require_complete_rejects_a_changes_required_reduced_review`; `test_require_complete_rejects_a_not_required_plan_review_at_level_2` |
| 12 | `test_scaffold_creates_exactly_the_level_artifact_set`; `test_level_2_scaffold_output_is_byte_identical_to_the_templates` |
| 13 | `test_scaffolded_and_filled_dossiers_validate_at_every_level`; `test_reduced_level_1_flow_scaffolds_fills_validates_and_summarizes` |
| 14 | `test_a_reduced_record_renders_publishes_and_validates`; `test_a_missing_required_key_or_an_unrecognized_key_is_refused` |
| 15 | `test_review_targets_are_null_exactly_without_a_plan` |
| 16 | `ReducedDossierSummaryTest` (four cases) |
| 17 | `tests/unit/test_contract_paths.py` (seven cases) |
| 18 | `test_contract_level_table_equals_the_required_sets`; `test_contract_path_list_equals_the_constants`; `test_recognized_artifacts_are_the_frozen_eleven_plus_the_report`; `test_reviewer_policy_states_the_regression_test_rule`; `test_level_lifecycles_are_stated_once_and_referenced_elsewhere` |
| 19 | the M1 tests above |
| 20 | `make test-contract` (skill parity, dogfood policy, repository paths): 153 OK |

TEST-003 check: in a scratch copy of the tree, each new guard was removed
one at a time (the fallback, the report back-write, report independence in
the validator and the record, the level 1 review waiver, report
concreteness, the absent-row status rule, the legacy `plan` rule, symlinked
plan presence, null targets in the validator and the record, level-keyed
scaffolding, generated status rows, completion narrowing, partial adoption
of `report`, the contract-path list, and the summary report arm). Each
removal failed its named test. Corrected in place by the coordinator on 2026-09-26, per code review L7: that claim was too strong. The code review found surviving mutations (M1 unreadable-artifact filter, since closed by Fix 1; L1-L4 recorded as non-blocking).

## Verification

- Focused runs: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest`
  over the validator, generator, summary, contract-path, contract, and
  integration dossier modules passed, except the sanctioned
  `test_repository_checkout_validates_clean`.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py projects`
  reports 40 diagnostics across 17 dossiers, and every one is in WFS-005's
  own pending coordinator/reviewer artifacts (templated `index.md`,
  `code-review.md`, `pr-desc.md`, and the not-yet-written `receipt.md`).
  Zero diagnostics fall on the other 16 dossiers (A3). This is a check; the
  regression guards are tests 8a and 8b.
- `PYTHONDONTWRITEBYTECODE=1 make check` (3.10.11) in the checkout: unit
  tier 1061 OK. The contract tier stops on the one pre-existing red,
  `test_durable_artifacts_do_not_embed_home_paths`, which names only
  `evals/workflow-simplification/wfs-005/plan-review-v1-pane.txt` and
  `plan-review-v2-pane.txt`. Those files are untracked coordinator captures
  created before this attempt started.
- To see the rest of the gate without touching those files, the checkout
  (including `.git`) was copied to a scratch directory, leaving out only that
  untracked capture directory, and `make -k check` was run with `codex` off
  `PATH`:
  - 3.10.11: metrics 10 OK, unit 1061 OK, contract 153 OK, integration 227
    run with the single sanctioned failure
    `test_repository_checkout_validates_clean`, techstack-eval 56 OK,
    receipts 55 valid, `make dossiers` red only on WFS-005 (40 issues, all
    WFS-005), memory-check, path-check (113 entries), readme-check,
    phase5-preflight (eligible, retired), and package-check all pass.
  - `make -k check PYTHON=/opt/homebrew/bin/python3.14` (3.14.6): identical
    results.
  - Eval directly under 3.14:
    `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 -m unittest evals.techstack_context_v1.test_cases`
    ran 56 tests, OK.
  - `sh -n bin/brichan`: exit 0.
- `git diff --stat -- src/brichan/resources PRODUCT.md config techstacks evals Makefile README_PYPI.md packaging`
  is empty. Installed mode and packaged resources are byte-unchanged (A5).
  `git status --short evals` shows only the pre-existing untracked
  `evals/workflow-simplification/wfs-005/`.
- `git status --short` / `git diff --stat`: 20 modified tracked files (1580
  insertions, 208 deletions) and 4 new files. Three of the modified entries
  (`.codex/config.toml`, `projects/brida-workflow-simplification/decisions.md`,
  `projects/brida-workflow-simplification/tasks.md`) and the untracked
  `.brichan*` directories predate this attempt and were not touched.

## Deviations and interpretations

1. Report sections in the validator come from an explicit
   `REPORT_SECTIONS` branch in `_validate_structure` (like the index status
   section), not from new entries in `ARTIFACT_EXTRA_SECTIONS`. The effect
   is the same (presence, exactly once, canonical order). This keeps the
   `validation.EXTRA_SECTION_FIELDS is ARTIFACT_EXTRA_SECTIONS` pin true
   and stops the record loader from reserving the four titles away from the
   report itself.
2. The design says "titles reserved for it". For a report record, the four
   section titles must be supplied, in order, and be concrete when passed.
   They are not refused on other artifacts, because no committed record uses
   them and a refusal would add a restriction the plan does not test.
3. `ReviewIndependence` gains an `against` field (default `"plan"`). The
   summary JSON therefore gains that key on every independence row. The text
   form changes only for the new report arm.
4. Wording changes on existing messages: the partial-adoption message now
   ends "owns its level's dossier", and the completion refusal now reads
   "plan review applies to every level 2 task".
5. Existing tests that encoded the old uniform artifact set move to the level
   that still has that rule. The full-set scaffold, symlink, and race tests
   move to level 2. The waived-code-review case moves to level 0. The
   not-required plan-review completion case moves to level 2, and a level 1
   arm is added. The Level 0 wrapper dry run now expects 4 planned
   artifacts. The misspelled or deleted record key now targets a required
   key.
6. Folded in the plan review's L1: the `.agents` reference's `## Review` and
   `## Closing` sentences no longer claim that every task has a plan review
   and a plan. The second "full task dossier" wording in `SKILL.md` is also
   updated.
7. The record loader does not replicate the validator's "code review
   mandatory at levels 1 and 2" rule, because the design's record change list
   does not include it. The validator (the sole authority) enforces it.

## Risks and open items

1. Resolved (corrected in place by the coordinator on 2026-09-26: captures redacted). Was: pre-existing gate red; the
   untracked pane captures `evals/workflow-simplification/wfs-005/plan-review-v1-pane.txt`
   and `plan-review-v2-pane.txt` contain home paths and fail
   `test_durable_artifacts_do_not_embed_home_paths`. `evals/` is out of this
   task's scope, so they were not edited.
2. Pre-existing quirk, not fixed (out of plan): `summarize_dossier` passes
   the caller's unresolved dossier path to `validate_dossier`. On macOS, a
   temporary directory reached through the `/var` symlink therefore gets a
   spurious "outside supplied projects root" diagnostic. The CLI path is
   unaffected. The new tests pass resolved paths.
3. Level self-declaration stays a documented, reviewer-checked exposure
   (M2 of the version 2 review); no mechanical check exists.
4. Plan-before-implementation order inside `report.md` and the Level 0
   contract-path review decision are trust boundaries. The workflow document
   states them explicitly; no tool can verify them.
5. The contract-path membership (the `src/brichan/` and `scripts/` prefixes)
   remains a reversible user judgment, per the plan's Uncertainty.
6. `make dossiers` and `test_repository_checkout_validates_clean` stay red
   until the coordinator and reviewer complete WFS-005's own `index.md`,
   `code-review.md`, `pr-desc.md`, and `receipt.md`.

## Fix 1 (code-review M1)

Task `WFS-005-FIX-1`, attempt `attempt-implement-2`. Scope: close code-review
finding M1 only. No production file changed.

Techstack verify returned `"status": "match"` for snapshot
`cace4c328331a3ccfadbcca80bf871ec7c7cbc536173c99b61b602c3d3dc8f43` before any
other work, and all ten selected rule files were read.

### Test added

`tests/unit/test_task_dossier_validator.py`,
`ReducedDossierValidatorTest.test_an_unreadable_plan_does_not_excuse_the_report`,
beside `test_a_symlinked_plan_does_not_excuse_the_report`. It builds a valid
full dossier, asserts it is valid, overwrites `plan.md` with non-UTF-8 bytes,
and asserts that the diagnostics include both `required task-dossier artifact
report.md is missing` and `plan.md: file: cannot read artifact`. The second
assertion proves that the unreadable arm is what the test exercises, not the
symlink arm.

### Mutation proof

Run on a copy of `src` and `tests` in a scratch directory outside the
repository, against `tests.unit.test_task_dossier_validator` (83 tests):

- Baseline, unmutated: 83 OK.
- Filter removed (the review's mutant: the `if not any(...)` block replaced
  with an unconditional `present.add(name)`): 1 failure,
  `test_an_unreadable_plan_does_not_excuse_the_report`. Before this fix, the
  review reported that this mutant survived.
- Filter inverted (`if not any(` to `if any(`): 15 failures, including the new
  test and `test_a_symlinked_plan_does_not_excuse_the_report`.
- The repository's `src/brichan/contracts/task_dossier/validation.py` was never
  edited. Its SHA-256 is
  `8a5a4059863ffae79efc826f79615f9027e3d17ad5b0f7781557ad6c340a67d0` both
  before and after the mutation runs (`shasum -a 256 -c` OK).

### Verification

- Focused: the six dossier suites (validator, generator, summary, contract
  paths, dossier contract, dossier workflow integration) ran 285 tests on
  Python 3.10.11 and on 3.14.6. On each, the only failure is
  `test_repository_checkout_validates_clean`.
- `PYTHONDONTWRITEBYTECODE=1 make -k check` and
  `make -k check PYTHON=/opt/homebrew/bin/python3.14` both ran with `codex`
  off `PATH` to match CI, and both gave identical results: metrics 10 OK,
  unit 1062 OK (1061 plus the new test), contract 153 OK, integration 227 with
  only `test_repository_checkout_validates_clean` failing, techstack-eval
  56 OK, receipts, memory-check, path-check (113 entries), readme-check,
  preflight, and package-check passing. The only two make errors are `test`
  (that one integration test) and `dossiers`, which reports 36 issues. All 36
  name WFS-005's own pending coordinator artifacts, and none falls on any
  other dossier.
