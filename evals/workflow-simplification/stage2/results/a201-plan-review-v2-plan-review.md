# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `WFS-A-201`
- Task level: `0`
- Artifact: `plan-review`
- Artifact version: `2`
- Origin: `reviewer:2026-09-25-wfs-a-201-plan-review-v2`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `8613cba2-e274-4a6b-abc1-564a651929c7`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `medium`
- Reviewing session: `8613cba2-e274-4a6b-abc1-564a651929c7`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `WFS-A-201-PLAN-001`
- Reviewed plan version: `3`

## Claim or decision

**PASS.** Plan version 3 closes all four findings of plan-review version 1
(`versions/v2/plan-review.md`, verdict `CHANGES REQUIRED` on plan version 2).
Each closure was re-verified against this worktree rather than accepted from
the plan's own table: the restated reference criterion is now recorded in a
coordinator-owned dossier artifact a later session can read
(`client-follow-up-questions.md:26`, origin `coordinator:2026-09-25-wfs-stage2`);
Step 4's expected-red set is now complete and exactly correct — I measured all
four components red and every other component green on both interpreters;
`sh -n bin/brichan` is included; and the validator baseline is re-measured with
a distribution-not-count comparison rule. The technical core is unchanged and
re-verified independently: the selected name
`test_prose_rejects_pipe_and_category_c_characters` describes exactly the two
assertions, the single-line `def` rename is behavior-neutral, the name is
unique in the repository, and a guard-substitution probe confirms each subtest
fails when and only when the guard its new name claims is removed. The plan
neither misses a necessary change nor adds an unnecessary one.

One divergence remains and is recorded as finding M1 rather than as a plan
defect: acceptance criterion 3 **as literally worded in this review packet**
("no other reference to the old name remains anywhere in the repository") will
not be met by following the plan, because
`projects/brida-workflow-simplification/tasks.md:29` keeps the old name by the
coordinator's own recorded option (b) decision. The plan is right to follow the
recorded decision, states the divergence openly, and flags the packet reissue
as a coordinator action it cannot perform itself. The required remedy is
coordinator-side and is stated under M1.

## Findings closure check against plan-review version 1

| Prior finding | Required | Verified state in version 3 | Closed |
|---|---|---|---|
| H1 (high) — restated criterion 3 not verifiable in the repository | Record the restatement where later sessions can read it (and reissue it to the implementation and code-review packets), or add a `tasks.md:29` step with the scope expansion | The first arm is done: `client-follow-up-questions.md` version 2 (coordinator-owned, phase `passed`, origin `coordinator:2026-09-25-wfs-stage2`) records both the restated criterion and the ratified gate at line 26, and `requirements.md:65-74`, `design.md:68-73`, and `plan.md:75-81` cite that artifact instead of a packet relay. The parenthetical second arm is not done and cannot be done by the planner — see M1. | Yes, as to the plan |
| M1 (medium) — Step 4 expected-failure set incomplete | Name `make path-check` and `test_repository_checkout_validates_clean` alongside `make dossiers` | `plan.md:153-163` names all four; `requirements.md:88-94` carries the same list; `plan.md:190-201` excludes exactly that list from escalation. Re-measured: the set is complete and nothing else is red. | Yes |
| L1 (low) — substitute gate run omits the `check` recipe body | Include `sh -n bin/brichan` | `plan.md:146` and `requirements.md:83` include it; `Makefile:76` confirms it is the recipe body; measured `rc=0`. | Yes |
| L2 (low) — validator baseline stale, invites a false mismatch | Say the count falls; prevent misreading a correct result as a discrepancy | `plan.md:171-177` and `requirements.md:95-100` instruct comparison of the distribution (no diagnostic in any planner-owned artifact) and state the falling count is the expected direction, never a discrepancy. See L1 below for one residual inaccuracy in the recorded snapshot that this rule already neutralizes. | Yes |

## Findings

### M1 (medium) — this review packet still carries the strict criterion 3; the reissue that plan-review version 1 also required has not happened

`client-follow-up-questions.md:26` now records the coordinator's restatement
verifiably, which is what plan-review version 1 principally demanded. The
packet issued for attempt `attempt-plan-review-2` nevertheless still states
criterion 3 as "No other reference to the old name remains anywhere in the
repository (`git grep` evidence)". Both statements come from the coordinator
and they still disagree.

Measured in this worktree (2026-09-25):

```
git grep -n test_prose_rejects_control_and_markup_characters
projects/brida-workflow-simplification/tasks.md:29
tests/unit/test_techstack_markdown.py:565
```

