# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `PYPI-003`
- Task level: `2`
- Artifact: `brief`
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

## Claim or decision

The repository is now publicly readable, so the PyPI long description no longer
needs to strip its hero image. The task is a designed one-line migration —
flip `public_repository` in `config/pypi-readme.json`, regenerate
`README_PYPI.md`, pin the shipped public mode and the exact anonymous raw hero
URL in tests, and close the corresponding gate in both durable-memory records
(`current-state.md` and the completed `PRODUCT.md` "Next, in order" item) —
with no release, remote mutation, or version bump.

## Version 2 amendments

Version 1 left the stale `PRODUCT.md:230` line ("Next, in order" item 3,
naming this same gate) as an open coordinator decision. The coordinator
decided on 2026-08-10 to include its one-line removal in this task as truth
reconciliation for the same requested gate, not a product-direction change.
Version 2 folded that into scope.

## Version 3 amendments

Plan-review version 2 returned `CHANGES REQUIRED` with findings H1–L1.
Version 3 closes them all without touching the six public-rendering
implementation paths: every review reference now names `PYPI-003-PLAN`
version 3 with required identity agreement across plan-review, index, and
receipt; the coordinator's post-PASS lifecycle transitions are explicitly
authorized (reviewers never make them); `references.md` gains exactly one
coordinator-owned receipt pointer; the repository probe is an unauthenticated
`curl`, not `gh api`; an executable offline temporary-copy negative procedure
proves the revert case; and the `current-state.md` baseline is corrected to
79 lines.

## Version 4 amendments

Plan-review version 3 returned `CHANGES REQUIRED`. Version 4 closes it: the
lifecycle becomes two coordinator-owned phases — Phase A after plan-review
PASS accepts the plan, marks the planning artifacts passed, creates the
schema-v2 accepted receipt with evidence pending, adds the exact one-line
`references.md` pointer, and sets the task to implementing, which is what
authorizes implementation; Phase B after implementation and code-review PASS
finalizes the receipt to reviewed PASS and completes the remaining artifacts,
metrics, memory, validation, and pane closure. Both probes lead with
`curl -q` (no auth headers, no netrc, sanitized fields). Version 3's manual
temporary-copy negative procedure is removed as self-imposed: the permanent
shipped-config test directly asserts `public_repository is True`, so a revert
fails the normal automated focused run. Review targets `PYPI-003-PLAN`
version 4. The six implementation paths and all exclusions are unchanged.

## Version 5 amendments

Plan-review version 4 returned `CHANGES REQUIRED` on Phase B only. Version 5
corrects it: the independent code reviewer alone writes the complete
`code-review.md` (content, `passed` phase state, verdict) and the
coordinator only verifies and projects it, never edits it; Phase B then runs
in order — verify evidence, update project memory/tasks/index/pr-desc/
metrics and other projections, close Brichan-owned idle/done panes except a
reporting pane, only then finalize the schema-v2 receipt to reviewed `PASS`
with actual evidence, and run the final full `make check` last on the
finalized receipt and tree. Nothing claims later evidence in advance.
Phase A, the exact receipt path, the `curl -q` probes, the automated
regression gate, the six implementation paths, and all exclusions are
preserved; review targets `PYPI-003-PLAN` version 5.

## Problem

- The 0.5.0 PyPI page shipped `assets/brichan-hero.png` as a relative target
  and rendered a broken image. The fix at the time was to derive the PyPI
  description from `packaging/pypi-readme.md` and, while the repository was
  private, drop relative images entirely (`scripts/build_pypi_readme.py`
  module docstring, lines 3–17).
- `config/pypi-readme.json` still says `"public_repository": false` (line 5),
  so the committed `README_PYPI.md` carries no hero image even though the
  correct `asset_base_url` and `link_base_url` are already configured
  (lines 6–7).
- Direct evidence recorded on 2026-08-10: the GitHub API reports
  `https://github.com/minhtran3124/Brichan` with visibility PUBLIC,
  `private: false`, default branch `main`; anonymous HTTP probes return 200
  for the repository URL and for
  `https://raw.githubusercontent.com/minhtran3124/Brichan/main/assets/brichan-hero.png`
  with content type `image/png`.
- `projects/brida-installable-tool/current-state.md` lines 56–58 still list
  confirming the public URL and fixing the PyPI image as an open gate.
