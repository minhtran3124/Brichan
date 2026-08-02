# TDW-009 task packet

## Objective

Implement the two highest-value follow-ups from the three-lane pilot:

1. a concise Level 0/1 dossier generator driven by one structured task record;
2. a deterministic dossier summary command.

Both capabilities must preserve all eleven standard artifacts, the existing
evidence contract, review independence, authority links, routing neutrality,
and fail-safe filesystem behavior.

## Scope

- Checkout mode only.
- Extend the existing task-dossier contract, importable implementation, thin
  script wrappers, documentation, repository gates, tests, and isolated
  evaluation samples.
- Preserve the current scaffolder and validator interfaces unless a compatible
  extension is explicitly justified by the accepted plan.
- Use only the Python standard library.

## Out of scope

- Installed `.brichan` schema or packaged resource changes.
- New keys or defaults in `config/model-routing.json`.
- Removing or merging any of the eleven standard artifacts.
- Generating unverifiable evidence, inferring review verdicts, or treating
  model confidence as proof.
- Remote actions, publishing, deployment, production changes, secrets, or
  permission broadening.

## Acceptance criteria

| ID | Criterion |
| --- | --- |
| `TDW-009-AC1` | A structured Level 0/1 task record can generate all eleven standard artifacts without overwriting an existing file, following a symlink, or escaping the selected projects root. |
| `TDW-009-AC2` | Generated artifacts preserve concrete claim, uncertainty, provenance, applicability, review linkage, and Level 0/1 evidence-depth requirements and can pass `--require-complete` when the record contains complete valid evidence. |
| `TDW-009-AC3` | Reproducible Level 0 and Level 1 samples retain 11/11 artifacts while reducing total dossier lines by at least 30% versus the 639-line and 716-line pilot baselines respectively. |
| `TDW-009-AC4` | A deterministic summary command reports artifact state, evidence count versus floor, effective model provenance, accepted-plan/review identity, authority-link health, and review independence; invalid or incomplete dossiers produce diagnostics and a nonzero exit. |
| `TDW-009-AC5` | Existing scaffold and validation behavior remains compatible, routing stays manifest-neutral, and installed resources remain unchanged. |
| `TDW-009-AC6` | Unit, contract, integration, focused evaluation, receipt/dossier, path, and full `make check` gates pass. |
| `TDW-009-AC7` | Durable evaluation compares the concise samples with the original pilots and records both benefits and residual risks without estimating unavailable timing, tokens, or cost. |
| `TDW-009-AC8` | Independent stronger plan and code reviews return PASS after any findings are remediated. |

## Permissions and constraints

- Planner owns only `requirements.md`, `brief.md`, `options.md`, `design.md`,
  and `plan.md` in this dossier.
- Reviewers own only `plan-review.md` and `code-review.md`.
- The implementation worker may write only paths explicitly accepted in
  `plan.md`; coordinator owns task packet, receipts, index, request,
  follow-up, PR description, project memory, metrics, and integration.
- Do not spawn sub-agents or use native delegation.
- Do not modify the user's existing `config/model-routing.json` diff.
- Do not commit, publish, deploy, or mutate remote state.

## Escalation conditions

- The design would weaken the eleven-artifact or evidence contract.
- Safe generation appears to require overwriting existing artifacts.
- The summary would duplicate receipt/project-memory authority instead of
  reporting linked health.
- Scope requires installed resources, routing changes, secrets, network access,
  or a new runtime dependency.

## Plan remediation amendment

Independent review of `TDW-009-P1` version 1 returned `CHANGES REQUIRED`.
Brichan resolves the three requested design decisions as follows:

1. Evaluation dossiers are unmistakably synthetic, non-authoritative test
   fixtures. Their reports must never present synthetic session inequality or
   PASS markers as evidence of real independent review. TDW-009's own dossier
   remains the real evidence trail.
2. Summary defaults to the complete gate: an incomplete dossier exits nonzero.
   A relaxed default is not authorized.
3. Generation uses a generator-specific POSIX directory-descriptor writer,
   anchored from the selected projects root. Existing scaffold behavior remains
   unchanged.

Plan version 1 must be preserved under
`projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v1/` before the
five standard planning artifacts are superseded by version 2. The planner may
write only those five snapshots plus its original five standard artifacts.
Version 2 must remediate every finding in `plan-review.md`, including atomic
per-artifact publication, post-preflight ancestor races, project-level summary
diagnostics, duplicate JSON keys and Markdown-structure injection, a closed
evaluation leaf allowlist, dirty-worktree baselines, authoring-burden metrics,
and exact source API imports/exports.

Before reviewing version 2, the reviewer may preserve its version-1
`plan-review.md` byte-identically at
`projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v1/plan-review.md`,
then replace the standard review artifact with a version-2 review naming
`TDW-009-P2`.

