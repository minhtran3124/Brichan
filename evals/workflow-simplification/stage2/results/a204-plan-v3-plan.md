# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `WFS-A-204`
- Task level: `1`
- Artifact: `plan`
- Artifact version: `3`
- Origin: `packet:WFS-A-204-PLAN@2026-09-25#attempt-plan-3`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `c106f802-fc5e-4e34-b6b4-c2d1f650fede`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `WFS-A-204-PLAN-001`
- Plan status: `draft`

## Version note

Version 3 (version 2 preserved at `versions/v2/plan.md`) closes every finding
of `plan-review.md` version 2 (verdict `CHANGES REQUIRED`, four low findings)
and adopts its one optional test-gap suggestion. The findings-closure table
below maps each version 2 finding to its resolution; the version 1 findings
were closed by version 2 and every closure was re-verified row by row by
plan-review version 2 ("No closure claim in the table is overstated"), so
that table is preserved at `versions/v2/plan.md` and not repeated here. The
selected option, the placement, the thirteen parity markers, and the drafted
section as a whole are unchanged — the review confirmed no finding touches
them. What changes: one sentence of the drafted packaged text and `R4`
(`L1-v2`), the completion gate in step 6 and `R12` (`L2-v2`, `L3-v2`), the
placement pin's legibility (`v2` test gap 3), and this plan's dossier
baseline, now measured once and recorded consistently (`L4-v2`).

## Findings closure (plan-review version 2)

| Finding | Resolution in version 3 |
| --- | --- |
| `L1-v2` (low): drafted packaged text states a `finish` refusal the shipped CLI does not enforce ("must hold healthy managed state") | Closed. The `--project` paragraph in `design.md` and `R4` now state the condition the code enforces — the target must be an initialized Brichan project holding a regular `.brichan/manifest.json`, refusal `no ledger for this target`, exit `1` — and state explicitly that `finish` does not verify managed-state health, with the pre-attestation health check recorded as a coordinator responsibility, not a refusal. A wording note in `design.md` forbids reintroducing the launch-path guard ("healthy managed state") into the `finish` text, and the review's test gap 1 (no contract assertion can cheaply pin this condition) is recorded there as a known limitation. Ground: `worker_ledger.py:195-220` re-read this session. |
| `L2-v2` (low): the enumerated completion gate omits two steps of `make check` (`sh -n bin/brichan`; the `metrics/test_validate_metrics.py` unittest) while claiming to satisfy the `make check` criterion | Closed, taking the first of the review's two offered corrections: step 6 and `R12` add both steps explicitly, so the gate is the ratified target list plus exactly the two steps that make it equivalent to `make check`. Both were measured green by the review (exit `0`; 10 tests, `OK`). The ratified list itself (`client-follow-up-questions.md` version 2) is coordinator-owned and is not edited; the supplements are applied under the coordinator's packet instruction to close every finding, and the traceability table now maps the criterion to the amended gate. |
| `L3-v2` (low): `techstack-eval` cannot be moved to Python 3.14 via `PYTHON=` because its recipe hardcodes `python3` | Closed. Step 6 and `R12` invoke the eval directly for the second interpreter — `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 -m unittest evals.techstack_context_v1.test_cases` — exactly as the review requires and as `techstacks/python/tests.md` (Verification) already states. Ground: `Makefile:39-40` re-read this session. |
| `L4-v2` (low): version 2 recorded both 39 and 38 for the same dossier-validator baseline | Closed. Version 3 records one measurement, taken after the version 3 artifacts were written, with its ownership distribution, in step 6 and Evidence below; the self-contradicting figures live only in the archived `versions/v2/plan.md`. The count is expected to move as coordinator and reviewer artifacts fill in — the ownership rule, not the count, remains the acceptance test. |
| v2 test gap 1: nothing guards the `L1-v2` sentence | Per the review, the fix is the sentence correction, not an assertion; recorded as a known limitation in `design.md` ("Parity-contract extension"). |
| v2 test gap 2: markers asserted on concatenated tree text | Known limitation, carried unchanged in `design.md`; acceptable because `IMMUTABLE_PATHS` fixes the packaged file set. No action, per the review. |
| v2 test gap 3 (optional): placement pin errors with `ValueError` instead of failing legibly if the section is deleted | Adopted. `design.md` assertion 4 now opens with `assertIn("## Worker ledger", text)` before the two `assertLess` calls. |
| v2 test gap 4: no test distinguishes the installed exit-`2` row from the checkout one | Covered indirectly by the exactly-once occurrence count, per the review. No action. |
| v2 residual risks (legacy launches undocumented; manifest-hash churn; worktree-specific expected-red list; WLG-001 provenance) | All carried forward unchanged, as the review accepts: `design.md` records the first two with reasons, step 6's ownership rule mitigates the third for the dossier half and this plan repeats the review's warning that a later session must re-measure rather than inherit the expected-red list, and `requirements.md` Uncertainty records the fourth. |

## Techstack scope

