# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `MEMORY-001`
- Task level: `2`
- Artifact: `design`
- Artifact version: `6`
- Origin: `planner:2026-08-09-memory-001-plan-v6`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `65f9eedd-94f2-489d-ad67-4e0edf5caf30`
- Effective route: `plan`
- Effective model: `claude-opus-5[1m]`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Claim or decision

The repair is document surgery across `PRODUCT.md`, the canonical packaged
installed policy, all seven indexed overviews, `projects/index.md`, the
installable-tool memory files, the dogfood guide, and the release checklist. The
gate is one small, self-contained `scripts/` entrypoint with fixed constants that
validates six things — product version, product verification date against the
matching changelog release, index entry status and path, overview lifecycle and
its agreement with the index, required memory files, and wheel filenames in a
short explicit document list. Everything else earlier versions specified is
removed.

## Version 6 amendments

Version 6 closes the version 5 findings by narrowing, not by adding.

- **Removed**: unindexed-project detection; the backticked-path validator for
  `current-state.md`; the sdist rule; the `docs/**` completeness contract
  assertion; the externally configurable declared-path subsystem; the seven-
  outcome exhaustive resolver claim; the 104-case matrix; and the
  every-caller/every-outcome acceptance criterion (v5 H1).
- **Right-sized**: the oracle keeps exact ordered triples for three golden
  fixtures and asserts paths plus check IDs elsewhere (v5 M1); §3.5's outcome
  model is internal and no longer claims exhaustive coverage.
- **Fixed**: `errno.errorcode.get(...)` with a numeric fallback (v5 M2); a
  calendar-invalid matching release date counts as no valid matching release and
  emits `changelog-release` (v5 M3).
- **Unchanged**: every repair in §1 and §2, the seven lifecycle values, the
  five-file edit count, wheel-only gating, the canonical slash grammar, no-follow
  resolution, and every authorization bound.

## 1. Document repairs

### 1.1 Canonical installed policy and its contract test

`src/brichan/resources/dogfood_v1/policy/operating-principles.md` item 2
currently ends (lines 10–12) with "Skip the `plan` worker only for a single
bounded edit with obvious acceptance criteria; never skip `implement` or
`review`." Its sibling `bootstrap.md` states the lifecycle unconditionally, and
`CHANGELOG.md` `[0.11.0]` published it that way; the exception is the outlier.
Replace that trailing sentence:

```text
   `.brichan/config/model-routing.json`. All three phases are mandatory: never
   skip `plan`, `implement`, or `review`, regardless of how small or bounded
   the change appears. The coordinator integrates a change only after the
   independent `review` worker has verified it.
```

Items 1 and 3–8 are byte-identical. `bootstrap.md` is not edited.

`tests/contract/test_dogfood_policy_contract.py` — the only existing test file
that changes — gains assertions that the mandate requires all three phases, that
`Skip the`, `bounded edit`, and `only for` are absent, and that the integration
gate names the independent `review` worker. Existing assertions are retained.

### 1.2 `PRODUCT.md`

| Location | Required change |
|---|---|
| line 12 | `Last verified: 2026-08-09 (package version 0.11.0).` |
| lines 90–91 (§6.1 step 2) | Split into checkout-discretionary versus installed-mandatory delegation; the installed clause is unconditional and cites the policy repaired in §1.1 |
| §6.2 | One sentence stating the unconditional installed-mode mandate |
| line 198 | `Verified as of 2026-08-09:` |
| line 202 | Replace "**Nothing is published yet.**" with the published/automated-release statement; add `Latest published version: 0.11.0` |
| lines 205–211 | Drop the completed trusted-publisher and `pypi`-environment items; retain external owner-repository dogfood, friction capture, and the open README-image/public-URL item |
| §10 dogfood claim | Record v0.11 live worker orchestration as *partial* evidence, external dogfood still open |

Non-goal §4 and drift-checklist item 1 are unchanged. §1.1 lands first, because
`PRODUCT.md` lines 3–10 give runtime policy precedence.

### 1.3 Guide and release checklist

`docs/guides/installable-dogfood.md` line 67 becomes `VERSION`-derived:

```bash
BRICHAN_SRC=/absolute/path/to/brichan
python3 -m pip wheel "$BRICHAN_SRC" --no-deps --no-build-isolation \
  --wheel-dir /tmp/brichan-wheel
python3 -m venv /tmp/brichan-venv
/tmp/brichan-venv/bin/python -m pip install --no-deps \
  "/tmp/brichan-wheel/brichan-$(cat "$BRICHAN_SRC/VERSION")-py3-none-any.whl"
```

