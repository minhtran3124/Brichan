# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `MEMORY-001`
- Task level: `2`
- Artifact: `brief`
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

Brichan's durable documents contradict Brichan's own shipped state, and nothing
in `make check` catches that class of drift. The task is to repair the
contradictions with evidence and leave behind one small, deterministic,
read-only gate that validates six specific claims. Version 6 removes the checker
scope the planner added on top of that; the repair itself is unchanged.

## Version 6 amendments

Five reviews found defects. The first two were real gaps in the repair. The last
three were defects in a *subsystem the accepted objective never asked for*: a
general path-and-input resolver, a 104-case matrix, and a claim that every
filesystem outcome, `errno`, and caller combination was covered. Each review
correctly found another undefined corner of that surface, and each fix made the
surface larger.

Version 6 ends that by narrowing. The checker validates six things. There is no
unindexed-project detection, no backticked-path validator, no sdist rule, no
repository-wide Markdown scan, and no configurable declared-path subsystem — all
planner additions, all removed. The version 5 findings close as a consequence:
the every-outcome criterion is deleted rather than satisfied (H1), the oracle
asserts exact triples for three golden fixtures instead of claiming canonical
detail text everywhere (M1), unknown `errno` values get a total lookup (M2), and
a calendar-invalid changelog date counts as no valid matching release (M3).

## Problem

- `PRODUCT.md` — read before any architecture change — states package version
  `0.5.0` and "**Nothing is published yet.**" `VERSION` says `0.11.0`, and the
  release checklist records automated PyPI publishing since `v0.9.0`.
- The canonical packaged installed policy still permits skipping the `plan`
  worker "for a single bounded edit", while its own sibling `bootstrap.md` and
  `CHANGELOG.md` `[0.11.0]` both state the three-phase lifecycle without
  qualification. The shipped policy under-delivers what was published about it.
- Project lifecycle state is unreconciled three ways at once: two overviews say
  `active` where the accepted state is `complete`, two carry no lifecycle field
  at all, and three index entries disagree. Nothing machine-readable ties an
  overview to its index entry.
- The `brida-installable-tool` memory is an append-only diary (139 lines against
  an 80-line target) pointing at `scripts/install-brida`, `.brida/`, and
  `BRIDA_ROOT`. Four pieces of shipped work were never registered in `tasks.md`.
- `docs/guides/installable-dogfood.md` tells a user to install
  `brichan-0.5.0-py3-none-any.whl`, a file no current build produces.

## Outcome

1. The packaged installed policy mandates all three worker phases with no
   bounded-edit exception, its one contract test proves it, and `PRODUCT.md` then
   describes a contract the product actually implements.
2. `PRODUCT.md`, the seven indexed overviews, `projects/index.md`, the
   installable-tool memory files, the dogfood guide, and the release checklist
   assert only what local evidence supports on 2026-08-09, with
   `current-state.md` and the `POLICY-001` task row using one phrase —
   "mandatory plan/implement/review lifecycle".
3. Seven lifecycle edits land in five changed files, and every indexed project
   carries exactly one machine-readable `- Lifecycle status:` matching its index
   entry.
4. `scripts/check_project_memory.py` validates six things: product version
   against `VERSION`; product verification date against the changelog release
   whose version matches `VERSION`; index entry status and a safe canonical
   `projects/<slug>/` path resolving to a real non-symlink directory; overview
   lifecycle validity and agreement with the index; the five required memory
   files present as regular non-symlink files; and no literal version-specific
   wheel filename in a short explicit document list.

## Constraints

- Read-only, offline, no subprocess, standard library only, Python 3.10+;
  `python3 scripts/check_project_memory.py [--root PATH]`, exit `0` or `1` only.
- Fixed repository-relative constants — no config file, no glob, no injectable
  path set. Component-wise `lstat` with no link following.
- Deterministic sorted output. The public contract is the path, the stable check
  ID, and deterministic text; no canonical detail template for every branch, and
  no claim that every node type, `errno`, or caller is covered by a fixture.
