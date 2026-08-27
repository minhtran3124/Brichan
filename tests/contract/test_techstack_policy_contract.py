"""The techstack operating contract must be delivered as real resources.

Packet acceptance, receipt placement, and the planning-reread gate are
coordinator policy: no production packet parser or acceptance helper exists.
The only thing that can regress silently is *delivery* — a frozen literal
dropped from one of the two policy surfaces, a resource that never reaches the
managed footprint, or a path that stops resolving. Every assertion here is
about delivery, never about resolver behavior, which the packet-1 through
packet-5 suites own.
"""

import ast
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.lifecycle import (  # noqa: E402
    CHECKOUT_POLICY_PATHS,
    DOCTOR_SCHEMA_VERSION,
    IMMUTABLE_PATHS,
    RESOURCE_PACKAGE,
    SCHEMA_VERSION,
    intended_manifest,
)

#: The local task dossier. Gitignored, so it is present on the author's
#: checkout only; the committed fixtures below carry its frozen blocks
#: everywhere else, and the one dossier-present test ties the two together.
DESIGN = (
    ROOT
    / "projects/brida-installable-tool/handoffs/TECHSTACK-001/design.md"
)
FIXTURES = ROOT / "tests/fixtures"
PACKET_FIXTURE = FIXTURES / "techstack_packet_block.md"
CHECKOUT_POLICY = ROOT / "docs/policy/techstacks.md"
PACKAGED_ROOT = ROOT / "src/brichan/resources/dogfood_v1"
PACKAGED_POLICY = PACKAGED_ROOT / "policy/techstacks.md"
PACKAGED_SKILL = PACKAGED_ROOT / "skills/herdr-orchestration"
CHECKOUT_SKILL = ROOT / ".agents/skills/herdr-orchestration"

#: The exact packet labels, in order, from design section 10. Compared to the
#: committed copy of that block rather than only retyped, so a drift in either
#: direction fails.
PACKET_BLOCK = """\
Techstack task ID: <task_id>
Techstack plan ID: <plan_id>
Techstack plan version: <plan_version>
Techstack attempt ID: <attempt_id>
Techstack as-of: <YYYY-MM-DD>
Techstack scope paths JSON: <scope_paths>
Techstack context chains JSON: <context_chains>
Techstack declared conflicts JSON: <declared_conflicts>
Techstack exception approvals JSON: <exception_approvals>
Techstack Snapshot JSON artifact: <repo-relative-path>
Techstack Snapshot SHA-256: <64-lowercase-hex>
Techstack selected files JSON: <selected-path-array>
Techstack acknowledged Context IDs JSON: <context-id-array>
Techstack required selected rule reads JSON: <selected-path-array>
Techstack verify command: brichan techstacks verify --project-root <QROOT> \
--snapshot-json <QPATH> --as-of <YYYY-MM-DD>
Techstack verification requirement: run-before-work
"""

#: Literals design sections 10 and 16 freeze. Each must survive byte for byte
#: on both policy surfaces; paraphrasing one is the regression this guards.
FROZEN_LITERALS = (
    "Techstack verification requirement: not-applicable",
    "Techstack verification acknowledgement: yes; snapshot_sha256=<digest>",
    "Techstack snapshot pointer: none; Techstack snapshot SHA-256: null",
    "pass; snapshot_sha256=<digest>",
    "pass; snapshot_sha256=null; status=not_applicable",
    "brichan techstacks verify --project-root <QROOT> --snapshot-json "
    "<QPATH> --as-of <YYYY-MM-DD>",
    "brichan techstacks resolve --project-root <QROOT> --input-json "
    "<QINPUT> --snapshot-directory <QDIR>",
    "196,608 bytes",
    "TASK_PACKET_BYTE_LIMIT",
    "<attempt-id>-<snapshot-sha256>.snapshot.json",
    ".brichan/project-memory/techstack-snapshots/<TASK-ID>",
)

#: The H3 planning-reread gate. Each entry is one requirement, so dropping any
#: single step from either surface fails rather than passing on the heading.
H3_MARKERS = (
    "re-resolve",
    "reread each",
    "plan worker",
    "latest digest",
    "semantically",
    "verify again before acceptance",
    "does not cure a plan that missed the final scope",
)

#: Publication safety rules from design sections 10 and 16: the retry bound and
#: the unmatched-attempt exclusion. Each surface states them in its own words,
#: so the markers are the shared wording rather than a whole sentence.
PUBLICATION_MARKERS = (
    "at most three drifted observations are retried",
    "no artifact is packetable",
    "only the selected artifact of a published resolution may enter a packet "
    "or a receipt",
)

