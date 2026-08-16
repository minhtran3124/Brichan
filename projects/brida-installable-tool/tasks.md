# Task register

## Active

| ID | Task | Owner/session | Model | Status | Acceptance criteria |
|---|---|---|---|---|---|

## Blocked

| ID | Blocker | Decision needed from | Next check |
|---|---|---|---|

## Recovery evidence

- `MEMORY-001` attempt 1: session `49c52563-1557-4351-ae69-8c36c8594bf6`, pane `w34:p9`.
- 2026-08-09T16:34:32Z: Herdr `blocked`; unchanged Claude subscription-limit prompt after the checker body was written.
- 2026-08-09T16:35:09Z: Herdr `blocked`; same prompt and no material progress.
- 2026-08-09T16:35:45Z: Herdr `blocked`; same prompt and no material progress.
- Decision: attempt 1 is stale and abandoned; preserve its whitespace-clean partial diff and use the one bounded replacement allowed by worker-recovery policy.

## Completed

| ID | Outcome | Evidence | Completed |
|---|---|---|---|
| DOGFOOD-007 | Source wrappers use explicit checkout entrypoints; installed console scripts remain managed-only; H1/M1/M2 remediated and independently reviewed | `handoffs/DOGFOOD-007/receipt.md`; focused 51/36/14/29; full 533/95/130/10 gate; plan/code review v2 `PASS` | 2026-08-15 |
| HERDR-001 | Implemented typed read-only Herdr monitoring; remediated PR #30 installer exposure and missing required-runtime findings; all independent reviews pass | `handoffs/HERDR-001/receipt.md`; code-review v5 `PASS`; 167 focused tests; final full gate with 523 unit, 93 contract, and 126 integration tests | 2026-08-14 |
| INIT-002 | Made `.agents/skills/herdr-orchestration/` a default, coexistence-safe init export; removed the opt-in flag and refused symlink-directed parent traversal | `handoffs/INIT-002/receipt.md`; independent version-2 plan/code review `PASS`; 16 focused, 86 affected reviewer, 403 unit, 82 contract, and 90 integration tests; all memory/path/package gates | 2026-08-10 |
| PYPI-003 | Confirmed the public GitHub repository and anonymous raw hero URL; enabled public PyPI README rendering, regenerated the description, and closed the completed durable-memory gate | `handoffs/PYPI-003/receipt.md`; code review `PASS`; 20 focused unit, 11 focused contract, 401 unit, and 81 contract tests; README, memory, and path gates | 2026-08-10 |
| MEMORY-001 | Repaired product/project memory, installed-policy and wheel-guide drift; added the offline read-only memory checker to `make check`; remediated all three implementation-review findings | `handoffs/MEMORY-001/receipt.md`; code review v2 `PASS`; 27 focused tests; full gate with 400 unit, 79 contract, and 90 integration tests | 2026-08-10 |
| COMPAT-001 | Audited coexistence with target `.claude`, `.agents`, `.codex`, instruction files, skills, hooks, and wrappers; filesystem-safe but runtime compatibility remains conditional pending live Codex probes | `brida-existing-instructions-compat` / `w27:p5`; `existing-instructions-compatibility-assessment.md`; focused tests and disposable coexistence probe | 2026-07-30 |
| ARCH-001 | Rust performance migration assessed; recommendation is to retain Python and gate any future selective prototype on measured bottlenecks | `brida-rust-rewrite-research` / `w27:p3`; `rust-migration-assessment.md`; local benchmarks and official sources | 2026-07-30 |
| INSTALL-001 | Comparable-product and adjacent-tool research | `brida-install-landscape` / `w1X:p34` / Codex Luna; six reverified official comparisons | 2026-07-29 |
| INSTALL-002 | Current repository installability and coupling audit | `brida-install-repo-audit` / `w1X:p35` / Codex Luna; local capability/gap and path evidence | 2026-07-29 |
| INSTALL-003 | Install/init/migrate/uninstall lifecycle options | `brida-install-lifecycle` / `w1X:p36` / Codex Luna; options, ownership, rollback, and prototype contract | 2026-07-29 |
| INSTALL-004 | Security, compatibility, and operational risk analysis | `brida-install-risks` / `w1X:p37` / Codex Luna; risk/compatibility evidence and scoped safety controls | 2026-07-29 |
| INSTALL-005 | Product positioning, adoption, and trade-off analysis | `brida-install-strategy` / `w1X:p38` / Codex Terra; conditional strategy and evidence gates | 2026-07-29 |
| INSTALL-006 | Independent synthesis review and two focused re-reviews | `brida-install-synthesis-review` / `w1X:p39` / Codex Sol high; final verdict `PASS` in `review.md` | 2026-07-29 |
| DOGFOOD-001 | Codex-first installed-package vertical slice implemented and independently reviewed | `brida-dogfood-codex-vslice` / `w1X:p3A`; `brida-dogfood-codex-review` / `w1X:p3B`; installed-wheel probes; final reviewer verdict `PASS`; 152-test `make check` | 2026-07-29 |
| DOGFOOD-002 | Claude implementation stabilization found no reproducible defect and made no code changes | `brida-dogfood-claude-stabilize` / `w1X:p3C`; configured `implement` route resolved to Claude Sonnet medium; independent wheel/adversarial probes and 152-test `make check` passed | 2026-07-29 |
| DOGFOOD-003 | One-command external installer with no virtualenv activation | Brida coordinator; `scripts/install-brida`; outside-checkout integration test | 2026-07-29 |
| DOGFOOD-004 | Independent safety and portability review of the external installer | `brida-installer-review` / `w1X:p3D`; Claude Opus high; final verdict `PASS`; 155-check independent `make check` | 2026-07-29 |
| DOGFOOD-005 | Installer prerequisite and reused-environment hardening | `brida-installer-pip-fix` / `w1X:p3E`; Claude Sonnet medium; pip-specific regressions, docs alignment, local-venv scan fix, and full suite passed | 2026-07-29 |
| PYPI-001 | `brichan` `0.5.0` PyPI release preparation, independently reviewed | `brida-brichan-pypi-implement` / `w1X:p3F` (Claude Sonnet medium); `brida-brichan-pypi-review` / `w1X:p3G` (Claude Opus high); receipt, clean artifacts, OIDC workflow, and full checks | 2026-07-29 |
| DOGFOOD-006 | Read-only JSON doctor diagnostics plus compact text summary with route models, policy bullets, repository/Git/dependency details, and required Herdr | `handoffs/DOGFOOD-006/receipt.md`; plan review PASS v3; code review PASS v2; focused/full tests, direct JSON/text probes, symlink/UTF-8 adversarial probes; full check passes from clean generated-artifact state | 2026-08-03 |
| RENAME-001 | Runtime rename from Brida to Brichan completed: importable package, console commands, installed-project directory, and installer all read `brichan`; `projects/brida-*` memory slugs deliberately retained | `src/brichan/`; `scripts/install-brichan`; `Rename package` commit; decision `2026-08-09 — Brida → Brichan rename completed; project slugs retained` | 2026-07-30 |
| PYPI-002 | `brichan` published on PyPI with tag-triggered Trusted Publishing; a `vX.Y.Z` tag push is the only publish trigger and the first fully automated publish was `v0.9.0` | `handoffs/PYPI-001/release-checklist.md`; `.github/workflows/publish.yml`; <https://pypi.org/project/brichan/> | 2026-08-03 |
| INIT-001 | `init` creates missing root `AGENTS.md`/`CLAUDE.md` pointers to `.brichan/` without editing pre-existing ones, and the `.agents/` skill export is gated behind the opt-in `--init-agents` flag | `feat: create missing root AGENTS.md/CLAUDE.md pointers during init` and `feat: gate the .agents/ skill export behind an opt-in --init-agents flag` commits; PRs #22 and #23; focused init tests | 2026-08-03 |
| POLICY-001 | The installed-project policy mandates the mandatory plan/implement/review lifecycle with no bounded-edit exception; the coordinator writes only under `.brichan/project-memory/` | `src/brichan/resources/dogfood_v1/policy/operating-principles.md`; `tests/contract/test_dogfood_policy_contract.py`; PR #25; `CHANGELOG.md` `[0.11.0]` | 2026-08-09 |
