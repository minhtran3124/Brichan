# Current state

Last updated: 2026-08-05

## Summary

Status: **Stage 1 fixed, verified, and committed and pushed as two
commits on `feature/opencode-stage1` (`1c739f3` then `33c8c48`); no PR opened.** Plan v13. The combined independent
review returned PASS on both the plan and the code and recommended shipping,
after re-deriving all three enumerations itself against a freshly downloaded
pinned tree and widening the sweep to the shipped package's full 11-package
dependency closure — wider than any implementation round went.

Six executable-surface vectors were found in total. The first four were each
found by something outside the guard's own logic: a live probe, an independent
review, post-commit instrumentation. The last two were found by the derivation's
own closure argument before any failure — `provider`/`providers` in round 8, and
the TUI document in round 12. That shift is the reason the reviewer judged the
discipline sufficient rather than hopeful.

Every executable surface is now derived from the provider's own implementation,
carried in code with source citations, drift-tested in the ADDED direction
against real mutated trees, and bound to a committed fixture so editing the
version pin alone fails `make check` offline.

## Verified environment

- OpenCode 1.18.12 is installed and authenticated with one OpenCode Go credential.
- Herdr 0.7.3 reports the OpenCode integration as current at version 8.
- The local OpenCode catalog exposes `opencode-go/gpt-5.6-luna` with low,
  medium, high, xhigh, and max variants.

## In progress

- OCS-001: guarded checkout coordinator and Herdr worker support.

## Completed recently

- Architecture research mapped the required dispatcher, provider command,
  routing, packaging, repository-contract, documentation, and test changes.
- Security research confirmed that Brichan needs authoritative provider-owned
  runtime configuration and environment, with unsafe overrides rejected before
  Herdr mutation.
- Independent review rejected plan v2 because it did not yet isolate executable
  OpenCode plugins, sanitize inherited behavior controls, prove interactive
  variant transport, or enforce the installed-project boundary.
- Plan v3 resolves those findings with provider pure mode, Herdr screen fallback,
  an all-prefix sanitizing shim, pinned-agent variant transport, merged-config
  preflight, installed-mode hard gating, and ten stable acceptance criteria.
- Independent v3 review found that pure mode does not suppress separately
  discovered custom JS/TS tools, and that capability preflight, agent pinning,
  and the direct installed console gate remain incomplete.
- Follow-up research proved the five built-in primary agents can be disabled
  until only `brichan-primary` is selectable, and the complete merged config can
  be checked with a strict positive capability allowlist. Project `AGENTS.md` is
  treated as user-authorized repository context; global/Claude instruction and
  skill surfaces are isolated or disabled.
- OCS-001-R4 settled two source facts that v7 depends on: `opencode --version`
  exits through yargs before any middleware, handler, or `migrateTuiConfig`
  call, so the version gate may safely precede the migration scan; and no CLI
  command prints the agent-scoped skill set, because `debug skill` calls
  `Skill.all()` while only `Skill.available(agent)` applies permission rules
  and is called solely by the session system-prompt builder.
- Source-backed custom-tool research enumerated all v1.18.12 discovery roots.
  Version 4 will disable project config discovery, isolate global config and the
  home-dot root, leave custom config dirs unset, pin the provider version, and
  scan every matching file/symlink before launch. Plan v4 uses the narrow
  version-pinned `OPENCODE_TEST_HOME` override; Brichan will not repurpose `HOME`.

## Blockers

- **FOURTH plugin-execution vector, confirmed live and open on 1.18.12 even with the
  round-5 fix.** A project `.opencode/opencode.json` declaring `plugin` executes
  under the guard: D8 globs only that root's `{tool,tools}`/`{plugin,plugins}`
  subdirectories, and D12 walks plain ancestors without ever appending a
  `.opencode` segment. Predicted by the v10 reviewer from the guard's code and
  then confirmed live by the coordinator. Note the near-miss: the first control
  run did not fire and made the finding look theoretical, because nested plugin
  paths resolve relative to the config file's directory; the finding was correct.
  The recurring shape means the next fix should derive D12's scan set from the
  provider's own config-discovery implementation rather than adding one more
  hand-listed location.

- **A second plugin-execution vector was found while instrumenting the L4
  mechanism, and it falsifies a premise the final review relied on.** A project
  `opencode.json` declaring `"plugin": ["./anything.js"]` executes that file
  even with `OPENCODE_DISABLE_PROJECT_CONFIG=true` set. D8 does not cover it,
  because the declared path need not sit under `{plugin,plugins}` — in the
  reproduction it was at the project root. The final review had ruled the
  `plugin`/`plugin_origins` residual out of Stage 1 scope specifically because
  "a project cannot inject a plugin entry" once project config is disabled;
  that premise is now shown to be false, so the residual is a local-file-drop
  vector rather than an org/managed-config one, and D13 clause 7 currently
  accepts `plugin` unconditionally without value-gating.
  **CONFIRMED on the pinned 1.18.12 after downgrading back to it**: the shipped
  guard launches and the declared plugin executes. Critically, the D13 allowlist
  cannot close this — `debug config` under the guard reports `plugin: []`,
  because the project's array is correctly excluded from the merge while the
  plugin loader reads the project `opencode.json` directly. The only viable
  control is a D12-style scan refusing any discovered `opencode.json` that
  carries a `plugin` key.
- Resolved: the provider was downgraded back to 1.18.12 with
  `opencode upgrade 1.18.12`; the 1.18.13 binary is kept at
  `~/.opencode/bin/opencode.1.18.13.bak`. The drift is recorded because it
  happened: **the installed OpenCode auto-updated 1.18.12 to 1.18.13 during
  coordinator instrumentation**, because those runs invoked bare `opencode` without
  `OPENCODE_DISABLE_AUTOUPDATE`. Consequence: the shipped guard now refuses
  every launch on the D6 version pin, which is the guard failing closed exactly
  as designed, so there is no exposure on this machine right now. All live probe
  evidence in this task was gathered on 1.18.12 and remains valid for that
  version. The plan's own rule applies: an upgrade re-opens the isolation review
  before the pin moves.
- Noted for the user, not blocking: Noted for the user, not blocking: the `review` route in
  `config/model-routing.json` resolves to Codex `gpt-5.6-sol`, which this
  account cannot use — Codex returns HTTP 400 "The 'gpt-5.6-sol' model is not
  supported when using Codex with a ChatGPT account." Every review since
  OCS-001-PR4C has therefore run on Claude. The manifest entry needs a decision
  (correct the model, or change the route runtime) outside this task.

## Risks

- OpenCode project/global/plugin configuration is merged at startup and can
  affect runtime behavior unless Brichan-owned overrides are authoritative.
- OpenCode model variants are model-specific; route validation must not imply
  a variant exists for every arbitrary model override.
- `--pure` disables the Herdr lifecycle plugin along with other external
  plugins; v3 will assess Herdr's screen-manifest fallback as the safer Stage 1
  lifecycle mechanism and require live evidence.
- No official mechanism was verified for disabling discovery of every custom
  project tool/agent surface, so a source-backed isolation design is required
  before implementation can be authorized.
- Installed-project plugin isolation remains explicitly out of scope.

## Next actions

1. Settle the open `npm.install` question with a live probe: can project-controlled
   configuration that is not already refused trigger a package install, whose
   lifecycle scripts execute by subprocess rather than by `import()`?
2. PR 26 is open: https://github.com/minhtran3124/Brichan/pull/26. Merging is the
   user's decision; the `npm.install` residual is named in its description.
3. Optional hardening the reviewer left as accepted residual: the authenticated
   org/well-known/managed network config source, and the closure argument's
   method boundary.
