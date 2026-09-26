# Code review

Independent review of the implementation, or the recorded evidence for why no implementation review applies.

## Artifact metadata

- Task ID: `WFS-A-201`
- Task level: `0`
- Artifact: `code-review`
- Artifact version: `1`
- Origin: `reviewer:2026-09-25-wfs-a-201-code-review-v1`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `2b6bf2ef-2397-46ba-9cb8-18ef0d0088a5`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `medium`
- Reviewing session: `2b6bf2ef-2397-46ba-9cb8-18ef0d0088a5`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `WFS-A-201-PLAN-001`
- Reviewed plan version: `3`

## Claim or decision

**PASS. Totals 15/15** — Spec fidelity 5, Code review 5, Empirical
verification 5. No finding at any severity.

The uncommitted change is exactly the one-line `def` rename that accepted
plan version 3 and `design.md` prescribe, and all four acceptance criteria
hold. Every claim in `implementation.md` that I checked reproduced in this
worktree; I re-ran the whole ratified gate on both interpreters rather than
reading the report's table, and I did not rely on the report as proof of
anything.

Three things I verified independently rather than accepting:

1. **The new name is accurate, and it is accurate for the right reason.**
   The two subtests drive `assert_invalid_leaf`
   (`tests/unit/test_techstack_markdown.py:363-369`) with a Scope prose
   bullet containing U+007C (`- Applies to a|b.`) and U+0085
   (`- Applies to a\u0085b.`); those are exactly the two retained
   rejections in `_is_prose` (`src/brichan/techstacks/markdown.py:329-332`).
   Nothing in the test asserts against a markup character — that behavior
   is the *accepting* sibling at `tests/unit/test_techstack_markdown.py:537`
   — so the old name over-claimed and the new one does not.
2. **The rename does not make a passing assertion vacuous (TEST-003).** A
   guard-substitution probe monkeypatched `markdown._is_prose` with
   variants missing each guard and re-ran only the renamed test: baseline
   ok; pipe guard removed → 1 failure; category-C guard removed → 1
   failure; both removed → 2 failures. Each subtest fails when, and only
   when, the guard its new name claims is removed, and the failures arrive
   through `parse_leaf`, the production path.
3. **The rename has no non-local effect.** `unittest` orders methods within
   a class by name, so a rename shifts execution position; this module
   defines no `setUp`, `setUpClass` or `tearDown` anywhere and copies the
   `BASE_LEAF_LINES` tuple per case, so the shift is inert. No file outside
   the module names the method: `/usr/bin/grep -rn "test_prose"` across
   `*.py`, `*.json`, `*.md`, `*.yml`, `*.yaml`, `*.cfg`, `*.toml` and
   `Makefile` returns only `tasks.md:29`, and nothing in `tests/` or
   `scripts/` introspects `_testMethodName` or filters on a `test_` prefix,
   so no CI selection, inventory or contract test keys off the old name.

## Per-criterion scores

| Criterion | Score | Basis |
|---|---|---|
| Spec fidelity | 5 | All four acceptance criteria hold. The edit matches `design.md`'s prescription byte for byte — `od -c` on line 565 shows four-space indentation, the exact new identifier, `(self):` and a single terminating LF, with no trailing whitespace. R2's only-if-needed comment allowance was correctly left unexercised: the leading comment at lines 566-569 already named both retained rejections. The one documented edge case — that criterion 3 is the coordinator's restated form, not the strict "anywhere in the repository" form — resolves in the implementer's favor, and this review packet carries the restated wording, which closes plan-review version 2's finding M1 on the coordinator side. |
| Code review | 5 | Behavior-neutral by construction and by measurement: `git diff --numstat` is `1 1 tests/unit/test_techstack_markdown.py` and `git status --short` lists that file alone. No assertion, subtest value, fixture, helper or comment changed. No silent regression is reachable — the probe above shows both guards still load-bearing, the name is unique in the repository (one `def`, no shadowing sibling that a duplicate name would have silently overridden), and no unrequested behavior change appears anywhere in the diff. Scope discipline held: `tasks.md:29` and the byte-frozen `versions/v1/` and `versions/v2/` copies were not touched. |
| Empirical verification | 5 | Every number in `implementation.md` reproduced exactly under my own runs (table below), including the ones easiest to fudge: the 40 validator diagnostics and their 30/5/5 distribution, and the `techstack-eval` count under the interpreter the recipe does not follow. The report's one divergence from the plan (40 diagnostics against the plan's 38) is explained correctly and by the rule the plan set — compare the distribution, not the count — and I confirmed the two extra lines are the `index.md` phase-state mismatches for `client-follow-up-questions` and `plan-review`. I also confirmed the validator's summary line means 40 diagnostics across the 8 dossiers *scanned*, not 8 dossiers with diagnostics (`src/brichan/contracts/task_dossier/validation.py:1261-1272`, where the count is `len(dossiers)`), so the report's "no diagnostic is in any other dossier" is true and not a misread. No edit followed the last successful check: every check in the table ran against the current bytes, after the implementer's last write. |

