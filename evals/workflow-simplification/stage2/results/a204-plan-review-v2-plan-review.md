# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `WFS-A-204`
- Task level: `1`
- Artifact: `plan-review`
- Artifact version: `2`
- Origin: `packet:WFS-A-204-PLAN-REVIEW@2026-09-25#attempt-plan-review-2`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `6b5efc0a-4bf7-43ae-904f-4e26da67deaa`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `6b5efc0a-4bf7-43ae-904f-4e26da67deaa`
- Review verdict: `CHANGES REQUIRED`

## Review target

- Reviewed plan ID: `WFS-A-204-PLAN-001`
- Reviewed plan version: `2`

Artifacts reviewed: `requirements.md` v2, `brief.md` v2, `options.md` v2,
`design.md` v2, `plan.md` v2, against `request.md` v1 and the
coordinator-owned `client-follow-up-questions.md` v2. Version 1 of this
artifact is preserved unmodified at `versions/v1/plan-review.md`; this is
version 2 of the same artifact and replaces it as the live review.

This reviewing session (`6b5efc0a-4bf7-43ae-904f-4e26da67deaa`) authored none
of them; the planner session is `6b5e7d82-9bdc-4a2e-824c-fb3b11060427` and the
version 1 reviewing session was `dead92d1-3d47-4d40-a165-fddf72ffe97c`. The
two identifiers are a deterministic consistency signal, not proof that two
sessions existed.

## Techstack scope

- Snapshot pointer: `projects/brida-workflow-simplification/handoffs/WFS-A-204/snapshots/attempt-plan-review-2-364e46759bb4ee7b8b38dba7631cf2eb570569051166385a47367f27fa8d0db3.snapshot.json`
- Snapshot SHA-256: `364e46759bb4ee7b8b38dba7631cf2eb570569051166385a47367f27fa8d0db3`
- Verified `status: match` before any review work, and all eight required
  selected rule files were read in this session. No path outside the declared
  scope paths was needed, and no new Context ID, chain, conflict, or exception
  need was discovered.

## Verdict

`CHANGES REQUIRED`, on four low findings. No medium, high, or critical defect
remains.

Version 2 closes every version 1 finding, and each closure was re-verified
here rather than accepted: the `## Worker ledger` placement now leaves the
packaged monitoring safeguards directly under the top-level heading, the
strengthened `--ledger-file` occurrence count and the new placement pin both
hold against a simulated edit, and the two baseline corrections match what I
re-measured. Every CLI literal in `requirements.md` `R1`-`R7` and in the
drafted packaged text was re-derived from the parser source and from captured
`--help` output of both installed entry points; all held.

What blocks acceptance is small and local. One sentence of the drafted
packaged text states a `finish` refusal broader than the shipped code enforces
(`L1-v2`), and that sentence ships into every installed project. The ratified
completion gate the plan transcribes is not equivalent to `make check`: two of
its steps are never run (`L2-v2`), and one of its targets cannot be moved to
Python 3.14 the way step 6 says (`L3-v2`). One recorded baseline number
contradicts another in the same file (`L4-v2`). All four are one-line
corrections to `requirements.md`, `design.md`, and `plan.md`. Nothing here
touches the selected option, the contract extension, or the placement fix.

## Findings closure check against version 1

Checked row by row against `versions/v1/plan-review.md`. The table at
`plan.md:41-51` is accurate and complete; every claimed closure was verified
independently.

