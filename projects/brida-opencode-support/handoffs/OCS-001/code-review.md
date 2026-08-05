# Code review

Independent review of the implementation, or the recorded evidence for why no implementation review applies.

## Artifact metadata

- Task ID: `OCS-001`
- Task level: `2`
- Artifact: `code-review`
- Artifact version: `3`
- Origin: `review-session-b1186941-code-review-round-2`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `b1186941-c727-43f5-bfb3-1ba4fa8fc0d0`
- Effective route: `review`
- Effective model: `claude-sonnet-5`
- Effective effort: `high`
- Reviewing session: `6bfb28a8-5d39-405b-8b00-f56659c775b0`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `OCS-001-PLAN`
- Reviewed plan version: `9`

## Claim or decision

**Resolved against plan version 9: PASS.** The final review returned PASS on plan v9 and CHANGES REQUIRED on the code with five findings; remediation round 4 and two coordinator follow-up probes closed them, and the confirming re-review returned PASS on the current tree. Evidence: `/tmp/brichan-ocs001-final-review.md` and `/tmp/brichan-ocs001-final-review-round2.md`. Superseded history follows. The verdict recorded below was reached against version 8, which live probe L4 subsequently falsified: a project-local `.opencode/plugin/*.js` executed under the guarded launch. Version 9 extends D8 to scan plugin roots and corrects D1. The version-8 findings and reasoning are retained as history; this artifact is pending a fresh verdict against version 9.

`The OCS-001 Stage 1 implementation is faithful to accepted plan version 8 and ready for the S9 live probes; the single round-1 Medium finding is closed and round 2 found no new defect.`

## Findings

**Round 2: none. Verdict PASS.** The round-1 finding below is closed; it is retained as the record of what was fixed, not as an open item.

1. **Medium (CLOSED in remediation round 1) — D9 skill-precheck leaks a provider value into its refusal diagnostic.** `src/brichan/cli/opencode.py:500-502` embeds a skill name parsed from the captured stdout of `opencode --pure debug skill` directly in the `GuardError` message. Plan S3 lists "unexpected discovered skill" among the refusals that must use key-path-only diagnostics with captured provider output never reaching user output. A discovered skill name is a data value in a provider-returned array, not a config key, so it is covered by that rule. The boundary still fails closed; only the diagnostic violates the plan. Remediation: refuse without naming the value, and assert in `SkillPrecheckTest` that the injected name is absent, mirroring `test_wrong_model_or_variant_refuses`.

## Round-2 adjudications

The writer remediated and disclosed two judgement calls plus a correction to Brichan's own instruction. The reviewer ruled on each, verifying by independent reproduction rather than accepting the writer's mutation-testing table:

1. **Count-instead-of-name diagnostic — acceptable.** The refusal now reports `len(unexpected)`. A cardinality is a function of how many elements were unexpected, not which, so the same integer results from any set of that size and no decoding recovers an identity. It is a Brichan-derived aggregate, not a redacted echo, and it materially aids S9 triage.
2. **Brichan's `default_runtime` instruction was wrong — writer correct.** `default_runtime` is read only by `resolve_coordinator`; worker routes resolve through `resolve_route` reading `settings.routes[name].runtime`. A test built on `default_runtime` would have passed without reaching the branch. The writer implemented the branch as the round-1 review described it and disclosed the discrepancy.
3. **The second D4 refusal path is currently unreachable on a real target — guard stays.** `config/model-routing.json` is in `IMMUTABLE_PATHS`, so a `.brichan` project with an OpenCode-routed manifest is `MALFORMED` and `inspect_project` raises before resolution. The reviewer confirmed this by source trace and by neutralizing the guard in its own script, proving it is load-bearing rather than vestigial. Its inertness is a property of an independent upstream control, which is what defence-in-depth means; removing it would weaken the boundary.
4. **Keeping Brichan-discovered filesystem paths in diagnostics — agreed.** Those paths come from Brichan's own glob over the local tree, not captured provider output, and suppressing them would make refusals unactionable while hiding nothing an attacker did not already control.

