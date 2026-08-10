# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `PYPI-003`
- Task level: `2`
- Artifact: `requirements`
- Artifact version: `6`
- Origin: `planner:2026-08-10-pypi-003-plan-v6`
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

Ten requirements make the public PyPI rendering flip minimal, pinned by
offline tests whose shipped-config assertion is itself the automated revert
gate, and closed in both durable-memory records, with fresh anonymous
verification at execution time, a two-phase coordinator-owned lifecycle, and
no remote mutation of any kind.

## Version 2 amendments

Version 1 held the stale `PRODUCT.md:230` line open as a coordinator
decision. The coordinator decided on 2026-08-10 to include its one-line
removal as truth reconciliation for the same requested gate. Version 2 added
R6a and folded it into acceptance criterion 5.

## Version 3 amendments

Version 3 closes every plan-review version 2 finding. The six public-rendering
implementation paths are unchanged.

## Version 4 amendments

Version 4 closes plan-review version 3: the lifecycle is split into two
coordinator-owned phases (acceptance-and-authorization before implementation;
finalization after implementation and code-review PASS) with a schema-v2
receipt created at acceptance; the `references.md` pointer names exactly
`projects/brida-installable-tool/handoffs/PYPI-003/receipt.md` as exactly one
line; both probes lead with `curl -q` and use no auth headers and no netrc;
the self-imposed manual temporary-copy negative procedure and its acceptance
criterion are removed — the permanent shipped-config test directly asserts
`public_repository is True`, so a revert to `false` fails that automated test
naturally under normal focused runs; and every review-identity reference
targets `PYPI-003-PLAN` version 4. The six implementation paths and all
exclusions are unchanged.

## Version 5 amendments

Version 5 closes plan-review version 4, correcting only Phase B ownership and
order: the independent code reviewer alone writes the complete
`code-review.md` — content, `passed` phase state, and `PASS`/`CHANGES
REQUIRED` verdict — and the coordinator never edits it, only verifies it and
projects it into `index.md` and the receipt. Phase B's sequence becomes:
verify evidence; update project memory, tasks, index, pr-desc, metrics, and
other coordinator projections; close Brichan-owned idle/done panes (keeping
any pane needed to report); only then finalize the schema-v2 receipt to
reviewed `PASS` with the actual evidence in hand; and run the final full
`make check` last, on the finalized receipt and tree. No artifact claims
later evidence in advance. Phase A, the exact receipt path, the `curl -q`
probes, the automated regression gate, the six implementation paths, and all
exclusions are preserved; review identity targets `PYPI-003-PLAN` version 5.

## Version 6 amendments

One-line provenance correction closing the isolated plan-review v5 low
finding: the H1 disposition row's active-current reference now reads
"version 5 as of this revision" instead of the stale "version 4". Nothing
else changes in this or any other artifact.

## Finding disposition

| Finding | Raised in | Status |
|---|---|---|
| H1 — acceptance required a PASS on the superseded plan version | plan-review v2 | Closed: every pre-implementation review reference names the current plan version — version 5 as of this revision — and R7a requires plan-review, index accepted-plan identity, and receipt plan identity to agree (criterion 7) |
| H2 — the authorized lifecycle could not make the full gate pass | plan-review v2 | Closed: R7 now authorizes the coordinator's exact post-PASS transitions — five planning artifacts `passed`, plan `accepted`, scaffold artifacts completed — and forbids the reviewer from making them |
| M1 — excluding `references.md` violated the receipt contract | plan-review v2 | Closed: R7 adds exactly one coordinator-owned `references.md` receipt pointer; the omission option is removed (`options.md` D4) |
| M2 — `gh api` is authenticated, not anonymous | plan-review v2 | Closed: R1 mandates an unauthenticated `curl` against the public GitHub API with no auth headers or credential helpers, sanitized to the four asserted fields (`design.md` §1) |
| M3 — the negative revert criterion had no executable step | plan-review v2 | Closed in v3 by a manual temporary-copy procedure; plan-review v3 found that bespoke manual matrix self-imposed. v4 closes it structurally: the permanent shipped-config test asserts `public_repository is True`, so the revert fails the normal automated focused run — no manual procedure exists or is required (R4) |
| L1 — stale 74-line baseline for `current-state.md` | plan-review v2 | Closed: baseline corrected to 79 lines; the −3 +3 edit keeps 79 ≤ 80 (R6, `design.md` §4.1) |

## Requirements

- **R1 — verification is fresh, anonymous, not remembered.** Immediately
  before the flip, the implementer runs one read-only probe pair — both
  invocations leading with `curl -q` as the first argument (disabling any
  local curl configuration), sending no authentication headers or tokens and
  using no netrc — against the public GitHub repository API and the raw
  image, recording output sanitized to the asserted fields only: the
  repository metadata must report
  `https://github.com/minhtran3124/Brichan`, visibility PUBLIC,
  `private: false`, default branch `main`; and an anonymous HTTP GET of
  `https://raw.githubusercontent.com/minhtran3124/Brichan/main/assets/brichan-hero.png`
  must return 200 with content type `image/png`. Any mismatch stops the task
  and escalates; the recorded 2026-08-10 evidence is treated as historical
  support, never as a substitute.
