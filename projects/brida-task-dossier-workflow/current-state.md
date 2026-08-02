# Current state

Last updated: 2026-08-02

## Summary

Status: implementation reviewed and passed. The checkout-only full-document
dossier contract is ready for Level 0/1/2 dogfood pilots.

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
- Implemented the checkout contract, eleven templates, dry-run-first
  scaffolder, read-only validator, policy integration, and repository gates.
- Independent Codex Sol high review reproduced eight substantive safety and
  evidence gaps across two review rounds; all were remediated and re-reviewed.
- Final verification passed 96 focused tests and `make check` with 234 unit,
  61 contract, and 53 integration tests.
- Preserved the pre-existing checkout routing diff exactly: plan uses Claude
  Opus high and routine review uses Codex Luna medium. Installed resources
  remain unchanged.

## Blockers

- None for the checkout-mode pilot.

## Risks

- Full docs may increase ceremony and create conflicting sources of truth unless
  templates remain concise and the task index is link-only.
- Evidence depth is mechanically countable but evidence quality still requires
  reviewer judgment.
- The closed index projection and single-table rule may create pilot friction.

## Next actions

1. Run Level 0/1/2 checkout-mode pilots with complete dossiers.
2. Measure ceremony, resumability, routing provenance, and review quality.
3. Evaluate pilot evidence before considering installed-mode support.

## Unverified assumptions

- The full-doc Level 0 workflow will produce acceptable ceremony; the pilot
  must measure this.
- The current `review` route is sufficient for routine Level 0/1 review; pilot
  evidence must test this against a stronger Level 2 one-off override.
