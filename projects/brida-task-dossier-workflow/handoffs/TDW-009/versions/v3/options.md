# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `options`
- Artifact version: `3`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md@TDW-009-P2-v2+task-packet-amendment-3`
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

## Version 3 supersession

Versions 1 and 2 are preserved at `versions/v1/options.md` and
`versions/v2/options.md`. Decisions A through G are re-affirmed with their
original reasoning and are summarized rather than restated. Decisions H through
L are new axes forced by the version-2 review. Every prior-review citation names
an archived immutable path.

## Re-affirmed decisions A through G

| Axis | Selected | Rejected, and why |
| --- | --- | --- |
| A record interface | JSON record plus a dedicated `generate` module | Markdown master record (silent empty sections); Python-API-only (record stops being reviewable evidence); TOML (`tomllib` is 3.11+); a `--record` flag on `scaffold.py` (scaffold behaviour is now forbidden to change) |
| B summary surface | Dedicated `summary` module, text by default, JSON on request | JSON-only (does not solve reading eleven files); a `--summary` flag on the validator (changes a command wired into `make check`) |
| C write anchoring | Descriptor walk from the projects root | Pathname writes with `O_NOFOLLOW` on the final component (ancestor re-resolution); `openat2` with `RESOLVE_BENEATH` (Linux-only, no stdlib binding) |
| D publication | Temporary plus `os.link`, published on `EEXIST` refusal | Direct write to the final name (truncation becomes permanent); `os.replace` (overwrites, and takes no `dir_fd`); `O_TMPFILE` plus `linkat` (Linux-only, `AT_EMPTY_PATH` unexposed) |
| E fixtures | Unmistakably synthetic, non-authoritative | Real independently authored sample reviews (two reviewer sessions for throwaway fixtures) |
| F summary exit | Complete gate as default and only semantics | Gate only when requested (default could exit zero for an incomplete dossier) |
| G injection | Refuse structural content | Escape or quote (needs its own round-trip proof against `parser.py`) |

## Decision H: closing the raced temporary source

The version-2 review showed that `os.link(tmp, final, ..., follow_symlinks=False)`
re-resolves `tmp` by directory entry after the inode check, so a substituted
source can publish a symlink or a foreign inode.

### H1 — Descriptor-bound link source

Bind the link's source to the open descriptor rather than to a name.

- Would close the finding completely.
- Rejected as unavailable: `os.AT_EMPTY_PATH` and `os.O_TMPFILE` are not exposed
  by this CPython build, and `/proc/self/fd` does not exist on darwin. There is
  no Python 3.10 standard-library spelling of this on both platforms.

### H2 — Trigger the stop condition and abandon the design

- The version-2 plan's own stop condition permits this.
- Rejected by the coordinator, who instead narrowed the threat model. Recorded
  because it was a live option and the reviewer named it.

### H3 — Narrow the threat model, lock, and verify after publication (selected)

Declare the non-cooperating same-OS-identity mutator out of scope; take a
dossier-scoped exclusive advisory lock so cooperating writers cannot collide;
keep no-overwrite publication; verify the final entry's type and inode against
the recorded temporary immediately after linking; and re-walk the canonical
chain before reporting success.

- Strengths: covers every attacker the tool can plausibly face, converts the
  residual case from silent corruption into a named nonzero failure, and states
  the limit in the open.
- Costs: detection, not prevention, for the excluded attacker; the foreign entry
  is left in place for the operator, because deleting an unverified entry is
  forbidden.
- Fixed by the packet amendment; recorded here with its cost so the trade is
  visible.

## Decision I: the dossier lock

### I1 — `flock` on the dossier directory descriptor (selected)

- Strengths: creates no file, adds no allowlist leaf, is released automatically
  when the descriptor closes, and is already held for the duration of the walk.
- Costs: advisory only — it binds cooperating writers, which is exactly the
  population the threat model covers.
- Confirmed: an exclusive non-blocking lock on a directory descriptor succeeded
  and a second holder was refused.

### I2 — A `.lock` file inside the dossier

- Rejected: adds a leaf to the closed evaluation allowlist, needs its own
  creation, cleanup, and staleness rules, and can be left behind by a crash.

### I3 — No lock

- Rejected: version 2's position. It leaves ordinary concurrent Brichan
  invocations — the common, cooperating case — racing each other, which is
  squarely inside the threat model.

## Decision J: ancestor-symlinked authority paths

### J1 — Make them validator-invalid (selected)

Add one shared ancestor helper and one call site in each of the two link
validators, plus regression tests.

- Strengths: one authority produces one verdict; the summary reports it; the
  version-2 contradiction disappears.
- Costs: expands the authorized `validation.py` scope from two hunks to five,
  adds two new diagnostics, and is a behaviour change for any checkout that has
  such a symlink.
- Fixed by the packet amendment.

### J2 — Keep the summary report informational and drop the nonzero promise

- Strengths: no validator change at all.
- Rejected: it weakens an accepted criterion, and it leaves an invalid authority
  link reported but tolerated.

### J3 — Let the summary decide invalidity itself

- Rejected outright: it creates the second validity authority the whole design
  forbids.

## Decision K: record artifact-version type

The version-2 example used the string `"1"` while its diagnostic table treated
the same key as an integer position.

### K1 — Integer with an exhaustive key-to-type table (selected)

- Strengths: the boolean-rejection test has a real target; the rendered value is
  `str(value)`, so output is unchanged; one table settles every key.
- Costs: record authors must write `1`, not `"1"`.

### K2 — String, with a digit-pattern check

- Rejected: it makes the exact-type rule vacuous for the one key the review
  named, and a string version would need its own numeric validation anyway.

## Decision L: backticks in free-text positions

Version 2 refused backticks in every single-line scalar, which contradicted its
own example and would have made ordinary `path:line` evidence unwritable.

### L1 — Refuse per rendered position class (selected)

Backtick-wrapped positions — metadata values, extra-section field values, index
identity values — refuse backticks and pipes, because the renderer wraps them in
a code span that a backtick would terminate. Free-text positions — evidence
items, uncertainty items, section titles — permit backticks, because a backtick
cannot create a section, field, table row, or list item under `parser.py`.

- Strengths: every refusal is justified by the parser primitive it protects; the
  worked example becomes valid; real evidence stays writable.
- Costs: two rule sets instead of one.

### L2 — Refuse backticks everywhere

- Rejected: it would forbid the single most common evidence form in this
  repository, and the version-2 example already violated it.

## Selected decision

A1, B1, C2, D3, E2, F1, G1, H3, I1, J1, K1, L1. Promoted into `design.md`.

## Claim or decision

The version-3 decisions are all consequences of one principle: keep only the
guarantees that can be demonstrated, and say plainly which ones were dropped.
`H1` was tested and found unavailable, so `H3` narrows the boundary in the open
rather than restating a promise the standard library cannot keep. `I1` covers
the cooperating writers that actually exist. `J1` removes a contradiction by
giving the single authority the check it was already assumed to have. `K1` and
`L1` remove two self-contradictions from the record schema, and `L1` in
particular is what makes the format usable for real `path:line` evidence.

## Evidence

- Direct execution on this platform decided `H1`, `H3`, and `I1` before they were
  selected: `os.link` with `follow_symlinks=False` over a symlinked source
  published a symlink at the destination; a post-publication
  `os.lstat(final, dir_fd=...)` against the recorded temporary inode separated
  that from an honest publication; `fcntl.flock(dir_fd, LOCK_EX | LOCK_NB)`
  succeeded and refused a second holder with `EWOULDBLOCK`; and neither
  `os.AT_EMPTY_PATH` nor `os.O_TMPFILE` is exposed, with no `/proc/self/fd` on
  darwin.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md:64-89`
  states the source-name race and names exactly two acceptable resolutions, one
  of which is the narrowing `H3` adopts.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md:93-113`
  establishes `J1`'s necessity against source: the receipt check at
  `validation.py:782-824` tests only `is_symlink` and `is_file`, and the memory
  check at `validation.py:827-885` tests the final candidate and containment but
  no ancestor.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md:160-174`
  states the `K1` and `L1` contradictions precisely — a string version against an
  integer diagnostic position, and a backticked evidence value against a rule
  refusing every backtick.
- `src/brichan/contracts/task_dossier/parser.py:40-47,57-74,77-87,90-95` fixes
  what each `L1` rule protects: sections key on `^## `, fields on `- Label:`,
  tables on lines that start and end with a pipe, and list items on a stripped
  `- ` prefix. A backtick appears in none of them.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:104-124`
  records the coordinator decisions that fix `H3`, `I1`, `J1`, and the
  implementation-start manifest.

## Uncertainty

- `H3` leaves a real, stated gap. If a future CPython exposes a descriptor-bound
  link, `H1` becomes available and the narrowing should be revisited. Nothing in
  the design depends on the narrowing being permanent.
- `I1` is advisory. A writer that ignores the lock is by definition the excluded
  attacker, so the lock's value is bounded by the same statement that bounds
  `H3`; it is not additional protection against that case.
- `J1`'s behaviour change cannot be measured beyond this checkout. No symlink
  exists anywhere here outside `.git` and `.venv`, so no existing dossier
  changes verdict, but a downstream checkout could newly fail.
- No unresolved uncertainty remains about which branch to take on `H`, `I`, or
  `J`: the packet amendment fixes all three.
