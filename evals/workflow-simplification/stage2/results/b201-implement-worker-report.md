# WFS-B-201 worker report

## Plan

Plan `WFS-B-201-PLAN-001`, version 1. Written before any code edit.

- Approach: rename `test_prose_rejects_control_and_markup_characters` in
  `tests/unit/test_techstack_markdown.py` to
  `test_prose_rejects_vertical_bar_and_category_c_characters`. The two subtest
  values are `a|b` (U+007C) and `a\u0085b` (U+0085, category Cc), so the new
  name names exactly those two rejections. Markup characters are no longer
  rejected (the preceding test asserts they are accepted), so "markup" is
  dropped.
- The existing comment already describes the retained rejections (U+007C and
  category C) accurately, so it stays as is.
- Files: `tests/unit/test_techstack_markdown.py` (one line), and this report.
- Risks: the old name may be referenced elsewhere. A `git grep` before the
  edit found one other reference, in
  `projects/brida-workflow-simplification/tasks.md` line 29, which is outside
  this packet's scope. It is not changed; see Risks and ambiguities.

## Changes

- `tests/unit/test_techstack_markdown.py`: renamed
  `test_prose_rejects_control_and_markup_characters` to
  `test_prose_rejects_vertical_bar_and_category_c_characters`. No assertion,
  subtest value, helper, comment, or other test changed.

## Verification

- Techstack verify (run before any other work):
  `bin/brichan techstacks verify ... --as-of 2026-09-25` returned
  `"status": "match"`, snapshot SHA-256
  `55d9597d1f0effe20b1be0a23199711f993ea93b6e93636ee5505c05b5395419`. All six
  required selected rule files were read.
- Focused: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest -v
  tests.unit.test_techstack_markdown` ran 47 tests, OK, including
  `test_prose_rejects_vertical_bar_and_category_c_characters ... ok`.
- `PYTHONDONTWRITEBYTECODE=1 make check` exited 2:
  - metrics tests: 10 tests OK. `test-unit`: 1026 tests OK.
  - `test-contract`: 148 tests, `FAILED (failures=2, skipped=1)`. The failures
    were exactly the two known worktree-only ones in
    `tests/contract/test_repository_paths.py`
    (`test_current_path_and_link_contracts_pass`,
    `test_every_non_ephemeral_root_file_is_classified`), each reporting
    `unclassified root files: .git`.
  - make stopped at that point, so each later `check` prerequisite was run
    on its own with `PYTHONDONTWRITEBYTECODE=1 make <target>`:
    `test-integration`, `techstack-eval`, `metrics`, `receipts`, `dossiers`,
    `memory-check`, `readme-check`, `phase5-preflight`, and `package-check` all
    exited 0. `path-check` exited 2 with `unclassified root files: .git`. This
    is the same script and the same worktree-only cause as the two known
    contract failures. `sh -n bin/brichan` exited 0.
- `git grep -n test_prose_rejects_control_and_markup_characters`: one match
  remains, `projects/brida-workflow-simplification/tasks.md:29`, which is out of
  scope (see below). There are no matches under `tests/` or `src/`.
- `git grep -n test_prose_rejects_vertical_bar_and_category_c_characters`: one
  match, `tests/unit/test_techstack_markdown.py:565`.
- `git status --short`: ` M tests/unit/test_techstack_markdown.py`. This report
  is not listed because the dossier is gitignored.
- `git diff --stat`: `tests/unit/test_techstack_markdown.py | 2 +-`, 1 file
  changed, 1 insertion(+), 1 deletion(-).

## Risks and ambiguities

- Acceptance criterion conflict: "no other reference to the old name remains
  anywhere in the repository" is not met. The backlog row S2-1 in
  `projects/brida-workflow-simplification/tasks.md` line 29 names the old test
  as the subject of this rename. That file is tracked and outside this
  packet's scope, so it was left unchanged. The coordinator should update or
  close that row when it records the task. Its old name is historical context
  there, not a live reference.
- `make check` fails on the worktree-only `.git` root file. Besides the two
  known contract failures, the `path-check` target fails for the same reason.
  All other gate steps pass. None of these failures relate to the rename.
- The change is behavior-neutral. It renames the test method only, and unittest
  discovery picks up the new name, as the focused run shows.
- Name choice: "vertical bar" stands for U+007C, and "category C" is the
  Unicode general category that the test comment and the section 6 amendment
  use.
