# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `WFS-A-204`
- Task level: `1`
- Artifact: `plan`
- Artifact version: `4`
- Origin: `packet:WFS-A-204-PLAN@2026-09-25#attempt-plan-4`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `cbe8f2f3-df53-44bd-85b0-f419269bce8c`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `WFS-A-204-PLAN-001`
- Plan status: `draft`

## Version note

Version 4 (version 3 preserved at `versions/v3/plan.md`) closes both findings
of `plan-review.md` version 3 (verdict `CHANGES REQUIRED`, two low findings,
neither touching the drafted packaged text, the selected option, the marker
set, the placement, or the completion gate). The findings-closure table below
maps each version 3 finding to its resolution; the version 2 findings were
closed by version 3 and every closure was re-verified by execution in
plan-review version 3 ("no closure claim is overstated"), so that table is
preserved at `versions/v3/plan.md` and not repeated here, as the version 1
table is at `versions/v2/plan.md`. The implementation steps, the traceability
table, and the risks are unchanged in substance; what changes besides the
metadata and this note: the closure table, the Techstack snapshot pointer for
this attempt, the dossier-validator baseline (re-measured in this session),
the step 6 note on the plan-review version-mismatch diagnostic, and the
Evidence and Uncertainty sections (plan-review v3 measured the full gate on
both interpreters, superseding the earlier specified-not-measured caveat).

## Findings closure (plan-review version 3)

| Finding | Resolution in version 4 |
| --- | --- |
| `L1-v3` (low): `R5` claimed to enumerate every `finish` refusal the shipped CLI enforces while omitting four it does enforce — the `no ledger for this target` refusal `R4` documents one row above, plus three `find_git_root` path-resolution usage refusals, all reproduced by the review at exit `1` | Closed, taking the first of the review's two offered corrections (narrow the quantifier), which the review itself calls the smaller change that "loses nothing an installed coordinator needs". `R5` now scopes its four-item list to the refusals that bound attestation integrity, states explicitly that neither the list nor the packaged text claims exhaustiveness, and records the omitted refusals: the `R4` resolution refusal stays documented where it is, and the three `find_git_root` refusals (`target project is not a directory`, `target project is not a Git repository root`, `cannot find a Git repository from`) are recorded as enforced but deliberately undocumented. A matching wording note in `design.md` forbids adding them to the packaged text, which would exceed the checkout content this task mirrors and add prose no marker pins. The drafted packaged text is unchanged — the review confirmed it never claims exhaustiveness, so nothing false was ever going to ship. Ground: `src/brichan/project.py:9,35-51` and `worker_ledger.py:726-730` re-read in this session. |
| `L2-v3` (low): `options.md` version 3's version note claimed "the metadata above is the only change" while its actual diff from version 2 also rewrote two Evidence bullets | Closed. The `options.md` version 4 note corrects the record with the review's suggested substance: version 3's diff from version 2 was the metadata plus two rewritten Evidence bullets. Ground: `diff versions/v2/options.md versions/v3/options.md` re-run in this session, showing exactly the metadata block, the version note, and the two Evidence bullets. |
| v3 test gap 1: nothing guards `R5`'s refusal list against the `L1-v3` gap, and nothing can cheaply | Per the review, the fix is the requirement correction, not an assertion; done in `R5` and recorded as a known limitation in `design.md` ("Parity-contract extension"). |
| v3 test gaps 2-4 (tree-text markers; coarse placement pin; no installed-vs-checkout exit-table test) | Known limitations carried unchanged; the review verified the placement pin catches reordering and deletion by mutation and accepts all three with no action. |
| v3 residual risks (legacy launches undocumented; manifest-hash churn; worktree-specific expected-red list; plan status `draft` needing coordinator acceptance; WLG-001 provenance) | All carried forward unchanged, as the review accepts: `design.md` records the first two with reasons; the expected-red baseline is re-measured below rather than inherited; plan acceptance (`draft` → `accepted`) is a coordinator action after this version's review, not a plan defect; `requirements.md` Uncertainty records the provenance caveat. |

## Techstack scope

