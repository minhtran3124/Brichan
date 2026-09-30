# WFS-B-203 independent code review

Task: `WFS-B-203`. Plan `WFS-B-203-PLAN-001`, version 2. Attempt
`attempt-review-1`. Reviewed on 2026-09-25.

Reviewer: an independent Claude Code main-agent session with no implementation
context. Policy: `docs/policy/reviewer.md`,
`docs/policy/operating-principles.md` section 5.

Reviewed tree state: four modified files, uncommitted, 66 insertions and 2
deletions, `git status --short` clean of anything else. All source edits are
timestamped 12:07:06; every verification recorded below ran after 12:19, so no
edit followed the last successful check.

## 1. Verdict

**PASS.**

## 2. Scores

| Criterion | Score |
| --- | --- |
| Spec fidelity | 5 / 5 |
| Code review | 4 / 5 |
| Empirical verification | 5 / 5 |

### Spec fidelity — 5 / 5

Each acceptance criterion was re-derived here, not taken from the report.

**AC1, byte-identical details for every previously valid call — proven.** A
scratch script loaded `git show HEAD:src/brichan/techstacks/model.py` as a
separate module beside the working one and compared `diagnostic_detail` across
the full previously valid grid: all 58 registry codes; `FILESYSTEM_ERROR` at
errno `None`, -1, 0, 1, 2, 13, 20, 62, 2^31-1, 2^63-1 and -2^63;
`INVALID_LEAF` at every line 0..65537 against each of the 20
`LEAF_GRAMMAR_RULES` members; and each call repeated in the in-module caller
shape with all three keywords passed and `None` where unused. Result: 1,310,954
calls, **0 mismatches**, and the old and new result digests are equal at
`4a30dfa3c37eb70dfaffc6f4d199e88c5bcc74252cc44d7d3c109fc70d86f4a0`. (This digest
differs from the one in `worker-report.md` because the two scripts hash
different tuple shapes over different grids; both are internally consistent, and
both report zero mismatches.)

Previously raising calls also behave identically. Ten edge cases were compared
old against new and all ten matched, including the four
`invalid_leaf_detail` refusals, the unknown-leaf-rule refusal, and `KeyError`
for an unknown code — with and without slots. The ordering matters: the new
body evaluates `DIAGNOSTIC_SPECS[code]` at `model.py:597` before the slot check
at `model.py:606`, so an unknown code still raises `KeyError` first, exactly as
before.

**AC2, refusal and its tests — holds.** `model.py:606` raises
`ValueError(f"{code} must not carry {' or '.join(unsupported)}")`. That mirrors
the established refusal style in the same module, most directly
`Diagnostic._check_location` at `model.py:2314`,
`raise ValueError(f"{self.code} must not carry a path")`. Guard-removal
mutation was run against a scratch mirror of `src/` and `tests/` so no tracked
file was touched: deleting the two-line `if unsupported:` block leaves all 140
focused tests running but **5 subtests fail**, one per distinct refusal class —
errno on an unslotted code, errno on `INVALID_LEAF`, `line` alone on an
unslotted code, `rule` alone on an unslotted code, and `line`+`rule` on
`FILESYSTEM_ERROR`.

The second test's `model.diagnostic(...)` assertions are sound rather than
incidentally satisfied: `UNREADABLE_FILE` and `FILESYSTEM_ERROR` are both field
class `P` (`model.py:458`, `model.py:461`), so the supplied
`path="techstacks/general.md"` is valid and `_check_location` cannot be the
`ValueError` source. Only the new guard can raise there.

**AC3, no registry, cap, literal, sort key, fixture digest, or public signature
change — holds.** The diff touches only the body and docstring of
`diagnostic_detail`, two lines plus a docstring paragraph in
`_Resolver._add_located`, and two test modules. `inspect.signature` on the
working tree returns
`(code: 'str', *, errno_value: 'int | None' = None, line: 'int | None' = None, rule: 'str | None' = None) -> 'str'`,
unchanged. `DIAGNOSTIC_REGISTRY` codes are equal between `HEAD` and the working
tree in both order and content (58 codes). `test_every_frozen_fixture_matches_its_recorded_size_and_digest`
and `test_every_design_fixture_is_frozen_byte_for_byte` pass.

