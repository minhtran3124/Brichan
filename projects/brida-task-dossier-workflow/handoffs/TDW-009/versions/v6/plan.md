# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `plan`
- Artifact version: `6`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v5/plan-review.md@TDW-009-P5-v5+task-packet-amendment-6`
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

- Plan ID: `TDW-009-P6`
- Plan status: `accepted`

## Version 6 supersession

`TDW-009-P1` through `TDW-009-P5` are preserved byte-identically at
`versions/v1/plan.md` to `versions/v5/plan.md` and are superseded by
`TDW-009-P6` version 6. No prior version is authorized for implementation. The
archived reviews are at `versions/v1/plan-review.md` to
`versions/v5/plan-review.md`.

Version 6 is bounded to the three reproduced executable defects and four test
gaps in the replacement review of version 5. Everything version 5 passed on is
carried forward unchanged, including the complete absence of rollback and the
exact 44-path allowlist.

## Precondition owned by the coordinator

Before implementation handoff the coordinator replaces
`baseline/pre-task-manifest.txt` with **one canonical JSON capture manifest** in
the exact schema specified in `design.md`, produced by the `build` mode of the
literal capture block in that artifact, captured after this plan is accepted.

It must carry exactly six top-level keys and satisfy every condition the strict
loader enforces:

1. `capture_map_version: 1`;
2. `exclusions` equal to the ten frozen entries;
3. `snapshot_dir` inside an excluded prefix, so snapshot files never become rows;
4. `allowlist_modified` — exactly **8** unique sorted paths, each present in
   `rows`;
5. `allowlist_new` — exactly **36** unique sorted paths, none present in `rows`,
   and their union exactly **44** unique paths;
6. `rows` — one entry per non-directory entry outside the exclusions, sorted by
   path, each with `path`, `type` (`f`, `l`, or `o`), `length`, and `sha256`,
   **including every symlink whether its target is a file or a directory**, and
   including pre-existing tracked modifications and pre-existing untracked leaves.

The snapshot directory must hold **exactly** the eight files named
`sha256(path.encode("utf-8")).hexdigest() + ".bin"` and nothing else, each
matching its `rows` digest.

`config/model-routing.json` appears in `rows` like any other file. This plan
records **no expected digest** for it. Implementation must not modify, revert,
absorb, or interpret it.

**Snapshots are evidence only.** No worker may restore from, delete from, or
write through a snapshot.

## Recovery policy

There is no rollback in TDW-009.

| Situation | Action |
| --- | --- |
| Implementation fails or a check does not pass | **Fix forward** within the 44 authorized paths. Do not revert, restore, or delete outside them. |
| Work has been committed in a scoped commit and must be undone | Request a **separately reviewed commit revert** from the coordinator. Outside this task. |
| Any temptation to restore from a snapshot, delete from a snapshot, or run `git checkout --` | **Forbidden.** Stop and escalate. |

## Authorized implementation paths

Exactly 8 modified tracked files and 36 new files: **44 paths**, unchanged from
versions 3 and 4. The preflight and delta tests are appended to test files
already in this list; no forty-fifth path is created.

### Modified tracked files (8)

| # | Path | Exact change |
| --- | --- | --- |
| 1 | `src/brichan/contracts/task_dossier/schema.py` | add four constants and four `__all__` entries |
| 2 | `src/brichan/contracts/task_dossier/validation.py` | five hunks only: import insertion after `ARTIFACTS,` on line 30; `EXTRA_SECTION_FIELDS` replacement at lines 71-78; `_symlinked_ancestor` helper after `_is_safe_relative`; one call site in `_validate_receipt_link`; one call site in `_validate_memory_link` |
| 3 | `src/brichan/contracts/task_dossier/__init__.py` | add exports; `main` stays `validation.main`; CLI entries only as `generate_main` and `summary_main` |
| 4 | `tests/unit/test_task_dossier_validator.py` | append ancestor-symlink regression cases only |
| 5 | `tests/contract/test_task_dossier_contract.py` | append cases only, including the capture-map exclusion-set contract |
| 6 | `tests/integration/test_task_dossier_workflow.py` | append cases only, including the preflight and after-delta tests |
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
| `config/model-routing.json` | User-owned protected state; no expected digest anywhere in this plan |
| `src/brichan/contracts/task_dossier/scaffold.py` | The generator imports only `dossier_path` |
| `src/brichan/contracts/task_dossier/parser.py` | Consumed unchanged |
| `src/brichan/resources/**` | Installed resources are out of scope; verified through the capture map |
| `docs/workflows/task-dossier/templates/**` | Templates back the scaffold and the contract tests |
| `docs/policy/**`, `PRODUCT.md`, `AGENTS.md`, `CLAUDE.md` | Policy is not changed by an implementation task |
| `projects/**` | Dossier, versions, capture, and memory writes belong to the coordinator, planner, and reviewers |
| `evals/task-dossier-pilots/results.md`, `simple/`, `normal/`, `high-risk/` | Recorded pilot evidence stays immutable |
| `metrics/**`, `bin/**`, `Makefile`, `pyproject.toml`, `CHANGELOG.md`, `VERSION` | No new gate, no packaging change, no release surface |
| `.brichan` state anywhere on disk | Checkout-only capability |

## Ordered steps

1. **Start preflight.** Run the `design.md` capture block in `preflight` mode
   against the canonical JSON manifest. The strict loader must accept the
   manifest — version, the ten exclusions, row shape and sort order, the exact
   8 / 36 / 44 allowlists — and the run must report identical rows, exactly eight
   authenticated snapshots, and all 36 planned-new paths absent from both `rows`
   and the filesystem. **Any nonzero exit is a stop, before any implementation
   write.** Record no digest for `config/model-routing.json`; read it only from
   the manifest. (`R-B1` through `R-B9`, `R-B12`, `R-X6`; v5 H1, H2, H3, AC5)

2. **Constants and validator hunks.** Add the four `schema.py` constants and
   `__all__` entries. Apply the five `validation.py` hunks. Confirm the existing
   validator suite passes unchanged. (`R-V1` through `R-V4`, `R-X1`, `R-X4`; AC5)

3. **`record.py`.** Implement the exhaustive key-to-type tables from `design.md`:
   `type(v) is ...` checks, `object_pairs_hook` duplicate rejection, JSON `null`
   as the only null, the four cross-record consistency refusals, and the **four**
   position-class injection rule sets — including `sections[].body[]` refusing
   any embedded line feed and `claim` permitting line feeds under per-line
   checks. No import of `validation.py`. (`R-G18` through `R-G27`; v4 M1, AC2)

4. **`generate.py`, Phases A to C.** Phase A renders and validates with no
   filesystem mutation. Phase B walks descriptors from the projects root,
   creating missing components with `os.mkdir(..., dir_fd=parent)`; both `ELOOP`
   and `ENOTDIR` are refusals; each level's device and inode is recorded. Phase C
   takes `fcntl.flock(dossier_fd, LOCK_EX | LOCK_NB)` immediately after the
   dossier descriptor is opened. (`R-G3` through `R-G8`, `R-G19`, `R-G25`,
   `R-G28`; AC1)

5. **`generate.py`, Phase D.** Bounded `O_EXCL` temporary, full write loop,
   `fsync`, inode verification, close, `os.link(..., follow_symlinks=False)`, the
   post-publication `os.lstat` check whose observed mismatch exits nonzero and
   leaves the entry in place, identity-verified cleanup, dossier `fsync`,
   partial-adoption diagnostic on any fault, and the final canonical re-walk
   whose drift exits `1`. `os.rename` and `os.replace` must not appear.
   (`R-G9` through `R-G17`; AC1)

6. **Generator CLI and wrapper.** `main()` with the documented arguments and
   three exit codes; `scripts/generate_task_dossier.py` shaped like
   `scripts/validate_task_dossiers.py:1-19`. (`R-G1`, `R-G2`, `R-X10`; AC2)

7. **`summary.py` computation.** Root verdict from
   `validate_projects(root, require_complete=True)`; detail from
   `validate_dossier`; the per-phase evidence rule; and the scope-code plus
   verdict-code exit composition. (`R-S1` through `R-S13`; AC4)

8. **Summary renderers, exports, wrapper.** Both renderers over one structure,
   carrying the independence caveat. Update `__init__.py`. Add
   `scripts/summarize_task_dossier.py`. Add a test asserting
   `main is validation.main` and that the three callables are distinct.
   (`R-S8`, `R-S14`, `R-X5`; AC4, AC5)

9. **Validator ancestor-link regression tests.** Append to
   `tests/unit/test_task_dossier_validator.py`: a symlinked ancestor above the
   receipt path and above the memory path each diagnosed; the clean case
   unchanged; the diagnostics originate from the validator; no existing
   diagnostic message changed. (`R-V5`, `R-V6`; AC5)

10. **Record-hardening, extraction, and line-feed tests.** One named diagnostic
    and one test per malformed class: malformed JSON; non-object root; non-UTF-8;
    duplicate key at top level and inside an artifact; boolean in an integer
    position; wrong exact type for `str`, `int`, `list`, and `dict` positions; the
    `"null"` string where JSON null is meant; unknown and missing top-level key;
    unknown, missing, and misspelled artifact; unknown and missing per-artifact
    key; identity mismatch; each of the four cross-record refusals; placeholder in
    claim, evidence, and uncertainty; evidence below the applicable rule; missing
    and invalid review verdict; unpaired `not-required`; non-null rationale on a
    required artifact; personal path; unsafe memory path; derived field and
    supplemental section on `index`; and one case per refused item in each of the
    four position classes.
    **Required pair:** an embedded line feed in a `sections[].body[]` element is
    **refused**, and a safe two-line `claim` with no structural line is
    **accepted**; plus a positive case proving a backticked `path:line` evidence
    item is accepted.
    **Extraction test:** parse the single fenced JSON block out of `design.md`
    itself, assert exactly eleven artifact keys with seventeen keys each, assert
    the four cross-record rules, render it, and assert `validate_dossier` returns
    zero diagnostics with and without `require_complete`. (`R-G26`, `R-G27`;
    v4 M1, AC2)

11. **Race, lock-ordering, and namespace-drift tests.** A symlinked dossier,
    `handoffs`, or project directory present before the walk is refused. The
    dossier descriptor is obtained, the directory is replaced by a symlink to a
    decoy outside the root, and publication runs against the held descriptor:
    every artifact lands in the original inode, the decoy stays empty, and the
    final re-walk makes the run exit `1`. The same swap injected between two
    publications. **Two-invocation first-creation test:** two cooperating apply
    invocations from a missing dossier converge on one inode, do not interleave,
    and the losing lock attempt creates no artifact and no temporary leaf.
    **Stable injected mismatch:** substitute the verified temporary source with a
    regular file and with a symlink immediately before `os.link`, and replace the
    final name after a successful link but before cleanup; assert the post-link
    check emits its diagnostic, the run never reports success, cleanup never
    unlinks the replacement, and a final entry may remain. Each such test carries
    a comment recording that it establishes the diagnostic path only and **is not
    evidence of detection against the excluded process**. (`R-G6` through
    `R-G8`, `R-G11`, `R-G17`; AC1)

12. **Publication fault-injection tests.** Patch `os.write` to short-write and to
    raise; `os.fsync` on the file and on the directory to raise; `os.close` to
    raise; `os.link` to raise `ENOSPC` and `EEXIST`; `os.unlink` during cleanup to
    raise; force temporary-name exhaustion; force a temporary inode mismatch; add
    a permission-denied case and a deterministic mocked `OSError` case so
    coverage does not depend on privilege. For each: no partial artifact, existing
    artifacts byte-identical, exit `1`, the partial-adoption diagnostic, no
    foreign file unlinked, and a retry republishing only the missing artifacts. An
    `EEXIST` collision must preserve the existing file and force the nonzero
    outcome. (`R-G10`, `R-G12` through `R-G16`; AC1)

13. **Round-trip against the validator.** Generate into a temporary root and
    assert `validate_dossier` returns zero diagnostics, covering request origin,
    redaction, and mutability; plan and review linkage; route-strength and
    override pairing; Level 0 and Level 1 ship authorization; and PR
    remote-action text. (`R-G19` through `R-G25`; AC2, AC6)

14. **Summary tests.** Every section present. The `passed` floor distinguished
    from the `not-required` one-item rule at Levels 0, 1, and 2. **Exit boundary,
    one test each:** existing but unreadable `index.md` exits `1`; a missing
    `index.md` in a handoff carrying dossier metadata, scanned at root level,
    exits `1` with partial adoption; an empty historical receipt-only handoff
    contributes no diagnostic; an unlistable dossier exits `2`; an absent
    projects root exits `2`; `--task` matching nothing exits `2`; `--task`
    matching more than one exits `2`; and an unmatched `--task` still prints the
    root-level diagnostic. Plus duplicate task IDs; a valid but `pending` dossier
    exiting `1`; an unreadable non-index artifact reported not omitted; authority
    links with a missing target, a symlinked target, and a symlinked ancestor,
    asserting the ancestor verdict comes from the validator; both independence
    arms; text and JSON parity; and no routing manifest opened. (`R-S3`, `R-S6`,
    `R-S7`, `R-S9`, `R-S11`; AC4, AC6)

15. **Author synthetic records and fixtures.** Both records under `records/`,
    task IDs `SYNTH-010` and `SYNTH-011`, slugs `synthetic-level0` and
    `synthetic-level1`, session identities matching `synthetic-fixture-`, every
    artifact claim stating non-authoritative test data. The Level 0 record is the
    complete worked record from `design.md`. Hand-write the two schema-v2
    `receipt.md` fixtures and the two `current-state.md` memory fixtures. No
    Markdown link syntax, no personal path, no embedded line feed in any
    `sections[].body[]` element. (`R-E1`, `R-E4`; AC3)

16. **Generate, validate, measure.** Dry run, then apply, into
    `evals/task-dossier-pilots/concise/projects/`. Record the exact output of each
    command in the evaluation table. Confirm 11/11 artifacts per sample, a passing
    complete gate, valid fixture receipts, and totals at or below 447 lines for
    Level 0 and 501 for Level 1. (`R-E3`, `R-E4`; AC2, AC3, AC6)

17. **Measure authoring burden.** Apply the `design.md` authored-value algorithm
    with its fixed `DECLARED_ORDER`, plus `wc -lc` per record and the combined
    total. Two independent runs must produce the same integer. No timing, token,
    or cost estimate. (`R-E5`, `R-E6`; AC3, AC7)

18. **Evaluation, inventory, documentation, contract tests.** Write
    `evals/task-dossier-pilots/concise/results.md` with measured lines against the
    baselines, artifact and evidence counts, the four metrics with an explicit
    statement of which measures compactness and which approximates burden, what
    the generator derived and refused to derive, residual risks including the
    excluded process as observation-only, and the fixed declaration that the
    samples prove contract validity only. Add the five manifest entries to
    `config/repository-paths.json`. Extend only the Tooling section of
    `docs/workflows/task-dossier.md`. Append the contract cases from version 4
    plus one asserting `design.md` contains exactly one fenced JSON block with
    eleven artifact keys, and one asserting the capture-map exclusion set matches
    the `design.md` table. Do not modify `evals/task-dossier-pilots/results.md`.
    (`R-E2`, `R-E5`; AC5, AC7)

19. **Full verification.** Run every command in the full table, including the
    explicit Python 3.10 run and the capture-map comparison over every protected
    path. (`R-X7`, `R-X8`; AC5, AC6)

20. **After-delta and its tests.** Run the `design.md` capture block in `delta`
    mode against the canonical manifest. It must report no removals, an empty
    unexpected set, an empty missing set, and a touched set **equal to all 44**
    authorized paths.
    Append to `tests/integration/test_task_dossier_workflow.py` — **an already
    authorized path, so no forty-fifth path is created** — tests that build an
    8/36/44 fixture tree and prove, using the block extracted from `design.md`:
    - **canonical round trip:** `build` output is accepted by the strict loader,
      and `preflight` against it exits `0`;
    - **manifest strictness:** wrong `capture_map_version`, altered exclusions,
      an unknown top-level key, a missing top-level key, 7-instead-of-8 modified,
      35-instead-of-36 new, a duplicate inside either list, a new path also
      present in `rows`, a duplicate row path, unsorted rows, a row missing a
      key, a row `type` outside `f`/`l`/`o`, a boolean `length`, and a duplicate
      JSON key — each exits nonzero;
    - **symlink completeness:** a pre-existing symlink **to a directory** yields
      an `l` row; retargeting it fails preflight and delta; replacing it with a
      real empty directory removes the row and fails; replacing it with a regular
      file flips the row `type` and fails; a symlink at an exclusion boundary is
      excluded, not recorded;
    - **set equality:** touching all 44 exits `0`; touching 43 exits nonzero and
      names the untouched path; touching all 44 plus one outside path exits
      nonzero and names the unexpected path; a removal exits nonzero;
    - **outside-allowlist changes:** a post-capture change to a pre-existing
      tracked file and to a pre-existing untracked file each fail preflight and
      land in `unexpected` at delta;
    - **snapshots:** a stray file in the snapshot directory, a corrupted
      snapshot, a removed snapshot, and a symlinked snapshot each fail preflight.
    Append to `tests/contract/test_task_dossier_contract.py` a case asserting the
    exclusion set is exactly the ten entries in the `design.md` table and that
    `design.md` contains exactly one fenced `python` block whose source defines
    `capture_map_version`. (`R-B1` through `R-B14`; v5 H1, H2, H3, test gaps 1-3,
    AC5, AC6)

21. **Hand off for review.** Report the delta output, focused and full test
    output, measured line and record metrics, and the preflight record. Do not
    commit, push, open a pull request, or write `plan-review.md` or
    `code-review.md`. Do not restore or delete anything. (AC8)

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
| `grep -n "model-routing.json\|model_routing" src/brichan/contracts/task_dossier/{record,generate,summary}.py` | no match |
| `make dossiers` | exit `0`; no new diagnostic on `TDW-006` through `TDW-009` |

Evaluation, after steps 16 and 17:

| Command | Expectation |
| --- | --- |
| `python3 scripts/validate_task_dossiers.py evals/task-dossier-pilots/concise/projects --require-complete` | exit `0`, two dossiers |
| `python3 scripts/validate_handoff_receipts.py evals/task-dossier-pilots/concise/projects` | exit `0`, two receipts |
| `python3 scripts/summarize_task_dossier.py evals/task-dossier-pilots/concise/projects` | exit `0` |
| explicit eleven-path `wc -l` per sample | Level 0 at most 447, Level 1 at most 501 |
| `wc -lc` per record plus the authored-value count | recorded; reproduces across two runs |

Full, at steps 19 and 20:

| Command | Expectation |
| --- | --- |
| `make check` | exit `0` |
| `python3.10 -m unittest tests.unit.test_task_dossier_generator tests.unit.test_task_dossier_summary tests.unit.test_task_dossier_validator tests.integration.test_task_dossier_workflow -v` | all pass on the 3.10 floor |
| `make dossiers`, `make receipts`, `make path-check` | exit `0` |
| `python3.10 capture.py preflight --root . --manifest <capture-manifest.json>` | exit `0` before any write |
| `python3.10 capture.py delta --root . --manifest <capture-manifest.json>` | exit `0`; touched set equals all 44; no removals; unexpected and missing both empty |
| capture-manifest comparison for `config/model-routing.json`, all files under `src/brichan/resources/`, and every artifact of `TDW-006`, `TDW-007`, `TDW-008` | every row identical to its capture |

Explicitly not used as preservation evidence: bare `git diff` or
`git status --short` against `HEAD`, any hard-coded digest for
`config/model-routing.json`, and any row-only or sectioned capture format.

## Stop conditions

Stop, write nothing further, and escalate when any becomes true:

- The canonical manifest is absent, is rejected by the strict loader, or does not
  carry exactly 8 modified, 36 new, and 44 union paths.
- The start preflight exits nonzero for any reason.
- The snapshot directory does not hold exactly the eight expected files, or any
  snapshot fails no-follow digest authentication.
- Any step would require modifying, reverting, or interpreting
  `config/model-routing.json`, or recording an expected digest for it.
- Any step would require restoring from a snapshot, deleting from a snapshot,
  running `git checkout --`, or any other rollback-shaped action.
- Closing a safety property appears to require modifying `scaffold.py` or
  `parser.py`, a Linux-only syscall, or a production hook added solely for a test.
- Publication appears to require `os.rename`, `os.replace`, deleting an existing
  file, or accepting a partial artifact at a final name.
- Any artifact, test name, comment, or report would claim prevention, detection,
  or compare-and-swap safety against the excluded process.
- The extraction test cannot load the literal fenced record block from
  `design.md`, or the capture block cannot be extracted and run.
- Making ancestor-symlinked authority paths invalid would change any existing
  diagnostic or require more than the five enumerated `validation.py` hunks.
- Meeting the 30% reduction appears to require dropping an artifact, dropping an
  evidence item, or lowering a level floor.
- Any dependency outside the standard library, or any construct requiring Python
  newer than 3.10.
- The after-delta touched set cannot be made to equal all 44 authorized paths, or
  closing a gap appears to need a forty-fifth path.

## Execution state

Steps 1 through 21 are unexecuted. This session was scoped to the version-5
snapshots and the five planner-owned artifacts, so no module, test, wrapper,
sample, fixture, capture manifest, or validator hunk was created, and no
acceptance criterion that depends on execution is claimed as met.
`TDW-009-AC1` through `AC7` are discharged at execution time on the `implement`
route; `TDW-009-AC8` is discharged by fresh independent review sessions.

## Claim or decision

Plan `TDW-009-P6` is accepted at version 6; `index.md` must echo that ID and
version. It authorizes exactly 44 paths, unchanged, and hosts every new
manifest, symlink, set-equality, and routing-probe test in test files that list
already contains. The implementation-start gate and the handoff delta are now
mechanically sound: one canonical JSON manifest emitted and consumed by the same
strict parser, symlink rows in both name positions, allowlists validated to
8 / 36 / 44 inside the manifest, and a delta that requires the touched set to
equal all 44. Rollback remains entirely absent.

## Evidence

- The literal capture block in `design.md` was **extracted mechanically and run
  on Python 3.10.11** before this plan was called passed. Against an 8/36/44
  fixture the twelve scenarios in steps 1 and 20 behaved exactly as specified:
  canonical capture and clean preflight exited `0`; a full 44-path touch exited
  `0`; touching 43 exited `1` naming the untouched path; touching 44 plus one
  outside path exited `1` naming the unexpected path; a symlink-to-directory
  retarget exited `1` at both preflight and delta; replacing that link with a
  real directory and with a regular file each exited `1`; outside-allowlist
  tracked and untracked changes each exited `1`; and the restored baseline
  exited `0`.
- Fourteen manifest mutations and four snapshot faults each failed closed on the
  extracted block, which is the executable basis for step 20's strictness and
  snapshot cases.
- Run against **this repository**, the extracted block produced a canonical
  manifest with 333 rows, 8 / 36 / 44 allowlists,
  `config/model-routing.json` at its current user-owned bytes, both pre-existing
  tracked modifications present, and all 16 files under `src/brichan/resources/`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v5/plan-review.md:65-92,94-121,122-151`
  state `H1`, `H2`, and `H3` with the reviewer's own reproductions, and `:217-229`
  lists the four test gaps that steps 14 and 20 now close.
- The step-14 routing probe technique was demonstrated read-only against an
  existing package module: a static scan found neither `model-routing.json` nor
  `model_routing`, and an import under an `open` spy recorded no routing file
  opened and no `model_routing` module in `sys.modules`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:229-262`
  fixes the four version-6 decisions and the `TDW-009-P6` identity, and holds the
  allowlist at 44.

## Uncertainty

- The capture, preflight, and delta remain point-in-time observations. A
  same-identity process mutating files between two observations defeats all
  three.
- The capture logic exists twice: as the literal block the implementer runs and
  inside the step-20 tests. Keeping them in step is a maintenance cost this plan
  accepts rather than solves.
- `delta` requires the touched set to equal all 44, so a partial implementation
  cannot hand off even to report progress. That is intended but removes an escape
  hatch a future task may want.
- The three counts 8, 36, and 44 are frozen in the capture block. A future scope
  change must alter the manifest and the constants together; until then the
  loader fails closed.
- Excluding `.env` and `.DS_Store` means changes to them are invisible to steps 1
  and 20.
- The 333-row figure is this working tree at planning time, not a contract.
- Removing rollback means a failed implementation leaves partial work in the tree
  until a coordinator-reviewed commit revert.
- The step-14 import probe was demonstrated on an existing module because the
  generator does not exist yet; its real subject is created at implementation
  time.
