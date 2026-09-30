# Implementation report

Implementation evidence for accepted plan `WFS-A-201-PLAN-001` version 3.

## Report metadata

- Task ID: `WFS-A-201`
- Plan ID: `WFS-A-201-PLAN-001`
- Plan version: `3`
- Attempt ID: `attempt-implement-1`
- Owner: `implementer`
- Authorship: `model`
- Effective model: `claude-opus-5-5`
- Date: `2026-09-25`
- Changes: uncommitted in the detached worktree

## Outcome

Done. The test is renamed from
`test_prose_rejects_control_and_markup_characters` to
`test_prose_rejects_pipe_and_category_c_characters`. The change is one
line and does not change behavior. Every plan step is met, and the ratified
completion gate is red only for the four expected-red components on both
interpreters. There are no deviations.

## Changed files

| Path | Change |
|---|---|
| `tests/unit/test_techstack_markdown.py` | Line 565: the `def` is renamed. The comment, subtests and helpers are byte-identical. |
| `projects/brida-workflow-simplification/handoffs/WFS-A-201/implementation.md` | This report. It is untracked and gitignored dossier state. |

`git diff --stat`: `tests/unit/test_techstack_markdown.py | 2 +-`, 1 file
changed, 1 insertion(+), 1 deletion(-). `git status --short`:
` M tests/unit/test_techstack_markdown.py` only.

## Plan steps

### Step 1 — Verify before work

`bin/brichan techstacks verify ... --snapshot-json
projects/brida-workflow-simplification/handoffs/WFS-A-201/snapshots/attempt-implement-1-ff4586a03aa87fa0420e36268c968f75fd91b2e6eb34d4039809b6a6cb4dcebf.snapshot.json
--as-of 2026-09-25` returned `"status": "match"` with no differences. The
observed sha256 is
`ff4586a03aa87fa0420e36268c968f75fd91b2e6eb34d4039809b6a6cb4dcebf`. This ran
before any other work. `brichan` is not on PATH, so the checkout
`bin/brichan` was used. I read all six selected rule files in full:
`techstacks/README.md`, `techstacks/general.md`,
`techstacks/policy/README.md`, `techstacks/policy/task-dossiers.md`,
`techstacks/python/README.md` and `techstacks/python/tests.md`. I also read
`docs/policy/operating-principles.md`.

### Step 2 — The edit

The edit follows `design.md` version 3 exactly:

```
-    def test_prose_rejects_control_and_markup_characters(self):
+    def test_prose_rejects_pipe_and_category_c_characters(self):
```

The new name matches the assertions. The two subtests reject U+007C
(`a|b`) and a Unicode category C character (U+0085, `Cc`). No markup
character is asserted against. The leading comment already names exactly
these two rejections, so it is unchanged.

### Step 3 — Neutrality verification

- `git diff -- tests/unit/test_techstack_markdown.py`: one `def` line
  removed and one added. Nothing else changed.
- `git grep -n test_prose_rejects_control_and_markup_characters`: the only
  hit is `projects/brida-workflow-simplification/tasks.md:29`. That row is
  permitted coordinator-owned residue under the restated criterion in
  `client-follow-up-questions.md` version 2, and it was not edited.
