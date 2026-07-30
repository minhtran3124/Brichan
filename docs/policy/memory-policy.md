# Project memory policy

This is the canonical Brichan project-memory policy.

## Read progressively

1. Read `projects/index.md` to locate the project.
2. Read `overview.md` and `current-state.md`.
3. Read `tasks.md` when planning or coordinating work.
4. Read `decisions.md` only when a past trade-off affects the current request.
5. Read `references.md` only when evidence or external context is needed.

Do not load every project or every history file.

## Write selectively

- Update `index.md` when a project is created, renamed, archived, or changes
  lifecycle state.
- Update `overview.md` only for stable facts: purpose, scope, architecture, and
  constraints.
- Replace stale information in `current-state.md`; do not append a diary.
- Append to `decisions.md` only for durable decisions with rationale.
- Update `tasks.md` when ownership or task state changes.
- Add pointers to `references.md`; do not paste large source documents.

## Size targets

- Project entry in `index.md`: at most three lines.
- `overview.md`: target under 120 lines.
- `current-state.md`: target under 80 lines.
- Active section of `tasks.md`: target under 30 tasks.
- Decision entry: target under 12 lines.

When a file exceeds its target, archive obsolete detail before adding more.

## Evidence and uncertainty

Mark unverified claims as `Unverified`. Include dates for time-sensitive facts.
Never convert a worker's assertion into durable memory until Brichan has checked
the relevant evidence.
