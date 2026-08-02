# Code review

Independent review of the implementation, or the recorded evidence for why no implementation review applies.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `code-review`
- Artifact version: `2`
- Origin: `review:projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md@TDW-009-P7-v7+bounded-remediation`
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
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `TDW-009-P7`
- Reviewed plan version: `7`

## Claim or decision

PASS. The bounded remediation closes both publication-cleanup branches and
adds the complete durable race and substitution matrix ordered by the accepted
plan. The updated genuine first-creation test starts two independent Python
processes with the dossier absent, places their barrier inside the final
component's `mkdir`, proves that the loser receives `EEXIST`, proves both
processes converge on one inode, and proves the nonblocking lock permits exactly
one publisher before any losing artifact or temporary is created.

The previously coordinator-owned repository blockers are also resolved:
`index.md` and `pr-desc.md` are concrete, the default dossier gate passes, and
the home-path contract has one exact exception for direct children of the
authenticated TDW-009 snapshot directory. The exception is not a generic
snapshot, project, home-path, descendant, or sibling bypass. All required code,
contract, evaluation, receipt, path, and repository gates are green.

This review was performed by the same permitted replacement independent
stronger reviewer that reviewed plan versions 5 through 7 and implementation
artifact version 1. Reviewer session
`019fc201-6e8c-7ed1-9ae4-7f807c954c51`, route `review`, model
`gpt-5.6-sol`, and effort `high` differ from implementer session
`9afaaede-48b4-4462-9d5e-7de989b292d9` using `claude-opus-5`.

## Findings by severity

### Critical

None.

### High

None.

### Medium

None.

### Low

None.

## Remediation verification

### M1 — Closed: post-link observation branches clean only run-owned temporaries

Both post-link failure branches now invoke the identity-checking cleanup helper
before raising (`generate.py:482-506`). A failed final `lstat` and an observed
final type/inode mismatch therefore remove this run's still-linked private
temporary, leave the final entry untouched, and preserve a temporary name that
has been replaced by a foreign inode. Successful publication retains strict
cleanup.

Durable tests independently reproduced final replacement, post-link
observation failure, regular-file and symlink source substitution, temporary
inode mismatch, injected `EEXIST`, ordinary cleanup, and foreign temporary
preservation. The tests assert the nonzero outcomes, final-entry preservation,
run-owned cleanup, and foreign-entry preservation appropriate to each branch.
The source-substitution class also carries the required limitation: these are
reachable diagnostic paths, not prevention or guaranteed detection against an
excluded non-cooperating same-identity process.

### M2 — Closed: genuine creation race and ordered publication faults are durable

`NamespaceSafetyTest.RACE_PROGRAM` and
`test_a_genuine_two_invocation_first_creation_race`
(`test_task_dossier_generator.py:843-1026`) provide a real two-process race:

- both reports prove the dossier was absent when each invocation started;
- both subprocesses stop inside `os.mkdir("SYNTH-010", ...)`;
- the winner creates and locks the dossier before the loser proceeds;
- the loser records the actual `FileExistsError` from `mkdir`, reopens the same
  inode, and is refused by the held nonblocking lock;
- exactly one invocation publishes all eleven artifacts, while the loser's
  observation under the held lock contains no artifact or private temporary.

The test uses file barriers and blocking waits rather than timing assumptions.
The companion deterministic test repeats the same race three times. During
this review, the primary test passed three separate Python 3.10 invocations,
and the complete 76-test generator module then passed.

The suite also now includes the namespace swap between two publications,
regular and symlink source substitutions, final-name replacement after link,
injected `EEXIST`, temporary-inode mismatch, post-link observation failure,
ordinary cleanup, and foreign-temporary preservation. The publication source
continues to contain no `os.rename` or `os.replace` operation.

### H1 — Closed: dossier completion and bounded opaque-evidence exception

`index.md` and `pr-desc.md` are concrete and consistent with plan P7/version 7;
default validation discovers and validates all four repository dossiers.

The home-path test's exception constructs one literal TDW-009 capture snapshot
directory and skips only when `path.parent` equals that exact directory
(`test_repository_contract.py:317-340`). An independent boundary probe showed:
an exact direct child is exempt; a nested child, sibling path, another task, and
another project are not. The exception therefore cannot serve as a generic
home-path bypass. Its safety remains coupled to the accepted P7 capture
preflight, which authenticates the exact eight opaque snapshot files and their
bytes.

## Correctness and security evidence

- The literal P7 executable capture/preflight/delta block was mechanically
  extracted from `design.md` and independently exercised under Python 3.10.
  At the implementation-isolation checkpoint it reported the frozen exact
  tuples of 8 modified and 36 new paths, all 44 touched, no removal, and no
  unexpected path. Its adversarial integration suite passes same-count
  substitution, misclassification, forged-full-delta, under-touch,
  over-touch, outside-allowlist tracked/untracked drift, 36-new absence,
  symlink-directory no-traversal and retarget/type drift, descriptor-walk path
  attacks, malformed manifest values, and non-file invariant cases.
