# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `design`
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

## Threat-model boundary

Read this before any other section. No statement anywhere in this dossier may be
read as a stronger claim than this one.

**Out of scope.** A non-cooperating process running under the same OS identity
that mutates directory entries while the generator holds the dossier lock, or
that mutates repository files during capture, preflight, implementation, or the
after-delta check. Such a process already has this tooling's privileges.

**Why the boundary sits here, as a tested fact.** No Python 3.10
standard-library primitive available on both darwin and Linux binds a hard
link's source identity to an open file descriptor. `os.AT_EMPTY_PATH` and
`os.O_TMPFILE` are not exposed by this CPython build, and `/proc/self/fd` does
not exist on darwin. `os.link` resolves its source by directory entry, and that
window cannot be closed portably.

**What is not claimed.** Neither prevention nor detection against the excluded
process. The post-publication check is a **point-in-time best-effort
observation**: it returns nonzero only if a type or inode mismatch is present at
the instant it runs. The capture map, the start preflight, and the after-delta
check are likewise **point-in-time observations of repository state**; none of
them is a compare-and-swap and none is claimed to be. A process mutating files
between two observations can defeat any of them.

**What is claimed.** Safety against pre-existing symlinks at any path component;
against namespace drift the generator can observe; against ordinary concurrent
Brichan invocations that cooperate with the dossier lock; against every
specified write, `fsync`, close, link, cleanup, and directory-`fsync` failure;
and refusal of malformed, hostile, or injected record content.

**Residual consequence.** A foreign inode or symlink can appear at a final
artifact name. The generator does not remove it. Manual inspection is required.

## Version 5 supersession

Versions 1 to 4 are preserved byte-identically under `versions/v1/` to
`versions/v4/`. Version 5 changes four things and removes one.

1. The implementation-start baseline becomes a **complete no-follow capture
   map** of every observed repository file outside an exact enumerated exclusion
   set, with path, type, byte length, and SHA-256 per row, including
   pre-existing tracked changes and untracked leaves.
2. An **exact executable start preflight** rebuilds that map, byte-compares it,
   authenticates every snapshot, and verifies every planned-new path is absent.
3. An **exact executable after-delta algorithm** computes changed, created, and
   removed sets against the capture and requires the unexpected set to be empty.
4. `sections[].body[]` refuses embedded line feeds; multi-line `claim` remains
   allowed and is checked per line.

**Removed: all rollback.** Automatic or in-task rollback is gone from TDW-009 —
every promise, procedure, and test. It was never a user requirement, and a
portable pathname procedure cannot provide honest compare-and-swap safety
against concurrent same-identity mutation. Snapshots exist **only as evidence**.
No worker may restore or delete from them.

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

Coordinator-owned, captured after plan version 5 is accepted, replacing
`baseline/pre-task-manifest.txt`. Version 4 recorded only protected paths, the
eight allowlist-modified paths, and the *names* of untracked leaves, so it could
not tell whether a pre-existing tracked or untracked file outside those sets had
been modified. The capture map removes that gap by recording **every observed
file outside an exact exclusion set**.

### Exact exclusion set

Nothing else is excluded. Every other file in the working tree gets a row,
including pre-existing tracked modifications and pre-existing untracked leaves.

| Exclusion | Form | Why |
| --- | --- | --- |
| `.git` | top-level directory prefix | version-control internals, not working state |
| `.venv` | top-level directory prefix | local interpreter, not repository content |
| `.pytest_cache` | top-level directory prefix | regenerated by any test run |
| `__pycache__` | any path component | regenerated by any import |
| `projects/brida-task-dossier-workflow/handoffs/TDW-009` | directory prefix | coordinator-, planner-, and reviewer-owned; includes `versions/` and the capture itself |
| `projects/brida-task-dossier-workflow/handoffs/TDWPLAN-009` | directory prefix | planner child receipt, coordinator-owned |
| `projects/brida-task-dossier-workflow/handoffs/TDWIMP-009` | directory prefix | implementer child receipt, coordinator-owned |
| `projects/brida-task-dossier-workflow/handoffs/TDWREV-009` | directory prefix | reviewer child receipt, coordinator-owned |
| `.DS_Store` | any file with this name | platform noise; already in `ignored_root_files` |
| `.env` | any file with this name | may carry secrets; already in `ignored_root_files` |

