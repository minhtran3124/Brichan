# Repository layout

Brichan uses stable repository adapters around an importable Python core.

```text
AGENTS.md / CLAUDE.md ──> docs/policy/
bin/ and scripts/ ──────> brichan.cli / brichan.contracts
brichan.cli ──────────────> provider adapters
brichan.orchestration ────> Herdr process, layout, and read-only monitoring
projects/evals/metrics    durable data; never imported by the core
```

## Boundaries

- `bin/` and `scripts/` are compatibility paths. They contain only bootstrap
  logic and delegate to `src/brichan/`.
- `src/brichan/contracts/receipts/` exposes schema, parser, discovery, and
  validation APIs.
- `src/brichan/orchestration/` owns provider-neutral layout and Herdr launch
  behavior. `monitor.py` adds the read-only preflight and worker-observation
  surface behind `bin/brichan-herdr-agent-observe`: it may run only
  non-mutating Herdr commands, caps every `herdr agent wait` at 30000 ms, and
  has no completion field, so a scheduling state can never be reported as
  acceptance evidence. Its evidence fallback uses a descriptor-relative
  `O_DIRECTORY | O_NOFOLLOW` walk, the same discipline as
  `src/brichan/contracts/task_dossier/generate.py`.
- `src/brichan/cli/` owns runtime dispatch and the Codex/Claude adapters.
- `projects/`, `evals/`, and `metrics/` are data and evidence. Importable
  modules must not depend on them.

## Verification layers

- `tests/unit/`: importable module behavior.
- `tests/contract/`: durable repository and policy contracts.
- `tests/integration/`: stable wrappers and provider command compatibility.

`make check` runs all layers, durable-data validators, structural checks, and
the source-package import check.

## Compatibility retirement

Temporary root documentation pointers are governed by
`config/compatibility-retirement.json`. Run:

```bash
make phase5-preflight
```

The default command validates and reports state without failing CI merely
because the compatibility window is still open. Actual pointer retirement must
first pass the strict gate:

```bash
python3 scripts/check_compatibility_retirement.py --require-eligible
```

Eligibility requires the exact protected pointer mapping, a completed
versioned release window, repository-wide search, external-link checks, fresh
Codex and Claude startup smokes, and full CI. Every passing gate requires
timestamped repository evidence; evidence predating release completion is
rejected.
