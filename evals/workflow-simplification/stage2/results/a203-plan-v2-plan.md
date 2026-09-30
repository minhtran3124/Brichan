# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `WFS-A-203`
- Task level: `1`
- Artifact: `plan`
- Artifact version: `2`
- Origin: `plan-worker:2026-09-25-wfs-a-203-plan-v2`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `b6163b30-92ea-4643-be11-39ee7e5ad122`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `WFS-A-203-PLAN-001`
- Plan status: `draft`

## Claim or decision

Execute design.md version 2 in six steps. An implementer who reads
requirements.md, design.md, and this plan can do the work without further
context; every acceptance criterion of the recorded request maps to a step
and a check below. Version 2 closes every finding of plan-review.md version 1
(verdict `CHANGES REQUIRED` on plan version 1); the closure table is below.

1. Re-verify scope: run the Techstack verify command for Snapshot
   `attempt-plan-2-bd6ff653b4385638f80a525c72362232bf073f6e5d9214dfa607ce8efb36f2fe.snapshot.json`
   with `--as-of 2026-09-25` against the worktree root and require status
   `match`; reread the seven selected rule files it names.
2. Record the pre-change baseline: run the enumeration script from design.md
   version 2 section "Byte-identity proof" and require 244 calls with sha256
   `6a26f5041d52249b88d785bffb5b6fd826de46311ae5bc4cda15f7f7ea63ef69`
   (already reproduced by planning at commit `6fe3977`).
3. Edit `src/brichan/techstacks/model.py`: replace the body of
   `diagnostic_detail` with the guarded form in design.md, keeping the
   signature, the three return expressions, both helper functions, and the
   `KeyError` precedence for unknown codes unchanged. Every guard tests
   `is not None`, never truthiness.
4. Edit `src/brichan/techstacks/resolver.py`: add the `_add_located`
   errno-forwarding decision from design.md, with its comment.
5. Add the tests specified in design.md version 2 section "Test design" to
   `tests/unit/test_techstack_model.py` (new `DiagnosticDetailArgumentTest`,
   including the `errno_value=0` and `line=0` refusal cases and the
   all-three-explicit-`None` equality cases),
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
   (client-follow-up-questions.md version 2), recording each result: with
   `PYTHONDONTWRITEBYTECODE=1`, run `make test-unit`, `make test-contract`,
   `make test-integration`, then `make techstack-eval`, `make metrics`,
   `make receipts`, `make dossiers`, `make memory-check`, `make path-check`,
   `make readme-check`, `make phase5-preflight`, `make package-check`
   individually — first on the 3.10 shell interpreter, then again with
   `PYTHON=/opt/homebrew/bin/python3.14` — accepting only the failures named
   in "Expected residual failures" below. Do not substitute a single
   `make check`: in this worktree `check` aborts inside its `test`
   prerequisite at `test-contract` (`Makefile:24-28,75`), so
   `test-integration` — the layer that exercises the edited `resolver.py`
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

## Findings closure (plan-review.md version 1)

| Finding | Resolution in version 2 |
|---|---|
| `H1` (step 6(c) never ran integration or later gates) | Step 6(c) replaced by the coordinator-ratified per-target gate: each test layer and each of the nine `check` gates runs individually and is recorded individually; the plan now states why a single `make check` is insufficient in this worktree. |
| `M1` (`path-check` missing from residual-failure list) | "Expected residual failures" now lists `make path-check` (`unclassified root files: .git`) as the third worktree-only expected red, with its shared `.git` cause; requirements R7 matches. |
| `M2` (false claim that `make check` covers 3.14) | The false parenthetical is gone. Step 6(c) runs the full per-target gate twice: on the 3.10 shell interpreter and again with `PYTHON=/opt/homebrew/bin/python3.14`, per the coordinator's ratified gate and rule `TEST-001`; the reviewer's baseline (unit layer green on 3.14, 1026 tests) is the comparison point. |
| `M3` (refusal tests all-truthy; truthiness guard would pass) | Design v2 test design adds `errno_value=0` and `line=0` refusal cases per applicable class; design and requirements R3 now state the guard is `is not None` by contract, with the two production sources of falsy values cited. |
| `M4` (`_parse` safety rested on an unpinned docstring) | Design v2 adds a map-code slot-contract test in `tests/unit/test_techstack_markdown.py` asserting every `parse_map` failure carries `line is None and rule is None`, pinning the `MarkdownError` promise the design depends on (rule `GENERAL-004`); the two production edits stay exactly as reviewed. |
| `L1` (enumeration silent on the explicit-`None` call shape) | The enumeration is extended to 244 calls — every call repeated in the all-three-explicit-`None` shape — with new pre-change baseline digest `6a26f5041d52249b88d785bffb5b6fd826de46311ae5bc4cda15f7f7ea63ef69` recorded and reproduced at commit `6fe3977`; the registry-wide equality test covers the same shape. |
| `L2` (R5 regression specified mock-only) | The R5 test's `UNREADABLE_FILE` arm now uses the real condition (`chmod` mode `0` with `skipIf` euid 0 and cleanup, the `tests/unit/test_techstack_filesystem.py:196-200` pattern) through the full production chain; the mock remains only for `RESOURCE_LIMIT`, which `chmod` cannot produce. |
| `L3` (accuracy notes: "public signature"; fixture citation) | Requirements R1 now records `diagnostic_detail` as module-internal (absent from `src/brichan/techstacks/__init__.py:56-96`), strengthening acceptance criterion 3; design v2 cites the design fixtures as asserted at, not defined at, `tests/unit/test_techstack_model.py:553-568`. |

