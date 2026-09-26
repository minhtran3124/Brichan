# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `WFS-005`
- Task level: `2`
- Artifact: `plan-review`
- Artifact version: `1`
- Origin: `wfs-005-plan-review-worker:2026-09-26:v1`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `review-session-70dac26e`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `review-session-70dac26e`
- Review verdict: `CHANGES REQUIRED`

## Review target

- Reviewed plan ID: `WFS-005-PLAN-001`
- Reviewed plan version: `2`

## Verdict

`CHANGES REQUIRED`. The direction is sound and the evidence base is real, but
the central compatibility argument is false as written: adding `report` to the
Level 0 and Level 1 required sets invalidates all six existing Level 0/1
dossiers, which is the one constraint the user set explicitly. Extending the
frozen `ARTIFACTS` registry also breaks four existing assertions the plan does
not budget for, and two of the repairs land outside the declared Techstack
scope. Findings C1-C3 and H1 block; M1-M4 and L1-L4 do not.

## Findings

### C1 — Critical, blocking. The reduced required set invalidates every existing Level 0/1 dossier, so R8 and A3 fail

`design.md:114-118` places `report` in the Level 0 and Level 1 required sets.
`design.md:143-148` then emits the missing-file diagnostic "only for the
level's required set". No existing dossier has a `report.md`: `design.md:355`
says so itself, in the same sentence that concludes those dossiers "stay
valid".

Eleven artifacts that do not include `report` are not a superset of
`{index, request, report, code-review}`. The monotone rule in
`design.md:121-123` protects a dossier against *newly required* checks on
artifacts it already has; it does nothing about a required artifact that did
not exist when the dossier was written. The compatibility argument in
`design.md:352-361` is therefore internally contradictory, and Option 2B's
stated justification in `options.md:60-65` rests on it.

Failure scenario, verified against the tree: six Level 0/1 dossiers exist
(`TDW-006` at level 0; `DOGFOOD-006`, `TDW-007`, `TDW-010`, `HERDR-091`,
`TECHSTACK-002` at level 1). After the change each gains a missing
`report.md` diagnostic, and under the new status-table rule
(`design.md:159-162`, which requires a row for the level-required union) each
also gains a missing `report` status row — twelve new diagnostics across
dossiers the user required to stay valid with no edits. Acceptance criterion
A3 (`requirements.md:90-92`) fails, `make dossiers` fails for reasons beyond
the allowed WFS-005 exception, and A6 (`requirements.md:98-102`) fails with
it.

The plan's own verification step (`plan.md:118-124`) asserts the opposite
outcome and would catch this at S2, after seven of the nine steps are
written.

Required: decide and state how the new required artifact applies to dossiers
that predate it. Three workable shapes, in my order of preference —
(a) require `report` only when the dossier declares the new contract (for
example, require `report` at Levels 0/1 only if no `plan.md` is present, so a
legacy full dossier satisfies the level through `plan`); (b) treat `report` as
recognized-but-not-required everywhere and make the Level 0/1 requirement
"`report` or `plan`"; (c) keep `report` required and grandfather by an
explicit, frozen exemption list. Option (a) also removes the need for any
edit to the six dossiers. Whichever is chosen, it needs a committed
regression test over the real legacy shapes, not only the single fixture of
design test 8.

### C2 — Critical, blocking. `ARTIFACTS` is a cross-cutting frozen registry; extending it breaks four existing assertions, two of whose repairs fall outside the declared scope

`design.md:111-113` and `plan.md:67-70` add `report` to `ARTIFACTS`. Four
existing assertions key off that tuple and are not in the design's test list
(`design.md:267-283`) or the plan's step sequence:

1. `tests/contract/test_task_dossier_contract.py:55-56` requires the index
   **template** to carry a status row per `ARTIFACTS` entry. The template has
   exactly eleven rows today
   (`docs/workflows/task-dossier/templates/index.md:42-52`), and
   `design.md:219-244` does not list it among the files to change.
2. `tests/contract/test_task_dossier_contract.py:320` asserts
   `list(ARTIFACTS) == list(payload["artifacts"])` against the eleven-artifact
   JSON record fenced in another task's frozen design artifact
   (`projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md`).
3. `tests/unit/test_task_dossier_generator.py:100` and `:427` assert the same
   equality against the same record.
