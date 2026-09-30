# Code review

Independent review of the implementation, or the recorded evidence for why no implementation review applies.

## Artifact metadata

- Task ID: `WFS-007`
- Task level: `0`
- Artifact: `code-review`
- Artifact version: `1`
- Origin: `wfs-007-code-review-worker:2026-09-26:v1`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `code-review-session-47a258a1`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `code-review-session-47a258a1`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `null`
- Reviewed plan version: `null`

The dossier carries no `plan.md`, so under `docs/workflows/task-dossier.md`
(Evidence contract) it has no plan artifact to review and both targets stay
null. The plan I reviewed against is the `Plan` section of `report.md`, which
names plan `WFS-007-PLAN-001` version 1; at level 0 that plan is not a
versioned dossier artifact, has no acceptance step, and gets no plan review.

## Review provenance

- Reviewing session `code-review-session-47a258a1` (full identifier
  `47a258a1-68b3-4c2a-bc35-552be9c11f56`) is a fresh session with no
  implementation context. It is not `report.md`'s authoring session
  (`coordinator-session-7d42ad6a`) and not `request.md`'s
  (`coordinator-session-7d42ad6a`). I did not make this change.
- `config/model-routing.json` points the `review` route at runtime `codex`,
  model `gpt-5.6-sol`, effort `medium`. This review instead ran Claude
  `claude-opus-5` at `high` effort. Verified by dry run: the `review` route
  resolves to `codex -c agents.enabled=false --disable multi_agent --disable
  multi_agent_v2 --model gpt-5.6-sol -c model_reasoning_effort=medium`. Level 0
  requires only the routine review route's strength, and `claude-opus-5` at
  `high` is not weaker than that, so the deviation does not lower reviewer
  strength; it is recorded here rather than left implicit. Levels 0 and 1 leave
  the index's review-route override null, so there is no field to record it in.
  Provider independence is not satisfied (implementer and reviewer are both
  Claude); model independence is (`claude-opus-5-5` implemented,
  `claude-opus-5` reviewed). This matches the precedent in
  `evals/workflow-simplification/stage2/results/a201-code-review-code-review.md`.
- Reviewed state: the uncommitted working tree of branch
  `feat/lifecycle-simplification`, one modified tracked file in scope,
  `config/model-routing.json`. `.codex/config.toml` and the untracked
  `.brichan` and `.brichan.bak-*` directories are out of scope per the packet;
  I checked the `.codex/config.toml` diff only far enough to confirm it carries
  no model or routing content (it adds `realtime_conversation = false` and an
  `mcp_servers.node_repl` block), and `.codex` is not a contract path, so it
  cannot change the review decision.
- No commit, push, remote action, or Herdr agent or pane operation was taken.
  I wrote exactly this one file.

## Verdict

`PASS`. All four acceptance criteria hold, and I established each by execution
rather than by reading `report.md`.

The change is one value. A structural comparison of the committed and working
copies as parsed JSON reports no key added, no key removed, and exactly one
value changed: `.routes.implement.model` from `claude-opus-5` to
`claude-opus-5-5`. `git diff --stat` agrees at 1 insertion and 1 deletion.
`runtime` stays `claude` and `effort` stays `medium`, and the launcher confirms
the resolved triple rather than the file's text.

`claude-opus-5-5` is a verified catalog model with a dated probe, and `medium`
is exactly the effort the catalog verified for it. The catalog records no alias
for it and directs callers to the canonical ID; the diff pins the canonical ID.

The checkout-only scope is structurally enforced, not merely intended:
`pyproject.toml` packages only `"brichan.resources.dogfood_v1" = ["**/*"]`, so
`config/model-routing.json` never ships, and the packaged manifest is byte
unchanged and still routes `implement` to `codex`/`gpt-5.6-terra`.

Two Low findings are recorded. Neither blocks. Both are dossier evidence and
close-out items outside the reviewed diff.

## Per-criterion scores

