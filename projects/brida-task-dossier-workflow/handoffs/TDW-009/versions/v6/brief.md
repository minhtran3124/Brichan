# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `brief`
- Artifact version: `6`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v5/plan-review.md@TDW-009-P5-v5+task-packet-amendment-6`
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

## Version 6 supersession

Versions 1 to 5 are preserved byte-identically under `versions/v1/` to
`versions/v5/`. The problem, the outcome, and the no-rollback stance are
unchanged. What changed is that the implementation-start gate and the handoff
delta now actually work: the replacement review of version 5 reproduced three
executable defects, and each is corrected and re-run here.

| Defect found in version 5 | Correction in version 6 |
| --- | --- |
| The executable could not consume the canonical capture it was told to produce | **One canonical JSON manifest**, emitted and consumed by the same strict parser |
| A symlink pointing at a directory produced no row, so retargeting it was invisible | Every directory-name entry is `lstat`-ed; a symlink becomes an `l` row and is never traversed |
| A truncated path list and a strict subset of the 44-path delta both passed | Allowlists live inside the manifest, validated to exactly 8 / 36 / 44, and the delta must touch **all 44** |

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
- The 8-path modified set, the 36-path new set, and their 44-path union live
  **inside** the manifest and are validated for exact equality before any state
  is examined, so no truncated external list can narrow a gate.
- An exact executable preflight must pass before any implementation write, and
  the after-delta must show the touched set equal to **all 44** authorized paths;
  a strict subset and a strict superset both fail.
- A generator static and import probe proves generator code neither reads nor
  names `config/model-routing.json`.
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
  canonical capture, clean preflight, a full 44-path touch passing, an
  under-touch failing, an over-touch failing, a symlink-directory retarget and
  type replacement failing, and outside-allowlist tracked and untracked changes
  failing.
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
generating the derivable half of a dossier and reporting the rest. Version 6
adds the one thing version 5 lacked: gates that actually run. The manifest a
coordinator is told to produce is now the exact JSON the code parses, every
symlink is a row wherever it is found, and the delta fails on a strict subset as
loudly as on a strict superset. Each correction was extracted from `design.md`
and executed on Python 3.10 before this artifact was called passed.

## Evidence

- `evals/task-dossier-pilots/results.md:49-64` states the measured ceremony
  problem — 639 dossier lines against one line of fixture — and concludes that
  keeping eleven artifacts is compatible with concise generated projections.
- `projects/brida-task-dossier-workflow/decisions.md:3-15` records the user's
  accepted decision that every level keeps the complete document set and that
  file presence is not proof.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v5/plan-review.md:31-40`
  is why version 6 exists: the exact block was incompatible with the canonical
  format it had to consume, omitted symlinks to directories, and enforced
  neither all 36 planned-new paths nor exact touched-set equality.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:229-262`
  records the four binding version-6 decisions: one canonical JSON manifest,
  symlink rows in both name positions, fail-closed 8/36/44 and touched-set
  equality, and a generator static and import routing probe.
- The literal capture block was extracted from `design.md` and run on Python
  3.10.11 across twelve scenarios before this brief was written: canonical
  capture, clean preflight, full 44-path touch passing, under-touch failing,
  over-touch failing, symlink-directory retarget failing at both preflight and
  delta, symlink-directory replaced by a real directory and by a regular file
  each failing, outside-allowlist tracked and untracked changes failing, and a
  restored baseline passing again.
- Run against this repository, the extracted block produced 333 rows with
  8 / 36 / 44 allowlists, `config/model-routing.json` at its current user-owned
  bytes, and all 16 files under `src/brichan/resources/`.

## Uncertainty

- Whether operators prefer authoring a JSON record over Markdown is untested;
  two samples are not a usage study.
- The generator reduces transcription error but cannot raise evidence quality.
- Session-identifier inequality is a consistency signal, not proof that two
  sessions existed.
- Removing rollback means a failed implementation leaves partial work in the
  tree until a coordinator-reviewed revert. That is the accepted cost.
- Excluding `.env` and `.DS_Store` from the capture map means changes to them
  are invisible to every check in this task.
- The capture map, preflight, and delta are point-in-time observations; a
  same-identity process mutating files between two observations defeats all of
  them.
