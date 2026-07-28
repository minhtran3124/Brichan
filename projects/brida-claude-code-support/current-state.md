# Current state

- Status: receipt hardening and second mixed-provider dogfood pilot complete.
- Claude Code 2.1.220 is authenticated and routable; Herdr reports Claude
  integration v7 as current.
- Brida has validated two sequential workflows using Claude Opus planning,
  Codex Terra implementation, and fresh Claude Opus review.
- Receipt schema version 1 now has copy-safe placeholders, contract-protected
  headings and fields, skill discoverability, and home-path guards.
- Task packets support an optional accepted plan ID/version/status and
  repo-relative receipt path. Existing packets may omit the block or use
  `null` values.
- `PILOT-002` filled a real receipt under
  `evals/mixed-provider-coding/PILOT-002/`; a fresh reviewer found it through
  `projects/index.md` → project memory → `references.md` without chat history.
- Both hardening and `PILOT-002` initially received `CHANGES REQUIRED` for
  weak test assertions. Minimal remediations were mutation-tested and both
  final reviews returned `PASS`.
- Latest validation: 14 repository contract tests and 33 total checks pass;
  `git diff --check` is clean.

## Main gaps and risks

- Receipt storage under `evals/mixed-provider-coding/<pilot-id>/` is validated
  for pilots but not yet adopted as a general project contract.
- Receipts and task-packet linkage remain optional and Markdown-only; no
  machine-enforced lifecycle state, retry limit, stale-worker rule, or receipt
  completeness validator exists.
- Optional test hardening remains for exact heading cardinality, table shape,
  tilde-style home paths, and label-to-section anchoring.
- No documented worktree or exclusive-file ownership policy exists for
  concurrent implementation.
- Model quality, latency, token, and cost comparisons remain unbenchmarked where
  observations were unavailable.

## Open questions

1. Should the validated evaluation-artifact receipt location become the
   default for all delegated implementation, or only cross-provider pilots?
2. Should a receipt become mandatory whenever an accepted upstream plan exists?
3. Should parallel implementation require separate git worktrees, exclusive
   file ownership, or both?

## Next actions

1. Decide the adoption boundary for receipt storage and mandatory use.
2. Add a receipt completeness validator only if receipts become a required
   completion gate.
3. Define worktree/file-ownership rules before any parallel code-writing pilot.
