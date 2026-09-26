# Code review

Independent review of the implementation, or the recorded evidence for why no implementation review applies.

## Artifact metadata

- Task ID: `WFS-A-203`
- Task level: `1`
- Artifact: `code-review`
- Artifact version: `1`
- Origin: `code-review-worker:2026-09-25-wfs-a-203-code-review-v1`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `84451be0-1122-4e9d-8966-6654f57ed140`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `84451be0-1122-4e9d-8966-6654f57ed140`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `WFS-A-203-PLAN-001`
- Reviewed plan version: `3`

Reviewed artifact: the uncommitted working tree at base commit `6fe3977`,
five modified files, `git diff --stat` = 187 insertions, 2 deletions. The
implementer's evidence is `implementation.md` version 1; this review treated
it as a claim to check, not as proof. Neither this authoring session nor this
reviewing session authored the plan (`9e873e25-e1da-4639-8f3b-5ef21cedbba8`)
or the plan review (`0d8fd148-56ad-4a5f-a9e4-43052ed437e1`).

## Claim or decision

Verdict: `PASS`. The change meets all four acceptance criteria of plan
`WFS-A-203-PLAN-001` version 3, and this review proved the two that are
provable rather than accepting the implementer's report: a 3776-case
differential over the full argument cross-product shows zero previously valid
calls whose returned detail changed and zero refusals that the guards over- or
under-apply, and one-guard-at-a-time removal shows each of the three refusal
classes has a test that fails when its guard is removed. No defect was found.
One medium test gap and one low evidence-wording inaccuracy are recorded
below; neither blocks acceptance.

## Scores

| Criterion | Score | Basis |
|---|---|---|
| Spec fidelity | 5 | All four acceptance criteria hold. Criterion 1 is proven, not asserted: the 244-call enumeration digest is identical on both trees, and an independent 3776-case differential over the full argument cross-product found zero changed return values and zero removed refusals. Criterion 2 holds for all three refusal classes under one-guard-at-a-time removal and under a truthiness rewrite. Criterion 3 holds: the diff moves no registry row, cap, literal, sort key, fixture, or signature, and both `diagnostic_detail` call sites are enumerated. Criterion 4 is met through the coordinator-ratified per-target substitute for `make check`, which this review re-ran in full on both interpreters. |
| Code review | 4 | The two production edits are correct, minimal, and byte-identical to the accepted design blocks; no regression survived a 3776-case differential or a 4104-input `parse_map` fuzz. One point is withheld for the new conditional at `src/brichan/techstacks/resolver.py:274`, whose preserved `FILESYSTEM_ERROR` branch is reachable production behavior that no test pins (finding `M1`); the change introduces the branch and leaves it unguarded against a later regression. |
| Empirical verification | 5 | Every quantitative claim in `implementation.md` reproduced exactly on this session's own runs: the 244-call digest, all six removal-sensitivity variant counts (3 / 2 / 281 / 114 / 2 errors), the 13-row gate table on both interpreters, and the 40 dossier-validator issues with their ownership. No claim was accepted without a command. The working tree has not changed since the last successful check: `git status --short` shows the same five modified paths, and this review re-ran the complete gate against that tree. |

Total: 14 / 15.

## Findings

No defect was found. Nothing in the diff violates the objective, an
acceptance criterion, or an established project invariant. The two entries
below are a test gap and an evidence-wording inaccuracy; neither blocks.

### `M1` (medium) — the new conditional's `FILESYSTEM_ERROR` branch is unpinned

`src/brichan/techstacks/resolver.py:274-278` introduces
`if code != "FILESYSTEM_ERROR": errno_value = None`. The `!=` is load-bearing
in the other direction too: `FILESYSTEM_ERROR` is genuinely reachable from
production resolution (`_errno_outcome`,
`src/brichan/techstacks/filesystem.py:307-309`, returns it as the default for
any errno outside `_ERRNO_OUTCOMES`), and its detail is the one detail that
renders the errno. Nothing fails if that branch is neutered.

Reproduction, on a disposable full copy of `src/` and `tests/`:

```
# replace line 274 with: if True:  # drop errno for every code
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest \
  tests.unit.test_techstack_model tests.unit.test_techstack_resolver \
  tests.unit.test_techstack_markdown
# -> Ran 193 tests ... OK
```

