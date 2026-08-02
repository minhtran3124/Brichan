# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `plan-review`
- Artifact version: `4`
- Origin: `review:projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md@TDW-009-P4-v4`
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

- Reviewed plan ID: `TDW-009-P4`
- Reviewed plan version: `4`

## Claim or decision

CHANGES REQUIRED. `TDW-009-P4` version 4 genuinely closes version-3 `H1`, `H3`,
`H4`, and `M1`: the literal worked record has eleven artifacts and validates;
summary exits now follow the current validator's discovery behavior; every
excluded-process statement is best-effort-only; and the lock follows safe
descriptor-relative directory creation but precedes every temporary and artifact
mutation. The routing file is correctly capture-time protected with no expected
digest in any version-4 planning artifact. The implementation allowlist remains
exactly 44 unique paths.

Version-3 `H2` is not yet closed. The canonical manifest does not record enough
capture-time state to compute its own `unexpected` set, does not require the
implementer to compare current state with the capture before starting, and calls
a byte-digest comparison an identity check during rollback. Snapshot bytes are
neither authenticated before restoration nor protected from partial rollback.
The manual “procedure run” supplies no exact executable command and cannot
establish these guarantees. These are implementation-boundary and rollback
safety defects, not documentation polish.

This review is independent of the planner. Reviewer session
`019fc133-dbb0-7951-8fcd-aed6107bc9c7`, route `review`, model `gpt-5.6-sol`, and
effort `high` are recorded in the parent and reviewer-child receipts. The
reviewer session differs from plan-author session
`3ebc7268-a8cd-464c-8d65-9920f2beac5c`
(`receipt.md:24-30`; `../TDWREV-009/receipt.md:24-28`).

## Version-3 finding verification

| Version-3 item | Version-4 result | Evidence and disposition |
| --- | --- | --- |
| `H1` incomplete worked record | Closed | The single fenced JSON block at `design.md:224-467` contains the exact eleven `ARTIFACTS` keys and seventeen keys per artifact. Independent extraction, rendering, and current-validator execution reproduced 410 lines and zero diagnostics both with and without `require_complete`. |
| `H2` digest-only manifest and stale routing digest | Partially closed | No version-4 planning artifact contains a hard-coded 64-hex digest, and capture-time routing bytes are the only reference (`requirements.md:33-43,146-154`; `plan.md:37-65`). Eight snapshots are now required, but the delta and rollback remain mechanically insufficient; see H1 through H3. |
| `H3` unreadable-index and partial-adoption exits | Closed | `requirements.md:130-135`, `design.md:589-620`, and `plan.md:248-265` match `discover_dossiers`, `discover_partial_dossiers`, `parse_artifact`, and `validate_projects`: existing unreadable index and root partial adoption exit `1`; unavailable or unmatched scope exits `2`; root diagnostics remain visible under task selection. |
| `H4` guaranteed-detection overclaim | Closed | The five artifacts consistently say neither prevention nor detection is guaranteed and limit the post-link check to a point-in-time observation (`requirements.md:53-71,87`; `brief.md:54-67`; `design.md:24-65,542-550`; `plan.md:210-227`). |
| `M1` impossible pre-mutation lock | Closed | The four-phase order at `design.md:469-521` permits only descriptor-relative `mkdir` before locking, takes the dossier lock immediately after opening it, and creates no temporary or artifact leaf before success. Step 11 includes the two-invocation first-creation case. |

## Findings by severity

### High

#### H1 — The manifest lacks the baseline needed to compute its exact `unexpected` set

The canonical manifest records repository `HEAD`, a dirty yes/no flag, protected
paths, the eight modified allowlist paths, the 36 absent new paths, and only the
*names* of pre-existing untracked leaves (`design.md:661-696`). The delta
procedure then requires identifying every tracked path “whose bytes differ” and
every path new since capture (`design.md:698-710`).

