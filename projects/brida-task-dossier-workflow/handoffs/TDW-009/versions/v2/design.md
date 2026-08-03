# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `design`
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

Version 1 is preserved byte-identically at `versions/v1/design.md`. Two
structural changes carry the critical and high findings: pathname-based writes
become a descriptor walk anchored at the projects root, and direct writes to the
final artifact name become atomic hard-link publication of a fully written,
`fsync`-ed temporary. `scaffold.py` is no longer edited in any way.

## Module layout

Three new modules, two new thin wrappers, three bounded edits.

| Path | Role | New or edited |
| --- | --- | --- |
| `src/brichan/contracts/task_dossier/record.py` | Record dataclasses, typed JSON loading, record diagnostics | new |
| `src/brichan/contracts/task_dossier/generate.py` | Rendering, descriptor walk, atomic publication, CLI `main()` | new |
| `src/brichan/contracts/task_dossier/summary.py` | Read-only summary computation, text and JSON rendering, CLI `main()` | new |
| `scripts/generate_task_dossier.py` | Thin bootstrap wrapper | new |
| `scripts/summarize_task_dossier.py` | Thin bootstrap wrapper | new |
| `src/brichan/contracts/task_dossier/schema.py` | Additive constants only | edited |
| `src/brichan/contracts/task_dossier/validation.py` | Exactly two hunks | edited |
| `src/brichan/contracts/task_dossier/__init__.py` | Exports, preserving the existing `main` binding | edited |
| `src/brichan/contracts/task_dossier/scaffold.py` | none | untouched |
| `src/brichan/contracts/task_dossier/parser.py` | none | untouched |

Import direction stays acyclic:

```text
schema.py ──▶ parser.py ──▶ validation.py ──▶ summary.py
    ├──▶ record.py ───▶ generate.py
    └──▶ scaffold.py ──▶ generate.py   (dossier_path only; no write code shared)
```

`record.py` and `generate.py` do not import `validation.py`; they mirror its
rules through `schema.py` constants and `parser.py` predicates. `summary.py`
imports `validation.py` so the validator stays the single authority.

## Exact source-API edits

`schema.py` gains four constants and four `__all__` entries:

```python
RECORD_SCHEMA_VERSION = 1
ARTIFACT_TITLES = {...}       # one H1 title per artifact, matching the templates
ARTIFACT_OWNERS = {...}       # the writer column of the standard-artifact table
ARTIFACT_EXTRA_SECTIONS = {   # value-identical to validation.EXTRA_SECTION_FIELDS
    "index": ((INDEX_IDENTITY_SECTION, INDEX_IDENTITY_FIELDS),),
    "request": ((REQUEST_PROVENANCE_SECTION, REQUEST_PROVENANCE_FIELDS),),
    "plan": ((PLAN_STATUS_SECTION, PLAN_STATUS_FIELDS),),
    "plan-review": ((REVIEW_TARGET_SECTION, REVIEW_TARGET_FIELDS),),
    "code-review": ((REVIEW_TARGET_SECTION, REVIEW_TARGET_FIELDS),),
    "pr-desc": ((REMOTE_ACTION_SECTION, REMOTE_ACTION_FIELDS),),
}
```

`validation.py` receives exactly two hunks and no others:

1. `ARTIFACT_EXTRA_SECTIONS,` inserted into the existing `from .schema import (...)`
   block immediately after `ARTIFACTS,` on line 30. ASCII ordering puts
   `ARTIFACTS` before `ARTIFACT_EXTRA_SECTIONS`, so the block stays sorted.
2. The literal at lines 71-78 replaced by
   `EXTRA_SECTION_FIELDS = ARTIFACT_EXTRA_SECTIONS`.

Without hunk 1 the replacement cannot execute; version 1 specified only hunk 2.

`__init__.py` exports, with the existing `main` binding preserved:

```python
from .record import ArtifactRecord, TaskRecord, load_record
from .generate import (
    apply_generation, main as generate_main, plan_generation, render_artifact,
)
from .summary import (
    DossierSummary, main as summary_main,
    render_summary_json, render_summary_text, summarize_dossier,
)
```

`main` continues to name `validation.main`. The two CLI entry points are
reachable only as `generate_main` and `summary_main`, so nothing rebinds `main`.
A unit test asserts `task_dossier.main is validation.main` and that the three
callables are distinct objects.

