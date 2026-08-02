# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `design`
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

## Module layout

Three new modules, two new thin wrappers, two bounded edits to existing modules.

| Path | Role | New or edited |
| --- | --- | --- |
| `src/brichan/contracts/task_dossier/record.py` | Record dataclasses, JSON loading, record-level diagnostics | new |
| `src/brichan/contracts/task_dossier/generate.py` | Deterministic Markdown rendering, plan/apply, CLI `main()` | new |
| `src/brichan/contracts/task_dossier/summary.py` | Read-only summary computation, text and JSON rendering, CLI `main()` | new |
| `scripts/generate_task_dossier.py` | Thin bootstrap wrapper | new |
| `scripts/summarize_task_dossier.py` | Thin bootstrap wrapper | new |
| `src/brichan/contracts/task_dossier/schema.py` | Additive constants only | edited |
| `src/brichan/contracts/task_dossier/scaffold.py` | Rename one private helper to a shared name | edited |
| `src/brichan/contracts/task_dossier/__init__.py` | Re-export the new public names | edited |

Import direction stays acyclic and one-way:

```text
schema.py  ──▶ parser.py ──▶ validation.py ──▶ summary.py
    │                                    ▲
    ├──▶ scaffold.py ──▶ generate.py ────┘ (generate imports scaffold, not validation)
    └──▶ record.py  ──▶ generate.py
```

`record.py` and `generate.py` do not import `validation.py`; they mirror its
rules through the shared constants in `schema.py` and the shared predicates in
`parser.py`. `summary.py` imports `validation.py` and calls `validate_dossier`
so the validator stays the single authority (`R-S9`).

## Additive constants in `schema.py`

Four constants are added. Nothing is removed or renamed.

```python
RECORD_SCHEMA_VERSION = 1

ARTIFACT_TITLES = {
    "index": "Task dossier index",
    "request": "Request provenance",
    ...   # one H1 title per artifact, matching the existing templates
}

ARTIFACT_OWNERS = {
    "index": "coordinator", "request": "coordinator",
    "requirements": "planner", "brief": "planner", "options": "planner",
    "design": "planner", "client-follow-up-questions": "coordinator",
    "plan": "planner", "plan-review": "reviewer", "code-review": "reviewer",
    "pr-desc": "generator",
}

ARTIFACT_EXTRA_SECTIONS = {
    "index": ((INDEX_IDENTITY_SECTION, INDEX_IDENTITY_FIELDS),),
    "request": ((REQUEST_PROVENANCE_SECTION, REQUEST_PROVENANCE_FIELDS),),
    "plan": ((PLAN_STATUS_SECTION, PLAN_STATUS_FIELDS),),
    "plan-review": ((REVIEW_TARGET_SECTION, REVIEW_TARGET_FIELDS),),
    "code-review": ((REVIEW_TARGET_SECTION, REVIEW_TARGET_FIELDS),),
    "pr-desc": ((REMOTE_ACTION_SECTION, REMOTE_ACTION_FIELDS),),
}
```

`validation.EXTRA_SECTION_FIELDS` is re-expressed as
`EXTRA_SECTION_FIELDS = ARTIFACT_EXTRA_SECTIONS` so one table serves both the
validator and the generator. This is a value-identical substitution: the
existing literal at `validation.py:71-78` has exactly these six keys and these
pairs, so every current diagnostic is unchanged, which the untouched validator
suite proves.

`ARTIFACT_OWNERS` reproduces the writer column of the standard-artifact table at
`docs/workflows/task-dossier.md:25-38`. A contract test asserts every value is a
member of `OWNERS` and that `plan-review` and `code-review` map to `reviewer`,
so the constant cannot drift from `_validate_ownership`.

## Record schema, version 1

The record is one UTF-8 JSON object. Unknown keys at any level are refused.

