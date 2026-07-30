# Task register

## Active

| ID | Task | Owner/session | Model | Status | Acceptance criteria |
|---|---|---|---|---|---|

## Blocked

| ID | Blocker | Decision needed from | Next check |
|---|---|---|---|

## Completed

| ID | Outcome | Evidence | Completed |
|---|---|---|---|
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
