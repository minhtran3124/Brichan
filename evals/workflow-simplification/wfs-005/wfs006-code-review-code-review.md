# Code review

Independent review of the implementation, or the recorded evidence for why no implementation review applies.

## Artifact metadata

- Task ID: `WFS-006`
- Task level: `1`
- Artifact: `code-review`
- Artifact version: `1`
- Origin: `wfs-006-code-review-worker:2026-09-26:v1`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `code-review-session-3ebd1946`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `medium`
- Reviewing session: `code-review-session-3ebd1946`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `null`
- Reviewed plan version: `null`

## Review provenance

- WFS-006 is a level 1 task. Level 1 carries no plan artifact, no plan
  acceptance, and no plan review, so the review targets above are `null`, as
  the Levels and Evidence-contract sections of
  `docs/workflows/task-dossier.md` require. The plan under review is the `Plan`
  section of `report.md`, plan ID `WFS-006-PLAN-001` version 1.
- Applicability is `required` unconditionally: level 1 makes an independent
  code review mandatory, and only level 0 may record it `not-required`.
- Reviewing session `code-review-session-3ebd1946` is a fresh session. It is
  not `report.md`'s authoring session (`claude-code-d3d6e5f7`), not the
  WFS-005 review sessions (`code-review-session-d0a06235`,
  `code-review-session-c6a70f04`), and not the coordinator session
  (`coordinator-session-7d42ad6a`). I did not implement any part of this
  change.
- Reviewed state: the uncommitted working tree of branch
  `feat/lifecycle-simplification`, restricted to
  `docs/workflows/task-dossier.md`,
  `src/brichan/contracts/task_dossier/`, and `tests/`. The
  `.codex/config.toml` change (four lines of local Codex client settings),
  the `.brichan*` backup directories, `evals/`, and the
  `projects/brida-workflow-simplification` markdown are outside the
  implementation diff, as the task packet states. I confirmed
  `.codex/config.toml` contains only `realtime_conversation = false` and an
  `mcp_servers.node_repl` toggle, nothing related to WFS-006.
- Declared level check: the diff is 141 insertions over 9 files, touches no
  authentication, secrets, payment, personal-data, destructive, or production
  path, and adds no new public surface, so no level-raising trigger in the
  Levels section fires toward level 2. Level 1 is correctly declared. The
  index's level-determination evidence is not yet written (`index.md` is still
  the scaffold template), so I checked the declaration against the stated
  rationale in `request.md`'s `Uncertainty` section instead, and record that
  substitution here.
- Every verification below was rerun in this session. Mutations ran on a copy
  of the working tree outside the repository; the repository working tree was
  never modified, and the only file this session wrote is this one.

## Verdict

`PASS`.

All seven scoped Lows are closed, each by a committed test that I confirmed
fails when the guard is removed or the fix reverted. Every acceptance criterion
is met. No critical, high, or medium finding. Four Lows are recorded below and
none of them blocks: three concern test coupling that has no cheaper
alternative, and one concerns a pathological-input case whose new behavior is
fail-closed and unchanged in direction from the accepted design.

## Per-criterion scores

| Criterion | Score | Basis |
| --- | --- | --- |
| Spec fidelity | 5/5 | The diff closes exactly L1 to L5, L8, and L9 and nothing else. `schema.py` is untouched, so L6's `plan`-satisfies rule stands as the accepted design; `projects/` is outside the diff, so L7 stays coordinator-owned. No refactor, no rename, no drive-by change: 141 insertions and 11 deletions, of which the three production hunks are 2 renamed parameters, 1 changed expression, and a 7-line guard. |
| Code review | 5/5 | The three production changes are correct and minimal, and I traced each one's reachability rather than reading the report's claim. L8 now leaves exactly one rule owning review targets in every plan state (readable, unreadable, symlinked, absent), which I verified by reading `_load_artifacts` and by mutating each arm separately. L9's lookup is total: every level-keyed lookup in the package now goes through `resolve_task_level`, a `TASK_LEVELS` membership test, or a raise, and `MINIMUM_EVIDENCE_ITEMS[FALLBACK_TASK_LEVEL]` is already pinned to the deepest floor by `tests/unit/test_task_dossier_generator.py:620`, so the new direct index cannot raise `KeyError`. L5 changes exactly one input class. |
| Empirical verification | 5/5 | Independently reproduced, not read from the report: all four L1 to L4 mutations with SHA-256 before and after, both L8 arms and L9 and L5 reverted separately, the L5 doc revert, the checker's exit behavior on eight input classes compared against `HEAD`'s module, the `projects` validator sweep against `HEAD` code, both gates on 3.10 and 3.14, and the frozen eval run directly under 3.14. Two probes the report did not run are recorded under Residual risks. |

