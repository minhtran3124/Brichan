# Decisions

## 2026-08-10 — New checkout task dossiers are local-only

- Status: accepted and implemented
- Context: Per-feature and per-bug dossiers are internal workflow state that
  must survive across local agent sessions without entering ordinary commits.
- Decision: Git ignores new `projects/*/handoffs/*/` directories while the
  project index and canonical direct project-memory files remain visible.
- Rationale: Git visibility is independent from filesystem availability, so
  agents and validators retain continuity without adding dossier churn to PRs.
- Guardrail: Existing tracked dossiers are not removed; force-adding a new
  dossier remains an explicit user action and no workflow does it implicitly.
- Owner: User

## 2026-08-02 — Full dossier for every task level

- Status: accepted by user
- Context: Future work needs durable evidence for model-authored requirements,
  design, planning, and review, including simple tasks.
- Decision: Every Level 0/1/2 task creates the same complete document set.
  Level changes evidence depth, reviewer strength, and authorization gates.
- Rationale: Missing artifacts cannot distinguish a deliberately skipped phase
  from lost context; explicit `not-required` decisions preserve the audit trail.
- Guardrail: File presence is not proof. Empty placeholders fail; claims need
  evidence, uncertainty, version, author/session, and review verdict.
- Owner: User

## 2026-08-02 — Concise generation keeps every artifact

- Status: accepted and implemented
- Context: Uniform full dossiers preserve evidence but repeat substantial
  metadata and status ceremony for Level 0/1 tasks.
- Decision: Use one strict structured JSON record to render all eleven standard
  artifacts; never collapse, omit, or replace them with the record.
- Rationale: Repetition can be generated safely without weakening artifact
  presence, provenance, evidence floors, or independent review.
- Guardrail: Rendering completes before mutation; publication is
  descriptor-relative, no-follow, no-replace, locked, and route-neutral.
- Owner: Brida coordinator under the user-approved recommendation

## 2026-08-02 — Summary validity stays validator-owned

- Status: accepted and implemented
- Context: A concise operational view is useful, but a second interpretation of
  dossier validity would create authority drift.
- Decision: Text and JSON summaries report deterministic observations while
  `validate_projects(..., require_complete=True)` remains the sole validity and
  exit-status authority.
- Rationale: One validator prevents task selection, link health, or formatting
  logic from hiding root-level evidence failures.
- Guardrail: Summary code does not read model routing and never mutates dossier
  or project state.
- Owner: Brida coordinator under the accepted P7 plan

## 2026-08-02 — Opaque capture exception is exact, not generic

- Status: accepted as bounded completion remediation
- Context: Three authenticated pre-task source snapshots contain historical
  home-path literals and therefore conflict with the authored-text hygiene
  contract despite being byte evidence rather than authored documentation.
- Decision: Exempt only direct children of the literal TDW-009
  `capture/snapshot` directory from the textual home-path scan.
- Rationale: Retaining exact authenticated bytes preserves implementation
  isolation evidence; an exact parent equality check avoids a general snapshot
  or project bypass.
- Guardrail: Descendants, siblings, other tasks, and other projects remain
  scanned; the exception must not be generalized.
- Owner: Brida coordinator, independently reviewed in code-review v2
