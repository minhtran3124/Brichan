# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `design`
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

## Threat-model boundary

Read this before any other section. Nothing below may be read as a stronger
claim than this.

**Out of scope.** A non-cooperating process running under the same OS identity
that mutates directory entries inside the dossier while the generator holds the
dossier lock. Such a process can already unlink, replace, or truncate any file
this tooling owns by direct action. This generator is a repository developer
tool, not a privilege boundary against processes that already have its
privileges.

**Why the boundary sits here, as a tested fact and not a convenience.** No
Python 3.10 standard-library primitive available on both darwin and Linux binds
a hard link's source identity to an open file descriptor. `os.AT_EMPTY_PATH` and
`os.O_TMPFILE` are not exposed by this CPython build, and `/proc/self/fd` does
not exist on darwin. `os.link` therefore resolves its source by directory entry,
and the window between the source's identity check and the link cannot be closed
portably.

**What follows, stated without softening.** If the excluded attacker substitutes
the temporary source name in that window, a foreign inode or a symlink can
appear at a final artifact name. The generator **detects** this immediately after
publication and fails the run with a named diagnostic. It does **not** prevent
it, and it does **not** remove the foreign entry, because deleting an entry the
run cannot prove it created is forbidden by the same contract.

**In scope, and claimed.** Pre-existing symlinks at any path component;
namespace drift the generator can observe; ordinary concurrent Brichan
invocations that cooperate with the dossier lock; every specified write, `fsync`,
close, link, cleanup, and directory-`fsync` failure; malformed, hostile, or
injected record content.

## Version 3 supersession

Versions 1 and 2 are preserved byte-identically at `versions/v1/design.md` and
`versions/v2/design.md`. Four structural changes: a dossier-scoped advisory lock,
post-publication inode verification, a final canonical re-walk, and
validator-owned ancestor-symlink invalidity. Two schema contradictions from
version 2 are resolved. Every prior-review citation names an archived path.

## Module layout

| Path | Role | New or edited |
| --- | --- | --- |
| `src/brichan/contracts/task_dossier/record.py` | Record dataclasses, typed JSON loading, record diagnostics | new |
| `src/brichan/contracts/task_dossier/generate.py` | Rendering, descriptor walk, lock, publication, re-walk, CLI `main()` | new |
| `src/brichan/contracts/task_dossier/summary.py` | Read-only summary, text and JSON rendering, CLI `main()` | new |
| `scripts/generate_task_dossier.py` | Thin bootstrap wrapper | new |
| `scripts/summarize_task_dossier.py` | Thin bootstrap wrapper | new |
| `src/brichan/contracts/task_dossier/schema.py` | Additive constants only | edited |
| `src/brichan/contracts/task_dossier/validation.py` | Exactly five hunks | edited |
| `src/brichan/contracts/task_dossier/__init__.py` | Exports, preserving the `main` binding | edited |
| `src/brichan/contracts/task_dossier/scaffold.py` | none | untouched |
| `src/brichan/contracts/task_dossier/parser.py` | none | untouched |

## Exact source-API edits

`schema.py` gains `RECORD_SCHEMA_VERSION`, `ARTIFACT_TITLES`, `ARTIFACT_OWNERS`,
and `ARTIFACT_EXTRA_SECTIONS`, plus four `__all__` entries.
`ARTIFACT_EXTRA_SECTIONS` is value-identical to the current
`validation.EXTRA_SECTION_FIELDS` literal.

`validation.py` receives exactly five hunks and no others:

| # | Location | Change |
| --- | --- | --- |
| 1 | line 30, inside `from .schema import (...)` | insert `ARTIFACT_EXTRA_SECTIONS,` after `ARTIFACTS,`; ASCII order keeps the block sorted |
| 2 | lines 71-78 | replace the literal with `EXTRA_SECTION_FIELDS = ARTIFACT_EXTRA_SECTIONS` |
| 3 | after `_is_safe_relative` at lines 772-780 | add `_symlinked_ancestor(repository_root, parts)`, which walks the repo-relative components from the repository root, `lstat`s each without following, and returns the first symlinked ancestor path or `None` |
| 4 | inside `_validate_receipt_link`, after the existing existence check | add one call; a symlinked ancestor emits a new named diagnostic |
| 5 | inside `_validate_memory_link`, after the existing candidate symlink check | add one call; a symlinked ancestor emits a new named diagnostic |

