# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `requirements`
- Artifact version: `3`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md@TDW-009-P2-v2+task-packet-amendment-3`
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

## Version 3 supersession

Versions 1 and 2 are preserved byte-identically at `versions/v1/` and
`versions/v2/` and are superseded, not rewritten. Version 3 exists because
independent review of `TDW-009-P2` version 2 returned `CHANGES REQUIRED` with
one critical, three high, and two medium findings plus nine partially covered
test-gap classes.

Every citation of a prior review in these artifacts names an immutable archived
path — `versions/v1/plan-review.md` or `versions/v2/plan-review.md` — never the
mutable standard `plan-review.md`, whose content is replaced by each review
version. This closes `M2`.

Three coordinator decisions in the version-3 amendment are binding inputs:

1. A malicious or non-cooperating same-OS-identity process that mutates
   directory entries while the generator holds the dossier lock is **outside**
   this repository tooling threat model. The design states the limitation
   prominently, uses a dossier-scoped advisory lock for cooperating writers,
   preserves no-overwrite publication, returns nonzero when a final canonical
   re-walk detects namespace drift, and claims no protection against the
   excluded attacker.
2. Ancestor-symlinked receipt and project-memory authority paths are invalid,
   not merely informational. Exact compatible changes and regression tests in
   `validation.py` and the task-dossier test paths make these conditions part of
   the sole validator verdict; the summary reports that verdict.
3. The pre-task baseline is replaced before implementation handoff by a
   coordinator-captured implementation-start manifest with repository identity,
   the exact path allowlist, presence/absence and digest evidence for every
   allowlisted path, an exact untracked-leaf inventory, and every file under
   `src/brichan/resources/` including package files.

## Threat-model boundary

Stated once, prominently, and never contradicted elsewhere.

**In scope.** Pre-existing symlinks at any path component; namespace drift the
generator can observe; ordinary concurrent Brichan invocations that cooperate
with the dossier lock; every specified write, `fsync`, close, link, cleanup, and
directory-`fsync` failure; malformed, hostile, or injected record content.

**Out of scope.** A non-cooperating process running under the same OS identity
that mutates directory entries inside the dossier while the generator holds the
dossier lock. Such a process can already unlink, replace, or truncate any file
this tooling owns by direct action; the generator is a repository developer tool
and is not a privilege boundary against itself.

**Consequence, stated without softening.** Because no Python 3.10 standard-library
primitive available on both darwin and Linux can bind a hard link's source
identity to an open descriptor, an excluded-attacker substitution of the
temporary source name between its identity check and publication can cause a
foreign inode or a symlink to appear at a final artifact name. The generator
**detects** this after publication and fails the run; it does **not** prevent it
and does not remove the foreign entry. No requirement below may be read as a
prevention claim against the excluded attacker.

## Generator requirements

| ID | Requirement |
| --- | --- |
| `R-G1` | One structured record file, read once, produces exactly the eleven artifacts named in `schema.py:17-29` — no more and no fewer. |
| `R-G2` | Generation is dry-run by default. Without an explicit apply flag no byte is written and the planned action list is printed. |
| `R-G3` | All eleven artifact bodies are rendered in memory and pass every record check before any filesystem mutation occurs. |
| `R-G4` | Every directory in the chain `<projects-root>/<project>/handoffs/<task-id>` is opened with `O_RDONLY \| O_DIRECTORY \| O_NOFOLLOW` relative to its already-open parent descriptor. No pathname below the operator-supplied projects root is ever re-resolved for a write. |
| `R-G5` | A component that is a symlink, or is not a directory, aborts before any write. Both `ELOOP` and `ENOTDIR` are refusals, because the two POSIX platforms in scope differ in which they raise. |
| `R-G6` | Replacing any ancestor directory with a symlink after its descriptor is obtained cannot redirect a write outside the projects root: every subsequent operation is descriptor-relative and bound to the original inode. |
| `R-G7` | Missing project, `handoffs`, and dossier directories are created with `os.mkdir(..., dir_fd=parent)` using single path components only. |
| `R-G8` | Apply mode acquires a dossier-scoped exclusive advisory lock with `fcntl.flock(dossier_fd, LOCK_EX \| LOCK_NB)` before any mutation, and holds it until the run ends. The lock is taken on the dossier directory descriptor itself, so it creates no file and is released by descriptor close. A conflicting holder is refused, not waited on. |
| `R-G9` | Each artifact is published by writing a private temporary in the dossier directory, writing it fully, `fsync`-ing it, verifying its device and inode against the writing descriptor, then `os.link(temp, final, src_dir_fd, dst_dir_fd, follow_symlinks=False)`. `os.rename` and `os.replace` are forbidden: rename overwrites, and `os.replace` does not accept `dir_fd`. |
| `R-G10` | Publication never overwrites. `EEXIST` from the publishing link means the artifact appeared in the window and is reported `preserve`; the existing bytes are untouched. |
| `R-G11` | Immediately after a successful link, the final name is verified with `os.lstat(final, dir_fd=dossier_fd)`: it must be a regular file whose device and inode equal the recorded temporary inode. A mismatch is a publication-integrity failure that exits nonzero with a diagnostic naming the artifact. The foreign entry is **not** unlinked, because the contract forbids deleting an entry this run did not verifiably create. |
| `R-G12` | A temporary file is unlinked only after its device and inode are re-verified against the descriptor that created it. On mismatch the temporary is left in place and diagnosed. Cleanup failure is reported and never masks a successful publication or converts a failure into success. |
| `R-G13` | No artifact is ever published in a partial state. Any write, `fsync`, or close failure aborts before publication. |
| `R-G14` | Temporary names are `O_EXCL`-created and bounded: a fixed counter range is tried and exhaustion is a refusal, never a fallback to an unbounded or predictable name. |
| `R-G15` | Multi-file partial progress is retained only when every retained artifact is complete. Such a run exits nonzero with an explicit partial-adoption diagnostic naming published and unpublished artifacts, so a retry has deterministic recovery semantics. |
| `R-G16` | The dossier directory descriptor is `fsync`-ed after publication. A directory-`fsync` failure is reported and forces a nonzero exit. |
| `R-G17` | Before returning success, the canonical chain `<projects-root>/<project>/handoffs/<task-id>` is re-walked read-only and each level's device and inode are compared against the held descriptors. Any drift exits nonzero with a deterministic namespace-drift diagnostic. A contained-but-detached run is never reported as successful generation. |
| `R-G18` | Record identity — `task_id`, `project`, `level` — must equal the identity supplied on the command line. |
| `R-G19` | The generator derives only mechanical fields: `Task ID`, `Task level`, `Artifact`, `Owner`, the index `Task identity` triple, the canonical receipt path, and the index artifact status table. |
| `R-G20` | The generator never derives, defaults, or infers claim, evidence, uncertainty, phase state, applicability, applicability rationale, authorship, authoring session, effective route, effective model, effective effort, reviewing session, review verdict, plan status, ship authorization, or review-target identity. A missing value is a refusal. |
| `R-G21` | A review artifact whose phase state is `passed` must carry an explicit verdict drawn from `REVIEW_VERDICTS`. The generator never writes a `PASS` the record did not state. |
| `R-G22` | Any record value that `parser.is_placeholder` classifies as a placeholder, in a position the contract requires to be concrete, is a refusal. |
| `R-G23` | A `passed` artifact must carry at least `MINIMUM_EVIDENCE_ITEMS[level]` concrete evidence items; a `not-required` artifact must carry at least one, plus a concrete rationale, claim, and uncertainty statement. These mirror `validation.py:276-355` exactly. |
| `R-G24` | Any record value matching `PERSONAL_PATH_PATTERNS` is a refusal. |
| `R-G25` | For `index`, only `INDEX_PROJECTION_SECTIONS` may be emitted, only the artifact status table may appear, and no receipt-owned field label may be emitted. Supplemental sections are refused for `index`. |
| `R-G26` | The record is parsed under the exhaustive key-to-type table in `design.md`, which names every key, its exact type, its nullability, and its element type. `json.load` is called with an `object_pairs_hook` that refuses duplicate keys at any depth. Every scalar is checked with `type(value) is ...`, never `isinstance`, so a JSON boolean cannot satisfy an integer position. The worked example in `design.md` validates under that table. |
| `R-G27` | Structural injection is refused per rendered position class, with each refusal justified by the exact `parser.py` primitive it protects: backtick-wrapped positions refuse backticks, pipes, newlines, and control characters; free-text positions refuse newlines, control characters, a line that starts with `#`, and a line that both starts and ends with `\|`; field-bearing positions additionally refuse a `- Label:` line. Backticks are permitted in free-text positions because they cannot create a section, field, table row, or list item. |
| `R-G28` | Rendering is deterministic: identical record plus identical target yields byte-identical output. No timestamp, hostname, process ID, or absolute path reaches artifact content. |
| `R-G29` | The generator reads the routing manifest never, and mentions neither `model-routing.json` nor `model_routing`, preserving `tests/contract/test_task_dossier_contract.py:192-198`. |