| Version 1 item | Claimed closure | Verified |
| --- | --- | --- |
| `M1` (medium) placement nests the monitoring safeguards | Section moved to immediately before `## Recover a swallowed Enter`; pinned by `R13` | **Yes.** Simulating the version 2 edit yields headings at lines 1 (`# Herdr commands`), 71 (`## Worker ledger`) and 112 (`## Recover a swallowed Enter`); the observation surface and the six "Safeguards that apply to every observation" bullets stay at lines 25-63, directly under the top-level heading. The variant choice is recorded at `options.md:75-87` and `design.md:52-67`. |
| `L1` (low) dossier-baseline rule misfires on `index.md` comparison rows | Rule restated in ownership terms (path before the first colon) plus the scanned-count note | **Yes.** `plan.md:119-127` and `R12` state exactly that, and my measurement confirms the rule now classifies the real output correctly. |
| `L2` (low) `make dossiers` exit code recorded as `1` | Recorded as make exit `2`, script exit `1` | **Yes.** Re-measured: `scripts/validate_task_dossiers.py projects` exits `1`, `make dossiers` exits `2`. |
| Test gap 1: `R8` guard accepts other affirmative phrasings | Replaced by an exactly-once occurrence count | **Yes.** `design.md:179-184`, `R8` at `requirements.md:44`; the count holds at `1` against the simulated edit. |
| Test gap 2: third assertion near-tautological | Removed, superseded by the count | **Yes.** |
| Test gap 3 (optional): nothing pins the placement | Adopted as a per-file placement assertion | **Yes.** `design.md:185-194`; `safeguards < ledger < recovery` holds on the simulated file and fails if the section is moved above the safeguards. |
| Test gap 4: markers asserted on concatenated tree text | Recorded as a known limitation, no action | **Yes.** `design.md:196-201`. |
| Residual risk: widened fourth acceptance criterion needs ratification | Ratified by the coordinator | **Partly.** `client-follow-up-questions.md:26` does ratify an explicit gate, which closes the authorization question. It does not make that gate equivalent to `make check` — see `L2-v2`. |
| Residual risk: installed legacy launches stay undocumented | No change, accepted | **Yes.** Correctly carried forward; still accurate, since a routed installed launch always resolves the fixed location. |

Two version 1 residual risks are absent from the closure table because they
required no action, and both are still carried in the artifacts: the
manifest-hash churn at `design.md:218-225`, and the WLG-001 provenance caveat
at `requirements.md:74`. No closure claim in the table is overstated.

## Findings

### `L1-v2` (low) — the drafted packaged text states a `finish` refusal the shipped CLI does not enforce

`design.md:104-107` drafts, for transcription into the packaged skill:

> `--project` names the target project root; when it is omitted, the Git root
> is discovered upward from the working directory. The target must hold healthy
> managed state, or the command refuses with `no ledger for this target` and
> exit `1`.

`requirements.md:40` (`R4`) states the same: "the target must hold healthy
managed state".

The shipped guard is narrower. `resolve_installed_location`
(`src/brichan/orchestration/worker_ledger.py:203-221`) resolves the root and
then calls `_state_manifest_is_regular` (`:195-201`), whose whole body is an
`os.lstat` of `.brichan/manifest.json` plus `stat.S_ISREG`. It never calls
`inspect_project` and never consults `StateKind`. A target whose
`.brichan/manifest.json` exists but is `MALFORMED` or `INCOMPATIBLE` therefore
passes, and `finish` proceeds to append a `finished` record. The asymmetry is
deliberate elsewhere in the same feature: a routed *launch* does require
health — `src/brichan/orchestration/worker_launch.py:495-503` raises
`RoutingError` when `inspection.kind is not StateKind.HEALTHY` — so an
installed coordinator reading the drafted sentence would reasonably conclude
`finish` carries the guard the launcher carries. It does not.

This matters because packet acceptance criterion one requires the packaged
text to state the installed `finish` refusals, and criterion two requires the
new text to match the shipped CLI. The sentence ships verbatim into every
project `brichan init` touches, and `plan.md:177-180` tells the implementer the
work is "transcription plus verification, not research", so a conforming
implementer will ship it.

Required change: replace "must hold healthy managed state" with the condition
the code enforces — the target must be an initialized Brichan project, that
is, hold a regular `.brichan/manifest.json` — in `design.md:104-107` and in
`R4`. Checking the health of a target before attesting stays a coordinator
responsibility and can be said as such, but not as a refusal.

### `L2-v2` (low) — the completion gate the plan runs is not equivalent to `make check`, and the plan claims it satisfies that criterion

The packet's fourth acceptance criterion and `GENERAL-001`
(`techstacks/general.md`) both name `make check`. `plan.md:105-111` and `R12`
(`requirements.md:48`) instead enumerate `make test-unit`, `make test-contract`,
`make test-integration`, then `techstack-eval`, `metrics`, `receipts`,
`dossiers`, `memory-check`, `path-check`, `readme-check`, `phase5-preflight`,
`package-check` individually, and `plan.md:153` maps that enumeration onto the
criterion in the traceability table. The enumeration is a strict subset of
`make check`:

