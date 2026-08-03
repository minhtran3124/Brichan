# Model-routing impact assessment

Status: verified
Verified: 2026-08-02
Scope: current adaptive task-dossier design against current checkout and
installed-project routing

## Verdict

The current `config/model-routing.json` still works mechanically. It parses,
resolves the coordinator defaults and all four required worker routes, produces
guarded provider commands, and passes focused tests.

The adaptive task-dossier design is compatible only if it remains
**routing-neutral**:

- workflow phases classify work and evidence;
- existing named routes select worker capability;
- phase names and task levels are not added to routing JSON;
- effective route/runtime/model/effort are recorded in task evidence;
- high-risk review strength and independence are enforced by workflow policy,
  not assumed from a route name.

No routing file was changed by this audit. The existing dirty checkout diff was
preserved.

## Current route matrices

### Checkout mode

Source: `config/model-routing.json`

| Role | Route | Runtime | Model | Effort | Workflow use |
|---|---|---|---|---|---|
| Default coordinator | — | Codex | `gpt-5.6-sol` | medium | Intake, Level 0 direct work, Close |
| Explicit Claude coordinator | — | Claude | `claude-fable-5` | medium | Checkout-only explicit runtime |
| Planning | `plan` | Claude | `claude-opus-5` | high | Brainstorm/design/plan when delegated |
| Implementation | `implement` | Claude | `claude-opus-5` | medium | Execute |
| Review | `review` | Codex | `gpt-5.6-luna` | medium | Routine independent review |
| Scan | `scan` | Claude | `claude-sonnet-5` | medium | Repository discovery and evidence scan |

The current uncommitted user diff changes:

- `plan`: `claude-fable-5` → `claude-opus-5`;
- `review`: `gpt-5.6-sol` → `gpt-5.6-luna`.

Both values are schema-valid and resolved correctly. The second change is a
semantic downgrade from a high-capability final reviewer to a fast routine
reviewer. It is acceptable for Level 1/routine review, but should not silently
be treated as sufficient for every Level 2/high-risk review.

Claude authentication was `loggedIn: true` when rechecked on 2026-08-02.
Authentication remains operational state and can lapse without making the JSON
invalid.

### Installed-project mode

Source for new initialization:
`src/brichan/resources/dogfood_v1/config/model-routing.json`

| Role | Route | Runtime | Model | Effort | Workflow use |
|---|---|---|---|---|---|
| Installed coordinator | — | Codex | `gpt-5.6-terra` | medium | Intake, Level 0 direct work, Close |
| Dormant Claude coordinator entry | — | Claude | `claude-opus-5` | high | Required by schema, not exposed by current Codex-only installed product |
| Planning | `plan` | Codex | `gpt-5.6-sol` | high | Design/plan |
| Implementation | `implement` | Codex | `gpt-5.6-terra` | medium | Execute |
| Review | `review` | Codex | `gpt-5.6-sol` | high | Material review in a fresh session |
| Scan | `scan` | Codex | `gpt-5.6-luna` | medium | Repository discovery and evidence scan |

An initialized target resolves workers from its own
`.brichan/config/model-routing.json`, not from the checkout config. Root config
changes therefore do not propagate to installed targets. The installed config
is package-owned, hashed, and immutable under schema v1.

A disposable initialized target resolved all four installed routes exactly as
listed and reported healthy schema-v1 state.

## Phase-to-route mapping

| Workflow phase | Routing behavior | Reason |
|---|---|---|
| Intake | Coordinator, no worker route | Clarify objective, scope, authority, and task level |
| Explore/Brainstorm | `plan` for option reasoning; `scan` only for repository/evidence discovery | Brainstorming and scanning are not the same capability |
| Design | `plan` | Architecture and trade-off synthesis |
| Plan | `plan` | Accepted implementation plan |
| Execute | `implement` | Bounded code/document implementation |
| Verify | Coordinator plus `scan` for mechanical evidence when useful | Verification is an evidence gate, not necessarily independent review |
| Review | `review` | Fresh independent session when required |
| Close | Coordinator, no worker route | Memory, cleanup, report |
| Ship | Coordinator-authorized action | PR/publish/deploy is authority, not model routing |

Level behavior:

- Level 0: coordinator may author concise docs, but a fresh `review` session
  records plan/design review; implementation routing is used only when needed.
