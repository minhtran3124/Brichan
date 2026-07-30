# Herdr commands

Check health and list existing agents before mutation:

```text
herdr status
herdr integration status
herdr agent list
herdr pane current --current
```

Start a named-route worker from the installed package:

```text
brichan-herdr-agent-start brichan-<name> \
  --anchor-pane <coordinator-pane-id> \
  --cwd <absolute-target-project> \
  --route <plan|implement|review|scan>
```

Use `--dry-run` or `--json` to resolve a route without calling Herdr. Inspect
and monitor with `herdr agent get`, `herdr agent read`, and bounded
`herdr agent wait` calls. Submit prompts with `herdr pane run`. Close only a
recorded Brichan-owned pane with `herdr pane close <pane-id>`.
