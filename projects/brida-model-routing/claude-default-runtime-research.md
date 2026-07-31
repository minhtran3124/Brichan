# Research: Claude Code as the default runtime

Last verified: 2026-07-31

## Executive finding

The evidence supports making Claude Code the **checkout coordinator default for
the one-owner dogfood stage**, provided the change is treated as a reversible
routing experiment rather than proof that Claude is generally better than
Codex.

The evidence does **not** support:

- changing installed-project mode, which is implemented and tested as Codex-only;
- declaring a general provider winner;
- changing the Codex review route;
- making cost, speed, or token-efficiency claims from the current data.

This scope matters. In checkout mode, the default is a settings choice with an
explicit Codex override. In installed-project mode, runtime support is an
architecture and security boundary.

## Why a Claude checkout default is supportable

### 1. It matches the current workflow topology

The active routing manifest already uses Claude for planning, implementation,
and scanning, while Codex provides independent review. Claude is therefore the
main-work provider even though bare checkout startup still selects Codex.

A Claude coordinator plus Codex reviewer gives the material review path
cross-provider independence. A Codex coordinator plus Codex reviewer preserves
fresh-session independence but shares a provider family and may preserve a
coordinator-shaped blind spot. This is an inference from the routing topology,
not a measured quality result.

Evidence:

- `config/model-routing.json`
- `projects/brida-model-routing/decisions.md`
- `docs/policy/reviewer.md`

### 2. The checkout implementation is already dual-runtime

Checkout dispatch loads `settings.default_runtime`; users can still override it
with `--runtime` or `BRICHAN_RUNTIME`. Both coordinator records are already in
the manifest, so changing the checkout default does not require a new adapter or
a new configuration contract.

The Claude adapter resolves the configured model and effort, disables native
Claude delegation, rejects permission bypasses, and preserves the Herdr-only
worker lifecycle. Existing tests cover Claude dispatch, malformed settings,
model and effort resolution, native-agent rejection, permission-bypass
rejection, and explicit runtime overrides.

Evidence:

- `src/brichan/cli/runtime.py:34-53,213-240`
- `src/brichan/cli/claude.py:18-53`
- `src/brichan/cli/provider_commands.py:215-254,322-346`
- `tests/unit/test_model_routing.py`
- `tests/integration/test_cli_compatibility.py`
- `tests/integration/test_worker_routing_cli.py`

An independent Codex worker ran 71 targeted routing, runtime, Herdr validation,
CLI compatibility, and installed-dogfood tests on 2026-07-31; all passed.

### 3. Local operational prerequisites are currently satisfied

Read-only checks on 2026-07-31 verified:

- Claude Code `2.1.220` is installed.
- Claude authentication succeeds outside the restricted sandbox using a
  Claude.ai Max account.
- Herdr `0.7.3` is healthy and its Claude integration is current at v7.
- The configured canonical Claude model IDs completed live probes on
  2026-07-29.

No account identifiers are stored in this report.

Authentication can lapse, so `claude auth status` remains a startup
precondition for a workflow that depends on Claude. Anthropic documents both
the supported authentication methods and the effect of expired credentials on
unattended sessions:
https://code.claude.com/docs/en/iam

### 4. The safety posture is compatible with Brichan

Brichan rejects Claude native-agent options and permission bypasses before
launch. It also prevents workers from overriding tool lists or settings through
the legacy command path.

Anthropic documents read-only defaults, approval for sensitive operations,
working-directory write boundaries, network approval, and configurable
permission rules:
https://code.claude.com/docs/en/security

For workers, Brichan adds Claude `auto` permission mode while still rejecting
`bypassPermissions`. For the coordinator, Brichan does not inject `auto`; the
user's normal Claude permission configuration continues to apply. This
distinction avoids using worker automation policy as an unsupported argument
for coordinator safety.

### 5. Existing evaluations show readiness, though not superiority

`BENCHMARK-002` gave Codex Terra and Claude Sonnet the same seeded
implementation/debugging fixture. Both passed implementation behavior, the
seeded fix, focused tests, and scope checks on the first pass.

Other mixed-provider pilots show Claude successfully performing planning and
independent review within the coordinator-mediated handoff contract. A real
tool-failure treatment also showed a Claude worker recovering after one
task-local failure, with independent Codex review returning `PASS`.

