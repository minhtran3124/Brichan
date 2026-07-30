# Installable-tool assessment

Status: reviewed baseline, then narrowed by accepted user dogfood decision
Last verified: 2026-07-29

## Outcome

Recommendation: **go directly to a narrow one-user dogfood prototype, then
expand only to 3–5 trusted users if it works**.

Brida should become an installed CLI that binds to an explicitly initialized
target repository. It should not copy or vendor the full Brida development
repository into every project.

The technical direction is feasible because the importable core, console
entrypoints, routing guards, receipt contracts, and test layers already exist.
The product is not ready for arbitrary-repository use because runtime startup,
configuration, policy discovery, and durable state still assume a Brida
checkout.

The owner is the first target user, so a separate market-discovery gate is not
required. Build only enough code to test root separation, safe policy/skill
loading, lifecycle ownership, and a real owner workflow. Commercialization,
broad adoption, and support for many environments are outside the current
decision.

## Evidence summary

- `pyproject.toml` declares Python 3.10+, no runtime Python dependencies, and
  five console entrypoints.
- Public setup still requires cloning Brida and starting `bin/brida`.
- `repository_root()` currently locates `AGENTS.md` plus `bin/`, or uses
  `BRIDA_ROOT`; the runtime dispatcher then executes a repository-local
  provider wrapper.
- Model routing defaults to `<Brida root>/config/model-routing.json`.
- The complete local suite passed on 2026-07-29: 61 unit, 37 contract, and 23
  integration tests, plus metrics, 33 receipt, repository-path, compatibility,
  package-import, and shell checks.
- Six reverified official-source comparisons found a recurring split between an
  installed executable and repository-local instructions or initialized
  workflow assets. This is an architecture precedent; demand evidence is not a
  requirement for the current dogfood scope.

## Comparable approaches

| Approach | What it validates | Limitation relative to Brida |
|---|---|---|
| Codex `AGENTS.md` | Hierarchical repository instructions are a native compatibility surface | Instructions are context, not Brida's durable task/evidence workflow |
| Claude Code `/init` and `CLAUDE.md` | Reviewable project initialization and scoped project memory | Runtime-specific and instructions are not hard enforcement |
| GitHub Copilot CLI `init` | A globally installed coding tool can initialize an existing repository | Focused on Copilot customization, not external worker ownership |
| Cline rules | Modular, path-scoped repository rules are familiar | Tool-specific format and prompt-level guidance |
| Aider conventions | A minimal, inspectable convention file can be enough for light usage | No initialization or coordination lifecycle |
| GitHub Spec Kit | CLI plus project init, dry-run upgrade, and owned workflow assets are workable | Spec-driven workflow rather than general project coordination |

For dogfooding, Brida's relevant value is the combined workflow: independent
worker ownership through Herdr, bounded task packets, evidence/receipt checks,
cleanup, and durable project state across Codex and Claude Code. Competitive
defensibility, uniqueness, and demand are not current acceptance criteria.

## Architecture options

| Option | Benefits | Costs and risks | Verdict |
|---|---|---|---|
| Keep clone-only | Lowest maintenance and migration risk | Poor adoption into existing repositories; split working context | Retain as compatibility mode |
| Installed CLI + project init | Small repo footprint, normal package lifecycle, explicit binding and ownership | Requires root/config/state separation and migrations | Preferred |
| Vendor Brida into each repository | Self-contained and easy to inspect | Large footprint, duplicated code, difficult updates and conflicts | Reject for dogfood prototype |
| Sidecar Brida checkout | Avoids target-repo files | Weak portability and policy discovery; two-root mental model remains | Optional advanced mode only |
| Project-local virtual environment only | Strong per-repo reproducibility | More setup and duplicated environments | Supported install mode, not sole architecture |

## Preferred product contract

Support both user-level installation (`pipx`/`uv tool` or equivalent) and a
project-local virtual environment. The package manager owns CLI upgrades;
Brida owns only project schema migration.

Proposed commands:

```text
brida init [--path REPO] [--dry-run] [--apply]
brida status [--path REPO]
brida doctor [--path REPO]
brida integrate <codex|claude> [--dry-run] [--apply]
brida migrate [--path REPO] [--dry-run] [--apply]
brida uninstall [--path REPO] [--dry-run] [--apply]
brida --version
```

Preferred project namespace:

```text
.brida/
  manifest.json
  config/model-routing.json
  projects/
  policy/                  # optional, only for reviewed native adapters
```

- The installed package owns code, immutable default templates, schemas, and
  migration logic.
- The target repository owns `.brida/` configuration, project memory, every
  generated provider adapter, and any optional policy copy required by an
  explicitly selected native-adapter model.
- `manifest.json` records schema version, template IDs, generated paths, and
  content hashes.
- `init` is idempotent and never overwrites an existing file.
- Provider integration is explicit. If `AGENTS.md` or `CLAUDE.md` is absent,
  Brida may propose a new thin adapter; if either exists, Brida presents a
  bounded patch and requires explicit apply authorization.
