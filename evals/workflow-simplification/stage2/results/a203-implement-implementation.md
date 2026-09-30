# Implementation

Implementation report for accepted plan `WFS-A-203-PLAN-001` version 3.

## Artifact metadata

- Task ID: `WFS-A-203`
- Task level: `1`
- Artifact: `implementation`
- Artifact version: `1`
- Owner: `implementer`
- Attempt ID: `attempt-implement-1`
- Authorship: `model`
- Effective model: `claude-opus-5-5`
- Base commit: `6fe3977` (changes left uncommitted)

## Outcome

Implemented the plan as written, with no deviations. `diagnostic_detail` now
raises `ValueError` for any non-`None` `errno_value`, `line`, or `rule` that
the given code's detail has no slot for. Every previously valid call returns
the same bytes: the 244-call enumeration digest is unchanged. The resolver's
`_add_located` drops the provenance-only errno before it builds a
non-`FILESYSTEM_ERROR` diagnostic, so production resolution produces the same
diagnostics as before.

## Changed files

| File | Change |
|---|---|
| `src/brichan/techstacks/model.py` | `diagnostic_detail` body: three `is not None` refusal guards and a docstring paragraph. The signature and both helpers are unchanged. |
| `src/brichan/techstacks/resolver.py` | `_add_located`: sets `errno_value = None` for every code except `FILESYSTEM_ERROR`, with the design's comment. |
| `tests/unit/test_techstack_model.py` | New `DiagnosticDetailArgumentTest` with 6 tests. |
| `tests/unit/test_techstack_resolver.py` | New `ObservationErrnoTest` with 2 tests. |
| `tests/unit/test_techstack_markdown.py` | New `MapGrammarTest.test_map_failures_carry_no_leaf_line_or_rule`. |
| `projects/brida-workflow-simplification/handoffs/WFS-A-203/implementation.md` | This report. |

`git diff --stat`: 5 files changed, 187 insertions, 2 deletions. The only
untracked file is this report. No other path changed.

## Plan steps

1. **Scope re-verified.** The implementer Snapshot `attempt-implement-1-cd04ee8e...`
   and the plan Snapshot `attempt-plan-3-008ff53c...` both returned `match` with
   no differences at `--as-of 2026-09-25`. All seven selected rule files were
   read, plus `docs/policy/operating-principles.md`.
2. **Baseline recorded** at `6fe3977` before any edit, on Python 3.10.11. The
   design.md enumeration gave `calls: 244`, sha256
   `6a26f5041d52249b88d785bffb5b6fd826de46311ae5bc4cda15f7f7ea63ef69`.
   Both class (b) probes, `errno_value=13` and `errno_value=0` with `line=1`
   and `rule="TITLE"`, returned
   `leaf bytes do not match the leaf grammar at line 1: TITLE`.
3. **`model.py` edited** with the guarded form from design.md version 3,
   copied verbatim. Every guard uses `is not None`. In the `INVALID_LEAF`
   branch, the errno guard runs before `invalid_leaf_detail`. The
   `DIAGNOSTIC_SPECS[code]` lookup still runs before the slotless guard, so
   `KeyError` still takes precedence for unknown codes.
4. **`resolver.py` edited** with the `_add_located` decision and comment from
   design.md.
5. **Tests added** as design.md "Test design" specifies. Nothing else was
   added or moved:
   - `test_valid_calls_render_the_registry_detail_in_both_call_shapes`
     covers R2 for every registry code, in both the omitted and the
     all-three-explicit-`None` call shapes.
   - `test_errno_refuses_for_every_code_without_an_errno_slot` covers class
     (c) for `errno_value` 13 and 0. It excludes `FILESYSTEM_ERROR` and
     `INVALID_LEAF`.
   - `test_invalid_leaf_refuses_errno_alongside_its_own_slots` covers class
     (b) for `errno_value` 13 and 0, each with `line=1, rule="TITLE"`.
   - `test_line_and_rule_refuse_for_every_code_without_leaf_slots` covers
     classes (a) and (c) with `line=1`, `line=0`, and `rule="LINE_SHAPE"`.
   - `test_unknown_code_still_raises_key_error` covers R4, with and without
     `line=1`.
   - `test_factory_propagates_the_refusal` checks that
     `diagnostic("UNSUPPORTED_PLATFORM", errno_value=13)` raises.
   - `ObservationErrnoTest.test_an_unreadable_selected_rule_file_reports_without_raising`
     is the R5 real-condition test: the selected leaf is `chmod 0o000`,
     skipped when running as root, and restored in cleanup. It expects
     `blocked` with exactly one `UNREADABLE_FILE` for `techstacks/general.md`,
     detail `a required file could not be read`.
   - `ObservationErrnoTest.test_a_general_class_observation_with_an_errno_reports_without_a_path`
     is the R5 class-`G` test. A mocked `read_project_file` returns
     `Observation(code="RESOURCE_LIMIT", errno_value=24)`, and the test
     expects one `RESOURCE_LIMIT` with no path and the registry detail.
   - `test_map_failures_carry_no_leaf_line_or_rule` pins the `MarkdownError`
     contract (`line is None` and `rule is None`) for these `parse_map`
     failures:
     - document-level `INVALID_MAP`: BOM, missing terminal LF, and an
       outside-form heading
     - row-level `INVALID_MAP`: an absolute row path and a duplicate row ID
     - `MAP_ROW_LIMIT`
     - `SELECTOR_LIMIT`
