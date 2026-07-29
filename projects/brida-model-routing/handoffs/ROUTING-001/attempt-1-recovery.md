# ROUTING-001 attempt 1 recovery evidence

- Worker: `brida-model-routing-impl`
- Pane: `w1X:p2T`
- Model: `gpt-5.6-sol`, high
- Session: unavailable before pane exit
- Outcome: abandoned before task execution

## Observations

1. `2026-07-29T05:39:44Z`: worker absent from `herdr agent list`;
   `herdr pane get w1X:p2T` returned `pane_not_found`.
2. `2026-07-29T05:39:56Z`: worker remained absent; pane remained
   `pane_not_found`.
3. `2026-07-29T05:40:04Z`: worker remained absent; pane remained
   `pane_not_found`.

## Repository evidence

`git status --short` and `git diff --stat` showed only coordinator-owned plan
and project-memory changes. Attempt 1 produced no implementation change.

## Replacement decision

The attempt is abandoned after the three required no-progress observations.
One bounded replacement is authorized with the same accepted plan, model,
scope, paths, constraints, and write ownership. The replacement must reach a
concrete agent session before task dispatch.
