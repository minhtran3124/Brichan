# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `TDW-008`
- Task level: `2`
- Artifact: `plan`
- Artifact version: `1`
- Origin: `packet:projects/brida-task-dossier-workflow/handoffs/TDW-008/task-packet.md@TDW-008-P1-v1`
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

- Plan ID: `TDW-008-P1`
- Plan status: `accepted`

## Claim or decision

Plan `TDW-008-P1` is accepted at version 1; the artifact version above is the
plan version that `index.md` must echo. Accepted means the steps are settled and
immutable, not executed: this planning session was directed to write only the
five planner artifacts, so no fixture, test, or directory was created and no test
result is reported.

## Steps

1. Create `evals/task-dossier-pilots/high-risk/release_policy.py` exactly as
   specified in `design.md`, including the fail-closed `_is_disabled` helper and
   the four fixed violation codes. Route: `implement`.
2. Create `evals/task-dossier-pilots/high-risk/test_release_policy.py` with the
   ten cases in the design test table, including the fail-closed value case, the
   all-violations ordering case, the determinism case, and the read-only case.
3. Run
   `python3 -m unittest discover -s evals/task-dossier-pilots/high-risk -t evals/task-dossier-pilots/high-risk -v`
   and record the observed pass count and the command that produced it.
4. Confirm no external side effect: `git status --short` lists only the two
   fixture files and the five planner artifacts, and no file outside
   `evals/task-dossier-pilots/high-risk/` is created, modified, or deleted.
5. Run `python3 scripts/validate_task_dossiers.py projects` and record the
   remaining diagnostics.
6. Coordinator writes `index.md` with `Review route strength: stronger` and a
   documented one-off override, `Ship authorization: not-requested`, plus
   `request.md`, `client-follow-up-questions.md`, and `receipt.md`. A fresh
   stronger review session writes `plan-review.md` and `code-review.md`. All of
   step 6 is outside the planning session's write scope.

## Authorization gates

- No step in this plan requires a secret, a credential, a network call, a
  broadened permission, or any remote action, and none may be added to it; a step
  that would need one is a stop condition, not a new step.
- Ship authorization stays `not-requested`. Level 2 is the only level that may
  record `user-authorized`, and doing so would require recorded evidence of the
  user's decision, which this session neither has nor claims.
- The stronger reviewer override at step 6 is a documented one-off routing
  decision recorded in `index.md` by the coordinator; it changes no named route
  in `config/model-routing.json`.

## Execution state

- Steps 1–5 are unexecuted. `TDW-008-AC4` and `TDW-008-AC5` are therefore
  discharged at execution time on the `implement` route.
- `TDW-008-AC1`, `TDW-008-AC2`, and `TDW-008-AC3` are satisfied by the five
  planner artifacts as written, with the threat model, authorization boundary,
  stop conditions, and rollback recorded in `design.md`.

## Rollback

Delete `evals/task-dossier-pilots/high-risk/`. Both files are new and untracked;
no commit exists to revert, no remote state changes, and no installed resource,
routing key, or project memory entry is touched, so the directory removal is the
complete rollback.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-008/task-packet.md:9-11,24-30,34-39`
  fixes plan ID `TDW-008-P1`, version 1, level 2, the authorized write scope these
  steps stay inside, and the five acceptance criteria they discharge.
- `src/brichan/contracts/task_dossier/validation.py:339-347` enforces the Level 2
  minimum of three concrete evidence items per passed artifact, and
  `src/brichan/contracts/task_dossier/validation.py:680-686` requires the
  documented stronger reviewer that step 6 assigns.
- `src/brichan/contracts/task_dossier/validation.py:454-477` forbids the plan
  author's session from being either the reviewing or the authoring session of a
  review artifact, which is why step 6 routes both reviews to a fresh session
  rather than to session `8aa41de8-a3f3-48ce-8d47-9aed67a452c6`.
- `docs/workflows/task-dossier.md:146-153` requires Level 2 to record the stronger
  one-off override in `index.md` and to record ship authorization explicitly,
  which is what the authorization gates above hold to `not-requested`.

## Uncertainty

- The scope conflict is recorded rather than resolved silently:
  `task-packet.md:24-27` authorizes the implementer to write the fixture and its
  tests, while this session's direction restricted writing to the five planner
  artifacts. The narrower scope was followed, so no guard has yet been executed
  and no test outcome is claimed.
- Whether the stronger reviewer's findings differ materially from a routine
  reviewer's remains open until step 6 completes and the three pilot reviews can
  be compared.
