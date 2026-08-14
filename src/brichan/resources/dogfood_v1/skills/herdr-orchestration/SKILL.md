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
- Terminal text is a bounded observation with a truncation risk of `none`,
  `possible`, or `confirmed`. On Herdr `0.7.3`,
  `possible` is the normal healthy outcome — not an error.
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

Read `references/commands.md` immediately before Herdr commands.
