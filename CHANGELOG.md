# Changelog

All notable changes to Brichan are documented here.

The format follows Keep a Changelog principles. The project does not yet claim
Semantic Versioning compatibility because its runtime contract is pre-1.0.

## [0.13.0] - 2026-08-28

### Added

- `brichan techstacks resolve` and `brichan techstacks verify`
  (`src/brichan/techstacks/`): a read-only, standard-library resolver for a
  target project's `techstacks/**` rules. A project opts in with a regular,
  non-symlink `techstacks/README.md` at its exact validated top-level Git root;
  every README is map-only and normative component rules live in non-README
  leaves. Resolution never creates, edits, removes, repairs, or
  inventory-manages `techstacks/**`. `resolve` prints one canonical Resolution;
  with `--snapshot-directory` it publishes one to three immutable
  `<attempt-id>-<snapshot-sha256>.snapshot.json` observation artifacts into the
  authorized directory alone — `projects/<project-slug>/handoffs/<TASK-ID>/snapshots`
  in a source checkout, `.brichan/project-memory/techstack-snapshots/<TASK-ID>`
  in an installed project — verifying each and retrying at most three drifted
  observations without overwriting, renaming, truncating, or deleting anything.
  `verify` exits `0` on `match` and `5` on drift or blocked.
- Canonical techstack policy at `docs/policy/techstacks.md` and its packaged
  counterpart `policy/techstacks.md`, plus a packaged
  `skills/herdr-orchestration/references/handoff-receipt.md`. The policy freezes
  the sixteen exact packet labels, the exact not-applicable form, the
  whole-packet 196,608-byte `TASK_PACKET_BYTE_LIMIT` cap, the receipt Scope and
  Verification pointer placement, and the planning-reread gate. Packet
  acceptance is coordinator policy: no production packet parser or acceptance
  helper exists, and none is added. A project root or Snapshot artifact path
  containing a pipe, CR, or LF is stated as out of contract for receipt
  embedding, because the receipt parser splits every table row on the pipe with
  no escape step.
- The doctor report gains an `agent_skill_export` section and moves to report
  schema `2`. The installed-state schema stays `1`. Because the two new
  immutable resources join the managed footprint, an already initialized
  project becomes incompatible with this package and requires deliberate backup
  and reinitialization; no migration runs and no state is silently repaired.

- `brichan-herdr-agent-observe` (`bin/brichan-herdr-agent-observe`,
  `src/brichan/orchestration/monitor.py`): a dependency-free, read-only Herdr
  preflight and worker-observation surface. Monitoring was previously prose in
  the skill with nothing typed or tested; the three authorities are now
  structurally separated. Herdr scheduling state is exposed as a scheduling
  signal only — the observation type has no completion, success, or done field,
  so `idle` or `done` can never be reported as acceptance evidence. Terminal
  text carries conservative completeness metadata and a truncation risk of
  `none`, `possible`, or `confirmed`, dominated by Herdr's native `truncated`
  flag; on Herdr `0.7.3` no capability proves history completeness, so a healthy
  read is `possible` and `none` is unreachable by design. A read is treated as
  successful only when the whole schema is present — string text, a boolean
  native `truncated`, and a source that canonically matches the one requested
  (`recent-unwrapped` and `recent_unwrapped` are the same source); any missing,
  mistyped, or mismatched field is a partial read and forces `confirmed`, so a
  truncated payload can never report false completeness. Malformed envelopes are
  owned failures rather than tracebacks: a syntactically valid payload whose
  `result` container is not an object is rejected before it is dereferenced, so
  a bad read stays a collected exit-`0` observation and a bad `agent get` stays
  an exit-`1` diagnostic. Acceptance evidence
  falls back to declared durable files, read through a descriptor-relative
  `O_DIRECTORY | O_NOFOLLOW` walk with metadata taken from the final held
  descriptor. Preflight parses `herdr status --json` through a strict JSON
  adapter and the plain-text `herdr integration status` rows through a separate
  parser anchored on the full frozen `0.7.3` row grammar, including its required
  trailing path group; a row is either fully understood — in which case only a
  bounded runtime identifier and status token are kept — or rejected as
  `malformed-row` with no remainder retained, so no home or configuration path
  can reach output. Each command is bound to its own adapter and validated
  against a complete argv grammar that rejects unknown or duplicated options,
  wrong arity, and tokens smuggled behind an allowed prefix; every
  `herdr agent wait` occurrence is capped at 30000 ms. A version or protocol outside the verified
  set (`0.7.3` / protocol `16`) is reported as `unverified` and never triggers
  an update or install. Both subcommands emit one deterministic JSON document
  and exit `0` report collected, `1` report impossible, `2` invalid invocation
  or rejected path.

