# References

| Topic | Source | Verified date | Notes |
|---|---|---|---|
| Herdr health | `herdr status` | 2026-07-27 | Client/server 0.7.3, protocol 16, compatible |
| Codex integration | `herdr integration status` | 2026-07-27 | Current, v6 |
| Worker lifecycle | `herdr agent read brida-herdr-smoke-20260727-01 --source recent-unwrapped --lines 120 --format text` | 2026-07-27 | Pane `w1X:p2` returned `BRIDA_HERDR_SPAWN_OK`; no files changed or agents spawned |
| Balanced layout smoke | `herdr pane layout --pane w22:p1` after each wrapper start | 2026-07-27 | 2: `128x72`; 3: `171x36`, `171x36`, `85x72`; 4: four `128x36` panes; temp workspace closed |
| Independent review | `herdr agent read brida-layout-review-sol --source recent-unwrapped --lines 180 --format text` | 2026-07-27 | Initial two medium findings fixed; remediation verdict PASS in pane `w1X:pH` |
