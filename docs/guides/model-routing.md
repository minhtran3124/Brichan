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
