# Options

Credible implementation options with trade-offs. Selected decisions are promoted into design and plan.

## Artifact metadata

- Task ID: `OCS-001`
- Task level: `2`
- Artifact: `options`
- Artifact version: `6`
- Origin: `coordinator-amendment-after-claude-review-v5`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `d95644de-8b6b-43bf-923e-5df8567eef29` plus coordinator amendment
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Claim or decision

`The selected design uses a sanitizing exec shim, provider-owned pure mode, fail-closed merged-config preflight, pinned-agent model/variant transport, screen-manifest lifecycle fallback, installed-mode hard gating, optional schema-v1 defaults, and wrapper/console/installer parity.`

Selected options and rejected alternatives:

- Select a package-owned shim that rebuilds compact guard config after removing inherited `OPENCODE_*`; reject Herdr JSON env transport and ambient mutation.
- Select exact-version source-backed isolation: `OPENCODE_DISABLE_PROJECT_CONFIG`, isolated XDG config and `OPENCODE_TEST_HOME`, plus independent discovery scanning; reject `HOME` repurposing and pure-only protection.
- Select `--pure` plus Herdr screen-manifest fallback; reject executing all external plugins merely to preserve richer Herdr plugin lifecycle/session metadata.
- Select a `debug config` preflight over the final merged config; reject assuming inline config outranks managed settings.
- Select a positive final-capability allowlist and exactly one primary agent; reject field-only checks and initial-agent-only selection.
- Trust repository `AGENTS.md` plus only its Herdr orchestration skill; reject global/Claude instructions and unrestricted skill discovery.
- Select option A: restore the exact absolute repository `AGENTS.md` through the guarded `instructions` field while keeping project-config discovery disabled; reject dropping policy or reopening project config.
- Keep routing schema version 1 with Codex/Claude required and OpenCode optional; reject a schema bump or required third key that invalidates installed manifests.
- Preserve the runtime/model/effort triple and map effort into pinned-agent `variant`; reject unsupported top-level TUI `--variant`, a stale per-model allowlist, and dropping effort parity.
- Support guarded legacy `-- opencode ...`; reject named-route-only behavior because the user requested parity.
- Add coordinator and internal exec wrappers, console scripts, installer exposure, and dogfood smoke while hard-rejecting OpenCode against installed `.brichan` targets.

## Evidence

- `src/brichan/cli/_root.py` currently provides one exec boundary suitable for explicit environment support.
- `src/brichan/resources/dogfood_v1/config/model-routing.json` proves installed schema-v1 state contains only Codex/Claude coordinator entries.
- `pyproject.toml` already exposes checkout-oriented `brichan-codex` and `brichan-claude` console scripts.
- Herdr documents OpenCode screen-manifest fallback; OpenCode documents `--pure`, agent-level variant, and managed settings above inline config.

## Uncertainty

- No material option remains unresolved; live hostile-config/plugin evidence remains an acceptance test rather than a design choice.
