# Brichan

[![PyPI version](https://img.shields.io/pypi/v/brichan.svg)](https://pypi.org/project/brichan/)
[![Python versions](https://img.shields.io/pypi/pyversions/brichan.svg)](https://pypi.org/project/brichan/)
[![License](https://img.shields.io/pypi/l/brichan.svg)](https://pypi.org/project/brichan/)

Coding agents are very good at the work in front of them and very bad at
remembering why it was asked for. Context lives in a chat window, so it is lost
when the window closes; decisions are re-litigated, status is reconstructed from
memory, and the record of what was actually verified never outlives the session.

Brichan is an AI Chief of Staff that sits above the coding agent rather than
inside it. You give it a project goal; it keeps only the context that goal
needs, hands bounded tasks to independent workers, checks the evidence they
return, and records decisions and status as files in your repository — outside
chat, where they survive the session.

## Requirements

- Linux or macOS with Python 3.10 or newer. No runtime Python dependencies.
- An existing top-level Git repository to operate on.
- The `codex` CLI on `PATH` — the coordinator runtime Brichan launches.
- [Herdr](https://herdr.dev), the worker control plane — required as soon as
  Brichan hands bounded tasks to workers (a single coordinator session runs
  without it):

```bash
$ curl -fsSL https://herdr.dev/install.sh | sh
$ herdr integration install codex
```

## Installation

```bash
$ pip install brichan
```

## Basic commands

```bash
$ brichan init --project <repo>            # preview the footprint (dry run)
$ brichan init --apply --project <repo>    # create it
$ brichan status --project <repo>          # one-line state verdict
$ brichan doctor --project <repo>          # health summary (--json for CI)
$ brichan run --project <repo> -- <args>   # launch the coordinator
```

## Usage

Initialization defaults to a dry run with zero writes, so you can preview the
complete footprint before anything is created. `--apply` then creates:

- a versioned `.brichan/` directory holding managed policy, model routing,
  Herdr skill resources, and mutable project memory;
- root `AGENTS.md` and `CLAUDE.md` pointers, when the repository does not
  already have them.

Adding `--init-agents` also exports the Herdr orchestration skill to
`.agents/skills/`, so a `codex` session started directly in the repository
(without `brichan run`) discovers it too.

Existing files are never modified, and repeating `init` against healthy state
is idempotent.

From inside a healthy initialized repository, bare `brichan` launches the
coordinator directly:

```bash
$ brichan
```

Arguments after `--` are forwarded to the runtime. Option-looking text after
`--` is treated as literal prompt content, so a prompt beginning with a dash
cannot silently become a flag:

```bash
$ brichan run --project <repo> -- --review the auth module
```

## Feature notes

- **Coordinator over workers.** You describe the outcome; Brichan reads only
  the project context that work needs, gives bounded tasks to independent
  workers through Herdr, verifies the results, and records decisions and
  status back into the repository.
- **Settings-driven model routing.** Coordinator defaults and worker routes
  come from `.brichan/config/model-routing.json`, so planning, implementation,
  review, and scan work may each use a different model.
- **Guarded launches.** Brichan rejects native delegation, permission
  bypasses, cwd/scope widening, profiles, remote execution, and arbitrary
  runtime configuration before launching.
- **Strict state diagnostics.** Malformed, dangling, symlinked, inaccessible,
  or incompatible `.brichan/` state is reported, never silently repaired.
  Schema v1 has no automatic migration: a package-version change requires
  deliberate backup and reinitialization.
- **Machine-readable health.** `brichan doctor --json` emits one JSON document
  covering repository, Git, policy, routing, memory, and dependency checks for
  scripts and CI.

## License

Brichan is available under the [MIT License](https://opensource.org/licenses/MIT).
