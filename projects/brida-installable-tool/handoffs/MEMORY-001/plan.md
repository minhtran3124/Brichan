# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `MEMORY-001`
- Task level: `2`
- Artifact: `plan`
- Artifact version: `6`
- Origin: `planner:2026-08-09-memory-001-plan-v6`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `65f9eedd-94f2-489d-ad67-4e0edf5caf30`
- Effective route: `plan`
- Effective model: `claude-opus-5[1m]`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `MEMORY-001-PLAN`
- Plan status: `accepted`

## Claim or decision

Execute the accepted Durable Memory Consistency Repair in seven bounded steps.
Version 6 keeps every repair the user accepted and removes the checker scope the
planner added. Versions 3 through 5 grew a general path-and-input subsystem, a
104-case matrix, and an every-outcome totality claim that no accepted requirement
asked for; each review then found another undefined corner of that surface.
Version 6 closes the version 5 findings by narrowing to six checks and proving
them with representative evidence. Plan version 5 is superseded.

## Finding disposition

| Finding | Raised in | Status |
|---|---|---|
| v1 H1 — seven-project lifecycle omitted | plan-review v1 | Closed in v2 |
| v1 M1 — symlink-following declared paths | plan-review v1 | Closed in v3 |
| v1 M3 — unauthorized sdist arm | plan-review v1 | Closed in v2; sdists stay out of scope |
| v2 H1 — canonical slash; follow-capable root scan | plan-review v2 | Closed in v3 |
| v2 M2 — seven edits / five files | plan-review v2 | Closed in v3 |
| v3 H1 — PRODUCT contradicted an excluded packaged policy | plan-review v3 | Closed in v4 |
| **v4 M2** — conflicting `changelog-release` triggers | **plan-review v4** | Closed in v5, retained here. Version 5's requirements table cited plan-review v5 for this row; that was the v5 L1 error and it is corrected in `requirements.md` |
| v1 M2, v2 M1, v3 M1, v4 H1, v4 M1 — the diagnostic-completeness thread | plan-review v1–v4 | **Closed in v6 by narrowing.** The general read-input and declared-path subsystems are gone, so there is no open-ended state space left to enumerate |
| **v5 H1** — the 104-case matrix cannot satisfy its every-caller/every-outcome criterion | plan-review v5 | **Closed** — the criterion and the matrix are deleted. `requirements.md` R21–R22 and `design.md` §4 replace them with contractual test categories and three golden fixtures |
| **v5 M1** — the ordered-triple oracle lacks exact details everywhere | plan-review v5 | **Closed** — `requirements.md` R20 and `design.md` §4: exact ordered triples for three named golden fixtures, paths plus check IDs elsewhere, no canonical detail table |
| **v5 M2** — unknown numeric `errno` escapes normalization | plan-review v5 | **Closed** — `design.md` §3.5 uses `errno.errorcode.get(exc.errno, f"errno-{exc.errno}")` |
| **v5 M3** — calendar-invalid matching changelog date unowned | plan-review v5 | **Closed** — `design.md` §3.4: a matching heading whose date is not a real calendar date counts as no valid matching release, emits one `changelog-release`, and suppresses only staleness |
| **v5 L1** — wrong provenance in one disposition row | plan-review v5 | **Closed** — corrected in `requirements.md` and above |

### Step 1 — Repair the canonical installed policy and its contract test

Apply `design.md` §1.1: replace item 2's trailing sentence in
`src/brichan/resources/dogfood_v1/policy/operating-principles.md` so all three
phases are mandatory and integration follows the independent `review` worker.
Items 1 and 3–8 stay byte-identical; `bootstrap.md` is not edited. Extend
`tests/contract/test_dogfood_policy_contract.py` with assertions that all three
phases are required and that `Skip the`, `bounded edit`, and `only for` are
absent, retaining every existing assertion.

**This step runs first**, because Step 2 states the mandate as fact and
`PRODUCT.md` lines 3–10 give runtime policy precedence. **Two files.**

