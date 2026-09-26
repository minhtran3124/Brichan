# Code review

Independent review of the implementation, or the recorded evidence for why no implementation review applies.

## Artifact metadata

- Task ID: `WFS-008`
- Task level: `0`
- Artifact: `code-review`
- Artifact version: `1`
- Origin: `wfs-008-code-review-worker:2026-09-26:v1`
- Owner: `reviewer`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `code-review-session-12df78ee`
- Effective route: `review`
- Effective model: `claude-opus-5`
- Effective effort: `high`
- Reviewing session: `code-review-session-12df78ee`
- Review verdict: `PASS`

## Review target

- Reviewed plan ID: `null`
- Reviewed plan version: `null`

The dossier carries no `plan.md`, so under `docs/workflows/task-dossier.md`
(Evidence contract) it has no plan artifact to review and both targets stay
null. The plan I reviewed against is the `Plan` section of `report.md`, which
names plan `WFS-008-PLAN-001` version 1; at level 0 that plan is not a
versioned dossier artifact, has no acceptance step, and gets no plan review.

## Review provenance

- Reviewing session `code-review-session-12df78ee` (full identifier
  `12df78ee-0bb8-4785-8282-bfe4f3408fec`) is a fresh session with no
  implementation context. It is not `report.md`'s authoring session
  (`claude-code-45e6ef45`) and not `request.md`'s
  (`coordinator-session-7d42ad6a`). I did not make this change.
- `config/model-routing.json` routes `review` to runtime `codex`, model
  `gpt-5.6-sol`, effort `medium`. Codex is usage-limited, which `request.md`
  records, so this review ran Claude `claude-opus-5` at `high` effort. Level 0
  requires only the routine review route's strength, and `claude-opus-5` at
  `high` is not weaker than that, so the deviation does not lower reviewer
  strength. Provider independence is not satisfied; model independence is
  (`claude-opus-5-5` implemented, `claude-opus-5` reviewed). Levels 0 and 1
  leave the index's review-route override null, so there is no field to record
  it in, and it is recorded here instead.
- Reviewed state: the uncommitted working tree of branch
  `fix/worktree-git-file` at `6bab70d`, two modified tracked files in scope,
  `scripts/check_repository_paths.py` and
  `tests/contract/test_repository_paths.py`.
- `.codex/config.toml` is out of scope per the packet. I read its diff only far
  enough to confirm it cannot bear on this review: it adds
  `realtime_conversation = false` and an `mcp_servers.node_repl` block, carries
  no path or classification content, and `.codex` is not a contract path.
- Mutation work ran on a scratch detached worktree outside the repository, never
  on the main checkout. Both scratch worktrees were removed; `git worktree list`
  shows only the main checkout and the pre-existing
  `brichan-policy-benchmark`.
- No commit, push, remote action, or Herdr agent or pane operation was taken. I
  wrote exactly this one file.

## Verdict

`PASS`. All four acceptance criteria hold, and I established each by execution
rather than by reading `report.md`.

The fix is correct and minimal. The root-file classification now exempts exactly
the root entry named `.git` and nothing else, which is the one thing that
differs between a main checkout, where `.git` is a directory that `is_file()`
already excluded, and a linked worktree, where `.git` is a regular pointer file
that `is_file()` admitted. I reproduced the bug in a fresh detached worktree
before the fix and its absence after, and I confirmed live — not only in a unit
test — that other unclassified root files are still reported alongside the
exempted `.git`.

Choosing code over the manifest is the right call and I agree with the stated
reason. `ignored_root_files` holds machine-local ephemera (`.DS_Store`, `.env`,
`CLAUDE.local.md`); git's own root entry is not machine-local ephemera, and a
manifest entry would be data that a later edit could widen without review.

The change is also consistent with an invariant the repository already holds
elsewhere rather than inventing one: `src/brichan/techstacks/filesystem.py`
already treats root `.git` as "either a directory or a regular worktree file"
(`GIT_MARKER_NAME` at line 823, and the comment at lines 939-994), and
`src/brichan/project.py` lines 39 and 49 already probe it with `exists()`, which
is worktree-safe. `scripts/check_repository_paths.py` was the outlier. I grepped
for other sites assuming a `.git` directory and found none left.

