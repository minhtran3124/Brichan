# Workflow documentation

This directory is the canonical location for tracked operational procedures.

- [Task dossier workflow](task-dossier.md) — the checkout-mode full-document
  task contract, its standard artifacts, and its validator.

## Recording a worker's lifecycle

A successful launch through `bin/brichan-herdr-agent-start` prints
`ledger: launch_id=<uuid>` on stderr. Carry that identifier into the matching
attestation once the worker's evidence is in hand:

```text
bin/brichan-herdr-worker-ledger finish \
  --worker <brichan-name> \
  --launch-id <uuid> \
  --evidence <repo-relative-path> [--evidence <citation> ...] \
  --ledger-file projects/<slug>/ledger/workers.jsonl
```

A `finished` record is an attestation, not an observation: the command cannot
verify completion, so it refuses an unmatched `--launch-id`, a name without the
`brichan-` prefix, and an empty evidence item. Each launch takes at most one
attestation, and consumers take the first `finished` record for a `launch_id`
in file order as the winning one.

The local `internal-docs/` directory remains ignored scratch material. It is
not migrated or published by Phase 1 because its content has not passed the
repository policy, branding, link, and accuracy contracts.
