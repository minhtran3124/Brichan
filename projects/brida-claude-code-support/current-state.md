# Current state

- Status: recovery contract hardening, one bounded replacement pilot, and one
  equivalent Codex–Claude benchmark are complete.
- Claude Code 2.1.220 is authenticated and routable; Codex and Claude Herdr
  integrations are current.
- Required operational receipts use
  `projects/<slug>/handoffs/<task-id>/receipt.md` and are validated by
  `make check`.
- Concurrent writers require disjoint path ownership, dedicated branches and
  worktrees, parent/child receipts, and integrated review.
- `RECOVERY-001` added normalized structural anchors for escalation after retry
  exhaustion, no authority expansion, and preservation of original evidence.
  Commit `a9f30dc` passed three controlled policy mutations and independent
  Claude Opus review.
- `RECOVERY-002` recorded three consecutive idle/no-progress observations,
  preserved the original session before `stale` then `abandoned`, and used one
  replacement with the same plan, receipt, read-only scope, and ownership.
- First review found that attempt 2 lacked an explicit `replaced` lifecycle
  state. The coordinator recorded it at `72ed9c3`; focused re-review returned
  `PASS`.
- `BENCHMARK-001` gave Codex Terra and Claude Sonnet the same read-only audit at
  commit `323d546`. Codex scored 12/12 in 69 seconds and found the lifecycle
  defect; Claude scored 10/12 in 73 seconds and missed it.
- Per-task token and cost totals were not reliably observable and remain
  unavailable. The benchmark is one policy-audit sample, not a general model
  ranking.
- All Brida-owned worker panes and disposable worktrees from these tasks are
  closed or removed.

## Main gaps and risks

- Recovery anchors assert required sentence presence; additive contradictory
  prose could remain undetected.
- The real-policy reflow test can become vacuous after future literal drift and
  duplicates one authority-policy literal.
- The recovery pilot injected a deliberate 39-second stall, not a live provider
  or tool failure. Realistic stale timing remains untested.
- Receipt schema records attempt and prior session but has no dedicated
  lifecycle-state field; `replaced` currently relies on human-readable evidence.
- Receipt evidence quality remains reviewer-judged even though completeness and
  lifecycle transitions are machine-gated.
- Validator failure diagnostics can expose an absolute checkout path, and
  direct test imports assume repository-root cwd.
- One benchmark sample is insufficient to change global routing or estimate
  provider cost.

## Open questions

1. Should receipt schema version 2 add a machine-validated attempt lifecycle
   state such as `active`, `stale`, `abandoned`, or `replaced`?
2. What safe fault should a realistic recovery pilot inject without adding an
   automatic killer or broadening worker authority?
3. Which repeated task set and telemetry source can provide reliable token and
   cost comparisons across providers?

## Next actions

1. Design receipt schema version 2 with validated attempt lifecycle state.
2. Repeat the benchmark across implementation, debugging, and review tasks
   before changing model routing.
3. Run a bounded real tool-failure pilot after its fault and cleanup mechanism
   receive explicit acceptance criteria.