- **R2 — the flip.** `config/pypi-readme.json` changes `"public_repository"`
  from `false` to `true` and nothing else; `asset_base_url` and
  `link_base_url` (already the verified Brichan URLs) stay byte-identical.
- **R3 — regeneration, never hand-editing.** `README_PYPI.md` is regenerated
  with `python3 scripts/build_pypi_readme.py`. The resulting diff against the
  committed file is exactly two added lines: one blank line and
  `![Brichan coordinating a team of AI workers](https://raw.githubusercontent.com/minhtran3124/Brichan/main/assets/brichan-hero.png)`.
  Any other difference stops the task. `packaging/pypi-readme.md` and
  `scripts/build_pypi_readme.py` are not edited.
- **R4 — the shipped mode is pinned.** The current suite does not pin it: both
  mode test classes use synthetic configs
  (`tests/unit/test_build_pypi_readme.py:12-20`), and the sync tests pass in
  either mode. Three focused offline regressions are added:
  1. unit (`ConfigTest`): `load_config()` returns `public_repository is True`
     with `asset_base_url == "https://raw.githubusercontent.com/minhtran3124/Brichan/main"`
     and `link_base_url == "https://github.com/minhtran3124/Brichan/blob/main"`;
  2. contract (`PackagingMetadataTest`): the committed `README_PYPI.md`
     contains the exact hero image line from R3;
  3. contract (`SdistBuildTest`): the built sdist's `PKG-INFO` contains the
     exact raw hero URL.
  No test performs network access; URLs are pinned as strings. The
  shipped-config pin is itself the executable revert gate: it directly
  asserts `public_repository is True`, so reverting the value to `false`
  fails that permanent automated test naturally in any normal focused run —
  no bespoke manual negative procedure exists or is required.
- **R5 — existing tests are preserved.** No existing assertion is deleted or
  weakened. The private-mode classes keep their synthetic configs and continue
  to prove the strip behaviour; `test_pypi_source_hero_resolves_when_the_repository_goes_public`
  remains valid (its override becomes a no-op).
