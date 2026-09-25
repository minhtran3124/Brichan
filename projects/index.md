# Project index

## Brida installable repository tool
- Status: active
- Summary: `brichan` is published on PyPI with tag-triggered Trusted Publishing; installed mode mandates the plan/implement/review lifecycle, and external owner-repository dogfood is the open gate.
- Memory: projects/brida-installable-tool/

## Brida system validation
- Status: complete
- Summary: Local smoke tests for Brida orchestration and Herdr worker lifecycle.
- Memory: projects/brida-system-validation/

## Brida workflow evaluation
- Status: complete
- Summary: Independent evaluation of reviewer, token/context, metrics, and long-horizontal-task claims.
- Memory: projects/brida-workflow-evaluation/

## Brida Claude Code support
- Status: active
- Summary: Dual-runtime handoffs, isolated concurrent writers, canonical validated receipts, and bounded worker recovery are established.
- Memory: projects/brida-claude-code-support/

## Brida repository structure refactor
- Status: complete
- Summary: Plan a scalable modular repository layout, migration path, and multi-agent-safe operating contracts.
- Memory: projects/brida-repository-structure-refactor/

## Brida settings-driven model routing
- Status: complete
- Summary: Move coordinator and worker role model selection into validated repository settings with safe per-launch overrides.
- Memory: projects/brida-model-routing/

## Brida task dossier workflow
- Status: active
- Summary: Evaluate an adaptive per-task dossier spanning intake, exploration, design, planning, implementation, review, and ship evidence.
- Memory: projects/brida-task-dossier-workflow/

## Brida worker ledger and agent visibility
- Status: active
- Summary: Persist which agent (route, runtime, model, effort) did each task step, as the base for `brichan status` and a Herdr plugin monitor.
- Memory: projects/brida-worker-ledger/

## Brida Jev decision layer
- Status: proposed
- Summary: Evaluate TypeSafe's Jev decision model for worker tool-call gating, injection screening, and coordinator triage beside the frontier routes, starting with a shadow pilot.
- Memory: projects/brida-jev-decision-layer/

## Brida workflow simplification
- Status: proposed
- Summary: Risk-proportional lifecycle (lighter Level 0/1 ceremony, verification kept) and `claude-opus-5-5` evaluation, gated on a two-stage A/B.
- Memory: projects/brida-workflow-simplification/

## Entry template

```text
## <project-name>
- Status: proposed | active | blocked | paused | complete | archived
- Summary: <one sentence>
- Memory: projects/<slug>/
```