Four Low findings are recorded. None blocks. Two are report and dossier evidence
corrections, one is a one-word test strengthening, and one is a coordinator
close-out item.

## Per-criterion scores

| Criterion | Score | Basis |
| --- | --- | --- |
| Spec fidelity | 5/5 | The diff is exactly what `request.md` and the `Plan` section of `report.md` specify, and nothing more. Two files changed; `config/repository-paths.json` is untouched, as the plan says it should be; the `unclassified root files:` error text is unchanged; the extraction into `unclassified_root_files` moves the existing comprehension verbatim and adds one term. "Every other root-file classification must stay as strict as today" holds, and I checked it live rather than by reading: in the worktree, with the `.git` pointer file present, `.git.bak` and `stray.txt` dropped at the root are both still reported. No scope drift and no incidental edit. |
| Code review | 4/5 | Nothing in the change is wrong or risky, and the exemption is as narrow as it can be: an exact-name test, not a prefix and not `SKIPPED_PARTS` reuse. One point off for two Lows. L3: the literal `.git` now exists three times across the two files — `SKIPPED_PARTS` at `scripts/check_repository_paths.py:18`, `GIT_METADATA` at line 21, and a hardcoded `".git"` at `tests/contract/test_repository_paths.py:68` — so the constant the change introduces is not actually the single source of truth it was introduced to be. L2: the plan's explicit rejection of `SKIPPED_PARTS` reuse is not pinned by any test, and I confirmed by mutation that reintroducing it survives the whole suite. |
| Empirical verification | 4/5 | Every claim in `report.md` reproduced in this session, on both interpreters, including the pre-fix failure signature, the post-fix pass, the mutation results, and the confinement of the `make check` red to WFS-008's own pending artifacts. The script's SHA-256 matches the value the report records. One point off for L1: one claim in the report's `Risks` section does not hold, and I established that it does not hold by running the mutation it names. |

## Findings

No Critical, High, or Medium finding.

### L1 — Low, not blocking. A claim in the report's `Risks` section is wrong: that test does not guard the change it is said to guard

`report.md`'s `Risks` section says of
`test_a_git_directory_is_not_an_unclassified_root_file`:

```text
it guards a change from `is_file()` to `exists()`, not the new exemption.
```

It guards neither, on its own. With the exemption present, a `.git` directory is
excluded by `path.name != GIT_METADATA` whether the predicate is `is_file()` or
`exists()`, so switching to `exists()` leaves the test green. I ran all three
cases against the test in isolation on a scratch copy:

| Mutation to `scripts/check_repository_paths.py` | `test_a_git_directory_is_not_an_unclassified_root_file` |
| --- | --- |
| delete `and path.name != GIT_METADATA` | `OK` |
| `if path.is_file()` becomes `if path.exists()` | `OK` |
| both, together | `FAILED (failures=1)` |

So the test fails only when both guards are removed at once. It is not a dead
assertion — it can fail — but it is weaker than the report claims, and under
`techstacks/python/tests.md` `TEST-003` a test named for a rejection is expected
to fail when the guard it names is removed.

The `is_file()` to `exists()` mutation is caught, just by a different test:
`test_current_path_and_link_contracts_pass` fails, because with `exists()` every
root directory becomes an unclassified root file.

Secondary, same artifact: the report's `Plan` gives the new signature as
`unclassified_root_files(root, manifest)`, while the code and the report's own
`Changes` section give `unclassified_root_files(root, ignored_root_files,
known_paths)`. The plan was written before implementing and `Changes` records
what shipped, so this is a stale sketch rather than a contradiction of fact, but
a reader comparing the two sections sees two signatures.

Not blocking: the acceptance criterion this bears on — a committed regression
test fails if the `.git` exemption is removed — holds through two other tests,
and I verified it independently. `DOSSIER-004` applies to the fix: correct both
lines in `report.md` in place, and do not append a later contradicting section.
Optionally, give the directory case its own reachable guard by asserting on a
root that also holds an unclassified file, so the test fails when either guard
goes.

### L2 — Low, not blocking. The plan's explicit design decision is not pinned by a test

`report.md`'s `Plan` states the exemption excludes the root entry named `.git`
"and nothing else: no pattern, no `SKIPPED_PARTS` reuse (that would also exempt
a root file named `__pycache__`)".