## Validator requirements

Authorized by coordinator decision 2. These extend the sole validator authority;
they do not create a second one.

| ID | Requirement |
| --- | --- |
| `R-V1` | `_validate_receipt_link` additionally rejects a canonical receipt path any of whose ancestors between the repository root and the receipt file is a symlink, with a new named diagnostic. |
| `R-V2` | `_validate_memory_link` additionally rejects a project-memory path any of whose ancestors between the repository root and the memory file is a symlink, with a new named diagnostic. |
| `R-V3` | Both checks share one helper that walks repo-relative components from the repository root and `lstat`s each, returning the first symlinked ancestor or nothing. It resolves nothing and follows nothing. |
| `R-V4` | Every existing validator diagnostic keeps its current condition, field locator, and message text. Only the two diagnostics in `R-V1` and `R-V2` are added. |
| `R-V5` | Regression tests in `tests/unit/test_task_dossier_validator.py` cover a symlinked ancestor for the receipt path, a symlinked ancestor for the memory path, and the unchanged clean case, and assert the new diagnostics originate from the validator rather than from the summary. |
| `R-V6` | `TDW-006`, `TDW-007`, `TDW-008`, and `TDW-009` continue to produce no new diagnostic, verified by running the validator over `projects` after the change. |

## Summary requirements

