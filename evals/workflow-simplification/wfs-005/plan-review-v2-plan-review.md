# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `WFS-005`
- Task level: `2`
- Artifact: `plan-review`
- Artifact version: `2`
- Origin: `wfs-005-plan-review-worker:2026-09-26:v2`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `review-session-faf2990c`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `review-session-faf2990c`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `WFS-005-PLAN-001`
- Reviewed plan version: `3`

## Review provenance

- Version 1 of this artifact reviewed plan version 2 with verdict
  `CHANGES REQUIRED` and is byte-frozen at `versions/v2/plan-review.md`
  (DOSSIER-003). This version supersedes it in place for plan version 3
  (DOSSIER-004); no section of version 1 is appended to or contradicted
  piecemeal.
- Reviewing session `review-session-faf2990c` is not the plan's authoring
  session (`plan-session-8ec2b29b`) and not version 1's reviewing session
  (`review-session-70dac26e`).

## Verdict

`PASS`. All four blocking findings are closed, and closed in the shapes the
previous review named as preferred. I re-derived each closure against the tree
rather than against the plan's account of it, and each one holds: the legacy
applicability rule makes the C1 failure structurally impossible rather than
merely unobserved; the frozen `ARTIFACTS` registry leaves every assertion C2
protected with its exact current meaning and keeps every touched path inside
the declared scope; the generator fixture loads unedited; and the scaffold and
the index template can no longer contradict each other. Two Medium and two Low
findings remain. None blocks: each is stated below with why, and the two
Mediums are cheap to fix during S2, S5, and S7.

## Findings

### M1 — Medium, not blocking. Fail-closed level resolution is specified for the validator only, while R7 requires it of all four tools; after the change the summary fails open in the opposite direction

`requirements.md:61-70` states R7 as a single rule over four tools: the
validator, scaffold, generator and summary "all four recognize the artifact
set by task level, and level resolution fails closed: an unparseable or
missing task level applies the largest required set and the deepest evidence
floor, not the smallest."

The design implements the fallback in one place. `design.md:226-232` changes
`_resolve_level` to fall back to `"2"`. The summary paragraph
(`design.md:296-302`) specifies the roster and the unreadable-row change and
says nothing about level resolution. In the code, `summary.py:227` reads
`Task level` from the index with no fallback at all, and `_evidence_rule`
(`summary.py:147-156`) resolves the floor as
`MINIMUM_EVIDENCE_ITEMS.get(level, 1)` — the smallest, which is exactly the
direction M1 asked the validator to abandon.

Failure scenario, concrete: an index declares `Task level: two`. After the
change `validate_dossier` applies the Level 2 required set and an evidence
floor of 3, and fails the dossier. `summarize_task_dossier.py` on the same
dossier resolves no level, applies a floor of 1, and reports each passed
artifact as meeting its evidence rule. The summary also has to build a
level-keyed roster (`design.md:296-297`) from a level it cannot resolve, and
the design does not say what it does then — the implementer has to invent it.

Two consequences beyond the misreport. First, R7 is not met as written.
Second, if the implementer closes it by copying the fallback into
`summary.py`, the fallback becomes a value spelled in two modules, which
PY-003 requires a test to pin equal; `design.md:440-516` adds no such pin
(test 19 exercises the validator only, `design.md:509-512`).

Recommend: put level resolution, including the fallback, in one helper in
`src/brichan/contracts/task_dossier/` and call it from both `validation.py`
and `summary.py`; extend test 19 with the summary arm; add the PY-003 pin.
`scaffold.py:115-116` and the record loader take the level as a validated
argument, so those two need nothing.

Why this does not block: no acceptance criterion names the summary's
fallback. A2 (`requirements.md:118-127`) asks only for "an unparseable level
receiving the Level 2 required set", which the validator arm satisfies, and
`docs/workflows/task-dossier.md:281-298` establishes that the summary is not a
second validity authority — the verdict stays
`validate_projects(root, require_complete=True)`. Nothing the summary
misreports changes a gate.

### M2 — Medium, not blocking. The reviewer-must-not-back-write guard is not extended to `report.md`, the artifact that now carries the plan

