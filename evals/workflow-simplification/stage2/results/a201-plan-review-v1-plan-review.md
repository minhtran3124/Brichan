# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `WFS-A-201`
- Task level: `0`
- Artifact: `plan-review`
- Artifact version: `1`
- Origin: `reviewer:2026-09-25-wfs-a-201-plan-review-v1`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `b21d917d-5f2c-4320-815d-c563d3c84ec8`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `medium`
- Reviewing session: `b21d917d-5f2c-4320-815d-c563d3c84ec8`
- Review verdict: `CHANGES REQUIRED`

## Review target

- Reviewed plan ID: `WFS-A-201-PLAN-001`
- Reviewed plan version: `2`

## Claim or decision

**CHANGES REQUIRED.** The technical core of the plan is correct and was
verified independently: the selected name
`test_prose_rejects_pipe_and_category_c_characters` accurately describes both
assertions, the single-line `def` rename is genuinely behavior-neutral, the
name is unique in the repository, and neither subtest becomes vacuous after
the rename. Two defects sit outside that core. First, following the plan as
written does **not** satisfy acceptance criterion 3 of the review packet ("no
other reference to the old name remains anywhere in the repository"): the
plan deliberately leaves `projects/brida-workflow-simplification/tasks.md:29`
carrying the old name, on the authority of a coordinator restatement whose
only record is the planner-owned artifacts themselves, while the packet
issued for this review attempt still states the unrestated criterion. Second,
the plan's Step 4 expected-outcome statement is factually incomplete for this
worktree: two further gate components fail for known environment reasons the
plan does not name, and the plan's own remediation rule directs the
implementer to stop and escalate on exactly those failures.

## Findings

### H1 (high) — the plan does not meet packet acceptance criterion 3, and the restatement it relies on is not verifiable in the repository

`requirements.md:60-67` (R3) and `plan.md:54-74` restate the reference
criterion as "no reference to the old name remains outside coordinator-owned
project memory and immutable dossier provenance", and record
`projects/brida-workflow-simplification/tasks.md:29` as permitted residue on
the authority of a coordinator "option (b)" decision of 2026-09-25. The
review packet for attempt `attempt-plan-review-1` still states the criterion
as "No other reference to the old name remains anywhere in the repository
(`git grep` evidence)". Both cannot hold.

Verified state before the change (`git grep -n`, this worktree, 2026-09-25):
the old name has exactly two tracked references,
`tests/unit/test_techstack_markdown.py:565` (the rename target) and
`projects/brida-workflow-simplification/tasks.md:29`. A whole-tree `grep -rI`
outside the dossier returns the same two lines and nothing else. So after the
plan's single-line edit, `git grep` will still return
`projects/brida-workflow-simplification/tasks.md:29`, and the packet's
criterion 3 fails on its own evidence command.

The plan's position is defensible on the merits — the `tasks.md:29` row is a
task-description row in coordinator-owned project memory, and editing it
would put the implementer outside both declared Techstack scope paths — but
the decision that makes it permissible is cited only as "relayed in the
version 2 coordinator packet" (`plan.md:181-184`, `requirements.md:113-114`).
There is no in-repository record a later reviewer, the code review, or task
close can check, and the packet that reached this review still carries the
strict wording.

Required: the coordinator either records the restated criterion where it is
verifiable for the remainder of this task's lifecycle (and reissues it to the
implementation and code-review packets so they do not apply the strict form),
or the plan gains an explicit step for `tasks.md:29` with the scope expansion
that implies. This review does not assert which resolution is correct; it
asserts that the plan and its governing criteria currently disagree.

### M1 (medium) — Step 4's expected-failure set is incomplete, and the plan's remediation rule turns the omissions into spurious escalations

`plan.md:110-129` predicts that `make check` stops in `test-contract` with
exactly the two known worktree-only failures, then directs the implementer to
run the remaining layers individually, naming only a red `make dossiers` as
further expected redness. Measured in this worktree at plan-review time, two
more components of that individual run fail:

- `make path-check` (`scripts/check_repository_paths.py`) exits `1` printing
  `unclassified root files: .git` — the same detached-worktree cause as the
  two contract failures, since `.git` is a file here rather than a directory.
  It never runs under `make check` itself because `check` reaches `path-check`
  only after `test` succeeds (`Makefile:75`), which is why the plan's
  `make check` prediction is nonetheless correct.
- `make test-integration` fails one test,
  `tests/integration/test_task_dossier_workflow.py:279`
  (`test_repository_checkout_validates_clean`), because the in-flight
  WFS-A-201 dossier still holds scaffold placeholders in `index.md`,
  `code-review.md`, `pr-desc.md`, and a missing `receipt.md`. This is the same
  lifecycle-sequencing cause the plan already accepts for `make dossiers`, but
  it surfaces as a test failure, not a validator diagnostic.

`plan.md:146-150` tells the implementer that "any test failure outside the two
known worktree-only contract failures" must be diagnosed and escalated rather
than fixed. Applied literally, both failures above trigger an escalation that
the plan could have predicted. Nothing is at risk of being broken — the rule
correctly forbids fixing — but the acceptance evidence the implementer
produces will not match the plan's stated expectation, and criterion 4 as
worded in the packet ("`make check` passes apart from the two known
worktree-only failures") is only satisfiable because `make check` aborts
before reaching the other two.

Required: Step 4 names `make path-check` and the
`test_repository_checkout_validates_clean` integration failure as expected
worktree/lifecycle redness alongside `make dossiers`, so the implementer
reports them instead of escalating.

### L1 (low) — the substitute gate run omits the `check` recipe body

`plan.md:120-124` reconstructs the aborted remainder of `make check` as
`make test-integration`, `make techstack-eval`, and the non-test targets
`metrics receipts dossiers memory-check path-check readme-check
phase5-preflight package-check`. That list matches the prerequisites of
`check` (`Makefile:75`) but omits the recipe line the target runs after them,
`sh -n bin/brichan` (`Makefile:76`). The launcher is untouched by this task,
so the omission costs no real coverage; it means only that "the rest of the
gate is exercised" is slightly overstated. The layers that run before the
abort (`metrics/test_validate_metrics.py`, `make test-unit`) are covered.

### L2 (low) — the recorded validator baseline is already stale and invites a false mismatch

`plan.md:166-170` records the baseline "the dossier validator reports 65
diagnostics, all in the WFS-A-201 scaffold placeholders that this plan's
artifacts replace". Measured now, `scripts/validate_task_dossiers.py projects`
reports 43 diagnostics, distributed as `index.md` 26, `code-review.md` 5,
`plan-review.md` 5, `pr-desc.md` 5, `receipt.md` 1, plus one summary line, and
none against the five planner-owned artifacts. The drop is exactly what
filling those five artifacts predicts, so the baseline is not wrong — but the
plan does not say the count will fall, so an implementer comparing Step 4
output against it can read a correct result as a discrepancy. (Counts above
were measured before this artifact was written; with it in place the total is
39, `plan-review.md` carries none of its own, and `index.md` gains two rows
reporting that its placeholder status table now disagrees with this
artifact — coordinator-owned, expected, and not repaired here.)

## Test gaps

- **No new test is needed, and the design's reasoning for that is sound.**
  `design.md:57-60` argues that a rename changes no executable behavior and
  that the renamed test is itself the regression coverage, so GENERAL-004 is
  satisfied without adding a case. Confirmed: nothing outside the module
  references the test by name, and no test enumerates test-method names, so
  the rename cannot break another assertion.
- **TEST-003 verified, not assumed.** `techstacks/python/tests.md` TEST-003
  requires a rejection-named test to call the production path and fail when
  the guard is removed. I checked this rather than taking `design.md:52-56` on
  trust: with `_is_prose` replaced in memory by a copy missing only the `|`
  guard, `- Applies to a|b.` parses successfully; with a copy missing only the
  category-C guard, `- Applies to a\u0085b.` parses successfully; the
  unmodified guard rejects both with `INVALID_LEAF` at line 13. Each subtest
  therefore fails when, and only when, the guard its new name claims is
  removed. Neither assertion is vacuous, and the rename does not touch this.
- **Gap — the category-C subtest instantiates only `Cc`.** U+0085 is category
  `Cc`; `Cf`, `Co`, `Cs`, and `Cn` are unexercised, so the new name's
  "category c characters" is broader than the fixture's coverage. The name
  still describes the guard the assertion drives, and
  `src/brichan/techstacks/markdown.py:331-332` rejects the whole category, so
  this is not a name-accuracy defect under criterion 1. Widening the fixture
  would change assertions and is forbidden by criterion 2; record it as
  coverage debt rather than acting on it here.
- **Gap — nothing pins a test name to its assertions.** The drift this task
  repairs is invisible to the suite: no check would have caught the name going
  stale when the prose class was amended, and none will catch the next one.
  Out of scope for a behavior-neutral rename; worth a separate follow-up if
  the pattern recurs.

## Residual risks

- **A second stale "markup" claim of the same origin survives, correctly out
  of scope.** `tests/unit/test_techstack_markdown.py:348-351`, the comment of
  `test_the_title_class_is_wider_than_the_prose_class`, still states that a
  title "may carry the markup characters a Scope or Verification bullet may
  not". After the same P6a amendment that made this task's name stale, prose
  accepts backticks and angle brackets, so two of that test's three fixture
  values (`<b>Title</b>`, ``Title `t` ``) are no longer prose-exclusive; only
  `Title | t` is. Fixing it here would breach criterion 2 (the diff must be
  the one `def` line), so the plan is right not to touch it — but neither the
  plan nor the requirements notes it exists, and it is the same class of
  finding as TECHSTACK-002 stage-2 `L3`. Recommend the coordinator record it
  as its own follow-up row.
- **Name generalization is a deliberate, defensible trade-off.**
  `options.md:42-46` rejects `..._pipe_and_control_characters` because
  "control" understates the guarded class. The selected name has the mirrored
  property: it states the class the guard enforces while the fixture
  instantiates one member of it. It matches the test's own comment
  (`tests/unit/test_techstack_markdown.py:566-569`) and the production check,
  which is the stronger anchor, so option A remains the right selection.
- **The `L3` provenance could not be reread at source.** `brief.md:57-62`
  records that the TECHSTACK-002 dossier is absent from this worktree; I
  confirmed that. The staleness claim does not depend on it: the code and the
  sibling acceptance test at `tests/unit/test_techstack_markdown.py:537-563`
  establish independently that markup characters are accepted.
- **Acceptance cannot be fully green inside this task.** `make dossiers` and
  `test_repository_checkout_validates_clean` stay red until the coordinator
  fills `index.md`, `receipt.md`, `code-review.md`, and `pr-desc.md`. That is
  lifecycle sequencing, as `plan.md:124-129` says — but it means the task
  cannot be closed on gate colour alone, and the close must read the
  diagnostics rather than the exit code.
- **Review-route provenance diverged from the configured route.**
  `config/model-routing.json` routes `review` to the codex runtime
  (`gpt-5.6-sol`, effort `medium`); this review ran on the claude runtime as
  `claude-opus-5`. Level 0 requires only the routine review route, and
  reviewer independence holds (the plan was authored by session
  `001cf011-1d97-4408-8c17-c4bc93269041` on `claude-fable-5`), so the verdict
  stands; the divergence is recorded because the metadata above must state
  what was effective, not what was configured.

## Evidence

- Reviewed artifacts:
  `projects/brida-workflow-simplification/handoffs/WFS-A-201/requirements.md`
  (v2), `brief.md` (v2), `options.md` (v2), `design.md` (v2), and `plan.md`
  (v2, plan ID `WFS-A-201-PLAN-001`, status `draft`), read in full against
  `request.md` v1.
- Name accuracy (criterion 1) confirmed at source:
  `src/brichan/techstacks/markdown.py:319-333` rejects `|` and any character
  whose Unicode category starts with `C`, and accepts backticks and angle
  brackets; `tests/unit/test_techstack_markdown.py:565-574` asserts exactly
  those two rejections; `tests/unit/test_techstack_markdown.py:537-563`
  asserts the markup acceptance that makes the old name false.
- Guard-sensitivity probe (TEST-003), run out-of-tree against the installed
  module with `_is_prose` substituted in memory only: removing the `|` guard
  makes `- Applies to a|b.` parse; removing the category-C guard makes
  `- Applies to a\u0085b.` parse; the unmodified guard rejects both with
  `INVALID_LEAF` at line 13. No repository file was modified.
- Reference evidence (criterion 3): `git grep -n
  test_prose_rejects_control_and_markup_characters` returns
  `tests/unit/test_techstack_markdown.py:565` and
  `projects/brida-workflow-simplification/tasks.md:29`; `git grep -n
  test_prose_rejects_pipe_and_category_c_characters` and `git grep -n
  test_prose_rejects_pipe` return nothing, so the selected name collides with
  nothing; a whole-tree `grep -rI` outside this dossier returns the same two
  old-name lines.
- Gate evidence measured at plan-review time (`PYTHONDONTWRITEBYTECODE=1`,
  `PYTHONPATH=src`, Python 3.10): focused module
  `tests.unit.test_techstack_markdown` 47/47 OK; `tests/contract` 148 tests,
  2 failures, both `tests/contract/test_repository_paths.py`
  ("unclassified root files: .git"); `scripts/check_repository_paths.py`
  exit 1, same message; `tests/integration` 222 tests, 1 failure
  (`tests/integration/test_task_dossier_workflow.py:279`); `techstack-eval`
  56/56 OK; `metrics/test_validate_metrics.py` 10/10 OK; `metrics`,
  `receipts`, `memory-check`, `readme-check`, `phase5-preflight` all exit 0;
  `git status --short` empty before and after this review's single write.
- Techstack Snapshot pointer for this review attempt:
  `projects/brida-workflow-simplification/handoffs/WFS-A-201/snapshots/attempt-plan-review-1-aa7f1d1723990905798ffd612907d54a12dd8e2d35ec1a87a1dd62c9d8cd15f8.snapshot.json`,
  sha256 `aa7f1d1723990905798ffd612907d54a12dd8e2d35ec1a87a1dd62c9d8cd15f8`,
  verify status `match` on 2026-09-25 before any other work; the six selected
  rule files (`techstacks/README.md`, `techstacks/general.md`,
  `techstacks/policy/README.md`, `techstacks/policy/task-dossiers.md`,
  `techstacks/python/README.md`, `techstacks/python/tests.md`) were read in
  full.
- Policy applied: `docs/policy/reviewer.md` (task-dossier section: reviewer
  writes `plan-review.md` and nothing else, names the exact plan ID and
  version, records reviewing session identity and a PASS / CHANGES REQUIRED
  verdict) and `docs/workflows/task-dossier.md` (evidence contract, level 0
  depth, review independence).

## Uncertainty

- The coordinator's 2026-09-25 "option (b)" decision is unverifiable from this
  worktree; H1 is raised on that basis and would be withdrawn if the decision
  is recorded somewhere a later session can read, and reissued to the
  implementation and code-review packets.
- `Effective effort` above is recorded as `medium`, the effort configured for
  the `review` route; this session surfaced no per-session effort value to
  confirm it directly. The recorded route and model are what actually ran.
- No other uncertainty remains: every claim the plan set makes about the code,
  the reference set, and the gate was checked against the repository rather
  than accepted, and the results are listed under Evidence.