Cost of the last two, stated rather than hidden: a change to a `.env` or
`.DS_Store` file is not observed by the map, the preflight, or the delta.

### Row format

One row per non-directory entry, sorted by path, tab-separated:

```text
<repo-relative-path>\t<type>\t<byte-length>\t<sha256>
```

`type` is `f` for a regular file, `l` for a symlink, `o` for anything else. The
walk never follows a symlink: a symlink row records the length and SHA-256 of the
**link target string**, never of the file it points at. Directories have no rows;
adding or removing a directory shows up as added or removed file rows.

### Capture file layout

```text
capture-map-version: 1
row-format: path<TAB>type<TAB>length<TAB>sha256
exclusion: <one line per entry in the exclusion table>
snapshot-dir: <repo-relative directory>

[rows]
<every row, sorted>

[snapshots]
<allowlist-modified path><TAB><snapshot file name>
```

**Snapshot naming is exact**, closing the version-4 ambiguity about flattening:
the snapshot file for repo-relative path `p` is named
`sha256(p.encode("utf-8")).hexdigest() + ".bin"`. No escaping, no collisions, no
directory structure.

### Snapshots are evidence only

The eight modified tracked paths have byte snapshots so a reviewer can see what
the implementer started from. **No worker may restore from, delete from, or
write through a snapshot.** They are read to authenticate the capture and for
nothing else. This is the whole of their purpose in version 5.

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

## Exact executable preflight and after-delta

One script, three modes, standard library only, read-only. It is reproduced here
verbatim; the implementer runs it as written and the tests in
`tests/integration/test_task_dossier_workflow.py` exercise the same logic. No
repository path is added for it: it is a heredoc the operator pastes, and its
behaviour is covered by an already-authorized test file.

