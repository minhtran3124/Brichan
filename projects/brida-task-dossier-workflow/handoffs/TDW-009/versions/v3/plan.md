# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `plan`
- Artifact version: `3`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md@TDW-009-P2-v2+task-packet-amendment-3`
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

- Plan ID: `TDW-009-P3`
- Plan status: `accepted`

## Version 3 supersession

`TDW-009-P1` version 1 and `TDW-009-P2` version 2 are preserved byte-identically
at `versions/v1/plan.md` and `versions/v2/plan.md` and are superseded by
`TDW-009-P3` version 3. Neither prior version is authorized for implementation.
Any review naming `TDW-009-P1` or `TDW-009-P2` reviews a superseded version;
the archived reviews are at `versions/v1/plan-review.md` and
`versions/v2/plan-review.md`.

## Precondition owned by the coordinator

The pre-task baseline at `baseline/pre-task-manifest.txt` is insufficient: it
records no digest or content for the tracked files the implementer will modify,
no repository identity, no exact untracked-leaf inventory, and omits
`src/brichan/resources/__init__.py`.

Before implementation handoff the coordinator replaces it with an
**implementation-start manifest** containing:

1. a stable repository identity;
2. the exact 44-path allowlist below;
3. for **every** allowlisted path, presence or absence, plus a digest for each
   path that exists — including all eight modified tracked files;
4. an exact untracked-leaf inventory, enumerating individual files rather than
   collapsing a directory to one entry;
5. every file under `src/brichan/resources/`, including
   `src/brichan/resources/__init__.py` and every package file;
6. the current digest of `config/model-routing.json`, expected to remain
   `31466a36cef7e6966dec52211d14769e2c91b8ab1a7be33b468ebcf501a4838d`.

It is captured **after** plan version 3 is accepted and **excludes**
coordinator-, planner-, and reviewer-owned dossier paths, so planning and review
leaves can never be counted as implementation leaves.

The implementer refuses to start if the manifest is absent or lacks any of the
six elements. Every preservation, delta, and rollback claim in this plan is made
against it, never against `HEAD`.

## Authorized implementation paths

Exactly 8 modified tracked files and 36 new files: **44 paths**. Version 2
authorized 43; the change is one added test file, required by the validator
extension in coordinator decision 2.

### Modified tracked files (8)

| # | Path | Exact change |
| --- | --- | --- |
| 1 | `src/brichan/contracts/task_dossier/schema.py` | add `RECORD_SCHEMA_VERSION`, `ARTIFACT_TITLES`, `ARTIFACT_OWNERS`, `ARTIFACT_EXTRA_SECTIONS` and four `__all__` entries |
| 2 | `src/brichan/contracts/task_dossier/validation.py` | five hunks only: import insertion after `ARTIFACTS,` on line 30; `EXTRA_SECTION_FIELDS` replacement at lines 71-78; `_symlinked_ancestor` helper after `_is_safe_relative`; one call site in `_validate_receipt_link`; one call site in `_validate_memory_link` |
| 3 | `src/brichan/contracts/task_dossier/__init__.py` | add record, generate, summary exports; `main` stays `validation.main`; CLI entries only as `generate_main` and `summary_main` |
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
eleven members of `ARTIFACTS`. Unchanged from version 2; the dossier lock adds no
leaf because it is taken on the directory descriptor itself.

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
| `src/brichan/contracts/task_dossier/scaffold.py` | The amendment forbids changing scaffold behaviour; the generator shares no write code and imports only `dossier_path` |
| `src/brichan/contracts/task_dossier/parser.py` | Consumed unchanged |
| `config/model-routing.json` | Routing neutrality; digest must match the manifest at handoff |
| `src/brichan/resources/**` including `__init__.py` | Installed resources are out of scope; every file digest-verified |
| `docs/workflows/task-dossier/templates/**` | Templates back the scaffold and the contract tests |
| `docs/policy/**`, `PRODUCT.md`, `AGENTS.md`, `CLAUDE.md` | Policy is not changed by an implementation task |
| `projects/**` | Dossier, versions, baseline, and memory writes belong to the coordinator, planner, and reviewers |
| `evals/task-dossier-pilots/results.md`, `simple/`, `normal/`, `high-risk/` | Recorded pilot evidence stays immutable |
| `metrics/**`, `bin/**`, `Makefile`, `pyproject.toml`, `CHANGELOG.md`, `VERSION` | No new gate, no packaging change, no release surface |
| `.brichan` state anywhere on disk | Checkout-only capability |

## Ordered steps

1. **Manifest precondition.** Confirm the implementation-start manifest exists
   and carries all six elements; refuse to proceed otherwise. Record the
   command that computes the implementation delta from it. (`R-X11`, `R-X12`;
   H2, AC5)

2. **Constants and validator hunks.** Add the four `schema.py` constants and
   `__all__` entries. Apply the five `validation.py` hunks. The helper walks
   repo-relative components from the repository root, `lstat`s each, follows
   nothing, and returns the first symlinked ancestor or `None`. Confirm the
   existing validator suite passes unchanged. (`R-V1` through `R-V4`, `R-X1`,
   `R-X4`; H1, AC5)

3. **`record.py`.** Implement the exhaustive key-to-type table exactly as
   `design.md` states: `type(v) is ...` checks, `object_pairs_hook` duplicate
   rejection, JSON `null` as the only null with the `"null"` string refused, the
   three cross-record consistency refusals, and the three position-class
   injection rule sets. Mirror `validation.py:276-355` for evidence depth. No
   import of `validation.py`. (`R-G18` through `R-G27`; M1, TG3, AC2)

4. **`generate.py`, rendering, walk, and lock.** `render_artifact` per the fixed
   block order. Descriptor walk from the projects root with
   `O_RDONLY | O_DIRECTORY | O_NOFOLLOW`, `fstat` verification, `os.mkdir` with
   `dir_fd` for missing components, both `ELOOP` and `ENOTDIR` as refusals, and
   the recorded device/inode per level. In apply mode take
   `fcntl.flock(dossier_fd, LOCK_EX | LOCK_NB)`; a conflicting holder is a named
   refusal, never a wait. (`R-G4` through `R-G8`, `R-G19`, `R-G25`, `R-G28`;
   C1, AC1)

5. **`generate.py`, publication and re-walk.** Render all eleven bodies before
   any mutation. Per artifact: bounded `O_EXCL` temporary, full write loop,
   `fsync`, inode verification, close, `os.link(..., follow_symlinks=False)`,
   then the **post-publication `os.lstat` check** that the final entry is a
   regular file whose device and inode equal the recorded temporary — mismatch
   is a publication-integrity failure that exits nonzero and leaves the entry in
   place. Identity-verified temporary cleanup. `fsync` the dossier descriptor.
   Partial-adoption diagnostic on any fault. Finally re-walk the canonical chain
   read-only and compare device and inode per level; drift exits `1`.
   `os.rename` and `os.replace` must not appear in the module. (`R-G9` through
   `R-G17`; C1, H3, AC1)

6. **Generator CLI and wrapper.** `main()` with the documented arguments and the
   three exit codes; `scripts/generate_task_dossier.py` shaped like
   `scripts/validate_task_dossiers.py:1-19`. (`R-G1`, `R-G2`, `R-X10`; AC2)

7. **`summary.py` computation.** `DossierSummary` and `summarize_dossier`. Root
   verdict from `validate_projects(root, require_complete=True)`; per-dossier
   detail from `validate_dossier`; the per-phase evidence rule; the exact
   unreadable-artifact versus unreadable-dossier boundary. (`R-S1` through
   `R-S13`; AC4)

8. **Summary renderers, exports, wrapper.** `render_summary_text` and
   `render_summary_json` over one structure, both carrying the independence
   caveat. Update `__init__.py` with the exact export list. Add
   `scripts/summarize_task_dossier.py`. Add a test asserting
   `main is validation.main` and that the three callables are distinct.
   (`R-S8`, `R-S14`, `R-X5`; AC4, AC5)

9. **Validator ancestor-link regression tests.** Append to
   `tests/unit/test_task_dossier_validator.py`: a symlinked ancestor above the
   receipt path is diagnosed; a symlinked ancestor above the memory path is
   diagnosed; the clean case is unchanged; the diagnostics originate from
   `validate_projects` and `validate_dossier`, not from any summary code. Assert
   no existing diagnostic message changed. (`R-V5`, `R-V6`; H1, TG7, AC5)

10. **Record-hardening tests.** One named diagnostic and one test per class:
    malformed JSON; non-object root; non-UTF-8; duplicate key at top level and
    inside an artifact; boolean in an integer position; wrong exact type for
    `str`, `int`, `list`, and `dict` positions; the `"null"` string where JSON
    null is meant; unknown and missing top-level key; unknown, missing, and
    misspelled artifact; unknown and missing per-artifact key; identity
    mismatch; each of the three cross-record consistency refusals; placeholder
    in claim, evidence, and uncertainty; evidence below the applicable rule;
    missing and invalid review verdict; unpaired `not-required`; non-null
    rationale on a required artifact; personal path; unsafe memory path;
    derived field and supplemental section on `index`; and one case per refused
    item in each of the three position classes, including a **positive** case
    proving a backticked `path:line` evidence item is accepted. Assert the
    worked example in `design.md` validates. (`R-G26`, `R-G27`; M1, TG3, AC2)

11. **Race and namespace-drift tests.** A symlinked dossier, `handoffs`, or
    project directory present before the walk is refused. The dossier descriptor
    is obtained, the directory is then replaced on disk by a symlink to a decoy
    outside the root, and publication runs against the held descriptor: assert
    every artifact lands in the original inode, the decoy stays empty, **and the
    final re-walk makes the run exit `1` rather than reporting success**. The
    same swap injected between two publications via a patched `os.link` first
    call. Substitute the verified temporary source with a regular file and with
    a symlink immediately before `os.link`: assert the post-publication check
    fails the run with the publication-integrity diagnostic, that the run never
    reports success, and — stated honestly — that a final entry **may** exist and
    is deliberately not removed. Replace the final name after a successful link
    but before cleanup: assert cleanup never unlinks it. A second concurrent
    holder of the dossier lock is refused. (`R-G6`, `R-G8`, `R-G11`, `R-G17`;
    C1, H3, TG1, AC1)

12. **Publication fault-injection tests.** Patch `os.write` to short-write and
    to raise; `os.fsync` on the file and on the directory to raise; `os.close`
    to raise; `os.link` to raise `ENOSPC` and `EEXIST`; `os.unlink` during
    cleanup to raise; force temporary-name counter exhaustion; force a
    temporary inode mismatch before publication; and add a permission-denied
    case on the dossier directory. For each: no partial artifact at any final
    name, pre-existing artifacts byte-identical, exit `1`, the partial-adoption
    diagnostic naming published and unpublished artifacts, no foreign file
    unlinked, and a retry republishing only the missing artifacts. A
    permission case that cannot run must be skipped with a recorded reason,
    never silently passed. (`R-G12` through `R-G16`; TG2, AC1)

13. **Round-trip against the validator.** Generate into a temporary root from a
    well-formed record, then run `validate_dossier` and assert zero
    diagnostics, covering request origin, redaction, and mutability; plan and
    review linkage; route-strength and override pairing; Level 0 and Level 1
    ship authorization; and PR remote-action text. (`R-G19` through `R-G25`;
    TG4, AC2, AC6)

14. **Summary tests.** Every reported section present. The `passed` floor
    distinguished from the `not-required` one-item rule at Levels 0, 1, and 2,
    including a Level 2 `not-required` artifact with one item reported
    compliant. Partial adoption; duplicate task IDs; `--task` matching none and
    matching more than one, both exit `2`. A valid but `pending` dossier exits
    `1`. The exit boundary: an unreadable **artifact** inside a discoverable
    dossier exits `1` and is reported not omitted; an absent, unlistable, or
    index-less **dossier** exits `2`. Authority links with a missing target, a
    symlinked target, and a symlinked ancestor — asserting the ancestor verdict
    comes from the validator, not from summary code. Both independence arms
    separately, with placeholder and with synthetic unequal identities. Text and
    JSON carrying the same facts and exit code. No routing manifest opened.
    (`R-S3`, `R-S6`, `R-S7`, `R-S11`; H1, TG5, TG6, TG7, AC4, AC6)

15. **Author synthetic records and fixtures.** Both records under `records/`,
    task IDs `SYNTH-010` and `SYNTH-011`, slugs `synthetic-level0` and
    `synthetic-level1`, every session identity matching `synthetic-fixture-`,
    every artifact claim stating non-authoritative test data. Hand-write the two
    schema-v2 `receipt.md` fixtures and the two `current-state.md` memory
    fixtures. No Markdown link syntax, no personal path. (`R-E1`, `R-E4`; AC3)

16. **Generate, validate, measure.** Dry run, then apply, into
    `evals/task-dossier-pilots/concise/projects/`. Record the exact output of
    each command in the evaluation verification table. Confirm 11/11 artifacts
    per sample, a passing complete gate, valid fixture receipts, and totals at
    or below 447 lines for Level 0 and 501 for Level 1. (`R-E3`, `R-E4`; AC2,
    AC3, AC6)

17. **Measure authoring burden.** Apply the `design.md` authored-value algorithm
    with its fixed `DECLARED_ORDER`, plus `wc -lc` per record and the combined
    total. Two independent runs of the algorithm must produce the same integer;
    record it. Do not estimate timing, tokens, or cost. (`R-E5`, `R-E6`; TG9,
    AC3, AC7)

18. **Evaluation, inventory, documentation, contract tests.** Write
    `evals/task-dossier-pilots/concise/results.md` with measured lines against
    the 639-line and 716-line baselines, artifact and evidence counts, the four
    metrics with an explicit statement of which measures compactness and which
    approximates burden, what the generator derived and refused to derive,
    residual risks including the excluded attacker, and the fixed declaration
    that the samples prove contract validity only. Add the five manifest
    entries to `config/repository-paths.json`. Extend only the Tooling section
    of `docs/workflows/task-dossier.md`. Append the contract cases: every
    `ARTIFACT_OWNERS` value in `OWNERS`; both reviews map to `reviewer`;
    `ARTIFACT_TITLES` and `ARTIFACT_EXTRA_SECTIONS` cover the right sets;
    `EXTRA_SECTION_FIELDS is ARTIFACT_EXTRA_SECTIONS`; the manifest inventories
    the five new files; both records use the synthetic prefix; and `results.md`
    carries the declaration. Do not modify
    `evals/task-dossier-pilots/results.md`. (`R-E2`, `R-E5`; AC5, AC7)

19. **Full verification.** Run every command in the full table, including the
    explicit Python 3.10 run, the manifest digest comparison over every
    protected path, and the 44-path delta command executed against a fixture
    that contains unrelated untracked planning and reviewer files plus
    pre-existing user changes. (`R-X7`, `R-X8`, `R-X11`; H2, TG8, AC5, AC6)

20. **Record the rollback procedure.** From the manifest, produce the exact
    reverse patch for the eight modified tracked files and the exact deletion
    list for the 36 new paths, each proven absent pre-implementation. Do not
    execute unless a stop condition fires. (`R-X13`; H2)

21. **Hand off for review.** Report the delta against the manifest, focused and
    full test output, measured line and record metrics, and the rollback
    procedure. Do not commit, push, open a pull request, or write
    `plan-review.md` or `code-review.md`. (AC8)

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
| manifest digest check for `scaffold.py` and `parser.py` | unchanged |

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
| manifest digest comparison over `config/model-routing.json`, every file under `src/brichan/resources/` including `__init__.py`, and every artifact of `TDW-006`, `TDW-007`, `TDW-008` | every digest identical |
| the 44-path delta command, run against a fixture with unrelated untracked planning and reviewer files and pre-existing user changes | exact set equality with the 44 authorized paths |

Explicitly not used as preservation evidence: bare `git diff` or
`git status --short` against `HEAD`. The working tree carries pre-existing user
changes, so those comparisons cannot separate this task's delta from the user's.

## Stop conditions

Stop, write nothing further, and escalate when any becomes true:

- The implementation-start manifest is absent or lacks any of its six elements.
- Closing a safety property appears to require modifying `scaffold.py` or
  `parser.py`, a Linux-only syscall, or a production hook added solely for a
  test.
- Publication appears to require `os.rename`, `os.replace`, deleting an existing
  file, or accepting a partial artifact at a final name.
- The post-publication verification or the final re-walk cannot be implemented,
  or would have to be downgraded to a warning.
- Making ancestor-symlinked authority paths invalid would change any existing
  validator diagnostic's condition or message, or would require more than the
  five enumerated `validation.py` hunks.
- Meeting the 30% reduction appears to require dropping an artifact, dropping an
  evidence item, or lowering a level floor.
- A sample appears to need a real reviewer session, or a synthetic verdict would
  have to be presented as real review evidence.
- Any dependency outside the standard library, or any construct requiring Python
  newer than 3.10.
- Any change to `config/model-routing.json`, `src/brichan/resources/`, or
  installed `.brichan` state appears necessary.
- The observed delta cannot be made to equal the 44 authorized paths.
- Any artifact would have to claim protection against the excluded attacker.

## Rollback

Computed from the implementation-start manifest, never from `HEAD`.

1. For each of the 8 modified tracked files, apply the reverse of this task's
   hunks only, using the manifest's recorded pre-implementation content.
   Whole-file `git checkout --` is forbidden: it reverts to `HEAD` and would
   discard the user's pre-existing changes.
2. Delete the 36 new paths, each proven absent in the manifest's
   presence/absence record and unchanged since.
3. Abort and escalate if any target's current digest differs from what the
   rollback expects, rather than forcing it.

No data migration occurs, no existing dossier is read or rewritten, no packaged
resource is touched, nothing is committed, and no remote state changes. Partial
rollback is safe: the new modules are unreferenced by any existing entry point.
The two added validator diagnostics revert with hunks 3 through 5 of file 2.

## Execution state

Steps 1 through 21 are unexecuted. This session was scoped to the version-2
snapshots and the five planner-owned artifacts, so no module, test, wrapper,
sample, fixture, manifest entry, or validator hunk was created, and no acceptance
criterion that depends on execution is claimed as met. `TDW-009-AC1` through
`AC7` are discharged at execution time on the `implement` route; `TDW-009-AC8`
is discharged by fresh independent review sessions.

## Claim or decision

Plan `TDW-009-P3` is accepted at version 3; `index.md` must echo that ID and
version. It authorizes exactly 44 paths — 8 modified tracked files and 36 new
files, of which 29 are enumerated evaluation leaves — forbids ten path groups by
name including `scaffold.py` and `parser.py`, orders 21 steps so that every
version-2 finding and every test-gap class is discharged by a named command, and
computes every preservation, delta, and rollback claim from a
coordinator-captured implementation-start manifest. The single path added since
version 2 is `tests/unit/test_task_dossier_validator.py`, required because
coordinator decision 2 moves ancestor-link invalidity into the validator.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md:115-138`
  itemizes what the pre-task baseline lacks — no digest or content for the
  modified tracked files, no commit identity, a collapsed untracked entry, and a
  missing `src/brichan/resources/__init__.py` — which is exactly the six-element
  manifest the precondition now requires.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md:140-156,205-217`
  supplies `H3` and the five additional required tests that steps 11, 12, 14,
  and 19 discharge, including the delta command run against a fixture holding
  unrelated untracked planning files.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md:219-233`
  independently confirms the version-2 arithmetic of 7 modified, 7 new, and 29
  evaluation leaves totalling 43 unique paths; adding
  `tests/unit/test_task_dossier_validator.py` reconciles that to 44.
- `src/brichan/contracts/task_dossier/validation.py:772-780,782-826,827-886`
  fixes the exact insertion points for hunks 3 through 5 of step 2 and shows
  that neither link validator currently inspects an ancestor.
- `src/brichan/contracts/task_dossier/validation.py:1109-1116` shows
  `discover_dossiers` globbing only the root it is given, so the isolated
  evaluation root in step 16 cannot join `make dossiers`.
- `src/brichan/contracts/receipts/validation.py:15-70,1123-1125` fixes the
  eleven required receipt sections for the step-15 fixtures and shows the glob
  that lets step 16 validate both with the existing tool.
- Python 3.10.11 is present on this machine, so the 3.10 floor run in step 19 is
  an executable check rather than an aspiration.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:99-139`
  records the three binding version-3 decisions and the requirement to preserve
  version 2 under `versions/v2/` before supersession; those five snapshots were
  written and digest-verified before any version-3 content was authored.

## Uncertainty

- Step 11's swap cases patch `os.link` and replace directory entries between
  operations. These are test seams over standard-library functions, not
  production hooks. If any case cannot be written without adding a hook to
  `generate.py`, the stop condition applies and the case is escalated rather
  than weakened.
- The temporary-source substitution tests assert **detection**, not prevention,
  and must record that a final entry may exist afterwards. Writing them as
  prevention tests would contradict the stated threat-model boundary, so a
  passing suite here is not evidence against the excluded attacker.
- The permission-denied case in step 12 may be unrunnable as root in some
  environments; it must be skipped with a recorded reason.
- The 447-line and 501-line targets are budgets, not predictions of the samples'
  real content. Exceeding one triggers the stop condition.
- The orphan-temporary case is recorded but unswept: a crash between temporary
  creation and publication leaves a recognisable `.tdgen.*.tmp` file that no
  step removes, because sweeping would mean deleting files the generator did not
  verify it created.