## Findings

No critical findings. No high findings. No medium findings.

### L1 — Low, not blocking. The L9 test calls a private function

`tests/unit/test_task_dossier_validator.py:1124` calls
`task_dossier._validate_state(artifact, "bogus", diagnostics)` directly, so the
test is coupled to a private function's signature and to the package exporting
it.

The coupling is justified, and I checked the alternative rather than accepting
the report's assertion. `_validate_state` is called from exactly one place,
`validation.py:1244`, with the level returned by `_resolve_level`, which either
returns a member of `TASK_LEVELS` or `resolve_task_level(level)`
(`validation.py:1170-1190`). Both are always valid keys, so the unknown-level
branch is unreachable through `validate_dossier` and no public-path test can
pin it. The two existing public-path tests,
`test_an_invalid_level_fails_closed_to_level_2`
(`tests/unit/test_task_dossier_validator.py:1241`) and
`test_an_unresolvable_level_fails_closed_to_level_2`
(`tests/unit/test_task_dossier_summary.py:483`), pass under both the old
`.get(level, 1)` and the new index, so they do not cover the change. The new
test does: reverting line 365 to `MINIMUM_EVIDENCE_ITEMS.get(level, 1)` fails
it and nothing else. That satisfies TEST-003's operative requirement, a test
that calls production code and fails when the guard is removed.

Does not block: the acceptance criterion explicitly asks for a test on a branch
that is unreachable from the public entry, and this is the only way to write
one. Cost is a rename of `_validate_state` breaking one test.

### L2 — Low, not blocking. The L2 test patches a module attribute

`tests/integration/test_task_dossier_workflow.py:190` reaches the contiguity
guard by `mock.patch.object(scaffold_module, "template_text", split_rows)`, so
it depends on `apply_scaffold` resolving `template_text` through a module
attribute lookup rather than a local binding or an import alias. An otherwise
behavior-preserving refactor of that call would silently stop exercising the
guard.

Justified: the guard at `src/brichan/contracts/task_dossier/scaffold.py:91`
defends against a malformed index template, and the real template's eleven
rows are already pinned contiguous by
`test_index_template_links_authorities_without_duplicating_them`, so the state
is unreachable without injection. The test also earns extra value beyond the
mutation: `assertFalse((self.dossier / "index.md").exists())` pins that the
scaffold leaves nothing behind when it refuses.

Does not block: no cheaper route to a defensive guard, and the guard's own
mutation is now caught.

### L3 — Low, not blocking. L5 also drops whitespace-only path names

`src/brichan/contracts/task_dossier/contract_paths.py:71` changed the filter
from `if name` to `if name.strip()`. Beyond refusing empty input, this drops a
path name consisting only of spaces or tabs. A diff whose only changed path is
such a name therefore now exits 2 rather than printing `contract-path: no`.

I compared eight input classes against `HEAD`'s module and found exactly one
behavioral delta, the intended one. In particular a whitespace-padded contract
path (`  docs/policy/x.md  `) answers `contract-path: no` both before and
after, because neither version strips names before matching, and blank lines
mixed with real names are harmless in both. So this is not a regression in any
case a real `git diff --name-only` can produce; it only widens the refusal.

Does not block: the direction is fail-closed, never a false `contract-path: no`,
which is what the finding asked for. Worth one sentence if the filter is ever
revisited: the module filters on `name.strip()` but matches on `name`.

### L4 — Low, not blocking. The doc's exit-2 enumeration is not itself pinned

`tests/contract/test_task_dossier_contract.py:190-191` pins the pipeline's
`set -o pipefail` first line and the sentence
`Empty or whitespace-only input is refused`, but not the clause
`or empty input` that the change added to the exit-code enumeration at
`docs/workflows/task-dossier.md:253-254`. Removing that clause alone would
leave the contract test green and the document internally inconsistent.

Does not block: the actual exit code is pinned by
`test_empty_or_blank_input_is_refused_not_answered_no` and
`test_the_wrapper_refuses_empty_input`, and the surviving prose sentence still
states the behavior, so a reader is not misled.