There is no capture-time byte or digest map for tracked paths outside
`[protected]` and `[allowlist-modified]`. Comparing them with `HEAD` is expressly
forbidden and would classify pre-existing user changes as implementation work.
This is not hypothetical: read-only status during review shows existing tracked
changes to `projects/brida-task-dossier-workflow/references.md` and `tasks.md`,
neither protected, allowlisted, nor excluded by the one
`TDW-009/**` capture-scope rule. Comparing with capture is also impossible
because their capture-time bytes are absent.

The procedure likewise records no digest or byte length for pre-existing
untracked leaves. It can notice a newly named untracked file, but cannot detect
the implementation modifying an untracked file that already existed. Therefore
`unexpected == {}` does not prove that no path outside the 44 was changed, and
`R-X14`, `TDW-009-AC5`, and the exact-write-scope gate remain unprovable.

Bounded revision: make the manifest a complete capture map for every observed
non-excluded file, recording at least path, file type, byte length, and SHA-256.
This includes pre-existing tracked changes and untracked leaves. Alternatively,
record a complete current working-tree identity that provides equivalent
before/after bytes without using `HEAD` as the task baseline. Define the exact
exclusion set and exact executable delta command, then test modification of a
pre-existing tracked file and a pre-existing untracked file outside the
allowlist. Both must enter `unexpected`.

#### H2 — The rollback is content-checked, not identity-checked, and can restore unauthenticated snapshots

The amendment requires an identity-checked rollback that never overwrites a
target changed after implementation (`task-packet.md:155-159`). The actual
procedure compares only `sha256(p)` with a post-implementation digest and then
restores or deletes by pathname (`design.md:717-735`; `plan.md:392-412`).

A path replaced after handoff by another inode with byte-identical content passes
that check. More seriously, a modified target replaced by a symlink to a file
with matching bytes can pass a normal pathname hash; “restore snapshot over p”
can then follow the link and overwrite a different target. No `lstat` file-type
check, `O_NOFOLLOW`, device/inode comparison, or descriptor re-verification is
specified.

Snapshot integrity is also unchecked. The manifest line records the original
file digest and a snapshot pathname, but the start precondition checks only that
the snapshot is readable (`plan.md:130-135`). Rollback never verifies that the
snapshot is a regular no-follow file whose bytes match the manifest digest.
`options.md:217-219` explicitly concedes that nothing verifies snapshots were not
altered between capture and rollback. A changed snapshot can therefore overwrite
an otherwise valid target with untrusted bytes.

Bounded revision: record the post-implementation file type, device, inode, byte
length, and digest for every path. Before rollback, `lstat` every target without
following links and require all recorded identities and digests to match.
Authenticate every snapshot against the capture digest and length, also
no-follow. Perform this as a complete read-only preflight over all 44 paths
before the first restore or deletion; abort with no rollback mutation if any
check fails. During restoration, use no-follow descriptors, re-check descriptor
identity before writing, verify full write and `fsync`, and perform a final
canonical identity check. State the concurrency boundary honestly if the
procedure cannot provide compare-and-swap semantics against an active
same-identity process.

#### H3 — The implementation-start precondition validates manifest shape, not capture-time state

Step 1 verifies that sections and snapshot pathnames exist, but does not compare
current protected or modified bytes with their capture digests, authenticate the
snapshots, or check that all 36 “new” paths are still absent
(`plan.md:130-135`). A file can change or a planned-new collision can appear
between coordinator capture and implementation start, yet implementation
proceeds against a stale baseline.

Step 19 compounds the ambiguity by constructing a fixture with “a pre-existing
collision at one planned new path” while expecting `unexpected` to stay empty and
the delta to equal all 44 paths (`plan.md:299-310`). If the collision predates
capture, the manifest is invalid because every new path must be recorded absent.
If it appears after capture, start preflight must refuse it; treating it as an
authorized created path falsely attributes another writer's file to this
implementation. Generator-level `EEXIST` must preserve the file and force the
nonzero collision outcome, not permit a successful 44-path handoff.

Bounded revision: before any implementation write, compare every protected and
allowlist-modified path with the capture's no-follow type, length, and digest;
verify every snapshot; verify every allowlist-new path is actually absent; and
verify the complete observed-state baseline from H1. Any mismatch is a stop.
Replace the collision procedure expectation with two cases: a capture-time
collision makes the manifest invalid, and a post-capture collision makes start
preflight or generation fail nonzero without attributing the path to
implementation.

