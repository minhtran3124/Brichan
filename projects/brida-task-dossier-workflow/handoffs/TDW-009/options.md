# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `TDW-009`
- Task level: `2`
- Artifact: `options`
- Artifact version: `7`
- Origin: `remediation:projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v6/plan-review.md@TDW-009-P6-v6+task-packet-amendment-7`
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

## Version 7 supersession

Versions 1 to 6 are preserved under `versions/v1/options.md` to
`versions/v6/options.md`. Decisions A through Z are re-affirmed and summarized.
Decisions AA through AD are new axes forced by the replacement review of version
6. Every prior-review citation names an archived immutable path.

## Re-affirmed decisions A through Z

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
| W capture representation | One canonical JSON emitted and consumed by one strict parser | Tab rows with canonical headers; two files that must agree |
| X directory symlinks | `lstat` every `dirnames` entry, emit an `l` row, drop from descent | `followlinks=True`; record only under protected prefixes |
| Y allowlist location | Inside the manifest | External list files; digest-authenticated external lists |
| Z passing delta | `(changed ∪ created)` equals all 44 | Subset allowed, superset rejected |

## Decision AA: where the authorization lives

### AA1 — Freeze the exact 8 and 36 path tuples in the reviewed executable (selected)

The loader compares manifest lists element for element and derives the 44-path
union from the constants.

- Strengths: the authorization cannot be redefined by whoever supplies the
  manifest; substitution and misclassification are refused with the offending
  path named; `build` needs no external list files at all.
- Costs: the plan and the tool are now coupled — a scope change requires editing
  and re-reviewing the block.
- Verified before selection: five probes, including a forged full-44 delta that
  version 6 accepted.

### AA2 — Keep counting 8 / 36 / 44 inside the manifest, as in version 6

- Rejected: the reviewer reproduced the fail-open. Replacing one accepted
  modified path and one accepted new path preserved every count and
  classification; preflight returned `0` and delta printed
  `touched set equals all 44 authorized paths` while two accepted paths went
  untouched and two unauthorized paths were written.

### AA3 — Hash the allowlists and record the digest in the plan

- Rejected: it puts a 64-hex constant back into a planning artifact, which the
  routing-digest history already showed goes stale, and it still requires the
  tool to trust a supplied list.

## Decision AB: reaching the snapshot directory

### AB1 — One frozen path, walked component by component with `O_DIRECTORY | O_NOFOLLOW` (selected)

Leaves are opened `O_NOFOLLOW` relative to that descriptor and confirmed regular
by `fstat` before hashing.

- Strengths: an absolute value, a traversal, a backslash, a non-excluded prefix,
  an alternate path, and an ancestor symlink are all refused; the read cannot
  leave the checkout.
- Costs: exactly one legal snapshot location; a different layout needs a new plan
  version.
- Verified before selection: eight probes, including symlinks at the final and at
  an intermediate component.

### AB2 — Validate the string, then use `os.path.join` and `os.listdir`

- Rejected: this is the version-6 shape. An absolute value discarded the root and
  pathname listing followed ancestor symlinks; both probes returned `0`
  incorrectly.

### AB3 — Resolve with `realpath` and compare prefixes

- Rejected: `realpath` follows links by construction, so it answers a question
  about the resolved target rather than about the path the manifest named.

## Decision AC: how strict the loader's value rules are

### AC1 — Exact non-boolean integer version, nonnegative lengths, 64 lowercase hex digests, zero pair for non-file rows (selected)

- Strengths: the loader now enforces the schema the design always claimed; a
  stored baseline cannot be authenticated by a malformed manifest.
- Costs: four more checks, each with its own diagnostic.
- Verified before selection: seven probes, including `true` accepted by version 6
  because Python `True == 1`.

### AC2 — Leave value checking to the honest `build` path

- Rejected: `build` is not the threat. The loader authenticates a stored file
  that a reviewer must be able to trust independently.

## Decision AD: where the generator routing probe lives

### AD1 — Both arms in the ordered generator unit-test step (selected)

- Strengths: the test is created by an ordered step against the real
  `generate.py`, not implied by a requirement or approximated by a grep.
- Costs: none beyond the test itself; the file is already authorized.

### AD2 — Keep it in `R-G29` and rely on the summary no-open test plus a grep

- Rejected: this is version 6. The summary test never imports the generator, and
  a command-line grep supplies only the static half.

## Selected decision

A1, B1, C2, D3, E2, F1, G1, H3, I1, J1, K1, L1, M1, N1, O1, P1, Q1, R1, S1, T1,
U1, V1, W1, X1, Y1, Z1. Promoted into `design.md`.

## Claim or decision

The version-7 decisions were each chosen after running the alternative and
watching it fail. `AA2` is not hypothetical — it is version 6, and a forged
8 / 36 / 44 manifest passed both gates. `AB2` is version 6 as well, and both an
absolute snapshot directory and an ancestor symlink returned `0`. `AC2` would
leave a stored baseline authenticated by a loader that accepts `true` as its
version. `AD2` is what left the required generator probe unwritten. In every case
the selected option was executed on Python 3.10 before being written down.

## Evidence

- The literal capture block in `design.md` was extracted mechanically and run on
  Python 3.10.11. `AA1`: substituting one accepted modified path, one accepted
  new path, both, and swapping one between the lists were each refused with the
  offending path named; a forged full-44 delta exited `1`.
- `AB1`: absolute, `..`-traversing, embedded-traversal, backslash, non-excluded,
  and alternate `snapshot_dir` values were refused before any filesystem access;
  a symlink at the final component and at an intermediate ancestor were each
  refused by the descriptor walk.
- `AC1`: `capture_map_version` of `true` and `1.0`, row `length` of `-1` and
  `true`, uppercase and malformed digests, and a non-file row with a non-zero
  length were each refused.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/versions/v6/plan-review.md:70-99`
  records the `AA2` reproduction, `:101-123` the `AB2` reproduction, `:149-167`
  the `AC2` gap, and `:125-145` the `AD2` gap.
- `projects/brida-task-dossier-workflow/handoffs/TDW-009/task-packet.md:266-296`
  fixes `AA1`, `AB1`, `AC1`, and `AD1` as coordinator decisions and holds the
  allowlist at 44.

## Uncertainty

- `AA1` couples the plan to the tool. A future scope change must edit the frozen
  tuples inside the reviewed block and be re-reviewed.
- `AB1` permits exactly one snapshot location. A coordinator who needs another
  layout must obtain a new plan version.
- `AC1` tightens what a stored manifest may contain; a manifest produced by an
  older `build` will now be refused, which is intended but is a compatibility
  break for any capture taken under version 6.
- `AD1` cannot be executed until `generate.py` exists; the technique was
  demonstrated on an existing module only.
- No unresolved uncertainty remains about which branch to take on AA, AB, AC, or
  AD: the amendment fixes all four and each was executed before selection.
