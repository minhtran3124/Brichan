# Current state

Last updated: 2026-07-27

## Summary

All four evaluation tracks have executed, baseline findings were remediated,
independent verification completed, and all Brida-owned eval panes were closed.

## Completed recently

- Defined four independent evaluation tracks and measurable outcomes.
- Reviewer baseline passed at recall 1.00 and precision 0.80.
- Reviewer retest passed at recall 1.00 and precision 1.00.
- Token A/B showed 68.2% less coordinator input but 36.9% more total tokens.
- Metrics validator now passes 10 tests from both supported working directories.

## In progress

None.

## Blockers

None.

## Risks

- Provider cost cannot be computed until pricing is independently verified.
- Herdr panes may auto-close before the usage tail is retained; an isolated
  Codex run was used for the exact token comparison.

## Next actions

- Use the measured delegation decision gate in future tasks.
- Add verified provider pricing before reporting dollar cost.
- Repeat the long-horizontal eval on a genuinely multi-day production task.

## Unverified assumptions

- Provider cost is not computed because no independently verified price source
  was recorded.
