# Concise Level 0/1 dossier evaluation

Date: 2026-08-02

## These samples are synthetic and prove contract validity only

These samples prove contract validity only; no verdict, session identifier, or identifier inequality anywhere under `concise/` is evidence of any real independent review.

Both samples in this directory are unmistakably synthetic, non-authoritative
test fixtures. Every session identity begins with `synthetic-fixture-`, every
artifact claim says so in its own words, and both receipts record a `null`
review verdict. They demonstrate that a generated dossier satisfies the
contract; they demonstrate nothing about the quality of any real work. The real
evidence trail for this change is the `TDW-009` dossier itself.

## Outcome

One structured record per task rendered all eleven standard artifacts for a
Level 0 and a Level 1 sample. Both pass the complete gate against an isolated
projects root, both carry a schema-v2 receipt and a canonical project-memory
file, and both land well inside the 30% line-reduction budget.

| Sample | Level | Artifacts | Dossier lines | Pilot baseline | Reduction | Budget |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `SYNTH-010` | 0 | 11/11 | 410 | 639 | 35.8% | 447 |
| `SYNTH-011` | 1 | 11/11 | 422 | 716 | 41.1% | 501 |

Baselines are the measured pilot totals in
`evals/task-dossier-pilots/results.md:49-64`.

## Authoring burden

Line reduction measures artifact compactness. It does not measure authoring
burden, because the record still has to be written. Both are recorded so that
neither is mistaken for the other.

| Metric | `SYNTH-010` | `SYNTH-011` | What it measures |
| --- | ---: | ---: | --- |
| Dossier lines across 11 artifacts | 410 | 422 | artifact compactness; the AC3 metric |
| Record lines | 227 | 304 | authoring burden, upper bound |
| Record bytes | 9,723 | 11,569 | authoring burden, upper bound |
| `authored_values` | 148 | 160 | authoring burden, closest proxy |
| Record plus dossier lines | 637 | 726 | total durable text |

`authored_values` counts every non-null, non-empty scalar a human actually
supplied, using the fixed `DECLARED_ORDER` algorithm in
`projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md:1267-1286`.
Dictionary keys are never counted; list elements are counted individually. Two
independent runs produced identical integers.

The honest reading: total durable text is roughly unchanged at Level 0 (637
against 639) and slightly higher at Level 1 (726 against 716). What changed is
where the text lives. The eleven artifacts stop being eleven hand-transcribed
copies of the same sixteen metadata fields and become one projection of a
single record, so the number of places a value can be wrong drops from eleven
to one. Compactness of the durable artifacts improved by 35.8% and 41.1%;
authoring effort did not drop by anything like that, and this evaluation does
not claim it did.

## What the generator derived, and what it refused to derive

Derived, because it is mechanically implied by the dossier path or the record:

- `Task ID`, `Task level`, `Artifact`, and `Owner` in every metadata block.
- The index `Task identity` triple and the canonical receipt path.
- The eleven-row artifact status table.
- The document title.

Refused, in every case, rather than inferred:

- Any claim, evidence item, or uncertainty statement.
- Any review verdict, reviewing session, or authoring session.
- Any effective route, model, or effort; the routing manifest is never opened.
- Any placeholder in a position the contract requires to be concrete.
- Any value that would inject Markdown structure into a rendered position.

A record supplying one of the four derived index identity fields is refused
outright, so the record cannot become a second authority for them.

## Evidence depth

The level floor governs `passed` artifacts; a `not-required` artifact meets a
one-item rule instead. `client-follow-up-questions` is `not-required` in both
samples and still carries a rationale, one evidence item, a concrete claim, and
an uncertainty statement.

- `SYNTH-010`, Level 0: 1 evidence item per artifact, floor 1.
- `SYNTH-011`, Level 1: 2 evidence items per artifact, floor 2.

## Commands and results

| Command | Result |
| --- | --- |
| `python3 scripts/generate_task_dossier.py SYNTH-010 --level 0 --project synthetic-level0 --record evals/task-dossier-pilots/concise/records/SYNTH-010.record.json --projects-root evals/task-dossier-pilots/concise/projects` | exit `0`; planned 11 artifacts, wrote none |
| the same command with `--apply` | exit `0`; `wrote 11 task-dossier artifact(s) for SYNTH-010.` |
| `python3 scripts/generate_task_dossier.py SYNTH-011 --level 1 --project synthetic-level1 --record evals/task-dossier-pilots/concise/records/SYNTH-011.record.json --projects-root evals/task-dossier-pilots/concise/projects --apply` | exit `0`; `wrote 11 task-dossier artifact(s) for SYNTH-011.` |
| `python3 scripts/validate_task_dossiers.py evals/task-dossier-pilots/concise/projects --require-complete` | exit `0`; `Validated 2 task dossier(s).` |
| `python3 scripts/validate_handoff_receipts.py evals/task-dossier-pilots/concise/projects` | exit `0`; `Validated 2 canonical handoff receipt(s).` |
| `python3 scripts/summarize_task_dossier.py evals/task-dossier-pilots/concise/projects` | exit `0` |
| explicit eleven-path `wc -l` per sample | 410 and 422 |
| `wc -lc` per record plus the `authored_values` count | reproduced identically across two runs |

## Residual risks

- The generator reduces transcription error. It cannot raise evidence quality:
  a record can hold eleven shallow-but-valid claims, and the contract will
  accept them.
- Whether operators prefer authoring JSON over Markdown is untested. One
  malformed bracket refuses the whole dossier, where a malformed Markdown
  artifact previously refused only itself.
- These samples are generated, so they exercise the renderer against the
  validator. They say nothing about hand-authored dossiers, which stay
  first-class and unmigrated.
- The capture map, the start preflight, the after-delta check, and the
  generator's post-publication check are all point-in-time observations. A
  non-cooperating process running under the same OS identity is outside the
  threat model: neither prevention nor detection is claimed against it.
- No timing, token, or cost measurement is recorded, because none was
  observed. None is estimated.

## Uncertainty

- Total durable text did not fall, and at Level 1 it rose slightly. Whether
  that trade — one authored source against eleven transcribed copies — is worth
  it in daily use is not settled by two synthetic samples.
- The 30% target was met on artifact lines at both levels with room to spare,
  but both samples sit near the evidence floor. A richer real dossier would
  narrow the margin, because the generator compresses ceremony and not
  judgment.