Corroborating: `grep -rn '"FILESYSTEM_ERROR"' tests/ evals/` returns no hit in
`tests/unit/test_techstack_resolver.py` or `tests/integration/`. The code is
correct as written; the gap is that a future edit collapsing the condition
would silently start emitting `filesystem operation failed with errno -1` in
place of the real errno, with every suite green. This is a newly created gap:
before the change `_add_located` had no conditional to break. Classified as a
test gap rather than a defect because acceptance criterion 2 concerns
refusals, which are covered, and `GENERAL-004` is satisfied by
`ObservationErrnoTest`, which does pin the branch the change altered.

### `L1` (low) — `implementation.md` overstates the call-site inventory

`implementation.md`, "Production call sites": "These are the only callers of
`diagnostic_detail` in the repository. No test or packaged export calls it."
The second sentence is false as of this change: `tests/unit/test_techstack_model.py`
calls `model.diagnostic_detail` at lines 672, 676, 685, 689, 694, 697, 711,
717, 728, 732, and 734 — the report's own new tests. Verified by
`grep -rn "diagnostic_detail" src/ tests/ evals/ scripts/`. The intended claim
(only two *production* callers, and no packaged export) is true and was
independently confirmed: `src/brichan/techstacks/model.py:2259`
(`Diagnostic.__post_init__`) and `src/brichan/techstacks/model.py:2349` (the
`diagnostic` factory), with `diagnostic_detail` absent from
`src/brichan/techstacks/__init__.py`. No check depends on the wording.

## Verification performed by this review

All commands ran from the worktree root with `PYTHONDONTWRITEBYTECODE=1`.

### Techstack scope

`bin/brichan techstacks verify` against the `attempt-code-review-1` Snapshot
at `--as-of 2026-09-25` returned `"status": "match"` with
`observed_snapshot_sha256` equal to the expected digest. All seven selected
rule files were read before any other work.

### Acceptance criterion 1 — byte identity, proven

- The design's 244-call enumeration, run against the edited worktree module
  and against a clean `git archive HEAD` copy of `src/`, printed the imported
  module path each time and gave `calls: 244`, sha256
  `6a26f5041d52249b88d785bffb5b6fd826de46311ae5bc4cda15f7f7ea63ef69` on both.
- Independently of the implementer's evidence, this review ran a differential
  over the full cross-product of every registry code plus one unknown code
  times `errno_value` in `(None, -1, 0, 13)` times `line` in
  `(None, 0, 1, 99999999)` times `rule` in `(None, "TITLE", "LINE_SHAPE",
  "BOGUS_RULE")` — 3776 cases — recording the returned string or the raised
  exception type on each tree and comparing. Result: 176 cases identical,
  3600 cases that returned a string before and now raise `ValueError`, **0
  cases whose returned value changed**, **0 cases that raised before and now
  return**, and **0 unjustified refusals** (every one of the 3600 supplies a
  non-`None` argument the code has no slot for). This is the strongest
  available form of the criterion: it proves the guards are exactly
  co-extensive with the slotless argument set, neither over- nor
  under-refusing.
- The implemented function body is byte-identical to the design.md version 3
  block: `diff` of `design.md:42-67` against
  `src/brichan/techstacks/model.py:583-608` is empty. The `_add_located` edit
  likewise matches the design block verbatim, comment included.

### Acceptance criterion 2 — removal-sensitive refusals

Each variant was built on a disposable full copy of `src/` and `tests/` and
exercised with the three new-test modules (193 tests).

| Variant | Result | Failing arms |
|---|---|---|
| Unmodified copy | `OK` | none |
| `FILESYSTEM_ERROR` guard (`model.py:598-599`) removed | 3 failures | class (a)+(c) `line`/`rule` arm |
| `INVALID_LEAF` errno guard (`model.py:602-603`) removed | 2 failures | class (b) arm only |
| Slotless guard (`model.py:606-607`) removed | 281 failures | class (c) errno, class (a)+(c) `line`/`rule`, factory propagation |
| All three guards rewritten on truthiness | 114 failures | every `errno_value=0` and `line=0` case |
| `_add_located` edit reverted | 2 errors | `ObservationErrnoTest`, both tests |
| Restored | `OK` | none |

