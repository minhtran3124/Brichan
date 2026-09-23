# Current state

Last updated: 2026-09-23

## Summary

WLG-001 (persisted worker ledger) is implemented and independently reviewed
(`PASS`) on branch `feat/worker-ledger`, uncommitted. `make check` exits 0 on
Python 3.10 and 3.14. Commit and PR await user approval.

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

- Plan and code reviews ran on Claude only (Codex usage limit until
  2026-09-27); no cross-provider review has been done.
- Installed ledger history resets at every package upgrade.
- `O_APPEND` atomicity is not guaranteed on network filesystems (documented).

## Next actions

- User approval: commit on `feat/worker-ledger` and open a PR.
- Follow-ups: packaged-skill and installable-dogfood guidance plus the
  memory-policy note (next release); ledger carry-over across upgrades;
  `brichan status` timeline; then the Herdr plugin monitor pane.

## Unverified assumptions

- None recorded.