### Changed

- The checkout and packaged `herdr-orchestration` skills now state the same
  monitoring safeguards, enforced by a new parity contract test so drift fails
  `make check`. The packaged skill previously omitted the
  done/idle-is-not-proof invariant, bounded waits of at most 30 seconds, the
  truncation and evidence-file fallback, the no-automatic-input rule, the
  paste-swallowed-Enter recovery guidance, and the three-observation
  no-progress rule with one bounded replacement. Because packaged skill files
  are hash-managed immutable resources, an upgraded package makes existing
  initialized `.brichan/` states report `incompatible`; the documented recovery
  is to back up `project-memory/`, delete `.brichan/`, and re-run
  `brichan init --apply`. No repair or migration code was added.

- `brichan init` now exports `.agents/skills/herdr-orchestration/` by default;
  the `--init-agents` flag is no longer needed or accepted. If `.agents/` or
  `.agents/skills/` already exists, initialization preserves its contents and
  adds only the missing Brichan skill layout. An existing
  `herdr-orchestration` export remains unmanaged and is never overwritten.

- Risk-based testing discipline in both operating policies
  (`docs/policy/operating-principles.md`,
  `src/brichan/resources/dogfood_v1/policy/operating-principles.md`), the
  reviewer finding list (`docs/policy/reviewer.md`), and the contributor
  checklist (`CONTRIBUTING.md`): code verification now requires tests of
  application-owned observable behavior with a distinct justification per
  test — the owned behavior or observed failure it covers — rejects
  duplicate, speculative, and implementation-coupled coverage, orders runs
  focused-to-broad and sequential by default, treats E2E, race, load, and
  stress tests as intentional choices serving a specific identified risk
  rather than defaults, makes lint/typecheck
  conditional on project configuration, requires failure diagnosis before
  code or tests change, and forbids weakening meaningful assertions to pass
  a gate. Focused runs remain implementation feedback; `make check` remains
  this repository's completion gate. Both worker task-packet templates
  (`.agents/skills/herdr-orchestration/references/task-packet.md`,
  `src/brichan/resources/dogfood_v1/skills/herdr-orchestration/references/task-packet.md`)
  now open with a mandatory pointer to the applicable operating policy, so
  delegated workers receive the discipline at dispatch time. Because
  packaged policy and skill resources are hash-managed, changing the
  packaged operating principles and the packaged task-packet reference makes
  existing initialized `.brichan/` state report `incompatible` after
  upgrading; the documented recovery is deliberate reinitialization, not
  migration code.

### Upgrade note

- Two new immutable packaged resources join the managed footprint and the
  packaged operating principles, task-packet reference, and
  `herdr-orchestration` skill all changed. Because those resources are
  hash-managed, existing `.brichan/` state reports `incompatible` after
  upgrading (schema v1 is migration-free by design). Back up
  `project-memory/`, delete `.brichan/`, and re-run `brichan init --apply`.
  No migration runs and no state is silently repaired.
- `brichan init --init-agents` is no longer accepted; the export it gated is
  now the default. Remove the flag from any scripted initialization.

