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
- Latest independent review at `5dfcfb8` passed 10 metrics tests and 48
  tests-directory checks, validated one canonical receipt, and left
  `git diff --check` clean.
- `CONCURRENT-002-P1` completed as one single-writer hardening task covering
  canonical receipt storage, completeness validation, structural policy tests,
  and stale-worker/retry rules. Implementation commit `71e3d9d` received an
  independent Claude Opus `PASS` after two controlled mutations and 40
  read-only parser probes.
- All Brida-owned `CONCURRENT-002` worker panes are closed, the disposable
  review worktree is removed, and 12 workflow metrics rows are committed.

## Main gaps and risks

- Historical pilot receipts remain under `evals/mixed-provider-coding/`; new
  operational receipts use the canonical project handoff path.
- Receipts remain Markdown, but canonical receipts now have a machine-enforced
  completeness and lifecycle gate. The validator deliberately cannot judge
  the semantic quality of short evidence values.
- Recovery-policy tests do not yet structurally anchor escalation after retry
  exhaustion, no-authority-expansion, or original-evidence preservation.
- The structural reflow helper is tested with inline literals rather than a
  shipped policy anchor.
- Validator failure diagnostics can expose an absolute checkout path on the
  console, and direct test-module imports assume the repository-root cwd.
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

1. Should the three unprotected worker-recovery guarantees become mandatory
   structural anchors before the first fault-recovery pilot?
2. Should validator diagnostics be repo-relative to avoid printing local
   checkout paths?
3. Should receipt evidence quality gain stronger semantic validation, or remain
   a reviewer responsibility?

## Next actions

1. Add structural anchors for recovery escalation, authority boundaries, and
   evidence preservation.
2. Run a controlled stale-worker/replacement pilot using the canonical receipt.
3. Compare mixed-provider quality, latency, token use, and cost on equivalent
   tasks once those observations are available.
