# Task dossier and receipt rules

## Rule metadata

- Context ID: `policy-dossiers`
- Reviewed on: `2026-08-26`
- Review within days: `180`
- Deprecated: `no`
- Evidence: `docs/workflows/task-dossier.md`; `docs/policy/memory-policy.md`

## Scope

- Applies to every durable artifact under projects/.

## Rules

- `DOSSIER-001`: Every tracked task links one canonical receipt at projects/PROJECT/handoffs/TASK/receipt.md, with PROJECT and TASK the project slug and task ID, that validates under schema version 2.
- `DOSSIER-002`: Quote the two path prefixes the home-path contract scan looks for bare, never with a trailing slash, in any artifact under projects/.
- `DOSSIER-003`: Archived plan versions under a task's handoffs versions directory are byte-frozen review evidence and are never edited.
- `DOSSIER-004`: Correct an evidence file in place; never append a later section that contradicts an earlier one.

## Overrides

- None.

## Verification

- make receipts, make dossiers, and make memory-check pass.

## Exceptions

- None.

## Examples

None.
