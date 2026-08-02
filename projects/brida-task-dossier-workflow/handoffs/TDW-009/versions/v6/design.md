# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `design`
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

## Threat-model boundary

Read this before any other section. No statement anywhere in this dossier may be
read as a stronger claim than this one.

**Out of scope.** A non-cooperating process running under the same OS identity
that mutates directory entries while the generator holds the dossier lock, or
that mutates repository files during capture, preflight, implementation, or the
after-delta check.

**Why the boundary sits here, as a tested fact.** No Python 3.10
standard-library primitive available on both darwin and Linux binds a hard
link's source identity to an open file descriptor. `os.AT_EMPTY_PATH` and
`os.O_TMPFILE` are not exposed by this CPython build, and `/proc/self/fd` does
not exist on darwin.

**What is not claimed.** Neither prevention nor detection against the excluded
process. The post-publication check, the capture map, the start preflight, and
the after-delta check are all **point-in-time observations**. None is a
compare-and-swap.

**What is claimed.** Safety against pre-existing symlinks at any path component;
against namespace drift the generator can observe; against ordinary concurrent
Brichan invocations that cooperate with the dossier lock; against every
specified write, `fsync`, close, link, cleanup, and directory-`fsync` failure;
and refusal of malformed, hostile, or injected record content.

**Residual consequence.** A foreign inode or symlink can appear at a final
artifact name. The generator does not remove it. Manual inspection is required.

## Version 6 supersession

Versions 1 to 5 are preserved byte-identically under `versions/v1/` to
`versions/v5/`. Version 6 is bounded to the three reproduced executable defects
in `versions/v5/plan-review.md`.

| Defect | Correction |
| --- | --- |
| `H1` the executable could not consume the canonical capture — two representations that cannot round-trip | **One canonical JSON manifest.** `build` emits it, `preflight` and `delta` consume it through a single strict parser. There is no row-only shadow format and no section-stripping convention. |
| `H2` symlinks to directories were absent from the "complete" map | Every `dirnames` entry is `lstat`-ed before descent. A symlink is emitted as an `l` row and **removed from descent**; only real directories are traversed. Listing and `lstat` errors fail closed. |
| `H3` the gates accepted truncated lists and a strict subset of the 44-path delta | The allowlist sets live **inside the manifest** and are validated to exactly **8 / 36 / 44** unique sorted paths before any state check. `delta` additionally requires `(changed ∪ created) == allowlist` exactly, so a strict subset or superset fails. |

Everything version 5 passed on is carried forward unchanged: the removal of all
rollback, the 44-path allowlist, `sections[].body[]` as a one-line class,
validator-owned summary validity, the literal eleven-artifact record, the
descriptor walk, the four-phase lock ordering, and publication.
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
| 1 | line 30, inside `from .schema import (...)` | insert `ARTIFACT_EXTRA_SECTIONS,` after `ARTIFACTS,` |
| 2 | lines 71-78 | replace the literal with `EXTRA_SECTION_FIELDS = ARTIFACT_EXTRA_SECTIONS` |
| 3 | after `_is_safe_relative` at lines 772-780 | add `_symlinked_ancestor(repository_root, parts)`, walking repo-relative components from the repository root, `lstat`-ing each without following, returning the first symlinked ancestor or `None` |
| 4 | inside `_validate_receipt_link`, after the existing existence check | add one call; a symlinked ancestor emits a new named diagnostic |
| 5 | inside `_validate_memory_link`, after the existing candidate symlink check | add one call; a symlinked ancestor emits a new named diagnostic |

Exactly two diagnostics are added; every existing diagnostic keeps its
condition, field locator, and message text.

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
`"null"` is refused wherever a null is meaningful. A null renders as `` `null` ``.

### Top level

| Key | Exact type | Nullable | Constraint |
| --- | --- | --- | --- |
| `schema_version` | `int` | no | equals `RECORD_SCHEMA_VERSION` |
| `task_id` | `str` | no | matches `TASK_ID_PATTERN`; equals the CLI value |
| `level` | `str` | no | member of `TASK_LEVELS`; equals the CLI value |
| `project` | `str` | no | matches `PROJECT_SLUG_PATTERN`; equals the CLI value |
| `origin` | `str` | no | non-placeholder; backtick-wrapped position |
| `index_identity` | `dict` | no | exactly the seven recorded labels below |
| `artifacts` | `dict` | no | exactly the eleven keys of `ARTIFACTS` |

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

Exactly seventeen keys, all required. Nullable means JSON `null` is permitted,
not that the key may be omitted.

| Key | Exact type | Nullable | Constraint |
| --- | --- | --- | --- |
| `version` | `int` | no | `>= 1`; rendered as its decimal string |
| `origin` | `str` | yes | inherits the top-level `origin` when null; `request` must render `user-request` |
| `phase_state` | `str` | no | member of `PHASE_STATES` |
| `applicability` | `str` | no | member of `APPLICABILITY_STATES`; paired with a `not-required` phase state |
| `applicability_rationale` | `str` | yes | non-null exactly when applicability is `not-required` |
| `authorship` | `str` | no | member of `AUTHORSHIP_KINDS` |
| `authoring_session` | `str` | yes | null exactly when authorship is `human` |
| `effective_route` | `str` | yes | null exactly when authorship is `human` |
| `effective_model` | `str` | yes | null exactly when authorship is `human` |
| `effective_effort` | `str` | yes | null exactly when authorship is `human` |
| `reviewing_session` | `str` | yes | non-null when `review_verdict` is non-null |
| `review_verdict` | `str` | yes | member of `REVIEW_VERDICTS`; non-null when a review artifact is `passed` |
| `fields` | `dict` | no | values are `str`; exactly the artifact's `ARTIFACT_EXTRA_SECTIONS` labels; `{}` for the five artifacts without extras and for `index` |
| `sections` | `list` | no | `[]` permitted; non-empty refused for `index` |
| `sections[].title` | `str` | no | unique within the artifact; no collision with a required or extra-section name |
| `sections[].body` | `list` | no | elements are `str`; **each element is exactly one rendered line and refuses an embedded line feed** |
| `claim` | `str` | no | non-placeholder; **line feeds permitted, every line checked separately** |
| `evidence` | `list` | no | elements are `str`; non-empty |
| `uncertainty` | `list` | no | elements are `str`; non-empty |

### Cross-record consistency

Refusals, not derivations.

- `index_identity["Accepted plan version"]` equals `artifacts.plan.version`, and
  `index_identity["Accepted plan ID"]` equals `artifacts.plan.fields["Plan ID"]`,
  whenever `artifacts.plan.fields["Plan status"]` is `accepted`.
- Both reviews' `fields["Reviewed plan version"]` equal the **decimal string** of
  `artifacts.plan.version`.
- Both reviews' `fields["Reviewed plan ID"]` equal
  `artifacts.plan.fields["Plan ID"]`.
- Neither review's `reviewing_session` nor `authoring_session` may equal
  `artifacts.plan.authoring_session`.

### Structural injection rules