The narrowness is half-pinned. Widening to a prefix is caught: I mutated
`path.name != GIT_METADATA` to `not path.name.startswith(GIT_METADATA)` and
`test_other_unclassified_root_files_are_still_reported` failed, because of the
`.git.bak` case.

The `SKIPPED_PARTS` widening the plan specifically names is not caught. I
mutated the same line to `path.name not in SKIPPED_PARTS` and the full contract
module reported `Ran 10 tests` / `OK`. A root file named `__pycache__` would
then be silently exempt, and nothing in the suite would notice.

The fix is one word: add `__pycache__` to the name tuple in
`test_other_unclassified_root_files_are_still_reported`
(`tests/contract/test_repository_paths.py:93`) and to its expected list. That
test already owns exactly this concern and already builds the temporary root.

Not blocking: the shipped code is correct, and this is a guard against a future
edit rather than a defect in the current behavior. It is recorded as a finding
rather than a residual risk because the plan names this specific widening as the
thing it is avoiding, so pinning it is inside the change's own stated contract.

### L3 — Low, not blocking. Three copies of the literal `.git` across the two changed files

The change introduces `GIT_METADATA = ".git"`
(`scripts/check_repository_paths.py:21`) to give the exemption one named home,
but the literal now appears three times:

- `scripts/check_repository_paths.py:18`: `SKIPPED_PARTS = {".git", "__pycache__"}`
- `scripts/check_repository_paths.py:21`: `GIT_METADATA = ".git"`
- `tests/contract/test_repository_paths.py:68`: `and path.name != ".git"`

The third is the one with teeth. `test_every_non_ephemeral_root_file_is_classified`
duplicates the production comprehension instead of calling
`unclassified_root_files`, so the copy in the test can drift from the code it is
meant to hold to account, and it would keep passing if the production exemption
changed name. I confirmed the drift is real today in direction if not in value:
deleting the exemption from the production function leaves that test green in a
main checkout, and it fails in a worktree only because of its own private copy
of the rule, not because of the code under test.

Two smaller points in the same family: `SKIPPED_PARTS` could read
`{GIT_METADATA, "__pycache__"}` so the module has one definition of the name;
and the new constant is called `GIT_METADATA` while the established constant for
the same concept elsewhere in the repository is `GIT_MARKER_NAME`
(`src/brichan/techstacks/filesystem.py:823`).

Not blocking: no current behavior is wrong, and the duplication in
`test_every_non_ephemeral_root_file_is_classified` predates this change — the
diff tightened an existing copy rather than creating one. Worth a follow-up that
has the test import `GIT_METADATA`, or delegate the `actual` set to
`unclassified_root_files`, so the rule lives in one place.

### L4 — Low, not blocking. The index records no level determination, so the level claim has no recorded basis to check

`docs/workflows/task-dossier.md` (Levels) requires the index's `Evidence`
section to record the level determination: the level-raising trigger that fixed
the level, or a recorded statement that none applies. `docs/policy/reviewer.md`
makes checking that recorded claim a reviewer obligation. `index.md` is still
the unedited template, its `Evidence` section reading
`<repository or source evidence for the claim>`, so there is no recorded claim
to check.

I therefore checked the triggers directly, and I accept the declared level 0:

- Level 1 triggers: no separate planning artifact or sub-delegation was
  requested; the work was done and verified inside one worker session and is not
  expected to resume; no architecture or compatibility surface changes, since
  the script is a local checkout validator that is not packaged and no caller's
  interface moves; and the four acceptance criteria needed no decomposition.
- The one arguable level 1 trigger is "multiple credible options exist". Two
  did: exempt `.git` in `config/repository-paths.json` under
  `ignored_root_files`, or exempt it in code. The implementer weighed both in
  one paragraph of the `Plan` and rejected the manifest on a stated policy
  ground. I judge that below the trigger, which reads to me as options needing
  evaluation rather than a choice settled by an existing rule. I record it
  because it is a judgment call, not an obvious one.
