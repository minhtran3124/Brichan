# Repository structure refactor plan

## Recommendation

Adopt a **stable adapters + canonical docs + importable core** structure.

- Keep runtime-discovery files and public repository entrypoints at the root.
- Move internal policy and operational documentation into an owned `docs/`
  taxonomy.
- Keep existing command paths as stable wrappers while implementation is
  extracted into `src/brida/`.
- Freeze durable evidence and project-memory locations during the refactor.
- Execute one reversible phase at a time; do not combine documentation moves,
  code extraction, and data migration in one change.

This gives Brida a smaller, intentional root without breaking Codex, Claude,
Herdr, receipt, or CI contracts.

## Target structure

```text
.
├── AGENTS.md                 # permanent Codex/project discovery adapter
├── CLAUDE.md                 # permanent Claude discovery adapter
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md           # retain initially; reassess after migration
├── SECURITY.md               # retain initially; reassess after migration
├── LICENSE
├── VERSION
├── Makefile
├── pyproject.toml            # add only when the importable package exists
├── bin/                      # stable user-facing launchers
├── scripts/                  # stable automation/compatibility wrappers
├── src/brida/
│   ├── cli/
│   ├── orchestration/
│   └── contracts/
│       └── receipts/
├── docs/
│   ├── index.md
│   ├── policy/
│   │   ├── identity.md
│   │   ├── operating-principles.md
│   │   ├── memory-policy.md
│   │   ├── model-catalog.md
│   │   └── reviewer.md
│   ├── workflows/            # canonical home for future tracked procedures
│   ├── architecture/
│   └── history/
│       └── setup-status.md
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── .agents/                  # runtime-specific adapters and skills
├── .claude/
├── .codex/
├── projects/                 # durable project memory and receipts; freeze
├── evals/                    # historical evidence; freeze
└── metrics/                  # generated/recorded metrics; freeze
```

The tree is a target boundary, not authorization to create every empty
directory immediately.

## Placement contract

| Category | Placement | Contract |
| --- | --- | --- |
| Native agent discovery | Root `AGENTS.md`, `CLAUDE.md` | Permanent, concise adapters; may reference canonical policy |
| Public repository entrypoints | Root README, changelog, license, version, Makefile | Stable paths |
| Contributor/security docs | Root for the first migration | Move to `.github/` or `docs/` only after link and platform checks |
| Internal policy | `docs/policy/` | Single canonical source, explicit owner and review requirement |
| Operational procedures | `docs/workflows/` | Procedure-oriented; not loaded at every agent startup |
| Historical setup notes | `docs/history/` | Non-normative and clearly labeled |
| Runtime commands | Existing `bin/` and validator paths | Stable wrappers; implementation may move behind them |
| Importable implementation | `src/brida/` | No dependency on project-memory or historical evidence |
| Durable state/evidence | `projects/`, `evals/`, `metrics/` | No relocation in this refactor |

## Module boundaries

```text
root discovery files ──> canonical policy docs
bin/ and scripts/ ─────> brida.cli
brida.cli ─────────────> brida.orchestration + brida.contracts
projects/evals/metrics   data only; never imported as implementation
```

Initial extraction candidates:

- `brida.contracts.receipts`: schema, parsing, validation, and discovery.
- `brida.orchestration`: Herdr client, pane/session layout, worker launch.
- `brida.cli`: compatibility entrypoints used by current wrappers.

Provider-specific behavior should sit behind orchestration adapters rather than
forking the whole architecture into Codex and Claude islands.

## Multi-agent coding contract

The refactor should make concurrent work safer through explicit ownership:

- One phase and one bounded path set per worker.
- Root adapters, shared schemas, and migration manifests are integrator-owned.
- Workers use independent Herdr main-agent sessions and isolated worktrees for
  concurrent writes.
- Every task packet states allowed paths, forbidden paths, acceptance commands,
  rollback point, and receipt location.