```json
{
  "schema_version": 1,
  "task_id": "TDW-010",
  "level": "0",
  "project": "example-project",
  "origin": "packet:projects/example-project/handoffs/TDW-010/task-packet.md@TDW-010-P1-v1",
  "index_identity": {
    "Project memory path": "projects/example-project/current-state.md",
    "Accepted plan ID": "TDW-010-P1",
    "Accepted plan version": "1",
    "Review route strength": "routine",
    "Review route override": "null",
    "Ship authorization": "not-requested",
    "Ship authorization evidence": "null"
  },
  "artifacts": {
    "requirements": {
      "version": "1",
      "origin": null,
      "phase_state": "passed",
      "applicability": "required",
      "applicability_rationale": "null",
      "authorship": "model",
      "authoring_session": "0000-session",
      "effective_route": "plan",
      "effective_model": "claude-opus-5",
      "effective_effort": "high",
      "reviewing_session": "null",
      "review_verdict": "null",
      "fields": {"Plan ID": "TDW-010-P1", "Plan status": "accepted"},
      "sections": [{"title": "Steps", "body": ["1. First step."]}],
      "claim": "One paragraph asserting what this artifact decides.",
      "evidence": ["`path/to/file.py:10-20` shows ..."],
      "uncertainty": ["No unresolved uncertainty remains."]
    }
  }
}
```

Rules:

- `schema_version` must equal `RECORD_SCHEMA_VERSION`; any other value is
  refused with the observed and expected values named.
- `task_id` must match `TASK_ID_PATTERN`, `project` must match
  `PROJECT_SLUG_PATTERN`, `level` must be a member of `TASK_LEVELS`, and all
  three must equal the values supplied on the command line (`R-G6`).
- `artifacts` must carry exactly the eleven keys of `ARTIFACTS`. A missing key
  and an unknown key are both refusals (`R-G1`, `R-G15`).
- `origin` is inherited from the top-level `origin` unless the artifact
  overrides it; both must be non-placeholder.
- `fields` is accepted only for the six artifacts in `ARTIFACT_EXTRA_SECTIONS`,
  must carry exactly that artifact's field labels, and is refused for the other
  five. For `index`, the `Task identity` values come from `index_identity`
  instead, and `Task ID`, `Task level`, `Project`, and `Canonical receipt path`
  are derived, not accepted — supplying them is a refusal.
- `sections` is an ordered list of supplemental sections rendered between the
  metadata block and `Claim or decision`. A section title colliding with a
  required section name, with an `ARTIFACT_EXTRA_SECTIONS` name, or with any
  other supplemental title in the same artifact is refused. `sections` is
  refused outright for `index` (`R-G13`).
- `claim` is a string; `evidence` and `uncertainty` are non-empty lists of
  strings.
- The literal string `"null"` is the recorded null, matching the existing
  artifacts and templates; it renders as `` `null` `` and reads as a placeholder
  to `parser.is_placeholder`. JSON `null` is accepted as a synonym in the
  optional metadata positions only and never in `claim`, `evidence`, or
  `uncertainty`.

## Record diagnostics

`record.load_record(path)` returns `(TaskRecord | None, list[Diagnostic])`,
reusing the existing `Diagnostic` dataclass so messages format identically to
the validator's. Every diagnostic names the record path, a dotted field locator,
and the reason.

