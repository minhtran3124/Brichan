# PILOT-003 plan

## Objective

Design a bounded real tool-failure recovery pilot that injects a reversible,
observable tool fault and proves cleanup through a written contract.

## Required design outputs

- Exact fault-injection point and trigger, with no process killer or broad
  permission increase.
- Control and treatment sequence, stop conditions, evidence capture, and
  rollback/cleanup steps.
- Cleanup contract with pre/post invariants, ownership, timeout/escalation, and
  acceptance tests.
- Risks, user decisions, and what remains unverified until execution.
