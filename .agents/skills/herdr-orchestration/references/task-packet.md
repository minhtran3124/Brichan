# Task packet

Use this template for each worker. Remove unused placeholders; do not omit
acceptance criteria. The upstream plan and receipt block is optional only when
there is no accepted plan and no multi-writer task. In that case, you may
omit the block or use `null` for every value.

When a receipt is mandatory, use its canonical repo-relative path:
`projects/<slug>/handoffs/<task-id>/receipt.md`.

```text
You are a worker agent coordinated by Brichan, an AI Chief of Staff acting on the
user's behalf.

Task ID:
<id>

Objective:
<one outcome>

Context:
<minimum context required>

Applicable operating policy:
- Read and follow `docs/policy/operating-principles.md`, including its
  testing discipline, before running Required verification.

Upstream plan and receipt (optional):
- Accepted plan ID: <plan-id or null>
- Plan version: <version or null>
- Plan status: <draft or accepted or implemented or reviewed or null>
- Handoff receipt path: <repo-relative path or null>
- Receipt requirement: <mandatory or not-required>

In scope:
- <item>

Out of scope:
- <item>

Deliverables:
- <artifact or report>

Acceptance criteria:
- <verifiable criterion>

Techstack task ID: <task_id>
Techstack plan ID: <plan_id>
Techstack plan version: <plan_version>
Techstack attempt ID: <attempt_id>
Techstack as-of: <YYYY-MM-DD>
Techstack scope paths JSON: <scope_paths>
Techstack context chains JSON: <context_chains>
Techstack declared conflicts JSON: <declared_conflicts>
Techstack exception approvals JSON: <exception_approvals>
Techstack Snapshot JSON artifact: <repo-relative-path>
Techstack Snapshot SHA-256: <64-lowercase-hex>
Techstack selected files JSON: <selected-path-array>
Techstack acknowledged Context IDs JSON: <context-id-array>
Techstack required selected rule reads JSON: <selected-path-array>
Techstack verify command: brichan techstacks verify --project-root <QROOT> --snapshot-json <QPATH> --as-of <YYYY-MM-DD>
Techstack verification requirement: run-before-work

Required verification:
- <test, lint, source, diff, reproduction, or evidence>

Constraints:
- Do not spawn sub-agents or delegate this task.
- Do not broaden permissions or access secrets.
- Do not modify files outside the stated scope.
- Do not perform destructive, remote, production, deployment, or publishing
  actions without explicit authorization.

Escalate when:
- <condition requiring Brichan/user decision>

Final response:
1. Outcome.
2. Files/artifacts changed.
3. Verification and evidence.
4. Risks, assumptions, and unresolved issues.
```

## Techstack block

Include the sixteen `Techstack ` labels above only when the target project opts
in with a regular, non-symlink `techstacks/README.md` at its top-level Git
root. Each label appears exactly once, in that order, as one LF-terminated
line; JSON values are compact, sorted-key UTF-8 on that line. `QROOT` and
`QPATH` are `shlex.quote` of the actual absolute project root and the
artifact's relative path. The selected-file and required-read arrays are
byte-identical and equal the Snapshot `selected_files[*].path` values, and the
acknowledged Context IDs are the unique Snapshot selected Context IDs sorted by
UTF-8 bytes.

A not-applicable resolution keeps the block and uses exact `none`, `null`,
empty selected, context, and read arrays, and
`Techstack verification requirement: not-applicable` for the six Snapshot,
read, and verify labels; it carries no artifact. A blocked resolution cannot be
packeted at all, and an unmatched publication attempt is never a pointer.

No packet, receipt, plan, or memory entry embeds Snapshot bytes or rule bodies.
The worker opens the selected pointers itself from the project root it holds,
and returns exact
`Techstack verification acknowledgement: yes; snapshot_sha256=<digest>` only
after the literal verify command exits `0` with `match`.

The complete task packet — not only the techstack block — is strict UTF-8 with
LF line endings, exactly one terminal LF, and at most 196,608 bytes. Brichan
refuses launch as `TASK_PACKET_BYTE_LIMIT` rather than truncating, omitting,
wrapping, or moving a field.

See `../../../../docs/policy/techstacks.md` for the resolve, publish, and
planning-reread contract.