### Medium

#### M1 — The section-body schema simultaneously requires and permits embedded newlines

The schema says each `sections[].body` list element represents one rendered line
(`design.md:180-185`). The position-class table groups
`sections[].body[]` with multi-line `claim` and refuses control characters
*other than* line feed (`design.md:201-215`), thereby permitting one body element
to contain multiple rendered lines.

That ambiguity affects exact validation, deterministic rendering, line counts,
and `authored_values`, which counts the multi-line string as one scalar. Two
conforming implementations can therefore produce different structures from the
same nominal schema.

Bounded revision: split `claim` from `sections[].body[]`. Permit line feeds in
`claim` subject to per-line structural checks, but refuse line feeds in each body
list element so one element is exactly one rendered line. Add one negative
embedded-newline body test and one positive multi-line claim test.

## Added-test verification

| Version-3 required addition | Version-4 status |
| --- | --- |
| Extract and validate the literal design example | Covered and independently reproduced: one fenced block, 11 artifacts, 17 keys each, four cross-record checks, 410 lines, zero validator diagnostics under both gates. |
| Separate unreadable/missing index and root partial/unmatched task | Covered by the explicit matrix in plan step 14, aligned with current source. |
| Two cooperating invocations from a missing dossier | Covered by step 11 with one-inode convergence, non-interleaving, and no losing temporary/artifact leaf. |
| Manifest parser, exact delta, and changed rollback target | Not adequately covered. Step 19 is a manual prose procedure with no exact command, uses an insufficient baseline, and tests only changed bytes rather than changed identity or snapshot corruption. |
| Stable injected mismatch without an adversarial-detection claim | Covered by step 11 and the required limiting test comment. |

Additional tests required by this review:

- Change a pre-existing tracked file and a pre-existing untracked file outside
  the allowlist after capture; both must appear in `unexpected`.
- Change protected bytes, modified-path bytes, a snapshot, and create each class
  of planned-new collision between capture and start; preflight must refuse
  before any implementation mutation.
- Replace a rollback target with a regular byte-identical inode, a symlink to
  matching bytes, a directory, and an unreadable entry; all must abort with no
  restore or deletion.
- Corrupt, replace, symlink, and remove a snapshot; all must abort before any
  rollback mutation.
- Put a mismatch at the last of 44 rollback targets and prove the first 43 remain
  untouched, establishing complete preflight rather than partial rollback.
- Reject an embedded newline in `sections[].body[]` while accepting a safe
  multi-line claim.

The plan's statement that automating the manifest procedure necessarily requires
a forty-fifth path (`plan.md:299-310,475-478`) is unsupported. The allowlist
already authorizes additions to existing unit, contract, and integration test
files. If no existing test file can host a real procedure, the coordinator may
accept a bounded 45th helper path; absent that decision, use an already
authorized test path rather than downgrading a required safety check to prose.

## Exact path, safety, and evidence verification

- The implementation allowlist reconciles exactly: 8 modified tracked paths,
  7 new source/test paths, and 29 closed evaluation leaves produce 44 total and
  44 unique paths. Both records, both memory files, both receipts, all 22
  generated artifacts, and `results.md` are included.
- No 64-hex expected digest appears in any of the five version-4 planning
  artifacts. `config/model-routing.json` is consistently protected at capture
  time and remains outside implementation scope.
- The current resource tree contains sixteen files, including
  `src/brichan/resources/__init__.py`; version 4 names all sixteen for
  capture-time protection. No packaged or installed-resource write is
  authorized.
- The validator remains the sole validity authority. Exactly five
  `validation.py` hunks are authorized, adding one helper and two diagnostics;
  summary code only reports the resulting verdict.
- The generator design remains Python-3.10 standard-library-only,
  routing-neutral, descriptor-relative, no-overwrite, no-rename/no-replace,
  atomic per artifact, and final-canonical-re-walk guarded. Fault, symlink,
  namespace, lock, cleanup, directory-`fsync`, and partial-progress tests remain
  explicit.
