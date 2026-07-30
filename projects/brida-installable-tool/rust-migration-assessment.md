# Rust migration assessment

Date: 2026-07-30

## Outcome

Do not rewrite Brida in Rust for performance at the current one-owner dogfood
stage. Keep Python, add a benchmark gate, and first remove unnecessary eager
imports if command startup becomes noticeable.

Rust should be reconsidered only for a measured CPU-bound path or as a separate
distribution decision when shipping without Python becomes a product
requirement.

## Brida-specific evidence

The current package is approximately 3,486 lines of Python backed by 4,508
lines of Python tests. Its main paths discover a Git root, read small JSON and
Markdown files, hash eight managed resources, construct guarded provider
commands, and replace the process with Codex or Claude. The long-running work
is performed by external Codex, Claude, Herdr, and Git processes.

Observed locally on Python 3.10.11 with warm filesystem cache, 40 repetitions:

| Command/path | Median | p95 |
|---|---:|---:|
| Empty Python process | 16.48 ms | 17.32 ms |
| `brida --version` | 51.50 ms | 54.76 ms |
| `brida status`, uninitialized | 53.32 ms | 54.77 ms |
| `brida init --dry-run` | 53.49 ms | 56.66 ms |
| `brida doctor`, uninitialized | 51.97 ms | 54.98 ms |
| `brida status`, healthy | 53.19 ms | 55.94 ms |
| `brida doctor`, healthy | 53.53 ms | 56.02 ms |
| Worker launcher dry-run | 48.36 ms | 51.20 ms |
| Validate 35 canonical receipts | approximately 50 ms wall time | not measured |

Import isolation showed a median of 15.23 ms for importing only `brida`,
43.97 ms for `brida.cli.runtime`, and 43.16 ms for `brida.lifecycle`.
`PYTHONPROFILEIMPORTTIME=1` confirmed that even `--version` eagerly loads
lifecycle and orchestration modules. This leaves a likely low-risk Python
startup optimization before any language migration.

Recorded model-worker tasks take tens of seconds: the repository's model
benchmark observed 69- and 73-second active durations. Eliminating the entire
roughly 50 ms Brida wrapper cost would save about 0.07% of a 70-second task and
would not reduce model or Herdr latency.

The current release artifact is a 46 KiB `py3-none-any` wheel. A Rust extension
would replace that universal artifact with platform-specific compiled wheels;
PyO3 documents the OS, architecture, and Python-version build matrix, with
`abi3` reducing but not eliminating it. A full Rust binary avoids the Python
runtime but introduces target-specific release artifacts or requires users to
have a Rust toolchain for `cargo install`. Rust and Cargo are not currently
installed in the owner environment.

## Options

| Option | Expected performance benefit now | Cost and risk | Reversibility |
|---|---|---|---|
| Keep Python; optimize eager imports if needed | Potentially tens of milliseconds on trivial commands | Low; preserves package/API and universal wheel | High |
| Port one measured hotspot through PyO3 | Near zero with today's 50 ms receipt corpus; useful only if a CPU path grows substantially | Medium; Rust toolchain, FFI boundary, compiled-wheel matrix | High with a Python fallback |
| Full Rust rewrite | At most roughly 50 ms per current command before external execution | High; reimplement and re-verify lifecycle, routing, CLI compatibility, and security guards | Low |

## Decision gates

Reconsider selective Rust only when profiling shows all of the following:

1. A Brida-owned CPU path has p95 latency above 200 ms or consumes at least 10%
   of a user-visible workflow.
2. The path runs often enough for the saving to matter.
3. A release-mode Rust prototype demonstrates at least a 2x improvement on the
   same corpus while passing the existing behavioral and adversarial tests.
4. The packaging and maintenance cost is acceptable.

Reconsider a full binary when running without Python 3.10+ becomes an explicit
product requirement. Treat that as a distribution/compatibility decision, not
as proof of a performance bottleneck.

The smallest reversible experiment is the receipt validator, currently the
largest plausibly CPU-scaling module. Only prototype it behind the existing
entry point, retain the Python implementation as fallback, and test with a
large representative corpus after its Python path exceeds the gates above.

## Sources

- Local code and artifacts: `src/brida/`, `tests/`, `pyproject.toml`,
  `dist/brichan-0.6.0-py3-none-any.whl`, and `metrics/runs.jsonl`
- Python import profiling:
  https://docs.python.org/3/using/cmdline.html#cmdoption-X
- Cargo release profiles:
  https://doc.rust-lang.org/cargo/reference/profiles.html
- Rust target support:
  https://doc.rust-lang.org/rustc/platform-support.html
- Cargo binary installation:
  https://doc.rust-lang.org/book/ch14-04-installing-binaries.html
- PyO3 build and wheel distribution:
  https://pyo3.rs/main/building-and-distribution

## Uncertainty

The Rust speedup ceiling is inferred, not measured A/B, because no Rust
toolchain is installed. Cold-cache and large-corpus scaling were not measured.
Those gaps do not affect the current recommendation because the observed Brida
overhead is already immaterial relative to its external agent workflows.
