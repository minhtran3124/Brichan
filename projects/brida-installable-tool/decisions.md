# Decision log

## 2026-07-29 — Explore installed CLI plus project initialization

- Status: superseded
- Context: Five independent assessments found strong package foundations but
  checkout-root coupling and no safe project lifecycle.
- Decision: Run bounded discovery and, only if it passes, a disposable
  prototype of an installed CLI plus explicit project initialization. Defer
  the MVP decision; retain clone mode and do not pursue full-repo vendoring.
- Rationale: This best separates tool-owned code from project-owned state while
  preserving current guardrails and enabling incremental validation.
- Trade-offs: Adds schema, migration, ownership, external-tool compatibility,
  and support obligations.
- Owner: Brida; final product authority remains with the user.
- Evidence: `assessment.md`; first independent verdict `CHANGES REQUIRED`,
  remediated before focused re-review.

## 2026-07-29 — One-user dogfood scope

- Status: accepted
- Context: The user is the first target user; a later cohort may contain 3–5
  trusted users.
- Decision: Proceed toward a narrowly supported installable dogfood tool.
  Exclude commercialization, market-demand gates, broad compatibility, and
  support for unrelated edge cases.
- Rationale: The immediate value is improving the owner's real Brida workflow,
  so direct use provides stronger evidence than market research.
- Trade-offs: The prototype may be intentionally environment- and
  runtime-specific; wider compatibility is deferred until a dogfood failure
  requires it.
- Owner: User.
- Evidence: User direction in the 2026-07-29 project turn; `assessment.md`.
- Supersedes: 2026-07-29 — Explore installed CLI plus project initialization.

## 2026-07-29 — Codex-first schema-v1 vertical slice

- Status: accepted
- Context: The one-user dogfood needs to run from an installed package inside
  an existing Git repository without a separate Brida checkout.
- Decision: Ship the first local vertical slice as Codex-only installed mode.
  `brida init` owns only a versioned `.brida/` footprint; project launch injects
  package-owned developer instructions and Herdr skill discovery through Codex
  CLI overrides and executes external `codex` directly at the target root.
  Checkout mode remains available only when the package proves it belongs to
  the `BRIDA_ROOT` checkout.
- Rationale: This creates the smallest end-to-end owner workflow while avoiding
  edits to target `AGENTS.md`, `.codex/`, `CLAUDE.md`, or root wrappers.
- Trade-offs: Installed mode uses a narrow Codex argument allowlist, schema v1
  has no repair/migration, and package upgrades require deliberate
  reinitialization. Windows, Claude installed mode, and broad repository shapes
  remain deferred.
- Owner: Brida within the user-approved one-owner dogfood scope.
- Evidence: `docs/guides/installable-dogfood.md`; installed-wheel integration
  tests; final independent reviewer verdict `PASS`; 152-test `make check`.

## 2026-07-29 — Dedicated external installer environment

- Status: accepted
- Context: The owner needs one-command installation from outside the Brida
  checkout without activating a virtual environment.
- Decision: Install Brida into a dedicated external venv and expose all console
  commands through guarded symlinks in a user command directory. Do not modify
  the target project's `.venv` or shell profile automatically.
- Rationale: Tool lifecycle stays independent from each target repository while
  `brida` remains directly executable.
- Trade-offs: Python 3.10+ with local `pip`, `setuptools`, `venv`, and `wheel`
  is still required; the user may need to add the command directory to `PATH`
  once.
- Evidence: `scripts/install-brida`; installed-dogfood integration tests;
  Claude Opus final verdict `PASS`; 155-check `make check`.

## 2026-07-29 — Brichan distribution identity with stable Brida runtime API

- Status: superseded
- Context: The tool needs a future pip/PyPI distribution identity while the
  owner relies on the existing `brida` imports and `brida-*` commands.
- Decision: Use `brichan` as the distribution and public repository-facing
  name for version `0.5.0`; retain the `brida` Python package and every
  existing console command. Prepare—but do not execute—PyPI Trusted Publishing.
- Rationale: It supports a future registry release without breaking the
  dogfood runtime or requiring target repositories to migrate command names.
- Trade-offs: The public repository URL, PyPI trusted publisher, GitHub `pypi`
  environment, and README image URL must be deliberately configured before the
  first upload.
- Owner: User.
- Evidence: `pyproject.toml`; `.github/workflows/publish.yml`;
  `handoffs/PYPI-001/receipt.md`; independent Claude Opus review `PASS`.

## 2026-08-09 — Brida → Brichan rename completed; project slugs retained

- Status: accepted
- Context: The earlier decision kept the `brida` Python package and `brida-*`
  commands while only the distribution was named `brichan`. That split is gone:
  the runtime package, console commands, `.brichan/` footprint, and installer
  are all `brichan`, and the distribution is published.
- Decision: `brichan` is the single name for the distribution, the importable
  package, the console commands, and the installed-project directory. The
  `projects/brida-*` memory slugs are deliberately retained, because renaming
  them would rewrite recorded history and every receipt pointer for no runtime
  benefit. Historical wording in `CHANGELOG.md`, existing receipts, and
  evidence files is preserved as written.
- Rationale: One runtime name removes the dual-identity trap the previous
  decision accepted as a temporary cost, while frozen slugs keep the audit
  trail intact.
- Trade-offs: Memory slugs and project titles read `brida` while the runtime
  reads `brichan`, so readers must know the slugs are historical labels.
- Owner: User.
- Evidence: `README.md`; `VERSION`; `scripts/install-brichan`;
  `src/brichan/`; `handoffs/MEMORY-001/receipt.md`.
- Supersedes: 2026-07-29 — Brichan distribution identity with stable Brida
  runtime API.
