# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `requirements`
- Artifact version: `1`
- Origin: `packet:projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md@TDW-009-P1-v1`
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

## Scope of this specification

Two checkout-mode capabilities are specified:

1. a **generator** that renders all eleven standard artifacts for one task from
   one structured task record;
2. a **summary** command that reports one dossier's state without repairing it.

Both are additive. Neither removes an artifact, lowers an evidence floor,
weakens a validator diagnostic, changes the four named routes, or touches
installed resources. `docs/workflows/task-dossier.md` remains the contract and
`validate_task_dossiers.py` remains the sole authority on dossier validity.

Requirement IDs below are referenced by `design.md` and `plan.md`.

## Generator requirements

| ID | Requirement |
| --- | --- |
| `R-G1` | One structured record file, read once, produces exactly the eleven artifacts named in `schema.py:17-29` — no more and no fewer. |
| `R-G2` | Generation is dry-run by default. Without an explicit apply flag no byte is written and the planned action list is printed. |
| `R-G3` | Every write uses exclusive creation that cannot truncate an existing file and cannot follow a symlink. An artifact that already exists is reported `preserve` and left byte-identical. |
| `R-G4` | A symlinked artifact path, a symlinked dossier directory, or a dangling symlink at any artifact path aborts generation before any write, exactly as `scaffold.py:120-138` already does. |
| `R-G5` | The dossier directory is resolved through the existing containment rule so a record can never write outside the selected projects root. |
| `R-G6` | Record identity — `task_id`, `project`, `level` — must equal the identity supplied on the command line; a mismatch is a refusal, not a silent preference. |
| `R-G7` | The generator derives only mechanical fields: `Task ID`, `Task level`, `Artifact`, `Owner`, the index `Task identity` triple, the canonical receipt path, and the index artifact status table. Every derived value is recomputable from the record and the dossier path. |
| `R-G8` | The generator never derives, defaults, or infers claim, evidence, uncertainty, phase state, applicability, applicability rationale, authorship, authoring session, effective route, effective model, effective effort, reviewing session, review verdict, plan status, ship authorization, or review-target identity. A missing value is a refusal. |
| `R-G9` | A review artifact whose phase state is `passed` must carry an explicit verdict drawn from `REVIEW_VERDICTS`. The generator never writes `PASS` that the record did not state. |
| `R-G10` | Any record value that `parser.is_placeholder` classifies as a placeholder, in a position the contract requires to be concrete, is a refusal. Generation cannot emit an unfilled template. |
| `R-G11` | A `passed` artifact must carry at least `MINIMUM_EVIDENCE_ITEMS[level]` concrete evidence items; a `not-required` artifact must carry at least one, plus a concrete rationale, claim, and uncertainty statement. These mirror `validation.py:276-355` exactly and are neither stricter nor looser. |
| `R-G12` | Any record value matching `PERSONAL_PATH_PATTERNS` is a refusal. |
| `R-G13` | For `index`, only the projection sections in `INDEX_PROJECTION_SECTIONS` may be emitted, only the artifact status table may appear, and no receipt-owned field label may be emitted. Supplemental sections are rejected for `index` and permitted for the other ten artifacts. |
| `R-G14` | Rendering is deterministic: identical record plus identical target path yields byte-identical output, with fixed artifact order, fixed section order, fixed field order, and no timestamp, hostname, absolute path, or unordered-collection repr. |
| `R-G15` | The generator refuses an unknown top-level key, an unknown per-artifact key, an unknown artifact name, an unknown `schema_version`, a non-object root, or malformed JSON, with a diagnostic naming the offending key. |
| `R-G16` | The generator reads the routing manifest never, and mentions neither `model-routing.json` nor `model_routing`, preserving the check at `tests/contract/test_task_dossier_contract.py:192-198`. |

## Summary requirements

