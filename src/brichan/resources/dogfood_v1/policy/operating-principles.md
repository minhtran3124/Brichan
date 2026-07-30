# Operating principles

1. Convert each request into an objective, scope, deliverables, acceptance
   criteria, constraints, permissions, and escalation conditions.
2. Work directly when a task is small or tightly coupled. Delegate only when a
   bounded independent worker materially helps.
3. Resolve named worker routes from `.brichan/config/model-routing.json`; never
   use an unavailable provider or Codex `ultra` reasoning for a worker.
4. Coordinate workers only through Herdr and the `herdr-orchestration` skill.
5. Verify diffs, tests, evidence, and known limitations before integrating.
6. Store durable facts and current state under `.brichan/project-memory/`.
7. Report outcome, changes, verification, decisions, risks, open questions, and
   the recommended next step.
