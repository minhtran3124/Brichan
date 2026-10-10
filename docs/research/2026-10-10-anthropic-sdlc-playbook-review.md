# Brichan vs. Anthropic's AI-native SDLC playbook

Research note, not policy. Date: 2026-10-10. Brichan baseline: `main` at
`200880c` (package 0.13.x). Where this note conflicts with `docs/policy/`, the
policy files win.

---

## 1. TL;DR

| Verdict | Count | Headline |
|---|---|---|
| ✅ Doing right | 10 | The artifact chain, evidence-before-done, independent review and "controls as code" are already stronger than the playbook asks. |
| ⚠️ Needs improvement | 9 | Few **deterministic guardrails at edit time** (no hooks), evals don't run on policy/skill changes, and no "repeat mistake → rule" loop. |
| ❌ Incorrect / gap | 4 | The Claude runtime still exposes the native **`Workflow`** multi-agent tool; the level-0 review decision is not enforced mechanically; the audit trail lives outside Git with no link from the PR; metrics are mostly `null`. |

**The three most worthwhile changes:**

1. Block the `Workflow` tool in the Claude launcher (1-line fix plus test; it enforces an existing non-goal).
2. Add `.claude/settings.json` hooks for what is currently advisory: protected paths, credential-in-diff, test-file edits during fixes.
3. Run `make check` plus the eval suites in CI **whenever policy, skills, `CLAUDE.md`/`AGENTS.md` or hooks change**, and turn each escaped defect into a regression eval.

---

## 2. Sources and method

