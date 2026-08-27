# Techstack rules

Resolution, Snapshot publication, and verification are executable package
behavior. Packet completeness and receipt placement are coordinator policy: no
package helper accepts a packet, and none exists.

## Ownership

`techstacks/**` belongs to the target project; never create, edit, remove,
repair, or inventory-manage it. The sole opt-in is a regular, non-symlink
`techstacks/README.md` at the exact validated top-level Git root. Every README
is map-only; normative component rules live in non-README leaves. Packets,
receipts, plans, and project memory carry pointers, digests, acknowledgements,
and decisions — never rule bodies or Snapshot bytes. A worker opens the
pointers itself. A worker's claim that it read a rule, verified a Snapshot, or
holds an approval is a claim, not evidence.

## Resolve and publish

Supply only an authorized Snapshot directory, never a digest-bearing filename:

```text
brichan techstacks resolve --project-root <QROOT> --input-json <QINPUT> --snapshot-directory <QDIR>
```

`QROOT`, `QINPUT`, and `QDIR` are `shlex.quote` of the actual absolute project
root and the normalized repo-relative input and directory paths. In an
installed project the only authorized directory is
`.brichan/project-memory/techstack-snapshots/<TASK-ID>`, and the artifact is
`<attempt-id>-<snapshot-sha256>.snapshot.json` inside it.

Each attempt resolves once, derives its own filename, publishes missing-only,
and verifies that exact artifact. A `match` selects it and stops. A `drift` or
`blocked` observation leaves the immutable artifact in place and starts a fresh
resolve; at most three drifted observations are retried, after which the status
is `observation_drift` and no artifact is packetable. Blocked and
not-applicable resolutions stop with no new artifact. Nothing is overwritten,
truncated, renamed, or deleted. Only the selected artifact of a published
resolution may enter a packet or a receipt.

## Task packet

An applicable packet contains these labels exactly once, in this order, each as
one LF-terminated line. JSON values are compact, sorted-key UTF-8 on that line:

```text
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
```

The selected-file and required-read arrays are byte-identical and equal the
Snapshot `selected_files[*].path` values. The acknowledged Context IDs are the
unique Snapshot selected Context IDs sorted by UTF-8 bytes.

A not-applicable packet uses exact `none`, `null`, empty selected, context, and
read arrays, and `Techstack verification requirement: not-applicable` for the
six Snapshot, read, and verify labels; it carries no artifact. A blocked
resolution cannot be packeted.

The complete task packet — not only the techstack block — is strict UTF-8 with
LF line endings, exactly one terminal LF, and at most 196,608 bytes. Refuse
launch as `TASK_PACKET_BYTE_LIMIT` rather than truncating, omitting, wrapping,
or moving a field.

The worker returns exact
`Techstack verification acknowledgement: yes; snapshot_sha256=<digest>` only
after the literal verify command exits `0` with `match`.

## Handoff receipt

No receipt field, section, or schema version is added; two existing sections
carry the pointers. See `.brichan/skills/herdr-orchestration/references/handoff-receipt.md`.

In `## Scope`, the `In scope` value appends the exact tokens
`Techstack snapshot pointer: <artifact path or none>; Techstack snapshot SHA-256: <digest or null>`,
or exactly `Techstack snapshot pointer: none; Techstack snapshot SHA-256: null`
for a not-applicable resolution.

In `## Verification`, one row records the literal verify command with
`pass; snapshot_sha256=<digest>`, or the literal publication command with
`pass; snapshot_sha256=null; status=not_applicable`.

The receipt parser splits every table line on the pipe character with no escape
step, and the Verification validator rejects any row that does not yield
exactly two columns. `shlex.quote` never removes or escapes a pipe, and a
backslash escape is not unescaped anywhere. A project root or Snapshot artifact
path containing a pipe, CR, or LF is out of contract for receipt embedding: do
not create a techstacks receipt for such a root. Roots containing a space, a
single quote, or a leading-dash final component are in contract.

## Planning reread

Reject plan acceptance whenever planning discovers a new path, Context ID or
chain, conflict, or exception need. Then re-resolve and publish a new Snapshot;
send the newly selected file pointers, the requirement to reread each pointer,
and the new Snapshot artifact pointer to a plan worker; receive a revised plan
acknowledging every final selected Context ID and file and the latest digest;
check it semantically; and verify again before acceptance. An implementation
worker rereading the new pointers does not cure a plan that missed the final
scope.

## Refusals

The coordinator — not a package helper — refuses a stale Snapshot digest, a
missing or unmatched verification acknowledgement, a worker-authored exception
approval, and plan acceptance before the mandatory reread has completed. Only
the coordinator authenticates user approval from durable evidence.
