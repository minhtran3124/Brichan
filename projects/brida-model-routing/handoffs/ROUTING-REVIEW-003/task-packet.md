You are a fresh independent release-gate reviewer. You did not implement this
change. Brida is the delegated project coordinator.

Task ID:
`ROUTING-REVIEW-003`

Objective:
Review the final plan `MODEL-ROUTING-P1` version 3 implementation and return
PASS only if no contract defect remains.

Inputs:
- `projects/brida-model-routing/plan.md`
- `projects/brida-model-routing/handoffs/ROUTING-REVIEW-001/receipt.md`
- `projects/brida-model-routing/handoffs/ROUTING-REVIEW-002/receipt.md`
- `projects/brida-model-routing/handoffs/ROUTING-FIX-001/receipt.md`
- `projects/brida-model-routing/handoffs/ROUTING-FIX-002/receipt.md`
- Complete current diff against `HEAD`.

Final evidence:
- `make check`: 61 unit, 37 contract, 23 integration tests plus metrics,
  32 receipts, 54 paths/50 references, compatibility, package, and shell gates.
- Fresh git-initialized isolated sandbox with external venv: same full gate
  passed.
- Fresh provider-first import succeeds.
- Fresh orchestration import loads no `brida.cli` module.
- Installed Codex 0.146.0 and Claude 2.1.220 parse generated commands.
- Real settings routes previously created scan/implement/review Herdr workers
  with expected model/effort metadata.
- Codex attached settings, profile, add-dir, sandbox bypass and Claude bare/tool
  overrides fail before Herdr.

Review requirements:
- Check AC1–AC8 and all findings from both prior reviews.
- Reproduce provider-first/no-eager-CLI import boundaries.
- Inspect local provider imports for correctness on named and legacy paths.
- Inspect strict provider argv normalization and legacy rejections.
- Check CLI > environment > manifest precedence.
- Check scope, docs, package/path/receipt contracts, and regression tests.

Rules:
- Read-only; do not edit files, spawn agents, access secrets, commit, push,
  deploy, or publish.
- Findings require exact file/line evidence and an acceptance-criterion or
  project-invariant violation.
- Keep optional hardening and live model availability under residual risks.

Return:
1. Verdict PASS or CHANGES REQUIRED.
2. Findings by severity.
3. Prior-finding closure table.
4. AC1–AC8 results.
5. Test gaps and residual risks.