- `Makefile:75-76`: `check` depends on `test` plus the nine targets, and its
  own recipe body is `sh -n bin/brichan`. Nothing in the plan runs it.
- `Makefile:24-28`: `test` runs
  `PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest metrics/test_validate_metrics.py -v`
  *before* delegating to the three suites. That is not `make metrics`, which
  runs `metrics/validate_metrics.py` twice (`Makefile:42-44`). Running the
  three suites individually skips it.

So two steps of `make check` are never executed by the plan's gate, while the
plan records the criterion as covered. Both pass today — I measured
`sh -n bin/brichan` exit `0` and the metrics unittest at 10 tests, `OK` — and
neither is plausibly affected by a documentation-plus-contract change, which is
why this is low rather than medium. But the equivalence claim is the plan's,
not the coordinator's: `client-follow-up-questions.md:26` ratifies a list of
targets, and `plan.md:153` is where that list is asserted to satisfy the
packet.

Required change: add `sh -n bin/brichan` and the
`metrics/test_validate_metrics.py` unittest to step 6 and `R12`, or run
`make check` once and report its known-red targets from the ratified list.

### `L3-v2` (low) — `techstack-eval` cannot be moved to Python 3.14 the way step 6 specifies

`plan.md:110-111` and `R12` run the whole target list "on the 3.10 shell
interpreter and again with `PYTHON=/opt/homebrew/bin/python3.14`", and
`techstack-eval` is in that list. `Makefile:39-40` hardcodes the interpreter:

```
techstack-eval:
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest evals.techstack_context_v1.test_cases -v
```

`PYTHON=` has no effect there, so the "3.14" run re-runs the eval on 3.10 — the
shell `python3` is 3.10.11 in this environment — and records it as a 3.14 pass.
This is not an incidental discovery: the selected rule
`techstacks/python/tests.md`, Verification, states it outright — "The eval is
run directly under both interpreters, because its recipe does not follow
`PYTHON=`." The plan acknowledges that Context ID and then specifies a gate
that contradicts it.

Required change: in step 6 and `R12`, invoke the eval directly for the second
interpreter, for example
`PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 -m unittest evals.techstack_context_v1.test_cases`,
rather than through `PYTHON=`.

### `L4-v2` (low) — `plan.md` contradicts its own measured dossier baseline

`plan.md:128` records "39 issues" and `plan.md:187` repeats "exits `1` with 39
issues", while `plan.md:191` records "(38 on 2026-09-25, after the version 2
planner artifacts were written)" for the same measurement of the same state.

Measured here before this artifact was written:
`PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py projects`
reports `Invalid task dossiers: 39 issue(s) across 8 dossier(s).` and exits
`1`. Ownership, by the path preceding the first colon: `index.md` 28,
`code-review.md` 5, `pr-desc.md` 5, `plan-review.md` 1 — exactly the
distribution `plan.md:128-132` predicts, including the missing-receipt
diagnostic being reported on the `index.md` row
(`index.md: Task identity.Canonical receipt path: canonical receipt does not
exist: ...`). So `39` is right and `38` is the stale figure.

`DOSSIER-003` freezes archived versions, and `DOSSIER-004` requires an evidence
file to be corrected in place rather than left self-contradicting. Required
change: correct `38` to `39` at `plan.md:191`. The plan's own point stands —
the ownership rule, not the count, is the acceptance test — which is why this
is low.

## Verification performed