`handoffs/PYPI-001/release-checklist.md` gains one per-release step, before the
tag-push step: reconcile `PRODUCT.md`, `current-state.md`, the seven overview
lifecycle values, and `projects/index.md`, then run `make memory-check`.

## 2. Project memory repairs

### 2.1 The seven lifecycle edits, in five files

| # | File | Line | Current | Required |
|---|---|---|---|---|
| 1 | `projects/brida-workflow-evaluation/overview.md` | 7 | `- Lifecycle status: active` | `- Lifecycle status: complete` |
| 2 | `projects/brida-model-routing/overview.md` | 7 | `- Lifecycle status: active` | `- Lifecycle status: complete` |
| 3 | `projects/brida-claude-code-support/overview.md` | after title | (absent) | insert `- Lifecycle status: active` |
| 4 | `projects/brida-repository-structure-refactor/overview.md` | after title | (absent) | insert `- Lifecycle status: complete` |
| 5 | `projects/index.md` | 24 | `- Status: active` | `- Status: complete` |
| 6 | `projects/index.md` | 29 | `- Status: active` | `- Status: complete` |
| 7 | `projects/index.md` | 34 | `- Status: proposed` | `- Status: active` |

Edits 5–7 share one file: **seven edits, five changed files**. The two overviews
without a field block open with a `#` title on line 1, a blank line 2, and
`## Objective` on line 3; the added line goes immediately after the title as a
single-line block, two added lines per file:

```text
# Brida Claude Code support

- Lifecycle status: active

## Objective
```

Untouched: the `brida-installable-tool`, `brida-system-validation`, and
`brida-task-dossier-workflow` overviews, and the `- Status:` lines of the four
already-correct index entries. `projects/index.md` also carries the
installable-tool `Summary` rewrite, within the three-line entry target.

### 2.2 Installable-tool memory

- **`current-state.md`** — replaced wholesale, ≤ 80 lines,
  `Last updated: 2026-08-09` (on or after the 2026-08-03 matching release date).
  Current state only: published distribution and automated release path; the
  `.brichan/` schema-v1 footprint; `scripts/install-brichan`;
  `brichan init/status/doctor/run`; the **mandatory plan/implement/review
  lifecycle** with its re-init consequence; open gates; standing risks. No
  `.brida/`, `brida init`, `BRIDA_ROOT`, or `scripts/install-brida`.
- **`decisions.md`** — append `2026-08-09 — Brida → Brichan rename completed;
  project slugs retained`, `Status: accepted`, with a `Supersedes:` line naming
  the 2026-07-29 entry, whose `Status:` changes to `superseded` without editing
  its body.
- **`tasks.md`** — the MEMORY-001 Active row plus four Completed rows:
  `PYPI-002` (published on PyPI, tag-triggered Trusted Publishing, first
  automated publish `v0.9.0`); `RENAME-001` (runtime rename completed);
  `INIT-001` (root agent-entry pointers and the opt-in `--init-agents` skill
  export); `POLICY-001` (installed policy mandates the **mandatory
  plan/implement/review lifecycle**). Existing rows untouched.
- **`references.md`** — correct the "Current public setup" row (`README.md`
  line 60 now leads with `pip install brichan`) and the `scripts/install-brida`
  pointer at line 36.

## 3. `scripts/check_project_memory.py`

### 3.1 Shape and CLI

```text
python3 scripts/check_project_memory.py [--root PATH]
```

`--root` defaults to the repository root derived from the script location.
Exit `0` with one stdout summary line when no diagnostic is produced; exit `1`
with sorted diagnostics on stderr otherwise. No other exit code. Read-only,
offline, no subprocess, standard library only, Python 3.10+.

`Diagnostic` is a frozen dataclass `(path, check, detail)` formatted as
`<path>: <check>: <detail>`, with `path` a repository-relative POSIX string.

### 3.2 Fixed constants

```text
VERSION_FILE   = "VERSION"
CHANGELOG_FILE = "CHANGELOG.md"
PRODUCT_FILE   = "PRODUCT.md"
INDEX_FILE     = "projects/index.md"

REQUIRED_MEMORY_FILES = ("overview.md", "current-state.md", "tasks.md",
                         "decisions.md", "references.md")

LIFECYCLE_VALUES = ("active", "archived", "blocked", "complete", "paused",
                    "proposed")

ACTIVE_PRODUCT_DOCUMENTS = (
    "PRODUCT.md",
    "README.md",
    "CONTRIBUTING.md",
    "packaging/pypi-readme.md",
    "docs/index.md",
    "docs/guides/installable-dogfood.md",
    "docs/guides/model-routing.md",
    "docs/architecture/repository-layout.md",
)
```

