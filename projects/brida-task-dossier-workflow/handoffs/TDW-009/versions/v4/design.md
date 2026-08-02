# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `design`
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

## Threat-model boundary

Read this before any other section. No statement anywhere in this artifact, or in
`requirements.md`, `brief.md`, `options.md`, or `plan.md`, may be read as a
stronger claim than this one.

**Out of scope.** A non-cooperating process running under the same OS identity
that mutates directory entries inside the dossier while the generator holds the
dossier lock. Such a process can already unlink, replace, or truncate any file
this tooling owns by direct action. This generator is a repository developer
tool, not a privilege boundary against processes that already hold its
privileges.

**Why the boundary sits here, as a tested fact.** No Python 3.10
standard-library primitive available on both darwin and Linux binds a hard
link's source identity to an open file descriptor. `os.AT_EMPTY_PATH` and
`os.O_TMPFILE` are not exposed by this CPython build, and `/proc/self/fd` does
not exist on darwin. `os.link` therefore resolves its source by directory entry,
and the window between the source's identity check and the link cannot be closed
portably.

**What is and is not claimed against the excluded process.** Neither prevention
nor detection is claimed. The immediate post-publication check is a
**point-in-time best-effort observation**: it returns nonzero *if, at the instant
it runs*, it observes a type or inode mismatch at the final name. A continuously
active excluded process can substitute the entry after that check, or change it
again before it, and the check will not observe the mismatch. The controlled
substitution tests in `plan.md` prove only that a mismatch which is still present
when the check runs is reported; they are not evidence of adversarial detection
and must never be cited as such.

**What is claimed.** Safety against pre-existing symlinks at any path component;
against namespace drift the generator can observe; against ordinary concurrent
Brichan invocations that cooperate with the dossier lock; and against every
specified write, `fsync`, close, link, cleanup, and directory-`fsync` failure.
Malformed, hostile, or injected record content is refused.

**Residual consequence.** If the excluded process substitutes the temporary
source name in the unclosable window, a foreign inode or a symlink can appear at
a final artifact name. The generator does not remove it, because deleting an
entry the run cannot prove it created is forbidden by the same contract. Manual
inspection is required.

## Version 4 supersession

Versions 1 to 3 are preserved byte-identically at `versions/v1/`, `versions/v2/`,
and `versions/v3/`. Version 4 changes five things: the worked record is now
complete and machine-verified; every detection claim is restated as point-in-time
best-effort; the summary exit table is derived from actual validator discovery
rather than from an assumed one; the lock ordering is corrected to what is
physically possible; and the implementation-start manifest gains byte snapshots,
a canonical format, and an identity-checked rollback that never overwrites a
concurrently changed target. No protected-file digest is hard-coded anywhere in
version 4.

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

Hunks 3 to 5 are authorized by coordinator decision 2 of the version-3
amendment. They add exactly two diagnostics; every existing diagnostic keeps its
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

Exactly seventeen keys. All are required; nullable means JSON `null` is
permitted, not that the key may be omitted.

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
| `sections[].body` | `list` | no | elements are `str`; one element per rendered line |
| `claim` | `str` | no | non-placeholder |
| `evidence` | `list` | no | elements are `str`; non-empty |
| `uncertainty` | `list` | no | elements are `str`; non-empty |

### Cross-record consistency

Refusals, not derivations. The generator never invents these.

- `index_identity["Accepted plan version"]` equals `artifacts.plan.version`, and
  `index_identity["Accepted plan ID"]` equals `artifacts.plan.fields["Plan ID"]`,
  whenever `artifacts.plan.fields["Plan status"]` is `accepted`.
- Both reviews' `fields["Reviewed plan version"]` equal the **decimal string** of
  `artifacts.plan.version`, because the validator compares the rendered strings.
- Both reviews' `fields["Reviewed plan ID"]` equal
  `artifacts.plan.fields["Plan ID"]`.
- Neither review's `reviewing_session` nor `authoring_session` may equal
  `artifacts.plan.authoring_session`.

### Structural injection rules

Refusal, not escaping, per **rendered position class**. Each rule names the
`parser.py` primitive it protects.