#: The blocked/not-applicable stop. The checkout surface writes "a blocked or
#: not-applicable resolution stops" and the packaged one "blocked and
#: not-applicable resolutions stop"; both must keep the stop and its outcome.
STOP_RULE = re.compile(
    r"blocked (?:or|and) not-applicable resolutions? stops? with no new artifact"
)

#: Brichan, not a package helper, owns every refusal.
REFUSAL_MARKERS = (
    "not a package helper",
    "stale snapshot digest",
    "verification acknowledgement",
    "worker-authored exception approval",
    "plan acceptance before the mandatory reread",
)


def normalized(path: Path) -> str:
    """Read a document with whitespace runs collapsed.

    Both policy surfaces wrap at 80 columns, so prose markers must assert
    wording rather than line breaks. Frozen literals are asserted against the
    raw bytes separately.
    """

    return " ".join(path.read_text(encoding="utf-8").split())


class TechstackPolicyDeliveryTest(unittest.TestCase):
    """The two policy surfaces exist and carry the same frozen contract."""

    def setUp(self):
        self.checkout = CHECKOUT_POLICY.read_text(encoding="utf-8")
        self.packaged = PACKAGED_POLICY.read_text(encoding="utf-8")

    def test_both_policy_surfaces_are_real_files_under_their_own_root(self):
        self.assertTrue(CHECKOUT_POLICY.is_file(), CHECKOUT_POLICY)
        self.assertTrue(PACKAGED_POLICY.is_file(), PACKAGED_POLICY)
        # No alternate package-resource root may be introduced.
        self.assertEqual(RESOURCE_PACKAGE, "brichan.resources.dogfood_v1")
        self.assertEqual(
            PACKAGED_ROOT,
            ROOT / "src" / Path(RESOURCE_PACKAGE.replace(".", "/")),
        )

    def test_the_packet_block_appears_byte_for_byte_on_both_surfaces(self):
        for text, label in ((self.checkout, "checkout"), (self.packaged, "packaged")):
            self.assertIn(PACKET_BLOCK, text, label)

    def test_the_packet_block_matches_the_design_bytes(self):
        """The design is the authority; the policy may not drift from it.

        The committed fixture is the design's block byte for byte (frozen and
        checked against the dossier by `TechstackDesignFixtureTest`), so this
        runs on every checkout rather than only where the dossier is.
        """

        self.assertEqual(PACKET_FIXTURE.read_text(encoding="utf-8"), PACKET_BLOCK)

    def test_every_frozen_literal_survives_on_both_surfaces(self):
        for text, label in ((self.checkout, "checkout"), (self.packaged, "packaged")):
            for literal in FROZEN_LITERALS:
                self.assertIn(literal, text, f"{label}: {literal}")

    def test_the_checkout_surface_names_the_checkout_snapshot_directory(self):
        self.assertIn(
            "projects/<project-slug>/handoffs/<TASK-ID>/snapshots",
            self.checkout,
        )

    def test_each_packet_label_appears_exactly_once_in_the_block(self):
        labels = [line.split(":", 1)[0] for line in PACKET_BLOCK.splitlines()]
        self.assertEqual(16, len(labels))
        self.assertEqual(len(labels), len(set(labels)))

    def test_both_surfaces_state_the_planning_reread_gate(self):
        for path, label in (
            (CHECKOUT_POLICY, "checkout"),
            (PACKAGED_POLICY, "packaged"),
        ):
            text = normalized(path).lower()
            for marker in H3_MARKERS:
                self.assertIn(marker, text, f"{label}: {marker}")

    def test_both_surfaces_bound_publication_and_exclude_unmatched_attempts(self):
        for path, label in (
            (CHECKOUT_POLICY, "checkout"),
            (PACKAGED_POLICY, "packaged"),
        ):
            text = normalized(path).lower()
            for marker in PUBLICATION_MARKERS:
                self.assertIn(marker, text, f"{label}: {marker}")
            self.assertRegex(text, STOP_RULE, label)

    def test_both_surfaces_place_every_refusal_with_brichan(self):
        for path, label in (
            (CHECKOUT_POLICY, "checkout"),
            (PACKAGED_POLICY, "packaged"),
        ):
            text = normalized(path).lower()
            for marker in REFUSAL_MARKERS:
                self.assertIn(marker, text, f"{label}: {marker}")

    def test_both_surfaces_state_the_pipe_boundary_as_out_of_contract(self):
        for path, label in (
            (CHECKOUT_POLICY, "checkout"),
            (PACKAGED_POLICY, "packaged"),
        ):
            text = normalized(path)
            self.assertIn("exactly two columns", text, label)
            self.assertIn("out of contract for receipt embedding", text, label)
            self.assertIn("space, a single quote", text, label)

    def test_neither_surface_claims_a_production_packet_helper(self):
        for path, label in (
            (CHECKOUT_POLICY, "checkout"),
            (PACKAGED_POLICY, "packaged"),
        ):
            self.assertIn("no package helper", normalized(path).lower(), label)
        for forbidden in (
            "validate_task_packet",
            "parse_task_packet",
            "accept_packet",
        ):
            for text, label in (
                (self.checkout, "checkout"),
                (self.packaged, "packaged"),
            ):
                self.assertNotIn(forbidden, text, f"{label}: {forbidden}")

    def test_neither_surface_embeds_a_home_path(self):
        for text, label in ((self.checkout, "checkout"), (self.packaged, "packaged")):
            self.assertNotIn("/Users/", text, label)
            self.assertNotIn("/home/", text, label)


