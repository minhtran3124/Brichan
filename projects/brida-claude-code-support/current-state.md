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
- New Claude workers launched through `bin/brida-herdr-agent-start` default to
  `--permission-mode auto`; explicit per-worker permission modes are preserved.
- `BENCHMARK-002` completed an equivalent implementation/debugging fixture:
  Codex Terra and Claude Sonnet both passed; tokens, cost, and independent
  elapsed time remain unavailable, so routing is unchanged.
- `PILOT-003` is complete: the control succeeded once; fresh treatment rerun
  `PILOT-003-T-R1` recorded one real task-local exit-42 fault followed by one
  successful retry, and independent Codex Terra re-review returned `PASS`.
- `PILOT-003-E` control passed: one task-local tool invocation returned exact
  success output with exit 0. The treatment worker also observed one real
  exit-42 fault and a successful retry, but the coordinator made a prohibited
  third post-run invocation. The treatment is `CHANGES REQUIRED`; it is not
  clean recovery evidence.
- `PILOT-003-T-R1` preserves raw worker output, byte-for-byte wrapper log, and
  pre-dispatch SHA-256/mode/target provenance. Its initial shell redirect was
  rejected before the tool ran; this is a non-blocking process-discipline risk.

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
2. Which larger repeated task set and telemetry source can provide reliable token and
   cost comparisons across providers?

## Next actions

1. Repeat `BENCHMARK-002` with more task instances before changing routing.
2. Decide whether replacement evidence should be co-located or immutable before
   tightening evidence-path durability.