- No current test pins the shipped rendering mode: the suite proves both modes
  against synthetic configs and proves README/description sync, but a silent
  revert of `public_repository` to `false` would regenerate cleanly and pass.

## Outcome

1. `config/pypi-readme.json` has `"public_repository": true`; base URLs are
   unchanged.
2. `README_PYPI.md` is regenerated and differs from the committed version by
   exactly one restored line (plus its separating blank line):
   `![Brichan coordinating a team of AI workers](https://raw.githubusercontent.com/minhtran3124/Brichan/main/assets/brichan-hero.png)`.
3. Focused offline regressions pin the shipped public mode, the exact hero URL
   in the committed description, and the exact hero URL in the built sdist's
   `PKG-INFO`.
4. The completed URL/image gate is removed from `current-state.md`, the
   verified public setup is recorded there as current state, and the two
   unrelated open gates are preserved.
5. The completed "Next, in order" item 3 (`PRODUCT.md:230`) is removed as a
   single deleted line; items 1 and 2 and every other `PRODUCT.md` line are
   byte-identical.

## Constraints

- Bounded file surface: `config/pypi-readme.json`, `README_PYPI.md` (generated
  only — never hand-edited), `tests/unit/test_build_pypi_readme.py`,
  `tests/contract/test_packaging_metadata.py`,
  `projects/brida-installable-tool/current-state.md`, `PRODUCT.md` (one
  deleted line), plus the coordinator-owned two-phase lifecycle records
  (`tasks.md` status cell, mandatory schema-v2 receipt, one exact
  `references.md` receipt-pointer line, metrics row, dossier artifacts and
  their transitions).
- `packaging/pypi-readme.md` and `scripts/build_pypi_readme.py` are correct as
  shipped and are not edited.
- No version bump, tag, push, PR mutation, release, publish, changelog change,
  secret access, or remote state change. The only network use is a fresh
  read-only, truly unauthenticated probe pair (`curl -q` leading both
  invocations; no auth headers, no netrc; sanitized fields only) immediately
  before the flip, because recorded reachability is evidence of the past,
  not a guarantee.
- Tests stay offline: they pin URL strings, never fetch them.
- Level 2: the generated description is a public packaging contract, so an
  independent stronger review is required before acceptance.

## Success signal

`python3 scripts/build_pypi_readme.py --check` passes in public mode; the
focused unit and contract suites pass including the three new pins;
`make memory-check` and `make path-check` pass; full `make check` passes at
task completion once the coordinator's Phase B finalization makes the
complete-dossier gate reachable. Negative signal, automated rather than
manual: the permanent shipped-config test directly asserts
`public_repository is True`, so reverting the flip fails the normal focused
test run naturally — no bespoke negative procedure exists.

## Evidence

- `scripts/build_pypi_readme.py:87-116` — `render` drops relative images in
  private mode and rewrites them to `asset_base_url` in public mode;
  `validate` (lines 119–129) forbids surviving relative targets either way.
- `config/pypi-readme.json:5-7` — `public_repository: false` beside the
  already-correct Brichan base URLs.
- `packaging/pypi-readme.md:7` — the root-relative hero
  `![Brichan coordinating a team of AI workers](/assets/brichan-hero.png)`;
  committed `README_PYPI.md` omits it.
- In-memory simulation on 2026-08-10 (read-only, no writes): rendering the
  shipped source with `public_repository: true` yields a description whose
  unified diff against committed `README_PYPI.md` is exactly the restored hero
  line plus one blank line, `validate` returns no errors, and the URL equals
  the anonymously probed one.
- Baseline on branch `fix/durable-memory-consistency` (2026-08-10):
  `tests.unit.test_build_pypi_readme` plus
  `tests.contract.test_packaging_metadata` — 28 tests, all pass — and
  `build_pypi_readme.py --check` reports in-sync.
- `tests/unit/test_build_pypi_readme.py:12-20` — both mode suites use
  synthetic configs, so no existing test pins the shipped mode.

## Uncertainty

- Network reachability is not permanent. The recorded probes prove the state
  on 2026-08-10; the plan requires one fresh read-only probe immediately
  before the flip and escalates on any mismatch.
- The live PyPI project page updates only when the next release is published;
  this task fixes the repository-side contract and authorizes no release.
