# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `plan-review`
- Artifact version: `2`
- Origin: `review:projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md@TDW-009-P2-v2`
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

- Reviewed plan ID: `TDW-009-P2`
- Reviewed plan version: `2`

## Claim or decision

CHANGES REQUIRED. `TDW-009-P2` version 2 materially improves version 1 and
correctly closes the synthetic-fixture, complete-default, path-count,
authoring-metric, and source-export findings. It is not yet safe to implement.
The proposed hard-link publication still re-resolves its temporary source name
after the inode check, allowing a raced-in symlink or foreign inode to be
published at the final artifact name. The summary also promises a nonzero exit
for ancestor-symlinked authority links while preserving a validator that does
not diagnose that state, and the captured baseline cannot support the plan's
own exact-delta and rollback claims.

This review remains independent of the planner. Reviewer session
`019fc133-dbb0-7951-8fcd-aed6107bc9c7` differs from plan-author session
`3ebc7268-a8cd-464c-8d65-9920f2beac5c`; both identities are recorded in
`receipt.md:24-30`.

## Prior-finding verification

| Prior item | Version-2 result | Evidence and disposition |
| --- | --- | --- |
| `C1` ancestor directory-symlink escape | Partially closed | The descriptor walk at `design.md:248-283` prevents an ancestor swap from redirecting operations outside the held directory. Atomic publication introduces a separate final-component source-name race described in critical finding C1 below. |
| `H1` truncated artifact published and preserved | Partially closed | Full write and `fsync` before publication at `design.md:285-330` prevent ordinary write faults from exposing a partial final file, but publication can still link a raced-in foreign source. |
| `H2` fabricated review and receipt authority | Closed | `requirements.md:120-124`, `design.md:419-449`, and `plan.md:221-254` require fixed synthetic identities, per-artifact non-authoritative claims, schema-valid fixture receipts, explicit receipt validation, and a fixed disclaimer that fixture PASS values prove no real review. |
| `H3` incomplete exits and lost project diagnostics | Partially closed | `requirements.md:91-96` makes `validate_projects(..., require_complete=True)` authoritative with no relaxed flag. The ancestor-link exit promise still conflicts with unchanged validator behavior; see H1 below. |
| `H4` duplicate JSON and Markdown injection | Partially closed | `requirements.md:74-75` and `design.md:151-221` add duplicate-key, exact-type, and structural refusal rules. Two internal schema contradictions remain; see M1. |
| `H5` broad evaluation authorization | Closed | Expanding `<A>` through the current eleven-member `ARTIFACTS` tuple produces 29 evaluation leaves; with seven modified and seven new source/test files, the set contains exactly 43 unique paths. No required evaluation receipt or memory leaf is missing. |
| `H6` dirty-tree preservation and rollback | Open | Version 2 rejects `HEAD`-relative proof, but the supplied baseline lacks data needed for its replacement. See H2. |
| `M1` output compression without authoring metrics | Closed with residual risk | `requirements.md:124` and `design.md:451-464` retain the AC3 output metric and add record lines, bytes, authored values, and combined lines without claiming time, token, or cost savings. No threshold proves preference or usability, which is correctly retained as uncertainty. |
| `M2` source import/export ambiguity | Closed | `requirements.md:105-106` and `design.md:61-105` authorize the missing validator import hunk, preserve `validation.main`, and export the two new CLI functions under non-colliding names. |

## Findings by severity

### Critical

#### C1 — Named-temporary hard-link publication can publish a raced-in symlink or foreign inode

The design verifies the temporary name against the writing descriptor, closes
the descriptor, then calls `os.link(tmp, final, ..., follow_symlinks=False)`
(`design.md:290-300`; `plan.md:140-148`). The source name is resolved again by
`os.link` after the identity check. A concurrent writer can unlink that name and
replace it in the window. Python 3.10's own `os.link` contract states that when
`follow_symlinks=False` and the source is a symlink, the operation creates a
hard link to the symlink itself. The final artifact can therefore become a
symlink, despite `R-G8`, `R-G11`, threat controls T4-T6, and `TDW-009-AC1`.

