# WFS-B-204 independent code review

Task: `WFS-B-204`. Plan: `WFS-B-204-PLAN-001`, version 1. Reviewer attempt:
`attempt-review-1`. Techstack Snapshot SHA-256:
`a34a32054ea7d62ce26d7b6143a09f006fc59ab4e84381a4e1d4ea06ae702339` (verify
returned `match` before any other work; all eight required selected rule files
were read).

Reviewing session: an independent Claude Opus 5 main-agent session with no
implementation context, in the detached worktree
`brichan-wfs-204b`. The diff was read directly; the implementer's
`worker-report.md` was read only after independent verification, for
comparison.

## 1. Verdict

**PASS**

## 2. Per-criterion scores

| Criterion | Score |
|---|---:|
| Spec fidelity | 5 / 5 |
| Code review | 5 / 5 |
| Empirical verification | 5 / 5 |

**Spec fidelity — 5/5.** Every acceptance criterion holds, checked
independently rather than from the report.

- `--task <TASK-ID>` on launch, recorded verbatim and never inferred:
  `commands.md:19` (launch block) and `commands.md:69-70`. The wording matches
  the shipped help text verbatim
  (`worker_launch.py:422-428`: "task identifier recorded verbatim in the worker
  ledger; never inferred when the flag is absent").
- Installed launches always use the fixed `.brichan/ledger/workers.jsonl` and
  reject `--ledger-file`: `commands.md:70-73`. Confirmed in code —
  `worker_launch.py:520-523` passes `installed_location(paths.project_root)`
  unconditionally for a named route, and
  `worker_ledger.py:139-149` fixes the path to
  `(".brichan", "ledger", "workers.jsonl")`. The `--ledger-file` flag is
  defined only when `checkout_root is not None`
  (`worker_launch.py:430-439`, `worker_ledger.py:688-691`).
- The installed `finish` command with `--project`, `--worker`, `--launch-id`,
  `--evidence`, its refusals, and attestation-not-proof:
  `commands.md:88-109`.
- Installed-mode text mentions no checkout-only flag as usable. The only two
  occurrences of `--ledger-file` in the packaged tree are
  `commands.md:72` and `commands.md:115`, both stating its rejection. No
  packaged fenced block contains it, and `bin/brichan-…` and
  `projects/<slug>/ledger` appear nowhere in the new text.
- `SKILL.md:15-25` threads the same rules through the workflow and renumbers
  the old step 7 to step 8. No other file in the skill tree references a step
  number, so the renumbering breaks nothing
  (`grep -rn "step [0-9]"` over the skill tree returns nothing).

**Code review — 5/5.** Every documented command, flag, exit code, stderr
string, and refusal was checked against the parser source and then executed.
No contract was weakened and no behavior changed: the diff is documentation
plus tests only, with no runtime source touched
(`git diff --stat`: `SKILL.md` +8/-3, `commands.md` +55/-3, parity contract
+10, plus one new untracked contract test).

Each documented refusal, executed against the shipped installed entry point in
a temporary target, exits `1` and writes nothing:

| Documented refusal | Observed |
|---|---|
| unmatched `--launch-id` | `1`, `no launched record for launch_id …`, ledger unchanged |
| already-finished `--launch-id` | `1`, `launch_id … already has a finished record`, ledger unchanged |
| worker name without `brichan-` | `1`, `worker name must begin with brichan-: worker` |
| empty / whitespace-only `--evidence` | `1`, `every --evidence item must be non-empty` |
| target that is not a Git root | `1`, `target project is not a Git repository root: …` |
| target with no regular `.brichan/manifest.json` | `1`, `no ledger for this target: …` |
| `--ledger-file` on installed `finish` | `2`, `unrecognized arguments: --ledger-file …` |
| `--ledger-file` on installed launch | `2`, argparse usage error |
| missing required flag on `finish` | `2`, usage text |

The exit-1 path for a non-Git-root target is reachable because
`ProjectError` subclasses `ValueError` (`project.py:9`) and
`_finish_command` catches `(LedgerError, ValueError, OSError)`
(`worker_ledger.py:722-726`); `LedgerError` is a `RuntimeError`
(`worker_ledger.py:102`) and is caught explicitly. Had `ProjectError` been a
bare `Exception`, the documented exit `1` would have been a traceback — it is
not.

The launch-side claims that need a live Herdr were verified by reading the
code path and confirming the pre-existing suite pins them:

- "appends exactly one `launched` record", "`ledger: launch_id=<uuid>` on
  stderr; stdout stays the verbatim `agent_started` envelope" —
  `worker_launch.py:679-699`, with the envelope written last at line 713.
- "`--dry-run` and `--json` write nothing" — the dry-run path returns at
  `worker_launch.py:568-570`, before the ledger block at line 679.
- "a launch that rolls back appends nothing" — the ledger block sits after the
  rollback scope closes (`worker_launch.py:649-677`), with the comment stating
  the invariant at lines 675-678.
- "a ledger failure after a start … the exit code stays `0` and the worker
  stays up" — `record_launch` never raises (`worker_ledger.py:570-607`) and the
  caller only prints a warning (`worker_launch.py:700-705`).
- "only a legacy launch … whose `--cwd` is not inside an initialized target"
  prints the no-location note — exactly right:
  `legacy_launch_location` (`worker_ledger.py:223-249`) walks upward and
  returns `None` only for a non-Git `--cwd` or a missing regular manifest,
  which
  `tests/integration/test_worker_routing_cli.py:836-857` pins, while
  `:859-877` pins that an initialized target does record.

The two parity markers I considered most likely to be wrong are both correct:
all seven new `PARITY_MARKERS` strings are present in *both* skill trees
(verified by reproducing `tree_text` over each tree), so the additions respect
`PACKAGED-001` and do not force the checkout superset into installed-mode
wording.

No manifest or packaging change is needed and none was made. Package data is a
glob (`pyproject.toml`, `"brichan.resources.dogfood_v1" = ["**/*"]`), and the
installed manifest hashes resource bytes at `init` time
(`lifecycle.py:139-151`) rather than from a checked-in digest list. Both
changed files are already in `IMMUTABLE_PATHS`
(`lifecycle.py:36-37`), so no entry was added. This matches `PACKAGED-002` and
`PACKAGED-003`: no resource added or removed, no state schema touched.

**Empirical verification — 5/5.** Every claim in the report that I re-ran
reproduced exactly, and no edit followed the last successful check (the three
runtime files are byte-identical to their pre-review copies, `cmp`-confirmed,
and `git status --short` is unchanged from the start of the review).

- Focused: `tests.contract.test_packaged_ledger_guidance_contract` (4 tests,
  OK), plus the parity and dogfood-policy contracts (33 tests together, OK) on
  Python 3.10.
- `TEST-001` both-interpreter gate: the new contract test, the parity contract,
  and `tests.unit.test_worker_ledger` ran under
  `/opt/homebrew/bin/python3.14` — 58 tests, OK.
- `PYTHONDONTWRITEBYTECODE=1 make check`: unit 1026 OK; the metrics validator
  10 OK; contract 152 with exactly the two known worktree-only failures and one
  pre-existing permitted skip. `make` aborts there, so every later layer was run
  individually: `test-integration` 222 OK, `techstack-eval` OK, `metrics`,
  `receipts`, `dossiers`, `memory-check`, `readme-check`, `phase5-preflight`,
  `package-check` all pass. `path-check` fails — same cause, see Finding L1.

## 3. Findings

No critical, high, or medium findings.

### Low

**L1 — `make check` fails in three places from the known worktree-only cause,
not two. Pre-existing; not this change's defect.**

Evidence: `tests/contract/test_repository_paths.py:64` and `:159` fail with
`unclassified root files: .git`, as the task packet describes. In addition
`make path-check` (`Makefile:52-53`, running
`scripts/check_repository_paths.py`) fails with the identical message and exit
`1`. That script is the very thing
`test_current_path_and_link_contracts_pass` shells out to, so it is one root
cause — a detached worktree's `.git` is a file, not a directory — surfacing at
a third gate step. I did not fix it, as instructed. Recorded only so the next
reader is not surprised that the gate stops in three places rather than two.
The implementer's report already states this at the same level of detail.

**L2 — one newly introduced prose line overflows the file's own wrap width.**

Evidence: `commands.md:24` is 90 characters —
`Herdr. Submit prompts with \`herdr pane run\`. Close only a recorded Brichan-owned pane with`.
The paragraph at `:22-25` was re-wrapped to insert the `--task` sentence, but
its last line was left at the old break. Every other prose line in the file is
at most 80 characters; the remaining over-80 lines are a table row and a
command line, which the file (and the checkout counterpart) does not wrap.
Reproduce: `awk 'length>80' …/references/commands.md`. This repository
configures no linter, so nothing enforces it and nothing breaks. Style only —
not a defect, and not a reason to withhold PASS.

## 4. Test gaps

**G1 — the new drift test is directional: it catches doc drift, not a
prefix-compatible parser rename.** This is the one gap with teeth, and it is
broader than the report's own note.

The report records that "argparse accepts unambiguous long-option prefixes, so
the drift test would not catch a doc that abbreviates a flag … this is
cosmetic", and its three mutations were all doc-side. The converse direction is
the one that matters, and it is unguarded. Renaming a parser flag to a longer
name for which the documented spelling is still an unambiguous prefix leaves the
packaged skill describing a flag that survives only by abbreviation, and
*nothing in the repository fails*:

- `worker_ledger.py:690`, `finish.add_argument("--project")` →
  `finish.add_argument("--project-root", dest="project")`:
  `tests.unit.test_worker_ledger` (38) OK, `make test-integration` (222) OK,
  and the new contract test (4) OK.
- `worker_launch.py:422`, `--task` → `--task-id` (with `dest="task"`):
  `make test-integration` (222) OK and the new contract test (4) OK.

Both were run with the file restored byte-identical afterwards (`cmp`).
A hardening option, should the team want it, is to assert the documented
spelling against the parser's own option strings rather than relying on a
successful parse — for example comparing the tokens beginning `--` in each
documented block against
`{s for a in parser._actions for s in a.option_strings}`, or parsing with
`allow_abbrev=False`. This is an improvement beyond the stated acceptance
criteria, which ask only that the documented commands and flags match the
shipped CLI — they do today. Recorded as a gap, not a defect.

**G2 — the new contract test covers only the happy path of `finish`; the
refusals it asserts in prose are behaviourally pinned elsewhere.** Removing the
already-finished refusal (`worker_ledger.py:632-633`), the `brichan-` prefix
refusal (`:703`), or adding `--ledger-file` back to the installed `finish`
parser each leaves
`tests.contract.test_packaged_ledger_guidance_contract` green. All three are
caught by the pre-existing `tests/unit/test_worker_ledger.py`
(`:608`, `:698`, `:770`) — I confirmed each mutation fails that suite. So the
behaviour is owned and covered; the new file correctly does not duplicate it,
which is the right call under operating-principles §5 ("coverage that restates
the implementation is cost, not evidence"). No action needed.

**G3 — no test asserts the packaged skill and the checkout skill stay
*consistent* about the fixed ledger path.** The parity markers require the
literal `.brichan/ledger/workers.jsonl` in both trees, which is the useful
half. Nothing would catch the two trees describing contradictory *behaviour*
for that path while both still containing the string. Low value; noted for
completeness.

## 5. Residual risks and required human decisions

**R1 — existing installed projects do not receive this guidance until
reinitialized.** `SKILL.md` and `references/commands.md` are immutable managed
resources (`lifecycle.py:36-37`). `inspect_project` compares each installed
file against the hash recorded in *that project's own* manifest
(`lifecycle.py:275-297`), not against the current package, so an already-
initialized target stays `HEALTHY` while holding the old text — the version
with no worker-ledger guidance, which is exactly the WLG-001 residual risk this
task closes. This is the deliberate `PACKAGED-002` path, correctly not
automated here. **Human decision:** which dogfood targets get backed up and
reinitialized, and when. Until that happens, the risk is closed in the package
but still open in the field.

**R2 — `--project` is optional in the installed parser, and the skill says so.**
Without it, `find_git_root()` walks upward from the process working directory
(`worker_ledger.py:203-221`). `commands.md:97-99` documents the fallback
accurately rather than claiming the flag is required. The residual risk is
operational: a coordinator running `finish` from inside the wrong repository
silently attests into that repository's ledger, where the unmatched-`launch_id`
refusal is the only thing standing between it and a misfiled record. That
refusal does hold (verified: exit `1`, nothing written, ledger not even
created). Making `--project` required is a behaviour change outside this
task's scope and would need its own decision.

**R3 — the packaged skill mentions the legacy `-- <command>` launch form
without documenting it.** `commands.md:82-84` scopes the no-location note to
"a legacy launch with an explicit command after `--`", but the packaged
`commands.md` has no legacy-launch section (the checkout copy does). The
sentence still does its job — telling an installed coordinator that a routed
launch never prints that note — so this is a coherence nit, not an error.

**R4 — the new test file is untracked.** `git status --short` shows
`?? tests/contract/test_packaged_ledger_guidance_contract.py`. Correct for an
uncommitted handoff, but whoever commits must `git add` it, or the parity
additions ship without the drift guard that justifies them.

**R5 — no evidence gaps.** Everything the acceptance criteria demand was
observable from this worktree without Herdr, and I observed it. The only claims
I could not execute end-to-end are the live-launch stderr lines, which require a
running Herdr control plane; those are pinned by
`tests/integration/test_worker_routing_cli.py:538`, `:593-648`, `:722-793`,
`:836-877`, which passed here (222 tests, OK).
