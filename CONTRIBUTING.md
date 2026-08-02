# Contributing

## Development setup

Brichan has no third-party Python runtime dependencies. Use Python 3.10 or newer:

```bash
python3 --version
make check
```

Codex and Herdr are required only for interactive orchestration and end-to-end
worker tests.

## Change workflow

1. State the objective and acceptance criteria.
2. Keep the change within one clear concern. Tracked tasks own a full task
   dossier; see [Task dossier workflow](docs/workflows/task-dossier.md).
3. Update documentation when behavior or operating contracts change.
4. Add or update regression tests for executable behavior.
5. Run `make check`.
6. Record observed workflow metrics when the change is an evaluation or
   delegated task.

Do not commit credentials, provider tokens, private conversation transcripts,
or sensitive project data.

## Documentation conventions

- Use repository-relative links.
- Mark time-sensitive claims with a verification date.
- Separate verified facts from assumptions.
- Use `null` for unavailable measurements.
- Keep project `current-state.md` concise and replace stale state rather than
  appending a diary.

## Pull requests

A pull request should contain:

- What changed and why.
- Verification commands and results.
- Risks and known limitations.
- Any changes to authority, security, provider routing, or cost behavior.

Material changes to orchestration, permissions, security, or public contracts
require an independent review using `docs/policy/reviewer.md`.
