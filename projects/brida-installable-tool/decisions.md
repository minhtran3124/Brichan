# Decision log

## 2026-08-26 — Design-parity tests read committed fixtures, not the dossier

- Status: accepted for `TECHSTACK-001` final remediation.
- Context: Final whole-feature review finding `H1-f-1`:
  `tests/contract/test_techstack_policy_contract.py` reads the gitignored
  dossier file `handoffs/TECHSTACK-001/design.md` unguarded, so `make check`
  exits 2 on every dossier-free clone and in CI; the reviewer reproduced this
  in a real clone. `M1-f-1`: two `tests/unit/test_cli_render.py` assertions
  guard the same read with `skipTest`, so on those clones the only
  byte-for-byte link between the design's §9 registry, §14 frozen block, and
  §16 cross-product and `AGENT_SKILL_EXPORT_DETAILS` silently disappears.
- Decision: Copy each frozen design block those three assertions compare
  against into a committed fixture under `tests/fixtures/`, beside
  `doctor_v2_text.json`, and point the assertions at the fixtures. The
  assertions then run everywhere. A contract test freezes each fixture's
  SHA-256 so the fixture cannot drift from the design silently, and the
  dossier-present path additionally asserts fixture bytes equal the design
  block, so the design stays the authority wherever it is on disk. Rejected:
  a `skipTest` guard alone (turns a gate assertion into a skip on CI, the
  exact `M1-f-1` defect), and tracking the dossier in git (changes what the
  repository publishes). The new fixture files are a coordinator amendment to
  Design §11's inventory.
- Rationale: A parity assertion that only runs on the author's machine is not
  a gate; a committed fixture keeps it a gate and keeps the design the source.
- Owner: User.
- Evidence: `handoffs/TECHSTACK-001/code-review.md` version 6, `H1-f-1` and
  `M1-f-1`, including the reviewer's clone reproduction.

## 2026-08-26 — Exempt the immutable version archive from the home-path scan

- Status: accepted for `TECHSTACK-001` step 10.
- Context: `tests/contract/test_repository_contract.py`
  `test_durable_artifacts_do_not_embed_home_paths` scans every file under
  `projects/` for two path-prefix substrings. The immutable archive
  `handoffs/TECHSTACK-001/versions/v3/design.md:258` contains the prose
  fragment `absolute`, `home`, `backslash`, ... joined by slashes, a list of rejected
  path kinds, and has failed the test since 2026-08-24. That failure halts
  `make test` before `techstack-eval` and every later `check` target, so the
  gate CLAUDE.md requires before any change is called done cannot pass.
- Decision: Add `projects/*/handoffs/*/versions/` to the test's exemption in
  the same explicit, narrow form as the existing TDW-009 capture-snapshot
  exemption, with a comment stating why: archived plan versions are
  byte-frozen review evidence, not authored durable text. Nothing else is
  exempted; live handoff artifacts, project memory, `evals`, and `metrics`
  remain scanned. Rejected: editing the archive (breaks the immutability every
  review has relied on), loosening the substring match (weakens a real guard
  for no gain), and a permanently qualified gate (violates the `make check`
  contract).
- Rationale: The archive is the one place where prose that merely mentions a
  path kind can never be corrected, so the scan's purpose — catching embedded
  personal paths in artifacts that are still being written — does not apply to
  it.
- Owner: User.
- Evidence: `impl-5-code-review-v2.md` and `impl-6-code-review-v2.md` closing
  judgments; `tests/contract/test_repository_contract.py:371-394`.

## 2026-08-26 — Delete the unspecified stale-snapshot digest branch

- Status: accepted for `TECHSTACK-001` packet 6 remediation.
- Context: `impl-6-code-review.md` finding `M2-i6-2`: the eval oracle at
  `evals/techstack_context_v1/test_cases.py:767-768` returns `stale_snapshot`
  when the acknowledged digest equals the superseded initial Snapshot. Design
  §16 states no such rule, the frozen corpus distinguishes `stale-snapshot` from
  `handoff-drift` by verification status, and a line trace shows the branch
  executes zero times over all 12 cases. Derived outcome 6 claimed both cases
  pass through it, which is false.
- Decision: Delete the branch; `handoff_drift` becomes the only outcome of a
  non-matching acknowledged digest. The alternative — keeping the branch and
  adding a thirteenth case to exercise it — is rejected because the 12-case
  corpus is frozen by Design §16 and any change requires a plan revision.
- Rationale: An oracle must encode only the policy the design states; a branch
  no authority specifies and no case reaches is a divergence waiting to be
  discovered by a future case.
- Owner: User.
- Evidence: `impl-6-code-review.md` `M2-i6-2` and §`Oracle precedence — traced,
  not read`; `design.md:2387-2389`.

## 2026-08-26 — Packet 6 derived outcomes ruled after the fact

- Status: accepted for `TECHSTACK-001` packet 6 review.
- Context: The packet-6 implementer recorded eight derived outcomes instead of
  escalating two that touch frozen literals: the 12-case `cases.json` was
  extracted from Design §16 because §15's only JSON block is the superseded
  version-5 corpus marked "MUST NOT implement", and the synthesized approval
  target is `STALE_RULE/general/null` per §16 although §10 (`design.md:1153`)
  still says `STALE_RULE/stale/null`. The packet's escalation rule covers
  exactly this case.
