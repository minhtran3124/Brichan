# Techstack rules

This is the canonical Brichan techstack-context policy. It governs how the
coordinator resolves a project's `techstacks/` rules, publishes the Snapshot a
worker must verify, states them in a task packet and a handoff receipt, and
regates planning when scope changes.

Resolution, Snapshot creation, publication, and verification are executable
package behavior. Packet completeness and receipt placement are coordinator
policy: no package helper accepts a packet, and none is added.

## Ownership

- `techstacks/**` belongs to the target project. Brichan never creates, edits,
  removes, repairs, or inventory-manages it.
- The sole opt-in is a regular, non-symlink `techstacks/README.md` at the exact
  validated top-level Git root. Every README is map-only; normative component
  rules live in non-README leaves such as
  `techstacks/frontend/components/Button.md`.
- Packets, receipts, plans, and project memory carry pointers, digests,
  acknowledgements, and decisions. They never carry rule bodies, Snapshot
  bytes, or a second rule authority. A worker opens the pointers itself from
  the project root it already holds.
- Brichan judges every acceptance below. A worker's assertion that it read a
  rule, verified a Snapshot, or holds an approval is a claim, not evidence.

## Resolve and publish

The coordinator supplies only an authorized Snapshot directory; it never
supplies a digest-bearing filename. Publication derives the filename from the
resolution it just performed:

```text
brichan techstacks resolve --project-root <QROOT> --input-json <QINPUT> --snapshot-directory <QDIR>
```

`QROOT`, `QINPUT`, and `QDIR` are `shlex.quote` of the actual absolute project
root and the normalized repo-relative input and directory paths.

The authorized directory is mode-specific and nothing else is accepted:

- Source checkout:
  `projects/<project-slug>/handoffs/<TASK-ID>/snapshots`
- Installed project:
  `.brichan/project-memory/techstack-snapshots/<TASK-ID>`

The published artifact is
`<attempt-id>-<snapshot-sha256>.snapshot.json` inside that directory. Each
attempt resolves once, derives its own filename, publishes missing-only, and
verifies that exact artifact. A `match` selects it and stops. A `drift` or
`blocked` observation leaves the immutable artifact in place and starts a fresh
resolve; at most three drifted observations are retried. After three
non-matching attempts the status is `observation_drift` and no artifact is
packetable. A blocked or not-applicable resolution stops with no new artifact.
Nothing is overwritten, truncated, renamed, or deleted.

Only the selected artifact of a published resolution may enter a packet or a
receipt. An unmatched attempt never may.

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

`QROOT` and `QPATH` are `shlex.quote` of the actual absolute root and the
artifact's relative path. The selected-file and required-read arrays are
byte-identical and equal the Snapshot `selected_files[*].path` values. The
acknowledged Context IDs are the unique Snapshot selected Context IDs sorted by
UTF-8 bytes.

A not-applicable packet uses exact `none`, `null`, empty selected, context, and
read arrays, and `Techstack verification requirement: not-applicable` for the
six Snapshot, read, and verify labels; it carries no artifact. A blocked
resolution cannot be packeted at all.

The complete task packet — not only the techstack block — is strict UTF-8 with
LF line endings, exactly one terminal LF, and at most 196,608 bytes. Brichan
refuses launch as `TASK_PACKET_BYTE_LIMIT` rather than truncating, omitting,
wrapping, or moving a field.

The worker returns exact
`Techstack verification acknowledgement: yes; snapshot_sha256=<digest>` only
after the literal verify command exits `0` with `match`.

## Handoff receipt

No receipt field, section, or schema version is added. The two existing
sections carry the pointers.

In `## Scope`, the `In scope` value appends the exact tokens
`Techstack snapshot pointer: <artifact path or none>; Techstack snapshot SHA-256: <digest or null>`.
The pointer is a normalized, nonempty, repo-relative POSIX path of at most
1,024 UTF-8 bytes; the digest is lowercase SHA-256 for an applicable
resolution. A not-applicable resolution appends exactly
`Techstack snapshot pointer: none; Techstack snapshot SHA-256: null`.

In `## Verification`, one row records the literal command and its result. An
applicable resolution records the verify command with `pass; snapshot_sha256=<digest>`,
or the observed failure. A not-applicable resolution records the publication
command with `pass; snapshot_sha256=null; status=not_applicable`.

The receipt parser splits every table line on the pipe character with no escape
step, and the Verification validator rejects any row that does not yield
exactly two columns. `shlex.quote` wraps a value in single quotes but never
removes or escapes a pipe, and a backslash escape is not unescaped anywhere.
A project root or Snapshot artifact path containing a pipe, CR, or LF is
therefore out of contract for receipt embedding: Brichan must not create a
techstacks receipt for such a root. Roots containing a space, a single quote,
or a leading-dash final component are in contract and round-trip unchanged.

## Planning reread

Brichan rejects plan acceptance whenever planning discovers a new path, Context
ID or chain, conflict, or exception need. When that happens Brichan must:

1. Re-resolve against the discovered scope and publish a new Snapshot.
2. Send the newly selected file pointers, the requirement to reread each
   pointer, and the new Snapshot artifact pointer to a plan worker.
3. Receive a revised plan that acknowledges every final selected Context ID and
   file and the latest digest.
4. Check the revised plan semantically, then verify again before acceptance.

An implementation worker rereading the new pointers does not cure a plan that
missed the final scope. This is an audited coordinator gate, not a package API.

## Refusals

Brichan — not a package helper — refuses:

- a stale Snapshot digest, whenever the acknowledged digest is not the latest
  published one;
- a missing or unmatched verification acknowledgement;
- a worker-authored exception approval, because only the coordinator
  authenticates user approval from durable evidence;
- plan acceptance before the mandatory reread above has completed.

Resolve and verify are read-only. They never write to `techstacks/**`, and
publication may create only its one to three immutable observation artifacts
under the authorized directory.
