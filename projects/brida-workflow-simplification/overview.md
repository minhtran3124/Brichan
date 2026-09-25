# Project overview

- Name: Brida risk-proportional workflow simplification
- Slug: brida-workflow-simplification
- Repository/path: repository root (`.`)
- Owner: Brichan
- Lifecycle status: proposed
- Last verified: 2026-09-25

## Purpose

Cut ceremony and handoffs that do not buy quality at low risk, while keeping
every verification step that does, now that stronger worker models
(`claude-opus-5-5`) are available. The change is adopted only if a measured
A/B shows no quality loss.

## In scope

- Level 0: one `implement` worker that writes its own short plan in the
  receipt, `make check`, and code review only when the diff touches a
  contract path; three dossier artifacts (request, receipt, evidence).
- Level 1: plan and implement merged into one worker; plan-review dropped;
  independent code review kept.
- Evaluating `claude-opus-5-5` for the `plan` and `implement` routes.
- The A/B protocol in `evals/workflow-simplification/protocol.md`.

## Out of scope

- Level 2 lifecycle: unchanged.
- Evidence before completion, durable memory, the Herdr lifecycle, the
  stdlib-only rule, reviewer independence for material changes: unchanged.
- Any policy, routing, or packaged-resource edit before the A/B passes and the
  user accepts the decision.

## Architecture

Policy-level change only: `docs/policy/operating-principles.md`, the packaged
`src/brichan/resources/dogfood_v1/policy/operating-principles.md`,
`docs/workflows/task-dossier.md`, the `herdr-orchestration` skill, and
`config/model-routing.json`. No new module is planned.

## Stable constraints

- Installed-mode "plan -> implement -> review for every change" is a durable
  contract (PRODUCT.md §6.2); relaxing it needs user sign-off and independent
  review.
- Measurements are observed only; `null` when unavailable.
- A model enters routing only after a catalog entry with a verification date.

## Success measures

- A/B arm B has no more escaped defects than arm A and passes `make check`
  on every task.
- Arm B uses fewer workers, handoff blockers, and dossier lines per task.
