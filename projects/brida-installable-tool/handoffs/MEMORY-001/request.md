# Request provenance

Redacted, read-only record of the originating request. Amendments are recorded as a new artifact version, never by rewriting history.

## Artifact metadata

- Task ID: `MEMORY-001`
- Task level: `2`
- Artifact: `request`
- Artifact version: `1`
- Origin: `user-request`
- Owner: `coordinator`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fe6e0-efcf-74d1-9c61-5297332e0ae6`
- Effective route: `coordinator`
- Effective model: `gpt-5.6-sol`
- Effective effort: `medium`
- Reviewing session: `null`
- Review verdict: `null`

## Request provenance

- Redaction applied: `yes`
- Mutability: `immutable`

## Claim or decision

Repair stale product and project memory, fix the version-specific wheel example,
extend release-memory review, and add a deterministic read-only consistency gate
to `make check` on a local fix branch. Track the product-contract change as
Level 2 with independent Herdr planning, implementation, and review. Exclude a
version bump, publication, push, pull request, external dogfood, and remote state.

## Evidence

- The accepted Durable Memory Consistency Repair plan supplied in the originating request.
- The explicit consistency interface and test plan reproduced in the version-6 planning artifacts.
- The branch and remote-action exclusions recorded in `receipt.md`.

## Uncertainty

- No unresolved request ambiguity remains; plan version 6 defines the bounded implementation contract.