### Step 2 — Repair `PRODUCT.md`

Apply `design.md` §1.2. **One file.**

### Step 3 — Reconcile lifecycle state across all seven indexed projects

Apply `design.md` §2.1: seven edits in five files — overview line 7 in
`brida-workflow-evaluation` and `brida-model-routing`, a new lifecycle line after
the title in `brida-claude-code-support` and
`brida-repository-structure-refactor`, and `projects/index.md` lines 24, 29, 34
plus the installable-tool `Summary` rewrite. The three already-correct overviews
and the four already-correct index `- Status:` lines stay byte-identical.
**Five files.**

### Step 4 — Repair installable-tool durable memory

Apply `design.md` §2.2: replace `current-state.md` (≤ 80 lines,
`Last updated: 2026-08-09`); append the superseding rename decision and mark the
2026-07-29 entry `superseded` without editing its body; add the MEMORY-001 Active
row and the four Completed rows to `tasks.md`; correct the two stale
`references.md` rows. `current-state.md` and the `POLICY-001` row both use
**"mandatory plan/implement/review lifecycle"**. **Four files.**

### Step 5 — Fix the wheel example and extend the release checklist

Apply `design.md` §1.3. **Two files.**

### Step 6 — Add the gate

Implement `scripts/check_project_memory.py` exactly as `design.md` §3 specifies
and no further:

- fixed constants (§3.2) — no config file, no glob, no injectable set;
- the six checks (§3.3) and only those ten check IDs;
- version, changelog, and date handling (§3.4), including the three states that
  count as no valid matching release;
- component-wise `lstat` no-follow resolution with the small internal outcome
  model and the `errno.errorcode.get(...)` fallback (§3.5);
- input failures and precedence (§3.6) — one diagnostic per unavailable input, no
  traceback;
- deterministic sorted output and the `[--root PATH]` CLI (§3.1, §3.7).

Do **not** implement: unindexed-project detection, a backticked-path validator, an
sdist rule, a repository-wide Markdown scan, or a configurable declared-path
subsystem. If any of those seems necessary, report it rather than adding it.

Write `tests/unit/test_check_project_memory.py` covering the `design.md` §4
categories — the three golden fixtures asserting exact ordered
`(path, check, detail)` triples, and every other category asserting paths plus
check IDs and byte-identical repetition — then
`tests/contract/test_project_memory_contract.py`. No test asserts a
`(path, check)` set as its whole oracle, and no test or docstring claims coverage
of every outcome, node type, `errno`, or caller. **Three new files.**

### Step 7 — Wire and verify

Add the `memory-check` Makefile target (`.PHONY`, `help`, and the `check`
prerequisite list after `dossiers`) and the `config/repository-paths.json`
`entries` item plus `Makefile` reference. Run the verification commands, update
`tasks.md`, and write the receipt. **Two files.**

## Authorized implementation paths

- `src/brichan/resources/dogfood_v1/policy/operating-principles.md`
- `tests/contract/test_dogfood_policy_contract.py`
- `PRODUCT.md`
- `docs/guides/installable-dogfood.md`
- `projects/index.md`
- All seven `projects/<slug>/overview.md` files — authorized so the implementer
  may verify each and record the three needing no change; only the four in
  Step 3 are expected to differ
- `projects/brida-installable-tool/current-state.md`, `decisions.md`,
  `tasks.md`, `references.md`
- `projects/brida-installable-tool/handoffs/PYPI-001/release-checklist.md`
- `scripts/check_project_memory.py` (new)
- `tests/unit/test_check_project_memory.py` (new)
- `tests/contract/test_project_memory_contract.py` (new)
- `Makefile`, `config/repository-paths.json`
- `projects/brida-installable-tool/handoffs/MEMORY-001/receipt.md` and the
  coordinator- and reviewer-owned dossier artifacts, written by their owners.
  `plan-review.md` version 5 is immutable; a fresh reviewer replaces it with a
  review of plan version 6.