- Snapshot pointer: `projects/brida-workflow-simplification/handoffs/WFS-A-204/snapshots/attempt-plan-3-2076d6d81e41514444deed218be3552e3d69398740c2584ad308a5994a528d7e.snapshot.json`
- Snapshot SHA-256: `2076d6d81e41514444deed218be3552e3d69398740c2584ad308a5994a528d7e`
- Verified `status: match` on 2026-09-25 before any version 3 work; all eight
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
   launch guidance and the observation block. Transcribe the version 3 drafted
   text from `design.md` exactly — its `--project` paragraph differs from the
   version 2 draft (finding `L1-v2`) — and keep the wording notes in
   `design.md`: prose `--task` (no change to the launch example block),
   installed exit-`2` row says "Invalid invocation" only, refusal condition is
   the regular `.brichan/manifest.json`, never "healthy managed state", no
   legacy no-location note, no checkout ledger path anywhere.
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
   `sh -n bin/brichan` is interpreter-independent and runs once.
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
     Baseline measured 2026-09-25 after the version 3 planner artifacts were
     written: 39 issues, owned by WFS-A-204 `index.md` (28: 5 unfilled
     metadata placeholders, 4 unfilled task-identity fields including the
     missing-receipt diagnostic, 19 artifact-status comparison rows),
     `code-review.md` (5), `pr-desc.md` (5), and `plan-review.md` (1: the
     review references plan version 2 while the live plan is version 3, which
     clears when the reviewer reviews this version). The count moves as those
     artifacts fill in; a diagnostic *owned by* a planner artifact or by
     another dossier is a new defect to diagnose.
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
| Every command and flag matches the shipped CLI, evidenced by `--help` or parser source — including stating no refusal the CLI does not enforce | `R4`, `R7` | 2, 4 |
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
  it rather than inherit it, as plan-review v2 warns; on the main checkout
  with a closed dossier, everything must be green.

## Claim or decision

Plan `WFS-A-204-PLAN-001` version 3 (draft): implement WFS-A-204 as the
two-file change specified in `design.md` version 3, in the seven steps above,
verified by CLI-fidelity capture, the extended skill-parity contract (markers,
occurrence count, and placement pin with its legibility guard), and the
`make check`-equivalent completion gate on both interpreters. All plan-review
version 2 findings are closed as tabled above, and the version 1 closures
stand as re-verified by that review. An implementer who reads
`requirements.md`, `design.md`, and this plan needs no further research: the
inserted text is fully drafted, its placement is exact, and every literal in
it is source-verified and claims only behavior the shipped CLI enforces.

## Evidence

- `projects/brida-workflow-simplification/handoffs/WFS-A-204/plan-review.md` version 2 (verdict `CHANGES REQUIRED`; findings `L1-v2`-`L4-v2`; test gaps 1-4; residual risks) is the change driver for this version; each finding's resolution is tabled above and cross-referenced to the revised artifact sections, and each underlying fact was independently re-verified in this session before revising: `worker_ledger.py:195-220` (the `finish` guard is `_state_manifest_is_regular`, an `os.lstat` plus `stat.S_ISREG`; no `inspect_project` call), `Makefile:24-28` and `:75-76` (`make check` = `test`, which first runs the `metrics/test_validate_metrics.py` unittest, plus nine targets plus `sh -n bin/brichan`), and `Makefile:39-40` (`techstack-eval` hardcodes `python3`).
- `projects/brida-workflow-simplification/handoffs/WFS-A-204/client-follow-up-questions.md` version 2 records the coordinator-ratified completion gate that step 6 states, as corrected by the review's required changes under the packet's instruction to close every finding; the coordinator-owned artifact itself is unedited.
- The Techstack snapshot verify command returned `status: match` with digest `2076d6d81e41514444deed218be3552e3d69398740c2584ad308a5994a528d7e` on 2026-09-25 in this session, and the resolution's scope paths contain both files this plan touches.
- Measured in this session on 2026-09-25 after the version 3 planner artifacts were written: `scripts/validate_task_dossiers.py projects` exits `1` with 39 issues, every one owned (path before the first colon) by WFS-A-204 `index.md` (28), `code-review.md` (5), `pr-desc.md` (5), or `plan-review.md` (1), and none by a planner artifact, while `make dossiers` exits `2`; the packaged `commands.md` has headings only at lines 1 and 65; `worker_launch.py:422-442` and `worker_ledger.py:670-742` carry the parser facts the steps transcribe; the packaged tree contains zero occurrences of `--ledger-file` today.

## Uncertainty

- The dossier-validator issue count (39 on 2026-09-25, measured after the version 3 planner artifacts were written) will move as the coordinator and reviewer fill their artifacts — it briefly read 38 while plan and plan-review versions agreed, and returns to 39 while this version awaits review; the ownership rule in step 6, not the count, is the acceptance test. The suite-level baseline (two `test_repository_paths` failures, one `test_task_dossier_workflow` failure, `path-check` red) was re-measured in this session and matches plan-review v2's measurement; if the implementation observes any different failing test name or message outside the expected-red list, that is a new finding to diagnose, not to absorb into this plan.
- Step 6's two direct 3.14 invocations were specified from the recipe text and the selected rule (`techstacks/python/tests.md`, Verification), not from a 3.14 execution in this session, matching the review's own recorded uncertainty; a later 3.14 measurement that contradicts them wins and must be recorded.
- No other unresolved uncertainty remains; no packet ambiguity rose to an escalation-worthy open question.
