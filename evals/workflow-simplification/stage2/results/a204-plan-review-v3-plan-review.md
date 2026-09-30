# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `WFS-A-204`
- Task level: `1`
- Artifact: `plan-review`
- Artifact version: `3`
- Origin: `packet:WFS-A-204-PLAN-REVIEW@2026-09-25#attempt-plan-review-3`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `a8170c4a-509f-4e96-a25e-b5cab9b8e257`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `a8170c4a-509f-4e96-a25e-b5cab9b8e257`
- Review verdict: `CHANGES REQUIRED`

## Review target

- Reviewed plan ID: `WFS-A-204-PLAN-001`
- Reviewed plan version: `3`

Artifacts reviewed: `requirements.md` v3, `brief.md` v3, `options.md` v3,
`design.md` v3, `plan.md` v3, against `request.md` v1 and the
coordinator-owned `client-follow-up-questions.md` v2. Versions 1 and 2 of this
artifact are preserved unmodified at `versions/v1/plan-review.md` and
`versions/v2/plan-review.md`; this is version 3 of the same artifact and
replaces version 2 as the live review.

This reviewing session (`a8170c4a-509f-4e96-a25e-b5cab9b8e257`) authored none
of them; the version 3 planner session is
`c106f802-fc5e-4e34-b6b4-c2d1f650fede`, the version 1 and 2 planner session was
`6b5e7d82-9bdc-4a2e-824c-fb3b11060427`, and the two earlier reviewing sessions
were `dead92d1-3d47-4d40-a165-fddf72ffe97c` (v1) and
`6b5efc0a-4bf7-43ae-904f-4e26da67deaa` (v2). Identifier inequality is a
deterministic consistency signal, not proof that four sessions existed.

## Techstack scope

- Snapshot pointer: `projects/brida-workflow-simplification/handoffs/WFS-A-204/snapshots/attempt-plan-review-3-de8b8b4e60027b2a016f041fe62288f7bcfa6a9f7391b1f75a7164abea340c48.snapshot.json`
- Snapshot SHA-256: `de8b8b4e60027b2a016f041fe62288f7bcfa6a9f7391b1f75a7164abea340c48`
- Verified `status: match` before any other work, and all eight required
  selected rule files were read in this session. No path outside the declared
  scope paths was needed, and no new Context ID, chain, conflict, or exception
  need was discovered.

## Verdict

`CHANGES REQUIRED`, on two low findings. No medium, high, or critical defect
remains.

All four version 2 findings are genuinely closed, and every closure was
re-derived here by execution rather than by reading the closure table. The
`L1-v2` sentence now states the condition the code enforces, and I reproduced
that condition against the shipped command: a Git root without a regular
`.brichan/manifest.json` refuses with exactly `no ledger for this target` and
exit `1`. The `L2-v2` gate is now step-for-step equivalent to `make check`
against `Makefile:24-28,75-76`. The `L3-v2` correction is not only specified
but works: I ran the prescribed direct 3.14 eval invocation (56 tests, `OK`).
The `L4-v2` baseline is one figure, `39`, and `39` is what I measured, with
the exact ownership distribution the plan predicts.

I also closed the measurement gap both earlier reviews recorded as
uncertainty. The whole completion gate now has a real two-interpreter
measurement: every target and suite was run on the 3.10 shell interpreter and
again under `/opt/homebrew/bin/python3.14`, and the expected-red list holds
identically on both. And I ran the real parity suite — not a simulation —
against a scratch copy carrying the version 3 drafted text and the proposed
contract extension: 17 tests `OK` on both interpreters, all thirteen markers
newly satisfied in the packaged tree, and three mutations of the guarded
properties each failing as intended.

