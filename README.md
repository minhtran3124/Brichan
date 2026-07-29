# Brida

![Brida coordinating a team of AI workers](assets/brida-hero.png)

> A friendly AI Chief of Staff for Codex and Claude Code.

Brida turns a big project goal into small, clear pieces of work. It chooses a
runtime, coordinates independent workers through [Herdr](https://github.com/),
checks their results, and keeps useful project memory outside the chat.

## Start here

You need a POSIX-compatible shell, Python 3.10+, one supported AI CLI, and
Herdr.

```bash
git clone <repository-url> brida
cd brida
make check
./bin/brida
```

The coordinator runtime and model defaults are read from
[`config/model-routing.json`](config/model-routing.json). To select Claude Code
for one session:

```bash
./bin/brida --runtime claude
```

Existing Claude coordinator environment overrides remain available as a
compatibility path:

```bash
BRIDA_CLAUDE_COORDINATOR_MODEL=fable ./bin/brida --runtime claude
```

### Model routing

The routing manifest is the only active repository source for coordinator
defaults and the named `plan`, `implement`, `review`, and `scan` worker routes.
The Python adapters validate it before launching a provider or mutating Herdr.

Explicit coordinator CLI options take precedence over compatibility environment
overrides, which take precedence over manifest values:

```bash
./bin/brida --model <verified-model>
./bin/brida-claude --model fable --effort high
```

Start a worker by named route:

```bash
bin/brida-herdr-agent-start brida-example \
  --anchor-pane <coordinator-pane-id> \
  --cwd <absolute-project-path> \
  --route implement
```

For one launch, `--runtime`, `--model`, and `--effort` override that route's
manifest values. Resolve and validate without calling Herdr by using `--dry-run`
for shell-readable output or `--json` for machine-readable output:

```bash
bin/brida-herdr-agent-start brida-example \
  --cwd <absolute-project-path> \
  --route review \
  --runtime codex \
  --model <verified-model> \
  --effort <supported-effort> \
  --json
```

The explicit command form remains a documented legacy compatibility path:

```bash
bin/brida-herdr-agent-start brida-example \
  --anchor-pane <coordinator-pane-id> \
  --cwd <absolute-project-path> \
  -- codex --model <verified-model>
```

Legacy commands are provider-allowlisted and receive the same code-enforced
native-delegation and permission-bypass guardrails as named routes.

## How it works

1. You give Brida a goal.
2. Brida reads only the project context it needs.
3. Independent workers receive bounded task packets through Herdr.
4. Brida checks the evidence, records durable state, and reports what is next.

Herdr is the only approved worker-control plane. Native runtime delegation is
disabled so worker ownership and cleanup stay visible and auditable.
Worker panes are arranged through Brida's balanced-layout launcher: two panes
use equal columns, three use equal area, and four use a 2x2 grid.

## Project memory

Each project can keep its working context in a small folder:

```text
projects/<project-slug>/
├── overview.md       # purpose and boundaries
├── current-state.md   # status and next actions
├── tasks.md           # ownership and acceptance criteria
├── decisions.md       # decisions and rationale
└── references.md      # evidence and source links
```

Create one from the template:

```bash
cp -R projects/_template projects/<project-slug>
```

See [the project memory policy](docs/policy/memory-policy.md) for the loading
and writing rules.

## Useful docs

- [AGENTS.md](AGENTS.md) — Brida’s operating rules
- [CLAUDE.md](CLAUDE.md) — Claude Code runtime adapter
- [Documentation index](docs/index.md) — canonical policy, workflows, and history
- [Identity](docs/policy/identity.md) — roles, authority, and boundaries
- [Operating principles](docs/policy/operating-principles.md) — how Brida works
- [Model catalog](docs/policy/model-catalog.md) — verified runtime and model notes
- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution guide
- [SECURITY.md](SECURITY.md) — security policy

## Development

Run the complete local validation suite:

```bash
make check
```

The importable implementation lives under `src/brida/`; stable commands remain
under `bin/` and `scripts/`. Tests are independently runnable by layer:

```bash
make test-unit
make test-contract
make test-integration
make package-check
```

See the [repository layout](docs/architecture/repository-layout.md) for module
and dependency boundaries.

## License

Brida is available under the [MIT License](LICENSE).

<p align="center"><sub>Built for calm, evidence-based project coordination.</sub></p>
