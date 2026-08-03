# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `requirements`
- Artifact version: `2`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/plan-review.md@TDW-009-P1-v1+task-packet-amendment`
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

## Version 2 supersession

Version 1 is preserved byte-identically at `versions/v1/requirements.md` and is
superseded, not rewritten. Version 2 exists because independent review of
`TDW-009-P1` version 1 returned `CHANGES REQUIRED` with one critical, six high,
and two medium findings plus nine test-gap classes.

Three coordinator decisions in the task-packet amendment are binding inputs and
are not re-opened here:

1. Evaluation dossiers are unmistakably synthetic, non-authoritative fixtures.
2. The summary defaults to the complete gate; an incomplete dossier exits
   nonzero. No relaxed default is authorized.
3. Generation uses a generator-specific POSIX directory-descriptor writer
   anchored from the selected projects root. Existing scaffold behaviour is
   unchanged.

## Scope of this specification

Two additive checkout-mode capabilities: a **generator** that renders all eleven
standard artifacts from one structured task record, and a **summary** command
that reports one dossier's state without repairing it. Neither removes an
artifact, lowers an evidence floor, weakens a validator diagnostic, changes the
four named routes, or touches installed resources.

## Generator requirements

| ID | Requirement |
| --- | --- |
| `R-G1` | One structured record file, read once, produces exactly the eleven artifacts named in `schema.py:17-29` — no more and no fewer. |
| `R-G2` | Generation is dry-run by default. Without an explicit apply flag no byte is written and the planned action list is printed. |
| `R-G3` | All eleven artifact bodies are rendered in memory and pass every record check before any filesystem mutation occurs. A render or validation failure leaves the dossier untouched. |
| `R-G4` | Every directory in the chain `<projects-root>/<project>/handoffs/<task-id>` is opened with `O_RDONLY \| O_DIRECTORY \| O_NOFOLLOW` relative to its already-open parent descriptor. No pathname below the operator-supplied projects root is ever re-resolved. |
| `R-G5` | A component that is a symlink, or is not a directory, aborts before any write. Both `ELOOP` and `ENOTDIR` are treated as refusals, because the two POSIX implementations in scope differ in which one they raise. |
| `R-G6` | Replacing the dossier directory, the `handoffs` directory, or the project directory with a symlink at any point after its descriptor is obtained cannot cause a write outside the projects root: every subsequent operation is descriptor-relative and therefore bound to the original inode. |
| `R-G7` | Missing project, `handoffs`, and dossier directories are created with `os.mkdir(..., dir_fd=parent)` using single path components only. A component containing a separator, `.`, or `..` is impossible by construction and is additionally refused. |
| `R-G8` | Each artifact is published atomically: written to a private temporary name in the dossier directory, fully written, `fsync`-ed, inode-identity-verified, then published with `os.link(temp, final, src_dir_fd, dst_dir_fd, follow_symlinks=False)`. `os.rename` and `os.replace` are forbidden because rename overwrites and `os.replace` does not accept `dir_fd`. |
| `R-G9` | Publication never overwrites. `EEXIST` from the publishing link means the artifact appeared in the window and is reported `preserve`; the existing bytes are untouched. |
| `R-G10` | A temporary file is unlinked only after its device and inode are re-verified against the descriptor that created it. On mismatch the temporary is left in place and a diagnostic is emitted, because unlinking an unverified name would delete a file this invocation did not create. |
| `R-G11` | No artifact is ever published in a partial state. Any write, `fsync`, or close failure aborts before publication, so a truncated body can never become a final artifact and can never be classified `preserve` by a later run. |
| `R-G12` | Multi-file partial progress is retained only when every retained artifact is complete. Such a run exits nonzero and emits an explicit partial-adoption diagnostic naming published and unpublished artifacts, so a retry has deterministic recovery semantics. |
| `R-G13` | The dossier directory descriptor is `fsync`-ed after publication so the directory entries are durable. |
| `R-G14` | Record identity — `task_id`, `project`, `level` — must equal the identity supplied on the command line; a mismatch is a refusal, not a silent preference. |
| `R-G15` | The generator derives only mechanical fields: `Task ID`, `Task level`, `Artifact`, `Owner`, the index `Task identity` triple, the canonical receipt path, and the index artifact status table. Every derived value is recomputable from the record and the dossier path. |
| `R-G16` | The generator never derives, defaults, or infers claim, evidence, uncertainty, phase state, applicability, applicability rationale, authorship, authoring session, effective route, effective model, effective effort, reviewing session, review verdict, plan status, ship authorization, or review-target identity. A missing value is a refusal. |
| `R-G17` | A review artifact whose phase state is `passed` must carry an explicit verdict drawn from `REVIEW_VERDICTS`. The generator never writes `PASS` that the record did not state. |
| `R-G18` | Any record value that `parser.is_placeholder` classifies as a placeholder, in a position the contract requires to be concrete, is a refusal. Generation cannot emit an unfilled template. |
| `R-G19` | A `passed` artifact must carry at least `MINIMUM_EVIDENCE_ITEMS[level]` concrete evidence items; a `not-required` artifact must carry at least one, plus a concrete rationale, claim, and uncertainty statement. These mirror `validation.py:276-355` exactly and are neither stricter nor looser. |
| `R-G20` | Any record value matching `PERSONAL_PATH_PATTERNS` is a refusal. |
| `R-G21` | For `index`, only the projection sections in `INDEX_PROJECTION_SECTIONS` may be emitted, only the artifact status table may appear, and no receipt-owned field label may be emitted. Supplemental sections are refused for `index` and permitted for the other ten artifacts. |
| `R-G22` | The record is parsed under an exact recursive type schema. `json.load` is called with an `object_pairs_hook` that refuses duplicate object keys; every scalar is checked with `type(value) is str` or `type(value) is int` so a JSON boolean can never satisfy an integer position; unknown and missing keys at every level are refused with the offending locator named. |
| `R-G23` | Markdown structure injection is refused, not escaped. Single-line scalar positions — metadata values, extra-section field values, index identity values, supplemental section titles, evidence items, and uncertainty items — refuse newlines, backticks, pipes, control characters, and a leading list marker. Multi-line positions — claim text and supplemental section bodies — refuse any line that would parse as a heading of level one or two, a table row, a list item, a `- Label:` field, or a fence. No accepted value can create a section, a field, a table, or an extra evidence bullet. |
| `R-G24` | Rendering is deterministic: identical record plus identical target yields byte-identical output, with fixed artifact order, fixed section order, fixed field order, and no timestamp, hostname, process ID, absolute path, or unordered-collection repr in the output. |
| `R-G25` | The generator reads the routing manifest never, and mentions neither `model-routing.json` nor `model_routing`, preserving the check at `tests/contract/test_task_dossier_contract.py:192-198`. |

## Summary requirements

| ID | Requirement |
| --- | --- |
| `R-S1` | The summary is read-only. It creates, modifies, moves, and deletes nothing, and never repairs what it reports. |
| `R-S2` | It reports per-artifact applicability and phase state for all eleven artifacts, in the fixed order of `ARTIFACTS`. |
| `R-S3` | Evidence depth is reported against the rule that actually applies to each artifact: the level floor from `MINIMUM_EVIDENCE_ITEMS` for a `passed` artifact, the one-item rule for a `not-required` artifact, and `not-applicable` for `pending`, `active`, and `blocked`. A `not-required` artifact is never labelled below-floor for holding fewer items than the level floor. |
| `R-S4` | It reports effective model provenance per artifact — authorship, authoring session, effective route, effective model, effective effort — read from the artifacts themselves, never resolved from the routing manifest. |
| `R-S5` | It reports plan identity and review identity: plan ID, plan status, plan artifact version, the index accepted plan ID and version, and each review's reviewed plan ID and version, flagging any disagreement. |
| `R-S6` | It reports authority-link health for the canonical receipt path and the project memory path: declared value, expected value, existence, not-a-symlink, no symlinked ancestor between the repository root and the target, and containment inside the repository. It reports health only and copies no receipt or project-memory content. |
| `R-S7` | It reports review independence as `independent`, `not-independent`, or `unknown` by comparing the plan authoring session against each review's reviewing session and against its authoring session, matching `validation.py:464-477`. Both comparison arms are reported separately. `unknown` is reported when either identity is a placeholder and is never reported as independent. |
| `R-S8` | Every rendered form states, in fixed wording, that session-identifier inequality is a deterministic consistency signal and not proof that two independent sessions existed. |
| `R-S9` | The root verdict comes from `validate_projects`, so partial-adoption and duplicate-task-ID diagnostics can never be lost. `validate_dossier` supplies per-dossier detail only and never produces an exit code that contradicts the root verdict. |
| `R-S10` | The complete gate is the default and only exit semantics: the exit code is `0` only when `validate_projects(..., require_complete=True)` produces no diagnostic for the selected scope. There is no flag that relaxes it. |
| `R-S11` | Exit codes are `0` for a clean complete verdict, `1` for any diagnostic or incompleteness, and `2` for a missing projects root, a `--task` value matching no discovered dossier, a `--task` value matching more than one dossier, or a dossier that cannot be read. Duplicate task IDs make `--task` ambiguous and are refused rather than silently resolved. |
| `R-S12` | Stale state is reported, not hidden: a status-table row disagreeing with the artifact it describes, a dangling or ancestor-symlinked receipt or memory link, a review naming a plan version other than the plan's current artifact version, a `passed` review whose verdict is `CHANGES REQUIRED`, and a handoff with dossier artifacts but no index each appear in the report and each force a nonzero exit. |
| `R-S13` | An artifact that cannot be read or parsed is reported as unreadable with its path and reason, and never silently omitted from any section. |
| `R-S14` | Output is deterministic and byte-stable for a fixed dossier: fixed section order, sorted collections, no timestamp, no process ID, and no absolute path beyond the operator-supplied root. A machine-readable form carries the same facts and the same exit code as the human form. |

## Safety and compatibility requirements

| ID | Requirement |
| --- | --- |
| `R-X1` | `ARTIFACTS`, `METADATA_FIELDS`, `PHASE_STATES`, `APPLICABILITY_STATES`, `MINIMUM_EVIDENCE_ITEMS`, and every existing validator diagnostic keep their current values and messages. Additions to `schema.py` are additive constants only. |
| `R-X2` | `scaffold.py` is not modified at all. Its CLI, its dry-run-first default, its private helpers, and its behaviour are untouched, and the generator shares no write code with it. The generator imports only `dossier_path` from it, for identity and containment validation of the declared path. |
| `R-X3` | `parser.py` is not modified. The generator and the summary consume its existing primitives. |
| `R-X4` | `validation.py` receives exactly two hunks: `ARTIFACT_EXTRA_SECTIONS` added to the existing `from .schema import (...)` block after `ARTIFACTS`, and the literal at `validation.py:71-78` replaced by `EXTRA_SECTION_FIELDS = ARTIFACT_EXTRA_SECTIONS`. No other line changes. |
| `R-X5` | `__init__.py` keeps `main` bound to `validation.main` unchanged. The two new CLI entry points are exported only under the non-colliding names `generate_main` and `summary_main`, and a test asserts both the preserved binding and the absence of collision. |
| `R-X6` | `config/model-routing.json` keeps its schema version, its four routes, and its values, and gains no workflow, phase, level, or artifact key. |
| `R-X7` | `src/brichan/resources/dogfood_v1/` is unchanged and the installed `.brichan` schema is untouched; the capability is checkout-only. |
| `R-X8` | Standard library only. No third-party dependency, and every module runs on the `requires-python = ">=3.10"` floor in `pyproject.toml:12`. Verification includes an explicit Python 3.10 run of the focused suites. |
| `R-X9` | Existing dossiers `TDW-006`, `TDW-007`, and `TDW-008` remain byte-identical. |
| `R-X10` | New wrappers under `scripts/` stay thin bootstrap shims that only extend `sys.path` and delegate to `src/`, matching the two existing dossier wrappers. |
| `R-X11` | Preservation is proved against a coordinator-owned pre-task path-and-digest baseline, never against `HEAD`. The working tree carries pre-existing user changes, so any check that assumes a clean `HEAD` is invalid by construction. |
| `R-X12` | Rollback reverts only hunks belonging to this task and deletes only paths this task created, verified against the same baseline. Whole-file `git checkout --` is forbidden because it would discard concurrent user edits. Rollback aborts when a target changed concurrently. |
| `R-X13` | No migration is required or performed: the record format is new, opt-in, and has no predecessor. Hand-authored dossiers stay first-class and are never rewritten by the generator. |

## Evaluation requirements

| ID | Requirement |
| --- | --- |
| `R-E1` | Evaluation dossiers are unmistakably synthetic fixtures. Every session identity in a sample record matches a fixed synthetic prefix, and every sample artifact states in its own claim that it is non-authoritative test data. |
| `R-E2` | No synthetic `PASS` verdict, synthetic reviewing session, or synthetic identifier inequality is presented anywhere as evidence of real independent review. `evals/task-dossier-pilots/concise/results.md` declares the samples non-authoritative in fixed wording, and a test asserts both the synthetic prefix and that declaration. |
| `R-E3` | Every evaluation output path is enumerated as a closed leaf allowlist in `plan.md`. The observed task delta is compared against that allowlist by exact set equality; a path outside it is a failure, not a warning. |
| `R-E4` | Each sample carries the fixtures its own validation requires: eleven artifacts, a schema-valid `receipt.md`, and the canonical project-memory file that `validation.py:827-885` resolves. Sample receipts are validated explicitly by the receipt validator against the isolated root. |
| `R-E5` | The durable evaluation records the AC3 metric unchanged — total lines across the eleven artifacts — and additionally records record line count, record byte count, authored non-blank value count, and combined record-plus-output lines. It states explicitly which metric measures artifact compactness and which approximates authoring burden, and claims no timing, token, or cost saving. |

## Remediation traceability

| Finding | Requirements | Plan steps |
| --- | --- | --- |
| `C1` raced directory-symlink escape | `R-G4` through `R-G7`, `R-X2` | 3, 4, 8 |
| `H1` truncated artifact published and preserved | `R-G3`, `R-G8` through `R-G13` | 4, 9 |
| `H2` fabricated review and receipt authority | `R-E1`, `R-E2`, `R-E4` | 12, 13, 15 |
| `H3` summary exit semantics and lost project diagnostics | `R-S9` through `R-S13` | 6, 11 |
| `H4` malformed JSON and Markdown-structure injection | `R-G22`, `R-G23` | 2, 10 |
| `H5` evaluation writes hidden behind a directory | `R-E3`, `R-E4` | 12, 13, 16 |
| `H6` dirty-worktree checks and rollback | `R-X11`, `R-X12` | 1, 17, 18 |
| `M1` compression measured, authoring burden not | `R-E5` | 14 |
| `M2` underspecified source-API edits | `R-X4`, `R-X5` | 1, 7 |
| `TG1` post-preflight ancestor races | `R-G6` | 8 |
| `TG2` write, flush, fsync, close, permission, disk-full faults | `R-G11`, `R-G12` | 9 |
| `TG3` duplicate keys, exact types, structure injection | `R-G22`, `R-G23` | 10 |
| `TG4` generator output against the validator result | `R-G15` through `R-G21` | 11 |
| `TG5` partial adoption, duplicate IDs, ambiguous task, incomplete default | `R-S9` through `R-S13` | 11 |
| `TG6` passed floor versus `not-required` one-item rule | `R-S3` | 11 |
| `TG7` authority-link ancestors and both independence arms | `R-S6`, `R-S7`, `R-S8` | 11 |
| `TG8` explicit 3.10 run and before/after byte manifest | `R-X8`, `R-X11` | 17 |
| `TG9` exact line-budget invocation and record-size metrics | `R-E5` | 14 |

## Acceptance-criteria traceability

| Parent AC | Requirements | Discharged by |
| --- | --- | --- |
| `TDW-009-AC1` | `R-G1` through `R-G14` | Plan steps 3, 4, 8, 9 |
| `TDW-009-AC2` | `R-G15` through `R-G23`, `R-E4` | Plan steps 2, 5, 10, 11, 13 |
| `TDW-009-AC3` | `R-G24`, `R-E3`, `R-E5` | Plan steps 12, 13, 14 |
| `TDW-009-AC4` | `R-S1` through `R-S14` | Plan steps 6, 7, 11 |
| `TDW-009-AC5` | `R-X1` through `R-X13` | Plan steps 1, 7, 16, 17 |
| `TDW-009-AC6` | all | Plan steps 11, 13, 17 |
| `TDW-009-AC7` | `R-E1`, `R-E2`, `R-E5` | Plan steps 14, 15 |
| `TDW-009-AC8` | all | Plan step 19, outside the implementation worker's scope |

## Claim or decision

Version 2 replaces the pathname-based write model that made `C1` possible with a
descriptor-anchored one, and replaces "accepted partial state" with atomic
per-artifact publication by hard link. Both were mechanically verified on this
platform before being specified. The remaining findings are closed by
tightening what the record may contain (`R-G22`, `R-G23`), by moving the root
verdict to `validate_projects` and making the complete gate the only exit
semantics (`R-S9` through `R-S11`), by declaring the evaluation fixtures
synthetic and enumerating their leaves (`R-E1` through `R-E4`), by measuring
authoring burden alongside output size (`R-E5`), and by replacing
`HEAD`-relative preservation checks with a pre-task digest baseline (`R-X11`,
`R-X12`). Scaffold behaviour is now explicitly out of bounds (`R-X2`), so the
one compatibility concession version 1 requested is withdrawn.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan-review.md:47-72`
  states `C1` precisely: `dossier_path` resolves containment once, `plan_scaffold`
  checks only the final dossier component, and `apply_scaffold` opens artifacts
  by full pathname, so `O_NOFOLLOW` protects only the last component. `R-G4`
  through `R-G7` remove pathname re-resolution entirely rather than adding
  another preflight.
