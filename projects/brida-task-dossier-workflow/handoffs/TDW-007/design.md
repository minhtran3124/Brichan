# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `TDW-007`
- Task level: `1`
- Artifact: `design`
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

Two files under `evals/task-dossier-pilots/normal/` implement and prove the
normalizer: a module holding one public function with a module-level compiled
pattern, and a `unittest` module beside it. The fixture is not importable from
`brichan` and is not discovered by any existing test layer, so a pilot fixture
can never become an accidental dependency of the shipped package.

## Structure

- `evals/task-dossier-pilots/normal/normalize_project_slug.py`
  - `_SEPARATOR_RUN = re.compile(r"[^a-z0-9]+")` at module level, compiled once.
  - `normalize_project_slug(value: str) -> str`:
    1. `text = value.strip().lower()`
    2. `slug = _SEPARATOR_RUN.sub("-", text).strip("-")`
    3. `if not slug: raise ValueError(...)`, quoting the offending input in the
       message so a caller can diagnose it.
    4. `return slug`
  - Standard library only; no I/O; no module-level side effect.
- `evals/task-dossier-pilots/normal/test_normalize_project_slug.py`
  - `unittest.TestCase` importing the module as a sibling, run with
    `python3 -m unittest discover -s evals/task-dossier-pilots/normal -t evals/task-dossier-pilots/normal`.

## Test design

| Case | Input | Expectation | Covers |
|---|---|---|---|
| normal input | `"  Brida Task  Dossier "` | `brida-task-dossier` | R1, R2 |
| repeated separators | `"a___b---c"` | `a-b-c` | R2 |
| edge separators | `"--alpha beta--"` | `alpha-beta` | R3 |
| digits | `"Project 42 v2"` | `project-42-v2` | R2, R6 |
| empty-normalized | `"!!!"`, `""`, `"   "` | `ValueError` | R4 |
| ASCII-only boundary | `"Café"` | `caf` | R6, options decision |
| grammar conformance | every returned slug | matches `PROJECT_SLUG_PATTERN` | R6 |

## Consequences

- Directory naming: `task-dossier-pilots` and `normal` contain a hyphen, so the
  fixture is not a valid package path. This is deliberate — it forces the
  `-s`/`-t` discovery form above and structurally prevents `import` from
  `src/brichan/`.
- No repository test layer changes. `Makefile:28-35` discovers only
  `tests/unit`, `tests/contract`, and `tests/integration`, so the pilot tests are
  run explicitly and never silently join `make check`.
- The `ValueError` message includes the raw input. Inputs here are literal test
  strings, and `docs/workflows/task-dossier.md:160-163` forbids personal or home
  paths in the dossier; no such value is quoted in any artifact.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-007/task-packet.md:14-17,32-33`
  fixes the four normalization behaviours and the five test cases that the table
  above maps one-to-one onto requirements.
- `src/brichan/contracts/task_dossier/schema.py:181` supplies the
  `PROJECT_SLUG_PATTERN` the grammar-conformance case asserts against, so that
  assertion checks an existing repository contract rather than a restated regex.
- `Makefile:28-35` confirms the three discovered test roots, which is why an
  `evals/` fixture cannot enter the default test run.

## Uncertainty

- Sibling-module import under `unittest discover` depends on the discovery start
  directory being on `sys.path`; the plan verifies this by running the command
  rather than assuming it, and falls back to `python3 -m unittest` against the
  file path if discovery misbehaves.
