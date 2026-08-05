# Model catalog

This is the canonical Brichan runtime capability and model-routing guidance
catalog. Active coordinator and worker route defaults live only in
`../../config/model-routing.json`. This file describes provider and model
capabilities only; it must not restate which route or coordinator currently
uses which model, so a routing change never requires editing this file.

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
Luna supports through `max`. Brichan must not choose `ultra` for workers because
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

| Alias | Canonical ID | Verified effort | Suggested uses |
|---|---|---:|---|
| `fable` | `claude-fable-5` | `low` | Complex planning, architectural reasoning, coordination, final review |
| `opus` | `claude-opus-5` | `high` | Complex implementation, difficult debugging |
| `sonnet` | `claude-sonnet-5` | `medium` | Repository scanning, summaries, routine implementation |

Claude is routable. Brichan pins canonical IDs in its routing files so a future
Claude alias update cannot silently change the model. Re-check
`claude auth status` before a session that depends on it, because
authentication can lapse. The active local Claude account route is `cld`/the
standard `claude` CLI. When the active manifest places review on the same
provider or model as the implementer or coordinator, the independence rules in
[reviewer policy](reviewer.md) still apply.

## OpenCode

- CLI: installed, version `1.18.12` (verified 2026-08-04).
- Routable as a Stage 1 guarded, checkout-oriented coordinator and worker only.
  Installed-project targets are out of scope.
- The version is pinned exactly. The isolation contract is source-line specific
  against this release and its pinned `yargs` dependency, so any upgrade
  re-opens the isolation review before the pin moves.
- Herdr integration: the Herdr plugin does not load under `--pure`, so worker
  state falls back to the screen manifest and is coarser than Codex or Claude
  worker state.
- Model and variant are pinned onto a single guarded primary agent; all five
  built-in primaries are disabled. Variant validation is syntactic only: only
  locally verified `opencode-go/gpt-5.6-luna` variants are documented, and
  Brichan does not verify that a provider accepts a given variant for a given
  model.
- Repository trust boundary: exactly one absolute `AGENTS.md` path plus the
  project `herdr-orchestration` skill are treated as user-authorized repository
  input. Every other skill is denied and the global configuration roots are
  hidden.

| Model | Verified variants | Suggested uses |
|---|---|---|
| `opencode-go/gpt-5.6-luna` | `low` through `max` | Guarded Stage 1 coordinator and worker sessions in the Brichan source checkout |

## Unavailable providers

The following CLIs were not found and must not be routed:

- Gemini
- Grok
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
