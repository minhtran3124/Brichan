import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.check_repository_paths import (
    markdown_sources,
    unclassified_root_files,
)


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
            "config/model-routing.json": "canonical",
            "projects": "frozen",
            "evals": "frozen",
            "metrics": "frozen",
        }
        for path, policy in expected_policies.items():
            self.assertIn(path, entries)
            self.assertEqual(policy, entries[path]["policy"])

    def test_internal_policy_files_are_canonical_without_root_stubs(self):
        entries = {entry["path"]: entry for entry in self.manifest["entries"]}
        policy_names = (
            "identity.md",
            "operating-principles.md",
            "memory-policy.md",
            "model-catalog.md",
            "reviewer.md",
            "techstacks.md",
        )
        for path in policy_names:
            self.assertNotIn(path, entries)
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
        # A linked worktree's root `.git` is a file; it is git metadata.
        actual = {
            path.name
            for path in ROOT.iterdir()
            if path.is_file()
            and path.name != ".git"
            and path.name not in ignored
        }
        self.assertEqual(actual, inventoried)

    def test_a_worktree_git_file_is_not_an_unclassified_root_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").write_text(
                "gitdir: /elsewhere/.git/worktrees/x\n", encoding="utf-8"
            )
            (root / "AGENTS.md").write_text("", encoding="utf-8")
            self.assertEqual(
                [], unclassified_root_files(root, set(), {"AGENTS.md"})
            )

    def test_a_git_directory_is_not_an_unclassified_root_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            self.assertEqual([], unclassified_root_files(root, set(), set()))

    def test_other_unclassified_root_files_are_still_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in (".git", ".git.bak", "stray.txt", ".env", "AGENTS.md"):
                (root / name).write_text("", encoding="utf-8")
            self.assertEqual(
                [".git.bak", "stray.txt"],
                unclassified_root_files(root, {".env"}, {"AGENTS.md"}),
            )

    def test_the_techstack_surfaces_are_inventoried_with_real_targets(self):
        """Step 7 adds a policy, a source package, and two skill references.

        Each must be classified, and each declared reference must name an
        inventoried target that really contains its needle — a dangling
        pointer between the policy and the skills is the failure this owns.
        """

        entries = {entry["path"]: entry for entry in self.manifest["entries"]}
        for path in (
            "docs/policy/techstacks.md",
            "src/brichan/resources/dogfood_v1/policy/techstacks.md",
            "src/brichan/techstacks/resolver.py",
            "src/brichan/techstacks/safe_open_helper.py",
            "scripts/verify_techstack_safe_open_linux.py",
            "scripts/verify_techstack_safe_open_macos.py",
            ".agents/skills/herdr-orchestration/references/handoff-receipt.md",
            "src/brichan/resources/dogfood_v1/skills/herdr-orchestration"
            "/references/handoff-receipt.md",
        ):
            self.assertIn(path, entries, path)
            self.assertEqual("file", entries[path]["kind"], path)
            self.assertTrue((ROOT / path).is_file(), path)

        techstack_references = [
            reference
            for reference in self.manifest["references"]
            if reference["target"] == "docs/policy/techstacks.md"
        ]
        self.assertEqual(4, len(techstack_references))
        for reference in techstack_references:
            source = ROOT / reference["source"]
            self.assertIn(
                reference["needle"],
                source.read_text(encoding="utf-8"),
                reference["source"],
            )

    def test_the_techstack_eval_package_is_inventoried_with_real_targets(self):
        """Step 7 classifies the eval; step 9 is what makes it exist.

        The four package members evolve with the contract `make check` runs,
        so they are canonical regression tests. The eight fixture files are
        byte-frozen Design section 15 inputs, so they are frozen historical
        evidence. Removing any of the thirteen fails here.
        """

        entries = {entry["path"]: entry for entry in self.manifest["entries"]}
        package = "evals/techstack_context_v1"

        self.assertIn(package, entries)
        self.assertEqual("directory", entries[package]["kind"])
        self.assertEqual("regression-test", entries[package]["category"])
        self.assertEqual("canonical", entries[package]["policy"])
        self.assertTrue((ROOT / package).is_dir())

        for member in ("__init__.py", "README.md", "cases.json", "test_cases.py"):
            path = f"{package}/{member}"
            with self.subTest(path=path):
                self.assertIn(path, entries)
                self.assertEqual("file", entries[path]["kind"])
                self.assertEqual("regression-test", entries[path]["category"])
                self.assertEqual("canonical", entries[path]["policy"])
                self.assertTrue((ROOT / path).is_file())

        fixtures = (
            "base/techstacks/README.md",
            "base/techstacks/general.md",
            "base/techstacks/frontend/README.md",
            "base/techstacks/frontend/components/Button.md",
            "base/evidence/button.txt",
            "stale/techstacks/README.md",
            "stale/techstacks/stale.md",
            "stale/evidence/stale.txt",
        )
        self.assertEqual(8, len(fixtures))
        for member in fixtures:
            path = f"{package}/fixtures/{member}"
            with self.subTest(path=path):
                self.assertIn(path, entries)
                self.assertEqual("file", entries[path]["kind"])
                self.assertEqual("historical-evidence", entries[path]["category"])
                self.assertEqual("frozen", entries[path]["policy"])
                self.assertTrue((ROOT / path).is_file())

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
