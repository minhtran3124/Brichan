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
            "scripts/generate_task_dossier.py",
            "scripts/summarize_task_dossier.py",
            "src/brichan/contracts/task_dossier/validation.py",
            "src/brichan/contracts/task_dossier/schema.py",
            "src/brichan/contracts/task_dossier/parser.py",
            "src/brichan/contracts/task_dossier/scaffold.py",
            "src/brichan/contracts/task_dossier/record.py",
            "src/brichan/contracts/task_dossier/generate.py",
            "src/brichan/contracts/task_dossier/summary.py",
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


DESIGN = (
    ROOT / "projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md"
)
CONCISE = ROOT / "evals/task-dossier-pilots/concise"

# The fixed declaration the evaluation must carry verbatim, on one line.
NON_AUTHORITATIVE_DECLARATION = (
    "These samples prove contract validity only; no verdict, session "
    "identifier, or identifier inequality anywhere under `concise/` is "
    "evidence of any real independent review."
)

# The exact ten frozen exclusions of the implementation-start capture map.
CAPTURE_EXCLUSIONS = (
    (".git", "directory prefix"),
    (".venv", "directory prefix"),
    (".pytest_cache", "directory prefix"),
    ("projects/brida-task-dossier-workflow/handoffs/TDW-009", "directory prefix"),
    ("projects/brida-task-dossier-workflow/handoffs/TDWPLAN-009", "directory prefix"),
    ("projects/brida-task-dossier-workflow/handoffs/TDWIMP-009", "directory prefix"),
    ("projects/brida-task-dossier-workflow/handoffs/TDWREV-009", "directory prefix"),
    ("__pycache__", "any path component"),
    (".DS_Store", "file name"),
    (".env", "file name"),
)


class TaskDossierRecordContractTest(unittest.TestCase):
    """The accepted design carries the fixture the generator is tested against."""

    def setUp(self):
        self.design = DESIGN.read_text(encoding="utf-8")

    def test_design_holds_exactly_one_fenced_record_with_eleven_artifacts(self):
        blocks = re.findall(
            r"^```json\n(.*?)^```$", self.design, re.MULTILINE | re.DOTALL
        )
        self.assertEqual(1, len(blocks))
        payload = json.loads(blocks[0])
        self.assertEqual(list(ARTIFACTS), list(payload["artifacts"]))
        for name, artifact in payload["artifacts"].items():
            with self.subTest(artifact=name):
                self.assertEqual(17, len(artifact))

    def test_design_holds_exactly_one_fenced_capture_block(self):
        blocks = re.findall(
            r"^```python\n(.*?)^```$", self.design, re.MULTILINE | re.DOTALL
        )
        capture = [block for block in blocks if "capture_map_version" in block]
        self.assertEqual(1, len(capture), "exactly one block defines the capture map")
        self.assertIn("CAPTURE_MAP_VERSION = 1", capture[0])
        self.assertIn("ALLOWLIST_MODIFIED", capture[0])
        self.assertIn("ALLOWLIST_NEW", capture[0])

    def test_the_capture_exclusion_set_is_exactly_the_documented_ten(self):
        table = re.findall(
            r"^\| `([^`]+)` \| ([a-z ]+) \|", self.design, re.MULTILINE
        )
        documented = [
            (value, kind.strip())
            for value, kind in table
            if kind.strip() in {"directory prefix", "any path component", "file name"}
        ]
        self.assertEqual(list(CAPTURE_EXCLUSIONS), documented)
        self.assertEqual(10, len(documented))

    def test_the_schema_constants_back_the_validator_literal(self):
        from brichan.contracts.task_dossier import validation
        from brichan.contracts.task_dossier.schema import (
            ARTIFACT_EXTRA_SECTIONS,
            ARTIFACT_OWNERS,
            ARTIFACT_TITLES,
            RECORD_SCHEMA_VERSION,
        )

        self.assertIs(validation.EXTRA_SECTION_FIELDS, ARTIFACT_EXTRA_SECTIONS)
        self.assertEqual(1, RECORD_SCHEMA_VERSION)
        self.assertEqual(set(ARTIFACTS), set(ARTIFACT_TITLES))
        self.assertEqual(set(ARTIFACTS), set(ARTIFACT_OWNERS))
        for artifact in ARTIFACTS:
            with self.subTest(artifact=artifact):
                template = (TEMPLATES / f"{artifact}.md").read_text(encoding="utf-8")
                self.assertTrue(
                    template.startswith(f"# {ARTIFACT_TITLES[artifact]}\n"),
                    f"{artifact} title drifted from its template",
                )
                self.assertIn(f"- Owner: `{ARTIFACT_OWNERS[artifact]}`", template)


class ConciseEvaluationContractTest(unittest.TestCase):
    """The evaluation samples must stay unmistakably synthetic."""

    def test_every_record_session_identity_is_marked_synthetic(self):
        for name in ("SYNTH-010", "SYNTH-011"):
            with self.subTest(record=name):
                payload = json.loads(
                    (CONCISE / "records" / f"{name}.record.json").read_text(
                        encoding="utf-8"
                    )
                )
                sessions = []
                for artifact in payload["artifacts"].values():
                    sessions.extend(
                        artifact[key]
                        for key in ("authoring_session", "reviewing_session")
                        if artifact[key] is not None
                    )
                self.assertTrue(sessions)
                for session in sessions:
                    self.assertTrue(
                        session.startswith("synthetic-fixture-"), session
                    )

    def test_every_sample_artifact_claims_it_is_non_authoritative(self):
        for name in ("SYNTH-010", "SYNTH-011"):
            payload = json.loads(
                (CONCISE / "records" / f"{name}.record.json").read_text(
                    encoding="utf-8"
                )
            )
            for artifact_name, artifact in payload["artifacts"].items():
                with self.subTest(record=name, artifact=artifact_name):
                    self.assertIn(
                        "Synthetic non-authoritative fixture data",
                        artifact["claim"],
                    )

    def test_results_carry_the_fixed_non_authoritative_declaration(self):
        text = (CONCISE / "results.md").read_text(encoding="utf-8")
        self.assertIn(NON_AUTHORITATIVE_DECLARATION, text)
        for needle in (
            "prove contract validity only",
            "point-in-time observations",
            "None is estimated.",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_every_sample_carries_eleven_artifacts_and_a_receipt(self):
        for project, task in (
            ("synthetic-level0", "SYNTH-010"),
            ("synthetic-level1", "SYNTH-011"),
        ):
            with self.subTest(task=task):
                dossier = CONCISE / "projects" / project / "handoffs" / task
                for artifact in ARTIFACTS:
                    self.assertTrue((dossier / f"{artifact}.md").is_file(), artifact)
                self.assertTrue((dossier / "receipt.md").is_file())
                self.assertTrue(
                    (CONCISE / "projects" / project / "current-state.md").is_file()
                )

    def test_the_recorded_pilot_results_are_not_modified(self):
        text = (ROOT / "evals/task-dossier-pilots/results.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("| Level 0 | 639 | 1 |", text)
        self.assertIn("| Level 1 | 716 | 86 |", text)


if __name__ == "__main__":
    unittest.main()