`_validate_ownership` (`validation.py:435-446`) rejects `Owner: reviewer` on
exactly `("plan", "design", "requirements")`. That tuple exists because
`docs/workflows/task-dossier.md:117-123` and `docs/policy/reviewer.md:46-53`
make reviewers write the two review artifacts "and nothing else in the
dossier".

At Levels 0 and 1 the plan moves into `report.md` (`design.md:197-204`:
"The worker's plan lives in the `Plan` section"). The design's `validation.py`
change list (`design.md:375-376`, expanded at `design.md:236-244`) adds the
report-based independence rule but does not extend that tuple, and nothing
else fills the gap: `ARTIFACT_OWNERS` is consumed only by the renderer
(`generate.py:111`) and by the contract test
(`test_task_dossier_contract.py:358-367`), never by the validator, so the
declared `Owner` of a hand-authored artifact is unchecked except for the
review artifacts.

Failure scenario: a Level 1 dossier whose `report.md` declares
`Owner: reviewer` and whose `code-review.md` uses a different session
validates clean. The effect is a net reduction in mechanical protection for
the plan across the levels this change touches: at Level 2 a reviewer-owned
`plan.md` is rejected; at Levels 0/1 a reviewer-owned `report.md` is not.

Recommend: add `report` to the tuple at `validation.py:435` and land it as a
TEST-003 rejection case beside design test 6.

Why this does not block: the substantive protection — session independence —
is present (`design.md:240-243`), and it is not weakened when a legacy
`plan.md` is present either, because `_validate_ownership:448-471` keys the
plan-author rule on `plan` and still covers both review arms. The prose
invariant also names only the three planning artifacts, so no documented
invariant is violated by the omission; it is a guard whose purpose transfers
to a new member that was not added.

### L1 — Low, not blocking. Does not block

`.agents/skills/herdr-orchestration/references/task-dossier.md:50-57` states
"Plan review and code review come from independent sessions and name the exact
reviewed plan ID and version." Under `design.md:206-210` a reduced Level 0/1
dossier has no plan artifact and leaves the review-target fields null, and
under `design.md:252-255` plan review need not apply below Level 2, so both
halves of that sentence become false at the reduced levels.

The design's edit list for that file (`design.md:354-358`) names the level
sentence at lines 20-21 and "the closing notes"; the `## Review` section is
not on it. The `## Closing` section's `--require-complete` sentence (lines
64-65), which the completion narrowing also makes conditional, is covered by
"the closing notes".

Does not block, and does not miss A1: line 5 of that same file declares the
canonical contract "wins any conflict", and A1 concerns the artifact-set and
lifecycle statements, which are fully covered — the only two restatements of
the artifact-set rule outside the canonical document are
`docs/policy/operating-principles.md:32-35` and that file's lines 20-21, and
both are on the edit list. One added sentence in S7 closes it.

### L2 — Low, not blocking. Does not block

`plan.md:153-155` and `requirements.md:96-98` both attribute the extra Python
3.14 eval run to a "SCRIPT-003 note in the Makefile docs". No such note
exists. `Makefile:39-40` does freeze `python3` literally, so the extra run is
correct and required; but the `techstack-eval` help line (`Makefile:11`)
carries no note, and no occurrence of `PYTHON=` appears anywhere in the
`Makefile`. Only the citation is wrong; the verification step it supports is
right.

Does not block. Note separately that SCRIPT-003's own obligation — "note in
the target's docs when it does not follow `PYTHON=`" — is currently unmet in
the repository. That is pre-existing, the design deliberately leaves the
`Makefile` unchanged (`design.md:431-433`), and fixing it is a separate task;
this plan does not create the gap.

## Findings closure checked against the version 2 review

Each row of `plan.md:45-65` checked against the corresponding finding in
`versions/v2/plan-review.md`, and each claimed mechanism checked against the
tree.