- Level 2 triggers: `docs/policy/reviewer.md`'s mandatory-review list does not
  apply — no authentication, authorization, secret, payment, or personal-data
  surface; no destructive migration; no production or deployment behavior, as
  the script never ships; no public API, database schema, or cross-service
  contract, `scripts/` being an internal contract path rather than an external
  one; not cross-cutting at two files and roughly forty lines; and no worker
  failed repeatedly. One writer produced the implementation, and no reliability,
  compatibility, cost, or permission trade-off is being accepted.

Nothing material turns on the level 0 versus level 1 question here: both levels
require the same four artifacts, the same routine reviewer strength, and
`not-requested` ship authorization, code review is required either way — at
level 0 because the diff touches a contract path, at level 1 unconditionally —
and every artifact already carries well above the level 1 floor of two evidence
items.

Not blocking, and not a defect in the diff: this is a coordinator close-out item
on `index.md`, which the packet places outside my write scope and whose current
red is sanctioned. It must be recorded before the dossier can pass.

## Test gaps

No test gap rises to the missing-regression-test defect in
`docs/policy/reviewer.md`, and there is no such defect here.

The behavior this change introduces is: the root entry named `.git` is exempt
from root-file classification. Two committed tests fail if it regresses, which I
verified by mutation on a scratch copy rather than by reading the report:

- Removing `and path.name != GIT_METADATA` fails
  `test_a_worktree_git_file_is_not_an_unclassified_root_file`,
  `test_other_unclassified_root_files_are_still_reported`, and, when the suite
  runs inside a worktree, `test_current_path_and_link_contracts_pass`.
- Widening it to `startswith` fails
  `test_other_unclassified_root_files_are_still_reported`.

Both new behavior-bearing tests call the production function
`unclassified_root_files` directly, so they satisfy `TEST-003`'s requirement
that a test named for a rejection exercise the production code path. The third
new test is weaker than claimed; that is L1, and it covers pre-existing
behavior, not the behavior this change introduces, so it is a finding about
evidence accuracy rather than a missing regression test.

Two coverage observations that are not defects:

- No committed test exercises a real detached worktree. The new tests use a
  temporary directory with a `.git` regular file as a stand-in. I checked the
  stand-in is faithful: in a real `git worktree add --detach`, the root `.git`
  is a 92-byte regular ASCII text file whose single line is
  `gitdir: <main checkout>/.git/worktrees/<name>`, which is exactly the shape
  the fixture writes. The real case is additionally covered end to end by
  `test_current_path_and_link_contracts_pass` whenever the suite runs inside a
  worktree, which is the environment the bug was reported from. A test that
  shells out to `git worktree add` would be slow and would need git in the test
  environment; I do not think the contract requires it. Recorded as a residual
  risk.
- The `SKIPPED_PARTS` widening is unpinned. That is L2, raised to a finding
  because the plan names it explicitly.

## Residual risks

1. **The exemption trusts the name, not the content.** `unclassified_root_files`
   exempts any root entry named `.git` without checking that it is a worktree
   pointer. A stray regular file literally named `.git` would be silently
   exempt. This cannot happen in a main checkout, where a `.git` directory
   occupies the name, and in a worktree the file is git's own. So the exposure
   is confined to a root that is neither, which for this script means only a
   test fixture. Hardening is available and has precedent in this repository if
   the coordinator ever wants it:
   `src/brichan/techstacks/filesystem.py` already validates the regular-file
   case rather than trusting the name. That is beyond this task's contract, so
   it is a risk to decide on, not a finding.
2. **Only this checker was fixed; `make check` as a whole is still not green in
   a worktree, and cannot be.** Task dossiers under
   `projects/*/handoffs/*/` are gitignored, so they do not exist in a fresh
   worktree, and `make dossiers` and the dossier integration test see a
   different world there. WFS-008 never claimed otherwise — its acceptance
   criteria name `make path-check` and one test module — but "the worktree bug
   is fixed" should not be read as "the suite runs clean in a worktree".
3. **`inventoried_root_files` still derives from every one-part manifest path,
   including directories.** A root *file* whose name matched an inventoried root
   *directory* — `projects`, `evals`, `metrics` — would be treated as
   classified. This is pre-existing and unchanged by the diff; the extraction
   moved the comprehension verbatim. Noted so it is not later mistaken for
   something this change introduced.
