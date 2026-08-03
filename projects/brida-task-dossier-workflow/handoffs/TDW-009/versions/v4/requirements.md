# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `requirements`
- Artifact version: `4`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md@TDW-009-P3-v3+task-packet-amendment-4`
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

## Version 4 supersession

Versions 1 to 3 are preserved byte-identically at `versions/v1/`, `versions/v2/`,
and `versions/v3/`. Version 4 exists because independent review of `TDW-009-P3`
version 3 returned `CHANGES REQUIRED` with four high findings and one medium.

Every citation of a prior review names an immutable archived path. Five
coordinator decisions in the version-4 amendment are binding inputs:

1. The current bytes of `config/model-routing.json` are user-owned protected
   state. The manifest captures whatever bytes exist at capture time. **No
   planning or implementation artifact hard-codes a digest for it**, absorbs it
   into implementation scope, or restores another version.
2. The same-identity threat boundary is unchanged. Post-publication checks are
   **point-in-time best-effort observation only**; neither prevention nor
   guaranteed detection may be claimed.
3. The manifest carries restorable byte snapshots and digests for every modified
   tracked path, records every planned new path absent, and comes with a
   canonical format, an exact set-delta procedure, and an identity-checked
   rollback that never overwrites a target changed after implementation.
4. Summary exits follow actual validator discovery: an existing unreadable
   `index.md` and root-level partial adoption exit `1`; a truly absent or
   unlistable requested scope and an unmatched `--task` exit `2`. Selected-task
   handling never overrides the project validator.
5. Safe descriptor-relative directory creation may precede the dossier lock. The
   lock is acquired immediately after opening the dossier and before any
   temporary-file or artifact mutation. A two-invocation first-creation test is
   required.

## Threat-model boundary

Stated once and never contradicted. `design.md` carries the full statement.

**Out of scope.** A non-cooperating process running under the same OS identity
that mutates dossier directory entries while the generator holds the lock.

**Claimed.** Safety against pre-existing symlinks at any path component; against
namespace drift the generator can observe; against ordinary concurrent Brichan
invocations that cooperate with the lock; against every specified write, `fsync`,
close, link, cleanup, and directory-`fsync` failure; and refusal of malformed,
hostile, or injected record content.

**Not claimed.** Neither prevention nor detection against the excluded process.
The post-publication check is a point-in-time best-effort observation: it returns
nonzero *if, at the instant it runs*, it observes a type or inode mismatch. An
excluded process active across the check window defeats it in either direction.
No requirement below may be read as a detection guarantee, and the controlled
substitution tests may never be cited as adversarial coverage.

## Generator requirements

| ID | Requirement |
| --- | --- |
| `R-G1` | One structured record file, read once, produces exactly the eleven artifacts named in `schema.py:17-29`. |
| `R-G2` | Generation is dry-run by default. Without an explicit apply flag no byte is written. |
| `R-G3` | Phase A: the record is loaded, fully validated, and all eleven bodies rendered in memory **before any filesystem mutation whatsoever**. Any failure leaves the tree untouched. |
| `R-G4` | Phase B: every directory in the chain `<projects-root>/<project>/handoffs/<task-id>` is opened with `O_RDONLY \| O_DIRECTORY \| O_NOFOLLOW` relative to its already-open parent. No pathname below the projects root is re-resolved for a write. |
| `R-G5` | A component that is a symlink or is not a directory aborts before any write. Both `ELOOP` and `ENOTDIR` are refusals. |
| `R-G6` | Replacing any ancestor with a symlink after its descriptor is obtained cannot redirect a write outside the projects root. |
| `R-G7` | Missing project, `handoffs`, and dossier directories are created with `os.mkdir(..., dir_fd=parent)` using single validated components. This creation may occur **before** the dossier lock exists, because a directory cannot be locked before it exists. |
| `R-G8` | Phase C: the exclusive advisory lock `fcntl.flock(dossier_fd, LOCK_EX \| LOCK_NB)` is acquired **immediately after the dossier descriptor is opened and before any temporary-file or artifact mutation**. A conflicting holder is refused, never awaited. The losing invocation creates no temporary and no artifact leaf. |
| `R-G9` | Phase D: each artifact is published by writing a private temporary in the dossier directory, writing it fully, `fsync`-ing it, verifying its device and inode against the writing descriptor, then `os.link(temp, final, src_dir_fd, dst_dir_fd, follow_symlinks=False)`. `os.rename` and `os.replace` are forbidden. |
| `R-G10` | Publication never overwrites. `EEXIST` means the artifact appeared in the window and is reported `preserve`. |
| `R-G11` | Immediately after a successful link, the final name is checked with `os.lstat(final, dir_fd=dossier_fd)` for regular-file type and matching device and inode. An observed mismatch exits nonzero with a named diagnostic and the entry is **not** unlinked. This check is a **point-in-time best-effort observation**, not a detection guarantee against the excluded process. |
| `R-G12` | A temporary is unlinked only after its device and inode re-verify against the creating descriptor. On mismatch it is left and diagnosed. Cleanup failure never converts a failure into success. |
| `R-G13` | No artifact is ever published in a partial state. |
| `R-G14` | Temporary names are `O_EXCL`-created and bounded; exhaustion is a refusal. |
| `R-G15` | Multi-file partial progress is retained only when every retained artifact is complete, with a nonzero exit and an explicit partial-adoption diagnostic. |
| `R-G16` | The dossier descriptor is `fsync`-ed after publication; failure forces a nonzero exit. |
| `R-G17` | Before returning success, the canonical chain is re-walked read-only and each level's device and inode compared against the held descriptors. Drift exits nonzero with a deterministic diagnostic. |
| `R-G18` | Record identity must equal the identity supplied on the command line. |
| `R-G19` | The generator derives only `Task ID`, `Task level`, `Artifact`, `Owner`, the index `Task identity` triple, the canonical receipt path, and the index artifact status table. |
| `R-G20` | The generator never derives, defaults, or infers any judgment-bearing value. A missing value is a refusal. |
| `R-G21` | A review artifact that is `passed` must carry an explicit verdict from `REVIEW_VERDICTS`. |
| `R-G22` | Any placeholder in a position the contract requires to be concrete is a refusal. |
| `R-G23` | Evidence depth mirrors `validation.py:276-355` exactly: the level floor for `passed`, the one-item rule plus concrete rationale, claim, and uncertainty for `not-required`. |
| `R-G24` | Any value matching `PERSONAL_PATH_PATTERNS` is a refusal. |
| `R-G25` | For `index`, only `INDEX_PROJECTION_SECTIONS` are emitted, only the status table appears, and supplemental sections are refused. |
| `R-G26` | The record is parsed under the exhaustive key-to-type tables in `design.md`, with `object_pairs_hook` duplicate rejection, `type(v) is ...` checks, JSON `null` as the only null, and the four cross-record consistency refusals. `design.md` carries **one literal complete eleven-artifact record**, each artifact holding all seventeen keys, and the extraction test loads that fenced block from `design.md` itself rather than a separate fixture. |
| `R-G27` | Structural injection is refused per rendered position class, each rule justified by the `parser.py` primitive it protects. Backticks are permitted in free-text and multi-line positions and refused only in backtick-wrapped positions. |
| `R-G28` | Rendering is deterministic; no timestamp, hostname, process ID, or absolute path reaches artifact content. |
| `R-G29` | The generator never reads the routing manifest and names neither `model-routing.json` nor `model_routing`. |

## Validator requirements

| ID | Requirement |
| --- | --- |
| `R-V1` | `_validate_receipt_link` rejects a receipt path with any symlinked ancestor between the repository root and the file, with a new named diagnostic. |
| `R-V2` | `_validate_memory_link` rejects a memory path with any symlinked ancestor, with a new named diagnostic. |
| `R-V3` | Both share one helper that walks repo-relative components from the repository root and `lstat`s each, resolving and following nothing. |
| `R-V4` | Every existing validator diagnostic keeps its condition, field locator, and message text. Exactly two are added. |
| `R-V5` | Regression tests in `tests/unit/test_task_dossier_validator.py` cover a symlinked ancestor for each authority path and the unchanged clean case, and assert the diagnostics originate from the validator rather than the summary. |
| `R-V6` | `TDW-006`, `TDW-007`, `TDW-008`, and `TDW-009` produce no new diagnostic, verified by running the validator over `projects` after the change. |

## Summary requirements

| ID | Requirement |
| --- | --- |
| `R-S1` | The summary is read-only. |
| `R-S2` | It reports per-artifact applicability and phase state for all eleven artifacts in `ARTIFACTS` order. |
| `R-S3` | Evidence depth is reported against the rule that applies: the level floor for `passed`, the one-item rule for `not-required`, `not-applicable` otherwise. A `not-required` artifact is never labelled below-floor for holding fewer items than the level floor. |
| `R-S4` | Effective model provenance is read from the artifacts, never from the routing manifest. |
| `R-S5` | Plan and review identity are reported with any disagreement flagged. |
| `R-S6` | Authority-link health is reported — declared value, expected value, existence, not-a-symlink, no symlinked ancestor, containment — as health only. Invalidity is the validator's verdict under `R-V1` and `R-V2`. |
| `R-S7` | Review independence is reported as two separate arms per review, each `independent`, `not-independent`, or `unknown`. |
| `R-S8` | Every rendered form states that session-identifier inequality is a consistency signal, not proof that two independent sessions existed. |
| `R-S9` | The root verdict comes from `validate_projects(root, require_complete=True)`. `validate_dossier` supplies detail only and never contradicts it. Selecting a task never suppresses a root-level diagnostic. |
| `R-S10` | The complete gate is the default and only exit semantics. No flag relaxes it. |
| `R-S11` | Exit codes follow **actual discovery**, not an assumed model. Exit `2` means the requested scope cannot be evaluated at all: a projects root that is absent or unlistable, a requested dossier directory that is absent or unlistable, a `--task` matching no discovered dossier, or a `--task` matching more than one. Exit `1` means the scope was evaluated and the validator produced a diagnostic — including an **existing but unreadable `index.md`**, which `discover_dossiers` finds because it globs the path without reading it, and including **root-level partial adoption**, which `validate_projects` raises for a handoff carrying dossier artifacts without an index. The process computes a scope code in `{0, 2}` and a verdict code in `{0, 1}` and exits with `2` if the scope code is `2`, else the verdict code. |
| `R-S12` | Stale state is reported, not hidden, and forces a nonzero exit through the validator verdict. |
| `R-S13` | An artifact that cannot be read or parsed is reported with path and reason and never silently omitted. |
| `R-S14` | Output is deterministic and byte-stable. A machine-readable form carries the same facts and the same exit code. |

## Safety and compatibility requirements

| ID | Requirement |
| --- | --- |
| `R-X1` | `ARTIFACTS`, `METADATA_FIELDS`, `PHASE_STATES`, `APPLICABILITY_STATES`, and `MINIMUM_EVIDENCE_ITEMS` keep their current values. Additions to `schema.py` are additive constants only. |
| `R-X2` | `scaffold.py` is not modified at all; the generator imports only `dossier_path` from it and shares no write code. |
| `R-X3` | `parser.py` is not modified. |
| `R-X4` | `validation.py` receives exactly five enumerated hunks. |
| `R-X5` | `__init__.py` keeps `main` bound to `validation.main`; the CLI entries are exported only as `generate_main` and `summary_main`. |
| `R-X6` | `config/model-routing.json` is **user-owned protected state**. Implementation must not modify, revert, or absorb it, and **no planning or implementation artifact records an expected digest for it**. The manifest captures whatever bytes exist at capture time, and that capture is the only reference. Its ownership question is the coordinator's to resolve, not the implementer's. |
| `R-X7` | Every file under `src/brichan/resources/` — sixteen files at the time of writing, including `__init__.py` and every package file — is unchanged and verified against the manifest capture. |
| `R-X8` | Standard library only, running on the `requires-python = ">=3.10"` floor, verified by an explicit Python 3.10 run of the focused suites. |
| `R-X9` | Existing dossiers `TDW-006`, `TDW-007`, and `TDW-008` remain byte-identical. |
| `R-X10` | New wrappers under `scripts/` stay thin bootstrap shims. |
| `R-X11` | The implementation-start manifest follows the canonical format in `design.md`: a version line, repository identity, an explicit capture-scope exclusion for coordinator-, planner-, and reviewer-owned dossier paths, a `[protected]` section, `[allowlist-modified]` with **eight** lines each carrying a digest and a restorable byte snapshot, `[allowlist-new]` with **thirty-six** lines each recorded `absent`, and `[untracked-leaves]` enumerating individual files with no collapsed directory. A digest alone is insufficient because it cannot reconstruct a reverse patch. |
| `R-X12` | The manifest is captured after plan version 4 is accepted. The implementer refuses to start if it is missing any element required by `R-X11`. |
| `R-X13` | Rollback is identity-checked and never overwrites. Each of the 44 paths is compared against the **post-implementation digest** recorded at handoff; a target whose current bytes differ is neither restored nor deleted, and the rollback aborts on that path and escalates. Whole-file `git checkout --` is forbidden. |
| `R-X14` | The exact set-delta procedure in `design.md` is used, requiring the unexpected set to be empty and the delta to equal the 44 authorized paths. |
| `R-X15` | No migration is performed. Hand-authored dossiers stay first-class. |

## Evaluation requirements

| ID | Requirement |
| --- | --- |
| `R-E1` | Evaluation dossiers are unmistakably synthetic; every session identity matches `synthetic-fixture-` and every sample artifact states in its own claim that it is non-authoritative test data. |
| `R-E2` | No synthetic verdict, session, or identifier inequality is presented as evidence of real review. `results.md` carries the fixed declaration, asserted by a contract test. |
| `R-E3` | Every evaluation output path is enumerated as a closed leaf allowlist, compared by exact set equality. |
| `R-E4` | Each sample carries eleven artifacts, a schema-valid `receipt.md`, and the canonical project-memory file, with receipts validated explicitly against the isolated root. |
| `R-E5` | The durable evaluation records the AC3 metric unchanged plus record lines, record bytes, `authored_values`, and combined lines, stating which measures compactness and which approximates burden. No timing, token, or cost claim. |
| `R-E6` | `authored_values` is produced by the exact algorithm and fixed `DECLARED_ORDER` in `design.md`, reproducible to the same integer across two runs. |

## Remediation traceability

| Finding from `versions/v3/plan-review.md` | Requirements | Plan steps |
| --- | --- | --- |
| `H1` worked record omitted ten artifacts | `R-G26` | 3, 10 |
| `H2` manifest cannot support rollback; stale hard-coded routing digest | `R-X6`, `R-X11` through `R-X14` | 1, 19, 20 |
| `H3` unreadable-index and partial-adoption exits contradict the validator | `R-S9`, `R-S11` | 7, 14 |
| `H4` normative text overclaims detection | threat-model boundary, `R-G11` | all five artifacts, 11 |
| `M1` lock cannot precede directory creation | `R-G3`, `R-G7`, `R-G8` | 4, 11 |
| Added test: extract and validate the literal complete example | `R-G26` | 10 |
| Added test: unreadable versus missing index; root partial versus unmatched task | `R-S11` | 14 |
| Added test: two cooperating invocations from a missing dossier | `R-G7`, `R-G8` | 11 |
| Added procedure run: manifest parse, delta, and concurrently changed rollback target | `R-X11` through `R-X14` | 19 |
| Added test: post-link diagnostic for a stable injected mismatch, without a detection claim | `R-G11` | 11 |

## Acceptance-criteria traceability

| Parent AC | Requirements | Discharged by |
| --- | --- | --- |
| `TDW-009-AC1` | `R-G1` through `R-G18` | Plan steps 4, 5, 11, 12 |
| `TDW-009-AC2` | `R-G19` through `R-G27`, `R-E4` | Plan steps 3, 6, 10, 13, 16 |
| `TDW-009-AC3` | `R-G28`, `R-E3`, `R-E5`, `R-E6` | Plan steps 15, 16, 17 |
| `TDW-009-AC4` | `R-S1` through `R-S14` | Plan steps 7, 8, 14 |
| `TDW-009-AC5` | `R-V4`, `R-V6`, `R-X1` through `R-X15` | Plan steps 1, 2, 8, 18, 19 |
| `TDW-009-AC6` | all | Plan steps 13, 14, 16, 19 |
| `TDW-009-AC7` | `R-E1`, `R-E2`, `R-E5`, `R-E6` | Plan steps 17, 18 |
| `TDW-009-AC8` | all | Plan step 21 |

## Claim or decision

Version 4 makes every normative statement match something that was executed or
read from source. The worked record in `design.md` is complete at eleven
artifacts and seventeen keys each, and was rendered and passed through the
repository's own `validate_dossier` twice with zero diagnostics before this
requirement was written, so `R-G26` is satisfiable rather than aspirational.
Every detection claim is downgraded to point-in-time best-effort observation.
`R-S11` is derived from what `discover_dossiers`, `discover_partial_dossiers`,
and `parse_artifact` actually do rather than from an assumed discovery model.
`R-G7` and `R-G8` state the only lock ordering that is physically possible. And
`R-X6` removes every hard-coded protected-file digest: the routing file's current
bytes are user-owned state that only the coordinator's capture may define.

## Evidence

- A read-only reference renderer rendered the complete worked record now in
  `design.md` into a temporary projects root; `validate_dossier` returned zero
  diagnostics and `validate_dossier(..., require_complete=True)` returned zero
  diagnostics, at 410 rendered lines across the eleven artifacts. Re-extracting
  the fenced block from the written `design.md` reproduced eleven artifact keys
  with seventeen keys each and satisfied all four cross-record rules.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md:71-90`
  states `H1`: the version-3 example supplied one artifact key against eleven
  required, making the mandated assertion impossible.