Refusal, not escaping, per **rendered position class**. Version 4 grouped
`sections[].body[]` with `claim` and allowed line feeds in both, which let one
body element become several rendered lines and made line counts and
`authored_values` implementation-dependent. Version 5 separates them.

| Class | Members | Refused | Protects |
| --- | --- | --- | --- |
| Backtick-wrapped | every metadata value, every `fields` value, every `index_identity` value, top-level `origin` | backtick, pipe, newline, control character | the code span the renderer wraps these in |
| Free-text single-line | `sections[].title`, `evidence[]`, `uncertainty[]` | newline, control character, a value starting with `#`, a value that both starts and ends with `\|` | `parse_sections`, `parse_table`, and the `list_items` bullet count |
| **Single rendered line** | **`sections[].body[]`** | **any line feed**, control character, a value starting with `#`, a value that both starts and ends with `\|`, a value matching `- <label>:` | one element is exactly one rendered line, so rendering, line counts, and `authored_values` are implementation-independent |
| Multi-line block | `claim` only | per line: any line starting with `#`, any line that both starts and ends with `\|`, any line matching `- <label>:`, any fence line; and any control character other than a line feed | `parse_sections`, `parse_table`, `parse_fields` |

Backticks are permitted in every class except backtick-wrapped, because no
`parser.py` primitive keys on a backtick.

### Parsing mechanics

`json.load(handle, object_pairs_hook=_reject_duplicate_keys)`; the hook raises on
the first repeated key at any depth. Types are checked with `type(v) is ...`,
never `isinstance`.

## Worked record: complete and machine-verified

This is a **complete eleven-artifact record**. It is the literal fixture the
extraction test loads: the test parses this fenced block out of this file,
validates it under the schema tables above, renders it, and runs the real
`validate_dossier` against the result.

Before this artifact was written the record below was rendered by a reference
renderer and checked with the repository's own validator: `validate_dossier`
returned **zero** diagnostics and `validate_dossier(..., require_complete=True)`
returned **zero** diagnostics, at **410 rendered lines** across the eleven
artifacts — inside the 447-line Level 0 budget. Its single `sections[].body`
element contains no line feed and so conforms to the tightened rule above.
```json
{
  "schema_version": 1,
  "task_id": "SYNTH-010",
  "level": "0",
  "project": "synthetic-level0",
  "origin": "synthetic-fixture:TDW-009-P4-v4",
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
    "index": {
      "version": 1,
      "origin": null,
      "phase_state": "passed",
      "applicability": "required",
      "applicability_rationale": null,
      "authorship": "model",
      "authoring_session": "synthetic-fixture-coordinator-0001",
      "effective_route": "coordinator",
      "effective_model": "synthetic-fixture-model",
      "effective_effort": "medium",
      "reviewing_session": null,
      "review_verdict": null,
      "fields": {},
      "sections": [],
      "claim": "Synthetic non-authoritative fixture data; it proves no real review. Fixture index artifact.",
      "evidence": ["`records/SYNTH-010.record.json` is this dossier's only source."],
      "uncertainty": ["No unresolved uncertainty remains; this is fixture data and proves no review."]
    },
    "request": {
      "version": 1,
      "origin": "user-request",
      "phase_state": "passed",
      "applicability": "required",
      "applicability_rationale": null,
      "authorship": "model",
      "authoring_session": "synthetic-fixture-coordinator-0001",
      "effective_route": "coordinator",
      "effective_model": "synthetic-fixture-model",
      "effective_effort": "medium",
      "reviewing_session": null,
      "review_verdict": null,
      "fields": {"Redaction applied": "yes", "Mutability": "immutable"},
      "sections": [],
      "claim": "Synthetic non-authoritative fixture data; it proves no real review. Fixture request artifact.",
      "evidence": ["`records/SYNTH-010.record.json` is this dossier's only source."],
      "uncertainty": ["No unresolved uncertainty remains; this is fixture data and proves no review."]
    },
    "requirements": {
      "version": 1,
      "origin": null,
      "phase_state": "passed",
      "applicability": "required",
      "applicability_rationale": null,
      "authorship": "model",
      "authoring_session": "synthetic-fixture-planner-0001",
      "effective_route": "plan",
      "effective_model": "synthetic-fixture-model",
      "effective_effort": "high",
      "reviewing_session": null,
      "review_verdict": null,
      "fields": {},
      "sections": [],
      "claim": "Synthetic non-authoritative fixture data; it proves no real review. Fixture requirements artifact.",
      "evidence": ["`records/SYNTH-010.record.json` is this dossier's only source."],
      "uncertainty": ["No unresolved uncertainty remains; this is fixture data and proves no review."]
    },
    "brief": {
      "version": 1,
      "origin": null,
      "phase_state": "passed",
      "applicability": "required",
      "applicability_rationale": null,
      "authorship": "model",
      "authoring_session": "synthetic-fixture-planner-0001",
      "effective_route": "plan",
      "effective_model": "synthetic-fixture-model",
      "effective_effort": "high",
      "reviewing_session": null,
      "review_verdict": null,
      "fields": {},
      "sections": [],
      "claim": "Synthetic non-authoritative fixture data; it proves no real review. Fixture brief artifact.",
      "evidence": ["`records/SYNTH-010.record.json` is this dossier's only source."],
      "uncertainty": ["No unresolved uncertainty remains; this is fixture data and proves no review."]
    },
    "options": {
      "version": 1,
      "origin": null,
      "phase_state": "passed",
      "applicability": "required",
      "applicability_rationale": null,
      "authorship": "model",
      "authoring_session": "synthetic-fixture-planner-0001",
      "effective_route": "plan",
      "effective_model": "synthetic-fixture-model",
      "effective_effort": "high",
      "reviewing_session": null,
      "review_verdict": null,
      "fields": {},
      "sections": [],
      "claim": "Synthetic non-authoritative fixture data; it proves no real review. Fixture options artifact.",
      "evidence": ["`records/SYNTH-010.record.json` is this dossier's only source."],
      "uncertainty": ["No unresolved uncertainty remains; this is fixture data and proves no review."]
    },
    "design": {
      "version": 1,
      "origin": null,
      "phase_state": "passed",
      "applicability": "required",
      "applicability_rationale": null,
      "authorship": "model",
      "authoring_session": "synthetic-fixture-planner-0001",
      "effective_route": "plan",
      "effective_model": "synthetic-fixture-model",
      "effective_effort": "high",
      "reviewing_session": null,
      "review_verdict": null,
      "fields": {},
      "sections": [],
      "claim": "Synthetic non-authoritative fixture data; it proves no real review. Fixture design artifact.",
      "evidence": ["`records/SYNTH-010.record.json` is this dossier's only source."],
      "uncertainty": ["No unresolved uncertainty remains; this is fixture data and proves no review."]
    },
    "client-follow-up-questions": {
      "version": 1,
      "origin": null,
      "phase_state": "not-required",
      "applicability": "not-required",
      "applicability_rationale": "No client question changes this synthetic fixture.",
      "authorship": "model",
      "authoring_session": "synthetic-fixture-coordinator-0001",
      "effective_route": "coordinator",
      "effective_model": "synthetic-fixture-model",
      "effective_effort": "medium",
      "reviewing_session": null,
      "review_verdict": null,
      "fields": {},
      "sections": [],
      "claim": "Synthetic non-authoritative fixture data; it proves no real review. No client follow-up applies.",
      "evidence": ["`records/SYNTH-010.record.json` records no open client question."],
      "uncertainty": ["No unresolved uncertainty remains; this is fixture data and proves no review."]
    },
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
      "effective_effort": "high",
      "reviewing_session": null,
      "review_verdict": null,
      "fields": {"Plan ID": "SYNTH-010-P1", "Plan status": "accepted"},
      "sections": [{"title": "Steps", "body": ["1. Synthetic fixture step; no work is authorized by it."]}],
      "claim": "Synthetic non-authoritative fixture data; it proves no real review. Fixture plan artifact.",
      "evidence": ["`records/SYNTH-010.record.json` is this dossier's only source."],
      "uncertainty": ["No unresolved uncertainty remains; this is fixture data and proves no review."]
    },
    "plan-review": {
      "version": 1,
      "origin": null,
      "phase_state": "passed",
      "applicability": "required",
      "applicability_rationale": null,
      "authorship": "model",
      "authoring_session": "synthetic-fixture-reviewer-0001",
      "effective_route": "review",
      "effective_model": "synthetic-fixture-model",
      "effective_effort": "medium",
      "reviewing_session": "synthetic-fixture-reviewer-0001",
      "review_verdict": "PASS",
      "fields": {"Reviewed plan ID": "SYNTH-010-P1", "Reviewed plan version": "1"},
      "sections": [],
      "claim": "Synthetic non-authoritative fixture data; it proves no real review. Fixture plan-review artifact.",
      "evidence": ["`records/SYNTH-010.record.json` is this dossier's only source."],
      "uncertainty": ["No unresolved uncertainty remains; this is fixture data and proves no review."]
    },
    "code-review": {
      "version": 1,
      "origin": null,
      "phase_state": "passed",
      "applicability": "required",
      "applicability_rationale": null,
      "authorship": "model",
      "authoring_session": "synthetic-fixture-reviewer-0001",
      "effective_route": "review",
      "effective_model": "synthetic-fixture-model",
      "effective_effort": "medium",
      "reviewing_session": "synthetic-fixture-reviewer-0001",
      "review_verdict": "PASS",
      "fields": {"Reviewed plan ID": "SYNTH-010-P1", "Reviewed plan version": "1"},
      "sections": [],
      "claim": "Synthetic non-authoritative fixture data; it proves no real review. Fixture code-review artifact.",
      "evidence": ["`records/SYNTH-010.record.json` is this dossier's only source."],
      "uncertainty": ["No unresolved uncertainty remains; this is fixture data and proves no review."]
    },
    "pr-desc": {
      "version": 1,
      "origin": null,
      "phase_state": "passed",
      "applicability": "required",
      "applicability_rationale": null,
      "authorship": "model",
      "authoring_session": "synthetic-fixture-coordinator-0001",
      "effective_route": "coordinator",
      "effective_model": "synthetic-fixture-model",
      "effective_effort": "medium",
      "reviewing_session": null,
      "review_verdict": null,
      "fields": {"Remote action authorized": "no"},
      "sections": [],
      "claim": "Synthetic non-authoritative fixture data; it proves no real review. Fixture pr-desc artifact.",
      "evidence": ["`records/SYNTH-010.record.json` is this dossier's only source."],
      "uncertainty": ["No unresolved uncertainty remains; this is fixture data and proves no review."]
    }
  }
}
```

