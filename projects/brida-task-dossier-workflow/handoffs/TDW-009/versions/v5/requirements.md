# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `requirements`
- Artifact version: `5`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md@TDW-009-P4-v4+task-packet-amendment-5`
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

## Version 5 supersession

Versions 1 to 4 are preserved byte-identically under `versions/v1/` to
`versions/v4/`. Version 5 exists because independent review of `TDW-009-P4`
version 4 returned `CHANGES REQUIRED` with three high findings and one medium.

Every citation of a prior review names an immutable archived path. Four
coordinator decisions in the version-5 amendment are binding inputs:

1. The implementation-start baseline is a **complete no-follow capture map** of
   every observed repository file outside an exact enumerated exclusion set,
   recording path, type, byte length, and SHA-256, including pre-existing tracked
   changes and untracked leaves. The eight modified tracked paths additionally
   carry authenticated byte snapshots. An exact executable preflight re-creates
   the map, byte-compares it, verifies every snapshot, and verifies every
   planned-new path absent before any implementation write. Any mismatch is a
   stop.
2. **Automatic and in-task rollback is removed from TDW-009** — every promise,
   procedure, and test. On failure the worker fixes forward within its 44 paths;
   after a successful scoped commit, recovery is an explicitly reviewed commit
   revert. **No worker may restore or delete from snapshots.**
3. Exact before/after delta checks and preflight tests live in an
   already-authorized integration or contract test file. **No forty-fifth path
   is authorized.**
4. `sections[].body[]` is exactly one rendered line and refuses embedded line
   feeds. Safe multi-line `claim` remains allowed and is checked per line.

## Threat-model boundary

**Out of scope.** A non-cooperating process running under the same OS identity
that mutates directory entries while the generator holds the dossier lock, or
that mutates repository files during capture, preflight, implementation, or the
after-delta check.

**Claimed.** Safety against pre-existing symlinks at any path component; against
namespace drift the generator can observe; against ordinary concurrent Brichan
invocations that cooperate with the lock; against every specified write, `fsync`,
close, link, cleanup, and directory-`fsync` failure; and refusal of malformed,
hostile, or injected record content.

**Not claimed.** Neither prevention nor detection against the excluded process.
The post-publication check, the capture map, the start preflight, and the
after-delta check are all **point-in-time observations**. None is a
compare-and-swap and none may be described as one. No requirement below may be
read as a detection guarantee.

## Generator requirements

| ID | Requirement |
| --- | --- |
| `R-G1` | One structured record file, read once, produces exactly the eleven artifacts named in `schema.py:17-29`. |
| `R-G2` | Generation is dry-run by default. |
| `R-G3` | Phase A: the record is loaded, fully validated, and all eleven bodies rendered in memory before any filesystem mutation whatsoever. |
| `R-G4` | Phase B: every directory in the chain is opened with `O_RDONLY \| O_DIRECTORY \| O_NOFOLLOW` relative to its already-open parent. No pathname below the projects root is re-resolved for a write. |
| `R-G5` | A component that is a symlink or is not a directory aborts before any write. Both `ELOOP` and `ENOTDIR` are refusals. |
| `R-G6` | An ancestor replaced by a symlink after its descriptor is obtained cannot redirect a write outside the projects root. |
| `R-G7` | Missing directories are created with `os.mkdir(..., dir_fd=parent)` using single validated components. This may occur before the dossier lock exists. |
| `R-G8` | Phase C: `fcntl.flock(dossier_fd, LOCK_EX \| LOCK_NB)` is acquired immediately after the dossier descriptor is opened and before any temporary-file or artifact mutation. A conflicting holder is refused, never awaited, and creates no temporary and no artifact leaf. |
| `R-G9` | Phase D: each artifact is published by writing a private temporary, writing it fully, `fsync`-ing it, verifying device and inode against the writing descriptor, then `os.link(..., follow_symlinks=False)`. `os.rename` and `os.replace` are forbidden. |
| `R-G10` | Publication never overwrites. `EEXIST` means the artifact appeared in the window and is reported `preserve`; a collision therefore preserves the existing file and forces the nonzero outcome. |
| `R-G11` | Immediately after a successful link the final name is checked with `os.lstat(..., dir_fd=dossier_fd)` for regular-file type and matching device and inode. An observed mismatch exits nonzero and the entry is not unlinked. This is a point-in-time best-effort observation, not a detection guarantee. |
| `R-G12` | A temporary is unlinked only after its identity re-verifies against the creating descriptor. Cleanup failure never converts a failure into success. |
| `R-G13` | No artifact is ever published in a partial state. |
| `R-G14` | Temporary names are `O_EXCL`-created and bounded; exhaustion is a refusal. |
| `R-G15` | Multi-file partial progress is retained only when every retained artifact is complete, with a nonzero exit and an explicit partial-adoption diagnostic. |
| `R-G16` | The dossier descriptor is `fsync`-ed after publication; failure forces a nonzero exit. |
| `R-G17` | Before returning success the canonical chain is re-walked read-only and each level's device and inode compared against the held descriptors. Drift exits nonzero. |
| `R-G18` | Record identity must equal the identity supplied on the command line. |
| `R-G19` | The generator derives only `Task ID`, `Task level`, `Artifact`, `Owner`, the index `Task identity` triple, the canonical receipt path, and the index status table. |
| `R-G20` | The generator never derives, defaults, or infers any judgment-bearing value. |
| `R-G21` | A review artifact that is `passed` must carry an explicit verdict from `REVIEW_VERDICTS`. |
| `R-G22` | Any placeholder in a position the contract requires to be concrete is a refusal. |
| `R-G23` | Evidence depth mirrors `validation.py:276-355` exactly. |
| `R-G24` | Any value matching `PERSONAL_PATH_PATTERNS` is a refusal. |
| `R-G25` | For `index`, only `INDEX_PROJECTION_SECTIONS` are emitted and supplemental sections are refused. |
| `R-G26` | The record is parsed under the exhaustive key-to-type tables in `design.md`, with `object_pairs_hook` duplicate rejection, `type(v) is ...` checks, JSON `null` as the only null, and the four cross-record consistency refusals. `design.md` carries one literal complete eleven-artifact record with seventeen keys each, and the extraction test loads that fenced block from `design.md` itself. |
| `R-G27` | Structural injection is refused per rendered position class. **`sections[].body[]` is a distinct class: each element is exactly one rendered line and refuses any embedded line feed**, so rendering, line counts, and `authored_values` are implementation-independent. **`claim` is the only multi-line class**: line feeds are permitted and every line is checked separately for headings, table rows, `- <label>:` fields, and fences. Backticks are permitted in every class except backtick-wrapped. |
| `R-G28` | Rendering is deterministic; no timestamp, hostname, process ID, or absolute path reaches artifact content. |
| `R-G29` | The generator never reads the routing manifest and names neither `model-routing.json` nor `model_routing`. |

## Validator requirements

| ID | Requirement |
| --- | --- |
| `R-V1` | `_validate_receipt_link` rejects a receipt path with any symlinked ancestor, with a new named diagnostic. |
| `R-V2` | `_validate_memory_link` rejects a memory path with any symlinked ancestor, with a new named diagnostic. |
| `R-V3` | Both share one no-follow helper that resolves nothing. |
| `R-V4` | Every existing validator diagnostic keeps its condition, field locator, and message text. Exactly two are added. |
| `R-V5` | Regression tests in `tests/unit/test_task_dossier_validator.py` cover a symlinked ancestor for each authority path and the unchanged clean case, asserting the diagnostics originate from the validator. |
| `R-V6` | `TDW-006` through `TDW-009` produce no new diagnostic. |

## Summary requirements

| ID | Requirement |
| --- | --- |
| `R-S1` | The summary is read-only. |
| `R-S2` | It reports per-artifact applicability and phase state for all eleven artifacts in `ARTIFACTS` order. |
| `R-S3` | Evidence depth is reported against the rule that applies: the level floor for `passed`, the one-item rule for `not-required`, `not-applicable` otherwise. |
| `R-S4` | Effective model provenance is read from the artifacts, never from the routing manifest. |
| `R-S5` | Plan and review identity are reported with any disagreement flagged. |
| `R-S6` | Authority-link health is reported as health only; invalidity is the validator's verdict under `R-V1` and `R-V2`. |
| `R-S7` | Review independence is reported as two separate arms per review. |
| `R-S8` | Every rendered form states that identifier inequality is a consistency signal, not proof of independence. |
| `R-S9` | The root verdict comes from `validate_projects(root, require_complete=True)`. Selecting a task never suppresses a root-level diagnostic. |
| `R-S10` | The complete gate is the default and only exit semantics. |
| `R-S11` | Exit codes follow actual discovery. Exit `2` means the requested scope cannot be evaluated: an absent or unlistable projects root, an absent or unlistable requested dossier, a `--task` matching no discovered dossier, or a `--task` matching more than one. Exit `1` means the scope was evaluated and the validator produced a diagnostic — including an existing but unreadable `index.md`, which `discover_dossiers` finds because it globs the path without reading it, and including root-level partial adoption. A scope code in `{0, 2}` and a verdict code in `{0, 1}` compose: exit `2` if the scope code is `2`, else the verdict code. |
| `R-S12` | Stale state is reported and forces a nonzero exit through the validator verdict. |
| `R-S13` | An artifact that cannot be read is reported with path and reason, never silently omitted. |
| `R-S14` | Output is deterministic; the machine-readable form carries the same facts and the same exit code. |

## Baseline, preflight, and delta requirements

| ID | Requirement |
| --- | --- |
| `R-B1` | The implementation-start baseline is a **complete no-follow capture map** with one row per non-directory entry, recording repo-relative path, type (`f`, `l`, or `o`), byte length, and SHA-256, sorted by path. A symlink row records the length and digest of the **link target string**; the walk never follows a link. |
| `R-B2` | The map covers **every observed file** outside the exact exclusion set enumerated in `design.md` — `.git`, `.venv`, `.pytest_cache`, any `__pycache__` component, the four TDW-009-related handoff directories, and any file named `.DS_Store` or `.env`. Nothing else is excluded, so pre-existing tracked modifications and pre-existing untracked leaves are included with full rows. |
| `R-B3` | The eight modified tracked paths carry byte snapshots named exactly `sha256(path.encode("utf-8")).hexdigest() + ".bin"`, removing the version-4 ambiguity about flattening. |
| `R-B4` | **Snapshots are evidence only.** No worker may restore from, delete from, or write through a snapshot. |
| `R-B5` | Before any implementation write, an exact executable preflight rebuilds the map and **byte-compares** it against the capture, authenticates every snapshot no-follow against its capture-row digest, and verifies every planned-new path is absent from both the filesystem and the capture. Any mismatch is a stop, reported per path. |
| `R-B6` | At handoff, an exact executable after-delta rebuilds the map and computes `changed`, `created`, and `removed` against the capture. Any removal is a failure. `unexpected = (changed ∪ created ∪ removed) − allowlist` must be empty. |
| `R-B7` | A post-capture modification to a pre-existing **tracked** file outside the allowlist, and to a pre-existing **untracked** file outside the allowlist, must each land in `unexpected` and exit nonzero. |
| `R-B8` | A collision at a planned-new path is handled by class: a **capture-time** collision makes the manifest invalid, because every new path must be recorded absent; a **post-capture** collision makes the start preflight fail. Neither is ever attributed to this implementation, and generator `EEXIST` preserves the existing file and forces the nonzero outcome. |
| `R-B9` | The preflight, delta, snapshot-authentication, and collision behaviours are tested in `tests/integration/test_task_dossier_workflow.py` or `tests/contract/test_task_dossier_contract.py`, both already authorized. **No forty-fifth path is created.** |
| `R-B10` | Every guarantee in `R-B1` through `R-B8` is a point-in-time observation. No requirement claims compare-and-swap safety against a concurrent same-identity process. |

## Recovery requirements

| ID | Requirement |
| --- | --- |
| `R-R1` | TDW-009 contains **no rollback** — no promise, no procedure, no test, no command. |
| `R-R2` | On implementation failure the worker **fixes forward** within its 44 authorized paths. It does not revert, restore, or delete outside them. |
| `R-R3` | After a successful scoped commit, recovery is a **separately reviewed commit revert** requested from the coordinator, outside this task. |
| `R-R4` | `git checkout --` on any path, restoring from a snapshot, and deleting from a snapshot are all forbidden to every worker. |

## Safety and compatibility requirements

| ID | Requirement |
| --- | --- |
| `R-X1` | `ARTIFACTS`, `METADATA_FIELDS`, `PHASE_STATES`, `APPLICABILITY_STATES`, and `MINIMUM_EVIDENCE_ITEMS` keep their current values. |
| `R-X2` | `scaffold.py` is not modified; the generator imports only `dossier_path`. |
| `R-X3` | `parser.py` is not modified. |
| `R-X4` | `validation.py` receives exactly five enumerated hunks. |
| `R-X5` | `__init__.py` keeps `main` bound to `validation.main`; CLI entries are exported only as `generate_main` and `summary_main`. |
| `R-X6` | `config/model-routing.json` is user-owned protected state. Implementation must not modify, revert, absorb, or interpret it, and **no planning or implementation artifact records an expected digest for it**. It appears in the capture map like any other file. |
| `R-X7` | Every file under `src/brichan/resources/` is unchanged, verified through the capture map. |
| `R-X8` | Standard library only on the `>=3.10` floor, verified by an explicit Python 3.10 run. |
| `R-X9` | Existing dossiers `TDW-006`, `TDW-007`, and `TDW-008` remain byte-identical. |
| `R-X10` | New wrappers under `scripts/` stay thin bootstrap shims. |
| `R-X11` | The implementation allowlist is exactly **44 paths**: 8 modified tracked, 7 new source and test, 29 evaluation leaves. |
| `R-X12` | No migration is performed. Hand-authored dossiers stay first-class. |

## Evaluation requirements

| ID | Requirement |
| --- | --- |
| `R-E1` | Evaluation dossiers are unmistakably synthetic; every session identity matches `synthetic-fixture-` and every sample artifact claims non-authoritative test data. |
| `R-E2` | No synthetic verdict, session, or identifier inequality is presented as evidence of real review; `results.md` carries the fixed declaration, asserted by a contract test. |
| `R-E3` | Every evaluation output path is in the closed leaf allowlist, compared by exact set equality. |
| `R-E4` | Each sample carries eleven artifacts, a schema-valid `receipt.md`, and the canonical project-memory file, with receipts validated against the isolated root. |
| `R-E5` | The durable evaluation records the AC3 metric plus record lines, record bytes, `authored_values`, and combined lines, stating which measures compactness and which approximates burden. |
| `R-E6` | `authored_values` uses the exact algorithm and fixed `DECLARED_ORDER` in `design.md`, reproducible to the same integer across two runs. |

## Remediation traceability

| Finding from `versions/v4/plan-review.md` | Requirements | Plan steps |
| --- | --- | --- |
| `H1` manifest cannot compute its `unexpected` set | `R-B1`, `R-B2`, `R-B6`, `R-B7` | 1, 19, 20 |
| `H2` rollback content-checked and restores unauthenticated snapshots | `R-R1` through `R-R4`, `R-B4` | removed from every step |
| `H3` start precondition validates shape, not state | `R-B5`, `R-B8` | 1, 20 |
| `M1` `sections[].body[]` both requires and permits newlines | `R-G27` | 3, 10 |
| Added: pre-existing tracked and untracked change lands in `unexpected` | `R-B7` | 20 |
| Added: protected, modified, snapshot, and collision drift refused at preflight | `R-B5`, `R-B8` | 20 |
| Added: embedded-newline body refused, safe multi-line claim accepted | `R-G27` | 10 |
| Added: tests hosted in an already-authorized file | `R-B9`, `R-X11` | 20 |
| Removed by amendment: rollback-target and snapshot-restore tests | `R-R1` | none |

## Acceptance-criteria traceability

| Parent AC | Requirements | Discharged by |
| --- | --- | --- |
| `TDW-009-AC1` | `R-G1` through `R-G18` | Plan steps 4, 5, 11, 12 |
| `TDW-009-AC2` | `R-G19` through `R-G27`, `R-E4` | Plan steps 3, 6, 10, 13, 16 |
| `TDW-009-AC3` | `R-G28`, `R-E3`, `R-E5`, `R-E6` | Plan steps 15, 16, 17 |
| `TDW-009-AC4` | `R-S1` through `R-S14` | Plan steps 7, 8, 14 |
| `TDW-009-AC5` | `R-B1` through `R-B10`, `R-V4`, `R-V6`, `R-X1` through `R-X12` | Plan steps 1, 2, 8, 18, 19, 20 |
| `TDW-009-AC6` | all | Plan steps 13, 14, 16, 19, 20 |
| `TDW-009-AC7` | `R-E1`, `R-E2`, `R-E5`, `R-E6` | Plan steps 17, 18 |
| `TDW-009-AC8` | all | Plan step 21 |

## Claim or decision

Version 5 makes the exact-write-scope gate provable and removes the one promise
that could not be kept honestly. The baseline becomes a complete no-follow
capture map over every observed non-excluded file, so a change to a pre-existing
tracked or untracked file outside the 44 lands in `unexpected` instead of going
unseen — the version-4 defect. The start preflight becomes an executable byte
comparison that also authenticates snapshots and proves every planned-new path
absent. Rollback is deleted rather than deepened: snapshots are evidence, no
worker may restore or delete from them, and recovery is fix-forward and then a
separately reviewed commit revert. `sections[].body[]` refuses line feeds so one
element is exactly one rendered line, while `claim` keeps safe multi-line prose
under per-line checks. Every guarantee is labelled a point-in-time observation.

## Evidence

- The capture script specified in `design.md` was executed read-only against
  this repository before these requirements were written. It produced a 333-row
  map that includes the pre-existing tracked modifications to
  `config/model-routing.json`, `projects/brida-task-dossier-workflow/references.md`,
  and `tasks.md` — the exact files the version-4 review named as unprovable — and
  excluded every enumerated exclusion.
- The same script was exercised against a purpose-built fixture: a post-capture
  change to a pre-existing tracked file and to a pre-existing untracked file each
  failed preflight and each landed in `unexpected` at delta time with exit `1`; a
  planned-new collision failed preflight; a corrupted, a removed, and a
  symlinked snapshot each failed preflight; and removing an observed file failed
  the delta. This is the executable basis for `R-B5` through `R-B8`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md:70-101`
  states `H1` with the same concrete example: tracked changes to `references.md`
  and `tasks.md` were neither protected, allowlisted, nor excluded, and had no
  capture-time bytes to compare against.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md:102-134,136-161`
  state `H2` and `H3`. `H2` is closed by removing rollback per the amendment
  rather than by the reviewer's bounded revision; `H3` is closed by the
  executable preflight.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md:165-181`
  states `M1`, and a read-only check confirmed the corrected rule is decidable:
  single-line body elements are accepted, an element with an embedded line feed
  is refused, a two-line `claim` with no structural line is accepted, and a
  `claim` whose second line is a heading is refused.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md:210-215`
  rejects the version-4 claim that automating the procedure needs a
  forty-fifth path, observing that the allowlist already authorizes additions to
  existing test files. `R-B9` adopts that, so `R-X11` holds at 44.
- Re-extracting the fenced record from the rewritten `design.md` reproduced
  eleven artifact keys with seventeen keys each, all four cross-record rules, and
  zero `validate_dossier` diagnostics under both gates, confirming the carried-forward
  worked record still satisfies `R-G26` after the schema change.

## Uncertainty

- The capture map, preflight, and delta are point-in-time observations. The
  excluded same-identity process defeats all three, and `R-B10` says so rather
  than mitigating it.
- Excluding `.env` and `.DS_Store` means changes to them are invisible to every
  check here. That is a deliberate trade against hashing a secret-bearing file.
- The 333-row figure is this working tree at planning time, not a contract; only
  byte equality against the coordinator's own capture matters.
- Removing rollback means a failed implementation leaves partial work in the tree
  until a coordinator-reviewed revert. That cost is accepted in exchange for not
  offering restoration that cannot be made safe.
- The worked record was validated through a reference renderer written for this
  planning session, not the implementation, which does not yet exist.