- Synthetic samples remain unmistakably non-authoritative: all session
  identifiers use `synthetic-fixture-`, every artifact claim disclaims real
  review, fixture receipts are validated in the isolated root, and the summary
  caveat says identifier inequality is not proof of independence.
- The authored-value traversal order and compactness metrics are reproducible.
  The literal Level 0 example independently reproduced the claimed 410 rendered
  lines, below the 447-line limit. Level 1 remains an execution-time measurement.
- All historical-review citations in version 4 point to immutable
  `versions/v3/plan-review.md` references. The archived version-3 review remains
  byte-identical with SHA-256
  `696269370116484147bb37bff79d27d57594010a712aefe2413e38ff27166065`.

## Residual risks and required human decisions

- Coordinator decision required: keep the implementation allowlist at 44 by
  hosting manifest tests in an existing authorized test file, or authorize one
  bounded helper path and revise the arithmetic. A manual, unspecified procedure
  is not equivalent evidence.
- Planner revision required: make the capture map sufficient for exact
  before/after comparison, turn start validation into a complete state
  preflight, and specify no-follow identity-checked rollback with authenticated
  snapshots.
- Coordinator decision required: define the rollback concurrency boundary. A
  portable procedure cannot honestly promise pathname compare-and-swap against
  an actively mutating same-identity process without an explicit exclusion or a
  stronger primitive.
- The coordinator-owned implementation-start manifest and snapshots do not yet
  exist. Their actual content and capture receipts require review before
  implementation starts; the superseded baseline remains insufficient.
- Residual risk retained honestly: the generator's post-link observation is not
  prevention or guaranteed detection, a foreign final entry may require manual
  removal, and a crash may leave an orphan temporary.
- Residual risk retained honestly: line and authored-value counts are
  reproducible proxies, not evidence of operator preference, evidence quality,
  time, token, or cost savings.
- No implementation, receipt or baseline update, coordinator-artifact update,
  routing or resource change, commit, remote action, permission expansion, or
  secret access is authorized by this review.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:141-183`
  fixes capture-time routing protection, best-effort-only observation, restorable
  snapshots, exact delta and identity-checked rollback, validator-derived exits,
  corrected lock ordering, the literal example, and the `TDW-009-P4` identity.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md:224-550,589-735`
  supplies the literal record, lock and publication protocol, validator-derived
  exit table, canonical manifest, set-delta pseudocode, and rollback pseudocode
  reviewed above.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan.md:37-135,190-321,323-412`
  supplies the 44-path allowlist, implementation-start precondition, extraction,
  race, summary, manifest, and rollback tests, verification table, stop
  conditions, and operational rollback.
- `src/brichan/contracts/task_dossier/parser.py:116-123` and
  `src/brichan/contracts/task_dossier/validation.py:772-885,1028-1195` establish
  unreadable-artifact diagnostics, authority-link insertion points, index-based
  discovery, partial-adoption diagnostics, and sole project-level validity.
- Independent read-only extraction found exactly one JSON block, eleven artifact
  keys in `ARTIFACTS` order, seventeen keys per artifact, and all four
  cross-record relationships. An isolated temporary rendering reproduced 410
  lines and zero current-validator diagnostics under default and complete gates.
- Read-only repository inspection reproduced 44 total and unique authorized
  paths, sixteen resource files, immutable historical citations, no hard-coded
  expected routing digest, and the pre-existing tracked and untracked state that
  makes H1 concrete.

## Uncertainty

- The exact coordinator location and lifecycle for the sibling snapshot
  directory are not yet instantiated. The planning format uses
  `snapshot/<flattened-path>` without defining the flattening algorithm; explicit
  per-path snapshot names can remove that ambiguity during revision.
- Permission behavior varies under privileged execution; the deterministic
  mocked `OSError` case appropriately prevents a skipped permission test from
  becoming a false pass.
- No uncertainty remains about the verdict. H1 makes the claimed exact
  implementation delta uncomputable from the canonical capture, while H2 and H3
  leave rollback and implementation start exposed to state changes the plan says
  they prevent.