6. **Verification.** Results are in the next section.

## Verification

All commands below ran from the worktree root with `PYTHONDONTWRITEBYTECODE=1`.

- **6(a) Focused suites.** `PYTHONPATH=src python3 -m unittest
  tests.unit.test_techstack_model tests.unit.test_techstack_resolver
  tests.unit.test_techstack_markdown` ran 193 tests: `OK`.
- **6(b) Byte-identity proof.**
  - The enumeration after the change gives `calls: 244`, sha256
    `6a26f5041d52249b88d785bffb5b6fd826de46311ae5bc4cda15f7f7ea63ef69`,
    identical to the step-2 baseline. The imported module path was printed
    and confirmed to be the edited worktree module.
  - The diff shows `filesystem_error_detail` and `invalid_leaf_detail`
    unchanged. The first two return expressions are textually unchanged.
    The third returns the same value through a local, `detail =
    DIAGNOSTIC_SPECS[code].detail` … `return detail`, exactly as design.md
    version 3 spells it; plan-review version 3 finding `L1` notes this
    wording point. The digest is the operative proof.
- **Removal sensitivity (rule `TEST-003`).** Each variant was built on a
  disposable full copy of `src/` and `tests/`, with the imported module path
  printed to confirm the copy was the one exercised. The three new-test
  modules were rerun against each variant:

  | Variant | Result | Failing tests |
  |---|---|---|
  | Complete guarded form | `OK` | none |
  | `FILESYSTEM_ERROR` guard removed | 3 failures | all in the class (a)+(c) `line`/`rule` test |
  | `INVALID_LEAF` errno guard removed | 2 failures | the class (b) test only |
  | Slotless guard removed | 281 failures | class (c) errno, class (a)+(c) `line`/`rule`, factory propagation |
  | All three guards rewritten on truthiness | 114 failures | every `errno_value=0` and `line=0` case, across all three refusal tests |
  | `_add_located` edit reverted | 2 errors | both `ObservationErrnoTest` tests: `ValueError` mid-resolution |

  Every variant still reproduced the 244-call digest. These counts match
  plan-review version 3's construction results (3 / 2 / 280 plus the factory
  test / 114).
