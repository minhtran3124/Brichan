# Design

Chosen approach and its structural consequences. Versioned or superseded, never silently rewritten.

## Artifact metadata

- Task ID: `PYPI-003`
- Task level: `2`
- Artifact: `design`
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

Six files change. One config boolean flips, the generator rewrites its one
output, three test assertions pin the now-public contract at the config,
description, and sdist layers, and two durable-memory records close the gate
(`current-state.md` and the completed `PRODUCT.md` "Next, in order" item).
Everything else — source document, generator, packaging metadata, policy,
routing — is untouched.

## Version 2 amendments

Per the coordinator's 2026-08-10 decision (`options.md` D3), §4 now also
removes the completed gate line from `PRODUCT.md` section 10 as a one-line
truth reconciliation.

## Version 3 amendments

Closing plan-review version 2: §1 replaces authenticated `gh api` with a
truly unauthenticated `curl` and sanitizes the recorded evidence to the four
asserted fields (M2); §4.1 corrects the baseline to 79 lines (L1); §5
authorizes the coordinator's exact post-PASS lifecycle transitions, adds the
one `references.md` receipt pointer, and fixes the review target to
`PYPI-003-PLAN` version 3 with required identity agreement (H1, H2, M1); new
§6 specifies the executable offline temporary-copy negative procedure (M3).
The six implementation files of §§2–4 are unchanged.

## Version 4 amendments

Closing plan-review version 3: §1's probes lead with `curl -q` (no auth
headers, no netrc, sanitized fields only); §5 becomes a two-phase
coordinator lifecycle — Phase A accepts the plan and authorizes
implementation with a schema-v2 accepted receipt and the exact
`references.md` pointer line, Phase B finalizes after code-review PASS; §6's
manual temporary-copy negative procedure is removed as self-imposed — the
permanent shipped-config test is the automated revert gate; review identity
targets `PYPI-003-PLAN` version 4. The six implementation files of §§2–4 are
unchanged.

## Version 5 amendments

Closing plan-review version 4, in §5.2 only: the independent code reviewer
alone authors the complete `code-review.md` — content, `passed` phase state,
and verdict — and the coordinator never edits it, only verifies and projects
it into `index.md` and the receipt; Phase B is reordered so the receipt is
finalized after project memory and pane cleanup, and the final full
`make check` runs last against the finalized receipt and tree, so nothing
claims later evidence in advance. Review identity targets `PYPI-003-PLAN`
version 5. §§1–4, §5.1, §6, and every exclusion are unchanged.

## 1. Fresh verification (execution-time, read-only)

Before any edit, the implementer runs and captures:

```bash
curl -q -s -H 'Accept: application/vnd.github+json' \
  https://api.github.com/repos/minhtran3124/Brichan \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); \
print({k: d.get(k) for k in ("html_url","visibility","private","default_branch")})'
curl -q -s -o /dev/null -w '%{http_code} %{content_type}\n' \
  https://raw.githubusercontent.com/minhtran3124/Brichan/main/assets/brichan-hero.png
```

Both invocations lead with `-q` as the first argument, so no local curl
configuration file can inject credentials or options; they send no
`Authorization` header and no token, and use no netrc or credential helper —
genuinely anonymous requests to the public GitHub API (unlike `gh api`,
which authenticates; plan-review v2 M2). Only the four
extracted fields are recorded, keeping the evidence sanitized. Expected:
`https://github.com/minhtran3124/Brichan`, `public`, `False`, `main`; then
`200 image/png`. Both commands are reads and mutate nothing. On any mismatch:
stop, change no files, escalate to the coordinator with the captured output.

## 2. The flip and regeneration

