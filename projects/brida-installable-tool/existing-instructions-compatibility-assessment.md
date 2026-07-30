# Existing `.claude` / `.agents` compatibility assessment

Date: 2026-07-30

## Outcome

Filesystem coexistence is safe in the current installed-project flow: Brida
creates only `.brida/` and does not edit `.claude/`, `.agents/`, `.codex/`,
`AGENTS.md`, `CLAUDE.md`, or target `bin/brida-*` wrappers.

Runtime coexistence is not yet safe enough to promise as a compatibility
contract. Installed Brida launches Codex with command-line configuration that
adds Brida instructions and a Brida skill path. Target Codex instructions and
trusted project configuration can still participate in the same session, and
the exact behavior of skill-list layering needs a live-Codex probe.

## Verified local behavior

The installed command constructs `-C <target-root>`, a
`developer_instructions=<Brida bootstrap + target paths>` override, and
`skills.config=[{path=<target>/.brida/skills/herdr-orchestration,enabled=true}]`,
along with model/reasoning settings and native-agent disabling. It does not
include paths under `.claude`, `.agents`, or `.codex` and does not invoke target
`bin/brida-*` wrappers.

A disposable repository containing `AGENTS.md`, `CLAUDE.md`,
`.claude/settings.json`, `.claude/settings.local.json`, `.claude/skills`,
`.claude/agents`, `.claude/hooks`, `.agents/skills`, `.codex/config.toml`, and
`bin/brida-codex` was tested. `brida init --apply` left every pre-existing file
byte-for-byte unchanged and created only `.brida/`.

## Compatibility matrix

| Target artifact | Brida installed mode reads | Brida writes | Current assessment |
|---|---|---|---|
| `AGENTS.md` / nested `AGENTS.md` | No; Codex reads it independently | No | Coexists, but its instructions may conflict with Brida bootstrap. Codex documents root-to-cwd concatenation; exact ordering versus `developer_instructions` is not documented here. |
| `CLAUDE.md` | No; installed mode is Codex-only | No | Inert for installed Brida; relevant when Claude runs separately. |
| `.claude/settings*.json`, skills, agents, hooks | No | No | Inert in installed Codex flow. Claude worker sessions may load target Claude configuration; that is a separate boundary. |
| `.agents/skills` | No direct Brida read | No | Provider auto-discovery behavior is unresolved for the current Codex build/docs. Do not promise these skills are preserved or ignored until a live probe. |
| `.codex/config.toml` | Brida does not read it; Codex may load trusted project config | No | Same-key CLI overrides take precedence. Brida can mask project `model`, `developer_instructions`, `skills.config`, and similar values; other project settings may still apply. |
| `bin/brida-*` | No | No | Installed launcher explicitly avoids target wrappers. |
| Existing `.brida/` | Yes, schema-v1 inspection | Only when absent and `--apply` | Existing malformed/incompatible state is refused; no automatic repair or migration. |

## Main risks

1. **High: skill configuration collision.** Brida sets `skills.config` on the
   command line. CLI config overrides outrank project config, but the official
   docs do not state whether this array is merged with or replaces existing
   per-skill overrides. A replacement could silently discard user skill
   disables or paths. Whether `.agents/skills` is independently discovered is
   also unverified.
2. **High: trusted project configuration is not surfaced.** Codex can load a
   trusted `.codex/config.toml`; Brida does not report its presence in `doctor`.
   Users may not realize project MCP/hooks/approval/config behavior participates
   while Brida injects its own command-line policy.
3. **Medium: instruction conflict.** A target `AGENTS.md` may contain rules
   for a normal pair-programming agent, including delegation or identity rules
   that conflict with Brida's coordinator contract. Exact conflict precedence
   is not established by current evidence.
4. **Medium: unsupported Claude entrypoint edge.** `brida-claude` is documented
   as checkout-oriented, but its root heuristic recognizes any cwd ancestor with
   `AGENTS.md` and `bin/`. A target with those markers plus a valid routing file
   can be mistaken for a Brida checkout when the installed entrypoint is invoked
   directly. This is outside supported installed mode but should be hardened
   before broad dogfood claims.

## Recommended compatibility contract

- `init` is namespace-safe and writes only `.brida/`.
- Installed Brida is Codex-only and does not promise Claude compatibility.
- `AGENTS.md` and trusted `.codex/config.toml` are provider inputs that may
  combine with or be overridden by Brida invocation settings.
- `.agents/skills` coexistence is unverified until a live Codex probe.
- `doctor` should eventually report detected instruction/config surfaces without
  reading or mutating them.

Before claiming full coexistence safety, add controlled tests with a real Codex
binary for an existing project skill, a user/project skill disable, conflicting
`AGENTS.md` versus Brida identity, and trusted `.codex/config.toml` hooks/MCP/
approval settings. Keep them read-only and inspect active sources.

## Sources and evidence

- Local implementation: `src/brida/lifecycle.py`, `src/brida/cli/codex.py`,
  `src/brida/cli/provider_commands.py`, `src/brida/cli/_root.py`.
- Local installed-mode contract: `docs/guides/installable-dogfood.md`.
- Codex instruction discovery and merge order:
  https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Codex config precedence and trusted project config:
  https://learn.chatgpt.com/docs/config-file/config-basic
- Codex `developer_instructions` and `skills.config` keys:
  https://learn.chatgpt.com/docs/config-file/config-reference
- Claude project settings and precedence:
  https://code.claude.com/docs/en/settings

## Unresolved

No live provider session inspected active skill sources. Claims about
`.agents/skills` discovery, array replacement/merge semantics, and relative
ordering of `developer_instructions` versus `AGENTS.md` remain unverified and
must not become a durable “safe” promise.