## Record schema, version 1

One UTF-8 JSON object, parsed under an exact recursive type schema.

```json
{
  "schema_version": 1,
  "task_id": "SYNTH-010",
  "level": "0",
  "project": "synthetic-level0",
  "origin": "synthetic-fixture:TDW-009-P2-v2",
  "index_identity": {
    "Project memory path": "projects/synthetic-level0/current-state.md",
    "Accepted plan ID": "SYNTH-010-P1",
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
      "authoring_session": "synthetic-fixture-planner-0001",
      "effective_route": "plan",
      "effective_model": "synthetic-fixture-model",
      "effective_effort": "medium",
      "reviewing_session": "null",
      "review_verdict": "null",
      "fields": {},
      "sections": [{"title": "Steps", "body": ["1. First step."]}],
      "claim": "One paragraph asserting what this artifact decides.",
      "evidence": ["`path/to/file.py:10-20` shows ..."],
      "uncertainty": ["No unresolved uncertainty remains."]
    }
  }
}
```

### Parsing rules

- `json.load(handle, object_pairs_hook=_reject_duplicate_keys)`. The hook raises
  on the first repeated key at any depth. Plain `json.load` keeps the last
  duplicate silently, which would let one record carry two `review_verdict`
  values and publish whichever the parser happened to keep.
- Types are checked exactly, never with `isinstance`: `type(value) is str`,
  `type(value) is int`, `type(value) is dict`, `type(value) is list`. This is the
  only way to reject a JSON boolean in an integer position, because
  `isinstance(True, int)` is true while `type(True) is int` is false.
- `schema_version` must be `RECORD_SCHEMA_VERSION` exactly.
- `task_id` matches `TASK_ID_PATTERN`, `project` matches `PROJECT_SLUG_PATTERN`,
  `level` is in `TASK_LEVELS`, and all three equal the command-line identity.
- `artifacts` carries exactly the eleven keys of `ARTIFACTS`; missing and
  unknown keys are both refusals.
- `fields` is required and may be non-empty only for the five non-index members
  of `ARTIFACT_EXTRA_SECTIONS`, where it must carry exactly that artifact's
  labels. For `index`, extra-section values come from `index_identity`, and
  `Task ID`, `Task level`, `Project`, and `Canonical receipt path` are derived —
  supplying any of them is a refusal.
- `sections` is refused outright for `index`; elsewhere titles must be unique
  within the artifact and must not collide with a required or extra-section name.
- `"null"` is the recorded null and renders as `` `null` ``; JSON `null` is
  accepted as a synonym only in optional metadata positions, never in `claim`,
  `evidence`, or `uncertainty`.

### Structural injection rules

Refusal, not escaping. Two position classes:

| Position class | Members | Refused content |
| --- | --- | --- |
| Single-line scalar | metadata values, `fields` values, `index_identity` values, `sections[].title`, `evidence[]`, `uncertainty[]` | any newline, backtick, pipe, control character, leading `- `, leading `#`, leading `\|` |
| Multi-line block | `claim`, `sections[].body[]` | any line matching a level-one or level-two heading, a table row, a list item, a `- Label:` field, or a fence; any control character other than a line feed |

The rule set is closed: no accepted value can create a section, a field, a table,
or an extra evidence bullet, so `parse_sections`, `parse_fields`, `parse_table`,
and `concrete_list_items` see exactly the structure the renderer intended. Each
class carries one named diagnostic and one test.

### Record diagnostics

`record.load_record(path, *, task_id, level, project)` returns
`(TaskRecord | None, list[Diagnostic])`, reusing the existing `Diagnostic`
dataclass so messages format identically to the validator's.