```python
#!/usr/bin/env python3
"""TDW-009 capture map: build, preflight, after-delta. Read-only, no-follow."""
import hashlib, os, stat, sys

EXCLUDED_DIRS = (
    ".git", ".venv", ".pytest_cache",
    "projects/brida-task-dossier-workflow/handoffs/TDW-009",
    "projects/brida-task-dossier-workflow/handoffs/TDWPLAN-009",
    "projects/brida-task-dossier-workflow/handoffs/TDWIMP-009",
    "projects/brida-task-dossier-workflow/handoffs/TDWREV-009",
)
EXCLUDED_ANY_DIR = ("__pycache__",)
EXCLUDED_NAMES = (".DS_Store", ".env")
NULL_SHA = "0" * 64


def excluded(rel):
    parts = rel.split("/")
    if parts[-1] in EXCLUDED_NAMES:
        return True
    if any(part in EXCLUDED_ANY_DIR for part in parts):
        return True
    return any(parts[: len(p.split("/"))] == p.split("/") for p in EXCLUDED_DIRS)


def row(root, rel):
    full = os.path.join(root, rel)
    mode = os.lstat(full).st_mode
    if stat.S_ISLNK(mode):
        target = os.readlink(full).encode("utf-8")
        return f"{rel}\tl\t{len(target)}\t{hashlib.sha256(target).hexdigest()}"
    if not stat.S_ISREG(mode):
        return f"{rel}\to\t0\t{NULL_SHA}"
    digest, length = hashlib.sha256(), 0
    with open(full, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
            length += len(chunk)
    return f"{rel}\tf\t{length}\t{digest.hexdigest()}"


def build_map(root):
    rows = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        rel_dir = os.path.relpath(dirpath, root)
        rel_dir = "" if rel_dir == "." else rel_dir.replace(os.sep, "/")
        dirnames[:] = sorted(
            d for d in dirnames if not excluded(f"{rel_dir}/{d}".lstrip("/"))
        )
        for name in sorted(filenames):
            rel = f"{rel_dir}/{name}".lstrip("/")
            if not excluded(rel):
                rows.append(row(root, rel))
    return sorted(rows)


def parse_rows(text):
    return {l.split("\t", 1)[0]: l for l in text.splitlines() if l.strip()}


def snapshot_name(rel):
    return hashlib.sha256(rel.encode("utf-8")).hexdigest() + ".bin"


def sha_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    mode, root = sys.argv[1], sys.argv[2]
    current = "\n".join(build_map(root)) + "\n"
    if mode == "build":
        sys.stdout.write(current)
        return 0

    capture = open(sys.argv[3], encoding="utf-8").read()
    if mode == "preflight":
        failures = 0
        if current != capture:
            a, b = parse_rows(capture), parse_rows(current)
            for p in sorted(set(a) | set(b)):
                if a.get(p) != b.get(p):
                    failures += 1
                    print(f"DRIFT {p}: capture={a.get(p)!r} current={b.get(p)!r}",
                          file=sys.stderr)
        snap_dir, modified, new_paths = sys.argv[4], sys.argv[5], sys.argv[6]
        rows = parse_rows(capture)
        for rel in open(modified, encoding="utf-8").read().split():
            snap = os.path.join(snap_dir, snapshot_name(rel))
            if rel not in rows:
                failures += 1
                print(f"SNAPSHOT {rel}: absent from capture map", file=sys.stderr)
                continue
            expected = rows[rel].split("\t")[3]
            if os.path.islink(snap) or not os.path.isfile(snap):
                failures += 1
                print(f"SNAPSHOT {rel}: missing or not a regular file", file=sys.stderr)
            elif sha_file(snap) != expected:
                failures += 1
                print(f"SNAPSHOT {rel}: digest does not match capture row", file=sys.stderr)
        for rel in open(new_paths, encoding="utf-8").read().split():
            if os.path.lexists(os.path.join(root, rel)):
                failures += 1
                print(f"COLLISION {rel}: planned-new path already exists", file=sys.stderr)
            if rel in rows:
                failures += 1
                print(f"COLLISION {rel}: planned-new path present in capture map",
                      file=sys.stderr)
        if failures:
            print(f"preflight FAILED: {failures} problem(s)", file=sys.stderr)
            return 1
        print(f"preflight OK: {len(parse_rows(current))} rows byte-identical; "
              "snapshots verified; new paths absent")
        return 0

    if mode == "delta":
        allowlist = set(open(sys.argv[4], encoding="utf-8").read().split())
        a, b = parse_rows(capture), parse_rows(current)
        changed = {p for p in a if p in b and a[p] != b[p]}
        created = set(b) - set(a)
        removed = set(a) - set(b)
        unexpected = (changed | created | removed) - allowlist
        for label, group in (("CHANGED", changed), ("CREATED", created), ("REMOVED", removed)):
            for p in sorted(group):
                print(f"{label} {p}{'  <-- UNEXPECTED' if p in unexpected else ''}")
        if removed:
            print(f"delta FAILED: {len(removed)} path(s) removed", file=sys.stderr)
            return 1
        if unexpected:
            print(f"delta FAILED: {len(unexpected)} path(s) outside the allowlist",
                  file=sys.stderr)
            return 1
        print(f"delta OK: {len(changed | created)} of {len(allowlist)} authorized "
              "paths touched; unexpected set empty")
        return 0
    raise SystemExit(f"unknown mode {mode!r}")


if __name__ == "__main__":
    raise SystemExit(main())
```

### Invocation

```bash
# coordinator, at capture time
python3 capture.py build . > <capture-dir>/capture-map.txt

# implementer, before any write; any nonzero exit is a stop
python3 capture.py preflight . <capture-dir>/capture-map.txt \
    <capture-dir>/snapshot <capture-dir>/allowlist-modified.txt \
    <capture-dir>/allowlist-new.txt

# implementer, at handoff
python3 capture.py delta . <capture-dir>/capture-map.txt \
    <capture-dir>/allowlist-all.txt
```

