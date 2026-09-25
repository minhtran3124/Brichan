# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `WFS-A-203`
- Task level: `1`
- Artifact: `plan-review`
- Artifact version: `3`
- Origin: `plan-review-worker:2026-09-25-wfs-a-203-plan-review-v3`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `0d8fd148-56ad-4a5f-a9e4-43052ed437e1`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `0d8fd148-56ad-4a5f-a9e4-43052ed437e1`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `WFS-A-203-PLAN-001`
- Reviewed plan version: `3`

## Claim or decision

`PASS`. Following plan version 3 meets all four acceptance criteria of the
recorded request, every claim its artifacts make about the code is true, and
the change set is both complete and minimal: nothing necessary is missing and
nothing unnecessary is added. This review did not read the plan and agree with
it — it executed it. The design's two edits were applied to a full disposable
copy of the worktree; the 244-call byte-identity digest was reproduced
unchanged; all three test layers returned results identical to the unpatched
copy; each of the three refusal guards was removed one at a time and the
design's specified test arms were shown to fail in exactly the removed guard's
class; and the same arms were shown to fail against a guard weakened to
truthiness.

Version 3 closes all five findings of plan-review version 2, including the
blocking `H1`. The class (b) arm that version 2 showed could not fail now can:
on the unguarded tree
`diagnostic_detail("INVALID_LEAF", errno_value=13, line=1, rule="TITLE")`
returns `leaf bytes do not match the leaf grammar at line 1: TITLE`, and
omitting the `errno_value is not None` guard makes that arm fail — reproduced
here by removing the guard.

Two findings remain, both `low` and neither blocking. One is a wording
contradiction inside design.md's own byte-identity proof that would make a
strict code reviewer reject a correct diff; the other is the last unstated
hole in the per-target substitution for `make check`. Neither changes the code
the implementer writes, and neither puts an acceptance criterion at risk.

## Verified planner claims

Re-derived in this worktree at commit `6fe3977` (clean tree, `git status
--short` empty). Nothing below is taken on the planner's or either previous
reviewer's word.

- The reviewed function is where R1 freezes it.
  `diagnostic_detail(code, *, errno_value=None, line=None, rule=None)` is at
  `src/brichan/techstacks/model.py:583-589`, its body is
  `:592-596`, and `invalid_leaf_detail`'s slot requirement is exactly
  `src/brichan/techstacks/model.py:572-573` as design.md and R6 cite it.
- The public-surface claim holds. `diagnostic_detail` appears nowhere in
  `src/brichan/techstacks/__init__.py`, so no packaged public signature is in
  play; repository-wide the function has exactly two callers,
  `src/brichan/techstacks/model.py:2247` and `:2337`, and no test calls it
  directly.
- Both callers are safe under the guard. `_errno_value`
  (`src/brichan/techstacks/model.py:2255-2262`) returns `None` for every
  non-`FILESYSTEM_ERROR` code and `_leaf_slots` (`:2264-2288`) returns
  `(None, None)` for every non-`INVALID_LEAF` code, so
  `Diagnostic.__post_init__` always passes the all-three-explicit shape with
  `None` in every inapplicable slot.
- The call-site inventory is complete. Of the 30 `findings.add` sites in
  `src/brichan/techstacks/resolver.py`, exactly one forwards `errno_value`
  (`_add_located`, `:266-277`, reached from `:290` and `:509`) and exactly one
  forwards `line`/`rule` (`_parse`, `:340-346`). Every other site passes only
  `path` and `context_id`. `_approval_diagnostic` (`:115-118`) passes
  `context_id` alone and the waiver rebuild (`:742-747`) passes no detail
  keyword. The factory (`src/brichan/techstacks/model.py:2318-2340`) stores no
  errno on the Diagnostic, so dropping an errno for a non-`FILESYSTEM_ERROR`
  code cannot move a field.
- The premise correction holds and step 4 is load-bearing, shown by
  construction. With the design's two edits applied to a full disposable copy,
  a `ProjectMixin` resolution over a selected rule file at mode `0` produced
  `blocked` with exactly one diagnostic, `UNREADABLE_FILE` /
  `a required file could not be read` — byte-identical to the unpatched copy.
  The observation really does carry an errno: instrumenting
  `read_project_file` showed `code='UNREADABLE_FILE' errno_value=13`. With
  only the `_add_located` edit reverted, the same probe raised
  `ValueError: UNREADABLE_FILE detail takes no arguments` out of
  `resolver.py:277` through `model.py:244`/`diagnostic`, aborting resolution.
