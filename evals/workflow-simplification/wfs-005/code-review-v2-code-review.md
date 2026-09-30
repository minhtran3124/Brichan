# Code review

Independent review of the implementation, or the recorded evidence for why no implementation review applies.

## Artifact metadata

- Task ID: `WFS-005`
- Task level: `2`
- Artifact: `code-review`
- Artifact version: `2`
- Origin: `wfs-005-code-rereview-worker:2026-09-26:v2`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `code-review-session-d0a06235`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `code-review-session-d0a06235`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `WFS-005-PLAN-001`
- Reviewed plan version: `3`

## Review provenance

- This is artifact version 2, a re-review after Fix 1
  (`WFS-005-FIX-1`, attempt `attempt-implement-2`). Version 1 returned
  `CHANGES REQUIRED` on one blocking Medium, M1, and is archived byte-frozen at
  `versions/v3/code-review.md` (DOSSIER-003). This version supersedes it in
  place and carries its non-blocking Lows forward; it does not redo the whole
  review.
- This review is the stronger one-off review override the user authorized for
  WFS-005 (`client-follow-up-questions.md` v1: "Run now, Claude reviewers"), so
  the `review` route's configured runtime and model
  (`config/model-routing.json`: codex, `gpt-5.6-sol`, medium) were overridden to
  a Claude reviewer at high effort. The override is recorded, not silent.
- Reviewing session `code-review-session-d0a06235` is a fresh session. It is
  not the plan's authoring session (`plan-session-8ec2b29b`), not the plan
  review's reviewing session (`review-session-faf2990c`), not the version 1
  review's session (`code-review-session-c6a70f04`), and not the implementation
  or fix worker's session (attempts `attempt-implement-1` and
  `attempt-implement-2`). I did not implement any part of this change or of
  Fix 1.
- Reviewed state: the uncommitted working tree of branch
  `feat/lifecycle-simplification`, 20 modified tracked files and 4 new files.
  `.codex/config.toml`,
  `projects/brida-workflow-simplification/decisions.md`, `tasks.md`, and the
  untracked directory under `evals/workflow-simplification/wfs-005` are
  coordinator or user files and were excluded, as the packet directs.

## Verdict

`PASS`. M1 is closed by execution, not by assertion: Fix 1's new test fails
when the guard is removed and passes with it, and the fix changed nothing else.
The whole change is +11 insertions and 0 deletions away from the state version 1
reviewed, all eleven lines in one test file. Every version 1 `PASS` judgment
re-confirmed on re-check. The gate is green on Python 3.10.11 and 3.14.6 with
only the two reds the packet sanctions, and both of those name WFS-005's own
pending coordinator artifacts and nothing else.

Nine Low findings are recorded and none blocks. Eight are carried forward from
version 1; one, L9, is new — found while re-confirming coordinator condition M1,
and it does not reopen that condition, because I proved the affected path
unreachable.

## Per-criterion scores

| Criterion | Score | Basis |
| --- | --- | --- |
| Spec fidelity | 5/5 | Unchanged from version 1. Fix 1 stayed inside its stated scope (close M1 only, no production file changed) and I verified that by diff arithmetic, not by reading the report: insertions went 1580 to 1591 with deletions fixed at 208, and `src/brichan/contracts/task_dossier/validation.py` still hashes to `8a5a4059863ffae79efc826f79615f9027e3d17ad5b0f7781557ad6c340a67d0`, the value the implementer recorded before the mutation runs. |
| Code review | 5/5 | Raised from 4/5. The one blocking gap is closed by a test that really kills the mutant. The four remaining untested new lines (L1-L4) are each defensive depth over an already-caught or already-pinned state, or presentational, and I re-verified L1 by mutation rather than carrying the claim. |
| Empirical verification | 5/5 | Independently reproduced in this session, not read from the report: the mutation proof, both full gates, the eval directly under 3.14, the dossier sweep over `projects`, and the level-2 escape, partial-adoption, fail-closed and byte-unchanged probes. |

## Findings

### M1 — closed. The unreadable-artifact presence filter now has a committed regression test that kills the mutant

Version 1's one blocking finding is closed. I verified it by execution, on a
copy of `src` and `tests` in a scratch directory outside the repository.

