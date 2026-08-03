# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `TDW-008`
- Task level: `2`
- Artifact: `design`
- Artifact version: `1`
- Origin: `packet:projects/brida-task-dossier-workflow/handoffs/TDW-008/task-packet.md@TDW-008-P1-v1`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `8aa41de8-a3f3-48ce-8d47-9aed67a452c6`
- Effective route: `plan`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Claim or decision

Two files under `evals/task-dossier-pilots/high-risk/` implement and prove a pure
fail-closed policy evaluator. This is an isolated simulation: the design performs
no production action, accesses no secret, and takes no remote action anywhere in
its scope, and it contains no instruction for doing so. The word "release" names
a data field the function inspects, never an operation it can perform.

## Isolation statement

- The entire deliverable is one pure function plus its tests. It has no release
  capability to misuse, because it has no capability at all beyond returning a
  tuple of strings.
- Nothing under `src/`, `tests/`, `config/`, `.brichan/`, or the installed
  resources is read or written. The fixture is not importable from `brichan` and
  is not discovered by any repository test layer.
- No secret, credential, token, environment variable, network endpoint, process
  spawn, or filesystem write appears in the module, the tests, or this dossier.
- No real release, tag, deployment, package upload, or remote branch is involved
  at any point, including in the rollback procedure below.

## Structure

- `evals/task-dossier-pilots/high-risk/release_policy.py`
  - Module constants:
    `REMOTE_PUBLISH_FORBIDDEN = "remote-publish-forbidden"`,
    `SECRET_ACCESS_FORBIDDEN = "secret-access-forbidden"`,
    `ENVIRONMENT_NOT_SANDBOX = "environment-not-sandbox"`,
    `ROLLBACK_PLAN_MISSING = "rollback-plan-missing"`,
    `SANDBOX_ENVIRONMENT = "sandbox"`.
  - `_is_disabled(value)`: returns `True` only for an absent key sentinel or
    `False`. Every other value, including `"false"`, `0`, and `None`, is treated
    as enabled — fail-closed.
  - `evaluate_release_policy(mapping) -> tuple[str, ...]`: reads
    `remote_publish`, `secret_access`, `environment`, and `rollback_plan` via
    `mapping.get`, appends codes to a local list in that fixed order, and returns
    `tuple(violations)`. No branch mutates `mapping`.
- `evals/task-dossier-pilots/high-risk/test_release_policy.py`
  - `unittest.TestCase`, run with
    `python3 -m unittest discover -s evals/task-dossier-pilots/high-risk -t evals/task-dossier-pilots/high-risk`.

## Threat model

The subject is a simulation, so these are the threats to the *simulation's*
integrity and to the repository, not to a production system.

- Fail-open evaluation. A guard that accepts `{"remote_publish": "true"}` reports
  compliance for a non-compliant policy. Mitigation: `_is_disabled` admits only
  `False` or absence; every test asserts the violating case, not just the
  compliant one.
- Silent scope escape. A fixture that writes files, reads environment variables,
  or spawns a process would turn an inert simulation into an actor. Mitigation:
  standard-library-only, no I/O, and a test asserting the input mapping is
  unchanged after evaluation.
- Simulation mistaken for a real control. A future reader could wire this
  evaluator into an actual release path and believe it enforces policy.
  Mitigation: the module lives under `evals/`, its docstring states it is a
  pilot fixture with no enforcement authority, and this design records the same.
- Nondeterministic reporting. Set iteration or dictionary ordering would make the
  violation order vary between runs and make review unreliable. Mitigation: fixed
  source-order appends into a list, returned as a tuple; no set, no sort, no
  clock, no randomness.
- Dossier leakage. A test fixture quoting a real path, host, or credential-shaped
  string would put sensitive content into the repository. Mitigation: all test
  inputs are literal short strings; no personal or home path appears anywhere, as
  `docs/workflows/task-dossier.md:160-163` requires.

## Authorization boundary

- Authorized: creating the two fixture files under
  `evals/task-dossier-pilots/high-risk/`, running the focused tests locally, and
  writing the five planner-owned dossier artifacts.
