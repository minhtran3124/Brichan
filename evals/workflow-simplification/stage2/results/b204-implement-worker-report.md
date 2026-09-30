# WFS-B-204 worker report

Task: WFS-B-204. Attempt: `attempt-implement-1`. Techstack Snapshot SHA-256:
`0408327094e51e639cd9372d2006db4b2d87e918d108db14c2ae01ea04f8ccc5` (verify
returned `match` before any other work).

## Plan

Plan `WFS-B-204-PLAN-001`, version 1. Written before any code edit.

Approach:

1. Ground every flag in the shipped CLI first. The installed entry points are
   `brichan-herdr-agent-start` (`brichan.orchestration.worker_launch:main`)
   and `brichan-herdr-worker-ledger` (`brichan.orchestration.worker_ledger:main`).
   Their installed parsers define `--task` on launch and `finish` with
   `--worker`, `--launch-id`, repeatable `--evidence`, optional `--task`,
   `--pane`, and `--project`; neither installed parser defines
   `--ledger-file`, so passing it is an argparse usage error (exit `2`).
2. Add a `## Worker ledger` section to the packaged
   `skills/herdr-orchestration/references/commands.md`, written for installed
   mode only: `--task <TASK-ID>` (verbatim, never inferred), the fixed
   `.brichan/ledger/workers.jsonl`, the rejected `--ledger-file`, the
   `ledger: launch_id=<uuid>` stderr line and the warning/no-location lines,
   the installed `finish` command with `--project <absolute-target-project>`,
   its refusals and exit codes, the one-attestation-per-launch rule, and that
   a `finished` record is an attestation, not proof.
3. Make the packaged `SKILL.md` workflow point at it: pass `--task` on launch,
   record the `launch_id`, and attest the finish from evidence only.
4. Tests (contract layer, `tests/contract/test_skill_parity_contract.py`):
   - add the ledger safeguards shared by both trees to `PARITY_MARKERS`, so a
     future drop from either tree fails (`PACKAGED-001` marker parity);
   - add packaged-only checks: the documented installed launch and `finish`
     commands are accepted by the shipped installed parsers (placeholders
     substituted; a parse failure is exit `2`, which the test distinguishes
     from a later refusal), and `--ledger-file` appears only as a rejected
     flag, never inside a packaged command block.

Files: the two packaged skill files above, the parity contract test, and this
report. No manifest change is expected: no resource is added or removed, so
`lifecycle.py`'s resource list and the packaging metadata contract stay as
they are.

Risks:

- The installed `--project` is optional in the parser (it falls back to the Git
  root discovered from the working directory). The objective names
  `--project <absolute-target-project>`; the text will present it as the
  documented form and state the fallback accurately rather than claim it is
  required.
- A legacy (`-- <command>`) installed launch resolves the ledger by an upward
  Git-root walk and may print the no-location note; the packaged skill only
  documents routed launches, so the text states the fixed location for them
  and keeps the note for the no-location case.
- Existing installed projects keep their old skill bytes until reinitialized;
  this is the normal packaged-resource update path (`PACKAGED-002`) and no
  installed state schema changes (`PACKAGED-003`).

## Changes

- `src/brichan/resources/dogfood_v1/skills/herdr-orchestration/references/commands.md`:
  the installed launch block now carries `--task <TASK-ID>`; a new
  `## Worker ledger` section states, for installed mode only: `--task`
  recorded verbatim and never inferred; the fixed
  `.brichan/ledger/workers.jsonl`; `--ledger-file` rejected as an
  unrecognized argument (exit `2`) before any Herdr call; the launch stderr
  lines (`ledger: launch_id=<uuid>`, the ledger-write warning, and the
  no-location note, scoped to legacy `--` launches outside an initialized
  target); the installed `finish` command with `--project`, `--worker`,
  `--launch-id`, repeatable `--evidence`, optional `--task` and `--pane`; its
  refusals (unmatched `launch_id`, already-finished `launch_id`, name without
  `brichan-`, empty or whitespace-only evidence, target that is not a Git root
  or lacks a regular `.brichan/manifest.json`), all exit `1` with nothing
  written; the first-in-file-order tie-break; "absence means unknown"; that a
  `finished` record is a coordinator attestation, not proof; and an exit-code
  table.
- `src/brichan/resources/dogfood_v1/skills/herdr-orchestration/SKILL.md`:
  workflow step 3 adds `--task <TASK-ID>` and the fixed ledger; step 4 records
  the `launch_id`; a new step 7 attests the finish with
  `brichan-herdr-worker-ledger finish --project <absolute-target-project>`
  (an attestation, not proof); the old step 7 becomes step 8.
- `tests/contract/test_skill_parity_contract.py`: seven worker-ledger
  safeguard phrases added to `PARITY_MARKERS`. All already occur in the
  checkout skill, so both trees must keep them (`PACKAGED-001`).
