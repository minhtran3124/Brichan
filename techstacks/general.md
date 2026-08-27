# General repository rules

## Rule metadata

- Context ID: `general`
- Reviewed on: `2026-08-26`
- Review within days: `180`
- Deprecated: `no`
- Evidence: `CLAUDE.md`; `AGENTS.md`

## Scope

- Applies to every task in this repository, on every path.

## Rules

- `GENERAL-001`: Run make check and see it exit 0 before calling any change done.
- `GENERAL-002`: Never commit credentials, tokens, or private transcripts, and never change remote state without explicit user authorization.
- `GENERAL-003`: Read docs/policy/ as the canonical runtime policy; when PRODUCT.md conflicts with it, policy wins and the conflict is reported.
- `GENERAL-004`: Add or update a regression test for every executable-behavior change.

## Overrides

- None.

## Verification

- PYTHONDONTWRITEBYTECODE=1 make check exits 0 on Python 3.10 and 3.14.
- git status --short shows no credential, token, or transcript file staged.

## Exceptions

- None.

## Examples

None.
