# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `brief`
- Artifact version: `4`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md@TDW-009-P3-v3+task-packet-amendment-4`
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

## Version 4 supersession

Versions 1 to 3 are preserved byte-identically at `versions/v1/`, `versions/v2/`,
and `versions/v3/`. The problem and the outcome are unchanged. What changed is
that version 3 still said more than it had shown: it claimed detection it could
not guarantee, published a "valid" record example holding one of eleven
artifacts, asserted summary exits that contradicted the validator's real
discovery behaviour, and hard-coded a digest for a file the user has since
changed.

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
- **Not claimed:** neither prevention **nor detection** against a non-cooperating
  process running under the same OS identity that mutates dossier entries while
  the lock is held. The post-publication check is a **point-in-time best-effort
  observation**: it reports a mismatch only if one is present at the instant it
  runs. Version 3 called this detection; that was an overclaim and is corrected.
- **Reason, not excuse:** no Python 3.10 standard-library primitive available on
  both darwin and Linux binds a hard link's source identity to an open
  descriptor. This was tested, not assumed.

## Constraints

- All eleven artifacts survive at every level.
- Generation must not manufacture evidence, infer a verdict, overwrite an
  existing artifact, follow a symlink, escape the projects root, publish a
  truncated file, or report success when the canonical path it names no longer
  holds the dossier it wrote.
- The dossier lock is acquired immediately after the dossier descriptor is
  opened and before any temporary or artifact mutation. Safe
  descriptor-relative directory creation may precede it, because a directory
  cannot be locked before it exists.
- Summary exits follow what the validator actually discovers: an existing
  unreadable `index.md` and root-level partial adoption are invalid scope, not
  unevaluable scope.
- Ancestor-symlinked authority paths are invalid, and that invalidity is the
  validator's verdict.
- **`config/model-routing.json` is user-owned protected state.** Implementation
  must not modify, revert, or absorb it, and no planning artifact records an
  expected digest for it. Its current bytes are whatever the coordinator's
  manifest captures.
- Preservation, delta, and rollback come from the implementation-start manifest,
  which carries restorable byte snapshots — a digest alone cannot rebuild a
  reverse patch.
- Standard library only, Python 3.10 floor, checkout mode only.
- `src/brichan/resources/**` (sixteen files), `scaffold.py`, and `parser.py` are
  untouched.

## Success signal

- A Level 0 and a Level 1 sample each keep 11/11 artifacts, pass the complete
  gate against an isolated root, and measure at least 30% fewer total lines than
  the 639-line and 716-line baselines, with record size and a reproducibly
  counted authored-value total reported alongside.
- The literal complete eleven-artifact record in `design.md` is extracted by a
  test, rendered, and passes `validate_dossier` with zero diagnostics.
- Deterministic tests prove: a post-descriptor ancestor swap cannot place a file
  outside the root; namespace drift exits nonzero; two cooperating invocations
  starting from a missing dossier converge on one inode without interleaving; an
  unreadable `index.md` exits `1` while an absent scope exits `2`; and
  ancestor-symlinked authority paths are diagnosed by the validator itself.
- `make check` passes, the focused suites pass under Python 3.10, and the
  manifest proves every protected path unchanged and the delta equal to the 44
  authorized paths.

## Non-goals

- Installed-mode support, packaged resource changes, or `.brichan` migration.
- Any change to `config/model-routing.json`, `scaffold.py`, or `parser.py`.
- Any claim of prevention or detection against the excluded process.
- Wiring the summary into `make check`.
- Rewriting the three existing hand-authored pilot dossiers.
- Claiming any timing, token, or cost saving.

## Claim or decision

The ceremony problem is a repetition problem, so the intervention remains
generating the derivable half of a dossier and reporting the rest. Version 4
adds the discipline that made version 3 unshippable: every safety statement is
either demonstrated or downgraded until it matches what was demonstrated. The
worked record is complete and machine-verified, detection is restated as
opportunistic observation, exits are read off the validator's real discovery
behaviour, the lock sits where it can physically sit, and no protected file's
digest is written into a plan that outlives the user's own edits to it.

## Evidence

- `evals/task-dossier-pilots/results.md:49-64` states the measured ceremony
  problem — 639 dossier lines against one line of fixture — and concludes that
  keeping eleven artifacts is compatible with concise generated projections.
- `projects/brida-task-dossier-workflow/decisions.md:3-15` records the user's
  accepted decision that every level keeps the complete document set and that
  file presence is not proof.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md:39-47`
  is why version 4 exists: an incomplete record example, digest-only manifest,
  contradictory exits, overclaimed detection, and an impossible lock ordering.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:143-180`
  records the five binding version-4 decisions, including that the routing file's
  current bytes are user-owned protected state and that post-publication checks
  are best-effort only.
- A read-only reference renderer rendered the complete worked record now in
  `design.md` and the repository's own `validate_dossier` returned zero
  diagnostics both with and without the complete gate, at 410 rendered lines —
  inside the 447-line Level 0 budget.

## Uncertainty

- Whether operators prefer authoring a JSON record over Markdown is untested; two
  samples are not a usage study.
- The generator reduces transcription error but cannot raise evidence quality.
  Independent review remains the only control for that.
- Session-identifier inequality is a consistency signal, not proof that two
  sessions existed.
- The ownership and durability of the current `config/model-routing.json` change
  cannot be inferred from repository state. This task captures it and refuses to
  interpret it; the coordinator owns that question.