- **6(c) Ratified completion gate** (client-follow-up-questions.md
  version 2). Each target ran on its own:

  | Check | 3.10.11 (shell `python3`) | 3.14.6 (`PYTHON=/opt/homebrew/bin/python3.14`) |
  |---|---|---|
  | `make test-unit` | 1035 tests `OK` | 1035 tests `OK` |
  | `make test-contract` | 148 tests, 2 failures (expected) | 148 tests, 2 failures (expected) |
  | `make test-integration` | 222 tests, 1 failure (expected) | 222 tests, 1 failure (expected) |
  | Frozen eval | `make techstack-eval`: 56 tests `OK` | Run directly: `/opt/homebrew/bin/python3.14 -m unittest evals.techstack_context_v1.test_cases -v`, 56 tests `OK` |
  | `metrics/test_validate_metrics.py` (run directly) | 10 tests `OK` | 10 tests `OK` |
  | `make metrics` | exit 0 | exit 0 |
  | `make receipts` | exit 0 | exit 0 |
  | `make dossiers` | exit 2 (expected), 40 issues | exit 2 (expected), 40 issues |
  | `make memory-check` | exit 0 | exit 0 |
  | `make path-check` | exit 2 (expected), `unclassified root files: .git` | same |
  | `make readme-check` | exit 0 | exit 0 |
  | `make phase5-preflight` | exit 0 | exit 0 |
  | `make package-check` | exit 0 | exit 0 |

  `sh -n bin/brichan`, the one `check` recipe line the gate omits
  (plan-review version 3 `L2`), exits 0.

  Expected-red items, all on the ratified list, identical on both
  interpreters:
  - `tests/contract/test_repository_paths.py`:
    `test_current_path_and_link_contracts_pass` and
    `test_every_non_ephemeral_root_file_is_classified`. Both fail with
    `unclassified root files: .git` because the worktree is detached.
  - `make path-check`: the same `.git` cause.
  - `tests/integration/test_task_dossier_workflow.py`
    `test_repository_checkout_validates_clean`, and `make dossiers`. All 40
    validator issues name this task's `index.md`, `code-review.md`, or
    `pr-desc.md` (template state), or the absent canonical `receipt.md`. The
    count is 40 rather than plan-review version 3's projected 38 because of
    two issues it did not project:
    - `index.md: Task identity.Accepted plan ID: expected 'WFS-A-203-PLAN-001' from plan.md, found '<plan-id or null>'`
    - `index.md: Task identity.Accepted plan version: expected '3' from plan.md, found '<positive integer or null>'`

    The validator raises these because plan.md now records `Plan status:
    accepted`, and index.md is still a template. Both are index.md
    template-state diagnostics, a cause the list already ratifies, and both
    are coordinator-owned. None names a planner- or implementer-owned
    artifact.
- **6(d) Dossier validator.** `python3 scripts/validate_task_dossiers.py
  projects` was run again after this report was written. Output: `Invalid
  task dossiers: 40 issue(s) across 8 dossier(s)`, the same 40 issues listed
  above. This report adds none.
- **Status.** `git status --short` shows the five `M` paths listed under
  "Changed files" plus this untracked report.

## Production call sites (acceptance criterion 3)

These are the only callers of `diagnostic_detail` in the repository. No test
or packaged export calls it, and it is absent from
`src/brichan/techstacks/__init__.py`.

- `src/brichan/techstacks/model.py:2259-2261`, `Diagnostic.__post_init__`.
  It passes `_errno_value()` and `_leaf_slots()`, which are `None` for every
  inapplicable slot. Unaffected: the registry-wide explicit-`None` test and
  the enumeration's explicit shape both pass.
- `src/brichan/techstacks/model.py:2349`, the `diagnostic` factory. It
  forwards its keywords verbatim, so a refusal propagates, as intended.
  Factory callers pass detail keywords at only two sites:
  - `resolver.py:280,282` (`_add_located`) now forwards an errno only for
    `FILESYSTEM_ERROR`.
  - `resolver.py:349-350` (`_parse`) forwards `MarkdownError.line` and
    `.rule`. Both are `None` for every map code, which the new markdown test
    pins. For `INVALID_LEAF` they are the leaf slots.

  Every other `findings.add` or `diagnostic(...)` site passes only `path`,
  `context_id`, or `waived_by`.

No registry row, cap, literal, sort key, fixture, fixture digest, or public
signature changed. `DiagnosticRegistryTest`, the contract tests, and the
frozen eval all pass unchanged.

## Deviations

None.

## Risks and notes

- `_add_located` is a production caller edit. It is required, not optional:
  the revert variant above makes real resolution raise. Its output is
  unchanged, but it is a visible departure from the literal wording
  "production callers are unaffected". Plan-review version 3 records the
  same point as a residual risk.
- `make check` was not run as a single command. It aborts inside `test` at
  `test-contract` in this detached worktree. The ratified per-target gate
  replaced it. On the main checkout, with a closed dossier, every gate must
  be green.
- The `ValueError` messages follow the reviewed proposal in design.md, and no
  test pins their wording.
- `make test-unit` on 3.14 prints a `SyntaxWarning` for an invalid escape
  sequence in `tests/unit/test_handoff_receipt_validator.py:733`. It is
  pre-existing, outside this task's authorized paths, and not a failure.
- `CHANGELOG.md` was left untouched, per the plan. Whether it needs an entry
  is the coordinator's decision.
