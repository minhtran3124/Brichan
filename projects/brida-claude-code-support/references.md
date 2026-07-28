# References

| Evidence | Date | Result |
| --- | --- | --- |
| `claude --version` | 2026-07-27 | Claude Code 2.1.220 installed |
| `herdr integration status` | 2026-07-27 | Claude integration current, v7 |
| `claude --help` | 2026-07-27 | Supports `--disallowed-tools`, project instructions, and runtime flags |
| Herdr Claude smoke test | 2026-07-27 | Worker `brida-claude-support-smoke`, pane `w1X:p9`; correct cwd, no writes, no spawned agents; `BRIDA_CLAUDE_HERDR_OK` |
| Five-worker Herdr read-only evaluation | 2026-07-28 | `MULTI-001`–`MULTI-005`; panes `w1X:p14`–`w1X:p18`; all reports collected and no worker-caused repo changes |
| `claude auth status` | 2026-07-28 | `loggedIn: false`; prior 2026-07-27 authentication evidence is stale |
| `claude auth status` outside restricted sandbox | 2026-07-28 | Re-authentication verified: `loggedIn: true`, method `claude.ai`, subscription `max`; no account identifiers stored |
| `PYTHONDONTWRITEBYTECODE=1 make check` | 2026-07-28 | 10 metrics tests + 21 repository tests passed; 16 metrics rows valid |
| OpenAI Agents SDK docs | 2026-07-28 | Manager/handoff patterns, structured outputs, sessions, hooks, and tracing: https://openai.github.io/openai-agents-python/agents/ |
| Claude Code agent teams and worktrees | 2026-07-28 | Native teams are not Brida's control plane; worktree isolation is a transferable pattern: https://code.claude.com/docs/en/agent-teams and https://code.claude.com/docs/en/worktrees |
| Microsoft AutoGen Core runtime | 2026-07-28 | Runtime-managed agent lifecycle and messaging comparison: https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/framework/agent-and-agent-runtime.html |
| LangGraph persistence and handoffs | 2026-07-28 | Checkpoints/resume and stateful handoff comparison: https://docs.langchain.com/oss/python/langgraph/persistence and https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs |
| Mixed-provider pilot `PILOT-001` | 2026-07-28 | Claude Opus plan `PILOT-001-P1` (`w1X:p19`) → Codex Terra implementation (`w1X:p1A`) → fresh Claude Opus review (`w1X:p1B`); reviewer `PASS`, 13 contract tests and 32 total checks pass |
| Mixed-provider dogfood receipt `PILOT-002` | 2026-07-28 | `evals/mixed-provider-coding/PILOT-002/handoff-receipt.md`; fresh reviewer found it through progressive memory without chat history and returned final `PASS` |
| Concurrent writer pilot `CONCURRENT-001` | 2026-07-28 | `evals/mixed-provider-coding/CONCURRENT-001/handoff-receipt.md`; two Codex Terra writers from dispatch SHA `83c713e`, disjoint committed path sets, conflict-free integration, 40 checks pass before independent review |
