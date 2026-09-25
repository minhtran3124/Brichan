# Stage 1 results: `claude-opus-5` vs `claude-opus-5-5`

Date: 2026-09-25. Protocol: `../../protocol.md` stage 1. Fixtures at
`40f46d8`; hidden tests now under each task's `hidden/`.

## Setup

- Two workers launched through Herdr from the same commit in separate
  detached worktrees, same packet, route `implement`, effort `medium`, model
  the only difference. Each worker planned its own work (no plan worker, no
  plan review).
- Blind review: one fresh session saw the two submissions as X and Y with no
  model names. The protocol calls for a different provider. Codex could not
  start: an update dialog was pending (installed 0.155.0, available 0.157.0),
  and it was not answered on the user's behalf. The reviewer was therefore
  `claude-fable-5` at `high` effort: same provider, but a different model
  from both arms.
- Mapping (revealed after scoring): X = `claude-opus-5-5`, Y = `claude-opus-5`.

## Results

| Measure | `claude-opus-5` (Y) | `claude-opus-5-5` (X) |
|---|---|---|
| Hidden tests (15 + 12 + 9) | 36/36 | 36/36 |
| Visible and own tests | all pass | all pass |
| Blind review score (3 tasks × 3 criteria × 5) | 41/45 | **45/45** |
| Functional defects found by review | 1 High (T1: `RecursionError` escapes on a deeply nested JSON line) | 0 |
| Other review findings | T3 Medium (docstring misstates where the suffix check runs), T3 Low, T1 Low | T2 Low (unreachable helper contract) |
| Worker wall time shown by the CLI | 6m 30s | 2m 47s |
| Session tokens shown in the CLI footer | 86,057 | 77,823 |
| Scope | only the three task directories | only the three task directories |
| User interventions | 0 | 0 |

The CLI footer token counts are display values and have not been verified
as billed usage. Cost is unavailable.

## Observations

- The hidden tests hit the ceiling again: both models passed every hidden
  case. Only the adversarial blind review separated the two arms.
- Both models found and fixed the same two unreported parser defects in T2
  (`$` accepting a trailing newline, and non-ASCII `\d`). Both flagged these
  as outside the reported symptom.
- Both models spotted the T3 trailing-slash ambiguity and resolved it in
  opposite directions. Each documented and tested its choice. `opus-5-5`
  chose the stricter reading, which preserves the invariant.
- `opus-5` ran `make check` without being asked and hit a pre-existing
  worktree-only failure: `test_repository_paths` sees `.git` as a file in a
  worktree. Recorded as a follow-up; not part of this benchmark.

## Verdict

Under the protocol rule, `claude-opus-5-5` is preferred. It was no worse on
the hidden tests, better on review findings (0 functional defects vs 1 High),
and faster in wall time.

Limits: three tasks, one sample per arm, and one reviewer from the same
provider. This is directional evidence, strong enough to use `opus-5-5` as the
`implement` model for stage 2. It is not proof of a general advantage.