- C1 — closed, in shape (a). `design.md:176-190` requires `report` at Levels
  0/1 only when no `plan.md` is present as a regular file, failing closed on a
  symlinked or unreadable plan. Verified on disk: seventeen contract-adopting
  dossiers exist, every one carries `plan.md`, none carries `report.md`
  anywhere under `projects/` or `evals/`, every one records
  `Applicability: required` for both reviews, and every one has exactly eleven
  index status rows. The six Level 0/1 dossiers are `TDW-006` (level 0) and
  `DOGFOOD-006`, `HERDR-091`, `TECHSTACK-002`, `TDW-007`, `TDW-010` (level 1),
  as stated. So the new required-set check, the Level 1/2 mandatory
  code-review rule (`design.md:236-239`), the status-table union rule
  (`design.md:245-251`) and the `"2"` level fallback each fire on no existing
  dossier — the version 2 defect is structurally unreachable, not merely
  unobserved. Test coverage is over real committed shapes at both levels
  (8a over `build_dossier`, which `tests/unit/test_task_dossier_validator.py:140-141`
  confirms builds the full eleven-artifact Level 1 shape, and 8b over the two
  committed concise samples), which answers the version 2 M4 note.
- C2 — closed by the separate registry. `ARTIFACTS` stays the frozen eleven
  (`design.md:140-151`). I re-checked each of the four protected assertions:
  the index-template row test (`test_task_dossier_contract.py:46-56`, an
  `assertIn` per name), the fenced-record equality (`:314-323`, an
  order-sensitive `list(ARTIFACTS) == list(payload["artifacts"])`), the two
  generator equalities (`tests/unit/test_task_dossier_generator.py:100`,
  `:427`), and the concise-sample presence test (`:419-428`). All four keep
  their exact meaning, so nothing under `projects/brida-task-dossier-workflow`
  or `evals/` is edited. The three re-keys are correctly identified and
  genuinely forced: `:29-31` compares the template glob to `ARTIFACTS`
  exactly and would fail once `report.md` joins the directory; `:347-367`
  asserts `set(ARTIFACTS) == set(ARTIFACT_TITLES)` and `== set(ARTIFACT_OWNERS)`,
  both of which gain `report`; `:33-44` is the evidence-contract sweep. Their
  cited locations (`design.md:404-420`) match the file.
- C2, additional check the plan does not make. I swept every remaining
  `ARTIFACTS` consumer for a second out-of-scope repair of the version 1
  class, and found none. `generate.py:156/176/217/545/563/599/625`,
  `record.py:511-518`, `scaffold.py:48/121`, `summary.py:211/230` and
  `validation.py:95/949/1180` are all inside the declared scope and all
  covered by `design.md:366-390`. The generator and summary assertions in
  `tests/unit/` stay true because an eleven-key record still renders eleven
  artifacts. I also checked the one candidate escalation the plan is silent
  about: the new files `contract_paths.py` and `scripts/check_contract_paths.py`
  do not have to be added to `config/repository-paths.json`, because
  `scripts/check_repository_paths.py:40-80` asserts that listed paths exist and
  enforces inventory completeness for root files only, and
  `test_task_dossier_contract.py:215-235` is an `assertIn` over a fixed list.
  So `config/` stays untouched and out of scope legitimately.
- C3 — closed. `tests/unit/test_task_dossier_generator.py:76-82` loads the
  frozen record with `level="0"`, `project="synthetic-level0"`, task
  `SYNTH-010`, confirming the corrected label at `design.md:280-287`, and
  `_cross_record` reads `record.artifacts["plan"]` unconditionally today
  (`record.py:830-832`), which is why the conditional cross-check is needed.
  The record carries a `plan` key, so the effective-required key rule accepts
  it with no edit.
- H1 — closed on both halves. The index template is not edited and its test
  stays keyed to `ARTIFACTS`; the scaffold generates rows for exactly what it
  scaffolds (`design.md:261-278`). I verified the byte-identity claim rather
  than accepting it: `docs/workflows/task-dossier/templates/index.md:42-52`
  holds eleven rows in exactly the form
  ``| `<name>` | `<required or not-required>` | `<phase state>` | `<name>.md` |``
  that `design.md:270-274` says the generator reproduces, and `_render`
  (`scaffold.py:63-68`) rewrites none of those placeholder cells, so Level 2
  output can be byte-identical. Tests 12 and 13 add the round trip the version
  2 review found missing.
