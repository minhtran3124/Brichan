# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `WFS-A-203`
- Task level: `1`
- Artifact: `plan-review`
- Artifact version: `2`
- Origin: `plan-review-worker:2026-09-25-wfs-a-203-plan-review-v2`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `93b15a50-f599-41ba-964f-94e1bcc84667`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `93b15a50-f599-41ba-964f-94e1bcc84667`
- Review verdict: `CHANGES REQUIRED`

## Review target

- Reviewed plan ID: `WFS-A-203-PLAN-001`
- Reviewed plan version: `2`

## Claim or decision

`CHANGES REQUIRED`. The design of the change is correct and is now verified by
construction, not by reading: this review applied design.md version 2's two
edits to a disposable copy of `src/` and `tests/`, reproduced the byte-identity
digest exactly, saw the techstack unit modules and the frozen eval stay green,
and confirmed by reverting only the resolver edit that step 4 is load-bearing.
Version 2 also closes all eight version-1 findings; each closure was checked
against the artifact it claims to change, and each holds.

Three defects remain, all in verification design rather than in the design of
the change. One is blocking: refusal class (b) of requirements R3 —
`INVALID_LEAF` given `errno_value` — has no removal-sensitive test under
design.md version 2 as written, because that call already raises `ValueError`
today, so acceptance criterion 2 is unmet for one of the three declared
classes. The other two are gate-coverage gaps in the R7 substitution for
`make check`: the 3.14 arm does not actually run the frozen eval under 3.14,
and one test module that `make check` runs is absent from the per-target list.

## Verified planner claims

Each was re-derived in this worktree at commit `6fe3977`; none is taken on the
planner's or the previous reviewer's word.

- `diagnostic_detail` is at `src/brichan/techstacks/model.py:583-596` with the
  signature requirements R1 freezes, and returns `DIAGNOSTIC_SPECS[code].detail`
  for every code but two. Observed silent drops:
  `diagnostic_detail("UNREADABLE_FILE", errno_value=13)`,
  `(..., errno_value=0)`, `(..., line=1)`, `(..., line=0)` and
  `(..., rule="LINE_SHAPE")` all return `a required file could not be read`;
  `diagnostic_detail("FILESYSTEM_ERROR", line=1)` returns the errno detail;
  `diagnostic_detail("INVALID_LEAF", errno_value=13, line=1, rule="TITLE")`
  returns the leaf detail.
- R1's version-2 correction is right: `diagnostic_detail` is absent from
  `__all__` (`src/brichan/techstacks/__init__.py:56-96`), so it is
  module-internal and no packaged public surface moves. Repository-wide it has
  exactly two callers, `src/brichan/techstacks/model.py:2247` and `:2337`, and
  no test calls it directly.
- Both callers stay safe under the guard: `_errno_value`
  (`src/brichan/techstacks/model.py:2255-2261`) returns `None` for every
  non-`FILESYSTEM_ERROR` code and `_leaf_slots`
  (`src/brichan/techstacks/model.py:2263-2287`) returns `(None, None)` for
  every non-`INVALID_LEAF` code.
- The call-site inventory is complete. Of the `findings.add` sites in
  `src/brichan/techstacks/resolver.py`, exactly one forwards `errno_value`
  (`_add_located`, `:266-277`, reached from `:290` and `:509`) and exactly one
  forwards `line`/`rule` (`_parse`, `:336-346`). `_approval_diagnostic`
  (`:115-118`) passes `context_id` only and the waiver rebuild (`:742-747`)
  passes no detail keyword. `errno_value` reaches nothing but
  `diagnostic_detail`: the factory (`src/brichan/techstacks/model.py:2318-2340`)
  stores no errno on the Diagnostic, so dropping it for non-`FILESYSTEM_ERROR`
  cannot move a field.
