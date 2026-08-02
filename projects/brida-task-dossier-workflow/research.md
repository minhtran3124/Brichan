# Adaptive task dossier research

Status: complete research; full-doc evidence direction accepted
Verified: 2026-08-02

## Accepted amendment — full docs at every level

The user accepted a stronger evidence requirement after the initial research:
every Level 0/1/2 task creates the same complete dossier. Risk level controls
document depth, reviewer strength, and authorization gates—not artifact
presence.

The complete baseline is `index.md`, read-only `request.md`,
`requirements.md`, `brief.md`, `options.md`, `design.md`,
`client-follow-up-questions.md`, versioned `plan.md`, `plan-review.md`,
`code-review.md`, `pr-desc.md`, and canonical `receipt.md`.

A phase may be `not-required`, but its artifact must contain a concrete
rationale and evidence. Empty placeholders do not count. Document presence
proves traceability only; confidence requires source evidence, unresolved
uncertainty, exact author/reviewer session identity, effective route/model, and
a review verdict.

## Executive conclusion

The current repository can support the intent behind the screenshot. The
accepted fit is **one full task dossier at every task level**, with adaptive
evidence depth.

Recommended direction:

```text
Intake → Explore → Design → Plan → Plan Review → Execute → Code Review → Close/Ship
```

- Use a stable task ID as identity. Branch and worktree are attributes.
- Keep project memory, task packets, and receipts authoritative in their
  existing domains.
- Reuse `handoffs/<task-id>/` as the artifact home for every tracked task.
- Create the same complete document set for Level 0, Level 1, and Level 2.
- Preserve request provenance after redaction and with explicit amendments.
- Always create `pr-desc.md`; if no PR is authorized, record
  `not-authorized`/`not-required` without performing remote action.

Overall feasibility:

| Dimension | Assessment | Notes |
|---|---|---|
| Checkout mode | High | Existing project memory and handoff folders can host the complete dossier |
| Installed mode prototype | Medium | Extra mutable content may be technically tolerated, but it is not part of the documented schema-v1 footprint |
| Installed mode product contract | Low without schema work | A managed/discoverable dossier tree needs an explicit versioned contract and compatibility tests |
| Full dossier for every task | Medium–High | Strong traceability; concise templates and validation must control ceremony |
| Adaptive evidence depth | High | Same artifacts, stronger evidence and review as risk rises |

## What the screenshot gets right

1. **Context should survive chat sessions.** This directly matches Brichan's
   durable-memory and context-economy goals.
2. **Intake, exploration, and design are distinct reasoning modes.** They should
   be available before planning when ambiguity or architecture warrants them.
3. **The original request has provenance value.** A later session should be able
   to distinguish original intent from clarified or amended scope.
4. **A task needs a navigable evidence trail.** A compact index linking request,
   plan, implementation evidence, review, and closure improves resumption.
5. **Reviews should leave durable findings.** Review evidence should not vanish
   into chat.
6. **Simple tasks should preserve the complete stage trace.** Non-material
   phases are explicitly `not-required` with rationale and evidence.

These ideas also appear in current spec-driven tools, but with fewer core
artifacts. GitHub Spec Kit uses a core `Spec → Plan → Tasks → Implement`
workflow and makes clarify/checklist/analyze conditional quality gates. Kiro
uses requirements, design, and tasks, including a Quick Spec path. OpenSpec
uses proposal, planning artifacts, implementation, and archive. The useful
industry pattern is staged intent with conditional gates—not a universal
eleven-file minimum.

Official references:

- [GitHub Spec Kit](https://github.github.io/spec-kit/)
- [GitHub Spec Kit agentic SDD](https://github.github.io/spec-kit/reference/agentic-sdd.html)
- [Kiro specs](https://kiro.dev/docs/web/specs/)
- [OpenSpec workflow](https://openspec.dev/docs/opsx)

## Current Brichan primitives to reuse

Verified repository facts:

- The coordinator already converts a request into objective, scope,
  deliverables, acceptance criteria, constraints, permissions, and escalation
  conditions (`docs/policy/operating-principles.md`).
- Durable project truth is deliberately split across `overview.md`,
  `current-state.md`, `tasks.md`, `decisions.md`, and `references.md`
  (`docs/policy/memory-policy.md`).
- Task packets already carry bounded assignment context
  (`.agents/skills/herdr-orchestration/references/task-packet.md`).
- Receipts already carry task identity, plan version, sessions, scope,
  branch/worktree, acceptance evidence, verification, implementation evidence,
  review verdict, risks, and cleanup
  (`.agents/skills/herdr-orchestration/references/handoff-receipt.md`).
- Independent review already has a severity/evidence contract
  (`docs/policy/reviewer.md`).
- Canonical receipts already live at
  `projects/<slug>/handoffs/<task-id>/receipt.md`.
- Installed mode has a fixed schema-v1 manifest with eight immutable resources
  and six mutable project-memory paths: one index plus five project files
  (`src/brichan/lifecycle.py`).

This means Brichan is not missing a lifecycle envelope. It is mainly missing:

- an explicit task materiality classification;
- a uniform full-document evidence envelope;
- original-request provenance and amendment rules;
- a compact per-task navigation view;
- conditional ship-output generation;
- phase transition and ownership rules.

## Artifact-by-artifact evaluation

| Screenshot artifact | Brichan-native treatment | Requirement |
|---|---|---|
| `index.md` | Thin manifest of links, task class, current phase, canonical status pointer | Required |
| `request.md` | Redacted provenance snapshot; immutable origin plus explicit amendment pointers | Required; never raw chat by default |
| `requirements.md` | Testable requirements and acceptance mapping | Required |
| `brief.md` | Concise task context without copying project memory | Required |
| `options.md` | Alternatives considered; selected durable choice promoted to project `decisions.md` | Required |
| `design.md` | Architecture, interfaces, compatibility, risks, rollback or evidenced no-change decision | Required |
| `client-follow-up-questions.md` | Questions, answers, or evidenced `not-required` status | Required |
| `plan.md` | Versioned implementation plan with authorized paths and acceptance mapping | Required |
| `plan-review.md` | Independent findings; reviewer does not rewrite the plan | Required |
| `code-review.md` | Implementation review or evidenced non-applicability; receipt owns final verdict | Required |
| `pr-desc.md` | Generated ship text or explicit `not-authorized`/`not-required` record | Required |

## Recommended task levels

### Level 0 — Simple

Use when work is low-risk, sequential, tightly coupled, and readily verified.

Uses the full dossier with concise evidence. Options/design/questions may be
`not-required` only with rationale. Plan/design review remains mandatory.

### Level 1 — Standard

Use for material implementation, research, explicit planning, resumed work, or
delegated work whose context should survive.

Uses the same dossier with material requirements, options, design, plan, review,
implementation evidence, and closure evidence.

### Level 2 — High-risk

Use for security/privacy, destructive changes, production/deployment, public
contracts, multi-writer work, or repeated worker failure.

Uses the same dossier with greater depth:

- explicit requirements and design;
- risk, rollback, and authorization decisions;
- parent/child receipts for multiple writers;
- independent review with a durable report;
- explicit closure/ship authorization and evidence.

## Source-of-truth rules

| Concern | Authority |
|---|---|
| Stable project facts | `overview.md` |
| Current project status | `current-state.md` |
| Active ownership | project `tasks.md` |
| Durable project decisions | `decisions.md` |
| Evidence discovery | `references.md` |
| Original task provenance | redacted immutable request snapshot, when created |
| Current accepted scope and plan | versioned accepted `plan.md` |
| Worker lifecycle and completion evidence | canonical receipt |
| Review detail | linked review artifact; receipt owns final verdict |
| Branch/worktree | receipt metadata, never task identity |
| PR text | generated output, never task truth |

The task `index.md` is a projection. It may point to authorities but must not
copy their changing content.

## What should not be implemented

- Empty files or self-confidence claims used as substitutes for evidence.
- Branch names as primary task IDs.
- Reviewer back-writing into an accepted plan.
- Silent replacement of original intent after clarification.
- Exact raw prompts or client data stored without redaction/retention rules.
- Shared mutable task artifacts without explicit ownership.
- A PR description or remote action implied by the word `Ship`.
- Document presence used as evidence that a phase passed.
- A schema-v1 installed-state expansion disguised as an implementation detail.
- A second task status that can disagree with `tasks.md` or the receipt.

## Key risks and mitigations

| Risk | Mitigation |
|---|---|
| Parallel sources of truth | Explicit authority table and link-only index |
| Documentation ceremony | Concise Level 0 content, generated metadata, and evidence-backed `not-required` decisions |
| Stale accepted plans | Version/status fields; amendments create a new version |
| Review changes intent retroactively | Findings reference plan version; remediation creates a follow-up version/attempt |
| Branch rename/reuse | Stable coordinator-assigned task ID |
| Sensitive request retention | Redaction, opt-in exact snapshot, no raw transcript |
| Concurrent writer conflicts | Coordinator-owned shared artifacts; exclusive writer paths |
| Installed-state incompatibility | Checkout pilot first; explicit schema decision later |
| “Ship” exceeds authority | Separate local close from authorized PR/publish/deploy actions |

## Feasibility detail

### Checkout mode

No new top-level workflow root is required for a pilot. Every tracked task can
reuse:

```text
projects/<slug>/handoffs/<task-id>/
├── index.md
├── request.md            # redacted, read-only provenance
├── requirements.md
├── brief.md
├── options.md
├── design.md
├── client-follow-up-questions.md
├── plan.md               # versioned
├── plan-review.md
├── code-review.md
├── pr-desc.md
└── receipt.md            # canonical lifecycle/evidence envelope
```

Every task creates this directory. Level determines evidence depth, not which
files exist. This is feasible with concise templates and contract checks;
automation can follow after dogfood.

### Installed-project mode

Schema v1 inventories exact managed and mutable paths. The current inspector
checks required paths and does not provide a contract for discovering,
validating, upgrading, or cleaning arbitrary task directories. An
implementation might technically tolerate extra files, but relying on that
would create undocumented state.

Therefore:

1. Do not add dossiers to schema v1 as an invisible convention.
2. Pilot in checkout mode.
3. If dogfood proves value, define a versioned installed-state contract,
   compatibility behavior, and explicit backup/reinitialization path.
4. Preserve the product rule against silent migration or repair.

## Comprehensive verdict

**Go** for a checkout-only, full-docs pilot with adaptive evidence depth.

**No-go** for empty evidence-free templates or changing installed schema before
measured dogfood evidence.

The main product improvement is not “more Markdown.” It is a small state
machine with stable task identity, conditional evidence gates, clear ownership,
and one authoritative trail that can be resumed safely.