- `projects/<slug>/handoffs/<task-id>/receipt.md` remains the canonical durable
  handoff path.
- Historical `evals/` are read-only during implementation.
- Changes to policy or discovery adapters require one Codex smoke test and one
  Claude smoke test before merge.
- Add a path/reference checker before moving the first file so silent
  instruction loss becomes a test failure.

`CLAUDE.md` should import or point to shared instructions while retaining any
Claude-only guidance. `AGENTS.md` remains the Codex project-root entrypoint;
nested `AGENTS.md` files may later scope guidance to modules when needed.

## Test, CI, release, and deployment strategy

`make check` remains the compatibility gate throughout the migration. The
current baseline is 65 passing tests, 16 metrics rows, and 10 canonical
receipts.

Add gates in this order:

1. **Structural contract:** required entrypoints, links/imports, no stale path
   references, and canonical receipt discovery.
2. **Unit tests:** receipt parser/schema and orchestration modules.
3. **Integration tests:** stable wrappers invoke the new package correctly.
4. **Runtime smoke:** `bin/brida`, Codex startup, Claude startup, and Herdr
   launcher behavior.
5. **Packaging lane:** only after `pyproject.toml` and `src/brida/` exist.

There is currently no verified package publication, container deployment, or
deployment workflow. This plan must not invent a deploy migration. A future
release lane is added only when Brida gains a real distributable artifact.

Compatibility policy:

- Keep executable wrapper paths permanently unless a separate deprecation is
  approved.
- Keep temporary Markdown pointer stubs for one release after canonical moves.
- Remove a stub only when repository search, link checks, both agent startup
  smokes, and `make check` pass without it.

## Migration phases

### Phase 0 — Characterize and guard

Status: complete on 2026-07-28.

Deliverables:

- Inventory every root file and classify it as discovery, public, policy,
  workflow, history, runtime, or durable data.
- Add a machine-readable path manifest and Markdown/import link checker.
- Capture current CLI, receipt, agent-startup, and `make check` behavior.
- Record an explicit rollback commit.

Acceptance:

- Existing baseline remains green.
- Every path consumed by Makefile, CI, tests, launchers, agent instructions, or
  receipt validation is represented.
- No files move in this phase.

Rollback: remove characterization-only tests and manifest.

### Phase 1 — Canonicalize documentation

Status: complete and independently reviewed on 2026-07-28.

Deliverables:

- Create `docs/index.md` and the policy/workflow/history taxonomy.
- Move internal policy and operational docs in small batches.
- Update `AGENTS.md`, `CLAUDE.md`, skill references, README links, and tests
  atomically with each batch.
- Leave root pointer stubs for moved policy files for one release.
- Keep ignored `internal-docs/` scratch outside the tracked migration until a
  separate content, branding, link, and accuracy review is authorized.

Acceptance:

- No duplicated normative policy.
- Codex reports the intended startup instructions. Claude is normally checked
  the same way; when provider quota is unavailable, static Claude contract
  checks pass and the runtime smoke remains explicitly deferred.
- Link/reference checker and `make check` pass.
- `projects/`, `evals/`, `metrics/`, and executable paths are unchanged.

Rollback: revert the individual documentation batch; root adapters remain valid.

### Phase 2 — Extract receipt contracts

Status: implemented; independently reviewed with final verdict `PASS`.

Deliverables:

- Introduce `pyproject.toml` and `src/brida/contracts/receipts/`.
- Extract schema, parsing, validation, and discovery from the current validator.
- Preserve the existing validator command as a thin wrapper.

Acceptance:

- Contract and unit tests cover valid, invalid, and discovery edge cases.
- All canonical receipts validate with unchanged semantics.
- Existing callers and `make check` remain green.

Rollback: point the stable wrapper back to the prior implementation.

### Phase 3 — Extract orchestration and CLI

Status: implemented; final review in progress.

