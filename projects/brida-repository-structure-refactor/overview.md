# Brida repository structure refactor

## Objective

Create an evidence-backed refactor plan that reduces root-level Markdown
sprawl, establishes clear module and documentation ownership, preserves
multi-agent coding contracts, and scales testing/deployment workflows.

## Scope

- Repository information architecture and module boundaries.
- Placement and ownership of policy, runtime, project-memory, evaluation, and
  contributor documentation.
- Multi-agent branch/worktree/receipt compatibility.
- Test, CI, packaging, release, and deployment implications.
- Phased migration with compatibility and rollback gates.

## Constraints

- Planning only; do not move or rewrite production files in this phase.
- Root-level entrypoints required by runtimes or community conventions may
  remain when justified.
- Existing Codex, Claude Code, Herdr, receipt, test, and project-memory
  contracts must remain valid throughout migration.
- No deployment, publishing, remote changes, or destructive actions.