Hunks 3 through 5 are authorized by coordinator decision 2. They add exactly two
diagnostics; every existing diagnostic keeps its condition, field locator, and
message text. The helper resolves nothing and follows nothing, so it cannot
change any currently passing verdict except by finding a symlinked ancestor,
and a read-only scan found no symlink anywhere in this checkout outside `.git`
and `.venv`.

`__init__.py` exports, with `main` still naming `validation.main`:

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

## Record schema, version 1

One UTF-8 JSON object. **JSON `null` is the only null.** The literal string
`"null"` is refused wherever a null is meaningful; version 2 accepted both and
that ambiguity is removed. A null renders as `` `null` ``.

### Top level

| Key | Exact type | Nullable | Constraint |
| --- | --- | --- | --- |
| `schema_version` | `int` | no | equals `RECORD_SCHEMA_VERSION` |
| `task_id` | `str` | no | matches `TASK_ID_PATTERN`; equals the CLI value |
| `level` | `str` | no | member of `TASK_LEVELS`; equals the CLI value |
| `project` | `str` | no | matches `PROJECT_SLUG_PATTERN`; equals the CLI value |
| `origin` | `str` | no | non-placeholder; backtick-wrapped position |
| `index_identity` | `dict[str, str \| int \| None]` | no | exactly the seven recorded labels below |
| `artifacts` | `dict[str, dict]` | no | exactly the eleven keys of `ARTIFACTS` |

### `index_identity`

The four derived index identity fields — `Task ID`, `Task level`, `Project`,
`Canonical receipt path` — are refused if supplied.

| Key | Exact type | Nullable | Constraint |
| --- | --- | --- | --- |
| `Project memory path` | `str` | no | safe repo-relative; name in `CANONICAL_MEMORY_FILES` |
| `Accepted plan ID` | `str` | yes | equals `artifacts.plan.fields["Plan ID"]` when the plan is accepted |
| `Accepted plan version` | `int` | yes | equals `artifacts.plan.version` when the plan is accepted |
| `Review route strength` | `str` | no | member of `REVIEW_ROUTE_STRENGTHS` |
| `Review route override` | `str` | yes | non-null exactly when strength is `stronger` |
| `Ship authorization` | `str` | no | member of `SHIP_AUTHORIZATION_STATES` |
| `Ship authorization evidence` | `str` | yes | non-null exactly when authorization is `user-authorized` |

### Per artifact

| Key | Exact type | Nullable | Constraint |
| --- | --- | --- | --- |
| `version` | `int` | no | `>= 1`; rendered as its decimal string |
| `origin` | `str` | yes | inherits the top-level `origin` when null |
| `phase_state` | `str` | no | member of `PHASE_STATES` |
| `applicability` | `str` | no | member of `APPLICABILITY_STATES`; paired with `not-required` phase state |
| `applicability_rationale` | `str` | yes | non-null exactly when applicability is `not-required` |
| `authorship` | `str` | no | member of `AUTHORSHIP_KINDS` |
| `authoring_session` | `str` | yes | null exactly when authorship is `human` |
| `effective_route` | `str` | yes | null exactly when authorship is `human` |
| `effective_model` | `str` | yes | null exactly when authorship is `human` |
| `effective_effort` | `str` | yes | null exactly when authorship is `human` |
| `reviewing_session` | `str` | yes | non-null when `review_verdict` is non-null |
| `review_verdict` | `str` | yes | member of `REVIEW_VERDICTS`; non-null when a review artifact is `passed` |
| `fields` | `dict[str, str]` | no | exactly the artifact's `ARTIFACT_EXTRA_SECTIONS` labels; `{}` for the five artifacts without extras and for `index` |
| `sections` | `list[dict]` | no | `[]` permitted; non-empty refused for `index` |
| `sections[].title` | `str` | no | unique within the artifact; no collision with a required or extra-section name |
| `sections[].body` | `list[str]` | no | one element per rendered line |
| `claim` | `str` | no | non-placeholder |
| `evidence` | `list[str]` | no | non-empty |
| `uncertainty` | `list[str]` | no | non-empty |

