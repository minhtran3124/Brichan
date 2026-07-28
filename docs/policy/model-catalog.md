# Model catalog

This is the canonical Brida runtime and model-routing catalog.

Last verified: 2026-07-28.

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

| Model | Verified catalog description | Default effort | Brida routing |
|---|---|---:|---|
| `gpt-5.6-sol` | Latest frontier agentic coding model | `low` | Complex architecture, difficult debugging, high-risk implementation, final review |
| `gpt-5.6-terra` | Balanced model for everyday agentic coding | `medium` | Default coordinator/worker, normal implementation, structured research |
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
- Authentication: verified outside the restricted sandbox on 2026-07-28.
  `claude auth status` reports
  `loggedIn: true`, method `claude.ai`, subscription `max`.
- Verified models: `opus` resolved to `claude-opus-5` in an observed headless
  run; `sonnet` resolved to Sonnet 5 in observed Herdr worker sessions. `fable`
  is accepted by the CLI but has not been exercised.

Claude is routable. Prefer it as an independent reviewer when the implementer
used Codex. Re-check `claude auth status` before a session that depends on it,
because authentication can lapse.

### Temporary Edgeful Claude route

The user authorized the interactive `cld-edgeful` alias as a temporary Claude
worker route on 2026-07-28 after the default Claude subscription reached its
limit. It uses a separate authenticated Edgeful team configuration and enables
Claude's bypass-permissions mode.

This authorization is narrow: launch it only as a Brida-owned Herdr worker,
disable the `Task` tool, give it a bounded task packet, and preserve normal
receipt, evidence, and pane-cleanup requirements. Do not interpret the alias as
general permission to broaden task scope or perform remote/destructive actions.

## Unavailable providers

The following CLIs were not found and must not be routed:

- Gemini
- Grok
- OpenCode
- Aider

## Routing policy

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