- The premise correction holds and step 4 is load-bearing, shown by
  construction rather than by argument. With design.md version 2's two edits
  applied to a disposable copy, a `ProjectMixin` resolution against a selected
  rule file at mode `0` produced `blocked` with exactly one diagnostic,
  `UNREADABLE_FILE` / `a required file could not be read` — byte-identical to
  the same probe on the unpatched copy. Reverting only the `_add_located` edit
  and rerunning raised
  `ValueError: UNREADABLE_FILE detail takes no arguments` out of
  `resolver.py:277` through `model.py:2344`, aborting resolution.
- The recorded baseline digest is exact. The design's version-2 enumeration
  reproduces `calls: 244`, `sha256:
  6a26f5041d52249b88d785bffb5b6fd826de46311ae5bc4cda15f7f7ea63ef69`, and
  reproduces the same digest after the two edits are applied. Its coverage
  claims hold: the registry has 58 rows (56 slotless), `LEAF_GRAMMAR_RULES`
  has 20 members, and `LEAF_FILE_BYTE_LIMIT + 1` is 65537; 56·2 + 6·2 + 3·20·2
  = 244.
- The `MarkdownError` map-code contract the design depends on holds today, so
  `M4`'s pinning test is well-posed. `parse_map` builds its cursor without
  `end_rule` or `shape_rule` (`src/brichan/techstacks/markdown.py:519-523`) and
  calls `normalize_document` without `attribute`, so every map failure —
  `cursor.fail()` (`:425`), `_parse_row` (`:476-502`), `SELECTOR_LIMIT`
  (`:497`), `MAP_ROW_LIMIT` (`:552`) — carries `line is None` and
  `rule is None`. The leaf path is safe for a different reason the design does
  not need to state: `parse_leaf` uses the single code `INVALID_LEAF`
  throughout (`:782-791`), which takes both slots.
- No behavior change escapes the two edited functions: applying them to a
  disposable copy left `tests.unit.test_techstack_model`,
  `test_techstack_resolver`, `test_techstack_markdown` and
  `test_techstack_filesystem` at 269 tests `OK`, identical to the unpatched
  copy, and `evals.techstack_context_v1.test_cases` at 56 tests `OK` in both.
- `H1`'s premise and remedy are correct. `check` lists `test` first
  (`Makefile:75`) and `test` runs its layers as sequential recipe lines
  (`Makefile:24-28`); this review observed `make test-contract` exit 1 on the
  two `.git` failures, which aborts `test` before `test-integration`.
- `M1`'s closure is correct and necessary: `make path-check` fails at baseline
  with `unclassified root files: .git`, and plan version 2 now lists it.
- The rest of the expected-red list is exact and complete for the gates that
  run. At baseline `make test-unit` is 1026 tests `OK`, `make test-integration`
  has exactly one failure, and `metrics`, `receipts`, `memory-check`,
  `readme-check`, `phase5-preflight` and `package-check` all pass.
- No documentation pins `diagnostic_detail`: it appears nowhere under `docs/`,
  `techstacks/`, `PRODUCT.md` or `AGENTS.md`, so the plan is right to authorize
  no doc edit.
- Option D's rejection still stands: `ValueError` registers nothing, while the
  `TechstackError` vectors are pinned by `CallerErrorRegistryTest`
  (`tests/unit/test_techstack_model.py:387-465`). The design fixtures are
  asserted at `tests/unit/test_techstack_model.py:553-568` and the cited test
  seams exist — `ProjectMixin` (`tests/unit/test_techstack_resolver.py:188-206`),
  the `read_project_file` patch precedent (`:317,428-437`), and the
  `chmod(0o000)` under `skipIf(os.geteuid() == 0, ...)` pattern
  (`tests/unit/test_techstack_filesystem.py:196-200`).

## Findings closure check (plan-review.md version 1)

Every row of plan.md's closure table was checked against the artifact it names.
`H1`, `M1`, `M2`, `M3`, `M4`, `L1`, `L2` and `L3` are all closed as described,
with two qualifications recorded as findings below: `M2`'s remedy leaves the
frozen eval un-run under 3.14 (`M1` below), and `M3`'s remedy is correct in
principle but one of its three arms is inert (`H1` below).