## Findings

**None.** No critical, high, medium or low finding. I looked specifically
for, and did not find: an assertion or fixture altered under cover of the
rename (`git diff` is one line); a name that still over-claims or now
under-claims what the assertions check; a vacuous assertion after the
rename (probed); a duplicate method name silently shadowing the other
(`grep -n "def test_prose_rejects"` returns one line); a stale reference in
code, tests, docs, CI config or tooling (exhaustive `/usr/bin/grep -rl`
across the worktree); an order-dependent interaction created by the shifted
sort position (no shared fixture state exists); and a gate failure outside
the four ratified expected-red components on either interpreter.

Items I considered and deliberately did **not** classify as defects, with
the reason each stays out of this section, are under residual risks.

## Test gaps

- **Category C is exercised by one representative.** The subtest
  instantiates only U+0085 (`Cc`), while `_is_prose`
  (`src/brichan/techstacks/markdown.py:331`) rejects the whole category;
  `Cf`, `Co`, `Cs` and `Cn` are unexercised. Widening the fixture would
  change a subtest value, which acceptance criterion 2 forbids, so this is
  correctly left as debt. Already recorded in plan version 3's follow-up
  section.
- **Nothing pins a test name to its assertions.** The drift this task
  repairs was invisible to the suite and would be invisible again. No guard
  was added, by design — adding one is out of scope and would be new
  executable behavior. Worth a follow-up only if the pattern recurs a third
  time.
- **One sibling instance of the same drift class remains, and I confirmed
  it.** `tests/unit/test_techstack_markdown.py:347-351` still says a title
  "may carry the markup characters a Scope or Verification bullet may not".
  After the same amendment that is false: prose accepts backticks and angle
  brackets, and of that test's three fixture values only `Title | t`
  (U+007C) is title-exclusive, because `_is_title`
  (`src/brichan/techstacks/markdown.py:336-341`) rejects category C but not
  U+007C. The test *name* there is still accurate — the title class is
  genuinely wider — so only the comment is stale, a narrower repair than
  this task's. Out of scope here under criterion 2; plan version 3 already
  referred it to the coordinator.

## Residual risks and required human decisions

- **`make check` does not exit 0 in this worktree, so `GENERAL-001` is met
  only through the ratified substitute.** The substitute gate is complete
  in substance — I ran all twelve components plus `sh -n bin/brichan` on
  both interpreters — but it is a coordinator ratification, not the rule's
  literal text. A single `PYTHONDONTWRITEBYTECODE=1 make check` exiting 0
  on a normal checkout, with the dossier closed, remains required before
  this change is called done on `main`. That is a coordinator or human step;
  nothing in this worktree can supply it. Not a defect: the worktree
  redness is pre-existing, its four causes are documented, and none is
  reachable from a test rename.
- **The ratified gate has one hole of its own, which I closed rather than
  reported as red.** The component list omits `make test`'s first group,
  `python -m unittest metrics/test_validate_metrics.py` (`Makefile:25`), so
  a strict layer-by-layer pass never runs it; on 3.10 `make check` covered
  it incidentally before aborting, but the 3.14 pass would not have. I ran
  it directly on 3.14: 10 tests, OK. Worth folding into the ratified list
  so the next detached-worktree task does not inherit the hole.
- **`tasks.md:29` now names a symbol that no longer exists.** Keeping it is
  the coordinator's recorded option (b) decision and criterion 3 permits it,
  so it is not a defect. It is still a dangling reference: after this change
  merges, a `git grep` for the old name returns a task row pointing at
  nothing. The coordinator should update or close that S2-1 row when closing
  the task, otherwise the row becomes the last thing in the repository
  asserting a test name that was removed to stop exactly that kind of false
  statement.