Every key in both tables is required; a missing key and an unknown key are both
refusals. Nullable means JSON `null` is permitted, not that the key may be
omitted.

### Cross-record consistency

Refusals, not derivations. The generator never invents these; it refuses a record
whose parts disagree.

- `index_identity["Accepted plan version"]` equals `artifacts.plan.version`, and
  `index_identity["Accepted plan ID"]` equals `artifacts.plan.fields["Plan ID"]`,
  whenever `artifacts.plan.fields["Plan status"]` is `accepted`.
- `artifacts["plan-review"].fields["Reviewed plan version"]` and the same key on
  `code-review` equal the decimal string of `artifacts.plan.version`.
- Both reviews' `Reviewed plan ID` equal `artifacts.plan.fields["Plan ID"]`.

### Structural injection rules

Refusal, not escaping, per **rendered position class**. Each rule names the
`parser.py` primitive it protects. This replaces version 2's single rule set,
which refused backticks everywhere and so contradicted its own example.

| Class | Members | Refused | Protects |
| --- | --- | --- | --- |
| Backtick-wrapped | every metadata value, every `fields` value, every `index_identity` value, top-level `origin` | backtick, pipe, newline, control character | the code span the renderer wraps these in; a backtick would terminate it and expose `parse_fields` and `parse_table` to the remainder |
| Free-text single-line | `sections[].title`, `evidence[]`, `uncertainty[]` | newline, control character, a value starting with `#`, a value that both starts and ends with `\|` | `parse_sections` keys on `^## `; `parse_table` keys on lines that start and end with a pipe; a newline would split one `list_items` bullet into two and inflate the evidence count |
| Multi-line block | `claim`, `sections[].body[]` | any line starting with `#`, any line that both starts and ends with `\|`, any line matching `- <label>:`, any fence line, any control character other than a line feed | `parse_sections`, `parse_table`, and `parse_fields` respectively |

Backticks are **permitted** in free-text and multi-line positions, because no
`parser.py` primitive keys on a backtick, so a backtick there cannot create a
section, field, table row, or list item. This is what makes ordinary
`` `path/to/file.py:10-20` `` evidence writable.

### Worked example

Valid under both tables and every rule above.

```json
{
  "schema_version": 1,
  "task_id": "SYNTH-010",
  "level": "0",
  "project": "synthetic-level0",
  "origin": "synthetic-fixture:TDW-009-P3-v3",
  "index_identity": {
    "Project memory path": "projects/synthetic-level0/current-state.md",
    "Accepted plan ID": "SYNTH-010-P1",
    "Accepted plan version": 1,
    "Review route strength": "routine",
    "Review route override": null,
    "Ship authorization": "not-requested",
    "Ship authorization evidence": null
  },
  "artifacts": {
    "plan": {
      "version": 1,
      "origin": null,
      "phase_state": "passed",
      "applicability": "required",
      "applicability_rationale": null,
      "authorship": "model",
      "authoring_session": "synthetic-fixture-planner-0001",
      "effective_route": "plan",
      "effective_model": "synthetic-fixture-model",
      "effective_effort": "medium",
      "reviewing_session": null,
      "review_verdict": null,
      "fields": {"Plan ID": "SYNTH-010-P1", "Plan status": "accepted"},
      "sections": [{"title": "Steps", "body": ["1. Synthetic fixture step."]}],
      "claim": "Synthetic non-authoritative fixture plan for generator evaluation.",
      "evidence": ["`evals/task-dossier-pilots/concise/records/SYNTH-010.record.json` is this dossier's only source."],
      "uncertainty": ["No unresolved uncertainty remains; this is fixture data and proves no review."]
    }
  }
}
```

The remaining ten artifact entries follow the same shape. `Accepted plan version`
is the integer `1`, matching `artifacts.plan.version`; the evidence item carries
backticks, which its position class permits.

### Parsing mechanics

`json.load(handle, object_pairs_hook=_reject_duplicate_keys)`; the hook raises on
the first repeated key at any depth. Types are checked with `type(v) is ...`,
never `isinstance`, because `isinstance(True, int)` is true while
`type(True) is int` is false — that is the only way to reject a JSON boolean in
an integer position.

### Record diagnostics

