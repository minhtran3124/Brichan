# Current state

Last updated: 2026-08-05

## Summary

Status: **OCS-001 Stage 1 is complete and awaiting the user's ship decision.**
Canonical plan is v9, `accepted`. Both the plan review and the code review
returned PASS against that exact text, and all seven live probes (L1-L5, E1,
E2) are recorded. Suites: 10/498/77/100. Everything is uncommitted on
`feature/opencode-stage1`.

The arc that matters: v8 passed an independent code review with 676 green tests
and was then falsified by live probe L4, which executed a project-local plugin
under the guarded launch. Static review had been wrong about this exact surface
once, so every later claim was checked live. The user chose to close it by
extending D8. v9 made D8's `{plugin,plugins}` scan the authoritative control,
stopped citing `--pure` as proof, and the final review then found a second hole
of the same class - D8 silently narrowed to cwd outside a Git worktree while
the provider walks to the filesystem root - now closed by refusing to launch
outside a worktree.

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

- None blocking. Noted for the user, not blocking: Noted for the user, not blocking: the `review` route in
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

1. Collect the implementation report (`/tmp/brichan-ocs001-impl-report.md`),
   verify `make check`/`make test`, and check AC1–AC9 evidence.
2. Independently review the code with a fresh session on a different model
   from the writer (manifest review route is unusable on this account — see
   Blockers note).
3. Run the live OpenCode worker lifecycle probes L1–L5 and E1–E2, complete the
   receipt and dossier, and close panes.
