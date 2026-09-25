# References

| Topic | Source | Verified date | Notes |
|---|---|---|---|
| Vendor docs | https://docs.typesafe.ai/ | 2026-09-24 | Three primitives; "one specific, well-scoped thing per question"; API ref at `/api.md`, Python SDK `typesafe-sdk` |
| Harness patterns | https://www.langchain.com/blog/building-a-harness-with-jev | 2026-09-24 | Model routing, tool risk gating, stop decisions; middleware excludes tool outputs from the judge |
| API and pricing | https://flaviocopes.com/jev/ | 2026-09-24 | `POST /v1/systemone`, `jev-latest`, $0.042/M input, 70-500 ms, ~64k context, 250k tok/s, 1,200 rpm |
| Technical explainer | https://blog.dailydoseofds.com/p/jev-clearly-explained | 2026-09-24 | RLCD calibration training; shadow-mode first; "schema safety != decision correctness" |
| 10-dataset benchmark | https://dev.to/aitejiu/benchmarking-jev-what-a-decision-model-can-and-cant-do-in-an-agent-harness-20po | 2026-09-24 | ~22.5k calls, $2.19; injection 100% P/R @0.10; shell gate FP 14.5% -> 1.8% via orthogonal nouls; difficulty routing 51.3% |
| Tool-risk calibration | https://dev.to/webofmike/i-benchmarked-jev-on-agent-tool-call-risk-calibration-held-49i3 | 2026-09-24 | 60 cases, 91.7%; every error had confidence < 1.000; ambiguous cases 71.4% |
| Injection weakness | https://venturebeat.com/security/companies-are-putting-jev-in-charge-of-ai-agent-decisions-and-prompt-injection-can-influence-the-verdict | 2026-09-24 | `rm -rf ~/.ssh` block 0.76 -> 0.48 after injected "pre-approved" field; keep deterministic checks |
| Reference hook impl | https://github.com/leepokai/jev-guard | 2026-09-24 | Claude Code / Codex `PreToolUse`/`PostToolUse`; risk 0-3, approval, user_requested, from_untrusted; ~$0.00004/call |
| Memory control paper | https://arxiv.org/html/2609.23986v1 | 2026-09-24 | Jev-Mem: System-One retrieval stop decisions; 6.6x faster construction on LoCoMo |
| Launch context | https://www.techspot.com/article/3172-meet-jev/ | 2026-09-24 | TypeSafe AI out of stealth 2026-09-15, $40M seed, founder Diego Almeida |
| Brichan cost baseline | `metrics/runs.jsonl` | 2026-09-24 | 25 runs, 67 workers, 99 reviewer findings, `cost_usd` null on every run |
| Brichan token A/B | `projects/brida-workflow-evaluation/current-state.md` | 2026-09-24 | Delegation: coordinator input -68.2%, total tokens +36.9% |
