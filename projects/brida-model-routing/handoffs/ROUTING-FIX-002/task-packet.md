You are an implementation worker coordinated by Brida, an AI Chief of Staff
acting on the user's behalf.

Task ID:
`ROUTING-FIX-002`

Objective:
Complete plan `MODEL-ROUTING-P1` version 3 by fixing the canonical import-order
cycle and final bounded legacy safety/test gaps from `ROUTING-REVIEW-002`.

Upstream plan and receipt:
- Accepted plan ID: `MODEL-ROUTING-P1`
- Plan version: `3`
- Plan status: `accepted`
- Plan path: `projects/brida-model-routing/plan.md`
- Review receipt:
  `projects/brida-model-routing/handoffs/ROUTING-REVIEW-002/receipt.md`
- Handoff receipt:
  `projects/brida-model-routing/handoffs/ROUTING-FIX-002/receipt.md`
- Receipt requirement: `mandatory`

In scope:
- Remove the eager `worker_launch` → `brida.cli.provider_commands` import edge.
  Import provider command builders only inside launch resolution paths that use
  them, without moving provider-specific code back into orchestration.
- Add fresh-interpreter tests proving:
  1. `import brida.cli.provider_commands` succeeds as the first Brida import.
  2. `import brida.orchestration` does not load `brida.cli` modules.
- Update `make package-check` to exercise provider-first import ordering.
- Reject legacy Codex `-p`/`--profile` (including attached/equals forms) and
  `--add-dir` before Herdr.
- Reject legacy Claude `--bare`, `--allowedTools`/`--allowed-tools`, and
  `--disallowedTools`/`--disallowed-tools` passthrough so Herdr hooks and Task
  denial do not depend on provider precedence.
- Add an integration test where explicit Claude `--model` beats both
  `BRIDA_CLAUDE_COORDINATOR_MODEL` and the manifest.
- Add focused launcher tests showing every new legacy rejection happens before
  fake Herdr receives a call.

Out of scope:
- Project memory and receipts; Brida owns them.
- New routing schema fields, hard-coded provider/model compatibility maps,
  credentials, deployments, releases, commits, pushes, or PR actions.

Acceptance criteria:
- Fresh provider-first import succeeds with no order dependency.
- Importing orchestration does not eagerly load `brida.cli`.
- All review findings are fixed or explicitly residual by prior agreement.
- Focused suite, `make check`, `git diff --check`, sandbox, runtime parsers, and
  a fresh independent review pass.

Required verification:
- Focused unit/integration/contract tests.
- `make check`.
- Direct fresh-interpreter import probes.
- `git diff --check`.

Constraints:
- Do not spawn agents or delegate.
- Do not modify project memory or receipts.
- Modify only plan version 3 authorized paths.
- Do not perform remote, destructive, deployment, or publishing actions.

Final response:
1. Findings fixed.
2. Files changed.
3. Exact test evidence.
4. Residual risks.