Every count matches `implementation.md`. Each of the three distinct refusal
classes therefore has at least one test that fails when its guard is removed,
and the `is not None` identity form is pinned against a truthiness weakening,
satisfying `TEST-003`.

The reverted-`_add_located` errors are real, not assertion artifacts:
`ValueError: UNREADABLE_FILE detail takes no arguments` and
`ValueError: RESOURCE_LIMIT detail takes no arguments` raised mid-resolution.
The first arises from a real `chmod 0o000` condition on a selected rule file,
not a mock, so the resolver edit is load-bearing for production behavior, as
the plan's scope finding claims.

### Acceptance criterion 3 — frozen contracts and call sites

- The complete diff touches only: the `diagnostic_detail` docstring and three
  guards; the `_add_located` conditional and its comment; three test files.
  No registry row, cap, literal, sort key, fixture, fixture digest, or public
  signature is in the diff, and `git status --short` shows no other path.
- Production call sites of `diagnostic_detail`: `model.py:2259` and
  `model.py:2349` only, confirmed by repository-wide grep; not exported from
  the package `__init__`.
- Sites that pass a detail keyword into the `diagnostic` factory:
  `resolver.py:280,282` (`_add_located`) and `resolver.py:345-350` (`_parse`).
  `_parse` forwards `MarkdownError.line`/`.rule` for `INVALID_MAP`,
  `MAP_ROW_LIMIT`, `SELECTOR_LIMIT`, and `INVALID_LEAF`, so the new slotless
  guard would raise mid-resolution if a map-class failure ever carried either.
  This review checked that promise two ways, because it is the one place the
  change could turn a diagnostic into a crash:
  - Statically: `parse_map` builds its cursor with `end_rule` and `shape_rule`
    left `None` (`markdown.py:523`, against the signature at
    `markdown.py:398-404`), every `parse_map` failure calls `cursor.fail()`
    with no rule, and `_parse_row`, `MAP_ROW_LIMIT`, and `SELECTOR_LIMIT`
    raise `MarkdownError(code)` bare. Every rule-carrying `fail(...)` site
    lives in the leaf-grammar section below `markdown.py:566`, reachable only
    from `parse_leaf`.
  - Empirically: 4104 mutated inputs (line deletions, insertions, case and
    whitespace mutations at every line, 4000 random byte mutations, and the
    encoding and terminator edge cases) were fed to `parse_map`; 3835 raised
    `MarkdownError`, all `INVALID_MAP`, and **0 carried a non-`None` `line`
    or `rule`**.
  - `resolver.py:747`, the waiver rewrite, forwards no detail keyword, so the
    new guards cannot fire there.
  The root/API error path is unaffected: `PROJECT_ROOT_FILESYSTEM_ERROR` is
  rendered by `root_api_error_for_code` (`model.py:401-410`), a separate
  function that does not call `diagnostic_detail`.

### Acceptance criterion 4 — the gate

`make check` was confirmed unusable as a single command in this worktree: it
aborts inside its `test` prerequisite at `test-contract` on the two known
`.git` failures, so `test-integration` and all ten later gates never run
(`Makefile:24-28,75`). The coordinator-ratified per-target substitute
(`client-follow-up-questions.md` version 2) covers every constituent of the
`check` recipe, including the `metrics/test_validate_metrics.py` line and
`sh -n bin/brichan`. This review ran all of it independently.

| Check | 3.10.11 | 3.14.6 |
|---|---|---|
| Focused three modules | 193 tests `OK` | n/a |
| `make test-unit` | 1035 tests `OK` | 1035 tests `OK` |
| `make test-contract` | 148 tests, 2 failures (expected) | 148 tests, 2 failures (expected) |
| `make test-integration` | 222 tests, 1 failure (expected) | 222 tests, 1 failure (expected) |
| Frozen eval | `make techstack-eval`, 56 tests `OK` | run directly, 56 tests `OK` |
| `metrics/test_validate_metrics.py` direct | 10 tests `OK` | 10 tests `OK` |
| `make metrics` | exit 0 | exit 0 |
| `make receipts` | exit 0, 46 receipts | exit 0, 46 receipts |
| `make dossiers` | exit 2 (expected), 40 issues | exit 2 (expected), 40 issues |
| `make memory-check` | exit 0 | exit 0 |
| `make path-check` | exit 2 (expected) | exit 2 (expected) |
| `make readme-check` | exit 0 | exit 0 |
| `make phase5-preflight` | exit 0 | exit 0 |
| `make package-check` | exit 0 | exit 0 |
| `sh -n bin/brichan` | exit 0 | n/a |

