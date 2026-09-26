# Code review

Independent review of the implementation, or the recorded evidence for why no implementation review applies.

## Artifact metadata

- Task ID: `WFS-005`
- Task level: `2`
- Artifact: `code-review`
- Artifact version: `1`
- Origin: `wfs-005-code-review-worker:2026-09-26:v1`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `code-review-session-c6a70f04`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `code-review-session-c6a70f04`
- Review verdict: `CHANGES REQUIRED`

## Review target

- Reviewed plan ID: `WFS-005-PLAN-001`
- Reviewed plan version: `3`

## Review provenance

- This review is the stronger one-off review override the user authorized for
  WFS-005 (`client-follow-up-questions.md` v1: "Run now, Claude reviewers"),
  so the `review` route's configured runtime and model
  (`config/model-routing.json`: codex, `gpt-5.6-sol`, medium) were overridden
  to a Claude reviewer at high effort. The override is recorded, not silent.
- Reviewing session `code-review-session-c6a70f04` is not the plan's authoring
  session (`plan-session-8ec2b29b`), not the plan review's reviewing session
  (`review-session-faf2990c`), and not the implementation worker's session
  (attempt `attempt-implement-1`). I did not implement any part of this change.
- Reviewed state: the uncommitted working tree of branch
  `feat/lifecycle-simplification`, 20 modified tracked files and 4 new files.
  The changes to `.codex/config.toml`,
  `projects/brida-workflow-simplification/decisions.md`, `tasks.md`, and the
  untracked directory under `evals/workflow-simplification/wfs-005` are
  coordinator or user files and were excluded from review, as the packet
  directs.

## Verdict

`CHANGES REQUIRED`. One blocking Medium finding, and it is a missing test,
not a broken behavior: the new fail-closed presence filter that keeps an
unreadable `plan.md` from excusing `report.md` ships with no committed
regression test, and removing it fails nothing in the suite. Everything else
holds. Every plan step S1-S9 is implemented, both coordinator conditions (M1
fail-closed level resolution, M2 the reviewer back-write guard over
`report.md`) are closed with named tests that really fail when the guard is
removed, all six acceptance criteria are met, and I reproduced the full gate
on Python 3.10 and 3.14 with only the two reds the packet sanctions. The
design's deliberate protections hold under adversarial probing: a reduced
dossier cannot escape level 2, every pre-existing dossier validates untouched,
partial adoption is strengthened, and packaged resources are byte-unchanged.

The fix is one test. I am not asking for a re-implementation, and no finding
below requires a design change.

## Per-criterion scores

| Criterion | Score | Basis |
| --- | --- | --- |
| Spec fidelity | 5/5 | Every plan step, both coordinator conditions, every file in design section 6, and every design test 1-20 is present and named. The seven recorded deviations are each effect-preserving and each has a stated reason; I checked all seven against the design and agree with all seven. |
| Code review | 4/5 | The code is single-sourced (`resolve_task_level`, `required_artifacts`), fails closed at every level decision, and touches nothing outside the declared scope. One new guard ships untested (M1 below) and four further new lines are invisible to the suite (L1-L4). |
| Empirical verification | 5/5 | Independently reproduced, not taken from the report: 1061 unit, 153 contract, 227 integration, 56 techstack-eval, 55 receipts, plus memory, path, readme, preflight and package checks on both interpreters. Only the two sanctioned reds appear, and every one of their 40 diagnostics falls on WFS-005's own pending artifacts. |

## Findings

### M1 — Medium, blocking. The new unreadable-artifact presence filter has no committed regression test; removing it fails nothing