The test is
`tests/unit/test_task_dossier_validator.py:1089`,
`ReducedDossierValidatorTest.test_an_unreadable_plan_does_not_excuse_the_report`,
beside `test_a_symlinked_plan_does_not_excuse_the_report`. It builds a valid
full dossier, asserts it valid, overwrites `plan.md` with non-UTF-8 bytes, and
asserts both that the diagnostics contain `required task-dossier artifact
report.md is missing` and that they contain `plan.md: file: cannot read
artifact`. The second assertion is what pins the test to the unreadable arm
rather than the symlink arm, so the two arms cannot pass for each other.

Reproducing commands, all on the scratch copy:

```bash
# baseline
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest \
  tests.unit.test_task_dossier_validator
# -> Ran 83 tests, OK

# the version 1 mutant: replace the filter with an unconditional add
#   artifacts[name] = parse_artifact(path, name, diagnostics)
#   present.add(name)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest \
  tests.unit.test_task_dossier_validator
# -> Ran 83 tests, FAILED (failures=1)
# -> FAIL: test_an_unreadable_plan_does_not_excuse_the_report
```

The mutant that survived in version 1 now dies, and it kills exactly one test:
the new one. I checked that it kills nothing else by running the other dossier
suites under the same mutant and comparing against the scratch baseline —
`tests.unit.test_task_dossier_generator`,
`tests.unit.test_task_dossier_summary`, `tests.unit.test_contract_paths` and
`tests.contract.test_task_dossier_contract` give the identical result mutated
and unmutated (153 run, 6 failures, 119 errors, all of them scratch-copy
artifacts from the absent `docs` tree and `Makefile`, not behavior). I also ran
the inverted mutant (`if not any(` to `if any(`): 15 failures, including both
the new test and the symlink test, which matches what the fix report claims.

The filter under test is
`src/brichan/contracts/task_dossier/validation.py:117-122`, and the mechanism is
worth stating because it is not local: the filter governs `present`, `present`
feeds `required_artifacts(level, present)`
(`validation.py:1228`), and that is what decides whether `report.md` is
required. `_validate_presence` itself keys on `artifacts`, which still holds the
unreadable file. So the guard is load-bearing exactly one call away from where
it is written, which is why an untested version of it was worth blocking on.

The repository's own `validation.py` was never edited: its SHA-256 is
`8a5a4059863ffae79efc826f79615f9027e3d17ad5b0f7781557ad6c340a67d0` before and
after all mutation runs, and `git status --short` shows no new modification.

### Fix 1 changed nothing else

Checked three independent ways rather than taken from the report:

1. Diff arithmetic. `implementation.md:213` records the pre-fix tree as 20
   modified tracked files, 1580 insertions, 208 deletions, 4 new files.
   `git diff --stat` now reports 20 modified tracked files, 1591 insertions,
   208 deletions, and the same 4 new files. That is +11 insertions and exactly
   zero deletions. The new test, with its leading blank line, is 11 lines. No
   other change of any kind fits in that budget, and nothing was removed.
2. Content. `src/brichan/contracts/task_dossier/validation.py` hashes to the
   value the implementer froze. `git diff --stat -- src/brichan/resources` is
   empty.
3. Test count. The unit tier went 1061 to 1062 on both interpreters — one test
   added, none removed or renamed.

### Coordinator corrections to `implementation.md`

Both corrections are in place, in the section that made the claim, with no later
section contradicting an earlier one, so DOSSIER-004 is met.

