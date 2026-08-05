# Decisions

## 2026-08-04 — Stage 1 scope

- Decision: implement checkout coordinator and Herdr worker support first;
  installed-project OpenCode support is a separate later stage.
- Rationale: installed mode currently has Codex-specific manifest, bootstrap,
  diagnostics, and provider safety contracts that need separate threat-model
  and migration decisions.
- Status: accepted by user authorization to proceed with Stage 1.

## 2026-08-04 — Writer isolation

- Decision: research, planning, and review workers are read-only; one
  implementation worker exclusively owns product-code changes.
- Rationale: obtain independent perspectives without concurrent write conflicts.
- Status: active for OCS-001.

## 2026-08-04 — Repository trust and provider isolation

- Decision: treat the target repository's `AGENTS.md` as user-authorized project
  context. Do not implicitly trust global OpenCode/Claude instructions, global
  skills, MCP, commands, custom agents, plugins, or executable custom tools.
- Decision: disable Claude compatibility and expose exactly one project skill,
  `herdr-orchestration`, through ordered permission rules `* deny` then
  `herdr-orchestration allow`; enforce a positive final-capability allowlist.
- Decision: pin the Stage 1 isolation contract to OpenCode `1.18.12`, use its
  narrow `OPENCODE_TEST_HOME` override plus isolated `XDG_CONFIG_HOME`, and
  reject every source-backed custom-tool discovery path before launch. Do not
  repurpose `HOME`.
- Rationale: repository content is explicitly in scope, while unrelated global
  and executable extension surfaces were not authorized. The internal home
  override is acceptable only under an exact provider version gate and avoids
  changing process-wide home semantics or credential storage.
- Status: accepted design input for OCS-001 plan version 5; live verification
  remains mandatory.

## 2026-08-04 — Provider merge residual

- Decision: perform a final merged-config preflight immediately before provider
  exec and refuse any mismatch. Accept the remaining narrow provider-owned
  race between that check and OpenCode's own later org/managed/well-known merge
  as a documented residual; do not claim inline config is globally authoritative.
- Rationale: OpenCode has no supported switch to remove authenticated org and
  managed merge layers while preserving credential-file authentication. The
  re-check minimizes the window and keeps fail-closed behavior on every
  observed mismatch.
- Status: accepted design input for OCS-001 plan version 6.