| ID | Requirement |
| --- | --- |
| `R-S1` | The summary is read-only. It creates, modifies, moves, and deletes nothing, and never repairs what it reports. |
| `R-S2` | It reports per-artifact applicability and phase state for all eleven artifacts, in the fixed order of `ARTIFACTS`. |
| `R-S3` | It reports each artifact's concrete evidence count against the level floor from `MINIMUM_EVIDENCE_ITEMS`, and names every artifact below its floor. |
| `R-S4` | It reports effective model provenance per artifact — authorship, authoring session, effective route, effective model, effective effort — read from the artifacts themselves, never resolved from the routing manifest. |
| `R-S5` | It reports plan identity and review identity: plan ID, plan status, plan artifact version, the index accepted plan ID and version, and each review's reviewed plan ID and version, flagging any disagreement. |
| `R-S6` | It reports authority-link health for the canonical receipt path and the project memory path: declared value, expected value, existence, not-a-symlink, and inside-repository. It reports health only and copies no receipt or project-memory content. |
| `R-S7` | It reports review independence as `independent`, `not-independent`, or `unknown` by comparing the plan authoring session against each review's reviewing session and authoring session, matching `validation.py:464-477`. `unknown` is reported when a session is a placeholder, and is never reported as independent. |
| `R-S8` | Exit code is `0` only when the dossier produces no validator diagnostic. Any invalid state exits `1`. With the complete gate requested, an incomplete dossier also exits `1`. A missing projects root, an absent requested task, or an unreadable dossier exits `2`. |
| `R-S9` | Validity is decided by calling the existing `validate_dossier`, not by a second implementation of the contract. The summary adds reporting, never a competing verdict. |
| `R-S10` | Output is deterministic and byte-stable for a fixed dossier: fixed section order, sorted collections, no timestamps, and no absolute path beyond the operator-supplied root. |
| `R-S11` | A machine-readable output form is available alongside the human form, carrying the same facts and the same exit code. |
| `R-S12` | Stale state is reported, not hidden: a status-table row disagreeing with the artifact it describes, a dangling receipt or memory link, a review naming a plan version other than the current one, and a `passed` review whose verdict is `CHANGES REQUIRED` each appear in the report and each force a nonzero exit. |

## Safety and compatibility requirements

| ID | Requirement |
| --- | --- |
| `R-X1` | `ARTIFACTS`, `METADATA_FIELDS`, `PHASE_STATES`, `APPLICABILITY_STATES`, `MINIMUM_EVIDENCE_ITEMS`, and every existing validator diagnostic keep their current values and messages. Additions to `schema.py` are additive constants only. |
| `R-X2` | `scaffold.py` keeps its CLI surface, its dry-run-first default, and its behaviour; the only permitted change is promoting the private exclusive-create helper to a shared name so the generator reuses one audited write primitive instead of copying it. |
| `R-X3` | `parser.py` is not modified. The generator and the summary consume its existing primitives. |
| `R-X4` | `config/model-routing.json` keeps its schema version, its four routes, and its values, and gains no workflow, phase, level, or artifact key. |
| `R-X5` | `src/brichan/resources/dogfood_v1/` is unchanged and the installed `.brichan` schema is untouched; the capability is checkout-only. |
| `R-X6` | Standard library only. No third-party dependency is added, and no module requires a Python newer than the `requires-python = ">=3.10"` floor in `pyproject.toml:12`. |
| `R-X7` | Existing dossiers `TDW-006`, `TDW-007`, and `TDW-008` remain byte-identical and keep passing `validate_task_dossiers.py projects --require-complete`. |
| `R-X8` | New wrappers under `scripts/` stay thin bootstrap shims that only extend `sys.path` and delegate to `src/`, matching the two existing dossier wrappers. |
| `R-X9` | Generated evaluation samples live in an isolated projects root under `evals/` so they are never discovered by `make dossiers`, and they carry no Markdown link that `check_repository_paths.py` would resolve. |
| `R-X10` | No migration is required or performed: the record format is new, opt-in, and has no predecessor. Hand-authored dossiers stay first-class and are never rewritten by the generator. |

## Acceptance-criteria traceability

