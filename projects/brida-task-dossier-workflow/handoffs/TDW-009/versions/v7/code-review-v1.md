# Code review

Independent review of the implementation, or the recorded evidence for why no implementation review applies.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `code-review`
- Artifact version: `1`
- Origin: `review:projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md@TDW-009-P7-v7+implementation-delta`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fc201-6e8c-7ed1-9ae4-7f807c954c51`
- Effective route: `review`
- Effective model: `gpt-5.6-sol`
- Effective effort: `high`
- Reviewing session: `019fc201-6e8c-7ed1-9ae4-7f807c954c51`
- Review verdict: `CHANGES REQUIRED`

## Review target

- Reviewed plan ID: `TDW-009-P7`
- Reviewed plan version: `7`

## Claim or decision

CHANGES REQUIRED. The exact 44-path implementation is substantially correct:
record loading and rendering are fail-closed, descriptor-relative publication
does not overwrite or follow links, routing neutrality is reproduced, the
summary delegates validity to the existing validator, both synthetic
evaluations pass, and the canonical P7 delta reports exactly all 44 authorized
paths with no removal or unexpected path.

Acceptance is nevertheless blocked by one concrete publication-cleanup defect,
missing race and fault tests explicitly ordered by the accepted plan, and two
required repository gates that are not green in the reviewed checkout. The
gate failures are coordinator-owned rather than evidence of a defect in the 44
implementation paths, but the end-to-end plan cannot receive a PASS while its
mandatory verification table is unmet.

This review was performed by the same permitted replacement independent
stronger reviewer that reviewed plan versions 5 through 7. Reviewer session
`019fc201-6e8c-7ed1-9ae4-7f807c954c51`, route `review`, model
`gpt-5.6-sol`, and effort `high` differ from implementer session
`9afaaede-48b4-4462-9d5e-7de989b292d9` using `claude-opus-5`.

## Findings by severity

### Critical

None.

### High

#### H1 — Required end-to-end repository gates are not green

The accepted plan requires the focused integration suite and `make dossiers`
to pass, then requires `make check` and all component gates to pass
(`plan.md:400-428`). They do not in the reviewed checkout:

- `make dossiers` exited `1`. Before this review artifact was finalized, its 39
  diagnostics were confined to coordinator-owned TDW-009 placeholders in
  `index.md`, `code-review.md`, and `pr-desc.md`. Replacing this review removes
  the `code-review.md` placeholder diagnostics, but cannot resolve the
  unauthorized coordinator artifacts.
- The focused integration module ran 44 tests with one failure:
  `test_repository_checkout_validates_clean`, caused by those same TDW-009
  dossier placeholders. The complete integration suite likewise had one
  failure in 79 tests.
- `make test-contract` ran 70 tests with one failure:
  `test_durable_artifacts_do_not_embed_home_paths`. Its complete offender list
  contained exactly three coordinator-owned files under
  `TDW-009/capture/snapshot/`; the focused TDW-009 contract module itself passed
  all 24 tests. This reproduces the claimed capture/home-path interaction, but
  it does not make the required gate green.

These failures are not attributed to generator, summary, validator, wrapper,
schema, documentation, configuration, or evaluation code. They are still an
acceptance blocker. The coordinator must finalize the standard TDW-009 dossier
and reconcile retention of the protected capture evidence with the repository
home-path contract, then rerun the exact full table. The reviewer did not alter
the capture, index, PR description, tests, or any protected state.

### Medium

#### M1 — Post-publication observation faults leave this run's private temporary behind

After a successful hard link, `generate.py` raises directly when the final
`lstat` fails or observes a type/inode mismatch; both branches precede the only
strict private-temporary cleanup (`generate.py:465-500`). That contradicts the
accepted partial-progress contract: a fault at artifact *k* must unlink its own
identity-verified temporary while leaving final entries in place
(`design.md:516-552`; `plan.md:190-196`).

Independent temporary-root probes reproduced both reachable cases without an
excluded source-name substitution:

- replacing `index.md` after the hard link but before the observation produced
  the required nonzero publication-integrity diagnostic and left both the
  replacement final entry and `.tdgen.SYNTH-010.index.<pid>.0.tmp`;
- injecting an `OSError` into the post-link `lstat` produced the required
  nonzero observation/partial-adoption diagnostic and again left the run-owned
  `.tdgen` temporary beside the complete final entry.

The final entry must remain untouched, and a substituted foreign temporary
must never be unlinked. The existing identity-checking cleanup helper already
distinguishes those cases. The failure branches need to invoke that helper so a
run-owned temporary is removed while a raced-in foreign entry is preserved.

#### M2 — The accepted publication/race test matrix is incomplete

The accepted plan expressly requires a namespace swap between two
publications, a genuine two-invocation race from a missing dossier, regular-file
and symlink substitution of the verified temporary immediately before
`os.link`, final-name replacement after link, an injected `EEXIST`, and a
temporary-inode mismatch (`plan.md:252-279`). The implemented suite does not
contain those durable cases:

- the only namespace-swap test injects the swap while acquiring the lock,
  before the first publication (`test_task_dossier_generator.py:761-794`);
- the test named as two invocations first completes one entire generation, then
  holds the resulting directory lock and calls a second generation
  sequentially (`test_task_dossier_generator.py:796-813`);
- the fault suite covers write, `fsync`, close, `ENOSPC`, cleanup, exhaustion,
  permission, retry, and a pre-existing foreign file, but no stable source/final
  substitution or temporary-inode mismatch
  (`test_task_dossier_generator.py:823-987`).

Manual adversarial probes showed that source regular-file substitution, source
symlink substitution, final-name replacement, and a swap between publications
all returned nonzero and did not redirect writes to the decoy. That is useful
review evidence, but it does not replace the plan-mandated regression tests and
it exposed M1. Add the literal ordered cases and assertions, including the
threat-model caveat required by the plan.

### Low

None.

## Correctness and security evidence

- The exact literal 458-line P7 capture block was mechanically extracted from
  `design.md` and executed under Python 3.10.11. Current `delta` exited `0`,
  listing exactly 8 changed and 36 created paths: touched equals all 44,
  removals are empty, and unexpected is empty. The manifest has 333 rows.
- `config/model-routing.json` remains a captured outside-delta row. All 16
  entries under `src/brichan/resources/` and all 13 leaves for each of TDW-006,
  TDW-007, and TDW-008 remain covered; any change would have appeared as
  unexpected in the successful delta.
- Record loading rejects duplicate keys, inexact and boolean integer values,
  unknown/missing keys, placeholders, unsafe paths, personal paths, Markdown
  structural injection, embedded body line feeds, malformed review provenance,
  insufficient evidence, and all four plan/review consistency violations
  (`record.py:1-936`). The design's literal record renders and passes the
  validator under both default and complete gates.
- Generation renders all eleven bodies before mutation, walks each component
  with descriptor-relative `O_DIRECTORY | O_NOFOLLOW`, takes a nonblocking
  dossier lock before temporary/artifact mutation, uses bounded `O_EXCL`
  temporaries and no-replace hard-link publication, `fsync`s file and directory,
  and performs the final identity re-walk (`generate.py:1-647`). No `os.rename`
  or `os.replace` call exists.
- Both required routing-neutrality arms currently pass: source inspection over
  `record.py`, `generate.py`, and `summary.py`, plus fresh-interpreter import and
  real dry-run under open-path spies. No routing path was opened and no routing
  module was loaded (`test_task_dossier_generator.py:492-574`).
- Summary validity and exit status come from
  `validate_projects(root, require_complete=True)`; task selection does not
  suppress root diagnostics. Authority rows remain health observations, with
  detailed dossier validity delegated to `validate_dossier`
  (`summary.py:196-399,547-583`). Text and JSON parity, read-only behavior,
  unreadable artifacts, partial adoption, duplicate IDs, authority links, and
  both independence arms all passed.
- The validator change is confined to the shared no-follow ancestor helper and
  its receipt/memory call sites while reusing the schema-owned extra-section
  map (`validation.py:69,776-919`). Its focused 67-test suite passed, including
  both new ancestor cases and the unchanged clean case.
- `schema.py` preserves the established state/evidence constants and adds the
  record version, exact titles, owners, and shared extra sections. Package
  `main` remains `validation.main`; generator and summary entry points are
  distinct exports. Both wrappers are 19-line bootstrap shims, and repository
  path inventory passed with 76 entries and 64 references.

## Test results

| Check | Independent result |
| --- | --- |
| Python 3.10 generator unit module | 67 passed |
| Python 3.10 summary unit module | 26 passed |
| Python 3.10 validator unit module | 67 passed |
| Python 3.10 TDW contract module | 24 passed |
| Python 3.10 focused integration module | 43 passed, 1 coordinator-placeholder failure |
| Complete unit suite | 331 passed |
| Complete integration suite | 78 passed, 1 coordinator-placeholder failure |
| Complete contract suite | 69 passed, 1 capture-snapshot/home-path failure |
| `make receipts` | passed; 43 canonical receipts |
| `make path-check` | passed; 76 entries, 64 references |
| metrics, README, compatibility, package checks | all passed |
| Isolated concise dossier validator | passed; 2 dossiers |
| Isolated concise receipt validator | passed; 2 receipts |
| Isolated concise text and JSON summaries | both exited 0 |
| Canonical P7 delta | exited 0; exact 8/36/44, no removal or unexpected path |

The synthetic Level 0 and Level 1 records reload cleanly and render
byte-identically to all 22 generated artifacts. Their measured artifact totals
are 410 and 422 lines, within the 447 and 501 budgets. Record measurements are
227 lines / 9,723 bytes / 148 authored values and 304 lines / 11,569 bytes / 160
authored values. Both independently reproduced authored-value counts match
`results.md`, both complete dossier and receipt gates pass, and every session
and claim remains explicitly synthetic and non-authoritative.

## Test gaps

- Add the exact missing plan-step-11 race and stable-mismatch tests, including a
  real two-invocation first-creation race and the swap between publications.
- Add the missing temporary-inode and injected-`EEXIST` fault cases from plan
  step 12, and assert run-owned private-temporary cleanup on every ordinary
  failure path while preserving any foreign replacement.
- Rerun the focused Python 3.10 command and the complete repository table only
  after H1's coordinator-owned state is resolved.

## Residual risks and required decisions

- A non-cooperating same-identity process remains outside the threat model. The
  adversarial probes establish only reachable diagnostic paths; they do not
  establish prevention or guaranteed detection.
- Capture, preflight, delta, and post-publication observations remain
  point-in-time. `.env` and `.DS_Store` remain explicit capture blind spots, and
  a process crash can still leave an orphan private temporary.
- The coordinator must decide how protected capture snapshots containing
  captured home paths can coexist with the durable-artifact home-path contract.
  The reviewer did not delete, rewrite, relocate, or weaken either authority.
- The implementer child receipt still records implementation and test evidence
  as pending. This review relies on independently reproduced source, diff,
  delta, test, and evaluation evidence rather than that stale receipt.
- No implementation, planning, receipt, baseline, routing, resource, project-
  memory, capture, commit, remote, publication, or deployment action was taken.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/requirements.md:53-189`
  defines the security, generator, validator, summary, compatibility, and
  evaluation contracts.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md:460-640`
  defines descriptor walking, lock/publication ordering, cleanup, summary, and
  sole-validator semantics.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan.md:180-340,400-428`
  orders the exact implementation tests and mandatory verification table.
- `src/brichan/contracts/task_dossier/record.py`, `generate.py`, and `summary.py`
  are the reviewed implementation cores; the findings cite their exact line
  ranges above.
- `tests/unit/test_task_dossier_generator.py`,
  `tests/unit/test_task_dossier_summary.py`, and
  `tests/integration/test_task_dossier_workflow.py` are the reproduced focused
  and adversarial evidence surfaces.
- `evals/task-dossier-pilots/concise/results.md` and its exact 29 authorized
  evaluation leaves provide the independently revalidated Level 0/1 evidence.
- `projects/brida-task-dossier-workflow/handoffs/TDWREV-009/receipt.md` records
  this replacement reviewer's exact session, route, model, effort, scope, and
  independence from the implementer.

## Uncertainty

- No uncertainty remains about the verdict or M1: the omitted cleanup is visible
  in source and was reproduced twice with run-owned private temporaries.
- The missing tests may expose further bounded defects when added. The manual
  substitutions and namespace swap did fail closed, so no broader unsafe-write
  claim is made.