Production call sites, traced independently rather than read from the report.
`diagnostic_detail` has exactly two callers, both in `model.py`:

- `model.py:2352`, in the `diagnostic()` factory — the sole route by which
  `resolver._Findings.add` (`resolver.py:244`) builds a Diagnostic.
- `model.py:2262`, in `Diagnostic.__post_init__` — safe by construction, since
  `_errno_value()` (`model.py:2269`) returns `None` unless the code is
  `FILESYSTEM_ERROR` and `_leaf_slots()` (`model.py:2277`) returns
  `(None, None)` unless the code is `INVALID_LEAF`.

`diagnostic_detail` is not re-exported from any `__init__`, and nothing outside
`src/brichan/techstacks/model.py` and the two test modules references it.

Of the roughly forty `findings.add` / `diagnostic(` sites in `resolver.py`,
exactly two can forward a slot:

- `_add_located` (`resolver.py:266`), reached from `_observation_diagnostic`
  (`resolver.py:296`) and the evidence loop (`resolver.py:515`), forwards
  `errno_value`. This is the one real production hazard, and it is the one the
  change closes at `resolver.py:278`.
- `_parse` (`resolver.py:345`) forwards `error.line` and `error.rule` for *any*
  `MarkdownError` code, not just `INVALID_LEAF`. This was the highest-risk
  unverified claim in the report, so it was checked two ways. Statically:
  `MarkdownError` gains a line or rule from only two construction sites,
  `markdown.py:360` (`normalize_document` under `attribute=True`) and
  `markdown.py:426` (`_Cursor.fail` given a non-`None` rule); `parse_map`
  builds its cursor with `end_rule` and `shape_rule` both defaulting to `None`
  (`markdown.py:523`, `markdown.py:399-405`) and calls `normalize_document`
  without `attribute`, and every map-side `cursor.fail()` is unattributed
  (`markdown.py:526, 534, 554, 558`). Empirically: 240,000 byte-mutated map and
  leaf documents derived from the real `techstacks/` files produced 112,637
  `INVALID_MAP` errors, every one with `line is None and rule is None`, and
  98,548 `INVALID_LEAF` errors, every one carrying both — **0 violations**. The
  two codes random mutation did not reach were exercised directly: a
  129-row map raises `MAP_ROW_LIMIT` with `line=None rule=None`, and an
  18-selector row raises `SELECTOR_LIMIT` with `line=None rule=None
  context_id='c0'`. Replaying every observed `(code, line, rule)` shape through
  `model.diagnostic` produced no guard crash.

So no production caller can trip the new refusal.

**AC4, `make check` — holds.** See section "Verification" below.

### Code review — 4 / 5

The implementation is correct and idiomatic. One point costs it a mark, and it
is a maintainability hazard rather than a defect; both are detailed in section
3 and section 5.

Two things are worth crediting. First, `resolver._add_located`'s new clearing
is not an invention: `filesystem.py:959-962` already forwards `errno_value`
only on the `FILESYSTEM_ERROR` branch and drops it for `FILESYSTEM_IO_ERROR`,
`RESOURCE_LIMIT`, `UNSUPPORTED_SAFE_OPEN` and `SYMLINK_REJECTED`. The change
follows an established project pattern rather than adding a new one. Second,
the new `"FILESYSTEM_ERROR"` literal in `resolver.py:278` is a registry member
and the literal already appears in `filesystem.py` (lines 93, 308, 959) and
`lifecycle.py:957`, so it does not newly violate `PY-003`'s single-sourcing
rule as the project practises it.