- M1 through M4 and L1 through L4 of the version 2 review are each adopted as
  recommended or correctly dissolved. M3's membership change is present at
  `design.md:96-117`; M2's mitigation at `design.md:69-79` and
  `requirements.md:104-111`; L1's stale comment is correctly located above
  `MINIMUM_EVIDENCE_ITEMS` (`schema.py:100-102`); L4 is restated at the
  strength the evidence supports (`design.md:628-632`), which I confirm is the
  right strength — `PARITY_MARKERS` (`test_skill_parity_contract.py:21-66`)
  contains the bare words `possible`, `confirmed`, `blocked` and `escalate`,
  and parity is asserted over the whitespace-normalized concatenation of each
  tree (`:97-108`), so running the contract suite is the only sound guard.
  None of the replaced sentences supplies a marker.
- The version 2 review's remaining test-gap notes are addressed: the Level 0
  contract-path trust boundary is now named explicitly rather than implied
  (`design.md:81-86`), and L2's concise samples are pinned by test 8b.

## What I verified

Claims checked against the tree rather than accepted, beyond the closure
checks above.

- Reduced recognition cannot be used to skip Level 2 requirements. Level 2's
  required set stays the eleven (`design.md:174`). The legacy rule only ever
  *removes* `report` from a required set, and `report` is not in Level 2's set,
  so the rule is a no-op at Level 2 — it cannot shrink that set by
  construction. `_resolve_level` fails closed to `"2"`. The Level 2
  stronger-reviewer rule (`validation.py:674-680`) and the ship gate
  (`:707-714`) are untouched. `MINIMUM_EVIDENCE_ITEMS` is unchanged
  (`design.md:63-67`). The completion narrowing is explicitly Level 0/1 only
  (`design.md:252-255`), and design test 11 pins that a `not-required`
  `plan-review.md` still fails completion at Level 2. Design test 7 pins
  rejection of a Level 2 dossier missing any one of the eleven. The only
  remaining exposure is which level a task declares, which is M2 of the
  version 2 review, pre-existing, and recorded as documentary.
- Existing dossiers stay valid. Baseline run of
  `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py projects`
  on 2026-09-26: 39 diagnostics across 17 dossiers, every one of them against
  WFS-005's own still-templated `index.md`, `code-review.md` and `pr-desc.md`
  plus this artifact's superseded plan-version reference; filtering WFS-005 out
  leaves zero. That is the baseline the change must preserve, and the rule
  analysis above shows each new check is unreachable on the other sixteen.
- Installed mode and packaged resources stay byte-unchanged. Nothing in
  `design.md:334-438` touches `src/brichan/resources/`, and
  `test_installed_resources_are_untouched_by_the_workflow`
  (`test_task_dossier_contract.py:259-268`) independently forbids the string
  `task-dossier` in any packaged file, so the guard is not self-reported. The
  immutable manifest hashes packaged resource bytes only
  (`src/brichan/lifecycle.py:143-153`). The planned `docs/policy/operating-principles.md`
  section 2 edit cannot force a packaged edit: the delegation and
  three-phase assertions read the packaged copy alone
  (`test_dogfood_policy_contract.py:64`, `:83-95`), and the only
  both-trees comparison is by testing-discipline marker (`:28-49`, `:124-132`),
  none of which comes from the artifact-set sentence. Editing `.agents/` is
  consistent with PACKAGED-001, which permits the checkout export to be a
  mode-specific superset.
- No PRODUCT.md conflict, so POLICY-001 raises no report. `PRODUCT.md:99-108`
  already states that checkout-mode delegation is discretionary while the
  unconditional `plan` to `implement` to `review` mandate is installed-mode
  only, and `:136-138` repeats that scoping. The durable-contract table
  (`:159-174`) makes no statement about the dossier artifact set, and the
  drift checklist (`:247-270`) is satisfied — no silent migration, policy kept
  canonical in one place, independent review obtained.
- A1 is fully covered. A repository-wide sweep for restatements of the
  artifact-set rule outside the canonical document returns exactly two hits,
  `docs/policy/operating-principles.md:34-35` and
  `.agents/skills/herdr-orchestration/references/task-dossier.md:20-21`, and
  both are on the S7 edit list. `docs/index.md`, `docs/workflows/README.md` and
  `CONTRIBUTING.md` only point at the contract, which is what
  `test_canonical_policy_points_at_the_contract`
  (`test_task_dossier_contract.py:135-152`) requires.
