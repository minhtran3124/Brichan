# Brichan

[![PyPI version](https://img.shields.io/pypi/v/brichan.svg)](https://pypi.org/project/brichan/)
[![Python versions](https://img.shields.io/pypi/pyversions/brichan.svg)](https://pypi.org/project/brichan/)
[![License](https://img.shields.io/pypi/l/brichan.svg)](https://pypi.org/project/brichan/)

![Brichan coordinating a team of AI workers](/assets/brida-hero.png)

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

The distribution is named `brichan`. The importable package stays `brida`, and
every console command keeps its existing `brida` / `brida-*` name.

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
$ /absolute/path/to/brida/scripts/install-brida
```

By default it creates an environment at `$HOME/.local/share/brida/venv` and
command symlinks in `$HOME/.local/bin`, selecting an available Python 3.10+
interpreter with `pip`, `setuptools`, `venv`, and `wheel`. If the command
directory is not on `PATH`, the installer prints the exact export to add to your
shell profile.

## Usage

Brichan operates on an existing top-level Git repository. Initialization
defaults to a dry run and performs zero writes, so you can preview the complete
footprint before anything is created:

```bash
$ brida init --project /absolute/path/to/repository
```

Once the footprint looks right, apply it:

```bash
$ brida init --apply --project /absolute/path/to/repository
```

This creates only a versioned `.brida/` directory holding managed policy, model
routing, Herdr skill resources, and mutable project memory. Repeating it against
healthy state is idempotent. Your `AGENTS.md`, `CLAUDE.md`, `.codex/`, and
provider configuration are left untouched.

Diagnose and launch from any directory by naming the target explicitly:

```bash
$ brida status --project /absolute/path/to/repository
$ brida doctor --project /absolute/path/to/repository
$ brida run --project /absolute/path/to/repository -- <codex arguments>
```

From inside a healthy initialized repository, bare `brida` launches Codex
directly:

```bash
$ brida
```

Arguments after `--` are forwarded to Codex. Option-looking text after `--` is
treated as literal prompt content, so a prompt beginning with a dash cannot
silently become a flag:

```bash
$ brida run --project /absolute/path/to/repository -- --review the auth module
```

Before the `--`, Brichan rejects native delegation, permission bypasses,
cwd/scope widening, profiles, remote execution, and arbitrary Codex
configuration. State diagnostics reject malformed, dangling, symlinked,
inaccessible, or incompatible `.brida/` state rather than silently repairing it.
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

- `brida-codex` — resolves coordinator routing from a Brida source checkout (or
  `BRIDA_ROOT`), or from an already-initialized project's `.brida/` state.
- `brida-claude` — resolves only from a checkout or `BRIDA_ROOT`.
- `brida-herdr-agent-start` — starts a Herdr worker session.
- `brida-validate-receipts` — validates canonical handoff receipts.

`brida-codex` and `brida-claude` are checkout-oriented and intended for
development, not standalone installed-project launches. `--help` and `--version`
work from any directory.

## License

Brichan is available under the [MIT License](https://opensource.org/licenses/MIT).
