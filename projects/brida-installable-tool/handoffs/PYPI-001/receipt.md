## Identity

- Receipt schema version: `2`
- Task ID: `PYPI-001`
- Project: `brida-installable-tool`
- Handoff timestamp (UTC): `2026-07-29T11:34:41Z`
- Receipt role: `standalone`
- Parent receipt path: `null`
- Attempt: `1`
- Replaces session: `null`
- Attempt origin: `initial`
- Attempt lifecycle state: `complete`
- Prior attempt state: `null`
- Replacement evidence path: `null`

## Plan version

- Artifact or plan ID: `brichan-pypi-readiness`
- Version: `1`
- Status: `reviewed`

## Sessions

| Role | Provider | Model | Brida-owned pane | Session |
| --- | --- | --- | --- | --- |
| Planner | `codex` | `gpt-5.6-terra` | `w1X:pA` | `019face0-0d80-7661-8a87-0ca3afb458bf` |
| Implementer | `claude` | `sonnet` | `w1X:p3F` | `fd8eb95a-c9e8-44fc-aae5-382f211cf685` |
| Reviewer | `claude` | `opus` | `w1X:p3G` | `8f6ea709-7606-4efd-b80c-02dbdaab77cc` |

## Scope

- In scope: Prepare a PyPI-ready `brichan` distribution while retaining the `brida` import package and all `brida-*` console commands; build both artifacts, validate metadata/README, add release CI scaffolding without publishing, and bump the unreleased release to `0.5.0`.
- Authorized paths: `pyproject.toml`, `VERSION`, `src/brida/__init__.py`, `CHANGELOG.md`, `README.md`, `docs/guides/installable-dogfood.md`, `CONTRIBUTING.md`, `Makefile`, `.github/workflows/ci.yml`, `.github/workflows/publish.yml`, `tests/`, `config/repository-paths.json`
- Exclusive write ownership: same as authorized paths
- Branch: `cli`
- Worktree: `primary`

## Non-goals

- Excluded work: Rename the local directory, rename or mutate the remote Git repository, publish to TestPyPI/PyPI, create accounts/tokens, alter the Python import package or `brida-*` commands, change model routing/catalog, or modify existing project memory outside this receipt.

## Acceptance criteria

| Criterion ID | Status | Evidence |
| --- | --- | --- |
| PYPI-1 | `pass` | `pyproject.toml`, `VERSION`, `src/brida/__init__.py`, and `CHANGELOG.md` agree on `brichan` `0.5.0`; wheel metadata retains all five `brida-*` commands. |
| PYPI-2 | `pass` | Independent clean builds produced `brichan-0.5.0.tar.gz` and `brichan-0.5.0-py3-none-any.whl`; wheel import, command smoke tests, and packaged resources passed. |
| PYPI-3 | `pass` | CI builds sdist/wheel on Python 3.10 and 3.13, runs `twine check`, installs a clean wheel, and smoke-tests the documented supported commands. |
| PYPI-4 | `pass` | `publish.yml` is tag-gated, tag/version-checked, OIDC-only, environment-bound, and cannot run a real publish until external PyPI trusted-publisher setup exists. |

## Verification

| Command | Result |
| --- | --- |
| clean `python -m build`, artifact install, and command smoke | pass — independent Claude Opus review |
| `python -m twine check dist/*` | pass — independent Claude Opus review |
| packaging metadata and CLI regression tests | pass — 4 packaging and 15 entrypoint tests |
| `PYTHONDONTWRITEBYTECODE=1 make check` | pass — 91 unit, 41 contract, 32 integration tests plus repository gates |

## Implementation evidence

- Changed artifacts: distribution metadata/version/changelog; README and install guide; CI/package and tag-gated publish workflows; release checklist; entrypoint behavior and regression tests.
- Diff evidence: OIDC publisher pinned to `ba38be9e461d3875417946c167d0b5f3d385a247` (`release/v1`), version-tag guard added, and no token/secret references in the publish workflow.
- Test evidence: clean artifacts, `twine check`, installed artifact smoke, focused packaging/CLI tests, full `make check`, and `git diff --check` passed.

## Review verdict

- Verdict: `PASS`
- Findings: Reviewer found no blocking defect. Pinning the publisher action, tag/version validation, changelog alignment, and explicit sdist scope were remediated after review. Public repository URL/README image and external PyPI setup remain release prerequisites.

## Risks and open decisions

- Risks: Public repository URL and remote rename are intentionally deferred; release workflow remains inert until trusted publishers are configured.
- Open decisions: Confirm remote repository rename and final public URL before enabling a real PyPI release.

## Cleanup status

- Brida-owned panes closed: `yes`
- Project memory updated: `yes`