Keeping the descriptor open does not by itself fix the defect because
`os.link` still names the source by directory entry. A post-link inode check
also cannot safely repair the result under this attacker model: between check
and unlink, the final name can be replaced, and the contract forbids deleting
an unverified foreign entry.

Bounded revision: select a publication primitive whose source identity is bound
to an open descriptor and whose destination creation is no-replace in one
kernel operation, or explicitly narrow the concurrent-writer threat model and
obtain user acceptance of the resulting reliability trade-off. If no
Python-3.10, standard-library, darwin-and-Linux primitive satisfies both
properties, trigger the existing stop condition rather than implementing the
named-temp hard-link design. Add a deterministic test that replaces the
temporary source after its last identity check and before publication, with
both a regular file and a symlink, and prove no final entry is created.

### High

#### H1 — Ancestor-link health cannot force a nonzero summary exit under the authorized validator changes

`R-S6` and `R-S12` require an ancestor-symlinked receipt or memory target to be
reported and force a nonzero exit (`requirements.md:88,94`). `R-S9` and `R-S10`
simultaneously make `validate_projects(..., require_complete=True)` the sole
root verdict (`requirements.md:91-92`). Current receipt-link validation checks
only `receipt.is_symlink()` and `receipt.is_file()`
(`validation.py:782-824`). Memory-link validation checks the final candidate
and repository containment but does not reject every symlinked ancestor
(`validation.py:827-885`). The design's statement that these states “already
produce a diagnostic” (`design.md:411-417`) is false.

`R-X4` authorizes exactly two unrelated validator hunks
(`requirements.md:105`), so implementation cannot make ancestor-link health a
validator diagnostic. Letting the summary invent a diagnostic or exit override
would violate the single-authority rule.

Bounded revision: either authorize the exact validator changes and regression
tests needed to make ancestor-symlinked authority paths invalid, or keep the
summary report informational and revise the nonzero promise through the
coordinator. Do not implement two competing validity authorities.

#### H2 — The pre-task baseline cannot prove the 43-path delta or derive the promised rollback

The baseline correctly records the current digest of
`config/model-routing.json`, all 15 files under `dogfood_v1`, and the TDW-006,
TDW-007, and TDW-008 files; every recorded digest reproduced successfully.
However, it records no digest, content snapshot, or task-start patch for any of
the seven tracked files the implementer will modify. It also does not record a
commit identity, and its working-tree section collapses the entire untracked
TDW-009 directory to one `??` entry (`baseline/pre-task-manifest.txt:62-69`).

Consequently the plan cannot compute a task-specific reverse patch “derived
from the baseline” (`plan.md:273-276,345-355`) or distinguish planning/reviewer
leaves created after the baseline from implementation leaves. The baseline also
omits `src/brichan/resources/__init__.py`, although the plan promises digest
comparison for `src/brichan/resources/**` (`plan.md:41-43,316`).

Bounded revision: before implementation, capture an implementation-start
baseline containing the exact 43-path allowlist, absence/presence plus digest
or content for every allowlisted path, all protected-resource files including
`src/brichan/resources/__init__.py`, the exact untracked leaf inventory, and a
stable repository identity. Define the exact command that computes the
implementation delta and reverse patch. Keep coordinator/planner/reviewer
artifacts outside that delta by capturing after this review or explicitly
excluding owner-scoped paths.

#### H3 — A successful descriptor-bound run can write to a detached directory while reporting the stale canonical path

The race tests deliberately replace the on-disk dossier path with a symlink
after obtaining its descriptor and expect all artifacts to land in the original
inode (`plan.md:171-180`). That proves containment, but the original inode may
now be renamed or detached from the requested
`<projects-root>/<project>/handoffs/<task-id>` path. The design performs no final
namespace-to-descriptor identity check and defines no nonzero “canonical path
changed during generation” result. It can therefore report exit `0` and action
paths at which the generated dossier does not exist.

