# Current state

- Status: receipt lifecycle schema v2 is implemented, migrated, mutation-tested,
  and independently reviewed `PASS`.
- `EVWAIT-001` (2026-10-05, branch `feat/herdr-agent-watch`, commits
  `746f82e` and `6882121`, not pushed): `brichan-herdr-agent-observe watch`
  streams worker state transitions as JSON lines for the Claude Code Monitor
  tool, so a Claude coordinator waits without a model turn per 30 s wait.
  Review `PASS` (5 Lows, fixed).
- `EVWAIT-002` (2026-10-05, same branch, commits `8481c45` and `7b6ed28`):
  `watch --source auto` (default) receives state changes pushed by Herdr
  `events.subscribe`, verified live on 0.9.1, and falls back to the
  EVWAIT-001 wait loop. Review v1 CHANGES REQUIRED (2 Medium, 2 Low) fixed;
  re-review v2 `PASS`. Not probed: a Herdr server restart. Codex still has a
  pending CLI update, so both reviews ran on Claude Fable 5.
- Claude Code 2.1.296 is authenticated and routable; Codex is not installed,
  so recent reviews run same-provider on Claude Fable 5.
- Checkout guardrails on `main` (2026-10-12): launches and `.claude/settings.json`
  deny `Agent`, `Task`, `Workflow`, `CronCreate`, `RemoteTrigger`; the hook
  asks before Bash starts `claude`/`codex` (`CLAUDE-007`–`CLAUDE-009`).
- Canonical receipts support schema v1 and v2. V2 separates immutable attempt
  origin from current lifecycle and validates prior state plus replacement
  evidence.
- `RECEIPT-V2-001` used Claude Opus planning, Codex Sol implementation, and
  Claude Opus review. Commits `843d3bf` and `7339415` implemented the validator
  and migrated three receipts.
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

1. Resume `CLAUDE-010` (research item M1, level 2) after the weekly usage
   reset on 2026-10-14, paused by the user on 2026-10-12: run a fresh plan
   re-review of `CLAUDE-010-P1` v3 (`claude-fable-5` `xhigh`), then accept the
   plan, write the receipt, implement, and code review. Branch
   `feat/protect-secrets-and-guardrails`; dossier
   `projects/brida-claude-code-support/handoffs/CLAUDE-010/`.
2. Fix the redirect false positive in `.claude/hooks/block_native_delegation.py`:
   `2>/dev/null` or `2>&1` makes `claude --version` ask, which stalls Herdr
   workers (seen 2026-10-12 in the `CLAUDE-010` plan review). Separate task.
3. Repeat `BENCHMARK-002` with more task instances before changing routing.
4. Decide whether replacement evidence should be co-located or immutable before
   tightening evidence-path durability.
