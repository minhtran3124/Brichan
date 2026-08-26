# Handoff receipt

This versioned planner-to-implementer/reviewer lifecycle envelope records a
bounded handoff and its receipt. Its section headings are contract-checked;
keep the headings unchanged and in this order. Use `null` when a value is
unknown or unavailable. Do not include personal or home paths.

Store each operational receipt at
`projects/<slug>/handoffs/<task-id>/receipt.md`. Add that repo-relative path to
the project's `references.md` so progressive memory can discover it.
Historical receipts under `evals/` remain evidence; do not migrate them, and
the canonical validator does not discover them by default.

Use `standalone` for a single-writer task, `parent` for the coordinating receipt
of a multi-writer task, and `child` for each writer receipt. A child names its
canonical parent receipt using a repo-relative path. Parent and standalone
receipts use `null`.

Schema versions `1` and `2` are supported. Schema version `2` records immutable
attempt origin separately from current lifecycle state: a successful
replacement has origin `replacement` and lifecycle `complete`. Attempt `1`
uses origin `initial` with null replacement provenance. A later attempt uses
origin `replacement`, names the stale or abandoned prior session, and points to
the existing repo-relative evidence that authorized replacement. Schema-v1
receipts omit the four schema-v2 identity fields. A schema-v2 lifecycle of
`stale` or `abandoned` is valid only at accepted plan status and requires
concrete implementation evidence in the receipt.

Attempt numbering starts at `1`, with `Replaces session` set to `null`. A later
attempt names the prior session it replaces.

An `accepted` receipt may keep implementation, verification, and review values
pending. An `implemented` receipt requires passing criteria and verification
plus concrete implementation evidence. A reviewed `PASS` additionally requires
cleanup and project memory to be complete. `CHANGES REQUIRED` remains valid
with actionable findings while remediation is active.

## Identity

- Receipt schema version: `2`
- Task ID: `<task-id>`
- Project: `<project-slug>`
- Handoff timestamp (UTC): `<ISO-8601 timestamp or null>`
- Receipt role: `<standalone, child, or parent>`
- Parent receipt path: `<repo-relative path or null>`
- Attempt: `<positive integer>`
- Replaces session: `<prior session identifier or null>`
- Attempt origin: `<initial or replacement>`
- Attempt lifecycle state: `<active, complete, stale, or abandoned>`
- Prior attempt state: `<stale, abandoned, or null>`
- Replacement evidence path: `<repo-relative evidence path or null>`

## Plan version

- Artifact or plan ID: `<artifact-id or null>`
- Version: `<version or null>`
- Status: `<accepted, implemented, or reviewed>`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `<provider or null>` | `<model or null>` | `<pane-id or null>` | `<session-id or null>` |
| Implementer | `<provider or null>` | `<model or null>` | `<pane-id or null>` | `<session-id or null>` |
| Reviewer | `<provider or null>` | `<model or null>` | `<pane-id or null>` | `<session-id or null>` |

## Scope

- In scope: `<bounded deliverables>`
- Authorized paths: `<paths or null>`
- Exclusive write ownership: `<paths or null>`
- Branch: `<branch or null>`
- Worktree: `<worktree identifier or null>`

## Non-goals

- Excluded work: `<items or null>`

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| `<criterion-id>` | `<pass or fail or pending or null>` | `<evidence or null>` |

## Verification

| Command | Result |
| --- | --- |
| `<command or null>` | `<pass, fail, pending, unavailable, or null>` |

## Implementation evidence

- Changed artifacts: `<paths, pending, or null>`
- Diff evidence: `<summary, command output, pending, or null>`
- Test evidence: `<summary, command output, pending, or null>`

## Review verdict

- Verdict: `<PASS, CHANGES REQUIRED, pending, or null>`
- Findings: `<findings, pending, or null>`

## Risks and open decisions

- Risks: `<risks or null>`
- Open decisions: `<decisions or null>`

## Cleanup status

- Brida-owned panes closed: `<yes or no or null>`
- Project memory updated: `<yes or no or null>`

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
therefore out of contract for receipt embedding: Brichan must not create a
techstacks receipt for such a root. Roots containing a space, a single quote,
or a leading-dash final component are in contract and round-trip unchanged.

See `../../../../docs/policy/techstacks.md` for the packet contract and the
planning reread gate.
