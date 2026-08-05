# Brida OpenCode support

- Name: Brida OpenCode support
- Slug: `brida-opencode-support`
- Repository/path: repository root (`.`)
- Owner: Brichan
- Lifecycle status: active
- Last verified: 2026-08-04

## Objective

Add OpenCode as an explicit checkout coordinator runtime and as a guarded
independent Herdr worker runtime, with behavior comparable to the existing
Codex and Claude Code adapters.

## In scope

- Checkout runtime selection and an OpenCode launcher/adapter.
- Settings-driven OpenCode coordinator and worker routes.
- Provider-native model and reasoning-variant translation.
- Herdr lifecycle integration and resumable OpenCode worker evidence.
- Runtime guards that disable native subagents, auto-approval, automatic
  sharing, automatic updates, and unsafe configuration overrides.
- Unit, contract, integration, documentation, and independent review evidence.

## Out of scope

- Installed-project OpenCode support.
- Changing the four active named routes to OpenCode before dogfood evidence.
- Publishing, deployment, remote changes, or provider credential changes.
- Modifying user-owned global OpenCode configuration beyond the already
  authorized Herdr integration installation.

## Stable constraints

- Herdr remains the only worker control plane.
- Workers are independent main-agent sessions and may not spawn subagents.
- Existing Codex and Claude Code behavior must remain compatible.
- Python 3.10+ and no new runtime dependencies.
- Permission, sharing, and configuration bypasses fail before Herdr mutation.

## Success measures

- `bin/brichan --runtime opencode` resolves a guarded OpenCode coordinator.
- Named and legacy worker paths support guarded OpenCode commands.
- A live bounded OpenCode worker reports lifecycle state through the current
  Herdr plugin and returns acceptance evidence.
- Complete repository checks and independent plan/code reviews pass.
