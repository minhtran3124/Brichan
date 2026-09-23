# References

| Topic | Source | Verified date | Notes |
|---|---|---|---|
| Herdr plugin system | https://herdr.dev/docs/plugins/ | 2026-09-21 | Manifest `herdr-plugin.toml`; CLI is the plugin API; v1 has no update command or sandbox |
| Herdr plugin marketplace | https://herdr.dev/plugins/ | 2026-09-21 | Listing via GitHub topic `herdr-plugin`; unreviewed |
| Launch hook point | `src/brichan/orchestration/worker_launch.py` (`_main`) | 2026-09-21 | Post-PR #34 layout: split, wait for prompt, `agent start --pane` |
| Receipt Sessions table | `src/brichan/contracts/receipts/validation.py` | 2026-09-21 | Header `Role, Provider, Model, Brida-owned pane, Session` |
| Handoff receipt | `projects/brida-worker-ledger/handoffs/WLG-001/receipt.md` | 2026-09-23 | Canonical WLG-001 receipt |
