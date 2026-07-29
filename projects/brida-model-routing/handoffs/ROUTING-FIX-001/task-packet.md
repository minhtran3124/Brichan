You are an implementation worker coordinated by Brida, an AI Chief of Staff
acting on the user's behalf.

Task ID:
`ROUTING-FIX-001`

Objective:
Remediate the independent review findings for accepted plan
`MODEL-ROUTING-P1` version 2 and make all focused repository gates pass.

Context:
The initial implementation is complete in the shared feature-branch worktree.
Independent review `ROUTING-REVIEW-001` found attached Codex short options can
bypass guard validation, provider command translation is in the wrong package,
an unreachable compatibility helper remains, and Claude's variadic deny flag
can absorb a legacy positional prompt. Coordinator-owned receipt/path findings
have already been fixed.

Upstream plan and receipt:
- Accepted plan ID: `MODEL-ROUTING-P1`
- Plan version: `2`
- Plan status: `accepted`
- Plan path: `projects/brida-model-routing/plan.md`
- Review evidence:
  `projects/brida-model-routing/handoffs/ROUTING-REVIEW-001/receipt.md`
- Handoff receipt:
  `projects/brida-model-routing/handoffs/ROUTING-FIX-001/receipt.md`
- Receipt requirement: `mandatory`

In scope:
- Move provider-specific command translation from
  `src/brida/orchestration/provider_commands.py` to a suitable module under
  `src/brida/cli/` and update imports/path registration/tests.
- Normalize and validate Codex forms `-c VALUE`, `-c=VALUE`, `-cVALUE`,
  `--config VALUE`, `--config=VALUE`, `-s VALUE`, `-s=VALUE`, `-sVALUE`,
  `-m VALUE`, `-m=VALUE`, and `-mVALUE`.
- Ensure equivalent forms cannot enable native delegation, select
  danger-full-access, request Codex `ultra`, or smuggle forbidden arbitrary
  legacy settings.
- Remove unreachable `_apply_worker_defaults` and replace dead tests with
  coverage of the active guard builders.
- Make Claude's native-agent deny option unambiguous before legacy positional
  prompts while preserving CLI compatibility.
- Update `docs/policy/operating-principles.md` to resolve named settings routes
  before consulting the model catalog.
- Add regression tests for attached option forms, `--enable multi_agent`,
  invalid coordinator env overrides, malformed coordinator manifest startup,
  legacy Claude launch, and non-JSON dry-run output where practical.

Out of scope:
- Project memory under `projects/brida-model-routing/` and `projects/index.md`;
  Brida owns these.
- New routing schema fields or a hard-coded provider/model compatibility map.
- Credentials, billing, deployments, publishing, permission expansion,
  commits, pushes, or PR creation.

Acceptance criteria:
- AC1–AC8 in plan version 2 remain satisfied.
- Every HIGH and MEDIUM review finding is fixed.
- LOW-1 and LOW-3 are fixed.
- LOW-2 remains an explicit residual risk because validating live model
  existence would require a dynamic provider catalog or reintroduce hard-coded
  model knowledge.
- Existing legacy and named-route compatibility remains green.

Required verification:
- Focused provider-command, routing, launcher, CLI, and contract tests.
- `make check`.
- `git diff --check`.
- Report exact commands and summaries.

Constraints:
- Do not spawn sub-agents or delegate.
- Do not modify project memory or handoff receipts.
- Do not modify files outside plan version 2 authorized paths.
- Do not perform destructive or remote actions.
- Preserve unrelated changes.

Final response:
1. Outcome and review findings addressed.
2. Files changed.
3. Exact verification.
4. Residual risks.
