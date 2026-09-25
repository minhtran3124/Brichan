# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `WFS-A-203`
- Task level: `1`
- Artifact: `plan-review`
- Artifact version: `1`
- Origin: `plan-review-worker:2026-09-25-wfs-a-203-plan-review-v1`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `db413ec3-ea03-4abd-a9bd-ca84f79808e5`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `db413ec3-ea03-4abd-a9bd-ca84f79808e5`
- Review verdict: `CHANGES REQUIRED`

## Review target

- Reviewed plan ID: `WFS-A-203-PLAN-001`
- Reviewed plan version: `1`

## Claim or decision

`CHANGES REQUIRED`. The design is correct: its two code edits are each
necessary, jointly sufficient, and nothing unnecessary is added. Every claim
the planning artifacts make about the code was independently re-derived and
holds, including the premise correction that the silent-drop path is
production-reachable — which this review reproduced against a real
filesystem condition, not a mock. The changes required are in the plan's
verification design, not in its design of the change: step 6(c) cannot
produce the evidence acceptance criteria 3 and 4 demand, the residual-failure
list is incomplete, the specified refusal tests pass against a defective
guard, and one safety argument the design depends on is left unpinned.

## Verified planner claims

Each was re-derived in this worktree at commit `6fe3977`; none is taken on
the planner's word.

- `diagnostic_detail` at `src/brichan/techstacks/model.py:583-596` returns
  `DIAGNOSTIC_SPECS[code].detail` for all but two codes. All three refusal
  classes are live silent drops today, observed directly:
  `diagnostic_detail("UNREADABLE_FILE", errno_value=13)` and
  `(..., line=0)` both return `a required file could not be read`;
  `diagnostic_detail("FILESYSTEM_ERROR", errno_value=13, line=1, rule="TITLE")`
  returns the errno detail; `diagnostic_detail("INVALID_LEAF",
  errno_value=13, line=1, rule="TITLE")` returns the leaf detail.
- R4 holds as stated: `diagnostic_detail("NO_SUCH_CODE", line=1)` raises
  `KeyError` today, and the design keeps the `DIAGNOSTIC_SPECS[code]` lookup
  ahead of the third guard, so it still will.
- The caller graph is exactly as inventoried. `diagnostic_detail` has
  precisely two callers repository-wide — `Diagnostic.__post_init__`
  (`src/brichan/techstacks/model.py:2247-2249`) and the `diagnostic` factory
  (`src/brichan/techstacks/model.py:2337`); no test calls it directly today.
  Both are safe under the guard because `_errno_value`
  (`src/brichan/techstacks/model.py:2255-2261`) returns `None` for every
  non-`FILESYSTEM_ERROR` code and `_leaf_slots`
  (`src/brichan/techstacks/model.py:2263-2287`) returns `(None, None)` for
  every non-`INVALID_LEAF` code.
- Of the 31 `findings.add` sites in `src/brichan/techstacks/resolver.py`,
  exactly one forwards `line`/`rule` (`_parse`, `resolver.py:340-346`) and
  exactly one forwards `errno_value` (`_add_located`, `resolver.py:266-277`);
  every other site passes only `path` and `context_id`. The waiver rebuild
  (`resolver.py:742-747`) passes no detail keyword and is safe because the
  only waivable codes are `DEPRECATED_RULE`, `MISSING_EVIDENCE`, and
  `STALE_RULE`, all slotless.
- `_add_located` is reached from two call sites (`resolver.py:290` and
  `resolver.py:509`), so the design's single edit inside `_add_located`
  covers both, and it correctly preserves errno for `FILESYSTEM_ERROR`,
  which `_ERRNO_OUTCOMES` produces as its default
  (`src/brichan/techstacks/filesystem.py:98-116,307-309`).
- The premise correction is right, and stronger than the planner showed. With
  the `ProjectMixin` base fixture and a selected rule file at mode `0`, real
  production resolution — no mocked observation — produced exactly one
  diagnostic, `UNREADABLE_FILE` / `a required file could not be read`, while
  `diagnostic_detail` was called as `("UNREADABLE_FILE", 13, None, None)`.
  Step 4 is therefore load-bearing: a guard without it breaks resolution of
  any project with an unreadable selected rule file. No existing test covers
  this path; `tests/integration/test_techstack_cli.py:1034,1052,1081` inject
  errno-carrying observations through the `fs.open_directory` seam on the
  snapshot-output path, not through `read_project_file`, so they do not
  exercise `_add_located`.
