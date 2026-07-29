# `brichan` PyPI release checklist

This repository is prepared for a future `brichan` release but nothing has
been published, tagged, or credentialed. The following must be done
deliberately, outside of this task, before a real release:

## One-time PyPI setup

- [ ] Confirm PyPI account/organization ownership of the `brichan` project
      name (or reserve it) before the first publish.
- [ ] Create a PyPI Trusted Publisher for this GitHub repository pointing at
      `.github/workflows/publish.yml`, the `pypi` environment, and the exact
      repository owner/name and branch/tag pattern that will publish.
- [ ] Create the `pypi` GitHub Environment in repository settings with
      required reviewers and/or branch/tag protection, matching the
      `environment: pypi` block in `.github/workflows/publish.yml`.
- [ ] Decide whether a `testpypi` environment and a matching Trusted
      Publisher are wanted for pre-release validation; this repository does
      not include a TestPyPI workflow.

## Per-release steps (not run by this task)

- [ ] Bump `pyproject.toml`, `VERSION`, `src/brida/__init__.py`, and
      `CHANGELOG.md` together for the release version.
- [ ] Run the full local verification (`PYTHONDONTWRITEBYTECODE=1 make check`,
      a clean `python -m build`, `twine check`, and an installed-artifact
      smoke test) before tagging.
- [ ] Push a `vX.Y.Z` tag matching `pyproject.toml`'s `version`; this is the
      only trigger for `.github/workflows/publish.yml`.
- [ ] Approve the `pypi` environment deployment when GitHub Actions requests
      it, if required reviewers are configured.
- [ ] Verify the published project page and `pip install brichan` in a
      disposable environment after the workflow completes.

## Known gaps intentionally left open

- **Public repository URL**: this checkout's `github` remote points at a
  non-standard host and is not confirmed to be a public, reachable URL, so no
  `project.urls` (Homepage/Source/Issues) were added to `pyproject.toml` and
  no such link was added to `README.md`. Provide a confirmed public URL to
  add these.
- **README hero image**: `README.md` embeds `assets/brida-hero.png` with a
  path relative to the repository. GitHub renders this correctly, but PyPI's
  README renderer will show a broken image, since a repository URL to
  resolve it against is not confirmed (see above). Fix once a public
  repository URL exists, either by adding `project.urls.Homepage` (some
  renderers can resolve relative links against it) or by switching to an
  absolute URL.
- **TestPyPI**: no TestPyPI workflow, environment, or Trusted Publisher was
  added; add one first if a pre-release publish rehearsal is wanted.
- **sdist scope**: the source distribution intentionally contains only the
  installable package inputs (`pyproject.toml`, `README.md`, `LICENSE`, and
  `src/`). It can be installed and built, but it is not a test-suite source
  archive.
