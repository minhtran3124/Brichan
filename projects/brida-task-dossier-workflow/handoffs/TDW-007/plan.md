# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `TDW-007`
- Task level: `1`
- Artifact: `plan`
- Artifact version: `1`
- Origin: `packet:projects/brida-task-dossier-workflow/handoffs/TDW-007/task-packet.md@TDW-007-P1-v1`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `8aa41de8-a3f3-48ce-8d47-9aed67a452c6`
- Effective route: `plan`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `TDW-007-P1`
- Plan status: `accepted`

## Claim or decision

Plan `TDW-007-P1` is accepted at version 1; the artifact version above is the
plan version that `index.md` must echo. The plan is accepted, not executed: this
planning session was directed to write only the five planner artifacts, so no
module, test, or fixture directory was created.

## Steps

1. Create `evals/task-dossier-pilots/normal/normalize_project_slug.py` exactly as
   specified in `design.md`. Route: `implement`.
2. Create `evals/task-dossier-pilots/normal/test_normalize_project_slug.py` with
   the seven cases in the design test table, including the ASCII-only boundary
   and the `PROJECT_SLUG_PATTERN` conformance assertion.
3. Run
   `python3 -m unittest discover -s evals/task-dossier-pilots/normal -t evals/task-dossier-pilots/normal -v`
   and record the observed pass count. If discovery cannot import the sibling
   module, fall back to `python3 -m unittest` against the test module path and
   record which form was used.
4. Report changed paths from `git status --short`; the list must contain only the
   two fixture files and the five planner artifacts.
5. Run `python3 scripts/validate_task_dossiers.py projects` and record the
   remaining diagnostics.
6. Coordinator writes `index.md`, `request.md`,
   `client-follow-up-questions.md`, and `receipt.md`; a fresh routine `review`
   session writes `plan-review.md` and `code-review.md`. Out of scope for the
   planning session.

## Execution state

- Steps 1–5 are unexecuted. `TDW-007-AC3` and `TDW-007-AC4` are therefore
  discharged at execution time on the `implement` route; no test result is
  claimed here.
- `TDW-007-AC1` and `TDW-007-AC2` are satisfied by the five planner artifacts as
  written.

## Rollback

Delete `evals/task-dossier-pilots/normal/`. Both files are new and untracked,
nothing under `src/`, `tests/`, `config/`, or the installed resources is touched,
and nothing is committed, so removing the directory restores the pre-task state.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-007/task-packet.md:8-10,21-25,29-34`
  fixes plan ID `TDW-007-P1`, version 1, level 1, the authorized write scope
  these steps stay inside, and the acceptance criteria they discharge.
- `src/brichan/contracts/task_dossier/validation.py:339-347` enforces the Level 1
  minimum of two concrete evidence items per passed artifact, which step 5
  checks against every artifact in this dossier.
- `src/brichan/contracts/task_dossier/validation.py:454-477` requires the plan
  author's session to differ from both the reviewing and the authoring session of
  each review artifact, which is why step 6 assigns the reviews to a fresh
  session rather than to session `8aa41de8-a3f3-48ce-8d47-9aed67a452c6`.

## Uncertainty

- The scope conflict is recorded rather than resolved silently: `task-packet.md:21-22`
  authorizes the implementer to write the fixture and its tests, while this
  session's direction restricted writing to the five planner artifacts. The
  narrower scope was followed, so the plan's step-level cost and test outcome
  remain unmeasured.