## Descriptor walk, directory creation, and the dossier lock

Version 3 said the lock precedes every mutation. That is not physically possible:
a directory cannot be locked before it exists. The corrected and precise ordering
is below; the useful safety property is that the lock precedes every
**temporary-file creation and artifact publication**, not every directory
creation.

```text
Phase A  render and check              no filesystem mutation whatsoever
  A1. load and validate the record in full
  A2. render all eleven artifact bodies in memory
  A3. any failure here leaves the tree untouched

Phase B  descriptor walk               safe descriptor-relative mkdir permitted
  B1. dossier_path(...)                identity and containment check only
  B2. rfd = os.open(projects_root, O_RDONLY|O_DIRECTORY|O_NOFOLLOW)
      verify os.fstat(rfd) == os.stat(projects_root, follow_symlinks=False)
  B3. for component in (project, "handoffs", task_id):     single components
          try:    cfd = os.open(component, O_RDONLY|O_DIRECTORY|O_NOFOLLOW, dir_fd=parent)
          except FileNotFoundError:
                  if not apply: record "would create"; stop
                  os.mkdir(component, 0o755, dir_fd=parent)   # EEXIST -> retry the open once
                  cfd = os.open(component, O_RDONLY|O_DIRECTORY|O_NOFOLLOW, dir_fd=parent)
          except OSError as e:
                  if e.errno in {ELOOP, ENOTDIR}: abort
          record (st_dev, st_ino) of cfd; close(parent); parent = cfd

Phase C  lock                          immediately after opening the dossier
  C1. fcntl.flock(dossier_fd, LOCK_EX | LOCK_NB)     refused, never awaited

Phase D  mutation                      nothing here runs before Phase C succeeds
  D1. temporary creation, writing, publication, cleanup, directory fsync
  D2. final canonical re-walk
```

A descriptor names an inode, not a path. An ancestor swapped after its descriptor
exists cannot redirect anything; an ancestor swapped before the open is refused
by `O_NOFOLLOW`. Both `ELOOP` and `ENOTDIR` are refusals, because darwin reports
`ENOTDIR` where Linux reports `ELOOP`.

`os.mkdir` in B3 is safe to run before the lock exists: it is
descriptor-relative, uses a single validated component, and creates only an
empty directory. Two cooperating invocations starting from a missing dossier
therefore race only on `mkdir`; the loser observes `EEXIST`, retries the open,
and both converge on the same inode. Phase C then admits exactly one of them, and
the other is refused before it can create any temporary or artifact leaf. This is
the two-invocation first-creation case the tests must cover.

The lock is taken on the dossier directory descriptor itself, so it creates no
file, adds no allowlist leaf, and is released when the descriptor closes. It is
advisory: it binds cooperating writers, which is exactly the population inside
the threat model, and it is not protection against the excluded process.

## Publication