What blocks acceptance is smaller than last round and ships nowhere. `R5`
claims to enumerate *every* `finish` refusal the shipped CLI enforces, and the
list omits the refusal `R4` documents one row above it plus three exit-`1`
path-resolution refusals I reproduced (`L1-v3`). And `options.md`'s version
note misdescribes its own diff (`L2-v3`). Both are one-clause corrections to
planner artifacts. Neither touches the drafted packaged text, the selected
option, the marker set, the placement, or the gate — all of which I verified
and would accept as they stand.

## Findings closure check against version 2

Checked row by row against `versions/v2/plan-review.md`. The table at
`plan.md:47-61` is accurate and complete; no closure claim is overstated, and
each was verified independently below rather than accepted.

| Version 2 item | Claimed closure | Verified |
| --- | --- | --- |
| `L1-v2` (low) drafted text states a `finish` refusal the CLI does not enforce | `--project` paragraph and `R4` restated to the enforced condition; a wording note forbids reintroducing "healthy managed state"; test gap 1 recorded as a limitation | **Yes, by execution.** `design.md:109-114` and `requirements.md:42` now say the target must hold a regular `.brichan/manifest.json` or the command refuses `no ledger for this target`, exit `1`, and state that `finish` does not verify managed-state health. I ran it: `finish --project <git-root-without-.brichan>` prints `brichan-herdr-worker-ledger: no ledger for this target: <root>` and returns `1`. `worker_ledger.py:195-200` is an `os.lstat` plus `stat.S_ISREG`, `:203-220` never calls `inspect_project`, and the launch-only health guard is `worker_launch.py:497-503`. The phrase "healthy managed state" appears nowhere in the v3 drafted text. The wording note is at `design.md:139-146`; the recorded limitation at `design.md:203-208`. |
| `L2-v2` (low) the gate omits two steps of `make check` | Both steps added to step 6 and `R12` | **Yes.** `Makefile:75-76` makes `check` depend on `test` plus nine targets with recipe `sh -n bin/brichan`, and `Makefile:24-28` makes `test` run the `metrics/test_validate_metrics.py` unittest before the three suites. `plan.md:112-131` and `requirements.md:50` now enumerate the three suites, the same nine targets, `sh -n bin/brichan`, and the metrics unittest — step-for-step equivalent, nothing left over on either side. I measured both added steps green on both interpreters (`sh -n bin/brichan` exit `0`; metrics unittest 10 tests `OK` under 3.10 and 3.14). |
| `L3-v2` (low) `techstack-eval` cannot move to 3.14 via `PYTHON=` | Direct 3.14 invocation substituted in step 6 and `R12` | **Yes, and the prescribed command works.** `Makefile:39-40` hardcodes `python3`. `plan.md:126-130` substitutes `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 -m unittest evals.techstack_context_v1.test_cases`; I ran exactly that: 56 tests, `OK`. The second substitution (the metrics unittest under 3.14) also runs: 10 tests, `OK`. `sh -n bin/brichan` is correctly called interpreter-independent. |
| `L4-v2` (low) `plan.md` recorded both 39 and 38 for one baseline | One measurement recorded, with its ownership distribution | **Yes.** `plan.md:149-159` and `:216` both record `39`, and the Uncertainty note at `:222-224` explains the `38` as a transient rather than restating it as a measurement — so nothing in the live file contradicts anything else in it (`DOSSIER-004`). Measured here: `Invalid task dossiers: 39 issue(s) across 8 dossier(s).`, script exit `1`, `make dossiers` exit `2`, ownership `index.md` 28 / `code-review.md` 5 / `pr-desc.md` 5 / `plan-review.md` 1 — the plan's distribution exactly. The archived `versions/v2/plan.md` is untouched (`DOSSIER-003`). |
| v2 test gap 3 (optional): placement pin raises `ValueError` instead of failing legibly | Adopted; assertion 4 opens with `assertIn` | **Yes, and it works.** `design.md:203-213`. I deleted the section from the scratch copy and the test failed with `AssertionError: '## Worker ledger' not found in ...`, not `ValueError`. |
| v2 test gaps 1, 2, 4 (no action) | Recorded as limitations / covered indirectly | **Yes.** Gap 1 at `design.md:203-208`, gap 2 at `design.md:199-203`, gap 4 covered by the occurrence count, which I mutation-tested below. |
| v2 residual risks (legacy launches; manifest-hash churn; worktree-specific expected-red list; WLG-001 provenance) | Carried forward unchanged | **Yes.** `design.md:147-152`, `design.md:243-250`, `plan.md:205-209`, `requirements.md:79`. The re-measure warning is stated as the review asked. |