- Decision: Both readings are upheld. §16 is the sole cases/schema/oracle
  authority by §15's own supersession sentence and by §16's precedence clause,
  the extracted corpus is byte-identical to the §16 block (8,629 bytes,
  `250759f6…86ba7`), and `general` is the only Context ID that makes
  `discovered-exception-approved-reread` resolve applicable. The `python3`
  literal in the `techstack-eval` recipe is frozen by Design §10 and stays; it
  means `make check PYTHON=…` does not carry the interpreter into the eval, so
  the eval is run directly under both interpreters as its own gate. The stale
  `STALE_RULE/stale/null` prose at `design.md:1153` is a plan-text defect of the
  same class as `L2-v6-1`, to be corrected in the next plan revision, not by
  any code change. Recording instead of escalating is a process finding for the
  packet-6 reviewer to weigh, not grounds to reopen the outcomes.
- Owner: User.
- Evidence: `impl-6-evidence.md` §`Derived outcomes` 1, 2, 4; `design.md:1153`,
  `:1823`, `:2361-2376`; coordinator re-run of the eval on 3.10.11 and 3.14.6
  (`Ran 56 ... OK` both) and `make path-check` (111 entries, 73 references).

## 2026-08-26 — Durable artifacts quote the home-path substrings bare

- Status: accepted for `TECHSTACK-001` and every later task.
- Context: `tests/contract/test_repository_contract.py`
  `test_durable_artifacts_do_not_embed_home_paths` scans every file under
  `projects/`, `evals`, and `metrics` for the two scanned substrings, each of
  which carries a trailing slash. Three files written after the first packet-5
  review — `projects/brida-installable-tool/current-state.md`,
  `handoffs/TECHSTACK-001/impl-5-code-review.md`, and
  `handoffs/TECHSTACK-001/impl-5-fix-task-packet.md` — quoted them verbatim
  while describing finding `M1-i5-1` and became offenders themselves.
- Decision: The coordinator dropped the trailing slash from each quoted
  substring in exactly those three files on 2026-08-26 and changed no other
  byte; the second packet-5 review confirmed the edit against the substring
  pattern. From now on any durable artifact that discusses this test or the
  finding quotes the prefixes bare, as `/Users` and `/home`, never with the
  trailing slash. The pre-existing false positive on the immutable archive
  `handoffs/TECHSTACK-001/versions/v3/design.md:258` is unaffected and still
  awaits a separate ruling.
- Rationale: Otherwise every review, packet, or memory note that names the
  finding re-breaks the gate, and the offender list stops being a signal.
- Owner: User.
- Evidence: `impl-5-evidence.md` §`FIX` offender-list escalation;
  `impl-5-code-review-v2.md` §`The coordinator slash-drop` and `L6-i5v2-6`.

## 2026-08-26 — Packet 6 owns the eval path classification

- Status: accepted for `TECHSTACK-001` implementation.
- Context: Plan step 7 requires `config/repository-paths.json` to classify the
  new policy, source, eval, and reference paths. Packet 5 could not classify
  `evals/techstack_context_v1/` because the checker rejects entries for paths
  that do not yet exist, and the package is step 9's add; its deferral named
  step 9 as owner although `impl-6-task-packet.md` did not authorize writing
  that file (`impl-5-code-review.md` finding `M3-i5-3`).
- Decision: Widen packet 6's authorized writes to `config/repository-paths.json`
  and `tests/contract/test_repository_paths.py`, scoped to thirteen eval
  entries using the existing `regression-test`/`canonical` and
  `historical-evidence`/`frozen` vocabulary, with a contract assertion that
  fails if any entry is removed. The alternative — recording an explicit v1
  deferral — was rejected because `path-check` validates only declared entries,
  so an uninventoried eval package would pass step 10 silently.
- Rationale: Keeps the step-7 acceptance bullet satisfiable by a named packet
  instead of by none, and closes the exact failure scenario the reviewer
  described.
- Owner: User.
- Evidence: User direction on 2026-08-26; `impl-5-code-review.md` `M3-i5-3`;
  `impl-6-task-packet.md` `Coordinator amendment`.

## 2026-08-25 — Step 7's immutable-manifest growth may update three step-6 tests

- Status: accepted.
- Context: Plan step 7 adds `policy/techstacks.md` and the packaged
  `references/handoff-receipt.md` to `IMMUTABLE_PATHS`, which moves the
  managed footprint from 15 to 17 files and the managed skill tree from
  three to four files. Fourteen assertions in three step-6 test files that
  packet 5's packet placed out of scope froze the old counts; the
  implementer escalated instead of editing them. Design §11's whole-feature
  modify list names all three files, and the frozen 27-output doctor text
  fixture does not encode the policy list.
- Decision: The packet-5 worker may make the mechanical edits — 15 → 17 in
  `test_cli_render`, one extra element in `test_cli_compatibility`'s frozen
  export list, and the `AgentSkillExportReportTest` fixtures rebuilt
  against a four-file managed tree — without weakening, skipping, or
  removing any assertion, and must stop if any existing assertion's
  expected row would change. The fixture file is untouched.
- Owner: Coordinator, within the user's implementation authorization.
- Evidence: `handoffs/TECHSTACK-001/impl-5-evidence.md` §`Escalation`.

## 2026-08-25 — Descent-suppressed section conditions are not applicable under §16

- Status: accepted; upheld by the fifth packet-4 review's independent ruling
  (2026-08-25), which found it holds under both readings of §16's scope
  and corrected the count to eight pairs with a spread of up to eleven
  registry places.
