# Runtime package rules

## Rule metadata

- Context ID: `python-runtime`
- Reviewed on: `2026-08-26`
- Review within days: `180`
- Deprecated: `no`
- Evidence: `pyproject.toml`; `tests/unit/test_module_boundaries.py`

## Scope

- Applies to every module under src/brichan/.

## Rules

- `PY-001`: Use only the Python standard library and target Python 3.10 or newer; do not add a third-party dependency without user sign-off.
- `PY-002`: Never import evals from src/brichan; the dependency is one-way and enforced by the module-boundary suite.
- `PY-003`: Keep frozen registries, caps, and diagnostic codes literal and single-sourced; a value spelled in two modules must be pinned equal by a test.
- `PY-004`: Fail closed on unsupported platforms, symlinked roots, and non-regular files; never open content before the type check.

## Overrides

- None.

## Verification

- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.unit.test_module_boundaries passes.
- make package-check passes with empty runtime dependencies.

## Exceptions

- None.

## Examples

None.
