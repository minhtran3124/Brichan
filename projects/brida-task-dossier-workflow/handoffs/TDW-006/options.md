# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `TDW-006`
- Task level: `0`
- Artifact: `options`
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

Option A — write the file literally and verify its bytes with `wc -c` and `od -c`
— is selected. The only material decision at Level 0 is how the byte-exactness
claim is proven, not how the bytes are produced; a literal write plus a byte-level
read-back is the shortest path that produces evidence rather than assertion.

## Options considered

- Option A (selected): write the file directly, then verify with
  `wc -c` (expect 35) and `od -c` (expect a single trailing `\n`). Cheapest, and
  the verification is independent of the write mechanism.
- Option B: generate the file with `printf 'Brichan task dossier pilot: simple\n'`.
  Equally exact, but shell quoting becomes an extra failure mode, and the command
  proves what was intended rather than what landed on disk.
- Option C: generate the file from a small Python helper committed beside it.
  Rejected: it adds a second file the packet does not authorize
  (`task-packet.md:19-25`) and inverts the ceremony ratio this pilot is measuring.

## Rejected trade-off

Verifying only with `cat` or by eye is rejected. A trailing-newline or
editor-added blank line is invisible in `cat` output, and
`docs/workflows/task-dossier.md:9-10` states that document presence is not
correctness evidence; the same standard applies to a fixture that merely looks
right.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-006/task-packet.md:14-15,31`
  requires exact UTF-8 content plus one newline and a local byte-exactness check,
  which is what separates Option A from a visual check.
- `evals/` currently holds only `2026-07-27-workflow-evaluation` and
  `mixed-provider-coding`, so `evals/task-dossier-pilots/simple/` is a new
  directory and no existing fixture convention constrains the choice.

## Uncertainty

- No unresolved option uncertainty remains: all three options produce identical
  bytes, so the selection turns only on evidence quality and authorized file
  count, both of which the packet settles.
