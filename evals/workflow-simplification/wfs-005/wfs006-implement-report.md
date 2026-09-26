# Worker report

The implementer's plan, written before implementing, and the record of what changed and how it was verified. Levels 0 and 1 only; see the level table in `docs/workflows/task-dossier.md`.

## Artifact metadata

- Task ID: `WFS-006`
- Task level: `1`
- Artifact: `report`
- Artifact version: `1`
- Origin: `WFS-006-report@1`
- Owner: `implementer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `claude-code-d3d6e5f7`
- Effective route: `implement`
- Effective model: `claude-opus-5-5`
- Effective effort: `medium`
- Reviewing session: `null`
- Review verdict: `null`

## Plan

- Plan `WFS-006-PLAN-001`, version 1, written before any code change. Scope is the WFS-005 code review version 2 Lows L1, L2, L3, L4, L5, L8 and L9; L6 and L7 are untouched.
- L1: add a validator test that replaces a required `report.md` with a symlink and asserts the symlink diagnostic appears while the missing-file diagnostic does not. No production change.
- L2: add an integration test that feeds `apply_scaffold` an index template whose status rows are split, through a wrapped `template_text`, and asserts the contiguity `ValueError`. No production change.
- L3: add a generator test that passes `record_artifacts` a record whose artifacts are in reverse order and asserts lifecycle order back. No production change.
- L4: add a summary test with a symlinked `code-review.md` (appended during the scan) and a missing `request.md` (appended after it) and assert the unreadable rows come back in lifecycle order. No production change.
- L5: in `contract_paths.main`, refuse input with no non-blank name: exit 2 with a stderr message and no stdout. Add tests for empty and whitespace-only input and for the wrapper script. In the Contract paths section of the workflow document, run the pipeline under `set -o pipefail` and state the empty-input refusal; pin both in the contract test.
- L8: pass the validator's `present` set to `_validate_unplanned_review_targets` and to the review-target part of `_validate_plan_linkage`, so every review-target rule treats an unreadable `plan.md` as absent, exactly as `required_artifacts` does. Add a test on the unreadable-plan state asserting the report is required and the review targets must be null, and that no rule demands a target equal to the unreadable plan's empty ID.
- L9: replace `MINIMUM_EVIDENCE_ITEMS.get(level, 1)` with `MINIMUM_EVIDENCE_ITEMS[resolve_task_level(level)]`, and add a test that calls `_validate_state` with an unknown level and asserts the level 2 floor of 3.
- Verification: each L1 to L4 mutation from the review, run against the new test with the file's SHA-256 recorded before and after; the focused dossier suites; `validate_task_dossiers.py projects`; and `make check` on Python 3.10 and 3.14.

## Changes

- `src/brichan/contracts/task_dossier/validation.py`: L9, the evidence floor is `MINIMUM_EVIDENCE_ITEMS[resolve_task_level(level)]`, so an unknown level gets the level 2 floor instead of the `.get` default of 1. L8, `_validate_unplanned_review_targets` and the review-target loop of `_validate_plan_linkage` now take the `present` set that `required_artifacts` uses, so an unreadable `plan.md` is absent for every review-target rule. Before, an unreadable plan required null targets under one rule and targets equal to its empty plan ID under the other.
- `src/brichan/contracts/task_dossier/contract_paths.py`: L5, input with no non-blank line exits 2 with `contract-path: no path names on input; refusing to decide` on stderr and nothing on stdout. The module docstring states the new exit-2 case.
- `docs/workflows/task-dossier.md`, Contract paths section only: the pipeline now starts with `set -o pipefail`, and the exit-code paragraph states that empty or whitespace-only input is refused.
- `tests/unit/test_task_dossier_validator.py`: L1 `test_a_symlinked_required_artifact_is_not_also_reported_missing`, L8 `test_an_unreadable_plan_is_absent_for_every_review_target_rule`, L9 `test_an_unknown_level_gets_the_deepest_evidence_floor`.
- `tests/integration/test_task_dossier_workflow.py`: L2 `test_scaffold_refuses_an_index_template_with_split_status_rows`, run through `apply_scaffold` with a wrapped `template_text`; `plan_scaffold` only reads templates and never reaches the guard.
- `tests/unit/test_task_dossier_generator.py`: L3 `test_artifacts_render_in_lifecycle_order_whatever_the_record_order`, plus the `dataclasses` import.
- `tests/unit/test_task_dossier_summary.py`: L4 `test_unreadable_rows_are_listed_in_lifecycle_order`.
- `tests/unit/test_contract_paths.py`: L5 `test_empty_or_blank_input_is_refused_not_answered_no` and `test_the_wrapper_refuses_empty_input`.
- `tests/contract/test_task_dossier_contract.py`: `test_contract_path_list_equals_the_constants` also pins the `set -o pipefail` first line of the pipeline and the empty-input sentence.
- `scripts/check_contract_paths.py` is unchanged; the wrapper already delegates to `main`.

## Verification

- Techstack verify, run before any work: `match`, snapshot `c87ca1f7d8072beb2d777c86109baa0de7fd705f4cce68911b116045947f2265`.
- L1 mutation, drop `or path.is_symlink()` in `_validate_presence`: `tests.unit.test_task_dossier_validator` 86 run, 1 failure, the new L1 test. `validation.py` restored, SHA-256 `ef851365af79ae181aff39550dcff2e0801eb3806939985de2a43c4d6779e678` before and after.
- L2 mutation, replace the contiguity `raise` with `pass`: `tests.integration.test_task_dossier_workflow` 50 run, 2 failures, the new L2 test and the pre-existing WFS-006 `test_repository_checkout_validates_clean`. `scaffold.py` restored, `c8c460080705d9abb764651f22d4755d1a2762b1eac41de75ce6ab7e2f5c8447` before and after.
- L3 mutation, `return tuple(record.artifacts)`: `tests.unit.test_task_dossier_generator` 86 run, 1 failure, the new L3 test. `generate.py` restored, `c9d25da69baa8cf9c457c2db96b8ecf4db2424d8e6d9d577827dba6c202a6116` before and after.
- L4 mutation, delete the `unreadable.sort(...)` line: `tests.unit.test_task_dossier_summary` 31 run, 1 failure, the new L4 test. `summary.py` restored, `861ed479ee10c48bad960bfebee382e640c71760b75c4204998dfaabe3b83546` before and after.
- Reverting each new fix fails its test: L5 (`if not names` to `if False`) fails 3 subtests and the wrapper test; each L8 arm (`present` back to `artifacts`, and dropping the linkage guard) fails the L8 test; L9 (back to `.get(level, 1)`) fails the L9 test. Every file was restored byte-for-byte.
- Before its fix, each L8 and L9 test failed on the unmodified production code.
- Sweep: `grep -nE '\.get\(\s*level|\.get\([^)]*level[^)]*,'` over `validation.py`, `generate.py`, `summary.py`, `record.py`, `scaffold.py` and `schema.py` finds nothing.
- Focused suites (`test_contract_paths`, `test_task_dossier_validator`, `test_task_dossier_summary`, `test_task_dossier_generator`, `test_task_dossier_workflow`, `test_task_dossier_contract`): 293 run, 1 failure, `test_repository_checkout_validates_clean`, whose diagnostics are all on WFS-006 `index.md` (15), `code-review.md` (5) and `receipt.md` (1).
- `python3 scripts/validate_task_dossiers.py projects`: output byte-identical to the same command run with HEAD's `src` and `scripts` taken from `git archive HEAD`. 20 issues, all on WFS-006 `index.md`, `code-review.md` and `receipt.md`, none on `report.md`, so every other dossier validates as before.
- `PYTHONDONTWRITEBYTECODE=1 make check` on Python 3.10 and with `PYTHON=/opt/homebrew/bin/python3.14`: both exit 2, only at `make test`. Unit 1069 OK, contract 153 OK, integration 228 with the one WFS-006 failure above. Because `make` stops there, the remaining `check` prerequisites were run one by one under both interpreters: `techstack-eval`, `metrics`, `receipts`, `memory-check`, `path-check`, `readme-check`, `phase5-preflight`, `package-check` and `sh -n bin/brichan` exit 0. `dossiers` exits 2 on the same 20 WFS-006 issues. The techstack eval also passes run directly under 3.14.
- `git status --short`: the nine in-scope files above, plus the pre-existing `.codex/config.toml` change and untracked `.brichan*/` directories, none of which I touched. `projects/` is not tracked.

## Risks

- Techstack snapshot drift: the required L5 edit to `docs/workflows/task-dossier.md` changes an evidence file of `techstacks/policy/task-dossiers.md`. Re-running verify now returns `drift` on that file's hash (`42faa2fd…` to `e1fae424…`) and on the evidence byte totals. The pre-work verify returned `match`. The reviewer attempt needs a fresh snapshot.
- L5 changes a documented exit contract: empty input moves from exit 0 to exit 2. Any caller that relied on an empty diff meaning "no" will now get a refusal. That is the change the finding asks for, and the workflow document states it.
- L8 also stops `_validate_plan_linkage` from demanding that review targets equal an unreadable plan's empty ID. It still diagnoses the plan's own fields. The only state affected is already invalid because of the unreadable file.
- The L9 test calls the private `_validate_state` directly, because the production path resolves the level first and cannot reach the lookup with an unknown level. The test is coupled to that function's signature.

## Claim or decision

WFS-006 closes WFS-005 code-review Lows L1, L2, L3, L4, L5, L8 and L9. Each has a committed test that fails when its guard is removed or its fix is reverted, and every other dossier validates exactly as before. L6 and L7 are unchanged.

## Evidence

- Mutation and revert runs for L1 to L5, L8 and L9, with SHA-256 before and after each, in `Verification` above.
- Validator output for `projects` is byte-identical under HEAD code and the changed code. Its 20 issues are all on WFS-006's pending coordinator and reviewer artifacts.
- `make check` on Python 3.10 and 3.14 is red only through `test_repository_checkout_validates_clean` and `make dossiers`, both on WFS-006 `index.md`, `code-review.md` and `receipt.md`. All other check targets exit 0.

## Uncertainty

- `Effective effort` is recorded as `medium` from the `implement` route in `config/model-routing.json`; the session did not report its own effort setting. The route names `claude-opus-5`, and the session ran `claude-opus-5-5`.
- `make check` cannot exit 0 until the coordinator completes WFS-006 `index.md` and `receipt.md` and the reviewer writes `code-review.md`.