- **R6 — gate closure in durable memory.**
  `projects/brida-installable-tool/current-state.md` loses only the completed
  gate bullet (lines 56–58, "Confirm the public repository URL … when the
  repository is public.") and gains one line under "Distribution and release"
  recording that the repository is public at
  `https://github.com/minhtran3124/Brichan` and that the PyPI description
  embeds the hero image via the anonymous raw URL, verified 2026-08-10. The
  external-dogfood and TestPyPI gates stay byte-identical, `Last updated:
  2026-08-10` is retained, and the file stays ≤ 80 lines (79 today; the
  −3 +3 edit keeps 79).
- **R6a — `PRODUCT.md` truth-up.** The single line
  `3. Confirm the public repository URL and fix the PyPI README image URL.`
  (`PRODUCT.md:230`, "Next, in order" item 3 in section 10) is deleted. Items
  1 and 2 keep their numbers, and every other line of `PRODUCT.md` —
  including `Verified as of 2026-08-09` and the `Last verified:` header, both
  already satisfying `make memory-check` — is byte-identical. This is truth
  reconciliation for the closed gate, per the coordinator's 2026-08-10
  decision, not a product-direction change.
- **R7 — two-phase coordinator-owned lifecycle, fully authorized.** The
  coordinator — never the reviewer — performs both phases.

  **Phase A — acceptance and authorization**, after the stronger reviewer
  records `PASS` on `PYPI-003-PLAN` version 5 and before any implementation:
  mark the five planning artifacts (`requirements.md`, `brief.md`,
  `options.md`, `design.md`, `plan.md`) `passed`; set `plan.md` Plan status
  to `accepted`; complete `request.md`, `index.md`, and
  `client-follow-up-questions.md` as applicable; create the **schema-v2
  accepted receipt** at
  `projects/brida-installable-tool/handoffs/PYPI-003/receipt.md` with
  downstream evidence recorded as pending; add **exactly one**
  receipt-pointer line reading exactly
  `projects/brida-installable-tool/handoffs/PYPI-003/receipt.md` to
  `projects/brida-installable-tool/references.md`; and advance the
  `PYPI-003` row in `tasks.md` to implementing status. Completing Phase A is
  what authorizes implementation.

  **Phase B — finalization**, after implementation and the code-review
  `PASS`. The independent code reviewer alone writes the complete
  `code-review.md` — its content, its `passed` phase state, and its
  `PASS`/`CHANGES REQUIRED` verdict; the coordinator never edits that file,
  only verifies it and projects it into `index.md` and the receipt. Then, in
  order, the coordinator: verifies the implementation evidence; updates
  current project memory, the `tasks.md` row, `index.md`, `pr-desc.md`, the
  `metrics/runs.jsonl` row, and its other projections; closes all
  Brichan-owned idle/done panes except any pane needed to report; **only
  after** project memory and cleanup are complete, finalizes the schema-v2
  receipt to reviewed `PASS` with the actual evidence then in hand; and runs
  the final full `make check` last, against the finalized receipt and tree.
  No artifact records later evidence in advance — the receipt carries only
  evidence that exists at its finalization, and the final `make check`
  result is observed after it. Phase B is what makes the complete-dossier
  gate and the final full gate pass.
- **R7a — plan identity agreement.** Before implementation begins,
  `plan-review.md`'s reviewed plan ID and version, `index.md`'s accepted-plan
  identity, and the receipt's plan identity must all record
  `PYPI-003-PLAN` version 5. Any disagreement blocks implementation or
  acceptance until reconciled.
- **R8 — bounds.** No version bump, tag, push, PR mutation, release, publish,
  changelog change, model-routing or packaged-policy change, secret access, or
  remote state mutation. The only network use is R1's read-only probes. No
  file outside `plan.md`'s authorized list changes.

## Acceptance criteria

1. R1's fresh probe output is recorded in the receipt, and the flip proceeded
   only on a full match.
2. `git diff` shows `config/pypi-readme.json` changed on exactly one line and
   `README_PYPI.md` changed by exactly the two added lines of R3.
3. The three R4 regressions exist and pass on the final tree. The
   shipped-config pin directly asserts `public_repository is True`, so the
   revert case is gated by the normal automated focused run; no manual
   negative procedure is executed or required.
4. `PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_pypi_readme.py --check`
   passes; `make readme-check`, `make memory-check`, `make path-check`, and
   the unit and contract suites pass.
5. `current-state.md` matches R6: the completed gate is gone, both unrelated
   gates are byte-identical, the file is ≤ 80 lines. `PRODUCT.md` matches
   R6a: `git diff -- PRODUCT.md` shows exactly one deleted line and zero
   added lines, and `grep -c "public repository URL" PRODUCT.md` reports `0`.
6. Implementation began only after R7 Phase A completed (artifacts `passed`,
   plan `accepted`, schema-v2 accepted receipt with pending evidence, the
   exact `references.md` pointer line, task status implementing), and full
   `PYTHONDONTWRITEBYTECODE=1 make check` passes when run last in R7
   Phase B, against the finalized receipt and tree. (At planning time the
   scaffolded PYPI-003 dossier is the sole source of `make dossiers`
   failures; this is sequencing, not a defect.)
7. An independent stronger reviewer returns `PASS` on `PYPI-003-PLAN`
   version 5 before implementation, and the complete `code-review.md` —
   content, `passed` phase state, and verdict — is authored solely by the
   independent code reviewer before finalization, with the R7a identity
   agreement holding: plan-review, index accepted-plan identity, and receipt
   plan identity all name `PYPI-003-PLAN` version 5.

## Evidence

- `config/pypi-readme.json:5-7`; `packaging/pypi-readme.md:7`;
  `scripts/build_pypi_readme.py:87-129` (render/validate contract).
- In-memory public-mode simulation (2026-08-10, read-only): diff = exactly the
  restored hero line plus a blank line; `validate` returned `[]`.
- Baseline: 28 tests in `tests.unit.test_build_pypi_readme` +
  `tests.contract.test_packaging_metadata` pass; `--check` reports in-sync;
  `scripts/validate_task_dossiers.py projects` reports 73 issues, all in the
  PYPI-003 scaffold.
- Recorded 2026-08-10 GitHub and anonymous HTTP probe evidence supplied in the
  task packet (R1 re-verifies it at execution time, unauthenticated).
- `plan-review.md` version 2 (`CHANGES REQUIRED`, findings H1–L1) — the
  authority for every version 3 amendment; its baseline observations
  (79-line `current-state.md`, dossier summary states, authenticated
  `gh api` semantics) are adopted as evidence.
- `plan-review.md` version 3 (`CHANGES REQUIRED`) — the authority for the
  version 4 amendments: the two-phase lifecycle with a schema-v2 accepted
  receipt authorizing implementation, the exact one-line `references.md`
  pointer, `curl -q` probes, and the removal of the self-imposed manual
  temporary-copy negative matrix.
- `plan-review.md` version 4 (`CHANGES REQUIRED`) — the authority for the
  version 5 amendments: reviewer-sole authorship of `code-review.md` and the
  corrected Phase B order ending with receipt finalization and the final
  full `make check`.

## Uncertainty

- Reachability is a point-in-time fact; R1 bounds it but cannot guarantee the
  URL's future availability. The pinned tests guard the contract, not the
  network.
- The live PyPI page reflects the fix only at the next published release,
  which this task does not authorize.