`record.load_record(path, *, task_id, level, project)` returns
`(TaskRecord | None, list[Diagnostic])`, reusing the existing `Diagnostic`
dataclass. Locators are dotted paths such as `artifacts.plan.evidence[1]` or
`index_identity.Accepted plan version`. One named diagnostic exists for each of:
malformed JSON; non-object root; non-UTF-8; duplicate key; wrong exact type;
`"null"` string where JSON null is meant; unknown or missing top-level key;
unknown, missing, or misspelled artifact; unknown or missing per-artifact key;
identity mismatch with the CLI; each of the three cross-record consistency
rules; placeholder in a concrete position; evidence below the applicable rule;
missing or invalid review verdict; unpaired `not-required`; non-null rationale on
a required artifact; personal path; unsafe memory path; derived field or
supplemental section supplied for `index`; and one per refused class in each of
the three position classes.

The evidence rule mirrors `validation.py:276-355`: the level floor applies to
`passed`, the one-item rule plus concrete rationale, claim, and uncertainty
applies to `not-required`, and a `required` artifact leaves its rationale null.

## Rendering

`render_artifact` emits, in fixed order: the H1 title from `ARTIFACT_TITLES`;
`## Artifact metadata` with the sixteen `METADATA_FIELDS` labels in declared
order; for `index` only, `## Task identity` with the eleven
`INDEX_IDENTITY_FIELDS` labels and `## Artifact status` with the four-column
header, separator, and one row per member of `ARTIFACTS`; for the five other
members of `ARTIFACT_EXTRA_SECTIONS`, that section with its labels in order; each
supplemental section in record order; then `## Claim or decision`,
`## Evidence`, `## Uncertainty`. Exactly one blank line separates blocks; the
file ends with a single newline; no lede paragraph is emitted.

Derived: `Task ID`, `Task level`, `Artifact`, `Owner`, the index identity
triple, the canonical receipt path, and the status table. Everything else is
recorded, with a refusal when absent. Determinism: iteration only over
module-level tuples; no timestamp, hostname, process ID, or absolute path
reaches artifact content. The process ID appears only in a temporary file name,
which never becomes content.

## Descriptor walk and dossier lock

```text
1. dossier_path(projects_root, project, task_id)      # identity + containment check only
2. rfd = os.open(projects_root, O_RDONLY|O_DIRECTORY|O_NOFOLLOW)
   verify os.fstat(rfd) == os.stat(projects_root, follow_symlinks=False)
3. for component in (project, "handoffs", task_id):   # single components by construction
       try:    cfd = os.open(component, O_RDONLY|O_DIRECTORY|O_NOFOLLOW, dir_fd=parent)
       except FileNotFoundError:
               if not apply: record "would create"; break
               os.mkdir(component, 0o755, dir_fd=parent)   # EEXIST -> one retry of the open
               cfd = os.open(component, O_RDONLY|O_DIRECTORY|O_NOFOLLOW, dir_fd=parent)
       except OSError as e:
               if e.errno in {ELOOP, ENOTDIR}: abort "component is a symlink or not a directory"
       record (st_dev, st_ino) of cfd; close(parent); parent = cfd
4. apply only: fcntl.flock(dossier_fd, LOCK_EX | LOCK_NB)   # refused, never waited on
5. every artifact operation uses dir_fd=dossier_fd
```

A descriptor names an inode, not a path. An ancestor swapped after its descriptor
exists cannot redirect anything; an ancestor swapped before the open is refused
by `O_NOFOLLOW`. Both `ELOOP` and `ENOTDIR` are refusals, because darwin reports
`ENOTDIR` where Linux reports `ELOOP`.

The lock is taken on the dossier directory descriptor itself, so it creates no
file, adds no allowlist leaf, and is released when the descriptor closes. It is
advisory: it binds cooperating writers, which is exactly the population inside
the threat model. A conflicting holder is refused with a named diagnostic rather
than waited on, so two concurrent generations can never interleave publications.

## Publication

All eleven bodies are rendered and validated before any mutation.

