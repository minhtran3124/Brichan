# Code review

Independent review of the implementation, or the recorded evidence for why no implementation review applies.

## Artifact metadata

- Task ID: `WFS-A-204`
- Task level: `1`
- Artifact: `code-review`
- Artifact version: `1`
- Origin: `packet:WFS-A-204-REVIEW@2026-09-25#attempt-code-review-1`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `e8260526-ff5e-4b3c-8a87-21ee0e449ba9`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `e8260526-ff5e-4b3c-8a87-21ee0e449ba9`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `WFS-A-204-PLAN-001`
- Reviewed plan version: `4`

Reviewed artifact: the uncommitted two-file change in this detached worktree,
against `plan.md` v4 (status `accepted`), `design.md` v4, `requirements.md` v4,
the packet acceptance criteria, and the coordinator-ratified completion gate in
`client-follow-up-questions.md` v2. The implementer's `implementation.md` was
read as a claim to test, not as proof; every table row in it was re-measured in
this session.

This reviewing session (`e8260526-ff5e-4b3c-8a87-21ee0e449ba9`) authored none of
the reviewed artifacts: the v4 planner session is
`cbe8f2f3-df53-44bd-85b0-f419269bce8c`, the plan-review v4 session is
`2fbce2ec-8fd9-4ba4-9b99-70fc73254216`. `implementation.md` records no session
identifier, only `Effective model: claude-opus-5-5`; identifier inequality and a
different model identifier are consistency signals, not proof of independence.

## Techstack scope

- Snapshot pointer: `projects/brida-workflow-simplification/handoffs/WFS-A-204/snapshots/attempt-code-review-1-83f558c900eef80979d2c64fa295ac4b1b89d4aed2bcceea89b876d330f6e1c4.snapshot.json`
- Snapshot SHA-256: `83f558c900eef80979d2c64fa295ac4b1b89d4aed2bcceea89b876d330f6e1c4`
- `brichan techstacks verify` returned `status: match` (observed digest equal to
  expected) before any other work in this session, and all eight required
  selected rule files were read. No path outside the declared scope paths was
  needed; no new Context ID, chain, conflict, or exception need was discovered.

## Verdict

`PASS`.

No critical, high, or medium defect exists. Every packet acceptance criterion
holds under independent measurement, the change is a pure insertion that removes
or reweakens nothing, and every guard the new test adds was shown to fail under
mutation. One low finding is recorded; it changes no behavior a coordinator
depends on and does not gate acceptance.

## Scores

| Criterion | Score | Basis |
| --- | ---: | --- |
| Spec fidelity | 5 | All four acceptance criteria verified independently. Every command, flag, refusal string, and exit code in the new text was reproduced against the shipped CLI or read in the parser source. The inserted text is a byte-exact transcription of the two `design.md` v4 blockquotes (342 and 2004 characters, both exact substrings of the edited file). Placement, the omitted legacy note, the narrowed exit-`2` row, and the `.brichan/manifest.json` refusal condition all follow the accepted plan. |
| Code review | 5 | `git diff --stat`: 2 files, 90 insertions, 0 deletions — no existing packaged byte, marker, label, or test was changed. `git status --short` shows exactly the two authorized tracked files. No executable behavior changed. The new test's four assertions and the thirteen new markers were each shown live by mutation (see Evidence). No contract was weakened to make a gate pass. |
| Empirical verification | 5 | Every claim in `implementation.md` was reproduced in this session rather than accepted: focused contracts (43 tests `OK`) on both interpreters, the full `make check`-equivalent gate on both interpreters with an identical expected-red set, the four `finish` refusals and both `--ledger-file` rejections executed against a scratch target, the dossier-diagnostic ownership split (30 / 5 / 5), and six of the implementer's parser-source line citations spot-checked. Literal `make check` was also run and stops exactly at the two known worktree-only failures. |

Total: 15/15.

## Findings