- Package upgrade and project migration are separate. A newer CLI may report a
  required migration but must not mutate project state implicitly.
- Uninstall removes only unchanged, manifest-recorded Brida-created files.
  User-edited or shared files remain with manual cleanup guidance.

## Provider policy and skill-loading options

`.brida/policy/` is not itself a native Codex or Claude Code discovery
location. A prototype must test the following options before selecting the
product default:

| Model | Benefits | Limitations and precedence | Prototype disposition |
|---|---|---|---|
| Brida-launch-time policy injection | Package owns the canonical bootstrap; no shared instruction file must be edited | Provider-specific flags/config; direct `codex` or `claude` launches are not Brida sessions; package policy can still conflict with higher-priority provider rules | Preferred first experiment; verify Codex `developer_instructions`/skill-path configuration and Claude `--append-system-prompt-file`/`--plugin-dir` behavior |
| Reviewed native adapters | Works with provider-native discovery and can support direct launches | Requires target-repo files; nested/closer instructions may override or conflict; prompt instructions cannot enforce non-negotiable policy | Optional explicit `brida integrate`; never claim guaranteed precedence |
| Provider plugin/skill distribution | Natural way to expose reusable workflow instructions and commands | Runtime-specific packaging, discovery, versioning, and uninstall semantics; not yet covered by the wheel | Prototype alongside injection for the Herdr skill |
| Direct provider launch without Brida | No extra wrapper UX | Cannot guarantee Brida identity, policy, skill, routing, or audit lifecycle | Unsupported as a Brida session unless the repository has an explicitly accepted native adapter |

The safe prototype default is therefore a session launched through `brida`.
Native adapters remain an explicit compatibility option. Neither model may
treat prompt instructions as mechanical permission enforcement.

## Herdr skill lifecycle and path migration

The `$herdr-orchestration` skill is a required runtime asset, not development
documentation. Today it lives under `.agents/skills/`, points to checkout-
relative policy/config references, and assumes receipts under `projects/`.

For an installed prototype:

- Brida owns the canonical skill, task/receipt templates, schemas, and
  migration logic. They must ship as versioned package resources or a
  version-pinned provider plugin; this choice must be proven for both runtimes.
- `brida` must expose the compatible skill to its launched coordinator session.
  An arbitrary direct provider launch is unsupported unless a native adapter
  separately establishes the same contract.
- The target repository owns generated adapters and `.brida/` state. Its
  manifest records the Brida version, project schema, skill contract version,
  generated paths, and hashes.
- Project migration updates state/config and generated adapters only after
  preview. Package/plugin upgrade supplies runtime assets separately.
- Uninstall removes only unchanged project-owned generated assets. Removing the
  installed CLI/plugin is delegated to its package manager.

Affected path contracts:

| Current checkout path | Prototype ownership/location |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Package-owned launch bootstrap; optional reviewed target-repo adapters |
| `docs/policy/` | Versioned package policy resources; optional project-owned copies only when an adapter requires them |
| `.agents/skills/herdr-orchestration/` | Versioned package resource or provider plugin exposed by `brida` |
| `config/model-routing.json` | `.brida/config/model-routing.json` with package defaults |
| `projects/_template/` | Versioned package templates |
| `projects/<slug>/` | `.brida/projects/<slug>/` |
| `projects/<slug>/handoffs/` | `.brida/projects/<slug>/handoffs/` |
| Receipt CLI default `projects/` | Explicit initialized project/state root; no process-cwd default |
| `.codex/config.toml` | Optional reviewed provider integration, never an implicit write |
| `metrics/`, `evals/`, compatibility-retirement evidence | Remain Brida development-repository assets; excluded from the dogfood repo footprint |

The prototype must inventory and test every consumer used by the owner workflow
before adopting `.brida/` as a stable contract. Consumers outside the dogfood
path may remain unsupported.

## Required technical work

1. Separate **tool root**, **target project root**, and **mutable state root**.
2. Before exposing installed arbitrary-repository use, replace repository-local
   wrapper selection/execution with direct package entrypoints.
3. Bundle immutable defaults/templates with explicit package-resource loading.
4. Prove package-owned policy injection and Herdr skill discovery for both
   providers, including precedence/conflict behavior.
5. Add an initialized-project marker and explicit root/config resolution.
6. Implement dry-run-first init, conflict detection, ownership hashes,
   migrations, rollback, and safe uninstall.
7. Make policy, skill, receipt, config, and memory paths explicit while
   preserving clone-mode
   compatibility.
8. Add `doctor` preflight for Python, provider CLIs, Herdr, versions, auth where
   required, repository state, and config/schema compatibility.
9. Add installed-wheel tests in disposable repositories for the selected
   dogfood runtime path; expand provider coverage only when the owner workflow
   requires it.

## Current and future risks

