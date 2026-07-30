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
3. Start a unique `brida-` worker with `brida-herdr-agent-start`, an absolute
   target `--cwd`, and a named route.
4. Record its name, pane ID, model, task, and status in project memory.
5. Submit the packet, monitor without busy-polling, and collect final evidence.
6. Check acceptance criteria and material risks.
7. Update project memory and close only the pane Brida created.

Do not broaden permissions, include secrets, use permission-bypass flags, let a
worker spawn agents, or choose Codex `ultra` for a worker.

Read `references/commands.md` immediately before Herdr commands.
