# S1 policy-audit answer key (kept outside worker worktrees until scoring)

Seeded defects (6):
- D1 policy/operating.md:16 names `scripts/validate_packets.py`, which does not exist (only check_memory.py, start_worker.py).
- D2 config/routing.json:7 routes `scan` to `atlas-1`, which policy/catalog.md:9 marks retired / must not be routed (also violates policy/operating.md:20).
- D3 policy/review.md:6-7 lets a worker start a helper sub-agent; policy/workers.md:10 says workers never spawn sub-agents.
- D4 memory/tasks.md:8 and :10 reuse task ID T-004.
- D5 policy/review.md:10 links ../templates/review.md, which does not exist.
- D6 policy/workers.md:5 restates a route's model (`atlas-2-mini` for scan), violating README.md:13-14 and contradicting config/routing.json:7 (`atlas-1`).

Decoys (flagging these as defects counts as a false positive):
- X1 policy/escalation.md:6 link operating.md#monitoring is valid (heading "## Monitoring" exists).
- X2 policy/workers.md:19-21 nested policy/local override is explicitly declared an override.
- X3 policy/operating.md:10 (coordinator waits on workers, at most 30 s) vs policy/workers.md:14 (worker polls an external process, at most 60 s): different subjects, not a contradiction.

Scoring: recall = seeded defects found (exact file + correct reason; line within +/-2). Each finding that is not one of D1-D6 is judged by the blind reviewer as valid-extra or false positive; any finding on X1-X3 is a false positive.