4. **The dossier validator's summary line reads as if the blast radius were
   wider than it is.** `make dossiers` prints `Invalid task dossiers: 20
   issue(s) across 20 dossier(s).` while all 20 issues are on the single WFS-008
   dossier. The second number is not the count of dossiers with issues: in
   `src/brichan/contracts/task_dossier/validation.py:1406-1407` it is
   `len(dossiers)`, the number of contract-adopting dossiers scanned. The two
   numbers coinciding at 20 makes the line read as one issue per dossier. After
   this artifact replaced the template the same line reads `16 issue(s) across
   20 dossier(s)`, which shows the second number is the scan population. It is
   pre-existing, outside this diff, and cosmetic, but it invites a future reader
   to over-read a sanctioned red.
5. **Provider independence is not satisfied.** Codex is usage-limited, so a
   Claude change was reviewed by Claude. Model independence holds and level 0
   asks only for routine reviewer strength.

## Claim or decision

`PASS`. The uncommitted change to `scripts/check_repository_paths.py` and
`tests/contract/test_repository_paths.py` is exactly the fix WFS-008 specifies:
the root-file classification exempts the root entry named `.git` and nothing
else, so `make path-check` and `tests.contract.test_repository_paths` pass
inside a detached worktree while every other unclassified root file is still
reported. All four acceptance criteria hold on both interpreters, verified by
execution in this session. Four Low findings are recorded and none blocks: L1
and L4 are evidence corrections in `report.md` and `index.md`, L2 is a one-word
test strengthening that pins a design decision the plan states, and L3 is a
consolidation of three copies of the `.git` literal.

## Evidence

- Review applicability: with `set -o pipefail`,
  `git diff --name-only --no-renames | python3 scripts/check_contract_paths.py`
  exits 3 and prints `contract-path: yes` and `scripts/check_repository_paths.py`.
  The directory prefix `scripts/` matches, so independent code review is
  required at level 0 and this artifact's applicability is `required`.
- Diff scope: `git status --short` shows exactly the two in-scope modified files
  plus the pre-existing `M .codex/config.toml` and the untracked `.brichan`,
  `.brichan.bak-*`, and two `evals/workflow-simplification/wfs-005/` files, all
  untouched by me. `git diff --stat -- .codex/config.toml` is
  `1 file changed, 4 insertions(+)`, adding `realtime_conversation = false` and
  an `mcp_servers.node_repl` block, with no path or classification content.
- Acceptance criterion 1, the worktree case, reproduced both ways. I created a
  detached worktree of `6bab70d` outside the repository. Its root `.git` is a
  regular file: `file` reports `ASCII text`, `ls -l` reports 92 bytes, and its
  content is one line, `gitdir: <main checkout>/.git/worktrees/<name>`.
  - Before the fix, at `6bab70d`: `make path-check` printed
    `unclassified root files: .git` and exited 2 (the script exits 1);
    `python3 -m unittest tests.contract.test_repository_paths` reported
    `Ran 7 tests` / `FAILED (failures=2)`, on
    `test_current_path_and_link_contracts_pass` and
    `test_every_non_ephemeral_root_file_is_classified`. This matches the report.
  - After copying the two changed files in: `make path-check` printed
    `repository paths valid: 113 entries, 75 references` and exited 0; the
    contract module reported `Ran 10 tests` / `OK` on Python 3.10.11 and again
    on 3.14.6. The test count rising from 7 to 10 is the three added tests.
  - Strictness preserved, checked live rather than only in a unit test: with the
    `.git` pointer file still present, `touch stray.txt .git.bak` at the
    worktree root made the script print
    `unclassified root files: .git.bak, stray.txt` and exit 1 — `.git` absent
    from the list, the other two reported. Removing them returned it to exit 0.
  - Worktree removed: `git worktree remove --force` then `git worktree prune`;
    `git worktree list` shows only the main checkout and the pre-existing
    `brichan-policy-benchmark`.
