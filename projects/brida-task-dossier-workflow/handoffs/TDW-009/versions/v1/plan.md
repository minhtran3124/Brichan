# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `plan`
- Artifact version: `1`
- Origin: `packet:projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md@TDW-009-P1-v1`
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

- Plan ID: `TDW-009-P1`
- Plan status: `accepted`

## Authorized implementation paths

The implementation worker may create or modify exactly these paths and no
others. Route: `implement`.

| # | Path | Action |
| --- | --- | --- |
| 1 | `src/brichan/contracts/task_dossier/schema.py` | modify — add four constants only |
| 2 | `src/brichan/contracts/task_dossier/scaffold.py` | modify — rename `_create_exclusively` to `create_exclusively` and update its one call site |
| 3 | `src/brichan/contracts/task_dossier/record.py` | create |
| 4 | `src/brichan/contracts/task_dossier/generate.py` | create |
| 5 | `src/brichan/contracts/task_dossier/summary.py` | create |
| 6 | `src/brichan/contracts/task_dossier/__init__.py` | modify — re-export new public names |
| 7 | `src/brichan/contracts/task_dossier/validation.py` | modify — one line: `EXTRA_SECTION_FIELDS = ARTIFACT_EXTRA_SECTIONS` |
| 8 | `scripts/generate_task_dossier.py` | create |
| 9 | `scripts/summarize_task_dossier.py` | create |
| 10 | `tests/unit/test_task_dossier_generator.py` | create |
| 11 | `tests/unit/test_task_dossier_summary.py` | create |
| 12 | `tests/contract/test_task_dossier_contract.py` | modify — append cases for the new constants and manifest entries |
| 13 | `tests/integration/test_task_dossier_workflow.py` | modify — append wrapper integration cases |
| 14 | `config/repository-paths.json` | modify — inventory paths 3, 4, 5, 8, 9 |
| 15 | `docs/workflows/task-dossier.md` | modify — extend the Tooling section only |
| 16 | `evals/task-dossier-pilots/concise/` | create — records, generated samples, and `results.md` |

## Paths that must remain untouched

| Path | Reason |
| --- | --- |
| `config/model-routing.json` | Routing neutrality; the user's existing diff must survive byte-identical |
| `src/brichan/resources/dogfood_v1/**` | Installed resources are out of scope |
| `src/brichan/contracts/task_dossier/parser.py` | `R-X3`; the generator consumes it unchanged |
| `docs/workflows/task-dossier/templates/**` | Templates back the scaffold and the contract tests |
| `docs/policy/**`, `PRODUCT.md`, `AGENTS.md`, `CLAUDE.md` | Policy is not changed by an implementation task |
| `projects/**` | Dossier and memory writes belong to the coordinator, planner, and reviewers |
| `evals/task-dossier-pilots/results.md` and the `simple`, `normal`, `high-risk` directories | Recorded pilot evidence stays immutable |
| `metrics/**`, `bin/**`, `Makefile`, `pyproject.toml`, `CHANGELOG.md`, `VERSION` | No new gate, no packaging change, no release surface |
| `.brichan` state anywhere on disk | Checkout-only capability |

## Ordered steps

Each step names the requirement it discharges and the check that proves it.

1. **Add the four constants.** Extend `schema.py` with `RECORD_SCHEMA_VERSION`,
   `ARTIFACT_TITLES`, `ARTIFACT_OWNERS`, and `ARTIFACT_EXTRA_SECTIONS`, add them
   to `__all__`, then replace the literal at `validation.py:71-78` with
   `EXTRA_SECTION_FIELDS = ARTIFACT_EXTRA_SECTIONS`. Run
   `python3 -m unittest discover -s tests/unit -t . -v` and confirm the existing
   validator suite still passes with no changed assertion. (`R-X1`, `AC5`)

2. **Write `record.py`.** Dataclasses `ArtifactRecord` and `TaskRecord`, and
   `load_record(path, *, task_id, level, project)` returning
   `(TaskRecord | None, list[Diagnostic])`. Implement every row of the
   record-diagnostics table in `design.md`, mirroring `validation.py:276-355`
   for the evidence floor and using `parser.is_placeholder` for concreteness.
   No import of `validation.py`. (`R-G6`, `R-G8` through `R-G12`, `R-G15`)