`PY-001` holds: standard library only, no new import. `PY-002` holds: no evals
import. `PY-004` is untouched. `GENERAL-004` holds: regression tests accompany
the behavior change.

### Empirical verification — 5 / 5

Every numbered claim in `worker-report.md` that could be re-run here was
re-run, and all of them held: byte identity, both guard-removal mutations, the
call-site trace, the 140-test focused run under both interpreters, and the
full `make check` breakdown including the `path-check` disclosure. Nothing was
accepted on assertion alone. No file was edited after the last successful
check.

## 3. Findings

**No critical, high, or medium findings.**

### Low 1 — the slot map and the rendering branches are stated twice, unpinned

`model.py:598` declares
`taken = {"FILESYSTEM_ERROR": ("errno_value",), "INVALID_LEAF": ("line", "rule")}`,
and `model.py:607` and `model.py:609` independently re-spell the same two codes
as the branches that actually render those slots. Nothing pins the two
statements equal. A future slotted code added to one and not the other fails
quietly in opposite directions: added to `taken` but not to the branches, its
slot is accepted and then silently dropped — the exact defect this task
removes; added to the branches but not to `taken`, the renderer becomes
unreachable because the guard refuses first.

Reproducing the first direction, on a scratch copy:

```
# in diagnostic_detail, extend the map only
taken = {"FILESYSTEM_ERROR": ("errno_value",), "INVALID_LEAF": ("line", "rule"),
         "UNREADABLE_FILE": ("errno_value",)}
>>> diagnostic_detail("UNREADABLE_FILE", errno_value=13)
'a required file could not be read'   # errno accepted, silently dropped
```

The existing suite stays green. This is classified low and not a defect: it
violates no acceptance criterion and no stated invariant, the registry is
closed, and adding a third slotted code is a Design-level change that would
draw its own review. It is recorded because the project already pins an
analogous cross-statement invariant — `tests/unit/test_techstack_markdown.py:678`
asserts the leaf-rule fixture table covers `model.LEAF_GRAMMAR_RULES` exactly —
so the pattern for closing it exists.

### Low 2 — `make check` has a third pre-existing failure the packet did not name

`path-check` exits 2 with `unclassified root files: .git`
(`scripts/check_repository_paths.py`), in addition to the two contract failures
the packet described. It is the same script and the same detached-worktree
cause — `.git` is a file, not a directory, in a worktree — and it is unrelated
to this change. The implementer disclosed it in `worker-report.md` under "Risks
and ambiguities". Recorded here so the packet's known-failure list can be
corrected for the next attempt; not attributable to the change.

## 4. Test gaps

1. **No committed test proves AC1's byte identity.** The proof exists only as
   scratch scripts, run twice independently — by the implementer and here — and
   both are gone with their scratch directories. The permanent suite asserts
   that details are *correct*, not that they are *unchanged across this edit*.
   That is the normal cost of a one-time migration proof and is acceptable; it
   is listed so the evidence's transience is on the record rather than assumed.

2. **No test pins the `taken` map to the rendering branches** (Low 1). The
   closing test would be small: for every code in `taken`, assert that
   supplying its slots changes the returned detail away from
   `DIAGNOSTIC_SPECS[code].detail`, and for every code not in `taken`, assert
   each slot is refused.

3. **The resolver regression test is skipped under euid 0.** The
   `@unittest.skipIf(os.geteuid() == 0, ...)` at
   `tests/unit/test_techstack_resolver.py:682` follows the existing pattern at
   `tests/unit/test_techstack_filesystem.py:196, 291, 664`, so it is the right
   call. But it is the *only* test covering the production errno path, and
   removing the `resolver.py:278` clearing is caught by nothing else. A CI
   runner executing as root would lose the whole guard. This is the same
   exposure the pre-existing filesystem tests already carry, so it is not new.