## [0.12.0] - 2026-08-10

### Changed

- The shipped operating principles no longer allow the `plan` worker to be
  skipped. Previously a coordinator could declare a change "a single bounded
  edit with obvious acceptance criteria" and go straight to `implement` —
  which is how the lifecycle was bypassed in practice, since every change
  looks bounded from the inside. All three phases are now mandatory
  regardless of the size of the change, and the coordinator integrates only
  after the independent `review` worker has verified it.
- The PyPI long description embeds the project hero image again. The image
  had been stripped since 0.5.0 because the readme builder treated the
  repository as private and could not emit a resolvable raw URL; the
  repository is public now, so `config/pypi-readme.json` declares it and the
  generated `README_PYPI.md` carries the image through to the rendered page.
- The README was rewritten for a public audience: what Brichan is and the
  problem it solves lead, ahead of the internal dogfooding detail.

### Added

- `make memory-check` (`scripts/check_project_memory.py`) validates durable
  project-memory consistency — project index and overview agreement, handoff
  receipts, and task/state cross-references — and is part of `make check`.

### Upgrade note

- Policy resources are hash-managed, so existing `.brichan/` state reports
  `incompatible` after upgrading (schema v1 is migration-free by design).
  Back up `project-memory/`, delete `.brichan/`, and re-run
  `brichan init --apply` to adopt the tightened policy.

## [0.11.0] - 2026-08-03

### Changed

- The installed-project policy now mandates the delegated worker lifecycle.
  Previously the coordinator was allowed to "work directly when a task is
  small", and in practice it implemented, tested, and installed dependencies
  inline without ever spawning a worker. Under the new policy, any task that
  creates, edits, or deletes repository files runs through `plan` →
  `implement` → `review` workers on the named routes; the coordinator writes
  only under `.brichan/project-memory/`; and a worker that cannot be started
  is reported as a blocker instead of worked around inline. Verified
  end-to-end: a real feature request produced plan, implement, review, and
  remediation workers through Herdr, with the coordinator never editing
  repository files itself.

### Upgrade note

- Because policy resources are hash-managed, existing `.brichan/` state
  reports `incompatible` after upgrading (schema v1 is migration-free by
  design). Back up `project-memory/`, delete `.brichan/`, and re-run
  `brichan init --apply` to adopt the new policy.

## [0.10.0] - 2026-08-03

### Added

- `brichan init --init-agents` exports the herdr-orchestration skill to
  `.agents/skills/herdr-orchestration/` in the target repository, so a
  `codex` session started directly there (without `brichan run`, which
  injects the skill from `.brichan/skills/` explicitly) still discovers it.
  The export is opt-in and follows the same contract as the root agent
  entry pointers: created only when the directory is absent, unmanaged
  afterwards, never edited or overwritten, and topped up by re-running
  `init --init-agents` against healthy state.

### Changed

- The PyPI long description was rewritten for the private-repository
  reality: the install-from-source and task dossier sections are gone,
  leaving package description, requirements, installation, basic commands,
  usage, and feature notes.

## [0.9.0] - 2026-08-03

### Added

- `brichan init` now creates root `AGENTS.md` and `CLAUDE.md` files in the
  target repository when they are absent, pointing agent runtimes at
  `.brichan/policy/bootstrap.md`. Existing files — including symlinks — are
  never edited or overwritten; created files belong to the repository from
  then on and are excluded from the manifest and health checks. Re-running
  `init` against healthy state creates any missing pointer, dry-run lists
  the new `create AGENTS.md` / `create CLAUDE.md` lines, and the interactive
  init tree shows and counts them.

### Changed

- The product non-goal forbidding mutation of a target repository's
  `AGENTS.md`/`CLAUDE.md` was narrowed to existing files: creating missing
  root pointers is now in scope, editing or overwriting present ones remains
  out of scope.

## [0.8.0] - 2026-08-03

### Added