```text
for artifact in ARTIFACTS:                  # fixed order, Phase D only
    tmp = f".tdgen.{task_id}.{artifact}.{pid}.{n}.tmp"     # n bounded, O_EXCL
    fd  = os.open(tmp, O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW, 0o644, dir_fd=dfd)
    write_all(fd, body); os.fsync(fd)
    rec = os.fstat(fd)
    verify (rec.st_dev, rec.st_ino) == lstat(tmp, dir_fd=dfd).identity
    os.close(fd)
    os.link(tmp, f"{artifact}.md", src_dir_fd=dfd, dst_dir_fd=dfd, follow_symlinks=False)
    st = os.lstat(f"{artifact}.md", dir_fd=dfd)     # point-in-time observation
    if not S_ISREG(st.st_mode) or (st.st_dev, st.st_ino) != (rec.st_dev, rec.st_ino):
        fail "publication integrity"; do NOT unlink the final entry
    cleanup(tmp)                            # identity re-verified, then unlink
os.fsync(dfd)
final_canonical_rewalk()
```

| Property | Mechanism | Strength |
| --- | --- | --- |
| Never overwrite | `os.link` fails `EEXIST`; existing bytes untouched; reported `preserve` | guaranteed |
| Never publish a partial body | full write plus `fsync` plus inode check before the link | guaranteed |
| Never follow a link | `O_NOFOLLOW` on the temporary, `follow_symlinks=False` on the link, `dir_fd` throughout | guaranteed |
| Never delete a foreign file | temporary unlinked only after its identity re-matches the creating descriptor; final entries never unlinked | guaranteed |
| Durable | `fsync` per artifact and on the dossier descriptor; a directory-`fsync` failure is a nonzero exit | guaranteed |
| Source-name substitution by the excluded process | the post-link `lstat` returns nonzero **if it observes** a type or inode mismatch at the instant it runs | **point-in-time best-effort observation; neither prevention nor detection is guaranteed** |

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
diagnostic naming the level that moved. A contained-but-detached run is never
reported as successful generation.

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
| `1` | Any record diagnostic, refusal, symlink abort, lock conflict, filesystem fault, observed publication-integrity mismatch, namespace drift, or partial-adoption outcome |
| `2` | Record file missing or unreadable, or projects root missing |

## Summary command

### Exit semantics derived from actual discovery

Version 3 asserted that a dossier without a readable `index.md` is undiscoverable
and exits `2`. That is wrong for an *existing but unreadable* index, and it
contradicts the requirement that root-level partial adoption be nonzero. The
table below is derived from what the current code actually does.

The governing rule: the exit code is `2` when the **requested scope cannot be
evaluated at all**, and `1` when the scope was evaluated and the sole validator
produced any diagnostic. Selecting a task never suppresses a root-level
diagnostic and never overrides `validate_projects`.

| Situation | Discovery behaviour | Exit |
| --- | --- | ---: |
| Existing but unreadable `index.md` | `discover_dossiers` globs `*/handoffs/*/index.md` without reading it, so the dossier **is** discovered; `parse_artifact` emits `cannot read artifact` | `1` |
| Existing but unreadable non-index artifact | same diagnostic from `parse_artifact` | `1` |
| Missing artifact file inside a discovered dossier | validator emits the missing-artifact diagnostic | `1` |
| Handoff carrying dossier artifacts but no `index.md`, under a root scan | `discover_partial_dossiers` and `validate_projects` emit `partial adoption` | `1` |
| Historical handoff with only a receipt and no dossier metadata | receipt-only exemption; no diagnostic | contributes `0` |
| Duplicate task IDs across two dossiers | `validate_projects` emits the duplicate-ID diagnostic | `1` |
| Projects root absent or unlistable | nothing can be scanned | `2` |
| Requested dossier directory absent or unlistable | the requested scope does not exist | `2` |
| `--task` matching no discovered dossier, including an index-less handoff | unmatched selection | `2` |
| `--task` matching more than one dossier | ambiguous selection | `2` |

Composition rule: the process computes a scope code in `{0, 2}` and a verdict
code in `{0, 1}` from `validate_projects(root, require_complete=True)`, and exits
with `2` if the scope code is `2`, else the verdict code. Root-level diagnostics
are always printed, including when the selection is unmatched, so an unmatched
`--task` can never hide a partial-adoption or duplicate-ID finding.

### Report sections

One `DossierSummary`, rendered by `render_summary_text` and
`render_summary_json` with identical facts and identical exit code.

1. **Identity** — task ID, level, project, dossier path relative to the root.
2. **Artifact state** — one row per member of `ARTIFACTS`.
3. **Evidence depth** — the level floor for `passed`, the one-item rule for
   `not-required`, `not-applicable` otherwise. A Level 2 `not-required` artifact
   holding one item is compliant, not below-floor.
4. **Provenance** — per artifact: authorship, authoring session, effective
   route, model, effort. The routing manifest is never opened.
5. **Plan and review identity** — plan ID, plan status, plan artifact version,
   index accepted plan ID and version, and each review's reviewed plan ID and
   version, marked `matches` or `differs`.
6. **Authority links** — declared value, expected value, existence,
   not-a-symlink, no symlinked ancestor, containment. Health only. Invalidity is
   the validator's verdict under hunks 4 and 5, reported here, never decided here.
7. **Review independence** — two separately reported arms per review, each
   `independent`, `not-independent`, or `unknown`.
8. **Independence caveat** — fixed wording: identifier inequality is a
   deterministic consistency signal, not proof that two independent sessions
   existed.
9. **Unreadable artifacts** — path and reason, never silently omitted.
10. **Diagnostics** — the formatted list from `validate_projects`, verbatim, plus
    per-dossier detail from `validate_dossier`.



## Implementation-start capture map

Coordinator-owned, captured after plan version 6 is accepted. One canonical
**JSON** document. `build` emits exactly this shape; `preflight` and `delta`
parse it with one strict loader and accept nothing else.

### Canonical schema

```text
{
  "capture_map_version": 1,
  "exclusions": {
    "dir_prefixes": [ 7 entries ],      exactly the frozen list
    "any_component": [ "__pycache__" ],
    "names": [ ".DS_Store", ".env" ]
  },
  "snapshot_dir": "<repo-relative directory, inside an excluded prefix>",
  "allowlist_modified": [ exactly 8 unique sorted paths, each present in rows ],
  "allowlist_new":      [ exactly 36 unique sorted paths, each absent from rows ],
  "rows": [ {"path": str, "type": "f"|"l"|"o", "length": int, "sha256": str}, ... ]
}
```

The strict loader fails closed on: invalid JSON; a non-object root; a duplicate
JSON key at any depth; any top-level key set other than the exact six; a
`capture_map_version` other than `1`; an `exclusions` object that is not the ten
frozen entries; a row missing or gaining a key; a row `type` outside `f`, `l`,
`o`; a `length` that is not an exact `int` (a JSON boolean is refused); a
duplicate row path; rows not sorted by path; an `allowlist_modified` that is not
exactly 8 unique sorted paths; an `allowlist_new` that is not exactly 36; a
union that is not exactly 44 unique paths; a modified path absent from `rows`;
or a new path present in `rows`.

Putting the allowlists **inside** the manifest is what closes `H3`: there are no
external whitespace-split list files to truncate, and membership is checked
before any filesystem state is examined.

### Row rules

One row per non-directory entry outside the exclusions, sorted by path.

