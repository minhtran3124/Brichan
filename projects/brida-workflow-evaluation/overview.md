# Project overview

- Name: Brida workflow evaluation
- Slug: brida-workflow-evaluation
- Repository/path: repository root (`.`)
- Owner: Brida
- Lifecycle status: active
- Last verified: 2026-07-27

## Purpose

Produce objective, reproducible evidence for four workflow claims: independent
review, coordinator-context optimization, metrics tracking, and long-horizontal
task execution.

## In scope

- Read-only or local reversible eval artifacts.
- Independent Herdr workers with bounded task packets.
- Token, elapsed-time, quality, lifecycle, and cleanup measurements.

## Out of scope

- Provider pricing claims without verified pricing data.
- Production, deployment, publishing, destructive, or remote mutations.

## Stable constraints

- Answer keys are withheld from evaluated reviewers.
- Unknown cost or token data is recorded as unavailable, never estimated.
- Brida-created workers use `brida-` names and are the only panes Brida may close.

## Success measures

- Each of the four claims receives a PASS, PARTIAL, or FAIL verdict.
- Every verdict cites a rerunnable command or captured artifact.
- Limitations and counter-evidence are reported.