| Criterion | Score | Basis |
| --- | --- | --- |
| Spec fidelity | 5/5 | The diff is exactly the change `request.md` and `report.md`'s `Plan` specify, and nothing more. Structural JSON comparison against the committed file shows one changed value and no added or removed key; `schema_version` stays `1` and the route set stays `{plan, implement, review, scan}`. `git status --porcelain -- src/brichan/resources/` is empty, so the installed-mode default is untouched, as the declared scope requires. No scope drift and no incidental edit. |
| Code review | 5/5 | Nothing in the change is wrong or risky. The routed model and effort are both verified in `docs/policy/model-catalog.md`, the canonical ID is pinned as that file directs, and no repository code, test, or doc duplicates the old value in a way this change breaks: the one test that mentions `claude-opus-5` (`tests/unit/test_cli_render.py:457`) writes its own temporary manifest and never reads the repository file. I looked for a prefix-collision hazard, since `claude-opus-5` is a proper prefix of `claude-opus-5-5`, and found no substring or `startswith` matching on model identifiers anywhere in `src/brichan`; the only model inspection is `validate_model`, a whole-string shape check. |
| Empirical verification | 4/5 | Every claim reproduced in this session, on both interpreters, and the one sanctioned red names only WFS-007's own pending artifacts. The point off is L1: one of the four evidence lines in `report.md`'s `Verification` section does not re-run as written. |

## Findings

No Critical, High, or Medium finding.

### L1 — Low, not blocking. The report's dry-run evidence line is not reproducible as written

`report.md`'s `Verification` section records:

```text
bin/brichan-herdr-agent-start brichan-probe --route implement --dry-run
```

Run verbatim, that exits 2 with
`brichan-herdr-agent-start: error: the following arguments are required: --cwd`.
The launcher requires `--cwd`; the recorded invocation omits it, so a
coordinator or auditor re-running the recorded command gets a usage error
rather than the resolved route, and could read that as the route being broken.

The claim the line supports is nonetheless true. Supplying the required option
reproduces the recorded output exactly:

```text
claude --permission-mode auto --model claude-opus-5-5 --effort medium --disallowed-tools=Task
```

and the `--json` form of the same run reports
`"resolved": {"effort": "medium", "model": "claude-opus-5-5", "runtime": "claude"}`
with `"route": "implement"` and `"dry_run": true`.

Not blocking: the underlying acceptance criterion holds and I verified it
independently. `DOSSIER-004` applies to the fix — correct the line in place by
adding the `--cwd` option, and do not append a later contradicting section.

### L2 — Low, not blocking. The index records no level determination, so the level claim has no recorded basis to check

`docs/workflows/task-dossier.md` (Levels) requires the index's `Evidence`
section to record the level determination: the level-raising trigger that fixed
the level, or a recorded statement that none applies. `docs/policy/reviewer.md`
then makes checking that recorded claim a reviewer obligation.
`index.md` is still the unedited template, so its `Evidence` section reads
`<repository or source evidence for the claim>` and there is no claim to check
against.

I therefore checked the triggers directly, and the declared level 0 is correct:

- Level 1 triggers: no explicit planning was requested; the work does not span
  sessions and is not expected to resume; the user fixed the model choice, so
  no competing credible option needed evaluation; no architecture or
  compatibility surface changes, because the packaged manifest that installed
  projects read is untouched; and the acceptance criteria needed no
  decomposition.
- Level 2 triggers: `docs/policy/reviewer.md`'s mandatory-review list does not
  apply — no authentication, authorization, secret, payment, or personal-data
  surface; no destructive migration; no production or deployment behavior, since
  the changed file never ships; no public API, schema, or cross-service
  contract, `config/` being an internal contract path rather than an external
  one; not cross-cutting at one changed value; and no worker failed repeatedly.
  Only one writer produced the implementation. The nearest candidate is the
  trade-off trigger, and I judge it not met: the change is one reversible value
  scoped to this checkout, both models are Opus-class under the same
  subscription so no cost tier moves, and the newer model carries a dated live
  probe plus a real worker run.

Not blocking, and not a defect in the diff: this is a coordinator close-out
item on `index.md`, which the packet places outside my write scope and whose
current red is sanctioned. It must be recorded before the dossier can pass.

## Test gaps

No test gap, and specifically no missing-regression-test defect.

I considered whether routing `implement` to a different model is a behavior
change that `docs/policy/reviewer.md` and `GENERAL-004` require a committed
regression test for, and concluded it is not:

- No executable code changed. The change is one data value in a configuration
  manifest, and the resolution mechanism it feeds is already covered by
  committed tests: `tests/unit/test_model_routing.py`'s
  `test_manifest_resolves_all_required_routes` parses the real repository
  manifest and asserts every required route resolves with a valid runtime and a
  non-empty model, and
  `tests/integration/test_worker_routing_cli.py`'s
  `test_named_route_builds_guarded_provider_command` covers named-route command
  construction. Both pass.
- Pinning the literal `claude-opus-5-5` in a test would work against the
  design the repository states and enforces elsewhere.
  `docs/policy/model-catalog.md` says active route defaults live only in
  `config/model-routing.json` so that a routing change never requires editing
  another file, and
  `tests/contract/test_repository_contract.py`'s
  `test_model_routing_manifest_has_only_model_selection_settings` actively
  asserts that no active model identifier appears in `src` or in `CLAUDE.md`.
  A value-pinning test would reintroduce the duplication that contract removes
  and make every future routing change a two-file edit.
- The manifest's own invariants are covered by that same contract test, which I
  re-ran: `schema_version` is `1`, the route set is exactly the four names, and
  no argv, permission, sandbox, approval, or delegation key is present.

The absence of a value-pinning test does have a consequence, recorded below as
a residual risk rather than a gap, because the hardening is beyond this task's
contract.

## Residual risks

1. **Nothing automated checks a routed model against the catalog.** The routing
   policy requires a model to be verified in `docs/policy/model-catalog.md`
   before it is routed, but that rule is enforced by policy and human judgment
   only. `validate_model` is a shape check —
   `^[A-Za-z0-9][A-Za-z0-9._:/-]*$` — and nothing under `scripts` or `tests`
   cross-references the manifest's model strings against the catalog; the only
   catalog references anywhere are presence checks on the file itself. I
   confirmed the hole by calling the validator directly: `claude-opus-55`, a
   plausible typo of this task's value, passes `validate_model` and would pass
   `make check`, failing only at live launch. For this task the guard held —
   the dry run and the catalog entry both check out — but the guard is
   procedural. A contract test asserting that every active model in
   `config/model-routing.json` appears in `docs/policy/model-catalog.md` would
   turn it into a gate. That is hardening beyond this task's contract, so it is
   a risk to decide on, not a finding.
2. **The evidence is directional, and the change is broader than the evidence's
   stated conclusion.** `evals/workflow-simplification/stage1/results/results.md`
   concludes the evidence is "strong enough to use `opus-5-5` as the `implement`
   model for stage 2", and states its limits plainly: three tasks, one sample
   per arm, one reviewer from the same provider as both arms, hidden tests at
   the ceiling for both, and cost unavailable. This change makes the model the
   standing checkout default rather than a stage-2 setting. That is the user's
   decision of 2026-09-26 and `request.md` and `report.md` both record the
   directional limit, so it is not a defect; it is the trade-off being carried.
   Reverting is one value.
3. **A stale managed manifest sits beside the checkout one and still routes
   `implement` elsewhere.** The untracked `.brichan/config/model-routing.json`
   routes `implement` to `codex`/`gpt-5.6-terra`, as do two of the three
   `.brichan.bak-*` copies. The checkout manifest correctly wins for
   `bin/brichan-herdr-agent-start`, which the dry run proves and which
   `test_model_routing.py`'s
   `test_repository_routing_never_promotes_colocated_managed_state` pins as
   DOGFOOD-007. But a caller that names the managed path explicitly, through
   `BRICHAN_MODEL_ROUTING_FILE` or installed mode, still gets
   `gpt-5.6-terra`. That is the declared checkout-only scope behaving as
   intended; it is worth stating so that a later "why did my worker come up on
   Terra" is not read as a regression in this change.
4. **The catalog's file-level verification date trails its newest entry.**
   `docs/policy/model-catalog.md` still says `Last verified: 2026-07-29` while
   the `claude-opus-5-5` entry it now supplies cites a probe on 2026-09-25 and
   a Claude Code version of `2.1.282`. The entry itself is dated and specific,
   so the acceptance criterion is met; the stale header is a pre-existing nit
   in a file this diff does not touch, and it slightly weakens the file as an
   at-a-glance authority.