## Test gaps

None owed. Under `docs/policy/reviewer.md`, a behavior change without a
committed regression test that fails on regression is a defect, not a gap. All
three behavior changes in this diff have one, and I confirmed each by reverting
the fix in isolation on a scratch copy:

- L5, the refusal, `tests/unit/test_contract_paths.py:83` and `:92`. Reverting
  `contract_paths.py:71-78` to `[name for name in names if name]` fails 3
  subtests and the wrapper test, 4 failures out of 9 tests.
- L5, the document, `tests/contract/test_task_dossier_contract.py:190-191`.
  Removing the `set -o pipefail` line and the refusal sentence fails
  `test_contract_path_list_equals_the_constants`, one failure beyond this
  suite's 4 baseline git-dependent failures on a non-repository scratch copy.
- L8, `tests/unit/test_task_dossier_validator.py:1108`. Each arm fails it
  alone: keying `_validate_unplanned_review_targets` back on `artifacts`
  (`validation.py:562`), and deleting the `"plan" not in present` guard
  (`validation.py:694`). 1 failure of 86 each time.
- L9, `tests/unit/test_task_dossier_validator.py:1124`. Reverting
  `validation.py:365` to `.get(level, 1)` fails it, 1 failure of 86.

The four pure-test Lows L1 to L4 are, by construction, the closing of previous
gaps; each mutation and its result is in Evidence.

Two coverage observations that are not gaps in this change, because they
concern behavior this diff did not alter, are recorded under Residual risks.

## Residual risks

1. The refusal collapses two distinct states into exit 2: a `git diff` that
   failed, and a `git diff` that legitimately changed nothing. The checker
   cannot tell them apart, and under `set -o pipefail` the pipeline reports the
   checker's 2 rather than Git's status, because pipefail yields the rightmost
   non-zero status. The coordinator must read the message, not only the code.
   This is the behavior the acceptance criterion specifies and the document
   states; WFS-005 L5's alternative, an `--expect-nonempty` flag, is the shape
   that would have preserved the distinction. No decision is required unless a
   caller needs to distinguish them.
2. Any caller outside this repository that treated exit 0 on an empty diff as
   "no review needed" now receives exit 2. The only in-repository caller is
   `scripts/check_contract_paths.py`, which delegates to `main` and is
   unchanged, and its wrapper behavior is now pinned by a test. A coordinator
   habit or an operator's shell history is outside the validator's sight.
3. Adjacent to L8 and not part of it: `docs/workflows/task-dossier.md:128-129`
   says a dossier without `plan.md` keeps its review targets and "the index's
   accepted-plan fields" null. The review-target half is enforced, and L8 has
   now unified it on the `present` set. The index half is enforced by nothing.
   I probed it rather than inferring it: a valid reduced level 1 dossier whose
   index declares `Accepted plan ID: GHOST-PLAN-001` and
   `Accepted plan version: 7`, with no `plan.md`, yields a diagnostic set
   identical to the same dossier with both fields null. The gap predates
   WFS-006 and sits outside every stated criterion, so it is a candidate
   follow-up Low for the coordinator, not a defect here.
4. Also adjacent and pre-existing: the index status-table rule keys on
   `artifacts`, not `present` (`validation.py:1066`). That is the right set for
   that rule, since an unreadable file is still a file the table should list,
   but it means `present` and `artifacts` remain deliberately different sets
   after L8. Anyone extending these rules should read `_load_artifacts`'
   docstring first; it states the distinction plainly.
5. Review-route deviation, for the coordinator to record: the `review` route in
   `config/model-routing.json` names the Codex runtime and `gpt-5.6-sol`, and
   this review ran a Claude session on `claude-opus-5`. Level 1 permits the
   routine route, and the session is fresh with no implementation context, but
   `docs/policy/reviewer.md` prefers a different verified provider from the
   implementer, and the implementer was a Claude session on `claude-opus-5-5`.
   Same provider family, and not a stronger model. Nothing in the change turns
   on this; it is a provenance fact the index should carry.