These observations establish that Claude is operationally usable in Brichan's
workflow. They do not establish that Claude is globally better.

Evidence:

- `evals/mixed-provider-coding/BENCHMARK-002/results.md`
- `projects/brida-claude-code-support/current-state.md`
- `projects/brida-claude-code-support/references.md`

### 6. The change is narrow and reversible

For a source checkout, the default is controlled by
`config/model-routing.json`. Explicit `--runtime codex` and
`BRICHAN_RUNTIME=codex` overrides remain available.

Installed-project dispatch separately hard-codes and validates Codex-only
support. Changing the checkout manifest therefore does not silently enable
Claude in initialized external repositories.

Evidence:

- `src/brichan/cli/runtime.py:157-177,224-240`
- `src/brichan/resources/dogfood_v1/config/model-routing.json`
- `README.md:90-160`

## Counterevidence and unresolved gaps

### No coordinator A/B exists

The two provider benchmarks evaluate worker tasks, not the long-lived Chief of
Staff role. There is no matched comparison for:

- intent preservation across several handoffs;
- acceptance-criteria quality;
- durable-memory accuracy;
- intervention and blocker rates;
- context use, latency, or cost at the coordinator level.

### One strict review sample favored Codex

In `BENCHMARK-001`, Codex Terra scored 12/12 and caught a missing literal
lifecycle requirement; Claude Sonnet scored 10/12 and incorrectly returned
`PASS`. This is meaningful directional evidence for keeping strict policy
review on Codex. It is not direct evidence against a Claude coordinator because
the proposed routing preserves the Codex review role.

### Current telemetry is insufficient

The benchmark records lack reliable per-task input tokens, output tokens, cost,
and independent elapsed time. The metrics schema also does not record
coordinator runtime or model, so current ledger rows cannot support a provider
comparison.

Anthropic's opt-in OpenTelemetry support exposes session counts, request
duration, input/output tokens, tool activity, and approximate cost:
https://code.claude.com/docs/en/monitoring-usage

Approximate telemetry cost is not billing evidence. Brichan should continue to
record cost as unavailable unless a verified billing source is attached.
Enabling telemetry also requires an explicit privacy and data-handling choice;
this research does not authorize that configuration change.

### Authentication is a runtime dependency

The local Claude account is authenticated now, but an expired login can stop
unattended progress. A default change should fail clearly or fall back only by
explicit user choice; silent provider fallback would violate deliberate
routing.

### Claude worker dispatch has a known TUI edge case

Long packets can arrive as an unsubmitted paste block and require an explicit
Enter. The Herdr command reference already defines detection and recovery. This
affects Claude workers, not bare coordinator startup, but it remains relevant to
the Claude-heavy workflow.

### Installed-project parity does not exist

Installed-project mode has a Codex-specific launcher, packaged policy injection,
scope restrictions, doctor behavior, and integration tests. A Claude installed
default would require a separate product change and independent security review.

## Recommended decision

Adopt this narrowly worded decision:

> During one-owner checkout dogfood, Claude Code is the default coordinator
> runtime. Codex remains available by explicit override and remains the default
> and only supported installed-project runtime. Codex remains the independent
> review route. This is a reversible workflow hypothesis, not a general provider
> ranking.

Before calling the routing permanent, complete at least three matched,
multi-step coordinator runs per provider across implementation, debugging, and
policy-sensitive work. Record:

- criterion-level acceptance results;
- reviewer findings and escaped defects;
- user interventions, approval pauses, retries, and recovery events;
- observed elapsed time;
- input/output tokens where directly observable;
- verified cost only when a billing source exists;
- authentication or dispatch failures.

Rollback to Codex as the checkout default if Claude causes a material safety
regression, repeated authentication/dispatch failures, lower acceptance
performance, or materially more user intervention without an offsetting quality
benefit.

## Conclusion

Claude is ready to be the **checkout dogfood default** because the adapter,
guardrails, Herdr integration, authentication, routing, and mixed-provider
workflow are already operational, and because the change improves
cross-provider review topology while remaining reversible.

The strongest honest claim is readiness for a bounded default experiment—not
demonstrated superiority. Installed-project mode should remain Codex-only until
Claude receives its own hardened vertical slice.