## Findings

### High

- `H1` — Refusal class (b) has no test that fails when its refusal is removed,
  so acceptance criterion 2 is unmet for one of the three declared classes.
  Requirements R3 declares class (b) as "`INVALID_LEAF` given `errno_value`",
  and design.md version 2 "Test design" specifies it as: "every code except
  `FILESYSTEM_ERROR` raises `ValueError` for `errno_value=13` and, separately,
  for `errno_value=0`". `INVALID_LEAF` is inside that set, but with no `line`
  and no `rule` it already raises `ValueError` today, before any new guard
  exists: `invalid_leaf_detail(None, None)` raises
  `INVALID_LEAF requires a line and a leaf grammar rule`
  (`src/brichan/techstacks/model.py:572-573`). This review observed, on the
  unpatched tree, `diagnostic_detail("INVALID_LEAF", errno_value=13)` and
  `(..., errno_value=0)` both raising exactly that. A loop written to the
  design's words therefore asserts `ValueError` for a call that raises
  `ValueError` with or without the new `if errno_value is not None` guard — an
  assertion that cannot fail, which rule `TEST-003` names a defect, and it is
  the only specified coverage of class (b). An implementer who omitted or
  inverted that one guard would ship a green suite. The remedy is small and
  belongs in design.md rather than in the implementer's discretion: the class
  (b) arm must supply slots the code does take alongside the errno, for example
  `diagnostic_detail("INVALID_LEAF", errno_value=13, line=1, rule="TITLE")` —
  which returns `leaf bytes do not match the leaf grammar at line 1: TITLE`
  today, observed, and must raise after the change — plus the falsy companion
  `errno_value=0` in the same shape. Classes (a) and (c) are unaffected: this
  review confirmed `FILESYSTEM_ERROR` with `line=1`, `line=0` or
  `rule="LINE_SHAPE"`, and every slotless code with any of the three, all
  return a detail today and so are genuinely removal-sensitive.

### Medium

- `M1` — The R7 gate's 3.14 arm does not run the frozen eval under 3.14, and
  both requirements R7 and plan step 6(c) state that it does. The recipe is
  `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
  evals.techstack_context_v1.test_cases -v` (`Makefile:39-40`) — a literal
  `python3`, not `$(PYTHON)`. This review ran
  `make techstack-eval PYTHON=/opt/homebrew/bin/python3.14` and `make -n` on
  the same target: the command executed is unchanged, so the second arm silently
  repeats the 3.10 run. `techstacks/python/tests.md` states this exact hazard in
  its Verification section — "The eval is run directly under both interpreters,
  because its recipe does not follow `PYTHON=`" — and `TEST-001` requires both
  interpreters for interpreter-sensitive change. The eval exercises techstack
  resolution, which this change edits, so the gap is material rather than
  formal. This is the same error class as version-1 finding `M2`, narrowed to
  one target: a stated 3.14 arm that does not reach the code. Step 6(c) must
  invoke the eval module directly under the 3.14 interpreter rather than
  through `make techstack-eval PYTHON=...`.
- `M2` — The per-target substitution for `make check` silently drops one test
  module, so the gate is not the equivalent it is presented as. `make test`
  runs `metrics/test_validate_metrics.py` as its own first recipe line
  (`Makefile:25`) before delegating to the three layers; `make metrics` runs
  `metrics/validate_metrics.py` twice and never that module
  (`Makefile:42-44`). Requirements R7 and plan step 6(c) list
  `test-unit`, `test-contract`, `test-integration` and the nine later gates,
  so under the substitution that module runs under neither interpreter, while
  the plan tells the implementer the per-target run is what `make check` would
  have done. It is green at baseline and unrelated to `src/brichan/techstacks`,
  so the risk is low — but the whole point of version-1 `H1`'s remedy was a
  gate whose coverage is stated truthfully, and an unstated hole reintroduces
  the same failure mode at smaller scale. Add the module to step 6(c), or state
  explicitly that it is excluded and why.

### Low