- The task dossier workflow: a structured set of handoff documents (brief,
  requirements, design, plan, code review, receipt, and more) with scaffolding,
  generation, summarization, and validation scripts, plus contract tests that
  keep the documents consistent with the repository's task lifecycle. See
  `docs/workflows/task-dossier.md`.
- `brichan doctor --json` emits the diagnostic report as machine-readable
  JSON instead of the operator-facing text summary.

### Changed

- `brichan doctor`'s text output was redesigned around a compact callout plus
  route and dependency summaries, making route resolution and missing
  dependencies easier to scan than the prior flat line list.

## [0.7.0] - 2026-07-30

### Changed

- Renamed the importable Python package, console commands, `.brida/` state
  directory, and `BRIDA_*` environment variables to `brichan`, `brichan-*`,
  `.brichan/`, and `BRICHAN_*` respectively, matching the `brichan` PyPI
  distribution name. Entries below this point describe releases made under
  the prior `brida` name.

### Verification

- Full local `make check` passes (262 tests across the metrics, unit,
  contract, and integration suites).
- `python -m build` produces a clean sdist and wheel; `twine check` passes on
  both, and the wheel installs into a disposable virtual environment where
  `brichan --version` reports the released version.

## [0.6.0] - 2026-07-30

### Changed

- `brida init` draws its footprint as a tree above a one-line description of
  what `.brida/` holds and a summary ending in the next command. The rendering
  applies only when stdout is a terminal, respects `NO_COLOR` and
  `TERM=dumb`, and falls back to ASCII connectors when the terminal cannot
  encode box drawing. Redirected output still emits the unchanged
  `dry-run: zero writes` and `create .brida/<path>` lines that scripts parse.
- `brida --help` and `brida --version` report Brida from a source checkout
  instead of forwarding to the runtime, which a checkout has no project state
  to launch into. Inside a healthy initialized project they still forward to
  `codex` as documented, and naming a runtime still forwards, so
  `brida --runtime codex --help` and `bin/brida-codex --help` are unaffected.
- The PyPI project page is now generated from a dedicated package README
  rather than `README.md`, which is written for readers already standing in
  the repository. Repository-relative images and links no longer reach the
  project page, where they resolved against pypi.org and rendered broken.

### Added

- `brida status --help` and `brida doctor --help` describe what the commands
  do. `status` names the four states it reports and the exit code each maps
  to; `doctor` names what it probes. Both state that they write nothing.
- `scripts/release_pypi.py` performs the release checklist in order and
  refuses to continue when the release is inconsistent. It previews by
  default, and reads `PYPI_TOKEN` from the environment or `.env`.

### Fixed

- A missing provider binary is reported as an owned, actionable error instead
  of a `FileNotFoundError` traceback. This affected `brida-codex`,
  `brida-claude`, `brida run`, and the checkout dispatcher on any machine
  without `codex` or `claude` installed, and had failed both packaging CI
  jobs on every push.

### Verification

- Full local `make check` passes (259 tests).
- CI passes on all four jobs, including both packaging matrices.
- `python -m build` produces a clean sdist and wheel; `twine check` passes on
  both, and the wheel installs and reports its version in a disposable
  environment.

## [0.5.0] - 2026-07-29

### Changed

- Set the distribution name to `brichan` in preparation for a future PyPI
  release (not yet published); the importable package stays `brida` and all
  `brida-*` console commands are unchanged.
- Added `wheel` to build-system requirements and PyPI classifiers/keywords so
  Python 3.10+ isolated and non-isolated wheel builds succeed.

### Added

- CI now builds and validates both sdist and wheel artifacts, installs them
  in a clean environment, runs `twine check`, and smoke-tests
  every documented installed command that does not require an external
  provider.
- A tag-gated Trusted Publishing GitHub Actions workflow scaffold using OIDC
  and a `pypi` environment. It cannot publish until trusted publishers are
  configured on PyPI; see the release checklist.
