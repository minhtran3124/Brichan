# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `TDW-008`
- Task level: `2`
- Artifact: `requirements`
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

TDW-008 requires a pure, read-only `evaluate_release_policy(mapping)` that reports
deterministic violations of a release policy and never performs a release. The
task is Level 2 because it simulates security-and-release-risk work and therefore
takes the stronger reviewer and the ship-authorization gate, not because the code
itself is dangerous: the function is a side-effect-free predicate over a mapping
and touches no release, secret, production system, or remote.

## Functional requirements

- `TDW-008-R1`: `evaluate_release_policy(mapping)` returns a deterministic,
  order-stable collection of violation codes; an empty result means compliant.
- `TDW-008-R2`: a violation is recorded when `remote_publish` is not explicitly
  safe (`remote_publish=true` is rejected).
- `TDW-008-R3`: a violation is recorded when `secret_access` is not explicitly
  safe (`secret_access=true` is rejected).
- `TDW-008-R4`: a violation is recorded for any `environment` other than
  `sandbox`.
- `TDW-008-R5`: a violation is recorded when `rollback_plan` is missing, not a
  string, or blank after stripping whitespace.
- `TDW-008-R6`: the function is read-only — it does not mutate the input mapping,
  perform I/O, spawn a process, read an environment variable, or import anything
  outside the standard library.
- `TDW-008-R7`: the same input always produces the same output; no clock, no
  randomness, no set iteration order, and no ambient state participates.
- `TDW-008-R8`: the fixture never executes, simulates executing, or documents how
  to execute a real release.

## Acceptance criteria

- `TDW-008-AC1`: all five planning artifacts contain at least three concrete
  evidence items and complete model, session, and route provenance
  (`task-packet.md:34-35`).
- `TDW-008-AC2`: `plan.md` records accepted `TDW-008-P1` version 1
  (`task-packet.md:36`).
- `TDW-008-AC3`: `design.md` records threats, the authorization boundary, stop
  conditions, and rollback (`task-packet.md:37-38`).
- `TDW-008-AC4`: tests cover all four guards deterministically
  (`task-packet.md:38`).
- `TDW-008-AC5`: focused tests pass with no external side effect
  (`task-packet.md:39`).

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-008/task-packet.md:9-11,15-20,34-39`
  supplies the plan identity, the four guards transcribed as R2–R5, the
  documentation duties, and the five acceptance criteria; AC3 and AC4 are the two
  clauses of packet line 37-38, which is why the packet's four acceptance bullets
  yield five criteria.
- `projects/brida-task-dossier-workflow/tasks.md` registers TDW-008 with
  acceptance criteria `TDW-008-AC1`–`AC5`, matching the five-way split recorded
  above rather than the packet's four bullets.
- `docs/workflows/task-dossier.md:126-128` lists the raise-to-Level-2 triggers;
  this task meets "security, privacy, destructive, production, or public-contract
  risk exists" as a simulation subject, which is why the level is 2 even though
  `docs/workflows/task-dossier.md:115-119` also demands a stronger reviewer and a
  ship gate as a consequence.
- `docs/policy/identity.md:33-40` requires Brichan to ask before touching
  production, deployment, credentials, or remote state; `TDW-008-R8` is the
  requirement that keeps this simulation on the safe side of that boundary.

## Uncertainty

- The packet says "reject `remote_publish=true`" but does not say what a
  non-boolean value such as the string `"true"` means. `options.md` resolves this
  fail-closed rather than leaving it open; it is recorded here because the
  resolution is derived, and a fail-open reading would silently weaken R2 and R3.
