# Brida settings-driven model routing

- Name: Brida settings-driven model routing
- Slug: `brida-model-routing`
- Repository/path: Brida repository root
- Owner: Brida
- Lifecycle status: complete
- Last verified: 2026-07-29

## Purpose

Move active coordinator and Herdr worker model selection out of prompts,
instructions, and hand-written commands into validated repository settings.

## In scope

- A dependency-free, machine-readable routing manifest.
- Named worker routes including plan, implement, review, and scan.
- Coordinator defaults for Codex and Claude.
- Settings resolution, safe one-off overrides, command construction, and
  pre-spawn validation.
- Documentation, compatibility behavior, and layered automated tests.
- Isolated sandbox and real installed-runtime smoke validation.

## Out of scope

- Automatic task classification or provider selection without a named route.
- Native Codex subagents or Claude background/native delegation.
- Secrets, provider credentials, billing, deployment, or production changes.
- Release/version publication.

## Architecture

Repository settings are the source of truth for active defaults. Importable
orchestration code validates and resolves a named route, then provider adapters
translate the resolved runtime, model, and effort into native CLI arguments.
Security and orchestration guardrails remain code-enforced and cannot be
weakened by routing settings.

## Stable constraints

- Python 3.10+ with no runtime dependencies.
- Herdr remains the only worker-control plane.
- Worker reasoning effort `ultra` is forbidden.
- Settings cannot contain arbitrary argv or permission-bypass controls.
- Existing explicit worker commands remain compatible during migration.

## Success measures

- Changing settings changes resolved planner/implementer commands without
  editing prompts or policy instructions.
- Invalid routes fail before Herdr mutates pane state.
- Existing and new automated checks pass.
- Real Codex and Claude command resolution is verified in an isolated sandbox.
