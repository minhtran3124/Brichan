# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `TDW-006`
- Task level: `0`
- Artifact: `brief`
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

The real outcome of TDW-006 is not the greeting file; it is a measurement of how
much ceremony the full-document dossier contract imposes on the smallest credible
unit of work. The fixture is deliberately trivial so that every recorded cost is
attributable to the contract rather than to the requirement.

## Outcome

- Produce one byte-exact 35-byte fixture and a complete Level 0 dossier around it.
- Record what Level 0 ceremony actually costs, so the pilot can answer the open
  question recorded in project memory about acceptable Level 0 overhead.

## Constraints

- Planner-owned artifacts only: `requirements.md`, `brief.md`, `options.md`,
  `design.md`, `plan.md`. Coordinator-owned and reviewer-owned artifacts stay
  unwritten by this session.
- No commit, publish, deploy, or remote action; no routing-config or installed
  resource change.
- Level 0 keeps the routine review route and records ship authorization as
  `not-requested`.

## Success signal

Level 0 passes when the fixture is byte-exact, the five planner artifacts each
carry at least one concrete evidence item with complete provenance, and the
read-only validator reports no diagnostic attributable to a planner artifact.

## Evidence

- `projects/brida-task-dossier-workflow/current-state.md` records the pilot's
  purpose under "Next actions" and lists "the full-doc Level 0 workflow will
  produce acceptable ceremony" as an unverified assumption this task measures.
- `docs/workflows/task-dossier.md:112-121,146-153` fixes that all levels produce
  the same artifact set, that Level 0 uses the routine review route, and that
  Levels 0 and 1 must record ship authorization as `not-requested`.

## Uncertainty

- Ceremony cost is observable but not yet observed: this brief asserts what will
  be measured, and the measurement itself only exists once the accepted plan is
  executed and the coordinator closes the dossier.