| Condition | Locator example | Requirement |
| --- | --- | --- |
| Malformed JSON | `file` | `R-G15` |
| Root is not an object | `file` | `R-G15` |
| Unknown or missing top-level key | `schema_version` | `R-G15` |
| Unknown artifact name | `artifacts.plan-summary` | `R-G1` |
| Missing artifact | `artifacts.pr-desc` | `R-G1` |
| Unknown per-artifact key | `artifacts.plan.notes` | `R-G15` |
| Identity mismatch with the CLI | `task_id` | `R-G6` |
| Placeholder where the contract requires concreteness | `artifacts.plan.claim` | `R-G10` |
| Evidence below the floor | `artifacts.plan.evidence` | `R-G11` |
| `passed` review without a verdict | `artifacts.code-review.review_verdict` | `R-G9` |
| Verdict outside `REVIEW_VERDICTS` | `artifacts.plan-review.review_verdict` | `R-G9` |
| Phase or applicability outside its vocabulary | `artifacts.brief.phase_state` | `R-G8` |
| `not-required` without paired applicability | `artifacts.options.applicability` | `R-G11` |
| Required artifact with a non-null rationale | `artifacts.design.applicability_rationale` | `R-G11` |
| Personal or home path in any value | `artifacts.brief.evidence[1]` | `R-G12` |
| Unsafe project-memory path | `index_identity.Project memory path` | `R-S6` |
| Supplemental section on `index` | `artifacts.index.sections` | `R-G13` |
| Receipt-owned field label in an `index` value | `artifacts.index.claim` | `R-G13` |

Evidence-floor checking mirrors `validation.py:276-355` term for term: a
`passed` artifact needs `MINIMUM_EVIDENCE_ITEMS[level]` concrete items; a
`not-required` artifact needs at least one item plus a concrete rationale,
claim, and uncertainty statement; a `required` artifact must leave the rationale
null. Concreteness is decided by `parser.is_placeholder`, not by a second
predicate.

## Rendering

`generate.render_artifact(record, artifact) -> str` emits, in this fixed order:

1. `# <ARTIFACT_TITLES[artifact]>` and a blank line.
2. `## Artifact metadata`, a blank line, then the sixteen labels of
   `METADATA_FIELDS` in their declared order, each as
   ``- <Label>: `<value>` ``.
3. For `index` only: `## Task identity` with the eleven labels of
   `INDEX_IDENTITY_FIELDS`, then `## Artifact status` with the four-column
   header, the separator row, and one row per member of `ARTIFACTS` in order.
4. For the other five artifacts in `ARTIFACT_EXTRA_SECTIONS`: that section with
   its declared field labels in order.
5. Each supplemental section from `sections`, in record order.
6. `## Claim or decision`, `## Evidence`, `## Uncertainty`.

Exactly one blank line separates blocks; the file ends with a single newline.
No lede paragraph is emitted. The lede in the templates is identical boilerplate
in every dossier and is already stated canonically in
`docs/workflows/task-dossier.md:25-38`; dropping it removes 22 lines per dossier
and no information. This is the one deliberate divergence from the template
byte-shape, and it is invisible to the validator, which requires headings and
fields rather than prose.

Determinism (`R-G14`): all iteration is over module-level tuples, never over a
set or a dict built from user input; no timestamp, hostname, user name, or
absolute path is emitted; `json` is used only for reading. A unit test renders
the same record twice and asserts byte equality, and renders it under a
different `PYTHONHASHSEED` and asserts the same bytes.

### Derived versus recorded

| Field | Source |
| --- | --- |
| `Task ID`, `Task level`, `Artifact`, `Owner` | derived |
| index `Task identity` `Task ID`, `Task level`, `Project` | derived |
| index `Canonical receipt path` | derived as `<projects-root-name>/<project>/handoffs/<task-id>/receipt.md` |
| index artifact status rows | derived from each artifact's recorded applicability and phase state |
| everything else | recorded, with a refusal when absent |

Deriving the receipt path is safe because `validation.py:805-815` accepts
exactly one value for it; deriving it removes a class of typo without removing a
decision. The status table is derived because it is a restatement — a derived
table can never disagree with the artifacts, which is precisely the stale state
`_validate_status_table` exists to catch.

## Generator CLI and API

```bash
python3 scripts/generate_task_dossier.py TDW-010 \
    --level 0 --project example-project --record path/to/TDW-010.record.json
python3 scripts/generate_task_dossier.py TDW-010 \
    --level 0 --project example-project --record path/to/TDW-010.record.json --apply
```

`--projects-root` defaults to `projects`, matching the scaffold. The positional
task ID, `--level`, and `--project` are required and are cross-checked against
the record (`R-G6`).

