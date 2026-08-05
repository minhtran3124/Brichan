# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `OCS-001`
- Task level: `2`
- Artifact: `requirements`
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

`Stage 1 requires a guarded OpenCode checkout coordinator, routed and legacy Herdr workers, checkout-oriented console parity, fail-before-mutation safety controls, backward-compatible routing schema behavior, complete regression evidence, and no installed-project OpenCode expansion. Version 6 additionally requires exact empty normalized agent options, an immediate final merged-config recheck, absolute AGENTS existence validation, and negative migration/skill/remote-config tests.`

Required outcomes:

- `bin/brichan --runtime opencode`, `BRICHAN_RUNTIME=opencode`, and the checkout-oriented `brichan-opencode` console command resolve the same guarded adapter.
- Named worker route overrides and legacy `-- opencode ...` commands produce guarded OpenCode launches through Herdr only.
- Native `task`/subagent use is denied, the primary agent is pinned, and subagent depth is zero; direct `@agent` and Task-tool attempts are live-tested.
- Every guarded process uses provider-owned `--pure`; project/global/npm plugins, including the installed Herdr plugin, do not execute. Herdr screen-manifest fallback supplies Stage 1 lifecycle visibility.
- A package-owned shim removes every inherited `OPENCODE_*` key without inspecting values, sets exactly the owned inline config and update-disable keys, and preserves non-OpenCode provider auth variables and credential-file use.
- A sanitized `opencode --pure debug config` preflight verifies final merged safety/model/variant fields and refuses managed/project overrides without logging resolved config or secrets.
- OpenCode must be exactly version 1.18.12; all four custom-tool discovery roots are isolated and independently scanned for singular/plural JS/TS files and symlinks before provider startup.
- Final capabilities use a positive allowlist: no MCP, config instructions, commands, unknown tools, extra agents, widened permissions, or unknown top-level keys.
- All five built-in primaries are disabled; only `brichan-primary` remains selectable. Repository `AGENTS.md` and exactly its `herdr-orchestration` project skill are trusted; global/Claude instruction and skill sources are isolated or denied.
- With project config discovery disabled, the exact absolute Brichan-computed `AGENTS.md` path is the sole allowed config instruction; relative, remote, and extra instructions are rejected. Provider TUI migration keys are rejected before startup.
- Existing Codex/Claude generated commands and installed Codex schema-v1 state remain compatible.
- OpenCode effort maps syntactically to `agent.brichan-primary.variant`; the TUI receives `--agent`, never top-level `--variant`; only verified default-model variants are claimed as available.
- OpenCode named/default/legacy workers against any target with `.brichan` state fail before Herdr mutation; installed mode remains Codex-only.
- Direct installed `brichan-opencode` use from a `.brichan` target fails before provider startup unless positively identified as the Brichan source checkout.
- Full unit, contract, integration, live Herdr lifecycle, dossier, receipt, and independent-review gates pass.

## Evidence

- `projects/brida-opencode-support/handoffs/OCS-001/request.md` records user scope and provider-egress authorization.
- `projects/brida-opencode-support/overview.md` records Stage 1 boundaries and stable constraints.
- `src/brichan/orchestration/model_routing.py` currently hard-codes Codex and Claude runtime keys and exact coordinator-key matching.
- `src/brichan/cli/provider_commands.py` currently guards only Codex and Claude and returns argv without provider-owned environment.
- Official OpenCode CLI/config/permission documentation and Herdr integration documentation are linked in `projects/brida-opencode-support/references.md`.

## Uncertainty

- Live acceptance must still prove hostile plugins do not execute under `--pure`, screen-manifest fallback is usable, preflight remains fail-closed, and both native-subagent invocation paths are denied.
