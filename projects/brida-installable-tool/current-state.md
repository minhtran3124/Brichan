# Current state

Last updated: 2026-08-17

## Summary

Status: active. `brichan` is published on PyPI and releases are automated. The
installed Codex vertical slice, the external installer, read-only `doctor`
diagnostics, and the mandatory worker lifecycle are all in place. The open gate
is dogfood in an external owner repository with real Codex and real Herdr.

HERDR-001 implements accepted plan `HERDR-HARDENING-PLAN-001` version 5 on the
user-authorized branch and draft PR #30. The typed monitor reads Herdr
terminal-buffer text/JSON, never screenshots; scheduling state is not completion
evidence. The external installer now exposes the observe command, and preflight
reports missing required Claude/Codex integration rows as unhealthy. Independent
code-review artifact v5 records `PASS`; evidence includes 167 focused tests and
a green full gate with 523 unit, 93 contract, and 126 integration tests. Only the
requested branch, commit, push, and draft PR were authorized; Herdr upgrade,
newer capability adoption, release, and publication remain unauthorized.

DOGFOOD-007 is locally complete. Source wrappers now select checkout behavior
through explicit wrapper-only entrypoints, while installed console scripts stay
managed-only and ignore target-controlled checkout claims. The bounded Claude
replacement closed forged-symlink, malformed-path, and deterministic-coverage
findings; focused 51/36/14/29 tests and full 533/95/130/10 gate pass with
`.brichan/` present. Fresh independent plan/code review version 2 records PASS.

POLICY-002 is locally complete. Both checkout and packaged operating policies now require
application-owned, distinctly justified tests; reject duplicate, speculative,
and implementation-coupled coverage; sequence focused-to-broad checks by
default; reserve specialized tests for identified risks; diagnose failures
before changes; and forbid weakening assertions. Both worker task packets point
to the applicable policy. The exact nine-file patch passes focused 8/12/18
contract suites, repository-path validation, and whitespace checks; the single
broad gate passes with 10 metrics, 533 unit, 99 contract, and 130 integration
tests; fresh independent code review version 1 records PASS with no findings. Existing
initialized `.brichan/` state will intentionally require documented
reinitialization after the packaged-resource hashes change.

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

- TECHSTACK-001 is complete on branch `feat/techstacks-rules` (from `main` at
  `5172eb1`) and uncommitted: plan version 10 steps 1–10 are implemented and
  independently reviewed `PASS`. Seven implementation packets each closed at a
  fresh review; the whole-feature review at max effort found 12/12
  requirements owned and tested, every frozen literal identical across model,
  resolver, CLI, doctor, policy, skill, and eval, the isolation closure
  re-executed through the real CLI with zero planted executions, and ten
  fail-closed categories exact on both interpreters; it held on one
  test-hygiene High (design-parity assertions read the gitignored dossier),
  closed by the user's committed-fixture remedy and confirmed at the closing
  review. `make check` exits 0 on Python 3.10.11 and 3.14.6 both in this
  checkout with zero skips and in a dossier-free clone — the first time both
  have been true in this task. No commit, push, pull request, release, or
  real owner-repository reinitialization has been made or authorized; the
  commit is the user's decision. Eight non-gating follow-ups survive, recorded
  in `handoffs/TECHSTACK-001/code-review.md` version 7 §`Closing judgment`:
  two plan-text corrections (`design.md:1153` approval target; `plan.md:559`
  provenance wording plus a stale `plan.md:511` citation in receipt and
  index), one cross-module cap assertion (`model.RELATIVE_PATH_BYTE_MAX` is
  pinned by no test), a prose clarification that `bin/brichan:13` predates the
  closure, two step-6 fixture-ordering wording notes, a missing hash-freeze for
  `tests/fixtures/doctor_v2_text.json`, and the carried unmeasured Linux and
  real-owner-tree caps.
- TECHSTACK-002 is open at intake (Level 1) for the eight non-gating
  follow-ups the TECHSTACK-001 closing review recorded, on the user's
  2026-08-26 direction, plus two findings from the same day's dogfood of
  `techstacks/` on this repository (committed as Brichan's own rule tree,
  3 maps, 6 leaves, 14 rules, resolved applicable and verified match): the
  leaf grammar's `_is_prose` (`src/brichan/techstacks/markdown.py:305`)
  rejects backticks and angle brackets inside Scope, Rules, and Verification
  bullets, which is real friction for a repository whose rules name commands
  and files; and `INVALID_LEAF` reports only "leaf bytes do not match the
  leaf grammar" with no line number or violated rule, so an author must
  bisect by hand. The grammar is frozen by plan version 10, so relaxing it is
  a plan revision; improving the diagnostic detail may not be. Its dossier is not yet scaffolded: the standard
  scaffold leaves placeholder artifacts that fail `make dossiers` until the
  plan, receipt, and reviewer sessions exist, so the coordinator scaffolds it
  at the moment planning is authorized. No planning worker has been started.
- Decide separately whether to authorize a Herdr upgrade or newer capability
  adoption; the accepted plan does not presuppose either decision.
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

- Claude worker routing is available again. The 2026-08-24 `Login expired`
  probe was a credential-namespace fault, not an expired subscription: Claude
  Code keys keychain credentials by `sha256(CLAUDE_CONFIG_DIR)[:8]`, and a
  process without that variable falls back to a dead legacy entry. Herdr-started
  Claude workers must therefore pass
  `--env CLAUDE_CONFIG_DIR=<config dir>`; `brichan-techstack-plan-review-v6` ran
  successfully that way on Claude `claude-opus-5` at max effort.
- Real Codex accepts the generated `developer_instructions` and `skills.config`
  CLI overrides in the owner environment exactly as validated against current
  official documentation.
- The narrow one-user allowlist is sufficient for the owner's first real
  external workflow.
