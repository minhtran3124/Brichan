# Brida task dossier workflow

- Name: Brida task dossier workflow
- Slug: brida-task-dossier-workflow
- Repository/path: repository root (`.`)
- Owner: Brida
- Lifecycle status: active
- Last verified: 2026-08-02

## Purpose

Operate and evaluate Brida's per-task dossier workflow inspired by
`Intake → Brainstorm → Design → Plan → Implement → Review → Ship`, with one
folder and one complete evidence set per task.

## In scope

- Fit with Brida's project memory, handoff receipts, reviewer policy, installed
  project state, and context-economy goals.
- Feasibility, risks, useful ideas, rejected ideas, and a phased plan.
- One full artifact set for every lane, with lane-specific evidence depth.
- Concise structured-record generation and deterministic read-only summaries.

## Out of scope

- Changing model routing as part of dossier generation or summary behavior.
- Installed-mode dossier generation or schema changes.
- Publishing, deployment, remote state, permission broadening, or secrets.

## Stable constraints

- Project memory remains selective and project-scoped.
- Worker lifecycles remain Herdr-only.
- Completion requires acceptance evidence, not document presence.
- Installed mode may write only inside its versioned managed state directory.
- No third-party Python runtime dependency.
- Generator and summary code remain route-neutral and checkout-only.
- The existing validator remains the sole authority for dossier validity.

## Success measures

- The screenshot proposal is mapped artifact-by-artifact to existing Brida
  primitives.
- The recommendation distinguishes mandatory, conditional, generated, and
  rejected artifacts.
- The plan has explicit evidence gates and avoids a second durable-memory truth
  system.