Public API: `load_record`, `TaskRecord`, `ArtifactRecord`, `render_artifact`,
`plan_generation`, `apply_generation`, `main`.

`plan_generation` returns `list[ScaffoldAction]` — the existing dataclass from
`scaffold.py`, reused so both commands print the same `action: path: reason`
shape. Actions are `create`, `preserve`, and `manual` for `receipt.md`.

### Write semantics

`apply_generation` calls `plan_generation` first, then writes only the `create`
actions through `scaffold.create_exclusively`, the promoted helper. That helper
opens with `os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW`, mode `0o644`,
and returns `False` when the file already exists. Consequences:

- Creation is atomic: `O_EXCL` makes existence and creation one operation, so a
  file that appears between planning and writing is preserved rather than
  overwritten.
- No temporary-file-plus-rename is used anywhere. `os.replace` overwrites by
  design and would defeat the whole guarantee.
- `O_NOFOLLOW` refuses a symlink that appears in the planning window; `ELOOP`
  and `EMLINK` are treated as "already exists", then the post-write symlink
  check converts that into an abort, exactly as `scaffold.py:202-216` does.
- A partially written dossier is left in place on abort. Nothing is rolled back,
  because rollback would mean deleting files, and deleting is the one thing this
  design refuses to do.

### Exit codes

| Code | Condition |
| --- | --- |
| `0` | Dry run planned, or apply completed with every planned `create` written or preserved |
| `1` | Any record diagnostic, any refusal, any symlink abort, or any filesystem error |
| `2` | Record file missing or unreadable, or projects root missing |

## Summary command

```bash
python3 scripts/summarize_task_dossier.py projects --task TDW-009
python3 scripts/summarize_task_dossier.py projects --task TDW-009 --require-complete
python3 scripts/summarize_task_dossier.py projects --format json
```

Without `--task`, every dossier discovered by `discover_dossiers` is summarized
in its already-sorted order. `summary.summarize_dossier(dossier, projects_root,
require_complete=False) -> DossierSummary` is the API; `render_text` and
`render_json` are pure functions of that structure.

Report sections, in fixed order:

1. **Identity** — task ID, level, project, dossier path relative to the root.
2. **Artifact state** — one row per member of `ARTIFACTS`: applicability, phase
   state, evidence count, floor, and `below-floor` when short (`R-S2`, `R-S3`).
3. **Evidence floor** — level, floor, lowest and highest observed counts, and
   the sorted list of artifacts below the floor.
4. **Provenance** — one row per artifact: authorship, authoring session,
   effective route, effective model, effective effort. Values are read from each
   artifact's metadata block. The routing manifest is never opened (`R-S4`,
   `R-G16`).
5. **Plan and review identity** — plan ID, plan status, plan artifact version,
   index accepted plan ID and version, and each review's reviewed plan ID and
   version, each marked `matches` or `differs` (`R-S5`).
6. **Authority links** — for the canonical receipt path and the project memory
   path: declared value, expected value, `exists`, `symlink`, `inside-repository`
   (`R-S6`). Health only; no content is read from either target beyond checking
   that it is a regular file.
7. **Review independence** — for `plan-review` and `code-review`, comparing the
   plan authoring session against the review's reviewing session and authoring
   session: `independent`, `not-independent`, or `unknown` (`R-S7`).
8. **Diagnostics** — the count and the formatted list returned by
   `validate_dossier`, printed verbatim (`R-S9`).

### Stale-state behaviour

The summary reports drift and never repairs it. A status-table row disagreeing
with its artifact, a receipt or memory link that does not resolve, a review
naming a plan version other than the plan's current artifact version, and a
`passed` review whose verdict is `CHANGES REQUIRED` all appear in sections 5, 6,
and 8 and all produce a nonzero exit, because each is already a
`validate_dossier` diagnostic (`R-S12`). The summary adds no verdict of its own:
if the validator is silent, the exit code is `0` however unusual the reported
state looks.

### Exit codes

