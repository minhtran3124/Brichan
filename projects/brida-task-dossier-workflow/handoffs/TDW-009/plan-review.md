# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `plan-review`
- Artifact version: `7`
- Origin: `review:projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md@TDW-009-P7-v7`
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
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `TDW-009-P7`
- Reviewed plan version: `7`

## Claim or decision

PASS. `TDW-009-P7` version 7 closes every acceptance-blocking version-6
finding and all four associated test gaps. The mechanically extracted literal
executable freezes the exact accepted 8 modified and 36 new paths, derives the
44-path union from those tuples, confines snapshot reads to one descriptor-
walked no-follow directory, and rejects the specified malformed manifest values.
The complete P6 regression matrix still behaves as required under Python
3.10.11. Plan step 10 now orders both generator routing-neutrality arms against
the real future generator in the authorized generator unit-test file.

Two low-severity prose defects remain, bounded below. Neither changes the exact
executable, the implementation precondition in `plan.md`, the authorized path
set, or any acceptance test. They do not block implementation.

This is the same permitted replacement independent stronger reviewer that
reviewed versions 5 and 6. Reviewer session
`019fc201-6e8c-7ed1-9ae4-7f807c954c51`, route `review`, model
`gpt-5.6-sol`, and effort `high` are recorded in the reviewer-child receipt and
differ from planner session `3ebc7268-a8cd-464c-8d65-9920f2beac5c`
(`../TDWREV-009/receipt.md:3-28`; `receipt.md:18-30`).

## Version-6 finding and test-gap verification

| Version-6 item | Version-7 result | Independent disposition |
| --- | --- | --- |
| `H1` counts did not authenticate the accepted 44 paths | Closed | The literal block holds exact frozen tuples matching the plan's 8 and 36 paths. Modified substitution, new substitution, both together, and modified/new misclassification were all rejected with unauthorized and missing paths named. A forged full-44 delta exited `1`. |
| `H2` snapshot path escaped or followed ancestors | Closed | Absolute, traversing, embedded-traversal, backslash, non-excluded, and alternate values were rejected by the loader. Final-component and intermediate-ancestor symlinks were rejected by the descriptor walk at CLI exit `1`. |
| `H3` generator routing probe absent from ordered work | Closed | Step 10 explicitly orders source scans over `record.py`, `generate.py`, and `summary.py`, then imports `generate`, runs a real dry run under a path-open spy, and checks both opened paths and `sys.modules` (`plan.md:219-250`). |
| `M1` boolean version and malformed rows accepted | Closed | Boolean and wrong integer versions, negative and boolean lengths, malformed, uppercase, and wrong-length digests, and both `o`-row invariant violations were rejected. |
| Same-count/forged-delta test gap | Closed | Step 20 names all four same-count mutations and the forged-full-delta refusal (`plan.md:369-373`). |
| Snapshot containment test gap | Closed | Step 20 names six value mutations and both symlink positions (`plan.md:374-378`). |
| Strict-value test gap | Closed | Step 20 covers boolean and float versions, negative and boolean lengths, digest classes, and both other-row invariant arms (`plan.md:379-382`). |
| Generator two-arm test gap | Closed | Both arms are now explicit ordered generator-unit-test work, not a summary assertion or grep substitute. |

## Findings by severity

### Critical

None.

### High

None.

### Medium

None.

### Low

#### L1 — Two capture-version statements are stale or stronger than the executable

The P7 design says the implementation-start capture is taken after plan version
6 is accepted (`design.md:642-646`), while the governing P7 plan correctly
requires capture after the current plan is accepted (`plan.md:42-47`). The plan
also says a manifest captured under version 6 will now be refused
(`plan.md:520-524`). An honest P6 build using the exact accepted lists produced a
manifest that the extracted P7 loader accepted, because the capture schema
version remains `1` and the values satisfy the stricter rules.

