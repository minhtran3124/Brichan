# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `WFS-A-203`
- Task level: `1`
- Artifact: `plan`
- Artifact version: `3`
- Origin: `plan-worker:2026-09-25-wfs-a-203-plan-v3`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `9e873e25-e1da-4639-8f3b-5ef21cedbba8`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `WFS-A-203-PLAN-001`
- Plan status: `draft`

`draft` is correct while coordinator acceptance is outstanding; it is the one
field that records acceptance, which is a coordinator step, while the sibling
artifacts' phase state `passed` records only that planner work is complete at
the required evidence depth (plan-review version 2 finding `L2`, second
note).

## Claim or decision

Execute design.md version 3 in six steps. An implementer who reads
requirements.md, design.md, and this plan can do the work without further
context; every acceptance criterion of the recorded request maps to a step
and a check below. Version 3 closes every finding of plan-review.md version 2
(verdict `CHANGES REQUIRED` on plan version 2); the closure table is below.
The two production edits are unchanged from version 2, which plan-review
version 2 verified by construction; every version-3 change is to
verification design.

1. Re-verify scope: run the Techstack verify command for Snapshot
   `attempt-plan-3-008ff53c2dd71f14fc9f541d7e9cd5e93bd0cbfffc1bb7061ef0a6f300a8b67e.snapshot.json`
   with `--as-of 2026-09-25` against the worktree root and require status
   `match`; reread the seven selected rule files it names.
2. Record the pre-change baseline: run the enumeration script from design.md
   version 3 section "Byte-identity proof" and require 244 calls with sha256
   `6a26f5041d52249b88d785bffb5b6fd826de46311ae5bc4cda15f7f7ea63ef69`
   (reproduced at commit `6fe3977` by the version-2 and version-3 planning
   sessions and by plan review). Also reproduce the two class (b) pre-change
   probes from design.md "Evidence" so the removal-sensitivity claim is
   re-checked on the tree being edited:
   `diagnostic_detail("INVALID_LEAF", errno_value=13, line=1, rule="TITLE")`
   and the `errno_value=0` companion must return
   `leaf bytes do not match the leaf grammar at line 1: TITLE`.
3. Edit `src/brichan/techstacks/model.py`: replace the body of
   `diagnostic_detail` with the guarded form in design.md, keeping the
   signature, the three return expressions, both helper functions, and the
   `KeyError` precedence for unknown codes unchanged. Every guard tests
   `is not None`, never truthiness; in the `INVALID_LEAF` branch the
   `errno_value` guard precedes the `invalid_leaf_detail` call.
4. Edit `src/brichan/techstacks/resolver.py`: add the `_add_located`
   errno-forwarding decision from design.md, with its comment.
5. Add the tests specified in design.md version 3 section "Test design" to
   `tests/unit/test_techstack_model.py` (new `DiagnosticDetailArgumentTest`:
   registry-wide equality including the all-three-explicit-`None` shape;
   class (c) errno refusals excluding `INVALID_LEAF`; the dedicated class (b)
   arm `errno_value=13, line=1, rule="TITLE"` and `errno_value=0, line=1,
   rule="TITLE"`; class (a)+(c) `line`/`rule` refusals including `line=0`;
   unknown-code `KeyError`; factory propagation),
   `tests/unit/test_techstack_resolver.py` (R5 regression: real `chmod`
   condition for `UNREADABLE_FILE`, mock only for `RESOURCE_LIMIT`), and
   `tests/unit/test_techstack_markdown.py` (map-code slot-contract test
   pinning `line is None and rule is None` for every `parse_map` failure).
   Add nothing else; move nothing.
6. Verify, smallest first, leaving all changes uncommitted:
   (a) `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest
   tests.unit.test_techstack_model tests.unit.test_techstack_resolver
   tests.unit.test_techstack_markdown`;
   (b) rerun the step-2 enumeration and require the identical digest;
   (c) run the coordinator-ratified per-target gate
   (client-follow-up-questions.md version 2) so that every named suite
   actually runs under both interpreters, recording each result:
   - 3.10 arm (shell interpreter): with `PYTHONDONTWRITEBYTECODE=1`, run
     `make test-unit`, `make test-contract`, `make test-integration`,
     `make techstack-eval`, `make metrics`, `make receipts`,
     `make dossiers`, `make memory-check`, `make path-check`,
     `make readme-check`, `make phase5-preflight`, `make package-check`
     individually, plus `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
     metrics/test_validate_metrics.py -v` — the module `make test` runs as
     its first recipe line (`Makefile:25`) that no per-target substitute
     covers (plan-review version 2 finding `M2`; green at baseline, 10
     tests).
   - 3.14 arm: rerun the same `make` targets with
     `PYTHON=/opt/homebrew/bin/python3.14`, except the frozen eval, which
     must be invoked directly —
     `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 -m unittest
     evals.techstack_context_v1.test_cases -v` from the worktree root —
     because the `techstack-eval` recipe pins a literal `python3` and does
     not follow `PYTHON=` (`Makefile:39-40`; `techstacks/python/tests.md`
     Verification; plan-review version 2 finding `M1`; green at baseline,
     56 tests). Also rerun the metrics test module under 3.14:
     `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 -m unittest
     metrics/test_validate_metrics.py -v` (green at baseline).
   Accept only the failures named in "Expected residual failures" below.
   Do not substitute a single `make check`: in this worktree `check` aborts
   inside its `test` prerequisite at `test-contract` (`Makefile:24-28,75`),
   so `test-integration` — the layer that exercises the edited `resolver.py`
   end to end — and every later gate would silently never run;
   (d) `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py
   projects` and report its output.

