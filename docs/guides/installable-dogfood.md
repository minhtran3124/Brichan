# Installed Codex dogfood

This schema-v1 vertical slice runs Brichan from an installed Python wheel inside
an existing top-level Git repository. It is intentionally limited to a
POSIX-compatible environment, Python 3.10+, and Codex launched through `brichan`.
Herdr is required only when Brichan coordinates worker sessions.

The PyPI distribution name, the importable Python package, and every console
command all share the name `brichan`/`brichan-*`, so a release installs with:

```bash
pip install brichan
```

To run a change that is not released yet, use the package-owned installer or a
manual wheel build from this checkout, both described below.

## Install without activating an environment

Run the package-owned installer by absolute path from any directory:

```bash
/absolute/path/to/brichan/scripts/install-brichan
```

The installer:

- resolves the Brichan source checkout from its own location, not the current
  working directory;
- selects Python 3.10+ with `pip`, `setuptools`, `venv`, and `wheel`;
- builds from a temporary source snapshot, leaving the checkout clean;
- creates a dedicated environment at
  `$HOME/.local/share/brichan/venv` by default, and refuses to reuse an
  existing one that lacks usable `pip`;
- links all Brichan commands into `$HOME/.local/bin`;
- never activates or modifies the target project's `.venv`.

No virtualenv activation is required. If `$HOME/.local/bin` is not on `PATH`,
the installer prints the exact shell-profile export and a full-path command
that works immediately.

Use explicit locations or a specific build interpreter when needed:

```bash
/absolute/path/to/brichan/scripts/install-brichan \
  --install-root /absolute/tool/location \
  --bin-dir /absolute/command/location \
  --python python3.13
```

Rerunning the installer upgrades the dedicated environment. It refuses to
overwrite non-symlink commands or symlinks that belong to another installation.
This dogfood stage does not publish a package or fetch build dependencies.

### Manual wheel installation

The equivalent manual flow is:

```bash
python3 -m pip wheel /absolute/path/to/brichan \
  --no-deps \
  --no-build-isolation \
  --wheel-dir /tmp/brichan-wheel
python3 -m venv /tmp/brichan-venv
/tmp/brichan-venv/bin/python -m pip install \
  --no-deps \
  /tmp/brichan-wheel/brichan-0.5.0-py3-none-any.whl
```

The build interpreter must already provide `pip`, `setuptools`, `venv`, and
`wheel`.

## Initialize a target repository

Use an explicit top-level Git repository during initial dogfood:

```bash
brichan init --project /absolute/path/to/repository
brichan init --apply --project /absolute/path/to/repository
```

`init` defaults to dry-run and performs zero writes. `--apply` installs the
state atomically. Repeating `--apply` against a healthy state reports
`no changes` and performs no file rewrites.

The complete footprint is:

```text
.brichan/
├── manifest.json
├── config/model-routing.json
├── policy/
│   ├── bootstrap.md
│   ├── identity.md
│   ├── memory-policy.md
│   └── operating-principles.md
├── skills/herdr-orchestration/
│   ├── SKILL.md
│   └── references/
│       ├── commands.md
│       └── task-packet.md
└── project-memory/
    ├── index.md
    └── main/
        ├── current-state.md
        ├── decisions.md
        ├── overview.md
        ├── references.md
        └── tasks.md
```

The manifest records schema and package versions plus hashes for managed
configuration, policy, and skill resources. Files under `project-memory/` are
mutable. Brichan never edits root `AGENTS.md`, `CLAUDE.md`, `.codex/`, or provider
configuration during initialization.

## Diagnose and run

```bash
brichan status --project /absolute/path/to/repository
brichan doctor --project /absolute/path/to/repository
brichan run --project /absolute/path/to/repository -- <codex arguments>
```

From inside a healthy initialized repository, bare `brichan` also launches Codex.
`status` reports project state only. `doctor` additionally resolves `codex` on
`PATH`; Herdr is reported as optional until worker coordination is needed.

`brichan --help` and `brichan --version` work from any directory, including one
that is not yet a Git repository or not yet initialized: they print
installed-package usage and version information instead of an uninitialized
error. Inside a healthy initialized project, `--help`/`--version` are instead
forwarded to `codex` as documented CLI overrides (see below).

From a source checkout — that is, with `BRICHAN_ROOT` pointing at a checkout
whose `src/brichan` is the running package — `brichan --help`/`--version` report
Brichan rather than the runtime, because a checkout has no project state to
launch into. Naming a runtime keeps the forwarding: `brichan --runtime codex
--help` reaches `codex`, as does `bin/brichan-codex --help`.

| Condition | Exit code |
|---|---:|
| Healthy | 0 |
| Uninitialized | 1 |
| Malformed or unsafe partial state | 2 |
| Incompatible schema/package version | 3 |
| Healthy state but required `codex` missing in `doctor` | 4 |

Launch uses the installed Python entrypoint, changes to the target root, and
executes `codex` from `PATH`. It never selects target `bin/brichan-*` wrappers.
Brichan supplies Codex CLI configuration overrides for:

- developer bootstrap policy;
- the initialized Herdr skill path;
- disabled Codex native-agent features;
- the configured model and reasoning effort.

Permission-bypass arguments, native-delegation re-enablement, and replacement
of the Brichan-owned bootstrap or skill overrides are rejected before execution.
Because these are CLI overrides, the flow does not depend on trusted
project-local `.codex/config.toml`.

Installed project mode intentionally accepts only model and reasoning-effort
overrides, help/version/terminal-display flags, and prompt text. It rejects
Codex cwd and writable-scope options (`-C`, `--cd`, `--add-dir`), profiles,
remote or cloud execution, approval and sandbox overrides, provider changes,
custom permission or writable-root configuration, and arbitrary `-c/--config`
keys. Use `--` before literal prompt text that begins with a hyphen.

State diagnostics use no-follow checks. A symlinked or dangling `.brichan`,
symlinked managed or memory file, or symlinked parent component is malformed.
Initialization uses a `.brichan-stage-*` directory and normally removes it on
failure; abrupt process or machine termination can leave that staging
directory for the user to inspect and remove deliberately.

## Compatibility boundary

The checkout workflow remains supported: `bin/brichan` sets `BRICHAN_ROOT` and
continues dispatching through repository `bin/brichan-codex` or
`bin/brichan-claude`. Installed-project mode is Codex-only. Schema-v1 has no
automatic migration or repair: malformed managed resources and package-version
mismatches require deliberate reinitialization in a disposable or backed-up
repository.

The `brichan-codex` and `brichan-claude` console commands remain checkout-oriented
after `pip install brichan`. `brichan-codex` resolves coordinator configuration
either from a Brichan source checkout (or `BRICHAN_ROOT`) or from an
already-initialized project's `.brichan/` state. `brichan-claude` only resolves
from a Brichan source checkout or `BRICHAN_ROOT`; it has no initialized-project
path and is not part of the Codex-first installed-project workflow. Outside
those contexts, both commands' `--help`/`--version` work everywhere and report
this plainly instead of raising a Python traceback; any other invocation
outside those contexts is rejected with an actionable, owned error.
