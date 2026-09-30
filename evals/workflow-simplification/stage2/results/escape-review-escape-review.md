# Blind review: WFS-ESCAPE-REVIEW

Reviewer: independent blind reviewer (did not author any submission).
Method: read both patches per task, verified every documented claim against the
copies' source, ran the focused tests of every touched file in every copy, and
ran mutation checks (all mutated files restored byte-for-byte; `cmp` verified
after each restore). Environment: system `python3` 3.10; all runs used
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src`. The copies are not git
repositories, so `make check` git-dependent steps were not run; instead the
relevant unit and contract layers were run identically in X and Y and compared.

---

## Task 201 (S2-1) — rename `test_prose_rejects_control_and_markup_characters`

Both patches are a single-line rename of the same test at
`tests/unit/test_techstack_markdown.py:565`, with no other change.
X: `test_prose_rejects_pipe_and_category_c_characters`.
Y: `test_prose_rejects_vertical_bar_and_category_c_characters`.

The test body (`X/tests/unit/test_techstack_markdown.py:565-574`, identical in
Y) asserts rejection of `|` (U+007C) and U+0085 (category Cc) only, matching
both names. U+007C's Unicode name is "VERTICAL LINE"; "pipe" is its common
name. This is a genuine naming ambiguity; both resolutions are defensible and
neither is penalized.

Old-name references: `grep -rn test_prose_rejects_control_and_markup_characters`
finds, in both copies, only `projects/brida-workflow-simplification/tasks.md:29`
— coordinator-owned project memory, explicitly permitted by the acceptance
criteria. Full-tree `diff -rq X Y` shows the test file as the only difference,
so neither submission made any change beyond the rename.

### Findings — X
None.

### Findings — Y
None.

### Hardening (not defects)
- None for either; the task forbids further change.

### Verification
- Focused tests: `python3 -m unittest tests.unit.test_techstack_markdown` — X:
  47 tests OK; Y: 47 tests OK.
- Liveness/mutation check (no behavior changed by the task, so this checks the
  renamed test is still a live guard): removing the `|` rejection at
  `src/brichan/techstacks/markdown.py:330-331` makes the renamed test fail in
  both copies (2 failures each). Files restored.

### Scores
| | Spec fidelity | Code review | Test evidence |
|---|---|---|---|
| X | 5 | 5 | 5 |
| Y | 5 | 5 | 5 |

**Verdict: tie.** Identical in substance; the one-word naming difference is a
defensible ambiguity on both sides.

---

## Task 203 (S2-3) — `diagnostic_detail` refuses unsupported keyword arguments

Both submissions implement the same design: `diagnostic_detail` raises
`ValueError` for any non-`None` argument the code does not take, and the one
production feed path (`_Resolver._add_located`,
`src/brichan/techstacks/resolver.py:266-282`) nulls `errno_value` for
non-`FILESYSTEM_ERROR` codes before it reaches the factory, preserving the old
observable output (the errno was previously silently dropped, and `Diagnostic`
stores no errno field, so output is unchanged).

Reachability of the new refusal from production was checked in both copies:
- `_Resolver._parse` (`resolver.py:341-352`) forwards `error.line`/`error.rule`
  from every `MarkdownError` into the factory. This is safe because map errors
  never carry line/rule: `parse_map` (`markdown.py:519-563`) only ever calls
  `cursor.fail()` bare, its cursor has no end/shape rules, and
  `_parse_metadata` (the only rule-attributed metadata failure,
  `markdown.py:577-580`) is called only from `parse_leaf` (`markdown.py:796`).
  Y pins this invariant with a test; X does not (see Hardening).
- `Diagnostic.__post_init__` (`model.py:2240-2262`) re-derives the detail via
  `diagnostic_detail`, but `_errno_value()` and `_leaf_slots()` are code-gated
  (`model.py:2267-2300`), so no disallowed argument can reach the refusal.

Byte-identical preservation of valid calls: I enumerated every registry code
with its valid argument grid (67 call shapes: all no-slot codes;
`FILESYSTEM_ERROR` × errno {None,0,2,13,24}; `INVALID_LEAF` × line {0,1,33} ×
rule {TITLE,LINE_SHAPE}) in both copies; outputs are identical between X and Y
and equal to `DIAGNOSTIC_SPECS[code].detail` / the untouched helpers, which
neither patch modifies — so both preserve the base's outputs
(scratch/equiv203.py, scratch/equiv_X.txt = scratch/equiv_Y.txt). Note the base
helper already refused `INVALID_LEAF` with missing slots
("INVALID_LEAF requires a line and a leaf grammar rule", `model.py:573`), so
"valid before" excludes those calls.

### Findings — X (ordered by severity)

1. **Medium — the "prove byte-identical, not just assert it" acceptance
   criterion has no supporting artifact in the final result.** X's patch adds
   only refusal tests (`tests/unit/test_techstack_model.py:659-682`) and one
   resolver test; nothing in the submission demonstrates that every previously
   valid call still returns the same detail. Reproduce:
   `grep -n "spec.detail\|DIAGNOSTIC_REGISTRY" 203/X/tests/unit/test_techstack_model.py`
   shows no added preservation test (Y adds
   `test_valid_calls_render_the_registry_detail_in_both_call_shapes`,
   `Y/tests/unit/test_techstack_model.py:660-697`, which is exactly this
   proof). My own equivalence run shows the code *is* correct; the defect is
   the missing required evidence/regression guard, not wrong behavior.

2. **Low — the refusal boundary at falsy values is untested; a plausible
   regression reintroduces the exact silent drop the task removes.**
   Reproduce: change `203/X/src/brichan/techstacks/model.py:601`
   `if value is not None and ...` to `if value and ...`, then
   `python3 -m unittest tests.unit.test_techstack_model` → **OK** (X's tests
   all use truthy values: errno 13, line 1; the one `line: 0` case also
   supplies `rule`, which still trips the refusal). The same mutation on Y
   fails 112 subtests (Y tests errno 0 and line 0 explicitly). Restored after
   the check.

3. **Low — spot-check coverage instead of registry-wide coverage.** X's
   refusal tests cover `UNREADABLE_FILE`, `INVALID_LEAF`, `FILESYSTEM_ERROR`
   only (`tests/unit/test_techstack_model.py:659-682`); the other registry
   codes' refusals are exercised only via the shared code path. Y iterates
   `model.DIAGNOSTIC_REGISTRY`. Unknown-code `KeyError` precedence is also
   untested in X (Y: `test_unknown_code_still_raises_key_error`).

### Findings — Y (ordered by severity)
None classified as defects.

### Hardening (not defects)
- X: no test pins the "map errors never carry line/rule" invariant that keeps
  the new refusal unreachable from `_Resolver._parse`; a future map-side rule
  attribution would crash resolution with only Y-style tests to catch it. Y
  added `test_map_failures_carry_no_leaf_line_or_rule`
  (`Y/tests/unit/test_techstack_markdown.py:324-372`).
- Both: refusal messages differ from each other (X: "`{code} must not carry
  {names}`"; Y: "`{code} detail takes only …` / `takes no arguments`"); both
  are ValueError with a descriptive message, consistent with the existing
  refusal style at `model.py:573`, so either is fine.

### Verification
- Focused tests (`tests.unit.test_techstack_model`,
  `tests.unit.test_techstack_resolver`, `tests.unit.test_techstack_markdown`):
  X: 69+71+47 = 187 OK. Y: 73+72+48 = 193 OK.
- Contract: `tests.contract.test_techstack_policy_contract` — both OK
  (1 skipped, identical).
- Mutation checks (all restored, `cmp`-verified):
  - Disable X's refusal raise → 5 failures (covered).
  - Disable each of Y's three refusal raises → 3, 2, and 281 sub-failures
    (each refusal class independently covered).
  - Remove the resolver errno guard → X: 1 error; Y: 2 errors (covered in
    both).
  - Truthiness mutation (finding X-2): X OK (miss), Y 112 failures (caught).
- Call sites: the only production feed of these kwargs is
  `_Findings.add` → `diagnostic` (`resolver.py:243-244`, `model.py:2349`),
  reached from `_add_located` (`resolver.py:280,282`) and `_parse`
  (`resolver.py:346-351`); both analyzed above. Registries, caps, literals,
  sort keys, and public signatures are untouched in both diffs.

### Scores
| | Spec fidelity | Code review | Test evidence |
|---|---|---|---|
| X | 4 | 5 | 3 |
| Y | 5 | 5 | 5 |

**Verdict: Y.** Same correct production change, but Y delivers the required
byte-identical proof as a registry-exhaustive regression test, covers every
refusal class across the whole registry including falsy boundaries, pins the
map-error invariant the refusal's production-safety depends on, and preserves
`KeyError` precedence under test. X's implementation is equally correct but its
evidence would let two plausible regressions (silent drop of falsy values;
future map-side line attribution) ship unnoticed.

---

## Task 204 (S2-4) — worker-ledger guidance in the packaged skill

Both submissions add the required guidance to the packaged
`herdr-orchestration` skill and extend the skill-parity markers. X also updates
the packaged `SKILL.md` workflow (steps 3-8) and adds an executable contract
test; Y documents in `references/commands.md` only, closely mirroring the
checkout skill's Worker ledger section, and adds a structural/text contract
test.

Accuracy of every claim in the new text was verified against the parser source
and empirically (scratch/verify204.py, run against the copies' `src`):
- `--task` exists on the launcher with verbatim-record semantics
  (`worker_launch.py:422-428`); installed mode never defines `--ledger-file`
  (`worker_launch.py:429-439`), so passing it is an argparse unrecognized-
  argument error, exit 2 — confirmed empirically for both launch and installed
  `finish`.
- `ledger: launch_id=<uuid>` on stderr, the ledger-write-failure warning with
  exit 0, and the no-location note for legacy launches:
  `worker_launch.py:679-704`, `worker_ledger.py:96`.
- Installed `finish`: flags `--worker --launch-id --evidence --task --pane
  --project` (`worker_ledger.py:679-692`); refusals each exit 1 with nothing
  written — confirmed empirically: double finish ("already has a finished
  record"), unmatched launch_id, non-`brichan-` worker name, whitespace-only
  evidence, non-Git-root `--project` (`ProjectError` is a `ValueError`,
  `project.py:9`, caught at `worker_ledger.py:727`), missing
  `.brichan/manifest.json` ("no ledger for this target",
  `worker_ledger.py:219`).
- "First `finished` record in file order wins": `launched_record` /
  `finished_record` return the first match (`worker_ledger.py:431-459`).
- Omitted `--project` → upward Git-root walk from the working directory
  (`worker_ledger.py:203-220`).

No claim in either submission's text contradicts the shipped CLI. Both keep
packaging, manifest, parity and the rest of the contract layer green (X: 152
tests OK; Y: 149 tests OK; base 148, X adds 4, Y adds 1; 1 identical skip).
The checkout skill already contains every marker phrase both submissions pin,
so parity holds in both trees.

### Findings — X (ordered by severity)
None classified as defects.

### Findings — Y (ordered by severity)

1. **Medium — acceptance criterion 2's evidence ("--help output … or the
   parser source") has no artifact in the final result, and the guidance is
   not coupled to the shipped CLI by any test.** Y's added tests assert only
   marker strings and section ordering
   (`Y/tests/contract/test_skill_parity_contract.py:76-92,99-122`).
   Reproduce: rename the launcher flag `--task` to `--work-item` in
   `204/Y/src/brichan/orchestration/worker_launch.py:423`, run the full
   contract layer → **OK** — stale guidance ships silently. The same mutation
   in X fails `test_the_documented_launch_command_parses_on_the_installed_launcher`
   (X's `tests/contract/test_packaged_ledger_guidance_contract.py` tokenizes
   and executes the documented command blocks against the installed entry
   points). Restored after the check. Today's text is accurate (verified
   above); the defect is the missing required evidence/regression coupling.

2. **Low — the launch command block still omits `--task`.** Y adds `--task`
   only as prose below the block
   (`Y/src/.../references/commands.md`, "Add `--task <TASK-ID>` …"), while the
   fenced `brichan-herdr-agent-start` example remains flag-less; a coordinator
   copying the block verbatim launches without task recording, and the task
   packet says the value is "never inferred". X adds the flag to the block
   itself. Defensible as a style choice ("states `--task` on launch" is
   literally satisfied), so scored low rather than medium.

### Hardening (not defects)
- X: argparse abbreviation makes the executable-guidance test tolerant of
  prefix-truncated flags in the docs — changing the documented `--launch-id`
  to `--launch` still passes both submissions' suites (verified by mutation;
  restored). X's test could additionally compare documented flags against the
  parser's option strings exactly.
- Y: documents "`2` | Invalid invocation" without naming `--ledger-file` in
  the exit table (X's table names it); the prose covers it, so informational
  only.
- X: `SKILL.md` step 7's inline finish command is a partial form
  (`--project` only); the full form is one `references/commands.md` hop away,
  which the step cites.

### Verification
- Contract layer (`unittest discover -s tests/contract`): X 152 OK
  (1 skipped); Y 149 OK (1 skipped).
- Worker unit tests (`tests/unit/test_worker_ledger.py` et al.): OK in both.
- Empirical CLI verification: scratch/verify204.py output above (exit codes
  0/1/2 and messages all match both submissions' text).
- Mutation checks (all restored, `cmp`-verified):
  - Docs: rename the documented finish subcommand → both fail (X via
    execution, Y via marker) — caught by both.
  - Docs: `--launch-id` → `--launch` in the block → both pass (argparse
    abbreviation; hardening note above).
  - CLI: `--task` → `--work-item` → X fails, Y passes (finding Y-1).

### Scores
| | Spec fidelity | Code review | Test evidence |
|---|---|---|---|
| X | 5 | 5 | 5 |
| Y | 4 | 5 | 3 |

**Verdict: X.** Both texts are accurate against the shipped CLI today, but
only X's final result contains the criterion-required evidence, as a contract
test that executes the documented command blocks against the installed entry
points — the exact drift guard the task's WLG-001 residual risk asks for. X
also integrates the ledger workflow into the packaged `SKILL.md` steps and
puts `--task` in the copyable launch block.

---

## Totals

| Task | X (Spec/Code/Test) | X total | Y (Spec/Code/Test) | Y total | Better |
|---|---|---|---|---|---|
| 201 | 5/5/5 | 15 | 5/5/5 | 15 | Tie |
| 203 | 4/5/3 | 12 | 5/5/5 | 15 | Y |
| 204 | 5/5/5 | 15 | 4/5/3 | 12 | X |
| **Sum** | | **42** | | **42** | 1 win each, 1 tie |

## Medium-or-higher defects

- **Task 201 — X:** none. **Y:** none.
- **Task 203 — X:** Medium — no artifact proving byte-identical preservation
  of valid calls (acceptance criterion "prove it, not just assert it");
  missing registry-wide preservation regression test
  (evidence: `203/X.patch` test hunks; contrast
  `203/Y/tests/unit/test_techstack_model.py:660-697`). **Y:** none.
- **Task 204 — X:** none. **Y:** Medium — no evidence artifact or test
  coupling the new guidance to the shipped CLI (acceptance criterion 2);
  reproducible: rename `--task` in `worker_launch.py:423`, contract layer
  stays green in Y, fails in X. **Y (low, for completeness):** launch example
  block omits `--task`.

## Reviewer notes on ambiguity (noted, not penalized)

- 201: "pipe" (X) vs "vertical_bar" (Y) for U+007C — both accurate.
- 203: refusal message wording differs; both consistent with the existing
  `model.py` refusal style.
- 204: documenting in `commands.md` only (Y) vs also rewriting the `SKILL.md`
  workflow (X) — the task's target is "the packaged skill", which both
  satisfy; X's workflow integration is a plus rather than Y's defect.