- Snapshot pointer: `projects/brida-workflow-simplification/handoffs/WFS-A-204/snapshots/attempt-plan-4-a5712ea81cd890f7c3fc53f6577b8790d144071df0687fa743b3563365c41e14.snapshot.json`
- Snapshot SHA-256: `a5712ea81cd890f7c3fc53f6577b8790d144071df0687fa743b3563365c41e14`
- Verified `status: match` on 2026-09-25 before any version 4 work; all eight
  required selected rule files were read in this session.
- Planning discovered **no path outside the declared scope paths**. Both files
  the implementation touches fall inside them:
  `src/brichan/resources/dogfood_v1/skills/herdr-orchestration/references/commands.md`
  under `src/brichan/resources/dogfood_v1`, and
  `tests/contract/test_skill_parity_contract.py` under `tests/contract`. No new
  Context ID, chain, conflict, or exception need was discovered.

## Implementation steps

1. **Re-verify the Techstack snapshot and reread the selected rule files.**
   Run the packet's verify command from the worktree root and require `match`;
   read the eight selected rule files. Acknowledge in the final response.
2. **Edit the packaged command reference.** In
   `src/brichan/resources/dogfood_v1/skills/herdr-orchestration/references/commands.md`,
   insert the drafted launch paragraph directly after the paragraph ending
   "Close only a recorded Brichan-owned pane with `herdr pane close
   <pane-id>`.", and insert the drafted `## Worker ledger` section immediately
   before `## Recover a swallowed Enter` — after the last "Safeguards that
   apply to every observation" bullet. Do not insert anything between the
   launch guidance and the observation block. Transcribe the drafted text from
   `design.md` exactly and keep its wording notes: prose `--task` (no change
   to the launch example block), installed exit-`2` row says "Invalid
   invocation" only, refusal condition is the regular
   `.brichan/manifest.json`, never "healthy managed state", no legacy
   no-location note, no `find_git_root` path-resolution refusals, no checkout
   ledger path anywhere.
