# Task dossier index

Projection of task state. It links canonical authorities and never copies their content.

## Artifact metadata

- Task ID: `<TASK-000>`
- Task level: `<0, 1, or 2>`
- Artifact: `index`
- Artifact version: `<positive integer>`
- Origin: `<immutable origin marker>`
- Owner: `coordinator`
- Phase state: `<pending, active, passed, not-required, or blocked>`
- Applicability: `<required or not-required>`
- Applicability rationale: `null`
- Authorship: `<model or human>`
- Authoring session: `<session identifier or null>`
- Effective route: `<named route or null>`
- Effective model: `<model identifier or null>`
- Effective effort: `<effort or null>`
- Reviewing session: `<session identifier or null>`
- Review verdict: `<PASS, CHANGES REQUIRED, or null>`

## Task identity

- Task ID: `<TASK-000>`
- Task level: `<0, 1, or 2>`
- Project: `<project-slug>`
- Canonical receipt path: `projects/<project-slug>/handoffs/<TASK-000>/receipt.md`
- Project memory path: `projects/<project-slug>/current-state.md`
- Accepted plan ID: `<plan-id or null>`
- Accepted plan version: `<positive integer or null>`
- Review route strength: `<routine or stronger>`
- Review route override: `<documented one-off override or null>`
- Ship authorization: `<not-requested or user-authorized>`
- Ship authorization evidence: `<evidence or null>`

## Artifact status

| Artifact | Applicability | Phase state | Path |
| --- | --- | --- | --- |
| `index` | `<required or not-required>` | `<phase state>` | `index.md` |
| `request` | `<required or not-required>` | `<phase state>` | `request.md` |
| `requirements` | `<required or not-required>` | `<phase state>` | `requirements.md` |
| `brief` | `<required or not-required>` | `<phase state>` | `brief.md` |
| `options` | `<required or not-required>` | `<phase state>` | `options.md` |
| `design` | `<required or not-required>` | `<phase state>` | `design.md` |
| `client-follow-up-questions` | `<required or not-required>` | `<phase state>` | `client-follow-up-questions.md` |
| `plan` | `<required or not-required>` | `<phase state>` | `plan.md` |
| `plan-review` | `<required or not-required>` | `<phase state>` | `plan-review.md` |
| `code-review` | `<required or not-required>` | `<phase state>` | `code-review.md` |
| `pr-desc` | `<required or not-required>` | `<phase state>` | `pr-desc.md` |

## Claim or decision

`<claim or decision this artifact asserts>`

## Evidence

- `<repository or source evidence for the claim>`

## Uncertainty

- `<unresolved uncertainty, or a recorded statement that none remains>`