This does not bypass the P7 precondition: the coordinator is expressly ordered
to build a fresh manifest after P7 acceptance, and preflight still compares all
current rows and authenticates snapshots. It is nevertheless inaccurate durable
documentation. Bounded correction outside implementation: change
`design.md:644` to version 7 and remove the claim that every v6-produced manifest
is mechanically refused, or add authenticated plan provenance if that stronger
property is actually required.

#### L2 — `R-B7` uses `non-f` where the executable and row model mean `o`

`R-B7` says every non-`f` row must use the zero pair
(`requirements.md:139-145`). Read literally, that includes an `l` symlink row and
conflicts with `R-B3`, which requires an `l` row to hash its link-target string.
The design row rules and executable correctly apply the zero-pair invariant only
to type `o` (`design.md:698-706,1059-1063`). The requested invariant probes used
type `o` and both failed as intended. Bounded documentation correction: replace
“non-`f`” with “`o`” or “other/non-file entry” in `R-B7`.

## Reproduced Python 3.10 executable matrix

Exactly one fenced Python block containing the canonical capture docstring was
found. Its 458 literal lines compiled and ran under Python 3.10.11; no block was
retyped or normalized.

- **Frozen authorization:** the literal tuples equal the independently expanded
  accepted lists exactly: 8 modified, 36 new, 44 unique and disjoint. `build`
  takes no list inputs. Same-count modified, new, combined, and
  misclassification mutations each failed. The forged-full-delta CLI returned
  `1` at the strict loader and named the substituted modified path.
- **Snapshot value confinement:** absolute, leading traversal, embedded
  traversal, backslash, non-excluded, and alternate excluded-prefix paths each
  failed before snapshot filesystem access.
- **Snapshot descriptor confinement:** replacing the final `snapshot` component
  with a directory symlink returned `1`; replacing the intermediate `capture`
  component with a directory symlink returned `1`. Restoring real directory
  components restored a clean preflight.
- **Strict values:** `capture_map_version` values `true` and `2`; row lengths
  `-1` and `true`; 64 non-hex characters, uppercase hex, and a 63-character
  digest; and type-`o` rows with nonzero length or nonzero digest all failed the
  loader. The existing float-version and malformed-row tests remain ordered.
- **Canonical path:** `build` returned `0`, its canonical JSON re-encoded
  byte-identically, the same loader accepted it, and clean preflight returned
  `0` with eight authenticated snapshots and all 36 frozen new paths absent.
- **Touched equality:** a full accepted 44-path touch returned `0`; 43 touched
  returned `1` and named the missing path; 44 plus one returned `1` and named the
  unexpected path.
- **Directory symlinks:** a symlink to a directory produced an `l` row and its
  target child was not traversed. Retargeting it, replacing it with a real
  directory, and replacing it with a regular file each made preflight and delta
  nonzero.
- **Outside drift:** modifying one pre-existing tracked and one pre-existing
  untracked outside-allowlist file made preflight return `1`; delta returned `1`
  and named both as unexpected.
- **Snapshot faults:** a stray file, corrupted leaf, removed leaf, and symlinked
  leaf each made preflight nonzero.

## Rechecked inherited contracts

- **Repository capture and exact scope:** the P7 block built canonical JSON over
  this checkout with 333 rows and exact 8/36/44 tuples. All eight modified paths
  are tracked; all 36 planned-new paths are absent from rows and the filesystem.
  The frozen tuples match the plan's 8 + 7 + 29 expansion element for element.
- **Protected state:** the map includes `config/model-routing.json`, the current
  pre-existing `references.md` and `tasks.md` changes, all 16 filesystem entries
  under `src/brichan/resources/`, and all 13 leaves in each of TDW-006, TDW-007,
  and TDW-008. No current planning artifact contains a hard-coded 64-hex routing
  digest.
- **Generator routing neutrality:** the ordered step now contains both required
  arms and names the authorized `tests/unit/test_task_dossier_generator.py`.
  The import arm is correctly left as implementation-time evidence because
  `generate.py` does not yet exist.
