# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `TDW-007`
- Task level: `1`
- Artifact: `options`
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

Option A — a single `re.sub` over the explicit ASCII class `[^a-z0-9]+` after
`strip().lower()`, followed by `strip("-")` — is selected. It is the only option
of the three that makes `TDW-007-R6` true by construction: the output alphabet is
the substitution's complement, so conformance to `PROJECT_SLUG_PATTERN` follows
from the character class rather than from testing.

## Options considered

- Option A (selected): `re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")`,
  raising `ValueError` when the result is empty. ASCII-only by construction;
  three operations; no dependency.
- Option B: classify with `str.isalnum()` and rebuild character by character.
  Reads as the more literal transcription of "non-alphanumeric" in the packet,
  but `str.isalnum()` is Unicode-aware — `"Café".isalnum()` is true per character
  — so `"Café Résumé"` would normalize to `café-résumé`, which fails
  `PROJECT_SLUG_PATTERN`. Rejected as a silent contract break.
- Option C: `unicodedata.normalize("NFKD", value)` with combining marks dropped,
  then Option A. Transliterates `Café` to `cafe` instead of rejecting it, which
  is friendlier, but it introduces lossy locale-sensitive behaviour the packet
  never asked for and adds a second boundary that the five required test cases do
  not cover. Rejected as scope growth.

## Decided boundary semantics

- Alphanumeric means ASCII `[a-z0-9]` after lowercasing. Non-ASCII letters are
  separators, so `"Café"` normalizes to `caf`, and a purely non-ASCII input
  raises `ValueError`.
- `strip("-")` runs after substitution, so `"--a--b--"` yields `a-b` and never a
  leading or trailing hyphen.
- Empty and whitespace-only input reach the `ValueError` branch through the same
  path as `"!!!"`; there is no separate empty-input special case.

## Evidence

- `src/brichan/contracts/task_dossier/schema.py:181` requires
  `^[a-z0-9]+(?:-[a-z0-9]+)*$`, which is what makes Option B's Unicode-aware
  behaviour a defect rather than a preference.
- `projects/brida-task-dossier-workflow/handoffs/TDW-007/task-packet.md:14-17`
  specifies trim, lowercase, run-collapse, edge-strip, and `ValueError` — five
  behaviours that Option A implements in three expressions with no branching
  beyond the empty check.
- `src/brichan/contracts/task_dossier/parser.py:5` solves this class of problem
  with `re` from the standard library, and `pyproject.toml:29` declares
  `dependencies = []`; Option A follows that existing precedent instead of
  introducing a slugify dependency.

## Uncertainty

- The ASCII-only decision is deliberate, not undecided: it makes `"Café"` yield
  `caf`, which is lossy. If a later task needs transliteration, that is a new
  requirement and a new artifact version, not a silent change to this one.
