# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `TDW-008`
- Task level: `2`
- Artifact: `brief`
- Artifact version: `1`
- Origin: `packet:projects/brida-task-dossier-workflow/handoffs/TDW-008/task-packet.md@TDW-008-P1-v1`
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

TDW-008 exercises the Level 2 machinery — three evidence items per artifact, a
documented stronger reviewer override, and a recorded ship-authorization decision
— against a subject that carries the shape of high-risk release work without any
of its consequences. The whole task is an isolated simulation: a pure predicate
over a mapping, with no production, secret, or remote action anywhere in its
scope.

## Outcome

- A read-only `evaluate_release_policy(mapping)` and its tests under
  `evals/task-dossier-pilots/high-risk/`, isolated from the shipped package.
- A Level 2 dossier whose design records the threat model, authorization
  boundary, stop conditions, and rollback, so the pilot can judge whether Level 2
  depth actually changes reviewer behaviour or only adds ceremony.

## Constraints

- Planner-owned artifacts only; coordinator-owned and reviewer-owned artifacts
  stay unwritten by this session.
- No secret access, no permission broadening, no publish, no deploy, no remote
  mutation, no commit. Nothing outside the fixture directory changes.
- Level 2 requires the coordinator to record a documented stronger review-route
  override in `index.md` and to record ship authorization explicitly; the ship
  here is not requested, and no user authorization is claimed by this session.

## Why this is safe

- The subject is a function that classifies a dictionary. It has no release
  capability to misuse: rejecting `remote_publish=true` is a string-returning
  branch, not a refusal of an actual publish.
- The fixture directory is outside `src/`, `tests/`, `config/`, and the installed
  resources, so nothing that ships or executes in CI is touched.

## Success signal

Level 2 passes when every guard is proven by a deterministic test, the input
mapping is observably unmutated, the changed-path report lists only the fixture
directory and the five planner artifacts, and the stronger reviewer can audit the
threat model and authorization boundary from `design.md` alone.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-008/task-packet.md:3-5,15-20`
  states that the packet is a safe simulation that must not touch a real release,
  secret, production system, or remote, which is the constraint this brief carries
  forward.
- `docs/workflows/task-dossier.md:115-119,146-153` sets Level 2 at three minimum
  evidence items with a documented stronger one-off reviewer override, and
  requires an explicit ship-authorization record.
- `docs/policy/identity.md:33-40` and `docs/policy/operating-principles.md:55-69`
  define the authorization boundary this task simulates and the evidence standard
  its dossier must meet.
- `projects/brida-task-dossier-workflow/current-state.md` records under
  "Unverified assumptions" that the routine `review` route must be tested against
  a stronger Level 2 one-off override; TDW-008 is the observation that supplies
  the stronger side of that comparison.

## Uncertainty

- Whether Level 2's extra depth changes reviewer findings, rather than only
  reviewer cost, is the open question this task exists to answer. It cannot be
  settled from inside the planning artifacts and is resolved only when the
  stronger reviewer's `plan-review.md` is compared against the routine reviews of
  TDW-006 and TDW-007.