- Context: `FIX4` routed every abort in `_scan_skill_directory`'s loop
  through one helper and recorded seven "descent-suppressed" pairs: a
  section row (`UNSUPPORTED_SAFE_OPEN`/`RESOURCE_LIMIT`) raised by
  `open_directory` on a child directory that sorts after an abort is never
  observed, because `scan.bounded` refuses the open; worst case row 7 is
  reported as row 8. Observing it would require opening a directory after
  an abort, which contradicts the disclosed cost bound and the shipped
  no-descent test.
- Decision: Opening a child directory is descent. Design §16 (version 10)
  states that a condition whose evidence lies only inside a directory the
  abort prevented descending is not applicable to that report, so the
  behaviour is conformant and no change is made. Recorded so a later
  reader does not mistake it for an unfixed route.
- Owner: Coordinator, within the user's implementation authorization.
- Evidence: `handoffs/TECHSTACK-001/impl-4-evidence.md` §`FIX4`;
  `handoffs/TECHSTACK-001/design.md` version 10 `:2062-2069`.

## 2026-08-25 — Clarification: only the entry counter stops at cap+1

- Status: accepted (coordinator clarification of the 2026-08-25 overflow
  ruling; no design change).
- Context: Third packet-4 review finding `L1-i4v3-2`. The ruling said
  bounded enumeration finishes the aborting level "each counter stopping at
  cap+1". The implementation caps the entry counter but records every
  directory observed at an already-listed level, and the reviewer proved
  that capping the directory set would silently move a reported row
  (`SKILL_ENTRY_LIMIT` → `SKILL_DIRECTORY_LIMIT`) for observations Design
  §16 (version 10) makes applicable.
- Decision: The clause applies to the entry counter only. The directory set
  is uncapped at the aborting level; the docstring says so and a test pins
  the row. The cost of finishing a level — one metadata call per name, no
  content read, no descent — is disclosed rather than claimed bounded in
  count.
- Owner: Coordinator, within the user's implementation authorization.
- Evidence: `handoffs/TECHSTACK-001/impl-4-code-review-v3.md` §`L1-i4v3-2`,
  §`L2-i4v3-3`.

## 2026-08-25 — Accept TECHSTACK-PLAN-001 version 10

- Status: accepted.
- Context: Version 10 is the user's one-sentence §16 amendment resolving
  `M1-i4v2-1` (precedence under bounded enumeration). A scoped independent
  review (Claude `claude-opus-5` high) returned `PASS`: the sentence is exact,
  stated once, decidable (the 65/65 fixture yields `SKILL_DIRECTORY_LIMIT`
  for `d…/e…` and `SKILL_ENTRY_LIMIT` for `z…/a…`, executed against the live
  section), already satisfied by `_scan_skill_directory` with no new bound,
  and every registry and fenced block is byte-identical to version 9.
- Decision: Accept version 10 as the plan of record, superseding version 9
  for step 6 only. The two wording Lows (`L1-v10-2`, `L2-v10-3`) are carried
  as residuals; the implementation packet takes the review's executed fixture
  descriptions as authority for those fixtures. `M1-v10-1` is fixed in the
  implementation packet as an in-design gap. Acceptance authorizes no
  commit, push, pull request, or release.
- Owner: User; recorded by the coordinator on the user's instruction.
- Evidence: `handoffs/TECHSTACK-001/plan-review.md` version 10;
  `handoffs/TECHSTACK-001/index.md` version 6.

## 2026-08-25 — Overflow-precedence ruling re-opened: unobservable conditions under bounded enumeration

- Status: decided by the user on 2026-08-25 — resolution (b), plan version 10.
- User decision: amend Design §16 with one sentence stating that a count
  condition is ranked only where bounded enumeration observed it, and that
  when enumeration aborts the reported row is the highest-ranked condition
  actually observed; add a step-6 acceptance bullet and an owning test at
  the finding's own counts (65 row entries and 65 directories) pinning that
  behaviour in both name orders. Resolution (a) was rejected because it
  infers entries it did not observe. Version 10 supersedes version 9 for
  step 6 only and receives a scoped independent review before acceptance.
- Context: Packet-4 re-review finding `M1-i4v2-1`. The 2026-08-25 ruling
  ("observe every count and depth condition at the aborting level, then rank
  by registry order") is implemented and correct for conditions whose
  evidence sits at already-enumerated levels, but a condition whose evidence
  lies inside a directory the abort stopped descending cannot be observed
  under any finite bound. The finding's own fixture (64 extra directories +
  62 extra files, which is 65 row entries and 65 directories) still reports
  `SKILL_DIRECTORY_LIMIT` or `SKILL_ENTRY_LIMIT` depending on whether the
  `references/` directory sorts before or after the 65th directory. Design
  §9's "first applicable row wins" and §3's bounded enumeration are in
  tension; the reviewer offered two resolutions: (a) charge the peer side's
  known row entries against the bounded side's cap, which infers rather than
  observes; or (b) a §16 sentence stating that a count condition is ranked
  only where bounded enumeration observed it, plus an owning test at the
  finding's own counts.
- Decision: Deferred to the user; either resolution amends the accepted
  design or its stated precedence semantics. `M2-i4v2-2` (name rows ranked
  by entry name at already-enumerated levels) is inside the design and is
  being fixed now.
- Owner: User.
- Evidence: `handoffs/TECHSTACK-001/impl-4-code-review-v2.md` §`M1-i4v2-1`.

## 2026-08-25 — Accept TECHSTACK-PLAN-001 version 9

