# Current state

Last updated: 2026-08-02

## Summary

Status: implementation and Level 0/1/2 dogfood pilots reviewed and passed. The
checkout-only full-document dossier contract is operational, with measured
evidence depth and ceremony.

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
- Completed three full-doc pilots: exact-byte Level 0, tested normalizer Level
  1, and fail-closed release-policy simulation Level 2.
- Verified all 33 standard pilot artifacts meet their lane evidence floor:
  Level 0 at least one item, Level 1 at least two, and Level 2 at least three.
- Routine Luna medium plan/code reviews passed Levels 0/1; a documented Sol
  high override passed Level 2, including 36 supplemental malformed cases and
  100 deterministic repetitions.
- Confirmed the current routing manifest remains effective without workflow
  keys: plan resolved to Claude Opus high, implement to Claude Opus medium,
  routine review to Codex Luna medium, and Level 2 used a one-off override.

## Blockers

- None for the checkout-mode pilot.

## Risks

- Full docs create substantial ceremony: the Level 0 dossier is 639 lines for a
  one-line fixture. Concise generation is needed without removing artifacts or
  weakening evidence.
- Evidence depth is mechanically countable but evidence quality still requires
  reviewer judgment.
- The closed index projection and single-table rule may create pilot friction.

## Next actions

1. Design a concise Level 0/1 generator for repetitive metadata, links, and
   status while retaining all eleven artifacts.
2. Add a dossier summary command for evidence depth, provenance, stale links,
   and review independence.
3. Gather more pilot samples before considering installed-mode support.

## Unverified assumptions

- One three-lane run is directional evidence, not enough to establish long-term
  throughput or resumability.
- Routine Luna medium review passed these bounded Level 0/1 samples, but broader
  product or compatibility changes may expose different review needs.
