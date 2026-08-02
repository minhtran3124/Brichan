# Task-dossier lane pilot results

Date: 2026-08-02

## Outcome

All three checkout-mode pilots passed their accepted plan, focused
implementation checks, independent plan review, independent code review, and
complete-dossier validation. The run demonstrates that one full eleven-artifact
dossier can be required for every lane while Level controls evidence depth and
review strength.

| Lane | Task | Requirement sample | Implementation evidence | Review | Dossier evidence |
| --- | --- | --- | --- | --- | --- |
| Simple / Level 0 | `TDW-006` | Exact greeting fixture | 35 exact UTF-8 bytes, one trailing line feed | Routine PASS, no findings | 11/11 artifacts; every artifact has at least 1 evidence item |
| Normal / Level 1 | `TDW-007` | Dependency-free project-slug normalizer | 7 focused tests PASS | Routine PASS, no findings | 11/11 artifacts; every artifact has at least 2 evidence items |
| High risk / Level 2 | `TDW-008` | Pure fail-closed release-policy simulation | 10 focused tests PASS; reviewer matrix passed 36 malformed cases and 100 deterministic repetitions | Stronger PASS, no findings | 11/11 artifacts; every artifact has at least 3 evidence items |

## Effective model routing

The workflow did not add or consume new keys in `config/model-routing.json`.
Actual worker launches followed the existing four-route contract:

| Phase | Effective route | Effective runtime/model/effort | Session |
| --- | --- | --- | --- |
| Requirements, options, design, plan | `plan` | Claude `claude-opus-5`, high | `8aa41de8-a3f3-48ce-8d47-9aed67a452c6` |
| Implementation, all lanes | `implement` | Claude `claude-opus-5`, medium | `6135c46e-a43e-4f14-9840-873bf01365c0` |
| Level 0/1 plan and code review | `review` | Codex `gpt-5.6-luna`, medium | `019fc0e5-9de0-7811-8bf1-c3bacd28eee9` |
| Level 2 plan and code review | `review` one-off stronger override | Codex `gpt-5.6-sol`, high | `019fc0e5-9e45-75d1-b92e-d8f4fe4fd44a` |

This is direct evidence that the current checkout routing changes remain
mechanically effective: the plan and routine-review workers resolved to the
models currently selected by the user, while the Level 2 reviewer used an
explicit stronger override without mutating the manifest.

## Evidence-depth audit

The validator passed all three complete dossiers. A direct parsed-artifact
audit found these evidence-item ranges:

- Level 0: 1–3 items per artifact.
- Level 1: 2–4 items per artifact.
- Level 2: 3–6 items per artifact.

This includes `client-follow-up-questions.md` when its state is
`not-required`; skipping a question still carries a rationale, evidence, a
claim, and an uncertainty statement.

## Ceremony and usability observations

The evidence contract works, but raw authoring cost is disproportionate at the
lower lanes:

| Lane | Dossier lines across 11 artifacts | Fixture and focused-test lines |
| --- | ---: | ---: |
| Level 0 | 639 | 1 |
| Level 1 | 716 | 86 |
| Level 2 | 1,009 | 154 |

The Level 0 result is the clearest warning: full documentation is valuable as a
durable proof trail, but manually authored prose is not a good default unit of
work for a one-line change. Keeping all eleven artifacts is compatible with
reducing ceremony if low-risk artifacts are concise generated projections over
the same canonical request, plan, receipt, test, and review evidence.

## Recommended follow-up

1. Keep the full eleven-artifact presence and evidence rules for every level.
2. Add a concise-mode generator for Level 0/1 that derives repetitive metadata,
   links, and status tables from one structured task record without weakening
   claims, uncertainty, provenance, or review.
3. Add a dossier summary command that reports evidence counts, stale links,
   model-route provenance, and review independence so operators do not inspect
   eleven files manually.
4. Preserve `config/model-routing.json` as the sole default model-selection
   surface; keep reviewer-strength escalation as a recorded one-off launch
   override.
5. Keep Level 2 threat model, stop conditions, authorization boundary,
   isolation, rollback, and stronger review explicit and non-generated where
   judgment is material.

## What not to do

- Do not make a missing artifact mean “simple” or “skipped”; that destroys the
  evidence the user requires.
- Do not add workflow-phase or lane keys to the routing manifest.
- Do not let the index copy receipt or project-memory authority.
- Do not treat file presence, evidence-item count, or model confidence as proof
  without executable checks and independent review.
- Do not convert the high-risk simulation into a production enforcement or
  release mechanism without a separately authorized task.

## Verification evidence

- `python3 scripts/validate_task_dossiers.py projects` — PASS, three dossiers.
- `python3 scripts/validate_task_dossiers.py projects --require-complete` —
  PASS, three dossiers.
- TDW-006 exact byte check — PASS, 35 bytes.
- TDW-007 focused unit suite — PASS, 7 tests.
- TDW-008 focused unit suite — PASS, 10 tests.
- TDW-008 strong-review supplemental matrix — PASS, 36 malformed cases and 100
  deterministic repetitions.

Timing, worker token totals, and per-task cost were not reliably observable and
are not estimated.
