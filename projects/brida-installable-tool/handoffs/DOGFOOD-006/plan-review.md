# Plan review

Independent review of requirements, options, design, and plan for the exact reviewed plan version.

## Artifact metadata

- Task ID: `DOGFOOD-006`
- Task level: `1`
- Artifact: `plan-review`
- Artifact version: `3`
- Origin: `review:DOGFOOD-006-P1-v3:019fc5de-ac86-7053-8464-d3269fdad90a`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fc5de-ac86-7053-8464-d3269fdad90a`
- Effective route: `review`
- Effective model: `gpt-5.6-sol`
- Effective effort: `medium`
- Reviewing session: `019fc5de-ac86-7053-8464-d3269fdad90a`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `DOGFOOD-006-P1`
- Reviewed plan version: `3`

## Claim or decision

PASS. Plan `DOGFOOD-006-P1` version 3 is complete and safe to implement within
its authorized paths. Requirements revision 3 closes the JSON contract at the
root, section, and nested-check levels; fixes the status vocabulary and
source/installed `ok`/exit behavior; and preserves installed state exits.
The plan makes the installed-wheel 0/1/2/3/4 matrix mandatory and retains
explicit subprocess, no-Herdr, read-only Git argv, worktree, and Git-index
evidence. Existing plain doctor output, installed schema, routing resources,
Herdr lifecycle, local Git state, and remote state remain outside mutation
scope.

Historical notes:

- Version 1 was `CHANGES REQUIRED` for incomplete dual-mode compatibility, an
  undefined JSON contract, and insufficient no-Herdr/no-Git evidence.
- Version 2 was `CHANGES REQUIRED` because nested section schemas and `ok`/exit
  semantics remained incomplete and installed-wheel coverage remained
  conditional.

## Findings by severity

### Critical

None.

### High

None.

### Medium

None.

### Low

None.

## Version 2 finding disposition

- V2 M1, exact nested schemas and `ok`/exit mapping: closed. Requirements now
  define every key and type for `repository`, `git`, `policies`,
  `model_routing`, `project_memory`, `dependencies`, `file_check`, and
  `dep_check` (`requirements.md:96-112`). They retain the closed status set from
  revision 2 (`requirements.md:81-89`) and define root `ok`, optional Herdr,
  source exits, installed exits, missing Codex, and missing Git
  (`requirements.md:113-117`).
- V2 M2, conditional installed-wheel evidence: closed. The wheel integration
  suite is now an unconditional authorized path with a mandatory installed JSON
  compatibility and exit matrix (`plan.md:55-64`).
- V1 M3 remained closed. Subprocess argv spying, Herdr non-execution, and
  worktree/Git-index snapshots remain required (`requirements.md:90-94`;
  `plan.md:44-49`).

## Schema and behavior verification

- Root: exactly `schema_version` integer `1`, `ok` boolean, and the six object
  sections, with no unknown root fields; output uses sorted keys, two-space
  indentation, and one trailing newline (`requirements.md:81-89`).
- `repository`: exactly status, string root, closed source/installed kind, and
  string detail (`requirements.md:98-99`).
- `git`: exactly status, nullable string branch/commit, nullable boolean
  dirty/untracked, and string detail (`requirements.md:100-102`).
- `policies` and `project_memory`: exactly status, a relative-path-to-file-check
  object, and string detail; each file check is exactly status, string path,
  and string detail (`requirements.md:103-106`).
- `model_routing`: exactly status, string path, nullable integer schema version,
  and string detail (`requirements.md:107-108`).
- `dependencies`: exactly status and the four named dependency checks; each
  dependency check is exactly status, nullable string path, boolean required,
  and string detail (`requirements.md:109-112`). Herdr is the sole optional
  dependency.
- Every status is in the closed set `ok`, `missing`, `invalid`, `unavailable`
  (`requirements.md:85-88`).
- Root `ok` is true exactly when every required section/check is `ok`, with
  optional missing Herdr ignored. Source exits are 0 when `ok`, 4 for Codex-only
  failure, and 2 for every other required failure, including missing Git.
  Installed mode preserves inspection exits 0/1/2/3 and uses 4 for healthy state
  with missing Codex (`requirements.md:113-117`).
- Source mode uses checkout inventory; installed mode delegates `.brichan` state
  semantics to `inspect_project()` (`requirements.md:38-46,90-92`;
  `plan.md:40-43`).

## Scope and safety verification

- Repository root, Git, canonical policy inventory, model-routing validation,
  project-memory inventory, and Python/Git/Codex/Herdr dependencies are all
  required report domains (`requirements.md:33-46,119-136`).
- Git is restricted to `status`/`rev-parse` queries with optional locks disabled;
  mutation commands are forbidden and missing Git is represented explicitly
  (`requirements.md:53-58`). Tests must inspect argv and snapshot the worktree
  and Git index (`requirements.md:93-94`; `plan.md:44-49`).
- Herdr is resolved only through `shutil.which`, remains optional, and is never
  invoked. A subprocess spy must prove non-execution
  (`requirements.md:50-52,93-94`; `plan.md:42-49`).
- Plain non-JSON doctor bytes and exits remain unchanged
  (`requirements.md:68-71`; `plan.md:31-33`).
- Implementation is bounded to lifecycle/dispatch/render, existing unit and
  integration suites, and the installed-dogfood guide (`plan.md:55-64`). The
  routing manifest, packaged resources, credentials, deployment, remote state,
  Herdr invocation, push, and PR creation are explicitly excluded
  (`plan.md:66-67`). No installed schema or dependency change is authorized
  (`requirements.md:72-74`).

## Test gaps

- No planning-stage test gap remains. The plan requires exact-schema and
  deterministic-serialization unit tests, healthy/missing/malformed and
  dependency cases, all installed exits, source and installed integration
  fixtures, Git/Herdr subprocess evidence, and filesystem/index snapshots
  (`plan.md:44-49`).
- These tests have not run because no implementation is under review. Focused
  results and `make check` are mandatory completion evidence
  (`requirements.md:75-77`; `plan.md:52-53`).

## Residual risks and required decisions

- In installed mode, the preserved lifecycle matrix can yield root `ok: false`
  with exit 0 when Git is unavailable but installed state is healthy and Codex
  is present. This follows the explicit v3 rule that only source-mode missing Git
  exits 2 while installed mode preserves state exits (`requirements.md:113-117`).
  It is deterministic and does not violate the recorded compatibility contract;
  documentation and tests should make the distinction visible.
- Ahead/behind tracking is explicitly excluded (`requirements.md:138-143`).
- Platform-specific `detail` text is diagnostic rather than stable; keys, types,
  statuses, and exits are contractual (`design.md:50-54`).
- Before/after snapshots are point-in-time evidence, not protection against an
  unrelated concurrent process. Isolated fixtures are sufficient for this task.
- No user decision is required before implementation. Code review and full
  validation remain required before completion.
- This review authorizes no implementation itself, project-memory update, Git
  mutation, Herdr call, secret access, push, PR, deployment, publication, or
  remote action.

## Evidence

- `projects/brida-installable-tool/handoffs/DOGFOOD-006/requirements.md:31-117`
  defines report scope, dual modes, safety rules, serialization, every exact
  schema, statuses, root `ok`, and exits.
- `projects/brida-installable-tool/handoffs/DOGFOOD-006/design.md:24-54` binds the
  implementation structure to requirements revision 3 and preserves the
  diagnostic-versus-stable distinction.
- `projects/brida-installable-tool/handoffs/DOGFOOD-006/plan.md:29-79` makes the
  schema, dual modes, installed matrix, safety tests, authorized paths,
  exclusions, documentation, and validation executable obligations.
- `src/brichan/cli/runtime.py:68-110,129-139,207-215` establishes current
  lifecycle dispatch and source-checkout identity behavior.
- `src/brichan/lifecycle.py:46-69,148-272,315-334` establishes installed state
  inspection, exits, read-only error handling, and current doctor dependencies.
- `tests/unit/test_project_lifecycle.py:232-247` and
  `tests/integration/test_installed_dogfood.py:355-393,506-522` establish the
  existing dependency and installed-wheel behaviors the new matrix must extend.

## Uncertainty

- No uncertainty remains about the plan verdict. Version 3 resolves every
  blocking version 1 and version 2 finding within the existing authorized scope.
- Implementation evidence remains unknown: exact emitted bytes, subprocess
  argv, Herdr non-execution, filesystem/index immutability, all exit cases,
  documentation accuracy, focused tests, and `make check` must be verified in
  code review before the task is complete.
