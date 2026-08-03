# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `brief`
- Artifact version: `5`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md@TDW-009-P4-v4+task-packet-amendment-5`
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

## Version 5 supersession

Versions 1 to 4 are preserved byte-identically under `versions/v1/` to
`versions/v4/`. The problem and the outcome are unchanged. Two things changed:
the baseline became strong enough to prove the write scope, and a promise that
could not be kept was deleted rather than reinforced.

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
- The baseline is a **complete no-follow capture map** of every observed file
  outside an exact enumerated exclusion set — including pre-existing tracked
  changes and untracked leaves — so a change outside the 44 authorized paths is
  visible rather than assumed absent.
- An exact executable preflight must pass before any implementation write, and
  an exact executable after-delta must pass at handoff.
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
- The preflight refuses a stale baseline, an unauthenticated snapshot, and a
  planned-new collision; the after-delta puts a post-capture change to a
  pre-existing tracked file and to a pre-existing untracked file into
  `unexpected`.
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
generating the derivable half of a dossier and reporting the rest. Version 5
adds the last two things that made version 4 unshippable: a baseline complete
enough that "nothing outside the 44 paths changed" is a computed result rather
than an assertion, and the deletion of a rollback that could not be made safe.
What remains is a task whose every safety statement is either demonstrated by an
executed check or labelled a point-in-time observation.

## Evidence

- `evals/task-dossier-pilots/results.md:49-64` states the measured ceremony
  problem — 639 dossier lines against one line of fixture — and concludes that
  keeping eleven artifacts is compatible with concise generated projections.
- `projects/brida-task-dossier-workflow/decisions.md:3-15` records the user's
  accepted decision that every level keeps the complete document set and that
  file presence is not proof.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md:40-47,70-101`
  is why version 5 exists: the canonical manifest could not compute its own
  `unexpected` set, and the reviewer named the pre-existing tracked changes to
  `references.md` and `tasks.md` as the concrete proof.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:185-215`
  records the four binding version-5 decisions: the complete capture map with an
  exact exclusion set, rollback removal with fix-forward and reviewed commit
  revert, tests in already-authorized files with no forty-fifth path, and the
  `sections[].body[]` line-feed rule.
- The capture script now specified in `design.md` was executed read-only against
  this repository and against a purpose-built fixture before this brief was
  written: it produced a 333-row map including those pre-existing tracked
  changes, and it refused a stale baseline, a corrupted snapshot, a planned-new
  collision, and post-capture edits to pre-existing tracked and untracked files.

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
