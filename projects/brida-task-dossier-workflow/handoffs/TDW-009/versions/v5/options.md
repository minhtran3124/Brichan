# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `options`
- Artifact version: `5`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md@TDW-009-P4-v4+task-packet-amendment-5`
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

## Version 5 supersession

Versions 1 to 4 are preserved under `versions/v1/options.md` to
`versions/v4/options.md`. Decisions A through Q are re-affirmed and summarized.
Decisions R through V are new axes forced by the version-4 review. Every
prior-review citation names an archived immutable path.

## Re-affirmed decisions A through Q

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

## Decision R: making the write-scope gate provable

Version 4's manifest recorded protected paths, the eight modified paths, the 36
absent paths, and only the *names* of untracked leaves. It could not tell whether
a pre-existing tracked or untracked file outside those sets had changed.

### R1 — Complete no-follow capture map over every observed non-excluded file (selected)

One row per non-directory entry: path, type, byte length, SHA-256, sorted.
Symlink rows hash the link target string; the walk never follows.

- Strengths: `unexpected` becomes computable rather than asserted; pre-existing
  tracked modifications and untracked leaves are covered by construction; a
  removal is visible because the row disappears.
- Costs: the capture is larger and must be regenerated to compare — 333 rows in
  this working tree at planning time.
- Verified before selection against this repository and a purpose-built fixture.

### R2 — Extend the manifest with digests for untracked leaves only

- Strengths: smaller than a full map.
- Rejected: it still leaves every unlisted tracked file uncovered, and the review
  named two such files that are currently modified.

### R3 — Compare against `HEAD`

- Rejected on the same ground it was rejected in version 2: the working tree
  carries pre-existing user changes, so a `HEAD` comparison misclassifies the
  user's work as implementation output.

## Decision S: rollback

### S1 — Remove rollback entirely (selected)

Fix forward within the 44 paths; after a scoped commit, recovery is a separately
reviewed commit revert; snapshots are evidence only and no worker may restore or
delete from them.

- Strengths: removes a promise that could not be made safe; eliminates the whole
  class of defects the review found — content-checked identity, symlink-followed
  restoration, unauthenticated snapshots, partial rollback.
- Costs: a failed implementation leaves partial work in the tree until a
  coordinator-reviewed revert.
- Fixed by the amendment; recorded here with its cost.

### S2 — Harden the rollback as the reviewer's bounded revision described

Record post-implementation type, device, inode, length, and digest; `lstat`
every target no-follow; authenticate every snapshot; complete read-only preflight
over all 44 before the first mutation.

- Strengths: closes the specific defects found.
- Rejected: it still cannot provide compare-and-swap against an active
  same-identity process, so it would ship a stronger-sounding procedure with the
  same real limit — and rollback was never a user requirement.

### S3 — Keep version 4's rollback unchanged

- Rejected outright: it could follow a symlink into a different target and
  restore unauthenticated bytes.

## Decision T: where the preflight and delta tests live

### T1 — In already-authorized test files (selected)

`tests/integration/test_task_dossier_workflow.py` and
`tests/contract/test_task_dossier_contract.py` are both already in the 44-path
allowlist as append-only modifications.

- Strengths: keeps the allowlist at exactly 44; the checks become real tests
  rather than prose.
- Costs: the tests must construct their own fixture trees rather than importing a
  shared helper.

### T2 — A forty-fifth helper module

- Strengths: a reusable importable implementation.
- Rejected: the amendment holds the allowlist at 44, and the version-4 claim that
  automation *required* a forty-fifth path was shown to be unsupported.

### T3 — Keep it a manual prose procedure, as in version 4

- Rejected: the review found this supplies no exact executable command and cannot
  establish the guarantee.

## Decision U: `sections[].body[]` versus `claim`

### U1 — Separate position classes (selected)

`sections[].body[]` is one rendered line per element and refuses embedded line
feeds; `claim` permits line feeds and is checked per line.

- Strengths: rendering, line counts, and `authored_values` become
  implementation-independent; multi-line prose stays available where it is
  actually needed.
- Costs: one more position class in the rule table.

### U2 — Allow line feeds in both

- Rejected: this is the version-4 state. One body element could become several
  rendered lines while `authored_values` counted it as one scalar, so two
  conforming implementations could diverge.

### U3 — Forbid line feeds in both

- Rejected: it would make `claim` a single line, and every real claim in this
  dossier is a paragraph.

## Decision V: the exclusion set

### V1 — Exclude `.git`, `.venv`, `.pytest_cache`, any `__pycache__`, the four TDW-009 handoff directories, `.DS_Store`, and `.env` (selected)

- Strengths: excludes only regenerated state, version-control internals, and
  owner-scoped dossier paths; everything else is observed.
- Costs, stated rather than hidden: a change to a `.env` or `.DS_Store` file is
  invisible to the map, the preflight, and the delta.

### V2 — Also exclude `evals/` or `projects/`

- Rejected: the evaluation leaves and the dossier tree are exactly where this
  implementation writes, so excluding them would blind the gate to its own scope.

### V3 — Include `.env`

- Rejected: it may carry secrets, and hashing it into a coordinator-owned
  artifact widens exposure for no gain the delta needs.

## Selected decision

A1, B1, C2, D3, E2, F1, G1, H3, I1, J1, K1, L1, M1, N1, O1, P1, Q1, R1, S1, T1,
U1, V1. Promoted into `design.md`.

## Claim or decision

The version-5 decisions continue the rule that a claim stays only if something
executed supports it. `R1` was selected after the capture script was run against
this repository and a fixture covering nine drift scenarios. `S1` removes
rollback because `S2` — the reviewer's own bounded revision — would still not
provide compare-and-swap against the excluded process, and rollback was never
requested. `T1` keeps the allowlist at 44 by using test files the plan already
authorizes, which the review showed was possible. `U1` splits two position
classes that version 4 conflated. `V1` names every exclusion and states what each
one costs.

## Evidence

- The capture script in `design.md` was executed read-only against this
  repository: `build` produced a 333-row map that includes the pre-existing
  tracked modifications to `config/model-routing.json`,
  `projects/brida-task-dossier-workflow/references.md`, and `tasks.md`, and
  excluded every entry in the `V1` exclusion table. This is the basis for
  selecting `R1` over `R2`.
- The same script was exercised against a purpose-built fixture for nine
  scenarios, all behaving as specified: clean preflight passed; post-capture
  changes to a pre-existing tracked file and to a pre-existing untracked file
  each failed preflight and each landed in `unexpected` at delta time; a
  planned-new collision failed with both `DRIFT` and `COLLISION`; corrupted,
  removed, and symlinked snapshots each failed; and removing an observed file
  failed the delta.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md:70-101`
  supplies the `R2` and `R3` rejections by naming two currently modified tracked
  files that no version-4 section covered.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md:102-134`
  describes the `S2` bounded revision this decision declines, and lists the four
  concrete rollback defects that `S1` removes by construction.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md:210-215`
  states that the version-4 forty-fifth-path claim was unsupported and that
  existing test files may host the checks, which is the basis for `T1`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v4/plan-review.md:165-181`
  states the `U2` defect precisely, and a read-only check confirmed `U1` is
  decidable: single-line body elements accepted, an embedded line feed refused, a
  two-line claim accepted, a claim whose second line is a heading refused.

## Uncertainty

- `R1` is a point-in-time observation. A same-identity process mutating files
  between capture and delta defeats it, and no option here changes that.
- `S1` leaves partial work in the tree after a failed implementation. Whether a
  coordinator-reviewed commit revert is fast enough in practice is untested.
- `T1` means the preflight and delta logic exists twice: once as the heredoc the
  implementer runs, once inside the tests. Keeping them in step is a maintenance
  cost this decision accepts rather than solves.
- `V1`'s `.env` exclusion is a deliberate blind spot. If a future task needs to
  prove `.env` unchanged, the exclusion must be revisited with the secret-handling
  question answered first.
- No unresolved uncertainty remains about which branch to take on R, S, T, U, or
  V: the amendment fixes all five.
