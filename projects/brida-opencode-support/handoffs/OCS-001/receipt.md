# Handoff receipt

## Identity

- Receipt schema version: `2`
- Task ID: `OCS-001`
- Project: `brida-opencode-support`
- Handoff timestamp (UTC): `2026-08-04T09:39:20Z`
- Receipt role: `standalone`
- Parent receipt path: `null`
- Attempt: `1`
- Replaces session: `null`
- Attempt origin: `initial`
- Attempt lifecycle state: `active`
- Prior attempt state: `null`
- Replacement evidence path: `null`

## Plan version

- Artifact or plan ID: `OCS-001-PLAN`
- Version: `13`
- Status: `accepted`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `claude` | `claude-fable-5` (v4 base) plus `claude-opus-5` coordinator amendments (v5–v8) | `w2D:p0` (closed) | `d95644de-8b6b-43bf-923e-5df8567eef29` |
| Implementer | `claude` | `claude-opus-5` | `w2D:p1B` | `153cf811-c7a3-4ba9-85f6-f9cf60d25844` |
| Reviewer | `claude` | `claude-sonnet-5` for both the passing v8 plan review and the code review | `w2D:p1A` (closed) and `w2D:p1C` | `7c83f31c-25f6-4883-8430-bbe1ca58043b` (plan) and `b1186941-c727-43f5-bfb3-1ba4fa8fc0d0` (code) |

## Scope

- In scope: Stage 1 guarded OpenCode checkout coordinator and Herdr worker support per accepted OCS-001-PLAN version 8 — routing entry, guard-config builder, shim with six-key guard environment and D6–D13 preflights, worker and coordinator dispatch, packaging/installer parity, contracts, docs, and tests, executed as S1–S8 with S9 handoff.
- Authorized paths: exactly the plan's "Exclusive implementation paths" list — new `src/brichan/cli/opencode.py`, `bin/brichan-opencode`, `bin/brichan-opencode-exec`; the named modified source/config, test, and doc files; `README_PYPI.md` regenerated only via `scripts/build_pypi_readme.py`.
- Exclusive write ownership: the single implementation writer owns every authorized path; the coordinator and reviewers write none of them.
- Branch: `feature/opencode-stage1`
- Worktree: `primary checkout at the repository root; no separate worktree`

## Non-goals

- Excluded work: `src/brichan/resources/dogfood_v1/**`; existing Codex/Claude adapters and lifecycle code; project memory/dossier files; global OpenCode/Herdr config; credentials; remote state; installed-project plugin isolation; any live-agent probe during S1–S8 (live probes L1–L5/E1–E2 run at S9 acceptance only).

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| `AC1` | `pass` | static + fake-provider tests in `tests/unit/test_opencode_commands.py` and integration suites; per-AC evidence in the implementation report |
| `AC2` | `pass` | forbidden-input refusal tests assert nonzero exit with zero fake-Herdr/provider calls |
| `AC3` | `pass` | environment-scrub and six-key guard tests; auth-reachability clause deferred to E2 as the plan states |
| `AC4` | `pending` | v8 failed this live: a project plugin executed under the guarded launch. Closed by the v9 D8 extension to `{plugin,plugins}` plus the round-4 no-Git-worktree refusal. Live evidence: L4 re-run refuses singular/symlinked/plural project plugin markers; a fake-HOME probe shows global-XDG and home-dot plugin markers never execute, protected by D7 isolation rather than by refusal |
| `AC5` | `pass` | all seven allowlist clauses plus run-2 mismatch refusal tested with key-path-only diagnostics; no-secret-leak assertion included |
| `AC6` | `pass` | direct in-session read of the `<available_skills>` block returned exactly `herdr-orchestration`, with `customize-opencode` absent; L5 pin held; L3 produced zero child sessions. Plus single-primary, options=={}, skill-permission, subagent_depth tests; in-session availability proof deferred to E1/L3/L5 by design |
| `AC7` | `pass` | pre-Herdr `.brichan` gate and D11 package-marker console-gate tests, including the lookalike-target dogfood case |
| `AC8` | `pass` | byte-identical Codex/Claude argv snapshots and manifest-compatibility tests unchanged and green |
| `AC9` | `pass` | packaging metadata, installer exposure, repository-path inventory, and installed-dogfood smoke all green |
| `AC10` | `pending` | `make check`/`make test` pass and all seven live probes L1–L5/E1–E2 are recorded; the final independent review returned PASS on plan v9 and CHANGES REQUIRED on the code, whose findings rounds 4 and the follow-up probes closed. The confirming re-review returned PASS; plan and code reviews both PASS against the exact v9 text |

## Verification

| Command | Result |
| --- | --- |
| `make check` | `pass` |
| `make test` | pass (metrics 10, unit 498, contract 77, integration 100; re-run independently by the coordinator after every remediation round) |

## Implementation evidence

- Changed artifacts: 5 new files (`src/brichan/cli/opencode.py`, `bin/brichan-opencode`, `bin/brichan-opencode-exec`, `tests/unit/test_opencode_commands.py`, plus regenerated `README_PYPI.md` path already tracked) and 20 modified source/config/test/doc files; complete list in the implementation report
- Diff evidence: `git diff --stat`: 25 files changed, 887 insertions, 28 deletions; `src/brichan/cli/_root.py` was authorized but deliberately unmodified (disclosed deviation: editing it risked AC8 argv identity; D11 lives in `opencode.py`)
- Test evidence: 80 new unit tests in `tests/unit/test_opencode_commands.py`; all suites green; full report with per-AC evidence in the implementation report referenced below

## Review verdict

- Verdict: `pending`
- Findings: all closed. Against plan v8 the code review ran two rounds — one Medium diagnostic leak in the D9 skill precheck, fixed, then PASS. Live probe L4 then falsified v8 by executing a project-local plugin under the guarded launch; the user chose to close it by extending D8, the plan became v9, and remediation round 3 implemented `{plugin,plugins}` scanning. The v9 final review returned PASS on the plan and CHANGES REQUIRED on the code with five findings: an incomplete plugin-entry-point audit, D8's worktree bound silently narrowing to cwd outside a Git repo, AC4 live coverage narrower than its own scope, AC6/E1 evidence not being a direct read of the `<available_skills>` block, and a stale receipt. Remediation round 4 closed the two code findings, Brichan closed the two evidence findings with follow-up live probes and this receipt closed the fifth. The confirming re-review returned **PASS** on the current tree, independently re-verifying test bindingness by reverting the fix in a scratch copy.

## Risks and open decisions

- Risks: `OPENCODE_TEST_HOME` is an internal, undocumented override, acceptable only under the exact D6 1.18.12 pin; D6's no-migration conclusion is version-pinned in both OpenCode and `yargs@18.0.0`; org/well-known and managed config merge after inline config with a documented bounded post-check race; agent-scoped skill availability is provable only in-session (E1). Implementation-stage additions, all fail-closed and to be checked first at L1: the allowlist's agent-entry shape for disabled built-ins was probed only for a plain agent; `variant` as an agent field is asserted by D3 but not yet observed live; skill-permission normalization accepts several ordered shapes but requires exactly `* deny` then `herdr-orchestration allow`.
- Open decisions: none for this task. Recorded for the user separately: the manifest `review` route (Codex `gpt-5.6-sol`) is unusable on this account and needs a routing decision outside OCS-001.

## Cleanup status

- Brida-owned panes closed: `yes`
- Project memory updated: `yes`
