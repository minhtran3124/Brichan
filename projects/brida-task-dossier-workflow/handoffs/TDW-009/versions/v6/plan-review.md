# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `plan-review`
- Artifact version: `6`
- Origin: `review:projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md@TDW-009-P6-v6`
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

- Reviewed plan ID: `TDW-009-P6`
- Reviewed plan version: `6`

## Claim or decision

CHANGES REQUIRED. `TDW-009-P6` version 6 closes the version-5 canonical-format,
directory-symlink, and touched-subset defects in the ordinary cases it tests. It
does not enforce equality to the accepted plan's exact 8 modified, 36 new, and
44 total paths: same-count substitutions can redefine the authorization and
still pass both preflight and delta. The snapshot directory is neither confined
to the repository nor opened without following ancestor symlinks. The required
generator static/import routing-neutrality test is also absent from the ordered
steps, and the strict manifest loader accepts a boolean version and malformed
length/digest rows. These are bounded version-7 corrections, but the first two
prevent this manifest from serving as the required authorization and protected-
state boundary for `TDW-009-AC5` and `TDW-009-AC6`.

This is the same permitted replacement independent stronger reviewer that
reviewed version 5. Reviewer session
`019fc201-6e8c-7ed1-9ae4-7f807c954c51`, route `review`, model
`gpt-5.6-sol`, and effort `high` are recorded in the reviewer-child receipt and
differ from planner session `3ebc7268-a8cd-464c-8d65-9920f2beac5c`
(`../TDWREV-009/receipt.md:3-28`; `receipt.md:18-30`).

## Version-5 finding and test-gap verification

| Version-5 item | Version-6 result | Independent disposition |
| --- | --- | --- |
| `H1` executable/canonical incompatibility | Closed | One mechanically extracted 344-line Python block emits canonical JSON and consumes it through the same loader. Its build output re-encoded byte-identically and passed preflight under Python 3.10.11. |
| `H2` directory symlinks omitted | Closed | A symlink to a directory emitted an `l` row, its target child was not traversed, and retargeting or replacing the entry with a real directory or regular file made preflight and delta nonzero. |
| `H3` truncated lists and subset delta | Partially closed | Counts 7 and 35 are rejected; 43 touched and 45 touched fail; 44 touched passes. Exact accepted-path membership remains unenforced, so a different 8/36/44 can pass. See H1. |
| Canonical round-trip test gap | Closed | Plan step 20 explicitly extracts the block and requires build-to-loader-to-preflight success (`plan.md:320-330`). |
| Directory-symlink test gap | Closed | Step 20 covers row emission, retargeting, real-directory replacement, regular-file replacement, and the exclusion boundary (`plan.md:331-335`). |
| Exact-list/touched-set test gap | Partially closed | Step 20 tests wrong counts and touched subsets/supersets, but never substitutes a different path while retaining 8/36/44 (`plan.md:325-338`). |
| Generator routing-neutrality test gap | Open | `R-G29` specifies the right two-part test, but no ordered step adds it to the generator suite. See H3. |

## Findings by severity

### Critical

None.

### High

#### H1 — Counts do not authenticate the accepted plan's exact 44 paths

The P6 amendment requires the modified list to equal the exact accepted
eight-item set, the new list to equal the exact accepted thirty-six-item set,
and their union to equal the exact accepted forty-four-item allowlist
(`task-packet.md:244-248`). The plan repeats that contract at
`plan.md:49-58,85-130`, and the threat model claims a forged allowlist is
guaranteed to be refused (`design.md:1223-1228`).

The literal executable contains only the numeric constants 8, 36, and 44
(`design.md:777-779`). `build` reads arbitrary external list files, and the
loader checks only count, uniqueness, sorting, present/absent classification,
and union cardinality (`design.md:891-898,945-963,971-980`). It contains no
frozen expected-path sets and performs no comparison to the plan's enumerated
paths.

The defect was reproduced on Python 3.10 with the mechanically extracted block.
One accepted modified path and one accepted new path were replaced by
`outside/forged-existing.txt` and `outside/forged-new.txt`, preserving 8/36/44.
The loader accepted the manifest and preflight returned `0`. After changing and
creating exactly the forged manifest's 44 paths, delta returned `0` and printed
`touched set equals all 44 authorized paths`; the two omitted accepted paths
remained untouched and both unauthorized paths were touched. Separate
same-count modified-only and new-only substitutions were also accepted.

Bounded revision: place the exact sorted eight-path and thirty-six-path tuples in
the literal executable (or another immutable value in that same reviewed
executable), require equality before build output or filesystem inspection, and
derive the 44-path union from those constants. Add modified-member, new-member,
misclassification, and forged-full-delta tests that retain the correct counts.

#### H2 — `snapshot_dir` can escape the repository and follows directory symlinks

