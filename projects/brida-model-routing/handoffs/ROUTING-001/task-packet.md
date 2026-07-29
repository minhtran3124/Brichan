You are a worker agent coordinated by Brida, an AI Chief of Staff acting on the
user's behalf.

Task ID:
`ROUTING-001`

Objective:
Implement accepted plan `MODEL-ROUTING-P1` version 1 end to end.

Context:
Brida currently duplicates active model defaults across Python, instructions,
tests, and hand-written Herdr commands. The accepted design makes
`config/model-routing.json` the active repository source of truth and uses
provider-neutral code to resolve coordinator defaults and named worker routes.

Upstream plan and receipt:
- Accepted plan ID: `MODEL-ROUTING-P1`
- Plan version: `1`
- Plan status: `accepted`
- Plan path: `projects/brida-model-routing/plan.md`
- Handoff receipt path:
  `projects/brida-model-routing/handoffs/ROUTING-001/receipt.md`
- Receipt requirement: `mandatory`

In scope:
- Every authorized implementation path in the accepted plan.
- Repository JSON routing settings for coordinator defaults and named `plan`,
  `implement`, `review`, and `scan` routes.
- Dependency-free Python 3.10 loader, validation, resolution, provider command
  construction, one-off override precedence, and no-mutation dry-run output.
- Herdr launcher named-route support plus legacy explicit-command compatibility.
- Code-enforced native delegation disabling and rejection of Codex `ultra`,
  permission-bypass options, arbitrary argv settings, invalid runtime/route,
  malformed settings, and unsupported effort.
- Coordinator adapter migration, docs, structural registration, and focused
  unit/integration/contract tests.

Out of scope:
- `projects/brida-model-routing/` and `projects/index.md`; Brida owns these.
- Automatic route classification, credentials, billing, deployment,
  publication, release/version bump, native delegation, or permission expansion.
- Commits, pushes, PR creation, or remote state changes.

Deliverables:
- Complete implementation in the shared feature-branch worktree.
- Tests demonstrating settings changes alter resolved commands without prompt
  edits and invalid configurations fail before Herdr mutation.
- A concise final report with changed files, test evidence, and residual risks.

Acceptance criteria:
- Meet AC1 through AC8 exactly as written in
  `projects/brida-model-routing/plan.md`.
- Keep model/effort configuration separate from security and permission policy.
- Do not duplicate active model defaults in Python constants or runtime
  instructions.
- Preserve existing explicit worker command behavior as a documented legacy
  compatibility path.

Required verification:
- Run focused tests for routing, adapters, launcher parsing/command generation,
  validation failure, dry-run no-mutation, and legacy compatibility.
- Run `make check`.
- Run `git diff --check`.
- Report commands and exact pass/fail summaries. Do not fabricate unavailable
  real-provider evidence; Brida will run final sandbox and real runtime tests.

Constraints:
- Do not spawn sub-agents or delegate this task.
- Do not broaden permissions or access secrets.
- Do not modify files outside the accepted plan's authorized implementation
  paths.
- Do not modify Brida project memory or receipt files.
- Do not perform destructive, remote, production, deployment, publishing,
  commit, push, or PR actions.
- Preserve unrelated user changes.

Escalate when:
- A required API would force arbitrary command execution or weaken a guardrail.
- Backward compatibility conflicts with fail-before-Herdr validation.
- The accepted criteria require a material architecture change beyond the plan.

Final response:
1. Outcome.
2. Files/artifacts changed.
3. Verification and evidence.
4. Risks, assumptions, and unresolved issues.
