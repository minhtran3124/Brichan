# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `plan-review`
- Artifact version: `5`
- Origin: `review:projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md@TDW-009-P5-v5`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fc201-6e8c-7ed1-9ae4-7f807c954c51`
- Effective route: `review`
- Effective model: `gpt-5.6-sol`
- Effective effort: `high`
- Reviewing session: `019fc201-6e8c-7ed1-9ae4-7f807c954c51`
- Review verdict: `CHANGES REQUIRED`

## Review target

- Reviewed plan ID: `TDW-009-P5`
- Reviewed plan version: `5`

## Claim or decision

CHANGES REQUIRED. `TDW-009-P5` version 5 correctly removes every rollback
mutation, preserves the 44-path authorization, tightens `sections[].body[]`,
retains validator-owned summary validity, and keeps the generator's publication
and lock threat boundary honest. It is not safe to authorize implementation.
The exact capture/preflight/delta block is incompatible with the canonical
capture format it is required to consume, omits symlinks that point to
directories from the supposedly complete map, and does not enforce either all
36 planned-new paths or exact touched-set equality with all 44 authorized paths.
Those three defects prevent the mandatory implementation-start gate and
handoff delta from establishing `TDW-009-AC5` and `AC6`.

This is the one permitted replacement independent stronger review. Reviewer
session `019fc201-6e8c-7ed1-9ae4-7f807c954c51`, route `review`, model
`gpt-5.6-sol`, and effort `high` are recorded in the reviewer-child receipt and
differ from planner session `3ebc7268-a8cd-464c-8d65-9920f2beac5c`
(`../TDWREV-009/receipt.md:3-28`; `receipt.md:17-30`).

## Version-4 finding verification

| Version-4 item | Version-5 result | Evidence and disposition |
| --- | --- | --- |
| `H1` incomplete outside-allowlist baseline | Partially closed | The exact block detects ordinary post-capture changes to pre-existing tracked and untracked regular files, and a read-only repository run produced 333 rows including the current changes to routing, references, and tasks. It is not a complete map because symlink-directory entries are omitted, and the canonical file cannot be consumed. See H1 and H2. |
| `H2` unsafe rollback | Closed | Requirements and plan contain no rollback command, procedure, or test. Snapshots are evidence-only, failure recovery is fix-forward inside the 44 paths, and a later commit revert is explicitly outside TDW-009 (`requirements.md:149-156`; `design.md:710-734`; `plan.md:63-74`). |
| `H3` shape-only start precondition | Open | The row-only probe validates current bytes and snapshot digests, but the required canonical representation crashes and the external modified/new lists are not checked for exact membership. See H1 and H3. |
| `M1` body-element newline ambiguity | Closed | The schema now makes `sections[].body[]` a one-line class and keeps only `claim` multi-line (`design.md:201-216`). The literal record contains no embedded body line feed, and plan step 10 requires the negative-body/positive-claim pair. |

## Findings by severity

### Critical

None.

### High

#### H1 — The executable preflight cannot consume the required canonical capture

The canonical format has headers, `[rows]`, and `[snapshots]`, with snapshot
lines keyed by the same modified paths as the row section
(`design.md:690-703`; `plan.md:40-57`). The executable instead makes `build`
emit only raw rows, reads the whole capture as if it were raw rows, byte-compares
that whole text to the rebuilt raw-row string, and parses every nonblank line as
a row (`design.md:801-835,817-842`; invocation at `design.md:891-904`).

The two representations cannot round-trip. In an exact Python 3.10 execution,
a row-only capture passed preflight. Wrapping the identical rows in the required
canonical headers and sections made preflight emit header drift and then raise
`IndexError`: the `[snapshots]` line for `tracked.txt` overwrote that path's
four-column `[rows]` entry in `parse_rows`, so the digest access at
`design.md:842` had no fourth field. Even without that collision, the headers
and section markers make `current != capture` permanently true.

This is a hard start blocker: plan step 1 requires this exact preflight to pass
before any implementation write (`plan.md:140-146`), while the stop condition
requires the canonical headers and sections (`plan.md:365-372`).

Bounded revision: choose one representation and make all three modes consume it.
Prefer making `build` emit the canonical format and adding a strict parser that
validates the version, the exact ten exclusions, one `[rows]` section, exactly
eight snapshot mappings, and no duplicate section/path keys; preflight and
delta must compare only canonical parsed rows. Add a canonical build-to-
preflight round-trip test and malformed/duplicate-section tests. A row-only test
does not discharge this finding.

#### H2 — Symlinks to directories are absent from the complete no-follow map

The contract requires one row for every non-directory entry and specifically
requires every symlink row to hash its link-target string
(`requirements.md:134-140`; `design.md:677-688`). `build_map` uses
`os.walk(..., followlinks=False)`, retains entries from `dirnames`, and emits
rows only for `filenames` (`design.md:786-798`). `os.walk` classifies a symlink
that points to a directory in `dirnames`; with `followlinks=False` it does not
descend through it, but the current loop never records it either.

The exact block was reproduced in a temporary fixture. A symlink to a regular
file produced an `l` row; a symlink to a directory produced no row. Retargeting
that directory symlink between capture and delta left both maps byte-identical,
and `delta` returned `0` with `unexpected` empty. This is a point-in-time change
between observations, not the excluded concurrent same-identity attacker.

The omission contradicts the claimed complete map, the absolute no-follow
symlink-row guarantee at `design.md:907-917`, and complete outside-allowlist
change detection. It can also blind the protection check if a future protected
subtree entry is a directory symlink.

Bounded revision: inspect every `dirnames` entry with no-follow `lstat` before
descent. Emit an `l` row and remove it from descent when it is a symlink; descend
only into actual directories. Fail closed on inspection/listing errors. Add
tests for a pre-existing directory symlink, retargeting it, replacing it with an
empty real directory, and a symlink at an exclusion boundary; every non-excluded
entry change must alter the map and fail preflight/delta as applicable.

#### H3 — The gates accept incomplete path lists and a strict subset of the 44-path delta

The plan requires all 36 planned-new paths absent and the final delta equal to
all 44 authorized paths (`plan.md:42-57,76-121,306-319,350-359`). The executable
trusts three external whitespace-split list files without validating their
counts or exact membership. Preflight iterates only paths present in the supplied
modified and new lists (`design.md:834-856`); the canonical layout does not
enumerate planned-new paths at all (`design.md:690-703`). A truncated new list
therefore narrows the check silently. In the reproduced fixture, a capture-time
collision at an intended new path was present in both the filesystem and map,
but omission of that path from `new_paths` let preflight return `0` and claim
that new paths were absent.

Delta has the same fail-open shape. It rejects removals and paths outside the
allowlist, but never computes `missing = allowlist - (changed union created)`
(`design.md:864-883`). A reproduced delta that changed one of two authorized
paths returned `0` and printed `delta OK: 1 of 2 authorized paths touched`.
Thus the exact command at `plan.md:358` does not establish its stated
`delta equals the 44 authorized paths` expectation, and the exact-set evaluation
requirement at `requirements.md:179-182` is not mechanically covered.

Bounded revision: make the canonical capture enumerate exact `[allowlist-modified]`
and `[allowlist-new]` sets or equivalently authenticate dedicated list files;
validate exact equality to the accepted 8/36/44 expansion before checking state.
Preflight must refuse missing, extra, duplicate, or misclassified entries.
Delta must require `(changed union created) == allowlist`, in addition to no
removals and empty `unexpected`, and must return nonzero for either missing or
extra paths. Add strict-subset, strict-superset, duplicate, truncated-list, and
capture-time-collision tests.

### Medium

None.

### Low

None.

## Reproduced safety and evidence checks

- **Exact allowlist arithmetic:** expanding the current eleven-member
  `ARTIFACTS` tuple produced 8 modified tracked paths, 7 new source/test paths,
  and 29 evaluation leaves: 44 total and 44 unique. All eight modified paths are
  tracked. All 36 planned-new paths are currently absent, and none falls under
  the capture exclusions. This verifies the plan's enumeration, not H3's
  executable enforcement.
- **Ordinary outside-allowlist changes:** with a row-only capture, changing one
  pre-existing tracked regular file and one pre-existing untracked regular file
  put both in `unexpected` and returned `1`. H2 bounds the claim: directory
  symlinks are invisible.
- **Routing and installed resources:** the exact block's current repository map
  had 333 rows and included `config/model-routing.json`, the pre-existing
  modified `references.md` and `tasks.md`, and all 16 current entries under
  `src/brichan/resources/`. No current planning artifact contains a hard-coded
  routing digest. These protections remain non-operational until H1-H3 are
  remediated.
- **No rollback mutation:** every version-5 rollback reference is historical or
  prohibitive. There is no restore/delete-from-snapshot command, reverse patch,
  checkout command, rollback test, or in-task revert. Publication's
  identity-verified temporary cleanup is not rollback.
- **Body line-feed rule:** the literal record has one `sections[].body[]`
  element and no embedded line feed. The position table refuses body line feeds
  while checking multi-line `claim` per line (`design.md:201-216`), and plan step
  10 explicitly tests both sides.
- **Worked synthetic fixture:** independent extraction found one fenced JSON
  block, exactly 11 `ARTIFACTS` keys in order, exactly 17 keys per artifact, all
  non-null session values prefixed `synthetic-fixture-`, all 11 claims stating
  that the data is synthetic and proves no real review, matching plan/review
  linkage, and review sessions distinct from the plan session. A reference
  render without template ledes produced the claimed 410 lines and zero current
  validator diagnostics under both default and complete gates. Fixture receipts
  and the Level 1 sample remain execution-time evidence, as the plan correctly
  states.
- **Summary sole-validator semantics:** the design derives the root verdict from
  `validate_projects(root, require_complete=True)`, never lets task selection
  suppress root diagnostics, and treats authority-link checks as health whose
  invalidity comes from the two bounded validator diagnostics
  (`design.md:588-644`). Current source inspection reproduced index-based
  discovery, partial-adoption discovery, and project-level duplicate-ID
  diagnostics. No competing summary validity authority is planned.
- **Generator publication and lock boundary:** render precedes all mutation;
  descriptor-relative directory creation may precede the dossier-directory
  `flock`; no temporary or artifact mutation precedes the lock; publication is
  full-write/`fsync`/no-replace hard-link with a point-in-time post-link check;
  and final success requires canonical inode re-walk (`design.md:466-567`). The
  narrowed same-identity limitation is stated consistently.
- **Python 3.10:** the exact 144-line capture block compiled under Python
  3.10.11. Local 3.10 probes confirmed `O_NOFOLLOW`, `O_DIRECTORY`, directory
  `flock`, required `dir_fd` operations, `os.link(..., follow_symlinks=False)`,
  file and directory `fsync`, and matching-inode hard-link publication.
- **Immutable history:** archived review hashes reproduced as v1
  `eba30d0f...8ddc4`, v2 `5494bfff...ebd`, v3 `69626937...66065`, and v4
  `15aa144e...5861`. The current planning artifacts cite prior findings through
  immutable versioned paths.

## Test gaps

- No planned test feeds the specified canonical capture format through the
  exact preflight and delta parser; existing row-only fixture claims would miss
  H1.
- The symlink-row test in plan step 20 does not require a symlink that points to
  a directory, retargeting that link, or replacing it with another entry type.
- No test requires the modified/new/all list sets themselves to equal 8/36/44,
  or requires delta to fail when an authorized path is untouched.
- `R-G29` says generator code neither reads nor names the routing manifest, but
  the explicit no-open test in plan step 14 is summary-only. Add a generator
  static/import probe so routing neutrality does not depend solely on final
  capture comparison.

## Residual risks and required decisions

- Planner revision is required before implementation: define one parseable
  canonical capture, include symlink-directory rows, and make all list and delta
  equalities fail closed. This is a bounded version-6 correction; it does not
  require a forty-fifth implementation path.
- After a passing re-review, the coordinator must create a fresh compliant
  implementation-start capture and snapshots. The current superseded baseline
  is not implementation authorization.
- The accepted residual risks remain: the capture and delta are point-in-time
  observations; `.env` and `.DS_Store` are explicit blind spots; the generator's
  post-link check does not guarantee detection against the excluded process; a
  crash may leave an orphan temporary; and synthetic identifier inequality is
  not proof of real independence.
- No implementation, planning edit, receipt or baseline update, routing or
  resource change, commit, remote action, permission expansion, deployment,
  publication, or secret access is authorized by this review.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:185-228`
  fixes the complete-map, no-rollback, no-45th-path, body-line, and P5 review
  requirements.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md:647-917`
  supplies the canonical layout and exact executable block reproduced above.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan.md:40-146,302-390`
  supplies the 44-path precondition, start gate, exact-delta expectation,
  verification commands, and stop conditions.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/requirements.md:134-182`
  supplies the complete-map, preflight, delta, recovery, compatibility, and
  exact evaluation-set contracts.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v1/plan-review.md`
  through `versions/v4/plan-review.md` preserve the full accumulated finding and
  remediation history used in this review.
- `projects/brida-task-dossier-workflow/handoffs/TDWREV-009/receipt.md:3-28`
  records this replacement session, exact model, effort, and exclusive review
  ownership.

## Uncertainty

- No uncertainty remains about the verdict. A compliant canonical baseline
  cannot pass the exact preflight as written, and the two successful fail-open
  probes directly contradict required exact-set guarantees.
- No implementation exists yet, so implementation-only publication faults,
  Level 1 line counts, generated fixture receipts, full repository gates, and
  code review remain future evidence and are not credited here.