3. **Write `generate.py`.** Implement `render_artifact`, `plan_generation`, and
   `apply_generation` exactly as the rendering section of `design.md` specifies:
   fixed block order, sixteen metadata fields in `METADATA_FIELDS` order, index
   identity and status table for `index` only, supplemental sections refused for
   `index`, one trailing newline. Reuse `dossier_path` and the promoted
   `create_exclusively` from `scaffold.py`; perform the symlink guard before any
   write and the abort after a collision. Add `main()` with the CLI in
   `design.md` and the three exit codes. (`R-G1` through `R-G5`, `R-G7`,
   `R-G13`, `R-G14`)

4. **Write `summary.py`.** Implement `DossierSummary`, `summarize_dossier`,
   `render_text`, `render_json`, and `main()`. Compute artifact state, evidence
   counts against `MINIMUM_EVIDENCE_ITEMS`, per-artifact provenance, plan and
   review identity, authority-link health, and review independence. Obtain the
   verdict by calling `validate_dossier`; do not re-derive it. Sort every
   collection before rendering. (`R-S1` through `R-S12`)

5. **Write the two wrappers.** `scripts/generate_task_dossier.py` and
   `scripts/summarize_task_dossier.py`, byte-for-byte the same shape as
   `scripts/validate_task_dossiers.py:1-19` apart from the docstring and the
   imported `main`. (`R-X8`)

6. **Unit-test the generator.** `tests/unit/test_task_dossier_generator.py`
   must cover at minimum: dry run writes nothing; apply writes eleven files;
   an existing artifact is reported `preserve` and its bytes are unchanged; a
   symlinked artifact aborts; a dangling symlink aborts; a symlinked dossier
   directory aborts; a task ID or project that would escape the projects root is
   refused; record identity mismatching the CLI is refused; malformed JSON,
   unknown top-level key, unknown artifact, missing artifact, and unknown
   per-artifact key each produce a named diagnostic; a placeholder claim,
   evidence item, or uncertainty item is refused; evidence below the level floor
   is refused; a `passed` review with no verdict is refused; a personal path in
   any value is refused; a supplemental section on `index` is refused; and two
   renders of one record are byte-identical, including under a different
   `PYTHONHASHSEED`. (`AC1`, `AC2`)

7. **Unit-test the summary.** `tests/unit/test_task_dossier_summary.py` must
   cover: every reported section is present for a valid dossier; evidence counts
   and the below-floor list are correct at each of levels 0, 1, and 2; provenance
   is read from artifacts and no routing manifest is opened; a status-table row
   disagreeing with its artifact is reported and exits `1`; a missing receipt
   target and a missing memory target are each reported and exit `1`; a review
   sharing the plan's authoring session reports `not-independent`; a placeholder
   session reports `unknown`; a `passed` review with `CHANGES REQUIRED` exits `1`
   under `--require-complete`; a missing projects root and an unknown `--task`
   exit `2`; and text and JSON output carry the same facts and the same exit
   code. (`AC4`)

8. **Author the two sample records.** Create
   `evals/task-dossier-pilots/concise/TDW-010.record.json` for a Level 0 sample
   and `evals/task-dossier-pilots/concise/TDW-011.record.json` for a Level 1
   sample, each with real claims, evidence, and uncertainty describing the
   sample itself. Records must contain no Markdown link syntax and no personal
   path. (`AC3`)

9. **Generate, validate, and measure the samples.** Generate into the isolated
   root `evals/task-dossier-pilots/concise/projects/`, dry run first, then apply.
   Then run, and record the exact output of, each of:
   - `python3 scripts/validate_task_dossiers.py evals/task-dossier-pilots/concise/projects`
   - the same command with `--require-complete`
   - `wc -l` over the eleven artifacts of each sample
   - `python3 scripts/summarize_task_dossier.py evals/task-dossier-pilots/concise/projects`
   Confirm 11/11 artifacts, a passing complete gate, and totals at or below 447
   lines for Level 0 and 501 for Level 1. Note that each sample needs a
   hand-written `receipt.md` in its dossier directory for the receipt link to
   resolve; the receipt stays coordinator-shaped and is not generated. (`AC2`,
   `AC3`, `AC4`)

