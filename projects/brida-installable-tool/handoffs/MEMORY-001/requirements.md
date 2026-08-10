# Requirements

Verifiable requirements and acceptance criteria derived from the recorded request.

## Artifact metadata

- Task ID: `MEMORY-001`
- Task level: `2`
- Artifact: `requirements`
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

Version 6 closes the version 5 findings by **narrowing the checker to the
accepted scope** and proving it with representative evidence, rather than by
adding more specification. Versions 3 through 5 grew a general path-and-input
subsystem, a 104-case matrix, and an every-outcome/every-caller totality claim
that the accepted objective never asked for — and each review found another
corner of that self-imposed surface undefined. The checker now validates six
things and nothing else. The repair scope is unchanged.

## Finding disposition

| Finding | Raised in | Status |
|---|---|---|
| v1 H1 — seven-project lifecycle omitted | plan-review v1 | Closed in v2 |
| v1 M1 — symlink-following declared paths | plan-review v1 | Closed in v3 |
| v1 M3 — unauthorized sdist arm | plan-review v1 | Closed in v2; the sdist rule stays out of scope in v6 |
| v2 H1 — canonical slash; follow-capable root scan | plan-review v2 | Closed in v3 |
| v2 M2 — seven edits / five files | plan-review v2 | Closed in v3 |
| v3 H1 — PRODUCT contradicted an excluded packaged policy | plan-review v3 | Closed in v4 |
| **v4 M2** — conflicting `changelog-release` triggers | **plan-review v4** | Closed in v5; retained in v6 (R7). *Version 5's table named plan-review v5 for this row; that was the L1 provenance error and it is corrected here.* |
| v1 M2, v2 M1, v3 M1, v4 H1, v4 M1 — the diagnostic-completeness thread | plan-review v1–v4 | **Closed in v6 by narrowing**: the checker no longer owns a general read-input subsystem, so there is no open-ended set of states to enumerate |
| **v5 H1** — the 104-case matrix cannot satisfy its every-caller/every-outcome criterion | plan-review v5 | **Closed** — that criterion and that matrix are removed. R21 replaces them with the contractual test categories in R22 |
| **v5 M1** — the ordered-triple oracle lacks exact expected details everywhere | plan-review v5 | **Closed** — R20 keeps exact ordered triples for three named golden fixtures and asserts path plus check ID and deterministic repetition elsewhere. No canonical detail template is claimed for every branch |
| **v5 M2** — unknown numeric `errno` escapes normalization | plan-review v5 | **Closed** — R14 mandates `errno.errorcode.get(...)` with a deterministic numeric fallback |
| **v5 M3** — calendar-invalid matching changelog date is an unowned parse state | plan-review v5 | **Closed** — R7: a matching heading whose date is not a real calendar date counts as **no valid matching release** and emits `changelog-release` |
| **v5 L1** — wrong provenance in one disposition row | plan-review v5 | **Closed** — corrected above |

## Requirements

### A. Product-document truth (`PRODUCT.md`)

- **R1 — version currency.** The `Last verified:` line states an ISO date and a
  package version equal to `VERSION`. Today `VERSION` is `0.11.0` and
  `PRODUCT.md` line 12 claims `0.5.0`.
- **R2 — publication status.** Section 10 no longer asserts "**Nothing is
  published yet.**" (line 202). It states that the `brichan` distribution is
  published on PyPI, that a `vX.Y.Z` tag push triggers
  `.github/workflows/publish.yml`, and that the first fully automated publish was
  `v0.9.0` on 2026-08-03. The "Next, in order" list keeps only outstanding work.
- **R3 — delegation contract, described accurately.** `PRODUCT.md` states that
  checkout mode retains discretionary delegation
  (`docs/policy/operating-principles.md` §2) while installed-project mode
  mandates the full `plan` → `implement` → independent `review` worker lifecycle
  for every repository-changing task, with no bounded-edit exception. This must
  be true of the repaired packaged policy (R4): `PRODUCT.md` lines 3–10 make it
  descriptive and give runtime policy precedence.
- **R3a — dogfood-evidence honesty.** Dogfood statements record v0.11 live worker
  orchestration as *partial* evidence and keep external owner-repository dogfood
  as an unfinished gate. Runtime-native delegation remains an explicit non-goal.

### B. Canonical installed-policy consistency

