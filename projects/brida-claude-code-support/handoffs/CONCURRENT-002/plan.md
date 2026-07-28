# CONCURRENT-002 accepted plan

- Plan ID: `CONCURRENT-002-P1`
- Version: `1`
- Status: `accepted`
- Accepted at: `2026-07-28T05:23:11Z`
- Implementation mode: `single writer`

## Objective

Productionize required receipts in one bounded implementation task: adopt a
canonical progressive-disclosure location, add machine completeness checks,
replace line-wrap-sensitive policy tests, and document stale-worker and retry
handling.

## Authorized implementation paths

- `.agents/skills/herdr-orchestration/SKILL.md`
- `.agents/skills/herdr-orchestration/references/handoff-receipt.md`
- `.agents/skills/herdr-orchestration/references/task-packet.md`
- `.agents/skills/herdr-orchestration/references/concurrent-writers.md`
- `.agents/skills/herdr-orchestration/references/worker-recovery.md`
- `scripts/validate_handoff_receipts.py`
- `tests/test_handoff_receipt_validator.py`
- `tests/test_concurrency_contract.py`
- `Makefile`

The canonical plan, receipt, project memory, changelog, metrics, and project
index remain Brida-owned integration artifacts.

## Required behavior

1. Discover canonical receipts only at
   `projects/<slug>/handoffs/<task-id>/receipt.md`.
2. Support `standalone`, `parent`, and `child` receipt roles with coherent
   parent-path rules.
3. Validate schema version, identity, accepted plan, bounded scope, acceptance
   rows, verification evidence, implementation evidence, verdict, and cleanup
   according to `accepted`, `implemented`, and `reviewed` lifecycle states.
4. Return nonzero with actionable file-and-field diagnostics for invalid
   receipts; never mutate a receipt.
5. Run the validator from `make check` without third-party dependencies.
6. Replace exact raw-string policy assertions with whitespace-normalized or
   structural checks, then reflow policy prose without weakening semantics.
7. Define stale detection from three consecutive evidenced no-progress
   observations, not elapsed time alone. Permit one replacement attempt by
   default, preserve the original session evidence, forbid scope expansion, and
   escalate after the retry limit or any material authority change.

## Acceptance criteria

- The accepted `CONCURRENT-002` receipt validates before implementation.
- Focused tests cover valid lifecycle states and failures for missing fields,
  invalid role/parent topology, incomplete review, failed cleanup, and unsafe
  personal paths.
- Structural policy tests detect semantic removal while allowing harmless line
  wrapping.
- New policy prose has no newly introduced line over 100 characters outside
  tables or frontmatter.
- `make check` and `git diff --check` pass.
- The writer changes and commits only authorized paths.
- An independent reviewer mutation-tests at least one validator gate and one
  normalized policy assertion.

## Non-goals

- No runtime scheduler, automatic worker termination, deployment, provider
  change, Agent Harness change, or migration of historical evaluation receipts.
