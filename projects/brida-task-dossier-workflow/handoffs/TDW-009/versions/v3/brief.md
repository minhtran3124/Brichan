# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `brief`
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

Versions 1 and 2 are preserved byte-identically at `versions/v1/brief.md` and
`versions/v2/brief.md`. The problem and the outcome are unchanged. What changed
is what this task is now willing to claim: version 2 promised concurrency
protection it could not deliver with the standard library, and promised a
nonzero summary exit that the unchanged validator could not produce. Version 3
replaces both promises with ones that hold.

Every prior-review citation in these artifacts names an archived immutable path,
never the mutable `plan-review.md`.

## Problem

The three-lane pilot proved the full-document contract works and priced it. A
one-line Level 0 change cost 639 lines of hand-authored dossier prose across
eleven artifacts; the Level 1 lane cost 716. Most of that volume is not
judgment — it is sixteen metadata fields repeated eleven times, an eleven-row
status table restating what each artifact already declares, two link fields
derivable from the dossier path, and a template lede copied into every file.

The second cost is inspection. Answering "is this dossier sound?" means opening
eleven files and cross-reading sessions, verdicts, evidence counts, and link
targets by eye.

## Outcome

1. **Generator** — one structured record renders all eleven artifacts, deriving
   only what is mechanically derivable and refusing to invent anything else.
2. **Summary** — one deterministic read-only report of artifact state, evidence
   depth, provenance, plan and review identity, authority-link health, and
   review independence, whose verdict is the validator's.

## What this task will and will not claim

Stated here so no later artifact softens it.

- **Claimed:** safety against pre-existing symlinks at any path component,
  against namespace drift the generator can observe, against ordinary
  concurrent Brichan invocations that cooperate with the dossier lock, and
  against every specified write, `fsync`, close, link, cleanup, and
  directory-`fsync` failure.
- **Not claimed:** protection against a non-cooperating process running under the
  same OS identity that mutates dossier directory entries while the generator
  holds the lock. That is outside this repository tooling's threat model. The
  generator detects the resulting bad publication and fails the run; it does not
  prevent it and does not remove the foreign entry.
- **Reason, not excuse:** no Python 3.10 standard-library primitive available on
  both darwin and Linux binds a hard link's source identity to an open
  descriptor. This was tested, not assumed.

## Constraints

- All eleven artifacts survive at every level.
- Generation must not manufacture evidence, infer a verdict, overwrite an
  existing artifact, follow a symlink, escape the projects root, publish a
  truncated file, or report success when the canonical path it names no longer
  holds the dossier it wrote.
- Ancestor-symlinked authority paths are invalid, and that invalidity is the
  validator's verdict — the summary reports it and never invents a second one.
- Evaluation samples are synthetic fixtures; nothing in them may be presented as
  evidence of real review.
- Preservation, delta, and rollback come from a coordinator-captured
  implementation-start manifest, never from `HEAD`.
- Standard library only, Python 3.10 floor, checkout mode only.
- `config/model-routing.json`, `src/brichan/resources/**`, `scaffold.py`, and
  `parser.py` are untouched.

## Success signal

- A Level 0 and a Level 1 sample each keep 11/11 artifacts, pass the complete
  gate against an isolated root, and measure at least 30% fewer total lines than
  the 639-line and 716-line baselines, with record size and a reproducibly
  counted authored-value total reported alongside.
- The summary reports every field named in `TDW-009-AC4`, takes its verdict from
  `validate_projects` under a non-negotiable complete gate, and distinguishes an
  unreadable artifact (exit 1) from an unreadable dossier (exit 2).
- Deterministic tests prove: a post-descriptor ancestor swap cannot place a file
  outside the root; namespace drift exits nonzero rather than reporting success;
  a substituted temporary source is detected and fails the run; and
  ancestor-symlinked authority paths are diagnosed by the validator itself.
- `make check` passes, the focused suites pass under Python 3.10, and the
  implementation-start manifest proves the routing manifest, every resource file,
  and the three pilot dossiers are byte-identical.

## Non-goals

- Installed-mode support, packaged resource changes, or `.brichan` migration.
- Any new key in the routing manifest.
- Any change to `scaffold.py` or `parser.py`.
- Any claim of protection against the excluded attacker.
- Wiring the summary into `make check`.
- Rewriting the three existing hand-authored pilot dossiers.
- Claiming any timing, token, or cost saving.

## Claim or decision

The ceremony problem is a repetition problem, so the intervention remains
generating the derivable half of a dossier and reporting the rest. Version 3
adds that this is only worth shipping if every safety statement it makes is one
it can demonstrate: writes anchored to descriptors, publication that never
overwrites and is verified after the fact, a final canonical re-walk so a
contained-but-detached run cannot report success, one validator that owns
authority-link validity, and an explicitly narrowed concurrency boundary stated
in the open rather than implied by silence.

## Evidence

- `evals/task-dossier-pilots/results.md:49-64` states the measured ceremony
  problem — 639 dossier lines against one line of fixture — and concludes that
  keeping eleven artifacts is compatible with concise generated projections.
- `projects/brida-task-dossier-workflow/decisions.md:3-15` records the user's
  accepted decision that every level keeps the complete document set and that
  file presence is not proof.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md:31-39,64-89`
  is why version 3 exists: the reviewer judged version 2 unsafe to implement
  because the publication step re-resolves its temporary source name after the
  identity check, and named threat-model narrowing with recorded acceptance as
  an acceptable resolution.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:99-133`
  records the three binding version-3 decisions — the excluded attacker, the
  validator-owned ancestor-link verdict, and the implementation-start manifest —
  which are the direct source of the claim boundary and three constraints above.
- Direct execution on this platform confirmed both halves of the claim boundary:
  `os.link` with `follow_symlinks=False` over a symlinked source published a
  symlink, while `fcntl.flock` on a directory descriptor took an exclusive lock
  and refused a second holder, and neither `os.AT_EMPTY_PATH` nor `os.O_TMPFILE`
  is exposed by this CPython build.

## Uncertainty

- Whether operators prefer authoring a JSON record over Markdown is untested.
  Version 3 adds a reproducible authored-value count so the next reader has a
  number, but two samples are not a usage study.
- The generator reduces transcription error but cannot raise evidence quality; a
  record with three shallow evidence items still clears the Level 2 floor.
  Independent review remains the only control.
- Session-identifier inequality is a consistency signal, not proof that two
  sessions existed. The summary says so in fixed wording.
- Making ancestor-symlinked authority paths invalid is a behaviour change. No
  such path exists in this checkout, but a downstream one could newly fail
  validation; that is the intended consequence of the coordinator's decision.
