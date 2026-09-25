# Implementation

Implementation evidence for accepted plan `WFS-A-204-PLAN-001` version 4.

## Metadata

- Task ID: `WFS-A-204`
- Plan ID: `WFS-A-204-PLAN-001`
- Plan version: `4` (status `accepted`)
- Attempt ID: `attempt-implement-1`
- Owner: `implementer`
- Date: `2026-09-25`
- Effective model: `claude-opus-5-5`
- Techstack snapshot SHA-256: `10c26d0c5c1959d970e793ed8bb3b6c4f9e72a809d1c01dca98352393393dd86` (verify returned `status: match`, `differences: []`, before any other work)

## Changed files

Exactly the two files the plan authorizes (`git diff --stat`: 2 files, 90 insertions, 0 deletions):

1. `src/brichan/resources/dogfood_v1/skills/herdr-orchestration/references/commands.md` (+49)
   - Launch paragraph inserted directly after the paragraph ending "Close only a recorded Brichan-owned pane with `herdr pane close <pane-id>`." and before "Observe workers through the read-only helper:".
   - `## Worker ledger` section inserted immediately before `## Recover a swallowed Enter`, after the last "Safeguards that apply to every observation" bullet. Existing packaged text is byte-unchanged.
2. `tests/contract/test_skill_parity_contract.py` (+41)
   - Thirteen worker-ledger markers appended to `PARITY_MARKERS` under a comment naming WFS-A-204. No existing marker, label, or test was modified.
   - New test `test_the_packaged_tree_never_offers_the_checkout_ledger_flag_as_usable` with the four specified assertions: the rejection sentence (`assertIn`), the excluded checkout path shape (`assertNotIn`), the exactly-once `--ledger-file` count (`assertEqual(1, ...)`), and the per-file placement pin (`assertIn("## Worker ledger", text)` legibility guard, then two `assertLess` calls for safeguards < ledger < recovery).

Also written: this file. No other path changed.

## Plan steps

| Step | How it was met |
| --- | --- |
| 1. Re-verify snapshot, reread rules | Verify command run first from the worktree root via `bin/brichan`: `status: match`, observed digest equal to expected. All eight selected rule files read, plus `docs/policy/operating-principles.md`. |
| 2. Edit packaged command reference | Both `design.md` version 4 blockquotes transcribed. A script extracted each blockquote from `design.md` and checked it is a substring of the edited file: both `True` (342 and 2004 characters). All wording notes kept: `--task` in prose only (launch example block unchanged); exit-`2` row says "Invalid invocation" only; refusal condition is the regular `.brichan/manifest.json`; no "healthy managed state" on `finish`; no legacy no-location note; no `find_git_root` refusals; no checkout ledger path. |
| 3. Extend parity contract | Markers and test added exactly as specified in `design.md` "Parity-contract extension". |
| 4. CLI fidelity | See "Command fidelity evidence" below. Every command, flag, refusal, and exit code in the new text matches. |
| 5. Focused contracts | `test_skill_parity_contract`, `test_dogfood_policy_contract`, `test_packaging_metadata`: 43 tests `OK` on 3.10 and on 3.14. |
| 6. Completion gate | See "Completion gate" below; only the listed expected-red items are red, identically on both interpreters. |
| 7. Evidence and handoff | This file; changes left uncommitted. |

## Command fidelity evidence

Captured with `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3` (3.10) calling the `pyproject.toml` entry points `brichan.orchestration.worker_launch:main` (`brichan-herdr-agent-start`) and `brichan.orchestration.worker_ledger:main` (`brichan-herdr-worker-ledger`).

- `brichan-herdr-agent-start --help`, exit `0`: options are `--anchor-pane`, `--cwd`, `--env`, `--route`, `--runtime`, `--model`, `--effort`, `--task`, `--dry-run`, `--json`; no `--ledger-file`. `--task` help: "task identifier recorded verbatim in the worker ledger; never inferred when the flag is absent".
- `brichan-herdr-agent-start brichan-x --cwd <dir> --route implement --ledger-file x.jsonl`: "error: unrecognized arguments: --ledger-file x.jsonl", exit `2` (argparse, before any Herdr call).
- `brichan-herdr-worker-ledger finish --help`, exit `0`: `--worker` (required), `--launch-id` (required), `--evidence` (required, repeatable), `--task`, `--pane`, `--project`; no `--ledger-file`.
- `finish ... --ledger-file x`: "unrecognized arguments", exit `2`.
- Refusals reproduced against a scratch Git repository, each exit `1`:
  - no `.brichan/manifest.json`: "no ledger for this target: <path>";
  - with a regular manifest, unknown launch id: "no launched record for launch_id u";
  - worker `other`: "worker name must begin with brichan-: other";
  - evidence `'  '`: "every --evidence item must be non-empty".
  After all four, the scratch target held no `.brichan/ledger` directory: nothing written.
