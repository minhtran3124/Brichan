# Settings-driven model routing implementation plan

- Plan ID: `MODEL-ROUTING-P1`
- Version: 3
- Status: reviewed
- Accepted: 2026-07-29
- Reviewed: 2026-07-29
- Amended: 2026-07-29 after independent reviews `ROUTING-REVIEW-001` and
  `ROUTING-REVIEW-002`
- Branch: `feat/settings-driven-model-routing`

## Objective

Replace active model hard-coding and hand-written worker model commands with a
validated repository settings contract for coordinator runtimes and named
Herdr worker routes.

## Design

1. Add `config/model-routing.json` with schema version 1, coordinator defaults,
   and named `plan`, `implement`, `review`, and `scan` routes.
2. Add an importable dependency-free routing module that loads, validates, and
   resolves runtime/model/effort values.
3. Extend the Herdr launcher with a named-route path while preserving explicit
   raw commands as a compatibility escape hatch.
4. Translate resolved routes into provider-native arguments. Keep native-agent
   disabling, permission safety, forbidden-effort rejection, and provider
   allowlisting code-enforced.
5. Make coordinator adapters read their defaults from the same manifest while
   preserving explicit CLI and documented compatibility overrides.
6. Remove active model defaults from prompts/instructions. Keep the model
   catalog as verified capability and routing guidance, not executable state.
7. Add unit, integration, contract, and structural coverage, including dry-run
   resolution that performs no Herdr mutation.

## Authorized implementation paths

- `config/model-routing.json`
- `config/repository-paths.json`
- `src/brida/cli/`
- `src/brida/orchestration/`
- `bin/`
- `tests/unit/`
- `tests/integration/`
- `tests/contract/`
- `README.md`
- `CLAUDE.md`
- `CHANGELOG.md`
- `Makefile`
- `docs/policy/model-catalog.md`
- `docs/policy/operating-principles.md`
- `.agents/skills/herdr-orchestration/`

Project memory under `projects/brida-model-routing/` remains coordinator-owned.

## Non-goals

- Automatic AI-based route selection.
- Provider credential or billing changes.
- Configurable sandbox, approval, permission, or arbitrary command arguments.
- Native runtime delegation.
- Version bump, release, deployment, or publication.

## Acceptance criteria

| ID | Criterion |
|---|---|
| AC1 | One repository JSON manifest is the active source of coordinator and named worker route defaults. |
| AC2 | `plan`, `implement`, `review`, and `scan` resolve to valid runtime/model/effort triples and can be changed without editing prompts or Python constants. |
| AC3 | The Herdr launcher supports named routes and a no-mutation dry-run/JSON resolution path while preserving legacy explicit commands. |
| AC4 | CLI one-off route overrides have documented precedence over manifest values. |
| AC5 | Unknown routes/runtimes, malformed settings, unsupported effort, Codex `ultra`, arbitrary argv settings, and permission-bypass attempts fail before Herdr starts a worker. |
| AC6 | Codex and Claude worker commands always disable native delegation independently of project trust or prompt compliance. |
| AC7 | Coordinator adapters consume manifest defaults and preserve explicit user overrides without embedding active model defaults in `CLAUDE.md`. |
| AC8 | Unit, integration, contract, path, package, receipt, isolated sandbox, and real installed-runtime smoke checks pass. |

## Required verification

- Focused routing and launcher unit tests.
- Stable wrapper integration tests with fake executables/Herdr.
- `make check`.
- Clean temporary sandbox copy with `make check`.
- Real installed `codex`, `claude`, and `herdr` version/auth/command-resolution
  smoke without spawning nested agents or making remote changes.
- Final diff review against AC1–AC8.

## Version 2 remediation amendment

- Normalize all provider-equivalent attached short-option forms before safety
  validation, including Codex `-c=K=V`, `-cK=V`, `-sV`, and `-mV`.
- Keep provider-specific command translation under `src/brida/cli/`; the
  orchestration package remains provider-neutral.
- Remove the unreachable launcher default helper and retarget its tests to the
  active guarded command builders.
- Prevent Claude's variadic `--disallowed-tools` flag from consuming a legacy
  positional prompt.
- Update worker-selection policy to resolve named settings routes first and use
  the catalog only to evaluate or change routing choices.
- Add regression coverage for attached option forms, coordinator delegation
  enabling, invalid coordinator environment overrides, malformed manifest
  startup, legacy Claude launch, and human-readable dry-run output.

## Version 3 import-boundary and legacy-safety amendment

- Remove the eager orchestration-to-provider-adapter import edge; provider
  command construction is loaded only when launch resolution needs it.
- Make the package gate import `brida.cli.provider_commands` first in a fresh
  interpreter and assert importing `brida.orchestration` does not eagerly load
  `brida.cli`.
- Reject legacy Codex profiles and extra directory grants because they can
  indirectly widen sandbox scope.
- Reject Claude bare mode and worker tool-list overrides because they can
  disable Herdr lifecycle hooks or make native-agent denial precedence depend
  on provider parser behavior.
- Add a combined CLI-over-environment precedence integration test.

## Rollback

Revert the feature commit. Legacy explicit worker command syntax remains
available during migration.
