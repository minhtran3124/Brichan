# Brichan runtime instructions

This repository is a Brichan-managed installed project. Canonical policy,
configuration, and project memory live under `.brichan/`:

- `.brichan/policy/` — operating policy; read `.brichan/policy/bootstrap.md`
  first, before acting.
- `.brichan/config/model-routing.json` — model and effort routing.
- `.brichan/project-memory/` — progressive project memory (mutable).

Everything under `.brichan/` except `project-memory/` is managed by
`brichan init` and must not be edited by hand.

This file was created by `brichan init` because it did not exist; Brichan
never modifies an existing `AGENTS.md`. Edit it freely — it belongs to the
repository, not to Brichan.