Eight documents: the four public entry points plus the four documentation pages
that describe installing or running Brichan — the only places an install command
plausibly appears. `docs/guides/installable-dogfood.md` line 67 is the sole
`brichan-X.Y.Z` token anywhere under `docs/`, `README.md`, `PRODUCT.md`,
`CONTRIBUTING.md`, or `packaging/` today, so this list is sufficient without a
repository-wide scan. There is no config file, no glob, and no injectable set.

### 3.3 The six checks

1. **`version-claim`** — each anchored token in `PRODUCT.md`
   (`\(package version (\d+\.\d+\.\d+)\)`,
   `^Latest published version: (\d+\.\d+\.\d+)\s*$`) must equal parsed `VERSION`.
   A bare `X.Y.Z` in prose is not matched.
2. **`date-claim` / `changelog-release`** — see §3.4.
3. **`index-status`** — each real entry declares one `- Status:` in
   `LIFECYCLE_VALUES`. Missing, empty, malformed, or out-of-enum → one
   diagnostic.
4. **`index-path`** — each entry's `- Memory:` value must match, in full,
   `^projects/(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)/$`, then resolve (§3.5) to an
   existing non-symlink directory. Any other value or outcome → one diagnostic
   whose detail names the reason.
5. **`overview-lifecycle` / `lifecycle-agreement`** — each indexed
   `overview.md` holds exactly one `^- Lifecycle status: (?P<value>.+)$` whose
   value, after stripping whitespace and one optional pair of single backticks,
   is in `LIFECYCLE_VALUES`. Zero, two or more, empty, or out-of-enum →
   `overview-lifecycle`. Exactly one valid value that differs from the entry's
   `Status` → `lifecycle-agreement`.
6. **`memory-completeness`** — each of `REQUIRED_MEMORY_FILES` resolves to an
   existing regular non-symlink file. Anything else → one diagnostic.
7. **`wheel-version`** — any `brichan-\d+\.\d+\.\d+-\S*\.whl` match in an
   `ACTIVE_PRODUCT_DOCUMENTS` file → one diagnostic, whether or not the version
   equals `VERSION`. Sdists are not checked.

Index parsing strips fenced blocks and skips the `## Entry template` section, so
the template's own `## <project-name>`, `- Status: proposed | active | …`, and
`- Memory: projects/<slug>/` lines at `projects/index.md` 41–44 are not entries.

### 3.4 Version, changelog, and date

`VERSION` is read first and must match `^\d+\.\d+\.\d+$`.

The lower bound for staleness is the date of the `CHANGELOG.md` heading matching
`^## \[<parsed VERSION>\] - (?P<date>\d{4}-\d{2}-\d{2})$`. There is **no valid
matching release** — and therefore exactly one `changelog-release` diagnostic —
in each of three cases, treated identically:

- no heading for the parsed version at all;
- only a heading for a different version, e.g. `0.10.0` when `VERSION` is
  `0.11.0`;
- a heading for the parsed version whose date matches the digit shape but is not
  a real calendar date (`2026-02-30`), detected by `date.fromisoformat` raising.

In all three, only the staleness comparison is suppressed.

`PRODUCT.md`'s `Last verified:` token is parsed with `date.fromisoformat`; a
`ValueError` is a `date-claim` diagnostic and does not depend on `VERSION` or the
changelog. Staleness — value earlier than the matching release date — is a
separate `date-claim`. There is no upper bound: none exists deterministically
offline.

### 3.5 Path resolution

Index `Memory:` targets and required memory files are resolved
component-wise. Phase 1 rejects on the string alone: absolute paths, `..`
components, a leading tilde, backslashes, empty components, and anything escaping
the root. Phase 2 `lstat`s each accumulated prefix from the root outward and
never follows a link; a symlink at any component, including the final one and
including a dangling link, is rejected as such.

A small internal outcome model distinguishes what the checks need — safe/unsafe,
missing, symlink, directory, regular file, and other — where "other" covers any
remaining node type or `lstat` error and carries a short reason. **No claim is
made that every filesystem node type, every `errno`, or every caller combination
is exhaustively tested.** Where an `OSError` reason is rendered, the detail uses
`errno.errorcode.get(exc.errno, f"errno-{exc.errno}")`, so an unknown numeric
`errno` produces a stable string rather than a `KeyError`.