6. Coordinator-owned remainder, not a risk in the code: `index.md` and
   `receipt.md` are still scaffold templates, so `make dossiers` and
   `test_repository_checkout_validates_clean` stay red until they are
   completed, and `make check` cannot exit 0 until then. The count moved when
   this version replaced the scaffold `code-review.md`: 20 diagnostics before
   (15 on `index.md`, 5 on `code-review.md`), 16 after, all 16 on `index.md`,
   one of them the missing receipt reported against the index's
   `Canonical receipt path`. This file now validates clean; the index's status
   table does not yet match the real applicability and phase state this file
   declares, which accounts for two of the sixteen.
7. `report.md` records `Effective model: claude-opus-5-5` while the `implement`
   route names `claude-opus-5`. Recording what actually ran is what the
   evidence contract asks for, so this is correct as written; I note it only so
   the coordinator does not read it as an inconsistency to be edited away.

## Claim or decision

WFS-006 passes independent code review. Every acceptance criterion is verified
in this session: each of the L1 to L4 mutations now fails a committed test with
the mutated file restored byte-for-byte; L5 refuses empty and whitespace-only
input with exit 2, a stderr message, and no stdout, pinned by tests and stated
in the workflow document alongside the recommended `set -o pipefail`; L8 keys
the review-target rules and the required-artifact rule on the same `present`
set, pinned by a test on the unreadable-`plan.md` state; L9 leaves no
fail-open level lookup in the package and fails closed to the level 2 floor
with a test; every existing dossier under `projects` validates exactly as
before; and `make check` on Python 3.10 and 3.14 is red only through WFS-006's
own pending `index.md`, `code-review.md`, and `receipt.md`. Four non-blocking
Lows are recorded. No critical, high, or medium finding.

## Evidence

- Techstack verify, run before any other work:
  `"status": "match"`, observed snapshot SHA-256
  `98ac1e7e0a07371264f05acc47a27ad5bf8fbc6d2f90bfae297bec5dda7ed26b`, pointer
  `projects/brida-workflow-simplification/handoffs/WFS-006/snapshots/attempt-code-review-1-98ac1e7e0a07371264f05acc47a27ad5bf8fbc6d2f90bfae297bec5dda7ed26b.snapshot.json`,
  as-of `2026-09-26`. All nine selected rule files read:
  `techstacks/README.md`, `general.md`, `policy/README.md`,
  `policy/canonical.md`, `policy/task-dossiers.md`, `python/README.md`,
  `python/runtime.md`, `python/scripts.md`, `python/tests.md`.
- L1 mutation, drop `or path.is_symlink()` at `validation.py:134`:
  `tests.unit.test_task_dossier_validator` 86 run, 1 failure,
  `test_a_symlinked_required_artifact_is_not_also_reported_missing`.
  `validation.py` SHA-256
  `ef851365af79ae181aff39550dcff2e0801eb3806939985de2a43c4d6779e678` before and
  after.
- L2 mutation, contiguity `raise` to `pass` at `scaffold.py:91`:
  `tests.integration.test_task_dossier_workflow` 50 run, 2 failures,
  `test_scaffold_refuses_an_index_template_with_split_status_rows` and the
  pending-dossier `test_repository_checkout_validates_clean`. `scaffold.py`
  SHA-256 `c8c460080705d9abb764651f22d4755d1a2762b1eac41de75ce6ab7e2f5c8447`
  before and after.
- L3 mutation, `return tuple(record.artifacts)` at `generate.py:155`:
  `tests.unit.test_task_dossier_generator` 86 run, 1 failure,
  `test_artifacts_render_in_lifecycle_order_whatever_the_record_order`.
  `generate.py` SHA-256
  `c9d25da69baa8cf9c457c2db96b8ecf4db2424d8e6d9d577827dba6c202a6116` before and
  after.
- L4 mutation, delete `unreadable.sort(...)` at `summary.py:246`:
  `tests.unit.test_task_dossier_summary` 31 run, 1 failure,
  `test_unreadable_rows_are_listed_in_lifecycle_order`. `summary.py` SHA-256
  `861ed479ee10c48bad960bfebee382e640c71760b75c4204998dfaabe3b83546` before and
  after. All four values equal the ones `report.md` recorded.
- Revert runs, each in isolation, are listed under Test gaps. Files restored
  byte-for-byte: `contract_paths.py`
  `e830347f7fbc3e67066f65357f06ae83bf22bccef14c983924a6deb5eb5ccc0b`,
  `docs/workflows/task-dossier.md`
  `e1fae424d7ca10ebcaa7d6b75dddf2c72b62b9c48d437f126325f2bc6c66b5b3`, which is
  the post-change hash `report.md` names in its drift risk.
