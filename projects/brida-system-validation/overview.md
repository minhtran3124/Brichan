# Project overview

- Name: Brida system validation
- Slug: brida-system-validation
- Repository/path: repository root (`.`)
- Owner: Brida
- Lifecycle status: active
- Last verified: 2026-07-27

## Purpose

Verify that Brida can create, instruct, monitor, and safely close independent
worker sessions through Herdr.

## In scope

- Read-only orchestration smoke tests.
- Herdr and Codex integration health checks.

## Out of scope

- Product implementation.
- Remote, destructive, deployment, or publishing actions.

## Stable constraints

- Workers are independent main-agent sessions created through Herdr.
- Workers must not spawn or delegate to additional agents.
- Brida closes only panes created and recorded for this validation project.

## Success measures

- Herdr reports a compatible running server and current Codex integration.
- A `brida-` worker returns the expected smoke-test response.
- The worker pane is closed after evidence is collected.