Nothing below was accepted from the plan; each item was re-derived in this
worktree. Unless stated otherwise the command prefix was
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src`.

CLI fidelity (`R1`-`R7`, packet criterion two) — all claims held:

- `--task` exists on the installed launcher with exactly the help text `R1`
  quotes. `worker_launch.py:422-428`; captured
  `brichan-herdr-agent-start --help` prints
  `--task TASK  task identifier recorded verbatim in the worker ledger; never inferred when the flag is absent`.
- `--ledger-file` is added only under `if checkout_root is not None`
  (`worker_launch.py:430-441`), so the installed usage line is
  `[-h] [--anchor-pane ...] --cwd CWD [--env ENV] [--route ROUTE] [--runtime RUNTIME] [--model MODEL] [--effort EFFORT] [--task TASK] [--dry-run] [--json] name`
  with no `--ledger-file`. Reproduced the rejection: an installed routed launch
  carrying it fails with
  `brichan-herdr-agent-start: error: unrecognized arguments: --ledger-file projects/x/ledger/workers.jsonl`
  and exit `2` (`R2`).
- The fixed installed location has exactly one spelling:
  `installed_location` returns parts `(".brichan", "ledger", "workers.jsonl")`
  from `STATE_DIRECTORY`, `LEDGER_DIRECTORY`, `LEDGER_FILE`
  (`worker_ledger.py:71-76,139-150`), and a routed installed launch always sets
  `ledger=installed_location(paths.project_root)` after refusing a non-`HEALTHY`
  target (`worker_launch.py:495-523`). The design's deliberate omission of the
  checkout-only "no ledger location" note (`design.md:133-137`) is therefore
  correct for the packaged file's scope.
- `ledger: launch_id=<uuid>` goes to stderr with stdout reserved for the
  verbatim `agent_started` envelope, and
  `warning: worker started but ledger write failed: <reason>` leaves the exit
  code `0` — `worker_launch.py:679-704`. `--json` sets `dry_run`
  (`:461-462`) and `--dry-run` returns before the ledger block (`:566-570`), so
  "`--dry-run` and `--json` write nothing" is true (`R3`).
- The installed `finish` parser takes required `--worker`, `--launch-id` and
  repeatable `--evidence`, optional `--task`, `--pane`, `--project`, and does
  not define `--ledger-file` (`worker_ledger.py:670-692`). Captured
  `brichan-herdr-worker-ledger finish --help` prints exactly that usage
  (`R4`). The console-script entry point is
  `brichan-herdr-worker-ledger = "brichan.orchestration.worker_ledger:main"`
  (`pyproject.toml:37`) and `main` always passes `checkout_root=None`
  (`worker_ledger.py:775-783`), so the packaged name and mode are right.
- All four documented refusals exist, each returning `1` and writing nothing:
  the `brichan-` prefix check and the empty-or-whitespace evidence check
  (`worker_ledger.py:700-716`), and the unmatched and already-finished
  `launch_id` checks (`:633-637`). Exit table `0`/`1`/`2` matches `:717-742`
  plus argparse (`R5`).
- "The first `finished` record for a `launch_id` in file order wins" is the
  code's own documented tie-break (`worker_ledger.py:445-453`) (`R6`).

Contract simulation of the version 2 edit (in memory; no repository file was
modified). I applied the drafted launch paragraph after the paragraph ending
"Close only a recorded Brichan-owned pane with `herdr pane close <pane-id>`."
and the drafted `## Worker ledger` section immediately before
`## Recover a swallowed Enter`, then ran every assertion of
`tests/contract/test_skill_parity_contract.py` plus the four proposed ones
against the result. Zero failures:

- All thirteen proposed markers are present in the checkout tree today, absent
  from the packaged tree today, and present in both after the edit — so
  `test_the_checkout_skill_states_every_safeguard` and
  `test_the_packaged_skill_states_every_safeguard` both pass (`R10`). This
  includes the two markers whose backtick handling could have gone either way:
  "`` `--task <TASK-ID>` ``" matches in both trees with the backticks, and
  "--project <absolute-target-project>" matches the backticked checkout prose
  at `.agents/skills/herdr-orchestration/references/commands.md:94` and the
  unbackticked packaged code block alike.
- `assertIn("rejects the flag `--ledger-file`", packaged)` holds;
  `assertNotIn("projects/<slug>/ledger/workers.jsonl", packaged)` holds;
  `packaged.count("--ledger-file")` is exactly `1`, versus `0` today (`R8`).
- The placement pin holds on the packaged `references/commands.md` read as its
  own file: `Safeguards that apply to every observation` at offset 1793,
  `## Worker ledger` at 2795, `## Recover a swallowed Enter` at 4604.