- The TEST-003 claim (version 1's L7) is corrected at
  `implementation.md:173`, inside the same paragraph, naming the code review and
  the date and stating which mutations survived. See L7 below for the one
  residual.
- The stale risk item is corrected at `implementation.md:255`, rewritten to
  open "Resolved (corrected in place by the coordinator on 2026-09-26: captures
  redacted)", with the superseded text kept as an explicit "Was:". The Outcome
  paragraph at `implementation.md:14-17` carries the matching correction. I
  verified the underlying claim rather than accepting it:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest
  tests.contract.test_repository_contract` runs 18 tests, OK, so
  `test_durable_artifacts_do_not_embed_home_paths` passes and the item is
  genuinely closed.

### L1 — Low, not blocking. `_validate_presence`'s symlink skip is invisible to the suite

Carried forward, and re-verified by mutation in this session rather than
restated. `src/brichan/contracts/task_dossier/validation.py:134` skips the
missing-file diagnostic when the required path is a symlink. Removing
`or path.is_symlink()` leaves `tests.unit.test_task_dossier_validator` at 83
tests, OK. The regression's effect is one extra, redundant diagnostic beside the
existing `dossier artifacts must not be symlinks` one, so the validator becomes
noisier rather than weaker, and the symlink refusal itself stays tested by
`test_a_symlinked_plan_does_not_excuse_the_report`. Does not block: no contract
statement depends on the suppressed duplicate.

### L2 — Low, not blocking. The index-template contiguity guard is untested

Carried forward from version 1. `src/brichan/contracts/task_dossier/scaffold.py:91`
raises when the index template's status rows are not contiguous; replacing the
check with `pass` fails no test. It guards a template whose eleven rows are
already pinned by
`test_index_template_links_authorities_without_duplicating_them`, so the state
it defends against cannot reach a released tree. Does not block: defensive depth
on an already-pinned input.

### L3 — Low, not blocking. `record_artifacts`' ordering is redundant, so its mutation survives

Carried forward from version 1. `src/brichan/contracts/task_dossier/generate.py:153`
re-orders the record's keys into `RECOGNIZED_ARTIFACTS` order; returning
`tuple(record.artifacts)` instead fails no test, because `record.py`'s loader
already builds `record.artifacts` by iterating `RECOGNIZED_ARTIFACTS`, so the
input is always ordered. Does not block: the property is real and enforced one
layer down, and rendering order is cosmetic.

### L4 — Low, not blocking. The summary's unreadable-row sort is untested

Carried forward from version 1. `src/brichan/contracts/task_dossier/summary.py:246`
sorts the unreadable rows into lifecycle order; removing the sort fails no test.
Presentation only, and the summary is explicitly a non-authority. Does not
block.

### L5 — Low, not blocking. The contract-path checker treats empty input as "no contract path"

Carried forward, and re-run in this session.
`src/brichan/contracts/task_dossier/contract_paths.py:56-76` returns exit 0 and
prints `contract-path: no` on empty stdin:

```bash
printf '' | PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_contract_paths.py
# contract-path: no        exit=0
printf 'docs/policy/x.md\n' | PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_contract_paths.py
# contract-path: yes       exit=3
printf '\xff\xfe\n' | PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_contract_paths.py
# contract-path: input is not UTF-8 path names; refusing to decide    exit=2
```

In the documented pipeline (`docs/workflows/task-dossier.md`, Contract paths) a
`git diff` that fails — a bad dispatch base, a wrong worktree, a forgotten pipe
— produces empty stdout, and an ordinary shell does not propagate the upstream
exit status, so the checker answers "no review needed" from no evidence.

Does not block: this is the behavior the accepted design specifies (exit 0 no, 3
yes, 2 invalid invocation or undecodable input), and the workflow document states
the trust boundary explicitly — the level 0 decision is the coordinator's and is
recorded with the checker's output. Worth a follow-up sentence recommending
`set -o pipefail`, or an `--expect-nonempty` flag, since the cheapest failure
mode of a safety check should not be silence.

### L6 — Low, not blocking. The legacy `plan`-satisfies rule is not restricted to legacy dossiers

Carried forward from version 1, and re-confirmed by probe in this session.
`required_artifacts` (`src/brichan/contracts/task_dossier/schema.py:314-322`)
drops `report` whenever `plan` is present, with no condition on the dossier's
age, so a brand-new Level 0 or Level 1 task can carry `plan.md` instead of
`report.md` and never write the mandated `Plan`, `Changes`, `Verification`,
`Risks` structure that R2 and R3 describe as the lifecycle. A level 0 dossier
holding `index`, `request`, `plan`, `code-review` and no report validates with
zero diagnostics under `--require-complete`.

Does not block. This is the plan review's shape (a), which plan version 3
adopted deliberately to close C1 without an exemption list, and
`docs/workflows/task-dossier.md` states it plainly ("At levels 0 and 1 a present
`plan.md` carries the plan, so `report.md` is then not required"). Nothing is
escaped — a level 1 task still needs a mandatory independent code review, and a
present `plan.md` validates under the full plan rules. Recorded so the
coordinator knows the report structure is a documented obligation, not a
mechanical one.

### L7 — Low, not blocking. The corrected TEST-003 paragraph still states the wrong sentence before correcting it

Version 1's L7 is closed: the coordinator corrected the claim in place at
`implementation.md:173`, per DOSSIER-004, and named this review as the source.

The residual is editorial. The corrected paragraph still reads "... and the
summary report arm). Each removal failed its named test. Corrected in place by
the coordinator on 2026-09-26, per code review L7: that claim was too strong."
The false sentence is retained verbatim immediately before its own retraction,
so a reader quoting the paragraph's fourth sentence alone would quote the wrong
record. The correction is in place and unambiguous in context, which is what
DOSSIER-004 requires, so this is a wording preference, not a contract breach.
Does not block: strike or rewrite the sentence at the next edit of that file, if
the file is edited again at all.

### L8 — Low, not blocking. Presence and review-target rules key on different sets

Carried forward from version 1. `_validate_unplanned_review_targets` keys on
`"plan" in artifacts` (`src/brichan/contracts/task_dossier/validation.py:556`)
while `required_artifacts` keys on the stricter `present` set. An unreadable —
not symlinked — `plan.md` therefore both requires `report.md` and forbids null
review targets at once. Only reachable in a dossier that is already invalid for
the unreadable file, so no valid state is affected. Does not block. Fix 1's new
test exercises exactly this state and its diagnostics show both rules firing,
which is the intended fail-closed direction.

### L9 — Low, not blocking, new in this version. One fail-open `.get` default survives in `validation.py`, and `implementation.md` claims none does

Found while re-confirming coordinator condition M1. Version 1 did not report it.

`src/brichan/contracts/task_dossier/validation.py:365` reads:

```python
    minimum = MINIMUM_EVIDENCE_ITEMS.get(level, 1)
