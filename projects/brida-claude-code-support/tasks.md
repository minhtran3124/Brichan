# Tasks

| ID | Task | Owner | Status | Acceptance evidence |
| --- | --- | --- | --- | --- |
| CLAUDE-001 | Add explicit runtime dispatch and launchers | Brida | complete | Shell syntax and contract tests pass |
| CLAUDE-002 | Add Claude Code policy adapter | Brida | complete | `CLAUDE.md` contract test passes |
| CLAUDE-003 | Validate local Claude Code startup | Brida | complete | Claude Code 2.1.220 version smoke passes |
| CLAUDE-004 | Validate Herdr Claude worker lifecycle | Brida | complete | `brida-claude-support-smoke`, pane `w1X:p9`, model alias `sonnet`; marker `BRIDA_CLAUDE_HERDR_OK` |
| CLAUDE-005 | Update durable evidence and commit | Brida | pending | Diff, tests, commit SHA |
| CLAUDE-006 | Validate parallel Herdr Claude workers | Brida | complete | `brida-demo-catalog` (pane `w1X:pB`) and `brida-demo-contract` (pane `w1X:pC`), Sonnet 5, both observed `working` concurrently 16:27:12-16:27:20; 6/6 reported facts independently re-verified |