```text
for artifact in ARTIFACTS:                  # fixed order
    tmp = f".tdgen.{task_id}.{artifact}.{pid}.{n}.tmp"     # n bounded, O_EXCL
    fd  = os.open(tmp, O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW, 0o644, dir_fd=dfd)
    write_all(fd, body); os.fsync(fd)
    rec = os.fstat(fd)
    verify (rec.st_dev, rec.st_ino) == lstat(tmp, dir_fd=dfd).identity
    os.close(fd)
    os.link(tmp, f"{artifact}.md", src_dir_fd=dfd, dst_dir_fd=dfd, follow_symlinks=False)
    st = os.lstat(f"{artifact}.md", dir_fd=dfd)            # POST-PUBLICATION VERIFY
    if not S_ISREG(st.st_mode) or (st.st_dev, st.st_ino) != (rec.st_dev, rec.st_ino):
        fail "publication integrity"; do NOT unlink the final entry
    cleanup(tmp)                            # identity re-verified, then unlink
os.fsync(dfd)
final_canonical_rewalk()
```

| Property | Mechanism | Bound |
| --- | --- | --- |
| Never overwrite | `os.link` fails `EEXIST`; existing bytes untouched; reported `preserve` | absolute |
| Never publish a partial body | full write plus `fsync` plus inode check before the link | absolute |
| Never follow a link | `O_NOFOLLOW` on the temporary, `follow_symlinks=False` on the link, `dir_fd` throughout | absolute |
| Never delete a foreign file | temporary unlinked only after its identity re-matches the creating descriptor; the final entry is never unlinked | absolute |
| Source-name substitution | detected by the post-publication `lstat` identity and regular-file check; run fails, entry left in place | **detection only**, and only outside the excluded-attacker exclusion |
| Durable | `fsync` per artifact and on the dossier descriptor; a directory-`fsync` failure is a nonzero exit | absolute |

`os.rename` and `os.replace` are forbidden: rename overwrites, and `os.replace`
does not accept `dir_fd`. Temporary-name exhaustion over the bounded counter is a
refusal, never a fallback to an unbounded or predictable name.

### Partial-progress semantics

A fault at artifact *k* leaves artifacts 1..*k*-1 published and complete, because
publication is atomic per artifact. Such a run unlinks its own identity-verified
temporary, emits a partial-adoption diagnostic naming published and unpublished
artifacts, and exits `1`. Nothing is deleted to clean up. A retry republishes
only the missing artifacts and reports the published ones as `preserve`.

### Final canonical re-walk

Before any success is reported, the chain
`<projects-root>/<project>/handoffs/<task-id>` is re-walked read-only and each
level's device and inode are compared against the descriptors held during
generation. Any mismatch is namespace drift: exit `1` with a deterministic
diagnostic naming the level that moved. This closes the version-2 case where a
descriptor-bound run stayed correctly contained while the canonical path it
reported no longer led to the dossier it had written. A contained-but-detached
run is never reported as successful generation.

## Generator CLI, API, and exit codes

```bash
python3 scripts/generate_task_dossier.py SYNTH-010 --level 0 \
    --project synthetic-level0 --record <record>.json --projects-root <root> [--apply]
```

Public API: `TaskRecord`, `ArtifactRecord`, `load_record`, `render_artifact`,
`plan_generation`, `apply_generation`, `main`. Actions use the existing
`ScaffoldAction` dataclass.

| Code | Condition |
| --- | --- |
| `0` | Dry run planned, or apply published every planned artifact and the final re-walk found no drift |
| `1` | Any record diagnostic, refusal, symlink abort, lock conflict, filesystem fault, publication-integrity failure, namespace drift, or partial-adoption outcome |
| `2` | Record file missing or unreadable, or projects root missing |

## Summary command

### Verdict and exit semantics

The root verdict comes from
`validation.validate_projects(root, require_complete=True)` — the only call that
raises partial-adoption and duplicate-task-ID diagnostics, and now also the only
call that raises the two ancestor-symlink diagnostics. The complete gate is the
default and there is no flag to relax it. `validate_dossier` attributes
per-dossier detail and never produces a contradicting exit.

**Exit boundary, stated exactly.** Exit `1` means the tool evaluated the
requested scope and it is invalid or incomplete. Exit `2` means the tool could
not evaluate the requested scope.

