# Model catalog

This is the canonical Brida runtime capability and model-routing guidance
catalog. Active coordinator and worker route defaults live only in
`../../config/model-routing.json`.

Last verified: 2026-07-29.

Evidence commands:

```text
codex debug models
claude --version
claude --help
claude auth status
command -v gemini grok opencode aider
```

Pricing was not verified. Do not make exact cost claims.

## Enabled Codex models

All listed Codex models report a 272,000-token context window and parallel tool
call support in the installed catalog.

| Model | Verified catalog description | Observed catalog effort | Suggested uses |
|---|---|---:|---|
| `gpt-5.6-sol` | Latest frontier agentic coding model | `low` | Complex architecture, difficult debugging, high-risk implementation, final review |
| `gpt-5.6-terra` | Balanced model for everyday agentic coding | `medium` | Normal coordination, implementation, structured research |
| `gpt-5.6-luna` | Fast and affordable agentic coding model | `medium` | Repository scanning, summaries, routine edits, test execution |
| `gpt-5.5` | Frontier model for complex coding and research | `medium` | Compatibility fallback when 5.6 is unavailable |
| `gpt-5.4` | Strong model for everyday coding | `medium` | Compatibility fallback for normal coding |
| `gpt-5.4-mini` | Small, fast, cost-efficient model for simpler coding | `medium` | Simple mechanical work when Luna is unavailable |

Sol and Terra support `low`, `medium`, `high`, `xhigh`, `max`, and `ultra`.
Luna supports through `max`. Brida must not choose `ultra` for workers because
the installed catalog describes it as enabling automatic task delegation.

## Claude Code

- CLI: installed, version `2.1.220`.
- Herdr integration: installed/current (v7).
- Authentication: verified on 2026-07-29. `claude auth status` reports
  `loggedIn: true`, method `claude.ai`, subscription `max`.
- Verified aliases: `fable`, `sonnet`, and `opus` each completed an isolated
  `claude -p` probe on 2026-07-29. Canonical IDs `claude-fable-5`,
  `claude-sonnet-5`, and `claude-opus-5` also completed live CLI probes. The
  installed CLI advertises these aliases and full names and supports efforts
  `low` through `max`.

| Alias | Canonical ID | Verified effort | Routed use |
|---|---|---:|---|
| `fable` | `claude-fable-5` | `low` | Claude coordinator alternative and lightweight bounded probes |
| `sonnet` | `claude-sonnet-5` | `medium` | Routine implementation |
| `opus` | `claude-opus-5` | `high` | Planning and independent review |

Claude is routable. Brida pins canonical IDs in its routing files so a future
Claude alias update cannot silently change the model. The active `claude`
coordinator uses `claude-fable-5` at `low`; implementation, planning, and
review deliberately retain the canonical Sonnet or Opus IDs where their higher
reasoning budget is warranted. Prefer Claude as an independent reviewer when
the implementer used Codex. Re-check `claude auth status` before a session that
depends on it, because authentication can lapse. The active local Claude
account route is `cld`/the standard `claude` CLI.

## Unavailable providers

The following CLIs were not found and must not be routed:

- Gemini
- Grok
- OpenCode
- Aider

## Routing policy

This table is selection guidance, not executable routing state. Change active
defaults in `config/model-routing.json`.

| Task | First choice | Escalate when |
|---|---|---|
| Fast repository inventory | Luna, `medium` | Findings require architectural inference |
| Routine implementation | Terra, `medium` | Cross-cutting design or repeated failure |
| Complex implementation | Sol, `high` | Only after scope and criteria are clear |
| Difficult root-cause debugging | Sol, `high` or `xhigh` | Reproduction is verified but cause remains unclear |
| Test/lint execution and summarization | Luna, `medium` | Failures require diagnosis |
| Independent code review | Different provider if verified; otherwise fresh Sol session | Security or production risk requires human review |
| Chief-of-Staff coordination | Terra, `medium` | Material strategy/architecture decision needs Sol or user |

Prefer one capable agent over several overlapping agents. A model change is not
a substitute for a better task packet.