- **R4 — the packaged policy states an unconditional three-phase lifecycle.**
  `src/brichan/resources/dogfood_v1/policy/operating-principles.md` item 2 loses
  its skip-plan exception (today lines 10–12: "Skip the `plan` worker only for a
  single bounded edit with obvious acceptance criteria"). All three phases become
  mandatory, and the coordinator integrates only after the independent `review`
  worker has verified. Items 1 and 3–8 are preserved byte-for-byte, and the
  sibling `bootstrap.md` — already unconditional — is not edited.
- **R5 — the existing contract test pins it.**
  `tests/contract/test_dogfood_policy_contract.py` gains assertions that all
  three phases are required and that no skip-plan exception remains, retaining
  every existing assertion. It is the only existing test file that changes:
  `tests/integration/test_installed_dogfood.py` line 205 asserts packaging
  membership, not content, and no test pins a golden policy hash.
- **R6 — one consistent phrase in durable memory.** `current-state.md` and the
  `POLICY-001` row in `tasks.md` both use **"mandatory plan/implement/review
  lifecycle"**. `CHANGELOG.md` is untouched; its `[0.11.0]` entry already
  describes the lifecycle unconditionally.

### C. What the checker validates — the complete list

The checker validates these six things and nothing else.

- **R7 — product version and verification date.**
  1. Every anchored package-version token in `PRODUCT.md` equals the contents of
     `VERSION`. Two anchored forms are matched:
     `\(package version (\d+\.\d+\.\d+)\)` and
     `^Latest published version: (\d+\.\d+\.\d+)\s*$`. A bare `X.Y.Z` in prose is
     not matched. Disagreement → `version-claim`.
  2. `PRODUCT.md`'s `Last verified:` date is not older than the date of the
     `CHANGELOG.md` heading matching
     `^## \[<VERSION>\] - (?P<date>\d{4}-\d{2}-\d{2})$`, where `<VERSION>` is the
     parsed contents of `VERSION`. Staleness → `date-claim`; an unparseable
     `Last verified:` token → `date-claim`.
  3. **No valid matching release → `changelog-release`.** This covers three
     states, identically: no heading for the parsed version at all; only a
     heading for a different version, such as `0.10.0` when `VERSION` is
     `0.11.0`; and a heading whose date matches the digit shape but is not a real
     calendar date, such as `2026-02-30`. In every case the staleness comparison
     is suppressed and nothing else is.
- **R8 — index entries.** For each real entry in `projects/index.md`:
  1. it declares a `- Status:` whose value is in
     `{proposed, active, blocked, paused, complete, archived}`; a missing,
     empty, malformed, or out-of-enum value → `index-status`;
  2. its `- Memory:` value matches, in full,
     `^projects/(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)/$`; any other value —
     absolute, traversal, tilde, backslash, extra or missing terminal slash,
     interior double slash, malformed slug, missing field — → `index-path`;
  3. after that grammar passes, exactly one terminal slash is removed and the
     result resolves, component-wise and without following any link, to an
     existing directory that is not a symlink. Anything else → `index-path`.

  The `## Entry template` section and fenced blocks are not entries.
- **R9 — overview lifecycle.** Each indexed `projects/<slug>/overview.md`
  contains exactly one line matching `^- Lifecycle status: (?P<value>.+)$` whose
  value — bare or wrapped in one pair of single backticks — is in the R8 enum.
  Zero, two or more, empty, or out-of-enum → `overview-lifecycle`. When exactly
  one valid value exists, it must equal that project's index `Status`;
  disagreement → `lifecycle-agreement`.
- **R10 — required memory files.** Each indexed project directory contains
  `overview.md`, `current-state.md`, `tasks.md`, `decisions.md`, and
  `references.md`, each resolving to an existing regular file that is not a
  symlink. Anything else → `memory-completeness`.
- **R11 — wheel filenames.** No document in the explicit active-product list
  contains a literal version-specific wheel filename matching
  `brichan-\d+\.\d+\.\d+-\S*\.whl`. Any match → `wheel-version`, whether or not
  the version equals `VERSION`. Source distributions are **not** checked.

**Explicitly out of scope**, and removed from earlier versions: unindexed-project
detection; validation of backticked repository paths inside `current-state.md`;
any sdist filename rule; any repository-wide or `docs/**` Markdown scan; and any
generic, externally configurable declared-path subsystem.

### D. Checker implementation contract

- **R12 — fixed constants, no external configuration.** Repository-relative
  constants for `VERSION`, `CHANGELOG.md`, `PRODUCT.md`, `projects/index.md`, the
  five required memory filenames, and a small explicit active-product-document
  list that includes at least `PRODUCT.md` and
  `docs/guides/installable-dogfood.md`. The full list is in `design.md` §3.2.
  There is no config file, no glob, and no injectable declared-path set.
- **R13 — input failures.** A required checker input that is missing, is a
  symlink, is not a regular file, or cannot be opened, read, or decoded as UTF-8
  produces **exactly one** deterministic file-specific `input` diagnostic naming
  that path, and suppresses the checks that depend on it. `VERSION` unavailable
  or not matching `^\d+\.\d+\.\d+$` suppresses `version-claim`,
  `changelog-release`, and the staleness comparison. `CHANGELOG.md` unavailable
  suppresses `changelog-release` and staleness. `projects/index.md` unavailable
  suppresses every project check. An unavailable active document suppresses only
  its own wheel scan. **No input state raises a traceback.**
- **R14 — path resolution and the internal outcome model.** Index `Memory:`
  targets and required memory files are resolved component-wise with `lstat`,
  never following a link. A small internal outcome model may be used — safe,
  missing, symlink, directory, regular file, other — but **no claim is made that
  every filesystem node type, every `errno`, or every caller combination is
  exhaustively tested.** Where an `OSError` is reported, its detail uses
  `errno.errorcode.get(exc.errno, ...)` with a deterministic numeric fallback, so
  an unknown numeric `errno` yields a stable string rather than a `KeyError`.
- **R15 — determinism and the public contract.** Diagnostics are sorted by
  `(repository-relative POSIX path, check ID, detail)`, each compared as a
  string. The public contract is the **path**, the **stable check ID**, and
  **deterministic text**; no canonical detail template is required for every
  branch. Repeated runs over an identical tree produce byte-identical stdout and
  stderr.
- **R16 — check IDs.** Exactly these exist: `version-claim`, `date-claim`,
  `changelog-release`, `index-status`, `index-path`, `overview-lifecycle`,
  `lifecycle-agreement`, `memory-completeness`, `wheel-version`, `input`.
- **R17 — precedence.** An `index-status` or `index-path` diagnostic for an entry
  suppresses that entry's downstream `overview-lifecycle`,
  `lifecycle-agreement`, and `memory-completeness` checks. A `memory-completeness`
  or `input` diagnostic for `overview.md` suppresses that project's
  `overview-lifecycle` and `lifecycle-agreement`.
- **R18 — CLI and behaviour.** `python3 scripts/check_project_memory.py
  [--root PATH]`. Exit `0` when no diagnostic is produced, with one stdout
  summary line; exit `1` otherwise, with diagnostics on stderr. No other exit
  code. Read-only, offline, no subprocess, standard library only, Python 3.10+.

### E. Durable memory, guide, and checklist repairs

- **R19 — lifecycle reconciliation.** Seven edits across **five changed files**:
  overview line 7 `active` → `complete` in `brida-workflow-evaluation` and
  `brida-model-routing`; a new `- Lifecycle status: active` in
  `brida-claude-code-support` and `- Lifecycle status: complete` in
  `brida-repository-structure-refactor`, each inserted as a single-line block
  after the title; and `projects/index.md` line 24 `active` → `complete`,
  line 29 `active` → `complete`, line 34 `proposed` → `active`. The target values
  are `brida-installable-tool` `active`, `brida-system-validation` `complete`,
  `brida-workflow-evaluation` `complete`, `brida-claude-code-support` `active`,
  `brida-repository-structure-refactor` `complete`, `brida-model-routing`
  `complete`, `brida-task-dossier-workflow` `active`. The three already-correct
  overviews and the four already-correct index `- Status:` lines stay
  byte-identical.
- **R19a — installable-tool memory.** `current-state.md` is replaced (≤ 80 lines
  per `docs/policy/memory-policy.md`, `Last updated: 2026-08-09`, no
  `.brida/` / `brida init` / `BRIDA_ROOT` / `scripts/install-brida`);
  `decisions.md` gains one appended superseding rename entry and the 2026-07-29
  entry is marked `superseded` without rewriting its body; `tasks.md` gains the
  MEMORY-001 Active row and four Completed rows (`PYPI-002`, `RENAME-001`,
  `INIT-001`, `POLICY-001`); `references.md`'s "Current public setup" row and its
  `scripts/install-brida` pointer are corrected. `CHANGELOG.md`,
  `projects/*/handoffs/`, `evals/`, and previously completed task rows are
  untouched.
- **R19b — guide and checklist.** `docs/guides/installable-dogfood.md` line 67
  derives the wheel filename from `VERSION` instead of embedding
  `brichan-0.5.0-py3-none-any.whl`. `handoffs/PYPI-001/release-checklist.md`
  gains one per-release step, before the tag-push step, reconciling `PRODUCT.md`,
  `current-state.md`, the seven overview lifecycle values, and
  `projects/index.md`, then running `make memory-check`.

### F. Wiring, tests, and bounds

- **R20 — the test oracle, proportionate.** Three **golden fixtures** assert
  exact ordered lists of full `(path, check, detail)` triples: the
  multiple-diagnostic fixture (all five required memory files missing), the
  unsafe-index-path fixture set (each rejection reason asserted verbatim), and
  one combined fixture. Every other test asserts the diagnostic **paths and check
  IDs** plus byte-identical repetition. No canonical detail text is claimed for
  every branch, and no test asserts a set of `(path, check)` pairs as its whole
  oracle.
- **R21 — no totality claims.** No requirement, design statement, or acceptance
  criterion asserts that every resolver outcome, every `errno`, every node type,
  or every caller combination is covered by a fixture. Coverage is the
  contractual categories in R22 and nothing more.
- **R22 — required test categories, no more and no less.** Valid fixture;
  version drift; stale verification date; missing required memory file; missing,
  duplicate, malformed-or-empty, and disallowed overview `Lifecycle status`;
  disallowed and malformed index `Status`; overview/index disagreement; unsafe
  index paths — absolute, traversal, malformed slug, symlinked target — plus a
  representative missing target and a representative non-directory target;
  hardcoded version-specific wheel filename, including one whose version equals
  `VERSION`; the canonical `VERSION`-derived wheel guide flow resolving to the
  current `VERSION` without a literal; invalid or missing matching changelog
  release, including a calendar-invalid date and an older-version-only release;
  an input/read failure returning a diagnostic without a traceback via a
  representative mocked `OSError`; repeated output byte-identical; no writes and
  no subprocess; and the checked-in repository passing the contract.
- **R23 — Makefile and manifest.** `make memory-check` runs the checker and joins
  the `check` prerequisite list; `config/repository-paths.json` gains an
  `entries` item for `scripts/check_project_memory.py` (category
  `structure-guard`, policy `stable-path`) and a `references` item
  `{Makefile → scripts/check_project_memory.py}`.
- **R24 — bounded change surface.** No change to `src/` **except**
  `src/brichan/resources/dogfood_v1/policy/operating-principles.md`. No change to
  any other packaged resource, `config/model-routing.json`, the receipt or
  task-dossier validators, `VERSION`, `pyproject.toml`, or released
  `CHANGELOG.md` entries. No version bump, tag, push, PR, publish, network
  access, secret access, permission broadening, or remote state change.
- **R25 — no artifact deletion.** `make check` runs against the working tree as
  observed. No deletion of `dist/`, `build/`, `src/brichan.egg-info/`, or any
  other generated artifact is authorized; a pre-existing artifact causing a
  failure is reported with output and attributed as pre-existing and unrelated.

## Acceptance criteria

1. The packaged policy contains no skip-plan exception, requires all three
   phases, and is otherwise byte-identical; `bootstrap.md` is unchanged;
   `tests/contract/test_dogfood_policy_contract.py` proves both and passes; no
   other existing test file changed; the policy repair preceded the `PRODUCT.md`
   edit.
2. `PRODUCT.md`, `current-state.md`, `decisions.md`, `tasks.md`,
   `references.md`, `projects/index.md`, the four overviews, the dogfood guide,
   and the release checklist match R1–R3a and R19–R19b. `current-state.md` and
   the `POLICY-001` row both read "mandatory plan/implement/review lifecycle";
   `CHANGELOG.md` is unchanged.
3. The seven lifecycle edits land in exactly five changed files, with the three
   already-correct overviews and four already-correct index `- Status:` lines
   byte-identical.
4. The checker implements R7–R11 and nothing else; the removed subsystems are
   absent from the source.
5. `python3 scripts/check_project_memory.py` exits `0` on the repaired tree, and
   `--root PATH` runs it against a fixture tree.
6. Every category in R22 has at least one passing test; the three R20 golden
   fixtures assert exact ordered triples; no test asserts a pair set as its whole
   oracle.
7. No input state produces a traceback, and an injected unknown numeric `errno`
   yields a stable deterministic string.
8. `make memory-check`, `make path-check`, `make test-contract`, and `make check`
   pass on observed current state; unrelated pre-existing failures are reported,
   not repaired and not deleted.
9. A fresh independent reviewer returns `PASS` on plan version 6.

## Evidence

- The canonical policy contradiction, in three files:
  `src/brichan/resources/dogfood_v1/policy/operating-principles.md` lines 10–12
  hold the skip-plan exception; `bootstrap.md` states the lifecycle
  unconditionally; `CHANGELOG.md` `[0.11.0]` lines 14–24 published it
  unconditionally. `PRODUCT.md` lines 3–10 give runtime policy precedence, which
  is why R3 depends on R4.
- `tests/contract/test_dogfood_policy_contract.py` lines 27–43 already pin the
  three phase words and the coordinator write boundary — where R5's assertions
  belong; `tests/integration/test_installed_dogfood.py` line 205 asserts
  packaging membership only, and no test pins a golden policy hash.
- The checked-in `CHANGELOG.md` opens with `## [Unreleased]` (undated) followed
  by `## [0.11.0] - 2026-08-03`, and `VERSION` contains `0.11.0`, so a valid
  matching release exists today and supplies 2026-08-03 as the R7 lower bound —
  which is why R19a's `Last updated: 2026-08-09` satisfies it and why the
  older-version-only and calendar-invalid cases must be constructed as fixtures.
- Lifecycle drift, file by file: `projects/index.md` lines 24, 29, 34 (`active`,
  `active`, `proposed`); `projects/brida-workflow-evaluation/overview.md` line 7
  and `projects/brida-model-routing/overview.md` line 7 (both `active`); and no
  lifecycle field in `projects/brida-claude-code-support/overview.md` or
  `projects/brida-repository-structure-refactor/overview.md`, each opening with a
  `#` title on line 1 and `## Objective` on line 3 — R19's seven edits in five
  files. Every index `Memory:` value carries the canonical terminal slash
  (lines 6, 11, 16, 21, 26, 31, 36), the basis for R8.
- `VERSION` = `0.11.0` against `PRODUCT.md` line 12 (`package version 0.5.0`) and
  line 202 ("**Nothing is published yet.**"), while
  `handoffs/PYPI-001/release-checklist.md` lines 3–8 record publication with
  Trusted Publishing since `v0.9.0`.
- `docs/guides/installable-dogfood.md` line 67 installs
  `brichan-0.5.0-py3-none-any.whl` and is the only version-specific
  `brichan-X.Y.Z` token under `docs/`, `README.md`, `PRODUCT.md`,
  `CONTRIBUTING.md`, or `packaging/` — which is why R12's small explicit list is
  sufficient and a repository-wide scan is unnecessary.
- `projects/brida-installable-tool/current-state.md` is 139 lines against the
  80-line target in `docs/policy/memory-policy.md` and names
  `scripts/install-brida` (lines 58, 127) though only `scripts/install-brichan`
  exists; `decisions.md` lines 5 and 34 show the supersede pattern R19a follows.
- `src/brichan/contracts/task_dossier/validation.py` lines 766–790
  (`_is_safe_relative`; `_symlinked_ancestor` walking components with
  `is_symlink()` and never following) is the in-repository precedent for R14;
  `scripts/check_repository_paths.py` lines 176–200 is the precedent for R18's
  exit contract; `config/repository-paths.json` already pairs `Makefile` with
  `scripts/check_repository_paths.py`, establishing R23's convention.

## Uncertainty

- Narrowing is a trade. Dropping the backticked-path validator means nothing
  mechanically prevents `scripts/install-brida` from reappearing in
  `current-state.md` after this repair fixes it; dropping unindexed-project
  detection means a new project directory can exist unindexed without a
  diagnostic. Both were planner additions, not accepted requirements, and both
  are now open risks rather than covered ones.
- R21 removes the totality claim rather than satisfying it. The checker's
  behaviour on an exotic node type or an unusual `errno` is deterministic by
  construction (R14) but is not proven by fixture for every case, and the
  requirements no longer pretend otherwise.
- The packaged-policy repair changes a shipped resource with no version bump and
  no `CHANGELOG.md` entry, both excluded here; hash-managed `.brichan/` state
  will observe a changed resource on deliberate re-init. Whether to bundle it
  into a `0.11.1` release is a coordinator decision.
- `date-claim` staleness has a lower bound only; a future-dated `Last verified:`
  is not detected without reading the wall clock.
- `lifecycle-agreement` detects disagreement, not wrongness.
  `brida-model-routing` is presently wrong *consistently* (overview `active`,
  index `active`, accepted `complete`), so the checker alone reports nothing for
  it; only the contract test's by-name assertion of the seven R19 values catches
  it.
- Two of the seven R19 values — `brida-repository-structure-refactor` and
  `brida-model-routing` as `complete` — are the coordinator's determination, not
  facts derived here; both projects still hold handoff directories.
- Whether the GitHub repository is now public cannot be verified locally and this
  task is offline; the repair asserts distribution publication only.
