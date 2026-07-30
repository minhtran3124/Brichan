import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.lifecycle import (
    MUTABLE_PATHS,
    StateKind,
    doctor_lines,
    documented_footprint,
    initialize_project,
    inspect_project,
    status_lines,
)
from brichan.project import ProjectError, find_git_root, project_paths


class ProjectLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "target"
        self.root.mkdir()
        (self.root / ".git").mkdir()
        self.paths = project_paths(explicit=self.root)

    def snapshot(self):
        state = self.paths.state_root
        return {
            path.relative_to(state).as_posix(): path.read_bytes()
            for path in state.rglob("*")
            if path.is_file()
        }

    def test_project_discovery_and_explicit_root_contract(self):
        nested = self.root / "src" / "nested"
        nested.mkdir(parents=True)
        self.assertEqual(self.root.resolve(), find_git_root(nested))
        self.assertEqual(self.root.resolve(), find_git_root(explicit=self.root))
        with self.assertRaisesRegex(ProjectError, "not a Git repository root"):
            find_git_root(explicit=nested)

    def test_dry_run_has_zero_writes_and_apply_is_idempotent(self):
        unrelated = self.root / "AGENTS.md"
        unrelated.write_bytes(b"user instructions\n")

        code, lines = initialize_project(self.paths, apply=False)
        self.assertEqual(0, code)
        self.assertEqual("dry-run: zero writes", lines[0])
        self.assertFalse(self.paths.state_root.exists())
        self.assertEqual(b"user instructions\n", unrelated.read_bytes())

        code, _ = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        before = self.snapshot()
        self.assertEqual(set(documented_footprint()), set(before))

        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertTrue(lines[0].startswith("no changes:"))
        self.assertEqual(before, self.snapshot())
        self.assertEqual(b"user instructions\n", unrelated.read_bytes())

    def test_status_distinguishes_all_schema_v1_states(self):
        code, lines = status_lines(self.paths)
        self.assertEqual(1, code)
        self.assertTrue(lines[0].startswith("uninitialized:"))

        initialize_project(self.paths, apply=True)
        code, lines = status_lines(self.paths)
        self.assertEqual(0, code)
        self.assertTrue(lines[0].startswith("healthy:"))

        manifest_path = self.paths.state_root / "manifest.json"
        original = manifest_path.read_bytes()
        manifest_path.write_text("{", encoding="utf-8")
        code, lines = status_lines(self.paths)
        self.assertEqual(2, code)
        self.assertIn("malformed:", lines[0])

        payload = json.loads(original)
        payload["schema_version"] = 99
        manifest_path.write_text(json.dumps(payload), encoding="utf-8")
        inspection = inspect_project(self.paths)
        self.assertIs(StateKind.INCOMPATIBLE, inspection.kind)
        self.assertEqual(3, inspection.exit_code)

    def test_mutable_memory_can_change_but_managed_resources_cannot(self):
        initialize_project(self.paths, apply=True)
        memory = self.paths.state_root / MUTABLE_PATHS[0]
        memory.write_text("# User project index\n", encoding="utf-8")
        self.assertIs(StateKind.HEALTHY, inspect_project(self.paths).kind)

        bootstrap = self.paths.state_root / "policy/bootstrap.md"
        bootstrap.write_text("modified\n", encoding="utf-8")
        inspection = inspect_project(self.paths)
        self.assertIs(StateKind.MALFORMED, inspection.kind)
        self.assertIn("managed resource was modified", inspection.detail)

    def test_symlinked_state_and_dangling_state_are_malformed(self):
        dangling = self.root / "missing-state"
        self.paths.state_root.symlink_to(dangling, target_is_directory=True)
        inspection = inspect_project(self.paths)
        self.assertIs(StateKind.MALFORMED, inspection.kind)
        self.assertEqual(".brichan must not be a symlink", inspection.detail)
        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(2, code)
        self.assertIn(".brichan must not be a symlink", lines[0])
        self.assertFalse(dangling.exists())

        self.paths.state_root.unlink()
        initialize_project(self.paths, apply=True)
        real_state = self.root / "real-state"
        self.paths.state_root.rename(real_state)
        self.paths.state_root.symlink_to(real_state, target_is_directory=True)
        inspection = inspect_project(self.paths)
        self.assertIs(StateKind.MALFORMED, inspection.kind)
        self.assertEqual(".brichan must not be a symlink", inspection.detail)

    def test_symlinked_managed_mutable_and_parent_paths_are_malformed(self):
        initialize_project(self.paths, apply=True)
        bootstrap = self.paths.state_root / "policy/bootstrap.md"
        outside_bootstrap = self.root / "outside-bootstrap.md"
        outside_bootstrap.write_bytes(bootstrap.read_bytes())
        bootstrap.unlink()
        bootstrap.symlink_to(outside_bootstrap)
        inspection = inspect_project(self.paths)
        self.assertIs(StateKind.MALFORMED, inspection.kind)
        self.assertIn("symlinked file is forbidden: policy/bootstrap.md", inspection.detail)

        bootstrap.unlink()
        bootstrap.write_bytes(outside_bootstrap.read_bytes())
        memory = self.paths.state_root / MUTABLE_PATHS[0]
        outside_memory = self.root / "outside-memory.md"
        outside_memory.write_bytes(memory.read_bytes())
        memory.unlink()
        memory.symlink_to(outside_memory)
        inspection = inspect_project(self.paths)
        self.assertIs(StateKind.MALFORMED, inspection.kind)
        self.assertIn(
            f"symlinked file is forbidden: {MUTABLE_PATHS[0]}",
            inspection.detail,
        )

        memory.unlink()
        memory.write_bytes(outside_memory.read_bytes())
        policy = self.paths.state_root / "policy"
        outside_policy = self.root / "outside-policy"
        policy.rename(outside_policy)
        policy.symlink_to(outside_policy, target_is_directory=True)
        inspection = inspect_project(self.paths)
        self.assertIs(StateKind.MALFORMED, inspection.kind)
        self.assertIn("symlinked parent component is forbidden: policy", inspection.detail)

    def test_apply_filesystem_failure_returns_exit_two(self):
        with patch(
            "brichan.lifecycle.tempfile.TemporaryDirectory",
            side_effect=PermissionError("reviewer-denied"),
        ):
            code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(2, code)
        self.assertEqual(
            (
                f"initialization failed: {self.paths.state_root}: "
                "PermissionError: reviewer-denied"
            ),
            lines[0],
        )
        self.assertFalse(os.path.lexists(self.paths.state_root))

    def test_inaccessible_state_returns_stable_malformed_for_all_commands(self):
        self.paths.state_root.mkdir()
        denied = PermissionError(
            13,
            "state access denied",
            str(self.paths.state_root),
        )
        with patch("brichan.lifecycle.Path.lstat", side_effect=denied):
            inspection = inspect_project(self.paths)
            status_code, status_output = status_lines(self.paths)
            doctor_code, doctor_output = doctor_lines(self.paths)
            init_code, init_output = initialize_project(self.paths, apply=True)

        self.assertIs(StateKind.MALFORMED, inspection.kind)
        self.assertIn("cannot inspect project state", inspection.detail)
        self.assertIn("PermissionError: state access denied", inspection.detail)
        for code, output in (
            (status_code, status_output),
            (doctor_code, doctor_output),
            (init_code, init_output),
        ):
            self.assertEqual(2, code)
            self.assertIn("PermissionError: state access denied", "\n".join(output))

    def test_inaccessible_manifest_lstat_is_malformed_not_exception(self):
        initialize_project(self.paths, apply=True)
        manifest = self.paths.state_root / "manifest.json"
        original_lstat = Path.lstat

        def inaccessible_manifest(path):
            if path == manifest:
                raise PermissionError(13, "manifest access denied", str(path))
            return original_lstat(path)

        with patch(
            "brichan.lifecycle.Path.lstat",
            autospec=True,
            side_effect=inaccessible_manifest,
        ):
            inspection = inspect_project(self.paths)
            status_code, status_output = status_lines(self.paths)
            doctor_code, doctor_output = doctor_lines(self.paths)
            init_code, init_output = initialize_project(self.paths, apply=True)

        self.assertIs(StateKind.MALFORMED, inspection.kind)
        self.assertIn(str(manifest), inspection.detail)
        for code, output in (
            (status_code, status_output),
            (doctor_code, doctor_output),
            (init_code, init_output),
        ):
            self.assertEqual(2, code)
            self.assertIn("manifest access denied", "\n".join(output))

    def test_doctor_has_deterministic_dependency_exit(self):
        initialize_project(self.paths, apply=True)
        with patch("brichan.lifecycle.shutil.which", return_value=None):
            code, lines = doctor_lines(self.paths)
        self.assertEqual(4, code)
        self.assertEqual("codex: missing", lines[2])
        self.assertEqual("herdr: optional-missing", lines[3])

        def available(name):
            return f"/opt/fake/{name}"

        with patch("brichan.lifecycle.shutil.which", side_effect=available):
            code, lines = doctor_lines(self.paths)
        self.assertEqual(0, code)
        self.assertTrue(lines[2].startswith("codex: ok "))
        self.assertTrue(lines[3].startswith("herdr: ok "))


if __name__ == "__main__":
    unittest.main()
