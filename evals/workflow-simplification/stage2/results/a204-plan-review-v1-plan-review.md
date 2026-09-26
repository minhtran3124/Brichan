# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `WFS-A-204`
- Task level: `1`
- Artifact: `plan-review`
- Artifact version: `1`
- Origin: `packet:WFS-A-204-PLAN-REVIEW@2026-09-25`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `dead92d1-3d47-4d40-a165-fddf72ffe97c`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `dead92d1-3d47-4d40-a165-fddf72ffe97c`
- Review verdict: `CHANGES REQUIRED`

## Review target

- Reviewed plan ID: `WFS-A-204-PLAN-001`
- Reviewed plan version: `1`

Artifacts reviewed: `requirements.md` v1, `brief.md` v1, `options.md` v1,
`design.md` v1, `plan.md` v1. The reviewing session did not author any of them
(planner session `22d40123-6f34-4491-8b8b-4c43e26981dc`).

## Techstack scope

- Snapshot pointer: `projects/brida-workflow-simplification/handoffs/WFS-A-204/snapshots/attempt-plan-review-1-3b5cf1ede21684e0f8d285dbd9d9cee3472602ab964067e9424b7c87d355a7ab.snapshot.json`
- Snapshot SHA-256: `3b5cf1ede21684e0f8d285dbd9d9cee3472602ab964067e9424b7c87d355a7ab`
- Verified `status: match` before any review work; all eight required selected
  rule files were read. No path outside the declared scope paths was needed to
  complete this review, and no new Context ID, chain, conflict, or exception
  need was discovered.

## Verdict

`CHANGES REQUIRED`. The plan is substantively correct: every claim it makes
about the shipped CLI was re-verified against the parser source and live
`--help` output and every one held, the contract analysis is right, the drafted
text satisfies acceptance criteria one, two and four when transcribed, and a
simulation of the edit shows the extended parity contract passing. One medium
defect blocks acceptance: the section-placement instruction, followed literally,
nests the packaged skill's monitoring safeguards under the new `## Worker
ledger` heading. Two low defects in the recorded baseline would make a
conforming implementer stop and diagnose expected state.

## Findings

### M1 (medium) — the ordered placement nests the monitoring safeguards under `## Worker ledger`

`design.md:29-31` and `plan.md:47-54` order the new `## Worker ledger` section
inserted "after the start-command guidance and before the 'Observe workers'
paragraph", stating this "mirrors the checkout ordering (launch, ledger,
monitor)".

That ordering is correct in the checkout file because its ledger section is
bounded by the next heading: `.agents/skills/herdr-orchestration/references/commands.md:72`
opens `## Worker ledger` and `:111` closes it with `## Legacy explicit
commands`. The packaged file has no such boundary. Its only headings are
`src/brichan/resources/dogfood_v1/skills/herdr-orchestration/references/commands.md:1`
(`# Herdr commands`) and `:65` (`## Recover a swallowed Enter`); everything at
`:25-64` sits directly under the top-level heading with no section of its own.

Applying the instruction as written (simulated in memory, no file changed)
produces headings at lines 1, 31 and 113, so the whole of the old `:25-64`
block renders as subsections of "Worker ledger":

- `:25-33` the `brichan-herdr-agent-observe` preflight/observe surface;
- `:35-45` the observe exit codes, the Herdr `0.9.1` minimum-version statement,
  and the `--until` / `--timeout 30000` wait spelling;
- `:47-63` the six "Safeguards that apply to every observation" bullets,
  including "A worker's `done` or `idle` state is not proof that acceptance
  criteria passed", "Never send input to a worker automatically", and the
  three-timestamped-no-progress staleness rule.

These are precisely the shared safeguards `PACKAGED-001` and
`tests/contract/test_skill_parity_contract.py:1-9` exist to protect, in the only
orchestration guidance an installed coordinator has. Filing them as ledger
sub-detail is a regression in the packaged skill's readability that no contract
catches, and the plan tells the implementer the work is "transcription plus
verification, not research" (`plan.md:135-137`), so a conforming implementer
will produce it.

Required change: keep the launch paragraph where it is (packaged
`commands.md:20-24`, after the start-command block) and move the `## Worker
ledger` section to immediately before `## Recover a swallowed Enter`
(`:65`) — or, if the checkout's launch/ledger/monitor order is to be preserved
literally, first give the observation block its own `##` heading in the same
edit. Both variants were simulated: the thirteen new markers, the three new
negative assertions, every existing negative assertion, and the ±900-character
paste-recovery window assertion
(`tests/contract/test_skill_parity_contract.py:203-207`) all pass either way, so
this costs nothing in contract terms.