Authorized implementation paths (all inside the Techstack scope paths):

- `src/brichan/techstacks/model.py`
- `src/brichan/techstacks/resolver.py`
- `tests/unit/test_techstack_model.py`
- `tests/unit/test_techstack_resolver.py`
- `tests/unit/test_techstack_markdown.py`

Excluded: every registry, cap, literal, sort key, fixture, public signature,
packaged resource, and policy file; `src/brichan/techstacks/filesystem.py`
and `src/brichan/techstacks/markdown.py` (read-only authorities for this
task); committing, branching, or any remote or destructive action.

## Findings closure (plan-review.md version 2)

| Finding | Resolution in version 3 |
|---|---|
| `H1` (class (b) refusal test could not fail: slotless `INVALID_LEAF` + `errno_value` already raises today) | Design v3 test design gives class (b) a dedicated arm that supplies slots the code does take alongside the inapplicable errno: `diagnostic_detail("INVALID_LEAF", errno_value=13, line=1, rule="TITLE")` and the falsy companion `errno_value=0` in the same shape, each asserted to raise `ValueError`. Both return the leaf detail on the unguarded tree (re-observed by this session), so the arm fails when the `errno_value is not None` guard is omitted or inverted, and the `0` case fails a truthiness guard. `INVALID_LEAF` is excluded from the class (c) errno loop, whose membership there was the inert assertion. Requirements R6 states the same shape as a requirement. |
| `M1` (3.14 arm never ran the frozen eval under 3.14: `techstack-eval` pins literal `python3`) | Step 6(c)'s 3.14 arm invokes the eval module directly under the 3.14 interpreter (`PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 -m unittest evals.techstack_context_v1.test_cases -v`) instead of `make techstack-eval PYTHON=...`, per the `techstacks/python/tests.md` Verification note and rule `TEST-001`; requirements R7 matches. Verified green at baseline by this session (56 tests, `OK`). |
| `M2` (`metrics/test_validate_metrics.py` ran under neither interpreter in the per-target substitution) | Step 6(c) adds the module explicitly on both arms via direct `-m unittest` invocation, restoring the coverage `make test`'s first recipe line (`Makefile:25`) would have provided; requirements R7 matches. Verified green at baseline by this session under both interpreters (10 tests, `OK` each). |
| `L1` (expected-red attribution for `make dossiers` omitted the absent `receipt.md`) | "Expected residual failures" now names the fourth cause: the canonical `receipt.md` does not exist yet (`canonical receipt does not exist`), coordinator-owned like the other three. This session's baseline validator run (38 issues) confirms every diagnostic names `index.md`, `code-review.md`, `pr-desc.md`, or the absent `receipt.md`. |
| `L2` (overstated falsy-value warrant; `Plan status: draft` beside phase state `passed`) | Requirements R3, brief.md, and design.md restate the warrant to match the evidence: `line=0` and errno `0` are production-real but neither reaches a code that does not take it today; `is not None` is required as the contract future callers must hit and as what the falsy-value tests assert. The `Plan status` field keeps `draft` deliberately — acceptance is the coordinator's step — and the "Plan status" section above now says so. |

Version-1 findings (`H1`, `M1`–`M4`, `L1`–`L3` of plan-review.md version 1)
remain closed: plan-review version 2 checked every row of the version-2
closure table against the artifact it names and confirmed each holds. That
table is preserved in `versions/v2/plan.md`; its two qualifications became
version-2 findings `M1` and `H1`, closed above.

## Acceptance criteria mapping

- Byte-identical valid calls, proven: steps 2 and 6(b) (244-call enumeration
  digest, both call shapes) plus the design constraint that the return
  expressions stay textually unchanged (checked in review on the diff).
  Requirements R2.
- Refusal per class with removal-sensitive tests: step 5 unit tests; each of
  the three refusal classes returns a detail on the unguarded tree and fails
  its test when the guard is removed — class (b) now via the slots-supplied
  shape — and the falsy-value cases fail a guard weakened to truthiness.
  Requirements R3, R6; rule `TEST-003`.
- No frozen contract moves; production callers unaffected, call sites shown:
  design.md "Call-site inventory"; step 5 resolver regression (real
  condition) and markdown contract tests; step 6(c) with untouched design
  fixtures and Snapshot digests. Requirements R1, R5; rules `PY-003`,
  `GENERAL-004`.
- Gates: steps 6(c) and 6(d), with every named suite genuinely run under
  both interpreters. Requirements R7; rules `GENERAL-001`, `TEST-001`.