| Class | Members | Refused | Protects |
| --- | --- | --- | --- |
| Backtick-wrapped | every metadata value, every `fields` value, every `index_identity` value, top-level `origin` | backtick, pipe, newline, control character | the code span the renderer wraps these in; a backtick would terminate it and expose `parse_fields` and `parse_table` to the remainder |
| Free-text single-line | `sections[].title`, `evidence[]`, `uncertainty[]` | newline, control character, a value starting with `#`, a value that both starts and ends with `\|` | `parse_sections` keys on `^## `; `parse_table` keys on lines that start and end with a pipe; a newline would split one `list_items` bullet into two and inflate the evidence count |
| Multi-line block | `claim`, `sections[].body[]` | any line starting with `#`, any line that both starts and ends with `\|`, any line matching `- <label>:`, any fence line, any control character other than a line feed | `parse_sections`, `parse_table`, and `parse_fields` respectively |

Backticks are **permitted** in free-text and multi-line positions, because no
`parser.py` primitive keys on a backtick. This is what makes ordinary
`` `path/to/file.py:10-20` `` evidence writable, and the worked example below
exercises it.

### Parsing mechanics

`json.load(handle, object_pairs_hook=_reject_duplicate_keys)`; the hook raises on
the first repeated key at any depth. Types are checked with `type(v) is ...`,
never `isinstance`, because `isinstance(True, int)` is true while
`type(True) is int` is false.

## Worked record: complete and machine-verified

This is a **complete eleven-artifact record**, not an abbreviation. It is the
literal fixture the extraction test loads: the test parses this fenced block out
of this file, validates it under the schema tables above, renders it, and runs
the real `validate_dossier` against the result. Version 3 supplied only
`artifacts.plan` and a prose promise about the other ten; that made the mandated
assertion impossible, which is the defect this section closes.

Before this artifact was written, the record below was rendered by a reference
renderer and checked with the repository's own validator: `validate_dossier`
returned **zero** diagnostics, and `validate_dossier(..., require_complete=True)`
returned **zero** diagnostics. Its rendered form totals **410 lines** across the
eleven artifacts, inside the 447-line Level 0 budget.

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

## Implementation-start manifest

Coordinator-owned, captured after plan version 4 is accepted, replacing
`baseline/pre-task-manifest.txt`. Version 3 recorded digests only, which cannot
reconstruct bytes; a reverse patch needs content.

**No protected-file digest is hard-coded in any planning artifact.** The manifest
records whatever bytes exist at capture time. In particular
`config/model-routing.json` is user-owned protected state: implementation must
neither absorb it into scope, nor revert it, nor compare it against a digest
written into a plan.

### Canonical format

A UTF-8 text file plus a sibling snapshot directory.

```text
manifest-version: 1
repository-head: <full commit id>
worktree-dirty: yes|no
capture-scope-excludes: projects/<slug>/handoffs/TDW-009/**   (coordinator, planner, reviewer owned)

[protected]                     # one line per file: path, sha256, byte length
config/model-routing.json <sha256> <bytes>
src/brichan/resources/<...>     <sha256> <bytes>       # all 16 files, including __init__.py
projects/<slug>/handoffs/TDW-006/<...>.md <sha256> <bytes>
projects/<slug>/handoffs/TDW-007/<...>.md <sha256> <bytes>
projects/<slug>/handoffs/TDW-008/<...>.md <sha256> <bytes>

[allowlist-modified]            # exactly 8 lines
<path> <sha256> <bytes> snapshot/<flattened-path>

[allowlist-new]                 # exactly 36 lines
<path> absent

[untracked-leaves]              # one line per file; never a collapsed directory
<path>
```

`snapshot/<flattened-path>` is a byte-for-byte copy of each of the eight modified
tracked files as they stood at capture time. That copy, not the digest, is what
makes a reverse patch constructible.

The implementer refuses to start if the file is absent, if
`manifest-version` is not `1`, if `[allowlist-modified]` does not hold exactly
eight lines each with an existing snapshot, if `[allowlist-new]` does not hold
exactly thirty-six `absent` lines, if any of the sixteen resource files is
missing, or if `[untracked-leaves]` collapses a directory.

### Exact set-delta procedure