`src/brichan/contracts/task_dossier/validation.py:116-122` adds a filter that
excludes an artifact from the `present` set when parsing it emitted a
`cannot read artifact` diagnostic. That filter is what makes an unreadable
`plan.md` fail closed toward requiring `report.md`. The rule is stated
normatively in three places: `docs/workflows/task-dossier.md:225` ("A
symlinked or unreadable `plan.md` is not present, so `report.md` is
required"), the docstring of `required_artifacts`
(`src/brichan/contracts/task_dossier/schema.py:314-322`), and `design.md`
section 3. Only the symlink arm is tested
(`tests/unit/test_task_dossier_validator.py:1079`). The unreadable arm is not
tested at all.

Reproducing input. On a copy of the tree outside the repository, replace the
filter with an unconditional `present.add(name)`:

```python
        artifacts[name] = parse_artifact(path, name, diagnostics)
        present.add(name)
```

then run the six dossier suites:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.unit.test_task_dossier_validator tests.unit.test_task_dossier_generator \
  tests.unit.test_task_dossier_summary tests.unit.test_contract_paths \
  tests.contract.test_task_dossier_contract tests.integration.test_task_dossier_workflow
```

The mutant survives: the only failures are the scratch-copy baseline ones, and
no dossier test detects the change. I verified the harness itself is sound by
mutating a covered constant in the same way (`FALLBACK_TASK_LEVEL` from `"2"`
to `"0"`), which killed five tests.

Why this blocks. Requirement R10 of the accepted `requirements.md` states that
every executable-behavior change adds or updates a regression test that fails
when the guard is removed, citing techstack rules `GENERAL-004` and
`TEST-003`; the plan's step sequence repeats that obligation for every step.
The guard is an executable behavior change and has no such test. The reviewer
rule this very change introduces
(`docs/policy/reviewer.md`, prompt `Rules:`) classifies exactly this as a
defect of at least medium severity rather than a test gap, so letting it
through on the rule's first application would contradict the change's own
thesis.

What limits the severity, stated so the coordinator can weigh it. A regression
here cannot turn an invalid dossier into a valid one: an unreadable artifact
always emits its own `cannot read artifact` diagnostic, so the dossier is
non-empty in `validate_dossier`'s return either way. The guard governs
diagnostic completeness and the fail-closed direction, not any validity
verdict. I confirmed this by writing an undecodable `plan.md` into an
otherwise valid legacy dossier on a scratch copy: 43 diagnostics, including
both `cannot read artifact` and `report.md is missing`.

Fix. One unit test beside `test_a_symlinked_plan_does_not_excuse_the_report`:
build a valid full dossier, overwrite `plan.md` with non-UTF-8 bytes, and
assert the diagnostics include `required task-dossier artifact report.md is
missing`. It fails when the filter is removed.

### L1 — Low, not blocking. `_validate_presence`'s symlink skip is invisible to the suite

`src/brichan/contracts/task_dossier/validation.py:134` skips the missing-file
diagnostic when the required path is a symlink. Removing `or
path.is_symlink()` fails no test. The effect of the regression is one extra,
redundant diagnostic beside the existing `artifact is a symlink` one, so the
validator becomes noisier rather than weaker, and the symlink refusal itself
stays tested. Does not block: no contract statement depends on the suppressed
duplicate.

### L2 — Low, not blocking. The index-template contiguity guard is untested

`src/brichan/contracts/task_dossier/scaffold.py:91` raises when the index
template's status rows are not contiguous. Replacing the check with `pass`
fails no test. It guards a template whose eleven rows are already pinned by
`test_index_template_links_authorities_without_duplicating_them`, so the state
it defends against cannot reach a released tree. Does not block: defensive
depth on an already-pinned input.

### L3 — Low, not blocking. `record_artifacts`' ordering is redundant, so its mutation survives

`src/brichan/contracts/task_dossier/generate.py:153` re-orders the record's
keys into `RECOGNIZED_ARTIFACTS` order. Returning `tuple(record.artifacts)`
instead fails no test, because `record.py`'s loader already builds
`record.artifacts` by iterating `RECOGNIZED_ARTIFACTS`, so the input is always
ordered. Does not block: the property is real and enforced one layer down, and
rendering order is cosmetic.

### L4 — Low, not blocking. The summary's unreadable-row sort is untested

`src/brichan/contracts/task_dossier/summary.py:246` sorts the unreadable rows
into lifecycle order. Removing the sort fails no test. Presentation only; the
summary is explicitly a non-authority. Does not block.

### L5 — Low, not blocking. The contract-path checker treats empty input as "no contract path"

`src/brichan/contracts/task_dossier/contract_paths.py:56-76` returns exit 0
and prints `contract-path: no` on empty stdin. In the documented pipeline
(`docs/workflows/task-dossier.md`, Contract paths), a `git diff` that fails —
a bad dispatch base, a wrong worktree, a forgotten pipe — produces empty
stdout, and an ordinary shell does not propagate the upstream exit status, so
the checker answers "no review needed" from no evidence. I confirmed this:
piping nothing prints `contract-path: no` with exit 0, while non-UTF-8 input
correctly exits 2.

Does not block: this is the behavior the accepted design specifies (exit 0 no,
3 yes, 2 invalid invocation or undecodable input), and the workflow document
already states the trust boundary explicitly — the level 0 decision is the
coordinator's and is recorded with the checker's output. Worth a follow-up
sentence recommending `set -o pipefail`, or an `--expect-nonempty` flag, since
the cheapest failure mode of a safety check should not be silence.

### L6 — Low, not blocking. The legacy `plan`-satisfies rule is not restricted to legacy dossiers

`required_artifacts` drops `report` whenever `plan` is present, with no
condition on the dossier's age. A brand-new Level 0 or Level 1 task can
therefore carry `plan.md` instead of `report.md` and never write the mandated
`Plan`, `Changes`, `Verification`, `Risks` structure that R2 and R3 describe
as the lifecycle. I verified it: a level 0 dossier holding `index`, `request`,
`plan`, `code-review` and no report validates with zero diagnostics under
`--require-complete`.

Does not block. This is the plan review's shape (a), which plan version 3
adopted deliberately to close C1 without an exemption list, and
`docs/workflows/task-dossier.md` states it plainly ("At levels 0 and 1 a
present `plan.md` carries the plan, so `report.md` is then not required").
Nothing is escaped — a level 1 task still needs a mandatory independent code
review, and a present `plan.md` validates under the full plan rules. Recording
it so the coordinator knows the report structure is a documented obligation,
not a mechanical one.

### L7 — Low, not blocking. `implementation.md`'s TEST-003 claim overstates what the suite verifies

`implementation.md` states: "Each removal failed its named test. No survivor
remained." My sweep of seven new guards found five survivors (M1, L1, L2, L3,
L4) and two kills (`render_artifact`'s missing-key guard, killed by
`test_rendering_an_artifact_the_record_lacks_is_refused`; `_unquote`, killed
by `test_contract_paths_match_and_other_paths_do_not`). The named guards the
report enumerates do each fail their named test — I did not find a
counterexample among those — but the blanket claim is wrong, so the report
should not be relied on as the TEST-003 record. Does not block on its own;
correct the sentence in place when M1 is fixed (DOSSIER-004: correct in place,
never append a contradicting section).

### L8 — Low, not blocking. Presence and review-target rules key on different sets

`_validate_unplanned_review_targets` keys on `"plan" in artifacts`
(`validation.py:556`) while `required_artifacts` keys on the stricter `present`
set. An unreadable — not symlinked — `plan.md` therefore both requires
`report.md` and forbids null review targets at once. Only reachable in a
dossier that is already invalid for the unreadable file, so no valid state is
affected. Does not block.

### Stale risk item in `implementation.md`, for the record

`implementation.md` Risks item 1 reports a pre-existing gate red,
`test_durable_artifacts_do_not_embed_home_paths`, naming two untracked pane
captures. It does not reproduce: the contract tier is 153 OK on both
interpreters in my runs, and `tests.contract.test_repository_contract` passes
18 tests. The captures were rewritten after the implementation attempt ended.
No coordinator action is needed for it; the item can be closed.

## Test gaps

Per the rule this change adds, a behavior change with no committed regression
test is a defect, so the gaps are filed as findings above rather than here.
Listed once more as a checklist:

- M1 (blocking): no test for the unreadable-plan arm of the fail-closed
  presence rule.
- L1-L4 (not blocking): four new lines whose removal the suite cannot detect.
  L1 and L2 defend states that are already caught or already pinned, L3 is
  redundant with the record loader, and L4 is presentational; a test for each
  is optional, not owed.

What is not a gap. The tests this change lands are substantive, not
decorative. I confirmed by mutation that the fail-closed level fallback, the
`report.md` back-write guard, report-author independence in both the validator
and the record loader, the level 1/2 review mandate, report concreteness, the
status-table absent-row rule, the legacy `plan` rule, the symlink arm, null
review targets, level-keyed scaffolding, generated status rows, completion
narrowing, partial adoption of `report`, and the contract-path list each have
at least one test that fails when the guard is removed. The two committed
legacy samples under `evals/task-dossier-pilots/concise` now own a real
regression guard (`test_the_committed_legacy_samples_validate_under_the_level_rules`),
which is the right answer to TEST-004 given that dossiers under `projects` are
gitignored.

## What I verified

Packet checks, each run rather than read:

- Every existing dossier validates unchanged.
  `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py projects`
  reports 40 diagnostics, and all 40 name WFS-005's own artifacts: 29 on the
  templated `index.md`, 5 on the templated `code-review.md`, 5 on the
  templated `pr-desc.md`, 1 on the absent `receipt.md`. Zero fall on the other
  16 dossiers.
- A reduced dossier cannot escape level 2. Declaring level 2 while carrying
  only the reduced four artifacts yields 18 diagnostics, one missing-file
  diagnostic per absent artifact. Downgrading a valid level 2 dossier by
  editing only `index.md` and deleting the eight artifacts level 0 does not
  require yields 14 diagnostics from four independent rules at once: the
  per-artifact `Task level` mismatch, the required `report.md`, the null
  review targets, and the status table's absent-row rule. The remaining
  exposure is self-declaration at creation time, which is M2's documented,
  reviewer-checked residual.
- Partial-adoption protection holds and is stronger. `discover_partial_dossiers`
  scans all recognized names, a `report.md`-only handoff is reported, and the
  real `projects` run produced no partial-adoption diagnostic.
- Installed mode and packaged resources are byte-unchanged.
  `git diff --stat -- src/brichan/resources PRODUCT.md config techstacks evals Makefile README_PYPI.md packaging`
  is empty, and `make test-contract` (skill parity, dogfood policy,
  repository paths) is 153 OK.
- The lifecycle is stated canonically once. `### Lifecycles by level` appears
  once, in `docs/workflows/task-dossier.md`; `docs/policy/operating-principles.md`
  section 2, `docs/policy/reviewer.md`, and both `herdr-orchestration` files
  now reference it. A repository-wide search for "eleven", "all levels", "all
  task levels", and "same standard artifact" across `docs`, `.agents`,
  `AGENTS.md`, `PRODUCT.md`, `CLAUDE.md`, and `src/brichan` finds no remaining
  normative duplicate; the three surviving mentions of "eleven" are code
  comments.

Additional checks:

- Both coordinator conditions. M1: `resolve_task_level` is the single level
  rule; the validator, summary, and record loader call it, the scaffold raises
  through `level_artifacts`, and the generator CLI refuses via argparse
  `choices`. M2: `report` is in the `_validate_ownership` back-write tuple and
  `test_reviewer_must_not_author_the_report` covers it.
- Level 2 is not weakened anywhere, and is tightened in one place: a
  `code-review` recorded `not-required` is now a diagnostic at level 2 as well
  as level 1, which no existing dossier trips.
- The monotone rule holds: a reduced level 1 dossier carrying an extra
  `design.md` validates with zero diagnostics under `--require-complete`.
- `report.md` is not a validation hole: it takes the level evidence floor,
  the structural section check, the passed-phase concreteness check, and the
  reviewer back-write guard.
- Level 2 scaffold output is byte-identical to the templates, which also pins
  `scaffold.STATUS_ROW` equal to the index template's row form.
- Contract-path checker behavior matches the document: `docs/policy/x.md` and
  the M3 additions `src/brichan/project.py` and
  `scripts/validate_task_dossiers.py` exit 3; `tests/unit/x.py` and
  `README.md` exit 0; non-UTF-8 input and a bad argument exit 2.
- `scripts/check_contract_paths.py` follows the existing 19-line wrapper
  pattern and file mode exactly.
- Full gate, both interpreters, with `codex` off `PATH` so the doctor check
  matches CI: metrics 10 OK, unit 1061 OK, contract 153 OK, integration 227
  run with the single sanctioned `test_repository_checkout_validates_clean`,
  techstack-eval 56 OK, 55 receipts valid, `make dossiers` red only on
  WFS-005, and memory-check, path-check (113 entries), readme-check,
  phase5-preflight and package-check all pass. `sh -n bin/brichan` exits 0.
  The techstack eval also runs 56 OK directly under Python 3.14.6, since its
  recipe does not follow `PYTHON=`.
- Every mutation check ran on a copy of the tree outside the repository. No
  tracked file was modified by this review other than this artifact.

## Claim or decision

The implementation of `WFS-005-PLAN-001` version 3 is correct, faithful to the
accepted plan and design, and independently verified green on Python 3.10 and
3.14; both coordinator conditions are closed with guards that really fail when
removed. It is returned `CHANGES REQUIRED` for exactly one reason: the new
fail-closed presence filter that stops an unreadable `plan.md` from excusing
`report.md` has no committed regression test, which violates requirement R10
and the reviewer rule this change itself introduces. One unit test closes it.
Seven Low findings are recorded and none blocks.

## Evidence

- Techstack verify returned `"status": "match"` for snapshot
  `53d20d1a398f270216d666a5e045edac32b44fb21fcab03dafcae442669fdb25` before
  any other work in this session, and all ten selected rule files
  (`techstacks/README.md`, `general.md`, `policy/README.md`,
  `policy/canonical.md`, `policy/packaged-resources.md`,
  `policy/task-dossiers.md`, `python/README.md`, `python/runtime.md`,
  `python/scripts.md`, `python/tests.md`) were read in full.
- Mutation evidence for M1 and L1-L4: on a full copy of the tree outside the
  repository, each of seven new guards was removed one at a time and the six
  dossier suites re-run; five removals changed no test result and two were
  killed by their named tests. The harness was validated by a control mutation
  (`FALLBACK_TASK_LEVEL` `"2"` to `"0"`) that killed five tests.
- Full-gate evidence: `PYTHONDONTWRITEBYTECODE=1 make -k check` and
  `make -k check PYTHON=/opt/homebrew/bin/python3.14`, both with `codex` off
  `PATH`, produced identical results — 10, 1061, 153 and 56 tests OK, 227
  integration with only `test_repository_checkout_validates_clean` failing,
  55 receipts valid, and `make dossiers` red only on WFS-005 — plus
  `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 -m unittest
  evals.techstack_context_v1.test_cases` at 56 OK under Python 3.14.6.
- Byte-unchanged evidence: `git diff --stat` over
  `src/brichan/resources`, `PRODUCT.md`, `config`, `techstacks`, `evals`,
  `Makefile`, `README_PYPI.md` and `packaging` is empty, so acceptance
  criterion A5 and requirement R1 hold; `docs/workflows/task-dossier.md`'s
  pinned needles survive, since the contract tier passes unchanged.
- Adversarial probe evidence: eleven scratch dossiers were built through
  `tests/unit/test_task_dossier_validator.py`'s helpers and validated — level
  2 with the reduced four (18 diagnostics), a level 0 waiver without a
  rationale (1), a reduced dossier without its receipt (1), a level 0 dossier
  with `plan` instead of `report` (0), a reduced dossier plus an extra
  `design.md` (0), a thin-evidence reduced dossier (4), an unreadable
  `plan.md` (43), and the index-only level downgrade (14).
- Spec basis: `plan.md` v3 (accepted, plan ID `WFS-005-PLAN-001`),
  `design.md` v2 sections 1-8, `requirements.md` v2 R1-R13 and A1-A6,
  `plan-review.md` v2 (`PASS`, findings M1 and M2 as the coordinator
  conditions), and `client-follow-up-questions.md` v1 (checkout-only scope,
  Claude reviewers, no migration, ship authorization not requested).

## Uncertainty

- Whether M1 should block is the one judgment in this review a reasonable
  reviewer could take the other way. The guard's regression cannot make an
  invalid dossier valid, so a coordinator could classify it Low and land the
  change with a follow-up. I block because requirement R10 is written without
  an exception and because the reviewer rule this change introduces is
  explicit that such a gap is a defect of at least medium severity; the
  coordinator has the standing to overrule that reading, and the cost either
  way is one test.
- Whether the contract-path membership should include the `src/brichan` and
  `scripts` prefixes remains the user-reversible judgment the plan recorded.
  I take no position; the implementation matches the accepted list exactly and
  the list stays a one-line, one-tuple-entry, one-test change.
- I did not re-derive the stage 2 evidence base (three tasks, one run per arm)
  that justifies the simplification itself. That was settled by the recorded
  decision and the plan review; this review covers the implementation of the
  accepted plan only, and the protocol's stop-and-rollback rule stays in force
  and is restated in the workflow document.
- No other uncertainty remains.