### Guarantees and their exact limits

| Property | Mechanism | Limit |
| --- | --- | --- |
| Pre-existing tracked modification outside the allowlist is caught | it has a capture row; a later change alters that row | point-in-time |
| Pre-existing untracked modification outside the allowlist is caught | untracked leaves get full rows, not just names | point-in-time |
| Post-capture collision at a planned-new path is caught | the path appears in the current map and `lexists` finds it | point-in-time |
| Snapshot corruption, replacement, removal, or symlinking is caught | each snapshot is `lstat`-checked no-follow and hashed against its capture row | point-in-time |
| Removal of any observed file is caught | it leaves the current map | point-in-time |
| Symlink substitution is not mistaken for content | `lstat` plus link-target hashing; the walk never follows | absolute |
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
  and appears in the map like any other file.
- **No rollback exists.** Recovery is fix-forward, then a separately reviewed
  commit revert.
- **Checkout only, routing neutral, no new gate.**

## Threat model

| # | Threat | Control | Strength |
| --- | --- | --- | --- |
| T1 | Ancestor swapped for a symlink after the safety check | descriptor walk; every operation `dir_fd`-relative | guaranteed |
| T2 | Symlink or non-directory at any path component | `O_DIRECTORY \| O_NOFOLLOW`; `ELOOP` and `ENOTDIR` both refusals | guaranteed |
| T3 | Record identity crafted to escape the projects root | pattern-validated identity, single components, no pathname write | guaranteed |
| T4 | Overwriting durable evidence | `os.link` fails `EEXIST`; rename and replace forbidden | guaranteed |
| T5 | Truncated artifact published | full write, `fsync`, inode check before the link | guaranteed |
| T6 | Temporary cleanup deleting a raced-in file | identity re-verified before `unlink`; final entries never unlinked | guaranteed |
| T7 | Two cooperating generations interleaving | exclusive `flock` immediately after opening the dossier | guaranteed for cooperating writers |
| T8 | Contained-but-detached run reported as success | final canonical re-walk comparing device and inode per level | guaranteed |
| T9 | **Excluded process substitutes a temporary source or a final entry** | post-publication `lstat` type and inode check | **point-in-time observation only** |
| T10 | Manufactured evidence or inferred `PASS` | every judgment value copied from the record | guaranteed |
| T11 | Index becoming a second authority | only projection sections and the status table | guaranteed |
| T12 | Duplicate JSON keys collapsing a verdict | `object_pairs_hook` refuses the first repeat | guaranteed |
| T13 | Boolean smuggled into an integer position | exact `type(v) is int` checks | guaranteed |
| T14 | Markdown structure injection | closed per-position refusal set; `sections[].body[]` refuses line feeds | guaranteed |
| T15 | Personal or home path in a durable artifact | every record string matched against `PERSONAL_PATH_PATTERNS` | guaranteed |
| T16 | Record content reaching execution | `json.load` only; record never written back | guaranteed |
| T17 | Summary masking project-level drift | verdict from `validate_projects`; selection never overrides it | guaranteed |
| T18 | Ancestor-symlinked authority path tolerated | validator hunks 4 and 5 | guaranteed |
| T19 | Synthetic fixture mistaken for real review evidence | synthetic prefix, per-artifact claim, `results.md` declaration, contract test | guaranteed |
| T20 | Implementation touching a path outside the 44 | complete capture map plus the after-delta unexpected set | **point-in-time observation** |
| T21 | Starting from a stale baseline | start preflight byte-compares the rebuilt map and authenticates snapshots | **point-in-time observation** |
| T22 | A worker destroying user work during recovery | rollback removed; no worker may restore or delete from snapshots | guaranteed by scope |

Residual, accepted and recorded: T9, T20, and T21 are observations, not
compare-and-swap; the projects root itself is opened by pathname; record size is
unbounded; a crash between temporary creation and publication leaves an orphan
temporary that nothing in this task sweeps; and `.env` and `.DS_Store` changes
are outside the capture map by design.

