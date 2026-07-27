# Current state

- Status: implementation validated locally; changes remain uncommitted.
- Claude Code 2.1.220 is installed locally.
- Herdr 0.7.3 reports Claude integration v7 as current.
- Claude coordinator defaults to Opus 5 via `opus`; Fable 5 is available via
  `BRIDA_CLAUDE_COORDINATOR_MODEL=fable`.
- Herdr implementation workers use Sonnet 5 via `sonnet`.
- Runtime dispatch and dedicated launchers are implemented locally.
- Claude worker lifecycle smoke validation passed through Herdr.
- Two Claude workers ran concurrently through Herdr on bounded task packets;
  their reported facts were re-verified independently before acceptance.
- `claude auth status` now succeeds (`loggedIn: true`), so the Claude provider
  is authenticated; `model-catalog.md` still records it as unverified.
- Task packets longer than one line arrive in the Claude TUI as a paste block
  and require a following `herdr pane send-keys <pane> Enter` to submit.
- A Brida-owned worker pane `w1X:p9` was used and is ready for cleanup.
- The release branch currently has no committed Claude-support changes.

## Next actions

1. Review the final diff and decide whether to commit the implementation.
2. Consider a follow-up test for a real Claude coordinator prompt if API usage
   is acceptable.
