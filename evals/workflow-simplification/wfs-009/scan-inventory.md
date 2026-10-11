# WFS-009 scan inventory: Claude model IDs and aliases

Scope: `config/ docs/ .agents/ src/ tests/ bin/ scripts/ packaging/ README.md README_PYPI.md CHANGELOG.md AGENTS.md CLAUDE.md PRODUCT.md Makefile pyproject.toml`
(`evals/`, `metrics/`, `projects/`, `.git/` excluded). All listed paths exist.

## Search commands

```sh
P=(config docs .agents src tests bin scripts packaging README.md README_PYPI.md CHANGELOG.md AGENTS.md CLAUDE.md PRODUCT.md Makefile pyproject.toml)
# full IDs (24 hits)
grep -rnoIE 'claude-(fable|opus|sonnet|haiku)[A-Za-z0-9._-]*' $P
# bare aliases (5 hits)
grep -rnoIE '(^|[^A-Za-z0-9-])(fable|opus|sonnet|haiku)([^A-Za-z0-9-]|$)' $P
```

Class notes: `catalog-record` = a row of the model/alias tables in `docs/policy/model-catalog.md`;
other mentions in that file (probe notes, guidance table) are `documentation`.
Prose uses such as "Sonnet 5" (catalog line 68) and "diffable" are not model values and are not listed.

## Table

| # | path:line | ID / alias | class |
|---|-----------|------------|-------|
| 1 | config/model-routing.json:11 | claude-fable-5 | active-routing-pin |
| 2 | config/model-routing.json:19 | claude-fable-5 | active-routing-pin |
| 3 | config/model-routing.json:24 | claude-opus-5-5 | active-routing-pin |
| 4 | config/model-routing.json:34 | claude-sonnet-5-5 | active-routing-pin |
| 5 | src/brichan/resources/dogfood_v1/config/model-routing.json:11 | claude-opus-5-5 | active-routing-pin |
| 6 | docs/policy/model-catalog.md:54 | fable | catalog-record |
| 7 | docs/policy/model-catalog.md:54 | claude-fable-5-1 | catalog-record |
| 8 | docs/policy/model-catalog.md:55 | claude-fable-5 | catalog-record |
| 9 | docs/policy/model-catalog.md:56 | opus | catalog-record |
| 10 | docs/policy/model-catalog.md:56 | claude-opus-5-5 | catalog-record |
| 11 | docs/policy/model-catalog.md:57 | claude-opus-5 | catalog-record |
| 12 | docs/policy/model-catalog.md:58 | sonnet | catalog-record |
| 13 | docs/policy/model-catalog.md:58 | claude-sonnet-5-5 | catalog-record |
| 14 | docs/policy/model-catalog.md:59 | claude-sonnet-5 | catalog-record |
| 15 | docs/policy/model-catalog.md:61 | claude-fable-5 | documentation |
| 16 | docs/policy/model-catalog.md:61 | claude-sonnet-5 | documentation |
| 17 | docs/policy/model-catalog.md:61 | claude-opus-5 | documentation |
| 18 | docs/policy/model-catalog.md:62 | claude-opus-5-5 | documentation |
| 19 | docs/policy/model-catalog.md:66 | claude-sonnet-5-5 | documentation |
| 20 | docs/policy/model-catalog.md:68 | claude-sonnet-5 | documentation |
| 21 | docs/policy/model-catalog.md:95 | claude-sonnet-5-5 | documentation |
| 22 | docs/policy/model-catalog.md:96 | claude-opus-5-5 | documentation |
| 23 | docs/policy/model-catalog.md:99 | claude-sonnet-5-5 | documentation |
| 24 | tests/integration/test_cli_compatibility.py:85 | sonnet | test-fixture |
| 25 | tests/integration/test_cli_compatibility.py:90 | sonnet | test-fixture |
| 26 | tests/unit/test_cli_render.py:456 | claude-fable-5 | test-fixture |
| 27 | tests/unit/test_cli_render.py:457 | claude-opus-5 | test-fixture |
| 28 | tests/unit/test_cli_render.py:466 | claude-fable-5 | test-fixture |
| 29 | tests/unit/test_cli_render.py:467 | claude-opus-5 | test-fixture |

## Active routing pins naming `claude-sonnet-5`, `claude-opus-5`, or `claude-fable-5` exactly

- `config/model-routing.json:11` — `claude-fable-5` (coordinator.runtimes.claude)
- `config/model-routing.json:19` — `claude-fable-5` (routes.plan)

No active routing pin names `claude-sonnet-5` or `claude-opus-5`. The `scan` route
(`claude-sonnet-5-5`), `implement` route (`claude-opus-5-5`), and the packaged
dogfood coordinator (`claude-opus-5-5`) are on the new IDs.

## Total

29 rows (24 full-ID occurrences + 5 bare-alias occurrences), matching the re-run of both commands.
