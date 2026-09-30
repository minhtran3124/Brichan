# Plan

Versioned execution plan. An accepted version is immutable; changes create a new version.

## Artifact metadata

- Task ID: `WFS-A-201`
- Task level: `0`
- Artifact: `plan`
- Artifact version: `2`
- Origin: `planner:2026-09-25-wfs-a-201-plan-v2`
- Owner: `planner`
- Phase state: `active`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `001cf011-1d97-4408-8c17-c4bc93269041`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Plan status

- Plan ID: `WFS-A-201-PLAN-001`
- Plan status: `draft`

## Claim or decision

Execute the rename in one edit and verify it in four bounded steps: verify
the implementation attempt's Techstack Snapshot before any work, apply the
single-line `def` rename of `design.md`, verify neutrality with the focused
module run and `git diff`/`git grep`, then run the full gate and the
dossier validator and report the two known worktree-only failures and the
pending coordinator/reviewer diagnostics as expected. The version 1
discovered-path escalation is resolved by the coordinator's option (b)
decision recorded below; no open question remains.

## Version 2 amendments

Version 1 escalated one discovered path outside the Techstack scope and
recorded plan acceptance as blocked on it. The coordinator decided on
2026-09-25 for option (b): the scope is unchanged and the reference
criterion is restated as "no reference to the old name remains outside
coordinator-owned project memory and immutable dossier provenance"
(`requirements.md` version 2, R3). The coordinator also corrected the
`request.md` origin to the bare `user-request` on its own side; nothing in
this plan depends on that. The edit, the selected name, the authorized
implementation path, and all verification steps are unchanged from
version 1, which is archived byte-frozen at
`projects/brida-workflow-simplification/handoffs/WFS-A-201/versions/v1/`.

## Discovered path outside the Techstack scope — resolved

**Prominent, per the packet's acceptance criteria.** The old test name has
exactly two tracked references
(`git grep -n test_prose_rejects_control_and_markup_characters`,
2026-09-25):

- `tests/unit/test_techstack_markdown.py:565` — the rename target, in
  scope.
- `projects/brida-workflow-simplification/tasks.md:29` — the S2-1 task-row
  description in coordinator-owned project memory, **not** in the
  Techstack scope paths
  (`projects/brida-workflow-simplification/handoffs/WFS-A-201`,
  `tests/unit/test_techstack_markdown.py`).

Coordinator resolution (2026-09-25, option (b)): `tasks.md` stays out of
scope, no Techstack re-resolution occurs, and the acceptance criterion is
restated as "no reference to the old name remains outside
coordinator-owned project memory and immutable dossier provenance". The
`tasks.md:29` row is coordinator-owned project memory and is therefore
permitted residue; the implementer must not edit it.

Untracked, gitignored dossier files (this dossier's `request.md` and these
planning artifacts) necessarily quote the old name as provenance; `git
grep` does not search them and they are not references to remove.

### Step 1 — Verify before work

Run the Techstack verify command from the implementation task packet (via
`bin/brichan` from the worktree root) and proceed only on `match`; reread
the six selected rule files named in the Snapshot. The planning attempt's
verification returned `match` on 2026-09-25 against sha256
`0270a2dc4984d6dfb37918fba7d0860c0273f97537a477c79991ad779dca142e`.

### Step 2 — The edit

Apply `design.md`: at `tests/unit/test_techstack_markdown.py:565`, rename
the `def` from `test_prose_rejects_control_and_markup_characters` to
`test_prose_rejects_pipe_and_category_c_characters`. One line; comment,
subtests, and helpers byte-identical. **One file.**

### Step 3 — Neutrality verification

```
git diff -- tests/unit/test_techstack_markdown.py
git grep -n test_prose_rejects_control_and_markup_characters
git grep -n test_prose_rejects_pipe_and_category_c_characters
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.unit.test_techstack_markdown -v
```

Expected: the diff is exactly one removed and one added `def` line; the
old-name grep hits only `projects/brida-workflow-simplification/tasks.md:29`,
the permitted coordinator-owned residue under the restated criterion; the
new-name grep hits only the renamed `def`; the module passes 47/47. Any
other diff line or failure: stop and escalate, per the remediation section.

