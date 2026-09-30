# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `WFS-A-201`
- Task level: `0`
- Artifact: `plan`
- Artifact version: `3`
- Origin: `planner:2026-09-25-wfs-a-201-plan-v3`
- Owner: `planner`
- Phase state: `active`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `b37a1f86-e9d2-440c-ad44-8a535521fe16`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `WFS-A-201-PLAN-001`
- Plan status: `draft`

## Claim or decision

Execute the rename in one edit and verify it in four bounded steps: verify
the implementation attempt's Techstack Snapshot before any work, apply the
single-line `def` rename of `design.md`, verify neutrality with the
focused module run and `git diff`/`git grep`, then run `make check` plus
the coordinator-ratified layer-by-layer completion gate on both
interpreters and the dossier validator, reporting exactly the four known
expected-red components of this detached worktree and the pending
coordinator/reviewer diagnostics. Version 3 closes all four findings of
plan-review version 1 (verdict `CHANGES REQUIRED` on plan version 2); the
edit, the selected name, and the authorized implementation path are
unchanged from versions 1 and 2.

## Version 3 amendments and findings closure

Plan-review version 1 confirmed the technical core (name accuracy,
neutrality, uniqueness, non-vacuous subtests, TEST-003 by probe) and
raised four findings. Each is closed as follows:

| Finding | Requirement raised | Resolution in version 3 |
|---|---|---|
| H1 (high) — restated criterion 3 not verifiable in the repository; plan and packet criteria disagreed | Record the restatement where later sessions can check it, or add a `tasks.md:29` step with a scope expansion | Closed by the coordinator: the restated criterion ("no reference to the old name outside coordinator-owned project memory and immutable dossier provenance") is now recorded in this dossier's `client-follow-up-questions.md` version 2 (origin `coordinator:2026-09-25-wfs-stage2`). `requirements.md` R3, `design.md`, and this plan cite that artifact instead of a packet relay. The scope is unchanged; `tasks.md:29` remains permitted coordinator-owned residue and is not edited. Remaining coordinator action (recommended below): carry the restated wording into the implementation and code-review packets, which the plan packet for this attempt did not yet do. |
| M1 (medium) — Step 4's expected-failure set was incomplete (`make path-check`, `test_repository_checkout_validates_clean`), turning known redness into spurious escalations | Name both as expected worktree/lifecycle redness alongside `make dossiers` | Step 4 now adopts the coordinator-ratified completion gate verbatim and names all four expected-red components: the two contract failures and `make path-check` (detached-worktree cause) and `make dossiers` plus the `test_repository_checkout_validates_clean` integration failure (in-flight-dossier cause). The remediation rule excludes exactly this list from escalation. All four were re-measured red in this session on 2026-09-25. |
| L1 (low) — the substitute gate run omitted the `check` recipe body | Include `sh -n bin/brichan` | Step 4's layer-by-layer run now ends with `sh -n bin/brichan` (Makefile:76), re-verified passing in this session. |
| L2 (low) — the recorded validator baseline (65 diagnostics) was stale and invited a false mismatch | Say the count falls; prevent misreading a correct result as a discrepancy | The baseline is re-measured (38 diagnostics as of this authoring, distributed `index.md` 28, `code-review.md` 5, `pr-desc.md` 5, none in the five planner-owned artifacts) and Step 4 instructs the implementer to compare the distribution — no diagnostic in any planner-owned artifact, all remaining diagnostics in pending coordinator/reviewer artifacts — never an absolute count, which moves as coordinator artifacts fill. |

Versions 1 and 2 are archived byte-frozen at
`projects/brida-workflow-simplification/handoffs/WFS-A-201/versions/v1/`
and `versions/v2/` (DOSSIER-003).

## Discovered path outside the Techstack scope — resolved

**Prominent, per the packet's acceptance criteria.** The old test name has
exactly two tracked references
(`git grep -n test_prose_rejects_control_and_markup_characters`,
re-measured 2026-09-25 in this session):

- `tests/unit/test_techstack_markdown.py:565` — the rename target, in
  scope.
- `projects/brida-workflow-simplification/tasks.md:29` — the S2-1 task-row
  description in coordinator-owned project memory, **not** in the
  Techstack scope paths
  (`projects/brida-workflow-simplification/handoffs/WFS-A-201`,
  `tests/unit/test_techstack_markdown.py`).

Coordinator resolution (2026-09-25, option (b), recorded in this dossier's
`client-follow-up-questions.md` version 2): `tasks.md` stays out of scope,
no Techstack re-resolution occurs, and the acceptance criterion is
restated as "no reference to the old name remains outside
coordinator-owned project memory and immutable dossier provenance". The
`tasks.md:29` row is coordinator-owned project memory and is therefore
permitted residue; the implementer must not edit it.

