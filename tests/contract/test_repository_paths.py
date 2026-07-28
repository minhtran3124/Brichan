import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.check_repository_paths import markdown_sources


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "config/repository-paths.json"


class RepositoryPathContractTest(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_approved_boundaries_are_inventoried(self):
        entries = {entry["path"]: entry for entry in self.manifest["entries"]}
        expected_policies = {
            "AGENTS.md": "permanent-root",
            "CLAUDE.md": "permanent-root",
            "CONTRIBUTING.md": "retain-root-first-migration",
            "SECURITY.md": "retain-root-first-migration",
            "projects": "frozen",
            "evals": "frozen",
            "metrics": "frozen",
        }
        for path, policy in expected_policies.items():
            self.assertIn(path, entries)
            self.assertEqual(policy, entries[path]["policy"])

    def test_internal_policy_files_have_canonical_docs_and_root_stubs(self):
        entries = {entry["path"]: entry for entry in self.manifest["entries"]}
        policy_names = (
            "identity.md",
            "operating-principles.md",
            "memory-policy.md",
            "model-catalog.md",
            "reviewer.md",
        )
        for path in policy_names:
            self.assertEqual(
                "one-release",
                entries[path]["policy"],
            )
            self.assertEqual(
                "canonical",
                entries[f"docs/policy/{path}"]["policy"],
            )

    def test_every_non_ephemeral_root_file_is_classified(self):
        ignored = set(self.manifest["ignored_root_files"])
        inventoried = {
            entry["path"]
            for entry in self.manifest["entries"]
            if entry["kind"] == "file"
            and len(Path(entry["path"]).parts) == 1
        }
        actual = {
            path.name
            for path in ROOT.iterdir()
            if path.is_file() and path.name not in ignored
        }
        self.assertEqual(actual, inventoried)

    def test_current_path_and_link_contracts_pass(self):
        result = subprocess.run(
            [sys.executable, "scripts/check_repository_paths.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("repository paths valid:", result.stdout)

    def test_ignored_markdown_is_not_scanned(self):
        relative_sources = {
            path.relative_to(ROOT).as_posix()
            for path in markdown_sources()
        }
        self.assertFalse(
            any(path.startswith("internal-docs/") for path in relative_sources)
        )
        self.assertIn("docs/index.md", relative_sources)


if __name__ == "__main__":
    unittest.main()