- `src/brichan/contracts/task_dossier/validation.py:1109-1116,1138-1195` and
  `src/brichan/contracts/task_dossier/parser.py:116-123` are the source of
  `R-S11`: discovery globs `*/handoffs/*/index.md` without reading it, so an
  existing unreadable index is discovered and `parse_artifact` diagnoses it,
  while partial adoption is raised only by `validate_projects`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md:92-119`
  supplies both halves of `H2`. Read-only hashing during this session confirmed
  the reviewer's finding that `config/model-routing.json` no longer matches the
  digest version 3 hard-coded, and `git diff --stat` shows the file modified
  relative to `HEAD`; `R-X6` therefore removes the digest rather than updating it.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md:149-171,175-194`
  supply `H4` and `M1`, whose corrections are the threat-model boundary above and
  the Phase A to Phase D ordering in `R-G3`, `R-G7`, and `R-G8`.
- A read-only count of `src/brichan/resources/` found sixteen files, which is the
  figure `R-X7` requires the manifest to cover and the figure the superseded
  baseline under-counted at fifteen.

## Uncertainty

- The excluded-process boundary is a stated limitation with no remedy inside the
  authorized standard-library and platform boundary. `R-G11` is opportunistic by
  construction, and the tests that exercise it establish a diagnostic path only.
- The worked record was validated through a reference renderer written for this
  planning session, not the implementation, which does not yet exist. A divergent
  implemented renderer will fail the extraction test — the outcome that test
  exists to produce.
- The ownership and intended durability of the current `config/model-routing.json`
  change cannot be inferred from repository state. `R-X6` requires the
  coordinator to capture whatever bytes exist and forbids the implementer from
  interpreting them; it does not resolve the ownership question.
- `R-V1` and `R-V2` are a behaviour change for any checkout with a symlinked
  ancestor above an authority path. None exists here.
- The manifest delta and rollback are a documented procedure executed and
  recorded in step 19, not an automated suite test, because adding a module to
  automate them would exceed the 44-path allowlist the amendment fixes.
