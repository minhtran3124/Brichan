# Brief

Short problem framing: outcome, constraints, and success signal.

## Artifact metadata

- Task ID: `DOGFOOD-006`
- Task level: `1`
- Artifact: `brief`
- Artifact version: `1`
- Origin: `coordinator:2026-08-03-doctor-json-plan`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fc5cb-b798-7c50-8d3d-b86e27aa04f8`
- Effective route: `coordinator`
- Effective model: `gpt-5.6-sol`
- Effective effort: `medium`
- Reviewing session: `<session identifier or null>`
- Review verdict: `<PASS, CHANGES REQUIRED, or null>`

## Claim or decision

Brichan needs a machine-readable, read-only health snapshot for the current
checkout. Success means an operator or script can identify the repository root,
Git state, required policy/config/memory files, and dependencies without
writing state or contacting Herdr.

## Evidence

- `src/brichan/lifecycle.py` currently exposes human-readable doctor lines only.
- The user's request and the checkout contract in `PRODUCT.md` define the
  required diagnostic domains and safety boundary.

## Uncertainty

- Installed-project text output must remain backward compatible while JSON is
  added as an explicit mode.