4. `tests/contract/test_task_dossier_contract.py:419-428` iterates `ARTIFACTS`
   over the two sample dossiers under `evals/task-dossier-pilots/concise`,
   asserting each `<artifact>.md` exists. Neither sample has a `report.md`.

Repairing 2 and 3 means editing a byte-frozen dossier artifact belonging to
another task — which `design.md:371` and `plan.md:86` promise not to do, and
which the dossier rules on evidence files constrain — or rewriting the
assertions. Repairing 4 means writing under `evals`. Neither
`projects/brida-task-dossier-workflow` nor `evals` is in the plan's declared
scope paths (`plan.md:44-48`), so the plan as written cannot reach `make
check` exit 0 inside its own scope. This is the same class of escalation the
version 1 plan raised for `CHANGELOG.md`, and `plan.md:155-158` now asserts
the opposite — that no path this plan touches is outside the declared scope.

Recommended alternative that dissolves 2, 3 and 4 entirely: do not mutate
`ARTIFACTS`. Keep it as the frozen eleven that every existing pin means, and
add a separate `RECOGNIZED_ARTIFACTS = ARTIFACTS + ("report",)` that the
validator, scaffold, generator, summary, and partial-adoption scan iterate.
Every assertion above keeps its current meaning, the index template needs no
new row, and only finding 1's template question remains — and it disappears
too, because the template's rows stay keyed to `ARTIFACTS`.

### H1 — High, blocking. Plan S1 and design section 4 contradict each other on the index status table

`plan.md:70-71` says to "Extend the template contract test to the twelve
recognized artifacts", which forces a `report` row into the index template.
`design.md:159-162` simultaneously makes "a row naming a recognized artifact
that is neither required nor present" a diagnostic, and `report` is neither
required nor scaffolded at Level 2 (`design.md:118-119`,
`design.md:172-175`).

Failure scenario: scaffold a Level 2 dossier after the change. It receives the
index template's twelve rows and the eleven required artifact files. The
validator then rejects its own scaffold output for the `report` row whose file
was never written. `design.md:160-162` asserts "Existing full dossiers keep
exactly their eleven rows", which is true of dossiers on disk but not of
anything newly scaffolded from the template the same change edits.

Design test 12 (`design.md:326-327`) checks only that the scaffold plans and
writes the right files; nothing validates the scaffolded dossier. Add that
round trip — scaffold at each level, fill, validate — and resolve which of the
two rules gives way.

### C3 — High, blocking. The frozen generator fixture is Level 0, not Level 1, and the monotone rule does not keep it loadable

`plan.md:86` and `design.md:177-181` both call it "the frozen eleven-artifact
Level 1 fixture" and rest the Option 2B rationale (`options.md:57-59`) on it
staying loadable. It is loaded at level `0`:
`tests/unit/test_task_dossier_generator.py:79-80` and `:118-119` pass
`level="0"`, `project="synthetic-level0"`, task `SYNTH-010`.

That matters beyond the label. Under the new record rule "required-set ⊆ keys
⊆ recognized-set for the record's level" (`design.md:177-179`), a level 0
record must carry a `report` key. The fixture has eleven keys and no `report`,
so it is refused — while `plan.md:86` promises the fixture is not edited. The
design's stated reason for choosing its central option is wrong for the exact
artifact it cites. Same root cause as C1; the C2 recommendation plus the C1
decision should resolve both, but the plan must say so rather than restate the
claim.

### M1 — Medium, not blocking. An unparseable task level silently selects the smallest required set

`_resolve_level` (`src/brichan/contracts/task_dossier/validation.py:1035-1048`)
falls back to `"0"` when `index.md` declares a level outside `TASK_LEVELS`. It
emits one diagnostic for the bad field, then returns `"0"`. Today that only
lowers the evidence-item floor. After this change it would also drop the
required set from eleven artifacts to four, so an index declaring, say,
`Task level: two` would lose seven missing-file diagnostics at the moment its
metadata is least trustworthy. The dossier still fails overall, so this is not
a silent pass — but the failure direction is wrong.

Recommend: when the level cannot be resolved, apply the largest required set
rather than the smallest, and land a test for it. Cheap, and it makes the new
level-keying fail closed.

### M2 — Medium, not blocking. Task level is self-declared, and the reduced set raises the payoff for declaring it low

