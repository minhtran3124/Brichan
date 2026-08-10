"""Checked-in repository contract for durable project-memory consistency."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "config/repository-paths.json"
MAKEFILE = ROOT / "Makefile"


class ProjectMemoryContractTest(unittest.TestCase):
    def test_checked_in_repository_memory_passes(self):
        result = subprocess.run(
            [sys.executable, "scripts/check_project_memory.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertIn("project memory consistent: 7 indexed projects", result.stdout)

    def test_makefile_wires_memory_check_into_the_full_gate(self):
        makefile = MAKEFILE.read_text(encoding="utf-8")
        self.assertIn("memory-check:\n\t$(PYTHON) scripts/check_project_memory.py", makefile)
        self.assertIn("receipts dossiers memory-check path-check", makefile)
        self.assertIn("make memory-check", makefile)

    def test_path_manifest_inventories_checker_and_makefile_reference(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        entries = {entry["path"]: entry for entry in manifest["entries"]}
        self.assertEqual(
            {
                "path": "scripts/check_project_memory.py",
                "kind": "file",
                "category": "structure-guard",
                "policy": "stable-path",
            },
            entries["scripts/check_project_memory.py"],
        )
        references = [
            reference
            for reference in manifest["references"]
            if reference.get("target") == "scripts/check_project_memory.py"
        ]
        self.assertEqual(
            [{"source": "Makefile", "target": "scripts/check_project_memory.py"}],
            references,
        )

    def test_seven_lifecycle_values_are_correct_by_project_name(self):
        expected = {
            "brida-installable-tool": "active",
            "brida-system-validation": "complete",
            "brida-workflow-evaluation": "complete",
            "brida-claude-code-support": "active",
            "brida-repository-structure-refactor": "complete",
            "brida-model-routing": "complete",
            "brida-task-dossier-workflow": "active",
        }
        actual = {}
        for slug in expected:
            overview = (ROOT / "projects" / slug / "overview.md").read_text(
                encoding="utf-8"
            )
            values = [
                line.removeprefix("- Lifecycle status: ").strip(" `")
                for line in overview.splitlines()
                if line.startswith("- Lifecycle status:")
            ]
            self.assertEqual(1, len(values), slug)
            actual[slug] = values[0]
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
