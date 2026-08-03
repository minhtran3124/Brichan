# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `plan`
- Artifact version: `4`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md@TDW-009-P3-v3+task-packet-amendment-4`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `3ebc7268-a8cd-464c-8d65-9920f2beac5c`
- Effective route: `plan`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `TDW-009-P4`
- Plan status: `accepted`

## Version 4 supersession

`TDW-009-P1`, `TDW-009-P2`, and `TDW-009-P3` are preserved byte-identically at
`versions/v1/plan.md`, `versions/v2/plan.md`, and `versions/v3/plan.md` and are
superseded by `TDW-009-P4` version 4. No prior version is authorized for
implementation. The archived reviews are at `versions/v1/plan-review.md`,
`versions/v2/plan-review.md`, and `versions/v3/plan-review.md`.

## Precondition owned by the coordinator

Before implementation handoff the coordinator replaces
`baseline/pre-task-manifest.txt` with an **implementation-start manifest** in the
canonical format specified in `design.md`, captured after this plan is accepted.
It must carry:

1. `manifest-version: 1` and a stable repository identity;
2. an explicit `capture-scope-excludes` line covering coordinator-, planner-, and
   reviewer-owned dossier paths;
3. a `[protected]` section holding path, digest, and byte length for
   `config/model-routing.json` **as it exists at capture time**, all sixteen
   files under `src/brichan/resources/` including `__init__.py`, and every
   artifact of `TDW-006`, `TDW-007`, and `TDW-008`;
4. `[allowlist-modified]` with exactly **8** lines, each carrying a digest and a
   restorable **byte snapshot** under a sibling `snapshot/` directory;
5. `[allowlist-new]` with exactly **36** lines, each recorded `absent`;
6. `[untracked-leaves]` enumerating individual files, never a collapsed
   directory.

**`config/model-routing.json` is user-owned protected state.** This plan records
no expected digest for it. The manifest's capture is the only reference.
Implementation must not modify, revert, or absorb the file, and must not infer
whether its current content is authorized; that classification is the
coordinator's.

The implementer refuses to start if the manifest is absent or missing any of the
six elements. Every preservation, delta, and rollback claim below is made against
it, never against `HEAD`.

## Authorized implementation paths

Exactly 8 modified tracked files and 36 new files: **44 paths**, unchanged from
version 3.

### Modified tracked files (8)

| # | Path | Exact change |
| --- | --- | --- |
| 1 | `src/brichan/contracts/task_dossier/schema.py` | add four constants and four `__all__` entries |
| 2 | `src/brichan/contracts/task_dossier/validation.py` | five hunks only: import insertion after `ARTIFACTS,` on line 30; `EXTRA_SECTION_FIELDS` replacement at lines 71-78; `_symlinked_ancestor` helper after `_is_safe_relative`; one call site in `_validate_receipt_link`; one call site in `_validate_memory_link` |
| 3 | `src/brichan/contracts/task_dossier/__init__.py` | add exports; `main` stays `validation.main`; CLI entries only as `generate_main` and `summary_main` |
| 4 | `tests/unit/test_task_dossier_validator.py` | append ancestor-symlink regression cases only |
| 5 | `tests/contract/test_task_dossier_contract.py` | append cases only |
| 6 | `tests/integration/test_task_dossier_workflow.py` | append cases only |
| 7 | `config/repository-paths.json` | inventory the five new source and wrapper files |
| 8 | `docs/workflows/task-dossier.md` | extend the Tooling section only |

### New source and test files (7)

`src/brichan/contracts/task_dossier/record.py` ·
`src/brichan/contracts/task_dossier/generate.py` ·
`src/brichan/contracts/task_dossier/summary.py` ·
`scripts/generate_task_dossier.py` ·
`scripts/summarize_task_dossier.py` ·
`tests/unit/test_task_dossier_generator.py` ·
`tests/unit/test_task_dossier_summary.py`

### Closed evaluation leaf allowlist (29)

All relative to `evals/task-dossier-pilots/concise/`. `<A>` expands to the
eleven members of `ARTIFACTS`.

| Group | Paths | Count |
| --- | --- | ---: |
| Records | `records/SYNTH-010.record.json`, `records/SYNTH-011.record.json` | 2 |
| Evaluation | `results.md` | 1 |
| Level 0 memory | `projects/synthetic-level0/current-state.md` | 1 |
| Level 0 artifacts | `projects/synthetic-level0/handoffs/SYNTH-010/<A>.md` | 11 |
| Level 0 receipt | `projects/synthetic-level0/handoffs/SYNTH-010/receipt.md` | 1 |
| Level 1 memory | `projects/synthetic-level1/current-state.md` | 1 |
| Level 1 artifacts | `projects/synthetic-level1/handoffs/SYNTH-011/<A>.md` | 11 |
| Level 1 receipt | `projects/synthetic-level1/handoffs/SYNTH-011/receipt.md` | 1 |

Reconciliation: 8 + 7 + 29 = 44 unique paths.

## Paths that must remain untouched

| Path | Reason |
| --- | --- |
| `config/model-routing.json` | User-owned protected state; no expected digest is recorded anywhere in this plan |
| `src/brichan/contracts/task_dossier/scaffold.py` | The generator shares no write code and imports only `dossier_path` |
| `src/brichan/contracts/task_dossier/parser.py` | Consumed unchanged |
| `src/brichan/resources/**`, sixteen files including `__init__.py` | Installed resources are out of scope; each verified against the manifest capture |
| `docs/workflows/task-dossier/templates/**` | Templates back the scaffold and the contract tests |
| `docs/policy/**`, `PRODUCT.md`, `AGENTS.md`, `CLAUDE.md` | Policy is not changed by an implementation task |
| `projects/**` | Dossier, versions, baseline, and memory writes belong to the coordinator, planner, and reviewers |
| `evals/task-dossier-pilots/results.md`, `simple/`, `normal/`, `high-risk/` | Recorded pilot evidence stays immutable |
| `metrics/**`, `bin/**`, `Makefile`, `pyproject.toml`, `CHANGELOG.md`, `VERSION` | No new gate, no packaging change, no release surface |
| `.brichan` state anywhere on disk | Checkout-only capability |

## Ordered steps

1. **Manifest precondition.** Confirm the manifest exists and carries all six
   elements, that `[allowlist-modified]` has eight lines each with a readable
   snapshot, and that `[allowlist-new]` has thirty-six `absent` lines. Refuse
   otherwise. Record no digest for `config/model-routing.json` anywhere in
   implementation output; read it only from the manifest. (`R-X6`, `R-X11`,
   `R-X12`; v3 H2, AC5)

2. **Constants and validator hunks.** Add the four `schema.py` constants and
   `__all__` entries. Apply the five `validation.py` hunks. Confirm the existing
   validator suite passes unchanged. (`R-V1` through `R-V4`, `R-X1`, `R-X4`; AC5)

3. **`record.py`.** Implement the exhaustive key-to-type tables from `design.md`:
   `type(v) is ...` checks, `object_pairs_hook` duplicate rejection, JSON `null`
   as the only null with the `"null"` string refused, the four cross-record
   consistency refusals, and the three position-class injection rule sets.
   Mirror `validation.py:276-355` for evidence depth. No import of
   `validation.py`. (`R-G18` through `R-G27`; v3 H1, AC2)

4. **`generate.py`, Phases A to C.** `render_artifact` per the fixed block
   order. Phase A renders and validates everything with **no** filesystem
   mutation. Phase B walks descriptors from the projects root, creating missing
   components with `os.mkdir(..., dir_fd=parent)`; both `ELOOP` and `ENOTDIR` are
   refusals; each level's device and inode is recorded. Phase C takes
   `fcntl.flock(dossier_fd, LOCK_EX | LOCK_NB)` **immediately after the dossier
   descriptor is opened**; a conflicting holder is a named refusal that creates
   no temporary and no artifact. (`R-G3` through `R-G8`, `R-G19`, `R-G25`,
   `R-G28`; v3 M1, AC1)

5. **`generate.py`, Phase D.** Bounded `O_EXCL` temporary, full write loop,
   `fsync`, inode verification, close, `os.link(..., follow_symlinks=False)`, the
   post-publication `os.lstat` regular-file and inode check whose observed
   mismatch exits nonzero and leaves the entry in place, identity-verified
   cleanup, dossier `fsync`, partial-adoption diagnostic on any fault, and the
   final canonical re-walk whose drift exits `1`. `os.rename` and `os.replace`
   must not appear in the module. (`R-G9` through `R-G17`; AC1)

6. **Generator CLI and wrapper.** `main()` with the documented arguments and
   three exit codes; `scripts/generate_task_dossier.py` shaped like
   `scripts/validate_task_dossiers.py:1-19`. (`R-G1`, `R-G2`, `R-X10`; AC2)

7. **`summary.py` computation.** `DossierSummary` and `summarize_dossier`. Root
   verdict from `validate_projects(root, require_complete=True)`; detail from
   `validate_dossier`; the per-phase evidence rule; and the exit composition of
   `design.md` — a scope code in `{0, 2}` and a verdict code in `{0, 1}`, exiting
   `2` if the scope code is `2`, else the verdict code, with root-level
   diagnostics always printed. (`R-S1` through `R-S13`; v3 H3, AC4)

8. **Summary renderers, exports, wrapper.** `render_summary_text` and
   `render_summary_json` over one structure, both carrying the independence
   caveat. Update `__init__.py`. Add `scripts/summarize_task_dossier.py`. Add a
   test asserting `main is validation.main` and that the three callables are
   distinct. (`R-S8`, `R-S14`, `R-X5`; AC4, AC5)

9. **Validator ancestor-link regression tests.** Append to
   `tests/unit/test_task_dossier_validator.py`: a symlinked ancestor above the
   receipt path is diagnosed; a symlinked ancestor above the memory path is
   diagnosed; the clean case is unchanged; the diagnostics originate from
   `validate_projects` and `validate_dossier`, not from summary code; and no
   existing diagnostic message changed. (`R-V5`, `R-V6`; AC5)

10. **Record-hardening and extraction tests.** One named diagnostic and one test
    per malformed class: malformed JSON; non-object root; non-UTF-8; duplicate
    key at top level and inside an artifact; boolean in an integer position;
    wrong exact type for `str`, `int`, `list`, and `dict` positions; the `"null"`
    string where JSON null is meant; unknown and missing top-level key; unknown,
    missing, and misspelled artifact; unknown and missing per-artifact key;
    identity mismatch; each of the four cross-record consistency refusals;
    placeholder in claim, evidence, and uncertainty; evidence below the
    applicable rule; missing and invalid review verdict; unpaired `not-required`;
    non-null rationale on a required artifact; personal path; unsafe memory path;
    derived field and supplemental section on `index`; one case per refused item
    in each of the three position classes; and a **positive** case proving a
    backticked `path:line` evidence item is accepted.
    **Extraction test:** parse the single fenced JSON block out of
    `design.md` itself, assert exactly eleven artifact keys with seventeen keys
    each, assert the four cross-record rules, render it, and assert
    `validate_dossier` returns zero diagnostics with and without
    `require_complete`. The fixture is the literal design block, not a copy.
    (`R-G26`, `R-G27`; v3 H1, AC2)

11. **Race, lock-ordering, and namespace-drift tests.** A symlinked dossier,
    `handoffs`, or project directory present before the walk is refused. The
    dossier descriptor is obtained, the directory is replaced on disk by a
    symlink to a decoy outside the root, and publication runs against the held
    descriptor: every artifact lands in the original inode, the decoy stays
    empty, and the final re-walk makes the run exit `1`. The same swap injected
    between two publications. **Two-invocation first-creation test:** start two
    cooperating apply invocations from a *missing* dossier; assert both converge
    on one directory inode, that publications do not interleave, and that the
    losing lock attempt creates no artifact and no temporary leaf. **Stable
    injected mismatch:** substitute the verified temporary source with a regular
    file and with a symlink immediately before `os.link`, and replace the final
    name after a successful link but before cleanup; assert the post-link check
    emits its diagnostic, the run never reports success, cleanup never unlinks
    the replacement, and a final entry may remain. Each of these tests carries a
    comment in the test file recording that it establishes the diagnostic path
    only and **is not evidence of detection against the excluded process**.
    (`R-G6` through `R-G8`, `R-G11`, `R-G17`; v3 H4, M1, AC1)

12. **Publication fault-injection tests.** Patch `os.write` to short-write and to
    raise; `os.fsync` on the file and on the directory to raise; `os.close` to
    raise; `os.link` to raise `ENOSPC` and `EEXIST`; `os.unlink` during cleanup to
    raise; force temporary-name counter exhaustion; force a temporary inode
    mismatch before publication; add a permission-denied case, and a
    deterministic mocked `OSError` case establishing the same exit behaviour so
    coverage does not depend on privilege. For each: no partial artifact at any
    final name, pre-existing artifacts byte-identical, exit `1`, the
    partial-adoption diagnostic naming published and unpublished artifacts, no
    foreign file unlinked, and a retry republishing only the missing artifacts. A
    permission case that cannot run is skipped with a recorded reason.
    (`R-G12` through `R-G16`; AC1)

13. **Round-trip against the validator.** Generate into a temporary root from a
    well-formed record, then assert `validate_dossier` returns zero diagnostics,
    covering request origin, redaction, and mutability; plan and review linkage;
    route-strength and override pairing; Level 0 and Level 1 ship authorization;
    and PR remote-action text. (`R-G19` through `R-G25`; AC2, AC6)

14. **Summary tests.** Every reported section present. The `passed` floor
    distinguished from the `not-required` one-item rule at Levels 0, 1, and 2,
    including a Level 2 `not-required` artifact with one item reported compliant.
    **Exit boundary, one test each:** an existing but unreadable `index.md`
    exits `1`; a missing `index.md` in a handoff carrying dossier metadata,
    scanned at root level, exits `1` with the partial-adoption diagnostic; an
    empty historical receipt-only handoff contributes no diagnostic; an
    unlistable dossier directory exits `2`; an absent projects root exits `2`;
    `--task` matching nothing exits `2`; `--task` matching more than one exits
    `2`; and an unmatched `--task` still prints the root-level partial-adoption
    or duplicate-ID diagnostic rather than suppressing it. Plus: duplicate task
    IDs; a valid but `pending` dossier exiting `1`; an unreadable non-index
    artifact reported not omitted; authority links with a missing target, a
    symlinked target, and a symlinked ancestor, asserting the ancestor verdict
    comes from the validator; both independence arms with placeholder and
    synthetic unequal identities; text and JSON carrying the same facts and exit
    code; and no routing manifest opened. (`R-S3`, `R-S6`, `R-S7`, `R-S9`,
    `R-S11`; v3 H3, AC4, AC6)

15. **Author synthetic records and fixtures.** Both records under `records/`,
    task IDs `SYNTH-010` and `SYNTH-011`, slugs `synthetic-level0` and
    `synthetic-level1`, every session identity matching `synthetic-fixture-`,
    every artifact claim stating non-authoritative test data. The Level 0 record
    is the complete worked record from `design.md`. Hand-write the two schema-v2
    `receipt.md` fixtures and the two `current-state.md` memory fixtures. No
    Markdown link syntax, no personal path. (`R-E1`, `R-E4`; AC3)

16. **Generate, validate, measure.** Dry run, then apply, into
    `evals/task-dossier-pilots/concise/projects/`. Record the exact output of
    each command in the evaluation table. Confirm 11/11 artifacts per sample, a
    passing complete gate, valid fixture receipts, and totals at or below 447
    lines for Level 0 and 501 for Level 1. (`R-E3`, `R-E4`; AC2, AC3, AC6)

17. **Measure authoring burden.** Apply the `design.md` authored-value algorithm
    with its fixed `DECLARED_ORDER`, plus `wc -lc` per record and the combined
    total. Two independent runs must produce the same integer. No timing, token,
    or cost estimate. (`R-E5`, `R-E6`; AC3, AC7)

18. **Evaluation, inventory, documentation, contract tests.** Write
    `evals/task-dossier-pilots/concise/results.md` with measured lines against
    the baselines, artifact and evidence counts, the four metrics with an
    explicit statement of which measures compactness and which approximates
    burden, what the generator derived and refused to derive, residual risks
    including the excluded process stated as best-effort observation only, and
    the fixed declaration that the samples prove contract validity only. Add the
    five manifest entries to `config/repository-paths.json`. Extend only the
    Tooling section of `docs/workflows/task-dossier.md`. Append the contract
    cases from version 3 plus one asserting `design.md` contains exactly one
    fenced JSON block with eleven artifact keys. Do not modify
    `evals/task-dossier-pilots/results.md`. (`R-E2`, `R-E5`; AC5, AC7)

19. **Full verification and manifest procedure run.** Run every command in the
    full table, including the explicit Python 3.10 run and the manifest
    comparison over every protected path. Then execute and record the
    **manifest procedure run**: parse the manifest; compute the exact set delta
    of `design.md` against a constructed fixture that contains modified tracked
    bytes, a pre-existing collision at one planned new path, unrelated untracked
    planning and reviewer leaves, and one rollback target changed after
    implementation; assert the unexpected set is empty, the delta equals the 44
    authorized paths, and the rollback aborts on the concurrently changed target
    without writing it. This is a recorded procedure run, not an automated suite
    test, because automating it would need a forty-fifth allowlist path.
    (`R-X7`, `R-X8`, `R-X11`, `R-X13`, `R-X14`; v3 H2, AC5, AC6)

20. **Record the rollback procedure and post-implementation digests.** Record a
    post-implementation digest for each of the 44 paths. Produce the reverse
    patch for the eight modified files from the manifest snapshots and the
    deletion list for the 36 new paths. Do not execute unless a stop condition
    fires. (`R-X13`; v3 H2)

21. **Hand off for review.** Report the delta against the manifest, focused and
    full test output, measured line and record metrics, the post-implementation
    digests, and the rollback procedure. Do not commit, push, open a pull
    request, or write `plan-review.md` or `code-review.md`. (AC8)

## Verification

Focused, after steps 9 through 14:

| Command | Expectation |
| --- | --- |
| `python3 -m unittest tests.unit.test_task_dossier_generator -v` | all pass |
| `python3 -m unittest tests.unit.test_task_dossier_summary -v` | all pass |
| `python3 -m unittest tests.unit.test_task_dossier_validator -v` | all pass, existing assertions unchanged |
| `python3 -m unittest tests.contract.test_task_dossier_contract -v` | all pass |
| `python3 -m unittest tests.integration.test_task_dossier_workflow -v` | all pass |
| `grep -n "os.replace\|os.rename" src/brichan/contracts/task_dossier/generate.py` | no match |
| `make dossiers` | exit `0`; no new diagnostic on `TDW-006`, `TDW-007`, `TDW-008`, `TDW-009` |
| manifest comparison for `scaffold.py` and `parser.py` | unchanged |

Evaluation, after steps 16 and 17:

| Command | Expectation |
| --- | --- |
| `python3 scripts/validate_task_dossiers.py evals/task-dossier-pilots/concise/projects --require-complete` | exit `0`, two dossiers |
| `python3 scripts/validate_handoff_receipts.py evals/task-dossier-pilots/concise/projects` | exit `0`, two receipts |
| `python3 scripts/summarize_task_dossier.py evals/task-dossier-pilots/concise/projects` | exit `0`, both summaries complete |
| explicit eleven-path `wc -l` per sample | Level 0 at most 447, Level 1 at most 501 |
| `wc -lc` per record plus the authored-value count | recorded; the count reproduces across two runs |

Full, at step 19:

| Command | Expectation |
| --- | --- |
| `make check` | exit `0` |
| `python3.10 -m unittest tests.unit.test_task_dossier_generator tests.unit.test_task_dossier_summary tests.unit.test_task_dossier_validator -v` | all pass on the 3.10 floor |
| `make dossiers`, `make receipts`, `make path-check` | exit `0` |
| manifest comparison over `config/model-routing.json`, all sixteen files under `src/brichan/resources/`, and every artifact of `TDW-006`, `TDW-007`, `TDW-008` | every path identical to its capture |
| the exact set-delta procedure against the step-19 fixture | unexpected set empty; delta equals the 44 authorized paths |
| the rollback procedure against a concurrently changed target | aborts on that path; writes and deletes nothing |

Explicitly not used as preservation evidence: bare `git diff` or
`git status --short` against `HEAD`, and any hard-coded digest for
`config/model-routing.json`.

## Stop conditions

Stop, write nothing further, and escalate when any becomes true:

- The manifest is absent, is not `manifest-version: 1`, lacks a snapshot for any
  of the eight modified paths, does not record all thirty-six new paths absent,
  omits any of the sixteen resource files, or collapses a directory in
  `[untracked-leaves]`.
- Any step would require modifying, reverting, or interpreting
  `config/model-routing.json`, or recording an expected digest for it.
- Closing a safety property appears to require modifying `scaffold.py` or
  `parser.py`, a Linux-only syscall, or a production hook added solely for a test.
- Publication appears to require `os.rename`, `os.replace`, deleting an existing
  file, or accepting a partial artifact at a final name.
- The post-publication check or the final re-walk cannot be implemented, or would
  have to be downgraded to a warning.
- Any artifact, test name, comment, or report would claim prevention or detection
  against the excluded process.
- The extraction test cannot load the literal fenced block from `design.md`, or
  that block does not validate.
- Making ancestor-symlinked authority paths invalid would change any existing
  diagnostic, or require more than the five enumerated `validation.py` hunks.
- Meeting the 30% reduction appears to require dropping an artifact, dropping an
  evidence item, or lowering a level floor.
- Any dependency outside the standard library, or any construct requiring Python
  newer than 3.10.
- The observed delta cannot be made to equal the 44 authorized paths, or closing
  a gap would need a forty-fifth.

## Rollback

Computed from the implementation-start manifest and the step-20
post-implementation digests, never from `HEAD`.

```text
for p in [allowlist-modified]:            # 8 paths
    if sha256(p) != post_implementation_sha256(p):  ABORT p
    else: restore snapshot/<flattened p> over p
for p in [allowlist-new]:                 # 36 paths
    if not exists(p): skip
    if sha256(p) != post_implementation_sha256(p):  ABORT p
    else: delete p
```

A target whose current bytes differ from what implementation left is **never
overwritten and never deleted**; the rollback aborts on that path and escalates.
Whole-file `git checkout --` is forbidden: it reverts to `HEAD` and would discard
pre-existing user changes, including the current `config/model-routing.json`
change. No data migration occurs, nothing is committed, and no remote state
changes.

## Execution state

Steps 1 through 21 are unexecuted. This session was scoped to the version-3
snapshots and the five planner-owned artifacts, so no module, test, wrapper,
sample, fixture, manifest entry, or validator hunk was created, and no acceptance
criterion that depends on execution is claimed as met. `TDW-009-AC1` through
`AC7` are discharged at execution time on the `implement` route; `TDW-009-AC8` is
discharged by fresh independent review sessions.

## Claim or decision

Plan `TDW-009-P4` is accepted at version 4; `index.md` must echo that ID and
version. It authorizes exactly 44 paths, unchanged from version 3, forbids ten
path groups by name, orders 21 steps so that every version-3 finding and every
added test is discharged by a named command, and computes every preservation,
delta, and rollback claim from a coordinator-captured manifest that carries byte
snapshots rather than digests alone. The plan records no digest for
`config/model-routing.json`, states the excluded-process boundary as
point-in-time best-effort observation everywhere it appears, and places the
dossier lock where it can physically be taken.

## Evidence

- A read-only reference renderer plus the repository's own validator established
  that the complete worked record now in `design.md` is genuinely valid:
  `validate_dossier` returned zero diagnostics with and without
  `require_complete`, at 410 rendered lines. Re-extracting the fenced block from
  the written `design.md` reproduced eleven artifact keys with seventeen keys
  each and satisfied all four cross-record rules, which is exactly what step 10
  asserts.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md:92-119`
  establishes that a digest cannot reconstruct a reverse patch and that the
  version-3 hard-coded routing digest was already stale. Read-only hashing in
  this session reproduced the mismatch and `git diff --stat` confirmed the file
  is modified relative to `HEAD`, which is why the precondition above records no
  digest and step 1 forbids implementation from interpreting the file.
- `src/brichan/contracts/task_dossier/validation.py:1109-1116,1138-1195` and
  `src/brichan/contracts/task_dossier/parser.py:116-123` are the source of the
  step-14 exit tests: discovery globs the index path without reading it, so an
  existing unreadable index is discovered and diagnosed, while partial adoption
  is raised only by `validate_projects`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md:175-194,210-221`
  supplies the `M1` lock-ordering correction and the five added tests that steps
  10, 11, 14, and 19 discharge.
- `src/brichan/contracts/receipts/validation.py:15-70,1123-1125` fixes the eleven
  required receipt sections for the step-15 fixtures and shows the glob that lets
  step 16 validate both with the existing tool.
- A read-only count of `src/brichan/resources/` found sixteen files, which is the
  coverage the precondition requires and the figure the superseded baseline
  under-counted at fifteen.
- Python 3.10.11 is present on this machine, so the 3.10 floor run in step 19 is
  an executable check rather than an aspiration.

## Uncertainty

- Step 11's swap cases patch `os.link` and replace directory entries between
  operations. These are test seams over standard-library functions, not
  production hooks. If a case cannot be written without adding a hook to
  `generate.py`, the stop condition applies.
- The substitution tests assert an observed mismatch, not detection. Their test
  file must carry that statement; a passing suite is not adversarial coverage.
- The step-19 manifest procedure is a recorded run rather than a suite test,
  because automating it would need a forty-fifth allowlist path. It is therefore
  reproducible only by following the written commands, and a future review may
  reasonably ask for the extra path.
- The permission-denied case in step 12 may be unrunnable as root; the mocked
  `OSError` case exists so exit behaviour is still established deterministically.
- The 447-line and 501-line targets are budgets. The Level 0 sample is expected
  at 410 lines by measurement of the worked record, but the Level 1 sample is
  unmeasured.
- The orphan-temporary case is recorded but unswept, because sweeping would mean
  deleting files the generator did not verify it created.
