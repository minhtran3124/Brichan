# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `plan-review`
- Artifact version: `3`
- Origin: `review:projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md@TDW-009-P3-v3`
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

- Reviewed plan ID: `TDW-009-P3`
- Reviewed plan version: `3`

## Claim or decision

CHANGES REQUIRED. `TDW-009-P3` version 3 closes most of the version-2 safety
design: descriptor-relative writes remain contained, a dossier advisory lock
serializes cooperating publishers, no-replace hard-link publication preserves
existing entries, and a final canonical re-walk prevents a detached dossier from
being reported as success. The validator extension is bounded and makes
authority-link invalidity part of the sole existing validity authority. The
44-path implementation allowlist also reconciles exactly.

Implementation is nevertheless not authorized. The purported valid record
example contains only one of eleven required artifacts; the implementation-start
manifest records only digests although rollback requires original tracked-file
content; summary exit rules contradict both each other and current discovery
behavior; and the principal same-identity limitation is described as guaranteed
detection in several normative passages even though the design later admits
detection is best-effort. A fifth contradiction says the dossier lock precedes
every mutation even though the dossier may have to be created before it can be
locked.

This review is independent of the planner. Reviewer session
`019fc133-dbb0-7951-8fcd-aed6107bc9c7`, route `review`, model `gpt-5.6-sol`, and
effort `high` are recorded in the parent and reviewer-child receipts. The
reviewer session differs from plan-author session
`3ebc7268-a8cd-464c-8d65-9920f2beac5c`
(`receipt.md:24-30`; `../TDWREV-009/receipt.md:24-28`).

## Version-2 finding verification

| Prior item | Version-3 result | Evidence and disposition |
| --- | --- | --- |
| `C1` raced temporary source | Partially closed under the accepted boundary | `design.md:24-55,302-360` names the excluded same-identity mutator, locks cooperating writers, verifies the published inode, and leaves an unverified final entry in place. The plan no longer claims prevention, but still claims unconditional detection despite admitting at `design.md:627-630` that detection is best-effort. See H4. |
| `H1` ancestor-link validity versus sole authority | Closed in plan | `requirements.md:114-126`, `design.md:87-102`, and `plan.md:137-142,189-194` authorize one shared no-follow helper, two validator call sites, two new diagnostics, and validator-owned regression tests. No summary-owned validity override remains. |
| `H2` inadequate baseline and rollback | Open | The new manifest is a mandatory precondition, but `plan.md:48-57` requires only digests while `plan.md:381-388` requires recorded original content to build reverse patches. The routing digest named by the plan also no longer matches the protected file. See H2. |
| `H3` detached-directory success | Closed in plan | `requirements.md:100`, `design.md:374-383`, and `plan.md:160-170,211-225` require a final device/inode re-walk and deterministic exit `1` on drift, including swaps before and between publications. |
| `M1` exact record schema and example | Open | The integer version and position-specific backtick rules are resolved, but the example asserted valid at `design.md:207-253` supplies only `artifacts.plan`, contradicting the exact eleven-key requirement at `design.md:133,174-176`. See H1. |
| `M2` mutable review evidence | Closed | All prior-review evidence references found in the five current planning artifacts point to `versions/v1/plan-review.md` or `versions/v2/plan-review.md`; none relies on the replaceable standard review path. |

## Findings by severity

### High

#### H1 — The “valid” worked record omits ten required artifacts

`R-G26` requires the worked example in `design.md` to validate under the
exhaustive schema (`requirements.md:109`). The schema says `artifacts` contains
exactly the eleven keys of `ARTIFACTS` and that missing keys are refusals
(`design.md:133,174-176`). The example then provides only `plan`
(`design.md:207-248`) and substitutes prose saying the other ten “follow the same
shape” (`design.md:251-253`).

A read-only extraction and JSON parse reproduced one artifact key, `plan`,
against eleven required keys. Therefore the plan's step-10 assertion that the
worked example validates (`plan.md:196-209`) cannot pass without weakening the
schema or testing a different record. This leaves version-2 `M1` unresolved and
blocks `TDW-009-AC2`.

