# Code review

Independent remediation review against the originating request and accepted
plan.

## Artifact metadata

- Task ID: `DOGFOOD-006`
- Task level: `1`
- Artifact: `code-review`
- Artifact version: `2`
- Origin: `review:DOGFOOD-006-P1-v3:codex-independent-2026-08-03:v2`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `codex-independent-review-2026-08-03`
- Effective route: `review`
- Effective model: `gpt-5`
- Effective effort: `high`
- Reviewing session: `codex-independent-review-2026-08-03`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `DOGFOOD-006-P1`
- Reviewed plan version: `3`

## Verdict

**PASS.** The current diff closes both version 1 findings. Installed JSON
diagnostics no longer traverse rejected state-root or parent symlinks, and
non-UTF-8 routing data now produces the required structured invalid result with
exit 2 and no traceback. No new request, plan, safety, schema, exit, or
backward-compatibility defect was found.

## Version 1 history

Artifact version 1 returned **CHANGES REQUIRED** for:

- H1: installed JSON diagnostics traversed a rejected symlinked `.brichan` and
  parsed routing data outside the target repository.
- M1: non-UTF-8 routing bytes escaped as an uncaught `UnicodeDecodeError` and
  exit 1 instead of one JSON document and exit 2.

Both findings are closed by the evidence below.

## Finding disposition

### Critical

None.

### High

#### H1 — Closed: unsafe installed state roots and parents are not traversed

`doctor_report()` now checks the installed state root itself with a no-follow
`lstat` classification and, when unsafe or absent, constructs policy, memory,
and routing sections without touching descendants
(`src/brichan/lifecycle.py:384-402,650-707`). For otherwise valid roots,
`_path_check()` validates every parent component before the leaf, rejecting a
symlinked parent before routing can be read
(`src/brichan/lifecycle.py:405-426,481-494`). This retains the authoritative
`inspect_project()` exit class and exact report shape.

Independent direct CLI probes verified:

- A resolving `.brichan` symlink to an external directory returned exit 2;
  repository, policies, project memory, and routing were `invalid`, routing
  `schema_version` was null, and the external valid routing file was not
  reflected in the report.
- A dangling `.brichan` symlink produced the same blocked, deterministic result
  and exit 2.
- A symlinked `.brichan/config` parent returned exit 2 with
  `model_routing.status: invalid`, null schema version, and detail identifying
  `parent config` as a symbolic link.

Unit coverage exercises resolving and dangling state roots, symlinked parents,
non-directory and missing state roots, exact schema, and no outside-content
reads (`tests/unit/test_project_lifecycle.py:565-661`). The real checkout CLI
also verifies that a linked external routing file is not parsed
(`tests/integration/test_cli_compatibility.py:503-527`). This satisfies the
installed no-follow contract in `requirements.md:38-49`.

### Medium

#### M1 — Closed: non-UTF-8 routing is a structured invalid result

`_routing_section()` now catches `UnicodeDecodeError`, records status
`invalid`, leaves `schema_version` null, and returns a diagnostic instead of
raising (`src/brichan/lifecycle.py:481-505`).

An independent installed-project CLI probe with byte `0xff` in
`.brichan/config/model-routing.json` emitted one parseable JSON document,
reported `model_routing.status: invalid`, `schema_version: null`, `ok: false`,
and exited 2 without a traceback. The integration test additionally asserts
empty stderr, exactly one trailing newline, JSON parsing, invalid status, and
exit 2 (`tests/integration/test_cli_compatibility.py:442-501`); unit coverage is
at `tests/unit/test_project_lifecycle.py:664-673`. This closes
`requirements.md:33-37,59-67`.

### Low

None.

## Tests and evidence checked

- Inspected the complete current diff and every changed source, test, and
  documentation file; remediation remains within the accepted implementation
  paths in `plan.md:55-64`.
- `git diff --check`: PASS before this artifact update.
- Focused remediation and compatibility suite: 32 tests passed in 7.394s,
  covering the full lifecycle report class, deterministic JSON rendering, real
  checkout CLI JSON/plain compatibility, and installed-wheel JSON/exit tests.
- Direct adversarial probes independently covered resolving and dangling
  `.brichan` symlinks, a symlinked routing parent, and non-UTF-8 routing bytes;
  all returned exit 2 with the expected exact-schema JSON behavior.
- Existing Git argv remains list-based and restricted to
  `--no-optional-locks`, `-C`, `rev-parse`, and `status`; Codex and Herdr remain
  resolution-only (`src/brichan/lifecycle.py:526-639`).
- Documentation now accurately records blocked unsafe roots/parents and
  non-UTF-8 handling (`docs/guides/installable-dogfood.md:205-220`).

## Test gaps and residual risks

- The installed-wheel root-file assertion still compares its pre-command
  snapshot with a cached original dictionary rather than rereading root files
  (`tests/integration/test_installed_dogfood.py:621-643`). This is optional test
  hardening, not a remaining DOGFOOD-006 defect: managed-state snapshots,
  worktree/Git-index snapshots, direct probes, and unit no-write tests provide
  independent coverage of the required invariant.
- Parent validation and the later file read are separate filesystem operations;
  an unrelated concurrent process could swap entries between them. Atomic
  descriptor-relative traversal was not required by the accepted plan and is a
  residual hardening opportunity rather than a defect in this bounded command.
- The full `make check` gate was not rerun in this re-review. Version 1 verified
  that doctor-focused tests passed while full validation was blocked by ignored
  generated `src/brichan.egg-info` and incomplete coordinator-owned dossier
  state. The coordinator must still obtain a passing full validation before
  reporting the task complete, as required by `requirements.md:75-77`.

## Required human decisions

None for this implementation. Any future decision to weaken the no-follow
state boundary would be a separate security/compatibility change requiring
explicit authorization.

## Claim or decision

Plan `DOGFOOD-006-P1` version 3 passes implementation re-review. H1 and M1 are
closed with code, regression tests, and independent direct-probe evidence.

## Evidence

- Concrete file/line references, focused test results, and adversarial probe
  outcomes recorded above.
- Accepted contracts in `requirements.md:33-117` and `plan.md:31-67`.

## Uncertainty

- No uncertainty remains about the H1 or M1 disposition. Passing full
  repository validation remains a coordinator completion gate, not evidence of
  an unresolved doctor implementation defect.