The 3.14 arm invoked the frozen eval directly, because the `techstack-eval`
recipe pins a literal `python3` and does not follow `PYTHON=`
(`Makefile:39-40`).

Every failure is on the ratified expected-red list and none is attributable to
the change:

- `tests/contract/test_repository_paths.py::test_current_path_and_link_contracts_pass`
  and `::test_every_non_ephemeral_root_file_is_classified`, both
  `unclassified root files: .git` — the two worktree-only failures named in
  the task packet. Reported, not fixed.
- `make path-check`, same `.git` cause.
- `tests/integration/test_task_dossier_workflow.py::test_repository_checkout_validates_clean`
  and `make dossiers`. All 40 validator issues were classified by artifact:
  29 name this task's `index.md`, 5 `pr-desc.md`, 5 `code-review.md`, and 1
  the absent canonical `receipt.md`. None names a planner- or
  implementer-owned artifact, and none names a source or test file. The count
  of 40 rather than the plan's projected 38 is explained by the two extra
  `index.md` diagnostics `implementation.md` already documents, which this
  review observed verbatim.

`make test-unit` on 3.14 emits a pre-existing `SyntaxWarning` from
`tests/unit/test_handoff_receipt_validator.py`, outside this task's paths and
not a failure.

## Test gaps

1. **`M1` above.** Nothing pins that `_add_located` still forwards the errno
   when the code *is* `FILESYSTEM_ERROR`. Closing it needs one resolver test
   in the shape of the existing `ObservationErrnoTest` class-`G` arm: inject
   an observation with `code="FILESYSTEM_ERROR"` and a real errno and assert
   the rendered detail names that errno rather than `-1`. Recommended, not
   required for this task.
2. The new markdown slot-contract test
   (`tests/unit/test_techstack_markdown.py:324`) pins `line is None and
   rule is None` for `parse_map` failures only. The symmetric leaf promise —
   that every `parse_leaf` failure *is* attributed, since an unattributed
   `INVALID_LEAF` raises in `invalid_leaf_detail` — remains unpinned. This is
   pre-existing and unchanged by the diff; the fuzz above gives this review
   independent confidence in the map half, which is the half the change
   depends on.
