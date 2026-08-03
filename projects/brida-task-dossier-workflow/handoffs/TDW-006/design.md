# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `TDW-006`
- Task level: `0`
- Artifact: `design`
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

## Claim or decision

One new directory `evals/task-dossier-pilots/simple/` holds one new file
`greeting.txt` of exactly 35 bytes. There is no module, no import surface, and no
test file, because the artefact under test is a literal byte sequence and its
verification is a byte-count plus an octal dump, not an assertion in code.

## Structure

- `evals/task-dossier-pilots/simple/greeting.txt` — the only file created.
- Content: `Brichan task dossier pilot: simple` + `\n`. 34 content bytes, one
  newline byte, 35 total; UTF-8, no BOM, LF line ending, no trailing blank line.
- The `task-dossier-pilots` parent directory is created implicitly and will be
  shared by TDW-007 (`normal/`) and TDW-008 (`high-risk/`); no shared file, no
  `__init__.py`, and no cross-pilot import is introduced.

## Verification design

- `wc -c` on the fixture must print `35`.
- `od -c` on the fixture must end in a single `\n` with no `\r` and no second
  newline.
- `git status --short` must list the fixture and the five planner artifacts and
  nothing else, which is how `TDW-006-AC4` becomes evidence instead of a claim.

## Consequences

- Because the fixture is inert data, no repository test layer changes:
  `Makefile:22-35` discovers tests under `tests/unit`, `tests/contract`, and
  `tests/integration`, none of which this touches.
- `make dossiers` (`Makefile:44-45`) remains the relevant gate for this task, and
  it is read-only.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-006/task-packet.md:14-15`
  fixes the path and the byte content that this structure implements.
- `Makefile:22-35,44-45` shows the test layers this design deliberately leaves
  untouched and the read-only dossier gate it must satisfy.

## Uncertainty

- No unresolved design uncertainty remains: a 35-byte inert fixture has no
  interface, no dependency, and no runtime behaviour to leave open.