`config/pypi-readme.json` line 5: `"public_repository": false` →
`"public_repository": true`. Lines 6–7 stay byte-identical. Then:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_pypi_readme.py
```

The expected `README_PYPI.md` diff is exactly two added lines after the badge
block (verified by in-memory simulation on 2026-08-10, `validate` clean):

```diff
 [![License](https://img.shields.io/pypi/l/brichan.svg)](https://pypi.org/project/brichan/)
+
+![Brichan coordinating a team of AI workers](https://raw.githubusercontent.com/minhtran3124/Brichan/main/assets/brichan-hero.png)

 Coding agents are very good at the work in front of them and very bad at
```

Any other change to `README_PYPI.md` falsifies the simulation: stop and
escalate. The file is never hand-edited.

## 3. Test additions

### 3.1 `tests/unit/test_build_pypi_readme.py` — `ConfigTest`

```python
def test_shipped_config_is_public_with_the_verified_base_urls(self):
    """PYPI-003: a silent revert to private mode must fail here, not ship."""
    config = build_pypi_readme.load_config()
    self.assertIs(config["public_repository"], True)
    self.assertEqual(
        config["asset_base_url"],
        "https://raw.githubusercontent.com/minhtran3124/Brichan/main",
    )
    self.assertEqual(
        config["link_base_url"],
        "https://github.com/minhtran3124/Brichan/blob/main",
    )
```

### 3.2 `tests/contract/test_packaging_metadata.py` — `PackagingMetadataTest`

```python
def test_committed_description_embeds_the_public_hero_image(self):
    """The 0.5.0 page shipped a broken hero; the public flip restores it."""
    committed = (ROOT / "README_PYPI.md").read_text(encoding="utf-8")
    self.assertIn(
        "![Brichan coordinating a team of AI workers]"
        "(https://raw.githubusercontent.com/minhtran3124/Brichan/main/assets/brichan-hero.png)",
        committed,
    )
```

### 3.3 `tests/contract/test_packaging_metadata.py` — `SdistBuildTest`

```python
def test_published_description_embeds_the_hero_image(self):
    """PKG-INFO is what PyPI renders; the raw URL must survive the build."""
    self.assertIn(
        "https://raw.githubusercontent.com/minhtran3124/Brichan/main/assets/brichan-hero.png",
        self._pkg_info(),
    )
```

No existing assertion changes. The private-mode classes keep their synthetic
`PRIVATE` config; `test_pypi_source_hero_resolves_when_the_repository_goes_public`
keeps its (now no-op) override and still proves the render path. No test
touches the network.

## 4. Gate closure in durable memory

### 4.1 `current-state.md`

- **Remove** the completed bullet at lines 56–58 ("Confirm the public
  repository URL and fix the PyPI README image URL; flip `public_repository`
  in `config/pypi-readme.json` when the repository is public.").
- **Add** one bullet at the end of "Distribution and release":

  ```text
  - The repository is public at https://github.com/minhtran3124/Brichan; the
    PyPI long description embeds the hero image through the anonymous raw URL
    (verified 2026-08-10).
  ```

- **Preserve byte-identically**: the external-dogfood gate, the TestPyPI gate,
  every other section, and `Last updated: 2026-08-10` (already current). Net
  size stays ≤ 80 lines: 79 today (plan-review v2 L1 corrected the earlier
  74-line claim), and the −3 +3 edit keeps 79.

### 4.2 `PRODUCT.md`

- **Delete** the single line at `PRODUCT.md:230`:
  `3. Confirm the public repository URL and fix the PyPI README image URL.`
- Items 1 and 2 of "Next, in order" keep their numbers; every other line —
  including `Verified as of 2026-08-09` and the `Last verified:` header,
  both already satisfying `make memory-check` — is byte-identical.
  `git diff -- PRODUCT.md` must show exactly one deleted line, zero added.

## 5. Lifecycle and review — two coordinator-owned phases

- **Stronger Level 2 review route**: independent review of `PYPI-003-PLAN`
  **version 5** and later of the implementation, by the documented one-off
  stronger override — Codex Sol at high effort (`config/model-routing.json`
  `review` route with the effort override recorded in `tasks.md`) — not the
  routine route. The override is recorded in `index.md` under Review route
  strength: `stronger`. Reviewers write review artifacts only; they make no
  lifecycle transitions.
- **Identity agreement (H1)**: `plan-review.md`'s reviewed plan ID/version,
  `index.md`'s accepted-plan identity, and the receipt's plan identity must
  all record `PYPI-003-PLAN` version 5 before implementation proceeds and
  before finalization completes.

### 5.1 Phase A — acceptance and authorization (after plan-review PASS, before implementation)

The coordinator, and only the coordinator:

1. marks the five planning artifacts (`requirements.md`, `brief.md`,
   `options.md`, `design.md`, `plan.md`) `passed`;
2. sets `plan.md` Plan status to `accepted` (the accepted version is then
   immutable);
3. completes `request.md`, `index.md`, and `client-follow-up-questions.md`
   as applicable;
4. creates the **schema-v2 accepted receipt** at
   `projects/brida-installable-tool/handoffs/PYPI-003/receipt.md`, recording
   the accepted plan identity (`PYPI-003-PLAN` version 5) with downstream
   implementation and review evidence explicitly pending;
5. adds **exactly one** receipt-pointer line reading exactly
   `projects/brida-installable-tool/handoffs/PYPI-003/receipt.md` to
   `projects/brida-installable-tool/references.md` (M1);
6. advances the `PYPI-003` row's status cell in `tasks.md` to implementing.

**Completing Phase A is what authorizes implementation.**

### 5.2 Phase B — finalization (after implementation and code-review PASS)

**Ownership boundary**: the independent code reviewer alone writes the
complete `code-review.md` — its content, its `passed` phase state, and its
`PASS`/`CHANGES REQUIRED` verdict. The coordinator never edits
`code-review.md`; it only verifies that artifact and projects its result
into `index.md` and the receipt.

After the reviewer's `PASS`, the coordinator, in this order:

1. verifies the implementation evidence against the plan's acceptance
   criteria;
2. updates current project memory, the `tasks.md` row, `index.md`,
   `pr-desc.md`, the `metrics/runs.jsonl` row, and its other coordinator
   projections;
3. closes all Brichan-owned idle/done panes, keeping only any pane needed to
   report;
4. **only after** project memory and pane cleanup are complete, finalizes
   the schema-v2 receipt to reviewed `PASS`, replacing the pending markers
   with the §1 sanitized probe output, the diff evidence, and the test
   results actually run — evidence that exists at that moment, never claimed
   in advance;
5. runs the final full `make check` last, against the finalized receipt and
   tree; its result is observed after the receipt and is not recorded inside
   it.

**Phase B is what makes the complete-dossier gate and the final full gate
pass**; the scaffolded placeholders are today the sole source of
`make dossiers` failures.

## 6. Revert regression — automated, not manual

The shipped-config unit pin (§3.1) directly asserts
`config["public_repository"] is True`. Reverting the flip therefore fails
that permanent test naturally in any normal focused run —
`make test-unit`, the focused unittest invocations, and full `make check`
are the executable regression gate. No bespoke manual negative procedure or
temporary-copy matrix exists; version 3's was removed as self-imposed
(plan-review v3).

## Consequences

- The public contract becomes triply pinned (config, description, PKG-INFO);
  reverting to private mode requires deliberately deleting tests.
- The live PyPI page is unchanged until the next release ships the new
  description; no release is authorized here.
- `PRODUCT.md`'s "Next, in order" list retains only outstanding work.

## Evidence

- In-memory simulation (2026-08-10): public-mode `expected()` differs from
  committed `README_PYPI.md` by exactly the §2 diff; `validate` returned `[]`.
- `scripts/build_pypi_readme.py:58-63` — public mode revalidates both base
  URLs as https, so the flip cannot ship with a malformed base.
- `tests/contract/test_packaging_metadata.py:125-135` — the existing
  no-relative-target PKG-INFO test stays green: the restored line contains
  `(https://raw...`, not `(assets/`.
- Baseline 28/28 focused tests pass and `--check` is in-sync, so any
  post-flip failure is attributable to this change.

## Uncertainty

- The sdist-layer pin (§3.3) skips on machines without a setuptools backend
  (existing `SkipTest` path); the description-layer pin (§3.2) still guards
  the URL there.
- If GitHub ever changes raw-URL semantics for public repositories, the pins
  hold locally while the page breaks; only release-time inspection catches
  that class of failure.
