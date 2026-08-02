# Request provenance

Redacted, read-only record of the originating request. Amendments are recorded as a new artifact version, never by rewriting history.

## Artifact metadata

- Task ID: `<TASK-000>`
- Task level: `<0, 1, or 2>`
- Artifact: `request`
- Artifact version: `<positive integer>`
- Origin: `<immutable origin marker>`
- Owner: `coordinator`
- Phase state: `<pending, active, passed, not-required, or blocked>`
- Applicability: `<required or not-required>`
- Applicability rationale: `null`
- Authorship: `<model or human>`
- Authoring session: `<session identifier or null>`
- Effective route: `<named route or null>`
- Effective model: `<model identifier or null>`
- Effective effort: `<effort or null>`
- Reviewing session: `<session identifier or null>`
- Review verdict: `<PASS, CHANGES REQUIRED, or null>`

## Request provenance

- Redaction applied: `yes`
- Mutability: `immutable`

## Claim or decision

`<claim or decision this artifact asserts>`

## Evidence

- `<repository or source evidence for the claim>`

## Uncertainty

- `<unresolved uncertainty, or a recorded statement that none remains>`