Bounded revision: replace the abbreviated object with one complete eleven-entry
record that satisfies every exact type, nullability, owner, extra-field,
review-linkage, evidence-floor, and cross-record rule. Keep the extraction test,
and make it load the literal fenced example from `design.md` rather than a
separate fixture.

#### H2 — The implementation-start manifest cannot support its promised rollback, and its routing digest is no longer current

The packet requires digest/content evidence and manifest-based delta and rollback
(`task-packet.md:118-124`). The plan narrows this to presence plus a digest for
every existing allowlisted path (`plan.md:45-57`), but later says rollback uses
the manifest's recorded pre-implementation content to construct reverse patches
for eight modified files (`plan.md:377-388`). A digest proves equality; it cannot
reconstruct bytes or a reverse patch. Step 1 also postpones defining the delta
command until implementation (`plan.md:132-135`) instead of specifying the
command or canonical manifest format that the reviewer can verify.

There is a second immediate precondition failure. `R-X6` and the plan require
`config/model-routing.json` to retain SHA-256 `31466a36...`
(`requirements.md:156`; `plan.md:56-57`), matching the old pre-task manifest
(`baseline/pre-task-manifest.txt:5-6`). Read-only hashing during this review
produced `dc9344c63da2bf65c45d62a3fb20b99efc752a5cfa84bb25e45dc99b119d436d`.
The file is currently modified relative to `HEAD`, and this review has no
authority to decide whether that newer content is user-owned, coordinator-owned,
or erroneous. Implementation must not revert it merely to satisfy the stale
digest.

Bounded revision: require byte snapshots or an equivalent task-start patch for
all eight modified tracked files, plus digests; define the manifest format and
exact set-delta/reverse-patch procedure before handoff; require all 36 new paths
to be recorded absent or stop. The coordinator must classify the current routing
change and either make its current accepted bytes the protected
implementation-start state or separately restore an authorized state. Update
the expected digest only through that decision, never through implementation.

#### H3 — Unreadable-index and index-less-dossier exits contradict the sole validator

The normative boundary says an unreadable artifact inside a discoverable dossier
exits `1`, while a dossier with no readable `index.md` is undiscoverable and
exits `2` (`requirements.md:140-145`; `design.md:413-425`). Those categories
overlap for an existing unreadable `index.md`.

Current `discover_dossiers` globs the path
`*/handoffs/*/index.md` without reading it
(`validation.py:1109-1116`). An existing but unreadable index is therefore
discoverable; `parse_artifact` emits `cannot read artifact`
(`parser.py:116-123`), so the sole validator supplies an invalid-scope
diagnostic and the stated `exit 1` rule applies. Conversely, a root scan of an
index-less handoff containing dossier artifacts is evaluable:
`discover_partial_dossiers` and `validate_projects` emit `partial adoption`
(`validation.py:1138-1195`). `R-S12` itself requires that state to appear and be
nonzero (`requirements.md:143`), contradicting the blanket index-less exit `2`.
Plan step 14 does not separately test an unreadable index or root-level partial
adoption (`plan.md:246-258`).

Bounded revision: define exits by actual discovery scope. At minimum, an existing
unreadable `index.md` and a root scan that diagnoses partial adoption are exit
`1`; a truly absent/unlistable requested scope or unmatched `--task` is exit
`2`. Specify selected-task behavior for an index-less partial dossier without
overriding `validate_projects`, then add separate tests for unreadable index,
missing index with dossier metadata under a root scan, empty historical handoff,
unlistable directory, and unmatched selected task.

#### H4 — Normative text overclaims detection against the excluded attacker

The accepted amendment permits narrowing the threat model but forbids claiming
protection against the non-cooperating same-identity mutator
(`task-packet.md:104-112`). Requirements, brief, options, and design repeatedly
say the generator “detects” the attack or converts it to a named failure
(`requirements.md:71-78`; `brief.md:66-70`; `options.md:65-78`;
`design.md:44-49,353-360,547-560,577-586`). A continuously active excluded
process can replace the final name after the post-link `lstat`, or change it
again before that check. The design's uncertainty section correctly concedes
that even detection is best-effort (`design.md:625-630`).

