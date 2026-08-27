# Handoff receipt

A versioned planner-to-implementer/reviewer envelope. Section headings are
contract-checked: keep them unchanged and in this order. Use `null` when a
value is unknown. Do not include personal or home paths.

Store each operational receipt at
`projects/<slug>/handoffs/<task-id>/receipt.md` in a source checkout, or under
`.brichan/project-memory/` in an installed project, and add that repo-relative
path to the project's `references.md`.

Use `standalone` for a single-writer task, `parent` for the coordinating
receipt of a multi-writer task, and `child` for each writer receipt. A child
names its canonical parent receipt with a repo-relative path; parent and
standalone receipts use `null`.

Schema versions `1` and `2` are supported. Schema version `2` records immutable
attempt origin separately from current lifecycle state. Attempt `1` uses origin
`initial` with null replacement provenance; a later attempt uses origin
`replacement`, names the stale or abandoned prior session, and points to the
existing repo-relative evidence that authorized replacement.

## Sections

- `## Identity` — receipt schema version, task ID, project, timestamp, receipt
  role, parent receipt path, attempt, replaces session, and the schema-v2
  attempt origin, attempt lifecycle state, prior attempt state, and replacement
  evidence path.
- `## Plan version` — artifact or plan ID, version, and status.
- `## Sessions` — one row per planner, implementer, and reviewer role.
- `## Scope` — in scope, authorized paths, exclusive write ownership, branch,
  and worktree.
- `## Non-goals` — excluded work.
- `## Acceptance criteria` — one row per criterion with status and evidence.
- `## Verification` — a two-column table of command and result.
- `## Implementation evidence` — changed artifacts, diff evidence, test
  evidence.
- `## Review verdict` — verdict and findings.
- `## Risks and open decisions` — risks and open decisions.
- `## Cleanup status` — panes closed and project memory updated.

## Techstack pointers

A techstack resolution adds no receipt field, section, or schema version. Two
existing sections carry it, as prose values only.

In `## Scope`, the `In scope` value appends the exact tokens
`Techstack snapshot pointer: <artifact path or none>; Techstack snapshot SHA-256: <digest or null>`.
The pointer is a normalized, nonempty, repo-relative POSIX path of at most
1,024 UTF-8 bytes and the digest is lowercase SHA-256 for an applicable
resolution. A not-applicable resolution appends exactly
`Techstack snapshot pointer: none; Techstack snapshot SHA-256: null`.

In `## Verification`, one row records the literal command and its result. An
applicable resolution records
`brichan techstacks verify --project-root <QROOT> --snapshot-json <QSELECTED> --as-of <YYYY-MM-DD>`
with result `pass; snapshot_sha256=<digest>`, or the observed failure. A
not-applicable resolution records
`brichan techstacks resolve --project-root <QROOT> --input-json <QINPUT> --snapshot-directory <QDIR>`
with result `pass; snapshot_sha256=null; status=not_applicable`. `QROOT`,
`QSELECTED`, `QINPUT`, and `QDIR` are `shlex.quote` of the actual absolute root
and the normalized repo-relative paths.

The receipt parser splits every table line on the pipe character with no escape
step, and the Verification validator rejects any row that does not yield
exactly two columns. `shlex.quote` wraps a value in single quotes but never
removes or escapes a pipe, and a backslash escape is not unescaped anywhere. A
project root or Snapshot artifact path containing a pipe, CR, or LF is
therefore out of contract for receipt embedding: do not create a techstacks
receipt for such a root. Roots containing a space, a single quote, or a
leading-dash final component are in contract and round-trip unchanged.

See `.brichan/policy/techstacks.md` for the packet contract and the planning
reread gate.