- `L1` — The expected-red attribution for `make dossiers` is incomplete in a
  way that does not change the implementer's work. Plan version 2 attributes
  those diagnostics to this task's pending `index.md`, `code-review.md` and
  `pr-desc.md`. This review's baseline run reports 39 issues, and one of them
  has a fourth cause: `receipt.md` does not exist in this dossier at all, so
  the validator reports
  `Task identity.Canonical receipt path: canonical receipt does not exist`.
  The cause is still coordinator-owned and outside the implementer's authorized
  paths, and `make receipts` passes at baseline, so nothing in the plan's
  instructions changes; the list should name it so the implementer does not
  have to decide alone whether a fourth diagnostic class is theirs.
- `L2` — Two accuracy notes, neither changing the work. First, requirements R3
  and design.md justify the `is not None` contract by saying the falsy values
  "exist in production": that is true of the values themselves, but neither
  reaches a code that does not take it. `line=0` is produced only by
  `normalize_document(..., attribute=True)`, which `parse_leaf` alone calls, so
  it accompanies `INVALID_LEAF`, which takes it
  (`src/brichan/techstacks/markdown.py:344-361,782-791`); and a zero errno from
  the bounded-helper frame (`src/brichan/techstacks/filesystem.py:645-650`) is
  dropped by step 4 once that edit lands. The `is not None` contract is still
  the right one — it is what makes the guard hold for callers added later, and
  what `H1` above turns on — but the stated warrant is stronger than the
  evidence supports. Second, plan.md records `Plan status: draft` while
  requirements, brief, options and design all record phase state `passed`; the
  dossier validator reads the artifact version, not this field, so it produced
  no diagnostic, but acceptance of version 2 is a coordinator step that this
  field still shows as outstanding.

## Test gaps

- Refusal class (b) is untested in the only sense acceptance criterion 2 asks
  for: no specified assertion distinguishes the guarded build from the
  unguarded one (`H1`).
- The frozen eval is untested under 3.14 despite the plan claiming it runs
  there, so an interpreter-sensitive regression in techstack resolution would
  not be caught by the gate as specified (`M1`).
- `metrics/test_validate_metrics.py` runs under neither interpreter (`M2`).
- No gap remains in the areas version 1 flagged. The falsy-value refusal cases
  exist for classes (a) and (c), the `MarkdownError` map-code contract is
  pinned, the byte-identity enumeration covers the all-three-explicit-`None`
  shape both production callers use, the integration layer runs, and the R5
  regression reaches the production chain through a real filesystem condition
  this review independently reproduced.

## Residual risks

- The refusal is a real behavior change on an internal function, so a caller
  added later that misattributes an errno, line or rule fails loudly inside
  resolution rather than at its own site. That is the task's intent; with
  `M4` closed by the markdown contract test, the one unpinned warrant is gone.
- The plan edits a production caller (`_add_located`) while acceptance
  criterion 3 asks that production callers be unaffected. This review treats
  that as satisfied rather than violated: the edit is necessary, demonstrated
  above by reverting it, and the diagnostics produced are byte-identical, shown
  on a real unreadable selected rule file. It remains a coordinator-visible
  deviation from the literal wording of the criterion.
- `CHANGELOG.md` stays outside the authorized paths. No gate requires an entry
  and `diagnostic_detail` is not public API, so this is a coordinator scope
  decision at close, not a defect.
- This dossier's `index.md`, `code-review.md` and `pr-desc.md` are still in
  template state and `receipt.md` is absent, so `make dossiers` and
  `tests/integration/test_task_dossier_workflow.py`
  `test_repository_checkout_validates_clean` keep failing until the coordinator
  brings them to a validating state. Writing this artifact clears only its own
  diagnostics.
- This review ran under the `claude` runtime on `claude-opus-5`, while
  `config/model-routing.json` gives the `review` route a different provider and
  model. The reviewing session is distinct from the planning session
  (`b6163b30-92ea-4643-be11-39ee7e5ad122`) and from the version-1 reviewing
  session (`db413ec3-ea03-4abd-a9bd-ca84f79808e5`), so reviewer independence
  holds; recording the divergence from the route default is a coordinator-owned
  observation.

