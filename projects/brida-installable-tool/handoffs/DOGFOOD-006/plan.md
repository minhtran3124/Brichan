# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `DOGFOOD-006`
- Task level: `1`
- Artifact: `plan`
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

## Plan status

- Plan ID: `DOGFOOD-006-P1`
- Plan status: `accepted`

## Claim or decision

1. Implement a lifecycle-owned structured doctor report and explicit
   `doctor --json` serialization. Preserve existing plain doctor output and
   installed-project behavior when JSON is not requested.
2. Use the exact version-1 JSON schema from requirements revision 3: enumerate
   required keys/types for all six sections and nested file/dependency checks,
   with closed statuses `ok`, `missing`, `invalid`, `unavailable`. Serialize
   sorted keys, two-space indentation, and one trailing newline. Root `ok` and
   source/installed exit mapping follow the specified required-check and
   Codex/Herdr rules exactly.
3. Select source-checkout versus installed-project mode explicitly. Source mode
   checks the checkout inventory; installed mode delegates state semantics to
   `inspect_project()` and preserves exit classes 0/1/2/3/4. Herdr is resolved
   only with `shutil.which` and is never launched.
4. Add unit coverage for healthy/missing/malformed checks, exact JSON schema,
   deterministic serialization, dependency handling, all installed exit
   classes, and no-write guarantees. Add subprocess-spy tests proving Git gets
   only `--no-optional-locks` read-only queries and Herdr is never executed.
   Add integration tests invoking `bin/brichan doctor --json` for temporary
   source and installed fixtures, including worktree/Git-index snapshots.
5. Update `docs/guides/installable-dogfood.md` with usage, exact JSON domains,
   statuses, exit semantics, and the read-only/no-Herdr guarantee.
6. Run focused tests and `make check`; record any unrelated generated-artifact
   failure separately. Do not push or open a PR.

Authorized implementation paths:
- `src/brichan/lifecycle.py`
- `src/brichan/cli/runtime.py`
- `src/brichan/cli/render.py`
- `tests/unit/test_project_lifecycle.py`
- `tests/unit/test_cli_render.py`
- `tests/integration/test_cli_compatibility.py`
- `tests/integration/test_installed_dogfood.py` (mandatory installed JSON
  compatibility and exit matrix)
- `docs/guides/installable-dogfood.md`

Excluded: `config/model-routing.json`, packaged resources, credentials,
deployment, remote state, Herdr invocation, push, and PR creation.

## Evidence

- `requirements.md`, `options.md`, and `design.md` in this dossier.
- Existing lifecycle source/tests, `PRODUCT.md`, and
  `config/repository-paths.json`.

## Uncertainty

- Plan version 3 incorporates the bounded corrections from independent reviews
  of versions 1 and 2; final implementation still needs code review and full
  validation.