### Critical

None.

### High

None.

### Medium

None.

### Low

**L1 — the `finish` usage block shows the optional `--project` as if it were
required.**

`src/brichan/resources/dogfood_v1/skills/herdr-orchestration/references/commands.md:88`
renders `--project <absolute-target-project>` unbracketed, while the same block
brackets the other two optional flags at line 87 (`[--task <TASK-ID>] [--pane
<pane-id>]`). The shipped parser makes `--project` optional:
`src/brichan/orchestration/worker_ledger.py:692` is `finish.add_argument("--project")`
with no `required=True`, and `finish --help` prints `[--project PROJECT]`
alongside the three genuinely required flags `--worker`, `--launch-id`, and
`--evidence`. Reproduce with:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -c \
  "import sys; from brichan.orchestration import worker_ledger as w; \
   sys.exit(w.main(['finish','--help']))"
```

Mitigation already present: lines 91-92 state the omission behavior explicitly
("when it is omitted, the Git root is discovered upward from the working
directory"), so no reader is misled about what the command does, and believing
the flag mandatory is the safer error — an explicit `--project` removes the
dependence on the process working directory. The rendering is also deliberate:
`design.md:107` drafts it this way, mirroring the checkout block where
`--ledger-file` genuinely is required (`worker_ledger.py:690`). Classified low
rather than as a residual-risk idea because it is a concrete, checkable
mismatch between the packaged text and `--help`, which the second acceptance
criterion names as the evidence standard. Fix, if the coordinator wants it, is
one bracket pair; it would change the packaged bytes and so needs a new plan
version, which is why it is not verdict-changing on its own.

## Test gaps

1. **Nothing pins the documented refusal set to the code's refusal set.** If a
   future change drops the `brichan-` prefix check
   (`worker_ledger.py:704-709`) or the empty-evidence check (`:710-717`), the
   packaged text keeps claiming the refusal and the parity contract still
   passes — the markers assert the prose exists, not that the CLI enforces it.
   `design.md` records this as a known limitation, and plan-review v3 accepted
   that no cheap assertion closes it. Verified live rather than assumed: all
   four documented refusals and both `--ledger-file` rejections were executed
   in this session.
2. **Markers are asserted against concatenated, whitespace-normalized tree
   text** (`tests/contract/test_skill_parity_contract.py:104-118`), so any file
   in either skill tree can satisfy any marker. Only `## Worker ledger` in
   `references/commands.md` is pinned to a file and to an ordering; the new
   launch paragraph at lines 25-29 has no placement assertion and would still
   pass if it moved to another packaged file.
3. **The placement pin's two `str.index` calls are unguarded**
   (`tests/contract/test_skill_parity_contract.py:353-355`). Only
   `"## Worker ledger"` has a leading `assertIn`; deleting the
   `Safeguards that apply to every observation` paragraph or the
   `## Recover a swallowed Enter` heading raises `ValueError` and surfaces as a
   unittest ERROR instead of a FAILURE. Reproduced on a scratchpad copy
   (mutation `m6`). The suite still goes red, so this is legibility, not a hole.
4. **Marker `"--project <absolute-target-project>"` couples the packaged
   contract to checkout-only prose.** `PARITY_MARKERS` requires it in both
   trees, and the checkout side carries it only inside a cross-reference
   sentence describing installed mode
   (`.agents/skills/herdr-orchestration/references/commands.md:94-95`). A
   checkout-only rewording of that sentence fails a contract that exists to
   guard the packaged text. Same shape as markers that already existed; noted
   so a future editor is not surprised.
5. **No test distinguishes the installed exit table from the checkout one**
   beyond the `--ledger-file` occurrence count. That count does catch the
   realistic regression (copying the checkout row `Invalid invocation,
   including a rejected --ledger-file value` into the packaged file raises the
   count to 2; verified as mutation `m3`), so the gap is narrow.

## Residual risks and required human decisions

