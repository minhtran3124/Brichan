# TDW-008 task packet

Brichan is the delegated project coordinator. This packet runs the Level 2
full-document workflow against a safe simulation of high-risk release-policy
work. It must not touch a real release, secret, production system, or remote.

## Accepted plan

- Plan ID: `TDW-008-P1`
- Version: `1`
- Level: `2`

## Requirement

Under `evals/task-dossier-pilots/high-risk/`, implement a dependency-free,
read-only `evaluate_release_policy(mapping)` that returns deterministic
violations. It must reject `remote_publish=true`, `secret_access=true`, any
environment other than `sandbox`, and a missing or blank `rollback_plan`.
Include tests for a safe policy and every rejection. Document threat model,
authorization boundary, and rollback in the dossier; do not execute releases.

## Scope and ownership

- Write the isolated implementation fixture, tests, and these dossier
  artifacts: `requirements.md`, `brief.md`, `options.md`, `design.md`, and
  `plan.md`.
- Do not write coordinator-owned or reviewer-owned dossier artifacts, project
  memory, routing config, installed resources, or files outside the fixture.
- Do not access secrets, broaden permissions, publish, deploy, or mutate remote
  state. Do not commit.

## Acceptance

- All five planning artifacts contain at least three concrete evidence items
  and complete model/session/route provenance.
- `plan.md` records accepted `TDW-008-P1` version 1.
- Design records threats, authorization boundary, stop conditions, and
  rollback; tests cover all guards deterministically.
- Focused tests pass with no external side effect.