| Condition | Locator example |
| --- | --- |
| Malformed JSON, non-object root, or non-UTF-8 | `file` |
| Duplicate object key at any depth | `artifacts.plan.review_verdict` |
| Wrong exact type, including boolean in an integer position | `artifacts.plan.version` |
| Unknown or missing top-level key | `schema_version` |
| Unknown, missing, or misspelled artifact | `artifacts.pr-desc` |
| Unknown per-artifact key | `artifacts.plan.notes` |
| Identity mismatch with the command line | `task_id` |
| Placeholder where the contract requires concreteness | `artifacts.plan.claim` |
| Evidence below the applicable rule | `artifacts.plan.evidence` |
| `passed` review without a verdict, or a verdict outside `REVIEW_VERDICTS` | `artifacts.code-review.review_verdict` |
| Phase or applicability outside its vocabulary, or unpaired `not-required` | `artifacts.options.applicability` |
| Required artifact with a non-null rationale | `artifacts.design.applicability_rationale` |
| Personal or home path in any value | `artifacts.brief.evidence[1]` |
| Unsafe project-memory path | `index_identity.Project memory path` |
| Supplemental section or derived field supplied for `index` | `artifacts.index.sections` |
| Single-line scalar carrying structural content | `artifacts.brief.evidence[0]` |
| Multi-line block carrying a heading, table, list, field, or fence line | `artifacts.design.claim` |

The evidence rule mirrors `validation.py:276-355` term for term: the level floor
applies to `passed`; the one-item rule plus concrete rationale, claim, and
uncertainty applies to `not-required`; a `required` artifact leaves its rationale
null. Concreteness is decided by `parser.is_placeholder`, not by a second
predicate.

## Rendering

`generate.render_artifact(record, artifact) -> str` emits, in fixed order: the
H1 title from `ARTIFACT_TITLES`; `## Artifact metadata` with the sixteen labels
of `METADATA_FIELDS` in declared order; for `index` only, `## Task identity` with
the eleven labels of `INDEX_IDENTITY_FIELDS` and `## Artifact status` with the
four-column header, separator, and one row per member of `ARTIFACTS`; for the
five other members of `ARTIFACT_EXTRA_SECTIONS`, that section with its labels in
order; each supplemental section in record order; then `## Claim or decision`,
`## Evidence`, `## Uncertainty`. Exactly one blank line separates blocks and the
file ends with a single newline. No lede paragraph is emitted; the template lede
is identical boilerplate already stated canonically at
`docs/workflows/task-dossier.md:25-38`.

Derived versus recorded is unchanged from version 1: `Task ID`, `Task level`,
`Artifact`, `Owner`, the index identity triple, the canonical receipt path, and
the status table are derived; every judgment-bearing value is recorded, with a
refusal when absent.

Determinism: iteration is only over module-level tuples; no timestamp, hostname,
process ID, or absolute path reaches the output. The temporary file name is the
one place a process ID appears, and it never becomes artifact content. A test
renders the same record twice and under a different `PYTHONHASHSEED` and asserts
byte equality.

## Descriptor walk

Closes `C1`. No pathname below the projects root is ever resolved twice.

```text
1. dossier_path(projects_root, project, task_id)      # identity + containment check only
2. rfd  = os.open(projects_root, O_RDONLY|O_DIRECTORY|O_NOFOLLOW)
   verify os.fstat(rfd) == os.stat(projects_root, follow_symlinks=False)
3. for component in (project, "handoffs", task_id):   # single components by construction
       try:    cfd = os.open(component, O_RDONLY|O_DIRECTORY|O_NOFOLLOW, dir_fd=parent)
       except FileNotFoundError:
               if not apply: record "would create"; break
               os.mkdir(component, 0o755, dir_fd=parent)     # EEXIST -> one retry of the open
               cfd = os.open(component, O_RDONLY|O_DIRECTORY|O_NOFOLLOW, dir_fd=parent)
       except OSError as e:
               if e.errno in {ELOOP, ENOTDIR}: abort "component is a symlink or not a directory"
       close(parent); parent = cfd
4. every artifact operation uses dir_fd=<dossier fd>
```

Why this closes the finding: a descriptor names an inode, not a path. An
ancestor swapped **after** its descriptor exists cannot redirect anything,
because nothing re-resolves the name. An ancestor swapped **before** the open is
refused by `O_NOFOLLOW`. There is no window between the two, which is exactly
what a preflight-then-open design cannot achieve.

Both `ELOOP` and `ENOTDIR` are refusals: darwin reports `ENOTDIR` when
`O_DIRECTORY | O_NOFOLLOW` meets a symlink, while Linux reports `ELOOP`. Treating
only one as a refusal would silently pass on one platform.