`_resolve_level` reads `Task level` from `index.md` with no independent
authority, and `docs/workflows/task-dossier.md:157-164` states the
level-raising triggers as prose the coordinator applies to itself. Today
mis-declaring a level 2 task as level 0 costs two evidence items per artifact,
a reviewer-strength field, and a ship gate. After this change it additionally
sheds seven artifacts, plan acceptance, plan review, and — at Level 0 with no
contract path touched — independent code review altogether.

Nothing in the plan, the design, or the validator closes this, and nothing
can close it mechanically: the validator sees a declared integer. I do not
class it as blocking, because it violates no acceptance criterion and the
channel already exists. It does deserve a recorded mitigation, because the
change multiplies its value. Recommend that the canonical statement require
`index.md` to record the trigger that fixes the level (or the recorded
absence of every trigger), so a wrong level is a reviewable claim with
evidence rather than an unexamined field — and that the reviewer policy name
level mis-declaration as a review finding.

On the narrower question of whether the reduced recognition can be used to
skip Level 2 *checks*: it cannot. Level 2's required set stays the eleven
(`design.md:119`), `_validate_completion`'s plan-review rule narrows only at
Levels 0/1 (`design.md:163-166`), and the level table and stronger-override
rule are untouched. The exposure is entirely in which level a task claims,
not in what Level 2 then demands.

### M3 — Medium, not blocking. Answering the design's open question on contract-path membership

`design.md:383-389` leaves the membership question open for this review. My
answer: the list in `design.md:73-77` is too narrow on the runtime side. It
covers `src/brichan/contracts/` and `src/brichan/lifecycle.py` but excludes
the rest of `src/brichan/` — the CLI entrypoints, orchestration, and worker
launch — and excludes `scripts/`, which holds the wrappers for the validator,
scaffold, generator, and summariser that enforce this very contract. A Level 0
change to worker launch or to a validator wrapper would skip independent
review.

The design's own tie-breaking rule is inclusion, and the stated cost of
over-inclusion is one routine review. Recommend `src/brichan/` and `scripts/`
as prefixes, replacing the narrower `src/brichan/contracts/` and
`src/brichan/lifecycle.py` entries. Leaving `tests/` off is defensible: a
test-only diff is reviewed by the gate it runs under.

### M4 — Medium, not blocking. No committed test pins acceptance criterion A3

A3 (`requirements.md:90-92`) is the no-migration guarantee, and it is the
criterion C1 breaks. Design test 8 (`design.md:314-316`) validates "an
unmodified copy of an existing full Level 1 dossier fixture" — one fixture,
chosen by the implementer, at one level. The real guarantee is over the six
dossiers on disk, and `plan.md:118-124` covers it only as a manual command in
the verification list.

The dossier directories are gitignored, so techstack rule TEST-004 forbids a
test that reads them as the sole owner of a gate assertion. Recommend instead
a committed fixture per distinct legacy shape — at minimum one Level 0 and
one Level 1 full eleven-artifact dossier — plus the existing manual run, and
say in the plan that the manual run is a check rather than the regression
guard.

### L1 — Low, not blocking. Does not block

`src/brichan/contracts/task_dossier/schema.py:100-101` carries the comment
"Level changes evidence depth, reviewer strength, and authorization gates. It
never changes which artifacts must exist." The change makes it false.
`design.md:225-233` handles the two prose statements of the same rule
(`docs/policy/operating-principles.md:33-35` and the pinned workflow-document
needle) but not this one. Add it to the S7 file list.

### L2 — Low, not blocking. Does not block

`evals/task-dossier-pilots/concise/results.md` presents `SYNTH-010` and
`SYNTH-011` as contract-valid samples. Under the Level 0/1 required set they
become invalid for a missing `report.md`. Nothing validates them
automatically, so this is an accuracy defect in a recorded result rather than
a red gate — but it is a recorded result, and correcting an evidence file in
place is the rule. Worth one line in the plan, and it is a second reason to
prefer the C2 recommendation, which leaves both samples untouched.

### L3 — Low, not blocking. Does not block

`plan.md:155-158` and `plan.md:180-182` state that no path the plan touches is
outside the declared scope and that no scope uncertainty remains. C2 shows two
paths outside it. This is wording that follows the substantive defect; it
corrects itself when C2 is resolved.

### L4 — Low, not blocking. Does not block

