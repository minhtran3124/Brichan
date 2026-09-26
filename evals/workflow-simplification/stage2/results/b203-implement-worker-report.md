# WFS-B-203 worker report

Attempt: `attempt-implement-1`. Outcome: **implemented under plan version 2
(option A).**

- Plan version 1 escalated with no code change. Its original scope could not be
  met without breaking a production caller.
- The coordinator then authorized option A and added
  `src/brichan/techstacks/resolver.py` to scope.
- All changes are uncommitted.

## Plan

Plan `WFS-B-203-PLAN-001`, version 1, written before any code edit.

Approach:

1. Treat an argument as "supplied" when it is not `None`. This is required
   because the two in-module callers, `diagnostic()` and
   `Diagnostic.__post_init__`, always pass all three keywords, with `None` for
   the slots a code does not use.
2. In `diagnostic_detail`, raise `ValueError` (the refusal style of
   `invalid_leaf_detail` and `Diagnostic.__post_init__`) when a code other than
   `FILESYSTEM_ERROR` gets a non-`None` `errno_value`, or a code other than
   `INVALID_LEAF` gets a non-`None` `line` or `rule`. That covers
   `INVALID_LEAF` given an errno and `FILESYSTEM_ERROR` given a line or rule.
3. Add a unit test for each refusal class, plus a byte-identity sweep over every
   registry code that compares the new function with the old logic on every call
   that was valid before.

Files: `src/brichan/techstacks/model.py`, one test module under `tests/unit`.

Risks identified before editing, and checked first:

- **R1 (production reachability).** The packet says the extra-argument path is
  unreachable from production. If any production path passes a non-`None` slot
  to a code that does not take it, the refusal turns a valid Resolution into a
  crash. I checked this before editing, and it **turned out to be true, so the
  plan stopped at step 1** (see Risks and ambiguities).

## Plan version 2

Plan `WFS-B-203-PLAN-001`, version 2 (option A, authorized by the coordinator
after the version 1 escalation; `src/brichan/techstacks/resolver.py` added to
scope). Written before any code edit.

Approach:

1. `resolver._add_located` is the only resolver site that forwards
   `errno_value`, and both observation paths (map and leaf reads through
   `_observation_diagnostic`, evidence reads) go through it. It clears
   `errno_value` for every code except `FILESYSTEM_ERROR`. That errno was never
   rendered, so every detail stays the same.
2. `model.diagnostic_detail` looks up the code first, so an unknown code still
   raises `KeyError` exactly as before. It then raises `ValueError(f"{code}
   must not carry ...")`, which mirrors `Diagnostic._check_location`'s "must not
   carry a path", when any non-`None` slot is not one the code takes:
   `errno_value` only for `FILESYSTEM_ERROR`, `line` and `rule` only for
   `INVALID_LEAF`. "Supplied" means not `None`, because `diagnostic()` and
   `Diagnostic.__post_init__` always pass all three keywords.
3. Tests:
   - A unit test in `tests/unit/test_techstack_model.py` for each refusal
     class: an errno on a non-errno code, including `INVALID_LEAF`; a line or
     rule on an unslotted code; a line or rule on `FILESYSTEM_ERROR`. Each one
     asserts `ValueError`, which only the new guard can raise for those inputs.
   - A resolver regression test in `tests/unit/test_techstack_resolver.py`: a
     mode-000 selected leaf still yields `blocked` with an exact
     `UNREADABLE_FILE` diagnostic. It is skipped under euid 0, following the
     existing filesystem-suite pattern.
4. Byte-identity proof: a scratch script loads the `HEAD` version of `model.py`
   alongside the working version and compares `diagnostic_detail` outputs over
   the full grid of previously valid calls: every code, every leaf rule, every
   line in bounds, and errno values including `None`, negative, zero, and large.

Files: `src/brichan/techstacks/model.py`,
`src/brichan/techstacks/resolver.py`, `tests/unit/test_techstack_model.py`,
`tests/unit/test_techstack_resolver.py`.

Risks: the frozen public signature stays unchanged; no registry, literal, or
fixture is touched. The new guard must never fire from `Diagnostic.__post_init__`.
That is safe because it derives slots from `detail` and returns `None` for
unslotted codes.

## Changes

Plan version 1 made no change. Plan version 2 changed four files (66
insertions, 2 deletions), all uncommitted:

