# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `TDW-007`
- Task level: `1`
- Artifact: `requirements`
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

## Claim or decision

TDW-007 requires a dependency-free `normalize_project_slug(value)` whose return
value always satisfies the slug grammar the repository already enforces at
`src/brichan/contracts/task_dossier/schema.py:181`, and which raises `ValueError`
rather than returning an empty string when no alphanumeric content survives
normalization. Level 1 is the correct level: the work spans an implementation
module plus a test module, decomposes into five named test cases, and admits more
than one credible normalization semantics.

## Functional requirements

- `TDW-007-R1`: the function trims leading and trailing whitespace, then
  lowercases the input.
- `TDW-007-R2`: each maximal run of non-alphanumeric characters collapses to
  exactly one `-`.
- `TDW-007-R3`: leading and trailing hyphens are stripped from the result.
- `TDW-007-R4`: `ValueError` is raised when no alphanumeric content remains; the
  function never returns an empty string.
- `TDW-007-R5`: the module imports only the Python standard library and performs
  no I/O, network, or filesystem access.
- `TDW-007-R6`: every returned slug matches `^[a-z0-9]+(?:-[a-z0-9]+)*$`, the
  existing `PROJECT_SLUG_PATTERN`.

## Acceptance criteria

- `TDW-007-AC1`: all five planning artifacts contain at least two concrete
  evidence items and complete model, session, and route provenance
  (`task-packet.md:29-30`).
- `TDW-007-AC2`: `plan.md` records accepted `TDW-007-P1` version 1
  (`task-packet.md:31`).
- `TDW-007-AC3`: tests cover normal input, repeated separators, edge separators,
  digits, and empty-normalized input (`task-packet.md:32-33`).
- `TDW-007-AC4`: focused tests pass and the worker reports changed paths
  (`task-packet.md:34`).

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-007/task-packet.md:8-10,14-17,29-34`
  supplies the plan identity, the normalization rules transcribed as R1–R4, and
  the four acceptance criteria above.
- `src/brichan/contracts/task_dossier/schema.py:181` defines
  `PROJECT_SLUG_PATTERN` as `^[a-z0-9]+(?:-[a-z0-9]+)*$`; `TDW-007-R6` binds the
  output to that existing grammar instead of inventing a target shape.
- `docs/workflows/task-dossier.md:122-124` lists the raise-to-Level-1 triggers.
  This task meets "multiple credible options exist" and "acceptance criteria
  require decomposition", and meets none of the Level 2 triggers at
  `docs/workflows/task-dossier.md:126-128`.

## Uncertainty

- The packet does not say whether non-ASCII alphanumerics such as `é` count as
  alphanumeric. `options.md` resolves this as an explicit ASCII-only decision
  forced by `TDW-007-R6`; it is recorded here because that requirement is
  derived rather than transcribed from the packet.
