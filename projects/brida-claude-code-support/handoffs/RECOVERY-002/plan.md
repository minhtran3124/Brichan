# RECOVERY-002 plan

- Plan ID: `RECOVERY-002-P1`
- Version: `1`
- Status: `accepted`
- Objective: exercise the bounded stale-worker and one-replacement policy
  without changing code or terminating a process automatically.

## Scope

- Give the original read-only worker a controlled stall checkpoint before it
  begins the evidence task.
- Record three consecutive no-progress observations with UTC timestamp, Herdr
  status, and recent-output evidence.
- Preserve the original session evidence, mark it `stale` then `abandoned`, and
  launch exactly one replacement.
- Give the replacement the same plan, canonical receipt, read-only scope, and
  no write ownership.
- Have the replacement verify the recovery guarantees in repository files.

## Evidence task

Report file/line and command evidence for:

1. the required three-observation stale threshold;
2. the one-replacement default and escalation after exhaustion;
3. replacement scope/authority and original-evidence preservation.

## Exclusions

- No repository writes by either worker.
- No automatic timeout killer, scheduler, process termination, permission
  broadening, deployment, publication, or remote action.
- No second replacement.

## Acceptance criteria

1. Three consecutive evidenced no-progress observations are recorded.
2. Original evidence is preserved before the worker becomes `abandoned`.
3. The replacement reuses this plan, receipt, scope, and ownership.
4. The replacement returns verified evidence for all three evidence questions.
5. The one-replacement limit is respected and all Brida-owned panes are closed.
