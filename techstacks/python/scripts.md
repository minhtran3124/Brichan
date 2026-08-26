# Scripts and entrypoint rules

## Rule metadata

- Context ID: `python-scripts`
- Reviewed on: `2026-08-26`
- Review within days: `180`
- Deprecated: `no`
- Evidence: `scripts/build_pypi_readme.py`; `packaging/pypi-readme.md`

## Scope

- Applies to scripts/, bin/, and the Makefile.

## Rules

- `SCRIPT-001`: Never edit README_PYPI.md by hand; edit packaging/pypi-readme.md and regenerate with python3 scripts/build_pypi_readme.py.
- `SCRIPT-002`: Checkout wrappers under bin/ call explicit checkout entrypoints; installed console entrypoints never inspect BRICHAN_ROOT for mode selection.
- `SCRIPT-003`: A make target that freezes a literal command keeps it literal; note in the target's docs when it does not follow PYTHON=.

## Overrides

- None.

## Verification

- make readme-check reports no drift.
- sh -n bin/brichan exits 0.

## Exceptions

- None.

## Examples

None.