- Status: accepted.
- Context: Version 9 is the user's 2026-08-25 amendment of accepted version
  8, adding three doctor `agent_skill_export` rows so the registry can
  describe a non-canonical project root, a resource limit, and an over-long
  entry name honestly. A scoped independent review (Claude `claude-opus-5`
  high) returned `PASS`: §9/§14/§16 at one identical 27-code order, every
  carried row byte-identical, twelve adversarial two-row states resolving to
  the intended winner in the live `_first_export_code`.
- Decision: Accept version 9 as the plan of record; it supersedes version 8
  for step 6 only. The two review Lows are folded into the step-6
  implementation packet. Acceptance authorizes no commit, push, pull request,
  or release.
- Owner: User; recorded by the coordinator on the user's instruction.
- Evidence: `handoffs/TECHSTACK-001/plan-review.md` version 9;
  `handoffs/TECHSTACK-001/index.md` version 5.

## 2026-08-25 — Overflow precedence ranks applicable conditions, not observed order

- Status: accepted.
- Context: Packet-4 review finding `M1-i4-1`. `_scan_skill_directory`
  returned at the first overflow it observed while walking sorted entry
  names, so an export exceeding both the 64-entry and 64-directory caps
  reported `SKILL_ENTRY_LIMIT` or `SKILL_DIRECTORY_LIMIT` depending on
  filenames. Design §9 states "The first applicable row of that table wins"
  and §16 calls its cross-product the sole authoritative ordering.
- Decision: Bounded enumeration finishes observing the aborting directory
  level — every count and depth condition applicable there, each counter
  stopping at cap+1 — and then ranks observed conditions by registry order.
  No registry, cap, detail, or row changes; the read bound stays finite.
- Rationale: The design ranks conditions, not observations; the fix applies
  it literally and keeps enumeration bounded.
- Owner: Coordinator, within the user's implementation authorization.
- Evidence: `handoffs/TECHSTACK-001/impl-4-code-review.md` §`M1-i4-1`.

## 2026-08-25 — Three packet-4 findings escalated to the user as design amendments

- Status: decided by the user on 2026-08-25 — amend the design as version 9.
- User decision: add three new doctor `agent_skill_export` detail rows in one
  amendment — one for a non-canonical (non-NFC) project root with null paths
  (`M2-i4-2`), one for a resource limit so `RESOURCE_LIMIT` no longer folds
  into `UNSUPPORTED_SAFE_OPEN` (`L1-i4-1`), and one for an over-long entry
  name or path so length violations stop reusing the NFC detail
  (`L5-i4-5`). The registry grows 24 → 27 in §9, §16's cross-product, §14's
  literal details, and the frozen text fixture; plan version 9 supersedes
  version 8 for step 6 only and receives a scoped independent review before
  coordinator acceptance and a bounded implementation packet.
- Status of the original escalation: resolved.
- Context: Packet-4 review findings `M2-i4-2` (a non-NFC project root emits
  absolute output paths that violate Design §9's strict-NFC grammar and no
  frozen detail fits a normalization failure), `L1-i4-1` (`RESOURCE_LIMIT`
  folds into `UNSUPPORTED_SAFE_OPEN`, reporting a transient descriptor or
  memory limit as a permanent platform gap, because the frozen 24-row
  registry has no resource code), and `L5-i4-5` (`SKILL_ENTRY_NAME_INVALID`'s
  frozen detail "not strict UTF-8 NFC" is also selected for over-long paths
  and components). Each needs either a new registry row or a §9/§16 sentence,
  which amends the accepted design.
- Decision: Deferred to the user. The coordinator does not amend an accepted
  design. Packet 4 cannot pass independent review while `M2-i4-2` is open.
- Owner: User.
- Evidence: `handoffs/TECHSTACK-001/impl-4-code-review.md` §`M2-i4-2`,
  §`L1-i4-1`, §`L5-i4-5`.

## 2026-08-25 — `is_date` accepts ASCII digits only; write-fault leftovers are a recorded residual

- Status: accepted.
- Context: Packet-3 re-review Lows. `L1-i3v2-1`: `model.is_date` used `\d`
  without `re.ASCII`, so a Snapshot `as_of` written in non-ASCII decimal
  digits passed validation and then crashed `date.fromisoformat` on the
  publish surface (exit 70) while `resolve` returned exit 0. `L2-i3v2-2`: a
  zero-byte artifact left by an `ENOSPC` during publication makes every retry
  for that digest report `SNAPSHOT_OUTPUT_REFUSED`.
- Decision 1: `is_date` is amended to `re.ASCII`, a bounded change to a
  packet-1 file; every consumer and Design §4's date grammar assume ASCII
  digits, so this is a validator tightening, not a contract change.
- Decision 2: The leftover is not repaired by code. Design §16 forbids
  unlinking or garbage-collecting artifacts and the frozen §2 exit-2 set has
  no line for a mismatched leftover, so the CLI reports refusal and the
  operator removes the zero-byte file by hand; recorded as a residual risk in
  the packet-3 evidence.
- Owner: Coordinator, within the user's implementation authorization.
- Evidence: `handoffs/TECHSTACK-001/impl-3-code-review-v2.md` §`L1-i3v2-1`,
  §`L2-i3v2-2`; `handoffs/TECHSTACK-001/impl-3-evidence.md` §`FIX2`.

## 2026-08-25 — Two packet-3 rulings: closed error hierarchy, lazy API exports

