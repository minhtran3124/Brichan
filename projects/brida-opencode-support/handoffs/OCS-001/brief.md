# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `OCS-001`
- Task level: `2`
- Artifact: `brief`
- Artifact version: `2`
- Origin: `planner-session-38ba0ad2-plan-v2`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `38ba0ad2-0366-48ee-8908-821ed7168864`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Claim or decision

`Add OpenCode as the third explicit checkout runtime and Herdr worker provider without weakening Herdr-only delegation, permission boundaries, installed-state compatibility, or Codex/Claude behavior.`

OpenCode differs from the existing providers because decisive controls are merged from configuration layers and environment rather than represented only by stable CLI flags. The implementation therefore needs one explicit command specification containing argv and owned environment, authoritative per-process guard configuration, and pre-spawn rejection of unsafe CLI/env inputs. Success is a guarded coordinator plus routed/legacy workers, a live plugin-backed lifecycle, unchanged installed-project behavior, and complete independent review evidence.

## Evidence

- `PRODUCT.md` defines Herdr-only workers, no new runtime dependencies, and installed-project Codex-only behavior.
- `src/brichan/cli/runtime.py` already dispatches checkout wrappers generically after validating a fixed runtime set.
- `src/brichan/orchestration/worker_launch.py` resolves commands before Herdr mutation but currently cannot carry provider-owned environment.
- Research tasks OCS-001-R1 and OCS-001-R2 are recorded complete with independent sessions in `projects/brida-opencode-support/tasks.md`.

## Uncertainty

- Exact OpenCode 1.18.12 config/flag spellings must be reconfirmed during implementation and locked by tests; the required controls and escalation boundary are settled.