| Code | Condition |
| --- | --- |
| `0` | Every summarized dossier produced zero diagnostics, including the complete gate when requested |
| `1` | Any diagnostic, or any incompleteness under `--require-complete` |
| `2` | Projects root missing, `--task` naming no discovered dossier, or a dossier that cannot be read |

Code `2` matches `validation.py:1220-1225`, which already returns `2` for a
missing projects root, so the two commands share one exit-code vocabulary.

## Line-reduction budget

A generated artifact costs `29 + C + E + U` lines, where `C` is claim lines,
`E` evidence items, and `U` uncertainty items. The index adds 30 lines for its
identity block and status table; `request`, `plan`, `plan-review`, and
`code-review` add 5 each; `pr-desc` adds 4.

| Level | Floor total | Baseline | 30% budget | Slack at the floor |
| --- | ---: | ---: | ---: | ---: |
| 0 (`E`=1) | 406 | 639 | 447 | 41 lines |
| 1 (`E`=2) | 417 | 716 | 501 | 84 lines |

The floor is a projection, not a measurement. The plan requires the implementer
to count the produced samples with `wc -l` over the eleven artifacts and to
record the observed numbers; if a sample exceeds its budget, the fix is to
tighten the record's prose, never to drop an artifact or an evidence item.

## Migration and compatibility boundary

- **No migration.** The record format is new and has no predecessor. Existing
  dossiers are neither read nor rewritten by the generator.
- **Additive only.** `schema.py` gains four constants; `validation.py` swaps one
  literal for a reference to one of them; `scaffold.py` renames one private
  helper and its single call site. No public name is removed or changed.
- **Hand authoring stays first-class.** A dossier may be scaffolded and written
  by hand, generated, or a mixture; the validator cannot tell the difference and
  is not asked to.
- **Checkout only.** `src/brichan/resources/dogfood_v1/` and the installed
  `.brichan` schema are untouched, preserving the check at
  `tests/contract/test_task_dossier_contract.py:200-209`.
- **Routing neutral.** No new manifest key, and neither new module names the
  manifest, preserving the check at
  `tests/contract/test_task_dossier_contract.py:192-198`.
- **No new repository gate.** `make check` keeps its current target list; the
  summary is not wired into it.

## Threat model

| # | Threat | Control |
| --- | --- | --- |
| T1 | Write through a symlinked artifact path to a file outside the dossier | `O_NOFOLLOW` on every create, a pre-write symlink guard, and a post-collision symlink abort |
| T2 | Dangling symlink invisible to `exists()` classified as creatable | `is_symlink()` checked first and separately, as `scaffold.py:126-129` already does |
| T3 | Record `task_id` or `project` crafted to escape the projects root | `dossier_path` reused unchanged: pattern-validated identity plus `resolve().relative_to(root)` |
| T4 | Overwriting durable evidence in an existing dossier | `O_EXCL` creation only; no truncation, no `os.replace`, no delete; collisions reported `preserve` |
| T5 | Manufactured evidence | Claim, evidence, and uncertainty are copied from the record and never synthesized; placeholders are refused |
| T6 | Inferred `PASS` | `review_verdict` is never defaulted; a `passed` review without an explicit verdict is refused |
| T7 | Index becoming a second authority | Only `INDEX_PROJECTION_SECTIONS` are emitted, only the status table is emitted, supplemental sections are refused for `index`, and receipt-owned labels are refused in index values |
| T8 | Personal or home path leaking into a durable artifact | Every record string is matched against `PERSONAL_PATH_PATTERNS` before rendering |
| T9 | Malicious or malformed record | `json.load` only — no `eval`, no import, no code path from record content to execution; unknown keys refused; the record is never written back |
| T10 | Summary silently repairing or masking drift | The summary opens files read-only, calls `validate_dossier` for the verdict, and prints diagnostics verbatim |
| T11 | Summary duplicating receipt or project-memory authority | Link fields are checked for existence, symlink status, and containment only; no content is read from the receipt or the memory file |
| T12 | Unsafe declared link paths (`..`, absolute, backslash) | The existing `_is_safe_relative` rule is mirrored for the recorded project-memory path before it is rendered |

