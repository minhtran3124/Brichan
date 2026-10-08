---
name: herdr-orchestration
description: Coordinate independent coding-agent sessions through Herdr with bounded task packets, explicit routing, evidence collection, and safe cleanup.
---

# Herdr orchestration

Create only independent main-agent sessions. Never use Codex native sub-agents
or automatic delegation.

## Workflow

1. Confirm `herdr status`, `herdr integration status`, and `herdr agent list`.
2. Write a bounded task packet using `references/task-packet.md`.
3. Start a unique `brichan-` worker with `brichan-herdr-agent-start`, an absolute
   target `--cwd`, and a named route.
4. Record its name, pane ID, model, task, and status in project memory.
5. Submit the packet, monitor without busy-polling, and collect final evidence.
6. Check acceptance criteria and material risks.
7. Update project memory and close only the pane Brichan created.

Do not broaden permissions, include secrets, use permission-bypass flags, let a
worker spawn agents, or choose Codex `ultra` for a worker.

## Monitoring safeguards

Observe workers with `brichan-herdr-agent-observe`, which is read-only and
emits one deterministic JSON report (`0` collected, `1` impossible, `2` invalid
invocation or rejected path).

- Herdr scheduling state is a scheduling signal only. A worker's `done` or
  `idle` state is not proof that acceptance criteria passed.
- Wait in bounded intervals of at most 30 seconds. Never busy-poll.
- Herdr `0.9.1` (protocol `22`) is the minimum supported version and the only
  verified control plane. Anything older or newer preflights as `unverified` —
  a reported state, never a block.
- Terminal text is a bounded observation with a truncation risk of `none`,
  `possible`, or `confirmed`. On `0.9.1`,
  `possible` is the normal healthy outcome — not an error. The read is plain
  terminal text with no native `truncated` flag, so `none` is unreachable by
  design.
- When risk is `possible` or `confirmed`, use the evidence-file fallback: read
  the declared durable evidence files instead of re-reading the screen.
  Presence metadata is never acceptance evidence: read and judge the content.
- Never send input to a worker automatically. A `blocked` worker is reported
  for coordinator judgment or user escalation.
- A long packet can arrive as `[Pasted text #1]` with the Enter swallowed,
  leaving the worker `idle` with the task never submitted. Recovery is a manual
  coordinator step: send `herdr pane send-keys <pane-id> Enter`, and only after
  a fresh `herdr agent get` plus `herdr agent read` observation shows the agent
  is still `idle` with an unsubmitted prompt. See `references/commands.md`.
- Before declaring a worker stale, record three timestamped no-progress
  observations, then allow one bounded replacement, then escalate.

Event-driven waiting (Claude Code runtime). A Claude Code coordinator should
not spend one model turn per bounded wait. Run `watch` under the Claude Code
Monitor tool, or as a background Bash task when only the final event matters:

```text
brichan-herdr-agent-observe watch <brichan-name> \
  [--source auto|events|wait] [--stop-on <state>]... \
  [--interval-ms 30000] [--max-duration-ms 1800000]
```

The helper, not the model, does the waiting and prints one compact JSON line
per scheduling-state transition (`"event": "state"`). With the default
`--source auto` it subscribes to Herdr's `events.subscribe` socket stream
(verified on `0.9.1` only), so each change is pushed; if the subscription
cannot be set up it falls back to bounded `herdr agent wait` calls of at most
30 seconds (`--source wait` forces that loop, `--source events` refuses the
fallback). Either way the state is re-read after every quiet interval, so a
lost agent is reported within one interval, and every line names its
`source`. It then prints exactly one final line: `stop` when a stop state is
reached (default `idle`, `done`, `blocked`; exit `0`), `expired` when the run
outlives `--max-duration-ms` (exit `0`; re-arm it), or `error` when the agent
is lost or Herdr fails (exit `1`). Silence means the worker is still in a
non-stop state, never that it crashed.

- A `stop` event is a scheduling signal only and is not proof of completion:
  follow it with `observe` and the evidence-file fallback.
- Start the watch only after a fresh observation shows the worker `working`.
  A `stop` on `idle` right after dispatch is the `[Pasted text #1]`
  swallowed-Enter case, not a finished task.
- Codex has no Monitor tool; a Codex coordinator keeps the bounded
  `herdr agent wait` loop.
- `watch` is read-only and never sends input to the worker.

## Techstack context

When the target project opts in with a regular, non-symlink
`techstacks/README.md` at its top-level Git root, read
`.brichan/policy/techstacks.md` before writing the packet. Resolve and publish
one Snapshot with

```text
brichan techstacks resolve --project-root <QROOT> --input-json <QINPUT> --snapshot-directory <QDIR>
```

into the authorized directory alone —
`.brichan/project-memory/techstack-snapshots/<TASK-ID>` in an installed project
— and never into a digest-bearing filename you chose. Publication derives
`<attempt-id>-<snapshot-sha256>.snapshot.json` after each resolve, verifies it,
and retries at most three drifted observations; blocked and not-applicable stop
with no artifact, and an unmatched attempt can never enter a packet.

The packet block, the exact not-applicable form, the whole-packet
196,608-byte cap, and the receipt pointer placement are stated in
`references/task-packet.md` and `references/handoff-receipt.md`. No packet or
receipt embeds Snapshot bytes or rule bodies; the worker opens the selected
pointers itself.

Brichan — not a package helper — rejects a stale Snapshot digest, a missing or
unmatched verification acknowledgement, a worker-authored exception approval,
and plan acceptance before the mandatory reread. A newly discovered path,
Context ID or chain, conflict, or exception need forces re-resolution: send the
newly selected pointers, the requirement to reread each one, and the new
Snapshot pointer to a plan worker, require a revised plan carrying the final
scope, every acknowledgement, and the latest digest, check it semantically, and
verify again before acceptance. An implementation worker rereading the new
pointers is explicitly insufficient.

## References

Read `references/commands.md` immediately before Herdr commands. Read
`references/handoff-receipt.md` for planner-to-implementer or reviewer
handoffs, including techstack Snapshot pointer placement.
