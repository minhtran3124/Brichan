# Decisions

## 2026-07-27 — Explicit dual-runtime support

Support Claude Code as both coordinator and worker runtime. Select it explicitly
with `--runtime claude`; do not auto-detect installed providers.

## 2026-07-27 — Herdr remains the worker-control plane

Claude Code native delegation is disabled by the launcher so worker creation,
ownership, evidence, and cleanup remain auditable through Herdr.

## 2026-07-27 — Claude model routing

Use Opus 5 through the `opus` alias for the Claude coordinator by default;
allow `BRIDA_CLAUDE_COORDINATOR_MODEL=fable` for Fable 5. Use Sonnet 5 through
the `sonnet` alias for Herdr implementation workers.

## 2026-07-28 — First mixed-provider pilot contract

For the first pilot, use a Markdown-only handoff/receipt template as a
non-mandatory Herdr reference. Do not extend the five-file project-memory
layout or mandate receipt storage until retrieval and lifecycle behavior are
evaluated separately.

## 2026-07-28 — Pilot receipt storage and optional packet linkage

Store filled pilot receipts under `evals/mixed-provider-coding/<pilot-id>/` and
link them from project `references.md`. Task packets may carry an accepted plan
ID/version/status and repo-relative receipt path, but the block remains
optional when no upstream plan exists.
