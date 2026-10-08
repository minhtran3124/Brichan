# Blind review: submissions X and Y (WFS-010-REVIEW, attempt review-1)

Reviewed plan: WFS-010-REVIEW, version 1. Reviewer: independent blind session
(no implementation context). Date: 2026-10-08.

Scope: `wfs010-review/X/` and `wfs010-review/Y/`, three tasks each. `TASK.md`
and `test_visible.py` verified byte-identical between X and Y per task
(`diff -q`, no output). All six submitted suites were run with
`python3 -m unittest discover -s wfs010-review/<X|Y>/<task> -p 'test_*.py' -v`;
all pass (X: 17/11/15 tests OK, Y: 6/11/4 tests OK). Differential and
adversarial checks are in `wfs010-review/scratch/diff_checks.py`; every
reproduction below was actually run from the repo root with
`python3 wfs010-review/scratch/diff_checks.py`.

Rubric interpretation (stated for score traceability): functional defects are
priced primarily under `Spec fidelity`; `Code review` covers clarity,
maintainability, and correctness concerns beyond those already priced;
`Test evidence` follows `docs/policy/operating-principles.md` testing
discipline (distinct justification per test, no duplicate or
implementation-coupled cases).

---

## T1: ledger summary

### Findings — X

**X-T1-1 (high, functional): `summarize` crashes with `RecursionError` on a
deeply nested JSON line instead of counting it `undecodable`.**
Evidence: `X/t1-ledger-summary/ledger_summary.py:21-24` catches only
`ValueError` around `json.loads`; a parseable-depth guard is absent.
TASK.md rule 2 requires any line that is not a conforming JSON object to be
"skipped and counted in `undecodable`"; the return contract ("Return exactly
these keys") permits no exception for such input.
Reproduction (ran): `summarize(b"[" * 20000 + b"\n" + b'{"event": "launched", "launch_id": "a"}\n')`
→ `RecursionError: maximum recursion depth exceeded ...`. Y on the same input
returns `{'finished': [], 'unknown': ['a'], ..., 'undecodable': 1, ...}`
(handled at `Y/t1-ledger-summary/ledger_summary.py:20`, which catches
`(ValueError, RecursionError)`).

**X-T1-2 (low, spec-ambiguity note): Unicode-whitespace-only lines count as
`undecodable`, not ignored.** Evidence: the blank-line check runs on raw bytes
(`X/t1-ledger-summary/ledger_summary.py:13`), and `bytes.strip()` strips only
ASCII whitespace. Reproduction (ran): a `b"\xc2\xa0"` (NBSP) line gives
`undecodable: 1` under X and `undecodable: 0` (ignored) under Y
(`Y/t1-ledger-summary/ledger_summary.py:16-17` strips after decoding, and
`str.strip()` strips Unicode whitespace). TASK.md rule 1 ("contain only
whitespace") does not define whitespace; both readings are defensible, so this
is recorded as a divergence, not a defect, for either submission.

### Findings — Y

**Y-T1-1 (low, spec-ambiguity note):** the mirror of X-T1-2 above; Y ignores
Unicode-whitespace-only lines. Same evidence and reproduction. Not scored as a
defect.

**Y-T1-2 (low, test gap): the `RecursionError` path Y's module explicitly
handles (`Y/t1-ledger-summary/ledger_summary.py:20`) has no test**, so a
regression (e.g. narrowing the except clause back to `ValueError`) would pass
Y's suite. Priced under Test evidence.

### Notes

Both implementations agree on every other specified rule, confirmed by the
suites and by cross-reading: pairing by `launch_id` only, first-wins
duplicates, whole-file orphan determination, launched-record ordering,
no-trailing-newline and trailing-`\r` handling. X's suite
(`X/t1-ledger-summary/test_ledger_summary.py`) has 16 single-purpose tests
mapping ~1:1 to TASK.md rules 1-8, including the subtle
finished-before-launched non-orphan case (`test_ledger_summary.py:84-91`).
Y's suite (`Y/t1-ledger-summary/test_ledger_rules.py`) covers the same rules
in 5 denser tests and adds a distinct, justified case that `\x0c` must not act
as a line separator (`test_ledger_rules.py:67-72`), but packs many rules per
assertion and misses the recursion-guard behavior its own module owns.

### Scores — T1

| Criterion | X | Y |
|---|---|---|
| Spec fidelity | 3 | 5 |
| Code review | 4 | 4 |
| Test evidence | 5 | 4 |

X spec 3: one confirmed high-severity crash on spec-covered input. Y code 4
(not 5): `_decode`'s three-way sentinel return (`None` / `False` / tuple,
consumed via `decoded is False` at `ledger_summary.py:41-43`) is a
maintainability wart. X code 4: clean two-pass structure with a useful
invariant comment (`ledger_summary.py:38-40`), but the uncaught-exception
oversight tempers it. Y test 4 per Y-T1-2.

---

## T2: prerelease ordering fix

### Findings — X

**X-T2-1 (medium, functional): `parse` accepts invalid SemVer strings,
violating its own contract ("Raises ValueError for anything that is not a
valid SemVer 2.0.0 string", `X/t2-prerelease-order/semver_order.py:20-21`) and
TASK.md's "Keep ... the existing `ValueError` behavior for invalid input".**
Root cause: the regex (`semver_order.py:8-13`) is anchored with `$`, which in
Python matches before a trailing newline, and is compiled without `re.ASCII`,
so `\d` matches non-ASCII digits. Reproductions (ran):
- `parse("1.0.0\n")` → `((1, 0, 0), ())`; `compare("1.0.0\n", "1.0.0")` → `0`.
- `parse("1٢.0.0")` → `((12, 0, 0), ())` (U+0662 ARABIC-INDIC TWO).
- `parse("1.0.0-rc.1٢")` → `((1, 0, 0), ('rc', '1٢'))`.
Y rejects all four probes with `ValueError`
(`Y/t2-prerelease-order/semver_order.py:12-13` uses `\Z` and `re.ASCII`, with
a comment stating exactly why).

**X-T2-2 (low, test gap): no invalid-input coverage beyond one duplicate.**
`X/t2-prerelease-order/test_semver_order.py:41-43` repeats the identical case
already in the shared `test_visible.py:15-17` (`compare("1.0", "1.0.0")`), a
duplicate under the project's testing discipline, and nothing probes the
class of inputs in X-T2-1 — the suite could not catch its own shipped defect.

### Findings — Y

None. A 625-pair differential sweep over 25 valid versions (core, prerelease,
build-metadata, boundary identifiers like `-0`, `-a-`, `--`) found zero
`compare` disagreements between X and Y (`scratch/diff_checks.py`), so Y's
key-based comparison is behaviorally confirmed against X's independent
pairwise implementation on valid input, and both fix the reported
`rc.2`/`rc.10` bug (both suites assert it).

### Notes

Y's module is also the better artifact: the `_identifier_key` +
tuple-comparison design (`Y/t2-prerelease-order/semver_order.py:31-56`) makes
the "longer set wins on equal prefix" rule fall out of tuple prefix semantics,
documented at `semver_order.py:52-53`. Y's suite covers the reported bug, the
full spec §11 example chain in both directions
(`test_precedence.py:13-27`), ASCII ordering edge cases including `-a-` vs
`-a0` (`:29-32`), numeric-below-alphanumeric at magnitude (`:34-35`), build
metadata ignored (`:37-39`), sort stability (`:41-42`), and ten invalid forms
under `subTest` (`:47-51`) — each with a distinct justification.

### Scores — T2

| Criterion | X | Y |
|---|---|---|
| Spec fidelity | 3 | 5 |
| Code review | 4 | 5 |
| Test evidence | 3 | 5 |

---

## T3: path guard normalization

### Findings — X

**X-T3-1 (low, contract interpretation): the `.jsonl` invariant is enforced on
the normalized path, not the value as supplied, and the docstring invariant
was reworded accordingly** (`X/t3-path-guard/path_guard.py:9` "final
*normalized* component"; check at `path_guard.py:41`). Consequence
(reproductions ran): X accepts `"ledger/workers.jsonl/"`,
`"ledger/workers.jsonl/."`, `"ledger/workers.jsonl//"`, and `"x.jsonl/./"`,
all returning `"ledger/workers.jsonl"` / `"x.jsonl"`; Y rejects every one
(`ValueError: path must end in .jsonl`, `Y/t3-path-guard/path_guard.py:38`).
The original docstring is not available to this review, so whether "final
component" originally meant as-supplied cannot be proven here; the sibling
`..` invariant is phrased "anywhere in the value as supplied" in both copies
(`path_guard.py:6`), which suggests as-supplied was the house reading, and a
trailing separator conventionally names a directory. The returned
(normalized) path still always ends in `.jsonl`, so no write-target escape
results; X's choice is self-consistent, documented, and tested
(`X/t3-path-guard/test_path_guard.py:22-25`), but it is the weaker reading of
"every security invariant ... must keep holding". Scored under Spec fidelity;
uncertainty recorded below.

### Findings — Y

**Y-T3-1 (low, contract interpretation): Y rejects trailing-separator forms
(`"ledger/x.jsonl//"`) that TASK.md's "accepts ... repeated `/` separators"
could be read to include.** Evidence: `Y/t3-path-guard/path_guard.py:38` and
the explicit documentation of the choice at `path_guard.py:16-18`;
tested at `Y/t3-path-guard/test_normalization.py:30-32`. The user complaint in
TASK.md concerns mid-path redundancy only, and a trailing `/` names a
directory, so this strictness is defensible and documented. Not scored as a
defect.

### Notes

Both preserve every other invariant against the value as supplied, confirmed
by reproduction: `..` and `.BrIcHaN` are rejected even when hidden among
redundant segments (`"ledger/.//../workers.jsonl"`, `"a/./.BriChan//x.jsonl"`
raise in both), absolute paths, backslash, and NUL are rejected, and both
normalize `"./ledger///.//workers.jsonl"`-style inputs identically otherwise.
One shared observation (no finding): both accept a bare `".jsonl"` final
component; only `.brichan` is a protected dotfile per the docstring, so this
is inside the contract. X's implementation carries an explicit
empty-after-normalization guard (`X/t3-path-guard/path_guard.py:39-40`);
Y reaches the same safety implicitly — `parts[-1]` must end in `.jsonl`, so
the join can never be empty — which is correct (verified) but rests on
unstated coupling between the suffix check and the filter
(`Y/t3-path-guard/path_guard.py:38-40`). X's 13 single-purpose tests and Y's
21 subTest cases both give strong, non-duplicative regression coverage of
their respective contracts, including the invariant-hidden-by-redundancy
cases.

### Scores — T3

| Criterion | X | Y |
|---|---|---|
| Spec fidelity | 4 | 5 |
| Code review | 5 | 4 |
| Test evidence | 5 | 5 |

X spec 4 / Y spec 5 per X-T3-1 vs Y-T3-1: Y's reading preserves the
as-supplied invariant pattern; X's rewords a documented security invariant.
X code 5 / Y code 4: X is explicit where Y is implicit (see note above);
both are correct and clear.

---

## Totals

| Task | Criterion | X | Y |
|---|---|---|---|
| T1 | Spec fidelity | 3 | 5 |
| T1 | Code review | 4 | 4 |
| T1 | Test evidence | 5 | 4 |
| T2 | Spec fidelity | 3 | 5 |
| T2 | Code review | 4 | 5 |
| T2 | Test evidence | 3 | 5 |
| T3 | Spec fidelity | 4 | 5 |
| T3 | Code review | 5 | 4 |
| T3 | Test evidence | 5 | 5 |
| **Total (max 45)** | | **36** | **42** |

## Overall preference: Y

Decisive reasons, in order of weight:

1. **X ships two confirmed functional defects; Y ships none.** X's T1
   `summarize` crashes on a spec-covered input class (X-T1-1, reproduced), and
   X's T2 `parse` accepts invalid SemVer strings against its own documented
   `ValueError` contract (X-T2-1, reproduced four ways). Every Y finding is an
   ambiguity divergence or a test gap, not incorrect behavior.
2. **Y validates inputs at the contract boundary deliberately** — `\Z` +
   `re.ASCII` with explanatory comments in T2, `(ValueError, RecursionError)`
   in T1, as-supplied invariant checks in T3 — exactly the discipline a guard
   or precedence module exists for.
3. **Y's T2 test evidence is decisively stronger** (bidirectional spec chain,
   boundary identifiers, stability, ten distinct invalid forms), while X's T2
   suite has no invalid-input case beyond one duplicated from the visible
   tests and could not have caught X's own defect.

X is ahead on test granularity in T1 and on explicitness in T3 — if X's two
functional defects were fixed, the gap would mostly close — but on this
evidence Y is the submission to prefer.

## Recorded uncertainty

- The original `path_guard.py` docstring was not provided, so X-T3-1 rests on
  the invariant wording reconstructed from the two submissions (both copies
  agree except for X's inserted "normalized"); it is scored as a low-severity
  interpretation finding, not a security defect, because the normalized return
  value provably keeps the `.jsonl` suffix.
- TASK.md T1 rule 1 does not define "whitespace"; X and Y diverge on
  Unicode-whitespace-only lines (X-T1-2 / Y-T1-1). Neither was penalized.