- Parser source for literals not reproduced by execution: `worker_ledger.py:76` and `139-149` (fixed path `.brichan/ledger/workers.jsonl`), `:636-638` (already-finished refusal "launch_id ... already has a finished record"), `:23` and `:450` (first `finished` record in file order wins); `worker_launch.py:698` (`ledger: launch_id=<uuid>` on stderr) and `:701` ("warning: worker started but ledger write failed: ").

## Mutation check of the new test

Run against the edited packaged file and restored from a saved copy afterwards (`cmp` identical, suite `OK`):

- section moved above the safeguards: `FAILED (failures=1)`;
- an affirmative second `--ledger-file` mention appended: `FAILED (failures=1)`;
- section deleted: `FAILED (failures=2)` (markers plus the legible `assertIn`, no `ValueError`).

## Completion gate

Ratified list from `client-follow-up-questions.md` version 2, plus `sh -n bin/brichan` and `metrics/test_validate_metrics.py` per plan step 6. All runs used `PYTHONDONTWRITEBYTECODE=1`.

| Target | 3.10 (shell `python3`) | 3.14 (`PYTHON=/opt/homebrew/bin/python3.14`, 3.14.6) |
| --- | --- | --- |
| `make test-unit` | exit 0 | exit 0 |
| `make test-contract` | exit 2: 149 tests, 2 failures (expected), 1 skipped | same |
| `make test-integration` | exit 2: 222 tests, 1 failure (expected) | same |
| `make techstack-eval` / direct `evals.techstack_context_v1.test_cases` | exit 0 | 56 tests `OK` (direct invocation) |
| `make metrics` | exit 0 | exit 0 |
| `make receipts` | exit 0 | exit 0 |
| `make dossiers` | exit 2 (expected) | exit 2 (expected) |
| `make memory-check` | exit 0 | exit 0 |
| `make path-check` | exit 2 (expected) | exit 2 (expected) |
| `make readme-check` | exit 0 | exit 0 |
| `make phase5-preflight` | exit 0 | exit 0 |
| `make package-check` | exit 0 | exit 0 |
| `metrics/test_validate_metrics.py` | `OK` | `OK` |
| `sh -n bin/brichan` | exit 0 (interpreter-independent) | — |

Expected-red items, diagnosed:

- `tests.contract.test_repository_paths`: `test_current_path_and_link_contracts_pass` ("unclassified root files: .git") and `test_every_non_ephemeral_root_file_is_classified` (extra item `'.git'`), plus `make path-check` ("unclassified root files: .git"). One cause: this detached worktree's `.git` is a file. Pre-existing, worktree-only; not fixed.
- `make dossiers` (make exit `2` over script exit `1`) and `tests.integration.test_task_dossier_workflow.test_repository_checkout_validates_clean`: "40 issue(s) across 8 dossier(s)", every diagnostic owned by a pending coordinator- or reviewer-owned WFS-A-204 artifact: `index.md` 30, `code-review.md` 5, `pr-desc.md` 5. No diagnostic is owned by a planner artifact, by this file, or by another dossier. The `plan-review.md` version-mismatch diagnostic from the plan's baseline is gone. The count differs from the plan's 38/39 baseline only in `index.md`-owned rows, which the plan says move as artifacts fill in.

No other failure was observed on either interpreter.

## Deviations

None. Both files match `design.md` version 4 as specified. No executable behavior changed, so no unit or integration test was added (plan "Risks and boundaries").

## Risks

- Editing an immutable packaged resource changes the hash `init` writes into new manifests. This is handled by the release process (`design.md` "Contract and manifest consequences"); no action was taken in this task.
- Known limitations carried from the plan: markers are asserted on concatenated tree text; no assertion pins the documented refusal set to the code's refusal set; the three `find_git_root` refusals are intentionally undocumented.
- The expected-red list and the dossier issue count are specific to this detached worktree and in-flight dossier. On the main checkout with a closed dossier, all gates must be green.