| Situation | Exit | Reason |
| --- | ---: | --- |
| Artifact file present but unreadable or undecodable, inside a discoverable dossier | `1` | `parse_artifact` already emits a `cannot read artifact` diagnostic, so the scope was evaluated and is invalid |
| Artifact file missing | `1` | the validator already emits a missing-artifact diagnostic |
| Dossier directory absent, not a directory, or unlistable | `2` | the scope cannot be evaluated |
| `index.md` absent or unreadable, so the dossier is not discoverable | `2` | `discover_dossiers` keys on `index.md`; without it there is no dossier to evaluate |
| Projects root missing | `2` | matches `validation.py:1220-1225` |
| `--task` matching no dossier | `2` | the requested scope does not exist |
| `--task` matching more than one dossier | `2` | duplicate task IDs make the request ambiguous; refused, never resolved to the first match |

### Report sections

One `DossierSummary`, rendered by `render_summary_text` and
`render_summary_json` with identical facts and identical exit code.

1. **Identity** — task ID, level, project, dossier path relative to the root.
2. **Artifact state** — one row per member of `ARTIFACTS`.
3. **Evidence depth** — the applicable rule per phase state: the level floor for
   `passed`, the one-item rule for `not-required`, `not-applicable` otherwise. A
   Level 2 `not-required` artifact holding one item is compliant, not
   below-floor.
4. **Provenance** — per artifact: authorship, authoring session, effective
   route, model, effort. The routing manifest is never opened.
5. **Plan and review identity** — plan ID, plan status, plan artifact version,
   index accepted plan ID and version, and each review's reviewed plan ID and
   version, marked `matches` or `differs`.
6. **Authority links** — declared value, expected value, existence,
   not-a-symlink, no symlinked ancestor, containment. Health only; no content is
   read from either target. Invalidity is the validator's verdict under hunks 4
   and 5, which this section reports rather than decides.
7. **Review independence** — two separately reported arms per review, each
   `independent`, `not-independent`, or `unknown`; a placeholder in either
   identity yields `unknown`.
8. **Independence caveat** — fixed wording: identifier inequality is a
   deterministic consistency signal, not proof that two independent sessions
   existed.
9. **Unreadable artifacts** — path and reason, never silently omitted.
10. **Diagnostics** — the formatted list from `validate_projects`, verbatim, plus
    per-dossier detail from `validate_dossier`.

## Evaluation design

### Synthetic, non-authoritative fixtures

Every session identity matches `synthetic-fixture-`; every sample artifact
states in its own claim that it is non-authoritative test data;
`evals/task-dossier-pilots/concise/results.md` carries the fixed declaration
that the samples prove contract validity only — never review quality, verdict
authenticity, or session independence. A contract test asserts the prefix in both
records and the declaration in `results.md`.

### Isolated root and fixtures

Samples are generated into `evals/task-dossier-pilots/concise/projects/`, which
`make dossiers` never scans because `discover_dossiers` globs only the root it is
given. Each sample carries eleven generated artifacts, a hand-written schema-v2
`receipt.md` with the eleven required receipt sections, and a `current-state.md`
directly inside the sample project, because `validation.py:827-885` resolves the
memory link against `projects_root.parent`. Both receipts are validated by
pointing the existing receipt validator at the isolated root;
`discover_receipts` globs `*/handoffs/*/receipt.md`.

### Authored-value counting algorithm

Exact and reproducible, so two implementers obtain the same integer.

```text
visit(value):
    if value is JSON null:                      return
    if type(value) is str:
        if value.strip() in {"", "null"}:       return
        count += 1;                             return
    if type(value) is int:                      count += 1; return
    if type(value) is list:  for item in value: visit(item); return
    if type(value) is dict:  for key in DECLARED_ORDER(dict): visit(value[key]); return
```

`DECLARED_ORDER` is fixed, never insertion order or sorted order:

| Mapping | Order |
| --- | --- |
| top level | `schema_version`, `task_id`, `level`, `project`, `origin`, `index_identity`, `artifacts` |
| `index_identity` | the seven recorded labels in `INDEX_IDENTITY_FIELDS` order |
| `artifacts` | `ARTIFACTS` order |
| per artifact | the per-artifact key order of the schema table above |
| `fields` | that artifact's `ARTIFACT_EXTRA_SECTIONS` label order |
| `sections[]` element | `title`, then `body` |