## Findings

### `L1-v3` (low) — `R5` claims to enumerate every `finish` refusal and omits four, including the one `R4` documents

`requirements.md:43` (`R5`):

> The packaged text states every finish refusal the shipped CLI enforces, each
> with exit `1` and nothing written: a worker name without the `brichan-`
> prefix, an empty or whitespace-only evidence item, a `--launch-id` that
> matches no `launched` record, and a `--launch-id` that already has a
> `finished` record.

The colon makes the four-item list the definition of "every refusal the
shipped CLI enforces". It is not exhaustive. The installed `finish` enforces
four more refusals, all exit `1` with nothing written, all of which I
reproduced against the shipped entry point:

| Reproduced invocation | Message | Exit |
| --- | --- | --- |
| `--project` naming a Git root with no regular `.brichan/manifest.json` | `no ledger for this target: <root>` | `1` |
| `--project` naming a path that is not a directory | `target project is not a directory: <path>` | `1` |
| `--project` naming a directory that is not a Git repository root | `target project is not a Git repository root: <path>` | `1` |
| `--project` omitted, no Git root above the working directory | `cannot find a Git repository from: <cwd>` | `1` |

The first is `resolve_installed_location`
(`src/brichan/orchestration/worker_ledger.py:203-220`); the other three are
`find_git_root` (`src/brichan/project.py:35-51`), whose `ProjectError` is a
`ValueError` subclass (`src/brichan/project.py:9`) and is therefore caught by
the `except (LedgerError, ValueError, OSError)` arm at
`src/brichan/orchestration/worker_ledger.py:726-730`, which returns `1`.

Two things make this a defect rather than a nitpick. First, `R5` is internally
inconsistent with the artifact it sits in: `R4` (`requirements.md:42`) states
the `no ledger for this target` refusal one row above, so `R5`'s list is
non-exhaustive by the plan's own account. Second, `R5` is a stated acceptance
criterion; a code reviewer measuring the implementation against it will find
refusals the shipped CLI enforces that the packaged text does not state, and
has to decide whether that is a defect or an inaccurate requirement. Closing
it now avoids that round-trip.

This is low, not medium, for three reasons: nothing false ships — the drafted
packaged text at `design.md:109-121` never claims its list is exhaustive, so
unlike `L1-v2` no wrong sentence reaches an installed project; all four
omitted refusals are usage errors on an operator's own `--project` value, with
self-explanatory messages; and the packet's criterion one ("its refusals") is
satisfied in substance, since the four `R5` names plus the `R4` one are the
refusals that bound attestation integrity, which is what that criterion is
for.

Required change, whichever the coordinator prefers: narrow `R5`'s quantifier
to the refusals it actually enumerates (for example "states the finish
refusals that bound attestation integrity", leaving `R4`'s resolution refusal
where it is), **or** add one clause to `R5` and to the drafted `--project`
paragraph covering the three `find_git_root` refusals. The first is the
smaller change and loses nothing an installed coordinator needs; the second
would make the packaged text a superset of the checkout text on this point,
which `PACKAGED-001` permits but no marker would pin.

### `L2-v3` (low) — `options.md`'s version note misdescribes its own diff

`options.md:24-32` states:

> This version exists so the plan version 3 artifact set carries one
> consistent authoring session and origin; the metadata above is the only
> change.