- `brida`, `brida-codex`, and `brida-claude` now provide `--help` and
  `--version` outside initialized projects or a source checkout; unsupported
  invocations there return an owned error rather than a Python traceback.

### Verification

- Full local `make check` passes.
- `python -m build` produces a clean sdist and wheel; the wheel installs and
  exposes all `brida-*` console commands in a disposable environment.

## [0.4.0] - 2026-07-29

### Added

- Repository-owned schema-v1 model routing for coordinator defaults and named
  `plan`, `implement`, `review`, and `scan` Herdr worker routes.
- Dependency-free routing validation, provider-native command construction,
  one-off route overrides, and no-mutation dry-run JSON resolution.

### Changed

- Coordinator adapters and Herdr worker launches now consume the routing
  manifest while preserving guarded legacy explicit worker commands.
- Native delegation disabling, forbidden effort, arbitrary setting, and
  permission-bypass checks are enforced in code before Herdr mutation.
- Simplified the README around getting started, how Brida works, and
  development; model-routing detail now lives in a dedicated guide.

### Verification

- Full local `make check` passes.
- GitHub Actions CI passes on commit `6a55c97d73945a3f09ca2e52b3613bcb52e0e3a7`
  for Python 3.10, Python 3.13, and source-package builds.
- Independent review passed acceptance criteria AC1-AC8 with no blocking
  findings.

## [0.3.1] - 2026-07-29

### Fixed

- Keep the importable `brida.__version__` value aligned with release metadata.

### Removed

- Retired the six temporary root policy pointers after the `v0.3.0`
  compatibility release; canonical policy and history remain under `docs/`.

## [0.3.0] - 2026-07-28

### Added

- Machine-readable repository path inventory, local Markdown-link validation,
  and structural characterization tests.
- Canonical `docs/policy/` and `docs/history/` taxonomy with one-release root
  compatibility pointers and permanent root agent-discovery adapters.
- Importable `src/brida/` core for receipt contracts, Herdr orchestration, and
  Codex/Claude CLI adapters while preserving existing command paths.
- Independent unit, contract, and integration test layers plus a CI wheel-build
  lane.
- Claude workers launched through Herdr now default to Claude Code's `auto`
  permission mode, while explicit per-worker modes remain supported.
- Versioned Markdown handoff/receipt template and repository contract coverage.
- Optional accepted-plan and receipt linkage in task packets with contract
  coverage.
- Mandatory receipts for accepted-plan and multi-writer handoffs, exclusive
  writer path ownership, isolated worktrees, and concurrent-writer contract
  coverage.
- Canonical project handoff receipts, a dependency-free receipt completeness
  gate, line-wrap-tolerant structural policy checks, and bounded stale-worker
  replacement rules.
- Structural coverage for recovery guarantees, a controlled one-replacement
  pilot, and a fixed-rubric Codex–Claude policy-audit benchmark.
- Receipt schema v2 with machine-validated attempt origin, lifecycle, prior
  state, replacement evidence, schema-v1 compatibility, and canonical receipt
  migration.

### Fixed

- Blank or whitespace-only receipt schema versions can no longer bypass
  version-gated lifecycle validation.

## [0.2.0] - 2026-07-27

### Added

- Balanced Herdr worker launcher that keeps coordinator and worker panes at
  equal area for groups of up to four total panes.
- Regression coverage for the supported one-, two-, three-, and four-pane
  layouts.

## [0.1.0] - 2026-07-27

### Added

- Repository-native AI Chief of Staff operating contract.
- Progressive durable project memory.
- Herdr-only worker orchestration skill.
- Independent reviewer protocol.
- Model routing catalog.
- JSONL workflow metrics, validator, and tests.
- Reproducible reviewer, token-context, metrics, and long-horizontal evals.
- Repository documentation, CI, and contract checks.
- MIT License.

### Fixed

- Launcher now disables native Codex agents consistently with project config.
