# Current state

- Status: concurrent two-writer pilot complete and independently reviewed.
- Claude Code 2.1.220 is authenticated and routable; Herdr reports Claude
  integration v7 as current.
- Brida has validated two sequential workflows using Claude Opus planning,
  Codex Terra implementation, and fresh Claude Opus review.
- Receipt schema version 1 now carries parent/child role, parent path, exclusive
  ownership, branch, and worktree fields while preserving its protected
  headings and hygiene guards.
- Receipts are mandatory for accepted-plan handoffs and multi-writer tasks.
  Task packets declare `mandatory` or `not-required`; the upstream block remains
  optional only when neither trigger applies.
- `PILOT-002` filled a real receipt under
  `evals/mixed-provider-coding/PILOT-002/`; a fresh reviewer found it through
  `projects/index.md` → project memory → `references.md` without chat history.
- Both hardening and `PILOT-002` initially received `CHANGES REQUIRED` for
  weak test assertions. Minimal remediations were mutation-tested and both
  final reviews returned `PASS`.
- `CONCURRENT-001` ran two Codex Terra writers concurrently from dispatch SHA
  `83c713e` in separate worktrees. Their committed path sets had an empty
  intersection and integrated without Git conflicts.
- Integration exposed two exact-anchor line-wrap failures. Both were returned
  to Writer A for owner-scoped remediation before the full suite passed.
- Latest validation: 10 metrics tests and 30 tests-directory tests pass;
  11 committed metrics rows are valid and `git diff --check` is clean.

## Main gaps and risks

- Receipt storage under `evals/mixed-provider-coding/<pilot-id>/` is validated
  for pilots but not yet adopted as a general project contract.
- Receipts remain Markdown-only; no machine-enforced lifecycle state, retry
  limit, stale-worker rule, or receipt completeness validator exists.
- Optional test hardening remains for exact heading cardinality, table shape,
  tilde-style home paths, and label-to-section anchoring.
- Exact string anchors can create integration failures from harmless Markdown
  wrapping; integrated tests remain necessary even when each shard meets its
  local gate.
- Initial independent review returned `CHANGES REQUIRED` for a committed-metrics
  count mismatch and missing integrated cherry-pick SHAs in receipts. Both
  evidence defects were remediated at `c2413fe`; mutation-tested re-review
  returned `PASS`. Long policy lines remain a non-blocking design risk.
- Model quality, latency, token, and cost comparisons remain unbenchmarked where
  observations were unavailable.

## Open questions

1. Should required receipts move from evaluation storage to a canonical
   `projects/<slug>/handoffs/` location after pilot review?
2. Should receipt completeness become a machine-enforced completion gate?
3. Should exact policy anchors be normalized structurally rather than bound to
   Markdown line wrapping?

## Next actions

1. Decide the canonical non-evaluation storage contract for required receipts.
2. Design a receipt completeness validator and stale-worker/retry policy.
3. Replace line-wrap-sensitive exact policy anchors with structural checks.