Untracked, gitignored dossier files (this dossier's `request.md` and these
planning artifacts) necessarily quote the old name as provenance; `git
grep` does not search them and they are not references to remove.

### Step 1 — Verify before work

Run the Techstack verify command from the implementation task packet (via
`bin/brichan` from the worktree root) and proceed only on `match`; reread
the six selected rule files named in the Snapshot. This planning attempt's
verification returned `match` on 2026-09-25 against sha256
`e184239fb498fccb40e729abd074ba34dcf36a15c18160385d66a4df249cc34d` before
any other work.

### Step 2 — The edit

Apply `design.md`: at `tests/unit/test_techstack_markdown.py:565`, rename
the `def` from `test_prose_rejects_control_and_markup_characters` to
`test_prose_rejects_pipe_and_category_c_characters`. One line; comment,
subtests, and helpers byte-identical. **One file.**

### Step 3 — Neutrality verification

```
git diff -- tests/unit/test_techstack_markdown.py
git grep -n test_prose_rejects_control_and_markup_characters
git grep -n test_prose_rejects_pipe_and_category_c_characters
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.unit.test_techstack_markdown -v
```

Expected: the diff is exactly one removed and one added `def` line; the
old-name grep hits only `projects/brida-workflow-simplification/tasks.md:29`,
the permitted coordinator-owned residue under the restated criterion; the
new-name grep hits only the renamed `def`; the module passes 47/47. Any
other diff line or failure: stop and escalate, per the remediation section.

### Step 4 — Gates and report

First, the packet-form gate and the dossier validator:

```
PYTHONDONTWRITEBYTECODE=1 make check
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py projects
```

