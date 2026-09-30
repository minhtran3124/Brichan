# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `WFS-A-204`
- Task level: `1`
- Artifact: `plan-review`
- Artifact version: `4`
- Origin: `packet:WFS-A-204-PLAN-REVIEW@2026-09-25#attempt-plan-review-4`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `2fbce2ec-8fd9-4ba4-9b99-70fc73254216`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `2fbce2ec-8fd9-4ba4-9b99-70fc73254216`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `WFS-A-204-PLAN-001`
- Reviewed plan version: `4`

Artifacts reviewed: `requirements.md` v4, `brief.md` v4, `options.md` v4,
`design.md` v4, `plan.md` v4, against `request.md` v1 and the
coordinator-owned `client-follow-up-questions.md` v2. Versions 1, 2, and 3 of
this artifact are preserved unmodified at `versions/v1/plan-review.md`,
`versions/v2/plan-review.md`, and `versions/v3/plan-review.md`; this is
version 4 of the same artifact and replaces version 3 as the live review.

This reviewing session (`2fbce2ec-8fd9-4ba4-9b99-70fc73254216`) authored none
of them: the version 4 planner session is
`cbe8f2f3-df53-44bd-85b0-f419269bce8c`, version 3's was
`c106f802-fc5e-4e34-b6b4-c2d1f650fede`, versions 1 and 2 were
`6b5e7d82-9bdc-4a2e-824c-fb3b11060427`, and the three earlier reviewing
sessions were `dead92d1-3d47-4d40-a165-fddf72ffe97c` (v1),
`6b5efc0a-4bf7-43ae-904f-4e26da67deaa` (v2), and
`a8170c4a-509f-4e96-a25e-b5cab9b8e257` (v3). Identifier inequality is a
deterministic consistency signal, not proof that five sessions existed.

## Techstack scope

- Snapshot pointer: `projects/brida-workflow-simplification/handoffs/WFS-A-204/snapshots/attempt-plan-review-4-de980e60b988a5b6cd3268935435ac1efa476f9c8735062d957dff0074b278fe.snapshot.json`
- Snapshot SHA-256: `de980e60b988a5b6cd3268935435ac1efa476f9c8735062d957dff0074b278fe`
- Verified `status: match` before any other work, and all eight required
  selected rule files were read in this session. No path outside the declared
  scope paths was needed, and no new Context ID, chain, conflict, or exception
  need was discovered.

## Verdict

`PASS`. No critical, high, or medium defect exists, and nothing remains that
would change a byte the implementation ships, a step it runs, or an assertion
it adds.

Both version 3 findings are genuinely closed, and I re-derived each closure by
execution rather than reading the closure table. `R5`
(`requirements.md:49`) no longer claims to enumerate every `finish` refusal:
it scopes its four-item list to the refusals that bound attestation integrity,
states in terms that neither the list nor the packaged text is exhaustive, and
records the four omitted refusals — the `no ledger for this target` resolution
refusal `R4` documents one row above, plus the three `find_git_root`
path-resolution usage refusals — with a companion wording note at
`design.md:149-160` forbidding their addition to the packaged text. I
reproduced all four against the shipped entry point at exit `1`, and I
confirmed the drafted packaged text is byte-identical to the version 3 draft,
so the correction is a requirement correction only, exactly as the version 3
review offered it. `L2-v3` is closed at `options.md:26-37`, and I verified the
corrected record by re-running the diff it rests on: `versions/v2/options.md`
against `versions/v3/options.md` is the metadata block, the version note, and
two Evidence bullets, which is what the note now says.

The substance I had to satisfy myself about independently, I did by execution,
not by reading the previous review. I applied the version 4 drafted text and
the proposed contract extension to a scratch copy of both skill trees outside
the repository and ran the real parity module: 17 tests `OK` on Python 3.10
and 3.14, headings landing at lines 1, 71, and 114 so the observation
safeguards stay directly under the top-level heading, all thirteen markers
moving `0`→`1` in the packaged tree while already present once in the checkout
tree, `--ledger-file` moving `0`→exactly `1`, and three mutations of the
guarded properties each failing as intended. Every CLI literal in `R1`-`R7`
holds against captured `--help` output and reproduced refusals. The completion
gate is step-for-step equivalent to `make check` against `Makefile:24-28,75-76`
and I measured it: the expected-red list is exactly the two `.git` worktree
failures with `path-check`, and the in-flight-dossier validator failures at
`39` issues with the ownership distribution the plan predicts, down to the
`plan-review.md` row naming version `'4'`.

