# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `plan-review`
- Artifact version: `1`
- Origin: `review:projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md@TDW-009-P1-v1`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fc133-dbb0-7951-8fcd-aed6107bc9c7`
- Effective route: `review`
- Effective model: `gpt-5.6-sol`
- Effective effort: `high`
- Reviewing session: `019fc133-dbb0-7951-8fcd-aed6107bc9c7`
- Review verdict: `CHANGES REQUIRED`

## Review target

- Reviewed plan ID: `TDW-009-P1`
- Reviewed plan version: `1`

## Claim or decision

CHANGES REQUIRED. Plan `TDW-009-P1` version 1 has a sound overall decomposition,
preserves the eleven-artifact contract, and reproduces the two pilot baselines,
but it is not safe or internally consistent enough to authorize implementation.
One critical filesystem race and five high-severity contract gaps prevent
`TDW-009-AC1`, `AC2`, `AC4`, `AC5`, and `AC6` from being established. The plan
must be superseded by a bounded version 2 before implementation.

This review is independent of the plan author. The reviewer session
`019fc133-dbb0-7951-8fcd-aed6107bc9c7`, recorded in the parent and child
receipts, differs from planner session
`3ebc7268-a8cd-464c-8d65-9920f2beac5c`.

## Findings by severity

### Critical

#### C1 — The pathname-based write design can follow a raced dossier-directory symlink and escape the projects root

`design.md:270-284` relies on a preflight followed by
`create_exclusively(path, text)` and claims that `O_NOFOLLOW` prevents link
following. In current source, however, `dossier_path` resolves containment only
once (`scaffold.py:87-95`), `plan_scaffold` checks only whether the final dossier
path is a symlink (`scaffold.py:117-118`), and `apply_scaffold` later calls
`mkdir` and opens every artifact by its full pathname
(`scaffold.py:188-202`). `O_NOFOLLOW` at `scaffold.py:159-162` protects only the
final artifact component. A concurrent writer can replace or create the dossier
directory as a symlink after planning and before an artifact open; the open then
walks that symlink and may create files outside the selected root.

This directly violates `TDW-009-AC1` (`task-packet.md:38`), `R-G4` and `R-G5`
(`requirements.md:46-47`), and threat controls T1/T3
(`design.md:396-399`). The planned tests cover only symlinks present before
preflight (`plan.md:107-119`) and cannot establish the claimed race guarantee.

Bounded revision: anchor generation to directory file descriptors opened from
the selected projects root with no-follow directory semantics, and create each
artifact relative to the verified dossier descriptor. Define safe creation of
missing project/handoff/dossier components without pathname re-resolution.
Authorize the exact helper changes this requires, then add deterministic races
that swap the dossier and each ancestor after preflight, before the first write,
and between artifact writes. Assert no outside file is created and no link is
followed.

### High

#### H1 — Write failures can publish a truncated artifact that every retry preserves

The promoted helper opens the final name and writes directly to it
(`scaffold.py:151-171`). A short write, encoding error, flush failure, close
failure, or exhausted filesystem can therefore leave a partially written final
artifact. The next generation run classifies that path as `preserve`, so the
record cannot recover it without a manual deletion. `design.md:285-287`
explicitly accepts a partially written dossier but does not distinguish
recoverable multi-file partial progress from a corrupt partial file. Neither
the generator tests (`plan.md:107-119`) nor the stop conditions
(`plan.md:214-232`) inject write, flush, or close failures.

Bounded revision: specify atomic publication for each newly created artifact,
or a cleanup protocol that removes only the inode created by this invocation
after verifying its identity. Render all eleven byte strings before any
filesystem mutation. Add fault-injection tests before the first byte, after a
partial write, on flush/fsync, and between artifacts; prove existing entries
remain byte-identical, no partial final artifact is preserved as success, and a
retry has deterministic recovery semantics. Multi-file partial progress may be
retained only if every retained artifact is complete and the command exits
nonzero with an explicit partial-adoption diagnostic.

#### H2 — The complete evaluation samples would fabricate review and receipt authority

Step 8 assigns the implementation worker both complete records, while step 9
requires those records to pass `--require-complete` and asks the same worker to
hand-write each `receipt.md` (`plan.md:133-151`). The complete gate requires an
applicable plan review and PASS verdicts for applicable reviews
(`validation.py:972-998`). Consequently the implementer-authored records must
supply reviewer sessions and PASS verdicts despite no independent sample-review
session being planned. Receipt-link validation checks only that `receipt.md`
exists (`validation.py:817-824`); the plan does not run receipt validation on
the isolated evaluation root. A placeholder receipt can therefore make a
sample appear authority-complete.

This conflicts with evidence-before-completion, review independence, and the
task packet prohibition on generated or inferred verdicts
(`task-packet.md:29-30`). It also makes the summary's reported
`independent` state an assertion about unequal strings, not evidence of an
independent review.

Bounded revision: choose and document one honest fixture contract. Either use
real independently authored sample review artifacts and schema-valid
coordinator receipts, with their ownership and exact paths assigned outside the
implementer; or use unmistakably synthetic fixture identities and receipts,
label every report as non-authoritative test data, and do not present fixture
PASS/independence as real review evidence. In either case, validate fixture
receipts explicitly and record that identifier inequality alone does not prove
session independence.

#### H3 — Summary exit semantics contradict AC4 and omit validator-owned project diagnostics

The parent criterion and brief require incomplete dossiers to produce a nonzero
summary exit (`task-packet.md:41`; `brief.md:65-66`). `R-S8` weakens that rule to
incompleteness only when a complete gate is requested
(`requirements.md:71`), and the design returns zero whenever default
validation emits no diagnostic (`design.md:345-354`). Because
`validate_dossier(..., require_complete=False)` accepts valid `pending`,
`active`, and `blocked` phase states, the default summary can exit zero for an
incomplete dossier.

The design also calls `discover_dossiers` and `validate_dossier` per dossier
(`design.md:305-308,331-343`). The validator's partial-adoption and duplicate
task-ID diagnostics live only in `validate_projects`
(`validation.py:1160-1195`). The proposed summary can therefore report a root
as healthy while the existing validator rejects that same root, and `--task`
is ambiguous when duplicate task IDs exist. That violates `R-S9`'s
single-authority rule.

Bounded revision: make the default summary invoke the existing complete gate so
incomplete state exits `1`, or revise AC4 explicitly with user approval.
Compute root validity through `validate_projects`, preserving partial-adoption
and duplicate-ID diagnostics, and define selected-task behavior for duplicates.
Keep `validate_dossier` for per-dossier detail, but never let it erase
project-level diagnostics or determine a conflicting exit.

#### H4 — Record validation does not close malformed-JSON and Markdown-structure injection cases

The design says unknown keys at every level are refused
(`design.md:96-99`) but does not reject duplicate JSON object keys. Standard
`json.load` silently keeps the last duplicate value; a read-only probe confirmed
that duplicate `review_verdict` keys collapse to one value. The schema also
allows arbitrary strings in claims, evidence, uncertainty, field values, and
supplemental bodies (`design.md:140-167`) without defining how embedded
newlines, headings, list markers, table rows, backticks, or field syntax are
escaped or refused. Such values can change the parsed Markdown structure or
the validator's evidence-item count.

The planned malformed-record matrix covers malformed JSON and unknown/missing
keys, but not duplicate keys, exact JSON types, boolean-as-integer confusion,
control characters, multiline metadata, or Markdown structure injection
(`plan.md:107-119`). This does not meet `R-G15`
(`requirements.md:57`) or the review gate that malformed fields must not be
silently accepted.

Bounded revision: define an exact recursive JSON type schema; reject duplicate
keys with `object_pairs_hook`; require `type(value) is int` where an integer is
intended; and either reject structural Markdown characters/newlines in scalar
positions or provide a rendering/round-trip rule proven not to create headings,
fields, tables, or extra evidence bullets. Add one named diagnostic and one test
for each malformed class.

#### H5 — Required evaluation writes are hidden behind a broad directory authorization

The packet permits implementation writes only at paths explicitly accepted by
the plan (`task-packet.md:52-54`). The plan calls
`evals/task-dossier-pilots/concise/` one of “exactly sixteen paths”
(`plan.md:29-51`), but that directory expands to two records, 22 generated
artifacts, two receipts, one or more project-memory files required by
`validation.py:827-885`, and `results.md`. Step 9 mentions receipts but not the
required memory files (`plan.md:140-151`). The leaf set, sample project slugs,
and receipt ownership are therefore not exact or complete.

Bounded revision: enumerate every evaluation leaf path, including each sample's
eleven artifacts, receipt, and canonical memory target, or define a closed
machine-checkable path pattern plus the exact expected file list and count.
Assign receipt and review writes to their canonical owners rather than the
implementer. Make the changed-path gate compare the observed task delta against
that leaf allowlist.

#### H6 — Dirty-worktree verification and rollback commands cannot prove preservation

The plan correctly acknowledges a pre-existing routing diff
(`plan.md:53-58`) but later expects plain
`git diff -- config/model-routing.json` to be empty and raw
`git status --short` to show only the sixteen authorized paths
(`plan.md:203-212`). Both commands compare with `HEAD`, not with the pre-task
working tree. Read-only inspection already shows pre-task changes outside the
implementation scope, so these expectations are impossible without discarding
or misclassifying user work.

Rollback is also inaccurate: the authorized table contains eight modified
tracked files, not seven, and many more than nine new files once generated
samples are expanded (`plan.md:34-51,234-245`). `git checkout --` reverts whole
files and can erase concurrent user edits rather than only TDW-009 hunks.

Bounded revision: capture a coordinator-owned pre-task path/byte baseline,
compare forbidden files byte-for-byte against that baseline, and compute the
implementation delta without assuming a clean `HEAD`. Correct the tracked/new
file counts. Roll back with a task-specific reverse patch or exact hunk
reversion, and delete only newly created paths proven to belong to this task;
abort rollback when a target changed concurrently.

### Medium

#### M1 — The evaluation proves output compression, not simpler authoring

The 639-line and 716-line pilot baselines are correct and reproducible: direct
`wc -l` over the eleven TDW-006 and TDW-007 artifacts reproduced both totals.
The new measurement, however, counts only generated Markdown
(`plan.md:140-158`). It excludes both JSON records even though the schema repeats
state, provenance, claim, evidence, uncertainty, and supplemental content for
all eleven artifacts (`design.md:96-167`). The project problem is authoring
ceremony (`brief.md:24-37`), so a 30% generated-output reduction alone does not
show that the structured source is materially simpler.

Bounded revision: retain AC3's exact dossier-only metric, but add record line and
byte counts, nonblank authored-value counts, and combined record-plus-output
counts to AC7's durable evaluation. State explicitly which metric measures
artifact compactness and which approximates authoring burden; do not claim time,
token, or cost savings.

#### M2 — Two source-API edits are underspecified

The plan restricts `validation.py` to one replacement line
(`plan.md:42,71-76`), but `ARTIFACT_EXTRA_SECTIONS` must also be added to the
existing schema import list at `validation.py:28-68`; the replacement cannot
run otherwise. The plan also says `__init__.py` will re-export all new public
names (`plan.md:41`), while the package already exports `validation.main`
(`__init__.py:11-16`) and both new CLI modules expose their own `main`. The
collision has no specified alias or compatibility rule.

Bounded revision: authorize and enumerate the import-list edit, then list the
exact package exports. Keep the existing `main` binding unchanged and either do
not re-export CLI mains or give them explicit non-conflicting names with tests.

## Test gaps

- No after-preflight race swaps the dossier or an ancestor symlink before or
  between writes; no test proves a raced root escape is impossible.
- No short-write, partial-write, flush, fsync, close, permission, or disk-full
  fault proves that final artifacts are complete and retries are recoverable.
- No duplicate-key, exact-type, multiline-metadata, heading, table, field, or
  evidence-bullet injection case exercises record refusal.
- No generator test covers request origin/redaction/mutability, plan/review
  linkage, route-strength/override pairing, Level 0/1 ship authorization, or
  forbidden PR remote-action text against the eventual validator result.
- No summary test covers partial adoption, duplicate task IDs, ambiguous
  `--task`, default valid-but-incomplete state, unreadable artifacts, or
  project-level diagnostics from `validate_projects`.
- No summary test distinguishes the Level floor for `passed` artifacts from the
  validator's one-item rule for `not-required` artifacts
  (`validation.py:276-309,339-347`); otherwise a valid Level 2
  `not-required` artifact can be labeled below-floor while validity exits zero.
- Authority-link tests omit symlinked ancestors, repository-containment drift,
  and races between health checks. Independence tests omit each comparison arm:
  plan session versus review `Authoring session`, versus `Reviewing session`,
  placeholders in either field, and synthetic unequal identifiers.
- No explicit Python 3.10 run is listed, and no before/after byte manifest proves
  installed resources, existing dossiers, and the user's routing diff remained
  unchanged from the pre-task state.
- The line-budget command is described but not fixed as an exact reusable script
  or explicit eleven-path invocation, and record-size measurements are absent.

## Residual risks and required human decisions

- Human decision required: choose whether the concise samples use real
  independently authored reviews and validated receipts, or clearly synthetic,
  non-authoritative fixture identities. A real PASS must not be generated by the
  implementation worker.
- Human decision required: confirm that incomplete dossiers must exit nonzero by
  default, as AC4 currently says. Any relaxed default changes an accepted
  criterion and requires coordinator/user acceptance before plan version 2.
- Human decision required: accept either an expanded scaffold-helper change or
  a generator-specific directory-descriptor writer. The current “rename only”
  boundary cannot close C1.
- Residual risk: identifier inequality is only a deterministic consistency
  signal, not cryptographic proof that two independent sessions existed. The
  summary and evaluation must describe that limitation.
- Residual risk: line count is an artifact-size metric, not evidence quality or
  operator effort. Reviewer judgment remains necessary even after record-size
  metrics are added.
- No implementation, commit, remote action, routing change, installed-resource
  change, permission broadening, or receipt mutation is authorized by this
  review.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:34-57`
  fixes AC1-AC8, exact-path implementation ownership, no fabricated evidence,
  no routing mutation, and no remote or permission expansion.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/requirements.md:39-90`
  defines generator, summary, compatibility, sole-validator-authority, and
  complete-gate requirements; lines 71-75 expose the incomplete-exit tension.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md:96-203,270-412`
  defines the record boundary, direct final-path write semantics, accepted
  partial state, summary exit rules, line budget, and threat model reviewed
  above.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan.md:29-65,85-245`
  supplies the authorized-path table, implementation/test steps, impossible
  dirty-tree checks, stop conditions, and inaccurate rollback counts.
- `src/brichan/contracts/task_dossier/scaffold.py:71-95,117-171,188-217` shows
  one-time containment, final-directory-only symlink preflight, pathname-based
  creation, direct writes to final names, and post-plan collision behavior.
- `src/brichan/contracts/task_dossier/validation.py:276-355,545-617,782-885,946-998,1028-1106,1160-1195`
  shows the actual evidence floors, review linkage, authority-link checks,
  complete gate, per-dossier authority, and project-level diagnostics.
- `evals/task-dossier-pilots/results.md:49-64` records the baseline metric and
  ceremony claim; direct read-only `wc -l` reproduction yielded exactly 639
  lines for TDW-006 and 716 for TDW-007.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/receipt.md:24-30` and
  `projects/brida-task-dossier-workflow/handoffs/TDWREV-009/receipt.md:24-28`
  record planner and reviewer session identities, route/model provenance, and
  confirm this review session is not the plan-author session.

## Uncertainty

- The exact directory-descriptor publication protocol and the choice between
  real versus synthetic evaluation reviews remain design decisions for plan
  version 2. They do not justify implementing version 1.
- No uncertainty remains about the verdict: the raced directory escape alone is
  acceptance-blocking, and the independent-review requirement is satisfied by
  the distinct session identities recorded above.