### L1 (low) — plan step 6's dossier-baseline rule misfires against the measured baseline

`plan.md:87-93` records that `make dossiers` fails while the task is in flight
and that "every diagnostic must name only the still-pending coordinator- or
reviewer-owned WFS-A-204 artifacts ... A diagnostic naming any planner artifact
or any other dossier is a new defect to diagnose."

Measured on 2026-09-25 in this worktree before this review wrote anything:
`PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py projects`
reports `Invalid task dossiers: 42 issue(s) across 8 dossier(s).` and exits `1`.
All 42 are owned by WFS-A-204 artifacts, as the plan expects, but twelve of them
are `index.md` comparison rows whose text names planner artifacts, for example
`index.md: Artifact status.requirements.Phase state: index says '<phase state>'
but requirements.md says 'passed'` and the equivalent rows for `brief`,
`options`, `design` and `plan`. Under the rule as written those are "a
diagnostic naming any planner artifact", so the implementer must stop and
diagnose expected state. The summary line compounds it: "across 8 dossier(s)" is
the count of dossiers scanned, not of dossiers holding issues.

Required change: restate the rule in terms of the artifact that *owns* the
diagnostic (the path before the first colon) rather than any artifact the
diagnostic mentions, and note that the "8 dossier(s)" figure is the scanned
count.

### L2 (low) — the recorded `make dossiers` exit code is wrong

`plan.md:85` records "`make dossiers` (exit 1)". Measured: the script
`scripts/validate_task_dossiers.py` exits `1`, but `make dossiers`
(`Makefile:49-50`) exits `2`, because GNU make returns `2` when a recipe fails.
The plan elsewhere demands exact baseline matching — "If the implementation
observes any different count, test name, or message, that is a new finding to
diagnose" (`plan.md:148`) — so the wrong number invites a false alarm at the
completion gate. Required change: record `make dossiers` exit `2`, script exit
`1`.

## Verification performed

Every factual claim the plan and design make about the shipped code was
re-derived from source in this worktree rather than accepted. All held:

- `--task` exists on the installed launcher with exactly the help text
  `requirements.md` `R1` quotes —
  `src/brichan/orchestration/worker_launch.py:422-428`, confirmed in captured
  `brichan-herdr-agent-start --help` output.
- `--ledger-file` is added only under `if checkout_root is not None`
  (`worker_launch.py:432-442`), so it is absent from the installed parser.
  Reproduced: an installed routed launch carrying it fails with
  `unrecognized arguments: --ledger-file ...`, exit `2` (`R2`).
- A routed installed launch cannot silently skip the ledger:
  `worker_launch.py:495-503` refuses a target whose state is not `HEALTHY`, and
  `:520-523` sets `ledger=installed_location(paths.project_root)`, whose only
  path is `.brichan/ledger/workers.jsonl`
  (`worker_ledger.py:76,139-149`). This makes the design's deliberate omission
  of the checkout-only "no ledger location" note (`design.md:103-107`) correct
  for the packaged file's scope.
- `ledger: launch_id=<uuid>` on stderr with stdout reserved for the
  `agent_started` envelope, and
  `warning: worker started but ledger write failed: <reason>` leaving exit `0`:
  `worker_launch.py:680-704` (`R3`). `--json` implies `--dry-run`
  (`:461-462`) and `--dry-run` returns before the ledger write
  (`:568-570`), so "`--dry-run` and `--json` write nothing" is true.
- The installed `finish` parser takes `--worker`, `--launch-id`, repeatable
  `--evidence` (all required), optional `--task`, `--pane`, and `--project`,
  and does not define `--ledger-file`: `worker_ledger.py:670-692`, confirmed in
  captured `brichan-herdr-worker-ledger finish --help` output (`R4`).
- `--project` resolves the explicit root, or the Git root discovered upward
  from the working directory when omitted, and refuses a target without healthy
  managed state with `no ledger for this target` — `worker_ledger.py:203-220`.
  That refusal path returns `1` (`:724-729`), and `ProjectError` subclasses
  `ValueError` (`src/brichan/project.py:9`) so a bad `--project` is caught, not
  an uncaught traceback.
- All four documented `finish` refusals exist and write nothing: the
  `brichan-` prefix check and the empty-evidence check at
  `worker_ledger.py:700-716`, the unmatched and already-finished `launch_id`
  checks at `:633-637`. Exit table `0`/`1`/`2` matches `:717-742` (`R5`).
