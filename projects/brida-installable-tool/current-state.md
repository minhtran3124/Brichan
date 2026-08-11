# Current state

Last updated: 2026-08-10

## Summary

Status: active. `brichan` is published on PyPI and releases are automated. The
installed Codex vertical slice, the external installer, read-only `doctor`
diagnostics, and the mandatory worker lifecycle are all in place. The open gate
is dogfood in an external owner repository with real Codex and real Herdr.

## Distribution and release

- The `brichan` distribution is published on PyPI; `pip install brichan` is the
  documented entry point (`README.md`).
- Releases are tag-triggered: pushing `vX.Y.Z` runs
  `.github/workflows/publish.yml`, which builds, validates, and publishes
  through PyPI Trusted Publishing. The first fully automated publish was
  `v0.9.0` on 2026-08-03. Current version: see `VERSION`.
- `scripts/install-brichan` installs the tool from any directory into a
  dedicated external virtual environment and exposes commands through guarded
  symlinks, with no virtualenv activation and no checkout build artifacts.
- `make check` includes a read-only, offline durable-memory consistency gate.
- The repository is public at https://github.com/minhtran3124/Brichan; the
  PyPI long description embeds the hero image through the anonymous raw URL
  (verified 2026-08-10).

## Installed-project shape

- Commands: `brichan init` (dry-run by default, `--apply` to write),
  `brichan status`, `brichan doctor` (text plus `--json`), and `brichan run`.
- `init` writes a versioned `.brichan/` directory — manifest, managed policy,
  model routing, Herdr skill resources, and mutable project memory — plus
  missing root agent pointers and the default
  `.agents/skills/herdr-orchestration/` export. Existing files and skills are
  left untouched; an existing `.agents/skills/` tree is topped up only when
  the Brichan skill is absent.
- `run` launches external `codex` directly at the target root through a narrow
  option allowlist; text after `--` is literal prompt content. Target-owned
  `bin/brichan-*` wrappers are never executed.
- State diagnostics refuse malformed, dangling, symlinked, inaccessible, or
  incompatible `.brichan/` state instead of repairing it.
- Installed mode supports Codex on POSIX with Python 3.10+.

## Policy in installed mode

- The packaged policy mandates the **mandatory plan/implement/review lifecycle**:
  every task that creates, edits, or deletes repository files runs
  `plan` → `implement` → independent `review`, with no bounded-edit exception,
  and the coordinator writes only under `.brichan/project-memory/`.
- Policy resources are hash-managed, so an existing `.brichan/` reports
  `incompatible` after a package upgrade or a deliberate policy change. Recovery
  is a deliberate backup of `project-memory/`, deleting `.brichan/`, and
  re-running `brichan init --apply`. Schema v1 is migration-free by design.

## Open gates

- Run the documented dogfood workflow in one external owner repository with real
  Codex and real Herdr, with explicit backup and reinitialization expectations,
  and record friction and defects before considering 3–5 trusted users.
- No TestPyPI rehearsal environment, workflow, or Trusted Publisher exists.

## Risks

- Schema v1 has no repair or migration path; version changes require deliberate
  backup and reinitialization.
- Abrupt process or machine termination may leave `.brichan-stage-*` directories
  for manual inspection and removal.
- The installed-project Codex allowlist deliberately blocks advanced
  subcommands and arbitrary configuration; option-like prompt text must follow
  `--`.
- The gitignored checkout `.venv/` contains an unexplained Unicode `𝜋thon`
  alias and packaging utilities. It is excluded from source scans and cannot
  enter the installer wheel snapshot, but its provenance is unresolved.

## Unverified assumptions

- Real Codex accepts the generated `developer_instructions` and `skills.config`
  CLI overrides in the owner environment exactly as validated against current
  official documentation.
- The narrow one-user allowlist is sufficient for the owner's first real
  external workflow.