- Status: accepted.
- Context: Packet-3 review findings `M1-i3-2` and `M2-i3-3`. The implementer
  had made `SnapshotOutputRefused` a third direct subclass of `TechstackError`,
  which Design §4 closes at exactly two, and had deferred the package export
  of `verify_snapshot` and `publish_snapshot` to a later step that does not
  exist, leaving half of Design §2's importable API unreachable except through
  the CLI module.
- Decision 1: `SnapshotOutputRefused` is a module-private plain `Exception`
  in `cli.py`, like `_Usage` and `_DuplicateKey`. Design §2:174 defines
  `SNAPSHOT_OUTPUT_REFUSED` as a CLI exit-2 surface condition, not an API
  caller error, so nothing requires it inside the closed hierarchy. A test
  asserts the hierarchy has exactly the two registry subclasses.
- Decision 2: `src/brichan/techstacks/__init__.py` may be amended to export
  `verify_snapshot` and `publish_snapshot` through a PEP 562 module-level
  `__getattr__` that imports `.cli` on first access, with `resolve_context`
  staying eager. Design §2 and §16 require both on the package surface, and
  the module-boundary guarantee requires that importing the package loads no
  CLI; only a lazy export satisfies both. This differs from the earlier
  rejection of a lazy `resolve_context` export, where an eager export was
  possible.
- Rationale: Both rulings apply the accepted design literally without
  amending it; the `__init__.py` amendment is bounded to two symbols and
  verified by the packet-3 re-reviewer.
- Owner: Coordinator, within the user's implementation authorization.
- Evidence: `handoffs/TECHSTACK-001/impl-3-code-review.md` §`M1-i3-2`,
  §`M2-i3-3`; `handoffs/TECHSTACK-001/impl-3-evidence.md` §`Remediation` (to
  be written).

## 2026-08-24 — Diagnostic overflow follows Design §4 literally; no pre-cap dedup

- Status: accepted.
- Context: Packet-2 review finding `M1-i2-1` showed `resolver.unique_diagnostics`
  removing byte-identical diagnostics before the 128-record cap, so a legal
  twelve-file tree that accumulates 224 identical `MAP_DEPTH_LIMIT` records
  returns one `MAP_DEPTH_LIMIT` where Design §4's frozen sentence requires
  exactly one rank-54 `DIAGNOSTIC_LIMIT`. The implementer had derived the dedup
  rather than escalating it. The reviewer offered two resolutions: drop the
  dedup, or amend Design §4 to authorize it.
- Decision: Drop the dedup. Design §4 owns overflow behaviour and authorizes no
  transformation of the accumulated array; the coordinator does not amend an
  accepted design to legitimize an undisclosed implementation choice. If
  removing dedup changes any frozen §15 case, the worker escalates rather than
  adjusting expectations.
- Rationale: Both results block, so no access changes, but consumers (the
  step-5 CLI and step-6 doctor) render the two codes differently, and a frozen
  cap must mean what the design says it means.
- Owner: Coordinator, within the user's implementation authorization.
- Evidence: `handoffs/TECHSTACK-001/impl-2-code-review.md` §`M1-i2-1`;
  `handoffs/TECHSTACK-001/impl-2-evidence.md` §`Remediation` (to be written).

## 2026-08-24 — Authorize the installed-wheel fixture to copy the whole package

- Status: accepted.
- Context: Plan step 4 exports `resolve_context` from
  `src/brichan/techstacks/__init__.py`. Packet 1's
  `installed_package_root()` fixture in `tests/unit/test_techstack_filesystem.py`
  simulates an installed wheel by copying a hardcoded four-file list, so any
  new module the package imports breaks the simulated install with
  `ModuleNotFoundError`. The packet-2 implementer escalated rather than
  choosing between a lazy export, dropping the export, or editing a packet-1
  test.
- Decision: The fixture copies every `.py` file under
  `src/brichan/techstacks/`, so the simulated install matches a real wheel.
  The export stays eager; a lazy `__getattr__` was rejected because an
  incomplete installation would then fail at first attribute access instead of
  at import. Only `installed_package_root()` may change in that file.
- Rationale: The fixture, not the export, was the fragile part; fixing it once
  keeps every later packet from re-breaking the same test.
- Owner: Coordinator, within the user's implementation authorization.
- Evidence: `handoffs/TECHSTACK-001/impl-2-evidence.md` §`Escalation and
  coordinator authorization`.

## 2026-08-24 — Authorize a bounded packet-1 amendment for prefix selectors

- Status: accepted.
- Context: The packet-2 implementer escalated that `model.is_selector` from
  packet 1 rejects any trailing slash, so the prefix selector `src/frontend/`
  in the frozen Design §15 fixture row cannot yield an applicable Snapshot.
  Design v8 §6 retains the version-3 authority design unchanged, and
  `versions/v3/design.md:465-480` defines a selector as the dot, an exact
  normalized relative path, or a prefix normalized relative path ending in
  exactly one slash. Packet 1 is defective on this point and its two
  independent reviews, which verified registries and literals, did not check
  selector grammar against the fixture.
- Decision: The packet-2 worker may amend `is_selector` only, add regression
  tests to `test_techstack_model.py`, and must not widen
  `is_normalized_relative_path`, which the Design §14 project-root canonical
  rule relies on to reject a terminal slash. The packet-2 independent reviewer
  verifies the amendment against packet 1 and the fixture.
- Rationale: The contract is unambiguous and frozen; an amendment is smaller
  and safer than a plan revision, and keeping the reviewer in the loop
  preserves the per-packet review invariant.
