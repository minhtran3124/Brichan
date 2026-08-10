# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `PYPI-003`
- Task level: `2`
- Artifact: `plan`
- Artifact version: `5`
- Origin: `planner:2026-08-10-pypi-003-plan-v5`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `6da0f1e7-0d9e-4881-8361-312f586c3487`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `PYPI-003-PLAN`
- Plan status: `accepted`

## Claim or decision

Execute the public PyPI rendering flip in five bounded steps over the same
six implementation files, with fresh unauthenticated verification before the
first edit, triple test pinning of the public contract whose shipped-config
assertion is itself the automated revert gate, gate closure in both
durable-memory records, and a two-phase lifecycle in which Phase A
authorizes implementation and Phase B finalizes — with `code-review.md`
authored solely by the independent reviewer and the receipt finalized before
the final full `make check`, never after it. No remote mutation, release,
version bump, or changelog change occurs at any step. Plan versions 1
through 4 are superseded.

## Version 2 amendments

Version 1 left the stale `PRODUCT.md:230` line as an open coordinator
decision. The coordinator decided on 2026-08-10 to include its one-line
removal as truth reconciliation for the same requested gate (`options.md`
D3). Step 4 gained the `design.md` §4.2 edit.

## Version 3 amendments

Version 3 closes every plan-review version 2 finding without changing the six
implementation files.

## Version 4 amendments

Version 4 closes plan-review version 3: the lifecycle splits into Phase A
(acceptance and authorization, including the schema-v2 accepted receipt with
pending evidence and the exact one-line `references.md` pointer) and Phase B
(finalization after code-review PASS); both probes lead with `curl -q` with
no auth headers and no netrc; the manual temporary-copy negative procedure
and its acceptance criterion are removed — the permanent shipped-config test
asserting `public_repository is True` is the automated revert gate; and
review identity targets `PYPI-003-PLAN` version 4. The six implementation
files and all exclusions are unchanged.

## Version 5 amendments

Version 5 closes plan-review version 4, in Phase B only: the independent
code reviewer alone writes the complete `code-review.md` (content, `passed`
phase state, verdict) and the coordinator only verifies and projects it into
`index.md` and the receipt, never editing it; Phase B runs in order —
evidence verification, then project memory/tasks/index/pr-desc/metrics and
other projections, then pane cleanup (keeping a reporting pane), then
receipt finalization to reviewed `PASS` with actual evidence, then the final
full `make check` last on the finalized receipt and tree. Nothing claims
later evidence in advance. Phase A, the exact receipt path, `curl -q`
probes, the automated regression gate, the six implementation files, and all
exclusions are unchanged; review identity targets `PYPI-003-PLAN` version 5.

## Finding disposition

| Finding | Raised in | Status |
|---|---|---|
| H1 — acceptance named the superseded plan version | plan-review v2 | Closed: all review references name the current plan version — version 5 as of this revision; plan-review, index accepted-plan identity, and receipt plan identity must agree (`requirements.md` R7a) |
| H2 — authorized lifecycle could not reach the full gate | plan-review v2 | Closed: the two-phase coordinator lifecycle authorizes every needed transition — Phase A accepts and authorizes, Phase B finalizes; reviewers make none of them (`design.md` §5) |
| M1 — `references.md` exclusion broke the receipt contract | plan-review v2 | Closed: exactly one coordinator-owned pointer line reading exactly `projects/brida-installable-tool/handoffs/PYPI-003/receipt.md`, added in Phase A (`options.md` D4) |
| M2 — `gh api` is authenticated | plan-review v2 | Closed: Step 1 uses `curl -q` (first argument) against `https://api.github.com/repos/minhtran3124/Brichan` with no auth headers and no netrc, same field assertions, sanitized evidence (`design.md` §1) |
| M3 — no executable negative verification | plan-review v2 | Closed in v3 by a manual temporary-copy procedure; plan-review v3 found that matrix self-imposed. v4 closes it structurally: the permanent shipped-config test asserts `public_repository is True`, so a revert fails the normal automated focused run (`design.md` §6) |
| L1 — stale 74-line baseline | plan-review v2 | Closed: corrected to 79 lines; the edit keeps 79 ≤ 80 (`design.md` §4.1) |

### Step 1 — Verify, fresh and unauthenticated

Run the two read-only probes in `design.md` §1 — both leading with
`curl -q` as the first argument, against
`https://api.github.com/repos/minhtran3124/Brichan` and the raw image, with
no auth headers, no tokens, and no netrc — and
capture the sanitized four-field output for the receipt. Proceed only on a
full match (`public`/`private: False`/`main`; `200 image/png`). On any
mismatch: stop with zero files changed and escalate. **Zero files.**

### Step 2 — Flip and regenerate

