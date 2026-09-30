# WFS-002 Blind Review: Submissions X and Y

Reviewer: independent worker agent (Task WFS-002-REVIEW), 2026-09-25.

Method: read both patches and all modules/tests; confirmed `TASK.md` and
`test_visible.py` are byte-identical between X and Y; ran all six unittest
discoveries; ran differential and fuzz checks from `scratch/` (`check_t1.py`,
`check_t2.py`, `check_t3.py`) comparing X and Y behavior on adversarial
inputs; cross-ran each submission's added tests against the other
implementation. Scores are 1–5 per criterion, each judged independently.

## Verification: required unittest runs

| Directory | Result |
|---|---|
| X/t1-ledger-summary | Ran 11 tests — OK |
| X/t2-prerelease-order | Ran 10 tests — OK |
| X/t3-path-guard | Ran 4 tests — OK |
| Y/t1-ledger-summary | Ran 14 tests — OK |
| Y/t2-prerelease-order | Ran 15 tests — OK |
| Y/t3-path-guard | Ran 14 tests — OK |

Cross-runs (informative): X's t1 tests on Y's implementation fail with 1
error (the RecursionError bug below); Y's t1 tests pass on X. Both t2 suites
pass on either implementation. The t3 suites fail on each other only on the
trailing-separator ambiguity described below.

---

## T1: ledger summary

The two implementations are algorithmically identical (same split-on-LF,
same blank handling, same single-pass dedup, same whole-file pairing). A
differential run over adversarial inputs (CRLF, bare CR, BOM, duplicate JSON
keys, NaN, lone surrogates, finish-before-launch, orphan dupes) found exactly
one behavioral difference: deeply nested JSON.

### Findings

- **HIGH — Y crashes on a deeply nested JSON line instead of counting it
  undecodable.** `Y/t1-ledger-summary/ledger_summary.py:23` catches only
  `ValueError` around `json.loads`; a line such as `b"[" * 100000` raises
  `RecursionError`, which escapes `summarize` entirely.
  Reproduce: `summarize(b"[" * 100000)` → `RecursionError`; X returns
  `undecodable=1`. TASK.md rule 2 requires any non-conforming line to be
  *skipped and counted*; one corrupt line taking down the whole summary
  violates that and the function's own docstring
  (`Y/.../ledger_summary.py:13-15` promises `None` for invalid JSON).
  X handles this explicitly (`X/t1-ledger-summary/ledger_summary.py:21-24`)
  and pins it in a test (`X/t1-ledger-summary/test_rules.py:37` — the
  `b"[" * 100000` line in `test_undecodable_line_kinds`).
- **LOW — Y decodes every line twice.** `Y/.../ledger_summary.py:52` decodes
  for the blank check, then `_decode_record` decodes again at line 18.
  Performance-only; no behavioral effect.

### Scores

| Criterion | X | Y |
|---|---|---|
| Spec fidelity | 5 | 4 |
| Code review | 5 | 4 |
| Test evidence | 5 | 4 |

Test evidence notes: both suites are strong and rule-by-rule. Y's suite has
some coverage X lacks (exact returned key set at `test_ledger_summary.py:227`,
same-worker-different-id negative at :166). X's suite has the one case that
actually matters as a differentiator — the deep-nesting crash shape — plus
CRLF-with-missing-final-LF (`test_rules.py:93`). Y's suite would not catch a
reintroduction of the crash its implementation actually has, which is what
costs it the point.

**Better overall: X.** Same design, but X survives an adversarial line that
crashes Y, and X's tests pin that case.

---

## T2: prerelease ordering

Both found the same root cause (prerelease tuples compared lexically as
strings, `semver_order.py` old line `return -1 if pre_a < pre_b else 1`) and
fixed it the same way: per-identifier comparison with numeric-vs-alphanumeric
rules. Both also fixed two latent validation holes in the same commit: the
`$` anchor accepting `"1.0.0\n"` (X: `fullmatch`,
`X/t2-prerelease-order/semver_order.py:25`; Y: `\Z`,
`Y/t2-prerelease-order/semver_order.py:15`) and `\d` matching non-ASCII
digits (both add `re.ASCII`).

Verification: both pass the full SemVer 2.0.0 §11 example chain pairwise
(361 pairs), plus an extended 19-version chain including `rc.2`/`rc.10`,
`--`, and multi-field prereleases. 300,000 random and structured fuzz
comparisons found **zero** behavioral disagreements between X and Y,
including error behavior (`ValueError` on identical input sets), antisymmetry
holds for both, and both sorts are stable on equal-precedence inputs.

### Findings

- **LOW (both, identical) — validation was tightened beyond the reported
  bug.** `"1.0.0\n"` and non-ASCII-digit versions were accepted by the
  original and now raise `ValueError`. TASK.md says "keep the existing
  ValueError behavior" but also "follow SemVer 2.0.0 precedence in full";
  these inputs are invalid SemVer, so treating the old acceptance as a bug is
  defensible. Both resolved this ambiguity the same way and both documented
  and tested it (X `test_regression.py:58-68`; Y `test_semver_order.py:85-97`).
  Noted, not penalized.
- **LOW — X's `_compare_prerelease` misreports equal inputs.**
  `X/t2-prerelease-order/semver_order.py:66` returns `1` for two identical
  tuples (it assumes the caller's `pre_a == pre_b` guard at :39). Unreachable
  through the public API today — confirmed by fuzz — but the helper's contract
  is a trap for future callers. Y's equivalent (`_cmp(len(a), len(b))`,
  `Y/.../semver_order.py:65`) returns 0 correctly. Informational.

