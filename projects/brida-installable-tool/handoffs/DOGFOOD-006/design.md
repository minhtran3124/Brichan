# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `DOGFOOD-006`
- Task level: `1`
- Artifact: `design`
- Artifact version: `3`
- Origin: `coordinator:2026-08-03-doctor-json-plan-v3`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fc5cb-b798-7c50-8d3d-b86e27aa04f8`
- Effective route: `coordinator`
- Effective model: `gpt-5.6-sol`
- Effective effort: `medium`
- Reviewing session: `null`
- Review verdict: `null`

## Claim or decision

Add a structured `doctor_report` collector in `lifecycle.py`. It will resolve
the current checkout root, check Git with bounded read-only subprocess queries,
check required `docs/policy/*`, `config/model-routing.json`, and project-memory
paths, validate routing through the existing loader, and resolve key binaries
with `shutil.which`. It will never invoke Herdr. In installed mode it will
reuse `inspect_project()` and preserve its existing state exit classes.

`runtime.py` accepts an explicit `--json` flag for `doctor`; JSON is emitted with
sorted keys, two-space indentation, and one trailing newline. The exact root is
`schema_version` (1), `ok`, `repository`, `git`, `policies`, `model_routing`,
`project_memory`, and `dependencies`. The section shapes and closed status
vocabulary are enumerated in requirements revision 3. Required checkout
failures return nonzero; Herdr remains optional. Source and installed mode
selection is explicit and tested independently, with installed state exit
classes preserved.

## Evidence

- `src/brichan/lifecycle.py` owns inspection and safe state checks.
- `src/brichan/cli/runtime.py` owns lifecycle argument parsing/dispatch.
- `bin/brichan` sets `BRICHAN_ROOT`, so checkout mode can be identified without
  changing installed-project behavior.
- Existing unit/integration tests establish no-write and exit-code conventions.

## Uncertainty

- Ahead/behind tracking is excluded. Platform-specific detail strings are
  diagnostic; root keys, nested keys/types, status values, and exit mapping are
  stable.
