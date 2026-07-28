# Current state

- Status: Phases 0–4 implemented and independently reviewed with final verdict
  `PASS`; all Brida-owned review panes are closed.
- Root now contains permanent discovery/public entrypoints and temporary
  one-release pointers; canonical internal policy and setup history live under
  `docs/`.
- Four independent read-only agents completed architecture/modules,
  multi-agent coding, testing/deployment, and future-scalability research.
- All four Brida-owned worker panes were closed after their evidence was
  collected and integrated.
- The integrated recommendation is documented in `refactor-plan.md`.
- Recommended architecture: stable root adapters, canonical `docs/` taxonomy,
  and an importable `src/brida/` core introduced only after documentation
  migration is stable.
- Phase 0 added a machine-readable path inventory, consumer-reference checks,
  local Markdown-link validation, and characterization tests.
- Phase 1 moved tracked internal policy and setup history into canonical
  `docs/` locations, retained one-release root pointers, and updated active
  consumers.
- Ignored `internal-docs/` scratch was deliberately not migrated or published.
- Phase 2 extracted receipt contracts behind the stable validator wrapper.
- Phase 3 extracted Herdr orchestration and Codex/Claude CLI adapters behind
  stable `bin/` paths.
- Phase 4 established independent unit, contract, and integration suites plus
  a wheel build/install/smoke CI lane.
- Release `v0.3.0` completed the compatibility window at
  `2026-07-28T12:59:20Z`.
- A fail-closed Phase 5 preflight now pins all six temporary pointers and
  requires timestamped release, link, repository-search, Codex/Claude startup,
  full-CI, and changelog evidence. Independent Codex review verdict is `PASS`.
- Post-release Codex and Claude startup smokes, external-link checks, and the
  stale root-reference search pass with durable evidence.
- Post-release GitHub Actions run `30362433787` passed Python 3.10, Python
  3.13, and package build/install checks at `2026-07-28T13:13:11Z`.
- All six retirement gates now pass; the active-state strict preflight must be
  recorded in an immutable commit before pointer deletion.
- A worker found `brida.__version__` lagging at `0.2.0`; the follow-up branch
  aligns it with `0.3.0` and adds contract coverage.

## Approved boundaries

1. `docs/policy/` is the canonical future internal-policy location.
2. `AGENTS.md` and `CLAUDE.md` remain permanent root discovery adapters.
3. `CONTRIBUTING.md` and `SECURITY.md` remain at root during the first
   migration.
4. Phases 0–4 are authorized and implemented; Phase 5 remains governed by its
   release-window and cross-runtime smoke gates.

## Next actions

1. Run and record strict preflight while `retired` is false and all pointers
   exist.
2. Retire the six pointers in the next commit.
3. Rerun both startup smokes on the retired tree and obtain final review.