- No existing negative assertion is tripped: none of "always send Enter",
  "send Enter automatically", "automatically send", "auto-answer", the four
  overbroad input-prohibition phrasings, or the retired `0.7.3` verified-set
  spellings appears in the edited packaged tree.
- The paste-recovery window assertion
  (`tests/contract/test_skill_parity_contract.py:203-207`) still passes with
  the section placed directly above the recovery flow: `idle`, `unsubmitted`
  and `herdr agent read` all remain inside the 900-character window before the
  `herdr pane send-keys <pane-id> Enter` marker.

Contract and manifest surface (`R9`, `R11`) — no edit needed anywhere else:

- `IMMUTABLE_PATHS` already lists
  `skills/herdr-orchestration/references/commands.md`
  (`src/brichan/lifecycle.py:28-39`), so no inventory changes and
  `PACKAGED-002` is not triggered; `intended_manifest()` hashes resource bytes
  at runtime (`:142-153`).
- No test pins the changed file's bytes or size. Every reference to it is a
  path assertion: `tests/contract/test_skill_parity_contract.py:113-114`,
  `tests/integration/test_installed_dogfood.py:1082`,
  `tests/integration/test_cli_compatibility.py:513`,
  `tests/unit/test_project_lifecycle.py:404,1301`. The installed-dogfood export
  test compares runtime-computed `managed_sha256` against
  `exported_sha256` (`:204,1090`), never a literal. The only frozen-bytes
  contract in the suite covers `tests/fixtures/` under `TEST-002`
  (`tests/contract/test_techstack_policy_contract.py:451-480`), not packaged
  resources.
- `config/repository-paths.json` carries no size or digest field, and its only
  `commands.md` reference entry is sourced from the *checkout* file
  (`:991-994`); `scripts/check_repository_paths.py:87-110` validates
  source/target existence and a needle, so the packaged edit cannot move
  `path-check`.
- Focused contracts green today, before any edit:
  `test_skill_parity_contract`, `test_dogfood_policy_contract`,
  `test_packaging_metadata` — 42 tests, `OK`.

Baseline re-measured independently on 2026-09-25 in this worktree, on the shell
interpreter (Python 3.10.11):

- `make test-unit`: 1026 tests, `OK`.
- `make test-contract`: 148 tests, 2 failures, 1 skipped — both failures in
  `tests/contract/test_repository_paths.py`
  (`test_current_path_and_link_contracts_pass` and
  `test_every_non_ephemeral_root_file_is_classified`), both
  `unclassified root files: .git`. These are the two known worktree-only
  failures; reported, not fixed.
- `make test-integration`: 222 tests, 1 failure —
  `test_task_dossier_workflow.test_repository_checkout_validates_clean`, whose
  output is the in-flight dossier's own 39 diagnostics.
- `make path-check`: exit `2`, `unclassified root files: .git` — same cause.
- `make dossiers`: exit `2`; `scripts/validate_task_dossiers.py projects`:
  exit `1`, 39 issues (finding `L4-v2`).
- Green, exit `0`: `techstack-eval`, `metrics`, `receipts`, `memory-check`,
  `readme-check`, `phase5-preflight`, `package-check`, plus `sh -n bin/brichan`
  and `python3 -m unittest metrics/test_validate_metrics.py` (10 tests, `OK`).

Scope and completeness of the planned change. The plan neither misses a
necessary change nor adds an unnecessary one, with one dependency worth
stating: the checkout tree needs no edit, because all thirteen markers already
hold there (verified) and `PACKAGED-001` permits the checkout export to be a
mode-specific superset. The packaged `SKILL.md` exclusion (`options.md:89-97`)
is sound — `SKILL.md` already routes the reader to
`references/commands.md` — and `R13`'s placement pin, optional in version 1, is
justified here because it is the only thing that makes the `M1` fix survive a
future edit.

## Test gaps

1. **Nothing guards the `L1-v2` sentence.** The proposed markers pin the
   attestation semantics and the refusal list, but no assertion pins the
   *condition* under which `finish` refuses to resolve a ledger. If the
   sentence ships as drafted, no test fails. This is a documentation-accuracy
   gap that the contract layer cannot close cheaply; the fix is to correct the
   sentence (see `L1-v2`), not to add an assertion.
