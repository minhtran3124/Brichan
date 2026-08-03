# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `TDW-007`
- Task level: `1`
- Artifact: `brief`
- Artifact version: `1`
- Origin: `packet:projects/brida-task-dossier-workflow/handoffs/TDW-007/task-packet.md@TDW-007-P1-v1`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `8aa41de8-a3f3-48ce-8d47-9aed67a452c6`
- Effective route: `plan`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Claim or decision

TDW-007 measures whether Level 1 depth — two concrete evidence items per artifact
and a routine reviewer — is sufficient for ordinary implementation work with real
edge cases. The slug normalizer is chosen because it has genuinely contestable
semantics at the boundaries (Unicode, empty result, separator runs) while staying
small enough that the dossier, not the algorithm, remains the object of study.

## Outcome

- A dependency-free normalizer plus a unit-test module under
  `evals/task-dossier-pilots/normal/`, both isolated from the shipped package.
- A Level 1 dossier that shows whether two evidence items per artifact carry
  enough signal for a routine reviewer to judge the boundary decisions.

## Constraints

- Planner-owned artifacts only; coordinator-owned and reviewer-owned artifacts
  stay unwritten by this session.
- Nothing outside the fixture directory changes: no edit to
  `src/brichan/`, no new dependency, no routing-config or installed-resource
  change, no commit, publish, deploy, or remote action.
- Level 1 keeps the routine review route and records ship authorization as
  `not-requested`.

## Success signal

Level 1 passes when the five named test cases and the ASCII-only boundary case
pass under `python3 -m unittest`, the changed-path report lists only the fixture
directory and the five planner artifacts, and the routine reviewer can reach a
verdict on the Unicode and empty-result decisions from the recorded evidence
alone, without re-deriving them.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-007/task-packet.md:14-17,32-34`
  fixes the normalizer semantics and the five required test cases that define
  the success signal above.
- `docs/workflows/task-dossier.md:115-119` sets Level 1 at two minimum evidence
  items with a routine review route and no ship gate, which is the depth this
  pilot is testing.
- `projects/brida-task-dossier-workflow/current-state.md` records under
  "Unverified assumptions" that the current `review` route may not be sufficient
  for routine Level 0/1 review; this task supplies one of the two observations
  needed to test that against TDW-008's stronger override.

## Uncertainty

- Whether two evidence items per artifact are enough for a routine reviewer is
  the open question this task exists to answer; it cannot be settled inside the
  planning artifacts and is resolved only by the independent `plan-review.md`
  the coordinator commissions.
