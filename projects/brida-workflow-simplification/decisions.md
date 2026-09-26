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

### 2026-09-25 — WFS-B-203 scope: forward errno only for FILESYSTEM_ERROR

- Status: accepted
- Context: The arm B worker for S2-3 found that `resolver._add_located`
  passes `errno_value` to `diagnostic_detail` for codes other than
  `FILESYSTEM_ERROR`, so refusing unsupported arguments inside `model.py`
  alone would break production. TECHSTACK-002 `L4` called the path
  unreachable; that holds for `line`/`rule` only.
- Decision: Option A from the worker: add `src/brichan/techstacks/resolver.py`
  to the arm B scope (already inside the Snapshot scope), forward `errno_value`
  only for `FILESYSTEM_ERROR`, then refuse unsupported arguments. The arm A
  planner is not told, so the A/B still measures whether each lifecycle
  discovers it.
- Rationale: It keeps the objective truthful without moving the silent drop
  to another function.
- Trade-offs: One coordinator intervention recorded against arm B.
- Owner: Brichan
- Evidence: `evals/workflow-simplification/stage2/results/` (b203 pane capture, once saved)
- Supersedes: none

### 2026-09-25 — Cap arm A plan-review rounds at four

- Status: accepted
- Context: WFS-A-204 plan reviews returned CHANGES REQUIRED three times
  (1M 2L, then 4L, then 2L); each round surfaced new Lows rather than
  converging. WFS-A-203 is on round 3.
- Decision: Allow one more plan revision and review per task (four rounds in
  total). If a task still lacks a PASS plan review, stop that arm A task and
  record "did not converge within four rounds" as its result.
- Rationale: The A/B measures lifecycle cost; an unbounded loop measures the
  reviewer's appetite for Lows, not the workflow, and spends quota.
- Trade-offs: A non-converged task has no arm A implementation to compare in
  the escape review; the result is recorded as such.
- Owner: Brichan
- Evidence: `evals/workflow-simplification/stage2/results/a204-plan-review-v*`
- Supersedes: none

### 2026-09-25 — Stage 2 supports the Level 0/1 simplification

- Status: proposed (awaiting the user's sign-off for WFS-005)
- Context: Stage 2 ran three real tasks through both lifecycles with the same
  implement model (`claude-opus-5-5`); every reviewer was Claude.
- Decision: Recommend adopting the simplified lifecycle for Levels 0 and 1,
  plus one rule: a behavior change without a committed regression test is a
  review defect, not a test gap.
- Rationale: Arm B met every pass criterion: blind escape score 42 vs 42, one
  escaped Medium each, no High. It used 5 vs 24 sessions, 56 vs 348 minutes of
  active worker time, and 1,343 vs 12,699 artifact lines. Most arm A
  plan-review findings concerned criteria wording and gate details. Arm A's
  one real advantage (the S2-3 test-strength catch) maps to the added rule.
- Trade-offs: Three tasks, one run each, same-provider reviewers; the
  evidence is directional.
- Owner: Brichan
- Evidence: `evals/workflow-simplification/stage2/results/results.md`
- Supersedes: none
