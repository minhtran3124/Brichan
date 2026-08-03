# Request provenance

Redacted, read-only record of the originating request. Amendments are recorded as a new artifact version, never by rewriting history.

## Artifact metadata

- Task ID: `TDW-007`
- Task level: `1`
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

The redacted originating request requires a runnable normal-lane requirements
sample after implementation, exercised through the complete workflow and
evaluated with evidence.

## Evidence

- `task-packet.md` records the dependency-free slug utility behavior, exclusive path, and acceptance criteria derived from the request.
- `requirements.md` translates that request into normalization, error, determinism, and test requirements.

## Uncertainty

- No unresolved request-provenance uncertainty remains; raw conversation content is intentionally excluded.
