# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `plan`
- Artifact version: `2`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/plan-review.md@TDW-009-P1-v1+task-packet-amendment`
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

- Plan ID: `TDW-009-P2`
- Plan status: `accepted`

## Version 2 supersession

Plan `TDW-009-P1` version 1 is preserved byte-identically at
`versions/v1/plan.md` and is superseded by `TDW-009-P2` version 2. Version 1 is
not authorized for implementation. Any `plan-review.md` or `code-review.md`
naming `TDW-009-P1` reviews the superseded version.

## Precondition owned by the coordinator

Before the implementation worker starts, the coordinator captures a pre-task
path-and-digest baseline at
`projects/brida-task-dossier-workflow/handoffs/TDW-009/baseline/pre-task-manifest.txt`,
covering at minimum `config/model-routing.json`, every file under
`src/brichan/resources/`, every artifact of `TDW-006`, `TDW-007`, and `TDW-008`,
and the tracked/untracked path list of the working tree. The implementer does
not write this file and must refuse to start without it.

This exists because the working tree already carries pre-existing user changes.
Every "unchanged" claim in this plan is made against that baseline, never
against `HEAD`.

## Authorized implementation paths

Exactly 7 modified tracked files and 36 new files. Nothing else.

### Modified tracked files (7)

| # | Path | Exact change |
| --- | --- | --- |
| 1 | `src/brichan/contracts/task_dossier/schema.py` | add `RECORD_SCHEMA_VERSION`, `ARTIFACT_TITLES`, `ARTIFACT_OWNERS`, `ARTIFACT_EXTRA_SECTIONS` and their four `__all__` entries |
| 2 | `src/brichan/contracts/task_dossier/validation.py` | two hunks only: `ARTIFACT_EXTRA_SECTIONS,` inserted after `ARTIFACTS,` on line 30, and lines 71-78 replaced by `EXTRA_SECTION_FIELDS = ARTIFACT_EXTRA_SECTIONS` |
| 3 | `src/brichan/contracts/task_dossier/__init__.py` | add record, generate, and summary exports; `main` stays bound to `validation.main`; CLI entry points exported only as `generate_main` and `summary_main` |
| 4 | `tests/contract/test_task_dossier_contract.py` | append cases only |
| 5 | `tests/integration/test_task_dossier_workflow.py` | append cases only |
| 6 | `config/repository-paths.json` | inventory the five new source and wrapper files |
| 7 | `docs/workflows/task-dossier.md` | extend the Tooling section only |

### New source and test files (7)

`src/brichan/contracts/task_dossier/record.py` ·
`src/brichan/contracts/task_dossier/generate.py` ·
`src/brichan/contracts/task_dossier/summary.py` ·
`scripts/generate_task_dossier.py` ·
`scripts/summarize_task_dossier.py` ·
`tests/unit/test_task_dossier_generator.py` ·
`tests/unit/test_task_dossier_summary.py`

### Closed evaluation leaf allowlist (29)

Every evaluation output path, enumerated. All are relative to
`evals/task-dossier-pilots/concise/`. `<A>` expands to the eleven members of
`ARTIFACTS`, giving eleven files per dossier.

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

The changed-path gate in step 16 compares the observed task delta against this
list by exact set equality. A path outside it fails the step; a missing path
fails the step.

## Paths that must remain untouched

| Path | Reason |
| --- | --- |
| `src/brichan/contracts/task_dossier/scaffold.py` | The packet amendment forbids changing scaffold behaviour; the generator shares no write code with it and imports only `dossier_path` |
| `src/brichan/contracts/task_dossier/parser.py` | Consumed unchanged by both new modules |
| `config/model-routing.json` | Routing neutrality; the user's pre-existing diff must survive byte-identical against the baseline |
| `src/brichan/resources/**` | Installed resources are out of scope |
| `docs/workflows/task-dossier/templates/**` | Templates back the scaffold and the contract tests |
| `docs/policy/**`, `PRODUCT.md`, `AGENTS.md`, `CLAUDE.md` | Policy is not changed by an implementation task |
| `projects/**` | Dossier, baseline, and memory writes belong to the coordinator, planner, and reviewers |
| `evals/task-dossier-pilots/results.md`, `simple/`, `normal/`, `high-risk/` | Recorded pilot evidence stays immutable |
| `metrics/**`, `bin/**`, `Makefile`, `pyproject.toml`, `CHANGELOG.md`, `VERSION` | No new gate, no packaging change, no release surface |
| `.brichan` state anywhere on disk | Checkout-only capability |

## Ordered steps

1. **Baseline and additive constants.** Confirm the coordinator baseline exists
   and is readable; refuse to proceed otherwise. Add the four constants to
   `schema.py` and `__all__`. Apply the two `validation.py` hunks — the import
   insertion after `ARTIFACTS,` on line 30 and the `EXTRA_SECTION_FIELDS`
   replacement. Run `python3 -m unittest tests.unit.test_task_dossier_validator -v`
   and confirm the existing suite passes with no changed assertion.
   (`R-X1`, `R-X4`, `R-X11`; H6, M2, AC5)

2. **`record.py`.** Dataclasses `ArtifactRecord` and `TaskRecord`;
   `load_record(path, *, task_id, level, project)` returning
   `(TaskRecord | None, list[Diagnostic])`. Implement the exact recursive type
   schema with `type(v) is ...` checks, the duplicate-key `object_pairs_hook`,
   every row of the record-diagnostics table, and the closed structural-injection
   rule set for single-line and multi-line positions. Mirror
   `validation.py:276-355` for evidence depth. No import of `validation.py`.
   (`R-G16` through `R-G23`; H4, AC2)

3. **`generate.py`, rendering and descriptor walk.** Implement
   `render_artifact` per the design's fixed block order, then the walk: open the
   projects root with `O_RDONLY | O_DIRECTORY | O_NOFOLLOW`, verify `fstat`
   against `stat(..., follow_symlinks=False)`, then open `<project>`,
   `handoffs`, `<task-id>` relative to the already-open parent, creating missing
   components with `os.mkdir(..., dir_fd=parent)`. Treat both `ELOOP` and
   `ENOTDIR` as refusals. Never use a pathname below the projects root twice.
   (`R-G4` through `R-G7`, `R-G15`, `R-G21`, `R-G24`; C1, AC1)

4. **`generate.py`, atomic publication.** Render all eleven bodies before any
   mutation. Per artifact: `O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW` temporary with
   `dir_fd`, full write loop, `fsync`, device/inode verification against the
   descriptor, close, then
   `os.link(tmp, final, src_dir_fd, dst_dir_fd, follow_symlinks=False)`.
   `EEXIST` means `preserve`. Clean up the temporary only after re-verifying its
   identity. `fsync` the dossier descriptor. On any fault, emit a
   partial-adoption diagnostic naming published and unpublished artifacts and
   exit `1`. `os.rename` and `os.replace` must not appear in the module.
   (`R-G3`, `R-G8` through `R-G13`; C1, H1, AC1)

5. **Generator CLI and wrapper.** `main()` with the documented arguments and the
   three exit codes; `scripts/generate_task_dossier.py` byte-shaped like
   `scripts/validate_task_dossiers.py:1-19` apart from docstring and imported
   `main`. (`R-G1`, `R-G2`, `R-G14`, `R-X10`; AC2)

6. **`summary.py` computation.** `DossierSummary` and `summarize_dossier`. Take
   the root verdict from `validate_projects(root, require_complete=True)`;
   attribute per-dossier detail with `validate_dossier`; never let the latter
   contradict the former. Apply the per-phase evidence rule: level floor for
   `passed`, one-item rule for `not-required`, `not-applicable` otherwise.
   (`R-S3`, `R-S9` through `R-S13`; H3, AC4)

7. **Summary renderers and package exports.** `render_summary_text` and
   `render_summary_json` over one structure, both carrying the independence
   caveat in fixed wording. Update `__init__.py` with the exact export list;
   `main` stays `validation.main`, CLI entries are `generate_main` and
   `summary_main`. Add `scripts/summarize_task_dossier.py`. Add a unit test
   asserting `main is validation.main` and that the three callables are
   distinct. (`R-S8`, `R-S14`, `R-X5`; M2, AC4, AC5)

8. **Descriptor-race tests.** Prove the C1 guarantee deterministically, not by
   luck. At minimum: a symlinked dossier directory present before the walk is
   refused; a symlinked `handoffs` or project directory is refused; the walk's
   dossier descriptor is obtained, the dossier directory is then replaced on
   disk by a symlink to a decoy directory outside the root, and publication is
   run against the held descriptor — assert every artifact lands in the original
   inode and the decoy stays empty; the same swap injected between two artifact
   publications via a patched `os.link` first call — assert the remaining
   artifacts still land in the original inode and nothing appears in the decoy.
   (`R-G6`; C1, TG1, AC1)

9. **Fault-injection publication tests.** Patch `os.write` to short-write and to
   raise, `os.fsync` to raise, `os.close` to raise, and `os.link` to raise
   `ENOSPC` and `EEXIST`. For each: assert no partial artifact exists at any
   final name, pre-existing artifacts are byte-identical, the exit code is `1`,
   the partial-adoption diagnostic names published and unpublished artifacts,
   no foreign file was unlinked, and a retry republishes only the missing
   artifacts. Add a permission-denied case on the dossier directory.
   (`R-G11`, `R-G12`; H1, TG2, AC1)

10. **Record-hardening tests.** One named diagnostic and one test per malformed
    class: malformed JSON; non-object root; duplicate key at top level and
    inside an artifact; boolean in an integer position; wrong exact type for
    string, list, and dict positions; unknown and missing top-level key; unknown,
    missing, and misspelled artifact; unknown per-artifact key; identity
    mismatch; placeholder in claim, evidence, and uncertainty; evidence below the
    applicable rule; `passed` review without a verdict; verdict outside
    `REVIEW_VERDICTS`; personal path; unsafe memory path; supplemental section or
    derived field on `index`; and one case per structural-injection class —
    embedded newline, backtick, pipe, leading list marker, heading line, table
    row, `- Label:` field line, and fence. (`R-G18` through `R-G23`; H4, TG3,
    AC2)

11. **Round-trip and summary tests.** Generator round trip: generate into a
    temporary root, then run `validate_dossier` and assert zero diagnostics for a
    well-formed record, covering request origin/redaction/mutability, plan and
    review linkage, route-strength and override pairing, Level 0 and Level 1
    ship authorization, and PR remote-action text. Summary tests: every reported
    section present; the `passed` floor distinguished from the `not-required`
    one-item rule at Levels 0, 1, and 2, including a Level 2 `not-required`
    artifact with one item reported compliant; partial adoption; duplicate task
    IDs; `--task` matching none and matching more than one, both exit `2`; a
    valid but `pending` dossier exiting `1` by default; an unreadable artifact
    reported not omitted; authority links with a missing target, a symlinked
    target, and a symlinked ancestor; both independence arms separately, with
    placeholder and with synthetic unequal identities; text and JSON carrying the
    same facts and the same exit code; and no routing manifest opened.
    (`R-S1` through `R-S14`, `R-G15` through `R-G21`; TG4, TG5, TG6, TG7, AC2,
    AC4, AC6)

12. **Author the synthetic records and fixtures.** Create both records under
    `records/`, using task IDs `SYNTH-010` and `SYNTH-011`, project slugs
    `synthetic-level0` and `synthetic-level1`, and session identities matching
    the fixed prefix `synthetic-fixture-`. Every artifact's claim states it is
    non-authoritative test data. Hand-write the two schema-v2 `receipt.md`
    fixtures with the eleven required receipt sections, and the two
    `current-state.md` memory fixtures. No Markdown link syntax and no personal
    path anywhere. (`R-E1`, `R-E4`; H2, H5, AC3)

13. **Generate, validate, and measure.** Dry run, then apply, into
    `evals/task-dossier-pilots/concise/projects/`. Record the exact output of:
    - `python3 scripts/validate_task_dossiers.py evals/task-dossier-pilots/concise/projects`
    - the same with `--require-complete`
    - `python3 scripts/validate_handoff_receipts.py evals/task-dossier-pilots/concise/projects`
    - `python3 scripts/summarize_task_dossier.py evals/task-dossier-pilots/concise/projects`
    - the explicit eleven-path `wc -l` per sample, listing every artifact name
    Confirm 11/11 artifacts per sample, a passing complete gate, valid fixture
    receipts, and totals at or below 447 lines for Level 0 and 501 for Level 1.
    (`R-E3`, `R-E4`; H2, H5, AC2, AC3, AC6)

14. **Measure authoring burden.** For each record: `wc -lc`, and a counted total
    of non-null scalar values plus list items. Compute record-plus-output lines.
    Record all four metrics. Do not estimate timing, tokens, or cost.
    (`R-E5`; M1, TG9, AC3, AC7)

15. **Write the durable evaluation.** Create
    `evals/task-dossier-pilots/concise/results.md`: measured lines against the
    639-line and 716-line baselines, artifact counts, evidence counts, the four
    authoring metrics with an explicit statement of which measures compactness
    and which approximates burden, what the generator derived, what it refused to
    derive, and residual risks. Carry the fixed declaration that the samples are
    synthetic and non-authoritative and prove contract validity only — never
    review quality, verdict authenticity, or session independence. Do not modify
    `evals/task-dossier-pilots/results.md`. (`R-E2`, `R-E5`; H2, AC7)

16. **Leaf-allowlist gate, inventory, and documentation.** Compute the task
    delta against the baseline and assert exact set equality with the 43
    authorized paths, of which 29 are the evaluation leaves. Add the five new
    source and wrapper entries to `config/repository-paths.json`, matching the
    existing dossier entries' categories and policies. Extend only the Tooling
    section of `docs/workflows/task-dossier.md`. Append the contract cases: every
    `ARTIFACT_OWNERS` value is in `OWNERS`; both review artifacts map to
    `reviewer`; `ARTIFACT_TITLES` and `ARTIFACT_EXTRA_SECTIONS` cover the right
    artifact sets; `EXTRA_SECTION_FIELDS is ARTIFACT_EXTRA_SECTIONS`; the
    manifest inventories the five new files; both sample records use the
    synthetic prefix; and `results.md` carries the non-authoritative declaration.
    (`R-E2`, `R-E3`; H5, AC5)

17. **Full verification.** Run every command in the verification table,
    including the explicit Python 3.10 run and the baseline digest comparison.
    (`R-X8`, `R-X11`; H6, TG8, AC5, AC6)

18. **Record the rollback procedure.** Produce the exact reverse patch for the
    seven modified tracked files and the exact deletion list for the 36 new
    paths, both derived from the baseline. Do not execute it unless a stop
    condition fires. (`R-X12`; H6)

19. **Hand off for review.** Report the task delta against the baseline, focused
    and full test output, measured line and record metrics, and the rollback
    procedure. Do not commit, push, open a pull request, or write
    `plan-review.md` or `code-review.md`. (AC8)

## Verification

Focused, after steps 8 through 11:

| Command | Expectation |
| --- | --- |
| `python3 -m unittest tests.unit.test_task_dossier_generator -v` | all pass |
| `python3 -m unittest tests.unit.test_task_dossier_summary -v` | all pass |
| `python3 -m unittest tests.unit.test_task_dossier_validator -v` | all pass, assertion count unchanged from step 1 |
| `python3 -m unittest tests.contract.test_task_dossier_contract -v` | all pass |
| `python3 -m unittest tests.integration.test_task_dossier_workflow -v` | all pass |
| `grep -n "os.replace\|os.rename" src/brichan/contracts/task_dossier/generate.py` | no match |
| `git diff -- src/brichan/contracts/task_dossier/scaffold.py src/brichan/contracts/task_dossier/parser.py` | empty |

Evaluation, after steps 13 and 14:

| Command | Expectation |
| --- | --- |
| `python3 scripts/validate_task_dossiers.py evals/task-dossier-pilots/concise/projects --require-complete` | exit `0`, two dossiers |
| `python3 scripts/validate_handoff_receipts.py evals/task-dossier-pilots/concise/projects` | exit `0`, two receipts |
| `python3 scripts/summarize_task_dossier.py evals/task-dossier-pilots/concise/projects` | exit `0`, both summaries complete |
| explicit eleven-path `wc -l` per sample | Level 0 at most 447, Level 1 at most 501 |
| `wc -lc` per record, plus the authored-value count | recorded, not compared to a threshold |

Full, at step 17:

| Command | Expectation |
| --- | --- |
| `make check` | exit `0` |
| `python3.10 -m unittest tests.unit.test_task_dossier_generator tests.unit.test_task_dossier_summary tests.unit.test_task_dossier_validator -v` | all pass on the 3.10 floor |
| `make dossiers` | exit `0`; the `projects` root is unaffected |
| `make receipts` | exit `0` |
| `make path-check` | exit `0` |
| digest comparison against the baseline for `config/model-routing.json`, `src/brichan/resources/**`, and every artifact of `TDW-006`, `TDW-007`, `TDW-008` | every digest identical |
| task delta against the baseline path list | exact set equality with the 43 authorized paths |

Explicitly not used: bare `git diff` or `git status --short` against `HEAD` as
evidence of preservation. The working tree carries pre-existing user changes, so
those comparisons cannot distinguish this task's delta from the user's.

## Stop conditions

Stop, write nothing further, and escalate when any becomes true:

- The coordinator baseline is missing, unreadable, or does not cover the files
  the verification table compares.
- Closing the descriptor-race guarantee appears to require modifying
  `scaffold.py` or `parser.py`, or a Linux-only syscall.
- Atomic publication appears to require `os.rename`, `os.replace`, deleting an
  existing file, or accepting a partial artifact at a final name.
- Meeting the 30% reduction appears to require dropping an artifact, dropping an
  evidence item, or lowering a level floor.
- A sample appears to need a real reviewer session, or a synthetic verdict would
  have to be presented as real review evidence.
- A test can only pass by changing an existing validator diagnostic, message, or
  exit code.
- Any dependency outside the standard library, or any construct requiring Python
  newer than 3.10.
- Any change to `config/model-routing.json`, `src/brichan/resources/`, or
  installed `.brichan` state appears necessary.
- The observed task delta cannot be made to equal the 43 authorized paths.

## Rollback

Derived from the baseline, never from `HEAD`.

1. For each of the 7 modified tracked files, apply the reverse of this task's
   hunks only. Whole-file `git checkout --` is forbidden: it reverts to `HEAD`
   and would discard the user's pre-existing changes.
2. Delete the 36 new paths, each verified against the baseline as absent
   pre-task. Delete nothing whose digest shows concurrent modification.
3. Abort the rollback and escalate if any target changed concurrently, rather
   than forcing it.

No data migration occurs, no existing dossier is read or rewritten, no packaged
resource is touched, nothing is committed, and no remote state changes. Partial
rollback is safe: the new modules are unreferenced by any existing entry point,
so removing them alone cannot break `make check`.

## Execution state

Steps 1 through 19 are unexecuted. This session was scoped to five version-1
snapshots and the five planner-owned artifacts, so no module, test, wrapper,
sample, fixture, or manifest entry was created, and no acceptance criterion that
depends on execution is claimed as met. `TDW-009-AC1` through `AC7` are
discharged at execution time on the `implement` route; `TDW-009-AC8` is
discharged by fresh independent review sessions.

## Claim or decision

Plan `TDW-009-P2` is accepted at version 2; `index.md` must echo that ID and
version, and any review must name them. The plan authorizes exactly 43 paths —
7 modified tracked files and 36 new files, of which 29 are enumerated evaluation
leaves — forbids ten path groups by name including `scaffold.py`, orders 19
steps so every review finding and every test-gap class is discharged by a named
command, and replaces every `HEAD`-relative preservation check with a comparison
against a coordinator-owned pre-task baseline. It is accepted, not executed.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan-review.md:178-217`
  supplies the two findings that reshaped this plan's bookkeeping: `H5` requires
  every evaluation leaf enumerated rather than a directory, and `H6` shows that
  `git diff` and `git status` against `HEAD` cannot prove preservation in a
  working tree that already carries user changes.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan-review.md:252-278`
  lists the nine test-gap classes; steps 8 through 11, 14, and 17 name a command
  for each, and `requirements.md` carries the `TG1` through `TG9` traceability
  rows that map them.
- `src/brichan/contracts/receipts/validation.py:15-70,1123-1125` fixes the
  eleven required receipt sections and shows `discover_receipts` globbing
  `*/handoffs/*/receipt.md`, which is why step 13 can validate both fixture
  receipts by pointing the existing receipt validator at the isolated root.
- `src/brichan/contracts/task_dossier/validation.py:1109-1116,1160-1195` shows
  `discover_dossiers` globbing only the root it is given — so the isolated
  evaluation root cannot join `make dossiers` — and shows that partial-adoption
  and duplicate-ID diagnostics exist only in `validate_projects`, which step 6
  therefore uses for the root verdict.
- `src/brichan/contracts/task_dossier/validation.py:28-34,71-78` fixes the two
  exact hunks step 1 authorizes: `ARTIFACTS` on line 30 of the schema import
  block, and the six-key `EXTRA_SECTION_FIELDS` literal at lines 71-78.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:83-91`
  requires version 1 preserved under `versions/v1/` before supersession and
  limits the planner to those snapshots plus the five standard artifacts; the
  five snapshots were written and digest-verified before any version 2 content
  was authored.
- Python 3.10.11 is present on this machine, so the 3.10 floor run in the
  verification table is an executable check rather than an aspiration.

## Uncertainty

- Step 8's second race case patches `os.link` to perform the directory swap on
  its first call. This is a test seam over a standard-library function, not a
  production hook; if the implementer finds it cannot be done without adding a
  hook to `generate.py`, the stop condition on scaffold and production hooks
  applies and the case is escalated rather than weakened.
- The permission-denied case in step 9 may be unrunnable as root in some CI
  environments. If so, it must be skipped with a recorded reason, not silently
  passed.
- The 447-line and 501-line targets are budgets, not predictions of the samples'
  real content. Exceeding one triggers the stop condition: tighten record prose
  and re-measure, never drop an artifact.
- The orphan-temporary case is recorded but unswept: a crash between temporary
  creation and publication leaves a recognisable `.tdgen.*.tmp` file that no step
  in this plan removes. Adding a sweeper would mean deleting files the generator
  did not verify it created, which the design refuses.
