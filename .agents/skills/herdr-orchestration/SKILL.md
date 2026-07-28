---
name: herdr-orchestration
description: Coordinate independent Codex or other coding-agent sessions through Herdr with bounded task packets, explicit model routing, status monitoring, evidence collection, and safe cleanup. Use whenever Brida delegates project research, implementation, testing, debugging, or review to a worker agent, or needs to inspect and manage a Brida-owned Herdr session.
---

# Herdr Orchestration

Create only independent main-agent sessions. Never use native Codex sub-agents
or automatic delegation as a substitute for Herdr.

## Workflow

1. Confirm Herdr and the required integration are healthy.
2. Write a complete task packet before creating a worker.
3. Read `references/commands.md` and select a verified provider/model from
   `../../../model-catalog.md`.
4. Start a uniquely named `brida-` worker with the balanced-layout wrapper in
   the intended project directory.
5. Record its agent name, pane ID, model, task, and status in project `tasks.md`.
6. Send the task packet and monitor status without busy-polling.
7. When blocked, read the recent output and either provide bounded guidance or
   escalate to the user.
8. Collect the final output, diff, tests, and other required evidence.
9. Check acceptance criteria; invoke an independent reviewer when required.
10. Update project memory, then close only the pane Brida created.

## Preconditions

Do not create a worker until the task has:

- One objective.
- Explicit scope and exclusions.
- Deliverables.
- Acceptance criteria.
- Permissions and constraints.
- Escalation conditions.
- A selected verified provider/model.

Use `references/task-packet.md` as the prompt template. When an accepted
upstream plan exists, fill its optional upstream plan and receipt block; when
one does not exist, omit the block or use `null` values.

A handoff receipt is mandatory for an accepted-plan handoff and for any
multi-writer task. One child receipt per writer and one parent receipt per task.
Use a standalone receipt for a single-writer task. Store operational receipts
at `projects/<slug>/handoffs/<task-id>/receipt.md` and add their paths to the
project's `references.md`.

## Safety

- Run `herdr agent list` before creating or closing anything.
- Never reuse or close an unrelated existing pane.
- Keep a record of Brida-owned pane IDs.
- Do not place secrets in prompts, names, environment variables, or logs.
- Do not use permission-bypass flags.
- Do not let a worker spawn further agents.
- Do not use Codex reasoning effort `ultra` for a worker.
- A worker's `done` or `idle` state is not proof that acceptance criteria passed.
- Never close a pane until its needed output and evidence are saved.

## References

- Read `references/commands.md` immediately before using Herdr commands.
- Read `references/task-packet.md` when constructing a new assignment or
  follow-up instruction.
- Read `references/handoff-receipt.md` for planner-to-implementer or reviewer
  handoffs.
- Read `references/concurrent-writers.md` when coordinating a multi-writer
  task.
- Read `references/worker-recovery.md` before declaring a worker stale,
  replacing it, or abandoning its task.
