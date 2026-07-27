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

The default runtime is Codex. To use Claude Code instead:

```bash
./bin/brida --runtime claude
```

The Claude coordinator uses Opus 5 by default. Herdr implementation workers
use Sonnet 5. To use Fable 5 for coordination:

```bash
BRIDA_CLAUDE_COORDINATOR_MODEL=fable ./bin/brida --runtime claude
```

### Model routing

- Codex coordinator: uses the Codex CLI default model unless you choose one
  explicitly.
- Claude coordinator: Opus 5 (`opus`) by default, or Fable 5 (`fable`).
- Herdr implementation workers: Sonnet 5 (`sonnet`).

Choose a Codex model explicitly with `-m`:

```bash
./bin/brida -m gpt-5.6-terra
```

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

See [memory-policy.md](memory-policy.md) for the loading and writing rules.

## Useful docs

- [AGENTS.md](AGENTS.md) — Brida’s operating rules
- [CLAUDE.md](CLAUDE.md) — Claude Code runtime adapter
- [identity.md](identity.md) — roles, authority, and boundaries
- [operating-principles.md](operating-principles.md) — how Brida works
- [model-catalog.md](model-catalog.md) — verified runtime and model notes
- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution guide
- [SECURITY.md](SECURITY.md) — security policy

## Development

Run the complete local validation suite:

```bash
make check
```

## License

Brida is available under the [MIT License](LICENSE).

<p align="center"><sub>Built for calm, evidence-based project coordination.</sub></p>
