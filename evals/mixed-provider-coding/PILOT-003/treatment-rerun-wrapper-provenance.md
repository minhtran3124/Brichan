# Treatment rerun wrapper provenance

Captured by Brida immediately before dispatch, before any worker invoked the
tool. This is provenance for the removed disposable worktree, not a post-run
reconstruction.

- Wrapper SHA-256: `a00569a5e7a9c40037244e01d2042d05e788491de1f55c2a09d1a41a5454c493`
- Wrapper mode: `0700`
- Original target path: `/private/tmp/brida-pilot-003-treatment-rerun.m4VzQy/pilot-fixture/pilot-tool`
- Trigger: exact argument vector `pilot-tool read receipt`, one time only.
- Fault result: stderr marker `PILOT003_FAULT_ONCE`, exit `42`.

The wrapper delegated every later invocation to the target above. Its recorded
fault event is preserved byte-for-byte in `treatment-rerun-wrapper.log`.