- `src/brichan/techstacks/model.py`, `diagnostic_detail`:
  - It looks up `DIAGNOSTIC_SPECS[code]` first, so an unknown code still
    raises `KeyError` as before.
  - It then raises `ValueError("<CODE> must not carry <slot>[ or <slot>]")`
    for any non-`None` slot the code does not take: `errno_value` only for
    `FILESYSTEM_ERROR`, `line` and `rule` only for `INVALID_LEAF`.
  - The docstring states the contract.
  - The signature, registries, caps, literals, and sort key are untouched.
- `src/brichan/techstacks/resolver.py`, `_Resolver._add_located`:
  `errno_value` is cleared for every code except `FILESYSTEM_ERROR` before it
  reaches `_Findings.add`. The docstring says why. This is the only resolver
  site that forwarded an errno.
- `tests/unit/test_techstack_model.py`, `DiagnosticRegistryTest`: one test per
  refusal class.
  - `test_an_errno_on_a_code_that_renders_none_is_a_caller_error` covers an
    unslotted code, and `INVALID_LEAF` with valid leaf slots.
  - `test_a_leaf_slot_on_a_code_other_than_invalid_leaf_is_a_caller_error`
    covers `line` alone and `rule` alone on an unslotted code, and both on
    `FILESYSTEM_ERROR`. It checks both `diagnostic_detail` and the public
    `diagnostic()` builder.
- `tests/unit/test_techstack_resolver.py`, `ReachabilityTest`:
  - Added `test_an_unreadable_selected_rule_file_blocks_without_its_errno`.
    A mode-000 selected leaf yields a `blocked` Resolution whose only diagnostic
    equals `model.diagnostic("UNREADABLE_FILE", path="techstacks/general.md")`,
    with detail `a required file could not be read`.
  - It is skipped under euid 0, following the existing filesystem-suite
    pattern.

## Verification

### Escalation evidence (plan version 1, unedited tree)

1. Techstack verify command (run before any other work): `status: match`,
   `observed_snapshot_sha256` =
   `b9695daf4ff6755275ef00e3def38f972192b25ae3afc003c1f776aa260aebd8`. All seven
   required rule files were read, along with `docs/policy/operating-principles.md`.
2. Call-site trace:
   - `src/brichan/techstacks/model.py` `diagnostic()` →
     `diagnostic_detail(code, errno_value=..., line=..., rule=...)`.
   - `src/brichan/techstacks/model.py` `Diagnostic.__post_init__` passes the
     slots it parses back out of `detail`, which are `None` for every
     non-slotted code, so it is safe.
   - `src/brichan/techstacks/resolver.py` `_Findings.add(code, **location)` →
     `diagnostic(code, **location)`.
   - `src/brichan/techstacks/resolver.py` `_add_located(code, relative_path,
     errno_value)` forwarded `errno_value` for every observation code. It is
     called from `_observation_diagnostic` (map and leaf reads) and from the
     evidence-read loop.
   - `src/brichan/techstacks/filesystem.py` `_errno_outcome` maps errnos to
     non-`FILESYSTEM_ERROR` codes (`UNREADABLE_FILE`, `SYMLINK_REJECTED`,
     `PATH_COMPONENT_NOT_DIRECTORY`, `DIRECTORY_REJECTED`,
     `SPECIAL_FILE_UNAVAILABLE`, `UNSUPPORTED_SAFE_OPEN`) and still attaches
     `errno_value`. The helper-frame parser sets an integer `errno_value` for
     every non-OK child status.
   - `src/brichan/techstacks/markdown.py`: only the leaf cursor (code
     `INVALID_LEAF`) carries `line` and `rule`. The map cursor has no
     `end_rule` or `shape_rule`, and `normalize_document` runs with
     `attribute=False` for maps.
   - Other `diagnostic(...)` call sites pass no slots: `resolver.py` in
     `_approval_diagnostic`, the waiver rebuild in exception matching,
     `UNUSED_INPUT_WITHOUT_ROOT`, and `UNSUPPORTED_PLATFORM`; and `model.py`
     for `DIAGNOSTIC_LIMIT`.
3. Suite probe: a scratch-only wrapper around `diagnostic_detail` recorded
   extra-argument calls without changing behavior. Results:
   - `tests/unit`: 1026 run, 0 failures.
   - `tests/contract`: 148 run, 2 failures (the known worktree-only `.git`
     failures).
   - `tests/integration`: 222 run, 0 failures.
   - **Zero** extra-argument calls were recorded. The errno path had no coverage.