One low, non-blocking observation remains (`O1`): the `plan.md` and `design.md`
version notes under-enumerate their own version 3 → version 4 diffs. It is
recorded below with evidence and a suggested in-place correction. I did not
make it blocking, and the reasoning is stated in the finding rather than left
implicit.

## Findings closure check against version 3

Checked row by row against `versions/v3/plan-review.md`. The table at
`plan.md:49-55` is accurate and complete; no closure claim is overstated.

| Version 3 item | Claimed closure | Verified |
| --- | --- | --- |
| `L1-v3` (low) `R5` claimed to enumerate every `finish` refusal and omitted four | Quantifier narrowed to "the refusals that bound attestation integrity"; non-exhaustiveness stated; the four omitted refusals recorded as enforced-but-deliberately-undocumented; matching wording note added to `design.md`; drafted packaged text unchanged | **Yes, by execution.** `requirements.md:49` now scopes the list and names the `R4` resolution refusal plus the three `find_git_root` messages; `design.md:149-160` forbids adding them to the packaged text with the code citations. I reproduced all four refusals against the shipped `finish`: `no ledger for this target` (Git root without a regular `.brichan/manifest.json`), `target project is not a directory`, `target project is not a Git repository root`, and `cannot find a Git repository from` — each exit `1`, each through the `except (LedgerError, ValueError, OSError)` arm at `worker_ledger.py:727`, `ProjectError` being a `ValueError` subclass (`project.py:9`, messages at `:36-38,:41-42,:51`). `diff versions/v3/design.md design.md` shows no change inside the drafted-text block (`design.md:77-131`), so the review's premise — nothing false was ever going to ship — still holds. |
| `L2-v3` (low) `options.md`'s version note misdescribed its own diff | Note corrected to "the metadata plus two rewritten Evidence bullets", with the diff named as ground | **Yes.** `options.md:26-37`. I re-ran `diff versions/v2/options.md versions/v3/options.md`: exactly the metadata block (version, origin, authoring session), the version note, and two Evidence bullets at `versions/v3/options.md:114-115`. The corrected note matches the measurement, and the archived version 3 file is untouched (`DOSSIER-003`). |
| v3 test gap 1 (refusal-set correspondence unguarded, and nothing can cheaply guard it) | Requirement correction, not an assertion; limitation recorded in `design.md` | **Yes.** `design.md:235-240` now records the limitation in its broadened form (the correspondence between the documented refusal set and the shipped refusal set), which is the right statement of it. |
| v3 test gaps 2-4 (tree-text markers; coarse placement pin; no installed-vs-checkout exit-table test) | Carried unchanged, no action | **Yes.** `design.md:229-234`. I mutation-tested the placement pin and the occurrence count myself; both catch what they claim to catch. |
| v3 residual risks (legacy launches; manifest-hash churn; worktree-specific expected-red list; `draft` plan status; WLG-001 provenance) | Carried forward; baseline re-measured rather than inherited | **Yes.** `design.md:149-165,255-266`, `plan.md:183-197,225-227`, `requirements.md:83`. The baseline is re-measured and correct: `38` before the version 4 planner artifacts, `39` after. I measured `39` now, with the predicted ownership split. |

## Findings

No blocking finding. One low, non-blocking observation:

### `O1` (low, non-blocking) — the `plan.md` and `design.md` version notes under-enumerate their own diffs

`plan.md:39-45` states:

> The implementation steps, the traceability table, and the risks are
> unchanged in substance; what changes besides the metadata and this note: the
> closure table, the Techstack snapshot pointer for this attempt, the
> dossier-validator baseline (re-measured in this session), the step 6 note on
> the plan-review version-mismatch diagnostic, and the Evidence and
> Uncertainty sections.

`diff versions/v3/plan.md plan.md` also shows, outside that enumeration:
step 2 gaining the prohibition "no `find_git_root` path-resolution refusals"
and losing the stale version 2 comparison (`plan.md:82-88`); a new step 6
sentence recording that plan-review version 3 measured the whole gate on both
interpreters (`plan.md:129-131`); the traceability row for CLI fidelity now
citing `R5` and "claiming no exhaustiveness it does not have"
(`plan.md:174`); and a rewritten `Claim or decision` (`plan.md:201-214`).