## Test gaps from round 1 (both now closed)

1. CLOSED — the manifest-route branch of the D4 pre-Herdr gate is now covered by `WorkerGateManifestBranchTest` (4 tests).
2. CLOSED — `test_a_source_checkout_that_initialized_itself_is_allowed` covers the D11 permissive branch, varying only the package marker between the allow and refuse assertions on the same directory.

## What the review independently confirmed

- D1–D13 fidelity traced clause by clause against a full read of `src/brichan/cli/opencode.py` (969 lines) and `tests/unit/test_opencode_commands.py` (997 lines); no clause was found unimplemented, weakened, or reordered outside its authorized position.
- No boundary bypass: the legacy `-m`/`--variant` path and the shim's own CLI cannot inject provider argv; no inherited `OPENCODE_*` key survives the scrub; symlink handling matches D8's owned-root scoping; the seven allowlist clauses each hold including normalized agent options and instruction shape; the run-2-to-`execvpe` window contains no provider call and the residual race is the one the plan already discloses and bounds.
- The `PreflightOrderingTest` order assertion is against a runtime-collected trace, not a static source reading, and the two run-2 tests exercise genuinely distinct drift and widening scenarios.
- The disclosed `_root.py` non-change is sound, not a gap: D11's gate is applied on top of whatever root `repository_root()` returns, independent of how that root resolved, and the installed-wheel integration test builds a real lookalike target with `.brichan` + `AGENTS.md` + `bin/` plus a hand-edited OpenCode routing entry and confirms the installed console still refuses.
- Scope is clean: every changed path is on the plan's authorized list, no excluded path was touched, and AC8's byte-identical Codex/Claude argv is explicitly tested and passing.

## Evidence

- Round-1 review: `/tmp/brichan-ocs001-code-review.md`. Round-2 re-review and final verdict: `/tmp/brichan-ocs001-code-review-round2.md`.
- Remediation record: `/tmp/brichan-ocs001-impl-report.md` section "Remediation round 1", including an audit of all 74 `GuardError` sites by data provenance that found exactly one defect, confirming rather than extending the finding.
- Implementation report under review: `/tmp/brichan-ocs001-impl-report.md`, read but independently re-verified against the code rather than trusted.
- The reviewer ran `make check` and `make test` itself in its own session: both pass, 10 metrics / 471 unit / 77 contract / 100 integration, repository paths valid at 79 entries and 71 references, `README_PYPI.md` in sync.
- The coordinator separately ran `make check` and `make test` before the review was launched, with identical results.
- Reviewer session `b1186941-c727-43f5-bfb3-1ba4fa8fc0d0` in Brichan-owned pane `w2D:p1C`; writer session `153cf811-c7a3-4ba9-85f6-f9cf60d25844` in pane `w2D:p1B`. Different models, no shared context.

## Uncertainty

- The review did not re-fetch OpenCode source this session; the OCS-001-R4 source claims underlying D6 and D9 were cross-checked against the plan text and code behavior rather than re-verified against `anomalyco/opencode`. Those claims were independently re-verified during the version-7 plan review and are not part of the uncommitted code under review.
- The verdict covers static and fake-provider evidence only. AC6's in-session skill-availability clause, and AC10's live-probe clause, remain unproven until L1–L5 and E1–E2 run at S9.
- Round 2 deliberately did not re-walk D1–D13 fidelity, the security sweep, or the full test-adequacy pass; those round-1 conclusions stand as recorded and were not re-asserted.
- The two new source files are untracked, so no byte-level pre/post diff was reconstructed for them. The reviewer re-read `check_final_config`, `_check_agent_entry`, `discovery_preflight`, `migration_scan`, and `require_direct_console_target` and found them identical to its round-1 reading.