Inspection established that no other existing test must change:
`tests/integration/test_installed_dogfood.py` line 205 asserts that the policy
resource is packaged rather than its content, and no test pins a golden hash of
any policy resource. `bootstrap.md` is already correct and is not authorized.

## Exclusions

Excluded files: `VERSION`, `pyproject.toml`, released `CHANGELOG.md` entries,
`config/model-routing.json`, `config/pypi-readme.json`, `README_PYPI.md`, every
file under `projects/*/handoffs/` other than this dossier and the PYPI-001
release checklist, every non-`overview.md` memory file of the six other projects,
`evals/`, `metrics/`, `.github/workflows/`, the receipt and task-dossier
validators, and every `docs/policy/` file. `src/` is excluded **except**
`src/brichan/resources/dogfood_v1/policy/operating-principles.md`; `tests/` is
excluded except `tests/contract/test_dogfood_policy_contract.py` and the two new
test files.

Excluded actions: version bump, tag, `git push`, PR creation, publishing,
TestPyPI or PyPI upload, network access, credential or secret access, permission
broadening, sub-agent spawning, renaming `projects/brida-*` slugs, rewriting
recorded history, and **deleting any generated artifact**.

Excluded checker scope, restated so it cannot creep back in: unindexed-project
detection; backticked-path validation in `current-state.md`; any sdist filename
rule; any repository-wide or `docs/**` Markdown scan; and any externally
configurable declared-path subsystem.

## Acceptance criteria

1. The packaged policy has no skip-plan exception, requires all three phases, and
   is otherwise byte-identical; `bootstrap.md` is unchanged;
   `tests/contract/test_dogfood_policy_contract.py` proves both and passes; no
   other existing test file changed; Step 1 preceded Step 2.
2. `PRODUCT.md` matches `design.md` §1.2; `current-state.md` and the
   `POLICY-001` row both read "mandatory plan/implement/review lifecycle";
   `CHANGELOG.md` is unchanged.
3. Step 3 produced exactly seven lifecycle edits in exactly five changed files;
   the three already-correct overviews and four already-correct index
   `- Status:` lines are byte-identical; all seven overviews carry exactly one
   lifecycle field with the `design.md` §2.1 values, each matching its index
   entry.
4. `current-state.md` is ≤ 80 lines with `Last updated: 2026-08-09`;
   `decisions.md` gained exactly one entry and the superseded entry's body is
   byte-identical apart from its `Status:` line; `tasks.md` gained the Active row
   and four Completed rows; the two `references.md` rows are corrected; the guide
   and release checklist match `design.md` §1.3.
5. The checker implements `design.md` §3 and nothing else; the excluded checker
   scope is absent from the source.
6. `python3 scripts/check_project_memory.py` exits `0` on the repaired tree, and
   `--root PATH` runs it against a fixture tree; exit codes are only `0` or `1`.
7. Every `design.md` §4 category has at least one passing test; the three golden
   fixtures assert exact ordered `(path, check, detail)` triples; no test uses a
   pair set as its whole oracle; no test or docstring claims exhaustive coverage
   of outcomes, node types, `errno` values, or callers.
8. No input state produces a traceback, and an injected unknown numeric `errno`
   yields a stable deterministic string.
9. Repeated runs over an identical tree produce byte-identical stdout and stderr;
   the suite proves no writes and no subprocess.
10. `make memory-check`, `make path-check`, `make test-contract`, and `make check`
    pass on observed current state; unrelated pre-existing failures are reported
    with output, not repaired and not deleted.
11. A fresh independent reviewer returns `PASS` on plan version 6.

## Verification commands