1. **Installed projects keep the old text until deliberate reinitialization.**
   `PACKAGED-002` forbids overwriting an export automatically, and the packaged
   resource hash is embedded in the manifest at `init` time
   (`src/brichan/lifecycle.py:143-153`). Independent observation that *narrows*
   the risk the plan records: `inspect_project` rejects a manifest whose
   `package_version` differs from the running package
   (`src/brichan/lifecycle.py:244-251`) **before** it compares any resource
   hash (`:275-297`), so any release already forces the same reinitialization.
   This change therefore adds no new upgrade burden beyond a version bump. No
   action in this task.
2. **The unconditional launch sentence is safe only because legacy launches are
   undocumented.** "A successful launch appends exactly one `launched` record"
   (`commands.md:73`) holds for routed installed launches, which always resolve
   the fixed location (`worker_launch.py:514-524`). A legacy installed launch
   (explicit command after `--`) resolves through `legacy_launch_location` and
   can append nothing, printing
   `ledger: no ledger location for this launch; not recorded`
   (`worker_launch.py:680`, `worker_ledger.py:96`). The packaged skill tree
   contains no mention of the legacy form, so nothing in it is false today; the
   sentence must be qualified if a future packaged edit documents legacy
   launches. Deliberate per `design.md` wording notes.
3. **Three enforced `finish` refusals are deliberately undocumented**:
   `target project is not a directory`, `target project is not a Git repository
   root`, and `cannot find a Git repository from` (`src/brichan/project.py:35-51`,
   each exit `1` through `worker_ledger.py:726-730`; the second was reproduced
   in this session). The exit table's parenthetical never claims exhaustiveness,
   so nothing false ships, but a coordinator who hits one of these will not find
   it in the skill. Closed knowingly as plan-review v3 finding `L1-v3`.
4. **`finish` writes into unhealthy managed state.** It requires only a regular
   `.brichan/manifest.json` (`worker_ledger.py:195-200`) and never calls
   `inspect_project`, so a `MALFORMED` or `INCOMPATIBLE` target still accepts an
   attestation. The packaged text states this as coordinator responsibility
   rather than as a refusal, which matches the code exactly; whether that
   division is right is a product decision, not a defect in this change.
5. **Same-model-family review.** `docs/policy/reviewer.md` prefers a different
   verified provider. The implementer ran `claude-opus-5-5` and this review ran
   `claude-opus-5` in a fresh session with no implementation context — an
   independent session, not an independent provider. `config/model-routing.json`
   routes `review` to `codex`/`gpt-5.6-sol`/`medium`, so this session is a
   coordinator one-off override. Human decision: whether that satisfies the
   preference for this level-1 documentation change.
6. **The expected-red baseline is worktree- and dossier-specific.** The two
   `tests/contract/test_repository_paths.py` failures and `make path-check` are
   caused by this detached worktree's `.git` file; `make dossiers` and
   `tests.integration.test_task_dossier_workflow.test_repository_checkout_validates_clean`
   are red only while this dossier is in flight. They must be re-measured on the
   main checkout before merge, where all gates must be green. Writing this
   artifact clears the five `code-review.md` diagnostics; `index.md`,
   `pr-desc.md`, and the missing `receipt.md` remain coordinator-owned work.

## Claim or decision

Accepted plan `WFS-A-204-PLAN-001` version 4 was implemented faithfully and is
accepted: verdict `PASS`, scores 5/5/5. The packaged `herdr-orchestration`
skill now states `--task <TASK-ID>` and its verbatim-recording rule, the fixed
installed `.brichan/ledger/workers.jsonl` location, the installed rejection of
`--ledger-file`, and the installed `finish` attestation with its `--project`
resolution, its four integrity refusals, its exit table, and the
attestation-not-proof invariant — every literal matching the shipped CLI. The
parity, packaging, and dogfood-policy contracts stay green, extended only where
they legitimately pin the changed bytes. One low finding (`L1`) and six residual
risks are recorded; none requires a change before merge.