Residual, accepted: the record file size is unbounded, so a pathological record
can exhaust memory. This is a local developer command operating on
operator-authored input in a checkout, so no cap is imposed; it is recorded
rather than silently ignored.

## Claim or decision

The selected design is three standard-library modules and two thin wrappers,
built on the primitives that already exist: `dossier_path` for containment, the
promoted `create_exclusively` for atomic non-following writes, `ScaffoldAction`
for reporting, `parser.is_placeholder` for concreteness, `schema` constants for
vocabulary, and `validate_dossier` for the verdict. Generation derives four
metadata fields, three index identity fields, one receipt path, and one status
table — every one of them recomputable — and refuses rather than defaults for
all sixteen judgment-bearing values. The summary computes one structure and
renders it two ways, delegating validity entirely to the existing validator.

## Evidence

- `src/brichan/contracts/task_dossier/scaffold.py:151-171` is the exact write
  primitive this design promotes and reuses: `O_CREAT | O_EXCL | O_WRONLY` plus
  `O_NOFOLLOW`, `ELOOP`/`EMLINK` folded into "already exists", and a `False`
  return that the caller converts into `preserve` or abort at lines 202-216.
- `src/brichan/contracts/task_dossier/scaffold.py:71-95` supplies the
  containment control for T3 unchanged — slug and task-ID patterns first, then
  `candidate.resolve().relative_to(root)` — so the generator adds no new path
  logic and inherits an already-reviewed guarantee.
- `src/brichan/contracts/task_dossier/validation.py:71-78` holds the six-key
  literal that `ARTIFACT_EXTRA_SECTIONS` replaces value-for-value, which is what
  makes the substitution provably behaviour-preserving under the existing
  912-line validator suite at `tests/unit/test_task_dossier_validator.py`.
- `src/brichan/contracts/task_dossier/validation.py:805-815` accepts exactly one
  value for `Canonical receipt path`, which is the concrete justification for
  deriving it rather than recording it.
- `src/brichan/contracts/task_dossier/validation.py:888-944` is the status-table
  cross-check that a derived table can never fail, and
  `validation.py:464-477` is the independence rule the summary mirrors in
  section 7 without reimplementing.
- `evals/task-dossier-pilots/results.md:54-58` supplies the 639 and 716 line
  baselines the budget table is computed against; the per-artifact totals in
  that table were confirmed by summing the eleven artifacts of `TDW-006` and
  `TDW-007` directly.
- `tests/contract/test_task_dossier_contract.py:192-209` fixes the two
  boundaries this design must not cross — no routing-manifest reference in any
  package module, and no `task-dossier` string in the installed resources.

## Uncertainty

- The 406-line and 417-line floors are arithmetic over the rendering rules above
  and have not been executed. They are recorded as a budget with stated slack,
  and the plan measures the real samples rather than asserting the projection.
  If the measurement disagrees, the measurement wins.
- Dropping the template lede is a deliberate divergence in byte-shape between a
  generated artifact and a scaffolded one. It is invisible to the validator, but
  a future contract test that compares generated output against template prose
  would fail; no such test exists today, and the plan adds none.
- `parser.is_placeholder` treats the bare strings `none`, `unknown`, and
  `unavailable` as placeholders. A legitimate claim consisting only of one of
  those words would be refused. This is inherited from the validator rather than
  introduced here, and is accepted rather than worked around, because diverging
  from the validator's predicate is exactly the divergence `R-G11` forbids.
- Whether `record.py` and `generate.py` should eventually import
  `validation.py` to reuse its per-artifact checks directly is left open. Today
  those checks operate on parsed Markdown rather than on a record, so reuse
  would require refactoring the validator — a larger change than this task
  authorizes, and one that would put generation and validation in one module.
