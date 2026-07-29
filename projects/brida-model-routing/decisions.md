# Decision log

## 2026-07-29 — Repository-owned routing manifest

- Status: accepted
- Context: Model defaults are duplicated across runtime code, instructions,
  documentation, tests, and hand-written Herdr commands.
- Decision: Use `config/model-routing.json` as the active routing source of
  truth and resolve named roles through importable orchestration code.
- Rationale: JSON is dependency-free on Python 3.10 and works consistently
  across Codex, Claude, and Herdr.
- Trade-offs: Provider-native profiles remain usable underneath Brida but are
  not the shared cross-provider routing contract.
- Owner: Brida
- Evidence: `projects/brida-model-routing/plan.md`
- Supersedes: Claude model routing decision dated 2026-07-27 for active defaults.

## 2026-07-29 — Safety settings remain non-configurable

- Status: accepted
- Context: Routing flexibility must not broaden worker authority.
- Decision: Configure only runtime, model, and effort; enforce native delegation
  disabling, forbidden effort, and permission-bypass rejection in code.
- Rationale: Model choice and security policy have different authority.
- Trade-offs: Adding a new provider requires code support rather than arbitrary
  command configuration.
- Owner: Brida
- Evidence: `projects/brida-model-routing/plan.md`
- Supersedes: null

## 2026-07-29 — Normalize provider argv before enforcing guardrails

- Status: accepted
- Context: Independent review found that Codex accepts attached short-option
  spellings that the initial token validator did not normalize.
- Decision: Parse all supported equivalent option forms into one normalized
  representation before model, effort, delegation, and permission checks.
- Rationale: A safety invariant must follow provider CLI semantics, not one
  preferred spelling.
- Trade-offs: Provider CLI syntax remains a compatibility surface that requires
  regression tests when provider versions change.
- Owner: Brida
- Evidence:
  `projects/brida-model-routing/handoffs/ROUTING-REVIEW-001/receipt.md`
- Supersedes: null

## 2026-07-29 — Provider command translation belongs to CLI adapters

- Status: accepted
- Context: Review found provider-specific command construction inside the
  provider-neutral orchestration package.
- Decision: Move command translation to `src/brida/cli/`; orchestration may
  consume the adapter but does not own provider syntax.
- Rationale: This matches the documented repository boundary and keeps routing
  resolution independent from provider argv details.
- Trade-offs: The Herdr launcher imports a stable CLI adapter module.
- Owner: Brida
- Evidence: `docs/architecture/repository-layout.md`
- Supersedes: null

## 2026-07-29 — Orchestration loads provider adapters only at resolution time

- Status: accepted
- Context: Moving provider translation under `src/brida/cli/` exposed an eager
  import cycle when that canonical module was imported first.
- Decision: Keep provider translation in CLI adapters and import it locally only
  when worker launch resolution requires provider command construction.
- Rationale: This removes order-dependent imports and preserves the
  provider-neutral orchestration package boundary.
- Trade-offs: One runtime-local import is less visible than a top-level import,
  so fresh-interpreter package checks become mandatory.
- Owner: Brida
- Evidence:
  `projects/brida-model-routing/handoffs/ROUTING-REVIEW-002/receipt.md`
- Supersedes: null