3. No test pins the three `ValueError` message strings. The design version 3
   states this deliberately ("the exact wording above is the reviewed proposal
   and may be adjusted in review without a design revision"), so this is a
   recorded decision, not an omission. The refusal class and exception type,
   which are the contract, are pinned.
4. The refusal is unreachable from production by construction after the
   `_add_located` edit, so no integration-level test exercises a refusal
   end to end. That is the intended design — the guard is a contract for
   future callers — and is correctly covered at the unit level instead.

## Residual risks and required human decisions

1. **A production caller was edited.** Acceptance criterion 3 says
   "production callers are unaffected"; `_add_located` is a production caller
   and it changed. Its *output* is unaffected — proven by the unchanged
   enumeration digest, by the unchanged resolver, contract, integration, and
   frozen-eval results, and by the fact that the dropped value was already
   being discarded inside `diagnostic_detail` — but the letter of the
   criterion is met only on the substance. This was raised and decided before
   implementation (plan version 3 "Scope findings"; plan-review version 3
   `PASS`), and `implementation.md` flags it honestly. No further decision is
   needed unless the coordinator wants the criterion's wording amended in the
   receipt.
2. **`plan.md` version 3 contradicts itself on plan status.** The metadata
   field reads `Plan status: accepted` while the "Plan status" section
   immediately below argues that "`draft` is correct while coordinator
   acceptance is outstanding". Under `DOSSIER-004` an evidence file should not
   carry two statements that disagree. This is planner- and
   coordinator-owned, outside this review's write scope, and it is the direct
   cause of two of the 40 validator issues (the `index.md` accepted-plan-ID
   and accepted-plan-version diagnostics fire precisely because the field says
   `accepted`). Coordinator decision at close.
3. **The expected-red list is worktree- and in-flight-specific.** On the main
   checkout with a closed dossier, `make check` must be green as one command;
   nothing in this review demonstrates that, and nothing can until the
   worktree and dossier states are resolved.
4. **`CHANGELOG.md`** was left untouched, per the plan. `diagnostic_detail` is
   not public API and no gate requires an entry, so whether the refusal
   deserves a changelog line is a coordinator decision.
5. **Writing this artifact changes the dossier validator output.** The 40-issue
   baseline recorded above was taken with `code-review.md` in template state
   (5 of the 40 issues). With this artifact in place the validator reports 36
   issues: the 5 template diagnostics are cleared and the `code-review` row of
   `index.md` now mismatches on applicability and phase state instead. Both
   remaining diagnostics are `index.md` template state, coordinator-owned, and
   on the ratified expected-red list; they clear when the coordinator fills
   `index.md`. Re-run of `PYTHONDONTWRITEBYTECODE=1 python3
   scripts/validate_task_dossiers.py projects` after writing this file:
   `Invalid task dossiers: 36 issue(s) across 8 dossier(s)`, with no issue
   naming a source file, a test file, or a planner- or implementer-owned
   artifact.

## Evidence

- The reviewed diff: `git diff`, `git status --short`, and
  `git diff --stat` (5 files, 187 insertions, 2 deletions) at base commit
  `6fe3977`, read in full.
- `src/brichan/techstacks/model.py:583-608` (the guarded
  `diagnostic_detail`), `:557-580` (both helpers, unchanged), `:2247-2296`
  (`Diagnostic.__post_init__`, `_errno_value`, `_leaf_slots`), `:2337-2352`
  (the `diagnostic` factory), `:401-420` (the separate root/API detail path).
- `src/brichan/techstacks/resolver.py:266-282` (`_add_located`), `:284-295`
  (`_observation_diagnostic`), `:340-352` (`_parse`), `:740-752` (the waiver
  rewrite).
- `src/brichan/techstacks/markdown.py:113-140` (the `MarkdownError` slot
  promise), `:344-365` and `:395-465` (`normalize_document`, `_Cursor`),
  `:519-563` (`parse_map`), `:566-780` (the leaf-grammar helpers),
  `:782-794` (`parse_leaf`).
- `src/brichan/techstacks/filesystem.py:95-116,307-309` (the errno mapping and
  the `FILESYSTEM_ERROR` default), `:940-1011` (the root error path).
- This session's own runs of 2026-09-25 recorded above: the Techstack verify
  (`match`), the 244-call enumeration on both trees, the 3776-case
  differential, the 4104-input `parse_map` fuzz, the seven removal-sensitivity
  variants, the neutered-`FILESYSTEM_ERROR`-branch probe, the full gate on
  both interpreters, and the artifact-ownership classification of all 40
  dossier-validator issues.
- `implementation.md` version 1 (checked, not trusted), `plan.md` version 3,
  `design.md` version 3, `plan-review.md` version 3, and
  `client-follow-up-questions.md` version 2.
- `docs/policy/reviewer.md`, `docs/workflows/task-dossier.md`, and the seven
  selected rule files of the Snapshot below.
- Techstack Snapshot pointer:
  `projects/brida-workflow-simplification/handoffs/WFS-A-203/snapshots/attempt-code-review-1-6f02061b8e9cc61a0db8e65763ca32ded935b2383d33c2037da4814ff92cf160.snapshot.json`,
  sha256
  `6f02061b8e9cc61a0db8e65763ca32ded935b2383d33c2037da4814ff92cf160`,
  verify status `match` on 2026-09-25 (attempt `attempt-code-review-1`,
  acknowledged Context IDs `general`, `policy`, `policy-dossiers`, `python`,
  `python-runtime`, `python-tests`, `root`).

## Uncertainty

- One residual uncertainty, and it is not resolvable from this worktree: no
  evidence here shows `make check` green as a single command, because the
  detached worktree's `.git` file makes that impossible regardless of this
  change. The ratified per-target substitute is complete with respect to the
  `check` recipe and was run in full, which is the strongest statement this
  environment supports.
- Everything else this review asserts was produced by a command run in this
  session against the tree under review. No implementer claim was accepted
  on report alone.