| ID | Requirement |
| --- | --- |
| `R-S1` | The summary is read-only. It creates, modifies, moves, and deletes nothing. |
| `R-S2` | It reports per-artifact applicability and phase state for all eleven artifacts, in the fixed order of `ARTIFACTS`. |
| `R-S3` | Evidence depth is reported against the rule that applies to each artifact: the level floor for `passed`, the one-item rule for `not-required`, and `not-applicable` for `pending`, `active`, and `blocked`. A `not-required` artifact is never labelled below-floor for holding fewer items than the level floor. |
| `R-S4` | It reports effective model provenance per artifact, read from the artifacts, never resolved from the routing manifest. |
| `R-S5` | It reports plan identity and review identity: plan ID, plan status, plan artifact version, the index accepted plan ID and version, and each review's reviewed plan ID and version, flagging disagreement. |
| `R-S6` | It reports authority-link health for the canonical receipt and project-memory paths: declared value, expected value, existence, not-a-symlink, no symlinked ancestor, and containment. It reports health only and copies no receipt or project-memory content. The **invalidity** of an ancestor-symlinked path is the validator's verdict under `R-V1` and `R-V2`, which the summary reports rather than decides. |
| `R-S7` | It reports review independence as two separately reported arms per review — plan authoring session versus the review's `Reviewing session`, and versus its `Authoring session` — each `independent`, `not-independent`, or `unknown`. A placeholder in either identity yields `unknown` and never `independent`. |
| `R-S8` | Every rendered form states, in fixed wording, that session-identifier inequality is a deterministic consistency signal and not proof that two independent sessions existed. |
| `R-S9` | The root verdict comes from `validate_projects(root, require_complete=True)`, so partial-adoption and duplicate-task-ID diagnostics can never be lost. `validate_dossier` supplies per-dossier detail only and never produces a contradicting exit. |
| `R-S10` | The complete gate is the default and only exit semantics. There is no flag that relaxes it. |
| `R-S11` | Exit `1` means the tool evaluated the requested scope and it is invalid or incomplete. Exit `2` means the tool could not evaluate the requested scope. The boundary is exact: an **unreadable artifact** inside a discoverable dossier is exit `1`, because the validator already diagnoses it; an **unreadable dossier** — the directory is absent, is not a directory, cannot be listed, or has no readable `index.md` and is therefore undiscoverable — is exit `2`. A missing projects root, a `--task` matching no dossier, and a `--task` matching more than one dossier are exit `2`. |
| `R-S12` | Stale state is reported, not hidden: a status-table row disagreeing with its artifact, a dangling or ancestor-symlinked authority target, a review naming a plan version other than the plan's current artifact version, a `passed` review whose verdict is `CHANGES REQUIRED`, and a handoff with dossier artifacts but no index each appear in the report and each force a nonzero exit through the validator verdict. |
| `R-S13` | An artifact that cannot be read or parsed is reported with its path and reason and never silently omitted. |
| `R-S14` | Output is deterministic and byte-stable for a fixed dossier. A machine-readable form carries the same facts and the same exit code as the human form. |