- **Reviewer independence is satisfied; reviewer strength is a coordinator
  call.** This session authored neither the plan (`claude-fable-5`, session
  `b37a1f86-e9d2-440c-ad44-8a535521fe16`) nor the implementation, which
  meets the dossier contract. But `config/model-routing.json` configures the
  `review` route for runtime `codex` and model `gpt-5.6-sol`, and this
  review ran on `claude-opus-5` — the same family as the implementer's
  `claude-opus-5-5` and not a stronger model than it. `docs/policy/reviewer.md`
  states a preference for a different provider, not a level 0 gate, and level
  0 permits the routine route, so I record this rather than treat it as a
  contract breach. Whether it is acceptable for this task is the
  coordinator's decision.
- **Judgment call I am recording openly, not burying:** the name says
  "category c characters" (a class) while one representative is asserted. I
  judged this accurate, not an over-claim, because the class is the guard's
  own class, the leading comment states which representative stands in for
  it and why, and the alternative reading would make almost every
  equivalence-class test name a defect. A reviewer applying criterion 1
  more literally could disagree; if the coordinator wants the stricter
  reading, the repair is a comment or a wider fixture, and the fixture
  route is blocked by criterion 2.

## Evidence

- Techstack verify, run before any other work, via `bin/brichan` from the
  worktree root (`brichan` is not on PATH) with
  `--snapshot-json projects/brida-workflow-simplification/handoffs/WFS-A-201/snapshots/attempt-code-review-1-3963f6b454b25c3b1e813e87a7e104f28b94a38618e70657a1662b96a5e091f4.snapshot.json --as-of 2026-09-25`:
  `"status": "match"`, `"differences": []`, observed sha256
  `3963f6b454b25c3b1e813e87a7e104f28b94a38618e70657a1662b96a5e091f4`,
  resolution `applicable`, 12 effective rules, 6 selected files. All six
  required selected rule files were then read in full: `techstacks/README.md`,
  `techstacks/general.md`, `techstacks/policy/README.md`,
  `techstacks/policy/task-dossiers.md`, `techstacks/python/README.md`,
  `techstacks/python/tests.md`. Acknowledged Context IDs: `general`,
  `policy`, `policy-dossiers`, `python`, `python-tests`, `root`.
- Criterion 1 — `tests/unit/test_techstack_markdown.py:565-573` against
  `src/brichan/techstacks/markdown.py:319-333`; the accepting sibling at
  `tests/unit/test_techstack_markdown.py:537`; the call site the fixture
  reaches, `_parse_ordinary_bullets` → `_is_prose`
  (`src/brichan/techstacks/markdown.py:652`).
- Criterion 1 non-vacuity probe — an ad hoc script outside tracked files
  patched `markdown._is_prose` per variant and ran only
  `LeafGrammarTest.test_prose_rejects_pipe_and_category_c_characters`:
  baseline `failures=0`; `drop_pipe` `failures=1`; `drop_cat_c`
  `failures=1`; both `failures=2`.
- Criterion 2 — `git status --short`: ` M tests/unit/test_techstack_markdown.py`
  and nothing else, including under `--untracked-files=all`.
  `git diff --numstat`: `1 1 tests/unit/test_techstack_markdown.py`.
  `git diff` body is one removed and one added `def` line. `od -c` on line
  565 confirms four leading spaces, the exact identifier, and no trailing
  whitespace. `design.md:25-35` prescribes that exact line.
- Criterion 3 — `git grep -n test_prose_rejects_control_and_markup_characters`:
  one hit, `projects/brida-workflow-simplification/tasks.md:29`, the
  permitted coordinator-owned residue.
  `git grep -n test_prose_rejects_pipe_and_category_c_characters`: one hit,
  `tests/unit/test_techstack_markdown.py:565`. Because `git grep` skips the
  gitignored dossier, I also ran `/usr/bin/grep -rl` over the whole worktree
  excluding `.git`: outside this dossier's own provenance files the old name
  survives only in `tasks.md`, which the restated criterion permits.
