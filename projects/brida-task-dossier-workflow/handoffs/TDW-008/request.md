# Request provenance

Redacted, read-only record of the originating request. Amendments are recorded as a new artifact version, never by rewriting history.

## Artifact metadata

- Task ID: `TDW-008`
- Task level: `2`
- Artifact: `request`
- Artifact version: `1`
- Origin: `user-request`
- Owner: `coordinator`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fbffa-7c8c-7eb1-b03a-fe86208bd015`
- Effective route: `coordinator`
- Effective model: `gpt-5.6-sol`
- Effective effort: `medium`
- Reviewing session: `null`
- Review verdict: `null`

## Request provenance

- Redaction applied: `yes`
- Mutability: `immutable`

## Claim or decision

The redacted originating request requires a high-risk lane sample to exercise
the full-document workflow and produce evaluation evidence, while remaining a
safe local simulation.

## Evidence

- `task-packet.md` records the four fail-closed release-policy guards, isolated path, and explicit prohibition on real release activity.
- `requirements.md` records deterministic, input-immutable, no-ambient-state behavior and Level 2 acceptance criteria.
- `design.md` records the threat model, authorization boundary, stop conditions, isolation strategy, and rollback.

## Uncertainty

- No unresolved request-provenance uncertainty remains; the simulation does not claim to represent production authorization complexity.
