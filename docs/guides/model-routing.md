# Model routing and worker launch settings

Brichan keeps active model selection in
[`config/model-routing.json`](../../config/model-routing.json). This manifest
controls coordinator defaults and the named worker routes `plan`, `implement`,
`review`, and `scan`.

It is intentionally limited to a runtime, model, and reasoning effort. It
cannot grant permissions, add arbitrary provider arguments, or enable native
delegation.

## Choose a coordinator runtime

Start Brichan with the default runtime from the manifest:

```bash
bin/brichan
```

Choose a runtime for one session:

```bash
bin/brichan --runtime claude
bin/brichan --runtime opencode
```

The provider adapters use the manifest's model and effort defaults. Explicit
provider options remain available for a one-off coordinator launch:

```bash
bin/brichan --runtime claude --model <model> --effort <effort>
```

## Start a worker by route

Use a named route when starting a worker. Brichan resolves and validates the
route before it asks Herdr to create a pane.

```bash
bin/brichan-herdr-agent-start brichan-example \
  --anchor-pane <coordinator-pane-id> \
  --cwd <absolute-project-path> \
  --route implement
```

For one worker launch, `--runtime`, `--model`, and `--effort` override the
route value. CLI values take precedence over the manifest.

```bash
bin/brichan-herdr-agent-start brichan-example \
  --cwd <absolute-project-path> \
  --route review \
  --runtime codex \
  --model <model> \
  --effort <effort> \
  --json
```

Use `--dry-run` for readable output or `--json` for structured output. Neither
option creates a Herdr pane.

## Change settings safely

Edit only `runtime`, `model`, and `effort` fields in
`config/model-routing.json`, then run:

```bash
make check
```

Malformed settings, unknown routes or runtimes, unsupported effort, Codex
`ultra`, and permission-bypass attempts fail before a worker starts. Codex and
Claude worker commands also disable their native delegation features
independently of the prompt.

## OpenCode (Stage 1, guarded and checkout-oriented)

The optional `coordinator.runtimes.opencode` entry enables a guarded OpenCode
coordinator. It is optional on purpose: a manifest without it keeps parsing, and
requesting OpenCode without it produces an owned error naming the missing key.

`bin/brichan --runtime opencode` and `bin/brichan-opencode` both reach one
adapter, which never spawns a provider itself. It resolves the routed model and
effort and hands off to `bin/brichan-opencode-exec`, the shim that owns the
whole boundary:

- Every inherited `OPENCODE_*` variable is removed without being inspected, and
  exactly six guard keys are set. `HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME`, and
  `XDG_CACHE_HOME` are never touched, so the real OpenCode credential file keeps
  resolving and no re-login is needed.
- The routed model and effort become `agent.brichan-primary.model` and
  `.variant` inside the pinned inline configuration. They never appear in
  provider argv; the launch is always
  `opencode --pure --agent brichan-primary`. A legacy `-m` is validated into
  that configuration and never forwarded.
- The provider version must be exactly `1.18.12`. The isolation contract is
  source-line specific, so any OpenCode upgrade re-opens the review before the
  pin moves.
- All four custom-tool discovery roots are isolated and then independently
  preflighted by Brichan itself, including symlinks and both the `tool/` and
  `tools/` spellings.
- The complete merged `debug config` document must satisfy a positive
  allowlist, checked twice: once after the migration scan and again immediately
  before launch. Organization, well-known, and managed configuration merge after
  the inline configuration and may use the network, so the second read is not
  redundant. A bounded provider-owned race remains after that final check.

Known limitations, stated plainly:

- **Variant validation is syntactic only.** Brichan checks that the value is one
  of `low`, `medium`, `high`, `xhigh`, `max`. It does not verify the provider
  accepts that variant for the routed model.
- **The Herdr plugin is disabled by `--pure`,** so an OpenCode worker's state is
  observed through the screen-manifest fallback rather than through the richer
  plugin state. Expect coarser state granularity than a Codex or Claude worker.
- **Repository instructions are trusted input.** Exactly one absolute
  `AGENTS.md` path from the target worktree reaches the session, together with
  the project `herdr-orchestration` skill; every other skill is denied and the
  global OpenCode, Claude, and home-dot roots are hidden. `AGENTS.md`
  auto-discovery has no provider disable switch, so that file and that one skill
  are treated as user-authorized repository input, not as an untrusted
  prompt-injection surface.
- **Installed targets are out of scope.** An OpenCode worker or a direct
  `brichan-opencode` run against a directory containing `.brichan` refuses
  before Herdr is contacted and before any provider starts.

## Legacy explicit commands

The explicit command form remains available for compatibility:

```bash
bin/brichan-herdr-agent-start brichan-example \
  --anchor-pane <coordinator-pane-id> \
  --cwd <absolute-project-path> \
  -- codex --model <model>
```

It is provider-allowlisted and still receives Brichan's delegation and
permission guardrails. Prefer named routes for new work: they are validated,
auditable, and easier to change centrally.
