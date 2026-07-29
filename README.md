# Brida

![Brida coordinating a team of AI workers](assets/brida-hero.png)

Brida is an AI Chief of Staff for Codex and Claude Code. Give it a project
goal; it keeps the necessary context, coordinates independent workers through
Herdr, checks their evidence, and records useful project state outside chat.

## Getting started

You need a POSIX-compatible shell, Python 3.10+, a supported AI CLI, and
Herdr when you want Brida to coordinate workers.

```bash
git clone <repository-url> brida
cd brida
make check
bin/brida
```

Brida starts with the repository default runtime. Choose Claude Code for one
session with:

```bash
bin/brida --runtime claude
```

See the [model-routing guide](docs/guides/model-routing.md) to change model
defaults, select a worker route, or use a one-off override.

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
- [Documentation index](docs/index.md)
- [Operating principles](docs/policy/operating-principles.md)
- [Security policy](SECURITY.md)

## License

Brida is available under the [MIT License](LICENSE).