## Evidence

- `git status --short` lists exactly two modified tracked files,
  `src/brichan/resources/dogfood_v1/skills/herdr-orchestration/references/commands.md`
  and `tests/contract/test_skill_parity_contract.py`; `git diff --stat` is
  `2 files changed, 90 insertions(+)` with zero deletions. The dossier is
  gitignored (`.gitignore:67`), so dossier writes cannot appear here; file
  mtimes show the two source files last written at `21:16:46` and
  `implementation.md` at `21:23:39` on 2026-09-25, i.e. the evidence file
  postdates the last edit.
- Transcription fidelity: a script extracted the two `design.md` v4 blockquotes
  and confirmed each is an exact substring of the edited packaged file (342 and
  2004 characters). The packaged diff is a pure insertion at two points, so no
  existing safeguard text moved or changed.
- CLI fidelity, executed in this session with `PYTHONDONTWRITEBYTECODE=1
  PYTHONPATH=src` on Python 3.10.11 against a scratch Git target outside the
  repository: `brichan-herdr-agent-start --help` lists `--task` with help text
  "task identifier recorded verbatim in the worker ledger; never inferred when
  the flag is absent" and no `--ledger-file`; passing `--ledger-file` to the
  installed launcher gives `error: unrecognized arguments: --ledger-file
  x.jsonl`, exit `2`, before any Herdr call; `finish --help` lists `--worker`,
  `--launch-id`, `--evidence`, `--task`, `--pane`, `--project` and no
  `--ledger-file`, which likewise exits `2`. Refusals reproduced, each exit `1`
  with nothing written: `no ledger for this target: <path>` (no manifest);
  `no launched record for launch_id u`; `worker name must begin with brichan-:
  other`; `every --evidence item must be non-empty` (whitespace evidence);
  and, after seeding one `launched` record, a first `finish` exit `0` followed
  by `launch_id L1 already has a finished record`, exit `1`. After the first
  four refusals the target held no `.brichan/ledger` directory.
- Parser and behavior source read directly: `worker_ledger.py:76-79` and
  `139-150` (fixed `.brichan/ledger/workers.jsonl`), `:195-200`
  (`_state_manifest_is_regular`, `os.lstat` + `S_ISREG`), `:203-220`
  (`--project` else upward Git-root walk; `no ledger for this target`),
  `:445-453` (first `finished` record in file order wins), `:634-638`
  (unmatched and already-finished refusals), `:670-692` (installed `finish`
  defines `--project`, checkout defines `--ledger-file`), `:701-742` (prefix
  and evidence refusals, exit `1`; checkout-only exit `2` path);
  `worker_launch.py:422-442` (`--task` help; `--ledger-file` defined only when
  a checkout root is present), `:514-524` (routed installed launches always use
  `installed_location`), `:568-570` (`--dry-run`/`--json` return `0` before any
  ledger write), `:680-704` (record written only after the rollback scope
  closes; `ledger: launch_id=<uuid>` and `warning: worker started but ledger
  write failed: ` on stderr, exit stays `0`), `:716` (stdout is the verbatim
  start envelope). `task_id=args.task` is passed straight through
  (`worker_ledger.py:735`); nothing infers it.
- Contract liveness, by mutation on a scratchpad copy of the packaged skill
  tree (no tracked file was modified): deleting the `## Worker ledger` section
  fails the heading guard plus 10 markers; moving it above the observation
  safeguards fails the `safeguards < ledger` ordering assertion; appending an
  affirmative `--ledger-file` sentence raises the occurrence count to 2 and
  fails; dropping "recorded verbatim and is never inferred" or "attestation,
  not proof" each fails one marker; deleting the safeguards paragraph raises
  `ValueError` (test gap 3). The unmutated tree is clean. All thirteen new
  markers were confirmed present in both skill trees, and the checkout path
  shape `projects/<slug>/ledger/workers.jsonl` is absent from the packaged
  tree.