10. **Write the durable evaluation.** Create
    `evals/task-dossier-pilots/concise/results.md` comparing both samples with
    the 639-line and 716-line pilot baselines: measured lines, artifact count,
    evidence counts, what the generator derived, what it refused to derive, and
    residual risks. Record `null` for timing, tokens, and cost; do not estimate
    them. Do not modify `evals/task-dossier-pilots/results.md`. (`AC7`)

11. **Extend the contract and integration tests.** Append to
    `tests/contract/test_task_dossier_contract.py`: every `ARTIFACT_OWNERS`
    value is in `OWNERS`; both review artifacts map to `reviewer`;
    `ARTIFACT_TITLES` and `ARTIFACT_EXTRA_SECTIONS` cover the right artifact
    sets; `EXTRA_SECTION_FIELDS` is `ARTIFACT_EXTRA_SECTIONS`; the manifest
    inventories the five new files; and `config/model-routing.json` is unchanged.
    Append to `tests/integration/test_task_dossier_workflow.py` a wrapper run of
    each new script asserting the documented exit codes. (`AC5`, `AC6`)

12. **Inventory and document.** Add the five new file entries to
    `config/repository-paths.json` — the three modules as `importable-api` or
    `importable-core`, the two wrappers as `automation-entrypoint` with policy
    `stable-wrapper`, matching the existing dossier entries. Extend only the
    Tooling section of `docs/workflows/task-dossier.md` with the two new
    commands and one sentence each on what generation derives and what the
    summary reports. (`AC5`, `AC6`)

13. **Full verification.** Run and record the exact result of each command in
    the verification table below. (`AC6`)

