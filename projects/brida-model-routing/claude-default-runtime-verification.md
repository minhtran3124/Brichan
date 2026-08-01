# Verification: Claude checkout-default research

Last verified: 2026-08-01

## Scope

Coordinator-owned verification of the revised research PR. This file records
observed repository evidence without claiming access to the prior worker's pane
output, authentication details, or live model-probe transcript.

## Observed local prerequisites

- `claude --version`: Claude Code `2.1.220`.
- `herdr --version`: Herdr `0.7.3`.
- The PR routing manifest keeps checkout default runtime `codex`, routes plan,
  implementation, and scan to Claude, and routes review to Codex.

No authentication status, account identifier, data-use setting, quota balance,
or live model result is stored here.

## Repository validation

The substantive revision commit and exact command results are recorded after
the revised research content is committed and validated.

## Evidence limits

- The earlier worker-reported 71-test run has a pane and provider session ID in
  `tasks.md`, but no retained command log or canonical receipt.
- Authentication and model availability are time-sensitive preflight checks,
  not permanent repository facts.
- Passing repository tests establishes implementation compatibility; it does
  not establish coordinator quality or provider superiority.