- Owner: Coordinator, within the user's implementation authorization.
- Evidence: `handoffs/TECHSTACK-001/impl-2-evidence.md` §`Escalation and
  coordinator authorization` (to be written by the worker).

## 2026-08-24 — Authorize TECHSTACK-001 implementation on `feat/techstacks-rules`

- Status: accepted.
- Context: `TECHSTACK-PLAN-001` version 8 was accepted earlier the same day
  after independent review `PASS`. The user then instructed the coordinator to
  open a new branch and start implementation.
- Decision: Implement accepted plan version 8 on branch `feat/techstacks-rules`
  in dependency order through bounded Herdr worker packets, each followed by
  focused tests and closed by a fresh independent code review before the next
  packet starts. Implementation authorization is local only: it does not
  authorize commit, push, pull request, release, reinitialization or export
  removal against a real owner repository, or any remote action.
- Rationale: The plan's step order encodes real dependencies (models and the
  hardened reader before parser, resolver, CLI, doctor, inventory, packet, and
  eval), and a per-packet review keeps the review route independent of the
  implementer at every step.
- Owner: User; recorded by the coordinator on the user's instruction.
- Evidence: `handoffs/TECHSTACK-001/plan.md` version 8 (`Plan status:
  accepted`); `handoffs/TECHSTACK-001/index.md` version 3.

## 2026-08-24 — Accept TECHSTACK-PLAN-001 version 8

- Status: accepted.
- Context: Draft plan versions 1 through 7 each received independent
  `CHANGES REQUIRED`. Version 8 was a bounded correction of the two version-7
  findings, and independent review v8 (Claude `claude-opus-5`, high) returned
  `PASS` after measuring the diff itself and re-running the doctor renderer,
  frozen eval corpus parse, and production receipt parser on version 8's bytes.
- Decision: Accept `TECHSTACK-PLAN-001` version 8 as the plan of record for the
  project-owned hierarchical `techstacks/` rules and the mandatory worker-context
  contract. Acceptance authorizes no implementation.
- Rationale: The review route stayed stronger than the planning route at every
  version, the hard contracts (isolated helper launch, doctor v2 cross-product,
  frozen eval corpus, receipt round trip) were verified by execution rather than
  by reading planner claims, and the only open finding is a wording defect.
- Owner: User; recorded by the coordinator on the user's instruction.
- Evidence: `handoffs/TECHSTACK-001/plan-review.md` version 8;
  `handoffs/TECHSTACK-001/index.md` version 3.

## 2026-08-24 — Advance doctor report schema to version 2

- Status: accepted for `TECHSTACK-001` plan revision.
- Context: Independent plan review v4 found that adding the
  `agent_skill_export` root key while retaining the exact doctor report schema
  v1 would be an unauthorized compatibility break.
- Decision: Advance the public doctor report schema from v1 to v2 for the
  additive export-diagnostics contract. Keep the installed `.brichan/` state
  schema at v1; no installed-state migration is introduced.
- Rationale: A visible report-version boundary is safer than silently changing
  the exact schema-v1 key set and lets consumers reject or adopt the new shape
  deliberately.
- Owner: User.
- Evidence: User direction on 2026-08-24; `handoffs/TECHSTACK-001/plan-review.md`
  finding H2-v4-2.

## 2026-08-24 — Machine-resolved techstacks with user-controlled skill refresh

- Status: accepted for `TECHSTACK-001` plan revision.
- Context: Plan review v1 found that instruction-only selection could not prove deterministic paths, hashes, conflicts, or drift, and existing unmanaged `.agents` skill exports would remain stale after `.brichan/` reinitialization.
- Decision: V1 will use a production resolver implemented with the Python standard library. Existing `.agents/skills/herdr-orchestration/` exports remain non-overwritten; Brichan will diagnose staleness and provide an explicit user-controlled backup/remove/re-export workflow.
- Rationale: Machine-owned behavior can receive behavioral tests, while refresh remains compatible with the no-automatic-overwrite invariant.
- Owner: User.
- Evidence: User direction on 2026-08-24; `handoffs/TECHSTACK-001/plan-review.md` findings H1 and H2.

## 2026-08-10 — Export the Brichan skill to `.agents/` by default

- Status: accepted
- Context: Direct Codex sessions need the packaged Herdr skill in the standard
  `.agents/skills/` discovery tree, and requiring `--init-agents` made this
  easy to omit.
- Decision: Every `brichan init` previews or creates the missing
  `.agents/skills/herdr-orchestration/` layout. Existing `.agents/` content and
  existing skill files remain untouched; the opt-in flag is removed.
- Rationale: The default initialized repository should work both through
  `brichan run` and through a direct Codex session without extra setup.
- Owner: User.
- Evidence: User direction on 2026-08-10; `tests/unit/test_project_lifecycle.py`.

## 2026-07-29 — Explore installed CLI plus project initialization

- Status: superseded
- Context: Five independent assessments found strong package foundations but
  checkout-root coupling and no safe project lifecycle.
- Decision: Run bounded discovery and, only if it passes, a disposable
  prototype of an installed CLI plus explicit project initialization. Defer
  the MVP decision; retain clone mode and do not pursue full-repo vendoring.
- Rationale: This best separates tool-owned code from project-owned state while
  preserving current guardrails and enabling incremental validation.
- Trade-offs: Adds schema, migration, ownership, external-tool compatibility,
  and support obligations.
- Owner: Brida; final product authority remains with the user.
- Evidence: `assessment.md`; first independent verdict `CHANGES REQUIRED`,
  remediated before focused re-review.

