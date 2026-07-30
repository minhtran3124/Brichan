# Current state

Last updated: 2026-07-29

## Summary

Status: active. Research, Stage 1 implementation, disposable installed-wheel
verification, and independent review are complete. The next stage is one-owner
dogfood in a selected real repository, followed later by 3–5 trusted users.

## Completed recently

- Audited coexistence with existing target `.claude`, `.agents`, `.codex`,
  instruction files, skills, hooks, and wrappers. `init` is byte-preserving
  outside `.brida/`, but runtime compatibility is conditional: `AGENTS.md` and
  trusted `.codex/config.toml` can participate in Codex, while `.agents/skills`
  discovery and `skills.config` array layering still need a live-provider probe.
- Assessed a Rust migration for performance using local Python 3.10.11
  benchmarks and an independent read-only worker. Current Brida commands are
  approximately 48–54 ms median; retain Python unless a measured CPU gate is
  crossed.
- Compared six products/mechanisms using reverified official sources.
- Audited current package readiness, repository coupling, lifecycle options,
  security/compatibility risks, positioning, advantages, and disadvantages.
- Verified the baseline complete suite: 121 tests plus metrics, 33 receipts,
  repository paths, compatibility, package imports, and shell checks passed.
- Added policy/skill-loading alternatives, the Herdr skill lifecycle, path
  migration inventory, scoped risks/guardrails, and sequenced evidence gates.
- Replaced market-oriented gates with three dogfood stages: disposable
  technical proof, one-user owner workflow, then 3–5 trusted users.
- Independent Codex Sol review initially returned `CHANGES REQUIRED`; nine
  bounded primary and consistency findings were remediated and final re-review
  returned `PASS`.
- All six Brida-owned research/review panes (`w1X:p34`–`w1X:p39`) were closed;
  the coordinator and unrelated workspaces were preserved.
- Implemented package-owned `brida init`, `status`, `doctor`, and direct Codex
  project launch with a versioned `.brida/` footprint.
- Preserved checkout mode while preventing target repositories from spoofing
  clone markers or executing target-owned `bin/brida-*` wrappers.
- Added no-follow state validation, deterministic malformed/incompatible
  diagnostics, target-local Herdr routing, and a narrow installed-project
  Codex option allowlist.
- Built and installed a wheel outside the checkout; verified init idempotency,
  exact resource packaging, hostile wrappers, routing contamination,
  symlink/dangling/inaccessible state, and literal `--` prompt boundaries with
  fake Codex.
- Independent Codex Sol implementation review required two remediation rounds
  and returned final `PASS`.
- Final coordinator and reviewer verification passed 152 tests plus metrics,
  receipts, repository-path, compatibility, import, shell, diff, and artifact
  checks.
- Re-checked `config/model-routing.json` at the user's request: the named
  `implement` route resolves to Claude Sonnet medium and Claude authentication
  is available.
- A Claude Sonnet implementation stabilization worker independently rebuilt
  and installed the wheel, reran adversarial probes and all 152 checks, found
  no reproducible defect, and made no code changes.
- Added `scripts/install-brida`: it can run from any directory, builds from a
  temporary source snapshot, installs into a dedicated external virtual
  environment, and exposes commands through safe symlinks without activation.
- Verified the installer from a disposable target repository with no
  `VIRTUAL_ENV`; `brida init --apply` succeeded through the installed command
  shim and left no checkout build artifacts.
- Hardened interpreter selection and dedicated-environment reuse so missing
  `pip` fails early with clear, non-destructive recovery guidance.
- Claude Sonnet implementation and Claude Opus independent review closed all
  installer prerequisite and local-venv scan findings with final verdict
  `PASS`.
- Final independent verification passed 155 checks, including 32 integration
  tests, 34 canonical receipts, shell parsing, and outside-checkout installation
  without activation.
- Prepared the future `brichan` `0.5.0` distribution without publishing it:
  wheel/sdist metadata, clean-artifact CI, tag/version validation, and an OIDC
  Trusted Publishing workflow are in place while `brida` imports and commands
  remain unchanged.
- Re-checked and pinned model routing: Claude coordinator uses
  `claude-fable-5` low, implementation uses `claude-sonnet-5` medium, and
  review uses `claude-opus-5` high. The canonical IDs and their aliases
  completed live probes. Claude Sonnet implementation and Claude Opus
  independent review returned `PASS`.

## In progress

- Select one owner repository and run the documented dogfood workflow with
  explicit backup/reinitialization expectations.
- Before the first PyPI release, confirm the public repository URL, configure
  the PyPI trusted publisher and GitHub `pypi` environment, fix the PyPI README
  image URL, then explicitly authorize upload.

## Blockers

- None.

## Risks

- Schema v1 intentionally has no repair or migration; package-version changes
  require deliberate backup and reinitialization.
- Abrupt process or machine termination may leave `.brida-stage-*` for manual
  inspection and removal.
- The installed-project Codex allowlist intentionally blocks advanced
  subcommands and arbitrary configuration; option-like prompt text must follow
  `--`.
- Real Codex and real Herdr execution in an owner repository remains the next
  dogfood evidence gate. Disposable acceptance used fake Codex and Herdr
  dry-run only.
- The gitignored Brida-checkout `.venv/` contains an unexplained Unicode
  `𝜋thon` alias and packaging utilities. It is excluded from source scans and
  cannot enter the installer wheel snapshot, but its provenance should be
  resolved before any future publishing step.

## Next actions

1. Choose one non-critical owner repository and back up any existing `.brida/`.
2. Run `/absolute/path/to/brida/scripts/install-brida`, then run `init`,
   `status`, `doctor`, direct
   Codex launch, and one bounded Herdr worker lifecycle.
3. Record friction and defects; only then decide whether to expand to 3–5
   trusted users.

## Unverified assumptions

- Real Codex accepts the generated `developer_instructions` and
  `skills.config` CLI overrides in the owner environment exactly as validated
  by current official documentation and command construction.
- The narrow one-user allowlist is sufficient for the owner's first real
  workflow.