Deliverables:

- Extract Herdr/session/launcher logic into `brida.orchestration`.
- Route existing `bin/` launchers through `brida.cli`.
- Separate provider-neutral orchestration from Codex/Claude adapters.

Acceptance:

- Existing launcher paths and arguments behave identically.
- Codex-only, Claude-only, and mixed-agent smoke tasks succeed.
- Cleanup contracts close only Brida-owned panes.

Rollback: restore wrapper delegation to the prior scripts.

### Phase 4 — Reorganize tests and harden CI

Status: implemented; final review in progress.

Deliverables:

- Classify tests into contract, integration, and unit suites.
- Keep `make check` as the aggregate command.
- Add supported Python-version and future packaging lanes without duplicating
  test logic.

Acceptance:

- CI preserves all existing checks.
- Each layer can run independently and the aggregate gate remains green.
- Path changes cannot silently bypass a contract test.

Rollback: retain the package extraction while restoring the previous test
entrypoint layout.

### Phase 5 — Retire temporary documentation stubs

Status: gated; not started.

Start only after one release/compatibility window.

`make phase5-preflight` validates the migration state without treating an open
compatibility window as a CI failure. Pointer removal requires
`scripts/check_compatibility_retirement.py --require-eligible` to pass first.

Acceptance:

- Repository-wide path search is clean.
- External/public links have been checked.
- Both agent startup smokes and full CI pass.
- Removal is documented in the changelog.
- Every gate has timestamped repository evidence no older than release-window
  completion.

Permanent native discovery files and command wrappers are not candidates for
this cleanup.

## Proposed implementation packets

| Packet | Scope | Dependencies |
| --- | --- | --- |
| RSR-001 | Path inventory, manifest, link/import checker | none |
| RSR-002 | `docs/` taxonomy and index | RSR-001 |
| RSR-003 | Policy migration and root adapters | RSR-002 |
| RSR-004 | Workflow/history migration | RSR-002 |
| RSR-005 | Receipt package extraction | RSR-001; after docs stabilize |
| RSR-006 | Orchestration/CLI extraction | RSR-005 |
| RSR-007 | Test/CI layering | RSR-005 and RSR-006 |
| RSR-008 | Compatibility audit and stub retirement | one release after RSR-003/004 |

RSR-003 and RSR-004 may run concurrently only with disjoint file ownership.
RSR-005 and RSR-006 should be sequential because they introduce the shared
package/bootstrap boundary.

## Future scaling triggers

These are recommended review triggers, not current facts or automatic
rearchitecture:

- Introduce a provider-adapter registry when a third coding runtime is added.
- Add CODEOWNERS when three or more contributors regularly edit shared policy
  or runtime boundaries concurrently.
- Add lightweight ADRs when architectural decisions repeatedly span more than
  one module or runtime.
- Split a module when it contains multiple independently changing contracts,
  not merely because it crosses an arbitrary line count.
- Generate project indexes/archives when manual project discovery becomes
  error-prone; keep each project's durable schema stable.
- Consider multi-repository separation only when release cadence, access
  control, or ownership is genuinely independent. Repository size alone is not
  enough.

## Explicit non-goals

- No microservices or multi-repository split.
- No replacement of Herdr with native subagents.
- No relocation of project memory, receipts, eval history, or metrics.
- No provider-specific duplicate implementations.
- No deployment or publication change without a real release artifact and
  separate approval.
- No unrelated permissions or tool-policy changes.

## Resolved implementation decisions

1. `docs/policy/` is the approved canonical policy location.
2. Root `AGENTS.md` and `CLAUDE.md` remain permanent runtime adapters.
3. `CONTRIBUTING.md` and `SECURITY.md` remain at root through the first
   migration.
4. Phases 0–4 were separately authorized and implemented behind their evidence
   gates. Phase 5 remains gated by the compatibility release window and final
   cross-runtime evidence.