Bounded revision: preserve descriptor-relative writes, but before success
re-walk the canonical chain read-only and compare each current directory's
device/inode with the held descriptors. Namespace drift must produce exit `1`
with a deterministic diagnostic; it must never be reported as successful
generation. Add project, handoffs, and dossier replacement tests both before
the first publication and between publications.

### Medium

#### M1 — The exact record type schema contradicts its own example and diagnostics

The example records artifact version as the string `"1"`
(`design.md:128-145`), while the diagnostic table uses
`artifacts.plan.version` as an integer position that rejects booleans
(`design.md:197-202`). The parsing rules never provide an exhaustive
top-level/per-artifact key-to-type table, so either interpretation is
implementable. The same example places a backtick-delimited evidence value at
`design.md:144`, although the structural rule refuses every backtick in an
evidence item (`design.md:177-189`).

Bounded revision: add an explicit schema table naming every key, exact type,
nullability, and element type; make the example valid under it; and tie each
exact-type test to that table. This must be resolved before `record.py` is
implemented.

#### M2 — Version-2 evidence still points to the mutable review location instead of the archived version-1 review

The five version-2 planning artifacts cite version-1 findings through
`handoffs/TDW-009/plan-review.md` at
`requirements.md:179,192`, `brief.md:124`, `options.md:214,218`,
`design.md:546`, and `plan.md:383,388`. The packet required the prior review to
be archived and this review to replace the standard path. Those citations now
point to artifact version 2 and no longer support the quoted version-1 line
ranges.

Bounded revision: supersede the affected planning artifacts and change every
prior-review evidence pointer to
`handoffs/TDW-009/versions/v1/plan-review.md`. Accepted artifacts must not rely
on a path whose content is intentionally replaced by each review version.

## Test-gap verification

| Prior test gap | Version-2 status |
| --- | --- |
| `TG1` post-preflight ancestor races | Partial. Project, handoffs, and dossier swaps are planned, but no final namespace-identity failure is asserted and no temporary-source substitution race is tested. |
| `TG2` write, flush/fsync, close, permission, and disk-full faults | Partial. `os.write`, `os.fsync`, `os.close`, `os.link`, and permission cases are planned. Missing are temporary-name inode mismatch, source substitution, cleanup `os.unlink` failure, directory-`fsync` failure, and bounded-temp-name exhaustion. |
| `TG3` duplicate keys, exact types, and structure injection | Partial. The classes are listed, but the artifact-version type and example contradictions make the expected exact-type tests indeterminate. |
| `TG4` generated output against the validator | Covered in `plan.md:204-219`, subject to resolving M1. |
| `TG5` partial adoption, duplicate IDs, ambiguous task, incomplete default | Covered, except ancestor-link invalidity cannot use the validator as planned and unreadable-artifact exit `1` versus unreadable-dossier exit `2` needs an exact boundary. |
| `TG6` `passed` floor versus one-item `not-required` rule | Covered explicitly at Levels 0, 1, and 2. |
| `TG7` authority-link ancestors and both independence arms | Independence coverage is complete. Ancestor-link coverage is specified but cannot satisfy the sole-authority exit contract without H1's revision. |
| `TG8` explicit Python 3.10 and before/after protection | Python 3.10.11 is present and the focused command is executable. Protection is incomplete because H2's baseline omits one resource file and every modified tracked-file snapshot. |
| `TG9` exact line budget and record-size metrics | Output and record metrics are present. The authored-value traversal still needs an exact counting algorithm so results are reproducible rather than manually interpreted. |

Additional required tests from this review:

- Replace the verified temporary source with a symlink and a regular file
  immediately before `os.link`; assert no final name is created.
- Replace the final name after a successful link but before any cleanup/check;
  prove cleanup never unlinks the replacement.