```text
observed   := every file under the repository, minus .git, .venv, __pycache__,
              minus every path under capture-scope-excludes
changed    := { p in [allowlist-modified] : sha256(p) != manifest sha256(p) }
created    := { p in [allowlist-new]      : p exists now }
unexpected := { p in observed : p is new since [untracked-leaves]
                                or p is tracked and its bytes differ }
              minus ([allowlist-modified] union [allowlist-new])
require unexpected == {}                       # no path outside the 44
require created subset of [allowlist-new]
delta      := changed union created            # must equal the 44 authorized paths at handoff
```

Because `capture-scope-excludes` removes the coordinator-, planner-, and
reviewer-owned dossier paths, planning and review leaves created after capture
can never be counted as implementation leaves.

### Identity-checked rollback

At handoff, step 21 records a **post-implementation digest** for each of the 44
paths. Rollback then proceeds per path:

```text
for p in [allowlist-modified]:
    if sha256(p) != post_implementation_sha256(p):  ABORT p   # changed after implementation
    else: restore snapshot/<flattened p> over p
for p in [allowlist-new]:
    if not exists(p):                                skip
    if sha256(p) != post_implementation_sha256(p):  ABORT p   # changed after implementation
    else: delete p
```

A target whose current bytes differ from what implementation left is **never
overwritten and never deleted**; the rollback aborts on that path and escalates.
Whole-file `git checkout --` is forbidden: it reverts to `HEAD` and would discard
pre-existing user changes, including the current routing-file change.

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
- **Protected state is whatever the manifest captured.** No digest is hard-coded.
- **Hand authoring stays first-class.**
- **Checkout only, routing neutral, no new gate.**

## Threat model

| # | Threat | Control | Strength |
| --- | --- | --- | --- |
| T1 | Ancestor swapped for a symlink after the safety check | descriptor walk; every operation `dir_fd`-relative | guaranteed |
| T2 | Symlink or non-directory at any path component | `O_DIRECTORY \| O_NOFOLLOW`; `ELOOP` and `ENOTDIR` both refusals | guaranteed |
| T3 | Record identity crafted to escape the projects root | pattern-validated identity, single components, `dossier_path` check, no pathname write | guaranteed |
| T4 | Overwriting durable evidence | `os.link` fails `EEXIST`; rename and replace forbidden | guaranteed |
| T5 | Truncated artifact published | full write, `fsync`, inode check before the link | guaranteed |
| T6 | Temporary cleanup deleting a raced-in file | identity re-verified before `unlink`; final entries never unlinked | guaranteed |
| T7 | Two cooperating generations interleaving | exclusive `flock` acquired immediately after opening the dossier, before any temporary or artifact mutation | guaranteed for cooperating writers |
| T8 | Contained-but-detached run reported as success | final canonical re-walk comparing device and inode per level | guaranteed |
| T9 | **Excluded process substitutes the temporary source or the final entry** | post-publication `lstat` type and inode check | **point-in-time best-effort observation only; neither prevention nor detection guaranteed** |
| T10 | Manufactured evidence or inferred `PASS` | every judgment value copied from the record; placeholders refused | guaranteed |
| T11 | Index becoming a second authority | only projection sections and the status table | guaranteed |
| T12 | Duplicate JSON keys collapsing a verdict | `object_pairs_hook` refuses the first repeat at any depth | guaranteed |
| T13 | Boolean smuggled into an integer position | exact `type(v) is int` checks | guaranteed |
| T14 | Markdown structure injection | closed per-position refusal set tied to `parser.py` primitives | guaranteed |
| T15 | Personal or home path in a durable artifact | every record string matched against `PERSONAL_PATH_PATTERNS` | guaranteed |
| T16 | Record content reaching execution | `json.load` only; record never written back | guaranteed |
| T17 | Summary masking project-level drift | verdict from `validate_projects`; selection never overrides it | guaranteed |
| T18 | Ancestor-symlinked authority path tolerated | validator hunks 4 and 5 | guaranteed |
| T19 | Synthetic fixture mistaken for real review evidence | synthetic prefix, per-artifact claim, `results.md` declaration, contract test | guaranteed |
| T20 | Rollback overwriting a concurrently changed target | per-path comparison against the post-implementation digest; abort rather than write | guaranteed |