It is not. Diffing `versions/v2/options.md` against the live file shows two
Evidence bullets rewritten as well (`options.md:113-114`): the plan-review
pointer moves from "version 1, finding M1 and its 'Required change'" to
"version 2 ... and its version 1 (at `versions/v1/plan-review.md`), finding
M1", and "re-verified in this planning session" gains "on 2026-09-25". Both
edits are improvements — they keep the evidence pointing at the live review —
but the version note says they did not happen.

This is bookkeeping, not a risk to the implementation: no requirement, step,
or drafted byte depends on it, and the substantive claim ("the option set, the
selection, and both sub-decisions are unchanged") is true — I diffed it. It is
reported because a version note is the audit record a later session trusts
instead of re-diffing, and `projects/` artifacts are held to accuracy rather
than to approximation.

Required change: replace "the metadata above is the only change" with
something true, for example "the metadata above and two Evidence pointers are
the only changes".

## Verification performed

Nothing below was accepted from the plan; each item was re-derived in this
worktree. Unless stated otherwise the command prefix was
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src` and the interpreter was the shell
`python3` (3.10.11).

The real parity suite against the version 3 drafted text — not a simulation.
Because this task may write only one file, I copied both skill trees and the
parity contract into a scratch directory outside the repository, applied the
version 3 drafted text exactly as `design.md:96-125` specifies it (launch
paragraph after the paragraph ending "Close only a recorded Brichan-owned pane
with `herdr pane close <pane-id>`."; `## Worker ledger` immediately before
`## Recover a swallowed Enter`), appended the thirteen markers and the new
test as `design.md:157-213` specifies, and ran the module. No repository file
was modified; `git status --short` is empty.

- **17 tests, `OK`**, on both 3.10 and 3.14. That is every existing assertion
  plus the new one.
- Headings in the edited packaged file land at lines 1 (`# Herdr commands`),
  71 (`## Worker ledger`) and 114 (`## Recover a swallowed Enter`), so the
  observation surface and the six "Safeguards that apply to every observation"
  bullets stay at lines 25-63 directly under the top-level heading. `R13` and
  the `M1` fix hold.
- Every one of the thirteen markers is a genuine new guard, counted
  mechanically: occurrences in the packaged tree go `0` before the edit to `1`
  after, and all thirteen are already present in the checkout tree. So both
  `test_the_checkout_skill_states_every_safeguard` and
  `test_the_packaged_skill_states_every_safeguard` pass, and neither marker
  was already satisfied for an unrelated reason (`R10`).
- `--ledger-file` occurrences in the packaged tree: `0` before, exactly `1`
  after, inside the rejection sentence; `projects/<slug>/ledger/workers.jsonl`
  is absent (`R8`).
- **Mutation-tested, satisfying `TEST-003`** — each of the three guarded
  properties fails when broken, and none of these assertions can pass
  vacuously:
  - Section moved above the safeguards → `AssertionError: 3799 not less than
    927`.
  - Section deleted → `AssertionError: '## Worker ledger' not found in ...`,
    which is the `assertIn` legibility guard adopted for v2 test gap 3 working
    as intended rather than a `ValueError`.
  - Affirmative "add `--ledger-file` ..." sentence appended →
    `AssertionError: 1 != 2` on the occurrence count, which is the `R8` guard
    the v1 review asked for working as intended.

CLI fidelity (`R1`-`R7`, packet criterion two) — every claim held. Captured
`--help` from both installed entry points and reproduced each refusal:

- `brichan-herdr-agent-start --help` prints
  `--task TASK  task identifier recorded verbatim in the worker ledger; never inferred when the flag is absent`,
  matching `R1` verbatim (`worker_launch.py:422-428`).
- The installed usage line carries no `--ledger-file`
  (`worker_launch.py:430-441` adds it only under
  `if checkout_root is not None`), and an installed launch passing it fails
  with `error: unrecognized arguments: --ledger-file projects/x/ledger/workers.jsonl`,
  exit `2` (`R2`).
