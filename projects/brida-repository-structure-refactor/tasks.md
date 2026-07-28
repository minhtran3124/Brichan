# Tasks

| ID | Task | Owner | Status | Acceptance evidence |
| --- | --- | --- | --- | --- |
| STRUCTURE-001 | Analyze repository architecture and module boundaries | `brida-structure-architecture` / `w1X:p27` / Codex Sol | complete | Current coupling map, target module tree, migration risks |
| STRUCTURE-002 | Analyze multi-agent coding adaptation | `brida-structure-multi-agent` / `w1X:p28` / Claude Opus | complete | Ownership/worktree/receipt/prompt-path compatibility plan |
| STRUCTURE-003 | Analyze testing, CI, release, and deployment impact | `brida-structure-testing-deploy` / `w1X:p29` / Codex Terra | complete | Contract inventory, migration test matrix, deployment gates |
| STRUCTURE-004 | Analyze future scalability and maintainability | `brida-structure-scalability` / `w1X:p2A` / Claude Sonnet | complete | Scale scenarios, extension boundaries, anti-patterns and trade-offs |
| STRUCTURE-005 | Integrate four reports into approved refactor plan | Brida | complete | `refactor-plan.md`: target tree, phases, acceptance criteria, rollback, decisions |
| RSR-001 | Implement Phase 0 path inventory and structural guardrails | Brida | complete | `config/repository-paths.json`, path/link checker, 4 characterization tests, `make check` |
| RSR-003-A | Audit Phase 1 policy moves and discovery/reference updates | `brida-phase1-policy-audit` / `w1X:p2B` / Codex Luna | complete | Seven active consumer groups, internal cross-links, pointer requirements, and verification checklist identified |
| RSR-004-A | Audit Phase 1 workflow/history moves and link risks | `brida-phase1-workflow-audit` / `w1X:p2C` / Claude Sonnet | complete | `setup-status.md` is tracked; `internal-docs/` is ignored scratch with stale links/branding and is excluded |
| RSR-002 | Integrate Phase 1 documentation taxonomy and compatibility adapters | Brida | complete | Canonical docs, pointer stubs, updated manifest/adapters, 71 passing tests |
| RSR-002-R | Independently review Phase 1 and verify Codex startup discovery | `brida-phase1-codex-review` / `w1X:p2D` / Codex Sol | complete | Fresh Codex session loaded canonical policies; two medium findings remediated; final verdict PASS |
| RSR-005 | Extract receipt contracts into importable package | Brida | complete | `pyproject.toml`, receipt schema/parser/discovery/validation APIs, stable validator wrapper |
| RSR-006 | Extract orchestration and runtime CLI adapters | Brida | complete | Importable Herdr layout/launcher and Codex/Claude dispatch modules; stable `bin/` wrappers |
| RSR-007 | Layer tests and harden CI/package checks | Brida | complete | Independent unit/contract/integration targets, wrapper smoke tests, CI wheel build/install lane |
| RSR-009 | Final independent review of Phases 2–4 | `brida-structure-final-review` / `w1X:p2E` / Codex Sol | complete | Final verdict `PASS`; 90 tests, installed-wheel smoke, path/receipt validation, and cleanup complete |
| RSR-008 | Audit and retire temporary documentation pointers | Brida | gated | Start only after one release/compatibility window, external-link check, both live startup smokes, and full CI |
| RSR-008-P | Independently review the Phase 5 retirement preflight | `brida-phase5-preflight-review` / `w1X:p2F` / Codex Sol | complete | Five bypass classes and two edge cases remediated; 36 contract tests, final verdict `PASS`, pane cleanup complete |
| RSR-010 | Run a real Claude startup smoke via `cld-edgeful` | `brida-claude-edgeful-smoke` / `w1X:p2G` / Claude Sonnet 5 | complete | Canonical startup-policy `PASS`, branch/HEAD and package boundaries verified, no worker writes, pane cleanup and aggregate checks complete |
| RSR-011-C | Refresh post-release Codex startup evidence | `brida-phase5-codex-postrelease` / `w1X:p2H` / Codex Luna | complete | Fresh canonical-policy, orchestration, release, wrappers/imports, and no-write checks returned `PASS` |
| RSR-011-L | Refresh post-release Claude startup evidence | `brida-phase5-claude-postrelease` / `w1X:p2J` / Claude Sonnet 5 | complete | Fresh canonical-policy, orchestration, release, wrappers/imports, and no-write checks returned `PASS` |
