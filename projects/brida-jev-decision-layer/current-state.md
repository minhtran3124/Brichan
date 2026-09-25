# Current state

Last updated: 2026-09-24

## Summary

Research complete; no code, no API key, no vendor contact. Waiting on the
user's decision to start a shadow-mode pilot.

## Completed recently

- 2026-09-24: desk research on Jev (vendor docs, LangChain harness guide, two
  independent benchmarks, VentureBeat injection report, jev-guard, Jev-Mem).
- Ranked five candidate decision points; ruled out route replacement.

## In progress

None.

## Blockers

None. Pilot needs user authorization for an API key (secret) and for a
launcher-owned worker hook (durable-contract change).

## Risks

- Vendor is two weeks old at research time; closed weights; API-only.
- Verdicts shift under prompt injection in the state (0.76 -> 0.48 block
  probability in a public demo).
- English-primary; non-English state degrades accuracy.
- Ambiguous tool calls scored 71.4% in a 60-case benchmark; only
  confidence == 1.000 was error-free.

## Next actions

1. User decides go/no-go on a shadow pilot (est. under $1 of Jev usage).
2. If go: catalog entry + verification probe, stdlib client, verdict logging
   on worker tool calls and pane observations, then threshold analysis.

## Unverified assumptions

- Vendor "445x cheaper / 193x faster" claims are self-reported.
- Pricing and latency were read from vendor docs and blog posts, not from a
  live Brichan probe.
