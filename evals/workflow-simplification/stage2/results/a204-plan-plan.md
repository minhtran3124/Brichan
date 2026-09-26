# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `WFS-A-204`
- Task level: `1`
- Artifact: `plan`
- Artifact version: `1`
- Origin: `packet:WFS-A-204-PLAN@2026-09-25`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `22d40123-6f34-4491-8b8b-4c43e26981dc`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `WFS-A-204-PLAN-001`
- Plan status: `draft`

## Techstack scope

- Snapshot pointer: `projects/brida-workflow-simplification/handoffs/WFS-A-204/snapshots/attempt-plan-1-5fbec657f553ce2eee42580e59998288cd75c247f087a42702d9d37f33eac80c.snapshot.json`
- Snapshot SHA-256: `5fbec657f553ce2eee42580e59998288cd75c247f087a42702d9d37f33eac80c`
- Verified `match` on 2026-09-25 before planning began; all eight required
  selected rule files were read.
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
   insert the drafted launch paragraph and the drafted `## Worker ledger`
   section from `design.md` ("Drafted packaged text"), after the
   start-command guidance and before the "Observe workers" paragraph. Keep the
   wording notes in `design.md`: prose `--task` (no change to the launch
   example block), installed exit-`2` row says "Invalid invocation" only, no
   legacy no-location note, no checkout ledger path anywhere.
3. **Extend the parity contract.** In
   `tests/contract/test_skill_parity_contract.py`, append the thirteen
   worker-ledger markers from `design.md` to `PARITY_MARKERS` under a comment
   naming this task, and add
   `test_the_packaged_tree_never_offers_the_checkout_ledger_flag_as_usable`
   with the three assertions specified in `design.md`. Do not modify or remove
   any existing marker, label, or test.
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
6. **Run the completion gate.** `PYTHONDONTWRITEBYTECODE=1 make check`, then
   the targets it aborts before reaching, individually. The planning session
   measured this worktree's exact baseline on 2026-09-25; the implementation
   must match it, with the only delta being the extended parity contract
   passing over the new text:
   - Two pre-existing worktree-only failures in
     `tests/contract/test_repository_paths.py` and one `path-check` target
     failure, all one cause: this detached worktree's `.git` is a file, so the
     scanner reports `unclassified root files: .git`. Report; do not fix.
   - `make dossiers` (exit 1) and
     `tests.integration.test_task_dossier_workflow.test_repository_checkout_validates_clean`
     (1 failure) while this task is in flight: every diagnostic must name only
     the still-pending coordinator- or reviewer-owned WFS-A-204 artifacts
     (`index.md`, `plan-review.md`, `code-review.md`, `pr-desc.md`, missing
     `receipt.md`). They clear when the coordinator and reviewer complete the
     dossier; editing those artifacts is out of every worker's scope. A
     diagnostic naming any planner artifact or any other dossier is a new
     defect to diagnose.
   - Everything else passes: metrics tests, `test-unit`, `test-contract`
     (apart from the two failures above), the remaining 221 integration
     tests, `techstack-eval`, `metrics`, `receipts`, `memory-check`,
     `readme-check`, `phase5-preflight`, `package-check`, and
     `sh -n bin/brichan`.
   Any failure outside this baseline is the implementation's to diagnose
   before any code or tests change.
7. **Collect acceptance evidence and hand off.** The diff of the two files,
   the captured `--help` and rejection outputs, the focused-contract and
   `make check` results, and a statement that no file outside the two named
   ones changed (`git status --short`). Leave everything uncommitted.

## Acceptance-criteria traceability

| Packet acceptance criterion | Requirements | Steps |
| --- | --- | --- |
| Packaged skill states `--task` verbatim-recording, the fixed installed ledger, the `--ledger-file` rejection, and the full `finish` attestation guidance | `R1`-`R6` | 2 |
| Every command and flag matches the shipped CLI, evidenced by `--help` or parser source | `R7` | 4 |
| No checkout-only flag presented as usable in installed-mode text | `R8` | 2, 3 |
| Packaging, manifest, and skill-parity contracts stay green, updated only where a contract legitimately pins the changed bytes | `R9`-`R11` | 3, 5 |
| `make check` passes apart from the two known worktree-only failures | `R12` | 6 |
| Out-of-scope paths reported prominently | — | none found; see "Techstack scope" |

## Risks and boundaries

- The packaged edit changes the resource hash `init` embeds in new manifests.
  Release-process handled (see `design.md`, "Contract and manifest
  consequences"); no action in this task.
- The implementer must not add a packaged file, edit the packaged `SKILL.md`
  or any checkout skill file, or reword existing packaged safeguards — the
  negative parity assertions and `PACKAGED-001`..`PACKAGED-003` bound the
  change to the drafted insertion.
- This is a documentation-plus-contract change with no executable-behavior
  change, so no unit or integration test changes are required; the regression
  guard demanded by `GENERAL-004`'s intent is the extended parity contract.

## Claim or decision

Plan `WFS-A-204-PLAN-001` version 1 (draft): implement WFS-A-204 as the
two-file change specified in `design.md`, in the seven steps above, verified by
CLI-fidelity capture, the extended skill-parity contract, and `make check`
modulo the two known worktree-only failures. An implementer who reads
`requirements.md`, `design.md`, and this plan needs no further research: the
inserted text is fully drafted and every literal in it is source-verified.

## Evidence

- `projects/brida-workflow-simplification/handoffs/WFS-A-204/request.md` (the recorded claim and gaps) and the packet's acceptance criteria are decomposed one-to-one in the traceability table above against `requirements.md` `R1`-`R12`.
- The Techstack snapshot verify command returned `status: match` with digest `5fbec657f553ce2eee42580e59998288cd75c247f087a42702d9d37f33eac80c` on 2026-09-25, and the resolution's scope paths contain both files this plan touches.
- `src/brichan/orchestration/worker_ledger.py` lines 660-742, `src/brichan/orchestration/worker_launch.py` (parser and line 701), and captured `--help`/rejection output ground every command literal the plan orders the implementer to transcribe.
- `tests/contract/test_skill_parity_contract.py` and `src/brichan/lifecycle.py` lines 29-40 and 143-153 ground the contract analysis: markers are the only pin on the changed bytes, and the manifest inventory is untouched because no resource path is added.

## Uncertainty

- The step 6 baseline was measured in this worktree on 2026-09-25 during planning, before any implementation change; it extends the task packet's stated environment facts with two consequences of the same causes (the `path-check` target shares the `.git`-file cause, and the in-flight dossier fails `make dossiers` plus one integration test until the coordinator and reviewer complete their artifacts). If the implementation observes any different count, test name, or message, that is a new finding to diagnose, not to absorb into this plan.
- No other unresolved uncertainty remains; no packet ambiguity rose to an escalation-worthy open question.
