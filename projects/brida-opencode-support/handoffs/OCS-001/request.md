# Request provenance

Redacted, read-only record of the originating request. Amendments are recorded as a new artifact version, never by rewriting history.

## Artifact metadata

- Task ID: `OCS-001`
- Task level: `2`
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

`The user requested implementation of Stage 1 OpenCode support using multiple independent workers for research, implementation, and review, and explicitly authorized repository-context egress to Claude Code, Codex, and OpenCode workers while excluding secrets and credentials.`

## Evidence

- User authorization recorded in the originating conversation on 2026-08-04.
- `projects/brida-opencode-support/overview.md` records the redacted scope and exclusions.
- `projects/brida-opencode-support/decisions.md` records Stage 1 scope and writer isolation.

## Uncertainty

- No unresolved request-provenance uncertainty remains; installed-project support and remote actions are explicitly excluded.