5. **I did not re-probe the model live.** Starting a real worker is out of
   scope, so the model's availability rests on the catalog's 2026-09-25 probe
   and the stage 1 worker run, not on an observation from this session.
   Authentication can lapse, and the catalog itself says to re-check before a
   session that depends on it.

## Claim or decision

`PASS`. The uncommitted change to `config/model-routing.json` is exactly the
one-line routing change WFS-007 specifies, all four acceptance criteria hold on
both interpreters, and nothing else in the manifest, in
`src/brichan/resources`, or in the packaged installed-mode defaults changes.
Two Low findings are recorded and neither blocks: L1 is a one-line evidence
correction in `report.md`, and L2 is the level determination the coordinator
still has to record in `index.md`, whose declared level 0 I independently
confirmed correct.

## Evidence

- Diff scope, measured two ways: `git diff --stat -- config/model-routing.json`
  reports `1 file changed, 1 insertion(+), 1 deletion(-)`, and a structural
  comparison of `git show HEAD:config/model-routing.json` against the working
  copy, both parsed as JSON and flattened, reports `keys added: none`,
  `keys removed: none`, and one changed value,
  `.routes.implement.model: 'claude-opus-5' -> 'claude-opus-5-5'`.
- Resolved route, not file text:
  `bin/brichan-herdr-agent-start brichan-wfs007-probe --cwd <repository root>
  --route implement --dry-run` prints
  `claude --permission-mode auto --model claude-opus-5-5 --effort medium --disallowed-tools=Task`,
  and the `--json` form reports
  `"resolved": {"effort": "medium", "model": "claude-opus-5-5", "runtime": "claude"}`.
  Acceptance criterion 1 holds: runtime `claude`, model `claude-opus-5-5`,
  effort `medium`.
- Catalog verification: `docs/policy/model-catalog.md` lists
  `| — | claude-opus-5-5 | medium | Implementation and debugging |` and records
  a live `claude -p` probe on 2026-09-25 under Claude Code `2.1.282` with
  `claude.ai` authentication, plus a Herdr worker run at `medium` in
  `evals/workflow-simplification/stage1/results/results.md`. It also states
  that no alias was verified and the canonical ID must be used, which the diff
  does. Acceptance criterion 2 holds, and the routed effort matches the
  verified effort.
- Packaged resources untouched: `git status --porcelain -- src/brichan/resources/`
  is empty and `git diff HEAD --stat -- src/brichan/` is empty.
  `src/brichan/resources/dogfood_v1/config/model-routing.json` still routes
  `implement` to `{"runtime": "codex", "model": "gpt-5.6-terra", "effort":
  "medium"}`. Acceptance criterion 3 holds.
- Checkout-only scope is structural, not just intended: `pyproject.toml`
  declares `[tool.setuptools.package-data]` as
  `"brichan.resources.dogfood_v1" = ["**/*"]`, so `config/model-routing.json`
  is not packaged and the change cannot reach an installed project.
  `make package-check` passes on both interpreters.
- Review applicability: with `set -o pipefail`,
  `git diff --name-only --no-renames | python3 scripts/check_contract_paths.py`
  exits 3 and prints `contract-path: yes` and `config/model-routing.json`. The
  directory prefix `config/` matches, so independent code review is required at
  level 0 and this artifact's applicability is `required`.
- `PYTHONDONTWRITEBYTECODE=1 make check` on Python 3.10.11: unit 1069 tests OK,
  contract 153 tests OK, metrics 10 tests OK, integration 228 tests with one
  failure, `test_task_dossier_workflow.TaskDossierWorkflowIntegrationTest.test_repository_checkout_validates_clean`.
  Because `check` runs `test` first, the later targets did not run under it, so
  I ran each one individually: `techstack-eval`, `metrics`, `receipts`,
  `memory-check`, `path-check`, `readme-check`, `phase5-preflight`, and
  `package-check` all exit 0; only `dossiers` fails.
- `PYTHONDONTWRITEBYTECODE=1 make check PYTHON=/opt/homebrew/bin/python3.14` on
  Python 3.14.6: the same single integration failure and the same individual
  target results, `dossiers` the only red.