- Focused contracts (`test_skill_parity_contract`, `test_dogfood_policy_contract`,
  `test_packaging_metadata`): 43 tests `OK` on Python 3.10.11 and on 3.14.6.
- Completion gate, `client-follow-up-questions.md` v2 as extended by plan step 6,
  all runs with `PYTHONDONTWRITEBYTECODE=1`. On 3.10: `test-unit` 1026 tests
  `OK`; `test-contract` 149 tests, 2 failures, 1 skipped; `test-integration` 222
  tests, 1 failure; `techstack-eval`, `metrics`, `receipts`, `memory-check`,
  `readme-check`, `phase5-preflight`, `package-check` exit `0`; `dossiers` and
  `path-check` exit `2`; `sh -n bin/brichan` exit `0`;
  `metrics/test_validate_metrics.py` 10 tests `OK`. On 3.14.6 via
  `PYTHON=/opt/homebrew/bin/python3.14`: identical results, with the two direct
  invocations the recipes do not honor green
  (`evals.techstack_context_v1.test_cases` 56 tests `OK`;
  `metrics/test_validate_metrics.py` 10 tests `OK`). The failing tests are
  exactly `test_current_path_and_link_contracts_pass`,
  `test_every_non_ephemeral_root_file_is_classified` (both
  `unclassified root files: .git`, this worktree's `.git` file) and
  `test_repository_checkout_validates_clean`. Literal
  `PYTHONDONTWRITEBYTECODE=1 make check` was also run: it exits `2`, stopping at
  those same two contract failures after `test-unit` and the metrics tests pass.
  `make check`'s target set equals the ratified list plus `sh -n bin/brichan`
  and `metrics/test_validate_metrics.py` (`Makefile:24-27,75-76`), so the
  decomposed run is `make check`-equivalent and strictly more informative.
- Dossier-diagnostic ownership before this artifact was written: 40 issues,
  `index.md` 30 (including the `canonical receipt does not exist` row),
  `code-review.md` 5, `pr-desc.md` 5 — all pending coordinator- or
  reviewer-owned WFS-A-204 artifacts, none owned by a planner artifact, by
  `implementation.md`, or by another dossier. This matches
  `implementation.md`'s split exactly.
- No frozen digest of the packaged resources exists in the repository: the only
  non-resource reference to the edited file is `src/brichan/lifecycle.py:37`
  (`IMMUTABLE_PATHS`), and manifest hashes are computed at `init` time
  (`:143-153`), so no contract byte needed updating beyond the parity markers.
  The packaged skill's other files carry no `ledger` or `--task` text in either
  tree, so the change creates no intra-tree contradiction and no packaged /
  checkout parity gap outside `references/commands.md`.

## Uncertainty

- This session cannot observe its own effort setting from inside; `high` is
  recorded as the depth actually applied (full gate on both interpreters,
  mutation testing, CLI reproduction against a scratch target), not as a value
  read from configuration. `config/model-routing.json` routes `review` to
  `codex`/`gpt-5.6-sol`/`medium`, so this session ran under a coordinator
  one-off model override.
- Review independence rests on identifier and model-identifier inequality plus
  this session having no implementation context; `implementation.md` records no
  authoring session identifier, so independence from the implementer cannot be
  proved from the dossier alone.
- The window between the last source edit (`21:16:46`) and `implementation.md`
  (`21:23:39`) is about seven minutes, which is tight for a gate that took this
  session roughly six minutes across both interpreters. Every result claimed in
  that table was independently re-measured here on the current bytes and
  matched, so the claims are verified regardless of when the implementer ran
  them.
- The expected-red baseline is specific to this detached worktree and this
  in-flight dossier; it is not evidence about the main checkout.
- No other unresolved uncertainty remains.
