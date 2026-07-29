## Identity

- Receipt schema version: `2`
- Task ID: `ROUTING-FIX-001`
- Project: `brida-model-routing`
- Handoff timestamp (UTC): `2026-07-29T06:20:38Z`
- Receipt role: `standalone`
- Parent receipt path: `null`
- Attempt: `1`
- Replaces session: `null`
- Attempt origin: `initial`
- Attempt lifecycle state: `complete`
- Prior attempt state: `null`
- Replacement evidence path: `null`

## Plan version

- Artifact or plan ID: `MODEL-ROUTING-P1`
- Version: `2`
- Status: `implemented`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `OpenAI` | `Codex coordinator` | `w1X:pA` | `019fac3c-177b-7061-9506-957ed48ccdd8` |
| Implementer | `OpenAI` | `gpt-5.6-terra, medium` | `w1X:p2Y` | `019fac8c-7331-7942-a88a-5ad04fa05724` |
| Reviewer | `Anthropic` | `Claude Opus 5, high` | `closed w1X:p2X` | `902bdb91-7cee-4296-b8ae-c5f248336c55` |

## Scope

- In scope: plan version 2 review remediation and regression tests
- Authorized paths: version 2 paths listed in
  `projects/brida-model-routing/plan.md`
- Exclusive write ownership: worker owns authorized implementation paths;
  Brida owns project memory and receipts
- Branch: `feat/settings-driven-model-routing`
- Worktree: shared feature-branch repository worktree

## Non-goals

- Excluded work: project memory, model compatibility catalog, credentials,
  deployment, publication, commits, pushes, and pull requests

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| `AC1` | `pass` | provider command relocation preserves the manifest as active source |
| `AC2` | `pass` | four configured routes resolve and real CLI parsers accept commands |
| `AC3` | `pass` | named, dry-run, JSON, and legacy paths pass integration tests |
| `AC4` | `pass` | precedence behavior remains covered and documented |
| `AC5` | `pass` | separated, equals, and attached Codex forms are normalized before guards |
| `AC6` | `pass` | Codex disables remain enforced and Claude uses attached deny before passthrough |
| `AC7` | `pass` | coordinator adapters and invalid manifest/env cases pass |
| `AC8` | `pass` | focused, full, isolated sandbox, receipt, path, and real CLI checks pass |

## Verification

| Command | Result |
| --- | --- |
| focused remediation tests | `pass; 66 tests` |
| `make check` | `pass; 58 unit, 37 contract, 21 integration` |
| `git diff --check` | `pass` |

## Implementation evidence

- Changed artifacts: provider commands moved to `src/brida/cli/`; launcher,
  wrappers, policy, path registry, and focused tests updated
- Diff evidence: stale provider-module and dead-helper scans have no matches
- Test evidence: worker and coordinator focused/full suites pass; coordinator
  fresh git-initialized sandbox and installed CLI parser smokes pass

## Review verdict

- Verdict: `pending`
- Findings: pending fresh independent review; prior required findings have
  regression coverage

## Risks and open decisions

- Risks: provider CLI equivalent spellings must remain synchronized with
  installed provider behavior
- Open decisions: model existence compatibility remains intentionally dynamic

## Cleanup status

- Brida-owned panes closed: `yes`
- Project memory updated: `yes`