- The recorded baseline digest is exact and its coverage claims hold. The
  design's enumeration reproduces `calls: 244`, `sha256:
  6a26f5041d52249b88d785bffb5b6fd826de46311ae5bc4cda15f7f7ea63ef69`, and
  reproduces the same 244 calls and the same digest under the guarded form and
  under every single-guard-removed variant. The registry has 58 rows
  (56 slotless), `LEAF_GRAMMAR_RULES` has 20 members and contains both `TITLE`
  and `LINE_SHAPE`, and `LEAF_FILE_BYTE_LIMIT + 1` is 65537;
  56*2 + 6*2 + 3*20*2 = 244.
- Every refusal arm design.md version 3 specifies returns a detail on the
  unguarded tree, so every one is removal-sensitive. Observed at baseline:
  the class (b) arms `("INVALID_LEAF", errno_value=13, line=1, rule="TITLE")`
  and the `errno_value=0` companion both return
  `leaf bytes do not match the leaf grammar at line 1: TITLE`; the class (a)
  arms `("FILESYSTEM_ERROR", line=1)`, `(..., line=0)` and
  `(..., rule="LINE_SHAPE")` all return
  `filesystem operation failed with errno -1`; and all 56 slotless codes
  return their registry detail for each of `errno_value=13`,
  `errno_value=0`, `line=1`, `line=0` and `rule="LINE_SHAPE"` — zero
  exceptions across 280 calls.
- Removal sensitivity is proven per guard, not asserted. Running the design's
  full specified test set against five variants of the guarded function: the
  complete form fails no arm; dropping the `FILESYSTEM_ERROR` guard fails
  exactly the 3 class (a) arms; dropping the `INVALID_LEAF` errno guard fails
  exactly the 2 class (b) arms; dropping the slotless guard fails 280 arms;
  and rewriting all three guards on truthiness fails 114 arms, including every
  `errno_value=0` and `line=0` case. All five variants reproduce the 244-call
  digest, confirming that no variant touches a valid call.
- `R4`'s `KeyError` precedence survives the guarded form. Under the design's
  code `diagnostic_detail("NO_SUCH_CODE")` and
  `diagnostic_detail("NO_SUCH_CODE", line=1)` both raise `KeyError`, because
  the `DIAGNOSTIC_SPECS[code]` lookup precedes the third guard.
- No behavior change escapes the two edited functions. On a full disposable
  copy of the worktree, patched and unpatched runs are identical layer for
  layer: `tests/unit` 1026 tests `OK` in both; `tests/contract` 148 tests with
  the same 5 failures and 1 error in both; `tests/integration` 222 tests with
  the same 3 failures and 1 error in both (the extra contract and integration
  reds are artifacts of the copy having no real Git directory, and are the
  same on both sides); the four techstack unit modules 269 tests `OK` in both;
  `evals.techstack_context_v1.test_cases` 56 tests `OK` in both.
- The `MarkdownError` map-code contract the design depends on holds today, so
  the version-3 pinning test is well-posed. `parse_map`
  (`src/brichan/techstacks/markdown.py:519-523`) builds its cursor with no
  `end_rule` and no `shape_rule` and calls `normalize_document` without
  `attribute`, so `cursor.fail()` with no rule (`:421-426`), every
  `_parse_row` raise (`:476-502`), `SELECTOR_LIMIT` (`:497`) and
  `MAP_ROW_LIMIT` (`:552`) all carry `line is None` and `rule is None`. The
  leaf path is safe for the reason the design gives: `parse_leaf` (`:782-791`)
  uses the single code `INVALID_LEAF`, which takes both slots.
- Every test seam the plan relies on exists. `ProjectMixin`
  (`tests/unit/test_techstack_resolver.py:188-214`), the `read_project_file`
  patch precedent (`:317`, `:430-437`), the
  `chmod(0o000)` under `skipIf(os.geteuid() == 0, ...)` pattern
  (`tests/unit/test_techstack_filesystem.py:196-200,291-296,664-668`),
  `MapGrammarTest` with `MAP_ROW_LIMIT` and `SELECTOR_LIMIT` payloads
  (`tests/unit/test_techstack_markdown.py:192,313,321`), and the design
  fixtures asserted by `DiagnosticRegistryTest`
  (`tests/unit/test_techstack_model.py:553-568`). `RESOURCE_LIMIT` is field
  class `G` and `Observation(code=..., errno_value=...)` is a valid
  construction, so the mock-only second resolver arm is well-formed.
- `M1`'s premise is exact. `make -n techstack-eval
  PYTHON=/opt/homebrew/bin/python3.14` prints
  `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
  evals.techstack_context_v1.test_cases -v` — a literal `python3`
  (`Makefile:39-40`), not `$(PYTHON)` — so the plan is right that
  `make techstack-eval PYTHON=...` silently repeats the 3.10 run. The
  replacement the plan specifies works: the direct invocation under
  `/opt/homebrew/bin/python3.14` (Python 3.14.6) is 56 tests `OK` at baseline.
- `M2`'s premise is exact and its remedy verified. `make test` runs
  `metrics/test_validate_metrics.py` as its own first recipe line
  (`Makefile:25`) and `make metrics` never runs it (`Makefile:42-44`). The
  module is 10 tests `OK` at baseline under both interpreters — the shell
  `python3` (3.10.11) and `/opt/homebrew/bin/python3.14`.
- The `make check` abort the plan cites is real. `check` lists `test` first
  (`Makefile:75`) and `test` runs its layers as sequential recipe lines
  (`Makefile:24-28`); `PYTHONDONTWRITEBYTECODE=1 make test-contract` exits 1
  here, which aborts `test` before `test-integration`, so the plan is right to
  refuse the single-command substitution.
- The expected-red list is exact and complete for the gates that run.
  `make test-contract` is 148 tests with exactly 2 failures, both
  `unclassified root files: .git`
  (`tests/contract/test_repository_paths.py:64,159`), and this worktree's
  `.git` is a 95-byte regular file. `make path-check` fails with the same
  `unclassified root files: .git`. `make test-integration` is 222 tests with
  exactly one failure, the dossier workflow test. `make dossiers` reports
  39 issues, and all 39 name this task's `index.md`, `code-review.md`,
  `pr-desc.md`, the absent `receipt.md`
  (`canonical receipt does not exist`), or this artifact's superseded plan
  version reference; none names a planner-owned artifact. The plan's
  arithmetic is right: 38 before plan version 3 existed, 39 once the
  `Reviewed plan version: ... found '2'` diagnostic appeared.
- Option D's rejection still stands: `ValueError` registers nothing, while the
  `TechstackError` code vectors and fixed details are pinned by
  `CallerErrorRegistryTest` (`tests/unit/test_techstack_model.py:387-465`), so
  adding a code would move a frozen contract that acceptance criterion 3
  forbids.
- Scope is unchanged from planning. The plan's Snapshot
  (`attempt-plan-3-008ff53c...`) verifies `match` in this worktree at
  `--as-of 2026-09-25`, and its scope paths and context chains are identical
  to this review's Snapshot (`attempt-plan-review-3-ac166c55...`), so the
  plan's "no re-resolution needed" claim is checkable and true.

## Findings closure check (plan-review.md version 2)

Every row of plan.md's closure table was checked against the artifact it names
and against the code. All five hold.

| Version-2 finding | Verdict | Evidence checked |
|---|---|---|
| `H1` (class (b) refusal test could not fail) | Closed | design.md "Test design" now gives class (b) a dedicated slots-supplied arm and excludes `INVALID_LEAF` from the class (c) errno loop; R6 states the same shape as a requirement. Verified by execution: the arm returns a detail at baseline, and removing the `INVALID_LEAF` errno guard fails exactly it and nothing else. The superseded slotless shape still raises today, so its exclusion was correct. |
| `M1` (3.14 arm never ran the frozen eval) | Closed | Plan step 6(c) and R7 replace `make techstack-eval PYTHON=...` with the direct 3.14 module invocation. `make -n` confirms the recipe pins literal `python3`; the direct invocation is 56 tests `OK` at baseline under 3.14.6. |
| `M2` (`metrics/test_validate_metrics.py` ran under neither interpreter) | Closed | Plan step 6(c) adds the module explicitly on both arms; R7 matches. 10 tests `OK` at baseline under 3.10.11 and 3.14.6. |
| `L1` (expected-red attribution omitted the absent `receipt.md`) | Closed | Plan "Expected residual failures" names the fourth cause with the validator's own wording; the diagnostic is present in this review's baseline run and is coordinator-owned. |
| `L2` (overstated falsy warrant; `Plan status: draft` beside `passed`) | Closed | R3, brief.md and design.md now say the falsy values are production-real but that neither reaches a code that does not take it today, and that `is not None` is warranted as the contract a later caller must hit and as what the falsy tests assert — which this review confirmed is exactly what the truthiness variant fails. Plan's new "Plan status" section states why `draft` is correct while acceptance is outstanding. |

Version-1 findings `H1`, `M1`-`M4` and `L1`-`L3` remain closed. This review
re-checked each independently rather than relying on version 2's check:
`path-check` is named in the residual list (`M1`); the falsy-value arms exist
and are removal-sensitive (`M3`); the `MarkdownError` pinning test is
specified and well-posed (`M4`); the enumeration and the registry-wide
equality test both cover the all-three-explicit-`None` shape (`L1`); the R5
regression has a real-`chmod` arm, which this review reproduced (`L2`); and
R1's module-internal correction is right (`L3`). Version-1 `H1`'s gate remedy
carries the two residual gaps recorded below as `L2` and under residual risks.

## Findings

### Low

- `L1` — design.md version 3 states half of its byte-identity proof in a form
  its own code block contradicts, which would make a strict code reviewer
  reject a correct diff. "Byte-identity proof" item 1 and the "Decisions the
  implementer must keep" bullet both say "The three return expressions are
  textually unchanged", and plan step 3 tells the implementer to keep "the
  three return expressions ... unchanged". But the guarded form in design.md
  rebinds the third one: today's `return DIAGNOSTIC_SPECS[code].detail`
  (`src/brichan/techstacks/model.py:596`) becomes
  `detail = DIAGNOSTIC_SPECS[code].detail` ... `return detail`. The two are
  value-identical and this review reproduced the 244-call digest unchanged
  with exactly the design's code, so no acceptance criterion is at risk; the
  operative proof is the digest, not the textual claim. The cost is process,
  not correctness: a code reviewer applying proof half 1 literally to the diff
  will find the third return expression changed. The correction is one line —
  say the three returned *values* are unchanged, or spell the third branch
  `return DIAGNOSTIC_SPECS[code].detail` after the guard while keeping the
  `DIAGNOSTIC_SPECS[code]` lookup ahead of it so `KeyError` still wins
  (`R4`). Either form satisfies `R2` and `R4`; both were exercised here.
- `L2` — The per-target substitution for `make check` still omits one `check`
  recipe line, so the gate is marginally narrower than it is presented as.
  `check` is its ten prerequisites plus `sh -n bin/brichan`
  (`Makefile:75-76`). Plan step 6(c) and R7 now cover all ten prerequisites
  and, per version-2 `M2`, `metrics/test_validate_metrics.py`; nothing covers
  the launcher syntax check. The risk is nil: `bin/brichan` is not an
  authorized implementation path, no authorized path can change it, and
  `sh -n bin/brichan` is green at baseline (observed). It is reported because
  version-2 `M2`'s remedy was a gate whose coverage is stated truthfully, and
  this is the last unstated hole in it. One clause naming it as excluded, and
  why, closes it; no run needs to be added.

## Test gaps

- None blocking. Each of the three refusal classes of `R3` now has specified
  coverage that this review proved fails when its guard is removed, and the
  falsy-value arms fail a guard weakened to truthiness. The registry-wide
  equality test plus the 244-call enumeration cover `R2` including its
  explicit-`None` clause; `R4`'s `KeyError` precedence is covered with and
  without an extra keyword; `R5` is covered through the production chain by a
  real `chmod` condition and, for the class-`G` branch that no real condition
  can reach, by a mock; and the `MarkdownError` map-code promise the design
  newly depends on is pinned.
- `sh -n bin/brichan` is the only step of `make check` the gate does not run
  (`L2`). It cannot regress from any authorized path.
- No test pins the `ValueError` message wording. This is deliberate — design.md
  records the wording as a reviewed proposal, and pinning it would be
  implementation-coupled — and `R3`'s style requirement (lowercase, names the
  code) is met by the proposed messages, which match
  `invalid_leaf_detail` and `Diagnostic._check_location`
  (`src/brichan/techstacks/model.py:573-579,2296-2304`). Not a gap to close.
- The plan adds no test for the pre-existing behavior that a waivable code
  rebuilt at `src/brichan/techstacks/resolver.py:742-747` is re-rendered with
  no detail keywords. This is correctly out of scope: no waivable code takes a
  detail slot, and the guard cannot change that path because all three
  arguments are `None` there.

## Residual risks

- The plan edits a production caller (`_add_located`) while acceptance
  criterion 3 asks that production callers be unaffected. This review treats
  that as satisfied rather than violated, on the same basis version 2 did and
  now re-verified: the edit is necessary — reverting only it makes real
  resolution raise — and the diagnostics produced are byte-identical on a real
  unreadable selected rule file. It remains a coordinator-visible deviation
  from the criterion's literal wording.
- Acceptance criterion 4's literal evidence is never produced: the plan
  deliberately never runs `make check`, because in this worktree it aborts
  inside `test`. The coordinator-ratified per-target run stands in
  (client-follow-up-questions.md version 2), and with `L2` noted it is
  otherwise a faithful superset of what `check` would have executed. That
  artifact's own uncertainty note is the standing condition: on the main
  checkout with a closed dossier, every gate must be green.
- The refusal is a real behavior change on an internal function. A caller
  added later that misattributes an errno, line or rule fails loudly inside
  resolution rather than at its own site. That is the task's intent, and the
  one unpinned warrant it rested on — the `MarkdownError` map-code contract —
  is pinned by the version-3 test design.
- `CHANGELOG.md` stays outside the authorized paths. No gate requires an entry
  and `diagnostic_detail` is not public API, so this is a coordinator scope
  decision at close, not a defect.
- This dossier's `index.md`, `code-review.md` and `pr-desc.md` are still in
  template state and `receipt.md` is absent, so `make dossiers` and
  `tests/integration/test_task_dossier_workflow.py`
  `test_repository_checkout_validates_clean` keep failing until the
  coordinator brings them to a validating state. Writing this artifact clears
  only its own diagnostic, taking the count from 39 to 38.
- Route and provider divergence, for the coordinator to record.
  `config/model-routing.json` gives the `review` route runtime `codex`, model
  `gpt-5.6-sol`, effort `medium`; this review ran on the `claude` runtime as
  `claude-opus-5` at effort `high`, as did reviews 1 and 2. Reviewer
  independence by session holds — this session
  (`0d8fd148-56ad-4a5f-a9e4-43052ed437e1`) is distinct from the version-3
  planning session (`9e873e25-e1da-4639-8f3b-5ef21cedbba8`) and from both
  earlier reviewing sessions (`db413ec3-ea03-4abd-a9bd-ca84f79808e5`,
  `93b15a50-f599-41ba-964f-94e1bcc84667`) — but `docs/policy/reviewer.md`
  prefers a different verified provider, and all three rounds of planning and
  review have now run on the same runtime.
- One methodological caution for the code reviewer, learned here.
  `tests/unit/test_techstack_resolver.py:22` inserts this worktree's `src`
  at the front of `sys.path`, so running a test module with `PYTHONPATH`
  pointed at a patched copy of `src` alone silently exercises the worktree's
  unpatched code instead. Every construction result above was obtained on a
  full copy of the tree, with the imported module paths printed and checked.

## Evidence

- `src/brichan/techstacks/model.py:557-596,2247-2262,2264-2288,2318-2340` and
  `src/brichan/techstacks/resolver.py:115-118,243-244,266-290,340-346,509,742-747`
  — the caller graph, the two detail helpers and the factory's field handling,
  re-derived rather than accepted; plus
  `src/brichan/techstacks/__init__.py` showing `diagnostic_detail` absent from
  the packaged surface.
- `src/brichan/techstacks/markdown.py:113-125,344-361,405-426,519-523,782-791`
  and `src/brichan/techstacks/filesystem.py:98-116,303-309,645-650` — the
  map-code slot contract, the leaf path's single code, the closed errno
  mapping that makes the silent-drop path production-reachable, and the two
  production sources of falsy non-`None` values.
- Construction verification of 2026-09-25 at commit `6fe3977`, on full
  disposable copies of the worktree outside it: design.md version 3's two
  edits applied; the enumeration reproducing `calls: 244`, `sha256:
  6a26f5041d52249b88d785bffb5b6fd826de46311ae5bc4cda15f7f7ea63ef69` before
  and after; `tests/unit` 1026 `OK`, `tests/contract` 148 and
  `tests/integration` 222 with results identical on both copies, the four
  techstack modules 269 `OK` and the eval 56 `OK` on both; a `ProjectMixin`
  resolution over a mode-`0` selected rule file yielding the same single
  `UNREADABLE_FILE` / `a required file could not be read` diagnostic on both;
  and, with only the `_add_located` edit reverted, the same probe raising
  `ValueError: UNREADABLE_FILE detail takes no arguments`.
- Guard-variant execution of the full specified test set at the same commit:
  the complete guarded form fails no arm; each guard removed in turn fails
  exactly its own class's arms (3, 2 and 280 arms); a truthiness rewrite fails
  114 arms including every `errno_value=0` and `line=0` case; all five
  variants reproduce the 244-call digest. This is the direct evidence that
  version-2 `H1` is closed and that the class (a) and (c) arms remain sound.
- Baseline probes on the unpatched tree recording every refusal arm design.md
  version 3 specifies: 280 slotless-code calls all returning their registry
  detail, the three `FILESYSTEM_ERROR` class (a) calls returning the errno
  detail, the two class (b) slots-supplied calls returning the leaf detail,
  and the superseded slotless class (b) calls still raising `ValueError`.
- `Makefile:3,24-28,39-44,75-76` with baseline gate runs of 2026-09-25:
  `make test-contract` 148 tests with exactly 2 `.git` failures, aborting
  `test`; `make path-check` failing with `unclassified root files: .git`;
  `make test-integration` 222 tests with exactly one failure;
  `make -n techstack-eval PYTHON=/opt/homebrew/bin/python3.14` printing bare
  `python3`; the direct 3.14 eval 56 tests `OK`;
  `metrics/test_validate_metrics.py` 10 tests `OK` under 3.10.11 and 3.14.6;
  and `sh -n bin/brichan` exiting 0.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py
  projects` at baseline: exit 1, `Invalid task dossiers: 39 issue(s) across 8
  dossier(s)`, all 39 lines naming this task's `index.md`, `code-review.md`,
  `pr-desc.md`, the absent `receipt.md`, or the superseded plan version
  reference this artifact replaces.
