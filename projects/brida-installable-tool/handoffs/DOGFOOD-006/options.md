# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `DOGFOOD-006`
- Task level: `1`
- Artifact: `options`
- Artifact version: `1`
- Origin: `coordinator:2026-08-03-doctor-json-plan`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fc5cb-b798-7c50-8d3d-b86e27aa04f8`
- Effective route: `coordinator`
- Effective model: `gpt-5.6-sol`
- Effective effort: `medium`
- Reviewing session: `<session identifier or null>`
- Review verdict: `<PASS, CHANGES REQUIRED, or null>`

## Claim or decision

Option A: format the existing `doctor_lines` output as JSON. This is small but
cannot add checkout policy, routing, memory, or Git checks cleanly.

Option B: add a read-only structured diagnostic collector with text/JSON
renderers and lifecycle dispatch. This provides one source of truth, preserves
plain output, and makes each check independently testable. Selected.

Option C: invoke a shell health script. This duplicates Python path discovery,
adds subprocess surface area, and weakens the standard-library boundary.

## Evidence

- Existing `inspect_project()` already separates safe inspection from rendering.
- `runtime.py` owns lifecycle parsing, while `config/repository-paths.json`
  inventories checkout policy/config/memory paths.

## Uncertainty

- Git queries must use read-only flags and report unavailable metadata instead of
  raising an uncaught exception.