- Criterion 4, `make check` on the 3.10 shell interpreter (Python 3.10.11):
  exit 2. Its first group ran 10 tests OK, `test-unit` ran 1026 OK, and it
  stopped in `test-contract` at 148 tests with exactly two failures,
  `test_current_path_and_link_contracts_pass` and
  `test_every_non_ephemeral_root_file_is_classified`, both
  `unclassified root files: .git` — the two known worktree-only failures,
  reported and not fixed.
- Criterion 4, ratified layer-by-layer gate, `PYTHONDONTWRITEBYTECODE=1`
  throughout, run twice — once on 3.10.11 and once with
  `PYTHON=/opt/homebrew/bin/python3.14` (Python 3.14.6):

  | Component | 3.10 | 3.14 |
  |---|---|---|
  | `make test-unit` | 1026 OK | 1026 OK |
  | `make test-contract` | 148, 2 failures (expected) | 148, same 2 (expected) |
  | `make test-integration` | 222, 1 failure `test_repository_checkout_validates_clean` (expected) | 222, same 1 (expected) |
  | `make techstack-eval` | 56 OK | 56 OK; direct 3.14 run of the eval also 56 OK |
  | `make metrics` | exit 0 | exit 0 |
  | `make receipts` | exit 0 | exit 0 |
  | `make dossiers` | 40 diagnostics (expected) | 40 diagnostics (expected) |
  | `make memory-check` | exit 0 | exit 0 |
  | `make path-check` | `unclassified root files: .git` (expected) | same (expected) |
  | `make readme-check` | exit 0 | exit 0 |
  | `make phase5-preflight` | exit 0 | exit 0 |
  | `make package-check` | exit 0 | exit 0 |
  | `sh -n bin/brichan` | exit 0 | interpreter-independent |

  Exactly the four ratified expected-red components are red on both
  interpreters; every other component is green on both. I additionally ran
  `metrics/test_validate_metrics.py` directly on 3.14 (10 tests, OK), which
  the ratified component list omits.
- Criterion 4 validator — `python3 scripts/validate_task_dossiers.py projects`
  exits 1 with 40 diagnostics, distributed `index.md` 30, `code-review.md` 5,
  `pr-desc.md` 5, all in this dossier. The five planner-owned artifacts
  (`requirements.md`, `brief.md`, `options.md`, `design.md`, `plan.md`) carry
  no diagnostic, which is the distribution the plan requires. Re-run after
  this artifact replaced the `code-review.md` template: 36 diagnostics,
  distributed `index.md` 31, `pr-desc.md` 5, and none for `code-review.md`.
  The `index.md` count rises by one because this artifact now declares
  `passed` while the coordinator's `index.md` still holds a placeholder for
  it; that projection mismatch and the `pr-desc.md` placeholders are the
  coordinator's to close. `make receipts`, `make memory-check` and
  `make readme-check` were re-run after the write and remain exit 0, and
  `make path-check` still reports only `unclassified root files: .git`.
- Focused module run — `PYTHONPATH=src python3 -m unittest
  tests.unit.test_techstack_markdown -v`: 47 tests, OK, with
  `test_prose_rejects_pipe_and_category_c_characters ... ok`. The renamed
  method is also collected and passing inside `make test-unit` on 3.14.
- Contract and policy sources read for this review:
  `docs/policy/reviewer.md`, `docs/policy/operating-principles.md` section 5,
  `docs/workflows/task-dossier.md` (evidence contract and levels),
  `config/model-routing.json`, and this dossier's `plan.md` version 3,
  `requirements.md`, `design.md`, `client-follow-up-questions.md` version 2,
  `plan-review.md` version 2 and `implementation.md`.

## Uncertainty

- `Effective effort` is recorded as `medium`, the effort
  `config/model-routing.json` configures for the `review` route. No
  per-session effort value was surfaced to this session, so that field is
  the configured value rather than an observed one. The recorded route and
  model are what actually ran.
- Whether reviewing on `claude-opus-5` satisfies the coordinator's intent
  for the `review` route, which the routing config points at `codex` and
  `gpt-5.6-sol`, is a coordinator decision and not something this session
  can settle. Independence from the plan and implementation sessions is
  established; comparative strength against the implementer's
  `claude-opus-5-5` is not.
- No other uncertainty remains about the change itself. Every acceptance
  criterion was measured in this worktree rather than inherited from
  `implementation.md`, and the one judgment call in criterion 1 — a
  class-level name verified by one class representative — is stated
  explicitly under residual risks rather than resolved silently.