## Plan version 3 remediation amendment

Independent review of `TDW-009-P2` version 2 returned `CHANGES REQUIRED`.
Brichan makes the following bounded reliability and authority decisions:

1. The generator must be safe against pre-existing symlinks, namespace drift
   that it can observe, ordinary concurrent Brichan invocations, and all
   specified write/publication failures. A malicious or non-cooperating
   same-OS-identity process that mutates directory entries while the generator
   holds the dossier lock is outside this repository tooling threat model.
   The design must state this limitation prominently, use a dossier-scoped
   advisory lock for cooperating writers, preserve no-overwrite publication,
   and return nonzero when a final canonical descriptor re-walk detects
   namespace drift. It must not claim protection against the excluded attacker.
2. Ancestor-symlinked receipt and project-memory authority paths are invalid,
   not merely informational. Exact compatible changes and regression tests in
   the already-authorized `validation.py` and task-dossier test paths may make
   these conditions part of the sole validator verdict. The summary must report
   that verdict rather than create a second validity authority.
3. Before implementation handoff, the coordinator will replace the baseline
   with an implementation-start manifest containing repository identity, the
   accepted plan's exact implementation-path allowlist, presence/absence and digest/content evidence for
   every allowlisted path, an exact untracked-leaf inventory, and every file
   under `src/brichan/resources/`, including package files. Delta and rollback
   commands must operate from this manifest and must preserve pre-existing user
   changes.

Plan version 2 must be preserved under
`projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/` before the
five standard planning artifacts are superseded by version 3. Version 3 must
also resolve the explicit record type/example contradictions, point historical
evidence to immutable versioned reviews, define reproducible authored-value
counting, define unreadable artifact versus unreadable dossier exit boundaries,
and close every test gap in the version-2 review. The accepted plan identity
will be `TDW-009-P3` version `3`.

Before reviewing version 3, the reviewer may preserve its version-2
`plan-review.md` byte-identically at
`projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v2/plan-review.md`,
then replace the standard review artifact with a version-3 review naming
`TDW-009-P3`.

## Plan version 4 remediation amendment

Independent review of `TDW-009-P3` version 3 returned `CHANGES REQUIRED`.
Brichan resolves the remaining decisions as follows:

1. The current bytes of `config/model-routing.json` are user-owned protected
   state. The implementation-start manifest must capture whatever exact bytes
   and digest exist at capture time; planning and implementation must not
   hard-code an older digest, absorb the file into implementation scope, or
   restore another version.
2. The accepted same-identity threat boundary remains unchanged. Immediate
   post-publication checks provide point-in-time best-effort observation only;
   neither prevention nor guaranteed detection may be claimed for the excluded
   non-cooperating process.
3. The implementation-start manifest must include restorable byte snapshots
   and digests for every modified tracked path, while every planned new path
   must be recorded absent. The plan must specify a canonical manifest format,
   exact set-delta procedure, and identity-checked rollback procedure that never
   overwrites a target changed after implementation.
4. Summary exits follow actual validator discovery: an existing unreadable
   `index.md` and root-level partial adoption exit `1`; a truly absent or
   unlistable requested scope and unmatched `--task` exit `2`. Selected-task
   handling must not override the project validator.
5. Safe descriptor-relative directory creation may precede the dossier lock.
   The lock must be acquired immediately after opening the dossier and before
   any temporary-file or artifact mutation. A two-invocation first-creation
   test is required.

Plan version 3 must be preserved under
`projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/` before the
five standard planning artifacts are superseded by version 4. Version 4 must
include a literal complete eleven-artifact worked record that validates under
the documented schema, correct every exit and threat-model statement, and close
all H1-H4/M1 findings and added tests from the version-3 review. The accepted
plan identity will be `TDW-009-P4` version `4`; its implementation allowlist
remains exactly 44 paths unless an independent review justifies another bounded
change.

Before reviewing version 4, the reviewer may preserve its version-3
`plan-review.md` byte-identically at
`projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md`,
then replace the standard review artifact with a version-4 review naming
`TDW-009-P4`.

## Plan version 5 remediation amendment

Independent review of `TDW-009-P4` version 4 returned `CHANGES REQUIRED`.
Brichan narrows the remaining boundary instead of introducing a new manifest
runtime:

1. The implementation-start baseline is a complete no-follow capture map of
   every observed repository file outside an exact enumerated exclusion set.
   Each row records relative path, file type, byte length, and SHA-256; the
   eight modified tracked paths additionally have authenticated byte snapshots.
   Pre-existing tracked changes and untracked leaves outside the exclusions are
   included. The implementer must run an exact executable preflight that
   re-creates this map and compares it byte-for-byte, verifies all snapshots,
   and verifies every planned-new path is absent before any implementation
   write. Any mismatch is a stop.
