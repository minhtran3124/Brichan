# Current state

Last updated: 2026-08-26

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
  `5172eb1`), committed in the branch's `feat` commits: plan version 10 steps 1–10 are implemented and
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
  commit is the user's decision. The eight non-gating follow-ups recorded in
  `handoffs/TECHSTACK-001/code-review.md` version 7 §`Closing judgment` were
  closed by TECHSTACK-002 on 2026-08-26 (TECHSTACK-001 is now at plan
  version 11, code review version 8); they were:
  two plan-text corrections (`design.md:1153` approval target; `plan.md:559`
  provenance wording plus a stale `plan.md:511` citation in receipt and
  index), one cross-module cap assertion (`model.RELATIVE_PATH_BYTE_MAX` is
  pinned by no test), a prose clarification that `bin/brichan:13` predates the
  closure, two step-6 fixture-ordering wording notes, a missing hash-freeze for
  `tests/fixtures/doctor_v2_text.json`, and the carried unmeasured Linux and
  real-owner-tree caps.
- TECHSTACK-002 is complete and committed on `feat/techstacks-rules` as
  `5573d0e` (2026-08-26; TECHSTACK-001 was committed in the preceding
  `feat` commits). All eleven inputs — the eight closing-review
  follow-ups, the two dogfood leaf-grammar findings, and the self-install
  `EXPORT_EXTRA` finding — are closed under accepted plan
  `TECHSTACK-PLAN-002` version 5: TECHSTACK-001 reissued as plan version 11
  (documentation only, version-10 bytes frozen); seven shared skill caps
  pinned across `lifecycle.py` and `techstacks/model.py`; the doctor text
  fixture digest frozen; a packaged-subset-of-checkout skill test under the
  owner-corrected `PACKAGED-001`; the launcher comment corrected; leaf prose
  now accepts backticks and angle brackets; `INVALID_LEAF` carries the line
  and the violated rule from a closed twenty-member registry. Linux stays a
  user-decided unmeasured residual and `EXPORT_EXTRA` a disclosed unowned
  status. Every stage was reviewed by a fresh independent session (plan v3
  `CHANGES REQUIRED` → v4 `PASS`, v5 `PASS`; R0 `PASS`; stage 1
  `CHANGES REQUIRED` on prose only → re-review `PASS`; stage 2 `PASS`;
  whole-task `code-review.md` v2 `PASS`), and `make check` exits 0 on Python
  3.10.11 and 3.14.6 (10/968/145/193/56, zero skips). Coordination moved
  from the Codex coordinator (usage-limited) to Claude Code on 2026-08-26;
  every worker ran on Claude while Codex stayed limited. Three errata
  against the immutable accepted plan (blocked CLI resolve exits 5, not 0;
  eighth T-LINE fixture unreachable; §7.4 count wording) and five
  non-gating Low follow-ups are recorded in `decisions.md` and
  `handoffs/TECHSTACK-002/code-review.md`. The user authorized the commit; no
  push, pull request, release, or publication has run.
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
- Installed state of this checkout refreshed 2026-08-26 by the documented
  user-controlled journey: `.brichan/` backed up to
  `.brichan.bak-2026-08-26/`, a wheel built from the checkout
  (`brichan-0.12.0`) and installed into a disposable venv, `brichan init
  --apply` run missing-only, and `project-memory/` restored from the backup.
  The manifest now lists all 10 immutable resources including
  `policy/techstacks.md` and `references/handoff-receipt.md`. Installed
  `brichan doctor` reports schema v2 `agent_skill_export: invalid /
  EXPORT_EXTRA`: this repository's tracked `.agents/skills/herdr-orchestration/`
  differs in all four shared files and carries four files the packaged skill
  does not (`agents/openai.yaml`,
  `references/concurrent-writers.md`, `references/task-dossier.md`,
  `references/worker-recovery.md`), so trimming only the extra files would
  expose `EXPORT_STALE`, not `EXPORT_CURRENT`; doctor correctly refuses to
  call the export current without overwriting it. No
  re-export was run. Checkout-mode `bin/brichan doctor` is unaffected and
  still healthy. `.brichan/config/model-routing.json` is an immutable packaged
  resource and therefore carries the package's Codex defaults, not the
  checkout's Claude routes in `config/model-routing.json`; checkout mode reads
  the latter.

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
