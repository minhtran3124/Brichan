# CONCURRENT-001 accepted plan

- Plan ID: `CONCURRENT-001-P1`
- Version: `1`
- Status: `accepted`
- Accepted at: `2026-07-28T04:50:31Z`
- Planning session: Claude Opus, Brida-owned pane `w1X:p1H`
- Original baseline: `2fc8a847f2e5169cb4c6dd1f72a1f8637f84ebb2`

## Objective

Encode the approved mandatory-receipt and concurrent-writer policy, then
validate it with two Codex writers operating concurrently from the same
dispatch baseline.

## Writer A

Authorized paths:

- `.agents/skills/herdr-orchestration/SKILL.md`
- `.agents/skills/herdr-orchestration/references/task-packet.md`
- `.agents/skills/herdr-orchestration/references/handoff-receipt.md`
- `.agents/skills/herdr-orchestration/references/concurrent-writers.md`

Writer A owns policy and reference documentation only.

## Writer B

Authorized paths:

- `tests/test_concurrency_contract.py`
- `tests/test_repository_contract.py`

Writer B owns test coverage only. No edit to
`tests/test_repository_contract.py` is required unless a verified collection
or compatibility issue makes it necessary.

## Integration ownership

Brida owns receipts, project memory, changelog, metrics, project index, version
metadata, and all Agent Harness paths. Writer path sets must not overlap.

## Acceptance

- Both writer branches descend from one dispatch baseline.
- Writer diffs have no intersecting paths and remain inside their authorization.
- Writer A remains green against the pre-existing suite.
- Writer B compiles and fails only through intentional policy-anchor assertions
  before Writer A is integrated.
- Integration is conflict-free and `make check` plus `git diff --check` pass.
- Parent and child receipts cross-link and contain no personal paths.
- An independent reviewer returns `PASS` on the integrated state.