```bash
git diff --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.contract.test_dogfood_policy_contract -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_project_memory.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.unit.test_check_project_memory -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.contract.test_project_memory_contract -v
PYTHONDONTWRITEBYTECODE=1 make memory-check
PYTHONDONTWRITEBYTECODE=1 make path-check
PYTHONDONTWRITEBYTECODE=1 make test-contract
PYTHONDONTWRITEBYTECODE=1 make dossiers
PYTHONDONTWRITEBYTECODE=1 make receipts
PYTHONDONTWRITEBYTECODE=1 make check
grep -n "Skip the\|bounded edit\|only for" src/brichan/resources/dogfood_v1/policy/operating-principles.md
grep -c "Lifecycle status" projects/*/overview.md
grep -n "^- Status:" projects/index.md
grep -n "mandatory plan/implement/review lifecycle" projects/brida-installable-tool/current-state.md projects/brida-installable-tool/tasks.md
awk 'END {print NR}' projects/brida-installable-tool/current-state.md
git diff --stat -- src/brichan/resources/dogfood_v1/policy/
git diff --name-only -- projects/ src/ tests/
git diff --stat
```

The twelfth command must return **no match** — direct proof the skip-plan
exception is gone. The seventeenth must show exactly one changed file under the
packaged policy directory.

`make check` runs against the working tree **as observed**. No removal of
`dist/`, `build/`, `src/brichan.egg-info/`, or any other generated artifact is
authorized; a pre-existing artifact causing a failure is reported with output,
attributed as pre-existing and unrelated, and left in place.

## Remediation and escalation

- **A check outside `design.md` §3.3 seems necessary.** Report it; do not add it.
  Three consecutive reviews were spent on scope the accepted objective never
  requested, and re-adding it is the failure mode this version exists to end.
- **The packaged-policy edit would touch more than item 2's final sentence.**
  Stop and report; items 1 and 3–8 and `bootstrap.md` are byte-identity
  obligations.
- **A test beyond `test_dogfood_policy_contract.py` fails after Step 1.** Report
  before changing anything: a second failure falsifies the inspection rather than
  authorizing a wider edit.
- **A fixture's expected result cannot be derived from `design.md` §3.3–§3.6.**
  That is a specification defect. Report it and stop; do not adjust the fixture
  to match an implementation.
- **A lifecycle value looks wrong.** `brida-repository-structure-refactor` and
  `brida-model-routing` as `complete` are the coordinator's determination while
  both still hold handoff directories. Escalate rather than writing a different
  value.
- **Step 3 touches more than five files.** Stop and report; the already-correct
  records must not be edited to satisfy a count.
- **`make check` fails for an unrelated reason.** Report with output; do not
  repair inside this task and do not delete artifacts to make it pass.
- **Escalate to the coordinator** when local evidence conflicts materially with
  the accepted plan; when the skip-plan exception turns out to be intentional, in
  which case only the user may revise the accepted intent and this plan must not
  weaken `PRODUCT.md` alone; when a repair would require editing a receipt,
  `CHANGELOG.md`, or another recorded-history file; or when a lifecycle value
  appears wrong.
- **Never** report the task done on a gate never observed failing. The
  lifecycle-disagreement fixture, the unsafe-path golden fixture, the
  older-version-only changelog fixture, and the no-match `grep` above are the
  mandatory demonstrations.

## Evidence

- `plan-review.md` version 5 (verdict `CHANGES REQUIRED`, reviewing session
  `019fe73b-8a92-7a01-8e05-7a62536e1faf`, worker
  `brichan-memory-001-plan-review-v5` / `w34:p7`, route `review`, model
  `gpt-5.6-sol`, effort `high`) findings H1, M1, M2, M3, and L1 — the inputs the
  disposition table answers.
- The policy contradiction in three files:
  `src/brichan/resources/dogfood_v1/policy/operating-principles.md` lines 10–12;
  `bootstrap.md`, unqualified; `CHANGELOG.md` `[0.11.0]` lines 14–24.
  `PRODUCT.md` lines 3–10 give runtime policy precedence, which is why Step 1
  precedes Step 2. `tests/contract/test_dogfood_policy_contract.py` lines 27–43
  are where Step 1's assertions belong;
  `tests/integration/test_installed_dogfood.py` line 205 asserts packaging
  membership only.
