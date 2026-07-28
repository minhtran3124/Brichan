# RECOVERY-001 plan

- Plan ID: `RECOVERY-001-P1`
- Version: `1`
- Status: `accepted`
- Objective: protect the three remaining worker-recovery guarantees with
  line-wrap-tolerant structural contract checks.

## Scope

- Modify only `tests/test_concurrency_contract.py`.
- Anchor escalation after the retry limit, no authority expansion, and
  preservation of original worker evidence.
- Make the reflow-tolerance test exercise a real policy anchor from
  `worker-recovery.md`.

## Exclusions

- No production runtime, scheduler, timeout killer, or automatic termination.
- No edits to recovery policy prose, receipt validator, project memory,
  configuration, or historical evaluations by the implementation worker.

## Acceptance criteria

1. Each of the three recovery guarantees has a normalized structural assertion.
2. The reflow test reads a shipped policy anchor and still rejects a semantic
   weakening.
3. The focused concurrency tests and full `make check` pass.
4. An independent reviewer verifies scope, mutation sensitivity, and clean
   restoration.

## Escalation

Escalate if satisfying the tests requires changing the policy meaning or any
path outside the single authorized test file.