`design.md:31` states "Three bookkeeping changes land here besides the
metadata" and lists three. The diff also rewrites the first recorded
limitation's attribution (`design.md:232`), the second recorded limitation's
substance from "the *condition* under which `finish` refuses" to "the
correspondence between the documented refusal set and the shipped code's
refusal set" (`design.md:235-240`), the parity-verification sentence under
"Contract and manifest consequences" (`design.md:255-258`), the
`Claim or decision` (`design.md:278-282`), and a second Evidence bullet
(`design.md:286`).

Why this is not blocking, stated rather than implied. Unlike `L2-v3`, neither
note makes an exclusive false claim: `options.md` version 3 said "the metadata
above is the only change", which excluded edits that existed; these notes
enumerate change drivers and every unlisted hunk traces to one of the drivers
they do name — the `L1-v3` closure (the broadened limitation, the added
exhaustiveness clause, the extra Evidence citation), the resolved
re-simulation uncertainty (the parity-verification sentence), or the pointer
move to version 3. The one edit that is hardest to fit, step 2's new
prohibition, changes no action an implementer takes: it forbids adding text the
drafted draft never contained, and it is the transcription of the
`design.md:149-160` note the same version note announces. Nothing about the
work changes, and no reader of the live artifacts is misled about what to
build. Reporting it as a defect would hold a fourth planning round over a
self-descriptive sentence, which the reviewer policy's "no style preference
without a real maintenance or correctness risk" rule tells me not to do.

Suggested handling, at the coordinator's discretion and not a required change:
the plan is still `Plan status: draft`, so tightening either sentence is an
in-place accuracy correction under `DOSSIER-004`, not a new artifact version.
"besides the metadata and this note, and smaller consequential edits to
step 2, step 6, the traceability row, and `Claim or decision`" would make
`plan.md:39-45` exact; "three bookkeeping drivers, with their consequential
edits" would do the same for `design.md:31`.

## Verification performed

Nothing below was accepted from the plan or from the version 3 review; each
item was re-derived in this worktree. Unless stated otherwise the command
prefix was `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src` and the interpreter was
the shell `python3` (3.10).

The real parity suite against the version 4 drafted text. Because this task
may write one file only, I copied both skill trees and
`tests/contract/test_skill_parity_contract.py` into a scratch directory
outside the repository, applied the drafted text exactly as `design.md:77-131`
specifies it (launch paragraph after the paragraph ending "Close only a
recorded Brichan-owned pane with `herdr pane close <pane-id>`.";
`## Worker ledger` immediately before `## Recover a swallowed Enter`),
appended the thirteen markers and the new test as `design.md:180-227`
specifies, and ran the module. No repository file was modified;
`git status --short` is empty.

- **17 tests, `OK`** on both 3.10 and 3.14 — every existing assertion plus the
  new one.
- Headings in the edited packaged file land at lines 1 (`# Herdr commands`),
  71 (`## Worker ledger`), and 114 (`## Recover a swallowed Enter`), so the
  observation surface and the six "Safeguards that apply to every observation"
  bullets stay directly under the top-level heading. `R13` and the `M1` fix
  hold, and these are the same three line numbers version 3 measured.
- All thirteen markers are genuine new guards, counted mechanically through
  the contract's own `tree_text` (`test_skill_parity_contract.py:90-103`):
  each occurs `0` times in the packaged tree before the edit, exactly `1`
  after, and exactly `1` in the checkout tree already — so both
  `test_the_checkout_skill_states_every_safeguard` and
  `test_the_packaged_skill_states_every_safeguard` pass without the checkout
  tree being touched, and no marker was already satisfied for an unrelated
  reason (`R10`).
- `--ledger-file` in the packaged tree: `0` before, exactly `1` after, inside
  the rejection sentence; `projects/<slug>/ledger/workers.jsonl` is absent
  (`R8`).
- **Mutation-tested (`TEST-003`).** Section moved above the safeguards →
  `AssertionError: 3799 not less than 927`. Section deleted →
  `AssertionError: '## Worker ledger' not found in ...`, the `assertIn`
  legibility guard working rather than a `ValueError`. Affirmative
  "you may also add `--ledger-file`" sentence appended →
  `AssertionError: 1 != 2`. All three match version 3's measurements exactly.
- The one existing assertion the insertion could plausibly have broken holds
  with margin: the paste-recovery ±900-character window
  (`test_skill_parity_contract.py:193-207`) still finds `idle`, `unsubmitted`,
  and `herdr agent read` at 82, 156, and 86 normalized characters from
  `herdr pane send-keys <pane-id> Enter`, so the section landing directly
  above the recovery flow is not near that boundary.