- The report artifact's structural checks work through the mechanism the design
  names. `_validate_structure` (`validation.py:130-170`) builds its expected
  sections from `EXTRA_SECTION_FIELDS` and enforces presence, exactly-once and
  canonical order, while iterating an empty field tuple checks nothing — so
  four report sections with empty field tuples give presence and ordering, and
  the concreteness check is the separate addition the design describes.
  Unexpected extra sections are not rejected, so the four report sections can
  be added without disturbing any other artifact.
- The reduced shape needs no relaxation of rules the design does not mention.
  `Accepted plan ID` and `Accepted plan version` are checked only inside
  `_validate_plan_linkage`, which returns early when `plan` is absent
  (`validation.py:544-546`), so leaving them null at Levels 0/1 requires no
  change; and `_validate_state` (`:236-350`) applies concreteness to
  `Claim or decision`, `Evidence` and `Uncertainty` only, never to the
  review-target fields, so a null review target is already acceptable. The
  new rule the design adds — review targets *must* be null without a plan —
  is therefore an addition, not a relaxation.
- Test 8b is achievable and TEST-004-compliant. The two concise samples are
  tracked by Git (29 files under `evals/task-dossier-pilots/concise`), declare
  levels 0 and 1, carry all eleven artifacts plus a receipt, record both
  reviews `required`, hold exactly eleven status rows, and validate clean
  today: `validate_task_dossiers.py evals/task-dossier-pilots/concise/projects`
  exits 0 with "Validated 2 task dossier(s)". They are not gitignored, so they
  can own a gate assertion.
- The M1 change breaks no existing assertion. No test in
  `tests/unit/test_task_dossier_validator.py` pins the current `"0"` fallback;
  the one test the design plans to rework,
  `test_levels_share_artifact_presence_but_differ_in_evidence_depth`
  (`:383-408`), asserts a full dossier valid at each level and that every level
  owns the same artifact set — the first half becomes test 8a, the second half
  is the assertion that must change, and the design says so.
- The wrapper claim is accurate: five existing wrappers, including
  `scripts/validate_task_dossiers.py`, are exactly 19 lines, so S6's pattern
  reference is real, and `test_source_wrappers_call_explicit_checkout_entrypoints`
  (`test_repository_contract.py:169-199`) constrains only named `bin/` files,
  not `scripts/`.
- The interpreter note is required, not redundant: `Makefile:39-40` freezes a
  literal `python3` for `techstack-eval`, while `make check` (`:75`) runs it.
  The test tiers use `unittest discover` (`:30-37`), so the new
  `tests/unit/test_contract_paths.py` is picked up without a `Makefile` change.
- Baseline suites are green before the change:
  `tests.unit.test_task_dossier_validator`,
  `tests.unit.test_task_dossier_generator`,
  `tests.unit.test_task_dossier_summary`,
  `tests.contract.test_task_dossier_contract`,
  `tests.contract.test_skill_parity_contract` and
  `tests.contract.test_dogfood_policy_contract` run 224 tests, all passing, so
  any red after implementation is attributable to the change.

## Test gaps

- The fail-closed rule has no summary arm; design test 19 covers the validator
  only. See M1.
- No rejection case covers a reviewer-owned `report.md`. See M2.
- Nothing pins that the `.agents/` reference's review statements stay true of
  the reduced levels; the parity suite compares the two trees to each other,
  not either tree to the canonical contract. That is the same documentary
  trust level the file itself declares, so it is an acceptable boundary rather
  than a missing test, and L1's one-sentence edit is the fix.
- Design tests 5, 6, 10, 17 and 19 are well specified against TEST-003: each
  names a production path and a guard whose removal flips the result. Test 13
  is the strongest addition in this version — it is the only test that can
  catch a future scaffold-versus-validator divergence, which is the class of
  defect H1 was.
- Test 8b pins the concise samples' recorded contract validity, closing the
  gap that made the version 2 L2 possible. Test 8a's two arms rest on
  `build_dossier`, which is committed, so neither legacy guard depends on a
  gitignored tree (TEST-004).

