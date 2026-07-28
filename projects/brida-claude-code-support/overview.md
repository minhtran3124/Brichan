# Brida Claude Code support

## Objective

Support Claude Code as an explicit Brida runtime without changing Brida's
provider-neutral coordination, verification, durable-memory, or authority
contracts.

## Scope

- Runtime selection through `bin/brida`.
- Dedicated Codex and Claude Code launchers.
- Claude Code policy adapter in `CLAUDE.md`.
- Herdr-only worker lifecycle.
- Runtime-specific tests and documentation.
- Coordinator-mediated handoffs between heterogeneous coding-agent runtimes.

## Architecture

- `bin/brida` selects the coordinator runtime explicitly and dispatches to the
  dedicated Codex or Claude launcher.
- Both launchers disable their runtime's native delegation path.
- `bin/brida-herdr-agent-start` is provider-neutral: Brida supplies the worker
  command, model, bounded task packet, and recorded `brida-` ownership.
- Herdr owns worker session creation, status observation, and pane cleanup;
  project Markdown owns durable human-readable state.

## Evaluated workflow direction

Use a sequential, coordinator-mediated handoff:

1. A read-only planner returns a bounded, versioned plan with scope,
   acceptance criteria, tests, risks, and open decisions.
2. Brida verifies and records the accepted handoff.
3. A separate provider/runtime implements from that accepted artifact.
4. Brida checks criterion-level evidence and routes material changes to a fresh
   independent reviewer, preferably from a different provider.
5. Brida updates durable memory before closing only its recorded worker panes.

Parallel research and review are appropriate when scopes do not overlap.
Parallel implementation requires explicit, non-overlapping path ownership,
dedicated branches and worktrees, parent/child receipts, and review of the
integrated state.

## Constraints

- The user approved both coordinator and worker support for Claude Code.
- Runtime selection is explicit; automatic provider detection is out of scope.
- Native runtime delegation must not bypass Herdr.
- No secrets or credentials may be stored in the repository.
- Chat history is not a durable handoff artifact.
- Required operational receipts use the canonical
  `projects/<slug>/handoffs/<task-id>/receipt.md` location and are checked by a
  dependency-free completeness validator in `make check`. Schema v1 remains
  compatible; schema v2 machine-validates immutable attempt origin, current
  lifecycle, prior-attempt state, and replacement evidence.
- Task packets remain human-readable rather than a machine-enforced schema.