- Acceptance criterion 2, the main checkout: `make path-check` prints
  `repository paths valid: 113 entries, 75 references` and exits 0 under both
  `python3` (3.10.11) and `PYTHON=/opt/homebrew/bin/python3.14` (3.14.6);
  `tests.contract.test_repository_paths` runs 10 tests `OK` under both. An
  unclassified root file other than `.git` is pinned by
  `test_other_unclassified_root_files_are_still_reported`
  (`tests/contract/test_repository_paths.py:90`), which asserts
  `[".git.bak", "stray.txt"]` from a root also holding `.git`, an ignored
  `.env`, and an inventoried `AGENTS.md`.
- Acceptance criterion 3, mutation, run on a scratch detached worktree with the
  two changed files copied in, never on the main checkout. Baseline on that copy
  was `Ran 10 tests` / `OK`. Four mutations, each applied to a pristine copy:

  | Mutation | Result |
  | --- | --- |
  | delete `and path.name != GIT_METADATA` | `FAILED (failures=3)`: `test_a_worktree_git_file_is_not_an_unclassified_root_file`, `test_other_unclassified_root_files_are_still_reported`, `test_current_path_and_link_contracts_pass` |
  | `!= GIT_METADATA` becomes `not path.name.startswith(GIT_METADATA)` | `FAILED (failures=1)`: `test_other_unclassified_root_files_are_still_reported` |
  | `!= GIT_METADATA` becomes `path.name not in SKIPPED_PARTS` | `OK` — survives (L2) |
  | `if path.is_file()` becomes `if path.exists()` | `FAILED (failures=1)`: `test_current_path_and_link_contracts_pass` |

  The first mutation shows three failures where the report records two; both are
  right. The report ran the mutation in the main checkout, where `.git` is a
  directory and `test_current_path_and_link_contracts_pass` therefore stays
  green; I ran it in a worktree, where that test fails too. The regression is
  caught in both environments.
- File restored byte-for-byte. Because every mutation ran on a scratch copy, the
  main checkout was never modified. `shasum -a 256` of both files before and
  after all mutation work is identical, and `diff` of the two recordings is
  empty:
  `867e609eee1959f065b725accaff178766769fffd327d7a2b5351e29793c0255  scripts/check_repository_paths.py`
  and
  `1a032a7036082b7b149d7795963072fc35f94de93df89b845030c88ca82540de  tests/contract/test_repository_paths.py`.
  The script digest equals the value `report.md` records. `git status --short`
  after the exercise is unchanged from before it, and the second scratch
  worktree was removed and pruned.
- Acceptance criterion 4, `make check` on both interpreters.
  `PYTHONDONTWRITEBYTECODE=1 make -k check` (Python 3.10.11) and the same with
  `PYTHON=/opt/homebrew/bin/python3.14` (3.14.6) both exit 2 with identical
  results. `-k` was needed to observe every target, because `check` runs `test`
  first and a plain `make check` stops there. Green on both: `test-unit`
  1069 `OK`, `test-contract` 156 `OK`, the metrics unit module 10 `OK`,
  `techstack-eval` 56 `OK`, `metrics` `valid: 31 row(s)`, `receipts`
  `Validated 58 canonical handoff receipt(s).`, `memory-check`
  `project memory consistent: 10 indexed projects, 8 active documents`,
  `path-check` `repository paths valid: 113 entries, 75 references`,
  `readme-check` `README_PYPI.md is in sync with packaging/pypi-readme.md`,
  `phase5-preflight` all six checks `pass`, and `package-check`'s three import
  probes. Red on both: `test-integration`, one failure,
  `test_task_dossier_workflow.TaskDossierWorkflowIntegrationTest.test_repository_checkout_validates_clean`,
  and `dossiers`, `Invalid task dossiers: 20 issue(s)`.
- The red is confined to WFS-008's own pending artifacts. All 20 validator
  issues name this task: 15 on `index.md` — five `Artifact metadata`
  placeholders, four `Task identity` placeholders including the not-yet-written
  canonical `receipt.md`, and six `Artifact status` rows disagreeing with the
  artifacts — and five on `code-review.md`'s `Artifact metadata` placeholders.
  Filtering both logs for `handoffs/` lines that do not name WFS-008 returns
  nothing, on both interpreters. The integration failure's assertion message is
  that same validator output. Acceptance criterion 4 holds under its stated
  exception.
