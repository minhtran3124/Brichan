# Current state

Last updated: 2026-07-27

## Summary

Herdr health, worker lifecycle, and balanced pane-layout smoke tests passed.

## Completed recently

- Confirmed Herdr 0.7.3 server and client are compatible.
- Confirmed Codex integration v6 is current.
- Created `brida-herdr-smoke-20260727-01` through Herdr in pane `w1X:p2`.
- Received the exact `BRIDA_HERDR_SPAWN_OK` response with no file changes or
  delegated agents.
- Verified live launcher layouts: 2 panes at 50/50, 3 panes at near-equal area,
  and 4 panes in an equal 2x2 grid.
- Independent Sol review found two ratio-normalization defects; both were fixed
  and the remediation review passed with no remaining findings.

## In progress

None.

## Blockers

None.

## Risks

- Existing Herdr panes belong to other workflows and must not be touched.
- Layouts above four panes or noncanonical split trees use best-effort placement.
- After a worker is confirmed started, resize/focus degradation is reported as a
  warning while the launcher returns success to prevent duplicate workers.

## Next actions

- Repeat lifecycle and layout smoke tests when validating future Herdr upgrades.

## Unverified assumptions

None.
