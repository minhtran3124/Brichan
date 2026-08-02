# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `brief`
- Artifact version: `1`
- Origin: `packet:projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md@TDW-009-P1-v1`
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
   depth against the level floor, effective provenance, plan and review
   identity, authority-link health, and review independence.

## Constraints

- All eleven artifacts survive at every level. Nothing is merged or dropped.
- The generator must not manufacture evidence, infer a review verdict, overwrite
  an existing artifact, follow a symlink, or escape the projects root.
- The summary must not become a second authority: it reports linked-authority
  health and never copies receipt or project-memory content.
- Standard library only, Python 3.10 floor, checkout mode only.
- `config/model-routing.json` and `src/brichan/resources/dogfood_v1/` are
  untouched.

## Success signal

- A Level 0 sample and a Level 1 sample each keep 11/11 artifacts, pass the
  complete-dossier gate, and measure at least 30% fewer total lines than the
  639-line and 716-line baselines.
- The summary reports every field named in `TDW-009-AC4` and exits nonzero on
  invalid or incomplete state.
- `make check` and the existing dossier suites pass unchanged, and `TDW-006`,
  `TDW-007`, and `TDW-008` stay byte-identical.

## Non-goals

- Installed-mode support, packaged resource changes, or `.brichan` migration.
- Any new key in the routing manifest.
- Wiring the summary into `make check`; it is a reporting tool, and gating a
  build on an in-progress dossier would be a behaviour change nobody asked for.
- Rewriting or upgrading the three existing hand-authored pilot dossiers.

## Claim or decision

The ceremony problem is a repetition problem, not an evidence problem, so the
correct intervention is to generate the derivable half of a dossier from one
structured record and to report the rest, rather than to relax any part of the
contract. Concretely: the sixteen-field metadata block, the status table, the
canonical receipt path, the owner assignment, and the boilerplate lede are
mechanical and are generated; claim, evidence, uncertainty, phase state,
provenance, and verdicts are judgment and stay operator-supplied, with a refusal
whenever the record omits one.

## Evidence

- `evals/task-dossier-pilots/results.md:49-64` states the measured ceremony
  problem in the pilot's own words — 639 dossier lines against one line of
  fixture — and already concludes that keeping eleven artifacts is compatible
  with reducing ceremony through concise generated projections.
- `evals/task-dossier-pilots/results.md:66-91` fixes both halves of the outcome
  above as recommended follow-ups 2 and 3, and its "what not to do" list is the
  source of the constraint that a missing artifact must never mean "simple".
- `projects/brida-task-dossier-workflow/decisions.md:3-15` records the user's
  accepted decision that every level keeps the complete document set and that
  file presence is not proof, which is why the outcome is generation of
  derivable fields rather than reduction of the artifact set.
- `projects/brida-task-dossier-workflow/current-state.md:50-55,57-62` lists
  concise generation and a summary command as the project's first two next
  actions and names the residual risk that evidence quality still requires
  reviewer judgment.
- `src/brichan/contracts/task_dossier/schema.py:35-52,75` shows the repetition
  concretely: sixteen metadata labels per artifact plus a four-column status row
  per artifact, all mechanically derivable from one record.

## Uncertainty

- Whether operators prefer authoring a JSON record over authoring Markdown is
  untested. This task produces two samples, not a usage study, so the record
  format's ergonomics remain unmeasured and the hand-authored path stays fully
  supported.
- The line-reduction target is a proxy for authoring cost, not a measurement of
  it. Timing, tokens, and cost were not reliably observable in the pilot and are
  not estimated here.
- The generator reduces transcription error but cannot raise evidence quality; a
  record with three shallow evidence items still clears the Level 2 floor.
  Independent review remains the only control for that, and this brief does not
  claim otherwise.