A whole-tree `grep -rIn` outside the dossier returns the same two lines and
nothing else. After the plan's single-line edit the first line survives, so
the strict wording fails on its own evidence command while the restated
wording (`requirements.md:65-74`) passes.

This is **not** a plan defect. The plan takes the recorded decision as
governing, refuses the `tasks.md` edit explicitly
(`plan.md:79-81`, `plan.md:182-188`), and records the reissue as a coordinator
follow-up (`plan.md:207-213`). Editing `tasks.md:29` instead would place the
implementer outside both declared Techstack scope paths and inside
coordinator-owned project memory, which the coordinator forbade.

Required, before the implementation packet is issued: carry the restated
wording of criterion 3 into the implementation and code-review packets. An
implementer handed the strict wording has a standing instruction to remove a
reference the plan forbids removing; that is the concrete risk, and it is the
one thing in this task that could still produce an out-of-scope edit.

### L1 (low) — the recorded validator distribution omits one row that is present right now

`plan.md:54` and `plan.md:176` record the baseline as 38 diagnostics
distributed `index.md` 28, `code-review.md` 5, `pr-desc.md` 5, none
planner-owned. Measured immediately before this artifact was written, the
total is 39: the same distribution plus one row against `plan-review.md`
itself — `Review target.Reviewed plan version: review must reference the exact
accepted plan version '3', found '2'` — because the top-level `plan-review.md`
was still version 1, reviewing plan version 2, while `plan.md` had advanced to
version 3. Publishing this artifact clears that row and returns the total to
38 with exactly the recorded distribution.

The plan's own rule already absorbs this: `plan-review.md` is reviewer-owned,
not planner-owned, and `plan.md:171-177` instructs comparison of the
distribution rather than the count. No change is required; it is recorded so
the implementer reading a 38 against a plan that says 38 does not conclude the
numbers were merely copied forward.

## Verification performed

Every claim below was measured in this worktree on 2026-09-25 under
`PYTHONDONTWRITEBYTECODE=1`, not taken from the plan or from plan-review
version 1.

- **Name accuracy (criterion 1, R1).** `src/brichan/techstacks/markdown.py:328-332`
  rejects `|` and any character whose Unicode category begins with `C`, and
  rejects nothing else in the markup class;
  `tests/unit/test_techstack_markdown.py:537-563` asserts that backticks and
  angle brackets are accepted in all six prose positions, which is what makes
  the present name false. `tests/unit/test_techstack_markdown.py:570-574`
  drives exactly two subtests, `- Applies to a|b.` and `- Applies to a\u0085b.`,
  through `assert_invalid_leaf` on a Scope bullet. The selected name states
  those two rejection classes and claims nothing further.
- **Guard sensitivity (TEST-003), by probe rather than assumption.** With
  `_is_prose` replaced in memory by a copy missing only the `|` guard,
  `- Applies to a|b.` parses and `- Applies to a\u0085b.` still raises
  `MarkdownError: INVALID_LEAF`; with a copy missing only the category-C
  guard, the results invert; the unmodified guard rejects both. Neither
  subtest is vacuous, each maps one-to-one onto one half of the new name, and
  the rename touches none of it. No repository file was modified; `git status
  --short` is empty.
- **Neutrality and uniqueness (criterion 2, R2).** The comment at
  `tests/unit/test_techstack_markdown.py:566-569` already states the retained
  rejections accurately, so the packet's only-if-needed comment allowance is
  correctly left unexercised and the diff is one `def` line.
  `git grep -n test_prose_rejects_pipe_and_category_c_characters` and
  `git grep -n test_prose_rejects_pipe` both return nothing, so the name
  collides with nothing. No file content anywhere in the repository names the
  module `test_techstack_markdown`, and nothing enumerates test-method names
  (`tests/contract/test_repository_contract.py:377`, `:422` scan file paths
  and content, not test identifiers), so the rename cannot break another
  assertion.
