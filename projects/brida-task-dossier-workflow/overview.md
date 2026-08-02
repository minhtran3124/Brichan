# Brida task dossier workflow

- Name: Brida task dossier workflow
- Slug: brida-task-dossier-workflow
- Repository/path: repository root (`.`)
- Owner: Brida
- Lifecycle status: proposed
- Last verified: 2026-08-02

## Purpose

Evaluate whether Brida should adopt an adaptive per-task dossier inspired by
the workflow `Intake → Brainstorm → Design → Plan → Implement → Review → Ship`,
including whether task artifacts should be grouped in one folder.

## In scope

- Fit with Brida's project memory, handoff receipts, reviewer policy, installed
  project state, and context-economy goals.
- Feasibility, risks, useful ideas, rejected ideas, and a phased plan.
- A lightweight path for simple tasks and a richer path for material tasks.

## Out of scope

- Implementing executable workflow automation in this research task.
- Changing canonical policy, public contracts, routing, or installed schema.
- Publishing, deployment, remote state, permission broadening, or secrets.

## Stable constraints

- Project memory remains selective and project-scoped.
- Worker lifecycles remain Herdr-only.
- Completion requires acceptance evidence, not document presence.
- Installed mode may write only inside its versioned managed state directory.
- No third-party Python runtime dependency.

## Success measures

- The screenshot proposal is mapped artifact-by-artifact to existing Brida
  primitives.
- The recommendation distinguishes mandatory, conditional, generated, and
  rejected artifacts.
- The plan has explicit evidence gates and avoids a second durable-memory truth
  system.