- The later change to `config/model-routing.json` is user-owned/external
  protected-state drift after that point-in-time isolation result. Per explicit
  direction it was neither normalized, reverted, included, nor attributed to
  the 44-path implementation. All 16 protected resource entries and the
  protected TDW-006, TDW-007, and TDW-008 leaves remain unchanged from capture.
- Generation renders all eleven bodies before mutation, rejects embedded body
  line feeds and unsafe record/path values, walks components descriptor-
  relatively with no-follow directory opens, locks before temporary or
  artifact mutation, stages with bounded exclusive names, publishes by
  no-replace hard link, verifies identities, and performs final namespace
  re-observation. No rollback mutation is present.
- Both generator routing-neutrality arms pass: static source inspection and a
  fresh-interpreter import plus real dry run under open-path spies. The
  generator neither opens the routing manifest nor imports routing modules.
- Summary validity and exit status come solely from
  `validate_projects(root, require_complete=True)`. Task selection does not
  suppress root diagnostics; authority rows remain observations, and detailed
  dossier validity remains delegated to the existing validator. Text/JSON
  parity, read-only behavior, partial adoption, unreadable artifacts, duplicate
  IDs, authority links, and both independence arms pass.
- The schema and validator retain established constants and shared extra-
  section ownership. Their Python 3.10 suites pass, including no-follow
  ancestor checks, review provenance, exact version/type handling, and the
  unchanged clean authority case. The implementation remains Python 3.10
  compatible.
- The wrapper scripts remain thin bootstrap shims, the package main remains
  validator-compatible, generator and summary exports are distinct, and the
  documentation/configuration/path inventories pass their contracts.

## Test results

| Check | Independent result |
| --- | --- |
| Genuine missing-dossier race, Python 3.10 | passed on 3 consecutive targeted runs |
| Complete generator unit module, Python 3.10 | 76 passed |
| Summary unit module, Python 3.10 | 26 passed |
| Validator unit module, Python 3.10 | 67 passed |
| Focused task-dossier integration module, Python 3.10 | 44 passed |
| Fresh complete unit suite | 340 passed |
| Fresh complete contract suite | 70 passed |
| Fresh complete integration suite | 79 passed |
| `make check` after the race-test update | passed, including every component gate |
| `make receipts` | passed; 43 canonical receipts |
| `make dossiers` | passed; 4 task dossiers |
| `make path-check` | passed; 76 entries, 64 references |
| metrics, README, compatibility, package, shell checks | all passed |
| Isolated concise dossier and receipt validators | both passed; 2 cases each |
| Isolated concise JSON summary | exited 0 with no diagnostics |

The synthetic Level 0 and Level 1 records reload cleanly and render
byte-identically to all 22 generated artifacts. Their measured artifact totals
remain within both accepted budgets; independently reproduced authored-value
counts match `results.md`. Both complete dossier and receipt gates pass, and
all sample sessions and claims remain explicitly synthetic and
non-authoritative.

## Test gaps

None within the accepted TDW-009-P7 scope.

## Residual risks and required decisions

- A non-cooperating process running under the same OS identity remains outside
  the accepted threat model. The adversarial tests establish fail-closed
  behavior when their observations fire, not a compare-and-swap guarantee.
- Capture, preflight, delta, and post-publication checks remain point-in-time.
  The documented capture blind spots remain, and a process crash can still
  leave an orphan private temporary.
- The exact snapshot-directory home-path exception depends on the accepted
  capture manifest/preflight continuing to authenticate the eight opaque
  pre-task files. It must not be generalized to descendants, sibling snapshots,
  other tasks, or newly unauthenticated evidence.
- `config/model-routing.json` currently differs from the earlier protected
  capture state because of later user-owned/external activity. The prior
  independent exact-44 checkpoint remains the implementation-isolation
  evidence; this review made no routing or resource change.
- No implementation, planning, receipt, baseline, routing, resource, project-
  memory, capture, commit, remote, publication, or deployment action was taken.
  Reviewer writes were limited to the authorized byte-identical v1 archive and
  this standard v2 review artifact.

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-009/requirements.md:53-189`
  defines the security, generator, validator, summary, compatibility, and
  evaluation contracts.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md:460-640`
  defines descriptor walking, lock/publication ordering, cleanup, summary, and
  sole-validator semantics.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/plan.md:180-340,400-428`
  orders the exact race, substitution, fault, and repository verification
  matrix.
- `src/brichan/contracts/task_dossier/generate.py:430-506` contains the reviewed
  identity checks, no-replace publication, and remediated cleanup branches.
- `tests/unit/test_task_dossier_generator.py:796-1043,1209-1385` contains the
  independently reproduced namespace, creation-race, publication-fault,
  substitution, cleanup, and threat-model evidence.
- `tests/contract/test_repository_contract.py:317-340` contains the reviewed
  exact opaque-snapshot exception; the complete 70-test contract suite passed.
- `evals/task-dossier-pilots/concise/results.md` and its exact authorized Level
  0/1 leaves provide the independently revalidated synthetic evaluation
  evidence.

## Uncertainty

No unresolved implementation finding remains within the accepted P7 threat
model and evidence scope. Residual uncertainty is limited to point-in-time
filesystem observations, excluded non-cooperating same-identity processes, and
continued authentication of the exact opaque snapshot evidence, as bounded
above; none changes the PASS verdict.