- L5 exit behavior, observed through `scripts/check_contract_paths.py`: empty,
  `\n`, and `  \n\t\r\n` each print
  `contract-path: no path names on input; refusing to decide` on stderr, print
  nothing on stdout, and exit 2; `README.md` prints `contract-path: no` and
  exits 0; `docs/policy/x.md` prints `contract-path: yes` and the path and
  exits 3; undecodable input still exits 2 with the UTF-8 message. Compared
  against the same module from `git archive HEAD`: the three empty cases are
  the only delta.
- L9 sweep over `src/brichan/contracts/task_dossier`: no
  `.get(<level>, <default>)` lookup anywhere. `validation.py:365`,
  `record.py:817`, and `summary.py:162` index through `resolve_task_level`;
  `schema.py:322` resolves before indexing; `scaffold.py:73-75` raises
  `ValueError`; `validation.py:1170` and `record.py:383` test `TASK_LEVELS`
  membership; the two CLIs restrict `--level` with argparse `choices`.
- L8 reachability traced in `_load_artifacts`
  (`validation.py:95-123`): an unreadable artifact is loaded into `artifacts`
  for its diagnostic but excluded from `present`, a symlink enters neither. So
  after the change exactly one rule owns review targets in each state, and the
  new test's level 1 eleven-artifact dossier with an undecodable `plan.md`
  requires `report.md`, demands null review targets under
  `_validate_unplanned_review_targets`, and no longer demands targets equal to
  the unreadable plan's empty ID.
- Dossier sweep: `scripts/validate_task_dossiers.py projects` under the changed
  code and under `HEAD`'s `src` and `scripts` from `git archive HEAD`, both
  against the same `projects` tree, produce identical output modulo the
  absolute root prefix: 20 issues across 18 dossiers, all on WFS-006
  `index.md` (15), `code-review.md` (5), and the missing `receipt.md` (1), none
  on `report.md`. Every other dossier validates as before.
- Gates on Python 3.10 and with `PYTHON=/opt/homebrew/bin/python3.14`:
  `PYTHONDONTWRITEBYTECODE=1 make check` exits 2 on both, stopping at
  `make test` with module boundaries 10 OK, unit 1069 OK, contract 153 OK, and
  integration 228 with the single `test_repository_checkout_validates_clean`
  failure whose diagnostics are all WFS-006's pending artifacts. Because make
  stops there, the remaining `check` prerequisites were run one by one under
  both interpreters: `techstack-eval`, `metrics`, `receipts`, `memory-check`,
  `path-check`, `readme-check`, `phase5-preflight`, and `package-check` exit 0,
  `sh -n bin/brichan` exits 0, and `dossiers` exits 2 on the same 20 issues.
  The frozen eval's recipe pins `python3`, so it was also run directly:
  `evals.techstack_context_v1.test_cases` 56 tests OK under 3.14.
- Probe for Residual risk 3: a reduced level 1 dossier with no `plan.md` and an
  index naming `GHOST-PLAN-001` version 7 yields the same diagnostics as the
  same dossier with both fields null.
- Plan-to-work check: `report.md`'s `Plan` section names each of the seven
  Lows, the mechanism for each, and the verification protocol, all before the
  `Changes` section. Every claim in `Changes` matches the diff, including that
  `scripts/check_contract_paths.py` is unchanged, and the diffstat holds no
  file the plan does not name.

## Uncertainty

- `Effective effort` is recorded as `medium`, the `review` route's configured
  effort in `config/model-routing.json`; this session did not report its own
  effort setting. The runtime and model differ from that route, as Residual
  risk 5 records.
- I did not re-verify the pre-work verify digest `c87ca1f7…` that `report.md`
  records, because the L5 edit to `docs/workflows/task-dossier.md` changed an
  evidence file of `techstacks/policy/task-dossiers.md` and that snapshot no
  longer matches the tree. The document's post-change hash
  `e1fae424…` is consistent with the drift the report predicted, and my own
  pre-work verify against the fresh snapshot returned `match`.
- Whether `.codex/config.toml` was modified by the implementer or predates the
  attempt is not something the working tree can settle. Its content is
  unrelated to WFS-006 and the task packet places it outside the diff, so it
  does not affect this verdict.
- No other unresolved uncertainty remains.
