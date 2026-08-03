# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `DOGFOOD-006`
- Task level: `1`
- Artifact: `requirements`
- Artifact version: `3`
- Origin: `coordinator:2026-08-03-doctor-json-plan-v3`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `98e27c66-74a6-4fdc-bbc6-614ebf8a225e`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Claim or decision

The requirements below fully cover the requested read-only `bin/brichan doctor
--json` diagnostics: the six requested report areas, the no-write / no-Herdr /
no-Git-mutation constraints, the nonzero-exit contract for an invalid checkout,
and the test, documentation, and full-validation obligations.

## Requirements

- R1 (JSON report): `bin/brichan doctor --json` emits exactly one JSON document
  on stdout containing structured sections for (a) the resolved repository
  root, (b) Git status, (c) required policy files, (d) model-routing
  configuration, (e) project-memory state, and (f) key dependencies
  (`python`, `git`, `codex`, `herdr`).
- R2 (dual target, existing lifecycle only): the report covers both targets the
  current lifecycle already distinguishes. When the resolved repository is the
  running Brichan source checkout (the identity test already implemented by
  `_checkout_root()` in `src/brichan/cli/runtime.py`), the policy, routing, and
  memory sections diagnose the checkout contract drawn from
  `config/repository-paths.json` (`internal-policy`, `runtime-config`, and
  `durable-state` entries). Otherwise the sections diagnose the installed
  `.brichan` footprint exactly as `inspect_project()` in
  `src/brichan/lifecycle.py` defines it today.
- R3 (no writes): the command performs no filesystem writes inside the target
  repository or the checkout. Diagnostics reuse the read-only primitives that
  `inspect_project()` already uses (`lstat`, file reads, `load_settings`).
- R4 (no Herdr call): `herdr` is only resolved on `PATH` via `shutil.which`,
  as `doctor_lines()` does today; the executable is never invoked, and it
  remains optional.
- R5 (no Git mutation): Git state is interrogated read-only. Any `git`
  subprocess must be a query (`status` / `rev-parse`) invoked with
  `--no-optional-locks` so no optional index refresh is written; no fetch,
  checkout, commit, or config command is ever run. A missing `git` executable
  degrades the Git section to an explicit `unavailable` status rather than
  failing the command.
- R6 (exit semantics): exit codes are deterministic and preserved. Installed
  targets keep the documented contract 0 healthy / 1 uninitialized /
  2 malformed / 3 incompatible / 4 healthy-but-`codex`-missing (`EXIT_CODES`
  and `doctor_lines` in `src/brichan/lifecycle.py`; exit table in
  `docs/guides/installable-dogfood.md`). A source checkout that fails its
  contract (missing canonical policy file, unparseable
  `config/model-routing.json`, missing projects memory) exits `2`; a valid
  checkout with `codex` missing exits `4`. Every invalid checkout therefore
  exits nonzero.
- R7 (text contract unchanged): default (non-`--json`) `doctor` output and
  exit codes stay byte-identical; the plain lifecycle lines are an asserted
  machine-readable contract per the module docstring of
  `src/brichan/cli/render.py`.
- R8 (bounded surface): no change to the installed `.brichan` schema, packaged
  resources under `src/brichan/resources/`, the model-routing manifest
  (`config/model-routing.json`), or any Herdr lifecycle behavior.
- R9 (verification): unit tests, integration tests, documentation updates, and
  a passing full validation (`make check`) are required before the task can be
  called done.

## Revision 2 amendments

- The JSON root is exactly `{\"schema_version\": 1, \"ok\": boolean,
  \"repository\": object, \"git\": object, \"policies\": object,
  \"model_routing\": object, \"project_memory\": object,
  \"dependencies\": object}`. Unknown root fields are not emitted.
- Each check object uses `status` from the closed set `ok`, `missing`,
  `invalid`, or `unavailable`, plus a stable `path`/`value` where applicable
  and a diagnostic `detail`; `ok` is true only when all required checks are
  `ok` and optional Herdr may be `missing`.
- JSON uses sorted keys, two-space indentation, and one trailing newline.
- Installed-project JSON is mandatory: it derives `.brichan` state and exit
  codes from `inspect_project()`; source-checkout JSON uses the checkout
  inventory. Separate tests cover both modes and all installed exit classes.
- Tests must spy on subprocess argv, assert no Herdr process is launched, and
  snapshot the worktree and Git index before/after the command.

## Revision 3 amendments

- `repository` is exactly `{\"status\": status, \"root\": string,
  \"kind\": \"source_checkout\"|\"installed_project\", \"detail\": string}`.
- `git` is exactly `{\"status\": status, \"branch\": string|null,
  \"commit\": string|null, \"dirty\": boolean|null,
  \"untracked\": boolean|null, \"detail\": string}`.
- `policies` and `project_memory` are exactly `{\"status\": status,
  \"files\": {relative_path: file_check}, \"detail\": string}`; each
  `file_check` is exactly `{\"status\": status, \"path\": string,
  \"detail\": string}`.
- `model_routing` is exactly `{\"status\": status, \"path\": string,
  \"schema_version\": integer|null, \"detail\": string}`.
- `dependencies` is exactly `{\"status\": status, \"python\": dep_check,
  \"git\": dep_check, \"codex\": dep_check, \"herdr\": dep_check}`;
  `dep_check` is exactly `{\"status\": status, \"path\": string|null,
  \"required\": boolean, \"detail\": string}`. Herdr is optional.
- The root `ok` is true iff every required section/check is `ok`; optional
  Herdr `missing` does not make it false. Source mode exits `0` when `ok`, `4`
  when only required Codex is missing, and `2` for any other required failure.
  Installed mode preserves `inspect_project()` state exits `0/1/2/3`, with `4`
  for healthy state with missing Codex. Missing Git exits `2` in source mode.

## Evidence

- `src/brichan/lifecycle.py` defines `inspect_project`, `EXIT_CODES`
  (healthy 0, uninitialized 1, malformed 2, incompatible 3), and
  `doctor_lines`, which already probes `codex` (required, exit 4 when missing)
  and `herdr` (optional) via `shutil.which` without executing either.
- `src/brichan/cli/runtime.py` dispatches `doctor` through
  `_lifecycle_command`, which resolves the target with
  `project_paths(explicit=args.project)` from `src/brichan/project.py`, and
  `_checkout_root()` already implements the source-checkout identity test.
- `config/repository-paths.json` inventories the checkout's canonical policy
  files (`docs/policy/identity.md`, `docs/policy/operating-principles.md`,
  `docs/policy/memory-policy.md`, `docs/policy/model-catalog.md`,
  `docs/policy/reviewer.md`; category `internal-policy`), runtime config
  (`config/model-routing.json`), and durable state (`projects`,
  `projects/index.md`), providing an existing contract for checkout validity.
- `docs/guides/installable-dogfood.md` documents current doctor behavior and
  the exit-code table this feature must preserve.

## Uncertainty

- Whether the Git section should also report ahead/behind counts against an
  upstream is unresolved; these requirements mandate only branch, commit, and
  dirty/untracked state, and the open question is recorded with a default
  assumption in `client-follow-up-questions.md`.
