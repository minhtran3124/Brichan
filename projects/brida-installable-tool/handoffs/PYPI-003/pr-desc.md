# Pull request description

Regenerable description built only from verified evidence. It never authorizes or instructs remote action.

## Artifact metadata

- Task ID: `PYPI-003`
- Task level: `2`
- Artifact: `pr-desc`
- Artifact version: `2`
- Origin: `projection:PYPI-003-pr-desc-v2`
- Owner: `generator`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fe9cf-025e-79b0-b809-a0edf58c883b`
- Effective route: `coordinator`
- Effective model: `gpt-5.6-sol`
- Effective effort: `medium`
- Reviewing session: `019feaa2-7fe1-7722-9a58-d059c10d99ed`
- Review verdict: `PASS`

## Remote action

- Remote action authorized: `no`

## Claim or decision

Confirm the public Brichan repository URL and restore the hero image in the
generated PyPI long description. Enable public rendering in the shipped config,
regenerate `README_PYPI.md`, pin the exact absolute raw URL in offline unit and
packaging-contract tests, and remove the completed URL/image gate from current
project and product memory.

## Evidence

- Anonymous probes verified `https://github.com/minhtran3124/Brichan` is public
  and the raw hero returned `200 image/png` on 2026-08-10.
- Twenty focused unit and eleven focused packaging-contract tests passed; the
  independent stronger review returned `PASS` with no findings.
- The complete 401-unit and 81-contract suites plus README, memory, and path
  gates passed. No push or PR mutation is authorized by this task.

## Uncertainty

- The live PyPI page will use the corrected long description only after a later,
  separately authorized release. Remote reachability remains point-in-time.
