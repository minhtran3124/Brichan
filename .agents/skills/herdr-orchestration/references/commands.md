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

## Start a Codex main agent

```text
herdr agent start <brida-name> \
  --cwd <absolute-project-path> \
  --no-focus \
  -- codex --disable multi_agent -m <model>
```

Use a unique name beginning with `brida-`. Do not pass
`--dangerously-bypass-approvals-and-sandbox`. Do not select `ultra` reasoning.

For an authenticated Claude provider:

```text
herdr agent start <brida-name> \
  --cwd <absolute-project-path> \
  --no-focus \
  -- claude --model <verified-model> --permission-mode manual
```

Do not use Claude until `claude auth status` succeeds.

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
