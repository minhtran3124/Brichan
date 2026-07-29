# Changelog

All notable changes to Brida are documented here.

The format follows Keep a Changelog principles. The project does not yet claim
Semantic Versioning compatibility because its runtime contract is pre-1.0.

## [Unreleased]

## [0.5.0] - 2026-07-29

### Changed

- Set the distribution name to `brichan` in preparation for a future PyPI
  release (not yet published); the importable package stays `brida` and all
  `brida-*` console commands are unchanged.
- Added `wheel` to build-system requirements and PyPI classifiers/keywords so
  Python 3.10+ isolated and non-isolated wheel builds succeed.

### Added

- CI now builds and validates both sdist and wheel artifacts, installs them
  in a clean environment, runs `twine check`, and smoke-tests
  every documented installed command that does not require an external
  provider.
- A tag-gated Trusted Publishing GitHub Actions workflow scaffold using OIDC
  and a `pypi` environment. It cannot publish until trusted publishers are
  configured on PyPI; see the release checklist.
- `brida`, `brida-codex`, and `brida-claude` now provide `--help` and
  `--version` outside initialized projects or a source checkout; unsupported
  invocations there return an owned error rather than a Python traceback.

### Verification

- Full local `make check` passes.
- `python -m build` produces a clean sdist and wheel; the wheel installs and
  exposes all `brida-*` console commands in a disposable environment.

## [0.4.0] - 2026-07-29

### Added

- Repository-owned schema-v1 model routing for coordinator defaults and named
  `plan`, `implement`, `review`, and `scan` Herdr worker routes.
- Dependency-free routing validation, provider-native command construction,
  one-off route overrides, and no-mutation dry-run JSON resolution.

### Changed

- Coordinator adapters and Herdr worker launches now consume the routing
  manifest while preserving guarded legacy explicit worker commands.
- Native delegation disabling, forbidden effort, arbitrary setting, and
  permission-bypass checks are enforced in code before Herdr mutation.
- Simplified the README around getting started, how Brida works, and
  development; model-routing detail now lives in a dedicated guide.

### Verification

- Full local `make check` passes.
- GitHub Actions CI passes on commit `6a55c97d73945a3f09ca2e52b3613bcb52e0e3a7`
  for Python 3.10, Python 3.13, and source-package builds.
- Independent review passed acceptance criteria AC1-AC8 with no blocking
  findings.

## [0.3.1] - 2026-07-29

### Fixed

- Keep the importable `brida.__version__` value aligned with release metadata.

### Removed

- Retired the six temporary root policy pointers after the `v0.3.0`
  compatibility release; canonical policy and history remain under `docs/`.

## [0.3.0] - 2026-07-28

### Added

- Machine-readable repository path inventory, local Markdown-link validation,
  and structural characterization tests.
- Canonical `docs/policy/` and `docs/history/` taxonomy with one-release root
  compatibility pointers and permanent root agent-discovery adapters.
- Importable `src/brida/` core for receipt contracts, Herdr orchestration, and
  Codex/Claude CLI adapters while preserving existing command paths.
- Independent unit, contract, and integration test layers plus a CI wheel-build
  lane.
- Claude workers launched through Herdr now default to Claude Code's `auto`
  permission mode, while explicit per-worker modes remain supported.
- Versioned Markdown handoff/receipt template and repository contract coverage.
- Optional accepted-plan and receipt linkage in task packets with contract
  coverage.
- Mandatory receipts for accepted-plan and multi-writer handoffs, exclusive
  writer path ownership, isolated worktrees, and concurrent-writer contract
  coverage.
- Canonical project handoff receipts, a dependency-free receipt completeness
  gate, line-wrap-tolerant structural policy checks, and bounded stale-worker
  replacement rules.
- Structural coverage for recovery guarantees, a controlled one-replacement
  pilot, and a fixed-rubric Codex–Claude policy-audit benchmark.
- Receipt schema v2 with machine-validated attempt origin, lifecycle, prior
  state, replacement evidence, schema-v1 compatibility, and canonical receipt
  migration.

### Fixed

- Blank or whitespace-only receipt schema versions can no longer bypass
  version-gated lifecycle validation.

## [0.2.0] - 2026-07-27

### Added

- Balanced Herdr worker launcher that keeps coordinator and worker panes at
  equal area for groups of up to four total panes.
- Regression coverage for the supported one-, two-, three-, and four-pane
  layouts.

## [0.1.0] - 2026-07-27

### Added

- Repository-native AI Chief of Staff operating contract.
- Progressive durable project memory.
- Herdr-only worker orchestration skill.
- Independent reviewer protocol.
- Model routing catalog.
- JSONL workflow metrics, validator, and tests.
- Reproducible reviewer, token-context, metrics, and long-horizontal evals.
- Repository documentation, CI, and contract checks.
- MIT License.

### Fixed

- Launcher now disables native Codex agents consistently with project config.
