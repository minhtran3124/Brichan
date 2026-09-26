# Worker report

The implementer's plan, written before implementing, and the record of what changed and how it was verified. Levels 0 and 1 only; see the level table in `docs/workflows/task-dossier.md`.

## Artifact metadata

- Task ID: `WFS-008`
- Task level: `0`
- Artifact: `report`
- Artifact version: `1`
- Origin: `WFS-008-report@1`
- Owner: `implementer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `claude-code-45e6ef45`
- Effective route: `implement`
- Effective model: `claude-opus-5-5`
- Effective effort: `medium`
- Reviewing session: `null`
- Review verdict: `null`

## Plan

- Plan `WFS-008-PLAN-001` version 1, written before editing code. Reproduced first: in a detached worktree of `6bab70d`, `make path-check` prints `unclassified root files: .git` (exit 2) and `tests.contract.test_repository_paths` fails twice (`test_every_non_ephemeral_root_file_is_classified`, `test_current_path_and_link_contracts_pass`).
- Fix in code, not the manifest. `ignored_root_files` in `config/repository-paths.json` lists machine-local ephemera (`.DS_Store`, `.env`, `CLAUDE.local.md`); `.git` is git's own metadata entry, already skipped by name for the link walk (`SKIPPED_PARTS`), so the exemption belongs beside it in `scripts/check_repository_paths.py`. A code constant also keeps the exemption out of a list a later edit could widen by accident.
- In `scripts/check_repository_paths.py`: add a `GIT_METADATA = ".git"` constant and extract the root-file classification into `unclassified_root_files(root, manifest)`, which excludes exactly the root entry named `.git` (file or directory; a directory is already excluded by `is_file()`), and nothing else: no pattern, no `SKIPPED_PARTS` reuse (that would also exempt a root file named `__pycache__`). `validate_manifest` calls it with `ROOT`; error text is unchanged.
- In `tests/contract/test_repository_paths.py`: make the duplicated live classification also exclude exactly `.git`, and add regression tests that call `unclassified_root_files` on a temporary root: a `.git` file is not reported; a `.git` directory is not reported; an unclassified root file other than `.git` (and a file named like it, `.git.bak`) is still reported.
- Verify: worktree reproduction after the fix, a mutation run removing the exemption (restored byte-for-byte, SHA-256 compared), `make check` on 3.10 and 3.14, `git status --short`. The diff touches the contract path `scripts/`, so an independent code review follows.

## Changes

- `scripts/check_repository_paths.py`: new `GIT_METADATA = ".git"` constant beside `SKIPPED_PARTS`; the root-file classification moved verbatim into `unclassified_root_files(root, ignored_root_files, known_paths)`, which adds one exclusion, `path.name != GIT_METADATA`. `validate_manifest` calls it with `ROOT`; the `unclassified root files:` error text is unchanged.
- `tests/contract/test_repository_paths.py`: the duplicated live classification in `test_every_non_ephemeral_root_file_is_classified` also excludes exactly `.git`; three new tests call `unclassified_root_files` on a temporary root: `test_a_worktree_git_file_is_not_an_unclassified_root_file`, `test_a_git_directory_is_not_an_unclassified_root_file`, `test_other_unclassified_root_files_are_still_reported` (`.git.bak` and `stray.txt` reported; `.git`, ignored `.env`, inventoried `AGENTS.md` not).
- `config/repository-paths.json`: unchanged (see Plan for why the manifest is the wrong home).

## Verification

- Techstack verify for snapshot `706914c8…58bb`: `status: match`.
- Before the fix, in `git worktree add --detach <SCRATCH>/wfs008-before HEAD` (`.git` is a 92-byte regular file): `make path-check` prints `unclassified root files: .git`, exit 2; `python3 -m unittest tests.contract.test_repository_paths`: `FAILED (failures=2)`. Worktree removed.
- After the fix, in a fresh detached worktree of `HEAD` with the two changed files copied in: `make path-check` prints `repository paths valid: 113 entries, 75 references`, exit 0; the contract module: `Ran 10 tests … OK`. Worktree removed (`git worktree list` shows only the main checkout and the pre-existing `brichan-policy-benchmark`).
- Main checkout: `make path-check` exit 0 with the same line; `tests.contract.test_repository_paths`: 10 tests OK.
- Mutation 1, delete the `and path.name != GIT_METADATA` line: `test_a_worktree_git_file_is_not_an_unclassified_root_file` and `test_other_unclassified_root_files_are_still_reported` fail (`FAILED (failures=2)`). Mutation 2, broaden to `not path.name.startswith(GIT_METADATA)`: `test_other_unclassified_root_files_are_still_reported` fails. After each, the file was restored from a copy; `cmp` clean and SHA-256 `867e609eee1959f065b725accaff178766769fffd327d7a2b5351e29793c0255` before and after.
- `PYTHONDONTWRITEBYTECODE=1 make -k check` with `PYTHON=python3` (3.10) and `PYTHON=/opt/homebrew/bin/python3.14`: exit 2 on both; failing targets are only `test-integration` (one test, `test_repository_checkout_validates_clean`) and `dossiers`, and every error line names WFS-008's pending `index.md` (28), `code-review.md` (10), or missing `receipt.md` (2). Unit 1069 OK, contract 156 OK, `path-check` and every other target pass.
- `git status --short`: `M scripts/check_repository_paths.py`, `M tests/contract/test_repository_paths.py`, plus the pre-existing `M .codex/config.toml` and untracked `.brichan*/` (untouched).

## Risks

- A root file literally named `.git` in a main checkout (where `.git` would be a directory) cannot coexist with the directory, so the exemption cannot hide a stray file there.
- `test_a_git_directory_is_not_an_unclassified_root_file` pins the directory case, which `is_file()` already covers; it guards a change from `is_file()` to `exists()`, not the new exemption.

## Claim or decision

The root-file check exempts exactly the root `.git` entry, file or directory, so `make path-check` and `tests.contract.test_repository_paths` pass in a detached worktree; every other unclassified root file is still reported.

## Evidence

- `scripts/check_repository_paths.py` (`GIT_METADATA`, `unclassified_root_files`); `tests/contract/test_repository_paths.py` (three new tests); the Verification section above.

## Uncertainty

- None remains for the fix. The `make check` red is solely WFS-008's own pending coordinator and reviewer artifacts.