Apply `design.md` §2: change `config/pypi-readme.json` line 5 to
`"public_repository": true`, then run
`PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_pypi_readme.py`. Confirm with
`git diff` that the config changed on exactly one line and `README_PYPI.md`
gained exactly the two expected lines. Any other diff: stop and escalate.
**Two files.**

### Step 3 — Pin the contract

Add the three tests of `design.md` §3, verbatim in intent: the shipped-config
public pin (unit), the committed-description hero-line pin (contract), and
the PKG-INFO raw-URL pin (contract). Delete or weaken nothing. **Two files.**

### Step 4 — Close the gate in both durable-memory records

Apply `design.md` §4.1 to
`projects/brida-installable-tool/current-state.md`: remove the completed
URL/image gate bullet (lines 56–58), append the one verified-public-setup
bullet to "Distribution and release", leave the two other open gates and all
other content byte-identical, keep ≤ 80 lines. Apply `design.md` §4.2 to
`PRODUCT.md`: delete the single line at 230 ("Next, in order" item 3) with
every other line byte-identical. **Two files.**

### Step 5 — Verify and hand off

The implementer runs the verification commands below and reports the
evidence — Step 1 sanitized probe output, diff evidence, test results — to
the coordinator. The revert case needs no separate step: the shipped-config
pin asserts `public_repository is True`, so the normal focused run is the
automated negative gate (`design.md` §6). **Zero additional implementation
files.**

Steps 2–4 run only after the coordinator has completed lifecycle **Phase A**
(`design.md` §5.1) — plan accepted, planning artifacts `passed`, schema-v2
accepted receipt created with pending evidence, the exact `references.md`
pointer line added, task set to implementing. After Step 5's evidence, the
independent code reviewer alone writes the complete `code-review.md` —
content, `passed` phase state, and verdict; the coordinator never edits it.
On the reviewer's `PASS`, the coordinator performs **Phase B** in the
`design.md` §5.2 order: verify evidence; update current project memory,
`tasks.md`, `index.md`, `pr-desc.md`, the metrics row, and other
projections; close Brichan-owned idle/done panes except a reporting pane;
only then finalize the receipt to reviewed `PASS` with the actual evidence;
and run the final full `make check` last, on the finalized receipt and tree.
Reviewers make no lifecycle transitions.

## Authorized implementation paths

- `config/pypi-readme.json` — the one-line flip
- `README_PYPI.md` — generator output only, never hand-edited
- `tests/unit/test_build_pypi_readme.py` — one added test
- `tests/contract/test_packaging_metadata.py` — two added tests
- `projects/brida-installable-tool/current-state.md` — gate closure per
  `design.md` §4.1
- `PRODUCT.md` — the single deleted line per `design.md` §4.2, authorized by
  the coordinator's 2026-08-10 decision
The six paths above are the complete implementation surface, unchanged since
version 2.

## Coordinator-owned lifecycle paths (two phases, per `design.md` §5)

Phase A (after plan-review PASS on version 5; authorizes implementation):

- The five planning artifacts' phase-state fields and `plan.md`'s Plan status
  (`active` → `passed`; `draft` → `accepted`) — coordinator only
- `request.md`, `index.md`, `client-follow-up-questions.md` — completed as
  applicable
- `projects/brida-installable-tool/handoffs/PYPI-003/receipt.md` — new,
  mandatory, schema-v2 accepted receipt recording `PYPI-003-PLAN` version 5
  with downstream evidence pending
- `projects/brida-installable-tool/references.md` — exactly one appended
  pointer line reading exactly
  `projects/brida-installable-tool/handoffs/PYPI-003/receipt.md`, nothing
  else
- `projects/brida-installable-tool/tasks.md` — the `PYPI-003` status cell to
  implementing

Phase B (after implementation and code-review PASS; finalizes, in the
`design.md` §5.2 order):

- `code-review.md` — authored in full by the independent reviewer (content,
  `passed` phase state, verdict); the coordinator never edits it, only
  verifies and projects it into `index.md` and the receipt
- Current project memory, `tasks.md` (status cell to completed), `index.md`,
  `pr-desc.md`, `metrics/runs.jsonl` (one appended row), and other
  coordinator projections — updated first
- Brichan-owned idle/done panes — closed, keeping any pane needed to report
- `receipt.md` — finalized to reviewed `PASS` with the actual evidence,
  only after memory and cleanup are complete
- Final full `make check` — run last, against the finalized receipt and tree

## Exclusions

Excluded files: `packaging/pypi-readme.md`, `scripts/build_pypi_readme.py`,
`pyproject.toml`, `VERSION`, `CHANGELOG.md`, `README.md`,
`config/model-routing.json`, every `src/` and `docs/policy/` file, and every
other project-memory or handoff file not named in the two path lists above.
Within `PRODUCT.md`, only the `design.md` §4.2 line deletion is authorized;
within `references.md`, only the single receipt-pointer line — any wider edit
to either is excluded.