2. **The markers are asserted on concatenated tree text.** Unchanged from
   version 1 test gap 4 and correctly recorded as a known limitation at
   `design.md:196-201`. Prose moved between packaged `.md` files would still
   pass. Acceptable because `IMMUTABLE_PATHS` fixes the packaged file set, and
   the new placement pin is per-file.
3. **The placement pin uses `str.index`, so a missing heading raises rather
   than asserts.** `design.md:185-194` specifies
   `text.index("## Worker ledger")`. If the section were deleted the test
   errors with `ValueError` instead of failing with a readable message. It is
   still red, so `TEST-003` is satisfied; a `assertIn` before the two
   `assertLess` calls would make the failure legible. Optional, no acceptance
   criterion requires it.
4. **No test distinguishes the installed exit-`2` row from the checkout one.**
   The packaged table row says "Invalid invocation" while the checkout row adds
   "including a rejected `--ledger-file` value" (`design.md:129-132`). The
   exactly-once occurrence count makes the checkout wording impossible in the
   packaged tree, so this is covered indirectly. No action.

## Residual risks and required human decisions

- **Installed legacy launches stay undocumented.** Carried forward unchanged
  from version 1 and still accurate: the drafted sentence is true for routed
  launches, the legacy `--` path can still print
  `ledger: no ledger location for this launch; not recorded`
  (`worker_launch.py:680`), and the packaged file documents no legacy launch.
  `design.md:133-137` records the omission with its reason. No acceptance
  criterion requires the extra sentence; a coordinator may add it later.
- **Manifest-hash churn on an immutable resource.** `design.md:218-225` states
  it correctly and I found no contract that needs editing. A target initialized
  from an older build of the same `package_version` would inspect as
  `MALFORMED` against a locally rebuilt package. Release-process handled; no
  action in this task.
- **The ratified expected-red list is worktree-specific.** It is sound here and
  I re-measured every entry, but `client-follow-up-questions.md:35` is right
  that on the main checkout with a closed dossier all of it must be green. A
  later session that inherits the list without re-measuring would absorb real
  failures. The plan's ownership rule mitigates this for the dossier half only.
- **Provenance of the originating residual risk could not be re-read at
  source.** `projects/brida-worker-ledger/handoffs/WLG-001/code-review.md` is
  not present in this worktree, as `requirements.md:74` already records. The
  gap it describes was verified directly against the packaged tree, so no
  requirement depends on it.
- **No decision is required from the user.** All four findings are
  coordinator-level calls, and `L2-v2` additionally touches the coordinator's
  own ratified gate rather than only the plan.

## Claim or decision

Plan `WFS-A-204-PLAN-001` version 2 is `CHANGES REQUIRED` on four low findings.
Every version 1 finding is genuinely closed, and each closure was re-verified
rather than accepted: the placement fix leaves the packaged monitoring
safeguards under the top-level heading, the strengthened `R8` guard and the new
placement pin both hold against a simulated edit, and the corrected baseline
matches what I measured. Following the plan would satisfy packet acceptance
criteria one and three, and criterion two except for the one sentence in
`L1-v2`; criterion four is met in substance but not as stated, because the
ratified gate omits two steps of `make check` (`L2-v2`) and cannot move
`techstack-eval` to Python 3.14 through `PYTHON=` (`L3-v2`). The revision is
three sentences in `requirements.md`, `design.md`, and `plan.md` plus one
number at `plan.md:191`; no finding touches the selected option, the drafted
section as a whole, the marker set, or the placement decision.

## Evidence

