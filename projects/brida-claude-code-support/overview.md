# Brida Claude Code support

## Objective

Support Claude Code as an explicit Brida runtime without changing Brida's
provider-neutral coordination, verification, durable-memory, or authority
contracts.

## Scope

- Runtime selection through `bin/brida`.
- Dedicated Codex and Claude Code launchers.
- Claude Code policy adapter in `CLAUDE.md`.
- Herdr-only worker lifecycle.
- Runtime-specific tests and documentation.

## Constraints

- The user approved both coordinator and worker support for Claude Code.
- Runtime selection is explicit; automatic provider detection is out of scope.
- Native runtime delegation must not bypass Herdr.
- No secrets or credentials may be stored in the repository.