- `tests/contract/test_packaged_ledger_guidance_contract.py` (new): executes
  the packaged skill's own command blocks against the shipped installed entry
  points. The documented `finish` block, with placeholders substituted, records
  a real `finished` attestation (exit `0`) in a temporary installed target. The
  documented launch block, `--task` included, passes the installed launcher's
  parser: it exits `1` at target resolution, not `2` with usage text. No
  packaged command block contains `--ledger-file`, and the text states its
  rejection. The installed-mode rule phrases are present.

No manifest, packaging-metadata, or `lifecycle.py` change: no resource was
added or removed, so the managed resource list is unchanged. No contract
pinned the changed bytes.

## Verification

CLI grounding, taken from the installed entry points with `PYTHONPATH=src`:

- `brichan.orchestration.worker_ledger.main(["finish", "--help"])`: usage
  `finish [-h] --worker WORKER --launch-id LAUNCH_ID --evidence EVIDENCE
  [--task TASK] [--pane PANE] [--project PROJECT]`, exit `0`.
- `brichan.orchestration.worker_launch.main(["--help"])`: options include
  `--task TASK  task identifier recorded verbatim in the worker ledger; never
  inferred when the flag is absent`, and there is no `--ledger-file`.
- The installed launcher with `--ledger-file a.jsonl --dry-run` printed
  `error: unrecognized arguments: --ledger-file a.jsonl` and exited `2`. The
  installed `finish` with `--ledger-file a.jsonl` did the same.
- Refusals and exit codes were read from `_finish_command`, `record_finish`,
  and `resolve_installed_location` in `worker_ledger.py`. The launch
  stderr lines and the legacy no-location path were read from
  `worker_launch.py` (`_resolve_launch`, `_main`) and `legacy_launch_location`.

Tests:

- Focused tests: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
  tests.contract.test_packaged_ledger_guidance_contract
  tests.contract.test_skill_parity_contract` ran 20 tests, OK, on Python 3.10.
  The same command under Python 3.14 was also OK.
- Mutation check (`TEST-003`), with the file restored byte-identical after
  each step (`cmp` confirmed): renaming `--project` to `--target` in the
  finish block failed 2 tests; renaming the launch `--task` to `--task-id`
  failed 1; adding `--ledger-file x.jsonl` to the finish block failed 2.
- `PYTHONDONTWRITEBYTECODE=1 make -k check` on the final bytes:
  - Unit: 1026 tests, OK.
  - Contract: 152 tests, `FAILED (failures=2, skipped=1)`. The only failures
    are the two known worktree-only ones in `tests/contract/test_repository_paths.py`
    (`test_current_path_and_link_contracts_pass` and
    `test_every_non_ephemeral_root_file_is_classified`), both
    `unclassified root files: .git`.
  - `path-check` also fails with the same `unclassified root files: .git`. It
    runs `scripts/check_repository_paths.py`, the script the first failing
    contract test calls, so it has the same worktree-only cause.
  - techstack-eval: 56 tests, OK. metrics: valid. receipts: 46 validated.
    dossiers: 7 validated. memory-check: consistent. readme-check: in sync.
    phase5-preflight: pass. package-check: pass.
  - The `test` recipe aborts after the contract failure, so integration was
    run separately: `PYTHONDONTWRITEBYTECODE=1 make test-integration` ran 222
    tests, OK.
- `git status --short`: `M` on the two packaged skill files and
  `tests/contract/test_skill_parity_contract.py`; `??` on
  `tests/contract/test_packaged_ledger_guidance_contract.py`. This report is
  under the ignored dossier tree and does not appear.
- `git diff --stat` (tracked files only; the new test file is untracked): 3
  files changed. `SKILL.md` +8/-3 lines, `commands.md` +55/-3 lines, the
  parity contract +10 lines.

## Risks and ambiguities

- `--project` is optional in the installed `finish` parser: without it, the Git
  root found from the current directory is used. The skill shows the
  `--project <absolute-target-project>` form the objective names, and states
  the fallback accurately instead of claiming the flag is required.
- argparse accepts unambiguous long-option prefixes, so the drift test would
  not catch a doc that abbreviates a flag, for example `--proj`. A doc
  abbreviation still runs, so this is cosmetic.
- An installed project picks up the new skill bytes only when it is
  reinitialized or updated through the normal packaged-resource path
  (`PACKAGED-002`). Until then, its managed and exported copies keep the old
  text. No installed state schema changed (`PACKAGED-003`).
- The launch drift test checks argument parsing only. It cannot start a
  worker without Herdr. The end-to-end ledger write on launch is already
  covered by `tests/integration/test_worker_routing_cli.py`.
- Pre-existing and worktree-only: the two `test_repository_paths` failures and
  the matching `path-check` failure (`.git` is a file in a detached worktree).
  They are reported and were not fixed.