- `git grep -n test_prose_rejects_pipe_and_category_c_characters`: the only
  hit is `tests/unit/test_techstack_markdown.py:565`.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest
  tests.unit.test_techstack_markdown -v` (Python 3.10.11): 47 tests, OK.
  `test_prose_rejects_pipe_and_category_c_characters
  (LeafGrammarTest) ... ok`.

### Step 4 — Gates and report

`PYTHONDONTWRITEBYTECODE=1 make check` on Python 3.10.11 exits 2. Its
components ran as follows:

- The first unittest group ran 10 tests, OK.
- `test-unit` ran 1026 tests, OK.
- `test-contract` ran 148 tests with exactly 2 failures, both in
  `tests/contract/test_repository_paths.py`:
  - `test_current_path_and_link_contracts_pass`
  - `test_every_non_ephemeral_root_file_is_classified`

  Both report `unclassified root files: .git`. They are expected,
  pre-existing and worktree-only, and they stop `make check` as the plan
  predicts.

Ratified layer-by-layer gate, with `PYTHONDONTWRITEBYTECODE=1` throughout:

| Component | 3.10 shell interpreter | `PYTHON=/opt/homebrew/bin/python3.14` |
|---|---|---|
| `make test-unit` | 1026 OK | 1026 OK |
| `make test-contract` | 148, 2 failures (expected: the two `.git` failures above) | same 2 failures (expected) |
| `make test-integration` | 222, 1 failure: `test_repository_checkout_validates_clean` (expected) | same 1 failure (expected) |
| `make techstack-eval` | 56 OK | 56 OK (the recipe runs bare `python3`); direct `python3.14 -m unittest evals.techstack_context_v1.test_cases`: 56 OK |
| `make metrics` | exit 0 | exit 0 |
| `make receipts` | exit 0 | exit 0 |
| `make dossiers` | exit 2, 40 issues (expected) | exit 2, 40 issues (expected) |
| `make memory-check` | exit 0 | exit 0 |
| `make path-check` | exit 2, `unclassified root files: .git` (expected) | same (expected) |
| `make readme-check` | exit 0 | exit 0 |
| `make phase5-preflight` | exit 0 | exit 0 |
| `make package-check` | exit 0 | exit 0 |
| `sh -n bin/brichan` | exit 0 | n/a (the interpreter doesn't matter) |

Every red cell is one of the four expected-red components that
`client-follow-up-questions.md` version 2 and plan Step 4 name. Every other
component is green on both interpreters.

The dossier validator was run with `PYTHONDONTWRITEBYTECODE=1 python3
scripts/validate_task_dossiers.py projects`. It exits 1 with 40 diagnostics,
and every one is in this dossier: `index.md` 30, `code-review.md` 5 and
`pr-desc.md` 5. The five planner-owned artifacts (`requirements.md`,
`brief.md`, `options.md`, `design.md`, `plan.md`) have no diagnostic, which
is the distribution the plan requires. No diagnostic is in any other
dossier.

The count is 40, against 38 when the plan was written. The two extra
diagnostics are `index.md` status mismatches for `client-follow-up-questions`
and `plan-review`: those artifacts now declare `passed`, but the still
unfilled coordinator `index.md` template shows placeholders. This follows
the plan's instruction to compare the distribution, not the absolute count.
Both are coordinator-owned and are not defects of this change. The
`test_repository_checkout_validates_clean` integration failure reports the
same `index.md` diagnostics.

## Acceptance criteria

- The name is accurate. The new name states exactly what the two assertions
  check: rejection of U+007C and of Unicode category C characters.
- Behavior is neutral. The diff is the one `def` line. No assertion,
  subtest value, helper or comment changed.
- No old-name references remain in scope. `git grep` finds the old name
  only in coordinator-owned `projects/brida-workflow-simplification/tasks.md:29`.
- The gate passes as ratified. `make check` fails only on the two known
  worktree-only contract failures. The layer-by-layer gate on 3.10 and 3.14
  is red only for the four expected-red components.

## Deviations

None.

## Risks and follow-ups

- `tasks.md:29` still quotes the old name. It is coordinator-owned
  and was left untouched by decision.
- The sibling stale comment at
  `tests/unit/test_techstack_markdown.py:347-351` and the category-C
  coverage gap (only `Cc` is exercised) remain. Both are out of scope and
  already referred to the coordinator in plan version 3.
- The `make dossiers` and integration redness will clear only after the
  coordinator fills `index.md`, `code-review.md`, `pr-desc.md` and
  `receipt.md`. This report is not a standard dossier artifact, and the
  validator raised no diagnostic for it.
