# Worker recovery

Use this policy when a Brida-owned worker appears blocked or stops making
progress.

## Evidence before stale status

Elapsed time alone never makes a worker stale. Record three consecutive
no-progress observations before assigning stale status. For each observation,
record its UTC timestamp, Herdr status, and relevant recent-output evidence.
An observation is no-progress only when the status and output show no material
advance toward the accepted task.

## Bounded replacement

The default retry limit is one replacement attempt. Preserve the original
session and pane evidence before replacement. The replacement must reuse the
accepted plan, canonical receipt, authorized scope, and write ownership.
Replacement does not grant broader permissions, authority, paths, or goals.

Record the original worker as `stale`, then `abandoned` when its attempt will
not resume. Record the new attempt as `replaced` and add replacement provenance
to its receipt. Do not rewrite or discard evidence from the original session.
In schema-v2 receipt vocabulary, `replacement` is the immutable attempt origin;
the current attempt lifecycle is recorded separately as `active`, `complete`,
`stale`, or `abandoned`.

## Escalation

Escalate after the one-replacement limit is exhausted. Escalate before retrying
when recovery would require any material authority, permission, scope,
ownership, architecture, or goal change. Do not implement an automatic timeout
killer, scheduler, or process termination policy from these rules.

## Cleanup

Close only panes that Brida created and recorded. Preserve the pane status,
recent-output evidence, task result, and replacement decision before cleanup.
Never close an unrelated pane.
