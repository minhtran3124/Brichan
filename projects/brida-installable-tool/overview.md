# Brida installable repository tool

- Name: Brida installable repository tool
- Slug: brida-installable-tool
- Repository/path: repository root (`.`)
- Owner: Brida
- Lifecycle status: active
- Last verified: 2026-07-29

## Purpose

Evaluate whether Brida should evolve from a repository that users clone and run
into a tool the owner installs into existing project repositories, with a later
small dogfood cohort of 3–5 trusted users.

## In scope

- Comparable products and adjacent approaches.
- Current repository/package readiness.
- Installation, initialization, update, and uninstall lifecycle.
- Compatibility, security, maintainability, and dogfood trade-offs.
- A feasibility conclusion and recommended product direction.
- Stage 1 Codex-focused implementation: installed package execution outside the
  Brida checkout, project initialization, status/doctor diagnostics,
  package-owned policy bootstrap, and Herdr skill discovery.
- Disposable-repository and installed-wheel verification.
- PyPI release preparation for the `brichan` distribution, including metadata,
  dual-artifact CI validation, and an inert Trusted Publishing workflow.

## Out of scope

- Publishing packages, deploying, contacting external parties, or changing
  remote state. Release preparation is in scope; an actual TestPyPI/PyPI
  upload remains a separately authorized action.
- Commercialization, market sizing, growth, pricing, or support for a broad
  user population.
- Broad platform and repository-shape compatibility beyond the dogfood
  environment.
- Automatic mutation of existing `AGENTS.md`, `CLAUDE.md`, or provider config.
- Production-grade migrations, Windows support, or broad multi-runtime support
  in the first vertical slice.
- Selecting irreversible compatibility or security trade-offs.

## Architecture

The current repository exposes a dependency-free Python package and console
entrypoints while also carrying repository-owned policy, project memory,
configuration, evidence, scripts, and runtime discovery adapters.

Installed schema v1 separates three roots: package-owned tool resources, the
target Git root, and target-owned `.brida/` state. It injects Brida policy and
Herdr skill discovery through invocation-level Codex configuration and never
uses target-owned Brida wrappers.

The local installer adds a fourth operational boundary: a dedicated external
virtual environment for the Brida executable. User command symlinks make it
available without activation and keep it independent from target `.venv`
lifecycles.

## Stable constraints

- Worker agents are independent main-agent sessions created through Herdr.
- Runtime-native delegation remains disabled.
- Existing Codex, Claude Code, Herdr, project-memory, receipt, and verification
  contracts must be accounted for.
- Research workers are read-only and may not publish or modify the repository.

## Success measures

- Independent evidence covers product analogues, technical feasibility, repo
  fit, lifecycle UX, risks, advantages, and disadvantages.
- Claims about current capability are verified against local files or tests.
- External claims cite direct, preferably official, sources and disclose
  uncertainty.
- The final recommendation defines a narrow one-user dogfood prototype and a
  bounded path to 3–5 trusted users.
- An installed wheel can initialize a disposable Git repository and launch a
  guarded Codex command rooted in that repository without executing repository-
  supplied Brida wrappers.
- Repeated initialization is safe, existing user files remain untouched, and
  status/doctor expose incomplete or incompatible state.
- Stage 1 disposable acceptance and independent review pass before any real
  owner-repository dogfood.
- A package-owned installer can install Brida from outside the checkout into a
  dedicated external environment, expose commands without activation, and
  leave a target repository's existing `.venv` untouched.