- **Generator publication and lock boundary:** all rendering precedes mutation;
  descriptor-relative directory creation may precede the dossier lock, but no
  temporary or artifact mutation does. Publication remains full-write,
  file-`fsync`, inode-check, no-replace hard-link, identity-verified private-
  temporary cleanup, directory-`fsync`, and final canonical re-walk. The
  excluded-process limitation remains point-in-time and explicit
  (`design.md:457-558`).
- **Summary sole-validator semantics:** root validity still comes only from
  `validate_projects(root, require_complete=True)`; task selection cannot
  suppress root diagnostics; authority-link observations are health details and
  validator diagnostics own invalidity (`design.md:580-638`). Current source
  still provides index discovery, partial-adoption discovery, and project-level
  duplicate-ID diagnostics.
- **Worked fixture and body line feeds:** independent extraction found one JSON
  block, the exact 11 artifacts in order, 17 keys each, all 13 non-null session
  values prefixed `synthetic-fixture-`, 11 claims disclaiming real review,
  correct plan/review linkage, and review sessions distinct from the plan
  session. Its single body element has no embedded line feed. An independently
  reconstructed render produced exactly 410 lines and zero current-validator
  diagnostics under both default and complete gates. Step 10 retains the
  negative-body and positive-multiline-claim tests.
- **No rollback mutation:** rollback references are historical, prohibitive, or
  a separately reviewed future commit revert. There is no restore/delete-from-
  snapshot procedure, reverse patch, checkout operation, or rollback test.
- **Python 3.10:** Python 3.10.11 ran the literal matrix. Separate probes
  confirmed nonblocking directory `flock`, `O_DIRECTORY`, `O_NOFOLLOW`, required
  `dir_fd` operations, no-follow hard-link publication with matching inode, and
  file and directory `fsync`.
- **Immutable review history:** archived hashes reproduce as v1
  `eba30d0f...8ddc4`, v2 `5494bfff...bebd`, v3 `69626937...66065`, v4
  `15aa144e...c5861`, v5 `9f3f3de5...a87a0`, and v6
  `52731ccb...c4f27c`. Version 6 was archived byte-identically before this
  standard artifact was created.

## Test gaps

No acceptance-blocking test gap remains in the accepted plan. L1 and L2 are
prose corrections; neither needs a new implementation path or test surface.

## Residual risks and required decisions

- The coordinator must generate the implementation-start manifest and snapshots
  after P7 acceptance, at the exact frozen location, before any implementation
  write. A structurally accepted older manifest is not authorization under the
  plan's coordinator-owned precondition.
- Capture, preflight, delta, and the post-publication observation remain
  point-in-time. The excluded non-cooperating same-identity process is not
  prevented or guaranteed to be detected.
- `.env` and `.DS_Store` remain explicit map blind spots. A crash may leave an
  orphan private temporary. A partial implementation cannot hand off because
  delta requires all 44 paths touched. These costs are stated and accepted.
- No implementation, receipt or baseline update, routing or resource change,
  project-memory update, commit, remote action, publication, deployment, secret
  access, or permission expansion is authorized by this plan review itself.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:264-297`
  defines the complete P7 amendment and exact review target.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md:642-1250`
  defines the canonical manifest and supplies the exact executable reproduced.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan.md:42-165,219-250,340-438`
  defines the fresh-capture precondition, exact 44-path authorization, ordered
  routing probes, adversarial matrix, and verification commands.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/requirements.md:70-176`
  supplies generator, summary, baseline, recovery, and compatibility contracts.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v1/plan-review.md`
  through `versions/v6/plan-review.md` preserve the accumulated independent
  review history.
- `projects/brida-task-dossier-workflow/handoffs/TDWREV-009/receipt.md:3-34`
  records this replacement session, exact model and effort, and review ownership.

## Uncertainty

- No uncertainty remains about the verdict. Every acceptance-blocking P6 probe
  was independently inverted by the extracted P7 block, and every inherited
  positive and negative scenario retained its required result.
- No implementation exists yet. Generator publication faults, the actual
  generator routing import probe, Level 1 fixture metrics, full repository gates,
  and code review remain execution-time evidence and are not credited here.
