# Request provenance

Redacted, read-only record of the originating request. Amendments are recorded as a new artifact version, never by rewriting history.

## Artifact metadata

- Task ID: `DOGFOOD-006`
- Task level: `1`
- Artifact: `request`
- Artifact version: `1`
- Origin: `user-request`
- Owner: `coordinator`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `human`
- Authoring session: `null`
- Effective route: `null`
- Effective model: `null`
- Effective effort: `null`
- Reviewing session: `null`
- Review verdict: `null`

## Request provenance

- Redaction applied: `yes`
- Mutability: `immutable`

## Claim or decision

The user requested a read-only JSON doctor command for checkout/project health,
including repository, Git, policy, routing, project-memory, and dependency
diagnostics, with nonzero status for invalid checkouts and no remote actions.

## Evidence

- The originating user request recorded in this artifact.
- The explicit instruction not to push or open a PR without asking.

## Uncertainty

- The exact JSON schema and definition of a valid checkout are to be settled
  during planning against the existing lifecycle contracts.