Components are `project`, the literal `handoffs`, and `task_id`. The first and
third are already pattern-validated, so no separator, `.`, or `..` can appear;
the generator re-checks anyway and refuses.

`dossier_path` is still called, for identity validation and for the declared
containment check, but its return value is never used as a write path.

## Atomic publication

Closes `H1`. All eleven bodies are rendered and validated before any filesystem
mutation.

```text
for artifact in ARTIFACTS:                 # fixed order
    tmp = f".tdgen.{task_id}.{artifact}.{pid}.{n}.tmp"
    fd  = os.open(tmp, O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW, 0o644, dir_fd=dfd)
    write_all(fd, body)                    # loop until every byte is written
    os.fsync(fd)
    assert (os.fstat(fd).st_dev, .st_ino) == stat(tmp, dir_fd=dfd, follow_symlinks=False)
    os.close(fd)
    os.link(tmp, f"{artifact}.md", src_dir_fd=dfd, dst_dir_fd=dfd, follow_symlinks=False)
    cleanup(tmp)                           # identity re-verified, then unlink
os.fsync(dfd)
```

| Property | Mechanism |
| --- | --- |
| Never overwrite | `os.link` fails `EEXIST` on an existing final name; the existing bytes are untouched and the artifact is reported `preserve` |
| Never publish a partial body | publication happens only after every byte is written and `fsync` succeeded; a fault before the link leaves nothing at the final name |
| Never follow a link | `O_NOFOLLOW` on the temporary, `follow_symlinks=False` on the link, `dir_fd` on both |
| Never delete a foreign file | a temporary is unlinked only after its device and inode re-match the descriptor that created it; on mismatch it is left and diagnosed |
| Durable | `fsync` on each artifact and on the dossier descriptor |

`os.rename` and `os.replace` are forbidden. Rename overwrites its destination by
design, and `os.replace` does not accept `dir_fd` at all, so it cannot be used
descriptor-relative.

Temporary-name collision is handled by `O_EXCL` plus a bounded counter `n` from
0 to 99; exhausting it is a refusal, not a fallback.

### Partial-progress semantics

A fault at artifact *k* leaves artifacts 1..*k*-1 published and complete, because
publication is atomic per artifact. Such a run:

- unlinks its own identity-verified temporary;
- emits a partial-adoption diagnostic naming published and unpublished artifacts;
- exits `1`.

Nothing is deleted to "clean up", because deleting is the one operation this
design refuses. A retry republishes only the missing artifacts, reports the
published ones as `preserve`, and therefore has deterministic recovery
semantics. A truncated artifact can never be among the preserved set.

## Generator CLI, API, and exit codes

```bash
python3 scripts/generate_task_dossier.py SYNTH-010 --level 0 \
    --project synthetic-level0 --record <record>.json --projects-root <root>
python3 scripts/generate_task_dossier.py ... --apply
```

Public API: `TaskRecord`, `ArtifactRecord`, `load_record`, `render_artifact`,
`plan_generation`, `apply_generation`, `main`. Actions are reported with the
existing `ScaffoldAction` dataclass so both commands print one
`action: path: reason` shape.

| Code | Condition |
| --- | --- |
| `0` | Dry run planned, or apply published every planned artifact |
| `1` | Any record diagnostic, refusal, symlink abort, filesystem fault, or partial-adoption outcome |
| `2` | Record file missing or unreadable, or projects root missing |

## Summary command

```bash
python3 scripts/summarize_task_dossier.py <projects-root> [--task TDW-009] [--format json]
```

### Verdict and exit semantics

Closes `H3`. The root verdict comes from
`validation.validate_projects(root, require_complete=True)`, which is the only
call that raises partial-adoption and duplicate-task-ID diagnostics. The
complete gate is the default and there is no flag to relax it, so a valid but
`pending` dossier exits nonzero. `validate_dossier` is used only to attribute
per-dossier detail and never produces a contradicting exit.

| Code | Condition |
| --- | --- |
| `0` | `validate_projects(..., require_complete=True)` produced no diagnostic for the selected scope |
| `1` | Any diagnostic, including incompleteness, partial adoption, or a `CHANGES REQUIRED` verdict on a `passed` review |
| `2` | Projects root missing; `--task` matching no dossier; `--task` matching more than one dossier; or a dossier that cannot be read |

