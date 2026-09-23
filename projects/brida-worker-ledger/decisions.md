# Decision log

### 2026-09-21 — Build visibility on a core ledger, not in a plugin

- Status: accepted
- Context: The user wants users to see which agent did what. Routing lives in
  `config/model-routing.json`; launch data is printed and discarded; receipts
  record sessions by hand; metrics hold aggregates only.
- Decision: Record a machine-written worker ledger in the core package first;
  `brichan status` and any Herdr plugin read it later.
- Rationale: The data gap, not the UI, is the blocker; CLI users benefit too.
- Trade-offs: No visible UI in the first step.
- Owner: user (approved option (a)); Brichan coordinator.
- Evidence: coordinator survey of `worker_launch.py`, receipt schema, task dossier schema, `metrics/README.md`.
- Supersedes: none

### 2026-09-21 — WLG-001 scope decisions from plan v1 options

- Status: accepted
- Context: Plan v1 (`options.md`) escalated three choices gating plan steps 3, 4, and 6.
- Decision: (1) ignore `/projects/*/ledger/` in Git; (2) ship the
  coordinator-attested `finish` CLI, console script, and `bin/` wrapper inside
  WLG-001; (3) defer the memory-policy note in both policy trees to the next
  release task, so WLG-001 touches no packaged resource.
- Rationale: machine data stays out of commits; start and finish together make
  the later `brichan status` timeline useful; no manifest hash change outside a release.
- Trade-offs: slightly larger WLG-001 scope; policy text lags the code until the next release.
- Owner: user.
- Evidence: user answers in the coordinator session on 2026-09-21.
- Supersedes: none

### 2026-09-21 — Accept WLG-001 plan v4 with three implementation conditions

- Status: accepted
- Context: Plan review round 3 returned `PASS` on plan v4 with two new Low
  findings and one test gap; all 17 earlier findings were resolved.
- Decision: Accept `WLG-001-PLAN-001` v4 instead of a fifth planning round.
  The implement packet must require: (C1, PR3-L1) the `.brichan` component
  check uses `casefold()` and the rejection tests include a case variant such
  as `.BRICHAN/ledger/workers.jsonl`; (C2, PR3-L2) the ledger consumer rule is
  "first `finished` record in file order wins" and R14 is documented as a
  one-at-a-time guarantee; (C3) a test pins that the installed `finish`
  entrypoint rejects `--ledger-file`.
- Rationale: The conditions are local and testable; another planning round
  costs Claude quota (94% weekly) for no design change.
- Trade-offs: The accepted plan text differs from the implemented contract on
  these three points; the code review must check them explicitly.
- Owner: Brichan coordinator.
- Evidence: `handoffs/WLG-001/plan-review.md` v3; coordinator confirmed the case-insensitive filesystem.
- Supersedes: none
