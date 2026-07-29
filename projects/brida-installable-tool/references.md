# References

- `projects/brida-installable-tool/handoffs/DOGFOOD-005/receipt.md` — bounded Claude implementation and review receipt for installer prerequisite hardening
- `projects/brida-installable-tool/handoffs/PYPI-001/receipt.md` — Brichan PyPI-readiness implementation and review receipt

| Topic | Source | Verified date | Notes |
|---|---|---|---|
| Current package metadata | `pyproject.toml` | 2026-07-29 | Python package and five console entrypoints are declared |
| Current public setup | `README.md` | 2026-07-29 | Getting started currently uses clone, `make check`, and `bin/brida` |
| Module boundaries | `docs/architecture/repository-layout.md` | 2026-07-29 | Importable core is separated from repository-owned durable data |
| Current runtime root coupling | `src/brida/cli/_root.py`; `src/brida/cli/runtime.py`; `src/brida/orchestration/model_routing.py` | 2026-07-29 | Startup requires Brida-root markers, local wrappers, and root-relative routing config |
| Local verification | `PYTHONDONTWRITEBYTECODE=1 make check` | 2026-07-29 | 121 tests and all durable-data, repository, package-import, and shell checks passed |
| Codex project instructions | https://developers.openai.com/codex/guides/agents-md | 2026-07-29 | Official documentation; redirected to current ChatGPT Learn page |
| Codex configuration | https://learn.chatgpt.com/docs/config-file/config-reference | 2026-07-29 | Official source for project config, developer instructions, and skill-path prototype options |
| Codex CLI configuration precedence | https://learn.chatgpt.com/docs/developer-commands#how-to-read-this-reference | 2026-07-29 | Official source confirming invocation-level `-c key=value` precedence used by the installed launcher |
| Claude project memory and init | https://code.claude.com/docs/en/memory | 2026-07-29 | Official docs cover `CLAUDE.md`, scoped rules, and reviewable `/init` behavior |
| Claude CLI policy/plugin surfaces | https://code.claude.com/docs/en/cli-usage | 2026-07-29 | Official source for append-system-prompt and plugin-directory prototype options |
| Copilot CLI project init | https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference | 2026-07-29 | `copilot init` writes or updates repository instructions |
| Copilot customization | https://docs.github.com/en/copilot/concepts/prompting/response-customization | 2026-07-29 | Official repository and path-specific instruction surfaces |
| Spec Kit project init | https://github.github.com/spec-kit/reference/core.html | 2026-07-29 | Official `specify init` project-scaffolding precedent |
| Spec Kit lifecycle | https://github.github.com/spec-kit/upgrade.html | 2026-07-29 | Official read-only check and dry-run upgrade precedent |
| Cline workspace rules | https://docs.cline.bot/customization/cline-rules | 2026-07-29 | Official modular project-rule precedent |
| Aider conventions | https://aider.chat/docs/usage/conventions.html | 2026-07-29 | Official minimal read-only convention-file precedent |
| Independent synthesis review | `projects/brida-installable-tool/review.md` | 2026-07-29 | Initial `CHANGES REQUIRED`; nine findings remediated; final verdict `PASS` |
| Concurrent routing mismatch | `config/model-routing.json`; final `PYTHONDONTWRITEBYTECODE=1 make check` | 2026-07-29 | Out-of-scope implement-route change caused four assertions for the previous Codex route to fail; change preserved |
| Herdr cleanup | `herdr agent list`; panes `w1X:p34`–`w1X:p39` | 2026-07-29 | Six Brida-owned panes closed; coordinator and unrelated workspaces preserved |
| Installed dogfood implementation | `src/brida/lifecycle.py`; `src/brida/project.py`; `src/brida/resources/dogfood_v1/`; `docs/guides/installable-dogfood.md` | 2026-07-29 | Schema-v1 lifecycle, packaged policy/skill/memory resources, and operating guide |
| Installed-wheel verification | `tests/integration/test_installed_dogfood.py`; `PYTHONDONTWRITEBYTECODE=1 make check` | 2026-07-29 | Five wheel tests and 152 total checks passed; fake Codex verified direct launch and adversarial boundaries |
| Implementation review | `brida-dogfood-codex-review` / `w1X:p3B` | 2026-07-29 | Initial and focused re-reviews found seven bounded defects; all remediated; final verdict `PASS` |
| Claude implementation stabilization | `brida-dogfood-claude-stabilize` / `w1X:p3C`; `config/model-routing.json` | 2026-07-29 | User-requested re-check confirmed `implement` → Claude Sonnet medium; worker found no new defect, changed no files, and passed wheel probes plus 152 checks |
| External installer | `scripts/install-brida`; `tests/integration/test_installed_dogfood.py` | 2026-07-29 | Dedicated external venv, safe command shims, no activation, and outside-checkout installation verified |
| Installer hardening and review | `brida-installer-pip-fix` / `w1X:p3E`; `brida-installer-review` / `w1X:p3D`; `projects/brida-installable-tool/handoffs/DOGFOOD-005/receipt.md` | 2026-07-29 | Claude Sonnet implementation; Claude Opus final `PASS`; 155 checks and 34 canonical receipts passed |
| Brichan PyPI readiness | `pyproject.toml`; `.github/workflows/ci.yml`; `.github/workflows/publish.yml`; `projects/brida-installable-tool/handoffs/PYPI-001/receipt.md` | 2026-07-29 | Claude Sonnet implementation and Claude Opus independent review `PASS`; artifacts, metadata, install smoke, and full checks passed; external publishing setup remains deferred |

Cursor was researched by a worker but its current official rules URL redirected
to a broader page; detailed Cursor claims are intentionally excluded from the
durable assessment pending re-verification.
