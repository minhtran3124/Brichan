# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `options`
- Artifact version: `2`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/plan-review.md@TDW-009-P1-v1+task-packet-amendment`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `3ebc7268-a8cd-464c-8d65-9920f2beac5c`
- Effective route: `plan`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Version 2 supersession

Version 1 is preserved byte-identically at `versions/v1/options.md`. Decisions A
and B are re-affirmed with their original reasoning; decisions C through G are
new axes that independent review forced into the open. Where the task-packet
amendment fixes an answer, the option comparison is still recorded, because the
rejected branch is what a later reader needs in order to understand the cost.

## Decision A: structured-record and generation interface

Five options were compared in version 1 and the outcome is unchanged.

- **A1 — JSON record plus a dedicated `generate` module and thin wrapper.**
  Selected. `json` is standard library on the 3.10 floor, parse failures carry
  line and column, the record is diffable and machine-checkable, and generation
  stays out of the scaffold's single responsibility.
- **A2 — Markdown master record parsed by `parser.py`.** Rejected on failure
  quality: `parse_sections` uses `setdefault`, so a mistyped heading yields an
  empty section instead of a named refusal.
- **A3 — Python API only, no file format.** Rejected as the primary interface;
  retained as the internal dataclass seam that A1 exposes.
- **A4 — TOML via `tomllib`.** Rejected on a version fact: `tomllib` is 3.11+
  and `pyproject.toml:12` pins `>=3.10`.
- **A5 — a `--record` flag on `scaffold.py`.** Rejected in version 1 to protect
  the scaffold's "never fills evidence" guarantee; version 2 strengthens the
  rejection, because the packet amendment now forbids changing scaffold
  behaviour at all.

## Decision B: summary output and API

- **B1 — dedicated `summary` module and wrapper, human text by default with a
  JSON form.** Selected. One computed structure rendered two ways; `make
  dossiers` and its output contract untouched.
- **B2 — JSON only.** Rejected as the sole form; adopted as the secondary form
  inside B1.
- **B3 — a `--summary` flag on `validate_task_dossiers.py`.** Rejected: that
  command is wired into `make dossiers` and `make check` at `Makefile:44-45,67`,
  so changing its output or exit-code space changes a repository gate.

## Decision C: write anchoring

### C1 — Pathname writes with `O_NOFOLLOW` on the final component (version 1, rejected)

Preflight the dossier path, then `os.open(full_path, ..., O_NOFOLLOW)` per
artifact.

- Cost: `O_NOFOLLOW` constrains only the last component. Every intermediate
  directory is re-resolved on each open, so an ancestor swapped between preflight
  and write is followed. This is the critical finding.
- Rejected. No amount of extra preflight closes it, because the check and the
  open are separate resolutions of the same name.

### C2 — Descriptor walk from the projects root (selected)

Open the projects root once, then walk `<project>`, `handoffs`, `<task-id>` with
`O_RDONLY | O_DIRECTORY | O_NOFOLLOW` relative to the already-open parent, and
perform every subsequent operation with `dir_fd`.

- Strengths: a swapped ancestor after the descriptor exists cannot redirect
  anything, because the descriptor names an inode rather than a path. A swapped
  ancestor before the open is refused by `O_NOFOLLOW`. There is no window
  between the two.
- Costs: a generator-specific writer that does not share code with the scaffold,
  and POSIX-only semantics.
- Confirmed available: `os.open`, `os.mkdir`, `os.stat`, `os.link`, and
  `os.unlink` all report `dir_fd` support on this platform.

### C3 — `openat2` with `RESOLVE_BENEATH`

- Strengths: the kernel enforces containment directly.
- Rejected: `openat2` is Linux-specific and has no CPython standard-library
  binding on the 3.10 floor. `PRODUCT.md:58` also names broad multi-platform
  support a non-goal, and a Linux-only path would make the capability behave
  differently per platform.

## Decision D: artifact publication

### D1 — Write directly to the final name (version 1, rejected)

- Cost: a short write, encoding error, flush failure, close failure, or full
  filesystem leaves a truncated file at the final name. Every later run then
  classifies it `preserve`, so the record cannot recover it without manual
  deletion.
- Rejected.

### D2 — Temporary file plus `os.replace`

- Cost: `os.replace` overwrites its destination by design, which is the single
  behaviour this contract must never have. It also does not accept `dir_fd`, so
  it cannot be used descriptor-relative under C2.
- Rejected on both grounds.

### D3 — Temporary file plus `os.link`, published on `EEXIST` refusal (selected)

Create a private temporary in the dossier directory, write it fully, `fsync` it,
verify its device and inode against the writing descriptor, then
`os.link(temp, final, src_dir_fd, dst_dir_fd, follow_symlinks=False)` and unlink
the identity-verified temporary.

- Strengths: publication is a single atomic operation that either creates the
  final name or fails `EEXIST`; a partially written body is never reachable
  under the final name; the no-overwrite guarantee is enforced by the kernel
  rather than by a prior existence check.
- Costs: a temporary file exists transiently, and a hard link requires the
  temporary and the final name to share a filesystem — guaranteed here, because
  both live in the same directory.
- Confirmed: linking onto an existing name failed with `EEXIST` and left the
  original bytes intact.

### D4 — `O_TMPFILE` plus `linkat`

- Strengths: no temporary name ever appears in the directory.
- Rejected: `O_TMPFILE` is Linux-specific and absent on darwin, and linking an
  unnamed file requires `AT_EMPTY_PATH`, which CPython does not expose.

## Decision E: evaluation fixture honesty

### E1 — Real independently authored sample reviews and coordinator receipts

- Strengths: sample `PASS` verdicts would be real evidence.
- Costs: two additional independent reviewer sessions and coordinator-authored
  receipts for throwaway fixtures, and a permanent obligation to re-review the
  samples whenever they are regenerated.

### E2 — Unmistakably synthetic, non-authoritative fixtures (selected)

- Strengths: no reader can mistake fixture data for evidence; no reviewer time is
  spent on throwaway samples; the real evidence trail stays TDW-009's own
  dossier.
- Costs: the samples prove the generator can produce a complete-gate-passing
  dossier, and nothing about review quality. That limit must be stated in the
  evaluation rather than left implicit.
- Fixed by the task-packet amendment; recorded here with its cost.

## Decision F: summary exit default

### F1 — The complete gate is the default and only exit semantics (selected)

- Strengths: matches `TDW-009-AC4` literally; an incomplete dossier can never
  exit zero.
- Costs: summarizing an in-progress dossier always exits nonzero. Acceptable,
  because the report still prints in full and the command is not wired into any
  gate.

### F2 — Complete gate only when requested (version 1, rejected)

- Cost: `validate_dossier` with the gate off accepts `pending`, `active`, and
  `blocked`, so the default summary could exit zero for an incomplete dossier —
  a direct contradiction of the accepted criterion.
- Rejected, and the amendment forbids a relaxed default.

## Decision G: structural injection handling

### G1 — Refuse structural characters and structural lines (selected)

- Strengths: one closed rule set, one named diagnostic per class, no dependence
  on the renderer and the validator's parser agreeing about escaping.
- Costs: a claim containing a pipe, or evidence quoting a fenced block, cannot
  be written through a record and must be hand-authored.

### G2 — Escape or quote structural content

- Strengths: no legitimate prose is unwritable.
- Rejected: an escaping rule needs its own round-trip proof that no escaped form
  can parse as a heading, field, table row, or extra evidence bullet under
  `parser.py`. That proof is larger than the feature it enables.

## Selected decision

A1, B1, C2, D3, E2, F1, G1. Promoted into `design.md`.

## Claim or decision

The two decisions that changed between versions are the ones that carried the
critical and high findings: pathname writes are replaced by a descriptor walk
(C1 to C2), and direct final-name writes are replaced by hard-link publication
(D1 to D3). Both alternatives that look simpler — `os.replace` and
`O_TMPFILE` — were rejected on mechanical facts rather than on preference: the
first overwrites and cannot take a `dir_fd`, the second does not exist on one of
the two platforms in scope. The three coordinator-fixed axes are recorded with
their rejected branches so the cost of each decision stays visible.

## Evidence

- Direct execution on this platform established the C2 and D3 facts before they
  were selected: `os.open`, `os.mkdir`, `os.stat`, `os.link`, and `os.unlink`
  report `dir_fd` support while `os.replace` does not; a link onto an existing
  name raised `EEXIST` and preserved the original content; and opening a
  symlinked directory with `O_DIRECTORY | O_NOFOLLOW` failed rather than
  following the link.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan-review.md:47-72`
  supplies the C1 rejection in source terms — one-time containment resolution at
  `scaffold.py:87-95`, a final-component-only preflight at `scaffold.py:117-118`,
  and pathname opens at `scaffold.py:188-202`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan-review.md:76-96`
  supplies the D1 rejection: a partially written final artifact is preserved by
  every later run, which turns a transient fault into permanent corruption.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:73-81`
  fixes E2, F1, and C2 as coordinator decisions, and forbids the scaffold change
  that version 1's A5 rejection had already made unattractive.
- `pyproject.toml:12` pins `requires-python = ">=3.10"` and `PRODUCT.md:57-58`
  names third-party runtime dependencies and broad multi-platform support as
  explicit non-goals, which together reject A4, C3, and D4.
- `Makefile:44-45,67` shows `validate_task_dossiers.py projects` wired into both
  `dossiers` and `check`, the concrete cost that rejects B3.

## Uncertainty

- C2 leaves one boundary open: the projects root itself is opened by pathname, so
  a symlinked ancestor above the operator-supplied root is trusted. This matches
  the existing scaffold and validator and is recorded rather than closed.
- D3 leaves a transient temporary file visible in the dossier directory. A
  crash between creation and publication leaves an orphan whose name is
  recognisable and whose removal is safe, but nothing in this task sweeps it;
  `design.md` records the cleanup rule and its identity check instead.
- E2 bounds what the evaluation can prove. It cannot show that the generator
  produces review-worthy content, only that it produces contract-valid content.
  No unresolved uncertainty remains about which branch to take, since the
  amendment fixes it.
