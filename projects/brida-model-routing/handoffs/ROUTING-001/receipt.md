## Identity

- Receipt schema version: `2`
- Task ID: `ROUTING-001`
- Project: `brida-model-routing`
- Handoff timestamp (UTC): `2026-07-29T05:37:05Z`
- Receipt role: `standalone`
- Parent receipt path: `null`
- Attempt: `2`
- Replaces session: `brida-model-routing-impl / w1X:p2T`
- Attempt origin: `replacement`
- Attempt lifecycle state: `complete`
- Prior attempt state: `abandoned`
- Replacement evidence path: `projects/brida-model-routing/handoffs/ROUTING-001/attempt-1-recovery.md`

## Plan version

- Artifact or plan ID: `MODEL-ROUTING-P1`
- Version: `1`
- Status: `implemented`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `OpenAI` | `Codex coordinator` | `w1X:pA` | `019fac3c-177b-7061-9506-957ed48ccdd8` |
| Implementer | `OpenAI` | `gpt-5.6-sol, high` | `w1X:p2V` | `019fac63-cc79-78f0-ba10-f7977d3365eb` |
| Reviewer | `OpenAI` | `Codex coordinator` | `w1X:pA` | `019fac3c-177b-7061-9506-957ed48ccdd8` |

## Scope

- In scope: settings manifest, routing resolver, provider command translation,
  safe Herdr route launch, coordinator defaults, documentation, and tests
- Authorized paths: paths listed in `projects/brida-model-routing/plan.md`
- Exclusive write ownership: worker owns authorized implementation paths;
  Brida owns `projects/brida-model-routing/` and `projects/index.md`
- Branch: `feat/settings-driven-model-routing`
- Worktree: `main repository worktree`

## Non-goals

- Excluded work: automatic routing, credentials, billing, permission expansion,
  version release, deployment, and publication

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| `AC1` | `pass` | `config/model-routing.json` is the active source |
| `AC2` | `pass` | all four routes resolve from settings without prompt constants |
| `AC3` | `pass` | named route, dry-run, JSON, and legacy paths verified |
| `AC4` | `pass` | one-off precedence is implemented, tested, and documented |
| `AC5` | `pass` | strict schema and normalized provider argv guard invalid input |
| `AC6` | `pass` | native delegation disabling is injected and bypass-tested |
| `AC7` | `pass` | coordinator wrappers consume settings and preserve overrides |
| `AC8` | `pass` | focused/full/sandbox/real-runtime checks pass after remediation |

## Verification

| Command | Result |
| --- | --- |
| focused unit/integration/contract tests | `pass; final coordinator suite 66 tests` |
| `make check` | `pass; 58 unit, 37 contract, 21 integration` |
| isolated sandbox validation | `pass; fresh git-initialized copy and external venv` |
| real installed-runtime smoke | `pass; Codex 0.146.0, Claude 2.1.220, Herdr 0.7.3` |

## Implementation evidence

- Changed artifacts: routing manifest and resolver, provider adapters, Herdr
  launcher, coordinator wrappers, policy/docs, repository paths, and tests
- Diff evidence: `git diff --check` passes; provider adapter boundary and stale
  reference scans pass
- Test evidence: worker, coordinator, isolated sandbox, installed CLI parser,
  and real Herdr route evidence captured

## Review verdict

- Verdict: `pending`
- Findings: `pending`

## Risks and open decisions

- Risks: provider CLI semantics and legacy raw-command compatibility require
  careful validation
- Open decisions: `null`

## Cleanup status

- Brida-owned panes closed: `yes`
- Project memory updated: `yes`
