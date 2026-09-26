# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `WFS-A-203`
- Task level: `1`
- Artifact: `plan`
- Artifact version: `1`
- Origin: `plan-worker:2026-09-25-wfs-a-203-plan-v1`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `26d661ea-d979-48bc-b7c7-a87c69edad4a`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `WFS-A-203-PLAN-001`
- Plan status: `draft`

## Claim or decision

Execute design.md version 1 in six steps. An implementer who reads
requirements.md, design.md, and this plan can do the work without further
context; every acceptance criterion of the recorded request maps to a step
and a check below.

1. Re-verify scope: run the Techstack verify command for Snapshot
   `attempt-plan-1-0aac87619568852fedf8ba257cde51531e6b078a3af247bc550f8764600caae6.snapshot.json`
   with `--as-of 2026-09-25` against the worktree root and require status
   `match`; reread the seven selected rule files it names.
2. Record the pre-change baseline: run the enumeration script from design.md
   section "Byte-identity proof" and require 122 calls with sha256
   `57b96aa6d240374df464cd4b01d9f5f74cfd123240c3577b5eba1bc73d5167c0`
   (already reproduced by planning at commit `6fe3977`).
3. Edit `src/brichan/techstacks/model.py`: replace the body of
   `diagnostic_detail` with the guarded form in design.md, keeping the
   signature, the three return expressions, both helper functions, and the
   `KeyError` precedence for unknown codes unchanged.
4. Edit `src/brichan/techstacks/resolver.py`: add the `_add_located`
   errno-forwarding decision from design.md, with its comment.
5. Add the tests specified in design.md section "Test design" to
   `tests/unit/test_techstack_model.py` (new `DiagnosticDetailArgumentTest`)
   and `tests/unit/test_techstack_resolver.py` (errno-carrying observation
   regression). Add nothing else; move nothing.
6. Verify, smallest first: (a)
   `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest
   tests.unit.test_techstack_model tests.unit.test_techstack_resolver`;
   (b) rerun the step-2 enumeration and require the identical digest;
   (c) `PYTHONDONTWRITEBYTECODE=1 make check` (includes the 3.10 shell
   interpreter and the repository's 3.14 gate), accepting only the failures
   named in "Expected residual failures" below; (d)
   `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py
   projects` and report its output. Leave all changes uncommitted.

Authorized implementation paths (all inside the Techstack scope paths):

- `src/brichan/techstacks/model.py`
- `src/brichan/techstacks/resolver.py`
- `tests/unit/test_techstack_model.py`
- `tests/unit/test_techstack_resolver.py`

Excluded: every registry, cap, literal, sort key, fixture, public signature,
packaged resource, and policy file; `src/brichan/techstacks/filesystem.py`
and `src/brichan/techstacks/markdown.py` (read-only authorities for this
task); committing, branching, or any remote or destructive action.

## Acceptance criteria mapping

- Byte-identical valid calls, proven: steps 2 and 6(b) (enumeration digest)
  plus the design constraint that the return expressions stay textually
  unchanged (checked in review on the diff). Requirements R2.
- Refusal per class with removal-sensitive tests: step 5 unit tests; each of
  the three refusal classes fails its test when the guard is removed.
  Requirements R3, R6; rule `TEST-003`.
- No frozen contract moves; production callers unaffected, call sites shown:
  design.md "Call-site inventory"; step 5 resolver regression test; step
  6(c) with untouched design fixtures and Snapshot digests. Requirements R1,
  R5; rules `PY-003`, `GENERAL-004`.
- Gates: step 6(c) and 6(d). Requirements R7; rule `GENERAL-001`.

## Expected residual failures at step 6(c)

- The two pre-existing worktree-only failures in
  `tests/contract/test_repository_paths.py` (`unclassified root files:
  .git`), reproduced by planning on 2026-09-25 before any change.
- Dossier-validation failures for this task's own pending coordinator- and
  reviewer-owned artifacts (`index.md`, `plan-review.md`, `code-review.md`,
  `pr-desc.md`), surfaced by `make dossiers` and by
  `tests/integration/test_task_dossier_workflow.py`
  (`test_repository_checkout_validates_clean`), reproduced by planning
  before any change. These are outside the implementer's authorized paths;
  see the open question below.

## Scope findings

- Planning discovered no path outside the declared Techstack scope paths.
  The implementation touches `src/brichan/techstacks` and `tests/unit` only;
  evidence reads also covered `tests/contract` (baseline failures), all
  within scope. `resolver.py` was not named in the recorded request but is
  inside the declared scope path `src/brichan/techstacks`; no re-resolution
  is needed.
- Premise correction to the recorded request: stage-2 finding L4 called the
  silent-drop path unreachable from production. Planning showed it is
  production-reachable — `_errno_outcome`
  (`src/brichan/techstacks/filesystem.py:307-309`) attaches a real errno to
  every errno-mapped, non-`FILESYSTEM_ERROR` observation code, and those
  reach `diagnostic_detail` via `_add_located`
  (`src/brichan/techstacks/resolver.py:266-277`). The objective stands, but
  a guard without step 4 would break resolution of, for example, a project
  with an unreadable selected rule file. This is why the plan touches
  `resolver.py`.

## Open question

- Requirements R7 carve-out (b): `make check` cannot go fully green while
  this dossier's coordinator- and reviewer-owned artifacts remain in
  template state, independent of the implementation. The coordinator must
  either bring those artifacts to a validating state before the
  implementer's final gate or accept the carve-out as stated. Not a design
  blocker; recorded for plan acceptance.

## Evidence

- requirements.md, options.md, and design.md version 1 in this dossier, and
  the planning baseline runs of 2026-09-25 at commit `6fe3977`: full
  `make check` reproducing exactly the two worktree-only contract failures,
  the dossier validator reproducing this dossier's pending-artifact
  diagnostics, and the 122-call enumeration digest.
- Techstack Snapshot pointer:
  `projects/brida-workflow-simplification/handoffs/WFS-A-203/snapshots/attempt-plan-1-0aac87619568852fedf8ba257cde51531e6b078a3af247bc550f8764600caae6.snapshot.json`,
  sha256
  `0aac87619568852fedf8ba257cde51531e6b078a3af247bc550f8764600caae6`,
  verify status `match` on 2026-09-25 (attempt `attempt-plan-1`, acknowledged
  Context IDs `general`, `policy`, `policy-dossiers`, `python`,
  `python-runtime`, `python-tests`, `root`).

## Uncertainty

- The open question above (coordinator decision on the R7 carve-out) is the
  one unresolved item; it does not change the design or the implementation
  steps. No other unresolved uncertainty remains.
