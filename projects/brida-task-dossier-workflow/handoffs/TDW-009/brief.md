# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `brief`
- Artifact version: `7`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v6/plan-review.md@TDW-009-P6-v6+task-packet-amendment-7`
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

## Version 7 supersession

Versions 1 to 6 are preserved byte-identically under `versions/v1/` to
`versions/v6/`. The problem, the outcome, and the no-rollback stance are
unchanged. What changed is that a supplied manifest can no longer redefine what
implementation may touch, or make the worker read outside the checkout.

| Defect found in version 6 | Correction in version 7 |
| --- | --- |
| Counting 8 / 36 / 44 let a same-count substitution redefine the authorization and pass both gates | The exact sorted 8-path and 36-path tuples are **frozen inside the reviewed executable**; the union is derived from them; equality is required, not counting |
| `snapshot_dir` could be absolute or reach through an ancestor symlink | **One frozen repository-relative path**, walked component by component from the repository descriptor with `O_DIRECTORY \| O_NOFOLLOW` |
| The required generator routing probe existed as a requirement but in no ordered step | **Both arms are now explicit in the ordered generator unit-test step** |
| The strict loader accepted a boolean version and malformed length/digest rows | Exact non-boolean integer version, nonnegative lengths, 64 lowercase hex digests, zero-length and zero-digest for non-file rows |

## Problem

The three-lane pilot proved the full-document contract works and priced it. A
one-line Level 0 change cost 639 lines of hand-authored dossier prose across
eleven artifacts; the Level 1 lane cost 716. Most of that volume is not
judgment — it is sixteen metadata fields repeated eleven times, an eleven-row
status table restating what each artifact already declares, two link fields
derivable from the dossier path, and a template lede copied into every file.

The second cost is inspection: answering "is this dossier sound?" means opening
eleven files and cross-reading sessions, verdicts, evidence counts, and link
targets by eye.

## Outcome

1. **Generator** — one structured record renders all eleven artifacts, deriving
   only what is mechanically derivable and refusing to invent anything else.
2. **Summary** — one deterministic read-only report whose verdict is the
   validator's.

## What this task will and will not claim

- **Claimed:** safety against pre-existing symlinks at any path component,
  against namespace drift the generator can observe, against ordinary concurrent
  Brichan invocations that cooperate with the dossier lock, and against every
  specified write, `fsync`, close, link, cleanup, and directory-`fsync` failure.
- **Not claimed:** neither prevention nor detection against a non-cooperating
  process running under the same OS identity. The post-publication check, the
  capture map, the start preflight, and the after-delta check are all
  **point-in-time observations**, never compare-and-swap.
- **Reason, not excuse:** no Python 3.10 standard-library primitive available on
  both darwin and Linux binds a hard link's source identity to an open
  descriptor. This was tested, not assumed.

## No rollback

TDW-009 contains no rollback — no promise, no procedure, no test, no command.

- On implementation failure the worker **fixes forward** within its 44
  authorized paths.
- After a successful scoped commit, recovery is a **separately reviewed commit
  revert**, requested from the coordinator and outside this task.
- Snapshots of the eight modified tracked paths exist **only as evidence**. No
  worker may restore from, delete from, or write through one. `git checkout --`
  is forbidden on every path.

Version 4 specified an identity-checked rollback; review showed it compared
bytes rather than identity, could follow a symlink into a different target, and
restored snapshots that were never authenticated. A portable pathname procedure
cannot offer compare-and-swap safety against a concurrent same-identity process,
so the honest move is to remove it, not to deepen it.

## Constraints

- All eleven artifacts survive at every level.
- Generation must not manufacture evidence, infer a verdict, overwrite an
  existing artifact, follow a symlink, escape the projects root, publish a
  truncated file, or report success when the canonical path it names no longer
  holds the dossier it wrote.
- The baseline is **one canonical JSON manifest** holding a complete no-follow
  map of every observed file outside an exact ten-entry exclusion set — including
  pre-existing tracked changes, pre-existing untracked leaves, and every symlink
  whether it points at a file or a directory. The same executable emits and
  consumes it; there is no second representation.
- The 8-path modified set and the 36-path new set are **frozen inside the
  reviewed executable**, not merely inside the manifest. The loader requires
  element-for-element equality and derives the 44-path union from the constants,
  so neither a truncated list nor a same-count substitution can narrow or
  redefine a gate.
- The snapshot directory is **one frozen repository-relative path** opened
  component by component from the repository descriptor with
  `O_DIRECTORY | O_NOFOLLOW`; absolute, traversing, backslash, non-excluded, and
  alternate values are refused.
- An exact executable preflight must pass before any implementation write, and
  the after-delta must show the touched set equal to **all 44** authorized paths;
  a strict subset and a strict superset both fail.
- Both generator routing-neutrality arms — forbidden-spelling source inspection
  and import plus a real dry-run under a path-open spy — are ordered steps in the
  generator unit-test suite, not merely stated requirements.
- Ancestor-symlinked authority paths are invalid, and that invalidity is the
  validator's verdict.
- `config/model-routing.json` is user-owned protected state: not modified, not
  reverted, not absorbed, not interpreted, and never given an expected digest in
  any planning artifact.
- Standard library only, Python 3.10 floor, checkout mode only.
- `src/brichan/resources/**`, `scaffold.py`, and `parser.py` are untouched.
- The implementation allowlist stays at exactly **44 paths**; new tests go in
  already-authorized test files.

## Success signal

- A Level 0 and a Level 1 sample each keep 11/11 artifacts, pass the complete
  gate against an isolated root, and measure at least 30% fewer total lines than
  the 639-line and 716-line baselines, with record size and a reproducibly
  counted authored-value total alongside.
- The literal complete eleven-artifact record in `design.md` is extracted by a
  test, rendered, and passes `validate_dossier` with zero diagnostics.
- The literal capture block extracts from `design.md` and runs on Python 3.10:
  canonical capture and clean preflight passing; a full 44-path touch passing;
  under-touch and over-touch failing; symlink-directory retarget and type
  replacement failing; outside-allowlist tracked and untracked changes failing;
  same-count member substitution, misclassification, and a forged full-44 delta
  failing; absolute, traversing, non-excluded, alternate, and ancestor-symlinked
  `snapshot_dir` failing; and boolean version, negative length, and malformed
  digest failing.
- An embedded line feed in `sections[].body[]` is refused while a safe
  multi-line `claim` is accepted.
- `make check` passes, the focused suites pass under Python 3.10, and the delta
  equals exactly the 44 authorized paths.

## Non-goals

- Installed-mode support, packaged resource changes, or `.brichan` migration.
- Any change to `config/model-routing.json`, `scaffold.py`, or `parser.py`.
- Any rollback, restore, or delete-from-snapshot behaviour.
- Any claim of prevention or detection against the excluded process.
- A forty-fifth authorized path.
- Wiring the summary into `make check`.
- Claiming any timing, token, or cost saving.

## Claim or decision

The ceremony problem is a repetition problem, so the intervention remains
generating the derivable half of a dossier and reporting the rest. Version 7
closes the last way the gate could be talked out of its job: the authorization is
frozen in the reviewed tool rather than supplied alongside it, and the one place
the worker reads coordinator-provided bytes is pinned to a single path opened
without ever following a link. Every correction was extracted from `design.md`
and executed on Python 3.10 before this artifact was called passed.

## Evidence

- `evals/task-dossier-pilots/results.md:49-64` states the measured ceremony
  problem — 639 dossier lines against one line of fixture.
- `projects/brida-task-dossier-workflow/decisions.md:3-15` records the user's
  accepted decision that every level keeps the complete document set.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v6/plan-review.md:31-41`
  is why version 7 exists: same-count substitutions redefined the authorization,
  the snapshot directory was neither confined nor opened without following
  ancestor symlinks, the generator probe was unplanned, and the loader accepted
  malformed values.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:266-296`
  records the four binding version-7 decisions.
- The literal capture block was extracted from `design.md` and run on Python
  3.10.11 across twenty-three probes before this brief was written: five for the
  frozen allowlists including a forged full-44 delta, eight for `snapshot_dir`
  containment and ancestor symlinks, seven for malformed manifest values, plus a
  clean canonical capture and preflight; and the thirteen-scenario version-6
  regression matrix was re-run under the version-7 executable with every expected
  exit code.

## Uncertainty

- Whether operators prefer authoring a JSON record over Markdown is untested.
- The generator reduces transcription error but cannot raise evidence quality.
- Session-identifier inequality is a consistency signal, not proof of review.
- Removing rollback means a failed implementation leaves partial work in the tree
  until a coordinator-reviewed revert.
- Excluding `.env` and `.DS_Store` means changes to them are invisible here.
- Freezing the 44 paths and the snapshot directory in the executable couples the
  plan to the tool: any scope or layout change now requires editing and
  re-reviewing that block.
- The capture, preflight, and delta are point-in-time observations; a
  same-identity process mutating files between two observations defeats them.
