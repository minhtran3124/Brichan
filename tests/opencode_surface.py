"""The binding artifact between ``OPENCODE_VERSION`` and its derived tables.

Three tables in :mod:`brichan.cli.opencode` are *derived* from the pinned
provider's own source rather than hand-listed: :data:`EXECUTABLE_SCANS` (the
directory families D8 refuses), :data:`CONFIG_DISCOVERY_SOURCES` (the files D12
scans), and :data:`EXECUTION_KEYS` (the keys whose values become modules the
provider loads).  Re-deriving them is the whole content of a version bump.

The problem this module exists for
----------------------------------

The derivations are checked against the real provider tree only by the opt-in
``BRICHAN_OPENCODE_PINNED_SOURCE`` classes in
``tests/unit/test_opencode_commands.py``.  Those classes *skip* when the
variable is unset, which is every ordinary run.  So before this module, editing
``OPENCODE_VERSION`` and nothing else left ``make check`` and ``make test``
fully green — the offline drift tests compare the tables against a transcript
that was itself written by hand at the old version, so they agree with
themselves and prove nothing about the new release.  A bump that silently
missed a provider-side addition to any of the three tables would ship green.

What this module does about it
------------------------------

:func:`surface_digest` canonicalises the version plus all three tables into one
sha256.  The pinned-source run writes that digest to :data:`FIXTURE_PATH`, and
an always-on contract test recomputes it and compares.  The fixture is
therefore a receipt: it says *this exact surface was checked against a real
extracted tree of this exact version*.  Change the version or any table without
regenerating it and the contract test fails offline, immediately, in
``make check``, naming the command to run.

What this does **not** guarantee
--------------------------------

This is a forcing function, not a proof, and the difference matters — this
project has repeatedly been bitten by controls that looked stronger than they
were.  Stated plainly:

* **The fixture can be hand-edited.**  Nothing stops a maintainer from pasting
  the new digest in (the failure message even prints it) without ever running
  the pinned-source check.  What the mechanism buys is that doing so is a
  deliberate, visible line in the diff instead of an omission nobody can see.
  A reviewer who reads a bump commit and finds a changed fixture with no quoted
  pinned-source output has found the thing to ask about.
* **It proves nothing about the provider.**  The digest is computed from
  Brichan's own tables.  It records *that* a verification ran, not that the
  tables are correct.  Correctness is still the pinned-source classes' job.

**What the digest's coverage claim means, and why it is now true.**  The digest
covers all three tables equally, so the receipt asserts all three were checked
against a real extracted tree.  When round 10 shipped it, that claim was
accurate for two of them: ``EXECUTABLE_SCANS`` and ``EXECUTION_KEYS`` each had a
pinned-source class reading the tree, while ``CONFIG_DISCOVERY_SOURCES`` was
verified against a hand-written transcript only.  Round 10 disclosed the
asymmetry rather than letting the receipt imply it away; round 11 closed it by
adding :class:`PinnedSourceConfigDiscoveryTest`, which enumerates every
configuration read in the pinned tree, re-derives the discovered basenames and
the managed roots from provider literals, and fails in the ADDED direction when
a release gains a read site or a filename.  All three tables are now verified by
a class of the same shape, so the digest's uniform claim is met rather than
aspirational.  That check is one of the three the receipt writer requires before
it will write.

Closing it was not free of consequence: reading the config surface from the tree
instead of from a transcript immediately found a file family the transcript had
never named — the TUI document, ``tui.json``/``tui.jsonc``, which carries its
own ``plugin`` key.  Round 11 escalated it as found-but-unscanned and recorded
that the digest did not cover it.  **Round 12 settled it and that caveat is now
retired.**  The TUI document is an executable surface: its ``plugin`` array is
the same ``PluginSpec`` shape the main config uses and reaches the same
``import()`` in ``plugin/loader.ts``.  Its four families are in
:data:`CONFIG_DISCOVERY_SOURCES` with ``document="tui"``, so the digest covers
them like any other entry, and the chain that justifies them is pinned against
the tree by ``PINNED_TUI_EXECUTION_CHAIN``.

``document`` is why that addition did not break the guard: migration keys apply
to the main document only, because ``theme`` and ``keybinds`` are the TUI
document's legitimate content and D10 writes a keybind backstop into the owned
root two steps before D12 scans it.
* **The regeneration path trusts its own inputs.**  :func:`write_fixture`
  checks the supplied tree self-identifies as ``OPENCODE_VERSION`` via its
  ``packages/opencode/package.json``, which stops the obvious wrong-tree
  mistake and not a determined one.

This module is deliberately not under ``src/``: it is test-support, has no
runtime caller, and adding a digest function to the guard would be dead
production code.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    # The contract layer runs without PYTHONPATH=src; the unit layer sets it
    # up itself.  Do it here so either importer works unchanged.
    sys.path.insert(0, str(ROOT / "src"))

from brichan.cli import opencode as oc  # noqa: E402


#: The committed receipt.  Regenerated only by the pinned-source run.
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "opencode-pinned-surface.json"

#: The exact command a maintainer must run to regenerate :data:`FIXTURE_PATH`.
#: Carried here so the failure message, the constant's docstring, and the guide
#: cannot drift into naming three different things.
REGENERATE_COMMAND = (
    "gh api repos/anomalyco/opencode/tarball/v{version} > /tmp/oc.tgz && "
    "mkdir -p /tmp/oc && tar -xzf /tmp/oc.tgz -C /tmp/oc && "
    "BRICHAN_OPENCODE_PINNED_SOURCE=/tmp/oc/<extracted-dir> "
    "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src "
    "python3 -m unittest tests.unit.test_opencode_commands"
)

#: The three derived tables, by the attribute name they carry in the guard.
DERIVED_TABLES = (
    "EXECUTABLE_SCANS",
    "CONFIG_DISCOVERY_SOURCES",
    "EXECUTION_KEYS",
)


def surface_records() -> dict:
    """Canonicalise the pinned version and the three derived tables.

    Every field of every entry is included, citations among them: a citation
    that moves is a re-derivation too, and a mechanism that ignored them would
    let a table be re-pointed at different source lines without notice.
    """

    return {
        "opencode_version": oc.OPENCODE_VERSION,
        "tables": {
            name: [asdict(entry) for entry in getattr(oc, name)]
            for name in DERIVED_TABLES
        },
    }


def surface_digest() -> str:
    """Return the sha256 over :func:`surface_records`, prefixed with its algorithm."""

    canonical = json.dumps(
        surface_records(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def fixture_contents() -> dict:
    """Build the fixture document for the surface as it currently stands."""

    records = surface_records()
    return {
        "_comment": (
            "Receipt for the BRICHAN_OPENCODE_PINNED_SOURCE verification. "
            "Regenerated by that run only; see tests/opencode_surface.py for "
            "what this does and does not guarantee. Hand-editing this file "
            "silences the contract test without verifying anything."
        ),
        "opencode_version": records["opencode_version"],
        "surface_digest": surface_digest(),
        "entry_counts": {
            name: len(entries) for name, entries in records["tables"].items()
        },
    }


def load_fixture() -> dict:
    """Read the committed receipt."""

    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def write_fixture() -> dict:
    """Overwrite the committed receipt with the current surface.

    Called only from the ``BRICHAN_OPENCODE_PINNED_SOURCE`` classes, after they
    have checked the supplied tree against the pin.  Writing is idempotent: an
    unchanged surface rewrites identical bytes, so a routine pinned-source run
    leaves no diff.
    """

    document = fixture_contents()
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return document


def mismatch_message(recorded: dict) -> str:
    """The message a maintainer sees when the surface and the receipt disagree.

    It has to answer three questions on its own, because whoever trips it is
    mid-edit and will not go looking: what happened, why the rest of the suite
    stayed green, and the exact command to run.
    """

    actual_version = oc.OPENCODE_VERSION
    recorded_version = recorded.get("opencode_version")
    if recorded_version != actual_version:
        what = (
            f"OPENCODE_VERSION moved from {recorded_version!r} to "
            f"{actual_version!r} without the pinned-source verification "
            "being re-run."
        )
    else:
        what = (
            "One of the source-derived tables "
            f"({', '.join(DERIVED_TABLES)}) changed without the pinned-source "
            "verification being re-run."
        )
    return (
        f"OpenCode pinned-surface receipt is stale.\n\n"
        f"{what}\n\n"
        "Why nothing else caught this: the offline drift tests compare these "
        "tables against a hand-written transcript, so they agree with "
        "themselves. The checks that read the real provider tree are opt-in "
        "and skip silently when BRICHAN_OPENCODE_PINNED_SOURCE is unset, which "
        "is every ordinary run. An unset run is not evidence.\n\n"
        "What to do — extract the release and re-run the derivations against "
        "it:\n\n"
        f"    {REGENERATE_COMMAND.format(version=actual_version)}\n\n"
        f"That run rewrites {FIXTURE_PATH.name} itself. If it FAILS, the "
        "provider's surface moved: fix the derived table in "
        "src/brichan/cli/opencode.py, not the test, and do not move the pin "
        "until it passes. Procedure and per-failure meanings: "
        'docs/guides/model-routing.md, "Moving the OpenCode version pin".\n\n'
        f"recorded digest: {recorded.get('surface_digest')}\n"
        f"actual digest:   {surface_digest()}\n\n"
        "Pasting the actual digest into the fixture by hand will silence this "
        "test without verifying anything. That is a deliberate, reviewable act; "
        "it is not the fix."
    )