3. **Extend the parity contract.** In
   `tests/contract/test_skill_parity_contract.py`, append the thirteen
   worker-ledger markers from `design.md` to `PARITY_MARKERS` under a comment
   naming this task, and add
   `test_the_packaged_tree_never_offers_the_checkout_ledger_flag_as_usable`
   with the four assertions specified in `design.md` ("Parity-contract
   extension"): the rejection sentence, the excluded checkout path shape, the
   exactly-once `--ledger-file` occurrence count, and the per-file placement
   pin opened by its `assertIn` legibility guard. Do not modify or remove any
   existing marker, label, or test.
4. **Verify command fidelity against the shipped CLI.** With
   `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src`, capture `--help` for the
   installed launcher (`brichan.orchestration.worker_launch:main`) and for
   `brichan-herdr-worker-ledger finish`
   (`brichan.orchestration.worker_ledger:main`), and reproduce the installed
   `--ledger-file` rejection (expect "unrecognized arguments", exit `2`).
   Check every command name, flag, refusal string, and exit code in the new
   text against that output or the parser source; record the outputs as
   acceptance evidence.
5. **Run the focused contracts first**, per the testing discipline:
   `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
   tests.contract.test_skill_parity_contract
   tests.contract.test_dogfood_policy_contract
   tests.contract.test_packaging_metadata -v` and require zero failures.
6. **Run the completion gate**: the coordinator-ratified target list
   (`client-follow-up-questions.md` version 2, ratified 2026-09-25) as
   corrected by plan-review version 2 findings `L2-v2` and `L3-v2`.
   On the 3.10 shell interpreter: `make test-unit`, `make test-contract`,
   `make test-integration`, then `make techstack-eval`, `metrics`, `receipts`,
   `dossiers`, `memory-check`, `path-check`, `readme-check`,
   `phase5-preflight`, `package-check` individually, plus the two `make check`
   steps the target list alone omits: `sh -n bin/brichan` and
   `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
   metrics/test_validate_metrics.py`. Then again under
   `PYTHON=/opt/homebrew/bin/python3.14` for every make target that honors
   `PYTHON=`, with two direct invocations replacing the ones that do not:
   `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 -m unittest
   evals.techstack_context_v1.test_cases` (the `techstack-eval` recipe
   hardcodes `python3`) and `PYTHONDONTWRITEBYTECODE=1
   /opt/homebrew/bin/python3.14 -m unittest metrics/test_validate_metrics.py`.
   `sh -n bin/brichan` is interpreter-independent and runs once. Plan-review
   version 3 measured this whole gate on both interpreters over the drafted
   change and found the expected-red list identical on both.
   Expected red, not to be fixed:
   - The two `tests/contract/test_repository_paths.py` failures and the
     `make path-check` target, all one worktree-only cause: this detached
     worktree's `.git` is a file, so the scanner reports
     `unclassified root files: .git`. Report; do not fix.
   - While this dossier is in flight: `make dossiers` (make exit `2` — GNU
     make recipe failure — over script exit `1`) and
     `tests.integration.test_task_dossier_workflow.test_repository_checkout_validates_clean`
     (1 failure). Attribute each validator diagnostic to the artifact whose
     path precedes the first colon: every diagnostic must be owned by a
     pending coordinator- or reviewer-owned WFS-A-204 artifact (`index.md`,
     `code-review.md`, `pr-desc.md`, `plan-review.md`, or the missing
     `receipt.md` reported via `index.md`). An `index.md`-owned comparison row
     whose *text* mentions a planner artifact (for example "index says
     '<phase state>' but requirements.md says 'passed'") is expected and is
     not a planner-artifact diagnostic. The summary's "across N dossier(s)"
     figure is the count of dossiers scanned, not of dossiers holding issues.
     Baseline measured 2026-09-25 in this session: 38 issues before the
     version 4 planner artifacts were written, owned by WFS-A-204 `index.md`
     (28: 5 unfilled metadata placeholders, 4 unfilled task-identity fields
     including the missing-receipt diagnostic, 19 artifact-status comparison
     rows), `code-review.md` (5), and `pr-desc.md` (5); 39 after, the one
     addition owned by `plan-review.md` ("review must reference the exact
     accepted plan version '4', found '3'"), which clears when the reviewer
     reviews this version. The count moves as those artifacts fill in; a
     diagnostic *owned by* a planner artifact or by another dossier is a new
     defect to diagnose.
   - Everything else passes on both interpreters, including the extended
     skill-parity contract over the new text.
   Any failure outside this expected-red list is the implementation's to
   diagnose before any code or tests change.
7. **Collect acceptance evidence and hand off.** The diff of the two files,
   the captured `--help` and rejection outputs, the focused-contract and
   completion-gate results on both interpreters, and a statement that no file
   outside the two named ones changed (`git status --short`). Leave everything
   uncommitted.

## Acceptance-criteria traceability

| Packet acceptance criterion | Requirements | Steps |
| --- | --- | --- |
| Packaged skill states `--task` verbatim-recording, the fixed installed ledger, the `--ledger-file` rejection, and the full `finish` attestation guidance including its refusals | `R1`-`R6` | 2 |
| Every command and flag matches the shipped CLI, evidenced by `--help` or parser source — including stating no refusal the CLI does not enforce and claiming no exhaustiveness it does not have | `R4`, `R5`, `R7` | 2, 4 |
| No checkout-only flag presented as usable in installed-mode text | `R8` | 2, 3 |
| New section does not demote existing packaged safeguards (plan-review M1) | `R13` | 2, 3 |
| Packaging, manifest, and skill-parity contracts stay green, updated only where a contract legitimately pins the changed bytes | `R9`-`R11` | 3, 5 |
| Completion gate passes apart from the expected-red list — the ratified gate as made `make check`-equivalent by the `L2-v2`/`L3-v2` corrections | `R12` | 6 |
| Out-of-scope paths reported prominently | — | none found; see "Techstack scope" |

## Risks and boundaries

- The packaged edit changes the resource hash `init` embeds in new manifests.
  Release-process handled (see `design.md`, "Contract and manifest
  consequences"); no action in this task.
- The implementer must not add a packaged file, edit the packaged `SKILL.md`
  or any checkout skill file, or reword existing packaged safeguards — the
  negative parity assertions and `PACKAGED-001`..`PACKAGED-003` bound the
  change to the drafted insertion, and the placement assertion bounds where it
  lands.
- This is a documentation-plus-contract change with no executable-behavior
  change, so no unit or integration test changes are required; the regression
  guard demanded by `GENERAL-004`'s intent is the extended parity contract.
- The expected-red list in step 6 is specific to this detached worktree and
  this in-flight dossier. A later session on another checkout must re-measure
  it rather than inherit it, as plan-review v2 and v3 both warn; on the main
  checkout with a closed dossier, everything must be green.

## Claim or decision

Plan `WFS-A-204-PLAN-001` version 4 (draft): implement WFS-A-204 as the
two-file change specified in `design.md` version 4, in the seven steps above,
verified by CLI-fidelity capture, the extended skill-parity contract (markers,
occurrence count, and placement pin with its legibility guard), and the
`make check`-equivalent completion gate on both interpreters. Both plan-review
version 3 findings are closed as tabled above; the version 1 and 2 closures
stand as re-verified by execution in plan-review version 3, which also ran the
real parity suite over the drafted text and measured the full gate on both
interpreters, and states it would accept the drafted text, the selected
option, the marker set, the placement, and the gate as they stand. An
implementer who reads `requirements.md`, `design.md`, and this plan needs no
further research: the inserted text is fully drafted, its placement is exact,
and every literal in it is source-verified and claims only behavior the
shipped CLI enforces.

## Evidence

- `projects/brida-workflow-simplification/handoffs/WFS-A-204/plan-review.md` version 3 (verdict `CHANGES REQUIRED`; findings `L1-v3`, `L2-v3`; test gaps 1-4; residual risks) is the change driver for this version; each finding's resolution is tabled above and cross-referenced to the revised artifact sections, and each underlying fact was independently re-verified in this session before revising: `src/brichan/project.py:9,35-51` (`ProjectError` subclasses `ValueError`; the three path-resolution refusal messages) with `worker_ledger.py:726-730` (the installed `finish` arm returns exit `1` for them), and `diff versions/v2/options.md versions/v3/options.md` (the version 3 diff was metadata plus two Evidence bullets).
- `projects/brida-workflow-simplification/handoffs/WFS-A-204/client-follow-up-questions.md` version 2 records the coordinator-ratified completion gate that step 6 states, as corrected by the plan-review v2 required changes under the packet's instruction to close every finding; the coordinator-owned artifact itself is unedited.
- The Techstack snapshot verify command returned `status: match` with digest `a5712ea81cd890f7c3fc53f6577b8790d144071df0687fa743b3563365c41e14` on 2026-09-25 in this session, and the resolution's scope paths contain both files this plan touches.
- Measured in this session on 2026-09-25: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py projects` exits `1` with 38 issues before the version 4 planner artifacts were written (owned `index.md` 28 / `code-review.md` 5 / `pr-desc.md` 5, matching plan-review v3's post-review measurement) and 39 after, the one addition owned by `plan-review.md` (the version-mismatch row that clears on review of this version); `make dossiers` exits `2`; the packaged `commands.md` has headings only at lines 1 and 65; `worker_launch.py:422-442` and `worker_ledger.py:670-692` carry the parser facts the steps transcribe; the packaged tree contains zero occurrences of `--ledger-file` today.

## Uncertainty

- The dossier-validator issue count (38 before / 39 after this version's artifacts were written, measured 2026-09-25 in this session) will move as the coordinator and reviewer fill their artifacts; the ownership rule in step 6, not the count, is the acceptance test. The suite-level baseline (two `test_repository_paths` failures, one `test_task_dossier_workflow` failure, `path-check` red) was measured by plan-review v3 on both interpreters and re-checked in this session; if the implementation observes any different failing test name or message outside the expected-red list, that is a new finding to diagnose, not to absorb into this plan.
- Step 6's two direct 3.14 invocations, previously specified from the recipe text alone, were measured green by plan-review version 3 (`evals.techstack_context_v1.test_cases`: 56 tests, `OK`; `metrics/test_validate_metrics.py`: 10 tests, `OK`, both under `/opt/homebrew/bin/python3.14`), so that earlier caveat is resolved; this session did not repeat the 3.14 runs.
- No other unresolved uncertainty remains; no packet ambiguity rose to an escalation-worthy open question.