## Safety and compatibility requirements

| ID | Requirement |
| --- | --- |
| `R-X1` | `ARTIFACTS`, `METADATA_FIELDS`, `PHASE_STATES`, `APPLICABILITY_STATES`, and `MINIMUM_EVIDENCE_ITEMS` keep their current values. Additions to `schema.py` are additive constants only. |
| `R-X2` | `scaffold.py` is not modified at all. The generator shares no write code with it and imports only `dossier_path`. |
| `R-X3` | `parser.py` is not modified. |
| `R-X4` | `validation.py` receives exactly five enumerated hunks: the `ARTIFACT_EXTRA_SECTIONS` import insertion, the `EXTRA_SECTION_FIELDS` replacement, the new shared ancestor helper, and one call-site addition in each of `_validate_receipt_link` and `_validate_memory_link`. No other line changes. |
| `R-X5` | `__init__.py` keeps `main` bound to `validation.main`. The two new CLI entry points are exported only as `generate_main` and `summary_main`, with a test asserting the preserved binding and the absence of collision. |
| `R-X6` | `config/model-routing.json` keeps its schema version, its four routes, and its values, and gains no workflow, phase, level, or artifact key. Its current digest `31466a36cef7e6966dec52211d14769e2c91b8ab1a7be33b468ebcf501a4838d` must be unchanged at handoff. |
| `R-X7` | Every file under `src/brichan/resources/`, including `src/brichan/resources/__init__.py` and every package file, is unchanged and digest-verified. The installed `.brichan` schema is untouched. |
| `R-X8` | Standard library only. Every module runs on the `requires-python = ">=3.10"` floor, verified by an explicit Python 3.10 run of the focused suites. |
| `R-X9` | Existing dossiers `TDW-006`, `TDW-007`, and `TDW-008` remain byte-identical. |
| `R-X10` | New wrappers under `scripts/` stay thin bootstrap shims matching the two existing dossier wrappers. |
| `R-X11` | Preservation, delta, and rollback are computed from the coordinator-captured implementation-start manifest, never from `HEAD`. The manifest records repository identity, the exact allowlist, presence/absence plus digest or content for every allowlisted path including the modified tracked files, the exact untracked-leaf inventory, and every protected resource file. |
| `R-X12` | The manifest is captured after plan version 3 is accepted, and explicitly excludes coordinator-, planner-, and reviewer-owned dossier paths, so planning and review leaves can never be confused with implementation leaves. |
| `R-X13` | Rollback reverts only this task's hunks and deletes only paths the manifest proves absent pre-implementation. Whole-file `git checkout --` is forbidden. Rollback aborts when a target changed concurrently. |
| `R-X14` | No migration is required or performed. Hand-authored dossiers stay first-class and are never rewritten by the generator. |

## Evaluation requirements