- `techstack-eval` run directly under 3.14, because its recipe freezes `python3`
  literally (`Makefile:39-40`) and so does not follow `PYTHON=`, as
  `techstacks/python/tests.md` requires:
  `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 -m unittest
  evals.techstack_context_v1.test_cases` reports `Ran 56 tests` / `OK`.
  `path-check` does follow `$(PYTHON)` (`Makefile:55-56`), so the 3.14 run
  exercised the changed script under 3.14.
- The manifest is untouched and the plan's reason for that holds:
  `config/repository-paths.json` carries
  `ignored_root_files: ['.DS_Store', '.env', 'CLAUDE.local.md']`, all
  machine-local ephemera, alongside 113 entries and 75 references, and 15
  inventoried root files.
- The repository already treated a regular-file `.git` as legitimate, so the fix
  aligns the outlier rather than inventing an exemption:
  `src/brichan/techstacks/filesystem.py:823` defines `GIT_MARKER_NAME = ".git"`
  and its comments at lines 939-994 distinguish "a directory `.git`" from "a
  regular worktree file"; `src/brichan/project.py:39` and `:49` probe
  `(candidate / ".git").exists()`, which covers both. A grep for `.git` across
  `scripts/` and `src/` found no remaining site that assumes a directory.
- L1 evidence: three isolated runs of
  `tests.contract.test_repository_paths.RepositoryPathContractTest.test_a_git_directory_is_not_an_unclassified_root_file`
  on a scratch copy — `OK` with the exemption deleted, `OK` with `is_file()`
  changed to `exists()`, `FAILED (failures=1)` with both removed together.
- L2 evidence: the `path.name not in SKIPPED_PARTS` mutation row above, `OK`
  across all 10 tests.
- L3 evidence: `scripts/check_repository_paths.py:18` and `:21`;
  `tests/contract/test_repository_paths.py:68`;
  `src/brichan/techstacks/filesystem.py:823`.
- L4 evidence:
  `projects/brida-workflow-simplification/handoffs/WFS-008/index.md` is the
  unedited template, its `Evidence` section still reading
  `<repository or source evidence for the claim>`, so it records no level
  determination for a reviewer to check.
- Techstack scope: Snapshot pointer
  `projects/brida-workflow-simplification/handoffs/WFS-008/snapshots/attempt-code-review-1-c3cc32be0f59dfdb67187278229992196929b2f94ba1d0beac67f6933082e1e5.snapshot.json`,
  digest `c3cc32be0f59dfdb67187278229992196929b2f94ba1d0beac67f6933082e1e5`.
  `bin/brichan techstacks verify --as-of 2026-09-26` returned `status: match`
  with `observed_snapshot_sha256` equal to that digest, run before any review
  work. All seven required selected rule files were read:
  `techstacks/README.md`, `techstacks/general.md`, `techstacks/policy/README.md`,
  `techstacks/policy/task-dossiers.md`, `techstacks/python/README.md`,
  `techstacks/python/scripts.md`, and `techstacks/python/tests.md`.

## Uncertainty

Three uncertainties remain, none of which changes the verdict.

1. Provider independence is not satisfied. `config/model-routing.json` routes
   `review` to `codex`/`gpt-5.6-sol` and `docs/policy/reviewer.md` prefers a
   different verified provider, but Codex is usage-limited, so this review ran
   Claude `claude-opus-5` at `high` effort. Model independence holds
   (`claude-opus-5-5` implemented) and level 0 requires only routine reviewer
   strength, which this meets or exceeds, so I judge the verdict sound.
2. Whether the manifest-versus-code choice counts as "multiple credible options
   exist" under the level 1 triggers is a judgment call. I concluded it does not
   and accepted level 0, and I recorded the reasoning in L4. Nothing material
   turns on it: the two levels share the artifact set, the reviewer strength,
   the ship gate, and, here, the mandatory review. The call belongs to the
   coordinator, who owns `index.md`.
3. Real-worktree coverage rests on the temporary-directory stand-in plus this
   session's live reproduction, not on a committed test that exercises a genuine
   worktree from a main checkout. I confirmed the stand-in matches the real
   artifact byte-shape, and the end-to-end test does cover the real case
   whenever the suite runs inside a worktree, so I judge the coverage adequate;
   a reader who wants the strongest possible guarantee would add a test that
   shells out to `git worktree add`.
