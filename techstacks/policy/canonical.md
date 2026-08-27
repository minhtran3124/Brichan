# Canonical policy rules

## Rule metadata

- Context ID: `policy-canonical`
- Reviewed on: `2026-08-26`
- Review within days: `180`
- Deprecated: `no`
- Evidence: `docs/policy/identity.md`; `docs/policy/operating-principles.md`

## Scope

- Applies to docs/policy/, PRODUCT.md, AGENTS.md, and CLAUDE.md.

## Rules

- `POLICY-001`: docs/policy/ is runtime policy and wins any conflict with PRODUCT.md; report the conflict to the user instead of resolving it silently.
- `POLICY-002`: Do not duplicate active model defaults in runtime instructions; config/model-routing.json is the single source.
- `POLICY-003`: Worker sessions are independent Herdr sessions with brichan- names and bounded task packets; never substitute native delegation for the Herdr lifecycle.

## Overrides

- None.

## Verification

- make memory-check and make path-check pass.

## Exceptions

- None.

## Examples

None.
