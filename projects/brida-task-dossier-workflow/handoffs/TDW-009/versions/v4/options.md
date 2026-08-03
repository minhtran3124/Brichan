# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `options`
- Artifact version: `4`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md@TDW-009-P3-v3+task-packet-amendment-4`
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

## Version 4 supersession

Versions 1 to 3 are preserved at `versions/v1/options.md`,
`versions/v2/options.md`, and `versions/v3/options.md`. Decisions A through L are
re-affirmed and summarized. Decisions M through Q are new axes forced by the
version-3 review. Every prior-review citation names an archived immutable path.

## Re-affirmed decisions A through L

| Axis | Selected | Rejected, and why |
| --- | --- | --- |
| A record interface | JSON record plus a dedicated `generate` module | Markdown master record (silent empty sections); Python-API-only (record stops being reviewable evidence); TOML (`tomllib` is 3.11+); a `--record` flag on `scaffold.py` (scaffold behaviour is forbidden to change) |
| B summary surface | Dedicated `summary` module, text by default, JSON on request | JSON-only; a `--summary` flag on the validator (changes a command wired into `make check`) |
| C write anchoring | Descriptor walk from the projects root | Pathname writes with `O_NOFOLLOW` on the final component; `openat2` with `RESOLVE_BENEATH` (Linux-only) |
| D publication | Temporary plus `os.link`, published on `EEXIST` refusal | Direct write to the final name; `os.replace` (overwrites, no `dir_fd`); `O_TMPFILE` plus `linkat` (Linux-only, `AT_EMPTY_PATH` unexposed) |
| E fixtures | Unmistakably synthetic, non-authoritative | Real independently authored sample reviews |
| F summary exit gate | Complete gate as default and only semantics | Gate only when requested |
| G injection | Refuse structural content | Escape or quote |
| H excluded attacker | Narrow the threat model, lock, and observe after publication | Descriptor-bound link source (unavailable); abandon the design (rejected by the coordinator) |
| I dossier lock | `flock` on the dossier directory descriptor | A `.lock` file (adds a leaf, needs staleness rules); no lock |
| J ancestor-symlinked authority paths | Validator-invalid via five enumerated hunks | Informational only; summary-decided (second authority) |
| K record artifact version | `int` with an exhaustive key-to-type table | `str` with a digit-pattern check |
| L backticks | Refuse per rendered position class | Refuse everywhere (would forbid ordinary `path:line` evidence) |

## Decision M: proving the worked record valid

Version 3 asserted its example was valid while supplying one of eleven artifacts.

### M1 — Complete literal record in `design.md`, extracted by the test (selected)

- Strengths: the mandated assertion becomes possible; the reviewer can parse the
  same bytes the test parses; there is exactly one source of truth.
- Costs: about 227 lines of JSON inside `design.md`.
- Verified before selection: the record was rendered by a reference renderer and
  the repository's own `validate_dossier` returned zero diagnostics with and
  without the complete gate.

### M2 — Abbreviated example plus a separate complete fixture file

- Strengths: keeps `design.md` shorter.
- Rejected: it adds a forty-fifth allowlist path, and it lets the documented
  example and the tested fixture drift apart — exactly the failure the review
  found.

### M3 — Generate the example from code at test time

- Rejected: the artifact of record would then contain no example at all, and a
  reviewer could not check the schema against anything concrete.

## Decision N: deriving the summary exit table

### N1 — Derive exits from actual discovery behaviour (selected)

Read `discover_dossiers`, `discover_partial_dossiers`, and `parse_artifact`, then
write the table from what they do: an existing unreadable `index.md` is
discovered and diagnosed, so exit `1`; root-level partial adoption is diagnosed,
so exit `1`; only an absent or unlistable scope, or an unmatched or ambiguous
`--task`, is exit `2`.

- Strengths: the promise and the code agree; no second authority.
- Costs: the rule needs a composition step — a scope code and a verdict code —
  rather than one flat table.

### N2 — Keep the version-3 rule that an index-less dossier exits `2`

- Rejected: it contradicts the requirement that root-level partial adoption be
  nonzero-and-reported, and it is wrong for an index that exists but cannot be
  read, because discovery globs the path without reading it.

### N3 — Make selection override the project verdict

- Rejected outright: an unmatched `--task` would then hide a partial-adoption or
  duplicate-ID finding, which is precisely the single-authority violation the
  whole design forbids.

## Decision O: what the implementation-start manifest carries

### O1 — Byte snapshots plus digests for the eight modified paths (selected)

- Strengths: a reverse patch is constructible; the digest still proves equality;
  the thirty-six new paths recorded `absent` make the delta exact.
- Costs: the manifest carries a snapshot directory, so it is no longer a single
  text file.

### O2 — Digests only, as in version 3

- Rejected on a mechanical fact: a digest proves equality but cannot reconstruct
  bytes, so the promised reverse patch could never be built from it.

### O3 — A task-start `git` patch instead of snapshots

- Strengths: compact.
- Rejected: it is `HEAD`-relative by construction, and the working tree already
  carries pre-existing user changes that a `HEAD`-relative patch would mix in.

## Decision P: the protected routing file

### P1 — Capture-time bytes are the only reference; no digest in any plan (selected)

- Strengths: survives the user editing the file between plan versions, which has
  already happened once; keeps ownership with the coordinator.
- Costs: no planning artifact can state what the file should contain, so a
  reviewer must read the manifest to check it.

### P2 — Update the hard-coded digest to the current value

- Rejected: it would be stale again the moment the user edits the file, and it
  implicitly asserts that the current bytes are authorized — a judgment neither
  the planner nor the implementer may make.

### P3 — Absorb the file into implementation scope and restore a known state

- Rejected outright: it would revert user-owned work and breaks the packet's
  standing prohibition on touching the routing manifest.

## Decision Q: lock ordering

### Q1 — Render, then walk with `mkdir`, then lock, then mutate (selected)

Phase A renders and validates with no mutation; Phase B may create directories
descriptor-relative; Phase C locks immediately on opening the dossier; Phase D
holds every temporary and artifact mutation.

- Strengths: physically possible, and it preserves the property that actually
  matters — no temporary or artifact leaf is created without the lock.
- Costs: a directory may exist before any lock does, so two invocations can race
  on `mkdir`. The loser observes `EEXIST`, retries the open, and both converge on
  one inode; the lock then admits exactly one.

### Q2 — Lock before every mutation including `mkdir`

- Rejected as impossible: a directory cannot be locked before it exists. Version
  3 stated this ordering and was wrong.

### Q3 — Lock a parent directory instead

- Rejected: it serializes unrelated dossiers under the same project and widens
  the lock's blast radius for no safety gain.

## Selected decision

A1, B1, C2, D3, E2, F1, G1, H3, I1, J1, K1, L1, M1, N1, O1, P1, Q1. Promoted into
`design.md`.

## Claim or decision

The version-4 decisions all follow one rule: a claim stays only if something was
executed or read that supports it. `M1` was chosen after the complete record was
actually rendered and validated, not before. `N1` was written by reading the
three discovery functions rather than by reasoning about what discovery ought to
do. `O2` was rejected on the mechanical fact that a digest cannot rebuild bytes.
`P1` was chosen because the hard-coded digest had already gone stale against a
live user edit. `Q2` was rejected because it describes something the filesystem
cannot do.

## Evidence

- A read-only reference renderer plus the repository's own validator decided
  `M1` before it was selected: the complete eleven-artifact record now in
  `design.md` rendered to 410 lines and produced zero diagnostics from
  `validate_dossier` both with and without `require_complete`.
- `src/brichan/contracts/task_dossier/validation.py:1109-1116,1138-1195` and
  `src/brichan/contracts/task_dossier/parser.py:116-123` are what `N1` was
  written from: discovery globs `*/handoffs/*/index.md` without opening it,
  `parse_artifact` emits `cannot read artifact`, and partial adoption exists only
  in `validate_projects`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md:92-119`
  supplies the `O2` rejection and the `P1` trigger: a digest cannot reconstruct a
  reverse patch, and the digest version 3 hard-coded no longer matches the file.
  Read-only hashing in this session reproduced that mismatch and `git diff --stat`
  confirmed the file is modified relative to `HEAD`.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v3/plan-review.md:175-194`
  supplies the `Q2` rejection in one sentence: the walk creates the dossier and
  only then locks it, so the version-3 ordering was unachievable.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:143-180`
  fixes `H3` wording, `N1`, `O1`, `P1`, and `Q1` as coordinator decisions and
  holds the implementation allowlist at 44 paths, which is why `M2` was rejected
  rather than merely disfavoured.
- Earlier direct execution in this planning effort established the `H3`, `I1`,
  and `D3` facts: `os.link` with `follow_symlinks=False` over a symlinked source
  published a symlink; `fcntl.flock` on a directory descriptor took an exclusive
  lock and refused a second holder; and neither `os.AT_EMPTY_PATH` nor
  `os.O_TMPFILE` is exposed by this build.

## Uncertainty

- `M1` costs about 227 lines in `design.md`. If a future review judges that too
  heavy, the only safe alternative is `M2` plus a forty-fifth allowlist path and
  an explicit drift test between example and fixture; that trade was not taken
  here.
- `N1`'s composition rule is derived from current code. If `discover_dossiers`
  ever reads the index rather than globing its path, the unreadable-index row
  moves from exit `1` to exit `2` and the table must be re-derived.
- `O1` leaves the snapshot directory unversioned and coordinator-owned; nothing
  in this task verifies that snapshots were not themselves altered between
  capture and rollback.
- `P1` records the routing file's ownership question as unresolved. The coordinator
  must still classify the change; this decision only prevents the planner and the
  implementer from deciding it by accident.
- No unresolved uncertainty remains about which branch to take on M, N, O, P, or
  Q: the amendment fixes all five.
