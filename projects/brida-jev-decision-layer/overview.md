# Project overview

- Name: Brida Jev decision layer
- Slug: brida-jev-decision-layer
- Repository/path: repository root (`.`)
- Owner: Brichan
- Lifecycle status: proposed
- Last verified: 2026-09-24

## Purpose

Evaluate whether TypeSafe AI's Jev, a non-generative "System One" decision
model (typed `noul`/`choice`/`score` questions over a `state`, calibrated
probabilities, ~100-300 ms, $0.042 per million input tokens, output free), can
take over the small judgments Brichan currently makes with frontier models or
does not make at all, without touching the plan/implement/review routes.

## In scope

Candidate decision points, ranked by expected value (research 2026-09-24):

1. Worker tool-call risk gate: `PreToolUse` hook on Claude Code and Codex
   workers asking orthogonal nouls (destructive, secrets, exfiltration,
   irreversible, outside declared scope) -> deny/ask/allow.
2. Prompt-injection screen on content workers read (`PostToolUse`).
3. Coordinator triage of worker observations (scheduling hint over the
   observed pane tail: needs user / needs guidance / progressing / apparently
   finished / stalled).
4. Reviewer-finding triage: defect-vs-hardening, severity, duplicate.
5. Progressive memory reads: "does this request touch a recorded decision".

## Out of scope

- Replacing any `plan`, `implement`, `review`, or `scan` route with Jev: it
  cannot generate, plan, or review, and difficulty prediction measured at
  chance (51.3%).
- Letting Jev deny or approve anything without a deterministic check beside it.
- Adopting the third-party `jev-guard` hooks wholesale (writes user config;
  the launcher rejects hook overrides).
- Adding the `typesafe-sdk` dependency (stdlib-only rule).

## Architecture

A small stdlib `urllib` client for `POST https://api.typesafe.ai/v1/systemone`
inside `src/brichan/`. Verdicts are hints layered on existing authority
classes; the three-authority rule in `orchestration/monitor.py` (scheduling
state, bounded observation, file-based evidence) is unchanged and Jev never
proves completion. Worker hooks, if adopted, are owned and installed by the
launcher; user-supplied hook overrides stay rejected.

## Stable constraints

- Standard library only; Python 3.10+.
- Jev must enter `docs/policy/model-catalog.md` with a verification date
  before any route or hook uses it; API key handling needs user authorization.
- Cost is recorded only from the response `usage` field; never estimated.
- Never send tool outputs to Jev when deciding whether to run a tool
  (injection moves the verdict; documented by the vendor).
- Any change to the launcher's hook handling is a durable-contract change and
  requires independent review and user sign-off.

## Success measures

- Shadow-mode pilot: Jev verdicts logged on real worker tool calls and pane
  observations, compared against what actually happened, thresholds set from
  Brichan's own data.
- Reduction in user interventions per run and in coordinator reads of full
  pane text, measured in `metrics/runs.jsonl`, not assumed.
