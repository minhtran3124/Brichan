# Brichan

![Brichan coordinating a team of AI workers](assets/brida-hero.png)

Brichan is an AI Chief of Staff for Codex and Claude Code. Give it a project
goal; it keeps the necessary context, coordinates independent workers through
Herdr, checks their evidence, and records useful project state outside chat.
Its existing runtime package and console commands remain `brida` and
`brida-*` for compatibility.

## Requirements

Brida coordinates independent worker sessions through
[Herdr](https://herdr.dev), the approved worker-control plane. A single
coordinator session runs without it, but Herdr is required as soon as Brida
hands off bounded tasks to workers.

Install it on Linux or macOS:

```bash
curl -fsSL https://herdr.dev/install.sh | sh
```

or via Homebrew on macOS:

```bash
brew install herdr
```

Then install the integration for your runtime, e.g.:

```bash
herdr integration install claude
herdr integration install codex
```

See the [Herdr documentation](https://herdr.dev/docs/) for other install
methods (mise, Nix, Windows preview) and integration options.

## Current dogfood scope

The primary one-user dogfood path is now an installed Python package running
inside an existing top-level Git repository. Installed-project mode currently
supports Codex on POSIX-compatible systems with Python 3.10+. Herdr is needed
only when Brida coordinates independent worker sessions.

Brida is published to PyPI as `brichan`, while the importable package stays
`brida` and every console command keeps its existing name:

```bash
pip install brichan
```

To install from this repository instead — for development, or to run a change
that is not released yet — use the installer. It can be invoked from any
directory and does not activate or modify the target project's virtual
environment:

```bash
/absolute/path/to/brida/scripts/install-brida
```

By default, the script creates a dedicated environment at
`$HOME/.local/share/brida/venv` and command symlinks in `$HOME/.local/bin`.
It automatically selects an available Python 3.10+ interpreter with `pip`,
`setuptools`, `venv`, and `wheel`, builds from a temporary source snapshot,
and installs all Brida console commands. No virtualenv activation is
required. If the command directory is not on `PATH`, the installer prints
the exact export to add to the shell profile.

## Initialize a project

Preview the complete footprint before writing:

```bash
brida init --project /absolute/path/to/repository
brida init --apply --project /absolute/path/to/repository
```

`init` defaults to dry-run and performs zero writes. `--apply` creates only a
versioned `.brida/` directory containing managed policy, model routing, Herdr
skill resources, and mutable project memory. Repeating it against healthy
state is idempotent.

Diagnose and launch from any directory with an explicit target:

```bash
brida status --project /absolute/path/to/repository
brida doctor --project /absolute/path/to/repository
brida run --project /absolute/path/to/repository -- <codex arguments>
```

From inside a healthy initialized repository, bare `brida` also launches
Codex. The installed entrypoint:

- leaves `AGENTS.md`, `CLAUDE.md`, `.codex/`, and provider configuration
  untouched;
- launches external `codex` directly at the target root and never executes
  target-owned `bin/brida-*` wrappers;
- injects package-owned Brida policy and Herdr skill discovery;
- rejects native delegation, permission bypasses, cwd/scope widening, profiles,
  remote execution, and arbitrary Codex configuration before `--`;
- treats option-looking text after `--` as literal prompt content.

State diagnostics reject malformed, dangling, symlinked, inaccessible, or
incompatible `.brida/` state without silently repairing it. Schema v1 has no
automatic migration: package-version changes require deliberate backup and
reinitialization. See the
[installed Codex dogfood guide](docs/guides/installable-dogfood.md) for the
exact footprint, exit codes, safeguards, and compatibility boundary.

## Checkout compatibility and development

The original checkout workflow remains available for development and for
Claude Code:

```bash
bin/brida
bin/brida --runtime claude
```

From a checkout, `brida --help` and `brida --version` report Brida itself; a
checkout has no project state to launch into. Name a runtime to reach its own
help instead, with `brida --runtime codex --help` or `bin/brida-codex --help`.

Checkout mode uses package-owned `bin/brida-*` wrappers. Installed-project mode
does not. Coordinator defaults and worker routes are settings-driven, so the
coordinator and implementation, review, planning, or scan workers may use
different runtimes. See the [model-routing guide](docs/guides/model-routing.md)
to change defaults, select a named route, or use a one-off override.

The `brida-codex` and `brida-claude` console commands installed by `brichan`
remain checkout-oriented: `brida-codex` resolves coordinator routing from a
Brida source checkout (or `BRIDA_ROOT`) or from an already-initialized
project's `.brida/` state, while `brida-claude` resolves only from a checkout
or `BRIDA_ROOT`. Both are for development and checkout use, not standalone
installed-project launches. `--help`/`--version` work from any directory; the
[installed Codex dogfood guide](docs/guides/installable-dogfood.md) has the
exact boundary.

## How it works

1. You describe the outcome and constraints.
2. Brida reads only the project context needed for that work.
3. Brida gives bounded tasks to independent workers through Herdr.
4. Brida verifies results, records decisions and status, then reports back.

Herdr is the worker control plane. Native runtime delegation stays disabled so
worker ownership, evidence, and cleanup remain visible.

Project context lives in `projects/<project-slug>/` as a small set of Markdown
files for overview, current state, tasks, decisions, and references. Read the
[project memory policy](docs/policy/memory-policy.md) for the contract.

## Development

Run the complete local validation suite before sharing a change:

```bash
make check
```

You can also run individual layers while iterating:

```bash
make test-unit
make test-contract
make test-integration
make package-check
```

The importable implementation is in `src/brida/`; stable command wrappers are
in `bin/` and `scripts/`. See [CONTRIBUTING.md](CONTRIBUTING.md) for the change
workflow and [the repository layout](docs/architecture/repository-layout.md)
for module boundaries.

## Learn more

- [Model routing and worker launch settings](docs/guides/model-routing.md)
- [Installed Codex dogfood](docs/guides/installable-dogfood.md)
- [Documentation index](docs/index.md)
- [Operating principles](docs/policy/operating-principles.md)
- [Security policy](SECURITY.md)

## License

Brida is available under the [MIT License](LICENSE).