## Evidence

- `src/brichan/techstacks/model.py:557-596,2247-2261,2263-2287,2318-2340` and
  `src/brichan/techstacks/resolver.py:115-118,243-244,266-290,336-346,509,742-747`
  — the caller graph and the factory's field handling, re-derived rather than
  accepted.
- `src/brichan/techstacks/markdown.py:113-125,344-361,405-426,519-523,782-791`
  and `src/brichan/techstacks/filesystem.py:98-116,307-309,645-650` — the
  map-code slot contract, the leaf path's single code, and the two production
  sources of falsy non-`None` values.
- Prototype verification of 2026-09-25 at commit `6fe3977`, on a disposable
  copy of `src/`, `tests/` and `evals/` outside the worktree: design.md version
  2's two edits applied; the enumeration reproducing `calls: 244`, `sha256:
  6a26f5041d52249b88d785bffb5b6fd826de46311ae5bc4cda15f7f7ea63ef69` both before
  and after; the four techstack unit modules at 269 tests `OK` and the eval at
  56 tests `OK` in both copies; a `ProjectMixin` resolution over a mode-`0`
  selected rule file yielding the same single `UNREADABLE_FILE` diagnostic in
  both; and, with only the `_add_located` edit reverted, the same probe raising
  `ValueError: UNREADABLE_FILE detail takes no arguments`.
- Pre-change probes on the unpatched tree recording every case design.md
  version 2's refusal tests specify, including
  `diagnostic_detail("INVALID_LEAF", errno_value=13)` and `(..., errno_value=0)`
  already raising `ValueError`, which is finding `H1`.
- `Makefile:3,24-28,39-44,75` with the baseline gate runs of 2026-09-25:
  `make test-contract` failing on the two `.git` failures and aborting `test`;
  `make path-check` failing with `unclassified root files: .git`;
  `make test-unit` at 1026 tests `OK`; `make test-integration` at exactly one
  failure; `metrics`, `receipts`, `memory-check`, `readme-check`,
  `phase5-preflight` and `package-check` all passing; and
  `make techstack-eval PYTHON=/opt/homebrew/bin/python3.14` executing bare
  `python3`, confirmed with `make -n`.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py projects`
  at baseline: 39 issues, every one naming this task's `index.md`,
  `code-review.md`, `pr-desc.md`, the absent `receipt.md`, or the superseded
  plan version reference this artifact replaces.
- `tests/unit/test_techstack_model.py:387-465,553-568`,
  `tests/unit/test_techstack_resolver.py:188-206,317,428-437`,
  `tests/unit/test_techstack_filesystem.py:196-200` and
  `src/brichan/techstacks/__init__.py:56-96` — the existing coverage, test
  seams and public surface the findings rest on.
- Techstack Snapshot pointer:
  `projects/brida-workflow-simplification/handoffs/WFS-A-203/snapshots/attempt-plan-review-2-947b545d9e6761a26d79c5e235132a165d497b85f38787bcc7c9bb9b9a6f0ea1.snapshot.json`,
  sha256
  `947b545d9e6761a26d79c5e235132a165d497b85f38787bcc7c9bb9b9a6f0ea1`,
  verify status `match` on 2026-09-25 (attempt `attempt-plan-review-2`,
  acknowledged Context IDs `general`, `policy`, `policy-dossiers`, `python`,
  `python-runtime`, `python-tests`, `root`).

## Uncertainty

- Whether `H1`'s remedy warrants a plan version 3 or an amendment to design.md
  alone is a coordinator decision. The finding is about one arm of one
  specified test, not about the design of the change, so no code-design
  revision is implied by any finding in this review.
- No unresolved uncertainty remains about the reviewed code claims. Every one
  was reproduced in this worktree at commit `6fe3977`, and the design's two
  edits were executed on a disposable copy rather than reasoned about.
