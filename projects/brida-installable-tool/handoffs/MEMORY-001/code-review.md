# Code review

Independent remediation review against the originating request, accepted plan,
and version-1 implementation findings.

## Artifact metadata

- Task ID: `MEMORY-001`
- Task level: `2`
- Artifact: `code-review`
- Artifact version: `2`
- Origin: `review:MEMORY-001-PLAN-v6:019fe769-cbd8-7bc3-b4fc-ec4604200b56:v2`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fe769-cbd8-7bc3-b4fc-ec4604200b56`
- Effective route: `review`
- Effective model: `gpt-5.6-sol`
- Effective effort: `max`
- Reviewing session: `019fe769-cbd8-7bc3-b4fc-ec4604200b56`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `MEMORY-001-PLAN`
- Reviewed plan version: `6`
- Review worker: `brichan-memory-001-code-review` / `w34:pB`
- Remediation implementer session: `019fe761-ed12-7560-bbdb-c388ba100c0d`

## Claim or decision

PASS. The cumulative implementation satisfies accepted plan
`MEMORY-001-PLAN` version 6. Implementer session
`019fe761-ed12-7560-bbdb-c388ba100c0d` addressed exactly the two medium and one
low findings from code-review artifact version 1, within
`scripts/check_project_memory.py` and
`tests/unit/test_check_project_memory.py`. Independent inspection, a direct
adversarial probe, 27 focused tests, and the full repository gate confirm all
three findings are closed. No new correctness, determinism, parser/path,
read-only/offline, scope, memory-accuracy, wiring, or regression issue was
found.

The product, packaged-policy, durable-memory, lifecycle, wheel-guide,
release-checklist, Makefile, and path-manifest repairs remain accurate and
bounded. The checker remains read-only, standard-library only, offline,
subprocess-free, deterministically sorted, and component-wise no-follow for
declared paths.

## Current findings by severity

### Critical

None.

### High

None.

### Medium

None.

### Low

None.

## Version 1 history and finding disposition

Artifact version 1, from reviewer session
`019fe769-cbd8-7bc3-b4fc-ec4604200b56`, returned CHANGES REQUIRED with two
medium findings and one low finding. Their complete dispositions follow.

### M1 — Closed: bad VERSION no longer suppresses CHANGELOG input availability

Version 1 found that `reader.text(CHANGELOG_FILE)` was nested under
`if version is not None`, so invalid VERSION plus unavailable CHANGELOG emitted
only the VERSION `input` diagnostic, contrary to R13.

The checker now reads/classifies the fixed changelog input unconditionally, then
performs release-date parsing only when both parsed VERSION and changelog text
are available (`scripts/check_project_memory.py:567-589`). This preserves the
required semantic suppression while independently owning the changelog input
failure.

The new regression changes VERSION to `not-a-version`, removes CHANGELOG, and
asserts the deterministic ordered path/check sequence
`CHANGELOG.md/input`, then `VERSION/input`
(`tests/unit/test_check_project_memory.py:380-388`). An independent synthetic
tree probe reproduced exactly:

```text
CHANGELOG.md: input: is missing
VERSION: input: holds 'not-a-version', which is not an X.Y.Z version
```

The probe exited without a traceback or mutation. M1 is closed.

### M2 — Closed: the wheel-flow test derives its result from the command

Version 1 found that the VERSION-derived wheel test wrote a canonical-looking
command but compared two values independent of that command, so a misspelled or
unrelated substitution path could still pass.

The test now extracts the command substitution, requires its relative input to
be exactly `VERSION`, reads that extracted path, replaces the actual command
token in memory, extracts the resulting wheel filename, and compares it with
`brichan-1.2.3-py3-none-any.whl`
(`tests/unit/test_check_project_memory.py:340-367`). It still proves the source
command contains no literal wheel version through the checker and invokes no
subprocess. M2 is closed.

### L1 — Closed: only the three named fixtures use full-triple golden oracles

Version 1 found that the unknown-errno and CLI failure tests froze complete
diagnostic details in addition to the three R20 golden fixtures.

The unknown-errno test now uses path/check identity, deterministic repetition,
and targeted properties for `errno-9876` and absence of `Traceback`, without
making the entire detail a golden template
(`tests/unit/test_check_project_memory.py:390-406`). The CLI failure test invokes
the command twice, compares complete output bytes for determinism, parses the
single diagnostic, asserts only path/check identity and a nonempty detail, and
retains exit/stream checks (`tests/unit/test_check_project_memory.py:408-437`).

A source audit found full `(path, check, detail)` list comparisons only at lines
138, 189, and 244: the required missing-memory-files, unsafe-index-path, and
combined golden fixtures. No pair-set oracle exists. L1 is closed.

## Cumulative scope and correctness assessment

- The dirty implementation surface remains the same 19 non-dossier paths: 16
  tracked changes plus the three required new checker/test files. No new
  implementation path, tracked deletion, or excluded-path change appeared
  during remediation.
- The remediation itself is confined to the two authorized paths named in the
  assignment. The checker change is the R13 input-order correction; the unit
  test changes add its regression, couple the wheel-flow assertion, and
  right-size the two non-golden oracles.
- The packaged-policy diff still changes only item 2's final mandate. Items 1
  and 3-8 remain untouched; `bootstrap.md`, `CHANGELOG.md`, `VERSION`,
  `pyproject.toml`, and `config/model-routing.json` remain unchanged.
- The seven lifecycle edits remain exactly five changed files. All seven
  overview values agree with the accepted by-name contract and index.
  `current-state.md` remains 78 lines, dated 2026-08-09, with none of the stale
  `.brida/`, `brida init`, `BRIDA_ROOT`, or `scripts/install-brida` references.
- The checker still implements only the six accepted invariant groups and ten
  check IDs. Unindexed-project detection, backticked-path validation, sdists,
  broad Markdown scanning, and configurable declared paths remain absent.
- Component-wise `lstat`, symlink rejection, UTF-8/OSError normalization,
  deterministic `(path, check, detail)` ordering, fixed inputs, Reader caching,
  and exit 0/1 behavior remain correct. No write or subprocess operation is
  reachable from the checker.

## Commands and evidence checked

- `git status --short --branch`, `git diff --name-status`, and
  `git ls-files --others --exclude-standard` — implementation paths remained
  within plan version 6; no tracked deletion was present.
- `git diff --check` — passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_project_memory.py` — exited 0
  with `project memory consistent: 7 indexed projects, 8 active documents`.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
  tests.unit.test_check_project_memory
  tests.contract.test_project_memory_contract
  tests.contract.test_dogfood_policy_contract -v` — 27 tests passed.
- Independent invalid-VERSION/missing-CHANGELOG synthetic-tree probe — emitted
  the two expected sorted `input` diagnostics, byte-stably and without a
  traceback.
- `PYTHONDONTWRITEBYTECODE=1 make memory-check` — passed.
- `PYTHONDONTWRITEBYTECODE=1 make path-check` — passed with 77 entries and 65
  references.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_handoff_receipts.py
  projects` — 45 receipts validated.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py projects`
  — six dossiers validated before this artifact advanced from version 1 to 2.
- `PYTHONDONTWRITEBYTECODE=1 make check` — passed, including 400 unit, 79
  contract, and 90 integration tests plus metrics, receipts, dossiers, memory,
  paths, README, retirement, package imports, and shell validation.

## Coordinator-owned lifecycle state

The interim receipt-enum issue recorded in artifact version 1 remains resolved
and is not an implementation finding. Before this version-2 artifact was
written, receipt validation, dossier validation, and full `make check` were
green. The receipt and active task row still describe remediation/re-review as
active and retain the earlier observed 26-focused/399-unit counts; those are
historically true pre-remediation observations. Projecting this PASS, current
27-focused/400-unit evidence, final task state, and cleanup belongs to the
coordinator and is outside this reviewer's exclusive write authority.

## Test gaps and residual risks

- No accepted plan-v6 test category remains missing. The three golden fixtures
  are exact full triples; all other diagnostic identities use paths/check IDs
  with deterministic repetition and only targeted detail properties where the
  contract requires them.
- As explicitly accepted in plan v6, the checker does not detect unindexed
  project directories, stale backticked repository paths, or
  source-distribution filenames.
- Path classification and subsequent reads are separate operations, so an
  unrelated process can replace a file between them. Descriptor-relative
  atomic traversal was outside the accepted local consistency threat model.
- The packaged-policy correction remains unreleased without a version bump or
  changelog entry, as expressly excluded. Deliberate re-init will observe its
  changed managed-resource hash.
- Date staleness has only the matching-release lower bound; future-dated
  verification claims remain outside scope.

## Required decisions

None for implementation acceptance. The coordinator may finalize the canonical
receipt, project task state, dossier projection, metrics if applicable, and
Brichan-owned pane cleanup using this PASS evidence. No remote or release action
is authorized.

## Evidence

- Accepted contract evidence: `requirements.md` R13 and R20-R22, `design.md`
  sections 3.6-3.7 and 4, and `plan.md` steps 6-7 and acceptance criteria 7-10.
- Initial-review evidence: code-review artifact version 1's M1, M2, and L1
  reproductions, exact file/line evidence, focused/full results, and residual
  risk assessment, all retained above with dispositions.
- Remediation evidence: cumulative source inspection of the checker and unit
  tests, direct M1 adversarial output, exact-golden source audit, 27 focused
  tests, and the green 400/79/90 full gate.
- Scope evidence: unchanged 19-path implementation set, no tracked deletion,
  unchanged excluded files, and passing path, receipt, dossier, and complete
  repository validators.

## Uncertainty

- No network access was used. PyPI availability and repository visibility were
  not independently reverified; the accepted local release checklist, tags,
  workflow, and durable memory remain the evidence for those claims.
- Exotic filesystem node types and every possible errno/caller combination
  were not exercised, consistent with R21's explicit non-totality bound.
- No uncertainty remains about the M1, M2, or L1 disposition or the PASS verdict
  against accepted plan version 6.