Excluded actions: version bump, tag, `git push`, PR creation or mutation,
release, publish, TestPyPI or PyPI upload, secret or credential access,
permission broadening, sub-agent spawning, and any remote state change. The
only network use is Step 1's two anonymous read-only probes.

## Acceptance criteria

The seven criteria in `requirements.md` govern, summarized: fresh
unauthenticated `curl -q` probes matched and their sanitized output is in
the receipt; the config and description diffs are exactly minimal; the three
pins exist and pass, with the shipped-config assertion serving as the
automated revert gate; the focused suites, `--check`,
`make readme-check`, `make memory-check`, and `make path-check` pass;
`current-state.md` matches `design.md` §4.1 (79 lines, ≤ 80); `PRODUCT.md`
shows exactly one deleted line per §4.2; implementation began only after
lifecycle Phase A, and full `make check` passes when run last in Phase B on
the finalized receipt and tree; and an independent stronger reviewer
(documented Codex Sol high override) returns `PASS` on `PYPI-003-PLAN`
version 5 before implementation, with `code-review.md` authored solely by
the independent reviewer, and with plan-review, index accepted-plan
identity, and receipt plan identity all recording `PYPI-003-PLAN`
version 5 (R7a).

## Verification commands

```bash
git diff --stat -- config/pypi-readme.json README_PYPI.md
git diff -- README_PYPI.md
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_pypi_readme.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.unit.test_build_pypi_readme -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.contract.test_packaging_metadata -v
PYTHONDONTWRITEBYTECODE=1 make readme-check
PYTHONDONTWRITEBYTECODE=1 make test-unit
PYTHONDONTWRITEBYTECODE=1 make test-contract
PYTHONDONTWRITEBYTECODE=1 make memory-check
PYTHONDONTWRITEBYTECODE=1 make path-check
grep -c "raw.githubusercontent.com/minhtran3124/Brichan/main/assets/brichan-hero.png" README_PYPI.md
awk 'END {print NR}' projects/brida-installable-tool/current-state.md
git diff -- PRODUCT.md
grep -c "public repository URL" PRODUCT.md
git diff --name-only
PYTHONDONTWRITEBYTECODE=1 make check   # at completion, after lifecycle Phase B
```

The first grep must report exactly `1`; the awk result must be ≤ 80; the
`PRODUCT.md` diff must show exactly one deleted line and zero added lines,
and its grep must report `0` (grep exits 1 on zero matches — expected);
`git diff --name-only` must list only authorized paths. `make dossiers` (and
therefore full `make check`) stays red until the coordinator's two-phase
lifecycle completes — Phase A lands the acceptance transitions and the
accepted receipt, Phase B finalizes it after code-review PASS; at planning
time the dossier diagnostics are all PYPI-003 scaffold placeholders. That is
lifecycle sequencing, not a defect to work around.

## Remediation and escalation

- **Step 1 mismatch** (repository not public, probe non-200, or content type
  not `image/png`): the evidence contradicts repository configuration — stop
  with zero changes and escalate with captured output.
- **Step 2 diff exceeds the expected two lines**: the simulation is
  falsified — stop and escalate; do not hand-adjust `README_PYPI.md`.
- **Any pre-existing test failure surfaces**: report it with output as
  pre-existing; do not repair, delete artifacts, or widen scope.
- **The `PRODUCT.md` edit would touch more than the one §4.2 line** (the
  surrounding list has drifted, or the line is not found verbatim at its
  recorded location): stop and escalate; byte-identity elsewhere is an
  obligation.
- **Closing the gate appears to require a version bump, release, or any
  product decision beyond the authorized line deletion**: escalate to the
  coordinator; the repository-side closure needs none of these.

## Evidence

- `design.md` §§1–5 and the in-memory simulation showing the exact expected
  `README_PYPI.md` diff with clean `validate` output.
- Baseline (2026-08-10, branch `fix/durable-memory-consistency`, PR 27 open):
  28/28 focused tests pass, `--check` in-sync, dossier validator issues all
  in the PYPI-003 scaffold.
- Task packet: recorded 2026-08-10 GitHub API and anonymous HTTP evidence;
  mandatory receipt path; Level 2 classification because the generated
  description is a public packaging contract.

## Uncertainty

- Reachability at implementation time is re-verified, not assumed; the plan
  cannot guarantee URL availability beyond Step 1's probes.
- The live PyPI page updates only at the next authorized release.
- Whether the sdist-layer pin runs depends on a local setuptools backend
  (existing skip path); the description-layer pin always runs.
