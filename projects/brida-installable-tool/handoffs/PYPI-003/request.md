# Request provenance

Redacted, read-only record of the originating request.

## Artifact metadata

- Task ID: `PYPI-003`
- Task level: `2`
- Artifact: `request`
- Artifact version: `1`
- Origin: `user-request`
- Owner: `coordinator`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fe9cf-025e-79b0-b809-a0edf58c883b`
- Effective route: `coordinator`
- Effective model: `gpt-5.6-sol`
- Effective effort: `medium`
- Reviewing session: `null`
- Review verdict: `null`

## Request provenance

- Redaction applied: `yes`
- Mutability: `immutable`

## Claim or decision

Confirm the canonical public repository URL, enable public PyPI README
rendering, restore the hero image through its anonymous raw URL, and remove the
completed gate from durable current state. The coordinator additionally
included the identical stale `PRODUCT.md` item as bounded truth reconciliation.

## Evidence

- The originating user request quoted the open gate in
  `projects/brida-installable-tool/current-state.md` and asked to complete it.
- GitHub and anonymous HTTP evidence observed on 2026-08-10 is recorded in the
  accepted plan and will be re-probed before implementation.
- `plan-review.md` artifact version 6 independently passed the bounded plan.

## Uncertainty

- The live PyPI page changes only with a future separately authorized release;
  this task updates repository-side release inputs only.