The canonical schema and `R-B13` require a repository-relative snapshot
directory inside an excluded prefix (`design.md:655,707-708`;
`requirements.md:138-145`). The loader checks only that `snapshot_dir` is a
nonempty string (`design.md:924-925`). Preflight then passes it to
`os.path.join`; an absolute value discards `root`, and ordinary pathname
`os.listdir`/`open` follows ancestor symlinks (`design.md:1007-1023`).

Two independent probes passed incorrectly. A manifest naming an absolute
snapshot directory outside the fixture root was accepted and preflight returned
`0`. A lexically compliant path under the excluded TDW-009 prefix whose final
directory component was a symlink to an external snapshot directory also
returned `0`, claiming all eight snapshots authenticated. Leaf-symlink refusal
does not prevent this ancestor traversal.

This contradicts both containment and the claimed no-follow snapshot boundary,
and allows a coordinator-supplied manifest to make the worker read outside the
authorized checkout. Bounded revision: require a normalized safe relative path
strictly below one frozen excluded prefix, reject absolute paths, `..`, and
backslashes, and open every snapshot-directory component with descriptor-
relative `O_DIRECTORY | O_NOFOLLOW` before listing and authenticating leaves.
Add absolute, traversal, non-excluded, and symlinked-ancestor cases.

#### H3 — The required generator static/import routing probe is not planned

The P6 amendment requires a generator probe proving that generator code neither
reads nor names `config/model-routing.json` (`task-packet.md:249-250`). `R-G29`
correctly specifies two arms in an already-authorized test: static source
inspection and import plus dry-run generation under an open spy
(`requirements.md:96`).

Plan step 14 remains a summary-test step. Its only open assertion says merely
`no routing manifest opened`; it does not import the generator, run dry-run
generation, or perform the generator source check (`plan.md:263-276`). The
verification grep supplies only the static half (`plan.md:366-367`). The
planning-session probe against existing `scaffold.py` demonstrates that the
technique works, but cannot test the future `generate.py` and is not an
implementation instruction (`plan.md:467-470`).

Bounded revision: explicitly add both `R-G29` arms to
`tests/unit/test_task_dossier_generator.py`: scan the generator module source for
both forbidden spellings, then import it and run a real dry-run generation under
a path-open spy, asserting no opened path ends in `model-routing.json` and no
`model_routing` module remains in `sys.modules`.

### Medium

#### M1 — The strict loader accepts values its guaranteed schema calls malformed

The design says one strict loader refuses malformed rows and a capture version
other than integer `1` (`design.md:662-670`), while the threat table claims exact
integer typing in both loaders (`design.md:1215-1217`). The implementation uses
ordinary equality for the version (`design.md:920-921`), so JSON `true` is
accepted because Python `True == 1`. Row validation requires only that `length`
has exact `int` type and `sha256` has string type (`design.md:930-938`); it does
not reject negative lengths or non-digest strings.

The extracted loader accepted `capture_map_version: true`. It also accepted a
row with `length: -1` and `sha256: "not-a-sha256"`. These mutations do not make
an honest `build` emit malformed data, but they falsify the strict-loader and
malformed-manifest guarantees used to authenticate a stored baseline.

Bounded revision: require `type(capture_map_version) is int`, nonnegative row
lengths, exactly 64 lowercase hexadecimal digest characters, and the fixed
zero-length/zero-digest pair for `o` rows. Add direct loader tests for each; the
current wrong-integer-version and boolean-length cases do not cover them.

### Low

None.

## Reproduced executable matrix

The fenced capture block was extracted mechanically from `design.md`, not
retyped. Exactly one matching block was found; its 344 lines compiled and ran
under Python 3.10.11.

- **Canonical format:** `build` returned `0`; its output was accepted by the same
  loader and canonical re-encoding was byte-identical.
- **Directory symlink:** the link emitted one `l` row; no target child appeared.
  Retargeting failed preflight and delta. Replacement by a real directory
  removed the row and failed; replacement by a regular file changed `l` to `f`
  and failed.
- **Nominal allowlist arithmetic:** the accepted expansion is 8 modified, 36
  new, 44 total, all unique. Counts 7 and 35 were rejected, and all 36 intended
  new paths are absent from both the repository map and filesystem.
- **Touched equality:** touching the manifest's full 44 returned `0`; touching
  43 returned `1` and named the missing path; touching 44 plus one returned `1`
  and named the unexpected path.
- **Outside changes:** post-capture changes to one pre-existing tracked file and
  one pre-existing untracked file each failed preflight and appeared as
  unexpected at delta.
- **Repository capture:** the extracted build produced canonical JSON with 333
  rows. It included `config/model-routing.json`, the current pre-existing
  `references.md` and `tasks.md` changes, and exactly all 16 filesystem entries
  under `src/brichan/resources/`. All eight modified paths are tracked. No
  planning artifact contains a hard-coded 64-hex routing digest.
- **Routing probe technique:** under Python 3.10, static inspection of existing
  `scaffold.py` found neither forbidden spelling. Import and a 12-action dry run
  under a `Path.open` spy opened 11 templates, zero routing paths, and loaded zero
  `model_routing` modules. H3 concerns the missing future-generator test, not the
  feasibility of the technique.