## 2026-07-29 — One-user dogfood scope

- Status: accepted
- Context: The user is the first target user; a later cohort may contain 3–5
  trusted users.
- Decision: Proceed toward a narrowly supported installable dogfood tool.
  Exclude commercialization, market-demand gates, broad compatibility, and
  support for unrelated edge cases.
- Rationale: The immediate value is improving the owner's real Brida workflow,
  so direct use provides stronger evidence than market research.
- Trade-offs: The prototype may be intentionally environment- and
  runtime-specific; wider compatibility is deferred until a dogfood failure
  requires it.
- Owner: User.
- Evidence: User direction in the 2026-07-29 project turn; `assessment.md`.
- Supersedes: 2026-07-29 — Explore installed CLI plus project initialization.

## 2026-07-29 — Codex-first schema-v1 vertical slice

- Status: accepted
- Context: The one-user dogfood needs to run from an installed package inside
  an existing Git repository without a separate Brida checkout.
- Decision: Ship the first local vertical slice as Codex-only installed mode.
  `brida init` owns only a versioned `.brida/` footprint; project launch injects
  package-owned developer instructions and Herdr skill discovery through Codex
  CLI overrides and executes external `codex` directly at the target root.
  Checkout mode remains available only when the package proves it belongs to
  the `BRIDA_ROOT` checkout.
- Rationale: This creates the smallest end-to-end owner workflow while avoiding
  edits to target `AGENTS.md`, `.codex/`, `CLAUDE.md`, or root wrappers.
- Trade-offs: Installed mode uses a narrow Codex argument allowlist, schema v1
  has no repair/migration, and package upgrades require deliberate
  reinitialization. Windows, Claude installed mode, and broad repository shapes
  remain deferred.
- Owner: Brida within the user-approved one-owner dogfood scope.
- Evidence: `docs/guides/installable-dogfood.md`; installed-wheel integration
  tests; final independent reviewer verdict `PASS`; 152-test `make check`.

## 2026-07-29 — Dedicated external installer environment

- Status: accepted
- Context: The owner needs one-command installation from outside the Brida
  checkout without activating a virtual environment.
- Decision: Install Brida into a dedicated external venv and expose all console
  commands through guarded symlinks in a user command directory. Do not modify
  the target project's `.venv` or shell profile automatically.
- Rationale: Tool lifecycle stays independent from each target repository while
  `brida` remains directly executable.
- Trade-offs: Python 3.10+ with local `pip`, `setuptools`, `venv`, and `wheel`
  is still required; the user may need to add the command directory to `PATH`
  once.
- Evidence: `scripts/install-brida`; installed-dogfood integration tests;
  Claude Opus final verdict `PASS`; 155-check `make check`.

## 2026-07-29 — Brichan distribution identity with stable Brida runtime API

- Status: superseded
- Context: The tool needs a future pip/PyPI distribution identity while the
  owner relies on the existing `brida` imports and `brida-*` commands.
- Decision: Use `brichan` as the distribution and public repository-facing
  name for version `0.5.0`; retain the `brida` Python package and every
  existing console command. Prepare—but do not execute—PyPI Trusted Publishing.
- Rationale: It supports a future registry release without breaking the
  dogfood runtime or requiring target repositories to migrate command names.
- Trade-offs: The public repository URL, PyPI trusted publisher, GitHub `pypi`
  environment, and README image URL must be deliberately configured before the
  first upload.
- Owner: User.
- Evidence: `pyproject.toml`; `.github/workflows/publish.yml`;
  `handoffs/PYPI-001/receipt.md`; independent Claude Opus review `PASS`.

## 2026-08-09 — Brida → Brichan rename completed; project slugs retained

- Status: accepted
- Context: The earlier decision kept the `brida` Python package and `brida-*`
  commands while only the distribution was named `brichan`. That split is gone:
  the runtime package, console commands, `.brichan/` footprint, and installer
  are all `brichan`, and the distribution is published.
- Decision: `brichan` is the single name for the distribution, the importable
  package, the console commands, and the installed-project directory. The
  `projects/brida-*` memory slugs are deliberately retained, because renaming
  them would rewrite recorded history and every receipt pointer for no runtime
  benefit. Historical wording in `CHANGELOG.md`, existing receipts, and
  evidence files is preserved as written.
- Rationale: One runtime name removes the dual-identity trap the previous
  decision accepted as a temporary cost, while frozen slugs keep the audit
  trail intact.
- Trade-offs: Memory slugs and project titles read `brida` while the runtime
  reads `brichan`, so readers must know the slugs are historical labels.
- Owner: User.
- Evidence: `README.md`; `VERSION`; `scripts/install-brichan`;
  `src/brichan/`; `handoffs/MEMORY-001/receipt.md`.
- Supersedes: 2026-07-29 — Brichan distribution identity with stable Brida
  runtime API.

## 2026-08-14 — Typed read-only Herdr monitoring boundary

- Status: accepted
- Context: Raw terminal-buffer observations and Herdr scheduling states could be
  mistaken for complete worker evidence; the user also questioned whether
  monitoring depended on screenshots.
- Decision: Observe Herdr through `brichan-herdr-agent-observe`. The monitor reads
  text/JSON envelopes, not bitmap screenshots; preserves scheduling state without
  interpreting completion; reports conservative truncation; and treats declared
  durable files as acceptance evidence only after content review. Keep verified
  support pinned to Herdr `0.7.3`/protocol `16` until a separately authorized
  upgrade and design revision.