- Direct execution on this platform confirmed every primitive `R-G4` through
  `R-G10` depends on: `os.open`, `os.mkdir`, `os.stat`, `os.link`, and
  `os.unlink` all report membership in `os.supports_dir_fd`; `os.replace` does
  not, which is the mechanical reason `R-G8` forbids it. A link onto an existing
  name failed with `EEXIST` and left the original bytes intact, and opening a
  symlinked directory with `O_DIRECTORY | O_NOFOLLOW` failed with `ENOTDIR` on
  darwin rather than `ELOOP`, which is why `R-G5` names both errnos.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan-review.md:126-150`
  shows the two independent defects `R-S9` through `R-S11` close: the default
  gate accepts `pending`, `active`, and `blocked`, and `validate_dossier` cannot
  see the partial-adoption and duplicate-task-ID diagnostics that
  `validation.py:1160-1195` raises only in `validate_projects`.
- A read-only probe reproduced the `H4` mechanism exactly: `json.loads` on an
  object with a repeated key returns only the last value, while the same input
  under an `object_pairs_hook` that tracks seen keys raises. The same probe
  confirmed `isinstance(True, int)` is true while `type(True) is int` is false,
  which is the basis for the exact-type rule in `R-G22`.
- `src/brichan/contracts/task_dossier/validation.py:827-885` resolves the
  project-memory link against `projects_root.parent`, requires a name from
  `CANONICAL_MEMORY_FILES` directly inside the project directory, and requires
  the file to exist — the concrete reason `R-E4` adds a synthetic memory file per
  sample, which version 1 omitted.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:68-91`
  records the three binding coordinator decisions and the instruction that
  version 1 be preserved
  before supersession; `versions/v1/` holds the five byte-identical snapshots
  that make this version a supersession rather than a rewrite.
