# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `WFS-A-204`
- Task level: `1`
- Artifact: `plan`
- Artifact version: `2`
- Origin: `packet:WFS-A-204-PLAN@2026-09-25#attempt-plan-2`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `6b5e7d82-9bdc-4a2e-824c-fb3b11060427`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `WFS-A-204-PLAN-001`
- Plan status: `draft`

## Version note

Version 2 (version 1 preserved at `versions/v1/plan.md`) closes every finding
of `plan-review.md` version 1 (verdict `CHANGES REQUIRED`) and adopts the
coordinator-ratified completion gate from `client-follow-up-questions.md`
version 2. The findings-closure table below maps each finding to its
resolution. The selected option, the drafted packaged text, and the marker set
are unchanged; the review verified them and blocked acceptance only on
placement and baseline corrections.

## Findings closure

| Finding | Resolution in version 2 |
| --- | --- |
| M1 (medium): ordered placement nests the monitoring safeguards under `## Worker ledger` | Closed. The section now goes immediately before `## Recover a swallowed Enter`, after the safeguards block; the launch paragraph stays after the launch guidance. Variant choice and rationale recorded in `options.md` ("Sub-decision — place `## Worker ledger` before `## Recover a swallowed Enter`") and `design.md` ("Why this placement"). The placement is pinned by a new contract assertion (`R13`), so the fix is durable. |
| L1 (low): step 6's dossier-baseline rule misfires against `index.md` comparison rows that mention planner artifacts | Closed. The rule is restated in ownership terms: a diagnostic is owned by the artifact path before its first colon, and every diagnostic must be owned by a pending coordinator- or reviewer-owned WFS-A-204 artifact; text mentioning planner artifacts inside an `index.md`-owned row is expected. The "across N dossier(s)" summary figure is noted as the scanned count, not a failing count. See step 6 and `R12`. |
| L2 (low): recorded `make dossiers` exit code wrong (`1` instead of `2`) | Closed. Step 6 and `R12` record `make dossiers` exit `2` (GNU make recipe failure) and script exit `1`. Re-measured in this planning session on 2026-09-25: script exit `1`, `make dossiers` exit `2`. |
| Test gap 1: `R8` guard accepts affirmative phrasings other than "add" | Closed. The third assertion becomes an exactly-once occurrence count of `--ledger-file` over the packaged tree text (`design.md`, assertion 3), which no second, affirmative mention can pass. `R8` restated accordingly. |
| Test gap 2: version 1's third assertion is near-tautological | Closed. That assertion is replaced by the occurrence count above. |
| Test gap 3 (optional): nothing pins the new section's placement | Adopted. A per-file placement assertion (`design.md`, assertion 4) pins safeguards < `## Worker ledger` < `## Recover a swallowed Enter` in the packaged `commands.md`, making the M1 fix durable (`R13`). |
| Test gap 4: markers asserted on concatenated tree text | Recorded as a known limitation in `design.md`, as the review recommends; acceptable because `IMMUTABLE_PATHS` fixes the packaged file set. No action. |
| Residual risk: widened fourth acceptance criterion needed coordinator ratification | Closed by the coordinator: `client-follow-up-questions.md` version 2 ratifies the completion gate, including the expected-red list. Step 6 and `R12` now state that ratified gate verbatim rather than a planner-widened criterion. |
| Residual risk: installed legacy launches stay undocumented | No change, as the review accepts: the packaged file documents only routed launches and `design.md` records the omission with its reason. No acceptance criterion requires the extra sentence; a coordinator may add it in a later task. |

## Techstack scope

- Snapshot pointer: `projects/brida-workflow-simplification/handoffs/WFS-A-204/snapshots/attempt-plan-2-28f8a7c798bf2d9d981665425e0979bdbc6ef14ad540d43fd13e21cd5c483f90.snapshot.json`
- Snapshot SHA-256: `28f8a7c798bf2d9d981665425e0979bdbc6ef14ad540d43fd13e21cd5c483f90`
- Verified `match` on 2026-09-25 before any version 2 work; all eight required
  selected rule files were read in this session.
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
   launch guidance and the observation block. Keep the wording notes in
   `design.md`: prose `--task` (no change to the launch example block),
   installed exit-`2` row says "Invalid invocation" only, no legacy
   no-location note, no checkout ledger path anywhere.