- "The first `finished` record for a `launch_id` in file order wins" is the
  code's own documented tie-break — `worker_ledger.py:445-453` (`R6`).
- No contract pins the bytes or size of the packaged `commands.md`:
  `intended_manifest()` hashes resources at runtime
  (`src/brichan/lifecycle.py:142-153`), the file is already in
  `IMMUTABLE_PATHS` (`:28-39`) so no inventory changes,
  `config/repository-paths.json` carries no size or digest field
  (`scripts/check_repository_paths.py` reads only classification), and
  `tests/contract/test_packaging_metadata.py:60-72`,
  `tests/contract/test_repository_paths.py:71-90`,
  `tests/contract/test_techstack_policy_contract.py:331-341` and
  `tests/integration/test_installed_dogfood.py:215-228` assert paths only
  (`R9`, `R11`).
- `options.md`'s discoverability claim is true: packaged `SKILL.md:91` says
  "Read `references/commands.md` immediately before Herdr commands", and
  `SKILL.md:17` already directs the coordinator to record a worker's task, so
  leaving `SKILL.md` unedited is defensible.

Contract simulation (in memory; no repository file was modified):

- All thirteen proposed markers are already present in the checkout tree text
  and absent from the packaged tree text today, and all thirteen are present in
  both after the drafted insertion — so `test_the_checkout_skill_states_every_safeguard`
  and `test_the_packaged_skill_states_every_safeguard` both pass (`R10`).
- The three assertions of the proposed
  `test_the_packaged_tree_never_offers_the_checkout_ledger_flag_as_usable` all
  hold against the drafted text (`R8`).
- No existing negative assertion is tripped: none of "always send Enter",
  "send Enter automatically", "automatically send", "auto-answer", the four
  overbroad input-prohibition phrasings, or the retired `0.7.3` verified-set
  spellings appears in the drafted text, and the paste-recovery window
  assertion still finds `idle`, `unsubmitted` and `herdr agent read`.
- `assertNotIn("projects/<slug>/ledger/workers.jsonl", packaged)` is the right
  narrow needle: the packaged tree legitimately contains
  `projects/<slug>/handoffs/<task-id>/receipt.md`
  (`.../references/handoff-receipt.md:8`), which a broader needle would hit.

Baseline re-measured independently of the plan, all matching `plan.md:81-98`
except finding L2:

- `make test-contract`: 148 tests, 2 failures, 1 skipped — both failures
  `tests/contract/test_repository_paths.py`, message `'.git'`.
- `scripts/check_repository_paths.py`: `unclassified root files: .git`.
- `make test-integration`: 222 tests, 1 failure
  (`test_task_dossier_workflow`), i.e. the 221 the plan predicts.
- Focused contracts green today: `test_skill_parity_contract`,
  `test_dogfood_policy_contract`, `test_packaging_metadata` — 42 tests, OK.

## Test gaps

1. **`R8` is only partially guarded.** The proposed assertions catch the exact
   phrase `add` + `--ledger-file` and the checkout ledger path shape, but any
   other affirmative phrasing ("pass `--ledger-file`", "use `--ledger-file`",
   "supply `--ledger-file`") would satisfy every assertion while presenting a
   checkout-only flag as usable. A stronger guard at the same cost: assert the
   packaged tree text contains exactly one occurrence of `--ledger-file`, or
   that every occurrence sits inside the rejection sentence.
2. **The third proposed assertion adds nothing over the first two.**
   `assertNotIn("add `--ledger-file`", self.packaged.lower())` lowercases a
   haystack against an already-lowercase needle and only excludes one
   historical wording. Near-tautological on a tree that will never carry the
   checkout sentence; it is not a defect, but it is not the guard `R8` deserves
   either — see gap 1.
3. **Nothing pins the new section's placement**, which is why M1 would survive
   `make check`. If the coordinator wants the fix from M1 to be durable, a
   single assertion that the packaged `commands.md` opens a heading between the
   ledger text and the observation bullets would close it. Optional; not
   required by any acceptance criterion.
4. **The ledger markers are asserted on concatenated tree text.** Moving the
   prose from `commands.md` into any other packaged `.md` would still pass, the
   same known limitation the existing suite handles per-file for the sixteen
   packet labels (`tests/contract/test_skill_parity_contract.py:266-288`).
   Acceptable here because `IMMUTABLE_PATHS` fixes the packaged file set, but
   worth recording.

## Residual risks and required human decisions

