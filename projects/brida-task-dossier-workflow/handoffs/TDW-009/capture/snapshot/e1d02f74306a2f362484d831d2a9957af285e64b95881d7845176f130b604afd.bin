import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.contracts.task_dossier.schema import (
    ARTIFACTS,
    BODY_SECTIONS,
    INDEX_IDENTITY_FIELDS,
    METADATA_FIELDS,
    METADATA_SECTION,
    INDEX_PROJECTION_SECTIONS,
    MEMORY_OWNED_SECTIONS,
    MINIMUM_EVIDENCE_ITEMS,
    RECEIPT_OWNED_FIELD_LABELS,
    RECEIPT_OWNED_SECTIONS,
)

TEMPLATES = ROOT / "docs/workflows/task-dossier/templates"
CONTRACT = ROOT / "docs/workflows/task-dossier.md"


class TaskDossierTemplateContractTest(unittest.TestCase):
    def test_every_standard_artifact_has_a_template(self):
        actual = sorted(path.name for path in TEMPLATES.glob("*.md"))
        self.assertEqual(sorted(f"{name}.md" for name in ARTIFACTS), actual)

    def test_templates_declare_the_full_evidence_contract(self):
        for artifact in ARTIFACTS:
            with self.subTest(artifact=artifact):
                text = (TEMPLATES / f"{artifact}.md").read_text(encoding="utf-8")
                self.assertIn(f"## {METADATA_SECTION}", text)
                for label in METADATA_FIELDS:
                    self.assertIn(f"- {label}:", text)
                for section in BODY_SECTIONS:
                    self.assertIn(f"## {section}", text)
                self.assertIn(f"- Artifact: `{artifact}`", text)
                self.assertNotIn("/Users/", text)
                self.assertNotIn("/home/", text)

    def test_index_template_links_authorities_without_duplicating_them(self):
        text = (TEMPLATES / "index.md").read_text(encoding="utf-8")
        self.assertIn("- Canonical receipt path:", text)
        self.assertIn("- Project memory path:", text)
        self.assertIn("- Accepted plan ID:", text)
        self.assertIn("- Accepted plan version:", text)
        self.assertIn("- Review route strength:", text)
        self.assertIn("- Ship authorization:", text)
        self.assertIn("| Artifact | Applicability | Phase state | Path |", text)
        for artifact in ARTIFACTS:
            self.assertIn(f"| `{artifact}` |", text)
        for owned in RECEIPT_OWNED_SECTIONS + MEMORY_OWNED_SECTIONS:
            self.assertNotIn(f"## {owned}", text)
        for label in RECEIPT_OWNED_FIELD_LABELS:
            self.assertNotIn(f"- {label}:", text)
        declared = re.findall(r"^## (.+)$", text, re.MULTILINE)
        self.assertEqual(list(INDEX_PROJECTION_SECTIONS), declared)

    def test_review_and_provenance_templates_carry_their_gates(self):
        request = (TEMPLATES / "request.md").read_text(encoding="utf-8")
        self.assertIn("- Redaction applied: `yes`", request)
        self.assertIn("- Mutability: `immutable`", request)

        plan = (TEMPLATES / "plan.md").read_text(encoding="utf-8")
        self.assertIn("- Plan ID:", plan)
        self.assertIn("- Plan status:", plan)

        for artifact in ("plan-review", "code-review"):
            text = (TEMPLATES / f"{artifact}.md").read_text(encoding="utf-8")
            self.assertIn("- Reviewed plan ID:", text)
            self.assertIn("- Reviewed plan version:", text)
            self.assertIn("- Owner: `reviewer`", text)

        pr_desc = (TEMPLATES / "pr-desc.md").read_text(encoding="utf-8")
        self.assertIn("- Remote action authorized: `no`", pr_desc)
        for forbidden in ("git push", "gh pr create", "gh pr merge"):
            self.assertNotIn(forbidden, pr_desc)