- `src/brichan/contracts/task_dossier/validation.py:28-34` shows the existing
  `from .schema import (...)` block with `ARTIFACTS` on line 30, which fixes the
  exact insertion point `R-X4` authorizes; `__init__.py:11-16` shows the existing
  `main` binding that `R-X5` preserves.

## Uncertainty

- `R-G6` guarantees that a post-descriptor swap cannot redirect a write outside
  the root; it does not guarantee the write succeeds. A racer that swaps an
  ancestor may cause a later artifact to fail, which `R-G12` converts into a
  nonzero exit with a partial-adoption diagnostic rather than into silence. That
  is the intended outcome and is not a residual defect.
- The projects root itself is opened by pathname once. If the operator supplies
  a root reached through a symlinked ancestor, generation writes inside whatever
  that root resolves to. This is the same trust boundary the existing scaffold
  and validator already assume, and it is recorded rather than removed.
- `R-G23` refuses structural characters instead of escaping them. Some
  legitimate prose — a claim containing a pipe, or evidence quoting a fenced
  block — is therefore unwritable through a record and must be hand-authored.
  Refusal was chosen over escaping because an escaping rule would need its own
  round-trip proof against the validator's parser.
- `R-S8` states the independence caveat but cannot remove it. Identifier
  inequality remains a consistency signal; only the receipt lifecycle records
  that two sessions actually existed. No unresolved uncertainty remains about
  the three coordinator decisions, which are treated as fixed inputs.