`Path.exists()`, `Path.resolve()`, `Path.is_dir()`, and `Path.is_file()` are not
used on unvalidated relative values.

### 3.6 Input failures and precedence

A required input that is missing, is a symlink, is not a regular file, or cannot
be opened, read, or decoded as UTF-8 produces exactly one `input` diagnostic
naming that path and suppresses the checks that depend on it. No input state
raises a traceback.

| Unavailable input | Suppresses |
|---|---|
| `VERSION`, or a value not matching `^\d+\.\d+\.\d+$` | `version-claim`, `changelog-release`, and the staleness comparison |
| `CHANGELOG.md` | `changelog-release` and the staleness comparison |
| `PRODUCT.md` | its own `version-claim`, `date-claim`, and `wheel-version` |
| `projects/index.md` | every project check |
| an active product document | only its own wheel scan |

Within a project: an `index-status` or `index-path` diagnostic for an entry
suppresses that entry's `overview-lifecycle`, `lifecycle-agreement`, and
`memory-completeness`. A `memory-completeness` or `input` diagnostic for
`overview.md` suppresses that project's `overview-lifecycle` and
`lifecycle-agreement`.

### 3.7 Determinism

Diagnostics are sorted by `(path, check, detail)`, each compared as a string,
before output. The public contract is the path, the stable check ID, and
deterministic text; no canonical detail template is fixed for every branch. No
wall clock, locale, `os.environ`, hash seed, or raw directory order reaches the
output, and repeated runs over an identical tree are byte-identical.

### 3.8 Wiring

`Makefile` gains

```make
memory-check:
	$(PYTHON) scripts/check_project_memory.py
```

in `.PHONY`, the `help` block, and the `check` prerequisite list after
`dossiers`. `config/repository-paths.json` gains one `entries` item
`{"path": "scripts/check_project_memory.py", "kind": "file", "category":
"structure-guard", "policy": "stable-path"}` and one `references` item
`{"source": "Makefile", "target": "scripts/check_project_memory.py"}`.

## 4. Tests

Unit tests build small synthetic trees under `--root`. **Three golden fixtures**
assert exact ordered lists of full `(path, check, detail)` triples; every other
test asserts diagnostic paths and check IDs, plus byte-identical repetition. No
test asserts a set of `(path, check)` pairs as its whole oracle, and no test or
requirement claims coverage of every resolver outcome, node type, `errno`, or
caller.

**Golden fixtures (exact ordered triples).**

| Fixture | Why it is golden |
|---|---|
| All five required memory files missing | Five diagnostics sharing a check and differing by path — proves multiplicity survives the oracle |
| The four unsafe index paths (absolute, traversal, malformed slug, symlinked target) | Each rejection reason is asserted verbatim |
| One combined tree — version drift, a stale date, a wheel literal, one unsafe path, one lifecycle disagreement | Proves the full sorted output, including cross-check ordering |

**Contractual categories** — each has at least one test, and the suite adds
nothing beyond them:

| Category | Cases |
|---|---|
| Valid fixture | clean tree → empty, exit `0` |
| Version drift | anchored token ≠ `VERSION` |
| Stale verification date | `Last verified:` earlier than the matching release |
| Missing required memory file | one absent file |
| Overview `Lifecycle status` | missing; duplicate; malformed or empty; disallowed value |
| Index `Status` | disallowed value; malformed value |
| Overview/index disagreement | valid values that differ |
| Unsafe index paths | absolute; traversal; malformed slug; symlinked target; representative missing target; representative non-directory target |
| Wheel filenames | a literal version-specific filename; one whose version equals `VERSION` |
| Canonical wheel flow | the `VERSION`-derived guide command resolves to the current `VERSION` with no literal present |
| Changelog release | no matching release; calendar-invalid matching date; older-version-only release |
| Input/read failure | representative mocked `OSError` → diagnostic, no traceback |
| Determinism | repeated output byte-identical |
| Side effects | no writes; no subprocess |
| Repository contract | the checked-in tree passes |

`tests/contract/test_project_memory_contract.py` runs the checker against this
repository requiring exit `0`, asserts the `memory-check` Makefile target and the
`config/repository-paths.json` entry and reference, and asserts the seven
lifecycle values **by name**. That by-name assertion is load-bearing:
`lifecycle-agreement` detects disagreement, not wrongness, and
`brida-model-routing` is presently wrong *consistently* — overview `active`,
index `active`, accepted `complete` — so the checker alone reports nothing for
it.