| Timing | Risk | Required treatment |
|---|---|---|
| Current, but exposed mainly by using the installed entrypoint in an arbitrary/untrusted repository | `repository_root()` can select an ancestor with `AGENTS.md` and `bin/`, then the package entrypoint executes that repository's `bin/brida-<runtime>` | Treat as a present executable-selection trust-boundary hazard. Direct package dispatch is a prerequisite for any arbitrary-repository prototype; add a negative regression test |
| Current | Repository instructions are behavioral context and can conflict or contain hostile guidance | Keep mechanical permission/routing guards package-owned; document precedence and never call prompt policy enforcement |
| Future lifecycle | Init/migrate/uninstall could overwrite, escape the target, follow unsafe links, or race another writer | Manifest ownership, target-scoped containment, atomic writes, immediate hash revalidation, preview, and rollback |
| Future distribution | CLI, provider plugin/skill, project schema, and external CLIs can version-skew | Version manifest, compatibility matrix, `doctor`, and fail-closed unsupported versions |
| Future state | Committed project memory may expose sensitive context | Human decision on committed/ignored/local-only state plus retention guidance |

## Prototype guardrails

- No implicit overwrite or merge of existing instructions, provider config,
  CI, or project state.
- For every Brida-managed destination and its parent chain, require canonical
  containment and reject traversal, unsafe symlinks, non-regular targets,
  ambiguous ownership, and changes since preview. Unrelated repository
  symlinks do not block the operation.
- Dry-run preview before every mutating lifecycle operation.
- Atomic writes; update the manifest last; retain recoverable rollback evidence.
- Fail closed on unsupported schema or external-tool version mismatch.
- Never treat repository instructions as a security boundary.
- No secrets in generated files, receipts, logs, prompts, or environment
  snapshots.
- Dirty-tree state outside the approved write set produces diagnostics, not an
  automatic failure. Block only conflicts, staged/modified managed paths,
  ambiguous rollback state, or operations whose documented safety model
  requires an unchanged snapshot.
- Dogfood support: the owner's POSIX environment, Python 3.10+, an explicit Git
  repository root, at least
  one supported authenticated provider, and compatible Herdr for orchestration.
- Windows, ambiguous nested repositories, automatic monorepo inference, shared
  concurrent mutation, and headless orchestration should remain unsupported
  unless a concrete dogfood repository requires them.

## Advantages

- Brida runs where the user's actual project context and Git history live.
- Setup becomes repeatable without duplicating the Brida codebase.
- The existing modular Python core and tests can be evolved incrementally.
- Project-local state is reviewable, portable, and versionable.
- Cross-runtime governance remains a meaningful distinction from native
  instruction files alone.

## Disadvantages

- Installability creates a long-lived schema, migration, ownership, and
  compatibility contract.
- Herdr and rapidly changing provider CLIs increase support burden.
- Existing instruction files and monorepo layouts make safe integration
  non-trivial.
- Brida adds files, process, token use, and latency; it is a poor fit for small
  one-off coding tasks.
- Current evidence does not establish lower cost or faster completion; those
  are not required claims for the initial dogfood tool.

## Sequenced dogfood stages

### Stage 1 — Disposable technical prototype

1. Build/install locally outside the Brida checkout; publishing to a package
   registry is unnecessary.
2. Initialize a small fixture set covering only the owner's supported
   environment and selected runtime path.
3. Prove direct package dispatch cannot execute target-repository wrappers.
4. Prove package-owned policy injection and Herdr skill discovery for the
   selected runtime; add the second runtime only when needed by the owner.
5. `init --dry-run` performs zero writes; apply writes only the approved list;
   a second apply is a no-op.
6. Existing instruction/provider files remain byte-identical unless a specific
   integration patch is approved.
7. Missing/incompatible Herdr fails before pane mutation.
8. Migration failure, rollback, and uninstall preserve user edits.
9. Unsafe managed-target symlinks, path escape, root ambiguity, concurrent
   target modification, and version skew fail closed; unrelated dirty paths
   produce diagnostics.
10. Clone mode and applicable existing checks remain green.

### Stage 2 — One-user owner dogfood

Use Brida on at least one real owner repository and one multi-session task. The
dogfood succeeds when:

- Installation and initialization do not require a separate Brida checkout.
- Brida launches in the intended target root with the required policy and skill.
- Project memory survives sessions and remains understandable.
- Worker evidence and cleanup contracts still hold.
- Update/migration/uninstall do not damage user-owned files.
- Repeated use is materially less awkward than clone-only Brida.

### Stage 3 — Trusted 3–5-user dogfood

Only after the owner workflow is stable, invite 3–5 trusted users with similar
environments and repository shapes. Validate that they can install, initialize,
run, and remove Brida from concise documentation. Their failures define the
next compatibility work; they do not create an obligation to support unrelated
platforms or edge cases.

There is no commercialization or broad-market gate in the current plan.
