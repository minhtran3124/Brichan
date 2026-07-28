# Setup status

This document is historical environment evidence, not normative policy.

Last checked: 2026-07-27.

| Step | Status | Evidence |
|---|---|---|
| 1. Operating contract | Complete | `docs/policy/identity.md`, `docs/policy/operating-principles.md` |
| 2. Identity and AGENTS | Complete | `AGENTS.md`, `docs/policy/identity.md` |
| 3. Progressive project memory | Complete | `docs/policy/memory-policy.md`, `projects/` |
| 4. Herdr integration | Complete | Herdr 0.7.3 running; Codex integration v6 current |
| 5. Model catalog | Complete | `codex debug models`; `docs/policy/model-catalog.md` |
| 6. Herdr-only workers | Complete | `.codex/config.toml`, `bin/brida`, `AGENTS.md`, skill |
| 7. Extra providers and reviewer | Complete for available environment | Reviewer ready; Claude auth unverified; Gemini/Grok absent |
| 8. Repository packaging | Complete | `README.md`, `Makefile`, CI, contribution/security policy, contract tests |

## Environment facts

- Codex CLI: `0.145.0`.
- Herdr: `0.7.3`, stable channel, compatible running server.
- Herdr Codex integration: current, v6.
- Herdr Claude integration: current, v7.
- Claude Code CLI: `2.1.220`, authentication not verified.
- Gemini/Grok/OpenCode/Aider: not found.

Do not mark an unavailable provider ready merely because its instruction exists.

Use `bin/brida` to start the coordinator. It explicitly disables both native
multi-agent feature variants even if project config discovery changes.

Run `make check` from the repository root before publishing or submitting
changes.