class TaskDossierDocumentationContractTest(unittest.TestCase):
    def setUp(self):
        self.contract = CONTRACT.read_text(encoding="utf-8")

    def test_index_template_carries_every_identity_field(self):
        text = (TEMPLATES / "index.md").read_text(encoding="utf-8")
        for label in INDEX_IDENTITY_FIELDS:
            self.assertIn(f"- {label}:", text)

    def test_contract_documents_the_remediated_gates(self):
        for needle in (
            "not an exemption from",
            "partial adoption",
            "must be exactly this task's",
            "Project memory path",
            "must record `not-requested`",
            "the plan to be `accepted`",
            "carry a `PASS` verdict",
            "including a dangling one",
            "created\nexclusively and without following links",
            "not a statement",
            "project-memory-owned one such as",
            "may declare only its projection",
            "Neither the reviewing session nor the",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.contract)

    def test_contract_documents_levels_states_and_authority(self):
        for needle in (
            "task level changes required\nevidence depth",
            "pending",
            "active",
            "passed",
            "not-required",
            "blocked",
            "routing-neutral",
            "canonical for delegated lifecycle evidence",
            "branch-independent",
        ):
            self.assertIn(needle, self.contract)

    def test_contract_states_documented_level_evidence_depth(self):
        for level, minimum in MINIMUM_EVIDENCE_ITEMS.items():
            self.assertRegex(
                self.contract,
                rf"\|\s*{level}\s*\|\s*{minimum}\s*\|",
                f"level {level} evidence depth is undocumented",
            )

    def test_canonical_policy_points_at_the_contract(self):
        sources = (
            "docs/index.md",
            "docs/workflows/README.md",
            "CONTRIBUTING.md",
            "docs/policy/operating-principles.md",
            "docs/policy/reviewer.md",
            ".agents/skills/herdr-orchestration/references/task-dossier.md",
        )
        for source in sources:
            with self.subTest(source=source):
                text = (ROOT / source).read_text(encoding="utf-8")
                self.assertIn("task-dossier.md", text)

        skill = (ROOT / ".agents/skills/herdr-orchestration/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("references/task-dossier.md", skill)

    def test_makefile_wires_the_validator_into_check(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("scripts/validate_task_dossiers.py projects", makefile)
        check = next(
            line for line in makefile.splitlines() if line.startswith("check:")
        )
        self.assertIn("dossiers", check)

    def test_repository_manifest_inventories_the_new_boundaries(self):
        manifest = json.loads(
            (ROOT / "config/repository-paths.json").read_text(encoding="utf-8")
        )
        entries = {entry["path"]: entry for entry in manifest["entries"]}
        for path in (
            "docs/workflows/task-dossier.md",
            "docs/workflows/task-dossier/templates",
            "scripts/validate_task_dossiers.py",
            "scripts/scaffold_task_dossier.py",
            "src/brichan/contracts/task_dossier/validation.py",
            "src/brichan/contracts/task_dossier/schema.py",
            "src/brichan/contracts/task_dossier/parser.py",
            "src/brichan/contracts/task_dossier/scaffold.py",
        ):
            self.assertIn(path, entries)


class TaskDossierRoutingNeutralityTest(unittest.TestCase):
    def test_routing_manifest_keeps_its_four_routes_and_no_workflow_keys(self):
        manifest = json.loads(
            (ROOT / "config/model-routing.json").read_text(encoding="utf-8")
        )
        self.assertEqual(1, manifest["schema_version"])
        self.assertEqual(
            {"plan", "implement", "review", "scan"}, set(manifest["routes"])
        )
        serialized = json.dumps(manifest).lower()
        for forbidden in ("dossier", "phase", "level", "artifact"):
            self.assertNotIn(forbidden, serialized)

    def test_dossier_contract_does_not_read_the_routing_manifest(self):
        package = ROOT / "src/brichan/contracts/task_dossier"
        for path in sorted(package.glob("*.py")):
            with self.subTest(module=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn("model-routing.json", source)
                self.assertNotIn("model_routing", source)

    def test_installed_resources_are_untouched_by_the_workflow(self):
        resources = ROOT / "src/brichan/resources/dogfood_v1"
        self.assertTrue(resources.is_dir())
        for path in sorted(resources.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            with self.subTest(resource=str(path.relative_to(ROOT))):
                self.assertNotIn(
                    "task-dossier", path.read_text(encoding="utf-8")
                )

    def test_dossier_artifacts_are_not_confused_with_receipts(self):
        validation = (
            ROOT / "src/brichan/contracts/task_dossier/validation.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("brichan.contracts.receipts", validation)
        self.assertTrue(
            re.search(r"handoffs/\*/index\.md", validation),
            "dossier discovery must key on index.md",
        )


if __name__ == "__main__":
    unittest.main()