| Parent AC | Requirements | Discharged by |
| --- | --- | --- |
| `TDW-009-AC1` | `R-G1`, `R-G3`, `R-G4`, `R-G5`, `R-G6` | Plan steps 2, 3, 6; unit tests for preserve, symlink abort, dangling symlink, root escape, and identity mismatch |
| `TDW-009-AC2` | `R-G7` through `R-G13` | Plan steps 2, 3, 7, 9; generated sample validated with the complete gate |
| `TDW-009-AC3` | `R-G14`, `R-X9` | Plan steps 8, 9; measured line counts against the 639-line and 716-line baselines at `evals/task-dossier-pilots/results.md:56-57` |
| `TDW-009-AC4` | `R-S1` through `R-S12` | Plan steps 4, 5, 7; unit tests for each reported field and each exit code |
| `TDW-009-AC5` | `R-X1` through `R-X8`, `R-X10` | Plan steps 1, 10, 11; contract tests plus the unchanged existing suites |
| `TDW-009-AC6` | all | Plan steps 7, 9, 12 |
| `TDW-009-AC7` | `R-X9` | Plan step 10 |
| `TDW-009-AC8` | all | Plan step 13, outside the implementation worker's scope |

## Claim or decision

TDW-009 is fully specified by the thirty-eight requirements above, and each one
is checkable by an executable command or a byte comparison rather than by
reviewer impression. The specification adds two opt-in capabilities and
subtracts nothing: the eleven-artifact set, the per-level evidence floors, the
review-independence rule, and the validator's sole authority over dossier
validity carry through unchanged, and the only sanctioned edits to existing
behaviour are the additive-constant and shared-write-helper boundaries fixed by
`R-X1` and `R-X2`.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:36-45`
  fixes acceptance criteria `TDW-009-AC1` through `TDW-009-AC8`; every row of the
  traceability table maps one of them onto named requirements and onto the plan
  step that discharges it.
- `src/brichan/contracts/task_dossier/validation.py:242-355` is the exact
  behaviour `R-G11` mirrors: `passed` artifacts are held to
  `MINIMUM_EVIDENCE_ITEMS[level]` concrete items at lines 339-347, while
  `not-required` artifacts need at least one item plus rationale, claim, and
  uncertainty at lines 276-309. Mirroring rather than reinventing is what keeps
  the generator from becoming a second, divergent contract.
- `src/brichan/contracts/task_dossier/scaffold.py:151-217` supplies the audited
  write primitive that `R-G3` and `R-X2` reuse: `O_CREAT | O_EXCL | O_WRONLY`
  plus `O_NOFOLLOW`, a pre-write symlink guard, and a post-collision abort that
  preserves whatever appeared during the planning window.
- `evals/task-dossier-pilots/results.md:54-58` records the 639-line Level 0 and
  716-line Level 1 baselines that `TDW-009-AC3` measures against, and fixes the
  measurement unit as total lines across the eleven artifacts.
- `tests/contract/test_task_dossier_contract.py:192-198` is why `R-G16` is a
  requirement rather than a preference: the routing-neutrality test scans every
  `*.py` file in the package, so a new module mentioning `model_routing` would
  fail an existing gate.
- `pyproject.toml:12` pins `requires-python = ">=3.10"`, which is the concrete
  basis for `R-X6` and for rejecting a `tomllib`-based record format in
  `options.md`.

## Uncertainty

- The 30% line-reduction target in `TDW-009-AC3` is arithmetic, not judgment,
  but the content a record author supplies is not bounded by these requirements.
  A verbose record can exceed the budget while satisfying every other
  requirement, so the plan measures the produced samples instead of asserting
  the projection, and `design.md` records both the floor and the slack.
- `R-S7` reports `unknown` when a session identity is a placeholder. Whether an
  `unknown` independence result should additionally force a nonzero exit is
  deliberately left to the validator: a placeholder session already produces a
  provenance diagnostic for a model-authored artifact, and duplicating that
  judgment in the summary would create the second authority `R-S9` forbids.
- No unresolved uncertainty remains about scope. The eleven-artifact set,
  routing neutrality, the installed-resource boundary, and the standard-library
  constraint are fixed by the parent packet and are restated here as refusable
  requirements rather than as assumptions.
