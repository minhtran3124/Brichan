# Current state

Last updated: 2026-09-23

## Summary

WLG-001 (persisted worker ledger) is merged to `main` via PR #35 (`e179bfc`,
2026-09-23) after independent review `PASS` and CI 8/8 green.

## Completed recently

- 2026-09-21: plan v1-v4 and three plan-review rounds; plan v4 accepted with
  conditions C1-C3.
- 2026-09-23: implementation (Claude `claude-opus-5`), code review (fresh
  Claude `claude-fable-5`, PASS), CR-L1 fixed; coordinator reran `make check`
  on both interpreters (exit 0).

## In progress

- None. No Brichan worker panes are open.

## Blockers

- None.

## Risks

- Plan and code reviews ran on Claude only; the user merged without a
  cross-provider review (2026-09-23).
- Installed ledger history resets at every package upgrade.
- `O_APPEND` atomicity is not guaranteed on network filesystems (documented).

## Next actions

- Follow-ups: packaged-skill and installable-dogfood guidance plus the
  memory-policy note (next release); ledger carry-over across upgrades;
  `brichan status` timeline; then the Herdr plugin monitor pane.

## Unverified assumptions

- None recorded.