3. **Extend the parity contract.** In
   `tests/contract/test_skill_parity_contract.py`, append the thirteen
   worker-ledger markers from `design.md` to `PARITY_MARKERS` under a comment
   naming this task, and add
   `test_the_packaged_tree_never_offers_the_checkout_ledger_flag_as_usable`
   with the four assertions specified in `design.md` ("Parity-contract
   extension"): the rejection sentence, the excluded checkout path shape, the
   exactly-once `--ledger-file` occurrence count, and the per-file placement
   pin. Do not modify or remove any existing marker, label, or test.
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
6. **Run the coordinator-ratified completion gate**
   (`client-follow-up-questions.md` version 2, ratified 2026-09-25): run
   `make test-unit`, `make test-contract`, `make test-integration`, then
   `techstack-eval`, `metrics`, `receipts`, `dossiers`, `memory-check`,
   `path-check`, `readme-check`, `phase5-preflight`, `package-check`
   individually, on the 3.10 shell interpreter and again with
   `PYTHON=/opt/homebrew/bin/python3.14`. Expected red, not to be fixed:
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
     `code-review.md`, `pr-desc.md`, or the missing `receipt.md` reported via
     `index.md`). An `index.md`-owned comparison row whose *text* mentions a
     planner artifact (for example "index says '<phase state>' but
     requirements.md says 'passed'") is expected and is not a planner-artifact
     diagnostic. The summary's "across N dossier(s)" figure is the count of
     dossiers scanned, not of dossiers holding issues. Baseline measured
     2026-09-25 after the version 2 artifacts were written: 39 issues, all
     owned by WFS-A-204 `index.md` (28), `code-review.md` (5), `pr-desc.md`
     (5), and `plan-review.md` (1: "review must reference the exact accepted
     plan version '2', found '1'", which clears when the reviewer reviews this
     version). A diagnostic *owned by* a planner artifact or by another
     dossier is a new defect to diagnose.
   - Everything else passes on both interpreters, including the extended
     skill-parity contract over the new text.
   Any failure outside this ratified expected-red list is the
   implementation's to diagnose before any code or tests change.
7. **Collect acceptance evidence and hand off.** The diff of the two files,
   the captured `--help` and rejection outputs, the focused-contract and
   completion-gate results on both interpreters, and a statement that no file
   outside the two named ones changed (`git status --short`). Leave everything
   uncommitted.

## Acceptance-criteria traceability

| Packet acceptance criterion | Requirements | Steps |
| --- | --- | --- |
| Packaged skill states `--task` verbatim-recording, the fixed installed ledger, the `--ledger-file` rejection, and the full `finish` attestation guidance | `R1`-`R6` | 2 |
| Every command and flag matches the shipped CLI, evidenced by `--help` or parser source | `R7` | 4 |
| No checkout-only flag presented as usable in installed-mode text | `R8` | 2, 3 |
| New section does not demote existing packaged safeguards (plan-review M1) | `R13` | 2, 3 |
| Packaging, manifest, and skill-parity contracts stay green, updated only where a contract legitimately pins the changed bytes | `R9`-`R11` | 3, 5 |
| Completion gate passes apart from the coordinator-ratified expected-red list | `R12` | 6 |
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

## Claim or decision

Plan `WFS-A-204-PLAN-001` version 2 (draft): implement WFS-A-204 as the
two-file change specified in `design.md` version 2, in the seven steps above,
verified by CLI-fidelity capture, the extended skill-parity contract (markers,
occurrence count, and placement pin), and the coordinator-ratified completion
gate on both interpreters. All plan-review version 1 findings are closed as
tabled above. An implementer who reads `requirements.md`, `design.md`, and
this plan needs no further research: the inserted text is fully drafted,
its placement is exact, and every literal in it is source-verified twice
(planning and independent review).

## Evidence

- `projects/brida-workflow-simplification/handoffs/WFS-A-204/plan-review.md` version 1 (verdict `CHANGES REQUIRED`; findings M1, L1, L2; test gaps 1-4; residual risks) is the change driver for this version; each finding's resolution is tabled above and cross-referenced to the revised artifact sections.
- `projects/brida-workflow-simplification/handoffs/WFS-A-204/client-follow-up-questions.md` version 2 records the coordinator-ratified completion gate step 6 now states, closing the review's acceptance-criterion residual risk.
- The Techstack snapshot verify command returned `status: match` with digest `28f8a7c798bf2d9d981665425e0979bdbc6ef14ad540d43fd13e21cd5c483f90` on 2026-09-25 in this session, and the resolution's scope paths contain both files this plan touches.
- Re-measured in this session on 2026-09-25 after the version 2 artifacts were written: `scripts/validate_task_dossiers.py projects` exits `1` with 39 issues, every one owned (path before the first colon) by WFS-A-204 `index.md`, `code-review.md`, `pr-desc.md`, or `plan-review.md`, and none by a planner artifact, while `make dossiers` exits `2`; the packaged `commands.md` has headings only at lines 1 and 65; `worker_launch.py:422-442` and `worker_ledger.py:670-742` carry the parser facts the steps transcribe; `src/brichan/resources/dogfood_v1/` contains zero occurrences of `--ledger-file` today.

## Uncertainty

- The dossier-validator issue count (38 on 2026-09-25, after the version 2 planner artifacts were written) will move as the coordinator and reviewer fill their artifacts; the ownership rule in step 6, not the count, is the acceptance test. The suite-level baseline (two `test_repository_paths` failures, one `test_task_dossier_workflow` failure, `path-check` red) was measured by planning and independently re-measured by the plan review on 2026-09-25; if the implementation observes any different failing test name or message outside the ratified expected-red list, that is a new finding to diagnose, not to absorb into this plan.
- No other unresolved uncertainty remains; no packet ambiguity rose to an escalation-worthy open question.
