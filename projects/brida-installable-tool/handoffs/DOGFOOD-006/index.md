# Task dossier index

Projection of task state. It links canonical authorities and never copies their content.

## Artifact metadata

- Task ID: `DOGFOOD-006`
- Task level: `1`
- Artifact: `index`
- Artifact version: `1`
- Origin: `projection:DOGFOOD-006-P1-v3+implementation`
- Owner: `coordinator`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fc5cb-b798-7c50-8d3d-b86e27aa04f8`
- Effective route: `coordinator`
- Effective model: `gpt-5.6-sol`
- Effective effort: `medium`
- Reviewing session: `019fc5f3-766d-74a2-8848-fce011562f93`
- Review verdict: `PASS`

## Task identity

- Task ID: `DOGFOOD-006`
- Task level: `1`
- Project: `brida-installable-tool`
- Canonical receipt path: `projects/brida-installable-tool/handoffs/DOGFOOD-006/receipt.md`
- Project memory path: `projects/brida-installable-tool/current-state.md`
- Accepted plan ID: `DOGFOOD-006-P1`
- Accepted plan version: `3`
- Review route strength: `routine`
- Review route override: `null`
- Ship authorization: `not-requested`
- Ship authorization evidence: `<evidence or null>`

## Artifact status

| Artifact | Applicability | Phase state | Path |
| --- | --- | --- | --- |
| `index` | `required` | `passed` | `index.md` |
| `request` | `required` | `passed` | `request.md` |
| `requirements` | `required` | `passed` | `requirements.md` |
| `brief` | `required` | `passed` | `brief.md` |
| `options` | `required` | `passed` | `options.md` |
| `design` | `required` | `passed` | `design.md` |
| `client-follow-up-questions` | `not-required` | `not-required` | `client-follow-up-questions.md` |
| `plan` | `required` | `passed` | `plan.md` |
| `plan-review` | `required` | `passed` | `plan-review.md` |
| `code-review` | `required` | `passed` | `code-review.md` |
| `pr-desc` | `required` | `passed` | `pr-desc.md` |

## Claim or decision

DOGFOOD-006 delivered and independently reviewed a read-only JSON doctor
diagnostic for source checkouts and installed projects.

## Evidence

- Implementation diff, focused tests, adversarial symlink/UTF-8 probes, and the
  PASS code review in this dossier.
- `make check` output and the final focused test run provide independent local
  validation evidence, with the generated-artifact caveat recorded below.

## Uncertainty

- Full validation has one known generated-artifact cleanliness failure and is
  rerun after coordinator-owned dossier artifacts are complete.
