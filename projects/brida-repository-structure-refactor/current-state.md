# Current state

- Status: Phases 0–4 implemented and independently reviewed with final verdict
  `PASS`; all Brida-owned review panes are closed.
- Root now contains only permanent discovery/public entrypoints; the six
  one-release pointers are retired and canonical policy/history remain under
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
- Immutable checkpoint commit
  `00fb58a5664403c0b17f7c4b595e26a3a33c67fe` records strict eligibility with
  `retired: no` and all six pointers present before the deletion commit.
- The controlled replay retired all six pointers again; path/reference checks,
  the full local suite, and final Codex/Claude startup smokes pass.
- Initial final review returned `CHANGES REQUIRED` only for missing immutable
  chronology and durable receipts/state; the replacement independent Claude
  review returned `PASS` after those findings were remediated.
- A worker found `brida.__version__` lagging at `0.2.0`; the follow-up branch
  aligns it with `0.3.0` and adds contract coverage.

## Approved boundaries

1. `docs/policy/` is the canonical future internal-policy location.
2. `AGENTS.md` and `CLAUDE.md` remain permanent root discovery adapters.
3. `CONTRIBUTING.md` and `SECURITY.md` remain at root during the first
   migration.
4. Phases 0–5 are authorized and implemented; permanent discovery adapters and
   command wrappers remain unchanged.

## Next actions

1. Commit the final review receipts and active project-memory updates.
2. Push the final retirement tree and verify CI on the literal retirement
   commit.
3. Open the follow-up PR for user review; do not merge without approval.
