# Sonnet 5.5 side-by-side: `claude-sonnet-5` vs `claude-sonnet-5-5`

Task `WFS-010`, 2026-10-08. Same shape as stage 1 of `../protocol.md`, with
the Sonnet pair and one extra scan task, because `scan` is the route Sonnet
serves.

## Setup

- Arms: identical packets, the same dispatch commit `40f46d8` in separate
  detached worktrees (`../brichan-s55-a`, `../brichan-s55-b`), effort
  `medium`, model the only difference. Arm A = `claude-sonnet-5`, arm B =
  `claude-sonnet-5-5`. All four workers were dispatched at
  2026-10-08T08:40:31Z.
- Coding: the three stage 1 tasks (`../stage1/t1-ledger-summary`,
  `t2-prerelease-order`, `t3-path-guard`), one worker per arm on the
  `implement` route with a model override. `40f46d8` predates the hidden
  tests, so workers cannot see them.
- Scan: `s1-policy-audit/pack/`, a small self-contained policy pack with six
  seeded defects and three decoys, one worker per arm on the `scan` route
  with a model override. The answer key stayed outside both worktrees until
  scoring and is added as `s1-policy-audit/answer-key.md` with the results.
- Packets carry a techstack Snapshot resolved in each worktree.

## Scoring

- Coding: hidden tests passed / total per task (`../stage1/<task>/hidden/`),
  visible and own tests, and a blind review that sees the arms as X and Y.
- Scan: seeded defects found (right file and reason, line within two),
  decoys flagged (false positives), and other findings the blind reviewer
  judges valid or false.
- Wall time from dispatch to the worker's final response; tokens only as
  shown in the CLI footer (display values, not billed usage).
- Preference rule (adapted from stage 1): `claude-sonnet-5-5` is preferred
  if it is no worse on hidden tests on every coding task and no worse on scan
  recall, and better on at least one of hidden tests, review findings, scan
  precision or recall, or elapsed time.

## Stored file names

The fixture's Markdown files and the two scan findings files are stored with
an added `.txt` suffix. The fixture contains a deliberately broken link
(seeded defect D5), and arm A quoted it as a Markdown link; the repository
link check scans every `*.md` file and would reject both. Contents are
byte-identical to what the workers saw and wrote. The worker ledger's
`finished` records for the two scan workers name the original `.md` paths.