The controlled substitution tests in `plan.md:211-225` prove only that a
mismatch which remains present until the check is observed. They cannot support
an unconditional adversarial detection claim. This is not a request to expand
the threat model; it is a request to make every normative statement match the
accepted narrow one.

Bounded revision: replace absolute detection language with a point-in-time
statement: the immediate post-publication check returns nonzero if it observes a
type/inode mismatch, but neither prevention nor detection is guaranteed against
the excluded process. Keep the deterministic controlled-race tests and label
their evidentiary limit explicitly.

### Medium

#### M1 — The dossier lock cannot precede every mutation when the dossier does not yet exist

`R-G8` says the lock is acquired before any mutation
(`requirements.md:90-92`). The specified walk creates a missing project,
`handoffs`, and dossier directory and only then locks the dossier descriptor
(`design.md:302-319`; `plan.md:151-168`). This ordering is unavoidable: a
directory cannot be locked before it exists. The useful safety property is that
the lock precedes every temporary-file creation and artifact publication, not
every directory-creation mutation.

The interleaved first-creation case is also absent from step 11, which tests only
a second holder on an already obtained dossier lock (`plan.md:211-225`).

Bounded revision: state that all record rendering and checking precedes any
filesystem mutation, safe descriptor-relative `mkdir` may occur before the
dossier lock exists, and the lock is acquired immediately after opening the
dossier and before any artifact or temporary-file mutation. Add a two-invocation
test starting from a missing dossier and prove both converge on one directory
inode, publications do not interleave, and the losing lock attempt creates no
artifact or temporary leaf.

## Test-gap verification

| Version-2 gap | Version-3 status |
| --- | --- |
| `TG1` ancestor/source races and namespace identity | Covered for the accepted model by plan step 11: project, handoffs, dossier, source, final-name, and between-publication swaps, with final re-walk exit `1`. The test must not be cited as protection against the excluded actor; see H4. |
| `TG2` write/publication/cleanup faults | Covered by step 12: short write, raised write, file and directory `fsync`, close, `ENOSPC`, `EEXIST`, cleanup unlink, inode mismatch, permission, and bounded-name exhaustion. |
| `TG3` exact types and structure injection | The matrix is comprehensive, but the required worked-example assertion is impossible until H1 is fixed. |
| `TG4` generated output against validator | Covered by step 13 across request, plan/review, route, authorization, and remote-action rules. |
| `TG5` project diagnostics and unreadable boundaries | Partial. Partial adoption and duplicate IDs are named, but unreadable index and root-level index-less partial adoption have contradictory expected exits; see H3. |
| `TG6` `passed` floor versus `not-required` rule | Covered explicitly at Levels 0, 1, and 2 in step 14. |
| `TG7` authority links and independence arms | Covered. Steps 9 and 14 require ancestor diagnostics from the validator and exercise both identity-comparison arms and placeholders. |
| `TG8` Python 3.10 and protected state | Python 3.10 is installed and the command is explicit. Resource coverage is specified for all 16 current files, but the manifest/rollback data and routing-state conflict in H2 remain unresolved. |
| `TG9` reproducible metrics | Covered by the fixed traversal order, scalar rules, explicit eleven-path `wc -l`, `wc -lc`, and two-run reproduction in `design.md:479-528` and `plan.md:267-278`. |

Additional required tests:

- Extract and validate the literal complete JSON example from `design.md`.
- Exercise unreadable `index.md` separately from missing `index.md`, and root
  partial adoption separately from unmatched `--task`.
- Start two cooperating apply invocations from a missing dossier and verify the
  corrected pre-lock directory-creation semantics.
- Validate the manifest parser and exact delta computation against modified
  tracked bytes, pre-existing new-path collisions, unrelated untracked leaves,
  and a concurrently changed rollback target.
- Assert the post-link check's diagnostic for a stable injected mismatch, while
  avoiding any assertion that it guarantees detection of the excluded actor.

## Exact path, authority, and protected-state verification

- The allowlist arithmetic is correct and exact: 8 modified tracked paths, 7 new
  source/test paths, and 29 evaluation leaves expand through the current
  eleven-member `ARTIFACTS` tuple to 44 total and 44 unique paths. All eight
  modified paths are tracked; all seven new source/test paths are currently
  absent.
