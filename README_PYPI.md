# Brichan

[![PyPI version](https://img.shields.io/pypi/v/brichan.svg)](https://pypi.org/project/brichan/)
[![Python versions](https://img.shields.io/pypi/pyversions/brichan.svg)](https://pypi.org/project/brichan/)
[![License](https://img.shields.io/pypi/l/brichan.svg)](https://pypi.org/project/brichan/)

Coding agents are very good at the work in front of them and very bad at
remembering why it was asked for. Context lives in a chat window, so it is lost
when the window closes; decisions are re-litigated, status is reconstructed from
memory, and the record of what was actually verified never outlives the session.
Running several agents at once makes this worse, not better, because nothing
owns the state between them.

This package introduces an AI Chief of Staff that sits above the coding agent
rather than inside it. You give it a project goal; it keeps only the context
that goal needs, hands bounded tasks to independent workers, checks the evidence
they return, and records decisions and status as files in your repository —
outside chat, where they survive the session.

The distribution, the importable package, and every console command all share
the name `brichan` / `brichan-*`.

## Requirements

Brichan coordinates independent worker sessions through
[Herdr](https://herdr.dev), the approved worker-control plane. A single
coordinator session runs without it, but Herdr is required as soon as Brichan
hands off bounded tasks to workers.

Install it on Linux or macOS:

```bash
$ curl -fsSL https://herdr.dev/install.sh | sh
```

or via Homebrew on macOS:

```bash
$ brew install herdr
```

Then install the integration for your runtime, e.g.:

```bash
$ herdr integration install claude
$ herdr integration install codex
```

See the [Herdr documentation](https://herdr.dev/docs/) for other install
methods (mise, Nix, Windows preview) and integration options.

## Installation

### PyPI

To install Brichan, simply:

```bash
$ pip install brichan
```

Brichan runs on POSIX-compatible systems with Python 3.10 or newer. It has no
runtime dependencies.

### From source

The repository ships an installer that builds a wheel and installs every console
command into a dedicated environment. It can be invoked from any directory and
does not activate or modify your project's virtual environment:

```bash
$ /absolute/path/to/brichan/scripts/install-brichan
```

By default it creates an environment at `$HOME/.local/share/brichan/venv` and
command symlinks in `$HOME/.local/bin`, selecting an available Python 3.10+
interpreter with `pip`, `setuptools`, `venv`, and `wheel`. If the command
directory is not on `PATH`, the installer prints the exact export to add to your
shell profile.

## Usage

Brichan operates on an existing top-level Git repository. Initialization
defaults to a dry run and performs zero writes, so you can preview the complete
footprint before anything is created:

```bash
$ brichan init --project /absolute/path/to/repository
```

Once the footprint looks right, apply it:

```bash
$ brichan init --apply --project /absolute/path/to/repository
```

This creates a versioned `.brichan/` directory holding managed policy, model
routing, Herdr skill resources, and mutable project memory, plus root
`AGENTS.md` and `CLAUDE.md` pointers when the repository does not already have
them. Repeating it against healthy state is idempotent. An existing
`AGENTS.md`, `CLAUDE.md`, `.codex/`, and provider configuration are left
untouched.

Diagnose and launch from any directory by naming the target explicitly:

```bash
$ brichan status --project /absolute/path/to/repository
$ brichan doctor --project /absolute/path/to/repository
$ brichan run --project /absolute/path/to/repository -- <codex arguments>
```

`doctor --json` emits the same diagnostics as machine-readable JSON for
scripts and CI. The default text output groups findings into a compact
callout with route and dependency summaries.

From inside a healthy initialized repository, bare `brichan` launches Codex
directly:

```bash
$ brichan
```

Arguments after `--` are forwarded to Codex. Option-looking text after `--` is
treated as literal prompt content, so a prompt beginning with a dash cannot
silently become a flag:

```bash
$ brichan run --project /absolute/path/to/repository -- --review the auth module
```

Before the `--`, Brichan rejects native delegation, permission bypasses,
cwd/scope widening, profiles, remote execution, and arbitrary Codex
configuration. State diagnostics reject malformed, dangling, symlinked,
inaccessible, or incompatible `.brichan/` state rather than silently repairing it.
Schema v1 has no automatic migration: a package-version change requires
deliberate backup and reinitialization.

### Coordinating workers

Herdr is the worker control plane. Native runtime delegation stays disabled so
worker ownership, evidence, and cleanup remain visible:

1. You describe the outcome and constraints.
2. Brichan reads only the project context that work needs.
3. Brichan gives bounded tasks to independent workers through Herdr.
4. Brichan verifies the results, records decisions and status, then reports back.

Herdr is needed only when Brichan coordinates independent worker sessions.
Project context is written to `projects/<project-slug>/` as a small set of
Markdown files covering overview, current state, tasks, decisions, and
references.

Coordinator defaults and worker routes are settings-driven, so the coordinator
and the implementation, review, planning, or scan workers may each use a
different runtime.

### Other console commands

Installing `brichan` also provides:

- `brichan-codex` — resolves coordinator routing from a Brichan source checkout (or
  `BRICHAN_ROOT`), or from an already-initialized project's `.brichan/` state.
- `brichan-claude` — resolves only from a checkout or `BRICHAN_ROOT`.
- `brichan-herdr-agent-start` — starts a Herdr worker session.
- `brichan-validate-receipts` — validates canonical handoff receipts.

`brichan-codex` and `brichan-claude` are checkout-oriented and intended for
development, not standalone installed-project launches. `--help` and `--version`
work from any directory.

### Task dossier workflow (developing Brichan itself)

Tasks tracked in the Brichan source checkout follow the task dossier
workflow: a fixed set of eleven handoff artifacts per task (request,
requirements, brief, options, design, plan, plan review, code review, PR
description, index, and receipt), scaffolded, generated, summarized, and
validated by checkout scripts. This is how Brichan's own repository is
developed, not a command available to an installed project — see the
[task dossier workflow docs](https://github.com/minhtran3124/Brichan/blob/main/docs/workflows/task-dossier.md)
in the source repository.

## License

Brichan is available under the [MIT License](https://opensource.org/licenses/MIT).