4. Direct reproduction on a scratch copy of the repository's `techstacks/` tree
   (its own `git init`, and the attempt's own
   `techstack-input-attempt-implement-1.json`), calling `resolve_context`:
   - A mode-000 `techstacks/general.md` made the wrapper log
     `UNREADABLE_FILE {'errno_value': 13}`.
   - The Resolution was `blocked` with `UNREADABLE_FILE techstacks/general.md
     'a required file could not be read'`.
   - With the refusal alone, this would have raised `ValueError` out of
     `resolve_context`.

### Implementation evidence (plan version 2)

5. Focused tests:
   `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest
   tests.unit.test_techstack_model tests.unit.test_techstack_resolver` ran 140
   tests, OK, on Python 3.10. The same modules on Python 3.14 ran 140 tests, OK.
6. Guard-removal checks (TEST-003). Each mutation was applied in place,
   restored from a backup, and confirmed identical with `cmp`:
   - Guard disabled in `diagnostic_detail`: both refusal tests fail (5 subtest
     failures). The resolver test still passes.
   - Errno clearing disabled in `_add_located`: the resolver regression test
     errors with `ValueError: UNREADABLE_FILE must not carry errno_value`,
     which is the production crash option A prevents. Both refusal tests still
     pass.
7. Byte-identity proof. A scratch script loaded
   `git show HEAD:src/brichan/techstacks/model.py` as a separate module and
   compared it with the working `diagnostic_detail` over every previously
   valid call:
   - Coverage: all 58 codes. The 56 unslotted codes are called with no slot.
     `FILESYSTEM_ERROR` is called with errno `None`, -1, 0, 1, 2, 13, 20, 62,
     2^31-1, and 2^63-1. `INVALID_LEAF` is called for every line from 0 to
     65537 against each of the 20 leaf grammar rules.
   - Each call was also repeated in the in-module caller shape: all three
     keywords passed, `None` where unused.
   - Result: 1,310,826 calls, 0 mismatches. The SHA-256 of all old details was
     `d500316a14d429585ade4dc0a51b7e1c9375f52aa2235abe3f5050345b99efa8`, and the
     new details produced the same digest.
   - The resolver change only clears an errno that no unslotted detail renders,
     so resolver output is unchanged (item 5, and the full suites below).
8. `PYTHONDONTWRITEBYTECODE=1 make check` exited 2:
   - metrics self-test: 10 run, OK.
   - `test-unit`: 1029 run, OK.
   - `test-contract`: 148 run, 2 failed (skipped=1). The failures were
     `test_current_path_and_link_contracts_pass` and
     `test_every_non_ephemeral_root_file_is_classified`, both
     `unclassified root files: .git`. These are the two known worktree-only
     failures.
   - `make check` stops at that first failing prerequisite, so each remaining
     prerequisite was run on its own:
     - `test-integration`: 222 run, OK.
     - `techstack-eval`: 56 run, OK.
     - `metrics`, `receipts`, `dossiers`, `memory-check`, `readme-check`,
       `phase5-preflight`, `package-check`: all exit 0.
     - `sh -n bin/brichan`: exit 0.
     - `path-check`: exit 2, `unclassified root files: .git`. It runs the same
       `scripts/check_repository_paths.py` classification as the two known
       contract failures, so it has the same worktree-only cause and is not
       caused by this change.
9. `git status --short`: ` M` on the four files listed under Changes and
   nothing else. This report sits in the gitignored dossier directory.
   `git diff --stat`: 4 files changed, 66 insertions(+), 2 deletions(-).

## Risks and ambiguities

- **Intended behavior change:** a call that supplies a non-`None` slot its code
  does not render now raises `ValueError` instead of returning the fixed detail.
  Such calls silently dropped their argument before, so they fall outside
  "every call that was valid before". The one production source of them, errno
  forwarding in `_add_located`, is closed in the same change.
- **"Supplied" means non-`None`:** an explicit `errno_value=None` on
  `UNREADABLE_FILE` is still accepted. The signature defaults to `None`, and
  both in-module callers always pass all three keywords, so an explicit `None`
  cannot be told apart from an omitted argument without changing the public
  signature, which is frozen.
- **Unknown codes:** an unknown code still raises `KeyError` before any slot
  check, as before.
- **Environment:** `make check` cannot exit 0 in this detached worktree because
  of `.git` classification. It fails in `test-contract` (the two known
  failures) and in `path-check` (the same check at the script level). The
  packet named the two contract failures; `path-check` is the same pre-existing
  cause, reported here rather than fixed.
- **Test skip:** the regression test depends on file permissions and is skipped
  under euid 0, where `chmod 000` does not deny reads. CI running as root would
  not exercise it.
