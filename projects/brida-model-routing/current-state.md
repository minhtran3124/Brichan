# Current state

Last updated: 2026-08-01

## Summary

Plan `MODEL-ROUTING-P1` version 3 is implemented and independently reviewed
with a `PASS` verdict. Pull request #12 merged to `main` at `6a55c97`; release
`v0.4.0` is published.

## Completed recently

- Researched making Claude Code the checkout coordinator default. The evidence
  supports a reversible one-owner dogfood default while preserving Codex-only
  installed mode and the Codex review route; it does not support a general
  provider ranking. See `claude-default-runtime-research.md`.
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
- Feature commit `218daa0` was pushed and pull request #12 was opened with
  verification evidence and residual risks.
- GitHub CI passed on Python 3.10, Python 3.13, and source-package builds; the
  pull request reports a clean merge state.
- Pull request #12 merged into `main` with its reviewed routing implementation
  and simplified getting-started documentation.

## In progress

- Post-release monitoring.

## Blockers

- None.

## Risks

- Provider config semantics differ; Brida must normalize only model and effort.
- Raw-command compatibility can bypass new validation unless clearly treated as
  a legacy escape hatch.
- Real runtime smoke tests must not create nested agents or remote changes.
- Claude worker `auto` mode can allow pushes and pull-request creation unless
  durable ask or deny rules establish the required human checkpoint.
- A Max subscription can stop long-lived coordinator work at usage limits, and
  its consumer-account data-use setting requires explicit user review.

## Next actions

1. Resolve the Claude worker remote-action checkpoint and complete the account
   privacy, authentication, model-access, and rollback preflight.
2. Decide whether to adopt the proposed checkout-only Claude dogfood default.
3. If adopted, run matched coordinator evaluations before making it permanent.
4. Monitor post-release feedback and address only evidence-backed findings.

## Unverified assumptions

- None.