- `brichan-herdr-worker-ledger finish --help` prints exactly
  `[-h] --worker WORKER --launch-id LAUNCH_ID --evidence EVIDENCE [--task TASK] [--pane PANE] [--project PROJECT]`
  — required `--worker`, `--launch-id`, repeatable `--evidence`, optional
  `--task`, `--pane`, `--project`, and no `--ledger-file`
  (`worker_ledger.py:670-692`). `finish --ledger-file` there is
  `error: unrecognized arguments`, exit `2` (`R4`).
- `no ledger for this target` fires on exactly the documented condition,
  reproduced on a Git root lacking `.brichan/manifest.json`: exit `1`
  (`R4`, and the ground for the `L1-v2` closure).
- The `brichan-` prefix refusal (`worker name must begin with brichan-`) and
  the empty-evidence refusal (`every --evidence item must be non-empty`) both
  return `1`, and both run before ledger resolution, so nothing is written
  (`worker_ledger.py:702-716`). The unmatched and already-finished
  `launch_id` refusals are at `:634-637`, after which the append is
  unreachable (`R5`).
- The exit table is right: installed `finish` returns `1` for every refusal
  and reaches `2` only through argparse, so the packaged row "Invalid
  invocation" — without the checkout's "including a rejected `--ledger-file`
  value" — is correct (`design.md:129-137`).
- `ledger: launch_id=<uuid>` goes to stderr with stdout reserved for the
  verbatim `agent_started` envelope, and
  `warning: worker started but ledger write failed: <reason>` leaves the exit
  code `0` (`worker_launch.py:679-704`). `--json` implies `--dry-run` per its
  own help text, and the ledger block sits after the rollback scope closes,
  so "a launch that rolls back appends nothing" and "`--dry-run` and `--json`
  write nothing" both hold (`R3`).
- The first-`finished`-record-wins tie-break is the code's own documented
  behavior (`worker_ledger.py:444-453`) (`R6`).

Contract and manifest surface (`R9`, `R11`) — no edit needed anywhere else:

- `IMMUTABLE_PATHS` already lists
  `skills/herdr-orchestration/references/commands.md`
  (`src/brichan/lifecycle.py:29-40`), so the inventory does not change and
  `PACKAGED-002` is not triggered; `intended_manifest()` hashes resource bytes
  at runtime (`:142-153`).
- No contract pins the changed file's bytes or size. Searching the whole test
  tree for a size, digest or byte assertion against `dogfood_v1` returns
  nothing. `tests/contract/test_packaging_metadata.py:62-72` reads each
  immutable resource only to assert it is non-empty and UTF-8 decodable;
  `:155-170` asserts sdist membership by path suffix.
  `tests/contract/test_dogfood_policy_contract.py` does not reference the file
  at all.
- `config/repository-paths.json:991-994` sources its only `commands.md` entry
  from the *checkout* file, so the packaged edit cannot move `path-check`.
- The three focused contracts are green today, before any edit:
  `test_skill_parity_contract`, `test_dogfood_policy_contract`,
  `test_packaging_metadata` — 42 tests, `OK`.

The completion gate, measured on both interpreters. This closes the
measurement gap both earlier reviews recorded: every step of step 6 was run
under the 3.10 shell interpreter and again under
`/opt/homebrew/bin/python3.14` (via `PYTHON=` for the make targets, directly
for the two that do not honor it). The expected-red list holds identically on
both, and nothing outside it failed on either.

| Step | 3.10 | 3.14 |
| --- | --- | --- |
| `test-unit` | 1026 tests, `OK` | 1026 tests, `OK` |
| `test-contract` | 148 tests, 2 failures, 1 skipped | 148 tests, 2 failures, 1 skipped |
| `test-integration` | 222 tests, 1 failure | 222 tests, 1 failure |
| `techstack-eval` | exit `0` | 56 tests, `OK` (direct invocation) |
| `metrics`, `receipts`, `memory-check`, `readme-check`, `phase5-preflight`, `package-check` | all exit `0` | all exit `0` |
| `path-check` | exit `2` | exit `2` |
| `dossiers` | exit `2` (script exit `1`, 39 issues before this artifact was written, 38 after) | exit `2` |
| `sh -n bin/brichan` | exit `0` | interpreter-independent, run once |
| `metrics/test_validate_metrics.py` | 10 tests, `OK` | 10 tests, `OK` (direct invocation) |