- Primary: [The AI-native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook) (claude.com, Aug 2026; reportedly revised 2026-09-28).
- Secondary commentary (context only):
  [Waydev: the missing measurement layer](https://waydev.co/anthropics-ai-native-sdlc-playbook-has-a-missing-layer-measurement/),
  [Port: implementing the playbook](https://www.port.io/blog/anthropic-ai-native-sdlc-playbook),
  [GenAI Playbook reading](https://www.genai-playbook.com/articles/ai-native-sdlc-playbook-en.html).
- Brichan evidence: [`PRODUCT.md`](../../PRODUCT.md),
  [`operating-principles.md`](../policy/operating-principles.md),
  [`reviewer.md`](../policy/reviewer.md),
  [`memory-policy.md`](../policy/memory-policy.md),
  [`task-dossier.md`](../workflows/task-dossier.md),
  [`workflow.md`](../workflow.md), `src/brichan/cli/provider_commands.py`,
  `.github/workflows/ci.yml`, `Makefile`, `metrics/runs.jsonl`, `evals/`.
- One live check (section 6, item X1): ran Claude Code 2.1.296 with and without
  `--disallowed-tools=Task` and compared the tools it reported.

**How to read the verdicts.** ✅ = matches or exceeds the playbook. ⚠️ =
partially there; a concrete step would close the gap. ❌ = contradicts
Brichan's own stated contract, or a playbook control is missing in a way that
causes a real risk. Deliberate divergences that follow from `PRODUCT.md`
non-goals are listed separately (section 7) and are not counted as defects.

---

## 3. The playbook in one page

**Thesis:** building is no longer the bottleneck. Planning, review/test and
deploy still run at human speed. So: (1) every stage commits **one artifact
to Git** and the next stage reads it; (2) human attention is concentrated **at
the gates**; (3) governance moves into **enforced configuration**: *"CLAUDE.md
gives context, a skill advises, a hook guarantees."*

| Stage | Artifact | Key plays |
|---|---|---|
| 1 Plan | `intent.md` | Capture intent with Claude; product owner reviews before committing. |
| 2 Design | `spec.md` | Spec generated from intent, constrained by policy skills; owner reviews, doesn't write. |
| 3 Build | `plan.md` + diff | Plan mode by default; short `CLAUDE.md` with a known-mistakes section; skills; **hooks** (protected paths, formatters, no secrets); parallel sessions in worktrees (start with 2–3). |
| 4 Test | tests | One-command feedback loop; failing test first for bugs (hook blocks test edits); **fresh-context verifier**; **20–50 continuous evals** run on changes to CLAUDE.md, skills or hooks; incident → eval. |
| 5 Deploy | reviewed PR | AI PR review guided by `REVIEW.md` (severity definitions, nit caps); the author never approves; hooks as approval gates; managed settings; CI starts read-only, then PR-only writes, scoped tokens, tiered prod deploys. |
| 6 Maintain | incident record → new `intent.md` | Deterministic triggers (σ bands) with tiered agent authority; scheduled scans; lessons file. |

**Adoption order:** start with the plays that have no prerequisites (intent,
CLAUDE.md, skills, feedback loop, hooks), then evals, then PR review and gates,
then CI/CD, then maintain loops.

**Metrics it names:** first-pass merge rate, plan-to-merge time, rework
cycles, repeat-mistake frequency, eval pass rate, incident-to-eval time, DORA.

---

## 4. Stage-by-stage scorecard

| Stage | Playbook expects | Brichan today | Verdict |
|---|---|---|---|
| Plan | `intent.md` committed, owner-reviewed | `request.md`: redacted, immutable origin; coordinator frames objective, scope and acceptance (operating principles §1) | ✅ (not committed: see C3) |
| Design | `spec.md` from intent, policy-constrained | Level 2: `requirements`, `brief`, `options`, `design`, `client-follow-up-questions`; techstack Snapshot pointers constrain scope | ✅ |
| Build: plan | Plan mode; `plan.md` versioned | `plan.md` (L2, accepted version immutable) or `report.md § Plan` written before implementing (L0/L1) | ✅ |
| Build: context | Short CLAUDE.md, known-mistakes section, corrections after 2 repeats | CLAUDE.md is 48 lines and points to policy, but has no known-mistakes section or correction loop | ⚠️ |
| Build: guardrails | Hooks: protected paths, formatters, no secrets | No `.claude/` directory, no hooks. The launcher blocks bypass flags; everything else is advisory or checked after the fact | ⚠️ |
| Build: parallelism | Worktree per session, start small, scale while review keeps up | One branch and one worktree per writer (`concurrent-writers.md`); Herdr workers | ✅ |
| Test: feedback loop | One non-zero-exit command, measurable done | `make check` is the single gate; CI runs it on 3.10 and 3.13 | ✅ |
| Test: failing test first | Commit the failing test; hook blocks test edits during the fix | Policy requires a regression test, and the reviewer treats a missing one as a ≥ medium defect. No test-first order and no hook | ⚠️ |
| Test: verifier | Fresh-context verifier | Independent reviewer in a fresh session, preferably another model family; "`done` is not proof" | ✅ (stronger) |
| Test: continuous evals | 20–50 real-task evals, run on config changes, gate on pass rate | `techstack-eval` runs in `make check`; workflow and dossier evals are one-off studies, not a regression suite over policy and skills | ⚠️ |
| Deploy: review policy | `REVIEW.md` with severity definitions, nit caps, spec/plan compliance | `reviewer.md` covers scope, a "no style nits" rule and test rules; severity levels are **named but not defined** | ⚠️ |
| Deploy: separation of duties | Author can't approve | Enforced in the dossier: reviewing and authoring sessions must differ | ✅ |
| Deploy: gates | Hooks as allow/ask/block; managed settings | Remote actions, publishing and level-2 ship need recorded user authorization; launcher rejects bypass modes | ✅ policy / ⚠️ enforcement |
| Deploy: CI/CD | Read-only first, PR-only writes, scoped tokens, tiered deploy | CI `permissions: contents: read`; release via tag + PyPI Trusted Publishing | ✅ |
| Maintain | Triggers, scans, incident → intent, lessons file | "Escaped defect returns the level to the full lifecycle" rule exists; no incident record, lessons file or scheduled scans | ⚠️ (low priority at dogfood stage) |
| Measure | Leading and lagging metrics | `metrics/runs.jsonl` holds observed values only, but they are mostly `null` (see C4) | ❌ / ⚠️ |

---

## 5. ✅ What Brichan is doing right

1. **Artifact chain = playbook's core idea.** The dossier (`request → requirements → design → plan → report → plan-review/code-review → pr-desc`) is the same "each stage writes, next stage reads" chain, with versioning and immutable origins.
2. **One source of truth per fact.** The dossier `index.md` links and never restates; policy is canonical in one place. This matches the playbook's source-of-truth sidebar.
3. **Fresh-context verification, made stronger.** The playbook asks for a verifier subagent. Brichan requires an independent session, prefers a different model family, and the validator checks that session IDs differ.
4. **Separation of duties is machine-checked.** The playbook relies on an approval rule. Brichan's validator rejects a review whose session authored the plan or report.
5. **Controls as code.** Dossier, receipt, memory, path and contract-path validators plus `make check` turn process rules into exit codes.
6. **One-command feedback loop.** `make check` is the single, non-zero-exit gate, and focused runs never replace it.
7. **Test discipline beyond the playbook.** Test owned behavior only; diagnose before changing tests; never weaken assertions to pass a gate.
8. **Human gates at the right places.** Publishing, remote state, secrets, permission broadening and level-2 ship need explicit user authorization. This is the playbook's "humans own judgment" applied to the riskiest edges.
9. **Least-privilege CI and release.** `contents: read` in CI, tag-triggered Trusted Publishing, and a wheel smoke test in a clean venv.
10. **Measurement honesty.** "Observed only, `null` otherwise" answers the main criticism of the playbook ([Waydev](https://waydev.co/anthropics-ai-native-sdlc-playbook-has-a-missing-layer-measurement/)). The level system ("raise the level when…", "an escaped defect returns the level to full ceremony") is the playbook's "confidence gate" idea.

---

## 6. ⚠️ Needs improvement / ❌ incorrect

### ❌ Incorrect or real gaps

| ID | Finding | Evidence | Why it matters |
|---|---|---|---|
| **X1** | **The Claude coordinator can still use native multi-agent orchestration through `Workflow`.** The launcher passes only `--disallowed-tools=Task`. | `src/brichan/cli/provider_commands.py:25`. Live check on Claude Code 2.1.296: with the flag, `Agent` disappears (the `Task` alias still works) but `Workflow` remains; without the flag, both are listed. | Breaks the first `PRODUCT.md` non-goal ("no runtime-native delegation") for the Claude runtime. The same risk exists for any future delegation tool name: the block list is name-based. Caveat: the tool list came from the model's self-report; confirm with a hook log or the `/tools` listing. |
| **C2** | **The level-0 "is review required?" decision is not enforced.** `check_contract_paths.py` exists, but "no gate ties the review decision to the checker's exit code". | `task-dossier.md`, "Trust boundary" paragraph | The playbook would put this in a hook or CI check. Today a mis-classified level-0 change skips review silently. |
| **C3** | **Dossiers are git-ignored, and nothing links a PR to its dossier.** | `.gitignore:67` (`/projects/*/handoffs/*/`); PR template has no Task-ID field | The playbook's minimum bar is *linkage*. Keeping dossiers local for privacy is a valid choice (section 7), but without a Task ID in the PR the Git history can't be traced back to intent and evidence. |
| **C4** | **Metrics can't answer the playbook's questions.** | `metrics/runs.jsonl`: 32 rows; `elapsed_seconds` null in 24, `cost_usd` null in 32, `coordinator_input_tokens` null in 30. No `rework_cycles`, `first_pass_review`, or `plan_to_merge` fields | "Measure instead of assume" (operating principles §2) is the policy, but there isn't enough data to decide whether level-2 ceremony pays off. |

### ⚠️ Needs improvement

| ID | Gap | Playbook play |
|---|---|---|
| I1 | No hooks at all. Protected paths, credential leaks and "don't edit tests during a fix" are advisory only. | Hooks as build guardrails / approval gates |
| I2 | `CLAUDE.md`/`AGENTS.md` have no **known-mistakes** section and no "same mistake twice → add a rule" loop. | CLAUDE.md play |
| I3 | Evals don't run as a regression suite when `docs/policy/**`, `.agents/skills/**`, `CLAUDE.md`, `AGENTS.md` or `config/model-routing.json` change. | Continuous evals |
| I4 | Bug fixes have no **failing-test-first** order (committed red test, then fix without editing it). | Feedback loop / test-first |
| I5 | `reviewer.md` names severities but doesn't define them; there is no explicit nit cap or "compliance against plan" item. | `REVIEW.md` |
| I6 | The herdr-orchestration skill has no **trigger test** (does it load when delegation is needed?), and skill changes have no sign-off rule. | Skills play |
| I7 | No incident or lessons record; escaped defects aren't turned into evals. | Maintain / incident → eval |
| I8 | Level-2 ceremony (11 artifacts) risks the bottleneck the playbook warns about: human review time. Simplification evals exist but aren't closed into policy. | Bottleneck thesis |
| I9 | No scheduled read-only jobs (dependency/security scan, stale-memory check, flaky-test triage). | CI/CD read-only steps, recurring scans |

---

## 7. Deliberate divergences (not defects)

| Playbook says | Brichan does | Keep? |
|---|---|---|
| Use subagents in `.claude/agents/` and parallel sessions | Herdr main-agent workers only | **Keep.** This is a product non-goal. The playbook's intent (isolated context, own tool limits) is met by Herdr. |
| Commit every artifact to Git | Dossiers stay local; memory files are committed | **Keep, but add linkage (C3).** |
| Auto mode once guardrails mature | Installed mode requires the full plan → implement → review lifecycle | **Keep for now.** Revisit after hooks (I1) and evals (I3) exist, which are the playbook's own prerequisites for auto mode. |
| Claude in PR review via `@claude` on GitHub | Review happens in a fresh Herdr session | Keep. Optional later (M5). |
| Production triggers, σ bands, Claude Tag | n/a, since Brichan is a dogfood CLI | Not applicable yet. |

---

## 8. Suggested updates, by level and effort

Effort: **S** ≈ < 1 h, **M** ≈ half a day to 1 day, **L** ≈ several days.
"Contract" means the change touches a [contract path](../workflows/task-dossier.md#contract-paths) and therefore needs independent review.

### Level 1: Easy (do first)

| # | Change | Fixes | Effort | Contract |
|---|---|---|---|---|
| E1 | **Done 2026-10-10 (PR #43):** `CLAUDE_NATIVE_AGENT_FLAGS` is now `--disallowed-tools=Agent,Task,Workflow`; tests assert the full flag. | X1 | S | yes (`src/`) |
| E2 | Add a `Task ID:` / `Dossier:` field to `.github/pull_request_template.md` and `pr-desc.md`'s template. | C3 | S | partial (`docs/workflows/`) |
| E3 | Add a short `## Known mistakes` section to `CLAUDE.md` and `AGENTS.md`, with the rule: "a mistake seen twice gets one line here or a hook." | I2 | S | yes |
| E4 | Define the severities in `reviewer.md` (critical/high/medium/low, one line each), add "compliance with accepted plan" as a review item, and cap low-severity nits (e.g. ≤ 3). | I5 | S | yes |
| E5 | In `operating-principles.md` § Testing discipline, add: "For a bug fix, commit the failing regression test first; the fix must not edit that test." | I4 | S | yes |
| E6 | Start `docs/history/lessons.md` (or a section in each project `decisions.md`): one entry per escaped defect, linking its regression test or eval. | I7 | S | no |

### Level 2: Medium

| # | Change | Fixes | Effort | Contract |
|---|---|---|---|---|
| M1 | Add a project `.claude/settings.json` with **fast, file-scoped hooks**: block edits to `.env*`/credentials patterns; block edits under `docs/policy/` unless the task opted in; warn on secrets in staged diffs. Mirror the same checks for Codex where its hook support allows. | I1 | M | yes (new root path → also `config/repository-paths.json`) |
| M2 | Make the contract-path decision a gate: `validate_task_dossiers.py --require-complete` (or a CI step) re-runs `check_contract_paths.py` against the recorded changed-path list and rejects a level-0 `not-required` review when the result is `yes`. | C2 | M | yes |
| M3 | Add a CI job filtered on `docs/policy/**`, `.agents/skills/**`, `CLAUDE.md`, `AGENTS.md`, `config/model-routing.json` that runs the eval suites and fails on a pass-rate drop. | I3 | M | yes |
| M4 | Extend the metrics schema with `rework_cycles`, `review_first_pass` (bool), `plan_to_merge_seconds`, and make the launcher or ledger record start/finish timestamps automatically, so `elapsed_seconds` stops being null. | C4 | M | yes |
| M5 | Add a skill trigger test: a contract test that the herdr-orchestration skill description matches the delegation phrases it must catch. Add "skill changes need independent review" to `reviewer.md`'s mandatory list. | I6 | M | yes |
| M6 | Add a PreToolUse hook that blocks any delegation tool (`Agent`, `Task`, `Workflow`) by matcher. This is defense in depth for X1 and catches future renames, which the CLI flag can't do. | X1 | M | yes |

### Level 3: Hard

| # | Change | Fixes | Effort | Contract |
|---|---|---|---|---|
| H1 | Build a **20–50 case regression eval suite** from past real tasks (`evals/mixed-provider-coding`, dossier pilots) with pass criteria, run on a schedule and on config changes, gating policy/skill PRs on pass rate. Every escaped defect adds a case. | I3, I7 | L | yes |
| H2 | Use the new metrics (M4) to **decide on level-2 ceremony**: compare first-pass review rate and rework for L1 vs L2 over N tasks; collapse or merge artifacts that don't move outcomes. | I8 | L | yes (policy) |
| H3 | Scheduled **read-only** CI jobs: dependency/security scan triage, stale `current-state.md` detection, flaky-test summary. Each opens an issue or a PR only, with scoped tokens. Needs user authorization (remote state). | I9 | L | yes |
| H4 | Optional: an opt-in **committed dossier summary** (redacted `index.md` + `plan.md` + verdicts) exported into the PR or a `docs/history/` record, so Git becomes the audit trail without committing private request text. | C3 | L | yes |
| H5 | Once M1, M3 and H1 are in place, evaluate a **lighter installed-mode path** for low-risk changes (the playbook's "auto mode once guardrails mature"). This is a product decision for the user, not a default. | I8 | L | yes (product) |

### Suggested order

`E1 → M6` (close the delegation hole) → `E2–E6` (cheap policy edits; can go in one reviewed change) → `M1, M2` (hooks and gates) → `M4 → H2` (measure, then simplify) → `M3 → H1` (evals) → `H3–H5`.

---

## 9. Open questions for the user

1. **X1:** Treat `Workflow` (and any future native-orchestration tool) as covered by the "no native delegation" non-goal? (Recommended: yes.)
2. **C3/H4:** Is a Task-ID link in PRs enough, or do you want a redacted dossier summary committed?
3. **M1:** Are project-scoped Claude hooks acceptable in this repo? `brichan init` must still never write hooks into a target repo, per the non-goal on mutating user-owned config.
4. **H3:** Scheduled CI jobs change remote state (issues/PRs). Do you authorize that scope?
