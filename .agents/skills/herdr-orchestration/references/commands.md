# Herdr command reference

Verified against Herdr `0.7.3`, protocol `16`, on 2026-07-27.

## Health and discovery

```text
herdr status
herdr integration status
herdr workspace list
herdr tab list
herdr agent list
```

List agents before mutation. The commands return JSON containing stable IDs such
as `workspace_id`, `tab_id`, `pane_id`, and `terminal_id`. Copy IDs exactly.

## Start a routed main agent

Resolve the coordinator pane once before starting a related worker group:

```text
herdr pane current --current
```

Copy its `pane_id` as `<coordinator-pane-id>`. Start workers through Brida's
wrapper so the coordinator tab stays balanced:

```text
bin/brida-herdr-agent-start <brida-name> \
  --anchor-pane <coordinator-pane-id> \
  --cwd <absolute-project-path> \
  --route <plan|implement|review|scan>
```

The named route is resolved from `config/model-routing.json`. For a one-off
launch, `--runtime`, `--model`, and `--effort` take precedence over the
manifest. Use `--dry-run` for a shell-readable command or `--json` for a
machine-readable resolution; both paths validate without calling Herdr:

```text
bin/brida-herdr-agent-start <brida-name> \
  --cwd <absolute-project-path> \
  --route review \
  --runtime codex \
  --model <verified-model> \
  --effort high \
  --json
```

Use a unique name beginning with `brida-`. The launcher rejects unsupported
runtimes and efforts, Codex `ultra`, arbitrary settings, native-agent options,
and permission-bypass controls before Herdr mutation.

## Legacy explicit commands

The explicit provider command remains available during migration:

```text
bin/brida-herdr-agent-start <brida-name> \
  --anchor-pane <coordinator-pane-id> \
  --cwd <absolute-project-path> \
  -- codex --model <verified-model>
```

Legacy commands are limited to the `codex` and `claude` providers and are
validated before Herdr mutation. The launcher injects native-delegation
disabling for both providers and defaults legacy Claude workers to
`--permission-mode auto`. Safe explicit Claude permission modes remain
compatible; `bypassPermissions` does not.

Do not use Claude until `claude auth status` succeeds.

The wrapper infers the coordinator workspace/tab, keeps focus on the
coordinator, and targets these layouts:

| Total panes | Layout |
|---:|---|
| 2 | Equal 50/50 columns |
| 3 | Equal-area T layout |
| 4 | Equal 2x2 grid |

For more than four panes or an already non-canonical split tree, it splits the
largest pane as a best effort and prints a warning. It does not move panes
between tabs or workspaces.

The launcher returns nonzero when no worker was started. Once Herdr confirms a
worker start, the launcher preserves Herdr's start JSON and returns success even
if a later best-effort resize or focus restoration fails; it prints that
degradation to stderr. This avoids interpreting a live worker as a failed start
and accidentally spawning a duplicate.

## Resolve and instruct

```text
herdr agent get <brida-name>
herdr agent read <brida-name> --source recent-unwrapped --lines 200 --format text
```

Resolve the returned `pane_id`. To enter prompt text into the active agent UI
and submit it:

```text
herdr pane run <pane-id> <task-packet>
```

`herdr agent send` writes literal text without submitting it. Prefer
`herdr pane run` for a prompt that must be followed by Enter.

A multi-line or long task packet can arrive in an agent TUI as a single paste
block that swallows the trailing Enter. Verified on Claude Code `2.1.220`: the
packet appeared as `[Pasted text #1]` and the worker stayed `idle` until an
explicit key was sent. After `herdr pane run`, confirm the worker actually
started:

```text
herdr agent get <brida-name>
herdr pane send-keys <pane-id> Enter
```

Send the Enter only when the agent is still `idle` and `herdr agent read` shows
an unsubmitted prompt. An `idle` worker after a dispatched packet means the
packet was never submitted, not that the task finished.

## Monitor

```text
herdr agent wait <brida-name> --status idle --timeout 30000
herdr agent get <brida-name>
herdr agent read <brida-name> --source recent-unwrapped --lines 200 --format text
```

Wait in bounded intervals of at most 30 seconds so the user continues receiving
progress updates. Treat `blocked` as a request to inspect output and decide
whether Brida can respond within its authority.

## Follow up

After resolving the current `pane_id`:

```text
herdr pane run <pane-id> <follow-up-instruction>
```

Send only the missing decision or correction. Do not restate the entire project
history.

## Close

```text
herdr pane close <brida-owned-pane-id>
```

Close only after:

- Final output and evidence were collected.
- Acceptance criteria were checked.
- Project memory was updated.
- The ID matches the Brida-owned record in `tasks.md`.

Do not close an entire workspace when it contains any pane Brida did not create.