## Residual risks and required human decisions

- Level self-declaration remains the largest standing exposure and is
  multiplied by this change, exactly as version 1 of this review concluded.
  The mitigation is documentary — recorded level-determination evidence plus a
  named reviewer finding — and the design is correct that nothing mechanical
  can close it over a declared integer. Accepted.
- Contract-path membership (`design.md:96-117`) adopts this review's earlier
  M3 recommendation. It is a judgment about the cost of over-inclusion, and
  the user may still prefer the narrower list. The plan keeps it cheap to
  reverse: one document line, one tuple entry, one pinned test.
- Evidence base: three tasks, one run per arm, same-provider reviewers. The
  protocol's stop-and-rollback rule stays in force and is restated in the
  workflow document (`plan.md:196-198`). Accepted.
- The plan-before-implementation ordering inside `report.md` is not
  tool-verifiable. The design now states this as a named boundary rather than
  implying it, which is the right handling at the same trust level the receipt
  lifecycle already carries.
- `PRODUCT.md:159-174` does not list the task-dossier workflow among the
  durable contracts, even though the workflow document calls itself the
  canonical checkout-mode contract and this task treats it as one. That gap is
  pre-existing and `PRODUCT.md` is outside the declared Techstack scope, so it
  is not this plan's defect; the user may want a follow-up task to add the row.
- An untracked `evals/workflow-simplification/wfs-005/` directory is present in
  the working tree. It predates implementation, but A5's `git diff` check
  (`requirements.md:134-137`) sees tracked changes only, so it will not confirm
  that `evals/` stayed untouched. Adding `git status --short evals` to the S9
  evidence would close that observation cheaply.
- Expected-red accounting during implementation: `make dossiers` and
  `test_repository_checkout_validates_clean` will be red from WFS-005's own
  pending coordinator artifacts. The plan states this correctly
  (`plan.md:160-165`) and correctly insists any other red is a defect. The
  measured baseline for that judgement is the 39 WFS-005-only diagnostics
  recorded above.

## Claim or decision

Plan `WFS-005-PLAN-001` version 3 is ready to implement. Every finding the
version 2 review classified as blocking is closed in the shape that review
named as preferred, and I confirmed each closure against the code rather than
against the plan's account of it: the legacy `plan`-satisfies rule makes the
no-migration guarantee structural, the frozen `ARTIFACTS` registry preserves
all four protected assertions and keeps every touched path inside the declared
Techstack scope, the frozen Level 0 generator fixture loads unedited, and the
untouched index template plus generated scaffold rows remove the
scaffold-versus-validator contradiction. Level 2 semantics, installed mode,
packaged resources, `evals/`, other tasks' dossiers and routing are all
provably unaffected, and the reduced recognition cannot shrink Level 2's
required set by construction. Two Medium findings — the missing summary arm of
the fail-closed rule and the un-extended reviewer back-write guard — and two
Low findings should be folded into S2, S5 and S7; none of them can make the
implementation miss an acceptance criterion, violate a documented invariant, or
break an existing contract, so none blocks.

## Evidence

- Findings closure re-derived against the tree: seventeen contract-adopting
  dossiers all carry `plan.md`, record `Applicability: required` for both
  reviews, and hold exactly eleven index status rows; no `report.md` exists
  anywhere under `projects/` or `evals/`; the six Level 0/1 dossiers are
  `TDW-006` (level 0) and `DOGFOOD-006`, `HERDR-091`, `TECHSTACK-002`,
  `TDW-007`, `TDW-010` (level 1). Together these make the version 2 C1 failure
  unreachable under `design.md:176-190`.
- C2 re-verified assertion by assertion:
  `tests/contract/test_task_dossier_contract.py:29-31`, `:33-44`, `:46-56`,
  `:314-323`, `:347-367`, `:419-428` and
  `tests/unit/test_task_dossier_generator.py:100`, `:427`; plus a full sweep of
  the remaining `ARTIFACTS` consumers (`generate.py:156/176/217/545/563/599/625`,
  `record.py:511-518`, `scaffold.py:48/121`, `summary.py:211/230`,
  `validation.py:95/949/1180`), every one inside the declared scope.