- Rationale: A typed, tested boundary makes parser, redaction, wait-cap, path, and
  exit-code behavior auditable while preventing terminal state from becoming an
  unsupported completion claim.
- Trade-offs: Healthy reads normally report truncation risk `possible`; later
  Herdr formats intentionally degrade to `unverified` or malformed findings; a
  released packaged-skill update would require deliberate installed-state
  backup and reinitialization.
- Owner: User-authorized HERDR-001 implementation.
- Evidence: `handoffs/HERDR-001/receipt.md`; code-review artifact v4 `PASS`;
  focused and full repository gates.
## 2026-08-26 — Approve TECHSTACK-002 planning gates G1–G3 and correction strategy

- Status: accepted for `TECHSTACK-002` plan revision.
- Context: Draft `TECHSTACK-PLAN-002` version 1 mapped all eleven inputs but
  could not be accepted before user rulings and a techstack re-resolution.
- Decision: Approve the bounded prose amendment that accepts backticks and
  angle brackets; approve deterministic `INVALID_LEAF` line and violated-rule
  attribution; retain mode-specific checkout and installed skill trees under
  marker parity with a packaged-subset contract; record Linux as an unmeasured
  residual with no push or remote action; and correct the TECHSTACK-001 prose
  defects through a versioned v11 reissue while preserving archived v10 bytes.
- Boundary: Brichan never edits `techstacks/**`. The project owner must correct
  `PACKAGED-001` before Brichan can re-resolve the final Snapshot. No exception
  is available because the rule's Exceptions section is `None`.
- Owner: User.
- Evidence: User confirmation on 2026-08-26; `handoffs/TECHSTACK-002/options.md`
  D6–D8; `handoffs/TECHSTACK-002/design.md` sections 6–9;
  `handoffs/TECHSTACK-002/plan.md` gates G1–G4.

## 2026-08-26 — Accept TECHSTACK-PLAN-002 version 4 and replace the usage-limited Codex reviewer

- Status: accepted for `TECHSTACK-002` implementation.
- Context: The Codex coordinator and its version-3 plan reviewer both stopped
  on a Codex usage limit; the reviewer had verified the Snapshot but written
  nothing. The user asked Claude Code to continue coordination.
- Decision: Replace the reviewer once with a fresh Claude `claude-opus-5`
  high session on the identical packet (the route `tasks.md` already allowed
  while Codex is limited); require a version 4 for the `CHANGES REQUIRED`
  findings on a re-resolved attempt-plan-4 Snapshot with unchanged scope;
  accept version 4 after its independent `PASS`; carry the three Low
  findings into packet instructions instead of a version 5; treat the stale
  gitignored `build/` and `src/brichan.egg-info/` as generated litter to
  remove before the `make check` gate, not as a code defect.
- Owner: Brichan (coordinator), within already authorized planning scope.
- Evidence: `handoffs/TECHSTACK-002/versions/v3/plan-review.md`;
  `handoffs/TECHSTACK-002/plan-review.md` version 2; `receipt.md`
  Verification rows; `tasks.md` TECHSTACK-002 row.

## 2026-08-26 — Correct two design-mandated sentences through plan version 5 before the P1–P3 fix

- Status: accepted for `TECHSTACK-002`.
- Context: The stage-1 review disproved by execution two sentences that
  `design.md` version 4 §3 and §4 mandate verbatim (the cross-module test's
  stated failure mode; the launcher comment's unqualified "fails closed"),
  and found the packaged-subset test's distinct justification unstated. A fix
  worker cannot ship corrected wording that contradicts the accepted design.
- Decision: Issue design/plan version 5 with exactly those corrections, the
  §8 justification, two re-anchored citations, and a bounded `P1–P3 fix`
  packet; run it in parallel with P6a/P6b under accepted version 4 because
  the write sets are disjoint and §6–§7 do not change; ship the fix after P6
  so two workers never run `make check` on a half-edited tree. No scope,
  packet, gate, or user ruling changes; the amendment corrects prose to
  match executed behavior.
- Owner: Brichan (coordinator); the user may overrule.
- Evidence: `handoffs/TECHSTACK-002/stage1-review.md` M1–M3, L2;
  `handoffs/TECHSTACK-002/p1-p3-evidence.md`.

## 2026-08-26 — Record the P6b exit-code erratum against accepted plan version 5

- Status: accepted erratum for `TECHSTACK-002`; the accepted plan text is
  not rewritten.
- Context: `plan.md` version 5 §P6b acceptance says the real-CLI resolve on
  a malformed leaf "freezes exact stdout bytes with empty stderr and exit 0".
  The shipped CLI contract, frozen by an existing integration test, exits 5
  for a blocked resolution; the implementer asserted 5 and the stage-2
  review confirmed the plan text was wrong (deviation 3, finding `L2`).
- Decision: The accepted plan version stays immutable; this entry, the
  dossier `index.md` Uncertainty, and the whole-task `code-review.md` carry
  the erratum. The test asserting exit 5 is correct. Two further stage-2
  wording notes (`design.md` §7.4's "8 bare raises" counts the leaf-reachable
  subset; §7.8's eighth T-LINE fixture is unreachable by construction and is
  asserted as its true outcome plus a reachable 32-line fixture) are recorded
  the same way.
- Owner: Brichan (coordinator).
- Evidence: `handoffs/TECHSTACK-002/stage2-review.md` §Rulings, `L1`, `L2`;
  `p6-evidence.md`; `tests/integration/test_techstack_cli.py`.
