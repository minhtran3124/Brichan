# Pull request description

Regenerable description built only from verified evidence. It never authorizes or instructs remote action.

## Artifact metadata

- Task ID: `MEMORY-001`
- Task level: `2`
- Artifact: `pr-desc`
- Artifact version: `1`
- Origin: `generator:MEMORY-001-reviewed-v1`
- Owner: `generator`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `019fe6e0-efcf-74d1-9c61-5297332e0ae6`
- Effective route: `coordinator`
- Effective model: `gpt-5.6-sol`
- Effective effort: `medium`
- Reviewing session: `019fe769-cbd8-7bc3-b4fc-ec4604200b56`
- Review verdict: `PASS`

## Remote action

- Remote action authorized: `no`

## Claim or decision

Repair durable product and project memory, derive the manual wheel path from
`VERSION`, align the installed worker-lifecycle contract, and add an offline,
read-only consistency checker wired into `make check`. No remote action is
authorized or performed.

## Evidence

- `code-review.md` version 2 records final `PASS` after all three initial findings were remediated.
- The checker, 27 focused tests, 400 unit tests, 79 contract tests, 90 integration tests, and full `make check` pass.
- `scripts/check_project_memory.py`, its unit/contract coverage, Makefile wiring, and the repository-path inventory implement the consistency gate.
- The originating request explicitly excludes push and pull-request creation.

## Uncertainty

- PyPI state was not rechecked over the network; durable claims rely on accepted local release history and workflow evidence.
- Excluded checker scope and the unreleased packaged-policy hash change remain documented in `code-review.md`.