class TechstackResourceInventoryTest(unittest.TestCase):
    """The new resources must reach the managed footprint, not just the tree."""

    def test_the_packaged_policy_is_immutable_managed_state(self):
        self.assertIn("policy/techstacks.md", IMMUTABLE_PATHS)

    def test_the_packaged_handoff_receipt_reference_is_immutable(self):
        self.assertIn(
            "skills/herdr-orchestration/references/handoff-receipt.md",
            IMMUTABLE_PATHS,
        )
        self.assertTrue(
            (PACKAGED_SKILL / "references/handoff-receipt.md").is_file()
        )

    def test_the_immutable_skill_still_carries_the_task_packet(self):
        self.assertIn(
            "skills/herdr-orchestration/references/task-packet.md",
            IMMUTABLE_PATHS,
        )

    def test_the_checkout_policy_list_carries_the_new_policy(self):
        self.assertIn(("docs/policy/techstacks.md", "file"), CHECKOUT_POLICY_PATHS)

    def test_every_immutable_path_names_a_readable_packaged_resource(self):
        for relative in IMMUTABLE_PATHS:
            with self.subTest(relative=relative):
                resource = PACKAGED_ROOT / relative
                self.assertTrue(resource.is_file(), relative)
                self.assertTrue(resource.read_bytes(), relative)

    def test_the_intended_manifest_hashes_both_new_resources(self):
        manifest = intended_manifest()
        resources = manifest["resources"]
        for relative in (
            "policy/techstacks.md",
            "skills/herdr-orchestration/references/handoff-receipt.md",
        ):
            self.assertIn(relative, resources, relative)
            self.assertEqual(64, len(resources[relative]), relative)

    def test_the_state_and_report_schemas_are_unchanged(self):
        """Immutable additions force reinitialization, never a migration."""

        self.assertEqual(1, SCHEMA_VERSION)
        self.assertEqual(2, DOCTOR_SCHEMA_VERSION)


class TechstackPathInventoryTest(unittest.TestCase):
    """Every new path is classified and every declared reference resolves."""

    def setUp(self):
        self.manifest = json.loads(
            (ROOT / "config/repository-paths.json").read_text(encoding="utf-8")
        )
        self.entries = {entry["path"]: entry for entry in self.manifest["entries"]}

    def test_the_checkout_policy_is_classified_as_internal_policy(self):
        entry = self.entries["docs/policy/techstacks.md"]
        self.assertEqual("internal-policy", entry["category"])
        self.assertEqual("canonical", entry["policy"])

    def test_the_new_source_package_is_classified(self):
        for module in (
            "__init__",
            "model",
            "markdown",
            "filesystem",
            "safe_open_helper",
            "resolver",
            "cli",
        ):
            path = f"src/brichan/techstacks/{module}.py"
            self.assertIn(path, self.entries, path)
            self.assertEqual("canonical", self.entries[path]["policy"], path)

    def test_the_local_platform_evidence_scripts_are_classified(self):
        for name in (
            "scripts/verify_techstack_safe_open_linux.py",
            "scripts/verify_techstack_safe_open_macos.py",
        ):
            self.assertIn(name, self.entries, name)
            self.assertEqual("local-evidence", self.entries[name]["category"], name)

    def test_the_checkout_and_packaged_references_are_classified(self):
        for name in (
            ".agents/skills/herdr-orchestration/references/task-packet.md",
            ".agents/skills/herdr-orchestration/references/handoff-receipt.md",
            "src/brichan/resources/dogfood_v1/policy/techstacks.md",
            "src/brichan/resources/dogfood_v1/skills/herdr-orchestration"
            "/references/task-packet.md",
            "src/brichan/resources/dogfood_v1/skills/herdr-orchestration"
            "/references/handoff-receipt.md",
        ):
            self.assertIn(name, self.entries, name)

    def test_every_classified_path_exists(self):
        for path, entry in self.entries.items():
            with self.subTest(path=path):
                target = ROOT / path
                if entry["kind"] == "file":
                    self.assertTrue(target.is_file(), path)
                else:
                    self.assertTrue(target.is_dir(), path)

    def test_every_declared_reference_resolves_and_is_present(self):
        for reference in self.manifest["references"]:
            source = ROOT / reference["source"]
            target = reference["target"]
            with self.subTest(source=reference["source"], target=target):
                self.assertIn(target, self.entries, target)
                self.assertTrue((ROOT / target).exists(), target)
                needle = reference.get("needle", target)
                self.assertIn(needle, source.read_text(encoding="utf-8"))