| ID | Requirement |
| --- | --- |
| `R-E1` | Evaluation dossiers are unmistakably synthetic fixtures. Every session identity matches the fixed prefix `synthetic-fixture-`, and every sample artifact states in its own claim that it is non-authoritative test data. |
| `R-E2` | No synthetic verdict, session, or identifier inequality is presented anywhere as evidence of real independent review. `results.md` carries the fixed non-authoritative declaration, asserted by a contract test. |
| `R-E3` | Every evaluation output path is enumerated as a closed leaf allowlist in `plan.md`, compared to the observed delta by exact set equality. |
| `R-E4` | Each sample carries eleven artifacts, a schema-valid `receipt.md`, and the canonical project-memory file that `validation.py:827-885` resolves. Sample receipts are validated explicitly against the isolated root. |
| `R-E5` | The durable evaluation records the AC3 metric unchanged, plus record line count, record byte count, authored-value count, and combined lines, and states which metric measures compactness and which approximates authoring burden. No timing, token, or cost claim is made. |
| `R-E6` | The authored-value count is produced by the exact algorithm in `design.md` — a fixed pre-order traversal of the declared schema order, counting each reached JSON scalar that is neither JSON `null` nor a string whose stripped form is empty or `null`, counting list elements individually and dictionary keys never. Two implementers following it must obtain the same integer. |

## Remediation traceability

| Finding from `versions/v2/plan-review.md` | Requirements | Plan steps |
| --- | --- | --- |
| `C1` raced temporary source publishes a symlink or foreign inode | `R-G8`, `R-G9`, `R-G11`, `R-G12`, threat-model boundary | 4, 5, 11 |
| `H1` ancestor-link exit promise versus unchanged validator | `R-V1` through `R-V6`, `R-S6`, `R-S12` | 2, 9, 14 |
| `H2` baseline cannot prove delta or rollback | `R-X11` through `R-X13` | 1, 19, 20 |
| `H3` detached-directory success with stale canonical path | `R-G17` | 5, 11 |
| `M1` record type schema contradicts its example | `R-G26`, `R-G27` | 3, 10 |
| `M2` evidence points at the mutable review path | version-3 supersession rule | all five artifacts |
| `TG1` post-preflight races plus namespace-identity failure | `R-G6`, `R-G17` | 11 |
| `TG2` inode mismatch, source substitution, cleanup and directory-`fsync` failure, temp exhaustion | `R-G11` through `R-G16` | 12 |
| `TG3` exact-type tests tied to the schema table | `R-G26`, `R-G27` | 3, 10 |
| `TG4` generated output against the validator | `R-G19` through `R-G25` | 13 |
| `TG5` unreadable artifact versus unreadable dossier boundary | `R-S11` | 14 |
| `TG6` `passed` floor versus `not-required` one-item rule | `R-S3` | 14 |
| `TG7` ancestor-link invalidity from the validator | `R-V5`, `R-S6` | 9, 14 |
| `TG8` Python 3.10 run and complete protected-state coverage | `R-X7`, `R-X8`, `R-X11` | 19 |
| `TG9` reproducible authored-value algorithm | `R-E6` | 17 |

## Acceptance-criteria traceability

| Parent AC | Requirements | Discharged by |
| --- | --- | --- |
| `TDW-009-AC1` | `R-G1` through `R-G18` | Plan steps 4, 5, 11, 12 |
| `TDW-009-AC2` | `R-G19` through `R-G27`, `R-E4` | Plan steps 3, 6, 10, 13, 16 |
| `TDW-009-AC3` | `R-G28`, `R-E3`, `R-E5`, `R-E6` | Plan steps 15, 16, 17 |
| `TDW-009-AC4` | `R-S1` through `R-S14` | Plan steps 7, 8, 14 |
| `TDW-009-AC5` | `R-V4`, `R-V6`, `R-X1` through `R-X14` | Plan steps 1, 2, 8, 18, 19 |
| `TDW-009-AC6` | all | Plan steps 13, 14, 16, 19 |
| `TDW-009-AC7` | `R-E1`, `R-E2`, `R-E5`, `R-E6` | Plan steps 17, 18 |
| `TDW-009-AC8` | all | Plan step 21, outside the implementation worker's scope |

