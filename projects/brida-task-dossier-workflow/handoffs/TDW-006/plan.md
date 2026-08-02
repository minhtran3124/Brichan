# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `TDW-006`
- Task level: `0`
- Artifact: `plan`
- Artifact version: `1`
- Origin: `packet:projects/brida-task-dossier-workflow/handoffs/TDW-006/task-packet.md@TDW-006-P1-v1`
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

- Plan ID: `TDW-006-P1`
- Plan status: `accepted`

## Claim or decision

Plan `TDW-006-P1` is accepted at version 1. The artifact version above is the
plan version, exactly as `task-packet.md:8-9` specifies and as
`src/brichan/contracts/task_dossier/validation.py:539-542,585-591` reads it when
the coordinator links the accepted plan from `index.md`. Accepted here means the
steps below are settled and immutable, not that they have been executed: this
planning session was directed to plan only and wrote no fixture.

## Steps

1. Create `evals/task-dossier-pilots/simple/greeting.txt` with
   `Brichan task dossier pilot: simple` and one trailing newline. Route:
   `implement`.
2. Verify `wc -c` prints `35` and `od -c` shows exactly one trailing `\n`.
3. Verify `git status --short` lists only the fixture and the five planner
   artifacts.
4. Run `python3 scripts/validate_task_dossiers.py projects` and record the
   diagnostics that remain.
5. Coordinator writes `index.md`, `request.md`,
   `client-follow-up-questions.md`, and `receipt.md`; a fresh routine `review`
   session writes `plan-review.md` and `code-review.md`. Out of scope for the
   planning session.

## Execution state

- Steps 1–4 are not executed by this session. `TDW-006-AC3` and `TDW-006-AC4`
  are therefore satisfied at execution time on the `implement` route, not by
  this artifact.
- `TDW-006-AC1` and `TDW-006-AC2` are satisfied by the five planner artifacts as
  written.

## Rollback

Delete `evals/task-dossier-pilots/simple/greeting.txt`. Nothing else is created,
nothing is committed, and no remote or installed state is touched, so removal of
one untracked file restores the pre-task state exactly.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-006/task-packet.md:8-10,29-32`
  fixes plan ID `TDW-006-P1`, version 1, level 0, and the acceptance criteria
  these steps discharge.
- `src/brichan/contracts/task_dossier/validation.py:329-355` shows that a
  `passed` artifact is checked for a concrete claim, level-minimum evidence, and
  a concrete uncertainty statement, which is what step 4 will confirm.

## Uncertainty

- The accepted plan is unexecuted, so its step-level cost is unmeasured; the
  scope conflict is recorded rather than resolved silently. The packet at
  `task-packet.md:19-20` authorizes the implementer to write the fixture, while
  this session's direction restricted writing to the five planner artifacts. The
  narrower scope was followed.