Dictionary keys are never counted; list elements are counted individually. The
result is reported as `authored_values`.

### Metrics

| Metric | Measures | Command |
| --- | --- | --- |
| Total lines across the eleven artifacts | artifact compactness, the AC3 metric | explicit eleven-path `wc -l` |
| Record lines and bytes | authoring burden, upper bound | `wc -lc` on the record |
| `authored_values` | authoring burden, closest proxy | the algorithm above |
| Record plus output lines | total durable text | sum of the first two |

### Line-reduction budget

A generated artifact costs `29 + C + E + U` lines; the index adds 30; `request`,
`plan`, `plan-review`, and `code-review` add 5 each; `pr-desc` adds 4.

| Level | Floor total | Baseline | 30% budget | Slack at the floor |
| --- | ---: | ---: | ---: | ---: |
| 0 (`E`=1) | 406 | 639 | 447 | 41 lines |
| 1 (`E`=2) | 417 | 716 | 501 | 84 lines |

A projection. The plan measures the produced samples; a sample over budget is
fixed by tightening record prose, never by dropping an artifact or an item.

## Migration and compatibility boundary

- **No migration.** The record format is new and has no predecessor. Existing
  dossiers are neither read nor rewritten by the generator.
- **Additive plus two new diagnostics.** `schema.py` gains four constants;
  `validation.py` takes five enumerated hunks that add exactly two diagnostics
  and change none; `__init__.py` adds exports without rebinding `main`;
  `scaffold.py` and `parser.py` are untouched.
- **Preservation is proved against the implementation-start manifest**, captured
  by the coordinator after plan version 3 is accepted, covering repository
  identity, the exact allowlist with presence and digest for every path
  including the modified tracked files, the exact untracked-leaf inventory, and
  every file under `src/brichan/resources/` including `__init__.py`.
- **Hand authoring stays first-class.** A dossier may be scaffolded, generated,
  or mixed.
- **Checkout only, routing neutral, no new gate.**

## Threat model

| # | Threat | Control | Bound |
| --- | --- | --- | --- |
| T1 | Ancestor swapped for a symlink after the safety check | descriptor walk; every operation `dir_fd`-relative | prevented |
| T2 | Symlink or non-directory at any path component | `O_DIRECTORY \| O_NOFOLLOW`; `ELOOP` and `ENOTDIR` both refusals | prevented |
| T3 | Record identity crafted to escape the projects root | pattern-validated identity, single components, `dossier_path` check, no pathname write | prevented |
| T4 | Overwriting durable evidence | `os.link` fails `EEXIST`; rename and replace forbidden; nothing truncated or deleted | prevented |
| T5 | Truncated artifact published | full write, `fsync`, inode check before the link | prevented |
| T6 | Temporary cleanup deleting a raced-in file | identity re-verified before `unlink`; final entries never unlinked | prevented |
| T7 | Two cooperating generations interleaving | exclusive `flock` on the dossier descriptor, refused not awaited | prevented |
| T8 | Contained-but-detached run reported as success | final canonical re-walk comparing device and inode per level | prevented |
| T9 | **Excluded attacker substitutes the temporary source name** | post-publication `lstat` type and inode check; run fails; foreign entry left in place | **detected, not prevented** |
| T10 | Manufactured evidence or inferred `PASS` | every judgment value copied from the record; placeholders refused | prevented |
| T11 | Index becoming a second authority | only projection sections and the status table; supplemental sections refused | prevented |
| T12 | Duplicate JSON keys collapsing a verdict | `object_pairs_hook` refuses the first repeat at any depth | prevented |
| T13 | Boolean smuggled into an integer position | exact `type(v) is int` checks | prevented |
| T14 | Markdown structure injection | closed per-position refusal set, each rule tied to a `parser.py` primitive | prevented |
| T15 | Personal or home path in a durable artifact | every record string matched against `PERSONAL_PATH_PATTERNS` | prevented |
| T16 | Record content reaching execution | `json.load` only; no `eval`, no import, record never written back | prevented |
| T17 | Summary masking project-level drift | root verdict from `validate_projects`; complete gate only | prevented |
| T18 | Ancestor-symlinked authority path tolerated | validator hunks 4 and 5 make it invalid; the summary reports that verdict | prevented |
| T19 | Synthetic fixture mistaken for real review evidence | synthetic prefix, per-artifact claim, `results.md` declaration, contract test | prevented |