CLI fidelity (`R1`-`R7`, packet criterion two) — every claim held. Captured
`--help` from both installed entry points and reproduced each refusal:

- The installed launcher prints `--task TASK  task identifier recorded
  verbatim in the worker ledger; never inferred when the flag is absent`,
  matching `R1` verbatim (`worker_launch.py:422-428`).
- The installed usage line carries no `--ledger-file`
  (`worker_launch.py:429-441` adds it only under
  `if checkout_root is not None`), and an installed launch passing it fails
  with `error: unrecognized arguments: ... --ledger-file ...`, exit `2`
  (`R2`).
- `brichan-herdr-worker-ledger finish --help` prints
  `[-h] --worker WORKER --launch-id LAUNCH_ID --evidence EVIDENCE [--task TASK] [--pane PANE] [--project PROJECT]`
  — required `--worker` and `--launch-id`, repeatable `--evidence`, optional
  `--task`, `--pane`, `--project`, and no `--ledger-file`
  (`worker_ledger.py:660-692`); `finish --ledger-file` there is
  `error: unrecognized arguments`, exit `2` (`R4`).
- Reproduced refusals, each exit `1`: `worker name must begin with brichan-`
  (`worker_ledger.py:705`), `every --evidence item must be non-empty`
  (`:713`) — both before ledger resolution, so nothing is written;
  `no ledger for this target: <root>` on a Git root lacking a regular
  `.brichan/manifest.json` (`:203-220`, whose only check is the `os.lstat`
  plus `stat.S_ISREG` at `:195-200`, never `inspect_project`); and
  `no launched record for launch_id <id>` on an initialized target (`:636`),
  after which I confirmed no ledger file or directory was created. The
  already-finished refusal is at `:638` and the first-`finished`-wins
  tie-break at `:445-453` (`R5`, `R6`).
- The exit table is right, including its `1` row's "write failure": a failed
  append returns a reason string from `record_finish` (`:611-651`) and
  `_finish_command` turns that into exit `1` (`:696-742`), so `2` is reachable
  only through argparse — which is why the packaged row says "Invalid
  invocation" without the checkout file's "including a rejected
  `--ledger-file` value".
- `ledger: launch_id=<uuid>` goes to stderr with stdout reserved for the
  verbatim `agent_started` envelope (`worker_launch.py:698`), and
  `warning: worker started but ledger write failed: <reason>` leaves the exit
  code `0` (`:701`); `--json` implies `--dry-run` per its own help text and
  the ledger block sits after the rollback scope closes, so "a launch that
  rolls back appends nothing" and "`--dry-run` and `--json` write nothing"
  both hold (`R3`).
- The omission of the legacy `ledger: no ledger location for this launch; not
  recorded` note is not merely tolerable but correct for this file: a routed
  installed launch sets `ledger=installed_location(paths.project_root)`
  unconditionally (`worker_launch.py:516-524`), so the `resolution.ledger is
  None` branch at `:679` is unreachable for the launches the packaged file
  documents, and the packaged tree documents no legacy path at all.

Contract and manifest surface (`R9`, `R11`) — no edit needed anywhere else.
`IMMUTABLE_PATHS` already lists
`skills/herdr-orchestration/references/commands.md`
(`src/brichan/lifecycle.py:29-40`), so the inventory does not change and
`PACKAGED-002` is not triggered; `intended_manifest()` hashes resource bytes
at runtime (`:143-155`). No test pins the changed file's bytes, size, or
digest — a search of the whole test tree for such an assertion against
`dogfood_v1` returns nothing. `config/repository-paths.json:991-994` sources
its only `commands.md` entry from the *checkout* file, so the packaged edit
cannot move `path-check`. The three focused contracts are green today, before
any edit: `test_skill_parity_contract`, `test_dogfood_policy_contract`,
`test_packaging_metadata` — 42 tests, `OK`.

The completion gate, measured. Every step of `plan.md:113-162` on the 3.10
shell interpreter, plus the two invocations that do not honor `PYTHON=` under
`/opt/homebrew/bin/python3.14`, plus the parity module under 3.14:

