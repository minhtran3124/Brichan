# TDW-006 task packet

Brichan is the delegated project coordinator. This packet runs the Level 0
full-document workflow against a deliberately simple requirement.

## Accepted plan

- Plan ID: `TDW-006-P1`
- Version: `1`
- Level: `0`

## Requirement

Create `evals/task-dossier-pilots/simple/greeting.txt` with the exact UTF-8
content `Brichan task dossier pilot: simple` followed by one newline.

## Scope and ownership

- Write the implementation fixture and these dossier artifacts:
  `requirements.md`, `brief.md`, `options.md`, `design.md`, and `plan.md`.
- Do not write `index.md`, `request.md`,
  `client-follow-up-questions.md`, `plan-review.md`, `code-review.md`,
  `pr-desc.md`, `receipt.md`, project memory, routing config, or installed
  resources.
- Do not commit, publish, deploy, or perform remote actions.

## Acceptance

- All five planning artifacts contain real Level 0 evidence and provenance.
- `plan.md` records accepted `TDW-006-P1` version 1.
- The fixture is byte-exact and checked locally.
- No file outside the authorized paths changes.
