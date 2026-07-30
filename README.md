# Brichan

![Brichan coordinating a team of AI workers](assets/brichan-hero.png)

Brichan is an AI Chief of Staff for Codex and Claude Code. Give it a project
goal; it keeps the necessary context, coordinates independent workers through
Herdr, checks their evidence, and records useful project state outside chat.

## Requirements

Brichan coordinates independent worker sessions through
[Herdr](https://herdr.dev), the approved worker-control plane. A single
coordinator session runs without it, but Herdr is required as soon as Brichan
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
only when Brichan coordinates independent worker sessions.

Brichan is published to PyPI as `brichan`, and every console command keeps
its existing name:

```bash
pip install brichan
```

To install from this repository instead — for development, or to run a change
that is not released yet — use the installer. It can be invoked from any
directory and does not activate or modify the target project's virtual
environment:

```bash
/absolute/path/to/brichan/scripts/install-brichan
```

By default, the script creates a dedicated environment at
`$HOME/.local/share/brichan/venv` and command symlinks in `$HOME/.local/bin`.
It automatically selects an available Python 3.10+ interpreter with `pip`,
`setuptools`, `venv`, and `wheel`, builds from a temporary source snapshot,
and installs all Brichan console commands. No virtualenv activation is
required. If the command directory is not on `PATH`, the installer prints
the exact export to add to the shell profile.

## Initialize a project

Preview the complete footprint before writing:

```bash
brichan init --project /absolute/path/to/repository
brichan init --apply --project /absolute/path/to/repository
```

`init` defaults to dry-run and performs zero writes. `--apply` creates only a
versioned `.brichan/` directory containing managed policy, model routing,
Herdr skill resources, and mutable project memory. Repeating it against
healthy state is idempotent.

Diagnose and launch from any directory with an explicit target:

```bash
brichan status --project /absolute/path/to/repository
brichan doctor --project /absolute/path/to/repository
brichan run --project /absolute/path/to/repository -- <codex arguments>
```

From inside a healthy initialized repository, bare `brichan` also launches
Codex. The installed entrypoint:

- leaves `AGENTS.md`, `CLAUDE.md`, `.codex/`, and provider configuration
  untouched;
- launches external `codex` directly at the target root and never executes
  target-owned `bin/brichan-*` wrappers;
- injects package-owned Brichan policy and Herdr skill discovery;
- rejects native delegation, permission bypasses, cwd/scope widening, profiles,
  remote execution, and arbitrary Codex configuration before `--`;
- treats option-looking text after `--` as literal prompt content.

State diagnostics reject malformed, dangling, symlinked, inaccessible, or
incompatible `.brichan/` state without silently repairing it. Schema v1 has no
automatic migration: package-version changes require deliberate backup and
reinitialization. See the
[installed Codex dogfood guide](docs/guides/installable-dogfood.md) for the
exact footprint, exit codes, safeguards, and compatibility boundary.

## Checkout compatibility and development

The original checkout workflow remains available for development and for
Claude Code:

```bash
bin/brichan
bin/brichan --runtime claude
```

From a checkout, `brichan --help` and `brichan --version` report Brichan
itself; a checkout has no project state to launch into. Name a runtime to
reach its own help instead, with `brichan --runtime codex --help` or
`bin/brichan-codex --help`.

Checkout mode uses package-owned `bin/brichan-*` wrappers. Installed-project
mode does not. Coordinator defaults and worker routes are settings-driven, so
the coordinator and implementation, review, planning, or scan workers may use
different runtimes. See the [model-routing guide](docs/guides/model-routing.md)
to change defaults, select a named route, or use a one-off override.

The `brichan-codex` and `brichan-claude` console commands installed by
`brichan` remain checkout-oriented: `brichan-codex` resolves coordinator
routing from a Brichan source checkout (or `BRICHAN_ROOT`) or from an
already-initialized project's `.brichan/` state, while `brichan-claude`
resolves only from a checkout or `BRICHAN_ROOT`. Both are for development and
checkout use, not standalone installed-project launches. `--help`/`--version`
work from any directory; the
[installed Codex dogfood guide](docs/guides/installable-dogfood.md) has the
exact boundary.

## How it works

1. You describe the outcome and constraints.
2. Brichan reads only the project context needed for that work.
3. Brichan gives bounded tasks to independent workers through Herdr.
4. Brichan verifies results, records decisions and status, then reports back.

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

The importable implementation is in `src/brichan/`; stable command wrappers are
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

Brichan is available under the [MIT License](LICENSE).
