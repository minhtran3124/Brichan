# Brichan

![Brichan coordinating a team of AI workers](assets/brichan-hero.png)

[![PyPI version](https://img.shields.io/pypi/v/brichan.svg)](https://pypi.org/project/brichan/)
[![Python versions](https://img.shields.io/pypi/pyversions/brichan.svg)](https://pypi.org/project/brichan/)
[![CI](https://github.com/minhtran3124/Brichan/actions/workflows/ci.yml/badge.svg)](https://github.com/minhtran3124/Brichan/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/minhtran3124/Brichan)](LICENSE)

Brichan is an open-source AI Chief of Staff for coding agents: a coordination
and verification harness that runs above coding-agent runtimes. Give it a
project outcome and it preserves the relevant context, coordinates independent
workers through [Herdr](https://herdr.dev), verifies their evidence, and keeps
decisions and project status in your repository instead of a chat window.

Codex and Claude Code provide the execution runtime, Herdr provides the worker
control plane, and Brichan provides the operating contract, routing, durable
memory, and verification layer above them.

Brichan is useful when work spans multiple agent sessions and you need more
than a stream of generated code: clear task boundaries, durable memory,
independent review, and evidence that the requested outcome was actually met.

> [!IMPORTANT]
> Brichan is pre-1.0 software. The current installed workflow supports Codex on
> Linux and macOS, and upgrades may require reinitializing managed state. See
> the [changelog](CHANGELOG.md) before upgrading.

## Why Brichan?

- **Durable project memory.** Stable facts, current status, decisions, tasks,
  and references live as Markdown in the repository.
- **Independent workers.** Planning, implementation, review, and research run
  in separate agent sessions with bounded assignments.
- **Evidence before completion.** A worker reporting `done` is not enough;
  Brichan checks acceptance criteria, tests, diffs, sources, and review
  findings as appropriate.
- **Controlled context.** The coordinator loads project information
  progressively and keeps detailed execution work out of its own context.
- **Guarded execution.** Brichan refuses permission bypasses, hidden scope
  widening, native delegation, and unsupported runtime configuration.

## Compatibility

| Workflow | Codex | Claude Code |
| --- | --- | --- |
| Installed into another repository | Supported | Not yet supported |
| Run from a Brichan source checkout | Supported | Supported |

The installed workflow requires:

- Linux or macOS;
- Python 3.10 or newer;
- an existing top-level Git repository;
- the `codex` CLI on `PATH`;
- Herdr when Brichan delegates work to independent agents.

Brichan has no third-party Python runtime dependencies.

## Quick start

Install Brichan from PyPI:

```bash
pip install brichan
```

Install Herdr and its Codex integration:

```bash
curl -fsSL https://herdr.dev/install.sh | sh
herdr integration install codex
```

On macOS, Herdr is also available through Homebrew:

```bash
brew install herdr
herdr integration install codex
```

Preview the files Brichan would add to your project, then initialize it:

```bash
brichan init --project /absolute/path/to/repository
brichan init --apply --project /absolute/path/to/repository
```

Initialization is a dry run by default and performs zero writes. Once the
project is initialized, check its health and launch the coordinator:

```bash
brichan doctor --project /absolute/path/to/repository
brichan run --project /absolute/path/to/repository
```

From inside a healthy initialized repository, you can simply run:

```bash
brichan
```

Then describe the outcome, constraints, and definition of done as you would to
a technical project lead. Brichan will decide how to split the work, coordinate
the required workers, verify their output, and maintain project memory.

## What initialization changes

`brichan init --apply` creates a versioned `.brichan/` directory containing
managed policy, model routing, the Herdr orchestration skill, and mutable
project memory. If the repository does not already contain root `AGENTS.md` or
`CLAUDE.md` files, Brichan creates small pointers that direct coding agents to
the managed policy. It also exports the Herdr skill to
`.agents/skills/herdr-orchestration/` so Codex sessions started directly in the
repository discover it.

Existing files and skills are never modified or overwritten. If `.agents/` or
`.agents/skills/` already exists, initialization adds only the missing
`herdr-orchestration` skill in the standard skill layout. Repeating
initialization against healthy state is idempotent.

Useful commands:

```bash
brichan status --project <repo>              # concise state verdict
brichan doctor --project <repo>              # dependency and state diagnostics
brichan doctor --json --project <repo>       # machine-readable diagnostics
brichan run --project <repo> -- <arguments>  # launch Codex with arguments
```

Arguments after `--` are treated as literal prompt content, including text
that begins with a dash.

## How it works

```text
You
  └── Brichan coordinator
        ├── planning worker
        ├── implementation worker
        ├── review worker
        └── research or scan worker
```

1. Brichan turns your request into scope, deliverables, acceptance criteria,
   constraints, and escalation conditions.
2. It launches independent main-agent sessions through Herdr with bounded task
   packets.
3. Workers return artifacts and evidence; Brichan checks the result and asks
   for remediation when needed.
4. Verified facts, decisions, status, references, and task ownership are
   recorded as durable project memory.

Herdr provides the visible worker control plane. Native runtime delegation
remains disabled so worker ownership, evidence, and cleanup stay auditable.

## Configuration and safety

Coordinator defaults and worker routes are settings-driven. Planning,
implementation, review, and scan work can each use a different supported
runtime, model, and reasoning effort. See the
[model-routing guide](docs/guides/model-routing.md) for the configuration
contract.

The installed launcher leaves existing agent instructions and provider
configuration untouched. It rejects native delegation, permission bypasses,
working-directory or scope widening, profiles, remote execution, and arbitrary
provider configuration before launching Codex.

State diagnostics report malformed, dangling, symlinked, inaccessible, or
incompatible `.brichan/` state rather than silently repairing it. Managed state
currently has no automatic migration; follow the upgrade notes in the
[changelog](CHANGELOG.md) when package versions change.

## Using a source checkout

The checkout workflow is intended for contributors and for Claude Code users:

```bash
git clone https://github.com/minhtran3124/Brichan.git
cd Brichan
bin/brichan
bin/brichan --runtime claude
```

Checkout mode reads routing from
[`config/model-routing.json`](config/model-routing.json). The
`brichan-codex` and `brichan-claude` console commands are also
checkout-oriented; the regular `brichan` command is the entry point for an
initialized external project.

## Contributing

Contributions are welcome. Bug reports, documentation improvements, focused
feature proposals, tests, and pull requests all help the project mature.

Before opening a pull request:

```bash
make check
```

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow and
review expectations. Use [GitHub Issues](https://github.com/minhtran3124/Brichan/issues)
for bugs and proposals. For vulnerabilities or reports involving credentials,
command execution, private project memory, or provider access, follow
[SECURITY.md](SECURITY.md) instead of opening a public issue.

The importable implementation lives in `src/brichan/`; tests are split across
unit, contract, and integration suites. See the
[repository layout](docs/architecture/repository-layout.md) before changing
module boundaries.

## Documentation

- [Documentation index](docs/index.md)
- [Operating principles](docs/policy/operating-principles.md)
- [Project memory policy](docs/policy/memory-policy.md)
- [Model routing](docs/guides/model-routing.md)
- [Task dossier workflow](docs/workflows/task-dossier.md)
- [Changelog](CHANGELOG.md)

## License

Brichan is available under the [MIT License](LICENSE).