- `f` regular file: `length` and `sha256` of its bytes.
- `l` **symlink, whether its target is a file or a directory**: `length` and
  `sha256` of the **link target string**. The walk never follows it.
- `o` anything else: length `0`, digest all zeros.

`os.walk` classifies a symlink-to-directory in `dirnames`. Version 5 emitted
rows only from `filenames`, so those links were invisible. Version 6 `lstat`s
every `dirnames` entry before descent, emits an `l` row when it is a link, and
descends only into real directories.

### Exclusion set

Exactly ten entries, frozen in the code and checked against the manifest.

| Exclusion | Form | Why |
| --- | --- | --- |
| `.git` | directory prefix | version-control internals |
| `.venv` | directory prefix | local interpreter |
| `.pytest_cache` | directory prefix | regenerated by any test run |
| `projects/brida-task-dossier-workflow/handoffs/TDW-009` | directory prefix | coordinator-, planner-, and reviewer-owned; also holds the capture and snapshots |
| `projects/brida-task-dossier-workflow/handoffs/TDWPLAN-009` | directory prefix | planner child receipt |
| `projects/brida-task-dossier-workflow/handoffs/TDWIMP-009` | directory prefix | implementer child receipt |
| `projects/brida-task-dossier-workflow/handoffs/TDWREV-009` | directory prefix | reviewer child receipt |
| `__pycache__` | any path component | regenerated by any import |
| `.DS_Store` | file name | platform noise |
| `.env` | file name | may carry secrets |

`snapshot_dir` must sit inside an excluded prefix so the snapshot files never
become rows of the map that authenticates them.

Cost of the last two, stated rather than hidden: a change to a `.env` or
`.DS_Store` file is invisible to the map, the preflight, and the delta.

### Snapshots

The eight modified tracked paths have byte snapshots named exactly
`sha256(path.encode("utf-8")).hexdigest() + ".bin"`. `preflight` requires the
snapshot directory to contain **exactly** those eight files and nothing else,
and authenticates each one no-follow against its `rows` digest.

**Snapshots are evidence only.** No worker may restore from, delete from, or
write through a snapshot.
## Recovery policy

There is no rollback in TDW-009.

- **During implementation:** on any failure the worker **fixes forward** within
  its 44 authorized paths. It does not revert, restore, or delete outside them.
- **After a successful scoped commit:** recovery is a **separately reviewed
  commit revert**, requested from the coordinator. It is not part of this task.
- **Never:** restoring or deleting from capture snapshots, `git checkout --` on
  any path, or any procedure that writes over a path this task did not create.

Version 4 specified an identity-checked rollback. Independent review showed it
compared bytes rather than identity, could follow a symlink into a different
target, and restored snapshots that were never authenticated. Rather than
deepening a procedure nobody asked for, version 5 removes it. A portable
pathname procedure cannot offer compare-and-swap safety against a concurrent
same-identity process, and pretending otherwise is the failure mode this dossier
has been correcting since version 1.


## Exact executable capture, preflight, and delta

One script, three modes, standard library only, Python 3.10 floor, read-only. It
is reproduced verbatim below. A reviewer can extract this fenced block and run
all three modes against the literal canonical manifest; the tests in
`tests/integration/test_task_dossier_workflow.py` exercise the same logic. No
repository path is added for it.

