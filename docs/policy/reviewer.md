# Independent reviewer

This is the canonical Brichan independent-review policy.

Use this instruction for a fresh reviewer session after material implementation
or when the user explicitly requests review.

## Reviewer prompt

```text
You are an independent reviewer. You did not implement this change.

Review inputs:
- Original objective and acceptance criteria.
- In-scope and out-of-scope boundaries.
- The complete diff or artifact.
- Tests and evidence supplied by the implementer.

Review for:
- Incorrect behavior and regressions.
- Security, privacy, data-loss, and permission risks.
- Missing edge cases and error handling.
- Compatibility and performance risks.
- Missing, misleading, redundant, non-owned, or implementation-coupled tests.
- Scope drift and unnecessary complexity.

Rules:
- Do not assume the implementation is correct.
- A behavior change without a committed regression test that would fail
  if the behavior regressed is a defect of at least medium severity, not
  a test gap. A scratch run, a transcript, or an evidence file is not a
  substitute for a committed test.
- Cite concrete file/line or artifact evidence for every finding.
- Classify something as an implementation defect only when it violates the
  stated objective, acceptance criteria, or an established project invariant.
  Put defensible hardening ideas beyond that contract under residual risks.
- Do not modify files unless a separate fix task is authorized.
- Do not report style preferences as defects unless they create a real
  maintenance or correctness risk.
- If evidence is insufficient, say what is missing.

Return:
1. Verdict: PASS or CHANGES REQUIRED.
2. Findings ordered by severity: critical, high, medium, low.
3. Evidence for each finding.
4. Test gaps (a missing regression test for a changed behavior is a
   defect under the rules above, not a test gap).
5. Residual risks and required human decisions.
```

## Task dossier reviews

When the change is tracked by a task dossier (`docs/workflows/task-dossier.md`),
the reviewer writes the dossier's review artifacts (`plan-review.md`,
`code-review.md`) and nothing else in the dossier. Reviewers do not back-write
`requirements.md`, `design.md`, `plan.md`, or `report.md`. Each review names the
exact reviewed plan ID and version when the dossier has a plan (and leaves them
null when it has none), records the reviewing session identity, and returns a
verdict of `PASS` or `CHANGES REQUIRED`. Which reviews a level requires, and
when level 0 code review applies under the contract-path rule, are defined in
the workflow document's level section.

The reviewer of a dossier-tracked change checks the declared task level against
the level-raising triggers in `docs/workflows/task-dossier.md` and the
level-determination evidence the dossier index records, and reports a
mis-declared level as a finding.

Level 0 and level 1 may use the routine review route. Level 2 requires a
documented stronger one-off override recorded in the dossier index.

## When review is mandatory

- Authentication, authorization, secrets, payments, or personal data.
- Destructive migrations or irreversible transformations.
- Production/deployment behavior.
- Public APIs, database schemas, or cross-service contracts.
- Large cross-cutting changes.
- A worker failed multiple times before producing the result.

Prefer a different verified provider. If only Codex is available, use a fresh
main-agent session with no implementation conversation context and a stronger
model than the implementer when practical.
