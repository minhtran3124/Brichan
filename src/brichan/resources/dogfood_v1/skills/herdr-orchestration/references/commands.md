# Herdr commands

Check health and list existing agents before mutation:

```text
herdr status
herdr integration status
herdr agent list
herdr pane current --current
```

Start a named-route worker from the installed package:

```text
brichan-herdr-agent-start brichan-<name> \
  --anchor-pane <coordinator-pane-id> \
  --cwd <absolute-target-project> \
  --route <plan|implement|review|scan>
```

Use `--dry-run` or `--json` to resolve a route without calling Herdr. Submit
prompts with `herdr pane run`. Close only a recorded Brichan-owned pane with
`herdr pane close <pane-id>`.

Observe workers through the read-only helper:

```text
brichan-herdr-agent-observe preflight [--agent <brichan-name>]
brichan-herdr-agent-observe observe <brichan-name> \
  --lines 200 \
  --project-root <absolute-target-project> \
  --evidence <repo-relative-path>
```

It exits `0` report collected, `1` report impossible, `2` invalid invocation or
rejected path. `herdr integration status` is text-only on `0.7.3`; its `--json`
flag exits `2`. The raw `herdr agent get`, `herdr agent read`, and bounded
`herdr agent wait` commands remain available for manual inspection.

Safeguards that apply to every observation:

- Herdr scheduling state is a scheduling signal only. A worker's `done` or
  `idle` state is not proof that acceptance criteria passed.
- Wait in bounded intervals of at most 30 seconds; every `herdr agent wait`
  carries `--timeout 30000` or less.
- Truncation risk is `none`, `possible`, or `confirmed`. On Herdr `0.7.3`,
  `possible` is the normal healthy outcome; `none` is unreachable by design.
- When risk is `possible` or `confirmed`, use the evidence-file fallback and
  read the declared durable files. Presence metadata is never acceptance
  evidence.
- Never send input to a worker automatically. A `blocked` worker is reported
  for coordinator judgment or user escalation.
- Before declaring a worker stale, record three timestamped no-progress
  observations, then allow one bounded replacement, then escalate.

## Recover a swallowed Enter

A multi-line or long task packet can arrive in an agent TUI as a single paste
block that swallows the trailing Enter. Verified on Claude Code `2.1.220`: the
packet appeared as `[Pasted text #1]` and the worker stayed `idle` until an
explicit key was sent. An `idle` worker after a dispatched packet means the
packet was never submitted, not that the task finished.

Recovery is a manual coordinator step, never automated. First take a fresh
observation:

```text
herdr agent get <brichan-name>
herdr agent read <brichan-name> --source recent-unwrapped --lines 200 --format text
```

Only when that fresh `herdr agent get` plus `herdr agent read` observation shows
the agent is still `idle` and an unsubmitted prompt is on screen, send the
swallowed Enter:

```text
herdr pane send-keys <pane-id> Enter
```

Send no other recovery key; this is the only manual keypress in this recovery
flow, and it is never sent without that observation first. Ordinary task
packets and follow-up instructions are still dispatched with `herdr pane run`
as described above.
