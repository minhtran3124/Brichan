# Herdr command reference

Verified against Herdr `0.9.1`, protocol `22`, on 2026-09-18 (task
`HERDR-091`). `0.9.1` is Brichan's minimum supported Herdr and the only pair in
the adapter's verified set.

This file was previously verified against `0.7.3`, protocol `16`, on
2026-07-27. `0.7.3` was dropped from the verified set in `HERDR-091` because
its `agent read` returned a JSON envelope that the current plain-text adapter
cannot parse. Where `0.7.3` appears below it is history or the unverified
path, never a supported version.

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

Copy its `pane_id` as `<coordinator-pane-id>`. Start workers through Brichan's
wrapper so the coordinator tab stays balanced:

```text
bin/brichan-herdr-agent-start <brichan-name> \
  --anchor-pane <coordinator-pane-id> \
  --cwd <absolute-project-path> \
  --route <plan|implement|review|scan>
```

The named route is resolved from `config/model-routing.json`. For a one-off
launch, `--runtime`, `--model`, and `--effort` take precedence over the
manifest. Use `--dry-run` for a shell-readable command or `--json` for a
machine-readable resolution; both paths validate without calling Herdr:

```text
bin/brichan-herdr-agent-start <brichan-name> \
  --cwd <absolute-project-path> \
  --route review \
  --runtime codex \
  --model <verified-model> \
  --effort high \
  --json
```

Use a unique name beginning with `brichan-`. The launcher rejects unsupported
runtimes and efforts, Codex `ultra`, arbitrary settings, native-agent options,
and permission-bypass controls before Herdr mutation.

## Legacy explicit commands

The explicit provider command remains available during migration:

```text
bin/brichan-herdr-agent-start <brichan-name> \
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

On Herdr `0.9.1` the wrapper launches in two steps, because
`agent start --workspace/--tab/--split` was removed: it runs `herdr pane split
<target-pane> --direction <right|down> --cwd <path> [--env K=V ...]`, takes the
new `pane_id` out of the returned `pane_info` envelope, and then runs `herdr
agent start <brichan-name> --kind <claude|codex> --pane <new-pane-id> --timeout
30000 -- <agent arguments>`. `--kind` names the canonical executable, so only
the arguments after it are forwarded. If the agent start fails, the wrapper
closes the pane it just created and nothing else.

The wrapper keeps focus on the coordinator and targets these layouts:

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
herdr agent get <brichan-name>
herdr agent read <brichan-name> --source recent-unwrapped --lines 200 --format text
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
herdr agent get <brichan-name>
herdr pane send-keys <pane-id> Enter
```

Send the Enter only when the agent is still `idle` and `herdr agent read` shows
an unsubmitted prompt. An `idle` worker after a dispatched packet means the
packet was never submitted, not that the task finished.

## Monitor

Prefer the typed read-only helper for any observation Brichan will act on:

```text
bin/brichan-herdr-agent-observe preflight [--agent <brichan-name>]
bin/brichan-herdr-agent-observe observe <brichan-name> \
  --lines 200 \
  --project-root <absolute-target-project> \
  --evidence <repo-relative-path> [--evidence <repo-relative-path> ...]
```

`preflight` reports the client/server version, protocol, compatibility, both
restart-need values, per-runtime integration health, and capability findings
such as the observed `trust_directory` manifest failure. A version or protocol
outside the verified set {`0.9.1`/`22`} is reported as
`unverified`; that is a
state, never a block, and the helper never updates, installs, or edits Herdr
state. A `0.7.3` server reports `unverified-version` and is still fully
reported on.

`observe` reports the scheduling state verbatim, the read text with its
completeness metadata, and presence metadata for each declared evidence file.
It has no completion field by design.

| Exit | Meaning |
|---:|---|
| `0` | Report collected, including `unverified`, degraded, and truncation findings |
| `1` | Report impossible (`herdr` missing, primary probe failed or schema-invalid) |
| `2` | Invalid invocation or rejected project-root/evidence path |

The raw commands remain available for manual inspection:

```text
herdr agent wait <brichan-name> --until idle --timeout 30000
herdr agent get <brichan-name>
herdr agent read <brichan-name> --source recent-unwrapped --lines 200 --format text
herdr integration status
```

The wait state option is `--until` on `0.9.1`; `--status` was removed and the
client exits `2` on it. `--until` is repeatable on the client, but Brichan
emits one state per wait and always with `--timeout 30000` or less.

`herdr integration status` is text-only on `0.9.1`; its
`--json` flag exits `2`. On `0.9.1` its rows added an `(experimental)` runtime
qualifier and an `outdated (vN < vM)` upgrade comparison, and four runtimes
(`qwen`, `antigravity-cli`, `grok`, `letta`); the helper parses all of them and
still rejects anything else as a malformed row.

Wait in bounded intervals of at most 30 seconds so the user continues receiving
progress updates. Treat `blocked` as a request to inspect output and decide
whether Brichan can respond within its authority.

### Truncation and the evidence-file fallback

`herdr agent read` returns a bounded UTF-8 observation, not a transcript
guarantee. The helper classifies truncation risk as `none`, `possible`, or
`confirmed`:

- `confirmed` — the read failed, or Herdr's native `truncated` flag is set. On
  `0.9.1` a read that exits nonzero, or returns no screen at all, is a failed
  read.
- `possible` — the normal healthy outcome on `0.9.1`. No capability
  proves
  alternate-screen history completeness, so a short read cannot be trusted as
  complete. Do not treat it as an error.
- `none` — unreachable by design. `herdr agent read` returns
  plain terminal text with no envelope and no native `truncated` flag — there
  is no JSON form, and `--format json` is refused — so nothing can prove a read
  complete. Reaching `none` requires an authorized
  Herdr upgrade plus a reviewed design revision.

When risk is `possible` or `confirmed`, the authoritative fallback is reading
declared evidence files, not re-reading the screen. Pass `--project-root` and
`--evidence`; the helper reports existence, regular-file status, size, and
mtime from a held descriptor, and rejects absolute, `~`-prefixed, `..`, and
symlinked paths. Presence metadata is never acceptance evidence: read and
judge the file contents.

### No automatic input

Never send input to a worker automatically. The helper cannot: its command
allowlist contains no `pane run`, `agent send`, `pane send-keys`, `pane close`,
or `agent start`, and every `agent wait` it emits is capped at 30000 ms. A
`blocked` worker is surfaced for coordinator judgment or user escalation, never
answered by tooling.

The paste-swallowed-Enter recovery below stays a manual coordinator step. Take
it only after a fresh `herdr agent get` plus `herdr agent read` observation shows
an unsubmitted `[Pasted text #1]` prompt on an `idle` worker.

Before declaring a worker stale, record three timestamped no-progress
observations, then allow one bounded replacement, then escalate. See
`worker-recovery.md`.

## Follow up

After resolving the current `pane_id`:

```text
herdr pane run <pane-id> <follow-up-instruction>
```

Send only the missing decision or correction. Do not restate the entire project
history.

## Close

```text
herdr pane close <brichan-owned-pane-id>
```

Close only after:

- Final output and evidence were collected.
- Acceptance criteria were checked.
- Project memory was updated.
- The ID matches the Brichan-owned record in `tasks.md`.

Do not close an entire workspace when it contains any pane Brichan did not create.