#: The markdown anchors of the design blocks the fixtures copy: section 9's
#: registry table, section 14's frozen literal block, section 16's
#: cross-product table, and section 16's three version-9 rendered blocks.
SECTION_9_HEADER = "| Code | Exact detail |"
SECTION_14_HEADING = "### Exact doctor `agent_skill_export` details"
SECTION_16_HEADER = (
    "| detail_code in precedence order | status/relation | path | managed_path "
    "| files |"
)
SECTION_16_VERSION_9_CODES = (
    "OUTPUT_PATH_NOT_CANONICAL",
    "RESOURCE_LIMIT",
    "SKILL_ENTRY_NAME_BYTE_LIMIT",
)


def design_packet_block(text: str) -> str:
    """The fenced packet block of design section 10, without its fences."""

    lines = text.split("\n")
    start = lines.index("Techstack task ID: <task_id>")
    end = lines.index("```", start)
    return "\n".join(lines[start:end]) + "\n"


def design_table_block(text: str, header: str) -> str:
    """The markdown table introduced by `header`: header, rule, body rows."""

    lines = text.split("\n")
    start = lines.index(header)
    end = start + 2
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    return "\n".join(lines[start:end]) + "\n"


def design_fenced_block(text: str, anchor: str) -> str:
    """`anchor`, one blank line, and the first ```text fence after it.

    Anchored because section 14 states three fenced literal blocks in the
    same shape and section 16 states one rendered block per code.
    """

    lines = text.split("\n")
    start = lines.index(anchor)
    opened = lines.index("```text", start)
    end = lines.index("```", opened + 1)
    return "\n".join([anchor, "", *lines[opened : end + 1]]) + "\n"


def design_version_9_blocks(text: str) -> str:
    return "\n".join(
        design_fenced_block(text, f"`{code}`:") for code in SECTION_16_VERSION_9_CODES
    )


#: Each committed fixture, how it is cut from the design, and its frozen
#: SHA-256. A fixture may change only together with its digest here, and only
#: when the dossier-present test below agrees with the design.
DESIGN_FIXTURES = (
    (
        "techstack_packet_block.md",
        design_packet_block,
        "1af351f27906156630c5330aab250ff893daad70c34896b4e59c85649e8d7aaf",
    ),
    (
        "doctor_section_9_registry.md",
        lambda text: design_table_block(text, SECTION_9_HEADER),
        "5b616e5421b3aafbedab3b35eb4ac92f4c5b6759875bda07b9a34ec6bdaead7e",
    ),
    (
        "doctor_section_14_block.md",
        lambda text: design_fenced_block(text, SECTION_14_HEADING),
        "6f5889823b9568a960dd7ec89863ce6aa11e3c7ae60466afd48a55380ad1299d",
    ),
    (
        "doctor_section_16_rows.md",
        lambda text: design_table_block(text, SECTION_16_HEADER),
        "d187254bb81c796ac14859e34e079fae764dbf13e4b9b43ae5daf0842b02264b",
    ),
    (
        "doctor_section_16_version_9_blocks.md",
        design_version_9_blocks,
        "28947c96ff2898b61a4644b576eee2c05a49263bd39de9d0893ab36dc09c434f",
    ),
)