4. **`root_api_error_for_code` is unguarded and untested for this shape.**
   `model.py:401-410` ignores `errno_value` for every code except
   `PROJECT_ROOT_FILESYSTEM_ERROR` — the same silent-drop shape this task
   removed from `diagnostic_detail`, in the parallel root/API outcome registry.
   It is outside the stated objective and outside the task's scope paths, so it
   is a residual risk rather than a gap in this change; noted so it is not
   mistaken for having been swept in.

## 5. Residual risks and required human decisions

### Residual risks

1. **The silent drop moved rather than disappeared.** Production still discards
   a real observation errno for `UNREADABLE_FILE`, `SYMLINK_REJECTED`,
   `PATH_COMPONENT_NOT_DIRECTORY`, `DIRECTORY_REJECTED`,
   `SPECIAL_FILE_UNAVAILABLE` and `UNSUPPORTED_SAFE_OPEN` — now at
   `resolver.py:278` instead of inside `diagnostic_detail`. Observable behavior
   is unchanged, the drop is now explicit and documented at
   `resolver.py:273-276`, and it matches `filesystem.py:959-962`. The
   coordinator authorized this as option A. Flagged because the L4 finding's
   spirit — diagnostic information silently lost — is narrowed to one function,
   not eliminated from the package.

2. **`errno_value=None` remains indistinguishable from omission.** An explicit
   `diagnostic_detail("UNREADABLE_FILE", errno_value=None)` is still accepted.
   Telling the two apart would need a sentinel default, which changes the
   frozen public signature and would breach AC3. The implementer identified
   this correctly and chose the constraint over the purity. Concur.

3. **`root_api_error_for_code` carries the same unguarded shape** (test gap 4).

4. **The refusal is a genuine behavior change for out-of-tree callers.** Any
   caller outside this repository passing an unsupported slot now gets a
   `ValueError` where it previously got the fixed detail. `diagnostic_detail`
   is not exported from any `__init__` and is not part of a published API
   surface, so the blast radius is nil in practice.

### Required human decisions

1. **Whether to close Low 1 now or defer.** A pinning test is cheap and the
   repository has the precedent. Deferring is defensible: the registry is
   closed and a third slotted code is a Design change. Coordinator's call —
   this reviewer would not block the change on it.

2. **Whether `root_api_error_for_code` gets its own follow-up task.** It is the
   same defect class in the sibling registry. If TECHSTACK-002 stage 2 intended
   L4 to cover the package rather than the one function, a follow-up is owed.

3. **Correct the packet's known-failure list** to name `path-check` alongside
   the two `tests/contract/test_repository_paths.py` failures, so a later
   worker in a detached worktree does not treat it as a new regression.

4. **Reviewer artifact naming.** `docs/policy/reviewer.md`, under "Task dossier
   reviews", says a reviewer writes `plan-review.md` and `code-review.md`. The
   packet directed exactly one file, `review.md`, and this handoff directory
   holds no `requirements.md`, `design.md`, `plan.md`, or `receipt.md`, so it
   is a handoff directory and not a task dossier in the
   `docs/workflows/task-dossier.md` sense. The packet was followed. If this
   task is later promoted to a tracked dossier, `DOSSIER-001` requires a
   canonical `receipt.md` here and this file would need renaming to
   `code-review.md`.

## Verification

All commands were run from this detached worktree's root, on Python 3.10.11
unless noted. Absolute paths are elided here to keep this artifact free of the
home-path prefixes `DOSSIER-002` governs.

1. **Techstack verify, run before any other work.** `bin/brichan techstacks
   verify --project-root <worktree> --snapshot-json
   projects/brida-workflow-simplification/handoffs/WFS-B-203/snapshots/attempt-review-1-d76a1315b4d62fbd4730278133b7b56ad2f2fa95b4e1aa1fed010a836fb44075.snapshot.json
   --as-of 2026-09-25` returned `"status": "match"` with
   `observed_snapshot_sha256` =
   `d76a1315b4d62fbd4730278133b7b56ad2f2fa95b4e1aa1fed010a836fb44075`. All
   seven required selected rule files were then read in full:
   `techstacks/README.md`, `techstacks/general.md`,
   `techstacks/policy/README.md`, `techstacks/policy/task-dossiers.md`,
   `techstacks/python/README.md`, `techstacks/python/runtime.md`,
   `techstacks/python/tests.md`.

