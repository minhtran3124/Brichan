# Brida

Brida is a repository-native AI Chief of Staff for Codex. It turns project goals
into bounded work, coordinates independent worker sessions through Herdr,
checks their output, and keeps durable project state outside chat history.

Brida is intentionally conservative:

- The human user owns goals, priorities, and material trade-offs.
- Brida coordinates, routes, verifies, and records project state.
- Workers are independent main-agent sessions managed through Herdr.
- Codex native multi-agent execution is disabled at both project-config and
  launcher levels.
- Unknown timing, token, and cost data remain unknown rather than estimated.

## Status

Current repository version: `0.1.0`.

The core workflow, reviewer workflow, metrics ledger, and Herdr lifecycle have
been smoke-tested locally. The bounded evaluation showed that delegation
reduced coordinator input tokens by 68.2% but increased total tokens by 36.9%;
delegation is therefore a context-isolation and parallelism tool, not an
automatic cost optimization.

See:

- [`setup-status.md`](setup-status.md) for locally verified tooling.
- [`evals/2026-07-27-workflow-evaluation/RESULTS.md`](evals/2026-07-27-workflow-evaluation/RESULTS.md)
  for evaluation results.
- [`metrics/README.md`](metrics/README.md) for the metrics schema.

## Requirements

- POSIX-compatible shell
- Python 3.10 or newer
- Codex CLI
- Herdr with a working Codex integration
- `make` is optional but recommended

Provider availability is environment-specific. Consult
[`model-catalog.md`](model-catalog.md) before routing a worker.

## Quick start

Clone the repository and enter it:

```bash
git clone <repository-url> brida
cd brida
```

Run the complete local validation:

```bash
make check
```

Start Brida:

```bash
./bin/brida
```

Arguments are forwarded to Codex, for example:

```bash
./bin/brida -m gpt-5.6-terra
```

Always use `bin/brida` for a coordinator session. The launcher sets the
repository as the Codex working directory and enforces the native-agent
guardrails.

## How a session works

At startup, Brida reads:

1. [`identity.md`](identity.md)
2. [`operating-principles.md`](operating-principles.md)
3. Project memory only when the request concerns a project

For project work, Brida progressively loads:

```text
projects/index.md
  └── projects/<slug>/overview.md
      ├── current-state.md
      ├── tasks.md
      ├── decisions.md
      └── references.md
```

The complete loading and write policy is in
[`memory-policy.md`](memory-policy.md).

## Create a project memory space

Copy the tracked template and register it in `projects/index.md`:

```bash
cp -R projects/_template projects/<project-slug>
```

Then fill in:

- `overview.md`: stable purpose, scope, architecture, and constraints
- `current-state.md`: current status, risks, and next actions
- `tasks.md`: active ownership, workers, pane IDs, and acceptance criteria
- `decisions.md`: durable decisions and rationale
- `references.md`: evidence and source pointers

Do not store secrets, credentials, raw private data, or full chat transcripts
in project memory.

## Delegation model

Brida delegates only when independent judgment, specialization, or parallel
bounded work provides material value. Every worker:

1. Receives a bounded task packet.
2. Runs as an independent main-agent session through Herdr.
3. Uses a `brida-`-prefixed name.
4. Is recorded in the relevant `tasks.md`.
5. Produces evidence against explicit acceptance criteria.
6. Is closed after evidence is saved.

The local orchestration skill lives at
`.agents/skills/herdr-orchestration/`.

## Independent review

Use [`reviewer.md`](reviewer.md) for high-risk or material changes. A reviewer
must be a fresh session that did not implement the change. Findings distinguish
contract defects from optional hardening so precision can be measured.

## Metrics

Completed evaluations and delegated tasks can be recorded in the append-only
`metrics/runs.jsonl` ledger.

```bash
make metrics
```

Unavailable measurements must be `null`. Cost must not be reported without a
verified source.

## Repository layout

```text
.
├── .agents/skills/       Local orchestration skill and references
├── .codex/config.toml    Project-scoped Codex guardrails
├── .github/              CI and contribution templates
├── bin/brida             Coordinator launcher
├── evals/                Reproducible workflow evaluations
├── metrics/              Ledger, validator, and tests
├── projects/             Durable project memory and template
├── tests/                Repository contract tests
├── AGENTS.md             Runtime instructions for Codex
├── identity.md           Authority and relationship model
├── memory-policy.md      Progressive durable-memory policy
├── model-catalog.md      Verified model/provider routing catalog
├── operating-principles.md
└── reviewer.md           Independent reviewer protocol
```

## Development

Before submitting a change:

```bash
make check
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for contribution rules and
[`SECURITY.md`](SECURITY.md) for reporting security issues.

## License

Brida is available under the [MIT License](LICENSE).
