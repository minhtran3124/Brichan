# Options

Credible implementation options with trade-offs. The selected decision is promoted into design.md or plan.md.

## Artifact metadata

- Task ID: `PYPI-003`
- Task level: `2`
- Artifact: `options`
- Artifact version: `5`
- Origin: `planner:2026-08-10-pypi-003-plan-v5`
- Owner: `planner`
- Phase state: `passed`
- Applicability: `required`
- Applicability rationale: `null`
- Authorship: `model`
- Authoring session: `6da0f1e7-0d9e-4881-8361-312f586c3487`
- Effective route: `plan`
- Effective model: `claude-fable-5`
- Effective effort: `high`
- Reviewing session: `null`
- Review verdict: `null`

## Claim or decision

Four decisions carry into the design: **D1-A** flip the shipped config and
regenerate; **D2-A** add focused shipped-mode and exact-URL regressions;
**D3-A** include the one-line removal of the completed gate from
`PRODUCT.md` section 10; **D4-A** record closure evidence in
`current-state.md` and the receipt, with exactly one coordinator-owned
receipt pointer in `references.md` per the handoff-receipt contract.

## Version 2 amendments

Version 1 selected leaving `PRODUCT.md` untouched and flagging its stale
line as an open coordinator decision. The coordinator resolved it on
2026-08-10: the removal is truth reconciliation for the same requested gate,
not a product-direction change, and is included. D3's selection is reversed
accordingly; D1, D2, and D4 are unchanged.

## Version 3 amendments

Plan-review version 2 finding M1 established that D4's exclusion of
`references.md` violated the mandatory receipt-discovery contract: every
operational receipt path must be added to the project's `references.md`, and
every existing receipt is discoverable that way. D4 is corrected — the
receipt pointer is required, coordinator-owned, and exactly one line. D1, D2,
and D3 are unchanged; the probe and negative-verification remediations (M2,
M3) are design and plan matters recorded there.

## Version 4 amendments

Per plan-review version 3: D4's pointer is fixed to the exact line
`projects/brida-installable-tool/handoffs/PYPI-003/receipt.md`, created in
lifecycle Phase A alongside the schema-v2 accepted receipt. The v3 manual
temporary-copy negative procedure — a design/plan construct, not an option
here — is removed as self-imposed; the permanent shipped-config test is the
automated revert gate. D1, D2, and D3 are unchanged.

## Version 5 amendments

Per plan-review version 4: no option selection changes. Phase B ownership
and order — reviewer-sole authorship of `code-review.md`, coordinator
verification and projection only, receipt finalized after memory and pane
cleanup, final full `make check` run last — are lifecycle corrections
recorded in `requirements.md` R7, `design.md` §5.2, and `plan.md`. D1–D4
stand as selected.

## D1 — How the hero image is restored

**D1-A — flip `public_repository` in the shipped config and regenerate
(selected).** This is the migration the pipeline was designed for: the module
docstring and the test
`test_pypi_source_hero_resolves_when_the_repository_goes_public` ("The
one-line flip must produce a reachable raw URL") both anticipate exactly this
change, and the base URLs are already correct. One config line changes; the
generator owns the output.

Rejected: **D1-B** hardcode the absolute raw URL in
`packaging/pypi-readme.md` — bypasses the render contract, leaves
`public_repository` falsely claiming private, and creates a second source of
truth for the URL; **D1-C** point the image at a commit-SHA raw URL — goes
stale on every release and contradicts the configured `main`-based
`asset_base_url` the tests already validate.

## D2 — How the shipped mode is protected

**D2-A — three focused offline regressions (selected).** The existing suite
cannot catch a silent revert: both mode test classes construct synthetic
configs, `test_shipped_config_loads` asserts only the source path, and the
sync tests (`--check`, `test_generated_description_is_in_sync_with_the_readme`)
pass in either mode so long as regeneration accompanied the revert. The new
pins — shipped config public with exact base URLs (unit), exact hero line in
the committed description (contract), exact raw URL in `PKG-INFO` (contract)
— make the public contract explicit at each layer that ships.

Rejected: **D2-B** rely on the existing sync tests — proven insufficient
above; **D2-C** a network reachability test — introduces an online, flaky
dependency into an offline suite and treats reachability as permanent, which
the task forbids; reachability is verified procedurally at execution time
(R1) instead.

## D3 — The residual `PRODUCT.md` line

**D3-A — include the one-line removal in this task (selected, by coordinator
decision 2026-08-10).** `PRODUCT.md:230` lists this gate as "Next, in order"
item 3 and becomes false the moment the gate closes — exactly the class of
durable contradiction MEMORY-001 existed to repair. The coordinator ruled the
deletion is truth reconciliation for the same requested gate, not a
product-direction change, which answers the scope objection: the authority
that bounded the task has widened it by one line. The edit is a single
deleted line with everything else byte-identical (`requirements.md` R6a).

Rejected: **D3-B** leave `PRODUCT.md` untouched and flag the line (version
1's selection) — defensible while the scope question was open, but once the
coordinator decided, deferring would knowingly ship a durable contradiction
and a second task for a one-line fix.

## D4 — Where the closure evidence lives

**D4-A — `current-state.md`, the receipt, and one `references.md` receipt
pointer (selected, corrected in v3, path fixed exactly in v4).** One line
under "Distribution and release" records the verified public setup with its
date; the receipt records the sanitized probe output and test evidence; and
the coordinator, in lifecycle Phase A, adds exactly one receipt-pointer line
naming exactly
`projects/brida-installable-tool/handoffs/PYPI-003/receipt.md` to
`references.md`, matching the convention of
the existing receipt pointers there. The pointer is not optional: the
handoff-receipt contract requires every operational receipt path to be added
to the project's `references.md` (plan-review v2 M1).

Rejected: **D4-B** omit `references.md` (versions 1–2's selection) — violated
the mandatory receipt-discovery contract and would leave the receipt absent
from progressive memory; **D4-C** a full verification-table row in
`references.md` — broader than the contract requires; the receipt carries the
evidence, the pointer makes it discoverable.

## Evidence

- `scripts/build_pypi_readme.py:13-17` and
  `tests/unit/test_build_pypi_readme.py:63-64,120-127` — the flip is the
  designed migration (D1).
- `tests/unit/test_build_pypi_readme.py:12-20,130-138` and
  `tests/contract/test_packaging_metadata.py:37-47` — synthetic configs and
  mode-agnostic sync tests; no shipped-mode pin exists (D2).
- `PRODUCT.md:230` — the completed gate as "Next, in order" item 3 — and the
  coordinator's recorded 2026-08-10 inclusion decision (D3).
- Task packet: enumerated in-scope files, minimal-surface directive, and the
  mandatory receipt at
  `projects/brida-installable-tool/handoffs/PYPI-003/receipt.md` (D3, D4).
- Plan-review v2 M1: the handoff-receipt instructions require every
  operational receipt path in `references.md`, and the existing PYPI-001,
  DOGFOOD-005/006, and MEMORY-001 receipt pointers there prove the
  convention (D4).

## Uncertainty

- D2-A pins strings, not reachability; a future URL breakage (repository made
  private again, asset moved) is caught only by the release process or by
  users, not by this suite.