Residual, accepted and recorded: T9 above; the projects root itself is opened by
pathname, so a symlinked ancestor above the operator-supplied root is trusted;
record size is unbounded; a crash between temporary creation and publication
leaves a recognisable orphan temporary that nothing in this task sweeps.

## Claim or decision

Version 4 makes every normative statement in this dossier match what was actually
tested. The worked record is complete, was rendered by a reference renderer, and
passed the repository's own `validate_dossier` twice — default and
`--require-complete` — with zero diagnostics, so the mandated extraction test is
now possible. Every detection claim against the excluded process is restated as
point-in-time best-effort observation, matching the design's own prior
concession. The summary exit table is derived from what `discover_dossiers`,
`discover_partial_dossiers`, and `parse_artifact` actually do, so an existing
unreadable `index.md` and root-level partial adoption exit `1` while only a truly
absent or unlistable scope exits `2`. The lock is specified where it can exist:
after descriptor-relative directory creation, immediately on opening the dossier,
and before any temporary or artifact mutation. The manifest gains byte snapshots,
a canonical format, an exact set-delta procedure, and an identity-checked
rollback that aborts rather than overwrite a concurrently changed target — and no
protected-file digest is hard-coded anywhere.

## Evidence

- A read-only reference renderer built from `schema.py` constants and the eleven
  templates rendered the complete worked record above into a temporary projects
  root; `validate_dossier` returned zero diagnostics and
  `validate_dossier(..., require_complete=True)` returned zero diagnostics, and
  the rendered dossier totalled 410 lines across the eleven artifacts. This is
  the executable basis for the extraction test and for the Level 0 budget claim.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md:71-90`
  states `H1` exactly: the version-3 example supplied one artifact key against
  eleven required, so the mandated assertion could not pass. The record above has
  all eleven keys with seventeen keys each.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md:121-147`
  establishes the exit contradiction against source, and
  `src/brichan/contracts/task_dossier/validation.py:1109-1116,1138-1195` plus
  `src/brichan/contracts/task_dossier/parser.py:116-123` confirm it: discovery
  globs the index path without reading it, `parse_artifact` emits
  `cannot read artifact`, and partial adoption is raised by `validate_projects`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md:92-119`
  supplies both halves of `H2`: a digest cannot reconstruct a reverse patch, and
  the digest version 3 hard-coded for `config/model-routing.json` no longer
  matches the file. Read-only hashing during this planning session reproduced the
  reviewer's current value and confirmed the file is modified relative to `HEAD`,
  which is why version 4 hard-codes no digest at all and treats the capture-time
  bytes as protected user state.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md:175-194`
  states `M1`: a directory cannot be locked before it exists. The Phase A to
  Phase D ordering above resolves it without weakening the property that matters.
- `src/brichan/contracts/task_dossier/validation.py:772-780,782-826,827-886`
  fixes the exact insertion points for hunks 3 to 5 and shows that neither link
  validator currently inspects an ancestor.
- A read-only count of `src/brichan/resources/` found sixteen files, confirming
  the manifest's resource coverage requirement and the reviewer's observation
  that the superseded baseline listed only fifteen.

## Uncertainty

- T9 is a stated limitation with no remedy inside the authorized boundary.
  Detection is opportunistic: an excluded process active across the check window
  can defeat it in either direction. The controlled tests establish the
  diagnostic path, not adversarial coverage, and must be labelled that way in
  the test file itself.
- The worked record was validated through a reference renderer written for this
  planning session, not through the implementation that does not yet exist. If
  the implemented renderer diverges from the documented rendering rules, the
  extraction test will fail — which is the outcome that test exists to produce.
- The final re-walk compares device and inode. On a filesystem that recycles
  inode numbers within a single run, drift could theoretically evade it.
- Hunks 4 and 5 are a behaviour change for any checkout with a symlinked
  ancestor above an authority path. None exists here; a downstream checkout could
  newly fail validation.
- The ownership and intended durability of the current `config/model-routing.json`
  change cannot be inferred from repository state. Version 4 therefore requires
  the coordinator to capture whatever bytes exist and forbids implementation from
  interpreting them; it does not resolve the ownership question.