Both `test-contract` failures are
`tests/contract/test_repository_paths.py::test_current_path_and_link_contracts_pass`
and `::test_every_non_ephemeral_root_file_is_classified`, both
`unclassified root files: .git`, on both interpreters. `make path-check`
shares that one cause. These are the two known worktree-only failures plus
their target; reported, not fixed, as instructed. The single
`test-integration` failure is
`test_task_dossier_workflow.test_repository_checkout_validates_clean`, whose
output is this in-flight dossier's own 39 diagnostics, every one owned by a
pending coordinator- or reviewer-owned WFS-A-204 artifact.

Scope and completeness of the planned change. The plan neither misses a
necessary change nor adds an unnecessary one. The checkout tree needs no edit,
because all thirteen markers already hold there — verified by count, not
assumed — and `PACKAGED-001` permits the checkout export to be a mode-specific
superset. The packaged `SKILL.md` exclusion (`options.md:96-104`) is sound.
The two files the plan touches are both inside the declared scope paths, and
the plan's "no path outside the declared scope paths" statement
(`plan.md:82-90`) is correct.

## Test gaps

1. **Nothing guards `R5`'s refusal list against the `L1-v3` gap, and nothing
   can cheaply.** Unchanged in kind from v2 test gap 1: the contract layer
   pins marker strings, not the correspondence between a documented refusal
   set and the shipped code's refusal set. The fix is the requirement
   correction (see `L1-v3`), not an assertion.
2. **The markers are asserted on concatenated tree text.** Carried from both
   earlier reviews and correctly recorded at `design.md:199-203`. Prose moved
   between packaged `.md` files would still pass. Acceptable because
   `IMMUTABLE_PATHS` fixes the packaged file set and the new placement pin is
   per-file. No action.
3. **The placement pin is now legible but still coarse.** It asserts
   `safeguards < ledger < recovery` on offsets, which catches reordering and
   deletion — I verified both — but not a section moved into a different
   packaged `.md` file, which gap 2 already covers. No action.
4. **No test distinguishes the installed exit-`2` table row from the checkout
   one.** Covered indirectly by the exactly-once occurrence count, which I
   mutation-tested. No action.

## Residual risks and required human decisions

- **Installed legacy launches stay undocumented.** Carried forward unchanged
  and still accurate: the drafted text is true for routed launches, the legacy
  `--` path can still print
  `ledger: no ledger location for this launch; not recorded`, and the packaged
  file documents no legacy launch, so nothing in it is false.
  `design.md:147-152` records the omission with its reason. No acceptance
  criterion requires the extra sentence.
- **Manifest-hash churn on an immutable resource.** `design.md:243-250` states
  it correctly and I found no contract that needs editing. A target
  initialized from an older build of the same `package_version` would inspect
  as `MALFORMED` against a locally rebuilt package. Release-process handled;
  no action in this task.
- **The expected-red list stays worktree-specific and dossier-specific.** It
  is sound here and I re-measured every entry on both interpreters, but on the
  main checkout with a closed dossier all of it must be green, as
  `client-follow-up-questions.md` and `plan.md:205-209` both say. The dossier
  half will also shift as the coordinator fills `index.md`, `code-review.md`
  and `pr-desc.md` and as this review lands: the `plan-review.md` diagnostic
  ("review must reference the exact accepted plan version '3', found '2'")
  clears with this artifact: measured again after writing this file, the
  validator reports `38 issue(s) across 8 dossier(s).`, owned `index.md` 28 /
  `code-review.md` 5 / `pr-desc.md` 5 and none by `plan-review.md`. So the
  implementation should expect **38**, not 39, unless another artifact changes
  first. The plan's ownership rule, not the count, is the acceptance test —
  and that rule is what makes this safe.