```

`implementation.md:128-129` states of the four tools that "None of them keeps a
`.get(level, 1)`-style fail-open lookup." That sentence is literally false: this
is one, spelled exactly that way, and its default `1` is the *shallowest*
evidence floor, the opposite of failing closed.

Condition M1 is nevertheless met, and I do not reopen it, because the default is
unreachable. `_validate_state` is called only at `validation.py:1235`, with the
`level` returned by `_resolve_level` (`validation.py:1155-1181`), which returns
either a member of `TASK_LEVELS` or `resolve_task_level(level)`; both are always
valid keys, so the `.get` can never take its default. I proved that on the
production path rather than by reading it — a reduced level 0 dossier whose
`index.md` declares `Task level: bogus` is validated against the level 2 floor:

```
index.md:   Evidence: level 2 requires at least 3 concrete evidence item(s), found 1
request.md: Evidence: level 2 requires at least 3 concrete evidence item(s), found 1
report.md:  Evidence: level 2 requires at least 3 concrete evidence item(s), found 1
```

The floor is 3, not the `.get` default's 1. I also swept for siblings: this is
the only remaining defaulted lookup of a level in the four tools.
`record.py:817` and `summary.py:162,240` go through `resolve_task_level`,
`schema.py:322` resolves before indexing, `scaffold.level_artifacts` raises
`ValueError` on an unknown level (`scaffold.py:71-75`), and the generator CLI
refuses through argparse `choices` (`generate.py:673`).

Does not block: no behavior is wrong, no acceptance criterion or condition is
violated, and no test is owed for an unreachable branch. Two cheap follow-ups,
neither required: index directly (`MINIMUM_EVIDENCE_ITEMS[level]`) so the
invariant is enforced rather than papered over, and correct the sentence at
`implementation.md:128-129`, which is the kind of blanket claim that L7 was
already about.

## Test gaps

Per the rule this change adds (`docs/policy/reviewer.md:29-32`), a behavior
change without a committed regression test that would fail on regression is a
defect, not a test gap, so such items are filed as findings above. Restated as a
checklist:

- The version 1 blocking gap is closed. The unreadable-plan arm of the
  fail-closed presence rule now has a committed test that kills the mutant, and
  I reproduced both the kill and the baseline.
- L1-L4, not blocking: four new lines whose removal the suite cannot detect. L1
  and L2 defend states that are already caught or already pinned, L3 is
  redundant with the record loader, and L4 is presentational. A test for each is
  optional, not owed.
- L9, not blocking: `validation.py:365`'s default is unreachable, so no test is
  owed for it. Indexing instead of defaulting would remove the question.
- No new gap was introduced by Fix 1. It added a test and changed nothing else.

What is not a gap, carried forward from version 1 and unchanged: the tests this
change lands are substantive. Version 1 confirmed by mutation that the
fail-closed level fallback, the `report.md` back-write guard, report-author
independence in both the validator and the record loader, the level 1/2 review
mandate, report concreteness, the status-table absent-row rule, the legacy
`plan` rule, the symlink arm, null review targets, level-keyed scaffolding,
generated status rows, completion narrowing, partial adoption of `report`, and
the contract-path list each have at least one test that fails when the guard is
removed. I re-verified the two that Fix 1 touches the neighborhood of (the
unreadable arm and the symlink arm) and did not re-run the other twelve, since
no production line changed.

## Residual risks

1. Level self-declaration stays a documented, reviewer-checked exposure. A task
   that declares the wrong level at creation time gets that level's reduced set,
   and no mechanical check contradicts it. This is the version 2 plan review's
   M2 residual and the workflow document states it. Everything downstream of the
   declaration is enforced: I re-confirmed that declaring level 2 while carrying
   only the reduced four yields 16 diagnostics, eight missing-file and eight
   status-table, and that downgrading a valid level 2 dossier by editing only
   `index.md` yields 14 diagnostics from four independent rules at once.
2. The contract-path checker's silence on empty input (L5). A broken pipe in the
   documented level 0 workflow reads as "no contract path". The decision is the
   coordinator's and is recorded with the checker's output, so the risk is
   procedural, not mechanical.
3. The legacy `plan`-satisfies rule applies to new tasks too (L6), so the
   `Plan`, `Changes`, `Verification`, `Risks` report structure is an obligation
   the reviewer enforces, not one the validator does.
4. Plan-before-implementation order inside `report.md`, and the Level 0
   contract-path review decision, are trust boundaries no tool can verify. The
   workflow document states both.
5. The contract-path membership (the `src/brichan` and `scripts` prefixes)
   remains a reversible user judgment, per the plan's Uncertainty. It stays a
   one-line, one-tuple-entry, one-test change.
6. `make dossiers` and `test_repository_checkout_validates_clean` stay red until
   the coordinator completes WFS-005's own `index.md`, `pr-desc.md`, and
   `receipt.md`. With this artifact written, 36 diagnostics remain and every one
   of them is on those three files.
7. Pre-existing and out of plan: `summarize_dossier` passes the caller's
   unresolved dossier path to `validate_dossier`, so on macOS a temporary
   directory reached through a symlinked parent gets a spurious "outside
   supplied projects root" diagnostic. The CLI path is unaffected and the new
   tests pass resolved paths.
8. The stage 2 evidence base behind the simplification itself (three tasks, one
   run per arm) was settled by the recorded decision and the plan review, not by
   this review. The protocol's stop-and-rollback rule stays in force and is
   restated in the workflow document.

## Claim or decision

The implementation of `WFS-005-PLAN-001` version 3 passes independent code
review at artifact version 2. Version 1's single blocking finding, M1, is closed
by execution: Fix 1's new test
`test_an_unreadable_plan_does_not_excuse_the_report` fails when the presence
filter is removed and passes with it, kills exactly that one test and no other,
and Fix 1 changed nothing else — +11 insertions, 0 deletions, one test file, with
`validation.py` byte-identical to the hash the implementer froze. Every earlier
`PASS` judgment re-confirmed: a reduced dossier cannot escape level 2, every
other dossier under `projects` validates untouched, partial adoption holds,
packaged resources and installed mode are byte-unchanged, the lifecycle is
stated canonically once and referenced elsewhere, the reviewer rule is in
`docs/policy/reviewer.md`, and both coordinator conditions hold. The gate is
green on Python 3.10.11 and 3.14.6 with only the two sanctioned reds, both of
which name WFS-005's own pending coordinator artifacts. Nine Low findings are
recorded, one of them new, and none blocks.

## Evidence

- Techstack verify returned `"status": "match"` with observed snapshot SHA-256
  `e43d6e098bc6c8b6d2b2ed466f9c38ef164ef23d32f42eac6b7d855134487df4`, run before
  any other work in this session, and all ten required selected rule files were
  read in full: `techstacks/README.md`, `techstacks/general.md`,
  `techstacks/policy/README.md`, `techstacks/policy/canonical.md`,
  `techstacks/policy/packaged-resources.md`,
  `techstacks/policy/task-dossiers.md`, `techstacks/python/README.md`,
  `techstacks/python/runtime.md`, `techstacks/python/scripts.md`,
  `techstacks/python/tests.md`.
- M1 mutation evidence, on a copy of `src` and `tests` in a scratch directory
  outside the repository: baseline
  `tests.unit.test_task_dossier_validator` 83 OK; the version 1 mutant (filter
  replaced with an unconditional `present.add(name)`) 83 run, 1 failure, that
  failure being `test_an_unreadable_plan_does_not_excuse_the_report`; the
  inverted mutant (`if not any(` to `if any(`) 15 failures. The other four
  dossier suites give the identical 153 run / 6 failures / 119 errors mutated
  and unmutated, so the mutant kills nothing but the new test. L1's mutant
  (`or path.is_symlink()` removed from `_validate_presence`) leaves 83 OK,
  confirming that survivor.
- Scope evidence for Fix 1: `git diff --stat` reports 20 modified tracked files,
  1591 insertions, 208 deletions against `implementation.md:213`'s recorded
  1580/208, so +11 insertions and 0 deletions; the new test is 11 lines;
  `shasum -a 256 src/brichan/contracts/task_dossier/validation.py` is
  `8a5a4059863ffae79efc826f79615f9027e3d17ad5b0f7781557ad6c340a67d0` both
  before and after every mutation run; `git diff --stat -- src/brichan/resources`
  is empty; the unit tier went 1061 to 1062.
- Full gate, both interpreters, with `codex` off `PATH` so the doctor check
  matches CI. `PYTHONDONTWRITEBYTECODE=1 make -k check` on 3.10.11 and
  `make -k check PYTHON=/opt/homebrew/bin/python3.14` on 3.14.6 gave identical
  results: metrics 10 OK, unit 1062 OK, contract 153 OK, integration 227 run
  with the single sanctioned failure `test_repository_checkout_validates_clean`,
  techstack-eval 56 OK, 55 canonical receipts validated, project memory
  consistent (10 indexed projects, 8 active documents), repository paths valid
  (113 entries, 75 references), `README_PYPI.md` in sync, compatibility
  retirement eligible and retired, and the package-check imports clean. The only
  two `make` errors are `test` (that one integration test) and `dossiers`. The
  frozen eval was also run directly under 3.14.6
  (`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /opt/homebrew/bin/python3.14 -m
  unittest evals.techstack_context_v1.test_cases`, 56 OK), because
  `Makefile:39-40` freezes a literal `python3` and does not follow `PYTHON=`,
  per SCRIPT-003.
- Focused runs: the six dossier suites (validator, generator, summary, contract
  paths, dossier contract, dossier workflow integration) ran 285 tests on 3.10.11
  and on 3.14.6, with only `test_repository_checkout_validates_clean` failing on
  each.
- Existing dossiers validate unchanged.
  `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py projects`
  reports 36 diagnostics across 17 dossiers: 30 on WFS-005's templated
  `index.md`, 5 on its templated `pr-desc.md`, 1 on its absent `receipt.md`.
  Zero fall on the other 16 dossiers, and zero now fall on `code-review.md`. The
  sanctioned integration failure names `handoffs/WFS-005` and no other dossier.
- Design-protection probes, re-run in this session through the validator's own
  helpers, on scratch dossiers outside the repository: declaring level 2 while
  carrying only the reduced level 0 four yields 16 diagnostics (eight
  missing-file, eight status-table); a conforming reduced level 0 and a
  conforming reduced level 1 each yield 0 under `--require-complete`; deleting
  `report.md` from a reduced level 1 dossier yields exactly the
  `report.md is missing` diagnostic; downgrading a valid level 2 dossier by
  editing only `index.md` yields 14 diagnostics from four independent rules.
  `required_artifacts` returns the reduced four at levels 0 and 1 and all eleven
  at level 2, and `resolve_task_level("bogus")` returns `"2"`.
- Condition evidence. M1 (fail-closed level resolution in all four tools):
  `resolve_task_level` at `schema.py:306-311` is the single rule;
  `validation.py:1170`, `record.py:817`, `summary.py:162,240` and
  `schema.py:322` all route through it, `scaffold.level_artifacts` raises on an
  unknown level (`scaffold.py:71-75`), and the generator CLI refuses via
  argparse `choices` (`generate.py:673`); a bogus declared level is validated
  against the level 2 floor of 3 evidence items. M2 (back-write guard over
  `report.md`): `report` is in the guarded tuple at `validation.py:479`, with
  the comment recording why, and
  `tests.unit.test_task_dossier_validator.ReducedDossierValidatorTest` runs
  16 tests, OK.
- Byte-unchanged and canonical-statement evidence:
  `git diff --stat -- src/brichan/resources` is empty; `### Lifecycles by level`
  appears exactly once across `docs`, `.agents`, `AGENTS.md`, `PRODUCT.md`,
  `CLAUDE.md` and `src`, at `docs/workflows/task-dossier.md:186`, with
  `docs/policy/operating-principles.md:33`, `docs/policy/reviewer.md:53,64` and
  `.agents/skills/herdr-orchestration/references/task-dossier.md:4` referencing
  the workflow document rather than restating it; the reviewer rule is at
  `docs/policy/reviewer.md:29-32` with the matching return item at line 46.
- The coordinator's corrections were checked against the files, not accepted:
  `implementation.md:173` (TEST-003 claim), `implementation.md:255` (risk item 1)
  and `implementation.md:14-17` (Outcome), and the underlying red is gone —
  `tests.contract.test_repository_contract` runs 18 tests, OK, so the home-path
  scan passes.
- Every mutation check ran on a copy outside the repository. No tracked file was
  modified by this review, and the only file written is this artifact.
- Spec basis: `plan.md` v3 (accepted, plan ID `WFS-005-PLAN-001`), `design.md`,
  `requirements.md` (R1-R13, A1-A6), `plan-review.md` v2 (`PASS`, findings M1
  and M2 as the coordinator conditions), `client-follow-up-questions.md` v1, the
  implementer's `implementation.md` including its Fix 1 section, and the archived
  `versions/v3/code-review.md` (artifact version 1).

## Uncertainty

- The escape probe's diagnostic count differs from version 1's: I reproduce 16
  diagnostics for a level 2 declaration over the reduced four, where version 1
  recorded 18. This is a probe-construction difference, not a behavior change —
  no production line differs between the two reviews, as the diff arithmetic and
  the `validation.py` hash establish. My 16 are the eight absent artifacts
  diagnosed twice each, once missing-file and once status-table, which is the
  protection the criterion asks about. I did not reconstruct version 1's exact
  fixture to account for the other two.
- I did not re-run the twelve mutation checks version 1 performed on guards that
  Fix 1 did not touch, since no production line changed and re-running them
  would only re-derive a settled result. If the coordinator wants the full sweep
  repeated against the post-fix tree, that is a cheap request and I did not make
  it a condition.
- L9's `.get(level, 1)` is unreachable today, and I proved that for the current
  single call site. It is unreachable by call-site discipline rather than by
  construction, so a future caller passing an unresolved level would silently
  get the shallowest floor. I record it as a Low rather than a Medium because no
  present behavior is wrong and no criterion is violated; a reviewer who weighs
  latent fail-open defaults more heavily could reasonably call it a Medium
  hardening request, and the fix is one character class — index instead of
  `.get`.
- Whether the contract-path membership should include the `src/brichan` and
  `scripts` prefixes remains the user-reversible judgment the plan recorded. I
  take no position; the implementation matches the accepted list exactly.
- I did not re-derive the stage 2 evidence base that justifies the
  simplification itself. That was settled by the recorded decision and the plan
  review; this review covers the implementation of the accepted plan only.
- No other uncertainty remains.
