# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `options`
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

## Decision A: structured-record and generation interface

Five options were considered. All keep the eleven artifacts; they differ in what
the operator authors and where generation lives.

### A1 — JSON record plus a new `generate` module and thin wrapper (selected)

One `*.record.json` file holds identity, per-artifact state, provenance, claim,
evidence, uncertainty, and any supplemental sections. A new
`src/brichan/contracts/task_dossier/generate.py` renders Markdown and exposes a
`main()`; `scripts/generate_task_dossier.py` is a thin bootstrap wrapper matching
the two existing ones.

- Strengths: `json` is standard library on the 3.10 floor; parse failures carry
  line and column; the record is trivially diffable and machine-checkable;
  generation stays out of the scaffold's single responsibility; the wrapper
  shape already exists twice in the repository.
- Costs: JSON has no comments and is awkward for multi-paragraph prose; the
  operator learns one new key vocabulary.
- Risk: a second file format to keep in step with `schema.py`. Mitigated by
  deriving the record's field vocabulary from `schema.py` constants rather than
  restating them, and by a contract test that ties record keys to
  `METADATA_FIELDS`.

### A2 — Markdown master record parsed by the existing `parser.py`

One `record.md` with a section per artifact, read back through
`parse_sections`, `parse_fields`, and `list_items`.

- Strengths: no new format for the operator; reuses parsing already audited.
- Costs: the record is itself Markdown that looks like a dossier artifact but is
  not one, so `discover_partial_dossiers` and the "partial adoption" diagnostic
  become ambiguous if it is ever placed inside a handoff directory. Errors
  degrade badly: a mistyped heading silently yields an empty section rather than
  a diagnostic, because `parse_sections` uses `setdefault` and returns `{}` for
  anything absent.
- Rejected: it trades precise refusals for familiarity, and `R-G10` and `R-G15`
  require precise refusals.

### A3 — Python API only, no file format

Export dataclasses and `generate_dossier(record, dossier)`; the operator writes
a short Python script.

- Strengths: smallest surface; no parsing code; maximal expressiveness.
- Costs: the durable artifact of a task becomes an ad-hoc script that nobody
  stores, so the record stops being reviewable evidence. It also puts arbitrary
  code between the operator and eleven files that must never be overwritten.
- Rejected as the primary interface; retained as an internal seam — A1 exposes
  the same dataclasses, so the API path exists without being the only path.

### A4 — TOML record via `tomllib`

- Rejected on a hard fact: `tomllib` landed in Python 3.11 and
  `pyproject.toml:12` pins `requires-python = ">=3.10"`. Adding `tomli` would
  breach the no-third-party-dependency non-goal in `PRODUCT.md:57`.

### A5 — Extend `scaffold.py` with a `--record` flag

- Strengths: no new module, no new wrapper, one command to learn.
- Costs: the scaffold's guarantee is "create empty standard artifacts, never
  overwrite, never fill evidence". Adding content generation to the same entry
  point makes that sentence untrue and puts evidence-bearing rendering behind a
  flag on the command operators currently trust to write nothing meaningful.
- Rejected. `R-X2` instead permits the one change that is genuinely shared:
  promoting the exclusive-create helper so both commands use a single audited
  write primitive.

## Decision B: summary output and API

### B1 — New `summary` module and wrapper, human text by default, `--format json` (selected)

- Strengths: the default output is readable at a glance; the JSON form carries
  identical facts and the identical exit code for scripting; validity is
  delegated to `validate_dossier`, so the summary never becomes a second
  contract implementation; `make dossiers` and its output contract are untouched.
- Costs: two rendering paths to keep in step, addressed by computing one
  `DossierSummary` structure and rendering it twice.

### B2 — JSON-only output

- Strengths: one renderer, trivially deterministic, easiest to test.
- Costs: the stated problem is an operator reading eleven files by eye; handing
  them raw JSON does not solve it. Rejected as the sole form, adopted as the
  secondary form inside B1.

### B3 — `--summary` flag on `validate_task_dossiers.py`

- Strengths: no new entry point.
- Costs: changes the output contract of the command wired into `make dossiers`
  and `make check` at `Makefile:44-45,67`, and mixes read-only diagnosis with
  reporting in one exit-code space. Rejected.

## Selected decision

A1 for the record and generator, B1 for the summary, with A3's dataclasses
exposed as the importable seam and B2's JSON retained as the secondary output
form. Promoted into `design.md`.

## Claim or decision

A JSON record rendered by a dedicated `generate` module, plus a dedicated
`summary` module producing text by default and JSON on request, is the minimal
standard-library design that satisfies every requirement without weakening an
existing guarantee. The two rejections that carry the most weight are A4, which
fails on a checkable version fact rather than on taste, and A5, which would
attach evidence-bearing generation to the command whose whole value is that it
writes nothing but empty templates.

## Evidence

- `pyproject.toml:12` pins `requires-python = ">=3.10"` and `PRODUCT.md:57`
  lists third-party Python runtime dependencies as an explicit non-goal;
  together these rule out A4 without further argument, because `tomllib` is
  unavailable before 3.11.
- `src/brichan/contracts/task_dossier/scaffold.py:1-7,98-148` states the
  scaffold's contract as "writes nothing without an explicit apply flag, never
  overwrites an existing artifact, and never fills evidence" and implements
  exactly that; A5 would have to amend that docstring, which is the concrete
  reason it was rejected.
- `src/brichan/contracts/task_dossier/parser.py:40-47` shows why A2 degrades
  badly: `parse_sections` builds a dictionary with `setdefault` and any absent
  heading simply yields nothing, so a mistyped record heading produces an empty
  value rather than the named refusal `R-G15` demands.
- `Makefile:44-45,67` shows `validate_task_dossiers.py projects` wired into both
  `dossiers` and `check`, which is the concrete cost that rejects B3: any change
  to that command's output or exit-code space changes a repository gate.
- `scripts/validate_task_dossiers.py:1-19` and
  `scripts/scaffold_task_dossier.py:1-19` establish the thin-wrapper shape that
  A1 and B1 copy verbatim — `sys.path` bootstrap, import `main`, `SystemExit`.

## Uncertainty

- JSON's lack of comments means a record cannot carry rationale beside a field;
  rationale lives in the artifacts the record produces. Whether that is
  irritating in practice is unmeasured, and a future option could accept a
  `"_comment"` key. It is deliberately not added now, because `R-G15` refuses
  unknown keys and an escape hatch would weaken that refusal.
- A2 was rejected on failure-mode quality, not on measured operator preference;
  if a later usage study shows Markdown authoring is materially preferred, the
  dataclass seam from A3 makes an alternative front end additive rather than a
  rewrite.
- No unresolved uncertainty remains about A4 or B3: both were rejected on
  checkable repository facts rather than on judgment.