- **`plan.md` records `Plan status: draft`.** Correct for a version awaiting
  review, but the `--require-complete` gate needs `accepted`, and the
  validator already reads the live plan version as `3`. Coordinator action
  after this verdict, not a plan defect.
- **Provenance of the originating residual risk could not be re-read at
  source.** `projects/brida-worker-ledger/handoffs/WLG-001/code-review.md` is
  not present in this worktree, as `requirements.md:79` records. The gap it
  describes was verified directly against the packaged tree, so no requirement
  depends on it.
- **No decision is required from the user.** Both findings are
  coordinator-level calls on planner-owned wording.

## Claim or decision

Plan `WFS-A-204-PLAN-001` version 3 is `CHANGES REQUIRED` on two low findings.
Every version 2 finding is genuinely closed, and each closure was re-derived by
execution rather than accepted: the corrected `--project` sentence matches the
refusal I reproduced, the gate is now step-for-step equivalent to `make check`,
the prescribed direct 3.14 eval invocation runs green, and the single recorded
baseline matches my measurement down to its ownership distribution. Following
the plan would satisfy all four packet acceptance criteria: the drafted text
states every required element and claims no refusal the CLI does not enforce,
every command and flag matches captured `--help` output, the real parity suite
passes over the drafted text on both interpreters with all thirteen markers
newly guarded and three mutations correctly red, and the gate is green apart
from the ratified expected-red list, which I measured on both interpreters.
What remains is one overstated quantifier in `R5` — inconsistent with `R4` one
row above it and with four refusals I reproduced — and one version note in
`options.md` that misdescribes its own diff. Both are one-clause corrections
to planner artifacts; neither reaches an installed project, and no finding
touches the selected option, the drafted section, the marker set, the
placement, or the completion gate.

## Evidence