Expected `make check` outcome in this detached worktree: the run stops in
`test-contract` with exactly the two known worktree-only failures in
`tests/contract/test_repository_paths.py` ("unclassified root files:
.git"), which are reported, never fixed. `make check` never reaches the
later gate components because `check` runs them only after `test`
succeeds (Makefile:75), so the ratified layer-by-layer gate follows.

Then the coordinator-ratified completion gate for detached worktrees
(`client-follow-up-questions.md` version 2), with
`PYTHONDONTWRITEBYTECODE=1` throughout — once on the 3.10 shell
interpreter, and again with `PYTHON=/opt/homebrew/bin/python3.14`:

```
make test-unit
make test-contract
make test-integration
make techstack-eval
make metrics receipts dossiers memory-check path-check readme-check phase5-preflight package-check
sh -n bin/brichan
```

The `techstack-eval` recipe invokes bare `python3` and does not follow
`PYTHON=` (Makefile:40), so the 3.14 pass runs the eval directly:
`PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 -m unittest
evals.techstack_context_v1.test_cases`.

Expected red, on both interpreters, reported and never fixed:

- `make test-contract`: exactly the two
  `tests/contract/test_repository_paths.py` failures, and
  `make path-check`: exit 1 — all "unclassified root files: .git",
  detached-worktree cause (`.git` is a file here, not a directory).
- `make dossiers`: nonzero, and `make test-integration`: exactly
  `tests/integration/test_task_dossier_workflow.py`
  (`test_repository_checkout_validates_clean`) — both caused by this
  in-flight dossier's pending coordinator- and reviewer-owned artifacts
  (`index.md`, `code-review.md`, `pr-desc.md`, absent `receipt.md`).

Everything else must be green, including `make test-unit` (with the
renamed test), `make techstack-eval` (56 tests), `make metrics receipts
memory-check readme-check phase5-preflight package-check`, and
`sh -n bin/brichan`. Any other failure is a defect: diagnose, report,
escalate — do not fix.

Validator interpretation: the report must show **no diagnostic for the
five planner-owned WFS-A-201 artifacts** (`requirements.md`, `brief.md`,
`options.md`, `design.md`, `plan.md`). Remaining diagnostics sit in
pending coordinator- and reviewer-owned artifacts and are listed by file
in the report. Compare the distribution, never an absolute count: the
total (38 at this authoring) moves as coordinator artifacts fill, and a
falling count is the expected direction, not a discrepancy.

## Authorized implementation paths

- `tests/unit/test_techstack_markdown.py` — the one-line rename.

Everything else is excluded, including `src/`, `docs/`, configuration,
packaged resources, `projects/brida-workflow-simplification/tasks.md`
(kept out of scope by the coordinator's option (b) decision), the archived
`versions/v1/` and `versions/v2/` copies (byte-frozen per DOSSIER-003),
and this dossier's coordinator- and reviewer-owned artifacts. No commit,
branch, push, or remote action; changes stay uncommitted.

## Remediation and escalation

- Any diff beyond the single `def` line: revert and re-apply; the edit is
  mechanical.
- Any failure outside the four expected-red components named in Step 4
  (two contract failures + `path-check`; `dossiers` +
  `test_repository_checkout_validates_clean`): diagnose before changing
  anything; a failure caused by the rename is impossible unless the name
  collided (it does not; `options.md`) — treat any such failure as
  pre-existing, report it, and escalate rather than fix. The four named
  components themselves are reported as expected and are **not**
  escalations.
- No recorded ambiguity remains; the version 1 `tasks.md` question is
  closed by the coordinator's option (b) decision in
  `client-follow-up-questions.md` version 2.

## Follow-up recommendations to the coordinator (non-blocking)

- **Reissue the restated criterion.** The plan packet for this attempt
  still carried the strict wording of criterion 3 ("anywhere in the
  repository") beside the instruction to apply
  `client-follow-up-questions.md` version 2, which restates it. Per
  plan-review H1, the implementation and code-review packets should carry
  the restated wording so neither applies the strict form.
- **Record the sibling stale comment as its own follow-up row.**
  `tests/unit/test_techstack_markdown.py:347-351`
  (`test_the_title_class_is_wider_than_the_prose_class`) still claims a
  title "may carry the markup characters a Scope or Verification bullet
  may not"; after the same P6a amendment only the `Title | t` fixture
  value is prose-exclusive. Same class as TECHSTACK-002 stage-2 `L3`; out
  of scope here under criterion 2.
- **Coverage debt, recorded not acted on:** the category-C subtest
  instantiates only `Cc` (U+0085); `Cf`, `Co`, `Cs`, `Cn` are unexercised
  though `_is_prose` rejects the whole category. Widening the fixture
  would change assertions and is forbidden by criterion 2. Separately,
  nothing pins a test name to its assertions, so name drift like this
  task's remains invisible to the suite; worth a follow-up only if the
  pattern recurs.

## Acceptance criteria

The four criteria of `requirements.md` version 3 govern: name accuracy
(R1), a diff of exactly one `def` line (R2), recorded `git grep` evidence
with no reference to the old name outside coordinator-owned project memory
and immutable dossier provenance — concretely, only the permitted
`tasks.md:29` residue (R3) — and the ratified two-interpreter gate with
exactly the four expected-red components plus the planner-clean validator
report (R4).

## Evidence

- Baseline re-measured 2026-09-25 in this session (Python 3.10.11):
  focused module 47/47 OK; `PYTHONDONTWRITEBYTECODE=1 make check` stops in
  `test-contract` with exactly the two known
  `tests/contract/test_repository_paths.py` failures; `make path-check`
  exits 1 ("unclassified root files: .git"); `make test-integration` 222
  tests, 1 failure (`test_repository_checkout_validates_clean`); `make
  techstack-eval` 56/56 OK; `make dossiers` 38 diagnostics (`index.md`
  28, `code-review.md` 5, `pr-desc.md` 5, none planner-owned); `sh -n
  bin/brichan` exits 0; `git status --short` empty before this plan
  set's writes.
- `git grep -n test_prose_rejects_control_and_markup_characters` baseline:
  exactly `tests/unit/test_techstack_markdown.py:565` and
  `projects/brida-workflow-simplification/tasks.md:29`; the new name and
  `test_prose_rejects_pipe` prefix return no hit.
- `projects/brida-workflow-simplification/handoffs/WFS-A-201/plan-review.md`
  version 1 (verdict `CHANGES REQUIRED` on plan version 2; findings H1,
  M1, L1, L2 closed above) and
  `projects/brida-workflow-simplification/handoffs/WFS-A-201/client-follow-up-questions.md`
  version 2 (the coordinator's recorded option (b) decision and ratified
  completion gate).
- Techstack Snapshot pointer:
  `projects/brida-workflow-simplification/handoffs/WFS-A-201/snapshots/attempt-plan-3-e184239fb498fccb40e729abd074ba34dcf36a15c18160385d66a4df249cc34d.snapshot.json`
  (sha256
  `e184239fb498fccb40e729abd074ba34dcf36a15c18160385d66a4df249cc34d`),
  verify status `match` on 2026-09-25 before any other work; acknowledged
  Context IDs `general`, `policy`, `policy-dossiers`, `python`,
  `python-tests`, `root`; scope paths as listed in the discovered-path
  section; all six selected rule files read in full.

## Uncertainty

- `Effective effort` is recorded as `high`, the effort
  `config/model-routing.json` configures for the `plan` route; this
  session surfaced no per-session effort value to confirm it directly.
  The recorded route and model are what actually ran.
- The plan packet for this attempt carried the strict criterion 3 wording
  beside the instruction to apply `client-follow-up-questions.md`
  version 2; this plan treats the coordinator's recorded answer as
  governing and flags the packet reissue above. No other uncertainty
  remains: the version 1 discovered-path question is closed by the
  recorded option (b) decision, and every Step 4 expectation was
  re-measured in this worktree rather than inherited.