2. **Focused tests, Python 3.10.**
   `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest
   tests.unit.test_techstack_model tests.unit.test_techstack_resolver` —
   140 tests, **OK**.

3. **Focused tests, Python 3.14** (`TEST-001`). Same command under
   `/opt/homebrew/bin/python3.14` — 140 tests, **OK**.

4. **Byte-identity proof.** Working `diagnostic_detail` compared against the
   `HEAD` module over 1,310,954 previously valid calls: **0 mismatches**,
   equal digests. Ten previously raising edge cases: all identical.

5. **Guard-removal mutation A.** `src/` and `tests/` mirrored into the
   scratchpad; the `if unsupported:` block deleted from the mirror's
   `model.py`. Focused run: **FAILED (failures=5)** — all five refusal
   subtests, and nothing else.

6. **Guard-removal mutation B.** Mirror's `model.py` restored; the two-line
   `if code != "FILESYSTEM_ERROR": errno_value = None` deleted from the
   mirror's `resolver.py`. Focused run: **FAILED (errors=1)** —
   `test_an_unreadable_selected_rule_file_blocks_without_its_errno` raises
   `ValueError: UNREADABLE_FILE must not carry errno_value`. This confirms the
   test exercises the real production errno path (errno 13 reaches
   `_add_located`) and is not an assertion that cannot fail, satisfying
   `TEST-003`. It also confirms the production crash option A prevents was
   real, not hypothetical.

7. **Parser fuzz.** 240,000 byte-mutated map and leaf documents, seeded, over
   the real `techstacks/` files: 0 violations of "only `INVALID_LEAF` carries
   `line`/`rule`". `MAP_ROW_LIMIT` and `SELECTOR_LIMIT` exercised directly,
   both unattributed.

8. **`PYTHONDONTWRITEBYTECODE=1 make check`** — exits 2.
   - metrics self-test: 10 run, **OK**.
   - `test-unit`: **1029 run, OK**.
   - `test-contract`: 148 run, **2 failures, 1 skipped**. Both are
     `unclassified root files: .git` —
     `test_current_path_and_link_contracts_pass`
     (`tests/contract/test_repository_paths.py:159`) and
     `test_every_non_ephemeral_root_file_is_classified`
     (`tests/contract/test_repository_paths.py:64`). These are exactly the two
     known worktree-only failures the packet described. Reported, not fixed.
   - `make` stops at that first failing prerequisite, so the remaining
     `check` prerequisites were each run on their own:
     `test-integration` **exit 0** (222 run, OK), `techstack-eval` **exit 0**
     (56 run, OK), `metrics` 0, `receipts` 0, `dossiers` 0, `memory-check` 0,
     `readme-check` 0, `phase5-preflight` 0, `package-check` 0,
     `sh -n bin/brichan` 0. `path-check` **exit 2**, same `.git` cause (Low 2).

   Apart from the known worktree-only `.git` classification failures, `make
   check` is clean. AC4 is met.

9. **Tree state.** `git status --short` shows ` M` on exactly the four expected
   files and nothing else. `git diff --stat`: 4 files changed, 66 insertions,
   2 deletions. No commit, branch, push, or remote action was taken. This
   review file sits in the gitignored handoff directory
   (`.gitignore:67`, `/projects/*/handoffs/*/`).

All mutation and identity work was done on copies under the session scratchpad.
No tracked file was modified by this review.

Techstack verification acknowledgement: yes; snapshot_sha256=d76a1315b4d62fbd4730278133b7b56ad2f2fa95b4e1aa1fed010a836fb44075