Residual, accepted and recorded: T9 above; the projects root itself is opened by
pathname, so a symlinked ancestor above the operator-supplied root is trusted,
exactly as the existing scaffold and validator assume; record size is unbounded;
a crash between temporary creation and publication leaves a recognisable orphan
temporary that nothing in this task sweeps.

## Claim or decision

The design is three standard-library modules, two thin wrappers, and five
enumerated validator hunks. Every control was verified mechanically on this
platform before being specified. The one guarantee version 2 could not keep is
now stated as a boundary rather than implied: the excluded attacker is named at
the top of this artifact, the residual case is converted from silent corruption
into a named nonzero failure by post-publication verification, cooperating
writers are serialized by a lock that creates no file, and a
contained-but-detached run is caught by a final canonical re-walk. Authority-link
invalidity moves into the validator so one authority yields one verdict, and the
record schema's two self-contradictions are replaced by an exhaustive
key-to-type table whose worked example validates under it.

## Evidence

- Direct execution on this platform established every version-3 control before
  it was specified: `os.link` with `follow_symlinks=False` over a symlinked
  source published a symlink at the destination, reproducing the version-2
  critical finding; a post-publication `os.lstat(final, dir_fd=...)` compared
  against the recorded temporary inode separated that raced publication from an
  honest one; `fcntl.flock(dir_fd, LOCK_EX | LOCK_NB)` succeeded on a directory
  descriptor and refused a second holder with `EWOULDBLOCK`; and neither
  `os.AT_EMPTY_PATH` nor `os.O_TMPFILE` is exposed by this build, with no
  `/proc/self/fd` on darwin.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md:64-89,140-156`
  states the two defects this design closes structurally: the source name is
  re-resolved by `os.link` after the identity check, and a descriptor-bound run
  can succeed while its canonical path no longer leads to the dossier.
- `src/brichan/contracts/task_dossier/validation.py:772-780,782-826,827-886`
  fixes the exact insertion points for hunks 3 through 5 — the
  `_is_safe_relative` helper block and the two link validators — and shows that
  neither currently inspects an ancestor.
- `src/brichan/contracts/task_dossier/parser.py:40-47,57-74,77-87,90-95` fixes
  what each injection rule protects: sections key on `^## `, fields on
  `- Label:`, tables on lines that start and end with a pipe, list items on a
  stripped `- ` prefix — and none of them keys on a backtick, which is why
  backticks are permitted in free-text positions.
- `src/brichan/contracts/receipts/validation.py:15-70,1123-1125` fixes the
  eleven required receipt sections and shows `discover_receipts` globbing
  `*/handoffs/*/receipt.md`, so the fixture receipts are validated by the
  existing tool against the isolated root.
- `src/brichan/contracts/task_dossier/validation.py:276-309,339-347,1160-1195`
  supplies the evidence-depth rule the record mirrors and the project-level
  diagnostics that make `validate_projects` the summary's verdict source.
- A read-only scan of the working tree found no symlink outside `.git` and
  `.venv`, so hunks 4 and 5 cannot change the verdict of any existing dossier.

## Uncertainty

- T9 is a stated limitation, not a solved problem. Detection depends on the
  post-publication `lstat` observing the entry before the excluded attacker
  changes it again; against an attacker that is by definition outside the model,
  even detection is best-effort. That is said plainly rather than hedged.
- `R-G11` leaves the foreign entry in place, so operator action is needed to
  inspect and remove it. Automatic removal was rejected because it would mean
  deleting an entry the run cannot prove it created.
- The final re-walk compares device and inode. On a filesystem that recycles
  inode numbers within a single run, drift could theoretically evade it. No such
  filesystem is in use here, and the check is strictly better than version 2's
  absence of any final identity check.
- Hunks 4 and 5 are a behaviour change for any checkout with a symlinked
  ancestor above an authority path. None exists here; a downstream checkout could
  newly fail validation. That is the intended consequence of coordinator
  decision 2.
- The line budget remains arithmetic over the rendering rules and has not been
  executed. The plan measures the real samples; if the measurement disagrees, the
  measurement wins.