- Recorded history is immutable: `CHANGELOG.md`, `projects/*/handoffs/`,
  `evals/`, and previously completed task rows keep their original terminology.
- No change to `src/` except the single packaged policy resource; no version
  bump, tag, push, PR, publish, network access, secret access, permission
  broadening, or deletion of generated artifacts.

## Success signal

`python3 scripts/check_project_memory.py` exits `0` on the repaired tree; every
contractual test category passes; and `PYTHONDONTWRITEBYTECODE=1 make check`
passes on observed state.

Four negative signals matter as much:

- `grep -n "Skip the\|bounded edit\|only for"` over the packaged installed policy
  must return no match.
- Reverting `- Lifecycle status: complete` to `active` in
  `projects/brida-model-routing/overview.md` must produce a
  `lifecycle-agreement` diagnostic.
- An index `Memory:` value that is absolute, traversing, malformed, or a symlink
  must produce exactly one `index-path` diagnostic naming its reason.
- `VERSION` `0.11.0` against a changelog whose only dated heading is `0.10.0`, or
  whose matching heading is dated `2026-02-30`, must produce exactly one
  `changelog-release`.

## Evidence

- `VERSION` = `0.11.0` against `PRODUCT.md` line 12 (`package version 0.5.0`) and
  line 202 ("**Nothing is published yet.**");
  `handoffs/PYPI-001/release-checklist.md` lines 3–8 record publication with
  Trusted Publishing since `v0.9.0`.
- The policy contradiction in three files:
  `src/brichan/resources/dogfood_v1/policy/operating-principles.md` lines 10–12;
  `bootstrap.md`, unqualified; `CHANGELOG.md` `[0.11.0]` lines 14–24.
- Lifecycle drift: `projects/index.md` lines 24, 29, 34 (`active`, `active`,
  `proposed`); `projects/brida-workflow-evaluation/overview.md` line 7 and
  `projects/brida-model-routing/overview.md` line 7 (both `active`); no lifecycle
  field in `projects/brida-claude-code-support/overview.md` or
  `projects/brida-repository-structure-refactor/overview.md`. Every index
  `Memory:` value carries the canonical terminal slash (lines 6, 11, 16, 21, 26,
  31, 36).
- `CHANGELOG.md` opens with `## [Unreleased]` (undated) then
  `## [0.11.0] - 2026-08-03`, so a valid matching release exists today and
  supplies the staleness lower bound the rewritten `current-state.md` must
  satisfy.
- `docs/guides/installable-dogfood.md` line 67 is the only `brichan-X.Y.Z` token
  under `docs/`, `README.md`, `PRODUCT.md`, `CONTRIBUTING.md`, or `packaging/`,
  which is why a short explicit document list suffices and a repository-wide scan
  is unnecessary.
- `src/brichan/contracts/task_dossier/validation.py` lines 766–790 already
  implement a lexical guard plus component-wise no-follow walk, so the path
  safety needs no new technique.

## Uncertainty

- Narrowing is a trade. Nothing now mechanically prevents `scripts/install-brida`
  from reappearing in `current-state.md` after this repair fixes it, and an
  unindexed project directory produces no diagnostic. Both were planner additions
  rather than accepted requirements; both are open risks the coordinator may
  reopen as separate tasks.
- The checker's behaviour on an exotic node type or an unusual `errno` is
  deterministic by construction but is not proven by fixture for every case, and
  version 6 says so rather than claiming otherwise.
- The packaged-policy repair ships with no version bump and no `CHANGELOG.md`
  entry, both excluded here; hash-managed `.brichan/` state observes a changed
  resource on deliberate re-init.
- `lifecycle-agreement` detects disagreement, not wrongness.
  `brida-model-routing` is presently wrong *consistently*, so only the contract
  test's by-name assertion of the seven accepted values catches it. Two of those
  seven values are the coordinator's determination while both projects still hold
  handoff directories.
- Repository visibility cannot be settled offline; the repair asserts
  distribution publication only.