## Claim or decision

Version 3 closes the version-2 findings by narrowing one guarantee honestly and
strengthening four others. The critical finding is closed the way the reviewer
named as acceptable and the coordinator then decided: the excluded attacker is
declared out of the threat model in fixed prominent wording, a dossier-scoped
advisory lock covers cooperating writers, no-overwrite publication is preserved,
and post-publication inode verification plus a final canonical re-walk convert
both the residual substitution and any namespace drift into a nonzero exit with a
named diagnostic. Nothing claims prevention against the excluded attacker.
`H1` is closed by making ancestor-symlinked authority paths validator-invalid
through five enumerated `validation.py` hunks, so one authority produces one
verdict. `H2` is closed by the implementation-start manifest. `M1` is closed by
an exhaustive key-to-type table whose worked example validates. `M2` is closed by
repointing every prior-review citation at an archived version.

## Evidence

- Direct execution on this platform reproduced the version-2 critical finding
  and its remedy: `os.link` with `follow_symlinks=False` over a symlinked source
  name published a symlink at the destination, and a post-publication
  `os.lstat(final, dir_fd=...)` compared against the recorded temporary inode
  distinguished that raced publication from an honest one. The same probe
  confirmed `fcntl.flock(dir_fd, LOCK_EX | LOCK_NB)` succeeds on a directory
  descriptor and refuses a second holder with `EWOULDBLOCK`, which is the lock
  `R-G8` specifies without creating any file.
- The same probe established the fact that forces the threat-model narrowing:
  `os.AT_EMPTY_PATH` and `os.O_TMPFILE` are not exposed by this CPython build and
  `/proc/self/fd` does not exist on darwin, so no portable Python 3.10
  standard-library primitive binds a link source to an open descriptor on both
  platforms.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md:64-89`
  states `C1` and names the two acceptable resolutions, one of which is an
  explicit threat-model narrowing with recorded acceptance; the version-3 packet
  amendment supplies that acceptance.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md:93-113`
  establishes `H1` against source: `validation.py:782-824` checks only
  `is_symlink` and `is_file` for the receipt, and `validation.py:827-885` checks
  the final candidate and containment but no ancestor, so `R-V1` through `R-V3`
  are required for the promised exit to come from the validator.
- A read-only scan of the working tree found no symlink anywhere outside `.git`
  and `.venv`, which is the concrete basis for `R-V6`: the two new diagnostics
  cannot change the verdict for any existing dossier.
- `src/brichan/contracts/task_dossier/validation.py:772-780,782-826,827-886`
  fixes the exact insertion points `R-X4` authorizes — the existing
  `_is_safe_relative` helper block, and the two link validators whose call sites
  gain one check each.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md:115-138,160-174`
  fixes the `H2` baseline gaps and the `M1` contradictions this version closes,
  including the omitted `src/brichan/resources/__init__.py` and the string-versus-integer
  artifact-version conflict.

## Uncertainty

- The excluded attacker is a stated limitation, not a solved problem. If a future
  CPython exposes `AT_EMPTY_PATH` or an equivalent descriptor-bound link, the
  narrowing should be revisited; nothing in this version depends on the
  narrowing being permanent.
- `R-G11` detects a raced publication but leaves the foreign entry in place, so
  operator action is required to inspect and remove it. Automatic removal was
  rejected because it would mean deleting an entry the run cannot prove it
  created.
- `R-G17` compares device and inode of the canonical chain. On a filesystem that
  recycles inode numbers within one run, a drift could theoretically evade the
  comparison. No such filesystem is in use here, and the check is strictly
  better than the version-2 absence of any final identity check.
- `R-V1` and `R-V2` add two diagnostics, which is a behaviour change for any
  repository that currently has a symlinked ancestor above an authority path.
  None exists here, but a downstream checkout could newly fail validation. This
  is the intended consequence of coordinator decision 2 and is recorded rather
  than hedged.
- No unresolved uncertainty remains about the three coordinator decisions, which
  are binding inputs rather than open questions.
