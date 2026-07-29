# Current state

Last updated: 2026-07-29

## Summary

Status: active. Research, Stage 1 implementation, disposable installed-wheel
verification, and independent review are complete. The next stage is one-owner
dogfood in a selected real repository, followed later by 3–5 trusted users.

## Completed recently

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

## In progress

- Select one owner repository and run the documented dogfood workflow with
  explicit backup/reinitialization expectations.

## Blockers

- None. Claude is intentionally deferred because local authentication was not
  available during routing checks.

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

## Next actions

1. Choose one non-critical owner repository and back up any existing `.brida/`.
2. Build/install the local wheel and run `init`, `status`, `doctor`, direct
   Codex launch, and one bounded Herdr worker lifecycle.
3. Record friction and defects; only then decide whether to expand to 3–5
   trusted users.

## Unverified assumptions

- Real Codex accepts the generated `developer_instructions` and
  `skills.config` CLI overrides in the owner environment exactly as validated
  by current official documentation and command construction.
- The narrow one-user allowlist is sufficient for the owner's first real
  workflow.