- `src/brichan/orchestration/worker_ledger.py:195-221` shows `finish` resolves the installed ledger behind `_state_manifest_is_regular` — an `os.lstat` plus `stat.S_ISREG` of `.brichan/manifest.json` — while `src/brichan/orchestration/worker_launch.py:495-503` refuses a launch whose `inspection.kind is not StateKind.HEALTHY`; the drafted sentence at `design.md:104-107` and `R4` (`requirements.md:40`) claim the launcher's guard for `finish` (finding `L1-v2`).
- `Makefile:75-76` (`check` depends on `test` plus nine targets and runs `sh -n bin/brichan`), `Makefile:24-28` (`test` additionally runs `metrics/test_validate_metrics.py`), and `Makefile:42-44` (`metrics` runs `validate_metrics.py`, a different file) versus the enumeration at `plan.md:105-111` and `requirements.md:48`, which `plan.md:153` maps onto the packet's fourth criterion (finding `L2-v2`). Both omitted steps measured green here: `sh -n bin/brichan` exit `0`, metrics unittest 10 tests `OK`.
- `Makefile:39-40` hardcodes `python3` for `techstack-eval`, and `techstacks/python/tests.md` Verification states the eval "is run directly under both interpreters, because its recipe does not follow `PYTHON=`"; `plan.md:110-111` nonetheless moves the whole list with `PYTHON=` (finding `L3-v2`). Shell `python3` is 3.10.11.
- `plan.md:128` and `:187` record 39 validator issues while `plan.md:191` records 38; measured `Invalid task dossiers: 39 issue(s) across 8 dossier(s).`, script exit `1`, `make dossiers` exit `2`, ownership `index.md` 28 / `code-review.md` 5 / `pr-desc.md` 5 / `plan-review.md` 1 (finding `L4-v2`, and confirmation that the version 1 `L1` and `L2` closures are correct).
- Simulating the version 2 edit in memory yields packaged `commands.md` headings at lines 1, 71 and 112, leaving the observation surface and the six "Safeguards that apply to every observation" bullets directly under `# Herdr commands`, and passes all thirteen markers in both trees, the four new assertions (`--ledger-file` count exactly `1`; offsets 1793 < 2795 < 4604), every existing negative assertion, and the ±900-character paste-recovery window — closing version 1 findings `M1` and test gaps 1-3.
- `src/brichan/orchestration/worker_launch.py:422-441,461-462,495-523,566-570,679-704`, `src/brichan/orchestration/worker_ledger.py:71-76,139-150,203-221,445-453,633-637,670-692,700-742`, `pyproject.toml:35-37`, and captured `--help` output of both installed entry points plus a reproduced `unrecognized arguments: --ledger-file`, exit `2`, confirm every CLI literal in `R1`-`R7` and in the drafted text.
- `src/brichan/lifecycle.py:28-39,142-153`, `tests/contract/test_skill_parity_contract.py:113-114`, `tests/integration/test_installed_dogfood.py:204,1082,1090`, `tests/integration/test_cli_compatibility.py:513`, `tests/unit/test_project_lifecycle.py:404,1301`, `config/repository-paths.json:991-994` and `scripts/check_repository_paths.py:87-110` carry paths and runtime-computed hashes only, with no byte or size pin on the changed file, confirming `R9` and `R11`.
- Suite baseline re-measured on 2026-09-25: `make test-unit` 1026 tests `OK`; `make test-contract` 148 tests, 2 failures, both `unclassified root files: .git`; `make test-integration` 222 tests, 1 failure (`test_task_dossier_workflow`); `make path-check` exit `2`; `techstack-eval`, `metrics`, `receipts`, `memory-check`, `readme-check`, `phase5-preflight`, `package-check` all exit `0`; focused contracts 42 tests `OK`.

## Uncertainty

- The two `tests/contract/test_repository_paths.py` failures and `make path-check` share one cause I did not attempt to fix, as instructed: this detached worktree's `.git` is a file, so the root-file scan reports it as unclassified. They are worktree-only and are reported, not diagnosed.
- I could not execute the completion gate under Python 3.14, because doing so would tell me only what the 3.10 run already tells me about a documentation change; `L3-v2` is derived from the recipe text and the selected rule, not from a 3.14 run. If a later session measures the gate on 3.14 and sees `techstack-eval` behave differently from what `L3-v2` predicts, that measurement wins.
- Every contract conclusion about the proposed edit comes from an in-memory simulation, because this task may write only this one file. The simulation reproduced `tree_text` and every assertion in the parity suite exactly, but it is not the suite running against a modified worktree; the implementation must still run step 5 and report the real result.
- No other unresolved uncertainty remains about the reviewed plan.
