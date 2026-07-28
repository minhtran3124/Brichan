# Decisions

## 2026-07-28 — Repository structure boundaries

Accepted by the user:

- Use `docs/policy/` as the canonical internal-policy location.
- Keep `AGENTS.md` and `CLAUDE.md` as permanent root discovery adapters.
- Keep `CONTRIBUTING.md` and `SECURITY.md` at the root during the first
  migration.
- Authorize Phase 0 characterization and guardrails only; no file migration is
  authorized yet.

Supporting constraints:

- Use stable root adapters, canonical documentation, and an importable core.
- Freeze `projects/`, `evals/`, `metrics/`, receipt paths, and executable paths
  during the documentation migration.

## 2026-07-28 — Phase 1 authorization

The user approved Phase 1 after Phase 0 evidence was reported:

- Move tracked internal policy into `docs/policy/`.
- Move tracked setup history into `docs/history/`.
- Keep permanent root `AGENTS.md` and `CLAUDE.md` adapters.
- Keep one-release compatibility pointers for moved root documents.
- Do not begin Phase 2 code extraction without separate authorization.

## 2026-07-28 — Phase 1 workflow and review exceptions

- Keep ignored `internal-docs/` scratch outside the tracked `docs/` migration.
  It contains stale paths and historical branding and requires a separate
  content review before publication.
- Claude Code reached its usage limit during Phase 1. Per user direction, a
  fresh Codex Sol session replaces the independent reviewer.
- Claude adapter behavior is covered by static contracts in this phase; a live
  Claude startup smoke is deferred until quota is available.

## 2026-07-28 — Phases 2–4 authorization and review

The user separately approved continuing the refactor through Phases 2–4:

- Extract receipt contracts into an importable package while preserving the
  validator command path.
- Extract Herdr orchestration and runtime adapters while preserving the
  existing `bin/` entrypoints.
- Split tests into unit, contract, and integration layers and add wheel
  build/install/smoke coverage to CI.
- Use Codex Sol for the independent final review because Claude Code quota is
  exhausted.

The final Codex review verdict is `PASS` after remediation of environment
default compatibility and stale authorization text. Phase 5 is not authorized
to bypass its original gate: temporary pointers stay until one completed
release/compatibility window, external-link checks, both live startup smokes,
and full CI.

## 2026-07-28 — Phase 5 retirement enforcement

- Keep the default preflight CI-safe while the compatibility window is open.
- Require strict preflight success before deleting any temporary pointer.
- Pin the exact six-file migration set; config edits cannot narrow it.
- Require timestamped file-and-fragment evidence for every passing gate.
- Refresh operational evidence after release-window completion.
- Codex Sol independently reviewed the state machine after adversarial
  remediation; final verdict `PASS`.
