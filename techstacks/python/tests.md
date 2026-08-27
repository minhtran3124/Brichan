# Test suite rules

## Rule metadata

- Context ID: `python-tests`
- Reviewed on: `2026-08-26`
- Review within days: `180`
- Deprecated: `no`
- Evidence: `Makefile`; `tests/fixtures/doctor_v2_text.json`

## Scope

- Applies to tests/ and to the frozen policy eval under evals/.

## Rules

- `TEST-001`: Match CI by running with PYTHONDONTWRITEBYTECODE=1 and PYTHONPATH=src, on both Python 3.10 and 3.14 when the change touches interpreter-sensitive code.
- `TEST-002`: A committed fixture that freezes bytes must also have its SHA-256 frozen by a contract test.
- `TEST-003`: A test named for a rejection must call the production code path and fail when the guard is removed; an assertion that cannot fail is a defect.
- `TEST-004`: Tests may read the gitignored task dossier only behind an explicit skip, and never as the sole owner of a gate assertion.

## Overrides

- None.

## Verification

- make test-unit, make test-contract, make test-integration, and make techstack-eval each pass.
- The eval is run directly under both interpreters, because its recipe does not follow PYTHON=.

## Exceptions

- None.

## Examples

None.