Duplicate task IDs make `--task` ambiguous, so it is refused with exit `2`
rather than resolved to the first match.

### Report sections

One `DossierSummary` structure, rendered by `render_summary_text` and
`render_summary_json` with identical facts and identical exit code.

1. **Identity** — task ID, level, project, dossier path relative to the root.
2. **Artifact state** — one row per member of `ARTIFACTS`: applicability, phase
   state, evidence count, the rule that applies, and `below-floor` only when the
   applicable rule is violated.
3. **Evidence depth** — the applicable rule per phase state: the level floor
   from `MINIMUM_EVIDENCE_ITEMS` for `passed`, the one-item rule for
   `not-required`, and `not-applicable` for `pending`, `active`, and `blocked`.
   A Level 2 `not-required` artifact holding one item is compliant, not
   below-floor. This is the distinction version 1 collapsed.
4. **Provenance** — per artifact: authorship, authoring session, effective route,
   effective model, effective effort, read from the artifacts. The routing
   manifest is never opened.
5. **Plan and review identity** — plan ID, plan status, plan artifact version,
   index accepted plan ID and version, and each review's reviewed plan ID and
   version, each marked `matches` or `differs`.
6. **Authority links** — for the canonical receipt and the project memory path:
   declared value, expected value, existence, not-a-symlink, no symlinked
   ancestor between repository root and target, and containment. Health only; no
   content is read from either target.
7. **Review independence** — two separately reported arms per review: plan
   authoring session versus the review's `Reviewing session`, and versus its
   `Authoring session`. Each is `independent`, `not-independent`, or `unknown`;
   a placeholder in either identity yields `unknown` and never `independent`.
8. **Independence caveat** — fixed wording stating that identifier inequality is
   a deterministic consistency signal, not proof that two independent sessions
   existed.
9. **Unreadable artifacts** — any artifact that cannot be read or parsed, with
   path and reason, never silently omitted.
10. **Diagnostics** — the formatted list from `validate_projects`, printed
    verbatim, plus per-dossier detail from `validate_dossier`.

### Stale-state behaviour

Drift is reported and never repaired: a status-table row disagreeing with its
artifact, a dangling or ancestor-symlinked link target, a review naming a plan
version other than the plan's current artifact version, a `passed` review with
`CHANGES REQUIRED`, and a handoff carrying dossier artifacts without an
`index.md`. Each already produces a diagnostic, so each forces exit `1`.

## Evaluation design

### Synthetic, non-authoritative fixtures

Per the packet amendment, the samples are fixtures, not evidence. Every session
identity in a record matches the fixed prefix `synthetic-fixture-`, every sample
artifact states in its own claim that it is non-authoritative test data, and
`evals/task-dossier-pilots/concise/results.md` carries the fixed declaration
that the samples prove contract validity only. A contract test asserts the
prefix in both records and the declaration in `results.md`.

What the samples prove: the generator can produce eleven artifacts that pass the
complete gate. What they do not prove: that any review happened, that any
verdict is real, or that the content is review-worthy. `results.md` states both
lists explicitly.

### Isolated root and fixtures

Samples are generated into `evals/task-dossier-pilots/concise/projects/`, which
`make dossiers` never scans because `discover_dossiers` globs only the root it is
given. Each sample needs three fixture classes its own validation requires:

- eleven generated artifacts;
- a hand-written schema-v2 `receipt.md` with the eleven required sections, whose
  validity is proved by running the receipt validator against the isolated root
  — `discover_receipts` globs `*/handoffs/*/receipt.md`, so both fixtures are
  covered;
- a `current-state.md` directly inside the sample project, because
  `validation.py:827-885` resolves the memory link against `projects_root.parent`
  and requires a `CANONICAL_MEMORY_FILES` name to exist there. Version 1 omitted
  this file entirely.

### Metrics

Closes `M1`. The AC3 metric is unchanged; three authoring-burden metrics are
added.

| Metric | Measures | Command |
| --- | --- | --- |
| Total lines across the eleven artifacts | artifact compactness, the AC3 metric | explicit eleven-path `wc -l` |
| Record line count and byte count | authoring burden, upper bound | `wc -lc` on the record |
| Authored non-blank value count | authoring burden, closest proxy | count of non-null scalar values plus list items in the record |
| Record plus output lines | total durable text | sum of the first two |

