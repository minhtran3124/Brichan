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
- Phase 5 pointer retirement is not eligible until one compatibility release
  window and the deferred live Claude startup smoke are complete.
- A fail-closed Phase 5 preflight now pins all six temporary pointers and
  requires timestamped release, link, repository-search, Codex/Claude startup,
  full-CI, and changelog evidence. Independent Codex review verdict is `PASS`.
- Current preflight: Codex startup, external links, and baseline stale-reference
  search pass; release window and full CI are pending; Claude startup is
  unavailable. Strict eligibility correctly fails.

## Approved boundaries

1. `docs/policy/` is the canonical future internal-policy location.
2. `AGENTS.md` and `CLAUDE.md` remain permanent root discovery adapters.
3. `CONTRIBUTING.md` and `SECURITY.md` remain at root during the first
   migration.
4. Phases 0–4 are authorized and implemented; Phase 5 remains governed by its
   release-window and cross-runtime smoke gates.

## Next actions

1. Keep the root compatibility pointers for one release.
2. Re-run the deferred live Claude startup smoke when provider quota returns.
3. Publish the refactor through an explicitly authorized release/CI workflow.
4. After that compatibility window, refresh every operational gate and require
   strict preflight success before removing any temporary pointer.
