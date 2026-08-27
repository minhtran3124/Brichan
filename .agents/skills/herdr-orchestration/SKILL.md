---
name: herdr-orchestration
description: Coordinate independent Codex or other coding-agent sessions through Herdr with bounded task packets, explicit model routing, status monitoring, evidence collection, and safe cleanup. Use whenever Brichan delegates project research, implementation, testing, debugging, or review to a worker agent, or needs to inspect and manage a Brichan-owned Herdr session.
---

# Herdr Orchestration

Create only independent main-agent sessions. Never use native Codex sub-agents
or automatic delegation as a substitute for Herdr.

## Workflow

1. Confirm Herdr and the required integration are healthy.
2. Write a complete task packet before creating a worker.
3. Read `references/commands.md`, select a named route from
   `../../../config/model-routing.json`, and use
   `../../../docs/policy/model-catalog.md` only as capability guidance.
4. Start a uniquely named `brichan-` worker with the balanced-layout wrapper in
   the intended project directory.
5. Record its agent name, pane ID, model, task, and status in project `tasks.md`.
6. Send the task packet and monitor status without busy-polling.
7. When blocked, read the recent output and either provide bounded guidance or
   escalate to the user.
8. Collect the final output, diff, tests, and other required evidence.
9. Check acceptance criteria; invoke an independent reviewer when required.
10. Update project memory, then close only the pane Brichan created.

## Preconditions

Do not create a worker until the task has:

- One objective.
- Explicit scope and exclusions.
- Deliverables.
- Acceptance criteria.
- Permissions and constraints.
- Escalation conditions.
- A selected named route or a documented legacy explicit provider command.

Use `references/task-packet.md` as the prompt template. When an accepted
upstream plan exists, fill its optional upstream plan and receipt block; when
one does not exist, omit the block or use `null` values.

A handoff receipt is mandatory for an accepted-plan handoff and for any
multi-writer task. One child receipt per writer and one parent receipt per task.
Use a standalone receipt for a single-writer task. Store operational receipts
at `projects/<slug>/handoffs/<task-id>/receipt.md` and add their paths to the
project's `references.md`.

A tracked task also owns a full task dossier in the same directory. Read
`references/task-dossier.md` before creating or resuming one. The receipt stays
canonical for delegated lifecycle evidence; the dossier index links to it.

## Techstack context

When the target project opts in with a regular, non-symlink
`techstacks/README.md` at its top-level Git root, read
`../../../docs/policy/techstacks.md` before writing the packet. Resolve and
publish one Snapshot with

```text
brichan techstacks resolve --project-root <QROOT> --input-json <QINPUT> --snapshot-directory <QDIR>
```

into the authorized directory alone —
`projects/<project-slug>/handoffs/<TASK-ID>/snapshots` in a source checkout, or
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

## Monitoring

Route every worker observation through the read-only helper rather than
interpreting raw terminal text:

```text
bin/brichan-herdr-agent-observe preflight [--agent <brichan-name>]
bin/brichan-herdr-agent-observe observe <brichan-name> \
  --lines 200 \
  --project-root <absolute-target-project> \
  --evidence <repo-relative-path>
```

It emits one deterministic JSON report and exits `0` report collected, `1`
report impossible, `2` invalid invocation or rejected path. Raw `herdr`
commands stay documented in `references/commands.md` as the underlying
reference.

Three authority classes stay separate:

- Herdr scheduling state (`idle`, `working`, `blocked`, `done`, and any future
  state) is a scheduling signal only. It tells Brichan when to look, when to
  wait, and when to escalate. A worker's `done` or `idle` state is not proof
  that acceptance criteria passed.
- Terminal text is a bounded observation. Every read carries a truncation risk
  of `none`, `possible`, or `confirmed`. On Herdr `0.7.3` no capability proves
  history completeness, so `possible` is the normal healthy outcome, not an
  error — do not over-escalate on it.
- Acceptance evidence is durable files only. When truncation risk is `possible`
  or `confirmed`, use the evidence-file fallback: declare the evidence paths and
  read those files. Presence metadata is never acceptance evidence: read and
  judge the content.

Wait in bounded intervals of at most 30 seconds. Never send input to a worker
automatically — no keys, no prompts, no nudges. A `blocked` worker is reported
for coordinator judgment or user escalation.

## Safety

- Run `herdr agent list` before creating or closing anything.
- Never reuse or close an unrelated existing pane.
- Keep a record of Brichan-owned pane IDs.
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
  handoffs, including techstack Snapshot pointer placement.
- Read `references/task-dossier.md` when creating, resuming, or closing the
  full task dossier of a tracked task.
- Read `references/concurrent-writers.md` when coordinating a multi-writer
  task.
- Read `references/worker-recovery.md` before declaring a worker stale,
  replacing it, or abandoning its task.
