# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `requirements`
- Artifact version: `6`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v5/plan-review.md@TDW-009-P5-v5+task-packet-amendment-6`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `3ebc7268-a8cd-464c-8d65-9920f2beac5c`
- Effective route: `plan`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Version 6 supersession

Versions 1 to 5 are preserved byte-identically under `versions/v1/` to
`versions/v5/`. Version 6 is bounded to the three reproduced executable defects
in the replacement review of `TDW-009-P5`, plus its four test gaps. Every prior
review is cited through an immutable archived path.

Four coordinator decisions in the version-6 amendment are binding inputs:

1. **One canonical JSON implementation-start manifest**, emitted and consumed by
   the same executable capture, preflight, and delta code. No row-only shadow
   format and no section-stripping convention.
2. The complete no-follow map records symlinks found in **both** file-name and
   directory-name positions. A symlink to a directory is an `l` row and is never
   traversed; retargeting it or replacing its entry type makes preflight and
   delta nonzero.
3. **Fail closed on set equality**: modified equals the exact 8-item set, new the
   exact 36-item set, their union the exact 44-item allowlist, and successful
   post-implementation `touched` equals all 44. A strict subset or superset is a
   failure.
4. A **generator static and import probe** in an already-authorized test file
   proves generator code neither reads nor names `config/model-routing.json`.

## Threat-model boundary

**Out of scope.** A non-cooperating process running under the same OS identity
that mutates directory entries while the generator holds the dossier lock, or
that mutates repository files during capture, preflight, implementation, or the
after-delta check.

**Claimed.** Safety against pre-existing symlinks at any path component; against
namespace drift the generator can observe; against ordinary concurrent Brichan
invocations that cooperate with the lock; against every specified write, `fsync`,
close, link, cleanup, and directory-`fsync` failure; and refusal of malformed,
hostile, or injected record and manifest content.

**Not claimed.** Neither prevention nor detection against the excluded process.
The post-publication check, the capture map, the start preflight, and the
after-delta check are all **point-in-time observations**, never compare-and-swap.

## Generator requirements

| ID | Requirement |
| --- | --- |
| `R-G1` | One structured record file, read once, produces exactly the eleven artifacts named in `schema.py:17-29`. |
| `R-G2` | Generation is dry-run by default. |
| `R-G3` | Phase A: the record is loaded, fully validated, and all eleven bodies rendered in memory before any filesystem mutation whatsoever. |
| `R-G4` | Phase B: every directory in the chain is opened with `O_RDONLY \| O_DIRECTORY \| O_NOFOLLOW` relative to its already-open parent. |
| `R-G5` | A component that is a symlink or is not a directory aborts before any write. Both `ELOOP` and `ENOTDIR` are refusals. |
| `R-G6` | An ancestor replaced by a symlink after its descriptor is obtained cannot redirect a write outside the projects root. |
| `R-G7` | Missing directories are created with `os.mkdir(..., dir_fd=parent)` using single validated components; this may precede the dossier lock. |
| `R-G8` | Phase C: `fcntl.flock(dossier_fd, LOCK_EX \| LOCK_NB)` is acquired immediately after the dossier descriptor is opened and before any temporary-file or artifact mutation. The losing invocation creates no temporary and no artifact leaf. |
| `R-G9` | Phase D: publication writes a private temporary, `fsync`s it, verifies device and inode against the writing descriptor, then `os.link(..., follow_symlinks=False)`. `os.rename` and `os.replace` are forbidden. |
| `R-G10` | Publication never overwrites; `EEXIST` preserves the existing file and forces the nonzero outcome. |
| `R-G11` | The post-link `os.lstat` check is a point-in-time best-effort observation, not a detection guarantee. |
| `R-G12` | A temporary is unlinked only after its identity re-verifies against the creating descriptor. |
| `R-G13` | No artifact is ever published in a partial state. |
| `R-G14` | Temporary names are `O_EXCL`-created and bounded; exhaustion is a refusal. |
| `R-G15` | Multi-file partial progress is retained only when every retained artifact is complete, with a nonzero exit and a partial-adoption diagnostic. |
| `R-G16` | The dossier descriptor is `fsync`-ed after publication; failure forces a nonzero exit. |
| `R-G17` | Before returning success the canonical chain is re-walked and device and inode compared per level; drift exits nonzero. |
| `R-G18` | Record identity must equal the identity supplied on the command line. |
| `R-G19` | The generator derives only `Task ID`, `Task level`, `Artifact`, `Owner`, the index `Task identity` triple, the canonical receipt path, and the index status table. |
| `R-G20` | The generator never derives, defaults, or infers any judgment-bearing value. |
| `R-G21` | A review artifact that is `passed` must carry an explicit verdict from `REVIEW_VERDICTS`. |
| `R-G22` | Any placeholder in a position the contract requires to be concrete is a refusal. |
| `R-G23` | Evidence depth mirrors `validation.py:276-355` exactly. |
| `R-G24` | Any value matching `PERSONAL_PATH_PATTERNS` is a refusal. |
| `R-G25` | For `index`, only `INDEX_PROJECTION_SECTIONS` are emitted and supplemental sections are refused. |
| `R-G26` | The record is parsed under the exhaustive key-to-type tables in `design.md`, with `object_pairs_hook` duplicate rejection, `type(v) is ...` checks, JSON `null` as the only null, and the four cross-record refusals. `design.md` carries one literal complete eleven-artifact record and the extraction test loads that fenced block from `design.md` itself. |
| `R-G27` | Structural injection is refused per rendered position class. `sections[].body[]` is exactly one rendered line and refuses any embedded line feed; `claim` is the only multi-line class and is checked per line. Backticks are permitted except in backtick-wrapped positions. |
| `R-G28` | Rendering is deterministic; no timestamp, hostname, process ID, or absolute path reaches artifact content. |
| `R-G29` | Generator code neither reads nor names the routing manifest. This is proved by a **two-part probe in an already-authorized test file**: a **static** check that no generator module source contains `model-routing.json` or `model_routing`, and an **import** check that importing the generator and running a dry-run generation opens no path ending in `model-routing.json` and leaves no `model_routing` module in `sys.modules`. Routing neutrality must not depend solely on the final capture comparison. |

## Validator requirements

| ID | Requirement |
| --- | --- |
| `R-V1` | `_validate_receipt_link` rejects a receipt path with any symlinked ancestor, with a new named diagnostic. |
| `R-V2` | `_validate_memory_link` rejects a memory path with any symlinked ancestor, with a new named diagnostic. |
| `R-V3` | Both share one no-follow helper that resolves nothing. |
| `R-V4` | Every existing validator diagnostic keeps its condition, field locator, and message text. Exactly two are added. |
| `R-V5` | Regression tests in `tests/unit/test_task_dossier_validator.py` cover both authority paths and the unchanged clean case, asserting the diagnostics originate from the validator. |
| `R-V6` | `TDW-006` through `TDW-009` produce no new diagnostic. |

## Summary requirements

| ID | Requirement |
| --- | --- |
| `R-S1` | The summary is read-only. |
| `R-S2` | It reports per-artifact applicability and phase state for all eleven artifacts in `ARTIFACTS` order. |
| `R-S3` | Evidence depth is reported against the rule that applies: the level floor for `passed`, the one-item rule for `not-required`, `not-applicable` otherwise. |
| `R-S4` | Effective model provenance is read from the artifacts, never from the routing manifest. |
| `R-S5` | Plan and review identity are reported with any disagreement flagged. |
| `R-S6` | Authority-link health is reported as health only; invalidity is the validator's verdict. |
| `R-S7` | Review independence is reported as two separate arms per review. |
| `R-S8` | Every rendered form states that identifier inequality is a consistency signal, not proof of independence. |
| `R-S9` | The root verdict comes from `validate_projects(root, require_complete=True)`; task selection never suppresses a root-level diagnostic. |
| `R-S10` | The complete gate is the default and only exit semantics. |
| `R-S11` | Exit `2` means the requested scope cannot be evaluated: an absent or unlistable projects root, an absent or unlistable requested dossier, a `--task` matching no discovered dossier, or one matching more than one. Exit `1` means the scope was evaluated and the validator produced a diagnostic, including an existing but unreadable `index.md` and root-level partial adoption. A scope code in `{0, 2}` and a verdict code in `{0, 1}` compose. |
| `R-S12` | Stale state is reported and forces a nonzero exit through the validator verdict. |
| `R-S13` | An unreadable artifact is reported with path and reason, never silently omitted. |
| `R-S14` | Output is deterministic; the machine-readable form carries the same facts and exit code. |

## Baseline, preflight, and delta requirements

| ID | Requirement |
| --- | --- |
| `R-B1` | The implementation-start baseline is **one canonical JSON manifest** with exactly six top-level keys: `capture_map_version`, `exclusions`, `snapshot_dir`, `allowlist_modified`, `allowlist_new`, `rows`. The same executable emits it in `build` and consumes it in `preflight` and `delta` through **one strict loader**. No second representation exists. |
| `R-B2` | `rows` holds one entry per non-directory entry outside the exclusions, sorted by path, each with exactly `path`, `type`, `length`, `sha256`. `type` is `f`, `l`, or `o`. |
| `R-B3` | A **symlink is recorded wherever it is found**, in file-name or directory-name position, as an `l` row whose length and digest are those of the **link target string**. A symlink to a directory is emitted as a row and **removed from descent**; only real directories are traversed. Listing and `lstat` errors fail closed. |
| `R-B4` | The map covers every observed file outside the exact ten-entry exclusion set enumerated in `design.md`, so pre-existing tracked modifications and pre-existing untracked leaves are included. |
| `R-B5` | The allowlists live **inside** the manifest. The loader fails closed unless `allowlist_modified` is exactly **8** unique sorted paths all present in `rows`, `allowlist_new` is exactly **36** unique sorted paths none present in `rows`, and their union is exactly **44** unique paths. There are no external list files for `preflight` or `delta` to trust. |
| `R-B6` | The strict loader additionally fails closed on invalid JSON, a non-object root, a duplicate JSON key at any depth, a top-level key set other than the six, a `capture_map_version` other than `1`, an `exclusions` object that is not the ten frozen entries, a malformed row, a `length` that is not an exact `int`, a duplicate row path, or unsorted rows. |
| `R-B7` | The eight modified tracked paths have byte snapshots named `sha256(path.encode("utf-8")).hexdigest() + ".bin"`. `preflight` requires the snapshot directory to contain **exactly** those eight files and nothing else, and authenticates each no-follow against its `rows` digest. |
| `R-B8` | **Snapshots are evidence only.** No worker may restore from, delete from, or write through a snapshot. |
| `R-B9` | Before any implementation write, `preflight` rebuilds the map, compares parsed rows against the manifest, authenticates the snapshots, and verifies every planned-new path absent from both `rows` and the filesystem. Any mismatch is a stop, reported per path. |
| `R-B10` | At handoff, `delta` rebuilds the map and computes `changed`, `created`, `removed`, `unexpected`, and `missing`. It fails unless `removed` is empty, `unexpected` is empty, `missing` is empty, and `(changed ∪ created)` **equals** the 44-path allowlist. A strict subset and a strict superset both fail. |
| `R-B11` | A post-capture modification to a pre-existing **tracked** file and to a pre-existing **untracked** file outside the allowlist must each fail preflight and land in `unexpected` at delta. |
| `R-B12` | A capture-time collision at a planned-new path makes the manifest invalid; a post-capture collision makes preflight fail. Neither is ever attributed to this implementation. |
| `R-B13` | `snapshot_dir` must sit inside an excluded prefix so snapshot files never become rows of the map that authenticates them. |
| `R-B14` | Every guarantee in `R-B1` through `R-B13` is a point-in-time observation. No requirement claims compare-and-swap safety. |

## Recovery requirements

| ID | Requirement |
| --- | --- |
| `R-R1` | TDW-009 contains **no rollback** — no promise, procedure, test, or command. |
| `R-R2` | On implementation failure the worker **fixes forward** within its 44 authorized paths. |
| `R-R3` | After a successful scoped commit, recovery is a **separately reviewed commit revert**, outside this task. |
| `R-R4` | `git checkout --`, restoring from a snapshot, and deleting from a snapshot are forbidden to every worker. |

## Safety and compatibility requirements

| ID | Requirement |
| --- | --- |
| `R-X1` | `ARTIFACTS`, `METADATA_FIELDS`, `PHASE_STATES`, `APPLICABILITY_STATES`, and `MINIMUM_EVIDENCE_ITEMS` keep their current values. |
| `R-X2` | `scaffold.py` is not modified; the generator imports only `dossier_path`. |
| `R-X3` | `parser.py` is not modified. |
| `R-X4` | `validation.py` receives exactly five enumerated hunks. |
| `R-X5` | `__init__.py` keeps `main` bound to `validation.main`; CLI entries are exported only as `generate_main` and `summary_main`. |
| `R-X6` | `config/model-routing.json` is user-owned protected state: not modified, reverted, absorbed, or interpreted, and **no planning or implementation artifact records an expected digest for it**. It appears in `rows` like any other file. |
| `R-X7` | Every file under `src/brichan/resources/` is unchanged, verified through the capture map. |
| `R-X8` | Standard library only on the `>=3.10` floor. The capture block and the focused suites are run explicitly under Python 3.10. |
| `R-X9` | Existing dossiers `TDW-006`, `TDW-007`, and `TDW-008` remain byte-identical. |
| `R-X10` | New wrappers under `scripts/` stay thin bootstrap shims. |
| `R-X11` | The implementation allowlist is exactly **44 paths**: 8 modified tracked, 7 new source and test, 29 evaluation leaves. Preflight and delta tests are appended to already-authorized test files; **no forty-fifth path is created**. |
| `R-X12` | No migration is performed. Hand-authored dossiers stay first-class. |

## Evaluation requirements

| ID | Requirement |
| --- | --- |
| `R-E1` | Evaluation dossiers are unmistakably synthetic; every session identity matches `synthetic-fixture-` and every sample artifact claims non-authoritative test data. |
| `R-E2` | No synthetic verdict, session, or identifier inequality is presented as evidence of real review; `results.md` carries the fixed declaration, asserted by a contract test. |
| `R-E3` | Every evaluation output path is in the closed leaf allowlist. |
| `R-E4` | Each sample carries eleven artifacts, a schema-valid `receipt.md`, and the canonical project-memory file, with receipts validated against the isolated root. |
| `R-E5` | The durable evaluation records the AC3 metric plus record lines, record bytes, `authored_values`, and combined lines. |
| `R-E6` | `authored_values` uses the exact algorithm and fixed `DECLARED_ORDER` in `design.md`. |

## Remediation traceability

| Item from `versions/v5/plan-review.md` | Requirements | Plan steps |
| --- | --- | --- |
| `H1` executable cannot consume the canonical capture | `R-B1`, `R-B6` | 1, 20 |
| `H2` symlinks to directories absent from the map | `R-B3` | 1, 20 |
| `H3` gates accept truncated lists and a strict subset | `R-B5`, `R-B10` | 1, 20 |
| Test gap: canonical build-to-preflight round trip, malformed and duplicate-section cases | `R-B1`, `R-B6` | 20 |
| Test gap: symlink-to-directory, retarget, type replacement, exclusion boundary | `R-B3` | 20 |
| Test gap: list sets equal 8/36/44; delta fails on an untouched authorized path | `R-B5`, `R-B10` | 20 |
| Test gap: generator static and import routing probe | `R-G29` | 14 |

## Acceptance-criteria traceability

| Parent AC | Requirements | Discharged by |
| --- | --- | --- |
| `TDW-009-AC1` | `R-G1` through `R-G18` | Plan steps 4, 5, 11, 12 |
| `TDW-009-AC2` | `R-G19` through `R-G27`, `R-E4` | Plan steps 3, 6, 10, 13, 16 |
| `TDW-009-AC3` | `R-G28`, `R-E3`, `R-E5`, `R-E6` | Plan steps 15, 16, 17 |
| `TDW-009-AC4` | `R-S1` through `R-S14` | Plan steps 7, 8, 14 |
| `TDW-009-AC5` | `R-B1` through `R-B14`, `R-G29`, `R-V4`, `R-V6`, `R-X1` through `R-X12` | Plan steps 1, 2, 8, 14, 18, 19, 20 |
| `TDW-009-AC6` | all | Plan steps 13, 14, 16, 19, 20 |
| `TDW-009-AC7` | `R-E1`, `R-E2`, `R-E5`, `R-E6` | Plan steps 17, 18 |
| `TDW-009-AC8` | all | Plan step 21 |

## Claim or decision

Version 6 makes the implementation-start gate and the handoff delta mechanically
sound, which is the only thing that stood between version 5 and implementation.
One canonical JSON manifest is emitted and consumed by the same strict parser, so
the format the coordinator is told to produce is exactly the format the code
accepts. A symlink is a row wherever it is found, including the directory-name
position that version 5 silently skipped. The allowlists live inside the manifest
and are validated to 8, 36, and 44 before any state is examined, and the delta
requires the touched set to equal all 44, so a strict subset now fails where
version 5 reported success. `R-G29` gains a static and import probe so routing
neutrality is proved directly rather than inferred from a capture comparison.

## Evidence

- The literal capture block in `design.md` was **extracted mechanically and run
  on Python 3.10.11** before this artifact was called passed. Against an 8/36/44
  fixture: `build` produced a canonical manifest its own strict loader accepted;
  `preflight` exited `0`; touching all 44 paths exited `0`; touching 43 exited
  `1` naming the untouched path; touching 44 plus one outside path exited `1`
  naming the unexpected path. The extracted block was byte-identical to the
  source it was written from.
- The same extracted block closed `H2` in four cases: a pre-existing symlink to a
  **directory** produced an `l` row; retargeting it changed that row's digest and
  made both preflight and delta exit `1`; replacing it with a real directory
  removed the row; replacing it with a regular file flipped `type` from `l` to
  `f`. Version 5's block produced no row at all for that entry.
- Fourteen manifest mutations each failed closed on the extracted block, covering
  every condition in `R-B6`, plus snapshot-directory exact membership and
  snapshot digest corruption for `R-B7`.
- Run against **this repository**, the extracted block produced a canonical
  manifest with 333 rows, 8 / 36 / 44, `config/model-routing.json` captured at
  its current user-owned bytes, both pre-existing tracked modifications present,
  and all 16 files under `src/brichan/resources/`.
- The `R-G29` probe technique was demonstrated read-only against an existing
  package module: a static source scan reported no `model-routing.json` and no
  `model_routing` occurrence, and an import under an `open` spy recorded no
  routing file opened and no `model_routing` module in `sys.modules`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v5/plan-review.md:65-92,94-121,122-151,217-229`
  state `H1`, `H2`, `H3`, and the four test gaps this version closes, each with
  the reviewer's own reproduction.

## Uncertainty

- The capture map, preflight, and delta remain point-in-time observations; the
  excluded same-identity process defeats all three.
- `.env` and `.DS_Store` are deliberate blind spots.
- The 333-row figure is this working tree at planning time, not a contract.
- `R-B10` requires the touched set to equal all 44. If a future review narrows
  the authorized scope, the manifest counts and the three constants in the
  capture block must change together; until they do, the block fails closed.
- The `R-G29` import probe was demonstrated on an existing module because the
  generator does not exist yet; its real subject is created at implementation
  time.
- The worked record was validated through a reference renderer written for this
  planning session, not the implementation.