## Claim or decision

Version 5 replaces the version-4 manifest with a complete no-follow capture map
over every observed non-excluded file, so the after-delta `unexpected` set is
computable rather than asserted — the defect that made version 4's exact-write
gate unprovable. The start preflight is now an executable byte comparison that
also authenticates snapshots and proves every planned-new path absent, so
implementation cannot begin against a stale baseline. Rollback is removed
entirely rather than deepened: snapshots are evidence, recovery is fix-forward
and then a separately reviewed commit revert, and no worker may restore or
delete from a snapshot. `sections[].body[]` now refuses line feeds so one element
is exactly one rendered line, while `claim` keeps safe multi-line prose under
per-line checks. All version-4 content that passed review — the literal
eleven-artifact record, the descriptor walk, the four-phase lock ordering,
publication, the validator-derived exit table, and the evaluation design — is
carried forward unchanged.

## Evidence

- The script in this artifact was executed read-only against this repository
  before being written down. `build` produced a 333-row map that includes the
  pre-existing tracked modifications to `config/model-routing.json`,
  `projects/brida-task-dossier-workflow/references.md`, and `tasks.md`, and
  excluded every enumerated exclusion — the concrete gap the version-4 review
  identified.
- The same script was exercised against a purpose-built fixture for nine
  scenarios: a clean preflight passed; a post-capture change to a pre-existing
  tracked file failed preflight; a post-capture change to a pre-existing
  untracked file failed preflight; a collision at a planned-new path failed with
  both a `DRIFT` and a `COLLISION` diagnostic; a corrupted, a removed, and a
  symlinked snapshot each failed; a delta touching only allowlisted paths passed;
  changes to a pre-existing tracked and to a pre-existing untracked file outside
  the allowlist each landed in `unexpected` and exited `1`; and removing an
  observed file exited `1`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md:70-101`
  states `H1` with the same concrete example this map closes: tracked changes to
  `references.md` and `tasks.md` were neither protected, allowlisted, nor
  excluded, and had no capture-time bytes to compare against.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md:102-134`
  states `H2`, whose bounded revision version 5 declines in favour of the
  amendment's instruction to remove rollback outright, and
  `:136-161` states `H3`, closed by the executable preflight above.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md:165-181`
  states `M1`: grouping `sections[].body[]` with `claim` permitted a body element
  to contain several rendered lines, which the tightened rule now refuses.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:185-215`
  fixes the five version-5 decisions: complete capture map with an exact
  exclusion set, rollback removal with fix-forward and reviewed commit revert,
  tests in already-authorized files with no forty-fifth path, the
  `sections[].body[]` line-feed rule, and the retained same-identity exclusion.
- A read-only check confirmed the corrected schema rule is decidable as written:
  two single-line body elements are accepted, an element carrying an embedded
  line feed is refused, a two-line `claim` with no structural line is accepted,
  and a `claim` whose second line is a heading is refused.

## Uncertainty

- The capture map, the preflight, and the after-delta check are point-in-time
  observations. None is a compare-and-swap, and the amendment's excluded
  same-identity process defeats all three. This is stated rather than mitigated.
- Excluding `.env` and `.DS_Store` means a change to either is invisible to every
  check in this task. That is a deliberate trade for not hashing a
  secret-bearing file, and it is recorded rather than hidden.
- The 333-row figure is this working tree at planning time, not a contract. The
  coordinator's capture will have its own row count, and only byte equality
  against that capture matters.
- The worked record was validated through a reference renderer written for this
  planning session, not the implementation, which does not yet exist. A divergent
  implemented renderer will fail the extraction test.
- Removing rollback means a failed implementation leaves partial work in the
  tree until a coordinator-reviewed revert. That is the accepted cost of not
  pretending to offer safe automatic restoration.
- The ownership and durability of the current `config/model-routing.json` change
  remain the coordinator's question; the map records it and refuses to interpret it.