- Re-walk and inode-compare the canonical directory chain before returning zero;
  assert namespace drift exits one even though descriptor-relative writes stayed
  contained.
- Prove ancestor-link diagnostics originate from the existing validator after
  the authorized validator revision, not from a second summary verdict.
- Execute the exact 43-path delta command against a fixture containing unrelated
  untracked planning/reviewer files and pre-existing user changes.

## Exact path and protected-state verification

- The implementation allowlist arithmetic is correct: 7 modified tracked paths,
  7 new source/test paths, and 29 evaluation leaves expand to 43 unique paths.
  Both sample memories, all 22 standard artifacts, both receipts, both records,
  and `results.md` are present in the expansion.
- `config/model-routing.json` currently matches baseline digest
  `31466a36cef7e6966dec52211d14769e2c91b8ab1a7be33b468ebcf501a4838d`.
- All 15 baseline-listed `src/brichan/resources/dogfood_v1/` files currently
  match their recorded digests. No installed-dogfood change is authorized.
- The broader `src/brichan/resources/**` verification is incomplete because
  `src/brichan/resources/__init__.py` is absent from the baseline.
- The archived version-1 review exists at
  `versions/v1/plan-review.md` with SHA-256
  `eba30d0f1bbe448fa24bc180c6ec9a2518e63ce38307bc8cf22c46cc7948ddc4`.

## Residual risks and required human decisions

- Human decision required if portable descriptor-bound no-replace publication
  cannot be implemented with Python 3.10's standard library on both current
  POSIX platforms. Narrowing the concurrency guarantee is a reliability
  trade-off and cannot be assumed by the implementer.
- Coordinator decision required on whether ancestor-symlinked authority links
  become validator-invalid through an expanded `validation.py` scope or remain
  informational summary health. The current plan requires both outcomes.
- Coordinator action required to capture a complete implementation-start
  baseline before any implementation handoff.
- Residual risk retained honestly: synthetic fixture session inequality proves
  only string consistency, not independent review. Version 2 now states this
  correctly.
- Residual risk retained honestly: record/output line counts are proxies, not
  measurements of operator preference, evidence quality, time, tokens, or cost.
- No implementation, commit, routing change, installed-resource change,
  permission expansion, receipt mutation, deployment, publication, or remote
  action is authorized by this review.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:68-97`
  records the binding remediation decisions, the version-1 archival requirement,
  and the requirement to close every prior finding before implementation.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md:248-330`
  specifies the descriptor walk and named-temporary hard-link publication whose
  remaining source-name race is finding C1.
- Python 3.10.11's local `os.link` contract states that
  `follow_symlinks=False` links a source symlink itself, and the local runtime
  confirms `os.link` supports both `dir_fd` and `follow_symlinks`; this makes the
  raced-source failure concrete rather than hypothetical.
- `src/brichan/contracts/task_dossier/validation.py:782-885,1160-1195` shows the
  current authority-link checks and the project-level validator diagnostics,
  establishing H1's sole-authority contradiction.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/baseline/pre-task-manifest.txt:5-69`
  shows exactly which protected digests and coarse working-tree entries were
  captured; read-only digest verification reproduced every listed value and
  confirmed the missing resource/package and modified-file baselines.
- Expanding the allowlist in `plan.md:50-95` with
  `schema.ARTIFACTS` produced 43 total and 43 unique paths:
  7 modified, 7 new source/test, and 29 evaluation leaves.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v1/plan-review.md`
  preserves the 338-line prior review used to check `C1`, `H1-H6`, `M1-M2`, and
  all nine test-gap classes.

## Uncertainty

- It is unresolved whether a portable publication primitive satisfying the full
  no-overwrite, no-partial, no-source-rebinding contract exists within the
  authorized Python 3.10 standard-library and platform boundary. That is a stop
  condition, not permission to weaken the guarantee.
- No uncertainty remains about the verdict: the source-name race can publish a
  symlink at a final artifact path, so `TDW-009-AC1` is not presently
  dischargeable by plan version 2.