| Step | Result |
| --- | --- |
| `test-unit` | 1026 tests, `OK` |
| `test-contract` | 148 tests, 2 failures, 1 skipped |
| `test-integration` | 222 tests, 1 failure |
| `techstack-eval`, `metrics`, `receipts`, `memory-check`, `readme-check`, `phase5-preflight`, `package-check` | all exit `0` |
| `path-check` | exit `2` (`unclassified root files: .git`) |
| `dossiers` | make exit `2` over script exit `1`, `39 issue(s) across 8 dossier(s).` |
| `sh -n bin/brichan` | exit `0` |
| `metrics/test_validate_metrics.py` under 3.14 | 10 tests, `OK` |
| `evals.techstack_context_v1.test_cases` under 3.14 | `OK` |
| parity module under 3.14 (scratch copy with the edit) | 17 tests, `OK` |

Both `test-contract` failures are
`tests/contract/test_repository_paths.py::test_current_path_and_link_contracts_pass`
and `::test_every_non_ephemeral_root_file_is_classified`, both
`AssertionError: 0 != 1 : unclassified root files: .git`; `make path-check`
shares that one cause. These are the two known worktree-only failures plus
their target — this worktree's `.git` is a file — and they are reported, not
fixed, as instructed. The single `test-integration` failure is
`test_task_dossier_workflow.test_repository_checkout_validates_clean`, whose
output is this dossier's own diagnostics. Ownership, taken as the artifact
path before the first colon: `index.md` 28 (5 unfilled metadata placeholders,
4 unfilled task-identity fields including the `canonical receipt does not
exist` row, 19 artifact-status comparison rows), `code-review.md` 5,
`pr-desc.md` 5, and `plan-review.md` 1 — `Review target.Reviewed plan version:
review must reference the exact accepted plan version '4', found '3'`, the row
this artifact clears. No diagnostic is owned by a planner artifact or by
another dossier, so the plan's acceptance rule holds.

Scope and completeness of the planned change. The plan neither misses a
necessary change nor adds an unnecessary one. The checkout tree needs no edit,
verified by count rather than assumed: all thirteen markers already occur
there. The packaged `SKILL.md` exclusion (`options.md:101-109`) is sound — the
packaged `SKILL.md` already routes the coordinator to
`references/commands.md`. Both files the plan touches are inside the declared
scope paths, and `plan.md:63-68`'s "no path outside the declared scope paths"
statement is correct.

## Test gaps

1. **The launch paragraph's placement is unpinned; only the section's is.**
   New this round, verified by mutation: relocating the whole `--task` /
   `--ledger-file` paragraph out of the launch guidance and into the
   `## Worker ledger` section leaves all 17 tests `OK`, because every marker
   is still present and the placement pin constrains only
   `safeguards < ledger < recovery`. No action asked: the consequence is
   reading order, not a lost safeguard, and `plan.md:75-88` states the
   position exactly. Recorded so a later session does not mistake the passing
   suite for a placement guarantee on that paragraph.
2. **Nothing guards `R5`'s refusal list against the `L1-v3` gap, and nothing
   can cheaply.** Carried from v2 gap 1 / v3 gap 1 and correctly recorded at
   `design.md:235-240`. The fix was the requirement correction, now made. No
   action.
3. **The markers are asserted on concatenated tree text.** Carried from all
   three earlier reviews, recorded at `design.md:229-234`. Prose moved between
   packaged `.md` files would still pass; acceptable because
   `IMMUTABLE_PATHS` fixes the packaged file set and the placement pin is
   per-file. No action.
4. **The placement pin is legible but coarse.** It asserts offsets, which
   catches reordering and deletion — I verified both — but not a section moved
   into a different packaged `.md` file, which gap 3 already covers. No
   action.
5. **No test distinguishes the installed exit-`2` table row from the checkout
   one.** Covered indirectly by the exactly-once occurrence count, which I
   mutation-tested. No action.

## Residual risks and required human decisions

- **The version notes under-enumerate their diffs (`O1`).** Non-blocking, with
  a suggested in-place correction while the plan is still `draft`. An auditor
  who trusts either note instead of re-diffing would not learn that step 2
  gained a prohibition or that a recorded limitation was broadened; both
  changes are correct, so the risk is to audit fidelity only.
- **Installed legacy launches stay undocumented.** Carried and now verified at
  the branch level (`worker_launch.py:516-524,679`): the note cannot fire for
  a routed installed launch, and the packaged file documents no legacy launch,
  so nothing in it is false. `design.md:161-165` records the omission with its
  reason. No acceptance criterion requires the extra sentence.
