# Project overview

- Name: Brida worker ledger and agent visibility
- Slug: brida-worker-ledger
- Repository/path: repository root (`.`)
- Owner: Brichan
- Lifecycle status: active
- Last verified: 2026-09-21

## Purpose

Make Brichan's multi-agent value visible: a user should be able to see which
coding agent (route, runtime, model, effort) did which part of a task, and what
each step produced. The first step is a machine-written worker ledger; later
steps build a `brichan status` view and a Herdr plugin monitor pane on top of it.

## In scope

- WLG-001: a persisted per-worker launch/finish ledger written by the core
  package, with no change to receipt or metrics schemas.

## Out of scope

- The Herdr plugin itself, `brichan status`, finding-to-worker attribution,
  and metrics schema changes (later tasks, each needing its own approval).
- Publishing to the Herdr plugin marketplace (remote state change).

## Architecture

The core `brichan` package stays the single source of logic. The ledger is
written at the one launch hook point (`brichan-herdr-agent-start`) and, when
observed, at worker completion (`brichan-herdr-agent-observe`). Any plugin is a
thin adapter that calls core CLI commands.

## Stable constraints

- Standard library only; Python 3.10+.
- Unavailable values are `null`, never estimated.
- A ledger write failure must never fail or roll back a worker launch.
- Installed `.brichan/` schema v1 is migration-free; any new state path must
  keep existing projects healthy.

## Success measures

- Every routed launch produces one durable ledger record with route, runtime,
  model, effort, pane, and timestamp.
- `make check` passes; no existing project becomes unhealthy.