2. Automatic or in-task rollback is removed from TDW-009. It was not a user
   requirement and a portable pathname procedure cannot provide honest
   compare-and-swap safety against concurrent same-identity mutation. On
   implementation failure the worker fixes forward within its 44 paths; after
   a successful scoped commit, recovery is by an explicitly reviewed commit
   revert. No worker may restore or delete from snapshots.
3. Exact before/after delta checks and manifest-preflight tests must live in an
   already-authorized integration or contract test file. No 45th helper path is
   authorized.
4. `sections[].body[]` is exactly one rendered line and must reject embedded
   line feeds. Safe multi-line `claim` remains allowed and is checked per line.

The same non-cooperating same-OS-identity process remains outside the capture,
implementation, and publication threat model; the plan must not claim
compare-and-swap protection against it.

Plan version 4 must be preserved under
`projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/` before the
five standard planning artifacts are superseded by version 5. Version 5 must
remove every rollback promise and procedure, define the exact complete-map
exclusions and executable preflight/delta commands, close H1-H3/M1 and all
added tests from the version-4 review, retain the exact 44-path allowlist, and
use accepted plan identity `TDW-009-P5` version `5`.

Before reviewing version 5, the reviewer may preserve its version-4
`plan-review.md` byte-identically at
`projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md`,
then replace the standard review artifact with a version-5 review naming
`TDW-009-P5`.

## Plan version 6 remediation amendment

Independent replacement review of `TDW-009-P5` version 5 returned
`CHANGES REQUIRED`. Version 6 is limited to the reproduced executable defects:

1. Use one canonical JSON implementation-start manifest. The executable
   capture, preflight, and delta code must emit and consume that exact JSON
   schema; no row-only shadow format or section-stripping convention is
   allowed. The reviewer must be able to extract the literal code block and run
   capture, preflight, and delta against the literal documented manifest.
2. The complete no-follow map must record symlinks found in both file-name and
   directory-name positions. A symlink to a directory is recorded as a symlink
   row and is never traversed. Retargeting it or replacing its entry type must
   make preflight/delta nonzero.
3. Fail closed on list and touched-set equality: modified paths must equal the
   exact eight-item set, new paths the exact thirty-six-item set, their union
   the exact forty-four-item allowlist, and successful post-implementation
   `touched` must equal all forty-four paths. A strict subset or superset is a
   failure.
4. Add a generator static/import probe in an already-authorized test file that
   proves generator code neither reads nor names `config/model-routing.json`.

Plan version 5 must be preserved under
`projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v5/` before the
five standard planning artifacts are superseded by version 6. Version 6 must
close every P5 review finding and test gap, retain the exact 44-path allowlist,
and use accepted plan identity `TDW-009-P6` version `6`.

Before reviewing version 6, the reviewer may preserve its version-5
`plan-review.md` byte-identically at
`projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v5/plan-review.md`,
then replace the standard review artifact with a version-6 review naming
`TDW-009-P6`.

## Plan version 7 remediation amendment

Independent replacement review of `TDW-009-P6` version 6 returned
`CHANGES REQUIRED`. Version 7 is restricted to four fail-closed corrections:

1. Freeze the exact sorted eight modified and thirty-six new path tuples inside
   the reviewed literal executable. `build`, loader, preflight, and delta must
   compare manifest lists to those constants, derive the forty-four union only
   from them, and reject same-count substitutions or misclassification.
2. Freeze one repository-relative snapshot directory inside the executable;
   the manifest may only repeat that exact value. Reject absolute, traversing,
   backslash-containing, or alternate paths. Open every component from the
   repository descriptor using `O_DIRECTORY | O_NOFOLLOW`; authenticate leaves
   descriptor-relatively and never follow an ancestor symlink.
3. Make the loader's guaranteed schema genuinely strict: exact non-boolean
   integer version, nonnegative exact-integer lengths, exactly 64 lowercase
   hexadecimal digests, and the documented zero-length/zero-digest invariant
   for non-file rows. Add direct malformed-manifest tests.
4. Add both generator routing-neutrality arms explicitly to the ordered
   generator unit-test step: forbidden-spelling source inspection and an import
   plus real dry-run under a path-open spy, with no routing opens or loaded
   routing module.

Plan version 6 must be preserved under
`projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v6/` before the
five standard planning artifacts are superseded by version 7. Version 7 must
close every P6 finding and test gap, retain the exact 44-path allowlist, and use
accepted plan identity `TDW-009-P7` version `7`.

Before reviewing version 7, the reviewer may preserve its version-6
`plan-review.md` byte-identically at
`projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v6/plan-review.md`,
then replace the standard review artifact with a version-7 review naming
`TDW-009-P7`.