- **Manifest-hash churn on an immutable resource.** `design.md:259-266` states
  it correctly and I found no contract that needs editing: a target
  initialized from an older build of the same `package_version` would inspect
  as `MALFORMED` against a locally rebuilt package. Release-process handled;
  no action in this task.
- **The expected-red list stays worktree-specific and dossier-specific.** I
  re-measured every entry rather than inheriting it. On the main checkout with
  a closed dossier all of it must be green, as
  `client-follow-up-questions.md` and `plan.md:194-197` both say. The dossier
  half will shift as the coordinator fills `index.md`, `code-review.md`,
  `pr-desc.md`, and `receipt.md`: with this artifact written, the
  `plan-review.md` row clears, so the implementation should expect **38**
  issues unless another artifact changes first. The plan's ownership rule, not
  the count, is the acceptance test.
- **`plan.md` records `Plan status: draft`.** Correct for a version awaiting
  review, but `--require-complete` needs `accepted` and the validator reads
  the live plan version as `4`. Coordinator action after this verdict, not a
  plan defect.
- **Provenance of the originating residual risk could not be re-read at
  source.** `projects/brida-worker-ledger/handoffs/WLG-001/code-review.md` is
  not present in this worktree, as `requirements.md:83` records. The gap it
  describes was verified directly against the packaged tree — zero
  occurrences of `--ledger-file`, `workers.jsonl`, or `Worker ledger` in
  `src/brichan/resources/dogfood_v1/` — so no requirement depends on it.
- **No decision is required from the user.** `O1` is a coordinator-level call
  on planner-owned wording, and it does not gate implementation.

## Claim or decision

Plan `WFS-A-204-PLAN-001` version 4 is `PASS`. Both version 3 findings are
genuinely closed and each closure was re-derived by execution: the narrowed
`R5` matches the refusal set I reproduced against the shipped `finish`, and
the corrected `options.md` version note matches the diff I re-ran. Following
this plan would satisfy all four packet acceptance criteria. The packaged text
states `--task` with its verbatim-recording rule, the fixed installed ledger
with the `--ledger-file` rejection, and the installed `finish` attestation
with `--project`, `--worker`, `--launch-id`, `--evidence`, its
integrity-bounding refusals, and the attestation-not-proof rule. Every
command, flag, refusal string, and exit code in it matches captured `--help`
output or the parser source, claims no refusal the CLI does not enforce, and
claims no exhaustiveness it does not have. Packaging, manifest, and
skill-parity contracts stay green with the parity contract extended rather
than weakened — 17 tests `OK` on both interpreters over the real drafted text,
thirteen markers newly guarded, three mutations correctly red. And the gate is
`make check`-equivalent and green apart from the ratified expected-red list,
which I measured. The one remaining item is a low, non-blocking imprecision in
two version notes, recorded as `O1` with a correction the coordinator may
apply in place before accepting the plan.

## Evidence