- **The gate (criterion 4, R4), on Python 3.10.11.** `make check` stops in
  `test-contract` with exactly the two `tests/contract/test_repository_paths.py`
  failures ("unclassified root files: .git") and reaches no later component,
  because `check` runs them only after `test` succeeds (`Makefile:75`) — so
  the plan's `make check` prediction and criterion 4 are both satisfiable as
  worded. Layer by layer: `test-unit` 1026 tests OK; `test-contract` 148
  tests, the 2 known failures; `test-integration` 222 tests, exactly 1 failure
  (`test_repository_checkout_validates_clean`); `techstack-eval` 56 OK;
  `metrics`, `receipts`, `memory-check`, `readme-check`, `phase5-preflight`,
  `package-check` all exit 0; `path-check` exits 1 ("unclassified root files:
  .git"); `dossiers` exits 1; `sh -n bin/brichan` exits 0.
- **The gate on Python 3.14.6**, with `PYTHON=/opt/homebrew/bin/python3.14`
  and the eval run directly because `Makefile:40` uses bare `python3`:
  identical outcome in every component — `test-unit` 1026 OK, `test-contract`
  the same 2 failures, `test-integration` the same 1 failure, eval 56 OK, all
  other targets exit 0, `path-check` and `dossiers` exit 1. The plan's "on
  both interpreters" claim holds.
- **Expected-red completeness.** The four components the plan names are red
  and are the only red components on either interpreter. Plan-review version
  1's M1 is therefore fully closed, and the plan's remediation rule
  (`plan.md:192-201`) no longer directs a spurious escalation.
- **Makefile citations.** `Makefile:24-28` (`test` runs
  `metrics/test_validate_metrics.py`, then the three layers), `:40`
  (`techstack-eval` uses bare `python3`), `:75` (`check` prerequisites), `:76`
  (`sh -n bin/brichan`) are all as the plan states. The layer-by-layer run
  plus the components `make check` executes before aborting covers the whole
  `check` target, including `metrics/test_validate_metrics.py`.
- **Archived versions (DOSSIER-003).** `versions/v1/` holds version 1 of the
  six planner and coordinator artifacts and `versions/v2/` holds version 2 of
  the five planner artifacts plus plan-review version 1. The archived
  `versions/v2/plan-review.md` is byte-identical to the top-level
  `plan-review.md` this artifact replaces, so publishing version 2 destroys no
  review evidence.
- **Artifact self-consistency.** `requirements.md`, `brief.md`, `options.md`,
  `design.md`, and `plan.md` all declare version 3, origin
  `planner:2026-09-25-wfs-a-201-plan-v3`, authoring session
  `b37a1f86-e9d2-440c-ad44-8a535521fe16`, route `plan`, model
  `claude-fable-5`. That differs from this reviewing session, so review
  independence holds on both arms. The validator reports no diagnostic against
  any of the five.

## Test gaps

- **No new test is needed and the design's reasoning is sound.**
  `design.md:62-67` argues that a rename changes no executable behavior and
  that the renamed test is its own regression coverage, so GENERAL-004 is
  satisfied without adding a case. Confirmed above: nothing references the
  test or module by name, and no check enumerates test identifiers.
- **Gap — the category-C subtest instantiates only `Cc`.** U+0085 is category
  `Cc`; `Cf`, `Co`, `Cs`, and `Cn` are unexercised, so the new name's class is
  broader than the fixture. It still names the guard the assertion drives
  (`src/brichan/techstacks/markdown.py:331-332` rejects the whole category),
  so this is not a name-accuracy defect under criterion 1. Widening the
  fixture would change assertions and is forbidden by criterion 2.
  `plan.md:221-227` already records it as coverage debt rather than acting on
  it, which is the correct disposition.
- **Gap — nothing pins a test name to its assertions.** The drift this task
  repairs is invisible to the suite; no check would have caught the name going
  stale when the prose class was amended, and none will catch the next one.
  Out of scope for a behavior-neutral rename. `plan.md:224-227` records it.
- **No test gap is introduced by version 3.** The plan adds no test and
  removes none; the assertion set is byte-identical before and after.

## Residual risks

- **The strict criterion 3 may still reach the implementer.** Restated from
  M1 because it is the only residual with a plausible path to an out-of-scope
  edit. Until the implementation packet carries the restated wording, an
  implementer holding both documents must choose between them.
- **A second stale "markup" claim of the same origin survives, correctly out
  of scope.** `tests/unit/test_techstack_markdown.py:347-351`
  (`test_the_title_class_is_wider_than_the_prose_class`) still states that a
  title "may carry the markup characters a Scope or Verification bullet may
  not"; after the same P6a amendment only the `Title | t` fixture value is
  prose-exclusive, while `<b>Title</b>` and ``Title `t` `` are not. Version 3
  now records this in both `design.md:74-82` and `plan.md:214-220`, which is
  what plan-review version 1 asked for. It remains a coordinator follow-up
  row, not work for this task.
- **Acceptance cannot be fully green inside this task.** `make dossiers` and
  `test_repository_checkout_validates_clean` stay red until the coordinator
  fills `index.md`, `code-review.md`, `pr-desc.md` and creates `receipt.md`.
  The close must read the diagnostics, not the exit code.
- **`index.md` is still an unfilled scaffold** and carries 28 of the 39
  current diagnostics, including an absent canonical receipt and a status
  table that disagrees with every artifact it projects. It is coordinator-owned
  and outside this review's single-file write scope, but it is the gating item
  for task close and it must record the accepted plan ID and version, review
  route strength `routine`, and ship authorization `not-requested`.
- **The two-interpreter gate is heavier than the change.** TEST-001 conditions
  the dual-interpreter run on interpreter-sensitive code, which a `def` rename
  is not; the general verification line asks for `make check` on both. The
  coordinator ratified the dual run, so the plan is right to follow it. Noted
  because this task is an arm of a workflow-simplification measurement, where
  process cost is itself the observable.
- **Review-route provenance diverged from the configured route.**
  `config/model-routing.json` routes `review` to the codex runtime
  (`gpt-5.6-sol`, effort `medium`); this review ran on the claude runtime as
  `claude-opus-5`. Level 0 requires only the routine review route and
  independence holds, so the verdict stands; the metadata records what was
  effective, not what was configured.

## Evidence

- Reviewed artifacts, read in full against `request.md` version 1:
  `requirements.md` (v3), `brief.md` (v3), `options.md` (v3), `design.md`
  (v3), and `plan.md` (v3, plan ID `WFS-A-201-PLAN-001`, status `draft`), with
  `client-follow-up-questions.md` (v2, coordinator-owned) and the archived
  `versions/v2/plan-review.md` (v1) as the closure baseline.
- Source evidence: `src/brichan/techstacks/markdown.py:319-333`;
  `tests/unit/test_techstack_markdown.py:537-563`, `:565`, `:566-569`,
  `:570-574`, `:347-351`; `Makefile:24-28`, `:40`, `:75`, `:76`;
  `tests/contract/test_repository_contract.py:394-432` (the home-path scan
  whose two bare prefixes `/Users` and `/home` DOSSIER-002 governs);
  `projects/brida-workflow-simplification/tasks.md:29`.
- Reference evidence (criterion 3): `git grep -n` for the old name returns
  `projects/brida-workflow-simplification/tasks.md:29` and
  `tests/unit/test_techstack_markdown.py:565`; `git grep -n` for the new name
  and for the `test_prose_rejects_pipe` prefix return nothing; a whole-tree
  `grep -rIn` outside this dossier returns the same two old-name lines.
- Guard-sensitivity probe (TEST-003): run out of tree with `_is_prose`
  substituted in memory only; results listed under Verification performed. No
  repository file was modified, and `git status --short` was empty before and
  after this review's single write.
- Gate evidence: both interpreters, all components, as listed under
  Verification performed. Validator before this write: 39 diagnostics across 8
  dossiers, distributed `index.md` 28, `code-review.md` 5, `pr-desc.md` 5,
  `plan-review.md` 1, none against the five planner-owned artifacts.
- Techstack Snapshot pointer for this review attempt:
  `projects/brida-workflow-simplification/handoffs/WFS-A-201/snapshots/attempt-plan-review-2-f03b2c93223620291d1d267974b8061472c70ba72bfd52bee0220aaf7e56a86f.snapshot.json`,
  sha256
  `f03b2c93223620291d1d267974b8061472c70ba72bfd52bee0220aaf7e56a86f`, verify
  status `match` on 2026-09-25 before any other work; acknowledged Context IDs
  `general`, `policy`, `policy-dossiers`, `python`, `python-tests`, `root`; all
  six selected rule files (`techstacks/README.md`, `techstacks/general.md`,
  `techstacks/policy/README.md`, `techstacks/policy/task-dossiers.md`,
  `techstacks/python/README.md`, `techstacks/python/tests.md`) read in full.
- Policy applied: `docs/policy/reviewer.md` (task-dossier section: the
  reviewer writes `plan-review.md` and nothing else, names the exact plan ID
  and version, records reviewing session identity and a PASS / CHANGES
  REQUIRED verdict, and never back-writes a planning artifact) and
  `docs/workflows/task-dossier.md` (evidence contract, level 0 depth, review
  independence, DOSSIER-003 archive immutability).

## Uncertainty

- Whether the coordinator will reissue criterion 3 in its restated form to the
  implementation and code-review packets is outside this worktree's
  observation. M1 is raised on that basis and would be withdrawn once the
  reissued packet exists; the plan itself needs no further change either way.
- `Effective effort` is recorded as `medium`, the effort
  `config/model-routing.json` configures for the `review` route; this session
  surfaced no per-session effort value to confirm it directly. The recorded
  route and model are what actually ran.
- No other uncertainty remains: every claim plan version 3 makes about the
  code, the reference set, the archives, and the gate was measured against
  this worktree rather than accepted, on both interpreters, and the results
  are listed above.
