# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `options`
- Artifact version: `6`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v5/plan-review.md@TDW-009-P5-v5+task-packet-amendment-6`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `3ebc7268-a8cd-464c-8d65-9920f2beac5c`
- Effective route: `plan`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Version 6 supersession

Versions 1 to 5 are preserved under `versions/v1/options.md` to
`versions/v5/options.md`. Decisions A through V are re-affirmed and summarized.
Decisions W through Z are new axes forced by the replacement review of version 5.
Every prior-review citation names an archived immutable path.

## Re-affirmed decisions A through V

| Axis | Selected | Rejected, and why |
| --- | --- | --- |
| A record interface | JSON record plus a dedicated `generate` module | Markdown master record; Python-API-only; TOML (3.11+); a `--record` flag on `scaffold.py` |
| B summary surface | Dedicated `summary` module, text by default, JSON on request | JSON-only; a `--summary` flag on the validator |
| C write anchoring | Descriptor walk from the projects root | Pathname writes with `O_NOFOLLOW` on the final component; `openat2` (Linux-only) |
| D publication | Temporary plus `os.link`, published on `EEXIST` refusal | Direct write to the final name; `os.replace`; `O_TMPFILE` plus `linkat` |
| E fixtures | Unmistakably synthetic, non-authoritative | Real independently authored sample reviews |
| F summary exit gate | Complete gate as default and only semantics | Gate only when requested |
| G injection | Refuse structural content | Escape or quote |
| H excluded process | Narrow the threat model, lock, and observe after publication | Descriptor-bound link source (unavailable); abandon the design |
| I dossier lock | `flock` on the dossier directory descriptor | A `.lock` file; no lock |
| J ancestor-symlinked authority paths | Validator-invalid via five enumerated hunks | Informational only; summary-decided |
| K record artifact version | `int` with an exhaustive key-to-type table | `str` with a digit-pattern check |
| L backticks | Refuse per rendered position class | Refuse everywhere |
| M worked record | Complete literal record in `design.md`, extracted by the test | Abbreviated example plus separate fixture; generated at test time |
| N summary exit table | Derived from actual discovery behaviour | Version-3's assumed model; selection overriding the project verdict |
| O baseline content | Byte snapshots plus digests | Digests only; a `HEAD`-relative patch |
| P protected routing file | Capture-time bytes only, no digest in any plan | Update the hard-coded digest; absorb and restore the file |
| Q lock ordering | Render, walk with `mkdir`, lock, then mutate | Lock before every mutation (impossible); lock a parent directory |
| R baseline completeness | Complete no-follow map over every observed non-excluded file | Digests for untracked leaves only; comparing against `HEAD` |
| S rollback | Remove it entirely; fix forward, then a reviewed commit revert | Harden it as the reviewer described; keep version 4's unchanged |
| T test location | Already-authorized integration and contract test files | A forty-fifth helper module; a manual prose procedure |
| U body versus claim | Separate position classes; body refuses line feeds | Allow line feeds in both; forbid them in both |
| V exclusion set | Ten enumerated entries, costs stated | Also excluding `evals/` or `projects/`; including `.env` |

## Decision W: one representation for the capture

### W1 — Canonical JSON emitted and consumed by one strict parser (selected)

`build` writes the JSON; `preflight` and `delta` read it through a single loader
that validates version, exclusions, row shape, sort order, and both allowlists.

- Strengths: the format a coordinator is told to produce is exactly the format
  the code accepts; a reviewer can extract the block and round-trip it; JSON
  removes the section and key-collision problems that broke version 5.
- Costs: the capture file is larger and less greppable than tab rows.
- Verified before selection: `build` output was accepted by its own loader, and
  fourteen mutations each failed closed.

### W2 — Keep tab rows and add canonical headers around them

- Rejected: this is the version-5 shape. The reviewer reproduced both failures —
  header lines made the byte comparison permanently unequal, and a `[snapshots]`
  line overwrote the same path's four-column row, raising `IndexError`.

### W3 — Two files, canonical metadata plus a rows sidecar

- Rejected: two artifacts that must agree is the same defect with more moving
  parts, and nothing would validate their agreement.

## Decision X: recording symlinks that point at directories

### X1 — `lstat` every `dirnames` entry, emit an `l` row, drop it from descent (selected)

- Strengths: the map becomes complete in the sense the contract already claimed;
  retargeting or replacing such a link is visible; no traversal ever follows a
  link.
- Costs: one `lstat` per directory entry.
- Verified before selection: version 5's block produced no row for a
  directory symlink and returned `delta OK` after retargeting it; the corrected
  block produces an `l` row and exits `1` on retarget, on replacement by a real
  directory, and on replacement by a regular file.

### X2 — Set `followlinks=True` and let the walk descend

- Rejected outright: it violates the no-follow guarantee and can loop.

### X3 — Record directory symlinks only under protected prefixes

- Rejected: partial completeness is what produced this finding.

## Decision Y: where the allowlists live

### Y1 — Inside the manifest, validated to exactly 8 / 36 / 44 (selected)

- Strengths: there are no external list files for a later mode to trust, so a
  truncated list cannot narrow a gate; membership is checked before any
  filesystem state is read.
- Costs: changing the authorized scope means re-capturing, and the three counts
  are frozen in the code so the loader fails closed until they change together.

### Y2 — External whitespace-split list files, as in version 5

- Rejected: the reviewer reproduced the fail-open. Omitting a colliding path from
  the new list let preflight return `0` while claiming the new paths were absent.

### Y3 — Authenticate external lists with digests recorded in the manifest

- Rejected: it re-introduces two artifacts that must agree, for no benefit over
  putting the lists in the manifest.

## Decision Z: what a passing delta means

### Z1 — `(changed ∪ created)` must equal all 44 (selected)

Plus no removals and an empty unexpected set. `missing` is computed and fatal.

- Strengths: an under-touch is now a failure. Version 5 printed
  `delta OK: 1 of 2 authorized paths touched` for a strict subset.
- Costs: a partial implementation cannot hand off, which is the intent.

### Z2 — Subset allowed, superset rejected

- Rejected: it accepts an incomplete implementation as authorized, and the
  amendment requires exact equality.

## Selected decision

A1, B1, C2, D3, E2, F1, G1, H3, I1, J1, K1, L1, M1, N1, O1, P1, Q1, R1, S1, T1,
U1, V1, W1, X1, Y1, Z1. Promoted into `design.md`.

## Claim or decision

The version-6 decisions were each chosen after running the alternative and
watching it fail. `W2` is not a hypothetical: it is version 5's shape, and the
reviewer reproduced both its byte-comparison failure and its `IndexError`. `X2`
and `X3` were rejected because partial completeness is exactly what let a
retargeted directory symlink pass unnoticed. `Y2` was reproduced fail-open by
the reviewer and again here. `Z2` is what version 5 shipped, and it reported
success for a strict subset. In every case the selected option was executed on
Python 3.10 before being written down.

## Evidence

- The literal capture block in `design.md` was extracted mechanically and run on
  Python 3.10.11. `W1`: `build` emitted a canonical manifest that its own strict
  loader accepted, and fourteen mutations — wrong version, altered exclusions,
  unknown and missing top-level keys, 7-not-8 modified, 35-not-36 new,
  duplicates in either list, a new path colliding with a row, a duplicate row
  path, unsorted rows, a malformed row, a bad row type, a boolean length, and a
  duplicate JSON key — each failed closed.
- `X1`: on a fixture with a symlink to a directory, the corrected block emitted
  an `l` row; retargeting it made preflight and delta exit `1`; replacing it with
  a real directory removed the row; replacing it with a regular file flipped the
  row type. `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v5/plan-review.md:94-121`
  records the reviewer's reproduction of the version-5 omission.
- `Y1` and `Z1`: with an 8/36/44 fixture, touching all 44 paths exited `0`;
  touching 43 exited `1` with `UNTOUCHED ... <-- MISSING`; touching 44 plus one
  outside path exited `1` with `<-- UNEXPECTED`.
  `versions/v5/plan-review.md:122-151` records both version-5 fail-opens.
- `versions/v5/plan-review.md:65-92` records the `W2` failure in the reviewer's
  own execution: canonical headers made `current != capture` permanently true and
  the `[snapshots]` line collided with a `[rows]` entry.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:229-262`
  fixes `W1`, `X1`, `Y1`, `Z1`, and the routing probe as coordinator decisions
  and holds the allowlist at 44.

## Uncertainty

- `W1` makes the manifest larger; nothing in this task measures how large the
  real capture will be beyond the 333 rows observed at planning time.
- `X1` costs one `lstat` per directory entry. On a very large tree that is
  measurable, but it was not measured here.
- `Y1` freezes 8, 36, and 44 in the code. A future scope change must alter the
  manifest and the constants together, and the loader fails closed until it does.
- `Z1` means a partial implementation cannot hand off even to report progress.
  That is intended, but it removes an escape hatch a future task may want.
- No unresolved uncertainty remains about which branch to take on W, X, Y, or Z:
  the amendment fixes all four and each was executed before selection.