- Lifecycle coordinates: `projects/index.md` lines 24, 29, 34;
  `projects/brida-workflow-evaluation/overview.md` line 7 and
  `projects/brida-model-routing/overview.md` line 7; the
  title-then-`## Objective` opening of
  `projects/brida-claude-code-support/overview.md` and
  `projects/brida-repository-structure-refactor/overview.md`; canonical `Memory:`
  values with terminal slashes at lines 6, 11, 16, 21, 26, 31, 36.
- `VERSION` = `0.11.0`; `CHANGELOG.md` `## [Unreleased]` followed by
  `## [0.11.0] - 2026-08-03`, so a valid matching release exists today and Step
  4's `Last updated: 2026-08-09` satisfies its lower bound; `PRODUCT.md` lines
  12, 90–91, 198, 202, 205–211; `docs/guides/installable-dogfood.md` line 67, the
  only `brichan-X.Y.Z` token in the active-document set;
  `projects/brida-installable-tool/current-state.md` lines 3, 58, 127 (139 lines);
  `decisions.md` lines 5, 34, 73–88;
  `handoffs/PYPI-001/release-checklist.md` lines 3–8 and 26–47.
- Wiring and safety precedent: `Makefile` `check` prerequisite list and `help`
  block; `config/repository-paths.json`'s `Makefile` pairing for
  `scripts/check_repository_paths.py`; that script's `main()` exit contract; and
  `src/brichan/contracts/task_dossier/validation.py` lines 766–790 for the
  lexical-plus-`lstat` no-follow walk.
- Policy bounds: `docs/policy/memory-policy.md` (80-line `current-state.md`,
  three-line index entry, append-only `decisions.md`); `PRODUCT.md` §8's boundary
  rule keeping the checker in `scripts/`; `docs/workflows/task-dossier.md`
  level-2 evidence depth and authorization gates.

## Uncertainty

- **Narrowing is a trade, not a free win.** Dropping the backticked-path
  validator means nothing mechanically prevents `scripts/install-brida` from
  reappearing in `current-state.md` after Step 4 fixes it, and dropping
  unindexed-project detection means a new unindexed project directory produces no
  diagnostic. Both were planner additions rather than accepted requirements; both
  are now open risks the coordinator may reopen as separate tasks.
- **The packaged-policy repair ships unreleased**, with no version bump and no
  `CHANGELOG.md` entry, both excluded here. Hash-managed `.brichan/` state
  observes a changed resource on deliberate re-init. Whether to bundle it into a
  `0.11.1` release is a coordinator decision this plan cannot make.
- `design.md` §3.5's outcome model is deterministic by construction but is not
  proven by fixture for every node type or `errno`; version 6 says so instead of
  claiming otherwise.
- `Plan status` records `accepted` at version 6 because the user accepted
  `MEMORY-001-UPSTREAM` and this artifact carries that decision forward.
  Versions 1–5 were each reviewed `CHANGES REQUIRED`; version 6 requires a fresh
  independent review. `plan-review.md` version 5 is preserved unchanged until
  that reviewer replaces it, so the validator reports one expected linkage
  diagnostic on it (`Reviewed plan version` `5` against plan version `6`),
  alongside the two `index.md` linkage diagnostics that clear when the
  coordinator records `MEMORY-001-PLAN` / `6`.
- Two of the seven accepted lifecycle values are the coordinator's determination,
  not facts verified here; `lifecycle-agreement` cannot prove them, so the
  contract test's by-name assertion carries that weight.
- The canonical receipt
  `projects/brida-installable-tool/handoffs/MEMORY-001/receipt.md` still does not
  exist, so the dossier cannot validate as complete regardless of these
  artifacts' quality. Creating it is coordinator work outside this task's
  authorized paths.
