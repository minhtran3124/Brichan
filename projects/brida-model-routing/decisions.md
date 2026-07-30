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

## 2026-07-30 — Review route may share the Codex coordinator model

- Status: accepted
- Context: The active manifest routes review to Codex `gpt-5.6-sol`, which is
  also the Codex coordinator default, while reviewer policy prefers
  cross-provider independence for review.
- Decision: Accept this as a deliberate current routing choice. Reviewer
  policy's fresh-session and no-implementation-context rules still apply to
  every review worker.
- Rationale: Review remains cross-provider relative to the Claude implement
  route; sharing the coordinator's model is a capability choice, not a loss of
  implementer independence.
- Trade-offs: A coordinator-biased blind spot is possible when the coordinator
  also authored the task packet under review.
- Owner: Brida
- Evidence: `config/model-routing.json`
- Supersedes: null

## 2026-07-30 — Model catalog must not restate active routing state

- Status: accepted
- Context: Every routing change previously required rewriting the
  `docs/policy/model-catalog.md` "Routed use" column and routing narrative,
  and forgetting caused silent drift between the catalog and the manifest.
- Decision: `docs/policy/model-catalog.md` describes provider and model
  capabilities only. Active route and coordinator assignments live only in
  `config/model-routing.json`; route-state rationale is recorded here in
  decisions, not in the catalog.
- Rationale: Eliminating the duplication removes both the drift risk and the
  maintenance burden instead of synchronizing them.
- Trade-offs: Reading the current assignments requires opening the manifest or
  a `--dry-run` launch instead of prose.
- Owner: Brida
- Evidence: `docs/policy/model-catalog.md`
- Supersedes: null