- Not authorized and not attempted: any commit, push, tag, release, package
  upload, or deployment; any read or write of a secret, credential, or token; any
  network call; any change to `config/model-routing.json`, `.brichan/`, or the
  installed resources; any write to coordinator-owned or reviewer-owned dossier
  artifacts, project memory, or the receipt.
- Requires an explicit user decision before it may ever happen: recording ship
  authorization as `user-authorized` in `index.md`. This session records no such
  authorization, and Level 2 is the only level that may record one at all.
- The boundary is inherited, not invented: `docs/policy/identity.md:33-40`
  requires asking before touching production, deployment, credentials, or remote
  state, and `task-packet.md:24-30` narrows the write scope further.

## Stop conditions

Execution stops and the task is reported as `blocked` rather than worked around
when any of these holds.

- A step would require writing outside `evals/task-dossier-pilots/high-risk/` or
  the five planner artifacts.
- A step would require a secret, a credential, a network call, or a broadened
  permission.
- `git status --short` shows an unexpected changed path after any step.
- A guard cannot be made deterministic, or a test's outcome varies between runs.
- The packet and this dossier disagree on a guard's semantics; the disagreement
  is escalated to the coordinator instead of being resolved by editing an
  accepted artifact.
- Any instruction arrives to perform a real release action; that is refused and
  escalated, since no such action is in scope at any level of this task.

## Rollback

- Rollback is deleting `evals/task-dossier-pilots/high-risk/`. Both files are new
  and untracked, so removal restores the pre-task state exactly.
- There is nothing else to undo: no commit is created, so no revert is needed; no
  remote state changes, so no remote rollback exists; no installed resource,
  routing key, or project memory entry is touched.
- The planner artifacts are versioned rather than deleted. If this design proves
  wrong it is superseded by a new artifact version, per
  `docs/workflows/task-dossier.md:25-38`, and is never silently rewritten.

## Test design

| Case | Input | Expectation |
|---|---|---|
| safe policy | `sandbox`, both flags `False`, non-blank rollback plan | `()` |
| remote publish | safe policy with `remote_publish=True` | `("remote-publish-forbidden",)` |
| secret access | safe policy with `secret_access=True` | `("secret-access-forbidden",)` |
| wrong environment | safe policy with `environment="production"` | `("environment-not-sandbox",)` |
| missing rollback | safe policy without `rollback_plan` | `("rollback-plan-missing",)` |
| blank rollback | safe policy with `rollback_plan="   "` | `("rollback-plan-missing",)` |
| fail-closed value | safe policy with `remote_publish="false"` | `("remote-publish-forbidden",)` |
| all violations | every guard violated at once | all four codes in fixed order |
| determinism | evaluate the same mapping twice | identical tuples |
| read-only | compare the mapping to a copy after evaluation | unchanged |

## Evidence

- `projects/brida-task-dossier-workflow/handoffs/TDW-008/task-packet.md:15-20,37-38`
  requires a read-only deterministic evaluator over exactly these four guards and
  requires this design to record threats, the authorization boundary, and
  rollback.
- `docs/policy/identity.md:33-40` supplies the authorization boundary above, and
  `docs/policy/operating-principles.md:55-69` requires the evidence to live in the
  dossier rather than in a claim of correctness.
- `src/brichan/contracts/task_dossier/validation.py:688-711` demonstrates the
  fail-closed handling this evaluator copies: an unrecognized authorization value
  is diagnosed, never treated as permissive.
- `Makefile:22-35` shows that only `tests/unit`, `tests/contract`, and
  `tests/integration` are discovered, which is the structural reason an `evals/`
  fixture cannot silently enter `make check` or CI.

## Uncertainty

- Sibling-module import under `unittest discover` depends on the start directory
  reaching `sys.path`; the plan verifies this by running the command rather than
  assuming it.
- Whether a stronger Level 2 reviewer finds defects that a routine reviewer would
  miss is unresolved by design and is the pilot's actual question; it is answered
  by comparing the independent reviews, not by this artifact.