### Step 4 — Gates and report

```
PYTHONDONTWRITEBYTECODE=1 make check
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_task_dossiers.py projects
```

Expected `make check` outcome in this detached worktree: the run stops in
`test-contract` with exactly the two known worktree-only failures in
`tests/contract/test_repository_paths.py` ("unclassified root files:
.git"), which are reported, never fixed. Because `make check` aborts
there, also run the remaining layers individually so the rest of the gate
is exercised: `make test-integration`, `make techstack-eval`, and the
non-test check targets (`make metrics receipts dossiers memory-check
path-check readme-check phase5-preflight package-check`). `make dossiers`
stays red until the coordinator's acceptance lifecycle completes the
coordinator- and reviewer-owned artifacts; the validator must report no
diagnostic for the five planner-owned WFS-A-201 artifacts, and remaining
diagnostics are listed in the report. That is lifecycle sequencing, not a
defect.

## Authorized implementation paths

- `tests/unit/test_techstack_markdown.py` — the one-line rename.

Everything else is excluded, including `src/`, `docs/`, configuration,
packaged resources, `projects/brida-workflow-simplification/tasks.md`
(kept out of scope by the coordinator's option (b) decision), the archived
`versions/v1/` copies (byte-frozen per DOSSIER-003), and this dossier's
coordinator- and reviewer-owned artifacts. No commit, branch, push, or
remote action; changes stay uncommitted.

## Remediation and escalation

- Any diff beyond the single `def` line: revert and re-apply; the edit is
  mechanical.
- Any test failure outside the two known worktree-only contract failures:
  diagnose before changing anything; a failure caused by the rename is
  impossible unless the name collided (it does not; `options.md`) — treat
  any such failure as pre-existing, report it, and escalate rather than
  fix.
- No recorded ambiguity remains; the version 1 `tasks.md` question is
  closed by the coordinator's option (b) decision.

## Acceptance criteria

The four criteria of `requirements.md` version 2 govern: name accuracy
(R1), a diff of exactly one `def` line (R2), recorded `git grep` evidence
with no reference to the old name outside coordinator-owned project memory
and immutable dossier provenance — concretely, only the permitted
`tasks.md:29` residue (R3) — and gate evidence with only the two known
worktree-only failures plus pending coordinator/reviewer dossier
diagnostics (R4).

## Evidence

- Baseline 2026-09-25 in this worktree: focused module 47/47;
  `PYTHONDONTWRITEBYTECODE=1 make check` fails with exactly the two known
  `tests/contract/test_repository_paths.py` failures; the dossier
  validator reports 65 diagnostics, all in the WFS-A-201 scaffold
  placeholders that this plan's artifacts replace.
- `git grep -n test_prose_rejects_control_and_markup_characters` baseline:
  exactly `tests/unit/test_techstack_markdown.py:565` and
  `projects/brida-workflow-simplification/tasks.md:29`.
- Techstack Snapshot pointer:
  `projects/brida-workflow-simplification/handoffs/WFS-A-201/snapshots/attempt-plan-1-0270a2dc4984d6dfb37918fba7d0860c0273f97537a477c79991ad779dca142e.snapshot.json`
  (sha256
  `0270a2dc4984d6dfb37918fba7d0860c0273f97537a477c79991ad779dca142e`),
  verify status `match` on 2026-09-25; acknowledged Context IDs `general`,
  `policy`, `policy-dossiers`, `python`, `python-tests`, `root`; scope
  paths as listed in the discovered-path section.
- Coordinator decision of 2026-09-25 selecting option (b) and restating
  the reference criterion (relayed in the version 2 coordinator packet);
  plan version 1 archived byte-frozen at
  `projects/brida-workflow-simplification/handoffs/WFS-A-201/versions/v1/`.

## Uncertainty

- No unresolved uncertainty remains: the version 1 discovered-path
  question is closed by the coordinator's option (b) decision, and the
  restated criterion is satisfied by the single-line rename as designed.
