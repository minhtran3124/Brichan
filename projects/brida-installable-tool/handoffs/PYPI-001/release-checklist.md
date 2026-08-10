# `brichan` PyPI release checklist

The `brichan` distribution is published on PyPI
(<https://pypi.org/project/brichan/>) and releases are automated: pushing a
`vX.Y.Z` tag triggers `.github/workflows/publish.yml`, which builds, validates,
and publishes via PyPI Trusted Publishing. The first fully automated publish
was `v0.9.0` (2026-08-03); earlier versions (0.5.0–0.8.0) were uploaded
manually while the publisher configuration was incomplete.

## One-time PyPI setup (completed)

- [x] PyPI ownership of the `brichan` project name is held by the publishing
      account (releases 0.5.0 onward live under it).
- [x] PyPI Trusted Publisher configured on 2026-08-03: owner `minhtran3124`,
      repository `Brichan`, workflow `publish.yml`, environment `pypi`. The
      claims must match exactly — a mismatch fails the publish job with
      `invalid-publisher`.
- [x] `pypi` GitHub Environment exists in repository settings, matching the
      `environment: pypi` block in `.github/workflows/publish.yml`.
- [ ] TestPyPI rehearsal environment: deliberately not set up. Add a
      `testpypi` environment, workflow, and matching Trusted Publisher first
      if a pre-release publish rehearsal is ever wanted.

## Per-release steps

- [ ] Bump `pyproject.toml`, `VERSION`, `src/brichan/__init__.py`, and
      `CHANGELOG.md` together for the release version (move the Unreleased
      section into a dated entry).
- [ ] Reconcile durable memory in the **same** change as the bump, before the
      verification run: `PRODUCT.md` (`Last verified:` and `Latest published
      version:`), `projects/brida-installable-tool/current-state.md`, the
      seven `projects/<slug>/overview.md` lifecycle values, and
      `projects/index.md` statuses. `make check` runs `make memory-check`,
      which **fails** the contract suite when `PRODUCT.md` still names the
      previous version or carries a `Last verified:` date earlier than the
      CHANGELOG release date — so reconciling after the verification run just
      means running it twice.
- [ ] Run the full local verification before tagging:
      `PYTHONDONTWRITEBYTECODE=1 make check`, a clean `python -m build`,
      `twine check` on both artifacts, and an installed-wheel smoke test in a
      disposable virtual environment. Remove any stale `dist/`,
      `src/brichan.egg-info/`, or `build/` artifacts first — the contract and
      integration suites fail on leftovers.
- [ ] Commit the bump and the memory reconciliation together as
      `chore(release): bump version to X.Y.Z` on `main`.
- [ ] Push a `vX.Y.Z` tag matching `pyproject.toml`'s `version`; the tag push
      is the only trigger for `.github/workflows/publish.yml`, and the
      workflow refuses a tag that does not match the package version.
- [ ] Create the GitHub release for the tag with notes drawn from the
      CHANGELOG entry.
- [ ] Verify the published page and `pip install brichan==X.Y.Z` in a
      disposable environment after the workflow completes. The PyPI JSON API
      reflects the release immediately; the pip simple index can lag a minute
      or two behind it.
- [ ] If the publish job fails after a successful build, fix the cause and
      re-run only the failed job (`gh run rerun <run-id> --failed`); the
      built artifacts are reused.

Schema v1 note: a package-version change makes previously initialized
`.brichan/` project state report `incompatible` by design (no automatic
migration). Installed projects need a deliberate backup and re-init after
upgrading.

## Known gaps intentionally left open

- **`project.urls`**: the repository went public in 0.12.0 and
  `public_repository` in `config/pypi-readme.json` was flipped to match, so
  the generated long description keeps images and absolute links. No
  `project.urls` (Homepage/Source/Issues) are set in `pyproject.toml` yet,
  so the PyPI sidebar still has no project links — add them when convenient.
- **TestPyPI**: no TestPyPI workflow, environment, or Trusted Publisher
  exists; add one first if a pre-release publish rehearsal is wanted.
- **sdist scope**: the source distribution intentionally contains only the
  installable package inputs. It can be installed and built, but it is not a
  test-suite source archive.
