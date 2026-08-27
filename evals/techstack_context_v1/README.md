# Techstack context evaluation v1

A frozen, mandatory evaluation of the techstack-context coordinator policy.
It is **test-only evidence**: it drives the production resolver, the production
`verify_snapshot`, and the production digest helpers, then applies this
package's own acceptance oracle. Nothing here validates production, and
`src/brichan` never imports `evals`.

## Command

```
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest evals.techstack_context_v1.test_cases -v
```

`make techstack-eval` runs exactly that line, and `make check` runs the target.

## Corpus

`cases.json` is schema version **2** — strict duplicate-free UTF-8 JSON, at most
32,768 bytes, with exactly 12 cases. Its bytes and the bytes of all eight
fixture files are frozen by SHA-256 in `test_cases.py`; changing any of them
fails before a single case runs.

Every case carries exactly `case_id`, `fixture`, `initial`, `discovered`,
`mutation`, `acknowledged_snapshot`, `planner_reread`, and `expected`. The
`initial` and `discovered` states are separate and each carries exactly
`scope_paths`, `context_chains`, `declared_conflicts`, and `exception_mode`;
the final state is their canonical union, except that a discovered exception
mode of `none` retains the initial mode and any other mode replaces it.

The loader accepts exactly four mutations — `none`, `edit_selected_leaf`,
`remove_root`, `make_selected_leaf_stale` — three acknowledgement targets —
`none`, `initial`, `final` — three exception modes — `none`,
`needed_unapproved`, `approved` — and nine reasons: `unchanged`,
`planner_reread_required`, `stale_snapshot`, `missing_acknowledgement`,
`exception_needed`, `observed_not_applicable`, `handoff_drift`,
`conflict_unresolved`, and `approved_exception`. Any other value, any other
count, any unknown or missing key, and any over-cap array is a hard rejection.

## The 12 cases

| Case ID | Fixture | Mutation | Reread | Accepted | Reason |
| --- | --- | --- | --- | --- | --- |
| `unchanged` | base | `none` | no | yes | `unchanged` |
| `discovered-scope-reread` | base | `none` | yes | yes | `unchanged` |
| `discovered-scope-no-reread` | base | `none` | no | no | `planner_reread_required` |
| `stale-snapshot` | base | `edit_selected_leaf` | no | no | `stale_snapshot` |
| `missing-acknowledgement` | base | `none` | no | no | `missing_acknowledgement` |
| `exception-needed` | stale | `none` | no | no | `exception_needed` |
| `root-disappeared` | base | `remove_root` | no | no | `observed_not_applicable` |
| `handoff-drift` | base | `none` | no | no | `handoff_drift` |
| `discovered-conflict-no-reread` | base | `none` | no | no | `planner_reread_required` |
| `discovered-conflict-reread` | base | `none` | yes | no | `conflict_unresolved` |
| `discovered-exception-no-reread` | base | `make_selected_leaf_stale` | no | no | `planner_reread_required` |
| `discovered-exception-approved-reread` | base | `make_selected_leaf_stale` | yes | yes | `approved_exception` |

Three cases are accepted; nine are rejected.

## Fixed constants

Every case resolves under one identity: task `TECHSTACK-EVAL-001`, plan
`TECHSTACK-EVAL-PLAN-001`, plan version `1`, attempt `attempt-1`, and
`as_of: 2026-08-24`.

The `approved` mode synthesizes one approval: `approval_id`
`eval-approval-1`, `coordinator_attested: true`, `authorized_by: user`,
authorization reference `eval://techstack-context-v1/stale-rule-approved`,
authorization digest
`f872fe15b7ac69588e139fe78741c7ba0df6eefa37148f5504a4b00ddb146967`,
`issued_on: 2026-08-24`, `expires_on: 2026-09-23`, reason
`approved eval stale-rule exception`, and target `STALE_RULE/general/null`. The
window is exactly 30 days and brackets the frozen `as_of`. Its scope and
binding digests are **not** frozen: the production hash functions derive both
from the final input.

## Disposable-copy boundary

Each case copies only the eight inventoried fixture files into a fresh
temporary root outside the repository. The empty `.git` directory that makes
that copy a project root, and every JSON document, exist only there. Mutations
apply only to the copy, and each one asserts that the copied bytes really
changed: `edit_selected_leaf` changes exactly one line,
`make_selected_leaf_stale` exactly two, and a replacement whose source line
matches nothing raises instead of quietly leaving a pristine copy that would
resolve applicable. The repository fixture bytes are hashed before and after
every run and must be identical.

## Relational digest oracle

Root identity carries the real device and inode, so a Snapshot digest is not
reproducible across hosts or runs. No expected Snapshot digest is stored
anywhere; digests are checked by relation only — the acknowledged digest
against the observed one, and the observed Snapshot against the project through
`verify_snapshot`. A test scans this package for stray 64-hex literals and
fails if one appears.

The oracle checks the production statuses, selected files, and diagnostic codes
for both resolutions, the verification relation, the latest-digest
acknowledgement, and the reread policy. Its precedence is exact: a H3 trigger
exists if discovery added any path, chain, declared conflict, or non-`none`
exception mode, and that gate closes before any digest, verification, conflict,
or exception check. A case that skipped the reread therefore reports
`planner_reread_required` even when the eventual resolution would have blocked
anyway. Separately, the eval proves that the approved exception is really
consumed as a waived warning, that the acknowledgement names the latest
Snapshot, and that verification succeeds.
