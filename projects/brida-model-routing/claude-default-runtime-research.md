# Research: Claude Code as the default runtime

Last verified: 2026-08-01

## Executive finding

The evidence supports making Claude Code the **checkout coordinator default for
the one-owner dogfood stage**, provided the change is treated as a reversible
routing experiment rather than proof that Claude is generally better than
Codex. Before that experiment includes Claude workers, remote-state actions
must have a durable human checkpoint because the current worker launcher uses
Claude `auto` permission mode.

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

An independent Codex worker reported that 71 targeted routing, runtime, Herdr
validation, CLI compatibility, and installed-dogfood tests passed on
2026-07-31. That run is identified by pane and session in `tasks.md`, but no
durable command log or receipt was retained, so this report does not treat the
exact count as independently reproducible evidence. A later coordinator-owned
validation is recorded separately in
`claude-default-runtime-verification.md`.

### 3. Local operational prerequisites are currently satisfied

The original research session recorded these read-only checks on 2026-07-31:

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

### 4. Coordinator safety is compatible; worker auto mode needs a checkpoint

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

`auto` is not equivalent to Brichan's no-remote-change contract. Anthropic
documents that it can execute without routine prompts and currently allows
pushes to any branch of the working repository, including the default branch.
Its configuration guide also says pull-request creation is allowed by default
and recommends explicit `permissions.ask` rules when a human checkpoint is
required:

- https://code.claude.com/docs/en/permission-modes
- https://code.claude.com/docs/en/auto-mode-config

Task-packet instructions still constrain worker intent, but a conversational
boundary is not a durable enforcement mechanism and may be lost after context
compaction. Before the dogfood experiment delegates implementation to a Claude
worker, configure explicit ask or deny rules for at least `git push` and
pull-request creation, then verify the effective permission configuration.
This is an existing Claude-worker gap, not a consequence of changing the
checkout coordinator default.

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

### Subscription quota can interrupt a long-lived coordinator

The original research records a Claude.ai Max subscription login. Anthropic
documents that Max usage is bounded, shared across Claude product surfaces, and
can stop requests until a reset or additional usage is available:
https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work

Quota exhaustion should be recorded separately from authentication and dispatch
failure. The experiment must not silently switch providers when it occurs.

### Consumer-account data settings need an explicit preflight

Anthropic documents that Free, Pro, and Max users can choose whether their data,
including Claude Code prompts and code, may be used to improve models:
https://code.claude.com/docs/en/data-usage

A coordinator can see broader project context than a bounded worker. Before
making Claude the default, the user should review the account's data-use setting
and confirm that the resulting exposure is acceptable. This research records no
account setting and does not make that privacy decision.

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

Before starting the experiment:

- verify Claude authentication and current model access;
- review the Max account's data-use setting;
- establish durable ask or deny rules for worker remote-state actions;
- confirm explicit `--runtime codex` rollback still launches successfully.

For the initial dogfood gate, complete one matched multi-step coordinator pair
per category—implementation, debugging, and policy-sensitive work—for three
runs per provider. Before calling the routing permanent, expand to at least
three matched pairs per category, or document why a different sample is
sufficient. Freeze the task packet and acceptance rubric before each pair, and
record:

- criterion-level acceptance results;
- reviewer findings and escaped defects;
- user interventions, approval pauses, retries, and recovery events;
- observed elapsed time;
- input/output tokens where directly observable;
- verified cost only when a billing source exists;
- authentication, quota, or dispatch failures;
- effective permission mode and any denied or attempted remote-state action.

Rollback to Codex immediately for an unauthorized remote-state action, a
permission or data-exposure regression, or an escaped policy-critical defect.
Also rollback if matched runs show repeated authentication, quota, or dispatch
failures, lower criterion-level acceptance, or materially more user
intervention without an offsetting quality benefit. Record the thresholds used
before interpreting the results rather than defining them after a preferred
outcome appears.

## Conclusion

Claude is technically ready for a **bounded checkout-default experiment**
because the coordinator adapter, native-delegation guard, authentication,
routing, and mixed-provider workflow are operational, and the change remains
reversible. The experiment should begin only after the privacy preflight and
worker remote-action checkpoint above; the current evidence does not establish
the full Claude-heavy workflow as safety-complete.

The strongest honest claim is readiness for a bounded default experiment—not
demonstrated superiority. Installed-project mode should remain Codex-only until
Claude receives its own hardened vertical slice.