- `tests/unit/test_techstack_model.py:387-465,553-568`,
  `tests/unit/test_techstack_resolver.py:22,188-214,317,430-437`,
  `tests/unit/test_techstack_filesystem.py:196-200,291-296,664-668` and
  `tests/unit/test_techstack_markdown.py:192,313,321` — the existing coverage
  and the test seams the plan's step 5 depends on.
- `versions/v1/plan-review.md` and `versions/v2/plan-review.md` — the two
  earlier reviews whose findings the closure table above was checked against,
  read byte-frozen and not edited (`DOSSIER-003`).
- Techstack Snapshot pointer:
  `projects/brida-workflow-simplification/handoffs/WFS-A-203/snapshots/attempt-plan-review-3-ac166c55717e3653582eb43fe389cc2d98884a8812240c136cdbee65c1d47073.snapshot.json`,
  sha256
  `ac166c55717e3653582eb43fe389cc2d98884a8812240c136cdbee65c1d47073`,
  verify status `match` on 2026-09-25 (attempt `attempt-plan-review-3`,
  acknowledged Context IDs `general`, `policy`, `policy-dossiers`, `python`,
  `python-runtime`, `python-tests`, `root`; all seven selected rule files
  read). The plan's own Snapshot `attempt-plan-3-008ff53c...` also verifies
  `match` here, with identical scope paths and context chains.

## Uncertainty

- No unresolved uncertainty remains about the reviewed code claims or about
  the plan's sufficiency. Every claim was re-derived at commit `6fe3977`, and
  the design's two edits and the removal sensitivity of every specified test
  arm were executed rather than reasoned about.
- Whether the two `low` findings are corrected before the plan is accepted, or
  carried as notes for the code reviewer, is a coordinator decision. Neither
  changes the code the implementer writes; `L1` changes one sentence of
  design.md and one clause of plan step 3, and `L2` changes one clause of plan
  step 6(c). This review does not make them conditions of `PASS`.