- The 29 evaluation leaves include both records, `results.md`, both memory
  files, all 22 artifact files, and both receipt fixtures. They are synthetic
  non-authoritative data by `requirements.md:170-175` and
  `plan.md:260-294`; receipt validation and the fixed disclaimer are explicit.
- `validation.py` can accept the five enumerated hunks without changing
  `parser.py` or `scaffold.py`: the schema import block, literal
  `EXTRA_SECTION_FIELDS`, `_is_safe_relative`, and both authority-link functions
  exist at the cited insertion points. The summary continues to take its verdict
  from `validate_projects(..., require_complete=True)`.
- The 15 resource files recorded by the old baseline still match their digests,
  and the current resource tree contains 16 files because
  `src/brichan/resources/__init__.py` was omitted from that baseline. Version 3
  correctly requires the implementation-start manifest to cover all 16. No
  resource mutation is authorized.
- The routing file does not currently match the digest hard-coded by version 3;
  this is an implementation stop, not permission to rewrite the file.
- The archived version-1 review hashes to
  `eba30d0f1bbe448fa24bc180c6ec9a2518e63ce38307bc8cf22c46cc7948ddc4`.
  The byte-preserved version-2 review hashes to
  `5494bfff6a76b0d4ed950d885b75313545dc4a60efdf15f284a6ba87f128bebd`.

## Residual risks and required human decisions

- Coordinator decision required: classify the current
  `config/model-routing.json` change and establish the byte sequence the
  implementation-start manifest must protect. The implementer may neither
  absorb nor revert it by assumption.
- Planner revision required: supply a genuinely complete valid record example,
  align unreadable and partial-adoption exits with the existing validator, make
  rollback inputs sufficient, and remove absolute detection claims.
- Coordinator confirmation required: the narrowed threat model remains accepted
  after wording is corrected to best-effort observation. The residual bad final
  entry may require manual inspection and removal.
- Residual risk: `flock` is advisory and binds only cooperating writers. The
  plan must continue to state that boundary prominently.
- Residual risk: a crash can leave an identity-unverified `.tdgen.*.tmp` orphan;
  no authorized sweep exists.
- Residual risk: line counts and authored-value counts are reproducible proxies,
  not proof of usability, preference, evidence quality, time, token, or cost
  savings.
- No implementation, receipt update, baseline update, coordinator-artifact
  update, routing or resource change, commit, remote action, permission
  expansion, or secret access is authorized by this review.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:99-139`
  fixes the accepted threat boundary, sole-validator decision,
  implementation-start manifest contents, version-2 archival requirement, and
  `TDW-009-P3` version-3 identity.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md:117-281,302-383,402-575,625-644`
  supplies the exact schema, incomplete worked example, lock/publication order,
  final re-walk, summary exits, metrics, threat claims, and the best-effort
  caveat reviewed above.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan.md:38-128,130-310,312-465`
  supplies the 44-path allowlist, manifest precondition, implementation and test
  sequence, verification, stop conditions, rollback, and evidence claims.
- `src/brichan/contracts/task_dossier/parser.py:116-123` and
  `src/brichan/contracts/task_dossier/validation.py:772-885,1028-1195` establish
  the actual unreadable-artifact diagnostic, authority-link insertion points,
  index-based discovery, partial-adoption diagnostics, and sole project verdict.
- Read-only probes parsed the fenced worked example as one artifact rather than
  eleven; expanded the allowlist to 44 total and 44 unique paths; reproduced
  both archived-review hashes; verified all 15 baseline-listed resource digests;
  found 16 current resource files; confirmed Python 3.10 is installed; and
  measured the current routing-file digest stated in H2.

## Uncertainty

- The current routing-file change occurred outside this review's write scope.
  Its ownership and intended durability cannot be inferred from repository state.
- Permission-denied tests can vary under privileged execution; the plan
  correctly requires a recorded skip rather than a false pass, but deterministic
  mocked `OSError` coverage should still establish exit behavior.
- No uncertainty remains about the verdict. H1 alone makes the mandated
  worked-example test impossible, and H2 and H3 prevent the accepted plan from
  providing its own rollback and summary guarantees.