```python
#!/usr/bin/env python3
"""TDW-009 canonical capture manifest: build, preflight, delta.

Read-only. Standard library only. Python 3.10 floor. Never follows a symlink.
One canonical JSON manifest is emitted by `build` and consumed by `preflight`
and `delta`; there is no second representation.
"""
import argparse
import hashlib
import json
import os
import stat
import sys

CAPTURE_MAP_VERSION = 1
EXCLUDED_DIR_PREFIXES = (
    ".git",
    ".venv",
    ".pytest_cache",
    "projects/brida-task-dossier-workflow/handoffs/TDW-009",
    "projects/brida-task-dossier-workflow/handoffs/TDWPLAN-009",
    "projects/brida-task-dossier-workflow/handoffs/TDWIMP-009",
    "projects/brida-task-dossier-workflow/handoffs/TDWREV-009",
)
EXCLUDED_ANY_COMPONENT = ("__pycache__",)
EXCLUDED_NAMES = (".DS_Store", ".env")
MODIFIED_COUNT = 8
NEW_COUNT = 36
ALLOWLIST_COUNT = 44
NULL_SHA = "0" * 64
TOP_LEVEL_KEYS = (
    "capture_map_version", "exclusions", "snapshot_dir",
    "allowlist_modified", "allowlist_new", "rows",
)
ROW_KEYS = ("path", "type", "length", "sha256")


class Fail(Exception):
    """Any fail-closed condition. Never recovered from."""


def excluded(rel):
    parts = rel.split("/")
    if parts[-1] in EXCLUDED_NAMES:
        return True
    if any(part in EXCLUDED_ANY_COMPONENT for part in parts):
        return True
    return any(parts[: len(p.split("/"))] == p.split("/") for p in EXCLUDED_DIR_PREFIXES)


def row_for(root, rel):
    full = os.path.join(root, rel)
    try:
        mode = os.lstat(full).st_mode
    except OSError as error:
        raise Fail(f"cannot lstat {rel}: {error}") from None
    if stat.S_ISLNK(mode):
        try:
            target = os.readlink(full).encode("utf-8")
        except OSError as error:
            raise Fail(f"cannot readlink {rel}: {error}") from None
        return {"path": rel, "type": "l", "length": len(target),
                "sha256": hashlib.sha256(target).hexdigest()}
    if not stat.S_ISREG(mode):
        return {"path": rel, "type": "o", "length": 0, "sha256": NULL_SHA}
    digest, length = hashlib.sha256(), 0
    try:
        with open(full, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
                length += len(chunk)
    except OSError as error:
        raise Fail(f"cannot read {rel}: {error}") from None
    return {"path": rel, "type": "f", "length": length, "sha256": digest.hexdigest()}


def build_rows(root):
    """Every non-directory entry outside the exclusions, symlinks included.

    A symlink whose target is a directory appears in os.walk's dirnames. It is
    recorded as an `l` row and removed from descent, so it is never traversed.
    """
    rows = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False, onerror=_walk_error):
        rel_dir = os.path.relpath(dirpath, root)
        rel_dir = "" if rel_dir == "." else rel_dir.replace(os.sep, "/")
        keep = []
        for name in sorted(dirnames):
            rel = f"{rel_dir}/{name}".lstrip("/")
            if excluded(rel):
                continue
            try:
                is_link = stat.S_ISLNK(os.lstat(os.path.join(root, rel)).st_mode)
            except OSError as error:
                raise Fail(f"cannot lstat directory entry {rel}: {error}") from None
            if is_link:
                rows.append(row_for(root, rel))
            else:
                keep.append(name)
        dirnames[:] = keep
        for name in sorted(filenames):
            rel = f"{rel_dir}/{name}".lstrip("/")
            if not excluded(rel):
                rows.append(row_for(root, rel))
    rows.sort(key=lambda r: r["path"])
    paths = [r["path"] for r in rows]
    if len(set(paths)) != len(paths):
        raise Fail("duplicate path produced by the walk")
    return rows


def _walk_error(error):
    raise Fail(f"cannot list directory: {error}")


def exclusions_object():
    return {
        "dir_prefixes": list(EXCLUDED_DIR_PREFIXES),
        "any_component": list(EXCLUDED_ANY_COMPONENT),
        "names": list(EXCLUDED_NAMES),
    }


def snapshot_name(rel):
    return hashlib.sha256(rel.encode("utf-8")).hexdigest() + ".bin"


def sha_regular_file(path):
    try:
        if os.path.islink(path) or not os.path.isfile(path):
            raise Fail(f"{path} is not a regular file")
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as error:
        raise Fail(f"cannot read {path}: {error}") from None


def read_list(path, count, label):
    with open(path, encoding="utf-8") as handle:
        items = handle.read().split()
    if len(items) != count:
        raise Fail(f"{label} must hold exactly {count} paths, found {len(items)}")
    if len(set(items)) != count:
        raise Fail(f"{label} contains duplicate paths")
    return sorted(items)


def load_manifest(path):
    """Strict canonical parse. Every deviation is fail-closed."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    def no_duplicate_keys(pairs):
        seen = set()
        for key, _ in pairs:
            if key in seen:
                raise Fail(f"duplicate JSON key {key!r} in the manifest")
            seen.add(key)
        return dict(pairs)
    try:
        manifest = json.loads(text, object_pairs_hook=no_duplicate_keys)
    except json.JSONDecodeError as error:
        raise Fail(f"manifest is not valid JSON: {error}") from None
    if type(manifest) is not dict:
        raise Fail("manifest root must be a JSON object")
    if tuple(sorted(manifest)) != tuple(sorted(TOP_LEVEL_KEYS)):
        raise Fail(f"manifest keys must be exactly {sorted(TOP_LEVEL_KEYS)}, found {sorted(manifest)}")
    if manifest["capture_map_version"] != CAPTURE_MAP_VERSION:
        raise Fail(f"capture_map_version must be {CAPTURE_MAP_VERSION}")
    if manifest["exclusions"] != exclusions_object():
        raise Fail("exclusions must match the ten frozen entries exactly")
    if type(manifest["snapshot_dir"]) is not str or not manifest["snapshot_dir"]:
        raise Fail("snapshot_dir must be a non-empty string")
    rows = manifest["rows"]
    if type(rows) is not list:
        raise Fail("rows must be a list")
    seen = set()
    for entry in rows:
        if type(entry) is not dict or tuple(sorted(entry)) != tuple(sorted(ROW_KEYS)):
            raise Fail(f"every row must hold exactly {sorted(ROW_KEYS)}")
        if type(entry["path"]) is not str or type(entry["sha256"]) is not str:
            raise Fail("row path and sha256 must be strings")
        if type(entry["length"]) is not int or type(entry["length"]) is bool:
            raise Fail("row length must be an integer")
        if entry["type"] not in ("f", "l", "o"):
            raise Fail(f"row type must be f, l, or o, found {entry['type']!r}")
        if entry["path"] in seen:
            raise Fail(f"duplicate row path {entry['path']!r}")
        seen.add(entry["path"])
    if [r["path"] for r in rows] != sorted(r["path"] for r in rows):
        raise Fail("rows must be sorted by path")
    modified, new = manifest["allowlist_modified"], manifest["allowlist_new"]
    for label, value, count in (("allowlist_modified", modified, MODIFIED_COUNT),
                                ("allowlist_new", new, NEW_COUNT)):
        if type(value) is not list or len(value) != count:
            raise Fail(f"{label} must hold exactly {count} paths, found "
                       f"{len(value) if type(value) is list else 'a non-list'}")
        if len(set(value)) != count:
            raise Fail(f"{label} contains duplicate paths")
        if value != sorted(value):
            raise Fail(f"{label} must be sorted")
    union = set(modified) | set(new)
    if len(union) != ALLOWLIST_COUNT:
        raise Fail(f"the allowlist union must hold exactly {ALLOWLIST_COUNT} unique "
                   f"paths, found {len(union)}")
    for path_value in modified:
        if path_value not in seen:
            raise Fail(f"allowlist_modified path {path_value!r} is absent from rows")
    for path_value in new:
        if path_value in seen:
            raise Fail(f"allowlist_new path {path_value!r} must be absent from rows")
    return manifest


def canonical_json(manifest):
    return json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def cmd_build(args):
    manifest = {
        "capture_map_version": CAPTURE_MAP_VERSION,
        "exclusions": exclusions_object(),
        "snapshot_dir": args.snapshot_dir,
        "allowlist_modified": read_list(args.allowlist_modified, MODIFIED_COUNT, "allowlist_modified"),
        "allowlist_new": read_list(args.allowlist_new, NEW_COUNT, "allowlist_new"),
        "rows": build_rows(args.root),
    }
    load_manifest_from_object(manifest)
    sys.stdout.write(canonical_json(manifest))
    return 0


def load_manifest_from_object(manifest):
    """Round-trip guard: build output must parse under the strict loader."""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as handle:
        handle.write(canonical_json(manifest))
        name = handle.name
    try:
        load_manifest(name)
    finally:
        os.unlink(name)


def cmd_preflight(args):
    manifest = load_manifest(args.manifest)
    failures = []
    captured = {r["path"]: r for r in manifest["rows"]}
    current = {r["path"]: r for r in build_rows(args.root)}
    for path_value in sorted(set(captured) | set(current)):
        if captured.get(path_value) != current.get(path_value):
            failures.append(f"DRIFT {path_value}: capture={captured.get(path_value)} "
                            f"current={current.get(path_value)}")
    snapshot_dir = os.path.join(args.root, manifest["snapshot_dir"])
    expected_snapshots = {snapshot_name(p) for p in manifest["allowlist_modified"]}
    try:
        present = set(os.listdir(snapshot_dir))
    except OSError as error:
        raise Fail(f"cannot list snapshot_dir {snapshot_dir}: {error}") from None
    if present != expected_snapshots:
        failures.append(f"SNAPSHOTDIR must hold exactly the {MODIFIED_COUNT} expected "
                        f"snapshots; extra={sorted(present - expected_snapshots)} "
                        f"missing={sorted(expected_snapshots - present)}")
    for path_value in manifest["allowlist_modified"]:
        snap = os.path.join(snapshot_dir, snapshot_name(path_value))
        try:
            if sha_regular_file(snap) != captured[path_value]["sha256"]:
                failures.append(f"SNAPSHOT {path_value}: digest does not match its capture row")
        except Fail as error:
            failures.append(f"SNAPSHOT {path_value}: {error}")
    for path_value in manifest["allowlist_new"]:
        if os.path.lexists(os.path.join(args.root, path_value)):
            failures.append(f"COLLISION {path_value}: planned-new path already exists")
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(f"preflight FAILED: {len(failures)} problem(s)", file=sys.stderr)
        return 1
    print(f"preflight OK: {len(current)} rows identical; {MODIFIED_COUNT} snapshots "
          f"authenticated; {NEW_COUNT} planned-new paths absent")
    return 0


def cmd_delta(args):
    manifest = load_manifest(args.manifest)
    allowlist = set(manifest["allowlist_modified"]) | set(manifest["allowlist_new"])
    captured = {r["path"]: r for r in manifest["rows"]}
    current = {r["path"]: r for r in build_rows(args.root)}
    changed = {p for p in captured if p in current and captured[p] != current[p]}
    created = set(current) - set(captured)
    removed = set(captured) - set(current)
    touched = changed | created
    unexpected = (touched | removed) - allowlist
    missing = allowlist - touched
    for label, group in (("CHANGED", changed), ("CREATED", created), ("REMOVED", removed)):
        for path_value in sorted(group):
            print(f"{label} {path_value}"
                  f"{'  <-- UNEXPECTED' if path_value in unexpected else ''}")
    for path_value in sorted(missing):
        print(f"UNTOUCHED {path_value}  <-- MISSING")
    problems = []
    if removed:
        problems.append(f"{len(removed)} path(s) removed")
    if unexpected:
        problems.append(f"{len(unexpected)} path(s) outside the allowlist")
    if missing:
        problems.append(f"{len(missing)} authorized path(s) untouched")
    if touched != allowlist:
        problems.append("touched set is not exactly the authorized allowlist")
    if problems:
        print("delta FAILED: " + "; ".join(problems), file=sys.stderr)
        return 1
    print(f"delta OK: touched set equals all {ALLOWLIST_COUNT} authorized paths; "
          "no removals; unexpected set empty")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="TDW-009 canonical capture manifest")
    sub = parser.add_subparsers(dest="mode", required=True)
    build = sub.add_parser("build")
    build.add_argument("--root", required=True)
    build.add_argument("--allowlist-modified", required=True)
    build.add_argument("--allowlist-new", required=True)
    build.add_argument("--snapshot-dir", required=True)
    build.set_defaults(func=cmd_build)
    for name, func in (("preflight", cmd_preflight), ("delta", cmd_delta)):
        node = sub.add_parser(name)
        node.add_argument("--root", required=True)
        node.add_argument("--manifest", required=True)
        node.set_defaults(func=func)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Fail as error:
        print(f"{args.mode} FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

### Invocation

```bash
# coordinator, at capture time
python3 capture.py build --root . \
    --allowlist-modified <8-path list> --allowlist-new <36-path list> \
    --snapshot-dir projects/brida-task-dossier-workflow/handoffs/TDW-009/capture/snapshot \
    > <capture-dir>/capture-manifest.json