`design.md:376` claims none of the phrases the `.agents` edits touch appears
in `PARITY_MARKERS`. The marker tuple includes bare generic words —
`"blocked"`, `"escalate"`, `"possible"`, `"confirmed"`
(`tests/contract/test_skill_parity_contract.py:29-47`) — and the parity check
concatenates each tree, so the claim holds only because those words survive
elsewhere in the tree, not because the edited files avoid them. The stated
mitigation (run the contract suite in S7) is the right one; the claim is just
stronger than the evidence.

## What I verified

Claims the plan and design make about the code, each checked against the tree
rather than accepted:

- Every function, constant, and module named in `design.md:142-195` and
  `design.md:246-265` exists as described: `_load_artifacts`, `_resolve_level`,
  `_validate_status_table`, `_validate_completion`, `discover_partial_dossiers`,
  `plan_scaffold`, `apply_scaffold`, and the summary roster and `(absent)`
  rendering. Correct.
- `_validate_completion` does refuse a `not-required` plan review for every
  task (`validation.py:1014-1027`), grounding the Option 1A rejection at
  `options.md:118`. Correct.
- `discover_partial_dossiers` scans `ARTIFACTS` minus `index`
  (`validation.py:1180`), so `report` joins the scan automatically. Correct,
  and the protection is strengthened as claimed.
- The workflow document's level table keeps the level and minimum-evidence
  columns adjacent, which is what
  `test_contract_states_documented_level_evidence_depth` matches
  (`tests/contract/test_task_dossier_contract.py:127-133`). The design's
  instruction to preserve that adjacency is correct and necessary.
- The `techstack-eval` recipe uses a literal `python3` and does not follow
  `PYTHON=` (`Makefile:39-40`), so the plan's extra 3.14 eval run
  (`plan.md:116-117`) is required, not redundant. Correct.
- Installed mode and packaged resources: the plan touches nothing under
  `src/brichan/resources`; the immutable manifest hashes packaged resource
  bytes only (`src/brichan/lifecycle.py:143-163`) and does not cover the
  checkout export, and `test_installed_resources_are_untouched_by_the_workflow`
  (`tests/contract/test_task_dossier_contract.py:259-268`) independently
  forbids any packaged file from mentioning the workflow. The byte-unchanged
  criterion is satisfiable as planned.
- The dogfood policy contract compares the checkout and packaged operating
  principles by marker, not by bytes
  (`tests/contract/test_dogfood_policy_contract.py:115-141`), so the planned
  section 2 edit does not force a packaged edit. The "all three phases are
  mandatory" mandate lives only in the packaged copy
  (`src/brichan/resources/dogfood_v1/policy/operating-principles.md:10`), so
  the checkout-only simplification creates no policy conflict.
- The stage 2 numbers the planning artifacts cite are accurate: 5 versus 24
  sessions, 1,343 versus 12,699 dossier lines, blind escape 42 versus 42, one
  escaped Medium each (`evals/workflow-simplification/stage2/results/results.md`
  lines 40-41, 61-63, 101-104).
- Current validator state: `validate_task_dossiers.py projects` reports 42
  diagnostics, every one of them against WFS-005's own still-templated
  `index.md`, `plan-review.md`, `code-review.md`, and `pr-desc.md`. No other
  dossier produces a diagnostic, which is the baseline C1 would break.

## Test gaps

- No committed regression test pins A3 over the real legacy shapes; see M4.
- Nothing validates a scaffolded dossier end to end, which is why H1's
  self-inconsistency is invisible to design test 12.
- Nothing pins the two sample dossiers under `evals/task-dossier-pilots` as
  contract-valid, so L2 would land unnoticed.
- Design test 16 exercises the contract-path checker, but no test or gate ties
  the Level 0 review decision to the checker's output; `design.md:105-107`
  leaves it as coordinator prose recorded in `code-review.md` evidence. That
  is a deliberate and acceptable trust boundary, but it should be named as one
  in the workflow document rather than implied.
- Design test 5 (report-section concreteness) and test 6 (report-based review
  independence) are well specified and, as written, satisfy TEST-003: each
  calls the production path and fails when the guard is removed.

## Residual risks and required human decisions

- Evidence base: three tasks, one run per arm, same-provider reviewers
  (`brief.md:83-87`). The protocol's stop-and-rollback rule remains the
  mitigation and the plan correctly keeps it in force
  (`plan.md:147-150`). Accepted.
- The plan-before-implementation ordering is not tool-verifiable
  (`design.md:390-393`). Agreed, and the design's framing — the same trust
  level the receipt lifecycle already carries — is the right one.
