# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `TDW-006`
- Task level: `0`
- Artifact: `requirements`
- Artifact version: `1`
- Origin: `packet:projects/brida-task-dossier-workflow/handoffs/TDW-006/task-packet.md@TDW-006-P1-v1`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `8aa41de8-a3f3-48ce-8d47-9aed67a452c6`
- Effective route: `plan`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Claim or decision

TDW-006 carries exactly one functional requirement — a byte-exact 35-byte UTF-8
fixture at `evals/task-dossier-pilots/simple/greeting.txt` — and four acceptance
criteria transcribed unchanged from the task packet. Nothing is inferred beyond
the packet, and Level 0 is the correct level because the work is single-file,
single-session, non-architectural, and carries no security, destructive, or
public-contract risk.

## Requirements

- `TDW-006-R1`: `evals/task-dossier-pilots/simple/greeting.txt` exists and holds
  the exact UTF-8 byte sequence `Brichan task dossier pilot: simple` followed by
  one `\n`, totalling 35 bytes with no BOM and no trailing blank line.
- `TDW-006-R2`: the dossier records the five planner-owned artifacts with Level 0
  evidence depth and complete model provenance.
- `TDW-006-R3`: no path outside the fixture and the five planner artifacts is
  modified, and nothing is committed, published, deployed, or sent remotely.

## Acceptance criteria

- `TDW-006-AC1`: all five planning artifacts contain real Level 0 evidence and
  provenance (`task-packet.md:29`).
- `TDW-006-AC2`: `plan.md` records accepted `TDW-006-P1` version 1
  (`task-packet.md:30`).
- `TDW-006-AC3`: the fixture is byte-exact and checked locally
  (`task-packet.md:31`).
- `TDW-006-AC4`: no file outside the authorized paths changes
  (`task-packet.md:32`).

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-006/task-packet.md:8-10,14-15,29-32`
  supplies the accepted plan identity, the single requirement, and the four
  acceptance criteria transcribed above.
- `docs/workflows/task-dossier.md:113-128` and
  `src/brichan/contracts/task_dossier/schema.py:102` fix Level 0 at one minimum
  concrete evidence item per passed artifact and list the raise-to-Level-1
  triggers, none of which this single-file fixture meets.

## Uncertainty

- No unresolved requirement uncertainty remains: the packet states the fixture
  path, byte content, and acceptance criteria literally, so no interpretation
  gap needed a client follow-up question.