# implementer, before any write; any nonzero exit is a stop
python3 capture.py preflight --root . --manifest <capture-dir>/capture-manifest.json

# implementer, at handoff
python3 capture.py delta --root . --manifest <capture-dir>/capture-manifest.json
```

After `build`, the two list files are no longer inputs: the allowlists live in
the manifest and both later modes read them from there.

### Guarantees and their exact limits

| Property | Mechanism | Limit |
| --- | --- | --- |
| The canonical manifest round-trips | `build` emits it and validates its own output through the same strict loader before printing | absolute |
| Malformed, duplicated, or truncated manifests are refused | one strict loader with fourteen fail-closed conditions | absolute |
| Symlink to a **file or a directory** is recorded and never followed | `lstat` on every `dirnames` and `filenames` entry; links dropped from descent | absolute |
| Retargeting or replacing a symlink is caught | the `l` row's target digest or the row `type` changes | point-in-time |
| Pre-existing tracked or untracked modification outside the allowlist is caught | every observed file has a row | point-in-time |
| Post-capture collision at a planned-new path is caught | `lexists` plus the row check | point-in-time |
| Snapshot corruption, replacement, removal, symlinking, or a stray file is caught | exact directory membership plus no-follow digest authentication | point-in-time |
| The delta equals **all 44** authorized paths | `(changed ∪ created) == allowlist`, plus no removals and an empty unexpected set | absolute for the observed state |
| A strict subset or superset of the 44 fails | `missing` and `unexpected` are both computed and both fatal | absolute for the observed state |
| Compare-and-swap against a concurrent same-identity process | **none** | explicitly not provided |
## Evaluation design

Every session identity matches `synthetic-fixture-`; every sample artifact states
in its own claim that it is non-authoritative test data;
`evals/task-dossier-pilots/concise/results.md` carries the fixed declaration that
the samples prove contract validity only. A contract test asserts the prefix in
both records and the declaration in `results.md`.

Samples are generated into `evals/task-dossier-pilots/concise/projects/`, which
`make dossiers` never scans. Each sample carries eleven generated artifacts, a
hand-written schema-v2 `receipt.md`, and a `current-state.md` directly inside the
sample project, because `validation.py:827-885` resolves the memory link against
`projects_root.parent`. Both receipts are validated by pointing the existing
receipt validator at the isolated root.

### Authored-value counting algorithm

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

`DECLARED_ORDER` is fixed, never insertion or sorted order: top level is
`schema_version`, `task_id`, `level`, `project`, `origin`, `index_identity`,
`artifacts`; `index_identity` follows `INDEX_IDENTITY_FIELDS` order restricted to
the seven recorded labels; `artifacts` follows `ARTIFACTS`; each artifact follows
the seventeen-key order of the schema table; `fields` follows that artifact's
`ARTIFACT_EXTRA_SECTIONS` label order; a `sections` element is `title` then
`body`. Dictionary keys are never counted; list elements are counted individually.

### Metrics

| Metric | Measures | Command |
| --- | --- | --- |
| Total lines across the eleven artifacts | artifact compactness, the AC3 metric | explicit eleven-path `wc -l` |
| Record lines and bytes | authoring burden, upper bound | `wc -lc` on the record |
| `authored_values` | authoring burden, closest proxy | the algorithm above |
| Record plus output lines | total durable text | sum of the first two |

### Line-reduction budget

| Level | Floor total | Baseline | 30% budget | Slack at the floor |
| --- | ---: | ---: | ---: | ---: |
| 0 (`E`=1) | 406 | 639 | 447 | 41 lines |
| 1 (`E`=2) | 417 | 716 | 501 | 84 lines |

The worked record above renders to 410 lines, measured, which is inside the
Level 0 budget and within 4 lines of the projection.



## Migration and compatibility boundary

- **No migration.** The record format is new and has no predecessor.
- **Additive plus two new diagnostics.** `schema.py` gains four constants;
  `validation.py` takes five enumerated hunks; `__init__.py` adds exports without
  rebinding `main`; `scaffold.py` and `parser.py` are untouched.
- **Protected state is whatever the capture map recorded.** No digest is
  hard-coded in any planning artifact. `config/model-routing.json` is user-owned
  and appears in `rows` like any other file.
- **No rollback exists.** Recovery is fix-forward, then a separately reviewed
  commit revert.
- **Checkout only, routing neutral, no new gate, no forty-fifth path.**

## Threat model

| # | Threat | Control | Strength |
| --- | --- | --- | --- |
| T1 | Ancestor swapped for a symlink after the safety check | descriptor walk; every operation `dir_fd`-relative | guaranteed |
| T2 | Symlink or non-directory at any path component | `O_DIRECTORY \| O_NOFOLLOW`; `ELOOP` and `ENOTDIR` both refusals | guaranteed |
| T3 | Record identity crafted to escape the projects root | pattern-validated identity, single components, no pathname write | guaranteed |
| T4 | Overwriting durable evidence | `os.link` fails `EEXIST`; rename and replace forbidden | guaranteed |
| T5 | Truncated artifact published | full write, `fsync`, inode check before the link | guaranteed |
| T6 | Temporary cleanup deleting a raced-in file | identity re-verified before `unlink` | guaranteed |
| T7 | Two cooperating generations interleaving | exclusive `flock` immediately after opening the dossier | guaranteed for cooperating writers |
| T8 | Contained-but-detached run reported as success | final canonical re-walk comparing device and inode | guaranteed |
| T9 | **Excluded process substitutes a temporary source or a final entry** | post-publication `lstat` check | **point-in-time observation only** |
| T10 | Manufactured evidence or inferred `PASS` | every judgment value copied from the record | guaranteed |
| T11 | Index becoming a second authority | only projection sections and the status table | guaranteed |
| T12 | Duplicate JSON keys collapsing a verdict or a manifest field | `object_pairs_hook` in both the record loader and the manifest loader | guaranteed |
| T13 | Boolean smuggled into an integer position | exact `type(v) is int` checks in both loaders | guaranteed |
| T14 | Markdown structure injection | closed per-position refusal set; `sections[].body[]` refuses line feeds | guaranteed |
| T15 | Personal or home path in a durable artifact | `PERSONAL_PATH_PATTERNS` match on every record string | guaranteed |
| T16 | Record content reaching execution | `json.load` only; record never written back | guaranteed |
| T17 | Summary masking project-level drift | verdict from `validate_projects`; selection never overrides it | guaranteed |
| T18 | Ancestor-symlinked authority path tolerated | validator hunks 4 and 5 | guaranteed |
| T19 | Synthetic fixture mistaken for real review evidence | synthetic prefix, per-artifact claim, `results.md` declaration, contract test | guaranteed |
| T20 | Implementation touching a path outside the 44 | complete capture map plus a non-empty `unexpected` set | **point-in-time observation** |
| T21 | Implementation touching **fewer** than the 44 | `missing = allowlist - touched` is computed and fatal | **point-in-time observation** |
| T22 | Starting from a stale baseline | preflight compares parsed rows and authenticates snapshots | **point-in-time observation** |
| T23 | A symlink-to-directory hiding a change | every `dirnames` entry is `lstat`-ed and recorded as an `l` row | **point-in-time observation** |
| T24 | A truncated or forged allowlist narrowing a gate | allowlists live inside the manifest and are validated to 8 / 36 / 44 first | guaranteed |
| T25 | Generator reading or naming the routing manifest | static source probe plus an import-and-open probe in an authorized test file | guaranteed |
| T26 | A worker destroying user work during recovery | rollback removed; no worker may restore or delete from snapshots | guaranteed by scope |

Residual, accepted and recorded: T9, T20, T21, T22, and T23 are observations, not
compare-and-swap; the projects root itself is opened by pathname; record size is
unbounded; a crash between temporary creation and publication leaves an orphan
temporary that nothing in this task sweeps; and `.env` and `.DS_Store` changes
are outside the capture map by design.

## Claim or decision

Version 6 makes the implementation-start gate and the handoff delta mechanically
sound. One canonical JSON manifest is emitted and consumed by the same strict
parser, so the format a reviewer is told to produce is the format the code
accepts. Every symlink is a row whether it points at a file or a directory, so
the map is complete in the sense the contract already claimed. The allowlists
live inside the manifest and are validated to exactly 8, 36, and 44 before any
state is examined, and the delta requires the touched set to equal all 44 — a
strict subset now fails where version 5 printed `delta OK`. Everything version 5
passed on is carried forward unchanged, including the complete absence of
rollback.

## Evidence

- The literal fenced block in this artifact was extracted mechanically and run
  on **Python 3.10.11** before this artifact was called passed. Against a
  purpose-built 8/36/44 fixture: `build` emitted a canonical manifest that its
  own strict loader accepted; `preflight` returned `0`; touching all 44 paths
  gave `delta OK: touched set equals all 44 authorized paths`; touching 43 gave
  `delta FAILED: 1 authorized path(s) untouched` with `UNTOUCHED ... <-- MISSING`;
  touching all 44 plus one outside path gave
  `delta FAILED: 1 path(s) outside the allowlist`.
- The same extracted block reproduced both `H2` cases that version 5 missed:
  a pre-existing symlink to a **directory** now produces an `l` row; retargeting
  it changed that row's target digest and made preflight and delta exit `1`;
  replacing it with a real empty directory removed the row; replacing it with a
  regular file flipped the row `type` from `l` to `f`. Each was nonzero.
- Fourteen manifest-strictness mutations each failed closed on the extracted
  block: wrong `capture_map_version`, altered exclusions, unknown and missing
  top-level keys, 7-instead-of-8 modified, 35-instead-of-36 new, duplicates in
  either list, a new path colliding with a row, a duplicate row path, unsorted
  rows, a row missing a key, a row `type` outside the vocabulary, a boolean
  `length`, and a duplicate JSON key.
- Snapshot handling was exercised on the extracted block: a stray file in the
  snapshot directory failed exact-membership, and a corrupted snapshot failed
  digest authentication.
- Run against **this repository**, the extracted block produced a canonical
  manifest with 333 rows, 8 modified, 36 new, 44 union, `config/model-routing.json`
  captured at its current user-owned bytes, both pre-existing tracked
  modifications present, and all 16 files under `src/brichan/resources/`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v5/plan-review.md:65-92,94-121,122-151`
  state `H1`, `H2`, and `H3` with the reproductions this version answers, and
  `:217-229` lists the four test gaps that plan steps 20 and 14 now close.

## Uncertainty

- The capture map, preflight, and delta remain point-in-time observations. A
  same-identity process mutating files between two observations defeats all
  three, and no change here alters that.
- Excluding `.env` and `.DS_Store` is a deliberate blind spot.
- The 333-row figure is this working tree at planning time, not a contract; only
  equality against the coordinator's own capture matters.
- The delta requires the touched set to equal all 44. If a future review reduces
  the authorized scope, the manifest counts and the three constants in the script
  must change together, and the script fails closed until they do.
- The worked record was validated through a reference renderer written for this
  planning session, not the implementation, which does not yet exist.
- Removing rollback means a failed implementation leaves partial work in the tree
  until a coordinator-reviewed commit revert.
