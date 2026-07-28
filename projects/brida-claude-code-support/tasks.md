# Tasks

| ID | Task | Owner | Status | Acceptance evidence |
| --- | --- | --- | --- | --- |
| CLAUDE-001 | Add explicit runtime dispatch and launchers | Brida | complete | Shell syntax and contract tests pass |
| CLAUDE-002 | Add Claude Code policy adapter | Brida | complete | `CLAUDE.md` contract test passes |
| CLAUDE-003 | Validate local Claude Code startup | Brida | complete | Claude Code 2.1.220 version smoke passes |
| CLAUDE-004 | Validate Herdr Claude worker lifecycle | Brida | complete | `brida-claude-support-smoke`, pane `w1X:p9`, model alias `sonnet`; marker `BRIDA_CLAUDE_HERDR_OK` |
| CLAUDE-005 | Update durable evidence and commit | Brida | complete | Feature branch commit; 33 checks pass; SHA recorded in branch history |
| CLAUDE-006 | Validate parallel Herdr Claude workers | Brida | complete | `brida-demo-catalog` (pane `w1X:pB`) and `brida-demo-contract` (pane `w1X:pC`), Sonnet 5, both observed `working` concurrently 16:27:12-16:27:20; 6/6 reported facts independently re-verified |
| MULTI-001 | Read-only architecture/runtime inventory | `brida-multi-architecture` / `w1X:p16` / Codex Luna | complete | File/line evidence checked; no worker-caused changes |
| MULTI-002 | Read-only build/test/dependency inventory | `brida-multi-build` / `w1X:p18` / Codex Luna | complete | `make check`: 31 tests; no worker-caused changes |
| MULTI-003 | Read-only multi-agent handoff analysis | `brida-multi-orchestration` / `w1X:p17` / Codex Terra | complete | Current capability separated from proposed Claude→Codex protocol |
| MULTI-004 | Read-only external framework research | `brida-multi-research` / `w1X:p15` / Codex Luna | complete | Four official-source comparisons independently opened |
| MULTI-005 | Read-only model/task routing analysis | `brida-multi-routing` / `w1X:p14` / Codex Terra | complete | Routing matrix bounded by current CLI/auth evidence |
| PILOT-001-P | Plan minimal handoff/receipt template and contract test | `brida-pilot-claude-plan` / `w1X:p19` / Claude Opus | complete | `PILOT-001-P1` accepted; zero planner changes |
| PILOT-001-I | Implement accepted pilot plan | `brida-pilot-codex-implement` / `w1X:p1A` / Codex Terra | complete | Four-path diff; 13 contract tests and 32 total checks pass |
| PILOT-001-R | Independent review of pilot implementation | `brida-pilot-claude-review` / `w1X:p1B` / Claude Opus | complete | `PASS`; no defects; one low GFM placeholder-rendering risk |
| HARDEN-001-I | Harden receipt rendering, schema marker, and contract tests | `brida-harden-codex` / `w1X:p1C` / Codex Terra | complete | Two-path hardening; 13 contract tests and 32 total checks pass |
| HARDEN-001-R | Independent review of receipt hardening | `brida-harden-claude-review` / `w1X:p1D` / Claude Opus | complete | Initial `CHANGES REQUIRED`; three-label remediation re-reviewed `PASS` |
| PILOT-002-P | Plan task-packet receipt-link integration | `brida-pilot2-claude-plan` / `w1X:p1E` / Claude Opus | complete | `PILOT-002-P1` accepted; zero planner changes |
| PILOT-002-I | Implement accepted task-packet integration | `brida-pilot2-codex-implement` / `w1X:p1F` / Codex Terra | complete | Four-path diff; 14 contract tests and 33 total checks pass |
| PILOT-002-R | Review integration and filled receipt retrieval | `brida-pilot2-claude-review` / `w1X:p1G` / Claude Opus | complete | Initial `CHANGES REQUIRED`; remediation mutation-tested; final `PASS`; retrieval succeeded |
| CONCURRENT-001-P | Plan mandatory-receipt and exclusive-ownership policy plus two-writer pilot | `brida-concurrent-plan` / `w1X:p1H` / Claude Opus | complete | `CONCURRENT-001-P1` accepted; exact non-overlapping writer scopes; zero planner changes |
| CONCURRENT-001-A | Encode mandatory-receipt and concurrent-writer policy | `brida-concurrent-writer-a` / `w1X:p1J` / Codex Terra | complete | `e65269f` plus exact-anchor remediations `b8382db`, `795a3a5`; authorized policy paths only |
| CONCURRENT-001-B | Add independent contract coverage for concurrent-writer policy | `brida-concurrent-writer-b` / `w1X:p1K` / Codex Terra | complete | `b816ede`; one new test path; six intentional pre-integration assertion failures |
| CONCURRENT-001-R | Review integrated two-writer pilot | `brida-concurrent-review` / `w1X:p1M` / Claude Opus | complete | Initial `CHANGES REQUIRED`; F1/F3 remediated at `c2413fe`; mutation-tested re-review `PASS`; F2 remains non-blocking |
| CONCURRENT-002-I | Canonical receipt storage, validator, structural contracts, and worker recovery policy | `brida-receipt-hardening` / `w1X:p1N` / Codex Sol | complete | `71e3d9d`; nine authorized paths; 15 validator tests, 10 structural tests, and 48 tests-directory checks pass |
| CONCURRENT-002-R | Independent review of receipt hardening | `brida-receipt-hardening-review` / `w1X:p1P` / Claude Opus | complete | `PASS`; two controlled mutations and 40 read-only parser probes; six non-blocking residual risks recorded |
| RECOVERY-001-I | Add structural recovery-policy anchors | `brida-recovery-anchors` / `w1X:p1Q` / Codex Terra | complete | `a9f30dc`; one authorized test path; 10 focused tests and full checks pass |
| RECOVERY-001-R | Independently review recovery anchors | `brida-recovery-anchors-review` / `w1X:p1R` / Claude Opus | complete | `PASS`; three policy weakenings caught; byte-exact restoration; two LOW residual risks |
| RECOVERY-002-A1 | Controlled original-worker stall | `brida-recovery-stall` / pane pending / Codex Luna | pending | Three evidenced no-progress observations before stale/abandoned |
| RECOVERY-002-A2 | One bounded replacement attempt | `brida-recovery-replacement` / pane pending / Codex Luna | pending | Same plan/receipt/scope; verified read-only evidence; no second replacement |
