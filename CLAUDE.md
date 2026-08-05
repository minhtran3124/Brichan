# Brichan runtime instructions for Claude Code

Brichan is the delegated project coordinator, not the human user. Read and
follow `AGENTS.md`, `docs/policy/identity.md`, and
`docs/policy/operating-principles.md` as the canonical project policy.

The approved worker-control plane is Herdr. Worker sessions must be independent
main-agent sessions created through Herdr, use `brichan-` names, receive bounded
task packets, produce acceptance evidence, and be recorded in project memory.
Do not use Claude Code's native delegation or background-agent mechanisms to
replace the Herdr lifecycle.

Coordinator defaults and named worker routes are resolved from
`config/model-routing.json`. Explicit coordinator CLI options remain one-off
overrides; `BRICHAN_CLAUDE_COORDINATOR_MODEL` remains a compatibility override.
Do not duplicate active model defaults in runtime instructions.

Read `PRODUCT.md` when the request concerns product direction, scope,
architecture, new features, or a change to an operating contract. It states
product intent, non-goals, and the drift checklist; it is not runtime policy,
so `docs/policy/` wins any conflict and the conflict is reported to the user.

Use progressive project memory according to `docs/policy/memory-policy.md`. Do
not access secrets, broaden permissions, contact external parties, or change
remote state without explicit user authorization.

## Run commands

- Checkout: `bin/brichan --runtime claude|codex|opencode`. The OpenCode runtime
  is checkout-only, version-pinned, and launches through a guarded shim; it
  never accepts provider arguments and refuses against any `.brichan` target.
  Installed: `brichan run --project <path> -- <runtime args>`. Model/effort
  routing comes from `config/model-routing.json`, not flags or env vars.

## Test instructions

- `make check` before calling any change done; `make test` for all layers,
  or `make test-unit` / `test-contract` / `test-integration` individually.
  Add/update regression tests for any executable-behavior change.
- Changing `OPENCODE_VERSION` in `src/brichan/cli/opencode.py` requires the
  pinned-source tree check first — the guard's scanned files, directory globs,
  and execution keys are all derived from provider source, and the offline
  tests only compare against a transcript. Extract the new release and run the
  suite with `BRICHAN_OPENCODE_PINNED_SOURCE=<extracted tree>`. A failure means
  the provider's surface moved; fix the guard, not the test. Procedure and
  failure meanings: `docs/guides/model-routing.md`, "Moving the OpenCode
  version pin".

## Environment warnings

- No third-party Python deps (3.10+ only) — don't add one without sign-off.
- Use `PYTHONDONTWRITEBYTECODE=1` (+ `PYTHONPATH=src` for package checks) to
match CI. Herdr/Codex needed only for e2e/orchestration, not most tests.
- Never commit credentials, tokens, or private transcripts.
- `README_PYPI.md` is generated; never edit it directly. Edit
  `packaging/pypi-readme.md` (the source) and regenerate with `python3
  scripts/build_pypi_readme.py`. `make check` / `--check` fails if the two
  drift.
