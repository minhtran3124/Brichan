# Current state

Last updated: 2026-07-29

## Summary

Plan `MODEL-ROUTING-P1` version 3 is implemented and independently reviewed
with a `PASS` verdict on branch `feat/settings-driven-model-routing`.

## Completed recently

- Reviewed current hard-coded model selection and official provider settings.
- Selected a repository-owned JSON manifest plus provider-neutral resolver.
- Initial implementation, full repository tests, isolated sandbox tests, and a
  real settings-driven Herdr smoke test completed.
- Independent Claude Opus review returned `CHANGES REQUIRED` with attached
  Codex option guard and repository-contract findings.
- Coordinator-owned receipt and durable-path contract findings are fixed.
- Remediation completed; coordinator reran 66 focused tests, full `make check`,
  a fresh isolated sandbox, installed Codex/Claude argument parsing, and
  attached-option rejection checks successfully.
- Fresh review found an import-order cycle in the canonical provider adapter and
  bounded legacy permission/hook hardening gaps.
- Plan version 3 remediation passed provider-first/no-eager-CLI import probes,
  61 unit, 37 contract, 23 integration tests, a fresh isolated sandbox, real
  provider parser checks, and legacy fail-before-Herdr probes.
- The final legacy Claude `--tools` guard and regressions passed 29 focused
  tests, full repository checks, and a fresh release sandbox.
- Final independent review passed AC1–AC8 with no blocking findings.

## In progress

- Commit, push, and pull-request handoff.

## Blockers

- None.

## Risks

- Provider config semantics differ; Brida must normalize only model and effort.
- Raw-command compatibility can bypass new validation unless clearly treated as
  a legacy escape hatch.
- Real runtime smoke tests must not create nested agents or remote changes.

## Next actions

1. Commit the reviewed implementation.
2. Push `feat/settings-driven-model-routing`.
3. Open a pull request with verification evidence and residual risks.

## Unverified assumptions

- None.