## 5. Consequences

- `make check` gains one target, so a durable-memory contradiction fails local
  validation and the release checklist can cite one command.
- The checker is a fourth `scripts/` guard alongside path, retirement, and readme
  checks, and stays smaller than any of them. No importable module gains a
  dependency on `projects/`, so `PRODUCT.md` §8 and
  `tests/unit/test_module_boundaries.py` are unaffected.
- `src/` stops being wholly excluded for one policy-text resource only: no import
  graph, schema, or packaging list changes, and
  `tests/integration/test_installed_dogfood.py` line 205 keeps passing because it
  asserts packaging membership. Hash-managed `.brichan/` state observes a changed
  resource on deliberate re-init.
- `make check` runs against the working tree as observed; no step deletes any
  generated artifact.

## Evidence

- The policy contradiction in three files:
  `src/brichan/resources/dogfood_v1/policy/operating-principles.md` lines 10–12;
  `bootstrap.md`, unqualified; `CHANGELOG.md` `[0.11.0]` lines 14–24.
  `PRODUCT.md` lines 3–10 give runtime policy precedence, which is why §1.1
  precedes §1.2.
- `tests/contract/test_dogfood_policy_contract.py` lines 27–43 pin the packaged
  principles today; `tests/integration/test_installed_dogfood.py` line 205
  asserts packaging membership only; no test pins a golden policy hash — so
  exactly one existing test file changes.
- The checked-in `CHANGELOG.md` opens with `## [Unreleased]` (undated) followed by
  `## [0.11.0] - 2026-08-03` while `VERSION` contains `0.11.0`, so a valid
  matching release exists today and supplies the 2026-08-03 lower bound §2.2's
  `Last updated: 2026-08-09` satisfies — and the older-version-only and
  calendar-invalid cases must be constructed as fixtures.
- Lifecycle coordinates: `projects/index.md` lines 24, 29, 34;
  `projects/brida-workflow-evaluation/overview.md` line 7 and
  `projects/brida-model-routing/overview.md` line 7; the title-then-`## Objective`
  opening of `projects/brida-claude-code-support/overview.md` and
  `projects/brida-repository-structure-refactor/overview.md`; and canonical
  `Memory:` values with terminal slashes at lines 6, 11, 16, 21, 26, 31, 36 —
  §2.1's seven edits in five files and §3.3's grammar.
- `VERSION` = `0.11.0` against `PRODUCT.md` line 12 and line 202;
  `handoffs/PYPI-001/release-checklist.md` lines 3–8;
  `docs/guides/installable-dogfood.md` line 67, the only `brichan-X.Y.Z` token
  under `docs/`, `README.md`, `PRODUCT.md`, `CONTRIBUTING.md`, or `packaging/` —
  which is why §3.2's eight-document list suffices.
- `projects/brida-installable-tool/current-state.md` is 139 lines against the
  80-line target in `docs/policy/memory-policy.md` and names
  `scripts/install-brida` (lines 58, 127) though only `scripts/install-brichan`
  exists; `decisions.md` lines 5 and 34 show the supersede pattern §2.2 follows.
- `src/brichan/contracts/task_dossier/validation.py` lines 766–790 is the
  in-repository precedent for §3.5's lexical-plus-`lstat` walk;
  `scripts/check_repository_paths.py` lines 176–200 for §3.1's exit contract; and
  `config/repository-paths.json`'s existing `Makefile` pairings for §3.8.

## Uncertainty

- Narrowing trades coverage for correctness of the contract. Nothing now
  mechanically prevents `scripts/install-brida` from reappearing in
  `current-state.md`, and an unindexed project directory produces no diagnostic.
  Both were planner additions rather than accepted requirements; both are now
  open risks.
- §3.5's outcome model is deterministic by construction but is not proven by
  fixture for every node type or `errno`. The design says so rather than claiming
  otherwise, which is the substance of the version 5 H1 closure.
- The packaged-policy repair ships with no version bump and no `CHANGELOG.md`
  entry, both excluded here.
- `date-claim` staleness has a lower bound only.
- `lifecycle-agreement` is blind to a consistently-wrong pair;
  `brida-model-routing` is that case today, so §4's by-name contract assertion is
  what covers it.
- Two of the seven §2.1 lifecycle values are the coordinator's determination;
  both projects still hold handoff directories.
- Whether the repository is public is not asserted and is not checked.