## Expected residual failures at step 6(c)

All ratified by the coordinator in client-follow-up-questions.md version 2;
any failure not listed here is a defect the implementer must diagnose.

- The two pre-existing worktree-only failures in
  `tests/contract/test_repository_paths.py` (`unclassified root files:
  .git`), reproduced by planning on 2026-09-25 before any change.
- `make path-check` (`unclassified root files: .git`), the same
  detached-worktree cause — the worktree's `.git` is a file, not a
  directory — reproduced by plan review at baseline.
- While this dossier is in flight: `make dossiers` and
  `tests/integration/test_task_dossier_workflow.py`
  (`test_repository_checkout_validates_clean`), whose diagnostics are owned
  by this task's pending coordinator- and reviewer-owned artifacts —
  `index.md`, `code-review.md`, and `pr-desc.md` in template state, plus the
  not-yet-created canonical `receipt.md`
  (`Task identity.Canonical receipt path: canonical receipt does not
  exist`) — all outside the implementer's authorized paths. This session's
  baseline run of the dossier validator reports 38 issues, every one naming
  one of those four causes and none naming a planner-owned artifact. A fifth
  expected diagnostic appears once plan version 3 exists:
  `plan-review.md: Review target.Reviewed plan version: review must reference
  the exact accepted plan version '3', found '2'` — reviewer-owned, cleared
  by the next plan review; observed by this session (39 issues total after
  authoring version 3).

## Scope findings

- Planning discovered no path outside the declared Techstack scope paths.
  The implementation touches `src/brichan/techstacks` and `tests/unit` only
  (the added third test file, `tests/unit/test_techstack_markdown.py`, is
  inside the declared scope path `tests/unit`); evidence reads also covered
  `tests/contract` and `tests/integration` (baseline failures), all within
  scope. The step 6(c) gate additions (`Makefile`, `metrics/`, `evals/`) are
  read-only command invocations, not edits. `resolver.py` was not named in
  the recorded request but is inside the declared scope path
  `src/brichan/techstacks`; no re-resolution is needed.
- Premise correction to the recorded request, upheld by two review rounds:
  stage-2 finding L4 called the silent-drop path unreachable from
  production. Planning showed it is production-reachable — `_errno_outcome`
  (`src/brichan/techstacks/filesystem.py:307-309`) attaches a real errno to
  every errno-mapped, non-`FILESYSTEM_ERROR` observation code, and those
  reach `diagnostic_detail` via `_add_located`
  (`src/brichan/techstacks/resolver.py:266-277`) — and plan-review version 2
  demonstrated by revert that a guard without step 4 breaks resolution. The
  objective stands; this is why the plan touches `resolver.py`.
- `CHANGELOG.md` stays out of scope, per plan-review's residual-risk note:
  no gate requires an entry and `diagnostic_detail` is not public API; any
  entry is a coordinator decision at close.

## Open questions

- None. Plan-review version 2's one uncertainty item — whether `H1` warrants
  a plan version 3 — was decided by the coordinator in this task packet:
  version 3 it is, and no finding implied a code-design revision, so the two
  production edits are byte-identical to the reviewed version-2 design.

## Evidence

- requirements.md, options.md, and design.md version 3 in this dossier;
  plan-review.md version 2 (the findings closed above; its version-1 closure
  check covers the superseded table now in `versions/v2/plan.md`); and this
  session's baseline runs of 2026-09-25 at commit `6fe3977`: the reproduced
  244-call digest, the class (b) pre-change probes (slots-supplied calls
  return the leaf detail; slotless calls already raise), the direct 3.14
  eval run (56 tests, `OK`), the metrics test module under both interpreters
  (10 tests, `OK` each), `make -n techstack-eval
  PYTHON=/opt/homebrew/bin/python3.14` printing a literal `python3` command,
  and the dossier validator baseline (38 issues, all coordinator- or
  reviewer-owned causes).
- client-follow-up-questions.md version 2 — the coordinator-ratified
  completion gate and expected-red list this plan adopts, executed truthfully
  per plan-review version 2 findings `M1` and `M2`.
- Techstack Snapshot pointer:
  `projects/brida-workflow-simplification/handoffs/WFS-A-203/snapshots/attempt-plan-3-008ff53c2dd71f14fc9f541d7e9cd5e93bd0cbfffc1bb7061ef0a6f300a8b67e.snapshot.json`,
  sha256
  `008ff53c2dd71f14fc9f541d7e9cd5e93bd0cbfffc1bb7061ef0a6f300a8b67e`,
  verify status `match` on 2026-09-25 (attempt `attempt-plan-3`, acknowledged
  Context IDs `general`, `policy`, `policy-dossiers`, `python`,
  `python-runtime`, `python-tests`, `root`).

## Uncertainty

- No unresolved uncertainty remains. Superseded versions 1 and 2 of every
  planner artifact are preserved under `versions/v1/` and `versions/v2/`,
  per the dossier contract (`DOSSIER-003`), and were not edited.
