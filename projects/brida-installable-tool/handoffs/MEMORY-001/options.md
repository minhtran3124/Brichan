# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `MEMORY-001`
- Task level: `2`
- Artifact: `options`
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

Seven decisions carry into the implementation: **D1-A** a standalone `scripts/`
checker with fixed constants; **D2-A** repair the canonical packaged installed
policy at source rather than qualifying `PRODUCT.md`; **D3-A** a dedicated
`- Lifecycle status:` field in every overview compared against the index;
**D4-A** an appended superseding rename decision; **D5-A** narrow the checker to
six accepted validations; **D6-A** a proportionate test oracle — exact ordered
triples for three golden fixtures, paths and check IDs elsewhere; and **D7-A**
the matching-current-version changelog trigger, with a calendar-invalid date
counting as no valid matching release.

## Version 6 amendments

D5, D6, and D7 are the decisions this version turns on. D5 is new and reverses a
series of planner-added scope decisions from versions 3–5; D6 replaces the
"exact ordered triples everywhere" choice; D7 is retained from version 5 with one
addition. Earlier options that justified only now-removed scope — declared
document sets beyond a fixed list, the declared-path gate, the seven-outcome
resolver totality, and diagnostic-precedence variants for subsystems that no
longer exist — are deleted rather than carried as history.

## D1 — Where the gate lives

**D1-A — standalone `scripts/check_project_memory.py` with fixed constants
(selected).** One new file, matching `scripts/check_repository_paths.py` and
`scripts/check_compatibility_retirement.py`, and honouring the `PRODUCT.md` §8
rule that importable modules must not depend on `projects/`. Constants live in
the module; `--root PATH` lets tests point it at a fixture tree without any
configuration surface.

Rejected: **D1-B** a JSON manifest plus thin script — adds an artifact, a schema,
and a malformed-manifest failure mode for a fixed four-path, eight-document set;
**D1-C** extending `check_repository_paths.py` — one script owning two unrelated
contracts makes a failure message ambiguous; **D1-D** a contract test with no
script — not runnable as a release step and not citable by the release checklist.

## D2 — How the installed-mode mandate is made true

**D2-A — repair the canonical packaged policy at source (selected).** Remove the
skip-plan exception from
`src/brichan/resources/dogfood_v1/policy/operating-principles.md`, extend the one
contract test that pins the resource, and only then let `PRODUCT.md` describe it.
`PRODUCT.md` lines 3–10 make it descriptive and give runtime policy precedence,
so a `PRODUCT.md` statement about installed mode is true only if the packaged
policy says the same thing. The repair also resolves an existing internal
contradiction — `bootstrap.md` already states the lifecycle unconditionally, and
`CHANGELOG.md` `[0.11.0]` published it that way.

Rejected: **D2-B** qualifying `PRODUCT.md` to match the exception — silently
weakens the accepted user intent, which only the user may revise, and leaves
`PRODUCT.md` contradicting `bootstrap.md` and the published changelog;
**D2-C** recording the conflict and changing nothing — the task exists to remove
exactly this class of unrecorded contradiction; **D2-D** also rewriting
`bootstrap.md` for symmetry — it is already correct, and byte identity there is
cheap evidence the repair was surgical.

## D3 — How lifecycle state becomes machine-readable

**D3-A — one `- Lifecycle status:` field per overview, compared against the index
(selected).** Five of the seven overviews already carry this exact field, so the
grammar is observed rather than invented and the repair is four edits instead of
seven rewrites. The duplication across two files is deliberate:
`lifecycle-agreement` is what converts it into a cross-check.

Rejected: **D3-B** index-only with prose overviews — discards a field five
overviews already have and leaves the primary read surface silent, the condition
that produced this defect; **D3-C** overview-only with a derived index — requires
generation tooling this task has not sized; **D3-D** YAML/TOML front matter — a
second document grammar and a parser for one enum, against the no-dependency
constraint.

## D4 — How the completed rename is recorded

