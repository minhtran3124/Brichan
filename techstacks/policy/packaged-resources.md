# Packaged resource rules

## Rule metadata

- Context ID: `policy-packaged`
- Reviewed on: `2026-08-26`
- Review within days: `180`
- Deprecated: `no`
- Evidence: `src/brichan/lifecycle.py`; `tests/contract/test_skill_parity_contract.py`

## Scope

- Applies to src/brichan/resources/dogfood_v1/ and the checkout export under .agents/.

## Rules

- `PACKAGED-001`: The packaged skill and its checkout export stay byte-identical; parity is proven by the skill-parity contract, not by inspection.
- `PACKAGED-002`: Adding a packaged policy or skill resource changes the immutable manifest and requires deliberate installed-state backup and reinitialization; never overwrite an existing export automatically.
- `PACKAGED-003`: Installed .brichan/ state stays schema version 1; a report-schema change is versioned separately and never migrates installed state silently.

## Overrides

- None.

## Verification

- make test-contract passes, including the skill-parity and dogfood-policy contracts.

## Exceptions

- None.

## Examples

None.
