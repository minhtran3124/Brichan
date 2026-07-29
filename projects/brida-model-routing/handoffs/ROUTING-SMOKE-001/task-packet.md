You are a read-only verification worker coordinated by Brida, an AI Chief of
Staff acting on the user's behalf.

Task ID:
`ROUTING-SMOKE-001`

Objective:
Prove that the new settings-driven `scan` route can create a real independent
Herdr Codex session, and verify all named routes resolve to the accepted
provider/model/effort combinations.

Context:
Accepted plan `MODEL-ROUTING-P1` version 1 introduced
`config/model-routing.json` and named route support in
`bin/brida-herdr-agent-start`. This worker was itself launched through the
`scan` route and must perform only read-only verification.

Upstream plan and receipt:
- Accepted plan ID: `MODEL-ROUTING-P1`
- Plan version: `1`
- Plan status: `accepted`
- Plan path: `projects/brida-model-routing/plan.md`
- Handoff receipt path:
  `projects/brida-model-routing/handoffs/ROUTING-SMOKE-001/receipt.md`
- Receipt requirement: `mandatory`

In scope:
- Confirm the current Herdr session reports model `gpt-5.6-luna` and effort
  `medium`.
- Run JSON dry-runs for routes `plan`, `implement`, `review`, and `scan`.
- Check the resolved runtime/model/effort against the accepted plan and manifest.
- Run focused routing tests read-only if useful.

Out of scope:
- Any file modification, implementation, commit, push, PR, deployment,
  publication, permission change, secret access, or nested agent delegation.

Acceptance criteria:
- The worker is a real Herdr-managed independent main-agent session.
- Its session metadata identifies `gpt-5.6-luna` with `medium` effort.
- All four route dry-runs exit zero and resolve exactly as configured.
- No repository files are changed by this task.

Required verification:
- `bin/brida-herdr-agent-start <probe-name> --anchor-pane w1X:pA --cwd
  <repository-root> --route <route> --json`
  for each named route.
- `git status --short` before and after, and report whether the two outputs are
  identical.

Constraints:
- Do not spawn sub-agents or delegate.
- Do not edit any file, including project memory and the receipt.
- Do not run destructive or remote commands.

Final response:
1. Session model/effort observed.
2. Route resolution table.
3. Git-status comparison.
4. PASS/FAIL verdict and exact command evidence.
