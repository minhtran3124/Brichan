# Decision log

## 2026-07-29 — Explore installed CLI plus project initialization

- Status: superseded
- Context: Five independent assessments found strong package foundations but
  checkout-root coupling and no safe project lifecycle.
- Decision: Run bounded discovery and, only if it passes, a disposable
  prototype of an installed CLI plus explicit project initialization. Defer
  the MVP decision; retain clone mode and do not pursue full-repo vendoring.
- Rationale: This best separates tool-owned code from project-owned state while
  preserving current guardrails and enabling incremental validation.
- Trade-offs: Adds schema, migration, ownership, external-tool compatibility,
  and support obligations.
- Owner: Brida; final product authority remains with the user.
- Evidence: `assessment.md`; first independent verdict `CHANGES REQUIRED`,
  remediated before focused re-review.

## 2026-07-29 — One-user dogfood scope

- Status: accepted
- Context: The user is the first target user; a later cohort may contain 3–5
  trusted users.
- Decision: Proceed toward a narrowly supported installable dogfood tool.
  Exclude commercialization, market-demand gates, broad compatibility, and
  support for unrelated edge cases.
- Rationale: The immediate value is improving the owner's real Brida workflow,
  so direct use provides stronger evidence than market research.
- Trade-offs: The prototype may be intentionally environment- and
  runtime-specific; wider compatibility is deferred until a dogfood failure
  requires it.
- Owner: User.
- Evidence: User direction in the 2026-07-29 project turn; `assessment.md`.
- Supersedes: 2026-07-29 — Explore installed CLI plus project initialization.

## 2026-07-29 — Codex-first schema-v1 vertical slice

- Status: accepted
- Context: The one-user dogfood needs to run from an installed package inside
  an existing Git repository without a separate Brida checkout.
- Decision: Ship the first local vertical slice as Codex-only installed mode.
  `brida init` owns only a versioned `.brida/` footprint; project launch injects
  package-owned developer instructions and Herdr skill discovery through Codex
  CLI overrides and executes external `codex` directly at the target root.
  Checkout mode remains available only when the package proves it belongs to
  the `BRIDA_ROOT` checkout.
- Rationale: This creates the smallest end-to-end owner workflow while avoiding
  edits to target `AGENTS.md`, `.codex/`, `CLAUDE.md`, or root wrappers.
- Trade-offs: Installed mode uses a narrow Codex argument allowlist, schema v1
  has no repair/migration, and package upgrades require deliberate
  reinitialization. Windows, Claude installed mode, and broad repository shapes
  remain deferred.
- Owner: Brida within the user-approved one-owner dogfood scope.
- Evidence: `docs/guides/installable-dogfood.md`; installed-wheel integration
  tests; final independent reviewer verdict `PASS`; 152-test `make check`.
