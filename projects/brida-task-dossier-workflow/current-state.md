# Current state

Last updated: 2026-08-02

## Summary

Status: proposed implementation. Research is complete. The user accepted a
full-document dossier for every task level; checkout-only implementation and
operating-contract changes have not started.

## Completed recently

- Mapped all eleven screenshot artifacts and seven phases to existing Brichan
  primitives.
- Verified checkout feasibility and the installed schema-v1 boundary.
- Compared current official Spec Kit, Kiro, and OpenSpec artifact workflows.
- Two independent read-only Codex workers completed repo-fit and adversarial UX
  audits.
- Wrote `research.md` and draft plan `TDW-PLAN-001`.
- Verified current checkout and installed routing manifests, phase mappings,
  provider divergence, and routing-neutral constraints in `routing-impact.md`.
- Replaced optional dossier creation with a uniform full-doc evidence contract;
  Level now controls depth, reviewer strength, and authorization gates.

## Blockers

- A bounded implementation task and independent operating-contract review are
  required before the pilot can run.

## Risks

- Full docs may increase ceremony and create conflicting sources of truth unless
  templates remain concise and the task index is link-only.
- Branch-derived identity may be ambiguous in multi-worktree or non-branch
  workflows.

## Next actions

1. Implement Phase 1 full-doc contracts and templates in a separate task.
2. Independently review the operating-contract change.
3. Run Level 0/1/2 checkout-mode pilots before considering automation.

## Unverified assumptions

- The full-doc Level 0 workflow will produce acceptable ceremony in real
  dogfood; this must be measured.
- The current checkout `review` route is sufficient for routine Level 1 review;
  the appropriate Level 2 reviewer override/default requires pilot evidence.
