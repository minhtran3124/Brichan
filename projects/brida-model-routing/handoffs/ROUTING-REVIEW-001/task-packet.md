You are an independent reviewer. You did not implement this change. Brida is
the delegated project coordinator acting on the user's behalf.

Task ID:
`ROUTING-REVIEW-001`

Objective:
Independently review the complete implementation of accepted plan
`MODEL-ROUTING-P1` version 1 for correctness, regressions, safety, compatibility,
test quality, and scope compliance.

Review inputs:
- Original objective and AC1–AC8:
  `projects/brida-model-routing/plan.md`
- Implementation task and receipt:
  `projects/brida-model-routing/handoffs/ROUTING-001/task-packet.md`
  `projects/brida-model-routing/handoffs/ROUTING-001/receipt.md`
- Live smoke-test evidence:
  `projects/brida-model-routing/handoffs/ROUTING-SMOKE-001/receipt.md`
- Complete working-tree diff against `HEAD`.
- Current manifest, code, tests, docs, and repository policy.

Known coordinator verification:
- Focused routing tests: 29 passed after coordinator fixes.
- Full repository `make check`: passed with metrics 10, unit 57, contract 37,
  integration 17, 27 receipt validations, repository path checks, compatibility
  gates, import check, and shell syntax.
- Isolated git-initialized sandbox at a temporary path: full `make check`
  passed using a virtual environment outside the copied repository.
- Installed Codex 0.146.0 and Claude Code 2.1.220 both parse generated route
  arguments.
- Real Herdr `scan` route created a Codex Luna/medium worker and all four JSON
  route dry-runs matched the manifest without changing repository status.

Review for:
- Incorrect behavior and regressions.
- Security, privacy, data-loss, and permission risks.
- Missing edge cases and error handling.
- Compatibility and performance risks.
- Missing or misleading tests.
- Scope drift and unnecessary complexity.

Specific invariants:
- Model/provider/effort defaults must be settings-driven, not active constants
  hidden in code or runtime instructions.
- Security controls remain code-enforced: native delegation disabled, Codex
  `ultra` rejected, permission bypass rejected, and arbitrary provider argv not
  allowed through named routes.
- Invalid settings/routes/overrides fail before Herdr mutation.
- Legacy explicit worker command behavior remains compatible and does not
  require loading a valid routing manifest.
- Route runtime switches cannot silently retain an incompatible provider model.
- `plan` and `review` route to Claude Opus/high; `implement` to Codex
  Terra/medium; `scan` to Codex Luna/medium.

Rules:
- Do not assume the implementation is correct.
- Cite concrete file/line evidence for every finding.
- Classify a defect only when it violates the objective, acceptance criteria,
  or an established project invariant; place optional hardening under residual
  risks.
- Do not modify any files.
- Do not spawn agents or delegate.
- Do not commit, push, open a PR, deploy, publish, broaden permissions, or
  access secrets.
- If evidence is insufficient, state what is missing.

Required verification:
- Inspect the complete diff and relevant surrounding code.
- Run focused read-only tests if useful.
- Run `git diff --check`.
- Compare implementation to AC1–AC8 one by one.

Return:
1. Verdict: PASS or CHANGES REQUIRED.
2. Findings ordered by severity: critical, high, medium, low.
3. Evidence for each finding.
4. AC1–AC8 assessment.
5. Test gaps.
6. Residual risks and required human decisions.
