# TDW-007 task packet

Brichan is the delegated project coordinator. This packet runs the Level 1
full-document workflow against a normal implementation requirement.

## Accepted plan

- Plan ID: `TDW-007-P1`
- Version: `1`
- Level: `1`

## Requirement

Under `evals/task-dossier-pilots/normal/`, implement a dependency-free
`normalize_project_slug(value)` utility and unit tests. It trims and lowercases
input, converts each run of non-alphanumeric characters to one hyphen, strips
edge hyphens, and raises `ValueError` when no alphanumeric content remains.

## Scope and ownership

- Write the implementation fixture, its tests, and these dossier artifacts:
  `requirements.md`, `brief.md`, `options.md`, `design.md`, and `plan.md`.
- Do not write coordinator-owned or reviewer-owned dossier artifacts, project
  memory, routing config, installed resources, or files outside the fixture.
- Do not commit, publish, deploy, or perform remote actions.

## Acceptance

- All five planning artifacts contain at least two concrete evidence items and
  complete model/session/route provenance.
- `plan.md` records accepted `TDW-007-P1` version 1.
- Tests cover normal input, repeated separators, edge separators, digits, and
  empty-normalized input.
- Focused tests pass and the worker reports changed paths.
