# Product definition

This document exists so that any coding agent working in this repository can
understand what Brichan is, what it is for, and which properties must survive
every change. Read it before proposing architecture, adding features, or
changing operating contracts.

It is descriptive of product intent. It is not runtime policy. The normative
runtime policy lives under `docs/policy/`; see
[Durable contracts](#7-durable-contracts) for the exact files.

Last verified: 2026-08-10 (package version 0.12.0).

## 1. What Brichan is

Brichan is an **AI Chief of Staff for coding agents** and, architecturally, a
**coordination and verification harness** above coding-agent runtimes. The user
states an outcome; Brichan holds the project context, converts the outcome into
bounded tasks, delegates those tasks to independent worker agent sessions,
verifies their evidence, and records durable project state outside of chat
history.

Codex and Claude Code are the execution runtimes. Herdr is the worker control
plane. Brichan supplies the operating contract, routing, durable memory, and
verification layer that coordinates them; it does not replace their execution
harnesses.

- Importable Python package and console commands: `brichan`, `brichan-*`.
- Distribution name on PyPI: `brichan`.
- Supported runtimes: Codex and Claude Code.
- Worker control plane: Herdr.
- Runtime dependencies: none beyond the Python standard library (3.10+).

## 2. The problem it solves

A single coding-agent session degrades on long-horizon work: context is
consumed by exploration, decisions disappear into chat scrollback, and claimed
completion is not distinguishable from verified completion.

Brichan's answer is a coordinator role with three hard commitments:

1. **Context economy** — the coordinator reads progressively and delegates work
   that would otherwise flood its own context.
2. **Durable memory** — stable facts, current state, tasks, decisions, and
   references live in Markdown files, not in the conversation.
3. **Evidence before completion** — a worker being `done` is not proof; the
   coordinator checks acceptance criteria against collected evidence.

## 3. Who it is for

The current audience is **one owner user (dogfood)**, with a planned expansion
to 3–5 trusted users. It is not built for a broad user population, and it is
not a commercial product today.

Practical consequence for agents: prefer a correct, verifiable narrow slice
over a broad, unverified one. Breadth is a later decision, not a default.

## 4. Explicit non-goals

Do not add these unless the user explicitly asks and authorizes them:

- Runtime-native delegation (Codex sub-agents, Claude Code background/native
  delegation) as a replacement for the Herdr worker lifecycle.
- Third-party Python runtime dependencies.
- Windows support, broad multi-platform or broad repository-shape support.
- Automatic mutation of a target repository's existing `AGENTS.md`,
  `CLAUDE.md`, `.codex/`, provider configuration, or existing skill files.
  (`brichan init` creates missing root `AGENTS.md`/`CLAUDE.md` pointers and
  adds its missing skill under `.agents/skills/herdr-orchestration/`, but
  never edits, overwrites, or re-manages existing files.)
- Automatic repair or migration of `.brichan/` state (schema v1 is deliberately
  migration-free).
- Publishing, deploying, remote-state changes, permission broadening, or secret
  access performed without explicit user authorization.
- Estimated metrics. Unavailable measurements are `null`, never guessed.

## 5. Mental model

```text
User      vision, priorities, trade-offs, final authority
  └── Brichan     context, planning, routing, delegation, verification, memory
        └── Workers   research, implementation, testing, debugging, review
```

Brichan is the delegated project coordinator. Brichan is **not** the human user and
must never present itself as such to a worker. Workers are independent
main-agent sessions with `brichan-` name prefixes, bounded task packets, and
required acceptance evidence.

Success is the user's intent surviving delegation with a verified result — not
the number of agents that were running.

## 6. How it works

### 6.1 Coordination loop

1. Convert the request into objective, scope, deliverables, acceptance
   criteria, constraints, and escalation conditions.
2. Decide whether to delegate — a decision that exists in checkout mode only.
   In checkout mode, delegation is discretionary
   ([`docs/policy/operating-principles.md`](docs/policy/operating-principles.md)
   §2): small, sequential, tightly coupled work is done directly. In
   installed-project mode delegation is mandatory and unconditional — every
   task that creates, edits, or deletes repository files runs the full `plan` →
   `implement` → independent `review` worker lifecycle, with no bounded-edit
   exception. That mandate is stated by the packaged policy resource
   [`operating-principles.md`](src/brichan/resources/dogfood_v1/policy/operating-principles.md),
   which is normative for installed projects.
3. Resolve a named worker route from settings
   ([`config/model-routing.json`](config/model-routing.json)).
4. Launch each worker through Herdr with a complete task packet.
5. Collect evidence (diff, tests, sources, reproduction, findings).
6. Check acceptance criteria; use an independent reviewer for material changes.
7. Update durable project memory.
8. Report in the fixed order defined by the operating principles, then close
   only Brichan-owned panes.

### 6.2 Two operating modes

**Checkout mode** — used for developing Brichan itself and for Claude Code.
Launch with `bin/brichan` or `bin/brichan --runtime claude`. Policy, project
memory, and configuration are repository-owned.

**Installed-project mode** — the current dogfood product shape. Brichan is
installed as a package and initializes an existing top-level Git repository:

```bash
/absolute/path/to/brichan/scripts/install-brichan
brichan init --project /absolute/path/to/repository          # dry-run, zero writes
brichan init --apply --project /absolute/path/to/repository  # creates .brichan/
brichan status  --project /absolute/path/to/repository
brichan doctor  --project /absolute/path/to/repository
brichan run     --project /absolute/path/to/repository -- <codex arguments>
```

In installed-project mode the delegated worker lifecycle is unconditional: every
repository-changing task runs `plan` → `implement` → independent `review`, and
the coordinator integrates only after that reviewer has verified the change.

Installed mode currently supports **Codex on POSIX with Python 3.10+**. It
writes a versioned `.brichan/` directory (manifest, managed policy, model
routing, Herdr skill resources, mutable project memory), missing root agent
pointers, and a missing `.agents/skills/herdr-orchestration/` export. It leaves
every pre-existing file untouched, including other skills. It launches
external `codex` directly and never executes target-owned `bin/brichan-*`
wrappers.

### 6.3 Safety posture of the launcher

The installed entrypoint rejects, before launch: native delegation, permission
bypasses, cwd/scope widening, profiles, remote execution, and arbitrary
provider configuration ahead of `--`. Text after `--` is literal prompt
content. State diagnostics refuse malformed, dangling, symlinked, inaccessible,
or incompatible `.brichan/` state instead of silently repairing it.

Any change that weakens one of these must be treated as a material change:
independent review is required.

## 7. Durable contracts

These are the load-bearing contracts. Changing one changes the product.

| Contract | Where | What it guarantees |
| --- | --- | --- |
| Identity and authority | [`docs/policy/identity.md`](docs/policy/identity.md) | What Brichan may do unattended vs. must ask about |
| Operating principles | [`docs/policy/operating-principles.md`](docs/policy/operating-principles.md) | Clarify → delegate → route → verify → record → report |
| Project memory | [`docs/policy/memory-policy.md`](docs/policy/memory-policy.md) | Progressive reads, selective writes, size targets |
| Model routing | [`config/model-routing.json`](config/model-routing.json), [`docs/guides/model-routing.md`](docs/guides/model-routing.md) | Settings-driven coordinator defaults and `plan`/`implement`/`review`/`scan` routes |
| Worker lifecycle | [`.agents/skills/herdr-orchestration/SKILL.md`](.agents/skills/herdr-orchestration/SKILL.md) | Task packets, `brichan-` naming, pane ownership, cleanup |
| Handoff receipts | [`scripts/validate_handoff_receipts.py`](scripts/validate_handoff_receipts.py) | Machine-validated evidence for accepted plans and multi-writer work |
| Techstack rules | [`docs/policy/techstacks.md`](docs/policy/techstacks.md) | Project-owned `techstacks/**`, pointer-only packets and receipts, planning reread |
| Independent review | [`docs/policy/reviewer.md`](docs/policy/reviewer.md) | Fresh session, preferably a different model family |
| Repository structure | [`config/repository-paths.json`](config/repository-paths.json) | Inventoried paths and valid local Markdown links |
| Workflow metrics | [`metrics/runs.jsonl`](metrics/runs.jsonl) | Observed measurements only; `null` when unavailable |

Project memory layout per project, in `projects/<slug>/`: `overview.md` (stable
facts), `current-state.md` (replaceable status), `tasks.md` (active work and
ownership), `decisions.md` (append-only rationale), `references.md` (pointers).
[`projects/index.md`](projects/index.md) is the entry point.

## 8. Repository map

```text
AGENTS.md, CLAUDE.md   agent discovery; point at docs/policy/
PRODUCT.md             this file: product intent and guardrails
docs/policy/           normative runtime policy (canonical)
docs/guides/           model routing, installed Codex dogfood
docs/architecture/     module boundaries
src/brichan/cli/         runtime dispatch and Codex/Claude adapters
src/brichan/orchestration/  Herdr layout, launch, model routing
src/brichan/contracts/   receipt schema, parser, discovery, validation
src/brichan/techstacks/  read-only techstack resolve, publish, verify
src/brichan/resources/   packaged dogfood_v1 policy, skills, memory templates
bin/, scripts/         stable wrappers; bootstrap only, delegate to src/
config/                repository paths, model routing, retirement gates
projects/, evals/, metrics/   durable data and evidence; never imported by src/
tests/unit|contract|integration   the three verification layers
```

Boundary rule: importable modules must not depend on `projects/`, `evals/`, or
`metrics/`. `bin/` and `scripts/` contain bootstrap logic only. See
[`docs/architecture/repository-layout.md`](docs/architecture/repository-layout.md).

## 9. Working in this repository

```bash
make check          # complete local validation; required before sharing a change
make test-unit      # importable module behavior
make test-contract  # repository and policy contracts
make test-integration  # wrappers and provider command compatibility
make path-check     # path inventory and local Markdown links
```

Adding a root-level file requires an entry in
[`config/repository-paths.json`](config/repository-paths.json), otherwise
`make path-check` fails. Behavior changes require regression tests and
documentation updates in the same change. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## 10. Current status and direction

Verified as of 2026-08-10:

Latest published version: 0.12.0

- The installed Codex vertical slice passed disposable-wheel verification and
  independent review.
- The `brichan` distribution is published on PyPI and releases are automated:
  pushing a `vX.Y.Z` tag triggers `.github/workflows/publish.yml`, which
  builds, validates, and publishes through PyPI Trusted Publishing. The first
  fully automated publish was `v0.9.0` on 2026-08-03.
- Dogfood evidence is **partial**. The v0.11 change was produced by live worker
  orchestration through Herdr in this repository — plan, implement, and review
  workers, with the coordinator never editing repository files. Dogfood in an
  external owner repository is still an open gate, so this is partial evidence
  rather than the finished one.

Next, in order:

1. One-owner dogfood in an external repository with real Codex and real Herdr.
2. Record friction and defects; only then consider 3–5 trusted users.

Live status lives in
[`projects/brida-installable-tool/current-state.md`](projects/brida-installable-tool/current-state.md),
not here.

## 11. Drift checklist

Before proposing or merging a change, confirm all of the following:

- [ ] It does not replace the Herdr worker lifecycle with native delegation.
- [ ] It does not add a runtime dependency.
- [ ] It does not widen permissions, scope, or provider configuration
      implicitly.
- [ ] Outside `.brichan/`, it only creates missing root agent pointers and the
      missing `.agents/skills/herdr-orchestration/` export; it does not mutate
      pre-existing user-owned files or skills.
- [ ] It does not silently repair or migrate state.
- [ ] It leaves `techstacks/**` project-owned: no create, edit, remove, repair,
      or inventory management, and no rule bodies in a packet, receipt, plan,
      or memory entry.
- [ ] It adds no production packet parser or acceptance helper: packet
      completeness and receipt placement stay coordinator policy.
- [ ] It does not report completion without evidence, or record unverified
      claims as durable memory.
- [ ] It keeps policy canonical in one place (no duplicated active defaults in
      runtime instruction files).
- [ ] It updates documentation and tests, and `make check` passes.
- [ ] Material changes to orchestration, permissions, security, routing, or
      public contracts received an independent review.

If a request conflicts with this document, do not silently follow either one.
State the conflict, propose the smallest change that resolves it, and let the
user decide.

## Canonical sources

- [`AGENTS.md`](AGENTS.md) — Codex runtime instructions
- [`CLAUDE.md`](CLAUDE.md) — Claude Code runtime instructions
- [`docs/index.md`](docs/index.md) — documentation index
- [`README.md`](README.md) — public entry point
- [`CHANGELOG.md`](CHANGELOG.md) — released behavior by version
- [`SECURITY.md`](SECURITY.md) — security policy

## Glossary

- **Coordinator** — the Brichan session that plans, routes, verifies, and records.
- **Worker** — an independent main-agent session created through Herdr, named
  `brichan-*`, given one bounded task packet.
- **Task packet** — the complete assignment: objective, scope and exclusions,
  deliverables, acceptance criteria, permissions, escalation conditions, route.
- **Receipt** — a validated Markdown record of a handoff, mandatory for
  accepted-plan and multi-writer tasks.
- **Route** — a named settings entry (`plan`, `implement`, `review`, `scan`)
  resolving to a runtime, model, and reasoning effort.
- **Checkout mode / installed-project mode** — the two ways Brichan runs; see §6.2.
- **Dogfood** — the current single-owner validation stage that gates expansion.