### Scores

| Criterion | X | Y |
|---|---|---|
| Spec fidelity | 5 | 5 |
| Code review | 5 | 5 |
| Test evidence | 5 | 5 |

Test evidence notes: X uniquely covers >64-bit numeric identifiers
(`test_regression.py:36-40`) and the `"-"`-is-alphanumeric ASCII trap
(`test_regression.py:42-45`). Y uniquely exercises `parse` directly, more
invalid shapes (`"v1.0.0"`, `" 1.0.0"`, `"1.0.0.0"`), and valid edge parses
(`test_semver_order.py:99-101`). Either suite would fail loudly if the
lexical-tuple compare were reintroduced.

**Better overall: tie.** Behaviorally indistinguishable fixes of the same
root cause, both with strong regression suites.

---

## T3: path guard normalization

Both keep all five security invariants, checking `..`, `.brichan`, absolute,
backslash and NUL against the value **as supplied** before any normalization.
A 300,000-case fuzz over hostile component combinations found **zero** cases
where either implementation returns a path violating any documented invariant
(no `..`, no `.brichan` any case, no leading `/`, no `\`/NUL, no empty or `.`
component, final component ends `.jsonl`). Both raise only `ValueError`.

The single behavioral difference — exhaustively characterized by fuzz, all
1,739 accept/reject differences are of this one shape — is the trailing
separator:

- Input `"ledger/workers.jsonl/"` (also `.../`, `/.`, `/./`, `//`):
  X rejects (`X/t3-path-guard/path_guard.py:41` checks the *supplied* final
  component, which is `""`); Y accepts and returns `"ledger/workers.jsonl"`
  (`Y/t3-path-guard/path_guard.py:42` checks the *normalized* final
  component).

**This is a genuine ambiguity in TASK.md, resolved differently.** TASK.md
says "components joined by a single `/`, with empty and `.` components
removed", which read literally supports Y (a trailing `/` yields an empty
component to be removed). The original docstring's invariant "The final
component ends in `.jsonl`" supports X's stricter reading (a trailing `/`
names a directory, and under the original code it was rejected). Both
document their choice explicitly (X docstring :20-21; Y docstring :12-15 and
test `test_path_guard.py:96` `test_suffix_checked_on_the_normalized_final_component`).
Neither resolution is penalized as such.

### Findings

- **MEDIUM — Y's updated docstring misstates its own contract.**
  `Y/t3-path-guard/path_guard.py:16-17` says "The invariants above are
  checked against the components as supplied, so a rejected component is
  never normalized away" — but the fifth invariant (final component ends in
  `.jsonl`) is checked on the *normalized* list (:42), not as supplied.
  Reproduce: `validate_ledger_path("ledger/workers.jsonl/")` is accepted,
  although the final component as supplied (`""`) does not end in `.jsonl`.
  The behavior is defensible; the docstring claim about it is inaccurate,
  and for a security guard the docstring is the contract callers audit.
- **LOW — Y widens acceptance beyond the user report.** The report cited only
  `.` components and doubled `/`; accepting a trailing `/` (directory-shaped
  input) and silently returning the file path is extra permissiveness a
  caller could trip over. Mitigated by TASK.md's literal wording and by Y's
  explicit tests; X made the opposite (conservative) choice and equally
  documented and tested it (`X/t3-path-guard/test_normalize.py:32-35`).
- **INFO — divergent error messages.** Both replace the old
  `"path is not normalized"` message; `ValueError` type is preserved in both,
  as required.

### Scores

| Criterion | X | Y |
|---|---|---|
| Spec fidelity | 5 | 5 |
| Code review | 5 | 4 |
| Test evidence | 5 | 5 |

Test evidence notes: both suites cover every invariant, including
normalization-cannot-launder cases (`a/../b`, `./../`, `.brichan`
interleaved with `.`/`//`, `//` absolute). Y additionally pins useful
positive cases X lacks (`"...jsonl"`, `"..a/b.jsonl"`,
`".brichan-old/workers.jsonl"` at `test_path_guard.py:66-81`); X pins the
directory-shaped rejections. Each suite would catch a regression of its own
contract.

**Better overall: X, narrowly.** Implementations are equally safe; X's
stricter trailing-`/` stance fits a security guard better and its docstring
is internally consistent, while Y's docstring misdescribes where its suffix
check runs.

---

## Totals

| Task | Criterion | X | Y |
|---|---|---|---|
| T1 | Spec fidelity | 5 | 4 |
| T1 | Code review | 5 | 4 |
| T1 | Test evidence | 5 | 4 |
| T2 | Spec fidelity | 5 | 5 |
| T2 | Code review | 5 | 5 |
| T2 | Test evidence | 5 | 5 |
| T3 | Spec fidelity | 5 | 5 |
| T3 | Code review | 5 | 4 |
| T3 | Test evidence | 5 | 5 |
| **Total** | | **45** | **41** |

**Overall preference: X** (T1: X, T2: tie, T3: X narrowly). The decisive
difference is T1's unhandled `RecursionError` in Y — the only functional bug
found in either submission — compounded by Y's T3 docstring/behavior
mismatch. Y is otherwise of equal quality, with test suites that are in
places broader than X's, and its T3 trailing-separator acceptance is a
defensible reading of TASK.md rather than a defect.
