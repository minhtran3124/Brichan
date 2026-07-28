# RECEIPT-V2-001 plan

- Plan ID: `RECEIPT-V2-001-P1`
- Version: `1`
- Status: `accepted`
- Planner: Claude Opus session
  `d26beba3-5271-4a75-b14f-9a796868124d`
- Objective: add machine-validated attempt origin and lifecycle state while
  preserving schema-v1 compatibility.

## Schema

Schema version 2 adds four required `Identity` fields:

| Field | Allowed values |
| --- | --- |
| `Attempt origin` | `initial`, `replacement` |
| `Attempt lifecycle state` | `active`, `complete`, `stale`, `abandoned` |
| `Prior attempt state` | `stale`, `abandoned`, `null` |
| `Replacement evidence path` | repo-relative evidence path or `null` |

`replacement` describes immutable attempt origin, not the final lifecycle
state. A successful replacement therefore records origin `replacement` and
lifecycle `complete`.

## Invariants

1. Attempt 1 has origin `initial`, `Replaces session: null`, prior state
   `null`, and evidence path `null`.
2. Attempt greater than 1 has origin `replacement`, a concrete prior session,
   prior state `stale` or `abandoned`, and an existing repo-relative evidence
   path without absolute, parent-traversal, or home-path syntax.
3. A replaced session cannot equal a session listed in the current receipt.
4. At `implemented` or `reviewed`, lifecycle is `complete`; replacement prior
   state is `abandoned`.
5. Lifecycle `active`, `stale`, or `abandoned` is valid only while plan status
   is `accepted`; stale or abandoned requires evidence.
6. A `PASS` verdict requires lifecycle `complete`; existing reviewed-PASS gates
   remain unchanged.
7. Schema versions 1 and 2 are accepted; other versions fail. V1 behavior
   remains compatible and rejects v2-only fields. V2 requires all four fields.
8. Retry-limit escalation remains policy-owned. Schema v2 does not hard-cap the
   attempt number or guess provider-specific session-ID formats.

## Compatibility and migration

- Keep schema-v1 canonical receipts valid indefinitely.
- Migrate the three existing canonical receipts to v2 in the writer change:
  `CONCURRENT-002` and `RECOVERY-001` become initial/complete; `RECOVERY-002`
  becomes replacement/complete with prior state abandoned and its existing
  observation evidence path.
- Historical receipts under `evals/` remain undiscovered and unchanged.
- The coordinator migrates this task's own receipt to v2 after implementation,
  avoiding concurrent writer/coordinator ownership of the active receipt.

## Authorized implementation paths

1. `.agents/skills/herdr-orchestration/references/handoff-receipt.md`
2. `.agents/skills/herdr-orchestration/references/worker-recovery.md`
3. `scripts/validate_handoff_receipts.py`
4. `tests/test_handoff_receipt_validator.py`
5. `tests/test_repository_contract.py`
6. `tests/test_concurrency_contract.py`
7. The existing canonical receipts for `CONCURRENT-002`, `RECOVERY-001`, and
   `RECOVERY-002`

No Makefile, CI, metrics, eval, configuration, runtime, or coordinator-owned
project-memory changes are authorized.

## Ordered implementation

1. Add v2 fields and directionality prose to the receipt template.
2. Add an additive schema-v2 vocabulary sentence to worker-recovery policy
   without rewording existing structural anchors.
3. Parse schema version before field-set validation and enforce version-specific
   required/forbidden identity fields.
4. Implement the invariants above with file- and field-qualified diagnostics.
5. Add positive v1/v2, topology, and reviewed-PASS tests.
6. Add controlled invalid mutations for missing/invalid fields, inverted
   origin, self-replacement, bad evidence paths, incompatible lifecycle/status,
   v2 fields in v1, and unsupported schema versions.
7. Add structural field-label policy coverage.
8. Migrate the three existing canonical receipts as an independently
   revertible change.

## Acceptance criteria

1. Valid schema-v1 behavior remains green; valid v2 initial and replacement
   receipts pass.
2. All four v2 fields are required and enum-checked; v1 rejects them.
3. Attempt/origin/session/prior-state/evidence invariants are machine-enforced.
4. Lifecycle is coherent with accepted, implemented, reviewed, and PASS states.
5. The three existing canonical receipts validate as schema v2; historical
   eval receipts remain untouched and undiscovered.
6. Validator remains read-only, standard-library-only, and gives actionable
   diagnostics.
7. Focused validator, concurrency, repository-contract, and full checks pass.
8. An independent reviewer mutation-tests at least origin inversion,
   self-replacement, bad evidence path, and incomplete reviewed-PASS state.

## Escalation

Escalate if implementation requires a provider-specific session regex, an
absolute attempt cap, rewording existing anchored recovery policy, migration of
historical eval receipts, or any path outside the authorized scope.