**D4-A — append a superseding decision; mark the prior entry `superseded`
(selected).** `docs/policy/memory-policy.md` makes `decisions.md` append-only,
and the file already demonstrates the pattern at lines 5 and 34.

Rejected: **D4-B** editing the 2026-07-29 entry in place — destroys the record of
a decision that was correct when taken; **D4-C** renaming the `projects/brida-*`
directories — breaks every recorded receipt path and manifest entry, and is
explicitly out of scope.

## D5 — How much the checker validates (the version 6 decision)

### D5-A — Exactly the six accepted validations (selected)

Product version; product verification date against the matching changelog
release; index entry status and safe canonical path; overview lifecycle and its
agreement with the index; required memory files; wheel filenames in a short
explicit document list. Nothing else.

- **For.** It is what the accepted objective asked for, and it is small enough to
  specify completely. The removed subsystems — unindexed-project detection, the
  backticked-path validator, the sdist rule, the `docs/**` scan, and the
  configurable declared-path set — were planner additions, and each dragged in
  states nobody had scoped: three consecutive reviews were spent defining
  behaviour for filesystem node types and `errno` values that the accepted checks
  never needed to distinguish. A contract that can be stated completely can be
  reviewed completely.
- **Against.** Real coverage is lost. Nothing now prevents
  `scripts/install-brida` from reappearing in `current-state.md` after this
  repair fixes it, and a new unindexed project directory produces no diagnostic.
  Those are genuine regressions against version 5's scope, recorded as open risks
  rather than hidden.

### D5-B — Keep the version 5 scope and finish specifying it (rejected)

- **For.** Broader drift coverage, and the extra checks were individually
  defensible.
- **Against.** Each review round closed one corner and revealed another; the
  subsystem's state space is larger than the problem it guards. Continuing costs
  more review than the additional coverage is worth, and the accepted objective
  never requested it.

### D5-C — Narrow now, restore the extra checks in a follow-up task (not this plan's call)

- **For.** Keeps the lost coverage on the roadmap with its own scope and review.
- **Against.** Nothing to decide here — it is the coordinator's choice once
  version 6 lands. Recording it means the removed checks are a deferral, not a
  judgement that they were worthless.

## D6 — What the tests assert

### D6-A — Exact ordered triples for three golden fixtures, paths and check IDs elsewhere (selected)

The golden fixtures are the multiple-diagnostic case (all five required memory
files missing), the unsafe-index-path set (each rejection reason verbatim), and
one combined tree.

- **For.** The three golden fixtures cover exactly what a weaker oracle cannot
  see: multiplicity when diagnostics share a check, the reason text for each path
  rejection, and cross-check sort order. Everywhere else, asserting paths plus
  check IDs and byte-identical repetition proves the contract that matters
  without freezing every detail string into the suite.
- **Against.** A detail-text regression outside the golden fixtures is not
  caught. Accepted: detail text is documented as deterministic, not as a
  canonical template.

### D6-B — Exact ordered triples for every fixture (version 5's choice; rejected)

- **For.** Maximum precision.
- **Against.** It requires a canonical detail string for every branch. Version 5
  asserted that oracle without supplying those strings, which is the substance of
  the v5 M1 finding — the oracle was stronger than the specification behind it.

### D6-C — Set of `(path, check)` pairs everywhere (rejected)

- **Against.** Collapses diagnostics that share a path and a check and cannot
  verify a rejection reason. Version 4's review established this concretely.

## D7 — When `changelog-release` fires

### D7-A — The dated heading whose bracketed version equals parsed `VERSION`, with calendar validity required (selected)

`VERSION` is parsed first. The matching release supplies the staleness lower
bound. Three states count identically as *no valid matching release*, each
emitting exactly one `changelog-release`: no heading for the parsed version; only
a heading for a different version; and a matching heading whose date is
digit-shaped but not a real calendar date.

