You are a fresh independent reviewer. You did not implement this change and
must not rely on the prior review verdict. Brida is the delegated project
coordinator acting on the user's behalf.

Task ID:
`ROUTING-REVIEW-002`

Objective:
Independently review the final implementation of accepted plan
`MODEL-ROUTING-P1` version 2 and return a release-gate verdict.

Review inputs:
- Plan and AC1–AC8: `projects/brida-model-routing/plan.md`
- Initial implementation receipt:
  `projects/brida-model-routing/handoffs/ROUTING-001/receipt.md`
- Prior CHANGES REQUIRED review:
  `projects/brida-model-routing/handoffs/ROUTING-REVIEW-001/receipt.md`
- Remediation receipt:
  `projects/brida-model-routing/handoffs/ROUTING-FIX-001/receipt.md`
- Live route receipt:
  `projects/brida-model-routing/handoffs/ROUTING-SMOKE-001/receipt.md`
- Complete current working-tree diff against `HEAD`.

Coordinator evidence:
- Focused final suite: 66 tests passed.
- Full repository `make check`: 58 unit, 37 contract, and 21 integration tests
  passed; metrics, 30 receipts, 54 paths/50 references, compatibility,
  package import, and shell syntax passed.
- Fresh git-initialized isolated repository copy with an external virtual
  environment passed the same full gate.
- Installed Codex 0.146.0 and Claude Code 2.1.220 parse generated commands.
- All four final JSON route dry-runs match the manifest.
- Real Herdr workers were created through `scan`, `implement`, and `review`
  routes with expected model/effort metadata.
- Attached Codex delegation and sandbox bypass forms now fail before Herdr.
- Claude uses the installed-runtime-verified single argument
  `--disallowed-tools=Task` before any passthrough or `--` separator.

Required review:
- Re-evaluate AC1–AC8 from the final code and evidence.
- Confirm every HIGH/MEDIUM finding from `ROUTING-REVIEW-001` is fixed.
- Confirm LOW-1 and LOW-3 are fixed.
- Treat LOW-2 (live model existence without a dynamic provider catalog) as a
  residual risk unless it violates an explicit acceptance criterion.
- Inspect attached/separated/equals Codex parsing and Claude `--` ordering.
- Check package boundaries, legacy compatibility, fail-before-Herdr behavior,
  tests, docs, and scope.

Rules:
- Do not assume the remediation is correct.
- Cite concrete file/line evidence for every finding.
- Do not edit files, spawn agents, commit, push, deploy, publish, broaden
  permissions, or access secrets.
- Run read-only focused tests and `git diff --check` if useful.
- Distinguish contract defects from optional hardening.

Return:
1. Verdict: PASS or CHANGES REQUIRED.
2. Findings by severity with exact evidence.
3. Prior-finding remediation assessment.
4. AC1–AC8 pass/fail.
5. Test gaps and residual risks.