## Acceptance criteria mapping

- Byte-identical valid calls, proven: steps 2 and 6(b) (244-call enumeration
  digest, both call shapes) plus the design constraint that the return
  expressions stay textually unchanged (checked in review on the diff).
  Requirements R2.
- Refusal per class with removal-sensitive tests: step 5 unit tests; each of
  the three refusal classes fails its test when the guard is removed, and
  the falsy-value cases fail a guard weakened to truthiness. Requirements
  R3, R6; rule `TEST-003`.
- No frozen contract moves; production callers unaffected, call sites shown:
  design.md "Call-site inventory"; step 5 resolver regression (real
  condition) and markdown contract tests; step 6(c) with untouched design
  fixtures and Snapshot digests. Requirements R1, R5; rules `PY-003`,
  `GENERAL-004`.
- Gates: steps 6(c) and 6(d) on both interpreters. Requirements R7; rules
  `GENERAL-001`, `TEST-001`.

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
  by this task's pending coordinator- and reviewer-owned artifacts
  (`index.md`, `code-review.md`, `pr-desc.md`), outside the implementer's
  authorized paths.

## Scope findings

- Planning discovered no path outside the declared Techstack scope paths.
  The implementation touches `src/brichan/techstacks` and `tests/unit` only
  (the added third test file, `tests/unit/test_techstack_markdown.py`, is
  inside the declared scope path `tests/unit`); evidence reads also covered
  `tests/contract` and `tests/integration` (baseline failures), all within
  scope. `resolver.py` was not named in the recorded request but is inside
  the declared scope path `src/brichan/techstacks`; no re-resolution is
  needed.
- Premise correction to the recorded request, upheld by review: stage-2
  finding L4 called the silent-drop path unreachable from production.
  Planning showed it is production-reachable — `_errno_outcome`
  (`src/brichan/techstacks/filesystem.py:307-309`) attaches a real errno to
  every errno-mapped, non-`FILESYSTEM_ERROR` observation code, and those
  reach `diagnostic_detail` via `_add_located`
  (`src/brichan/techstacks/resolver.py:266-277`) — and plan-review version 1
  reproduced it against a real unreadable selected rule file. The objective
  stands, but a guard without step 4 would break resolution. This is why the
  plan touches `resolver.py`.
- `CHANGELOG.md` stays out of scope, per plan-review's residual-risk note:
  no gate requires an entry and `diagnostic_detail` is not public API; any
  entry is a coordinator decision at close.

## Open questions

- None. The version-1 open question (the completion-gate carve-out for this
  dossier's pending coordinator- and reviewer-owned artifacts) was answered
  and ratified by the coordinator on 2026-09-25 in
  client-follow-up-questions.md version 2, which this plan adopts verbatim
  in step 6(c) and "Expected residual failures".

## Evidence

- requirements.md, options.md, and design.md version 2 in this dossier;
  plan-review.md version 1 (the findings closed above); and the planning
  baseline runs of 2026-09-25 at commit `6fe3977`: the reproduced 122-call
  digest, the new 244-call digest, and the observed silent drops
  (`diagnostic_detail("UNREADABLE_FILE", line=0)` and `errno_value=0` both
  returning the registry detail).
- client-follow-up-questions.md version 2 — the coordinator-ratified
  completion gate and expected-red list this plan adopts.
- Techstack Snapshot pointer:
  `projects/brida-workflow-simplification/handoffs/WFS-A-203/snapshots/attempt-plan-2-bd6ff653b4385638f80a525c72362232bf073f6e5d9214dfa607ce8efb36f2fe.snapshot.json`,
  sha256
  `bd6ff653b4385638f80a525c72362232bf073f6e5d9214dfa607ce8efb36f2fe`,
  verify status `match` on 2026-09-25 (attempt `attempt-plan-2`, acknowledged
  Context IDs `general`, `policy`, `policy-dossiers`, `python`,
  `python-runtime`, `python-tests`, `root`).

## Uncertainty

- No unresolved uncertainty remains. Superseded version 1 of every planner
  artifact is preserved under `versions/v1/`, per the dossier contract
  (`DOSSIER-003`).