- The recorded baseline digest is exact: the design's enumeration script
  reproduces `calls: 122`, `sha256:
  57b96aa6d240374df464cd4b01d9f5f74cfd123240c3577b5eba1bc73d5167c0`. Its
  coverage claims also hold — the registry has 58 rows (so 56 slotless
  codes), `LEAF_GRAMMAR_RULES` has 20 members, and
  `LEAF_FILE_BYTE_LIMIT + 1` is 65537, the line bound the script probes.
- Option D's rejection is well-founded: `ValueError` adds nothing to any
  frozen registry. The `TechstackError` code vectors and fixed details are
  pinned by `CallerErrorRegistryTest`
  (`tests/unit/test_techstack_model.py:387-465`); plain `ValueError` messages
  are registered nowhere, so acceptance criterion 3 ("no registry, cap,
  literal, sort key, fixture digest, or public signature changes") is met by
  the design as written.
- The design's cited test seams exist: `ProjectMixin`
  (`tests/unit/test_techstack_resolver.py:188-206`), the
  `mock.patch.object(resolver, "read_project_file")` precedent
  (`tests/unit/test_techstack_resolver.py:317,430-437`), and the frozen
  design fixtures asserted at `tests/unit/test_techstack_model.py:553-568`.
- The plan's carve-out (b) is accurately attributed. At baseline the dossier
  validator reports 42 issues and every one of them names this task's own
  `index.md`, `plan-review.md`, `code-review.md`, or `pr-desc.md`; the
  integration layer has exactly one failure,
  `tests.integration.test_task_dossier_workflow.TaskDossierWorkflowIntegrationTest.test_repository_checkout_validates_clean`.

## Findings

### High

- `H1` — Step 6(c) cannot evidence acceptance criteria 3 and 4, and never
  runs the integration layer at all. `check` depends on `test` first
  (`Makefile:75`), and `test` runs `test-unit`, then `test-contract`, then
  `test-integration` as three lines of one recipe (`Makefile:24-28`). At this
  worktree's baseline `test-contract` fails on the two known `.git` failures
  and `make` aborts the recipe: this review observed
  `FAILED (failures=2, skipped=1)`, `make[1]: *** [test-contract] Error 1`,
  `make: *** [test] Error 2`, exit 2 — so `test-integration` and all nine
  later `check` targets never executed. `make -k check` does not help: it
  continues to the sibling targets but still never runs `test-integration`,
  because the abort is inside the `test` recipe. The change edits
  `src/brichan/techstacks/resolver.py`, whose end-to-end coverage lives in
  `tests/integration/test_techstack_cli.py`, so the dynamic evidence that
  "production callers are unaffected" is exactly the evidence the gate skips.
  Worse, the plan's expected-failure list matches what the aborted run
  prints, so an implementer would correctly see only the two listed failures
  and declare step 6(c) satisfied while 222 integration tests and nine gates
  had not run. Step 6(c) must run the layers and gates individually and
  record each: `make test-unit`, `make test-contract`, `make
  test-integration`, then `techstack-eval`, `metrics`, `receipts`,
  `dossiers`, `memory-check`, `path-check`, `readme-check`,
  `phase5-preflight`, `package-check`.

### Medium

- `M1` — The residual-failure list omits a third pre-existing worktree-only
  failure. Once `H1` is fixed and the later gates actually run,
  `make path-check` fails from the same cause: `scripts/check_repository_paths.py`
  prints `unclassified root files: .git` and `make: *** [path-check] Error 1`.
  This review observed it in the `make -k check` baseline. The plan's
  "Expected residual failures" and requirements R7(a) name only the two
  `tests/contract/test_repository_paths.py` failures, so the implementer
  would meet an unlisted failure and have to decide alone whether it is
  theirs. It must be listed, with its shared `.git` cause.
- `M2` — Step 6(c) claims `make check` "includes the 3.10 shell interpreter
  and the repository's 3.14 gate". It does not. The Makefile has a single
  `PYTHON ?= python3` (`Makefile:3`) and no 3.14 target anywhere, so
  `make check` runs one interpreter — 3.10 in this shell. `techstacks/general.md`
  states the verification as `make check` exiting 0 on both 3.10 and 3.14,
  and `techstacks/python/tests.md` `TEST-001` asks for both. Believing the
  false parenthetical, the implementer would skip the second interpreter
  entirely. The 3.14 gate is a separate run with `PYTHON=` pointed at a 3.14
  interpreter; this review confirmed the unit layer is green there at
  baseline (1026 tests, `OK`, exit 0), which gives the implementer a clean
  comparison point.
- `M3` — The specified refusal tests pass against a defective guard, so they
  do not verify R3. Every value in the design's "Test design" is truthy
  (`errno_value=13`, `line=1`, `rule="LINE_SHAPE"`), while R3 and acceptance
  criterion 2 state the contract for any non-`None` value. A guard written
  `if errno_value or line or rule:` instead of `is not None` satisfies all
  five specified tests and still silently drops `errno_value=0` and
  `line=0` — and both are real values: `line=0` is what
  `normalize_document(..., attribute=True)` reports for a document-level leaf
  failure (`src/brichan/techstacks/markdown.py:358-361`), and a zero errno is
  producible by the helper frame
  (`src/brichan/techstacks/filesystem.py:647`). `diagnostic_detail("UNREADABLE_FILE",
  line=0)` returning the registry detail was observed directly in this
  review. Add `errno_value=0` and `line=0` cases to the refusal tests; rule
  `TEST-003` treats an assertion that cannot fail as a defect, and these are
  three assertions that cannot fail for the values most likely to be got
  wrong.
- `M4` — The design's safety argument for `_parse` rests on a docstring, and
  the change converts a future violation of it into a production exception.
  `_parse` forwards `error.line` and `error.rule` for every `MarkdownError`
  code (`src/brichan/techstacks/resolver.py:340-346`); the design's warrant
  is the `MarkdownError` docstring promising both are `None` for
  `INVALID_MAP`, `MAP_ROW_LIMIT`, and `SELECTOR_LIMIT`
  (`src/brichan/techstacks/markdown.py:113-125`). This review confirmed the
  promise holds today: `attribute=True` and the `end_rule`/`shape_rule`
  cursor arguments are passed only by `parse_leaf`
  (`src/brichan/techstacks/markdown.py:519-523` versus `782-791`), and every
  failure on the map path omits the rule
  (`src/brichan/techstacks/markdown.py:526,534,552,554,558` and `_parse_row`,
  `476-502`). But no test pins it, and after this change a regression stops
  being a silent drop and becomes a `ValueError` raised mid-resolution — exit
  70 `INTERNAL_ERROR` through the CLI's catch-all
  (`src/brichan/techstacks/cli.py:925-926`), and a raw `ValueError` out of
  `resolve_context` for library callers. Either pin the contract with a test
  asserting every `parse_map` failure carries `line is None and rule is
  None`, or make `_parse` state the decision explicitly the way step 4 makes
  `_add_located` state it. Rule `GENERAL-004` asks for a regression test
  behind an executable-behavior change, and this is the one behavior change
  the plan leaves unguarded.

### Low

- `L1` — R2's stated proof does not cover R2's own explicit-`None` clause.
  The enumeration omits inapplicable arguments, while both production callers
  pass all three explicitly every time
  (`src/brichan/techstacks/model.py:2247-2249,2337`). The digest is correct
  and reproducible, but it is silent about the only call shape production
  uses. The design's registry-wide equality test covers explicit `None` for
  slotless codes only — not `line=None, rule=None` for `FILESYSTEM_ERROR`,
  nor `errno_value=None` for `INVALID_LEAF`, which are precisely the two new
  guards. Extend the enumeration, or the equality test, to the
  all-three-explicit-`None` shape.
- `L2` — The R5 regression test is specified mock-only, when a stronger
  real-condition test is available and idiomatic here. This review reached
  the exact path with `ProjectMixin` plus `chmod(0)` on a selected rule file,
  no mock, matching the established pattern of `os.chmod(..., 0o000)` under
  `@unittest.skipIf(os.geteuid() == 0, ...)`
  (`tests/unit/test_techstack_filesystem.py:196-200,291-296,664-668`). Prefer
  the real condition for `UNREADABLE_FILE` and keep the mock only for
  `RESOURCE_LIMIT`, which `chmod` cannot produce.
- `L3` — Two non-blocking accuracy notes. R1 calls `diagnostic_detail` a
  "public signature", but it is absent from
  `src/brichan/techstacks/__init__.py:56-96`, so it is module-internal and no
  packaged public surface moves — which strengthens, rather than weakens,
  acceptance criterion 3. And design.md cites
  `DESIGN_DIAGNOSTIC_ROWS`/`DESIGN_DIAGNOSTIC_DETAILS` as "pinned in
  `tests/unit/test_techstack_model.py:554-568`", which is where they are
  asserted, not where they are defined. Neither changes the work.

## Test gaps

- No test pins refusal for a falsy non-`None` argument (`errno_value=0`,
  `line=0`), so `M3`'s defective guard ships green.
- No test pins the `MarkdownError` map-code contract that `_parse`'s safety
  now depends on (`M4`).
- No test exercises the byte-identity claim in the explicit-`None` call shape
  that both production callers use (`L1`).
- The plan's gate never runs `tests/integration/`, so no test at all
  exercises the edited `resolver.py` end to end under the plan as written
  (`H1`).
- The R5 regression test as specified asserts an assumed observation shape
  rather than the production chain that produces it (`L2`).

## Residual risks

- The refusal is a real behavior change on an internal function, so any
  unaudited caller added later fails loudly rather than silently. That is the
  point of the task; the residual risk is only that the failure surfaces
  inside resolution as `INTERNAL_ERROR` rather than at the misattributing
  call site. `M4` is the one place that risk is currently unguarded.
- `CHANGELOG.md` is outside the plan's authorized paths. No gate requires an
  entry — `tests/contract/test_repository_contract.py:352-360` pins only the
  version-to-changelog agreement — and `diagnostic_detail` is not public
  API, so this is a coordinator scope decision rather than a defect.
- The plan's open question stands and is correctly framed: writing this
  artifact clears its own diagnostics but `index.md`, `code-review.md`, and
  `pr-desc.md` remain in template state, so both the `dossiers` gate and
  `test_repository_checkout_validates_clean` keep failing until the
  coordinator brings them to a validating state. The carve-out is a
  coordinator decision, not something the implementer can clear.
- This review ran under the `claude` runtime on `claude-opus-5`, while
  `config/model-routing.json` gives the `review` route `codex` on
  `gpt-5.6-sol`. The reviewing session is independent of the planning session
  and the model is a different family from the planner's `claude-fable-5`, so
  reviewer independence and strength hold; recording the divergence from the
  route default is a coordinator-owned observation.

## Evidence

- `src/brichan/techstacks/model.py:557-596,2247-2261,2263-2287,2337` and
  `src/brichan/techstacks/resolver.py:243-244,266-290,340-346,509,742-747` —
  the reviewed caller graph, re-derived rather than accepted.
- `src/brichan/techstacks/filesystem.py:98-116,307-309,647` and
  `src/brichan/techstacks/markdown.py:113-125,344-361,415-426,519-523,782-791`
  — the two production feeds of inapplicable arguments and the docstring
  contract `M4` asks to be pinned.
- `Makefile:3,24-28,75` with the baseline runs of 2026-09-25 at commit
  `6fe3977`: `make check` exit 2 aborting at `test-contract` with the two
  `.git` failures and `test-integration` unreached; `make -k check` adding
  `dossiers` (42 issues, all this task's own artifacts) and `path-check`
  (`unclassified root files: .git`); `make test-integration` alone at exactly
  one failure; `make test-unit` green under both 3.10 and a 3.14 interpreter
  (1026 tests, `OK`).
- The design's enumeration reproduced at `calls: 122`, `sha256:
  57b96aa6d240374df464cd4b01d9f5f74cfd123240c3577b5eba1bc73d5167c0`, and a
  real `chmod(0)` resolution observing `diagnostic_detail` called as
  `("UNREADABLE_FILE", 13, None, None)` for the diagnostic
  `a required file could not be read`.
- `tests/unit/test_techstack_model.py:387-465,553-568`,
  `tests/unit/test_techstack_resolver.py:188-206,317,430-437`,
  `tests/unit/test_techstack_filesystem.py:196-200,291-296,664-668`,
  `tests/integration/test_techstack_cli.py:1034,1052,1081`, and
  `src/brichan/techstacks/__init__.py:56-96` — the existing coverage and
  public surface the findings rest on.
- Techstack Snapshot pointer:
  `projects/brida-workflow-simplification/handoffs/WFS-A-203/snapshots/attempt-plan-review-1-6a89e610b00a331b84767f79a2f3605a1d260a36bac05a5cf3ded449659e456f.snapshot.json`,
  sha256
  `6a89e610b00a331b84767f79a2f3605a1d260a36bac05a5cf3ded449659e456f`,
  verify status `match` on 2026-09-25 (attempt `attempt-plan-review-1`,
  acknowledged Context IDs `general`, `policy`, `policy-dossiers`, `python`,
  `python-runtime`, `python-tests`, `root`).

## Uncertainty

- Whether `H1`'s remedy should be a revised plan version or an
  implementer-side instruction is a coordinator decision; the finding is
  about the gate's coverage, not about the design of the change, so no design
  revision is implied by any finding in this review.
- No unresolved uncertainty remains about the reviewed code claims: every one
  was reproduced in this worktree at commit `6fe3977`.
