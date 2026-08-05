# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `OCS-001`
- Task level: `2`
- Artifact: `design`
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

`OpenCode support is an additive, fail-closed provider adapter: a package-owned shim sanitizes inherited provider controls, preflights the final merged config, then launches a pinned primary agent in pure mode while installed projects remain Codex-only.`

Design contract:

1. Add OpenCode builders and strict argv guards in `provider_commands.py`; model/effort become `agent.brichan-primary.model/variant` in compact inline JSON, not TUI `--variant`.
2. Add `opencode.py` with coordinator and internal exec entrypoints. Before provider exec, remove all inherited `OPENCODE_*`, set only `OPENCODE_CONFIG_CONTENT` and `OPENCODE_DISABLE_AUTOUPDATE`, and never inspect/log removed values.
3. Run sanitized `opencode --pure debug config`; require exact sharing/update/subagent/task/agent/model/variant fields and refuse mismatch, timeout, nonzero, or invalid JSON while naming only key paths.
4. Launch `opencode --pure --agent brichan-primary`. Pure mode intentionally disables the installed Herdr plugin and every other external plugin; lifecycle acceptance uses Herdr's screen manifest.
5. Reject explicit unsafe controls and `OPENCODE_*` worker env input before Herdr. The in-pane shim handles independently inherited Herdr shell/server environment before provider exec.
6. Add OpenCode to checkout runtime/effort syntax with optional schema-v1 coordinator defaults. Reject named/default/legacy OpenCode worker resolution for every target containing `.brichan` before any Herdr subprocess.
7. Add coordinator/internal wrappers and console scripts, installer exposure, installed-dogfood smoke, and repository-path inventory. Existing Codex/Claude argv and installed resources remain unchanged.
8. Verify hostile-plugin non-execution, screen-fallback lifecycle, direct `@general` and Task-tool denial, and final merged-config authority in bounded scratch/live probes.
9. Gate on OpenCode 1.18.12, isolate all source-confirmed custom-tool discovery roots without changing `HOME`, and independently reject every matching JS/TS path or symlink before startup.
10. Disable all five built-in primary agents and require exactly one primary. Positive-allowlist the complete merged config; expose only repository `AGENTS.md` and its `herdr-orchestration` skill.
11. Reject direct `brichan-opencode` from any installed `.brichan` target before provider preflight unless the source checkout is positively identified.
12. Restore only the absolute repository `AGENTS.md` through `instructions`; scan ancestor OpenCode configs for migration keys before provider startup, and treat TUI keybinds as a separate owned `tui.json` file rather than a debug-config field.

## Evidence

- `src/brichan/cli/provider_commands.py` shows provider-specific guards and the current argv-only worker boundary.
- `src/brichan/orchestration/worker_launch.py::_resolve_launch` performs resolution before any Herdr subprocess.
- `src/brichan/orchestration/model_routing.py::parse_settings` currently exact-matches coordinator runtimes, exposing the installed-manifest compatibility trap.
- Official OpenCode CLI/schema/config docs describe `--pure`, agent-level variant, task permission, subagent depth, and managed precedence.
- Official Herdr docs describe screen-manifest fallback whenever the OpenCode lifecycle plugin is not installed or actively reporting.

## Uncertainty

- Live acceptance must prove pure mode prevents plugin side effects and screen fallback provides usable Stage 1 state; richer plugin-reported session restore remains explicitly out of scope.