- The red is confined to WFS-007's own pending artifacts, before and after
  this artifact was written. Reviewing the state I was given, `make dossiers`
  reported `Invalid task dossiers: 20 issue(s)`, all 20 naming this task: ten on
  `index.md` and `code-review.md` template placeholders in `Artifact metadata`,
  one on the not-yet-written canonical `receipt.md`, three on `Task identity`
  placeholders in `index.md`, and six on `Artifact status` rows in `index.md`
  disagreeing with the artifacts. After this artifact replaced the
  `code-review.md` template the count is 16, with zero issues on
  `code-review.md`: the remainder are `index.md`'s placeholders and the missing
  `receipt.md`, both coordinator-owned and both outside my write scope.
  Filtering the validator output for dossier paths other than WFS-007 returns
  nothing, before or after, on both interpreters. Acceptance criterion 4 holds
  under its stated exception.
- Routing unit tests re-run directly:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest
  tests.unit.test_model_routing tests.unit.test_cli_render` runs 77 tests, OK.
- No repository artifact depends on the old value in a way this change breaks.
  `git grep -n 'claude-opus-5'` outside `evals` and `projects` returns only:
  the changed line itself; three catalog lines in `docs/policy/model-catalog.md`;
  two historical `metrics/runs.jsonl` rows; the packaged manifest's coordinator
  Claude runtime; and `tests/unit/test_cli_render.py:457` and `:467`, which
  build a manifest in a temporary directory and never read the repository file.
- No prefix-collision hazard, checked because `claude-opus-5` is a proper
  prefix of `claude-opus-5-5`: no `startswith` or substring matching on model
  identifiers exists under `src/brichan`; the only inspection is
  `validate_model` in `src/brichan/orchestration/model_routing.py:77`, a
  whole-string `re.fullmatch` against `^[A-Za-z0-9][A-Za-z0-9._:/-]*$`.
- L1 reproduction: the command as recorded in `report.md` exits 2 with
  `brichan-herdr-agent-start: error: the following arguments are required: --cwd`;
  adding `--cwd` produces the output `report.md` claims, verbatim.
- L2 basis: `projects/brida-workflow-simplification/handoffs/WFS-007/index.md`
  is the unedited template, its `Evidence` section still reading
  `<repository or source evidence for the claim>`, so it records no level
  determination for a reviewer to check.
- Techstack scope: Snapshot pointer
  `projects/brida-workflow-simplification/handoffs/WFS-007/snapshots/attempt-code-review-1-8915cd6577e68288dca65d9726ae2c26f7a23c14bc9e8dd6b6966a695d598a81.snapshot.json`,
  digest `8915cd6577e68288dca65d9726ae2c26f7a23c14bc9e8dd6b6966a695d598a81`.
  `brichan techstacks verify --as-of 2026-09-26` returned `status: match` with
  `observed_snapshot_sha256` equal to that digest, before any review work. All
  four selected rule files were read: `techstacks/README.md`,
  `techstacks/general.md`, `techstacks/policy/README.md`, and
  `techstacks/policy/task-dossiers.md`.

## Uncertainty

Three uncertainties remain, none of which changes the verdict.

1. Provider independence is not satisfied. `config/model-routing.json` routes
   `review` to `codex`/`gpt-5.6-sol`, and `docs/policy/reviewer.md` prefers a
   different verified provider, but this review ran Claude `claude-opus-5` at
   `high` effort. Model independence holds and level 0 requires only routine
   reviewer strength, which `claude-opus-5` at `high` meets or exceeds, so I
   judge the verdict sound; whether a Claude reviewer satisfies the
   coordinator's intent for a change that selects a Claude model is the
   coordinator's call, not mine.
2. The routed model's availability is carried from the catalog's 2026-09-25
   probe and the stage 1 worker run, not observed in this session. Starting a
   real worker is out of scope, so a dry run is the strongest evidence I could
   produce, and a dry run starts nothing and proves resolution only.
3. Whether `claude-opus-5-5` is genuinely better than `claude-opus-5` for the
   `implement` route remains open on the merits. Stage 1 is three tasks with
   one sample per arm, both arms at the hidden-test ceiling, separated only by
   one blind reviewer from the same provider, with cost unavailable. That is
   directional, which `request.md`, `report.md`, and the results file all say.
   My PASS is that the change faithfully and safely implements the user's
   decision, not that the decision is empirically proven.
