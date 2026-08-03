# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `requirements`
- Artifact version: `7`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v6/plan-review.md@TDW-009-P6-v6+task-packet-amendment-7`
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

## Version 7 supersession

Versions 1 to 6 are preserved byte-identically under `versions/v1/` to
`versions/v6/`. Version 7 is bounded to the four fail-closed corrections in the
replacement review of `TDW-009-P6`, plus its four test gaps. Every prior review
is cited through an immutable archived path.

Four coordinator decisions in the version-7 amendment are binding inputs:

1. The exact sorted **eight modified** and **thirty-six new** path tuples are
   frozen inside the reviewed literal executable. `build`, the loader, preflight,
   and delta compare manifest lists to those constants, derive the forty-four
   union only from them, and reject same-count substitutions and
   misclassification.
2. **One repository-relative snapshot directory is frozen** in the executable;
   the manifest may only repeat that exact value. Absolute, traversing,
   backslash-containing, and alternate paths are refused, every component is
   opened from the repository descriptor with `O_DIRECTORY | O_NOFOLLOW`, and
   leaves are authenticated descriptor-relatively without ever following an
   ancestor symlink.
3. The loader's guaranteed schema is genuinely strict: exact **non-boolean**
   integer version, **nonnegative** exact-integer lengths, digests of exactly
   **64 lowercase hexadecimal** characters, and the **zero-length, zero-digest**
   invariant for non-file rows, with direct malformed-manifest tests.
4. **Both generator routing-neutrality arms are explicit in the ordered
   generator unit-test step**: forbidden-spelling source inspection, and import
   plus a real dry-run under a path-open spy, asserting no routing opens and no
   loaded routing module.

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
| `R-G29` | Generator code neither reads nor names the routing manifest, proved by **two arms placed in the ordered generator unit-test step**, not merely stated here: a **static** arm scanning the sources of `record.py`, `generate.py`, and `summary.py` for both forbidden spellings `model-routing.json` and `model_routing`, and an **import** arm that imports the generator, runs a **real dry-run generation** under a path-open spy, and asserts no opened path ends in `model-routing.json` and no `model_routing` module remains in `sys.modules`. A summary-side no-open assertion and a command-line grep are not equivalent. |

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
| `R-B1` | The implementation-start baseline is **one canonical JSON manifest** with exactly six top-level keys, emitted by `build` and consumed by `preflight` and `delta` through **one strict loader**. |
| `R-B2` | `rows` holds one entry per non-directory entry outside the exclusions, sorted by path, each with exactly `path`, `type`, `length`, `sha256`. |
| `R-B3` | A **symlink is recorded wherever it is found**, in file-name or directory-name position, as an `l` row hashing the **link target string**, and is removed from descent. Listing and `lstat` errors fail closed. |
| `R-B4` | The map covers every observed file outside the exact ten-entry exclusion set, so pre-existing tracked modifications and untracked leaves are included. |
| `R-B5` | The **exact sorted eight-path and thirty-six-path tuples are frozen inside the executable**. `build` emits them; the loader requires the manifest's `allowlist_modified` and `allowlist_new` to **equal those tuples element for element**; and `ALLOWLIST_ALL` is **derived from the constants**, never from the manifest. Counting is not sufficient: a same-count substitution and a misclassification between the two lists are both refused, with the offending path named. |
| `R-B6` | The loader fails closed on invalid JSON, a non-object root, a duplicate JSON key at any depth, a top-level key set other than the six, an `exclusions` object that is not the ten frozen entries, a duplicate row path, unsorted rows, or a malformed row. |
| `R-B7` | Value-level strictness is exact: `capture_map_version` must be the **non-boolean integer** `1`; every row `length` must be an exact **nonnegative** integer; every `sha256` must be **exactly 64 lowercase hexadecimal** characters; and every non-`f` row must record **length `0` and the all-zero digest**. |
| `R-B8` | `snapshot_dir` is **one frozen repository-relative path** inside a frozen excluded prefix. The manifest may only repeat it exactly. Absolute paths, `..` traversal, backslashes, empty or `.` components, non-excluded prefixes, and alternate paths are all refused before the filesystem is touched. |
| `R-B9` | The snapshot directory is reached by **walking every component from the repository descriptor with `O_RDONLY \| O_DIRECTORY \| O_NOFOLLOW`**, so no ancestor symlink is ever followed. Listing uses that descriptor; each leaf is opened `O_RDONLY \| O_NOFOLLOW` relative to it and confirmed a regular file by `fstat` before hashing. |
| `R-B10` | The directory must contain **exactly** the eight expected snapshot files and nothing else, each authenticated against its `rows` digest. |
| `R-B11` | **Snapshots are evidence only.** No worker may restore from, delete from, or write through a snapshot. |
| `R-B12` | Before any implementation write, `preflight` rebuilds the map, compares parsed rows, authenticates the snapshots, and verifies every frozen planned-new path absent from both `rows` and the filesystem. Any mismatch is a stop. |
| `R-B13` | At handoff, `delta` fails unless `removed` is empty, `unexpected` is empty, `missing` is empty, and `(changed ∪ created)` **equals `ALLOWLIST_ALL`**. A strict subset and a strict superset both fail. |
| `R-B14` | A post-capture modification to a pre-existing tracked or untracked file outside the allowlist must fail preflight and land in `unexpected` at delta; a capture-time collision at a planned-new path makes the manifest invalid and a post-capture collision fails preflight. |
| `R-B15` | Every guarantee in `R-B1` through `R-B14` is a point-in-time observation. No requirement claims compare-and-swap safety. |

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

| Item from `versions/v6/plan-review.md` | Requirements | Plan steps |
| --- | --- | --- |
| `H1` counts do not authenticate the accepted 44 paths | `R-B5` | 1, 20 |
| `H2` `snapshot_dir` escapes the repository and follows ancestor symlinks | `R-B8`, `R-B9`, `R-B10` | 1, 20 |
| `H3` the generator routing probe is in no ordered step | `R-G29` | 10 |
| `M1` the loader accepts a boolean version and malformed rows | `R-B7` | 20 |
| Test gap: same-count member substitution and forged full-44 delta | `R-B5` | 20 |
| Test gap: absolute, traversing, non-excluded, ancestor-symlinked `snapshot_dir` | `R-B8`, `R-B9` | 20 |
| Test gap: boolean version, negative length, malformed digest | `R-B7` | 20 |
| Test gap: both routing-neutrality arms in the generator suite | `R-G29` | 10 |

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

Version 7 makes the manifest unable to redefine what implementation may touch or
where the worker reads. The accepted 8-path and 36-path tuples are frozen inside
the reviewed executable and compared element for element; the 44-path union is
derived from those constants; so a same-count substitution or a misclassification
is refused rather than counted as valid. The snapshot directory is one frozen
repository-relative value, walked component by component from the repository
descriptor with `O_DIRECTORY | O_NOFOLLOW`, so neither an absolute value nor an
ancestor symlink can redirect the read. The strict loader now enforces the schema
it always claimed. Both generator routing-neutrality arms move from a
requirement into the ordered step that creates them.

## Evidence

- The literal capture block in `design.md` was **extracted mechanically and run
  on Python 3.10.11** before this artifact was called passed; the extracted file
  was byte-identical to the source it was built from. `build` now takes no
  path-list arguments and emits the frozen tuples.
- **`R-B5`, five probes:** substituting one accepted modified path, one accepted
  new path, both at once, and swapping one path between the lists — each keeping
  8 / 36 / 44 — were refused with the offending path named; a forged full-44
  delta, which version 6 accepted with `touched set equals all 44 authorized
  paths`, exits `1`.
- **`R-B8` and `R-B9`, eight probes:** absolute, `..`-traversing,
  embedded-traversal, backslash, non-excluded, and alternate `snapshot_dir`
  values were refused before any filesystem access; a symlink at the final
  snapshot component and at an intermediate ancestor were each refused by the
  descriptor walk; restoring real directories returned `0`.
- **`R-B7`, seven probes:** `capture_map_version` of `true` and `1.0`, row
  `length` of `-1` and `true`, uppercase and malformed digests, and a non-file
  row with a non-zero length were each refused.
- **Carried-forward regression, thirteen scenarios re-run under the version-7
  executable:** canonical capture and clean preflight exited `0`; a full 44-path
  touch exited `0`; 43 and 45 touched each exited `1`; a symlink-to-directory
  retarget failed at preflight and delta; replacement by a real directory and by
  a regular file each failed; outside-allowlist tracked and untracked changes
  each failed; a stray, a corrupted, and a symlinked snapshot each failed; the
  restored baseline exited `0`.
- The record extraction test still passes against the rewritten `design.md`:
  one fenced JSON block, eleven artifacts, seventeen keys each, four
  cross-record rules, and zero `validate_dossier` diagnostics under both gates.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v6/plan-review.md:70-99,101-123,125-145,149-167,249-256`
  state `H1`, `H2`, `H3`, `M1`, and the four test gaps this version closes, each
  with the reviewer's own reproduction.

## Uncertainty

- The capture map, preflight, and delta remain point-in-time observations; the
  excluded same-identity process defeats all three.
- Freezing the 44 paths and the snapshot directory inside the executable couples
  the plan to the tool: any future scope or layout change requires editing that
  block and re-reviewing it. That is the accepted cost of an unforgeable
  authorization.
- `.env` and `.DS_Store` remain deliberate blind spots.
- The `R-G29` import arm was demonstrated on an existing module because the
  generator does not exist yet; its real subject is created at implementation
  time.
- The worked record was validated through a reference renderer written for this
  planning session, not the implementation.