- The one candidate out-of-scope repair the plan does not discuss is a
  non-issue: `scripts/check_repository_paths.py:40-80` enforces inventory
  completeness for root files only, and
  `tests/contract/test_task_dossier_contract.py:215-235` is an `assertIn` over
  a fixed list, so two new non-root files need no `config/` edit.
- M1's evidence: `requirements.md:61-70` versus `design.md:226-232` and
  `design.md:296-302`, against `summary.py:227` and `summary.py:147-156`
  (`MINIMUM_EVIDENCE_ITEMS.get(level, 1)`), with `design.md:509-512` showing
  test 19 has no summary arm.
- M2's evidence: `validation.py:435-446` (the three-name tuple) and
  `:448-471` (the plan-author independence rule that still covers legacy
  shapes), against `design.md:197-204` (the plan moves into `report.md`) and
  `design.md:375-376`; `ARTIFACT_OWNERS` consumed only at `generate.py:111`
  and `tests/contract/test_task_dossier_contract.py:358-367`.
- L1's evidence: `.agents/skills/herdr-orchestration/references/task-dossier.md:5`,
  `:20-21`, `:50-57`, `:59-70` against the edit list at `design.md:354-358`.
  L2's evidence: `plan.md:153-155` and `requirements.md:96-98` against
  `Makefile:11` and `Makefile:39-40`, with no `PYTHON=` occurrence anywhere in
  the `Makefile`.
- Baseline measurements on 2026-09-26:
  `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py projects`
  reports 39 diagnostics across 17 dossiers, all against WFS-005's own
  artifacts and none against any other dossier;
  `validate_task_dossiers.py evals/task-dossier-pilots/concise/projects` exits
  0 with "Validated 2 task dossier(s)"; and the six dossier and parity test
  modules run 224 tests with zero failures.
- Byte-unchanged guarantees checked at their guards rather than in prose:
  `src/brichan/lifecycle.py:143-153`,
  `tests/contract/test_task_dossier_contract.py:259-268`,
  `tests/contract/test_dogfood_policy_contract.py:28-49`, `:64`, `:83-95`,
  `:124-132`, and `tests/contract/test_skill_parity_contract.py:21-66`,
  `:97-108`.
- Scope and product alignment: `PRODUCT.md:99-108`, `:136-138`, `:159-174`,
  `:247-270`; `docs/policy/operating-principles.md:32-35`;
  `docs/workflows/task-dossier.md:8`, `:117-123`, `:147-164`, `:281-298`;
  `docs/policy/reviewer.md:46-57`.
- Techstack Snapshot pointer:
  `projects/brida-workflow-simplification/handoffs/WFS-005/snapshots/attempt-plan-review-2-8372e56058931c212b207017ca7b488b5e49fac148e897693cc15430ed7a3545.snapshot.json`,
  sha256
  `8372e56058931c212b207017ca7b488b5e49fac148e897693cc15430ed7a3545`, verified
  `match` on 2026-09-26 before any other work; all ten selected rule files were
  read in full under this attempt.

## Uncertainty

- I did not implement the change. M1 and M2 are read from the design's stated
  rules against the current code, not observed as failures; each names the exact
  site and the exact shape that exposes it, and both sites were read on disk. A
  revised design that alters those rules invalidates the reasoning, not merely
  the finding.
- The four blocking findings of version 1 are closed by reasoning about
  unreachability plus the committed guards that will pin it, not by running the
  new tests, which do not exist yet. The reachability arguments rest on
  properties I measured on disk today — every dossier carries `plan.md`, both
  reviews `required`, eleven status rows, no `report.md`, no dossier declaring
  an invalid level — and a dossier added or edited before implementation could
  change them. Tests 8a and 8b are the durable guards; the measurements are
  today's baseline.
- The Level 2 byte-identical scaffold output claim is verified as *achievable*
  from the template's exact row form, not as observed output, since the
  generator does not exist yet. Test 12 is the right pin for it.
- L2 reports what the evidence supports: the absent note is a citation defect,
  and whether SCRIPT-003's own documentation obligation should be met in this
  task or a follow-up is a user decision, not a finding.
- No other unresolved uncertainty remains for this review.