#: Committed fixtures that freeze bytes without being cut from the design, as
#: `(name, byte_count, sha256)`. `TEST-002` requires every byte-freezing
#: fixture to have its digest frozen by a contract test; the doctor text
#: fixture read by `tests.unit.test_cli_render` was the one that had none, so
#: a rendering change could rewrite it with nothing in the diff to review.
#: Changing the fixture now requires changing its row in the same diff.
FROZEN_FIXTURES = (
    (
        "doctor_v2_text.json",
        20863,
        "3b70cf771df54ef607c0812eab81a6ff047f1a102adb45935776f885df3cd1fa",
    ),
)


class TechstackDesignFixtureTest(unittest.TestCase):
    """The committed design blocks are frozen and, where possible, authentic.

    The packet block above and the three `AGENT_SKILL_EXPORT_DETAILS` parity
    assertions in `tests.unit.test_cli_render` read these fixtures instead of
    the gitignored dossier, so they gate every checkout and CI. The dossier
    itself remains the authority: wherever it is on disk, each fixture must be
    the block the design states, byte for byte.
    """

    def test_every_design_fixture_is_frozen_byte_for_byte(self):
        for name, _, digest in DESIGN_FIXTURES:
            with self.subTest(fixture=name):
                self.assertEqual(
                    digest,
                    hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest(),
                )

    def test_every_design_fixture_equals_its_design_block(self):
        """The only permitted skip: the dossier is local, the fixtures are not."""

        if not DESIGN.is_file():
            self.skipTest(
                "the TECHSTACK-001 design dossier is not on this checkout; "
                "the committed fixtures are its frozen copy"
            )
        design = DESIGN.read_text(encoding="utf-8")
        for name, extract, _ in DESIGN_FIXTURES:
            with self.subTest(fixture=name):
                self.assertEqual(
                    extract(design), (FIXTURES / name).read_text(encoding="utf-8")
                )


class TechstackPolicyIsDeliveryOnlyTest(unittest.TestCase):
    """This module proves delivery, never resolver behavior."""

    def test_no_resolver_module_is_imported_here(self):
        """Asserted over this module's own import graph, not over its text.

        A textual search would match the assertion itself, so the check reads
        the parsed imports instead.
        """

        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        self.assertFalse(
            {name for name in imported if name.startswith("brichan.techstacks")},
            imported,
        )

    def test_the_skill_surfaces_delegate_rather_than_restate_behavior(self):
        for skill, policy_pointer in (
            (CHECKOUT_SKILL, "docs/policy/techstacks.md"),
            (PACKAGED_SKILL, ".brichan/policy/techstacks.md"),
        ):
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(policy_pointer, text, str(skill))
            self.assertIn("techstacks/README.md", text, str(skill))


class FrozenFixtureDigestTest(unittest.TestCase):
    """Byte-frozen fixtures that no design block generates."""

    def test_every_frozen_fixture_matches_its_recorded_size_and_digest(self):
        for name, byte_count, digest in FROZEN_FIXTURES:
            with self.subTest(fixture=name):
                payload = (FIXTURES / name).read_bytes()
                self.assertEqual(byte_count, len(payload))
                self.assertEqual(digest, hashlib.sha256(payload).hexdigest())


class PackagedSkillExportRelationTest(unittest.TestCase):
    """The checkout export is a path superset of the packaged skill.

    `PACKAGED-001` requires marker parity for shared safeguards — owned by
    `tests.contract.test_skill_parity_contract` — and allows the checkout
    export to be a mode-specific superset that is not byte-identical to the
    installed-mode skill. The one relation that would be a real regression on
    this checkout is a packaged path missing from the export, the doctor's
    `EXPORT_MISSING` outcome. This asserts that containment only: never byte
    equality, and never inequality, so it stays true under any later
    mode-neutral rewrite of either tree. Its coverage distinct from the parity
    contract, which already detects the removal of any of today's four packaged
    files, is twofold: the path set is derived from `PACKAGED_SKILL.rglob`, so
    a packaged file added later is automatically required in the export; and a
    symlink standing in for a regular export file is rejected here while the
    parity contract reads through it.
    """

    def test_every_packaged_skill_path_exists_in_the_checkout_export(self):
        packaged = sorted(
            path.relative_to(PACKAGED_SKILL)
            for path in PACKAGED_SKILL.rglob("*")
            if path.is_file() and not path.is_symlink()
        )
        self.assertTrue(packaged, str(PACKAGED_SKILL))
        for relative in packaged:
            with self.subTest(path=str(relative)):
                exported = CHECKOUT_SKILL / relative
                self.assertTrue(
                    exported.is_file() and not exported.is_symlink(), str(exported)
                )


if __name__ == "__main__":
    unittest.main()
