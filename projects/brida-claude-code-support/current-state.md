# Current state

- Status: receipt lifecycle schema v2 is implemented, migrated, mutation-tested,
  and independently reviewed `PASS`.
- Claude Code 2.1.220 is authenticated and routable; Codex and Claude Herdr
  integrations are current.
- Canonical receipts support schema v1 and v2. V2 separates immutable attempt
  origin from current lifecycle and validates prior state plus replacement
  evidence.
- `RECEIPT-V2-001` used Claude Opus planning, Codex Sol implementation, and
  Claude Opus review. Commits `843d3bf` and `7339415` implemented the validator
  and migrated three receipts.
- Initial review found a HIGH blank-schema bypass. Coordinator remediation
  `d788a8b` made unsupported-version handling unconditional and added blank and
  whitespace regression coverage; focused re-review returned `PASS`.
- All required tests pass: 53 focused tests, 10 metrics tests, 62 repository
  tests, and four canonical receipt validations.
- Concurrent-writer isolation, recovery pilots, and the first equivalent
  Codex–Claude policy benchmark remain complete.
- Per-task token and cost totals remain unavailable. One benchmark sample is
  not a general model ranking.
- All Brida-owned worker panes and disposable worktrees for completed tasks are
  closed or removed.

## Main gaps and risks

- Replacement receipts depend on the referenced evidence file continuing to
  exist; moving it can invalidate historical receipts.
- Evidence-path repo-root inference uses `projects_root.parent`, which is
  correct for repository checks but heuristic for custom roots.
- A missing schema line emits both missing-field and unsupported-version
  diagnostics; this is cosmetic.
- Schema-v1 compatibility intentionally leaves new v2-only attempt invariants
  unenforced.
- Recovery anchors can miss additive contradictory prose, and the controlled
  stall pilot was not a live provider or tool failure.
- Receipt evidence quality remains reviewer-judged even though completeness and
  lifecycle transitions are machine-gated.
- One benchmark sample is insufficient to change global routing or estimate
  provider cost.

## Open questions

1. Should historical replacement evidence be immutable or copied beside each
   canonical receipt to avoid path-existence coupling?
2. What safe fault should a realistic recovery pilot inject without adding an
   automatic killer or broadening worker authority?
3. Which repeated task set and telemetry source can provide reliable token and
   cost comparisons across providers?

## Next actions

1. Repeat equivalent Codex–Claude benchmarks for implementation and debugging
   tasks before changing model routing.
2. Design a bounded real tool-failure pilot with explicit fault injection and
   cleanup acceptance criteria.
3. Decide whether replacement evidence should be co-located or immutable before
   tightening evidence-path durability.