`results.md` states which metric measures compactness and which approximates
authoring burden, and claims no timing, token, or cost saving.

### Line-reduction budget

A generated artifact costs `29 + C + E + U` lines. The index adds 30; `request`,
`plan`, `plan-review`, and `code-review` add 5 each; `pr-desc` adds 4.

| Level | Floor total | Baseline | 30% budget | Slack at the floor |
| --- | ---: | ---: | ---: | ---: |
| 0 (`E`=1) | 406 | 639 | 447 | 41 lines |
| 1 (`E`=2) | 417 | 716 | 501 | 84 lines |

This is a projection. The plan measures the produced samples; if a sample
exceeds its budget the fix is to tighten record prose, never to drop an artifact
or an evidence item.

## Migration and compatibility boundary

- **No migration.** The record format is new and has no predecessor. Existing
  dossiers are neither read nor rewritten by the generator.
- **Additive only.** `schema.py` gains four constants; `validation.py` takes
  exactly two hunks; `__init__.py` adds exports without rebinding `main`.
  `scaffold.py` and `parser.py` are untouched.
- **Preservation is proved against a baseline, not `HEAD`.** The working tree
  carries pre-existing user changes, so a coordinator-owned pre-task
  path-and-digest manifest is the reference for every "unchanged" claim.
- **Hand authoring stays first-class.** A dossier may be scaffolded, generated,
  or mixed; the validator cannot tell and is not asked to.
- **Checkout only, routing neutral, no new gate.** Installed resources and the
  routing manifest are untouched, neither new module names the manifest, and
  `make check` keeps its current target list.

## Threat model

| # | Threat | Control |
| --- | --- | --- |
| T1 | Ancestor directory swapped for a symlink after the safety check | Descriptor walk: every operation is `dir_fd`-relative, so a post-open swap cannot redirect a write and a pre-open swap is refused |
| T2 | Symlink or non-directory at any path component | `O_DIRECTORY \| O_NOFOLLOW`, with both `ELOOP` and `ENOTDIR` treated as refusals |
| T3 | Record identity crafted to escape the projects root | Pattern-validated identity, single-component names only, `dossier_path` containment check, and no pathname write |
| T4 | Overwriting durable evidence | Publication by `os.link`, which fails `EEXIST`; `os.rename` and `os.replace` forbidden; nothing is ever truncated or deleted |
| T5 | Truncated artifact published or later preserved | Full write plus `fsync` plus inode verification before the link; a fault leaves nothing at the final name |
| T6 | Temporary cleanup deleting a raced-in file | Device and inode re-verified against the creating descriptor before `unlink`; mismatch leaves the file and diagnoses |
| T7 | Manufactured evidence or inferred `PASS` | Claim, evidence, uncertainty, and every verdict are copied from the record; placeholders refused; a `passed` review without an explicit verdict refused |
| T8 | Index becoming a second authority | Only `INDEX_PROJECTION_SECTIONS` emitted, only the status table, supplemental sections refused for `index`, receipt-owned labels refused in index values |
| T9 | Duplicate JSON keys silently collapsing a verdict | `object_pairs_hook` refuses the first repeat at any depth |
| T10 | Boolean smuggled into an integer position | Exact `type(value) is int` checks throughout |
| T11 | Markdown structure injection creating sections, fields, tables, or evidence bullets | Closed refusal rule set over single-line and multi-line positions |
| T12 | Personal or home path leaking into a durable artifact | Every record string matched against `PERSONAL_PATH_PATTERNS` |
| T13 | Malicious record content reaching execution | `json.load` only; no `eval`, no import, no code path from record content to execution; the record is never written back |
| T14 | Summary masking project-level drift | Root verdict from `validate_projects`; complete gate is the only exit semantics; diagnostics printed verbatim |
| T15 | Summary duplicating receipt or memory authority | Link fields checked for existence, symlink status, ancestor links, and containment only; no content read |
| T16 | Synthetic fixture mistaken for real review evidence | Fixed synthetic session prefix, per-artifact non-authoritative claim, `results.md` declaration, and a contract test over all three |