- Level self-declaration (M2) is the largest standing exposure after this
  change, and no tooling closes it.
- Contract-path membership (M3) is a judgment call the user may want to make
  rather than inherit from the plan.
- User decision required: how to resolve C2. Either re-resolve the Techstack
  snapshot to include the other task's handoff directory and the evals tree —
  accepting an edit to another task's frozen design artifact — or adopt the
  separate-registry approach, which keeps the change inside the current scope.
  I recommend the second.

## Claim or decision

Plan `WFS-005-PLAN-001` version 2 is not ready to implement. Its step
sequence, verification commands, and risk register are sound, and its claims
about the existing code are accurate wherever I could check them. But the
design's compatibility argument is false in the one place that matters most:
placing a brand-new `report` artifact in the Level 0/1 required set breaks all
six existing Level 0/1 dossiers, defeating the no-migration constraint the
user set and the acceptance criteria A3 and A6 that encode it. Extending the
frozen `ARTIFACTS` registry compounds this by breaking four assertions the
plan does not account for, two of which cannot be repaired inside the declared
Techstack scope. A revised version that keeps `ARTIFACTS` frozen, adds a
separate recognized-artifact tuple, and states how the new required artifact
applies to dossiers that predate it would clear C1, C2, C3, and H1 together
and would stay inside the current scope.

## Evidence

- `design.md:114-123` and `design.md:352-361` versus the tree: six Level 0/1
  dossiers (`TDW-006` level 0; `DOGFOOD-006`, `TDW-007`, `TDW-010`,
  `HERDR-091`, `TECHSTACK-002` level 1) exist under the projects tree and none
  contains a `report.md`, so the required-set change makes each one invalid
  (C1).
- `tests/contract/test_task_dossier_contract.py:55-56`, `:320`, `:419-428` and
  `tests/unit/test_task_dossier_generator.py:100`, `:427` each key on
  `ARTIFACTS`; the index template holds exactly eleven rows
  (`docs/workflows/task-dossier/templates/index.md:42-52`), the fenced record
  in the other task's design artifact holds exactly eleven keys, and the two
  concise sample dossiers hold no `report.md` (C2).
- `tests/unit/test_task_dossier_generator.py:79-80` and `:118-119` load the
  frozen record at level `0`, not level `1` as `plan.md:86` and
  `design.md:177-181` state (C3).
- `plan.md:70-71` versus `design.md:159-162`: the template test extension and
  the new status-table rejection cannot both hold for a Level 2 dossier
  scaffolded from the template (H1).
- `src/brichan/contracts/task_dossier/validation.py:1035-1048` resolves the
  level from `index.md` alone and falls back to `"0"` on an unparseable value
  (M1, M2).
- Baseline run of `validate_task_dossiers.py projects` on 2026-09-26: 42
  diagnostics, all against WFS-005's own templated artifacts, none against any
  other dossier.
- `Makefile:39-40`, `src/brichan/lifecycle.py:143-163`,
  `tests/contract/test_dogfood_policy_contract.py:115-141`, and
  `tests/contract/test_task_dossier_contract.py:259-268` confirm the eval
  interpreter note, the packaged-manifest boundary, and the marker-based
  policy comparison the plan relies on.
- Techstack Snapshot pointer:
  `projects/brida-workflow-simplification/handoffs/WFS-005/snapshots/attempt-plan-review-1-18c7f382cb21b33319a2d825e41978e6d6cfcb113c472e723cda031522d24482.snapshot.json`,
  sha256
  `18c7f382cb21b33319a2d825e41978e6d6cfcb113c472e723cda031522d24482`, verified
  `match` on 2026-09-26 before this review began; all ten selected rule files
  were read in full.

## Uncertainty

- I did not implement the change, so C1, C2, C3, and H1 are read from the
  design's stated rules against the current code rather than observed as test
  failures. Each names the exact assertion and the exact shape that breaks it,
  and the shapes were verified on disk; but a revised plan that alters those
  rules invalidates the reasoning, not just the finding.
- The contract-path membership answer in M3 is a judgment about the cost of
  over-inclusion, not a derivation. Reasonable people could keep the narrower
  list.
- I checked the parity-marker claim by reading the marker tuple, not by
  running the contract suite against a hypothetical edited tree, so L4 states
  what the evidence supports rather than a stronger guarantee.
- No other unresolved uncertainty remains for this review.
