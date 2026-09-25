# Decision log

### 2026-09-25 — Simplify ceremony by risk level, keep verification

- Status: proposed (direction accepted by the user 2026-09-25; policy change
  pending the A/B result and final user sign-off)
- Context: Level 0 dossier pilots produced 639 dossier lines for a one-line
  fixture, and plan and code review found 0 defects on all three synthetic
  pilots. Real material tasks still produced many review findings (worker
  ledger 21, memory consistency 15, task dossier 10/8/8). Most blockers
  came from handoff mechanics. `claude-opus-5-5` is now available.
- Decision: Pursue risk-proportional simplification: Level 0 = one
  implement worker + `make check` + contract-path-triggered code review, three
  artifacts; Level 1 = merged plan+implement worker, no plan-review,
  independent code review kept; Level 2 unchanged. Gate adoption on the A/B
  protocol in `evals/workflow-simplification/protocol.md`.
- Rationale: Stronger models reduce, but do not remove, subtle defects, and
  independent review is where Brichan's findings actually come from. Cutting
  documents and handoffs removes cost that has no measured quality return.
- Trade-offs: Reverses the 2026-08-02 pilot recommendation to keep all eleven
  artifacts at every level. Fewer independent checkpoints at Level 0. The
  evidence base is thin (25 runs, mostly on this repository).
- Owner: Brichan
- Evidence: `metrics/runs.jsonl`, `evals/task-dossier-pilots/results.md`
- Supersedes: none (would amend the task-dossier "all levels, eleven
  artifacts" rule if accepted)
