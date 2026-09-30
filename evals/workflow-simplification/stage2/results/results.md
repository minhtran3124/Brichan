# Stage 2 results: current lifecycle (A) vs simplified lifecycle (B)

Date: 2026-09-25. Protocol: `../../protocol.md` stage 2, reduced by the user
to three tasks with every reviewer on Claude (Codex was blocked by a pending
update dialog). Base commit `6fe3977`; one detached worktree per task and arm.
Both arms used `claude-opus-5-5` at `medium` effort to implement (the stage 1
winner), so the comparison isolates the lifecycle.

| Task | Level | Objective |
|---|---|---|
| S2-1 | 0 | Rename a unit test whose name no longer matches its assertions |
| S2-3 | 1 | `diagnostic_detail` refuses keyword arguments its code does not take |
| S2-4 | 1 | Worker-ledger guidance in the packaged `herdr-orchestration` skill (contract path) |

- **Arm A (current):** planner (`claude-fable-5` high) → plan review
  (`claude-opus-5` high) → implementer → code review (`claude-opus-5` high),
  with the full eleven-artifact dossier.
- **Arm B (simplified):** one implementer that plans in its report, then code
  review only for Level 1 or a contract path. Arm B keeps only the receipt,
  the worker report, and the review.
- **Blind escape review:** one `claude-fable-5` high session reviewed both
  final diffs of every task as X/Y, with the mapping randomized per task
  (`escape-mapping.json`).

## Cost

Active time is the CLI's per-turn "worked for" value, summed over each arm's
sessions. Waits caused by the usage window are excluded. "Context tokens" is
the CLI footer at session end, summed. It is not verified billed usage;
cost is unavailable.

| Task | Arm | Sessions | Plan-review rounds | Active worker time | Context tokens (sum) | Dossier/report lines |
|---|---|---:|---:|---:|---:|---:|
| S2-1 | A | 6 | 2 (1 CHANGES REQUIRED) | 68m 27s | 804,460 | 3,044 |
| S2-1 | B | 1 | 0 | 4m 06s | 71,610 | 156 |
| S2-3 | A | 8 | 3 (2 CHANGES REQUIRED) | 134m 12s | 1,319,306 | 4,361 |
| S2-3 | B | 2 | 0 | 25m 30s | 269,500 | 679 |
| S2-4 | A | 10 | 4 (3 CHANGES REQUIRED) | 145m 15s | 1,736,935 | 5,294 |
| S2-4 | B | 2 | 0 | 26m 22s | 291,564 | 508 |
| **Total** | **A** | **24** | 9 | **347m 54s** | **3,860,701** | **12,699** |
| **Total** | **B** | **5** | 0 | **55m 58s** | **632,674** | **1,343** |

Arm A used about 5× the sessions, 6× the active worker time and context
tokens, and 9× the artifact lines. Arm A S2-4 converged on the last round
allowed by the four-round cap (`projects/brida-workflow-simplification/decisions.md`).
The coordinator also spent more effort on arm A: scaffolding, request,
follow-up questions v1/v2, archiving review versions, closing
index/pr-desc/receipt, and two sets of phase-state repairs at close.

Coordinator interventions: arm A 2 (S2-1 criterion answer, plus one ratified
gate recorded in `client-follow-up-questions.md` v2 for all three dossiers);
arm B 1 (S2-3 scope decision, option A, `resolver.py`). No user
interventions in either arm.

## Quality

| Measure | Arm A | Arm B |
|---|---|---|
| Acceptance criteria met (every task) | yes | yes |
| Worktree gate (expected-red items only) | yes | yes |
| Independent code review verdict | PASS ×3 | PASS ×2 (S2-1 had no review: Level 0, no contract path) |
| Blind escape review score (3 tasks × 15) | 42 | 42 |
| Escaped medium+ defects | 1 Medium (S2-4) | 1 Medium (S2-3) |
| Escaped high/critical defects | 0 | 0 |

Escape review per task (`escape-review-escape-review.md`):

- **S2-1:** tie, 15/15 each; no defects. Both arms made the same one-line
  rename.
- **S2-3:** A 15, B 12. B's Medium: no committed test proves byte identity for
  valid calls. B's implementer and reviewer each proved it with a scratch run
  (1,310,954 calls, 0 mismatches), and B's own review listed the missing test
  as a test gap. B's Low: no test covers falsy refusal values (`errno_value=0`,
  `line=0`). Arm A's second plan review caught exactly that before
  implementation.
- **S2-4:** B 15, A 12. A's Medium: no test ties the new guidance to the
  shipped CLI, so renaming `--task` in the launcher leaves the contract suite
  green in A and red in B. A's Low: the launch example block omits `--task`.
  None of arm A's four plan reviews or its code review raised either point.
  Arm B's implementer added the CLI-coupled test and placed the new section
  correctly on its first attempt. Arm A's plan v1 had misplaced it (plan
  review v1 Medium).

What the reviews in each lifecycle actually caught:

- Both lifecycles found, independently, that the TECHSTACK-002 `L4` premise
  was wrong: `resolver._add_located` passes `errno_value` in production. Arm B
  found it during implementation and escalated; arm A found it during
  planning.
- Most arm A plan-review findings concerned criteria wording, lists of
  expected worktree failures, make-target equivalence, and 3.10/3.14 gate
  details. Arm B workers handled the same issues by reporting them.
- Arm A's reviews found one real test-quality issue (the S2-3 class (b)
  refusal test could not fail, and falsy values were untested) that arm B
  shipped as a Low.

## Verdict against the protocol's pass criteria

1. Arm B passes the gate and every acceptance criterion on every task:
   **met.**
2. Arm B has no more escaped medium+ defects than arm A (1 vs 1) and no
   escaped high or critical defects: **met.**
3. Arm B uses fewer workers and fewer dossier lines per task: **met** (5 vs
   24 sessions; 1,343 vs 12,699 lines).

Stage 2 supports the proposed simplification for Level 0/1. It also points
to one targeted addition that keeps arm A's one real advantage cheaply:
require the arm B review to classify a missing regression test for a behavior
change as a defect rather than a test gap.

## Limits

- Three tasks, one run per arm, all on this repository.
- Every reviewer was Claude; the protocol asked for a different provider.
- The escape reviewer saw only final diffs, not each arm's evidence files.
  Both Mediums are "missing test or evidence in the diff", not wrong behavior.
- Arm A's cost includes review churn partly caused by coordinator packet
  wording (the S2-1 criterion, the worktree gate), which a mature packet
  template would reduce. Arm B was exposed to the same wording and absorbed
  it by reporting.
- Session time excludes coordinator effort, which was also much higher in
  arm A.