14. **Hand off for review.** Report changed paths from `git status --short`, the
    focused and full test output, and the measured line counts. Do not commit,
    do not push, do not open a pull request, and do not write `plan-review.md`
    or `code-review.md`. (`AC8`, discharged by fresh independent sessions
    outside this worker's scope)

## Verification

Focused, run after steps 6, 7, and 11:

| Command | Expectation |
| --- | --- |
| `python3 -m unittest tests.unit.test_task_dossier_generator -v` | all pass |
| `python3 -m unittest tests.unit.test_task_dossier_summary -v` | all pass |
| `python3 -m unittest tests.unit.test_task_dossier_validator -v` | all pass, unchanged count |
| `python3 -m unittest tests.contract.test_task_dossier_contract -v` | all pass |
| `python3 -m unittest tests.integration.test_task_dossier_workflow -v` | all pass |
| `python3 scripts/validate_task_dossiers.py evals/task-dossier-pilots/concise/projects --require-complete` | exit `0`, two dossiers |
| `python3 scripts/summarize_task_dossier.py evals/task-dossier-pilots/concise/projects` | exit `0`, both summaries complete |
| `wc -l` over each sample's eleven artifacts | Level 0 at most 447, Level 1 at most 501 |

Full, run at step 13:

| Command | Expectation |
| --- | --- |
| `make check` | exit `0` |
| `make dossiers` | exit `0`, existing `projects` dossiers unaffected |
| `make receipts` | exit `0` |
| `make path-check` | exit `0` |
| `git status --short` | only the sixteen authorized paths appear |
| `git diff -- config/model-routing.json` | empty against the pre-task working tree |
| `git diff -- src/brichan/resources` | empty |
| `git diff -- projects/brida-task-dossier-workflow/handoffs/TDW-006 TDW-007 TDW-008` | empty |

## Stop conditions

Stop, write nothing further, and escalate to the coordinator when any of these
becomes true:

- Meeting the 30% reduction appears to require dropping an artifact, dropping an
  evidence item, or lowering a level floor. Report the measured numbers instead.
- A test can only pass by changing an existing validator diagnostic, message, or
  exit code.
- The design appears to require overwriting an existing artifact, deleting a
  file, following a symlink, or writing outside the selected projects root.
- Any dependency outside the standard library, or any construct that requires
  Python newer than 3.10, appears necessary.
- Any change to `config/model-routing.json`, to `src/brichan/resources/`, or to
  installed `.brichan` state appears necessary.
- The summary would need to read receipt or project-memory content rather than
  link health.
- Focused verification passes but `make check` fails for a reason outside the
  sixteen authorized paths.

## Rollback

Every change is either a new file or a bounded edit to a tracked file, and
nothing is committed. Rollback is:

1. `git checkout --` the seven modified tracked files in the authorized table.
2. Delete the nine new files and `evals/task-dossier-pilots/concise/`.

No data migration occurs, no existing dossier is read or rewritten, no packaged
resource is touched, and no remote state changes, so this restores the pre-task
tree exactly. Partial rollback is also safe: the new modules are unreferenced by
any existing entry point, so removing them alone cannot break `make check`.

## Execution state

Steps 1 through 14 are unexecuted. This session was scoped to the five planner
artifacts, so no module, test, wrapper, sample, or manifest entry was created,
and no acceptance criterion that depends on execution is claimed as met.
`TDW-009-AC1` through `AC7` are discharged at execution time on the `implement`
route; `TDW-009-AC8` is discharged by fresh independent review sessions.

## Claim or decision

Plan `TDW-009-P1` is accepted at version 1; `index.md` must echo that ID and
this artifact version. The plan authorizes exactly sixteen paths, forbids nine
path groups by name, orders fourteen steps so that every parent acceptance
criterion is discharged by a named command, and defines seven stop conditions
that halt the work rather than let it weaken the evidence contract. It is
accepted, not executed: this planning session wrote only the five planner
artifacts.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:47-57`
  restricts the planner to the five planner artifacts and states that the
  implementation worker may write only paths explicitly accepted in this plan,
  which is why the authorized and forbidden path tables are exhaustive and
  path-level rather than directory-level.
- `Makefile:44-45,67` shows `dossiers` running the validator against `projects`
  and `check` depending on it, which is why step 9 generates into an isolated
  root under `evals/` — `discover_dossiers` at `validation.py:1109-1116` globs
  only the root it is given, so the samples cannot join the repository gate.
- `src/brichan/contracts/task_dossier/scaffold.py:151-217` is the write
  behaviour step 3 reuses rather than reimplements, and is the basis for the
  rollback claim that nothing existing can be truncated: every write is an
  exclusive create, so rollback never has to restore overwritten content.
- `src/brichan/contracts/task_dossier/validation.py:946-998` defines the
  complete gate that step 9 runs against both samples, including the rule that a
  `passed` review with a `CHANGES REQUIRED` verdict is not a complete task,
  which is the case step 7 tests explicitly.
- `tests/unit/test_task_dossier_validator.py` holds 912 lines of existing
  validator coverage that step 1 must leave passing unchanged; that suite is the
  proof obligation for the value-identical `EXTRA_SECTION_FIELDS` substitution.
- `scripts/validate_task_dossiers.py:1-19` fixes the thin-wrapper shape step 5
  copies: `sys.path` bootstrap, import `main`, `raise SystemExit(main())`, and
  nothing else.

## Uncertainty

- Step 9 requires a hand-written `receipt.md` per sample so the canonical
  receipt link resolves, because `validation.py:817-824` requires the file to
  exist and the receipt is deliberately not generated. The sample receipts are
  authored by the implementer inside `evals/`; whether that is the right home
  for sample receipts long term is unresolved and is recorded rather than
  decided here.
- The 447-line and 501-line targets in the verification table are budgets, not
  predictions of the samples' real content. If a sample exceeds its budget the
  stop condition applies: tighten the record prose and re-measure, never drop an
  artifact.
- `check_repository_paths.py:119-176` resolves every Markdown link in tracked
  and untracked files, so a generated artifact containing link syntax would fail
  `make path-check`. Step 8 forbids link syntax in the records, but the
  generator does not enforce it; this is an accepted residual risk caught by the
  gate in step 13 rather than by a refusal.
- One scope tension is recorded rather than resolved: the parent packet reserves
  the routing manifest and installed resources absolutely, while step 12 must
  edit `config/repository-paths.json`. These are different files with different
  policies — the routing manifest is `canonical` model selection, the path
  manifest is the repository inventory that every new file is required to join —
  and the plan treats editing the latter as in scope and the former as a stop
  condition.