Residual, accepted and recorded: the projects root itself is opened by pathname,
so a symlinked ancestor above the operator-supplied root is trusted, exactly as
the existing scaffold and validator assume. Record size is unbounded. A crash
between temporary creation and publication leaves a recognisable orphan
temporary that nothing in this task sweeps.

## Claim or decision

The design is three standard-library modules and two thin wrappers built on a
descriptor walk and hard-link publication, with `scaffold.py` and `parser.py`
untouched. Every control above was verified mechanically on this platform before
being specified: `dir_fd` support for the five syscalls used, `EEXIST` on a link
to an existing name with the original bytes intact, `ENOTDIR` rather than
`ELOOP` when `O_DIRECTORY | O_NOFOLLOW` meets a symlinked directory,
duplicate-key rejection through `object_pairs_hook`, and `type(True) is int`
being false. The summary delegates its verdict to `validate_projects` under a
non-negotiable complete gate, and the evaluation is declared synthetic so no
fixture verdict can be read as review evidence.

## Evidence

- Direct execution on this platform established the write-path controls before
  they were specified: `os.open`, `os.mkdir`, `os.stat`, `os.link`, and
  `os.unlink` report membership in `os.supports_dir_fd` while `os.replace` does
  not; `os.link` onto an existing name raised `EEXIST` and left the original
  content unchanged; `os.open` with `O_DIRECTORY | O_NOFOLLOW` on a symlinked
  directory failed with `ENOTDIR` on darwin; and `os.fstat` of the writing
  descriptor matched `os.stat(..., dir_fd=..., follow_symlinks=False)` of the
  temporary name, which is the identity check T6 relies on.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan-review.md:47-72`
  fixes the exact defect the descriptor walk removes — containment resolved once
  at `scaffold.py:87-95`, a final-component-only preflight at
  `scaffold.py:117-118`, and pathname opens at `scaffold.py:188-202`.
- `src/brichan/contracts/task_dossier/validation.py:1160-1195` raises the
  partial-adoption and duplicate-task-ID diagnostics only inside
  `validate_projects`, which is why the summary's root verdict comes from that
  function rather than from `validate_dossier`.
- `src/brichan/contracts/task_dossier/validation.py:276-309,339-347` is the
  source of the corrected evidence-depth rule: `not-required` requires at least
  one item regardless of level, while only `passed` is held to
  `MINIMUM_EVIDENCE_ITEMS[level]`.
- `src/brichan/contracts/task_dossier/validation.py:827-885` resolves the memory
  link against `projects_root.parent` and requires an existing
  `CANONICAL_MEMORY_FILES` name directly inside the project directory, which is
  the concrete reason each sample carries a synthetic `current-state.md`.
- `src/brichan/contracts/receipts/validation.py:15-70,1123-1125` fixes the eleven
  required receipt sections and shows `discover_receipts` globbing
  `*/handoffs/*/receipt.md`, so running the receipt validator against the
  isolated root validates both fixture receipts.
- `src/brichan/contracts/task_dossier/validation.py:28-34` and
  `src/brichan/contracts/task_dossier/__init__.py:11-16` fix the two exact
  source-API edits: `ARTIFACTS` sits on line 30 of the schema import block, and
  `main` is already bound to `validation.main`.

## Uncertainty

- The descriptor walk guarantees a post-open swap cannot redirect a write; it
  does not guarantee the write succeeds. A racer may cause a later artifact to
  fail, which becomes a nonzero exit with a partial-adoption diagnostic rather
  than silence. That is the intended outcome.
- Hard-link publication requires the temporary and the final name to share a
  filesystem. They always do here, because both live in the same directory, but
  the constraint is inherent to the mechanism and is recorded rather than
  assumed away.
- Refusing structural characters instead of escaping them makes some legitimate
  prose unwritable through a record — a claim containing a pipe, or evidence
  quoting a fenced block. Those artifacts must be hand-authored. Escaping was
  rejected because it would need its own round-trip proof against `parser.py`.
- The line budget remains arithmetic over the rendering rules and has not been
  executed. The plan measures the real samples; if the measurement disagrees, the
  measurement wins.
- No unresolved uncertainty remains about the three coordinator-fixed axes, which
  are treated as binding inputs rather than open design questions.