- `src/brichan/orchestration/worker_ledger.py:195-200` (`_state_manifest_is_regular` is an `os.lstat` of `.brichan/manifest.json` plus `stat.S_ISREG`) and `:203-220` (`resolve_installed_location` refuses `no ledger for this target` on that check alone and never calls `inspect_project`), versus the launch-only health guard at `src/brichan/orchestration/worker_launch.py:497-503`, confirm the `L1-v2` closure at `design.md:109-114` and `requirements.md:42`; reproduced by running `finish --project` against a Git root without `.brichan/manifest.json` (exit `1`, message verbatim).
- `src/brichan/project.py:9,35-51` and `src/brichan/orchestration/worker_ledger.py:726-730` prove the four exit-`1` refusals `R5` (`requirements.md:43`) omits while claiming to state "every finish refusal the shipped CLI enforces" — one of them the refusal `R4` (`requirements.md:42`) documents one row above; all four reproduced against the shipped entry point (finding `L1-v3`).
- `diff versions/v2/options.md options.md` shows two Evidence bullets rewritten at `options.md:113-114` in addition to the metadata, contradicting the version note's "the metadata above is the only change" at `options.md:31` (finding `L2-v3`).
- `Makefile:75-76` (`check` = `test` plus nine targets, recipe `sh -n bin/brichan`), `:24-28` (`test` runs the `metrics/test_validate_metrics.py` unittest first), `:42-44` (`metrics` runs a different file) and `:39-40` (`techstack-eval` hardcodes `python3`) confirm the `L2-v2` and `L3-v2` closures at `plan.md:112-131` and `requirements.md:50` are step-for-step equivalent to `make check`; both added steps and the prescribed direct 3.14 eval invocation measured green (`sh -n bin/brichan` exit `0`; metrics unittest 10 tests `OK`; eval 56 tests `OK`).
- The real parity suite run against a scratch copy carrying the version 3 drafted text and the proposed contract extension: 17 tests `OK` under both 3.10 and 3.14; packaged headings at lines 1, 71, 114 with the observation safeguards at 25-63 under the top-level heading; all thirteen markers `0`→`1` in the packaged tree and already `1` in the checkout tree; `--ledger-file` count `0`→exactly `1`; and three mutations each failing as intended (section moved: `3799 not less than 927`; section deleted: `'## Worker ledger' not found`; affirmative flag sentence added: `1 != 2`) — confirming `R8`, `R10`, `R13` and `TEST-003`.
- Captured installed `--help` for both entry points plus reproduced refusals confirm every literal in `R1`-`R7`: the `--task` help text verbatim; the installed usage line with no `--ledger-file` and its `unrecognized arguments` exit `2`; `finish` usage `[-h] --worker WORKER --launch-id LAUNCH_ID --evidence EVIDENCE [--task TASK] [--pane PANE] [--project PROJECT]`; `worker name must begin with brichan-` and `every --evidence item must be non-empty` each exit `1` before ledger resolution (`worker_ledger.py:702-716`); the unmatched and already-finished checks at `:634-637`; the tie-break at `:444-453`; and `worker_launch.py:679-704` for the stderr `launch_id` line and the warning that leaves exit `0`.
- `src/brichan/lifecycle.py:29-40,142-153`, `tests/contract/test_packaging_metadata.py:62-72,155-170`, and `config/repository-paths.json:991-994` carry paths and runtime-computed hashes only, with no byte or size pin on the changed file anywhere in `tests/`, confirming `R9` and `R11`; the three focused contracts pass today (42 tests, `OK`).
- Completion gate measured on both interpreters: `test-unit` 1026 tests `OK` on 3.10 and 3.14; `test-contract` 148 tests with the same 2 `unclassified root files: .git` failures on both; `test-integration` 222 tests with the same single `test_task_dossier_workflow` failure on both; `metrics`, `receipts`, `memory-check`, `readme-check`, `phase5-preflight`, `package-check` exit `0` on both; `path-check` and `dossiers` exit `2` on both; `scripts/validate_task_dossiers.py projects` exit `1` with `39 issue(s) across 8 dossier(s).` owned `index.md` 28 / `code-review.md` 5 / `pr-desc.md` 5 / `plan-review.md` 1 — confirming the `L4-v2` closure and the whole expected-red list; re-measured after this artifact was written, the script reports `38 issue(s) across 8 dossier(s).` with no diagnostic owned by `plan-review.md`.
- `git status --short` is empty: the parity simulation ran on a scratch copy outside the repository, so no repository file was modified by this review.

## Uncertainty

- The two `tests/contract/test_repository_paths.py` failures and `make path-check` share one cause I did not attempt to fix, as instructed: this detached worktree's `.git` is a file, so the root-file scan reports it as unclassified. They are worktree-only and are reported, not diagnosed.
- The parity verification ran the real contract module against a faithful scratch copy of both skill trees, not against a modified worktree, because this task may write only one file. The copy is byte-identical to the trees plus the specified edit, and the module computes its own tree text, so the result is the suite's real behavior on the edited content — but the implementation must still run plan step 5 in place and report the real result, and a transcription that differs from `design.md`'s drafted text in any marker-bearing phrase could still fail.
- My `L1-v3` reproduction used a temporary directory and a non-Git path rather than a real `brichan init` target, because initializing one is outside this task's scope. Since any project `brichan init` touches is a Git root by construction (`project_paths` resolves through `find_git_root`), the three `find_git_root` refusals cannot fire on a legitimately initialized target — which is exactly why the finding is low rather than medium.
- I did not re-verify every line number the planner artifacts cite, only those load-bearing for a finding or a closure; the ones I checked were accurate.
- No other unresolved uncertainty remains about the reviewed plan.
