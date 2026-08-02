import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.contracts.task_dossier import scaffold as scaffold_module
from brichan.contracts.task_dossier.schema import ARTIFACTS
from brichan.contracts.task_dossier.scaffold import (
    apply_scaffold,
    dossier_path,
    plan_scaffold,
)


class TaskDossierWorkflowIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.checkout = Path(self.temporary_directory.name)
        self.projects = self.checkout / "projects"
        self.dossier = self.projects / "example" / "handoffs" / "TASK-001"
        self.dossier.mkdir(parents=True)

    def run_script(self, script, *arguments):
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), *arguments],
            cwd=self.checkout,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_scaffold_dry_run_writes_nothing(self):
        actions = plan_scaffold(
            self.dossier, "TASK-001", "1", "example", repository_root=ROOT
        )
        self.assertEqual(
            len(ARTIFACTS),
            sum(1 for action in actions if action.action == "create"),
        )
        self.assertEqual([], sorted(self.dossier.iterdir()))

    def test_scaffold_apply_creates_the_complete_dossier(self):
        apply_scaffold(self.dossier, "TASK-001", "1", "example", repository_root=ROOT)
        written = sorted(path.name for path in self.dossier.glob("*.md"))
        self.assertEqual(sorted(f"{name}.md" for name in ARTIFACTS), written)
        index = (self.dossier / "index.md").read_text(encoding="utf-8")
        self.assertIn("- Task ID: `TASK-001`", index)
        self.assertIn("- Task level: `1`", index)
        self.assertIn("- Project: `example`", index)
        self.assertFalse((self.dossier / "receipt.md").exists())

    def test_scaffold_preserves_existing_artifacts(self):
        existing = self.dossier / "design.md"
        existing.write_text("# my design\n", encoding="utf-8")
        actions = apply_scaffold(
            self.dossier, "TASK-001", "1", "example", repository_root=ROOT
        )
        self.assertEqual("# my design\n", existing.read_text(encoding="utf-8"))
        preserved = [
            action for action in actions if action.path == existing
        ]
        self.assertEqual(["preserve"], [action.action for action in preserved])

    def test_scaffolded_placeholders_fail_validation(self):
        apply_scaffold(self.dossier, "TASK-001", "1", "example", repository_root=ROOT)
        result = self.run_script("validate_task_dossiers.py", "projects")
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("Invalid task dossiers", result.stderr)
        self.assertIn("canonical receipt does not exist", result.stderr)

    def test_validator_wrapper_accepts_a_checkout_without_dossiers(self):
        result = self.run_script("validate_task_dossiers.py", "projects")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Validated 0 task dossier(s)", result.stdout)

    def test_scaffold_wrapper_defaults_to_a_dry_run(self):
        result = self.run_script(
            "scaffold_task_dossier.py",
            "TASK-002",
            "--level",
            "0",
            "--project",
            "example",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("planned 11 task-dossier artifact(s)", result.stdout)
        self.assertFalse(
            (self.projects / "example" / "handoffs" / "TASK-002").exists()
        )

    def test_scaffold_wrapper_rejects_an_unstable_task_id(self):
        result = self.run_script(
            "scaffold_task_dossier.py",
            "feature-branch",
            "--level",
            "0",
            "--project",
            "example",
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("branch-independent", result.stderr)

    # --- review remediation: finding 1, scaffold containment and symlinks ---

    def test_scaffold_rejects_a_project_slug_that_escapes_the_root(self):
        for slug in ("../escaped", "..", "Example", "a/b", "example/../.."):
            with self.subTest(slug=slug):
                with self.assertRaises(ValueError) as error:
                    dossier_path(self.projects, slug, "TASK-001")
                self.assertIn("lowercase hyphenated slug", str(error.exception))

    def test_scaffold_path_stays_inside_the_projects_root(self):
        resolved = dossier_path(self.projects, "example", "TASK-001")
        self.assertEqual(self.dossier.resolve(), resolved.resolve())

    def test_scaffold_wrapper_rejects_an_escaping_project_and_writes_nothing(self):
        outside = self.checkout / "escaped"
        outside.mkdir()
        result = self.run_script(
            "scaffold_task_dossier.py",
            "TASK-003",
            "--level",
            "0",
            "--project",
            "../escaped",
            "--apply",
        )
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("lowercase hyphenated slug", result.stderr)
        self.assertEqual([], sorted(outside.iterdir()))

    def test_scaffold_refuses_to_write_through_a_dangling_symlink(self):
        escape_target = self.checkout / "outside.md"
        (self.dossier / "design.md").symlink_to(escape_target)
        self.assertFalse(escape_target.exists())

        with self.assertRaises(ValueError) as error:
            plan_scaffold(
                self.dossier, "TASK-001", "1", "example", repository_root=ROOT
            )
        self.assertIn("symlinked artifact", str(error.exception))

        with self.assertRaises(ValueError):
            apply_scaffold(
                self.dossier, "TASK-001", "1", "example", repository_root=ROOT
            )
        self.assertFalse(escape_target.exists())
        # The rejection happens before any write, so no other artifact appears.
        self.assertEqual(["design.md"], sorted(p.name for p in self.dossier.iterdir()))

    def test_scaffold_refuses_to_write_through_a_resolving_symlink(self):
        escape_target = self.checkout / "outside.md"
        escape_target.write_text("original\n", encoding="utf-8")
        (self.dossier / "brief.md").symlink_to(escape_target)

        with self.assertRaises(ValueError):
            apply_scaffold(
                self.dossier, "TASK-001", "1", "example", repository_root=ROOT
            )
        self.assertEqual("original\n", escape_target.read_text(encoding="utf-8"))
        self.assertEqual(["brief.md"], sorted(p.name for p in self.dossier.iterdir()))

    def test_scaffold_rejects_a_symlinked_dossier_directory(self):
        linked = self.projects / "example" / "handoffs" / "TASK-004"
        linked.symlink_to(self.dossier, target_is_directory=True)
        with self.assertRaises(ValueError) as error:
            plan_scaffold(linked, "TASK-004", "0", "example", repository_root=ROOT)
        self.assertIn("must not be a symlink", str(error.exception))

    def test_scaffolded_index_links_the_canonical_authorities(self):
        apply_scaffold(self.dossier, "TASK-001", "1", "example", repository_root=ROOT)
        index = (self.dossier / "index.md").read_text(encoding="utf-8")
        self.assertIn(
            "- Canonical receipt path: `projects/example/handoffs/TASK-001/receipt.md`",
            index,
        )
        self.assertIn(
            "- Project memory path: `projects/example/current-state.md`", index
        )

    # --- second re-review: residual 2, write-after-plan race ---

    def _race(self, create):
        """Run the real renderer, but let a writer land between plan and write.

        ``_render`` is called only in the write loop, once per planned create,
        in ARTIFACTS order. Creating the collision on the first call reproduces
        a file appearing after planning but before its own write.
        """
        original = scaffold_module._render
        state = {"fired": False}

        def racing_render(*arguments, **keywords):
            if not state["fired"]:
                state["fired"] = True
                create()
            return original(*arguments, **keywords)

        return mock.patch.object(
            scaffold_module, "_render", side_effect=racing_render
        )

    def test_apply_never_overwrites_a_file_created_after_planning(self):
        target = self.dossier / "brief.md"

        def concurrent_writer():
            target.write_text("written by another writer\n", encoding="utf-8")

        with self._race(concurrent_writer):
            actions = apply_scaffold(
                self.dossier, "TASK-001", "1", "example", repository_root=ROOT
            )

        self.assertEqual(
            "written by another writer\n", target.read_text(encoding="utf-8")
        )
        collided = [action for action in actions if action.path == target]
        self.assertEqual(["preserve"], [action.action for action in collided])
        self.assertIn("appeared after planning", collided[0].reason)
        # Every other artifact is still scaffolded; the collision is contained.
        self.assertEqual(
            sorted(f"{name}.md" for name in ARTIFACTS),
            sorted(path.name for path in self.dossier.glob("*.md")),
        )

    def test_apply_never_follows_a_symlink_created_after_planning(self):
        escape_target = self.checkout / "outside.md"
        escape_target.write_text("original\n", encoding="utf-8")
        link = self.dossier / "brief.md"

        def concurrent_symlink():
            link.symlink_to(escape_target)

        with self._race(concurrent_symlink):
            with self.assertRaises(ValueError) as error:
                apply_scaffold(
                    self.dossier, "TASK-001", "1", "example", repository_root=ROOT
                )

        self.assertIn("symlinked artifact", str(error.exception))
        self.assertEqual("original\n", escape_target.read_text(encoding="utf-8"))
        self.assertTrue(link.is_symlink())

    def test_apply_is_idempotent_and_never_rewrites_its_own_output(self):
        apply_scaffold(self.dossier, "TASK-001", "1", "example", repository_root=ROOT)
        stamped = {
            path.name: path.read_text(encoding="utf-8")
            for path in self.dossier.glob("*.md")
        }
        actions = apply_scaffold(
            self.dossier, "TASK-001", "1", "example", repository_root=ROOT
        )
        self.assertEqual(
            [], [action for action in actions if action.action == "create"]
        )
        for name, text in stamped.items():
            self.assertEqual(
                text, (self.dossier / name).read_text(encoding="utf-8"), name
            )

    def test_repository_checkout_validates_clean(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_task_dossiers.py"), "projects"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
