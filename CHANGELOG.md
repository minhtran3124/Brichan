# Changelog

All notable changes to Brida are documented here.

The format follows Keep a Changelog principles. The project does not yet claim
Semantic Versioning compatibility because its runtime contract is pre-1.0.

## [Unreleased]

### Fixed

- Keep the importable `brida.__version__` value aligned with release metadata.

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
