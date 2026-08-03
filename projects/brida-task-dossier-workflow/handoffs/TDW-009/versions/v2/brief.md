# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `brief`
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

Version 1 is preserved byte-identically at `versions/v1/brief.md`. The problem
statement and the outcome are unchanged; what changed is the safety bar the
outcome must clear and the honesty bar the evaluation must clear. Independent
review found that version 1's write model could be raced into escaping the
projects root, that its evaluation samples would have manufactured review
authority, and that its default summary exit could report an incomplete dossier
as healthy.

## Problem

The three-lane pilot proved the full-document contract works and priced it. A
one-line Level 0 change cost 639 lines of hand-authored dossier prose across
eleven artifacts; the Level 1 lane cost 716. Most of that volume is not
judgment. It is sixteen metadata fields repeated eleven times, an eleven-row
status table that restates what each artifact already declares, two link fields
whose only valid value is derivable from the dossier path, and a template lede
copied verbatim into every file.

The second cost is inspection. Answering "is this dossier sound?" currently
means opening eleven files and cross-reading sessions, verdicts, evidence
counts, and link targets by eye. The validator answers "valid or not" but does
not report the state an operator needs in order to act.

## Outcome

Two additive checkout-mode capabilities:

1. **Generator** — one structured record renders all eleven artifacts, deriving
   only what is mechanically derivable and refusing to invent anything else.
2. **Summary** — one deterministic read-only report of artifact state, evidence
   depth against the rule that applies to each artifact, effective provenance,
   plan and review identity, authority-link health, and review independence.

## Constraints

- All eleven artifacts survive at every level. Nothing is merged or dropped.
- Generation must not manufacture evidence, infer a review verdict, overwrite an
  existing artifact, follow a symlink, escape the projects root, or publish a
  truncated file — including under a concurrent attacker who swaps a directory
  after the safety check has run.
- The summary must not become a second authority: it reports linked-authority
  health, delegates its verdict to the existing validator, and never copies
  receipt or project-memory content.
- Evaluation samples are synthetic fixtures. Nothing they contain — no `PASS`,
  no reviewer session, no unequal identifier pair — may be presented as evidence
  of real independent review.
- Standard library only, Python 3.10 floor, checkout mode only.
- `config/model-routing.json`, `src/brichan/resources/dogfood_v1/`,
  `parser.py`, and `scaffold.py` are untouched.

## Success signal

- A Level 0 sample and a Level 1 sample each keep 11/11 artifacts, pass the
  complete gate against an isolated projects root, and measure at least 30%
  fewer total lines than the 639-line and 716-line baselines — with record size
  and authored-value counts reported alongside, so the claim is about authoring
  burden and not only about output size.
- The summary reports every field named in `TDW-009-AC4`, computes its root
  verdict through `validate_projects`, and exits nonzero for any invalid or
  incomplete dossier by default.
- Deterministic tests prove a post-check directory swap cannot place a file
  outside the projects root, and that no injected write, flush, or close failure
  can leave a partial artifact behind.
- `make check` passes, the focused suites pass under Python 3.10, and a pre-task
  digest baseline proves the routing manifest, installed resources, and the three
  pilot dossiers are byte-identical.

## Non-goals

- Installed-mode support, packaged resource changes, or `.brichan` migration.
- Any new key in the routing manifest.
- Any change to `scaffold.py`, including the helper rename version 1 proposed.
- Wiring the summary into `make check`; it is a reporting tool, and gating a
  build on an in-progress dossier would be a behaviour change nobody asked for.
- Rewriting or upgrading the three existing hand-authored pilot dossiers.
- Claiming any timing, token, or cost saving.

## Claim or decision

The ceremony problem is a repetition problem, not an evidence problem, so the
intervention remains generating the derivable half of a dossier and reporting the
rest. Version 2 adds that this is only worth doing if the generator is
provably safe under concurrency and provably honest about what it did not
verify: writes are anchored to directory descriptors rather than pathnames,
artifacts are published atomically by hard link so a partial body can never
become a final artifact, and the evaluation fixtures are labelled synthetic so
no reader mistakes a generated `PASS` for a review.

## Evidence

- `evals/task-dossier-pilots/results.md:49-64` states the measured ceremony
  problem in the pilot's own words — 639 dossier lines against one line of
  fixture — and already concludes that keeping eleven artifacts is compatible
  with reducing ceremony through concise generated projections.
- `projects/brida-task-dossier-workflow/decisions.md:3-15` records the user's
  accepted decision that every level keeps the complete document set and that
  file presence is not proof, which is why the outcome is generation of
  derivable fields rather than reduction of the artifact set.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan-review.md:31-36,282-291`
  is why version 2 exists and why its constraints are stricter: the reviewer
  judged version 1 unsafe to implement and named the three decisions the
  coordinator has since fixed in the packet amendment.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:73-81`
  fixes those decisions — synthetic non-authoritative fixtures, a complete-gate
  default, and a generator-specific descriptor writer with scaffold unchanged —
  which is the direct source of three constraints and one non-goal above.
- `src/brichan/contracts/task_dossier/schema.py:35-52,75` shows the repetition
  concretely: sixteen metadata labels per artifact plus a four-column status row
  per artifact, all mechanically derivable from one record.

## Uncertainty

- Whether operators prefer authoring a JSON record over authoring Markdown is
  untested. Version 2 adds record size and authored-value counts so the next
  reader has a number rather than an impression, but two samples are still not a
  usage study, and the hand-authored path stays fully supported.
- The generator reduces transcription error but cannot raise evidence quality; a
  record with three shallow evidence items still clears the Level 2 floor.
  Independent review remains the only control for that.
- Session-identifier inequality is a consistency signal, not proof that two
  sessions existed. The summary now says so in fixed wording, which bounds the
  claim without removing the limitation.