## Rechecked inherited contracts

- **No rollback mutation:** every rollback reference in version 6 is historical,
  prohibitive, or a separately reviewed future commit revert. There is no
  restore/delete-from-snapshot procedure, reverse patch, checkout operation, or
  rollback test. Identity-verified cleanup of the generator's own private
  temporary is not rollback.
- **Body line feeds:** the schema makes `sections[].body[]` a one-rendered-line
  class and permits line feeds only in `claim`; plan step 10 requires the
  negative-body and positive-claim pair (`design.md:191-208`;
  `plan.md:206-225`). The literal record has one body element and no embedded
  line feed.
- **Synthetic fixture:** independent extraction found one fenced JSON record,
  the exact 11 `ARTIFACTS` in order, 17 keys per artifact, 13 non-null session
  fields all prefixed `synthetic-fixture-`, all 11 claims disclaiming real review,
  correct plan/review links, and review sessions distinct from the plan session.
  An independently reconstructed reference render produced exactly 410 lines
  with zero current-validator diagnostics under both default and complete gates.
- **Summary sole-validator semantics:** the design derives the root verdict only
  from `validate_projects(root, require_complete=True)`, composes scope and
  verdict codes without letting task selection suppress root diagnostics, and
  treats authority-link checks as health while validator diagnostics own
  invalidity (`design.md:579-635`). Current source inspection reproduced
  index-based discovery, partial-adoption discovery, and project-level duplicate
  ID diagnostics.
- **Generator publication and lock boundary:** all rendering precedes mutation;
  descriptor-relative directory creation may precede the dossier lock, but no
  temporary or artifact mutation does. Publication is full-write, file-`fsync`,
  inode-check, no-replace hard-link, identity-verified private-temporary cleanup,
  directory-`fsync`, and final canonical re-walk. The post-link observation is
  correctly bounded against the excluded process (`design.md:457-558`).
- **Python 3.10 compatibility:** Python 3.10.11 reproduced the capture matrix.
  Separate local probes confirmed `O_NOFOLLOW`, `O_DIRECTORY`, nonblocking
  directory `flock`, required `dir_fd` operations, no-follow hard-link creation,
  matching-inode publication, and file and directory `fsync`.
- **Protected and immutable state:** the current map covers routing, resources,
  project memory, and the 13 leaves in each of TDW-006, TDW-007, and TDW-008.
  Review hashes reproduce as v1 `eba30d0f...8ddc4`, v2
  `5494bfff...bebd`, v3 `69626937...66065`, v4 `15aa144e...c5861`, and v5
  `9f3f3de5...a87a0`. The standard v5 review was archived at `versions/v5/`
  byte-identically before this artifact replaced it.

## Test gaps

- No capture test substitutes a wrong modified or new member while preserving
  exact counts and classifications, then proves a forged full-44 delta fails.
- No test rejects an absolute, traversing, non-excluded, or ancestor-symlinked
  `snapshot_dir`.
- No strict-loader test supplies a boolean capture version, negative length, or
  malformed digest.
- No ordered generator test performs both required routing-neutrality arms; the
  summary no-open test and command-line grep are not equivalent.

## Residual risks and required decisions

- Planner revision is required before implementation. The four corrections fit
  existing test files and the literal design block; no forty-fifth
  implementation path is needed.
- After a passing re-review, the coordinator must generate a fresh canonical
  implementation-start manifest and snapshots. No superseded baseline or review
  authorizes implementation.
- Accepted residual risks remain point-in-time observation, deliberate `.env`
  and `.DS_Store` blind spots, an orphan private temporary after a crash, and no
  detection guarantee against the excluded same-identity process. Synthetic
  identifier inequality remains a consistency signal, not proof of review.
- No implementation, planning edit, receipt or baseline update, routing or
  resource change, project-memory update, commit, remote action, publication,
  deployment, secret access, or permission expansion is authorized by this
  review.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:230-262`
  defines the complete P6 amendment and review identity.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md:639-1129`
  defines the canonical manifest and supplies the exact executable reproduced.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan.md:42-156,312-393`
  defines the precondition, exact 44-path authorization, tests, and verification.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/requirements.md:64-170`
  supplies generator, summary, baseline, recovery, and compatibility contracts.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v1/plan-review.md`
  through `versions/v5/plan-review.md` preserve the accumulated review history.
- `projects/brida-task-dossier-workflow/handoffs/TDWREV-009/receipt.md:3-34`
  records this replacement session, exact model and effort, and review ownership.

## Uncertainty

- No uncertainty remains about the verdict. A same-count forged allowlist and an
  external/symlinked snapshot directory each passed the literal gate, directly
  contradicting mandatory P6 contracts.
- No implementation exists yet. Generator publication faults, the actual
  generator routing probe, Level 1 fixture metrics, full repository gates, and
  code review remain execution-time evidence and are not credited here.