- **The packet's fourth acceptance criterion is not literally satisfiable in
  this worktree, and the plan's widening of it is correct.** The packet allows
  only "the two known worktree-only failures"; `R12` and `plan.md:81-98` also
  accept the `path-check` target, `make dossiers`, and one
  `test_task_dossier_workflow` failure. I re-measured all of them: `path-check`
  shares the identical `.git`-is-a-file cause as the two contract failures, and
  the dossier failures are the in-flight dossier itself. The expansion is
  evidenced and sound, but it is a change to a stated acceptance criterion and
  the coordinator should ratify it explicitly rather than let it pass
  implicitly.
- **Installed legacy launches stay undocumented.** The drafted sentence "An
  installed launch always appends to the target's fixed
  `.brichan/ledger/workers.jsonl`" is true for routed launches only; the legacy
  `--` path resolves through `legacy_launch_location`
  (`worker_launch.py:532-538`) and can degrade to
  `ledger: no ledger location for this launch; not recorded` (`:680`). The
  packaged file documents no legacy launch, so nothing in it is false, and
  `design.md:103-107` records the omission with its reason. An installed
  coordinator who nonetheless hits that note has no documented explanation. One
  sentence would close it; no acceptance criterion requires it.
- **Manifest-hash churn on an immutable resource.** `design.md:160-167` records
  this correctly and I found no contract that needs editing. It remains a
  release-process concern: a target initialized from an older build of the same
  `package_version` inspects as `MALFORMED` against a locally rebuilt package.
  No action in this task.
- **Provenance of the originating residual risk could not be re-read at
  source.** `projects/brida-worker-ledger/handoffs/WLG-001/code-review.md` is
  not present in this worktree, as `requirements.md` already records. The gap
  it describes was verified directly against the packaged tree, so no
  requirement depends on it.
- **No decision is required from the user.** Every open item above is a
  coordinator-level call.

## Claim or decision

Plan `WFS-A-204-PLAN-001` version 1 is `CHANGES REQUIRED`. Its CLI claims,
contract analysis and drafted text are correct and were independently verified,
and following it would satisfy acceptance criteria one, two, three and four.
It is blocked on M1: the ordered placement of `## Worker ledger` would file the
packaged skill's monitoring safeguards as ledger sub-detail, because the
packaged `commands.md` lacks the heading boundary the checkout file has. M1 plus
the two baseline corrections L1 and L2 are a plan revision, not a redesign; no
finding touches the selected option, the drafted text, or the contract
extension.

## Evidence

- `design.md:29-31` and `plan.md:47-54` order the placement; packaged `src/brichan/resources/dogfood_v1/skills/herdr-orchestration/references/commands.md:1,25-64,65` shows the file has no heading boundary before the observation block, while `.agents/skills/herdr-orchestration/references/commands.md:72,111` shows the checkout file does — an in-memory simulation of the edit yields headings at lines 1, 31 and 113 (finding M1).
- `src/brichan/orchestration/worker_launch.py:422-442,461-462,495-523,568-570,680-704` and `src/brichan/orchestration/worker_ledger.py:76,139-149,203-220,445-453,633-637,670-692,700-742`, plus captured `--help` output of both installed entry points and a reproduced `unrecognized arguments: --ledger-file`, exit `2`, confirm every CLI literal in `requirements.md` `R1`-`R7` and `design.md`'s drafted text.
- An in-memory application of the drafted text shows all thirteen proposed markers present in both trees, the three new negative assertions holding, and every existing negative and window assertion in `tests/contract/test_skill_parity_contract.py` still passing (`R8`, `R10`).
- `src/brichan/lifecycle.py:28-39,142-153`, `tests/contract/test_packaging_metadata.py:60-72`, `tests/contract/test_repository_paths.py:71-90` and `config/repository-paths.json` carry no byte or size pin on the changed file, confirming `R9` and `R11`.
- Re-measured baseline on 2026-09-25: `make test-contract` 148 tests / 2 failures (`'.git'`), `make test-integration` 222 tests / 1 failure, `scripts/check_repository_paths.py` `unclassified root files: .git`, `scripts/validate_task_dossiers.py projects` 42 issues exit `1` while `make dossiers` exits `2` (findings L1 and L2).

## Uncertainty

- No unresolved uncertainty remains about the reviewed plan. The one judgment I did not resolve is editorial and named for the coordinator: M1 has two acceptable fixes — move the section below the safeguard bullets, or give the observation block its own heading — and the contract evidence does not prefer one over the other.