- `requirements.md:49` (`R5`, narrowed and explicitly non-exhaustive, recording the `R4` resolution refusal and the three `find_git_root` messages) with `design.md:149-160` (the companion wording note) closes `L1-v3`; ground re-derived by reproducing all four refusals against the shipped installed `finish`, each exit `1`: `worker_ledger.py:203-220` and `:195-200` for `no ledger for this target`, `project.py:9,36-38,41-42,51` with the `except (LedgerError, ValueError, OSError)` arm at `worker_ledger.py:727` for the three path-resolution messages.
- `options.md:26-37` closes `L2-v3`; `diff versions/v2/options.md versions/v3/options.md` re-run in this session is exactly the metadata block, the version note, and two Evidence bullets, which is what the corrected note states. The archived versions are unmodified (`DOSSIER-003`).
- The real parity module run against a scratch copy carrying the version 4 drafted text (`design.md:77-131`) and the proposed extension (`design.md:180-227`): 17 tests `OK` under 3.10 and 3.14; packaged headings at lines 1, 71, 114 with the observation safeguards under the top-level heading; all thirteen markers `0`→`1` in the packaged tree and already `1` in the checkout tree; `--ledger-file` `0`→exactly `1` with `projects/<slug>/ledger/workers.jsonl` absent; three mutations red (`3799 not less than 927`; `'## Worker ledger' not found`; `1 != 2`); and the paste-recovery ±900-character window still satisfied at 82/156/86 characters — confirming `R8`, `R10`, `R13`, and `TEST-003`.
- Captured installed `--help` for both entry points plus reproduced refusals confirm every literal in `R1`-`R7`: the `--task` help text verbatim (`worker_launch.py:422-428`); the installed usage line with no `--ledger-file` (`:429-441`) and its `unrecognized arguments` exit `2`; `finish` usage `[-h] --worker WORKER --launch-id LAUNCH_ID --evidence EVIDENCE [--task TASK] [--pane PANE] [--project PROJECT]` (`worker_ledger.py:660-692`); `worker name must begin with brichan-` (`:705`) and `every --evidence item must be non-empty` (`:713`) each exit `1` before ledger resolution with nothing written; `no launched record for launch_id` (`:636`) and the already-finished refusal (`:638`); the first-`finished`-wins tie-break (`:445-453`); write failures returning a reason through `record_finish` (`:611-651`) into exit `1` (`:696-742`); and `worker_launch.py:698,701` for the stderr `launch_id` line and the warning that leaves exit `0`.
- `src/brichan/lifecycle.py:29-40,143-155`, the absence of any byte, size, or digest assertion against `dogfood_v1` in `tests/`, and `config/repository-paths.json:991-994` (checkout-sourced) confirm `R9` and `R11`; the three focused contracts pass today (42 tests, `OK`). `worker_launch.py:516-524,679` confirms the legacy-note omission is correct for routed installed launches.
- `Makefile:24-28,75-76` (`check` = `test` plus nine targets plus `sh -n bin/brichan`, with `test` running the metrics unittest first) and `:39-40` (`techstack-eval` hardcodes `python3`) confirm `plan.md:113-131` is step-for-step equivalent to `make check`; measured: `test-unit` 1026 `OK`; `test-contract` 148 with the two `unclassified root files: .git` failures; `test-integration` 222 with the single in-flight-dossier failure; seven targets exit `0`; `path-check` exit `2`; `dossiers` make exit `2` over script exit `1`; `sh -n bin/brichan` exit `0`; and both 3.14 direct invocations `OK`.
- `scripts/validate_task_dossiers.py projects` reports `39 issue(s) across 8 dossier(s).`, script exit `1`, owned `index.md` 28 / `code-review.md` 5 / `pr-desc.md` 5 / `plan-review.md` 1, the last being the version-mismatch row naming `'4'` — the plan's predicted baseline and distribution exactly (`plan.md:149-158`).
- `diff versions/v3/plan.md plan.md` and `diff versions/v3/design.md design.md` are the evidence for `O1`: changes at `plan.md:82-88,129-131,174,201-214` and `design.md:232,235-240,255-258,278-282,286` fall outside the notes' enumerations at `plan.md:39-45` and `design.md:31`.
- `git status --short` is empty apart from this artifact: the parity verification ran on a scratch copy outside the repository, and no other repository file was modified by this review.

## Uncertainty

- The two `tests/contract/test_repository_paths.py` failures and `make path-check` share one cause I did not attempt to fix, as instructed: this detached worktree's `.git` is a file, so the root-file scan reports it as unclassified. They are worktree-only and are reported, not diagnosed.
- The parity verification ran the real contract module against a faithful scratch copy of both skill trees, not against a modified worktree, because this task may write one file only. The copy is byte-identical to the trees plus the specified edit, and the module computes its own tree text, so the result is the suite's real behavior on the edited content — but the implementation must still run plan step 5 in place and report the real result, and a transcription differing from the drafted text in any marker-bearing phrase could still fail. One transcription detail the implementer should note: the absence-rule marker contains double quotes, so it must be written as a single-quoted Python string.
- My reproduction of the four `L1-v3` refusals used temporary directories rather than a real `brichan init` target, because initializing one is outside this task's scope. Since any project `brichan init` touches is a Git root by construction, the three `find_git_root` refusals cannot fire on a legitimately initialized target — which is why leaving them out of the packaged text is sound.
- I measured the gate on the 3.10 shell interpreter and ran only the parity module and the two prescribed direct invocations under 3.14; the full 3.14 sweep is version 3's measurement, which I did not repeat. Nothing in this documentation-and-contract change is interpreter-sensitive, and the parity module is the only suite the change touches.
- I did not re-verify every line number the planner artifacts cite, only those load-bearing for a finding, a closure, or an acceptance criterion; the ones I checked were accurate.
- No other unresolved uncertainty remains about the reviewed plan.