- **For.** It is the accepted user contract, and the only reading under which the
  lower bound means anything — a date drawn from an older release would let a
  verification date predate the current release and still pass. Folding calendar
  validity into the same outcome closes the v5 M3 gap without inventing a new
  check ID or a new suppression rule.
- **Against.** It overlaps one fact with
  `tests/contract/test_repository_contract.py::test_version_matches_changelog` —
  that a heading for the current version exists. The overlap is bounded and
  deliberate: the checker needs the *date*, the contract test needs the
  *agreement*.

### D7-B — The first dated heading regardless of version (rejected)

- **Against.** Silently accepts a stale lower bound: with `VERSION` `0.11.0` and
  a newest dated heading of `0.10.0`, a verification date older than the current
  release passes — the drift this task exists to catch.

### D7-C — A distinct check ID for a calendar-invalid matching date (rejected)

- **For.** Distinguishes "no heading" from "bad date" in the output.
- **Against.** A second ID with its own suppression rule for a state the user
  already grouped under "invalid or missing matching changelog release". The
  detail text distinguishes them; the contract stays one rule.

## Evidence

- The D2 chain, in three files:
  `src/brichan/resources/dogfood_v1/policy/operating-principles.md` lines 10–12
  hold the skip-plan exception; `bootstrap.md` states the lifecycle
  unconditionally; `CHANGELOG.md` `[0.11.0]` lines 14–24 published it that way.
  `PRODUCT.md` lines 3–10 establish that runtime policy wins on conflict, which
  is why D2-B cannot work.
- `tests/contract/test_dogfood_policy_contract.py` lines 27–43 pin the packaged
  principles today, and `tests/integration/test_installed_dogfood.py` line 205
  asserts packaging membership only — so D2-A's test surface is exactly one file,
  and no test pins a golden policy hash.
- D3 evidence: five of seven overviews already carry `- Lifecycle status:`
  (`projects/brida-model-routing/overview.md` line 7 among them, with a
  backticked slug on line 4 that forces value normalization), while
  `projects/brida-claude-code-support/overview.md` and
  `projects/brida-repository-structure-refactor/overview.md` carry none.
- D5 and D7 scope evidence: `docs/guides/installable-dogfood.md` line 67 is the
  only `brichan-X.Y.Z` token under `docs/`, `README.md`, `PRODUCT.md`,
  `CONTRIBUTING.md`, or `packaging/`, so a fixed eight-document list suffices;
  and `CHANGELOG.md` opens with `## [Unreleased]` then
  `## [0.11.0] - 2026-08-03` while `VERSION` is `0.11.0`, so D7-A and D7-B agree
  on today's tree — which is why the older-version-only and calendar-invalid
  cases must be constructed as fixtures before the trigger can be settled.
- D6 evidence: `src/brichan/contracts/task_dossier/schema.py` defines its
  `Diagnostic` as a three-part record formatted as one line, and
  `src/brichan/contracts/task_dossier/validation.py` emits multiple diagnostics
  sharing a path and differing only in field and message — in-repository proof
  that a pair-based identity would collapse real output.
- `projects/brida-installable-tool/decisions.md` lines 5 and 34 show the
  supersede pattern D4-A follows, and lines 73–88 hold the entry it must mark.

## Uncertainty

- D5-A's cost is real and unmeasured: no one has established how often a dangling
  path or an unindexed project would actually have been caught. The decision
  rests on review economics, not on a demonstrated absence of value.
- D6-A leaves detail text outside the golden fixtures unpinned, so a wording
  regression there is invisible to the suite.
- D7-A's overlap with `test_version_matches_changelog` is bounded to one fact
  today. If that test is relaxed, `changelog-release` silently becomes the sole
  guard for it.
- D2-A lands a shipped-resource change without a version bump or changelog entry,
  both excluded from this task; hash-managed `.brichan/` state observes a changed
  resource on deliberate re-init.
- D3-A accepts deliberate duplication of lifecycle state across two files and
  relies on `lifecycle-agreement` to make it a cross-check; that check cannot
  detect a consistently-wrong pair, which `brida-model-routing` is today.