- Level 1: invoke only the existing routes materially needed by the task.
- Level 2: require explicit design/plan and fresh review; route strength and
  effective resolution must be recorded.

## Compatibility boundaries

### Compatible without routing schema changes

- Adding Level 0/1/2 classification to workflow documentation.
- Mapping multiple phases to an existing route.
- Reusing the same routes with lighter evidence depth for simple work.
- Recording effective route/model/effort in a task index or receipt.
- Using a documented one-off route override when stronger review is required.
- Keeping checkout and installed routing different by design.

### Requires routing code/schema changes

- Adding `brainstorm`, `design`, `verify`, or `ship` keys to
  `config/model-routing.json`.
- Adding task level, risk, authority, fallback, capability, or independence
  fields to route objects.
- Automatically selecting a route from task classification.
- Defining tiered routes such as `review_standard` and `review_high_risk`.
- Provider fallback or auth-aware automatic rerouting.

The parser requires exactly `plan`, `implement`, `review`, and `scan`, and each
route accepts exactly `runtime`, `model`, and `effort`. Unknown fields fail
before Herdr mutation.

## Findings

### High — Route names do not encode workflow levels or phase gates

Task classification must stay outside model routing. Otherwise the proposal
changes a load-bearing public contract and requires parser, documentation,
packaging, and regression changes.

### High — Checkout and installed modes intentionally behave differently

Checkout delegates plan/implement/scan to Claude, while installed mode is
Codex-only. Task artifacts must record effective resolution and must not claim
that a phase always uses one provider/model.

### High — Review independence is not a route property

A different route name or model does not prove a fresh independent session.
Session identity and plan version must remain in the receipt/review evidence.

### Medium — Current checkout review default is routine, not universal high-risk

`gpt-5.6-luna` medium is consistent with fast routine review in the model
catalog. For Level 2 work, either:

1. use a documented per-launch override to a stronger verified reviewer;
2. change the checkout review default after a separate routing decision; or
3. add tiered review routes in a future routing schema.

The pilot should use option 1 and measure frequency before changing schema.

### Medium — Provider health is outside JSON validation

Dry-run validates syntax and command construction, not credentials or provider
availability. Preflight must report an unavailable configured provider rather
than silently selecting another model.

### Medium — Root config is not the installed source of truth

Changing `config/model-routing.json` affects checkout mode only. New installed
targets receive the packaged config; existing targets retain their initialized
managed copy until an explicit supported reinitialization/update lifecycle.

### Medium — Overrides need an evidence rule

The CLI correctly permits runtime/model/effort overrides, but a Level 2 task
must record the route name and effective values. A downgrade must not happen
silently.

### Low — Routing decision memory is stale relative to the dirty checkout

`projects/brida-model-routing/decisions.md` records `gpt-5.6-sol` as the active
review route, while the current working-tree config uses Luna. This may be an
intentional unaccepted local change, so the audit did not rewrite durable
decision history.

## No-regression test plan

1. Parse and dry-run all four routes from both manifests.
2. Assert coordinator defaults for both checkout runtimes and installed Codex.
3. Assert a healthy installed target uses its own managed routing file.
4. Assert Level 0 creates the full dossier and receives fresh plan/design review.
5. Assert phase mappings use only the four existing named routes.
6. Assert skipped phases are `not-required`, not inferred from missing files.
7. Assert receipt/index records effective runtime, model, and effort.
8. Assert Level 2 review uses a fresh session and exact accepted-plan version.
9. Assert overrides remain guard-enforced and visible in evidence.
10. Assert missing provider/auth returns a bounded preflight failure.
11. Assert checkout config changes do not mutate installed target config.
12. Assert schema-v1 remains unchanged during the checkout-only pilot.

## Recommended decision

Keep `TDW-PLAN-001` routing-neutral and preserve the current four-route schema.
For the checkout pilot:

- use `plan` for delegated brainstorm/design/planning;
- use `scan` only for discovery/evidence scanning;
- use `implement` for execution;
- use `review` for routine review;
- use an explicit, recorded stronger override for Level 2 review;
- allow the coordinator to author concise Level 0 docs, but require a fresh
  `review` session for plan/design evidence;
- perform Intake, Close, and authorized Ship in the coordinator.

Do not change routing JSON until pilot evidence shows repeated need for
tier-specific routes or automated capability selection.
