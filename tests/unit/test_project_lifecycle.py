import ast
import builtins
import contextlib
import errno
import inspect
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unicodedata
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan import lifecycle
from brichan.lifecycle import (
    AGENT_ENTRY_PATHS,
    AGENT_SKILLS_DIR,
    AGENT_SKILL_EXPORT_DETAILS,
    AGENT_SKILL_EXPORT_FILE_DETAILS,
    AGENT_SKILL_EXPORT_ROWS,
    CHECKOUT_MEMORY_PATHS,
    CHECKOUT_POLICY_PATHS,
    DOCTOR_SCHEMA_VERSION,
    EXIT_CODES,
    Inspection,
    MANAGED_SKILL_DIR,
    MUTABLE_PATHS,
    ROUTING_RELATIVE_PATH,
    StateKind,
    doctor_lines,
    doctor_report,
    documented_footprint,
    initialize_project,
    inspect_project,
    status_lines,
)
from brichan.project import ProjectError, ProjectPaths, find_git_root, project_paths
from brichan.techstacks import filesystem as techstack_filesystem
from brichan.techstacks import model as techstack_model


REPORT_KEYS = {
    "schema_version",
    "ok",
    "agent_skill_export",
    "repository",
    "git",
    "policies",
    "model_routing",
    "project_memory",
    "dependencies",
}
STATUSES = {"ok", "missing", "invalid", "unavailable"}
EXPORT_RELATIONS = {
    "not_applicable",
    "managed_state_unavailable",
    "current",
    "missing",
    "stale",
    "extra",
    "comparison_unavailable",
}
SIDE_STATUSES = {
    "regular",
    "absent",
    "unsafe",
    "unreadable",
    "over_limit",
    "not_checked",
}


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
        self.assertEqual("herdr: missing", lines[3])

        def available(name):
            return f"/opt/fake/{name}"

        with patch("brichan.lifecycle.shutil.which", side_effect=available):
            code, lines = doctor_lines(self.paths)
        self.assertEqual(0, code)
        self.assertTrue(lines[2].startswith("codex: ok "))
        self.assertTrue(lines[3].startswith("herdr: ok "))


class AgentEntryFilesTest(unittest.TestCase):
    """`init` provisions root AGENTS.md/CLAUDE.md pointers, never edits them."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "target"
        self.root.mkdir()
        (self.root / ".git").mkdir()
        self.paths = project_paths(explicit=self.root)

    def test_agent_entry_contract_names_both_runtime_files(self):
        self.assertEqual(("AGENTS.md", "CLAUDE.md"), AGENT_ENTRY_PATHS)

    def test_dry_run_lists_missing_agent_entries_without_writing(self):
        code, lines = initialize_project(self.paths, apply=False)
        self.assertEqual(0, code)
        self.assertIn("create AGENTS.md", lines)
        self.assertIn("create CLAUDE.md", lines)
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertFalse((self.root / "CLAUDE.md").exists())

    def test_apply_creates_missing_agent_entries_pointing_at_state(self):
        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertIn("create AGENTS.md", lines)
        self.assertIn("create CLAUDE.md", lines)
        for name in AGENT_ENTRY_PATHS:
            content = (self.root / name).read_text(encoding="utf-8")
            self.assertIn(".brichan/policy/bootstrap.md", content, name)
        self.assertIs(StateKind.HEALTHY, inspect_project(self.paths).kind)

    def test_existing_agent_entry_is_kept_and_missing_one_is_added(self):
        agents = self.root / "AGENTS.md"
        agents.write_bytes(b"user instructions\n")

        code, lines = initialize_project(self.paths, apply=False)
        self.assertEqual(0, code)
        self.assertNotIn("create AGENTS.md", lines)
        self.assertIn("create CLAUDE.md", lines)

        code, _ = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertEqual(b"user instructions\n", agents.read_bytes())
        self.assertTrue((self.root / "CLAUDE.md").is_file())

    def test_healthy_project_gains_missing_agent_entries_on_reinit(self):
        initialize_project(self.paths, apply=True)
        (self.root / "CLAUDE.md").unlink()

        code, lines = initialize_project(self.paths, apply=False)
        self.assertEqual(0, code)
        self.assertIn("create CLAUDE.md", lines)
        self.assertFalse((self.root / "CLAUDE.md").exists())

        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertIn("create CLAUDE.md", lines)
        self.assertTrue((self.root / "CLAUDE.md").is_file())

        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertTrue(lines[0].startswith("no changes:"))
        self.assertNotIn("create CLAUDE.md", lines)

    def test_symlinked_agent_entry_is_treated_as_present_and_untouched(self):
        outside = self.root / "outside.md"
        link = self.root / "CLAUDE.md"
        link.symlink_to(outside)

        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertNotIn("create CLAUDE.md", lines)
        self.assertTrue(link.is_symlink())
        self.assertFalse(outside.exists())


class AgentSkillsExportTest(unittest.TestCase):
    """`init` exports the Herdr skill for direct codex runs."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "target"
        self.root.mkdir()
        (self.root / ".git").mkdir()
        self.paths = project_paths(explicit=self.root)

    def test_skill_export_contract_names_the_codex_discovery_dir(self):
        self.assertEqual(".agents/skills/herdr-orchestration", AGENT_SKILLS_DIR)

    def test_default_dry_run_lists_missing_skill_export_without_writing(self):
        code, lines = initialize_project(self.paths, apply=False)
        self.assertEqual(0, code)
        self.assertIn("create .agents/skills/herdr-orchestration/SKILL.md", lines)
        self.assertIn(
            "create .agents/skills/herdr-orchestration/references/commands.md",
            lines,
        )
        self.assertIn(
            "create .agents/skills/herdr-orchestration/references/task-packet.md",
            lines,
        )
        self.assertFalse((self.root / ".agents").exists())

    def test_apply_exports_the_skill_byte_identical_to_managed_state(self):
        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertIn("create .agents/skills/herdr-orchestration/SKILL.md", lines)
        exported = self.root / AGENT_SKILLS_DIR / "SKILL.md"
        managed = self.paths.state_root / "skills/herdr-orchestration/SKILL.md"
        self.assertEqual(managed.read_bytes(), exported.read_bytes())
        self.assertIs(StateKind.HEALTHY, inspect_project(self.paths).kind)

    def test_existing_skill_export_is_never_touched(self):
        existing = self.root / AGENT_SKILLS_DIR
        existing.mkdir(parents=True)
        marker = existing / "SKILL.md"
        marker.write_bytes(b"user skill\n")

        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertNotIn(
            "create .agents/skills/herdr-orchestration/SKILL.md", lines
        )
        self.assertEqual(b"user skill\n", marker.read_bytes())

    def test_healthy_project_gains_missing_skill_export_on_reinit(self):
        initialize_project(self.paths, apply=True)
        exported = self.root / AGENT_SKILLS_DIR
        shutil.rmtree(exported)

        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertIn("create .agents/skills/herdr-orchestration/SKILL.md", lines)
        self.assertTrue((self.root / AGENT_SKILLS_DIR / "SKILL.md").is_file())

        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertTrue(lines[0].startswith("no changes:"))

    def test_existing_agents_skills_are_preserved_while_export_is_added(self):
        other_skill = self.root / ".agents/skills/user-skill/SKILL.md"
        other_skill.parent.mkdir(parents=True)
        other_skill.write_bytes(b"user skill\n")

        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertIn("create .agents/skills/herdr-orchestration/SKILL.md", lines)
        self.assertEqual(b"user skill\n", other_skill.read_bytes())
        self.assertTrue((self.root / AGENT_SKILLS_DIR / "SKILL.md").is_file())

    def test_symlinked_agents_directory_cannot_redirect_the_export(self):
        outside = self.root.parent / "outside-agents"
        outside.mkdir()
        (self.root / ".agents").symlink_to(outside, target_is_directory=True)

        code, lines = initialize_project(self.paths, apply=True)

        self.assertEqual(2, code)
        self.assertTrue(lines[0].startswith("initialization failed:"), lines)
        self.assertFalse(
            (outside / "skills/herdr-orchestration/SKILL.md").exists()
        )

    def test_symlinked_skills_directory_cannot_redirect_the_export(self):
        agents = self.root / ".agents"
        outside = self.root.parent / "outside-skills"
        agents.mkdir()
        outside.mkdir()
        (agents / "skills").symlink_to(outside, target_is_directory=True)

        code, lines = initialize_project(self.paths, apply=True)

        self.assertEqual(2, code)
        self.assertTrue(lines[0].startswith("initialization failed:"), lines)
        self.assertFalse((outside / "herdr-orchestration/SKILL.md").exists())

    def test_cli_default_exports_the_skill(self):
        from brichan.cli import runtime as cli_runtime

        with contextlib.redirect_stdout(io.StringIO()):
            code = cli_runtime.main(
                ["init", "--apply", "--project", str(self.root)]
            )
        self.assertEqual(0, code)
        self.assertTrue((self.root / AGENT_SKILLS_DIR / "SKILL.md").is_file())

    def test_removed_cli_flag_is_rejected(self):
        from brichan.cli import runtime as cli_runtime

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as caught:
                cli_runtime.main(
                    ["init", "--init-agents", "--project", str(self.root)]
                )
        self.assertEqual(2, caught.exception.code)
        self.assertIn(
            "unrecognized arguments: --init-agents", stderr.getvalue()
        )
        self.assertFalse((self.root / ".agents").exists())


class DoctorReportTest(unittest.TestCase):
    """`doctor --json` is read-only, exactly shaped, and exit-stable."""

    @classmethod
    def setUpClass(cls):
        cls.git = shutil.which("git")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.temp_path = Path(self.temporary.name)

    # -- fixtures ---------------------------------------------------------

    def git_repository(self, root: Path) -> Path:
        if self.git is None:
            self.skipTest("git executable is not available")
        root.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [self.git, "init", "--quiet", str(root)],
            check=True,
            capture_output=True,
            text=True,
        )
        return root

    def source_checkout(self) -> Path:
        """A minimal checkout that satisfies the source-mode contract."""

        root = self.git_repository(self.temp_path / "checkout")
        for relative_path, kind in (*CHECKOUT_POLICY_PATHS, *CHECKOUT_MEMORY_PATHS):
            path = root / relative_path
            if kind == "directory":
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"# {relative_path}\n", encoding="utf-8")
        routing = root / ROUTING_RELATIVE_PATH
        routing.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / ROUTING_RELATIVE_PATH, routing)
        return root

    def installed_project(self) -> Path:
        root = self.git_repository(self.temp_path / "target")
        initialize_project(project_paths(explicit=root), apply=True)
        return root

    def fake_which(self, *, missing: tuple[str, ...] = ()):
        """Resolve dependencies deterministically, keeping git real."""

        real_which = shutil.which

        def which(name):
            if name in missing:
                return None
            if name == "git":
                return real_which("git")
            return f"/opt/fake/{name}"

        return patch("brichan.lifecycle.shutil.which", side_effect=which)

    def report(self, root: Path, *, source: bool, missing: tuple[str, ...] = ()):
        paths = project_paths(explicit=root)
        with self.fake_which(missing=missing):
            return doctor_report(
                paths,
                checkout_root=paths.project_root if source else None,
            )

    # -- shape ------------------------------------------------------------

    def assert_exact_schema(self, report: dict) -> None:
        self.assertEqual(REPORT_KEYS, set(report))
        self.assertIs(int, type(report["schema_version"]))
        self.assertEqual(DOCTOR_SCHEMA_VERSION, report["schema_version"])
        self.assertIs(bool, type(report["ok"]))

        repository = report["repository"]
        self.assertEqual({"status", "root", "kind", "detail"}, set(repository))
        self.assertIn(repository["status"], STATUSES)
        self.assertIs(str, type(repository["root"]))
        self.assertIn(repository["kind"], {"source_checkout", "installed_project"})
        self.assertIs(str, type(repository["detail"]))

        git = report["git"]
        self.assertEqual(
            {"status", "branch", "commit", "dirty", "untracked", "detail"},
            set(git),
        )
        self.assertIn(git["status"], STATUSES)
        for key in ("branch", "commit"):
            self.assertIn(type(git[key]), (str, type(None)), key)
        for key in ("dirty", "untracked"):
            self.assertIn(type(git[key]), (bool, type(None)), key)
        self.assertIs(str, type(git["detail"]))

        for name in ("policies", "project_memory"):
            section = report[name]
            self.assertEqual({"status", "files", "detail"}, set(section), name)
            self.assertIn(section["status"], STATUSES)
            self.assertIs(str, type(section["detail"]))
            self.assertIs(dict, type(section["files"]))
            self.assertTrue(section["files"], name)
            for relative_path, check in section["files"].items():
                self.assertIs(str, type(relative_path))
                self.assertEqual({"status", "path", "detail"}, set(check))
                self.assertIn(check["status"], STATUSES)
                self.assertIs(str, type(check["path"]))
                self.assertIs(str, type(check["detail"]))

        routing = report["model_routing"]
        self.assertEqual({"status", "path", "schema_version", "detail"}, set(routing))
        self.assertIn(routing["status"], STATUSES)
        self.assertIs(str, type(routing["path"]))
        self.assertIn(type(routing["schema_version"]), (int, type(None)))
        self.assertIs(str, type(routing["detail"]))

        dependencies = report["dependencies"]
        self.assertEqual(
            {"status", "python", "git", "codex", "herdr"},
            set(dependencies),
        )
        self.assertIn(dependencies["status"], STATUSES)
        for name in ("python", "git", "codex", "herdr"):
            check = dependencies[name]
            self.assertEqual({"status", "path", "required", "detail"}, set(check), name)
            self.assertIn(check["status"], STATUSES)
            self.assertIn(type(check["path"]), (str, type(None)), name)
            self.assertIs(bool, type(check["required"]), name)
            self.assertIs(str, type(check["detail"]), name)
        self.assertTrue(dependencies["codex"]["required"])
        self.assertTrue(dependencies["herdr"]["required"])

        self.assert_exact_export_schema(report["agent_skill_export"])

    def assert_exact_export_schema(self, export: dict) -> None:
        """Design section 9's closed section and row grammar."""

        self.assertEqual(
            {
                "status",
                "mode",
                "relation",
                "path",
                "managed_path",
                "files",
                "detail_code",
                "detail",
            },
            set(export),
        )
        code = export["detail_code"]
        self.assertIn(code, AGENT_SKILL_EXPORT_ROWS)
        status, relation, nonnull, complete = AGENT_SKILL_EXPORT_ROWS[code]
        self.assertEqual(status, export["status"])
        self.assertIn(export["status"], STATUSES)
        self.assertEqual(relation, export["relation"])
        self.assertIn(export["relation"], EXPORT_RELATIONS)
        self.assertIn(export["mode"], {"source_checkout", "installed"})
        self.assertEqual(dict(AGENT_SKILL_EXPORT_DETAILS)[code], export["detail"])
        for key in ("path", "managed_path"):
            value = export[key]
            if nonnull:
                self.assertIs(str, type(value), key)
                self.assertTrue(1 <= len(value.encode("utf-8")) <= 4096, key)
            else:
                self.assertIsNone(value, key)
        self.assertIs(list, type(export["files"]))
        if not complete:
            self.assertEqual([], export["files"])
        self.assertLessEqual(len(export["files"]), 128)

        row_details = {row[0]: row for row in AGENT_SKILL_EXPORT_FILE_DETAILS}
        paths = [row["relative_path"] for row in export["files"]]
        self.assertEqual(
            sorted(paths, key=lambda value: value.encode("utf-8")), paths
        )
        self.assertEqual(len(set(paths)), len(paths))
        for row in export["files"]:
            self.assertEqual(
                {
                    "relative_path",
                    "managed_status",
                    "managed_sha256",
                    "exported_status",
                    "exported_sha256",
                    "relation",
                    "detail_code",
                    "detail",
                },
                set(row),
            )
            relative = row["relative_path"]
            self.assertTrue(1 <= len(relative.encode("utf-8")) <= 1024)
            self.assertFalse(relative.startswith("/"))
            self.assertFalse(relative.endswith("/"))
            self.assertNotIn("//", relative)
            self.assertNotIn("\\", relative)
            for component in relative.split("/"):
                self.assertTrue(1 <= len(component.encode("utf-8")) <= 255)
                self.assertNotIn(component, (".", ".."))
            _, row_relation, row_detail = row_details[row["detail_code"]]
            self.assertEqual(row_relation, row["relation"])
            self.assertEqual(row_detail, row["detail"])
            self.assertTrue(1 <= len(row_detail.encode("utf-8")) <= 64)
            for side in ("managed", "exported"):
                self.assertIn(row[f"{side}_status"], SIDE_STATUSES)
                digest = row[f"{side}_sha256"]
                if row[f"{side}_status"] == "regular":
                    self.assertIs(str, type(digest))
                    self.assertEqual(64, len(digest))
                    self.assertEqual(digest, digest.lower())
                    int(digest, 16)
                else:
                    self.assertIsNone(digest, side)

    def test_healthy_source_checkout_is_ok_and_exactly_shaped(self):
        root = self.source_checkout()
        code, report = self.report(root, source=True)
        self.assert_exact_schema(report)
        self.assertEqual(0, code)
        self.assertTrue(report["ok"])
        self.assertEqual("source_checkout", report["repository"]["kind"])
        self.assertEqual(str(root.resolve()), report["repository"]["root"])
        self.assertEqual("ok", report["git"]["status"])
        self.assertEqual(1, report["model_routing"]["schema_version"])
        self.assertEqual(
            {relative for relative, _ in CHECKOUT_POLICY_PATHS},
            set(report["policies"]["files"]),
        )
        self.assertEqual(
            {relative for relative, _ in CHECKOUT_MEMORY_PATHS},
            set(report["project_memory"]["files"]),
        )

    def test_missing_herdr_invalidates_source_checkout(self):
        root = self.source_checkout()
        code, report = self.report(root, source=True, missing=("herdr",))
        self.assertEqual(2, code)
        self.assertFalse(report["ok"])
        self.assertEqual("missing", report["dependencies"]["herdr"]["status"])
        self.assertEqual("missing", report["dependencies"]["status"])
        self.assertIsNone(report["dependencies"]["herdr"]["path"])

    def test_source_checkout_exit_matrix(self):
        root = self.source_checkout()

        code, report = self.report(root, source=True, missing=("codex",))
        self.assertEqual(4, code)
        self.assertFalse(report["ok"])
        self.assertEqual("missing", report["dependencies"]["codex"]["status"])

        missing_policy = root / CHECKOUT_POLICY_PATHS[0][0]
        missing_policy.unlink()
        code, report = self.report(root, source=True)
        self.assertEqual(2, code)
        self.assertFalse(report["ok"])
        self.assertEqual("missing", report["policies"]["status"])
        self.assertEqual(
            "missing",
            report["policies"]["files"][CHECKOUT_POLICY_PATHS[0][0]]["status"],
        )
        missing_policy.write_text("# restored\n", encoding="utf-8")

        (root / ROUTING_RELATIVE_PATH).write_text("{", encoding="utf-8")
        code, report = self.report(root, source=True)
        self.assertEqual(2, code)
        self.assertEqual("invalid", report["model_routing"]["status"])
        self.assertIsNone(report["model_routing"]["schema_version"])
        self.assertIn("malformed JSON", report["model_routing"]["detail"])

        (root / ROUTING_RELATIVE_PATH).write_text(
            json.dumps({"schema_version": 1}), encoding="utf-8"
        )
        code, report = self.report(root, source=True)
        self.assertEqual(2, code)
        self.assertEqual("invalid", report["model_routing"]["status"])
        self.assertEqual(1, report["model_routing"]["schema_version"])
        self.assertIn("routing config is invalid", report["model_routing"]["detail"])

    def test_missing_project_memory_directory_exits_two(self):
        root = self.source_checkout()
        shutil.rmtree(root / "projects")
        code, report = self.report(root, source=True)
        self.assertEqual(2, code)
        self.assertEqual("missing", report["project_memory"]["status"])
        self.assertEqual("missing", report["project_memory"]["files"]["projects"]["status"])

    def test_symlinked_required_path_is_invalid(self):
        root = self.source_checkout()
        policy = root / CHECKOUT_POLICY_PATHS[0][0]
        outside = root / "outside-policy.md"
        outside.write_bytes(policy.read_bytes())
        policy.unlink()
        policy.symlink_to(outside)
        code, report = self.report(root, source=True)
        self.assertEqual(2, code)
        self.assertEqual("invalid", report["policies"]["status"])
        self.assertIn(
            "symbolic link",
            report["policies"]["files"][CHECKOUT_POLICY_PATHS[0][0]]["detail"],
        )

    def test_missing_git_executable_is_unavailable_and_exits_two_in_source_mode(self):
        root = self.source_checkout()
        code, report = self.report(root, source=True, missing=("git",))
        self.assert_exact_schema(report)
        self.assertEqual(2, code)
        self.assertFalse(report["ok"])
        self.assertEqual("unavailable", report["git"]["status"])
        for key in ("branch", "commit", "dirty", "untracked"):
            self.assertIsNone(report["git"][key], key)
        self.assertEqual("missing", report["dependencies"]["git"]["status"])

    def test_unreadable_git_query_degrades_without_raising(self):
        root = self.source_checkout()
        paths = project_paths(explicit=root)
        with self.fake_which(), patch(
            "brichan.lifecycle.subprocess.run",
            side_effect=OSError("git exploded"),
        ):
            code, report = doctor_report(paths, checkout_root=paths.project_root)
        self.assertEqual(2, code)
        self.assertEqual("unavailable", report["git"]["status"])
        self.assertIn("git exploded", report["git"]["detail"])

    # -- installed mode ---------------------------------------------------

    def test_installed_project_preserves_every_state_exit_class(self):
        root = self.git_repository(self.temp_path / "target")
        paths = project_paths(explicit=root)

        code, report = self.report(root, source=False)
        self.assert_exact_schema(report)
        self.assertEqual(1, code)
        self.assertFalse(report["ok"])
        self.assertEqual("installed_project", report["repository"]["kind"])
        self.assertEqual("missing", report["repository"]["status"])
        self.assertIn("uninitialized", report["repository"]["detail"])

        initialize_project(paths, apply=True)
        code, report = self.report(root, source=False)
        self.assert_exact_schema(report)
        self.assertEqual(0, code)
        self.assertTrue(report["ok"])
        self.assertEqual("ok", report["repository"]["status"])
        self.assertEqual(
            {relative for relative, _ in ((path, "file") for path in MUTABLE_PATHS)},
            set(report["project_memory"]["files"]),
        )
        self.assertEqual(1, report["model_routing"]["schema_version"])

        code, report = self.report(root, source=False, missing=("codex",))
        self.assertEqual(4, code)
        self.assertFalse(report["ok"])

        manifest = paths.state_root / "manifest.json"
        original = manifest.read_bytes()
        manifest.write_text("{", encoding="utf-8")
        code, report = self.report(root, source=False)
        self.assertEqual(2, code)
        self.assertEqual("invalid", report["repository"]["status"])
        self.assertIn("malformed", report["repository"]["detail"])

        payload = json.loads(original)
        payload["schema_version"] = 99
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        code, report = self.report(root, source=False)
        self.assertEqual(3, code)
        self.assertEqual("invalid", report["repository"]["status"])
        self.assertIn("incompatible", report["repository"]["detail"])

    def read_spy(self):
        """Record every path whose contents are read during a report."""

        reads: list[str] = []
        original_text = Path.read_text
        original_bytes = Path.read_bytes

        def read_text(path, *positional, **keywords):
            reads.append(str(path))
            return original_text(path, *positional, **keywords)

        def read_bytes(path, *positional, **keywords):
            reads.append(str(path))
            return original_bytes(path, *positional, **keywords)

        return reads, patch.multiple(
            Path,
            read_text=read_text,
            read_bytes=read_bytes,
        )

    def assert_state_root_is_not_traversed(self, root: Path, outside: Path) -> None:
        paths = project_paths(explicit=root)
        reads, spy = self.read_spy()
        with self.fake_which(), spy:
            code, report = doctor_report(paths)

        self.assert_exact_schema(report)
        self.assertEqual(2, code)
        self.assertFalse(report["ok"])
        self.assertEqual("invalid", report["repository"]["status"])
        for section in ("policies", "project_memory"):
            self.assertEqual("invalid", report[section]["status"], section)
            self.assertIn("symbolic link", report[section]["detail"], section)
            self.assertTrue(report[section]["files"], section)
            for check in report[section]["files"].values():
                self.assertEqual("invalid", check["status"])
        self.assertEqual("invalid", report["model_routing"]["status"])
        self.assertIsNone(report["model_routing"]["schema_version"])
        self.assertIn("symbolic link", report["model_routing"]["detail"])

        # Nothing behind the link, and nothing outside the target, was read.
        for path in reads:
            self.assertFalse(
                path.startswith(str(outside)),
                f"read outside the target: {path}",
            )

    def test_resolving_state_symlink_is_invalid_and_never_traversed(self):
        root = self.installed_project()
        outside = self.temp_path / "outside-state"
        (root / ".brichan").rename(outside)
        (root / ".brichan").symlink_to(outside, target_is_directory=True)
        self.assert_state_root_is_not_traversed(root, outside)

    def test_dangling_state_symlink_is_invalid_and_never_traversed(self):
        root = self.git_repository(self.temp_path / "dangling")
        outside = self.temp_path / "outside-missing"
        (root / ".brichan").symlink_to(outside, target_is_directory=True)
        self.assert_state_root_is_not_traversed(root, outside)

    def test_symlinked_parent_component_is_invalid_and_not_read_through(self):
        root = self.installed_project()
        outside = self.temp_path / "outside-config"
        (root / ".brichan" / "config").rename(outside)
        (root / ".brichan" / "config").symlink_to(outside, target_is_directory=True)

        paths = project_paths(explicit=root)
        reads, spy = self.read_spy()
        with self.fake_which(), spy:
            code, report = doctor_report(paths)

        self.assert_exact_schema(report)
        self.assertEqual(2, code)
        self.assertEqual("invalid", report["model_routing"]["status"])
        self.assertIsNone(report["model_routing"]["schema_version"])
        self.assertIn("parent config", report["model_routing"]["detail"])
        self.assertIn("symbolic link", report["model_routing"]["detail"])
        for path in reads:
            self.assertFalse(
                path.startswith(str(outside)),
                f"read through a symlinked parent: {path}",
            )

    def test_state_root_that_is_not_a_directory_is_invalid(self):
        root = self.git_repository(self.temp_path / "file-state")
        (root / ".brichan").write_text("not a directory\n", encoding="utf-8")
        code, report = self.report(root, source=False)
        self.assert_exact_schema(report)
        self.assertEqual(2, code)
        self.assertEqual("invalid", report["policies"]["status"])
        self.assertIn("not a directory", report["policies"]["detail"])
        self.assertEqual("invalid", report["model_routing"]["status"])

    def test_uninitialized_state_reports_missing_without_traversal(self):
        root = self.git_repository(self.temp_path / "bare")
        code, report = self.report(root, source=False)
        self.assert_exact_schema(report)
        self.assertEqual(1, code)
        for section in ("policies", "project_memory"):
            self.assertEqual("missing", report[section]["status"], section)
            self.assertIn(".brichan state directory", report[section]["detail"])
        self.assertEqual("missing", report["model_routing"]["status"])
        self.assertIsNone(report["model_routing"]["schema_version"])

    def test_undecodable_routing_config_is_invalid_and_exits_two(self):
        root = self.source_checkout()
        (root / ROUTING_RELATIVE_PATH).write_bytes(b'{"schema_version": "\xff\xfe"}')
        code, report = self.report(root, source=True)
        self.assert_exact_schema(report)
        self.assertEqual(2, code)
        self.assertFalse(report["ok"])
        self.assertEqual("invalid", report["model_routing"]["status"])
        self.assertIsNone(report["model_routing"]["schema_version"])
        self.assertIn("utf-8", report["model_routing"]["detail"])

    def test_installed_exit_is_never_changed_by_a_missing_git_executable(self):
        root = self.installed_project()
        code, report = self.report(root, source=False, missing=("git",))
        self.assertEqual(0, code)
        self.assertFalse(report["ok"])
        self.assertEqual("unavailable", report["git"]["status"])

    def test_checkout_root_elsewhere_still_selects_installed_mode(self):
        """`--project other-repo` from a checkout diagnoses the other repo."""

        checkout = self.source_checkout()
        target = self.installed_project()
        paths = project_paths(explicit=target)
        with self.fake_which():
            code, report = doctor_report(paths, checkout_root=checkout)
        self.assertEqual(0, code)
        self.assertEqual("installed_project", report["repository"]["kind"])
        self.assertEqual(str(target.resolve()), report["repository"]["root"])

    # -- safety -----------------------------------------------------------

    def snapshot(self, root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): (
                path.read_bytes() if path.is_file() else b"<dir>"
            )
            for path in sorted(root.rglob("*"))
            if not path.is_symlink()
        }

    def test_report_writes_nothing_to_the_worktree_or_git_index(self):
        for source, root in (
            (True, self.source_checkout()),
            (False, self.installed_project()),
        ):
            with self.subTest(source=source):
                index = root / ".git" / "index"
                before = self.snapshot(root)
                before_index = index.read_bytes() if index.exists() else None
                self.report(root, source=source)
                self.assertEqual(before, self.snapshot(root))
                self.assertEqual(
                    before_index,
                    index.read_bytes() if index.exists() else None,
                )

    def test_git_is_only_queried_read_only_and_herdr_is_never_executed(self):
        root = self.source_checkout()
        paths = project_paths(explicit=root)
        real_run = subprocess.run
        commands: list[list[str]] = []

        def spy(arguments, *positional, **keywords):
            commands.append([str(item) for item in arguments])
            return real_run(arguments, *positional, **keywords)

        with self.fake_which(), patch(
            "brichan.lifecycle.subprocess.run", side_effect=spy
        ):
            doctor_report(paths, checkout_root=paths.project_root)

        self.assertTrue(commands)
        read_only_subcommands = {"rev-parse", "status"}
        for command in commands:
            self.assertEqual(Path(command[0]).name, "git", command)
            self.assertEqual("--no-optional-locks", command[1], command)
            self.assertEqual("-C", command[2], command)
            self.assertEqual(str(root.resolve()), command[3], command)
            self.assertIn(command[4], read_only_subcommands, command)
            for forbidden in ("fetch", "checkout", "commit", "config", "gc", "push"):
                self.assertNotIn(forbidden, command, command)
        joined = " ".join(" ".join(command) for command in commands)
        self.assertNotIn("herdr", joined)
        self.assertNotIn("codex", joined)


class SkillNameGrammarTest(unittest.TestCase):
    """`relative_path` is closed, so a name that cannot form one has no row."""

    def test_a_representable_name_decodes_unchanged(self):
        for name in ("SKILL.md", "references", "café.md", "a" * 255):
            with self.subTest(name=name):
                self.assertEqual(name, lifecycle._skill_component(name.encode("utf-8")))

    def test_every_unrepresentable_name_is_refused(self):
        for raw in (
            b"",
            b"\xff\xfe.md",
            "é.md".encode("utf-8"),
            b"a" * 256,
            b"we\tird.md",
            b"back\\slash.md",
            b".",
            b"..",
        ):
            with self.subTest(raw=raw):
                self.assertIsNone(lifecycle._skill_component(raw))


class AgentSkillExportReportTest(unittest.TestCase):
    """Design section 9's export comparison, over real managed/export trees."""

    @classmethod
    def setUpClass(cls):
        cls.git = shutil.which("git")

    def setUp(self):
        if self.git is None:
            self.skipTest("git executable is not available")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.temp_path = Path(self.temporary.name)
        self.root = self.temp_path / "target"
        subprocess.run(
            [self.git, "init", "--quiet", str(self.root)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.paths = project_paths(explicit=self.root)
        self.managed_root = self.paths.state_root / MANAGED_SKILL_DIR
        self.export_root = self.paths.project_root / AGENT_SKILLS_DIR

    # -- fixtures ---------------------------------------------------------

    def initialize(self):
        code, _ = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)

    def fake_which(self, *, missing: tuple[str, ...] = ()):
        real_which = shutil.which

        def which(name):
            if name in missing:
                return None
            if name == "git":
                return real_which("git")
            return f"/opt/fake/{name}"

        return patch("brichan.lifecycle.shutil.which", side_effect=which)

    def report(self, *, source: bool = False, missing: tuple[str, ...] = ()):
        with self.fake_which(missing=missing):
            return doctor_report(
                self.paths,
                checkout_root=self.paths.project_root if source else None,
            )

    def section(self, **keywords) -> dict:
        return self.report(**keywords)[1]["agent_skill_export"]

    def assert_code(self, code: str, **keywords) -> dict:
        section = self.section(**keywords)
        self.assertEqual(code, section["detail_code"], section)
        expected = AGENT_SKILL_EXPORT_ROWS[code]
        self.assertEqual(expected[0], section["status"])
        self.assertEqual(expected[1], section["relation"])
        self.assertEqual(dict(AGENT_SKILL_EXPORT_DETAILS)[code], section["detail"])
        if expected[2]:
            self.assertEqual(str(self.managed_root), section["managed_path"])
            self.assertEqual(str(self.export_root), section["path"])
        else:
            self.assertIsNone(section["managed_path"])
            self.assertIsNone(section["path"])
        if not expected[3]:
            self.assertEqual([], section["files"])
        return section

    def rows(self, section: dict) -> dict[str, dict]:
        return {row["relative_path"]: row for row in section["files"]}

    def descent_spy(self):
        """Record every entry the comparison metadata-classifies."""

        seen: list[str] = []
        real = techstack_filesystem.classify_entry

        def classify(parent_fd, name):
            seen.append(name)
            return real(parent_fd, name)

        return seen, patch.object(
            techstack_filesystem, "classify_entry", side_effect=classify
        )

    # -- mode and state ---------------------------------------------------

    def test_source_checkout_is_not_applicable_and_inspects_neither_tree(self):
        self.initialize()
        seen, spy = self.descent_spy()
        with spy:
            section = self.assert_code(
                "SOURCE_CHECKOUT_NOT_APPLICABLE", source=True
            )
        self.assertEqual("source_checkout", section["mode"])
        self.assertEqual([], seen)

    def test_installed_state_that_is_not_healthy_never_descends_the_trees(self):
        cases = {
            "MANAGED_STATE_UNINITIALIZED": lambda: None,
            "MANAGED_STATE_MALFORMED": lambda: (
                self.initialize(),
                (self.paths.state_root / "manifest.json").write_text(
                    "{", encoding="utf-8"
                ),
            ),
            "MANAGED_STATE_INCOMPATIBLE": lambda: (
                self.initialize(),
                self._rewrite_manifest(schema_version=99),
            ),
        }
        for code, prepare in cases.items():
            with self.subTest(code=code):
                self.setUp()
                prepare()
                seen, spy = self.descent_spy()
                with spy:
                    section = self.assert_code(code)
                self.assertEqual("installed", section["mode"])
                self.assertEqual([], seen)

    def _rewrite_manifest(self, **changes):
        manifest = self.paths.state_root / "manifest.json"
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload.update(changes)
        manifest.write_text(json.dumps(payload), encoding="utf-8")

    def output_path_section(self, project_root: Path, state_root: Path) -> dict:
        """The section for one directly-constructed pair of absolute roots."""

        paths = ProjectPaths(
            tool_root=self.paths.tool_root,
            project_root=project_root,
            state_root=state_root,
        )
        return lifecycle.agent_skill_export_section(
            paths, source_mode=False, inspection=None
        )

    def assert_null_output_paths(self, code: str, section: dict) -> None:
        self.assertEqual(code, section["detail_code"], section)
        self.assertIsNone(section["path"])
        self.assertIsNone(section["managed_path"])
        self.assertEqual([], section["files"])
        self.assertEqual("unavailable", section["status"])
        self.assertEqual("comparison_unavailable", section["relation"])

    def test_an_over_long_absolute_output_path_nulls_both_paths(self):
        long_root = Path("/" + "d" * 4100)
        self.assert_null_output_paths(
            "OUTPUT_PATH_BYTE_LIMIT",
            self.output_path_section(long_root, long_root / ".brichan"),
        )

    def test_a_non_nfc_absolute_output_path_nulls_both_paths(self):
        """Both strings are grammar-checked before any state is inspected."""

        root = Path("/e\u0301xport")
        self.assertNotEqual(unicodedata.normalize("NFC", str(root)), str(root))
        self.assert_null_output_paths(
            "OUTPUT_PATH_NOT_CANONICAL",
            self.output_path_section(root, root / ".brichan"),
        )

    def test_the_byte_bound_outranks_non_canonical_across_both_strings(self):
        """Design section 9's order, not whichever string is tested first.

        `agent_skill_export_section` tolerates a `state_root` that does not
        nest under `project_root`, so the two conditions can land on different
        strings. Both are collected before one row is chosen.
        """

        managed_root = Path("/e\u0301xport")
        export_root = Path("/" + "d" * 4200)
        self.assertNotEqual(
            unicodedata.normalize("NFC", str(managed_root)), str(managed_root)
        )
        self.assertEqual(
            str(export_root), unicodedata.normalize("NFC", str(export_root))
        )
        self.assertGreater(
            len(str(export_root / AGENT_SKILLS_DIR).encode("utf-8")),
            lifecycle.SKILL_OUTPUT_PATH_BYTE_LIMIT,
        )
        self.assert_null_output_paths(
            "OUTPUT_PATH_BYTE_LIMIT",
            self.output_path_section(export_root, managed_root),
        )

    # -- semantic relations -----------------------------------------------

    def test_a_current_export_reports_complete_byte_identical_rows(self):
        self.initialize()
        code, report = self.report()
        section = report["agent_skill_export"]
        self.assertEqual(0, code)
        self.assertTrue(report["ok"])
        self.assertEqual("EXPORT_CURRENT", section["detail_code"])
        self.assertEqual(
            [
                "SKILL.md",
                "references/commands.md",
                "references/handoff-receipt.md",
                "references/task-packet.md",
            ],
            [row["relative_path"] for row in section["files"]],
        )
        for row in section["files"]:
            self.assertEqual("current", row["relation"])
            self.assertEqual("FILE_CURRENT", row["detail_code"])
            self.assertEqual(row["managed_sha256"], row["exported_sha256"])
            self.assertEqual(64, len(row["managed_sha256"]))

    def test_rows_sort_by_relative_path_bytes(self):
        self.initialize()
        (self.managed_root / "Z.md").write_text("z\n", encoding="utf-8")
        (self.managed_root / "a.md").write_text("a\n", encoding="utf-8")
        section = self.section()
        paths = [row["relative_path"] for row in section["files"]]
        self.assertEqual(sorted(paths, key=lambda p: p.encode("utf-8")), paths)

    def test_an_absent_export_root_is_missing_with_complete_rows(self):
        self.initialize()
        shutil.rmtree(self.export_root)
        section = self.assert_code("EXPORT_MISSING")
        self.assertEqual(4, len(section["files"]))
        for row in section["files"]:
            self.assertEqual("missing", row["relation"])
            self.assertEqual("FILE_MISSING", row["detail_code"])
            self.assertEqual("absent", row["exported_status"])
            self.assertIsNone(row["exported_sha256"])
            self.assertEqual("regular", row["managed_status"])

    def test_one_missing_exported_file_is_missing(self):
        self.initialize()
        (self.export_root / "references" / "commands.md").unlink()
        section = self.assert_code("EXPORT_MISSING")
        row = self.rows(section)["references/commands.md"]
        self.assertEqual("FILE_MISSING", row["detail_code"])
        self.assertEqual("current", self.rows(section)["SKILL.md"]["relation"])

    def test_a_modified_exported_file_is_stale(self):
        self.initialize()
        (self.export_root / "SKILL.md").write_text("drifted\n", encoding="utf-8")
        section = self.assert_code("EXPORT_STALE")
        row = self.rows(section)["SKILL.md"]
        self.assertEqual("FILE_STALE", row["detail_code"])
        self.assertEqual("stale", row["relation"])
        self.assertNotEqual(row["managed_sha256"], row["exported_sha256"])

    def test_an_extra_exported_file_wins_over_stale_and_missing(self):
        self.initialize()
        (self.export_root / "extra.md").write_text("extra\n", encoding="utf-8")
        (self.export_root / "SKILL.md").write_text("drifted\n", encoding="utf-8")
        (self.export_root / "references" / "commands.md").unlink()
        section = self.assert_code("EXPORT_EXTRA")
        rows = self.rows(section)
        self.assertEqual("FILE_EXTRA", rows["extra.md"]["detail_code"])
        self.assertEqual("absent", rows["extra.md"]["managed_status"])
        self.assertIsNone(rows["extra.md"]["managed_sha256"])
        self.assertEqual("FILE_STALE", rows["SKILL.md"]["detail_code"])
        self.assertEqual(
            "FILE_MISSING", rows["references/commands.md"]["detail_code"]
        )

    # -- per-entry failures -----------------------------------------------

    def test_a_symlinked_exported_entry_is_unsafe_on_the_exported_side(self):
        self.initialize()
        target = self.export_root / "SKILL.md"
        target.unlink()
        target.symlink_to(self.managed_root / "SKILL.md")
        section = self.assert_code("SKILL_UNSAFE")
        row = self.rows(section)["SKILL.md"]
        self.assertEqual("FILE_EXPORTED_UNSAFE", row["detail_code"])
        self.assertEqual("unsafe", row["exported_status"])
        self.assertEqual("not_checked", row["managed_status"])
        self.assertIsNone(row["managed_sha256"])
        self.assertIsNone(row["exported_sha256"])

    def test_an_unexpected_directory_is_an_unsafe_row_entry(self):
        self.initialize()
        target = self.export_root / "SKILL.md"
        target.unlink()
        target.mkdir()
        section = self.assert_code("SKILL_UNSAFE")
        row = self.rows(section)["SKILL.md"]
        self.assertEqual("FILE_EXPORTED_UNSAFE", row["detail_code"])
        self.assertEqual("unsafe", row["exported_status"])

    def test_a_managed_side_failure_identifies_the_managed_side(self):
        self.initialize()
        unsafe = self.managed_root / "extra.md"
        os.mkfifo(unsafe)
        section = self.assert_code("SKILL_UNSAFE")
        row = self.rows(section)["extra.md"]
        self.assertEqual("FILE_MANAGED_UNSAFE", row["detail_code"])
        self.assertEqual("unsafe", row["managed_status"])
        self.assertEqual("absent", row["exported_status"])

    def test_an_unreadable_entry_leaves_the_other_side_not_checked(self):
        self.initialize()
        unreadable = self.managed_root / "extra.md"
        unreadable.write_text("secret\n", encoding="utf-8")
        shutil.copy2(unreadable, self.export_root / "extra.md")
        unreadable.chmod(0)
        self.addCleanup(unreadable.chmod, 0o644)
        if os.access(unreadable, os.R_OK):
            self.skipTest("this user can read a mode-0 file")
        section = self.assert_code("SKILL_UNREADABLE")
        row = self.rows(section)["extra.md"]
        self.assertEqual("FILE_MANAGED_UNREADABLE", row["detail_code"])
        self.assertEqual("unreadable", row["managed_status"])
        self.assertEqual("not_checked", row["exported_status"])
        self.assertIsNone(row["exported_sha256"])

    def test_a_per_file_byte_limit_outranks_an_unsafe_entry(self):
        """Design section 9 orders the byte rows above unsafe and unreadable."""

        self.initialize()
        os.mkfifo(self.managed_root / "a-unsafe.md")
        big = self.managed_root / "b-big.md"
        big.write_bytes(b"x" * (lifecycle.SKILL_FILE_BYTE_LIMIT + 1))
        section = self.assert_code("MANAGED_SKILL_BYTE_LIMIT")
        rows = self.rows(section)
        self.assertEqual("FILE_MANAGED_UNSAFE", rows["a-unsafe.md"]["detail_code"])
        self.assertEqual("FILE_MANAGED_OVER_LIMIT", rows["b-big.md"]["detail_code"])

    def test_a_per_file_over_limit_returns_the_complete_union(self):
        self.initialize()
        oversized = b"x" * (lifecycle.SKILL_FILE_BYTE_LIMIT + 1)
        (self.managed_root / "big.md").write_bytes(oversized)
        (self.export_root / "big.md").write_bytes(oversized)
        section = self.assert_code("MANAGED_SKILL_BYTE_LIMIT")
        rows = self.rows(section)
        self.assertEqual(5, len(rows))
        row = rows["big.md"]
        self.assertEqual("FILE_MANAGED_OVER_LIMIT", row["detail_code"])
        self.assertEqual("over_limit", row["managed_status"])
        self.assertIsNone(row["managed_sha256"])
        self.assertEqual("not_checked", row["exported_status"])

    def test_an_exported_over_limit_is_named_on_the_exported_side(self):
        self.initialize()
        (self.export_root / "big.md").write_bytes(
            b"x" * (lifecycle.SKILL_FILE_BYTE_LIMIT + 1)
        )
        section = self.assert_code("EXPORTED_SKILL_BYTE_LIMIT")
        row = self.rows(section)["big.md"]
        self.assertEqual("FILE_EXPORTED_OVER_LIMIT", row["detail_code"])
        self.assertEqual("over_limit", row["exported_status"])
        self.assertEqual("absent", row["managed_status"])

    # -- bounded enumeration ----------------------------------------------

    def test_an_aggregate_over_limit_suppresses_every_row(self):
        self.initialize()
        (self.managed_root / "huge.md").write_bytes(
            b"x" * (lifecycle.SKILL_AGGREGATE_BYTE_LIMIT + 1)
        )
        self.assert_code("MANAGED_SKILL_AGGREGATE_BYTE_LIMIT")

    def test_an_exported_aggregate_over_limit_names_the_exported_side(self):
        self.initialize()
        (self.export_root / "huge.md").write_bytes(
            b"x" * (lifecycle.SKILL_AGGREGATE_BYTE_LIMIT + 1)
        )
        self.assert_code("EXPORTED_SKILL_AGGREGATE_BYTE_LIMIT")

    def test_the_file_count_limit_suppresses_every_row(self):
        self.initialize()
        for index in range(lifecycle.SKILL_ENTRY_COUNT_LIMIT + 1):
            (self.managed_root / f"f{index:03d}.md").write_text("x\n", encoding="utf-8")
        self.assert_code("SKILL_ENTRY_LIMIT")

    def test_sixty_four_entries_per_side_still_compare(self):
        self.initialize()
        for index in range(lifecycle.SKILL_ENTRY_COUNT_LIMIT - 4):
            name = f"f{index:03d}.md"
            (self.managed_root / name).write_text("x\n", encoding="utf-8")
            (self.export_root / name).write_text("x\n", encoding="utf-8")
        section = self.assert_code("EXPORT_CURRENT")
        self.assertEqual(lifecycle.SKILL_ENTRY_COUNT_LIMIT, len(section["files"]))
        self.assertLessEqual(len(section["files"]), lifecycle.SKILL_FILE_ROW_LIMIT)

    def test_the_directory_count_limit_suppresses_every_row(self):
        self.initialize()
        for index in range(lifecycle.SKILL_DIRECTORY_COUNT_LIMIT + 1):
            (self.managed_root / f"d{index:03d}").mkdir()
        self.assert_code("SKILL_DIRECTORY_LIMIT")

    def test_the_depth_limit_suppresses_every_row(self):
        self.initialize()
        deep = self.managed_root
        for index in range(lifecycle.SKILL_MAX_DEPTH + 1):
            deep = deep / f"d{index}"
        deep.mkdir(parents=True)
        self.assert_code("SKILL_DEPTH_LIMIT")

    def test_six_directory_levels_are_still_compared(self):
        self.initialize()
        deep = self.managed_root
        for index in range(lifecycle.SKILL_MAX_DEPTH):
            deep = deep / f"d{index}"
        deep.mkdir(parents=True)
        (deep / "leaf.md").write_text("leaf\n", encoding="utf-8")
        section = self.assert_code("EXPORT_MISSING")
        self.assertIn("d0/d1/d2/d3/d4/d5/leaf.md", self.rows(section))

    # -- cap boundaries ----------------------------------------------------
    #
    # Design section 3 fixes the per-side caps at literal 64 row entries and
    # literal 64 directories, so these fixtures count in literals: a cap that
    # drifted with its constant would move a constant-derived fixture with it
    # and stay invisible.

    def add_files(self, root: Path, prefix: str, count: int) -> None:
        for index in range(count):
            (root / f"{prefix}{index:03d}.md").write_text("x\n", encoding="utf-8")

    def add_directories(self, root: Path, prefix: str, count: int) -> None:
        for index in range(count):
            (root / f"{prefix}{index:03d}").mkdir()

    def nest_directories(self, root: Path, prefix: str, depth: int) -> Path:
        deep = root
        for index in range(depth):
            deep = deep / f"{prefix}{index}"
        deep.mkdir(parents=True)
        return deep

    def test_sixty_four_managed_row_entries_are_the_last_that_compare(self):
        # 4 exported resources + 60 added = the literal 64-entry cap, exactly.
        self.initialize()
        self.add_files(self.managed_root, "u", 60)
        self.assertEqual(64, self.measure_side(self.managed_root)[0])
        section = self.assert_code("EXPORT_MISSING")
        self.assertEqual(64, len(section["files"]))

    def test_sixty_five_managed_row_entries_stop_the_comparison(self):
        # 4 exported resources + 61 added = exactly one past the cap.
        self.initialize()
        self.add_files(self.managed_root, "u", 61)
        self.assertEqual(65, self.measure_side(self.managed_root)[0])
        section = self.assert_code("SKILL_ENTRY_LIMIT")
        self.assertEqual("skill file count exceeds 64", section["detail"])
        self.assertEqual("unavailable", section["status"])
        self.assertEqual([], section["files"])

    def test_sixty_four_exported_row_entries_are_the_last_that_compare(self):
        self.initialize()
        self.add_files(self.export_root, "u", 60)
        self.assertEqual(64, self.measure_side(self.export_root)[0])
        section = self.assert_code("EXPORT_EXTRA")
        self.assertEqual(64, len(section["files"]))

    def test_sixty_five_exported_row_entries_stop_the_comparison(self):
        self.initialize()
        self.add_files(self.export_root, "u", 61)
        self.assertEqual(65, self.measure_side(self.export_root)[0])
        section = self.assert_code("SKILL_ENTRY_LIMIT")
        self.assertEqual("skill file count exceeds 64", section["detail"])
        self.assertEqual("unavailable", section["status"])
        self.assertEqual([], section["files"])

    def test_sixty_four_managed_directories_are_the_last_that_compare(self):
        # 1 exported `references/` + 63 added = the literal 64-directory cap.
        self.initialize()
        self.add_directories(self.managed_root, "d", 63)
        self.assertEqual(64, self.measure_side(self.managed_root)[1])
        section = self.assert_code("EXPORT_CURRENT")
        self.assertEqual(4, len(section["files"]))

    def test_sixty_five_managed_directories_stop_the_comparison(self):
        self.initialize()
        self.add_directories(self.managed_root, "d", 64)
        section = self.assert_code("SKILL_DIRECTORY_LIMIT")
        self.assertEqual("skill directory count exceeds 64", section["detail"])
        self.assertEqual("unavailable", section["status"])
        self.assertEqual([], section["files"])

    def test_sixty_four_exported_directories_are_the_last_that_compare(self):
        self.initialize()
        self.add_directories(self.export_root, "d", 63)
        self.assertEqual(64, self.measure_side(self.export_root)[1])
        section = self.assert_code("EXPORT_CURRENT")
        self.assertEqual(4, len(section["files"]))

    def test_sixty_five_exported_directories_stop_the_comparison(self):
        self.initialize()
        self.add_directories(self.export_root, "d", 64)
        section = self.assert_code("SKILL_DIRECTORY_LIMIT")
        self.assertEqual("skill directory count exceeds 64", section["detail"])
        self.assertEqual("unavailable", section["status"])
        self.assertEqual([], section["files"])

    def test_an_unexpected_directory_consumes_a_row_entry_slot(self):
        """Section 16: it counts against the 64 row entries of its own side."""

        self.initialize()
        # Both sides land on exactly 64 row entries; the exported side then
        # carries one directory where the managed side has a row entry, which
        # section 16 charges to the exported side's row-entry cap as the 65th.
        self.add_files(self.managed_root, "u", 60)
        self.add_files(self.export_root, "u", 60)
        (self.export_root / "w.md").write_text("x\n", encoding="utf-8")
        exported_skill = self.export_root / "SKILL.md"
        exported_skill.unlink()
        exported_skill.mkdir()
        section = self.assert_code("SKILL_ENTRY_LIMIT")
        self.assertEqual("skill file count exceeds 64", section["detail"])
        self.assertEqual("unavailable", section["status"])
        self.assertEqual([], section["files"])

    # -- abort precedence --------------------------------------------------
    #
    # Design section 9 ranks the *applicable* conditions by registry order, so
    # a fixture in which two abort conditions hold must report the same code
    # whichever entry name the enumeration happens to reach first.

    def test_the_entry_cap_outranks_a_directory_cap_reached_first(self):
        self.initialize()
        self.add_directories(self.managed_root, "d", 65)
        self.add_files(self.managed_root, "e", 64)
        section = self.assert_code("SKILL_ENTRY_LIMIT")
        self.assertEqual("skill file count exceeds 64", section["detail"])

    def test_the_entry_cap_outranks_a_directory_cap_reached_last(self):
        self.initialize()
        self.add_directories(self.managed_root, "z", 65)
        self.add_files(self.managed_root, "a", 64)
        section = self.assert_code("SKILL_ENTRY_LIMIT")
        self.assertEqual("skill file count exceeds 64", section["detail"])

    def test_the_entry_cap_outranks_a_depth_cap_reached_first(self):
        self.initialize()
        self.nest_directories(self.managed_root, "a", lifecycle.SKILL_MAX_DEPTH + 1)
        self.add_files(self.managed_root, "z", 64)
        section = self.assert_code("SKILL_ENTRY_LIMIT")
        self.assertEqual("skill file count exceeds 64", section["detail"])

    def test_the_entry_cap_outranks_a_depth_cap_reached_last(self):
        self.initialize()
        self.nest_directories(self.managed_root, "z", lifecycle.SKILL_MAX_DEPTH + 1)
        self.add_files(self.managed_root, "a", 64)
        section = self.assert_code("SKILL_ENTRY_LIMIT")
        self.assertEqual("skill file count exceeds 64", section["detail"])

    def test_only_the_directory_cap_exceeded_reports_the_directory_row(self):
        self.initialize()
        self.add_directories(self.managed_root, "d", 64)
        section = self.assert_code("SKILL_DIRECTORY_LIMIT")
        self.assertEqual("skill directory count exceeds 64", section["detail"])

    def test_only_the_depth_cap_exceeded_reports_the_depth_row(self):
        # Literal 7, so a drifted `SKILL_MAX_DEPTH` cannot move the fixture
        # with it; `test_six_directory_levels_are_still_compared` pins six.
        self.initialize()
        self.nest_directories(self.managed_root, "d", 7)
        section = self.assert_code("SKILL_DEPTH_LIMIT")
        self.assertEqual("skill directory depth exceeds 6", section["detail"])

    def test_an_over_long_relative_path_reports_the_length_row(self):
        """1,024 bytes is the row cap; the absolute path stays under PATH_MAX."""

        self.initialize()
        # Descriptor-relative so the host PATH_MAX never bounds the fixture.
        self.nest_over_long_relative_path()
        section = self.assert_code("SKILL_ENTRY_NAME_BYTE_LIMIT")
        self.assertEqual(
            "a skill entry name exceeds 255 or a path exceeds 1024 bytes",
            section["detail"],
        )

    def mkdir_relative(self, root: Path, name: str) -> None:
        """`mkdir` one name descriptor-relative, or skip when the host refuses.

        Descriptor-relative so the bound this asserts is the registry's, not
        the host `PATH_MAX` the absolute path would otherwise reach first.
        """

        directory_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.mkdir(name, dir_fd=directory_fd)
        except OSError as error:  # pragma: no cover - filesystem dependent
            self.skipTest(f"cannot create a {len(name.encode())}-byte name: {error}")
        finally:
            os.close(directory_fd)

    def test_an_over_long_component_reports_the_length_row(self):
        """256 NFC bytes in 128 characters: a length violation, not encoding."""

        self.initialize()
        name = "é" * 128
        self.assertEqual(name, unicodedata.normalize("NFC", name))
        self.assertGreater(
            len(name.encode("utf-8")), lifecycle.SKILL_COMPONENT_BYTE_LIMIT
        )
        self.mkdir_relative(self.managed_root, name)
        self.assert_code("SKILL_ENTRY_NAME_BYTE_LIMIT")

    def test_a_name_that_is_both_over_long_and_non_nfc_reports_its_length(self):
        """A name is measured before it is decoded, so its length wins.

        100 decomposed characters: 300 bytes over the 255-byte component
        bound, and 200 characters under this host's `NAME_MAX`.
        """

        self.initialize()
        name = "e\u0301" * 100
        self.assertNotEqual(name, unicodedata.normalize("NFC", name))
        self.assertGreater(
            len(name.encode("utf-8")), lifecycle.SKILL_COMPONENT_BYTE_LIMIT
        )
        self.mkdir_relative(self.managed_root, name)
        if name not in os.listdir(self.managed_root):
            self.skipTest("this filesystem normalizes entry names")
        self.assert_code("SKILL_ENTRY_NAME_BYTE_LIMIT")

    def test_a_non_nfc_entry_name_suppresses_every_row(self):
        """Within both bounds, so the encoding row keeps this one."""

        self.initialize()
        name = "é.md"
        try:
            (self.managed_root / name).write_text("x\n", encoding="utf-8")
        except OSError as error:  # pragma: no cover - filesystem dependent
            self.skipTest(f"cannot create a non-NFC name here: {error}")
        if name not in os.listdir(self.managed_root):
            self.skipTest("this filesystem normalizes entry names")
        self.assertLessEqual(
            len(name.encode("utf-8")), lifecycle.SKILL_COMPONENT_BYTE_LIMIT
        )
        self.assert_code("SKILL_ENTRY_NAME_INVALID")

    # -- name rows against each other and the entry cap --------------------
    #
    # Design section 9 ranks the *applicable* conditions by registry order, so
    # a tree in which a name row and a lower row both hold must report the
    # name row whichever entry name the enumeration reaches first. Every pair
    # below is one logical state built twice: once with the higher-ranked
    # condition's name sorting first, once sorting last.

    def test_the_length_row_outranks_a_non_nfc_name_sorting_last(self):
        """Row 13 over row 14 across two different names, length name first."""

        self.initialize()
        self.nest_over_long_relative_path(lead="a")
        self.add_non_nfc_file(b"ze\xcc\x81xport.md")
        section = self.assert_code("SKILL_ENTRY_NAME_BYTE_LIMIT")
        self.assertEqual(
            "a skill entry name exceeds 255 or a path exceeds 1024 bytes",
            section["detail"],
        )

    def test_the_length_row_outranks_a_non_nfc_name_sorting_first(self):
        """The same state with the non-NFC name reached first instead."""

        self.initialize()
        self.nest_over_long_relative_path(lead="z")
        self.add_non_nfc_file(b"ae\xcc\x81xport.md")
        self.assert_code("SKILL_ENTRY_NAME_BYTE_LIMIT")

    def test_the_encoding_row_outranks_an_entry_cap_reached_last(self):
        """Row 14 over row 15: the non-NFC name is reached first."""

        self.initialize()
        self.add_non_nfc_file(b"ae\xcc\x81xport.md")
        self.add_files(self.managed_root, "z", 70)
        section = self.assert_code("SKILL_ENTRY_NAME_INVALID")
        self.assertEqual("a skill entry name is not strict UTF-8 NFC", section["detail"])

    def test_the_encoding_row_outranks_an_entry_cap_reached_first(self):
        """The same state with the 70 files reached first instead."""

        self.initialize()
        self.add_non_nfc_file(b"ze\xcc\x81xport.md")
        self.add_files(self.managed_root, "a", 70)
        self.assert_code("SKILL_ENTRY_NAME_INVALID")

    def test_the_length_row_outranks_an_entry_cap_reached_last(self):
        """Row 13 over row 15: the over-long path is reached first.

        Both conditions live on the level the descriptor names, so the entry
        cap is the only row that could stop enumeration before the over-long
        name is measured.
        """

        self.initialize()
        directory_fd = self.open_deep_level()
        try:
            self.mkdir_at(directory_fd, "0" + "n" * 249)
            self.add_files_at(directory_fd, "e", 70)
        finally:
            os.close(directory_fd)
        section = self.assert_code("SKILL_ENTRY_NAME_BYTE_LIMIT")
        self.assertEqual(
            "a skill entry name exceeds 255 or a path exceeds 1024 bytes",
            section["detail"],
        )

    def test_the_length_row_outranks_an_entry_cap_reached_first(self):
        """The same state with the 70 files reached first instead."""

        self.initialize()
        directory_fd = self.open_deep_level()
        try:
            self.mkdir_at(directory_fd, "z" + "n" * 249)
            self.add_files_at(directory_fd, "e", 70)
        finally:
            os.close(directory_fd)
        self.assert_code("SKILL_ENTRY_NAME_BYTE_LIMIT")

    # -- precedence under the bounded enumeration --------------------------
    #
    # Design section 16 (version 10) ranks an enumeration-abort condition only
    # where section 3's bounded enumeration actually observed it: enumeration
    # finishes listing the directory level at which any abort trips, so every
    # condition observable at levels already listed is ranked by registry
    # order, and a condition whose evidence lies only inside a directory the
    # abort prevented descending is not applicable.
    #
    # The three `M2-i4v2-2` name-row pairs the version-10 step-6 bullet also
    # names are owned above, one test per pair per name order: rows 13, 14, and
    # 13 from `test_the_length_row_outranks_a_non_nfc_name_sorting_last`
    # through `test_the_length_row_outranks_an_entry_cap_reached_first`. Each
    # of those fixtures places both of its conditions on one already-listed
    # level, which is what makes the assertion true; they are not repeated
    # here.

    def measure_side(self, root: Path) -> tuple[int, int]:
        """Count one side's row-bearing entries and directories, by walk.

        Independent of the enumeration under test, so a fixture that drifted
        away from the counts the finding is about cannot stay silent.
        """

        entries = 0
        directories = 0
        for _, names, filenames in os.walk(root):
            directories += len(names)
            entries += len(filenames)
        return entries, directories

    def test_sixty_five_of_each_reports_the_directory_row_when_last(self):
        """`references/` is itself the 65th directory, so it is never descended.

        Its three row entries are therefore never observed, the 62 observed
        entries stay inside the 64-entry cap, and `SKILL_ENTRY_LIMIT` is not
        applicable to this report.
        """

        self.initialize()
        # 1 exported `references/` + 64 added = 65 directories; 4 exported
        # files + 61 added = 65 row entries. Literals, not constants.
        self.add_directories(self.export_root, "d", 64)
        self.add_files(self.export_root, "e", 61)
        self.assertEqual((65, 65), self.measure_side(self.export_root))
        section = self.assert_code("SKILL_DIRECTORY_LIMIT")
        self.assertEqual("skill directory count exceeds 64", section["detail"])

    def test_sixty_five_of_each_reports_the_entry_row_when_descended(self):
        """The same counts, with `references/` before the extra directories.

        It is descended before any cap trips, so its three row entries are
        observed at an already-listed level and the 65th row entry ranks
        ahead of the directory cap.
        """

        self.initialize()
        self.add_directories(self.export_root, "z", 64)
        self.add_files(self.export_root, "a", 61)
        self.assertEqual((65, 65), self.measure_side(self.export_root))
        section = self.assert_code("SKILL_ENTRY_LIMIT")
        self.assertEqual("skill file count exceeds 64", section["detail"])

    def resource_limit_on(self, name: str):
        """Exhaust descriptors on exactly one entry name, as `EMFILE` would.

        Every other name still reaches the real classifier, so the fixture is
        one ordinary tree with one transient failure in it.
        """

        real_classify = techstack_filesystem.classify_entry

        def classify(parent_fd, entry_name):
            if entry_name == name:
                return techstack_filesystem.Observation(code="RESOURCE_LIMIT")
            return real_classify(parent_fd, entry_name)

        return patch.object(
            techstack_filesystem, "classify_entry", side_effect=classify
        )

    def test_a_resource_failure_outranks_an_entry_cap_reached_last(self):
        """Row 8 over row 15, with the faulting entry reached first."""

        self.initialize()
        (self.managed_root / "a_emfile").write_text("x\n", encoding="utf-8")
        self.add_files(self.managed_root, "z", 70)
        with self.resource_limit_on("a_emfile"):
            section = self.assert_code("RESOURCE_LIMIT")
        self.assertEqual(
            "a process filesystem resource was exhausted", section["detail"]
        )

    def test_a_resource_failure_outranks_an_entry_cap_reached_first(self):
        """The same state with the 70 files reached first instead.

        `SKILL_ENTRY_LIMIT` trips at an already-listed level and stops descent
        only; the faulting entry on that same level is still classified, so
        row 8 is observed and outranks row 15.
        """

        self.initialize()
        (self.managed_root / "z_emfile").write_text("x\n", encoding="utf-8")
        self.add_files(self.managed_root, "a", 70)
        with self.resource_limit_on("z_emfile"):
            self.assert_code("RESOURCE_LIMIT")

    def test_the_entry_cap_stops_descent_into_an_undescended_directory(self):
        """The other half of the entry cap: it still refuses every descent.

        The over-long path sits five levels down inside a directory sorting
        after the 65th row entry, so the abort prevents descending to it and
        Design section 16 makes row 13 not applicable to this report even
        though row 13 outranks row 15.
        """

        self.initialize()
        self.add_files(self.managed_root, "a", 70)
        self.nest_over_long_relative_path(lead="z")
        section = self.assert_code("SKILL_ENTRY_LIMIT")
        self.assertEqual("skill file count exceeds 64", section["detail"])

    def test_the_entry_counter_stops_one_past_its_cap(self):
        """A level of 70 files records 65 entries, not 70.

        Once the row is recorded and `files` is suppressed, no further entry
        can change the answer, so the count stops even though the level is
        still listed and classified to the end for the conditions that can.
        """

        self.initialize()
        self.add_files(self.managed_root, "a", 70)
        scan = lifecycle._scan_skill_side(
            self.paths.project_root,
            os.path.relpath(self.managed_root, self.paths.project_root),
            "MANAGED_SKILL_AGGREGATE_BYTE_LIMIT",
        )
        self.assertIn("SKILL_ENTRY_LIMIT", scan.failures)
        self.assertTrue(scan.bounded)
        self.assertEqual(lifecycle.SKILL_ENTRY_COUNT_LIMIT + 1, len(scan.entries))

    def errno_on(self, **names: int):
        """Raise a real `OSError` from the metadata call for named entries.

        The observation is then produced by the production `_errno_outcome`
        table rather than by a hand-written observation code, and every other
        name still reaches the real filesystem. The platform predicates probe
        `os.stat` with a `dir_fd` too, so they are held supported: otherwise
        the section answers before enumeration ever runs and the assertion
        would pass for the wrong reason.
        """

        real_stat = os.stat

        def stat_call(path, *positional, dir_fd=None, **keywords):
            if dir_fd is not None and path in names:
                number = names[path]
                raise OSError(number, os.strerror(number))
            return real_stat(path, *positional, dir_fd=dir_fd, **keywords)

        @contextlib.contextmanager
        def armed():
            with patch.object(
                techstack_filesystem, "is_supported_platform", return_value=True
            ), patch.object(os, "stat", side_effect=stat_call):
                yield

        return armed()

    def test_the_capability_row_outranks_a_resource_row_sorting_last(self):
        """Rows 7 and 8 on one level are ranked by section 9, not by name.

        The capability row is permanent and actionable and the resource row is
        transient, so which one an operator is shown may not depend on which
        entry name sorts first.
        """

        self.initialize()
        (self.managed_root / "a_unsup").write_text("x\n", encoding="utf-8")
        (self.managed_root / "z_nomem").write_text("x\n", encoding="utf-8")
        with self.errno_on(a_unsup=errno.EOPNOTSUPP, z_nomem=errno.ENOMEM):
            section = self.assert_code("UNSUPPORTED_SAFE_OPEN")
        self.assertEqual(
            "required safe-open primitives are unavailable", section["detail"]
        )

    def test_the_capability_row_outranks_a_resource_row_sorting_first(self):
        """The same level with the two entry names exchanged."""

        self.initialize()
        (self.managed_root / "a_nomem").write_text("x\n", encoding="utf-8")
        (self.managed_root / "z_unsup").write_text("x\n", encoding="utf-8")
        with self.errno_on(a_nomem=errno.ENOMEM, z_unsup=errno.EOPNOTSUPP):
            section = self.assert_code("UNSUPPORTED_SAFE_OPEN")
        self.assertEqual(
            "required safe-open primitives are unavailable", section["detail"]
        )

    def test_the_directory_set_keeps_every_directory_its_level_listed(self):
        """The directory set is not capped, and the reported row depends on it.

        All 200 directories were observed at an already-listed level, so
        Design section 16 makes every one of them applicable, and the
        unexpected-directory accounting reads the whole set. Capping it at
        cap+1 would drop the exported side's regular files at
        `q100`-`q103` out of that accounting and report row 16 instead of
        row 15.

        Only four exported files, and 60 extra managed files to carry the
        managed count: 65 exported files at those paths would trip the
        exported side's own entry cap, so row 15 would be reported for a
        second reason and a capped directory set would stay invisible.
        """

        self.initialize()
        self.add_files(self.managed_root, "a", 60)
        # 4 managed resources + 60 added = exactly the 64-entry cap, so the
        # four unexpected directories below are what take the side past it.
        self.assertEqual(64, self.measure_side(self.managed_root)[0])
        self.add_directories(self.managed_root, "q", 200)
        for index in range(100, 104):
            (self.export_root / f"q{index:03d}").write_text("x\n", encoding="utf-8")
        scan = lifecycle._scan_skill_side(
            self.paths.project_root,
            os.path.relpath(self.managed_root, self.paths.project_root),
            "MANAGED_SKILL_AGGREGATE_BYTE_LIMIT",
        )
        self.assertIn("SKILL_DIRECTORY_LIMIT", scan.failures)
        self.assertEqual(201, len(scan.directories))
        section = self.assert_code("SKILL_ENTRY_LIMIT")
        self.assertEqual("skill file count exceeds 64", section["detail"])

    def cost_spy(self):
        """Count content reads and record every directory opened by name."""

        reads: list[str] = []
        opened: list[str] = []
        real_read = techstack_filesystem.read_bounded_regular
        real_open = techstack_filesystem.open_directory

        def read_bounded_regular(parent_fd, name, limit):
            reads.append(name)
            return real_read(parent_fd, name, limit)

        def open_directory(parent_fd, name):
            opened.append(name)
            return real_open(parent_fd, name)

        @contextlib.contextmanager
        def armed():
            with patch.object(
                techstack_filesystem,
                "read_bounded_regular",
                side_effect=read_bounded_regular,
            ), patch.object(
                techstack_filesystem, "open_directory", side_effect=open_directory
            ):
                yield

        return reads, opened, armed()

    def test_a_wide_aborting_level_reads_no_content_and_descends_nothing(self):
        """The cost of finishing an aborting level is bounded in kind.

        Finishing a 2,000-name level costs one metadata call per name on it,
        which nothing bounds in count; what is bounded is the kind of work.
        No file content is read and the marker directory sorting after the
        abort is never opened, so no descent is paid for.
        """

        self.initialize()
        self.add_files(self.managed_root, "a", 2000)
        (self.managed_root / "zmark").mkdir()
        (self.managed_root / "zmark" / "inner.md").write_text("x\n", encoding="utf-8")
        reads, opened, spy = self.cost_spy()
        with spy:
            section = self.assert_code("SKILL_ENTRY_LIMIT")
        self.assertEqual("skill file count exceeds 64", section["detail"])
        self.assertEqual([], reads)
        self.assertNotIn("zmark", opened)

    def test_an_abort_below_finishes_every_ancestor_level_without_descent(self):
        """The cost bound spans the ancestors, and stays bounded in kind.

        Section 16 makes every condition observable at a level *already
        listed* applicable, so an abort three levels down finishes the two
        ancestor levels above it as well: their 300 later names each are still
        classified, which is one metadata call apiece and the whole reason the
        reported row is the registry minimum rather than whatever the deepest
        level happened to raise. What the bound forbids is the other kind of
        work — no file content is read anywhere, and neither ancestor's marker
        directory is opened once `bounded` is set.
        """

        self.initialize()
        first = self.managed_root / "a_one"
        second = first / "a_two"
        third = second / "a_three"
        third.mkdir(parents=True)
        (third / "z_unsup").write_text("x\n", encoding="utf-8")
        for level, mark in ((first, "zmark_one"), (second, "zmark_two")):
            self.add_files(level, "z", 300)
            (level / mark).mkdir()
            (level / mark / "inner.md").write_text("x\n", encoding="utf-8")
        seen, descent = self.descent_spy()
        reads, opened, spy = self.cost_spy()
        with descent, spy, self.errno_on(z_unsup=errno.EOPNOTSUPP):
            section = self.assert_code("UNSUPPORTED_SAFE_OPEN")
        self.assertEqual(
            "required safe-open primitives are unavailable", section["detail"]
        )
        self.assertEqual([], reads)
        self.assertNotIn("zmark_one", opened)
        self.assertNotIn("zmark_two", opened)
        # Both ancestor levels finished: 300 later names classified on each,
        # and both marker directories were classified without being opened.
        later = [n for n in seen if n.startswith("z") and n.endswith(".md")]
        self.assertEqual(600, len(later))
        self.assertIn("zmark_one", seen)
        self.assertIn("zmark_two", seen)

    # -- the enumeration loop holds no return ------------------------------
    #
    # Four consecutive reviews found the same defect on a route not yet
    # covered: an abort inside the enumeration loop that recorded its row and
    # returned mid-level, so a higher-ranked condition later on the same
    # already-listed level was never observed and the reported row depended on
    # entry names. `_abort_scan` is now the only way an abort is recorded
    # there, and the two tests below own the shape and the whole pair matrix
    # rather than one more route.

    def enumeration_loop(self) -> ast.For:
        """The `for name, relative in listed:` loop, parsed from the source."""

        source = textwrap.dedent(inspect.getsource(lifecycle._scan_skill_directory))
        function = ast.parse(source).body[0]
        loops = [
            node
            for node in function.body
            if isinstance(node, ast.For)
            and isinstance(node.iter, ast.Name)
            and node.iter.id == "listed"
        ]
        self.assertEqual(1, len(loops), "the enumeration loop moved or was renamed")
        return loops[0]

    def test_the_enumeration_loop_holds_no_return(self):
        """The defect class is closed by shape, not one route at a time.

        A `return` inside this loop unwinds the whole side mid-level, which is
        exactly what Design section 16 forbids: the level already listed must
        finish so every condition observable on it is ranked by section 9's
        registry order. Reinstating any one of them fails here before any
        fixture has to catch it.
        """

        returns = [
            node
            for node in ast.walk(self.enumeration_loop())
            if isinstance(node, ast.Return)
        ]
        self.assertEqual([], returns, "an abort still unwinds the aborting level")

    def test_every_abort_in_the_loop_goes_through_the_helper(self):
        """`_abort_scan` is the single recording site inside the loop.

        Recording a row without setting `scan.bounded` would leave descent
        running below an abort; setting `bounded` without recording would lose
        the row. One helper does both, so neither half can drift alone.
        """

        loop = self.enumeration_loop()
        calls = [node for node in ast.walk(loop) if isinstance(node, ast.Call)]
        bare = [
            call
            for call in calls
            if isinstance(call.func, ast.Attribute)
            and call.func.attr == "add"
            and isinstance(call.func.value, ast.Attribute)
            and call.func.value.attr == "failures"
        ]
        self.assertEqual([], bare, "a failure is recorded without `_abort_scan`")
        aborts = [
            call
            for call in calls
            if isinstance(call.func, ast.Name) and call.func.id == "_abort_scan"
        ]
        # The section row raised while classifying, the section row raised by
        # a refused directory open, the directory cap, the depth cap, the
        # aggregate bound, and the entry cap.
        self.assertEqual(6, len(aborts))

    # -- every pair of abort rows on one level -----------------------------
    #
    # Design section 9 ranks the *applicable* conditions by registry order, so
    # a level on which two abort conditions both hold must report the same row
    # whichever of them the sorted walk reaches first. The matrix below builds
    # every co-constructible pair in both name orders on one already-listed
    # level whose relative prefix is 1,004 bytes, so that the 1,024-byte
    # relative-path row can sit on the same level as every other condition.
    #
    # The depth cap is decided on the level under test too — from that level's
    # own `depth` and a directory *on* it, with only the refused directory's
    # contents below — so it pairs with every other condition rather than
    # standing outside the matrix. Its pairs are built six components deep,
    # where any directory on the level exceeds `SKILL_MAX_DEPTH`; every other
    # pair keeps the four-component level, where none does.
    #
    # `needs_open` marks the two conditions that are observable only by
    # opening a directory the level listed. Section 16 makes such a condition
    # not applicable once an abort has refused descent, so when a bounding
    # condition sorts ahead of it the pair is not simultaneously observable
    # and the expectation is the registry minimum of what remains. That is the
    # same clause `test_the_entry_cap_stops_descent_into_an_undescended_
    # directory` owns, and refusing those opens is what keeps the cost of
    # finishing an aborting level free of descent. On a depth-capped level
    # they are suppressed in *both* orders: the depth check at
    # `lifecycle.py:1176` runs before the open guard for the same entry, so a
    # directory there is never opened whichever name sorts first.

    ABORT_PAIR_CONDITIONS = {
        # key: (registry code, sets `scan.bounded`, needs a directory open)
        "aggregate": ("MANAGED_SKILL_AGGREGATE_BYTE_LIMIT", True, False),
        "classify_resource": ("RESOURCE_LIMIT", True, False),
        "classify_unsupported": ("UNSUPPORTED_SAFE_OPEN", True, False),
        "depth_limit": ("SKILL_DEPTH_LIMIT", True, False),
        "directory_limit": ("SKILL_DIRECTORY_LIMIT", True, False),
        "entry_limit": ("SKILL_ENTRY_LIMIT", True, False),
        "name_byte_limit": ("SKILL_ENTRY_NAME_BYTE_LIMIT", False, False),
        "name_invalid": ("SKILL_ENTRY_NAME_INVALID", False, False),
        "open_resource": ("RESOURCE_LIMIT", True, True),
        "open_unsupported": ("UNSUPPORTED_SAFE_OPEN", True, True),
    }

    def errno_on_names(self, stat_errnos: dict, open_errnos: dict):
        """Raise real `OSError`s from the two production entry primitives.

        `classify_entry` reaches an entry through `os.stat` with a `dir_fd`,
        and `open_directory` reaches it through `os.stat` and then `os.open`
        with a `dir_fd`, so injecting at the syscall keeps `_errno_outcome`
        and its closed table in the path instead of hand-writing an
        observation code. Every other name still reaches the real filesystem.
        The platform predicates probe `os.stat` with a `dir_fd` too, so they
        are held supported: otherwise the section answers before enumeration
        runs and an assertion would pass for the wrong reason.
        """

        real_stat = os.stat
        real_open = os.open

        def stat_call(path, *positional, dir_fd=None, **keywords):
            if dir_fd is not None and path in stat_errnos:
                number = stat_errnos[path]
                raise OSError(number, os.strerror(number))
            return real_stat(path, *positional, dir_fd=dir_fd, **keywords)

        def open_call(path, *positional, dir_fd=None, **keywords):
            if dir_fd is not None and path in open_errnos:
                number = open_errnos[path]
                raise OSError(number, os.strerror(number))
            return real_open(path, *positional, dir_fd=dir_fd, **keywords)

        @contextlib.contextmanager
        def armed():
            with patch.object(
                techstack_filesystem, "is_supported_platform", return_value=True
            ), patch.object(os, "stat", side_effect=stat_call), patch.object(
                os, "open", side_effect=open_call
            ):
                yield

        return armed()

    def truncate_at(self, directory_fd: int, name: str, size: int) -> None:
        """Create one regular file of exactly `size` bytes without writing them.

        The enumeration takes the size from the metadata call and no content
        is ever opened once an abort has suppressed `files`, so a sparse file
        is the same fixture as a written one at none of the cost.
        """

        handle = os.open(
            name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644, dir_fd=directory_fd
        )
        try:
            os.ftruncate(handle, size)
        finally:
            os.close(handle)

    def write_non_nfc_at(self, directory_fd: int, raw: bytes) -> str:
        """Create one in-bounds decomposed name from raw bytes, or skip."""

        name = os.fsdecode(raw)
        self.assertNotEqual(name, unicodedata.normalize("NFC", name))
        self.assertLessEqual(len(raw), lifecycle.SKILL_COMPONENT_BYTE_LIMIT)
        self.write_at(directory_fd, name)
        if name not in os.listdir(directory_fd):
            self.skipTest("this filesystem normalizes entry names")
        return name

    def build_abort_condition(
        self,
        key: str,
        directory_fd: int,
        prefix: str,
        stat_errnos: dict,
        open_errnos: dict,
        components: int = 4,
    ) -> None:
        """Make exactly one abort condition true, under one sort prefix.

        Every name is at most 20 bytes but for the 250-byte name the
        relative-path row needs, so this level's own 1,004-byte prefix keeps
        every other entry inside the 1,024-byte bound. `components` is the
        chain length, which the directory cap counts: every chain name was
        itself a directory observed at its parent level.
        """

        if key == "classify_unsupported":
            name = f"{prefix}_unsup"
            self.write_at(directory_fd, name)
            stat_errnos[name] = errno.EOPNOTSUPP
        elif key == "classify_resource":
            name = f"{prefix}_nomem"
            self.write_at(directory_fd, name)
            stat_errnos[name] = errno.ENOMEM
        elif key == "open_unsupported":
            name = f"{prefix}_unsupdir"
            self.mkdir_at(directory_fd, name)
            open_errnos[name] = errno.EOPNOTSUPP
        elif key == "open_resource":
            name = f"{prefix}_emfiledir"
            self.mkdir_at(directory_fd, name)
            open_errnos[name] = errno.EMFILE
        elif key == "name_byte_limit":
            # 1,004 + 250 = 1,254 relative bytes, on this same level.
            self.mkdir_at(directory_fd, prefix + "n" * 249)
        elif key == "name_invalid":
            self.write_non_nfc_at(directory_fd, os.fsencode(prefix) + b"e\xcc\x81.md")
        elif key == "entry_limit":
            self.add_files_at(directory_fd, prefix, 70)
        elif key == "depth_limit":
            # One directory on a level six components down: its own depth is
            # already the cap, so the child this name would need is refused.
            self.mkdir_at(directory_fd, f"{prefix}_deep")
        elif key == "directory_limit":
            # The chain's own components + the rest = the 65th directory here.
            for index in range(65 - components):
                self.mkdir_at(directory_fd, f"{prefix}d{index:02d}")
        elif key == "aggregate":
            for index in range(17):
                self.truncate_at(
                    directory_fd,
                    f"{prefix}_big{index:02d}",
                    lifecycle.SKILL_FILE_BYTE_LIMIT,
                )
        else:  # pragma: no cover - a condition without a fixture
            self.fail(f"no fixture builds the {key} condition")

    def pair_components(self, first: str, second: str) -> int:
        """Six chain components when the depth cap is one of the pair, else four."""

        return 6 if "depth_limit" in (first, second) else 4

    def expected_pair_row(self, first: str, second: str) -> str:
        """The registry minimum of the conditions section 16 makes applicable."""

        first_code, first_bounds, first_needs_open = self.ABORT_PAIR_CONDITIONS[first]
        second_code, _, second_needs_open = self.ABORT_PAIR_CONDITIONS[second]
        # A level deep enough to raise the depth cap refuses every open on it,
        # in either name order, because the depth check precedes the open
        # guard for the same entry.
        depth_capped = self.pair_components(first, second) == 6
        applicable = []
        if not (first_needs_open and depth_capped):
            applicable.append(first_code)
        if not (second_needs_open and (first_bounds or depth_capped)):
            applicable.append(second_code)
        order = [code for code, _ in AGENT_SKILL_EXPORT_DETAILS]
        return min(applicable, key=order.index)

    def assert_pair_row(self, first: str, second: str) -> str:
        """Build one ordered pair on one level and assert its reported row."""

        self.initialize()
        stat_errnos: dict[str, int] = {}
        open_errnos: dict[str, int] = {}
        components = self.pair_components(first, second)
        directory_fd = self.open_deep_level(components=components)
        try:
            self.build_abort_condition(
                first, directory_fd, "a", stat_errnos, open_errnos, components
            )
            self.build_abort_condition(
                second, directory_fd, "z", stat_errnos, open_errnos, components
            )
        finally:
            os.close(directory_fd)
        expected = self.expected_pair_row(first, second)
        with self.errno_on_names(stat_errnos, open_errnos):
            self.assert_code(expected)
        return expected

    def test_every_abort_pair_on_one_level_is_ranked_by_the_registry(self):
        """Both name orders of every co-constructible pair report one row.

        The pair is what the reported row must not depend on: each ordered
        variant is the same logical state with the two conditions' names
        exchanged, so a route that unwinds its level mid-way answers the two
        variants differently and fails here. Ten conditions are 45 unordered
        pairs and 90 ordered variants, counted here so that a condition
        dropped from the table cannot quietly shrink the matrix.
        """

        keys = sorted(self.ABORT_PAIR_CONDITIONS)
        self.assertEqual(10, len(keys))
        variants = 0
        for index, first in enumerate(keys):
            for second in keys[index + 1 :]:
                for ordered in ((first, second), (second, first)):
                    variants += 1
                    with self.subTest(first=ordered[0], last=ordered[1]):
                        self.setUp()
                        self.assert_pair_row(*ordered)
        self.assertEqual(90, variants)

    def deep_level_pair(self) -> Path:
        """Six short components; the level whose children exceed the depth cap.

        Short names so the whole pair stays far inside the 1,024-byte
        relative-path bound: the row this level decides is the depth cap, not
        a name row.
        """

        return self.nest_directories(self.managed_root, "d", 6)

    def test_the_capability_row_outranks_a_depth_cap_on_its_own_level(self):
        """Row 7 over row 17, with the depth-capped directory reached first.

        The depth cap trips on the level that holds the directory it refuses,
        so an entry sorting after it on that same level must still be
        classified and its section row must still outrank.
        """

        self.initialize()
        deep = self.deep_level_pair()
        (deep / "a_deep").mkdir()
        (deep / "z_unsup").write_text("x\n", encoding="utf-8")
        with self.errno_on(z_unsup=errno.EOPNOTSUPP):
            section = self.assert_code("UNSUPPORTED_SAFE_OPEN")
        self.assertEqual(
            "required safe-open primitives are unavailable", section["detail"]
        )

    def test_the_capability_row_outranks_a_depth_cap_reached_after_it(self):
        """The same level with the two names exchanged.

        The depth check is not guarded by `scan.bounded` — it costs no open —
        so both rows are observed in this order too and the answer is
        unchanged.
        """

        self.initialize()
        deep = self.deep_level_pair()
        (deep / "a_unsup").write_text("x\n", encoding="utf-8")
        (deep / "z_deep").mkdir()
        with self.errno_on(a_unsup=errno.EOPNOTSUPP):
            self.assert_code("UNSUPPORTED_SAFE_OPEN")

    # -- the fourth review's own reproductions -----------------------------
    #
    # Built the way the reviewer built them — on the managed root, with real
    # bytes and no injection where none is needed — rather than through the
    # matrix above, so the two flips it reported are owned by fixtures that
    # match its recipes exactly.

    def add_full_size_files(self, root: Path, prefix: str, count: int) -> None:
        """`count` regular files of exactly the 262,144-byte per-file cap."""

        for index in range(count):
            (root / f"{prefix}{index:02d}").write_bytes(
                b"x" * lifecycle.SKILL_FILE_BYTE_LIMIT
            )

    def test_the_entry_cap_outranks_the_aggregate_bound_with_the_bytes_first(self):
        """Row 15 over row 18, with no injection at all.

        17 files of exactly 262,144 bytes are 4,456,448 bytes and, with 60
        ordinary files beside them, 77 entries: both bounds are true of one
        level, and section 9 fixes the answer at the entry cap. An operator
        with a 4.2 MB, 77-file tree may not be told to shrink bytes or to
        delete files depending on which of their files sorts first.
        """

        self.initialize()
        self.add_full_size_files(self.managed_root, "a_big", 17)
        self.add_files(self.managed_root, "b", 60)
        section = self.assert_code("SKILL_ENTRY_LIMIT")
        self.assertEqual("skill file count exceeds 64", section["detail"])

    def test_the_entry_cap_outranks_the_aggregate_bound_with_the_bytes_last(self):
        """The same 77-entry, 4,456,448-byte level with the names exchanged."""

        self.initialize()
        self.add_files(self.managed_root, "a", 60)
        self.add_full_size_files(self.managed_root, "z_big", 17)
        self.assert_code("SKILL_ENTRY_LIMIT")

    def test_the_capability_row_outranks_the_aggregate_bound_sorting_last(self):
        """Row 7 over row 18: eleven registry places, on one level.

        A filesystem that cannot support the safe-open primitives at all is a
        permanent and actionable condition; being told instead that the tree
        is too large is the flip the fourth review reported.
        """

        self.initialize()
        self.add_full_size_files(self.managed_root, "a_big", 17)
        (self.managed_root / "z_unsup").write_text("x\n", encoding="utf-8")
        with self.errno_on(z_unsup=errno.EOPNOTSUPP):
            section = self.assert_code("UNSUPPORTED_SAFE_OPEN")
        self.assertEqual(
            "required safe-open primitives are unavailable", section["detail"]
        )

    def test_the_capability_row_outranks_the_aggregate_bound_sorting_first(self):
        """The same state with the failing entry reached first instead."""

        self.initialize()
        (self.managed_root / "a_unsup").write_text("x\n", encoding="utf-8")
        self.add_full_size_files(self.managed_root, "z_big", 17)
        with self.errno_on(a_unsup=errno.EOPNOTSUPP):
            self.assert_code("UNSUPPORTED_SAFE_OPEN")

    def test_a_refused_directory_open_is_ranked_with_a_peer_section_row(self):
        """Row 7 over row 8 when the resource row comes from `open_directory`.

        `EMFILE` surfaces on this route and only on it: the walk holds one
        descriptor per open level and `classify_entry` opens nothing. The
        capability row on a later name of the same level must still outrank
        it.
        """

        self.initialize()
        (self.managed_root / "a_emfile_dir").mkdir()
        (self.managed_root / "z_unsup").write_text("x\n", encoding="utf-8")
        with self.errno_on_names(
            {"z_unsup": errno.EOPNOTSUPP}, {"a_emfile_dir": errno.EMFILE}
        ):
            section = self.assert_code("UNSUPPORTED_SAFE_OPEN")
        self.assertEqual(
            "required safe-open primitives are unavailable", section["detail"]
        )

    def test_a_refused_directory_open_does_not_outrank_by_sorting_first(self):
        """The same state with the capability row reached first instead.

        The refused open is then never attempted — the capability row has
        already refused every descent — so row 7 is the only applicable row
        and the answer is unchanged.
        """

        self.initialize()
        (self.managed_root / "a_unsup").write_text("x\n", encoding="utf-8")
        (self.managed_root / "z_emfile_dir").mkdir()
        with self.errno_on_names(
            {"a_unsup": errno.EOPNOTSUPP}, {"z_emfile_dir": errno.EMFILE}
        ):
            self.assert_code("UNSUPPORTED_SAFE_OPEN")

    # -- byte-cap boundaries -----------------------------------------------
    #
    # One fixture at exactly the cap and one a single byte past it, both sized
    # in literals, so a cap that drifted by one moves the answer of one of the
    # pair. `SKILL_FILE_ROW_LIMIT` gets a literal only: the `len(union) > 128`
    # branch is unreachable while both sides are capped at 64 row entries and
    # that cap is ranked first, so no fixture can observe it.

    def test_every_section_three_cap_is_the_literal_the_registry_freezes(self):
        self.assertEqual(4096, lifecycle.SKILL_OUTPUT_PATH_BYTE_LIMIT)
        self.assertEqual(1024, lifecycle.SKILL_RELATIVE_PATH_BYTE_LIMIT)
        self.assertEqual(255, lifecycle.SKILL_COMPONENT_BYTE_LIMIT)
        self.assertEqual(262144, lifecycle.SKILL_FILE_BYTE_LIMIT)
        self.assertEqual(4194304, lifecycle.SKILL_AGGREGATE_BYTE_LIMIT)
        self.assertEqual(64, lifecycle.SKILL_ENTRY_COUNT_LIMIT)
        self.assertEqual(64, lifecycle.SKILL_DIRECTORY_COUNT_LIMIT)
        self.assertEqual(6, lifecycle.SKILL_MAX_DEPTH)
        self.assertEqual(128, lifecycle.SKILL_FILE_ROW_LIMIT)

    def test_every_shared_section_three_cap_equals_its_techstacks_model_twin(self):
        """The seven skill caps spelled in both modules are pinned equal.

        Seven of the nine caps above have a `brichan.techstacks.model` twin
        (`SKILL_OUTPUT_PATH_BYTE_LIMIT` and `SKILL_FILE_ROW_LIMIT` have none),
        and `PY-003` requires a value spelled in two modules to be pinned
        equal by a test. The literal pins — the test above for `lifecycle` and
        `test_numeric_constants_match_the_design` for `model` — already catch
        every one-sided edit. This test's own failure mode is the one they
        cannot see: a two-sided edit that moves the twins of a pair apart while
        each literal pin is updated to its own side's new value — divergence,
        not motion. Moving both twins to the same new value with both pins
        updated passes every test, correctly, because the two modules still
        agree and only the design literal has moved. The import is test-side
        only; `lifecycle` still does not import `techstacks` at module scope.
        """

        self.assertEqual(
            lifecycle.SKILL_RELATIVE_PATH_BYTE_LIMIT,
            techstack_model.RELATIVE_PATH_BYTE_MAX,
        )
        self.assertEqual(
            lifecycle.SKILL_COMPONENT_BYTE_LIMIT,
            techstack_model.PATH_COMPONENT_BYTE_MAX,
        )
        self.assertEqual(
            lifecycle.SKILL_FILE_BYTE_LIMIT,
            techstack_model.MANAGED_SKILL_FILE_BYTE_LIMIT,
        )
        self.assertEqual(
            lifecycle.SKILL_FILE_BYTE_LIMIT,
            techstack_model.EXPORTED_SKILL_FILE_BYTE_LIMIT,
        )
        self.assertEqual(
            lifecycle.SKILL_AGGREGATE_BYTE_LIMIT,
            techstack_model.SKILL_AGGREGATE_BYTE_LIMIT,
        )
        self.assertEqual(
            lifecycle.SKILL_ENTRY_COUNT_LIMIT, techstack_model.SKILL_ENTRY_LIMIT
        )
        self.assertEqual(
            lifecycle.SKILL_DIRECTORY_COUNT_LIMIT,
            techstack_model.SKILL_DIRECTORY_LIMIT,
        )
        self.assertEqual(
            lifecycle.SKILL_MAX_DEPTH, techstack_model.SKILL_DEPTH_LIMIT
        )

    def test_a_file_of_exactly_262144_bytes_still_compares(self):
        self.initialize()
        payload = b"x" * 262144
        (self.managed_root / "big.md").write_bytes(payload)
        (self.export_root / "big.md").write_bytes(payload)
        section = self.assert_code("EXPORT_CURRENT")
        row = self.rows(section)["big.md"]
        self.assertEqual("current", row["relation"])
        self.assertIsNotNone(row["managed_sha256"])

    def test_a_file_of_262145_bytes_is_over_the_per_file_cap(self):
        self.initialize()
        (self.managed_root / "big.md").write_bytes(b"x" * 262145)
        self.assert_code("MANAGED_SKILL_BYTE_LIMIT")

    def fill_managed_aggregate(self, total: int) -> None:
        """Grow the managed side to exactly `total` aggregate bytes."""

        present = sum(
            path.stat().st_size
            for path in self.managed_root.rglob("*")
            if path.is_file()
        )
        remaining = total - present
        self.assertGreater(remaining, 0)
        index = 0
        while remaining > 0:
            chunk = min(remaining, 262144)
            (self.managed_root / f"a{index:03d}.bin").write_bytes(b"x" * chunk)
            remaining -= chunk
            index += 1

    def test_an_aggregate_of_exactly_4194304_bytes_still_compares(self):
        self.initialize()
        self.fill_managed_aggregate(4194304)
        self.assert_code("EXPORT_MISSING")

    def test_an_aggregate_of_4194305_bytes_is_over_the_aggregate_cap(self):
        self.initialize()
        self.fill_managed_aggregate(4194305)
        self.assert_code("MANAGED_SKILL_AGGREGATE_BYTE_LIMIT")

    def test_a_relative_path_of_exactly_1024_bytes_still_compares(self):
        """1,004 bytes of prefix plus a 20-byte name: the cap, exactly."""

        self.initialize()
        directory_fd = self.open_deep_level()
        try:
            self.write_at(directory_fd, "p" * 20)
        finally:
            os.close(directory_fd)
        section = self.assert_code("EXPORT_MISSING")
        longest = max(
            len(row["relative_path"].encode("utf-8")) for row in section["files"]
        )
        self.assertEqual(1024, longest)

    def test_a_relative_path_of_1025_bytes_is_over_the_path_cap(self):
        self.initialize()
        directory_fd = self.open_deep_level()
        try:
            self.write_at(directory_fd, "p" * 21)
        finally:
            os.close(directory_fd)
        self.assert_code("SKILL_ENTRY_NAME_BYTE_LIMIT")

    # -- capability and helper outcomes -----------------------------------

    def test_an_unsupported_platform_makes_the_comparison_unavailable(self):
        self.initialize()
        with patch.object(
            techstack_filesystem, "is_supported_platform", return_value=False
        ):
            self.assert_code("UNSUPPORTED_SAFE_OPEN")

    def test_every_bounded_helper_outcome_keeps_its_own_detail_code(self):
        self.initialize()
        for observed, expected in (
            ("SAFE_OPEN_HELPER_BUSY", "SAFE_OPEN_HELPER_BUSY"),
            ("SAFE_OPEN_HELPER_TIMEOUT", "SAFE_OPEN_HELPER_TIMEOUT"),
            ("SAFE_OPEN_HELPER_FAILED", "SAFE_OPEN_HELPER_FAILED"),
            ("SAFE_OPEN_HELPER_LEAK", "SAFE_OPEN_HELPER_LEAK"),
            ("UNSUPPORTED_SAFE_OPEN", "UNSUPPORTED_SAFE_OPEN"),
            ("RESOURCE_LIMIT", "RESOURCE_LIMIT"),
        ):
            with self.subTest(observed=observed):
                with patch.object(
                    techstack_filesystem,
                    "read_bounded_regular",
                    return_value=techstack_filesystem.Observation(
                        code=observed
                    ),
                ):
                    self.assert_code(expected)

    def test_the_section_observation_map_keeps_every_code_separate(self):
        """A transient resource failure is never a permanent platform gap."""

        self.assertEqual(
            {
                "UNSUPPORTED_SAFE_OPEN": "UNSUPPORTED_SAFE_OPEN",
                "RESOURCE_LIMIT": "RESOURCE_LIMIT",
                "SAFE_OPEN_HELPER_BUSY": "SAFE_OPEN_HELPER_BUSY",
                "SAFE_OPEN_HELPER_TIMEOUT": "SAFE_OPEN_HELPER_TIMEOUT",
                "SAFE_OPEN_HELPER_FAILED": "SAFE_OPEN_HELPER_FAILED",
                "SAFE_OPEN_HELPER_LEAK": "SAFE_OPEN_HELPER_LEAK",
            },
            lifecycle._SKILL_SECTION_OUTCOMES,
        )

    def test_the_two_errno_classes_select_different_detail_codes(self):
        """The real errno table, not a hand-written observation code.

        Design section 3 gives the capability and resource classes the same
        side outcome, so only the section registry separates them.
        """

        self.initialize()
        real_stat = os.stat

        def refusing(number):
            def stat_call(path, *positional, dir_fd=None, **keywords):
                # Only the bounded reader passes `dir_fd`; every other doctor
                # section still observes the real filesystem.
                if dir_fd is not None:
                    raise OSError(number, os.strerror(number))
                return real_stat(path, *positional, dir_fd=dir_fd, **keywords)

            return stat_call

        for number, expected in (
            (errno.EMFILE, "RESOURCE_LIMIT"),
            (errno.ENFILE, "RESOURCE_LIMIT"),
            (errno.ENOMEM, "RESOURCE_LIMIT"),
            (errno.EINVAL, "UNSUPPORTED_SAFE_OPEN"),
            (errno.ENOTSUP, "UNSUPPORTED_SAFE_OPEN"),
            (errno.EOPNOTSUPP, "UNSUPPORTED_SAFE_OPEN"),
        ):
            with self.subTest(errno=number):
                # The platform predicates probe `os.stat` with a `dir_fd` too,
                # so they are answered before the enumeration is refused.
                with patch.object(
                    techstack_filesystem, "is_supported_platform", return_value=True
                ), patch.object(os, "stat", side_effect=refusing(number)):
                    section = self.assert_code(expected)
                self.assertEqual([], section["files"])

    # -- invariants -------------------------------------------------------

    def test_a_side_hash_is_present_only_for_a_regular_side(self):
        self.initialize()
        (self.export_root / "extra.md").write_text("extra\n", encoding="utf-8")
        (self.export_root / "references" / "commands.md").unlink()
        section = self.section()
        self.assertTrue(section["files"])
        for row in section["files"]:
            for side in ("managed", "exported"):
                status = row[f"{side}_status"]
                digest = row[f"{side}_sha256"]
                if status == "regular":
                    self.assertIsInstance(digest, str)
                    self.assertEqual(64, len(digest))
                    self.assertEqual(digest, digest.lower())
                else:
                    self.assertIsNone(digest, (side, status))

    def test_comparing_writes_nothing_to_either_tree(self):
        self.initialize()
        before = self.tree_snapshot()
        self.report()
        self.assertEqual(before, self.tree_snapshot())

    # -- the read-only guarantee, over every section state ------------------

    def prepare_export_state(self, code: str, stack: contextlib.ExitStack):
        """Build `code`'s state on a fresh target and return its driver."""

        oversized = b"x" * (lifecycle.SKILL_FILE_BYTE_LIMIT + 1)
        enormous = b"x" * (lifecycle.SKILL_AGGREGATE_BYTE_LIMIT + 1)
        if code == "SOURCE_CHECKOUT_NOT_APPLICABLE":
            self.initialize()
            return lambda: self.section(source=True)
        if code == "OUTPUT_PATH_BYTE_LIMIT":
            # The only row no real root can reach: a 4,100-byte project root.
            self.initialize()
            long_root = Path("/" + "d" * 4100)
            long_paths = ProjectPaths(
                tool_root=self.paths.tool_root,
                project_root=long_root,
                state_root=long_root / ".brichan",
            )
            return lambda: lifecycle.agent_skill_export_section(
                long_paths, source_mode=False, inspection=None
            )
        if code == "OUTPUT_PATH_NOT_CANONICAL":
            # The other row no real root can reach: an NFD absolute root.
            self.initialize()
            return lambda: self.output_path_section(
                Path("/e\u0301xport"), Path("/e\u0301xport/.brichan")
            )
        if code == "MANAGED_STATE_UNINITIALIZED":
            return self.section
        if code == "MANAGED_STATE_MALFORMED":
            self.initialize()
            (self.paths.state_root / "manifest.json").write_text(
                "{", encoding="utf-8"
            )
            return self.section
        if code == "MANAGED_STATE_INCOMPATIBLE":
            self.initialize()
            self._rewrite_manifest(schema_version=99)
            return self.section

        self.initialize()
        if code == "UNSUPPORTED_SAFE_OPEN":
            stack.enter_context(
                patch.object(
                    techstack_filesystem, "is_supported_platform", return_value=False
                )
            )
        elif code.startswith("SAFE_OPEN_HELPER_"):
            stack.enter_context(
                patch.object(
                    techstack_filesystem,
                    "read_bounded_regular",
                    return_value=techstack_filesystem.Observation(code=code),
                )
            )
        elif code == "RESOURCE_LIMIT":
            stack.enter_context(
                patch.object(
                    techstack_filesystem,
                    "read_bounded_regular",
                    return_value=techstack_filesystem.Observation(
                        code="RESOURCE_LIMIT"
                    ),
                )
            )
        elif code == "SKILL_ENTRY_NAME_BYTE_LIMIT":
            self.nest_over_long_relative_path()
        elif code == "SKILL_ENTRY_NAME_INVALID":
            name = "e\u0301.md"
            (self.managed_root / name).write_text("x\n", encoding="utf-8")
            if name not in os.listdir(self.managed_root):
                self.skipTest("this filesystem normalizes entry names")
        elif code == "SKILL_ENTRY_LIMIT":
            self.add_files(self.managed_root, "u", 62)
        elif code == "SKILL_DIRECTORY_LIMIT":
            self.add_directories(self.managed_root, "d", 64)
        elif code == "SKILL_DEPTH_LIMIT":
            self.nest_directories(self.managed_root, "d", 7)
        elif code == "MANAGED_SKILL_AGGREGATE_BYTE_LIMIT":
            (self.managed_root / "huge.md").write_bytes(enormous)
        elif code == "EXPORTED_SKILL_AGGREGATE_BYTE_LIMIT":
            (self.export_root / "huge.md").write_bytes(enormous)
        elif code == "MANAGED_SKILL_BYTE_LIMIT":
            (self.managed_root / "big.md").write_bytes(oversized)
        elif code == "EXPORTED_SKILL_BYTE_LIMIT":
            (self.export_root / "big.md").write_bytes(oversized)
        elif code == "SKILL_UNSAFE":
            target = self.export_root / "SKILL.md"
            target.unlink()
            target.symlink_to(self.managed_root / "SKILL.md")
        elif code == "SKILL_UNREADABLE":
            unreadable = self.managed_root / "extra.md"
            unreadable.write_text("secret\n", encoding="utf-8")
            shutil.copy2(unreadable, self.export_root / "extra.md")
            unreadable.chmod(0)
            self.addCleanup(unreadable.chmod, 0o644)
            if os.access(unreadable, os.R_OK):
                self.skipTest("this user can read a mode-0 file")
        elif code == "EXPORT_EXTRA":
            (self.export_root / "extra.md").write_text("extra\n", encoding="utf-8")
        elif code == "EXPORT_STALE":
            (self.export_root / "SKILL.md").write_text("drifted\n", encoding="utf-8")
        elif code == "EXPORT_MISSING":
            (self.export_root / "SKILL.md").unlink()
        elif code != "EXPORT_CURRENT":  # pragma: no cover - registry drift
            self.fail(f"no fixture builds the {code} state")
        return self.section

    def deep_level_components(self, components: int) -> list[int]:
        """Component byte lengths whose chain leaves a 1,004-byte prefix.

        The prefix a level of `components` chain names carries is the sum of
        their lengths plus one slash each, and every fixture below is written
        against the same 1,004 bytes: a 20-byte name on that level is exactly
        the 1,024-byte row cap and a 250-byte name is 1,254. Four components
        are 250 bytes each, six are 167, 167, 166, 166, 166, 166 — short
        enough that the deepest chain the depth cap allows still fits.
        """

        budget = 1004 - components
        base, remainder = divmod(budget, components)
        lengths = [base + (1 if index < remainder else 0) for index in range(components)]
        self.assertEqual(1004, sum(lengths) + components)
        self.assertLessEqual(max(lengths), lifecycle.SKILL_COMPONENT_BYTE_LIMIT)
        return lengths

    def open_deep_level(self, lead: str = "0", components: int = 4) -> int:
        """A chain `components` deep; returns a descriptor on the deepest.

        Descriptor-relative so the host `PATH_MAX` never bounds the fixture.
        That level's own relative prefix is 1,004 bytes whatever the component
        count, so every fixture built on it keeps the same byte budget. At six
        components the level sits at depth six, where any directory on it
        exceeds `SKILL_MAX_DEPTH`; at four it does not. `lead` is the first
        byte of the first component, which is how a caller sorts the whole
        chain before or after a sibling name. The caller closes the descriptor.
        """

        directory_fd = os.open(self.managed_root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            for index, length in enumerate(self.deep_level_components(components)):
                name = (lead if index == 0 else f"{index}") + "n" * (length - 1)
                os.mkdir(name, dir_fd=directory_fd)
                next_fd = os.open(
                    name, os.O_RDONLY | os.O_DIRECTORY, dir_fd=directory_fd
                )
                os.close(directory_fd)
                directory_fd = next_fd
        except OSError as error:  # pragma: no cover - filesystem dependent
            os.close(directory_fd)
            self.skipTest(f"cannot nest long components here: {error}")
        return directory_fd

    def nest_over_long_relative_path(
        self, lead: str = "0", over_long: str = "0"
    ) -> None:
        """Five 250-byte components: 1,254 relative bytes, five levels deep."""

        directory_fd = self.open_deep_level(lead)
        try:
            self.mkdir_at(directory_fd, over_long + "n" * 249)
        finally:
            os.close(directory_fd)

    def mkdir_at(self, directory_fd: int, name: str) -> None:
        """`mkdir` one name relative to an open descriptor, or skip."""

        try:
            os.mkdir(name, dir_fd=directory_fd)
        except OSError as error:  # pragma: no cover - filesystem dependent
            self.skipTest(f"cannot create a {len(name.encode())}-byte name: {error}")

    def write_at(self, directory_fd: int, name: str, payload: bytes = b"x\n") -> None:
        """Create one regular file relative to an open descriptor, or skip."""

        try:
            handle = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                0o644,
                dir_fd=directory_fd,
            )
        except OSError as error:  # pragma: no cover - filesystem dependent
            self.skipTest(f"cannot create a {len(name.encode())}-byte name: {error}")
        try:
            os.write(handle, payload)
        finally:
            os.close(handle)

    def add_files_at(self, directory_fd: int, prefix: str, count: int) -> None:
        for index in range(count):
            self.write_at(directory_fd, f"{prefix}{index:03d}.md")

    def add_non_nfc_file(self, raw: bytes) -> str:
        """Create one in-bounds decomposed name from raw bytes, or skip.

        The name is built from bytes rather than from a source literal so that
        no editor or normalizing toolchain can quietly compose it, and it is
        asserted non-NFC and inside the component bound before it is used.
        """

        name = os.fsdecode(raw)
        self.assertNotEqual(name, unicodedata.normalize("NFC", name))
        self.assertLessEqual(len(raw), lifecycle.SKILL_COMPONENT_BYTE_LIMIT)
        try:
            with open(os.path.join(os.fsencode(self.managed_root), raw), "wb") as file:
                file.write(b"x\n")
        except OSError as error:  # pragma: no cover - filesystem dependent
            self.skipTest(f"cannot create a non-NFC name here: {error}")
        if name not in os.listdir(self.managed_root):
            self.skipTest("this filesystem normalizes entry names")
        return name

    @contextlib.contextmanager
    def write_monitor(self):
        """Record every call to a write-capable primitive inside the block."""

        writes: list[str] = []
        write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        real_os_open = os.open
        real_io_open = builtins.open

        def guarded_os_open(path, flags, *positional, **keywords):
            # `subprocess` opens `/dev/null` read-write to wire the bounded
            # helper's stdin; that is the one write-mode open doctor may make
            # and it touches neither tree.
            if flags & write_flags and path != os.devnull:
                writes.append(f"os.open({path!r}, {flags:#o})")
            return real_os_open(path, flags, *positional, **keywords)

        def guarded_io_open(file, mode="r", *positional, **keywords):
            if isinstance(mode, str) and set(mode) & set("wxa+"):
                writes.append(f"open({file!r}, {mode!r})")
            return real_io_open(file, mode, *positional, **keywords)

        def guarded(name, real):
            def call(*positional, **keywords):
                writes.append(f"os.{name}{positional!r}")
                return real(*positional, **keywords)

            return call

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                patch.object(os, "open", side_effect=guarded_os_open)
            )
            # Platform predicate 4 asks whether `os.open` itself supports
            # `dir_fd`; the wrapper must inherit that or the whole section
            # would answer `UNSUPPORTED_SAFE_OPEN` under the monitor.
            stack.enter_context(
                patch.object(
                    os, "supports_dir_fd", frozenset(os.supports_dir_fd) | {os.open}
                )
            )
            stack.enter_context(
                patch("builtins.open", side_effect=guarded_io_open)
            )
            for name in ("mkdir", "rename", "unlink", "symlink", "chmod", "utime"):
                stack.enter_context(
                    patch.object(
                        os, name, side_effect=guarded(name, getattr(os, name))
                    )
                )
            yield writes

    def tree_metadata(self) -> dict[str, tuple]:
        """Contents *and* mode, inode, size, and both timestamps, per path.

        Descriptor-relative, because one section state deliberately nests a
        relative path longer than this host's `PATH_MAX`.
        """

        metadata: dict[str, tuple] = {}
        for root in (self.paths.state_root, self.paths.project_root / ".agents"):
            try:
                root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            except OSError:
                continue
            try:
                self.collect_metadata(
                    root_fd, str(root.relative_to(self.paths.project_root)), metadata
                )
            finally:
                os.close(root_fd)
        return metadata

    def collect_metadata(
        self, directory_fd: int, prefix: str, metadata: dict[str, tuple]
    ) -> None:
        for name in sorted(os.listdir(directory_fd)):
            observed = os.lstat(name, dir_fd=directory_fd)
            key = f"{prefix}/{name}"
            content = b"<not a readable regular file>"
            if stat.S_ISREG(observed.st_mode):
                try:
                    handle = os.open(name, os.O_RDONLY, dir_fd=directory_fd)
                except OSError:
                    pass
                else:
                    try:
                        content = b"".join(iter(lambda: os.read(handle, 65536), b""))
                    finally:
                        os.close(handle)
            metadata[key] = (
                observed.st_mode,
                observed.st_ino,
                observed.st_size,
                observed.st_mtime_ns,
                observed.st_ctime_ns,
                content,
            )
            if stat.S_ISDIR(observed.st_mode):
                child_fd = os.open(
                    name, os.O_RDONLY | os.O_DIRECTORY, dir_fd=directory_fd
                )
                try:
                    self.collect_metadata(child_fd, key, metadata)
                finally:
                    os.close(child_fd)

    def test_no_section_state_lets_doctor_write_or_touch_either_tree(self):
        """All 27 rows, under a monitor on every write-capable primitive."""

        for code, _ in AGENT_SKILL_EXPORT_DETAILS:
            with self.subTest(code=code):
                self.setUp()
                with contextlib.ExitStack() as stack:
                    drive = self.prepare_export_state(code, stack)
                    before = self.tree_metadata()
                    with self.write_monitor() as writes:
                        section = drive()
                self.assertEqual(code, section["detail_code"], section)
                self.assertEqual([], writes)
                self.assertEqual(before, self.tree_metadata())

    def test_every_nonnull_output_path_obeys_the_absolute_path_grammar(self):
        """Design section 9's grammar, over all 27 rows, not the reachable few.

        A path is either null or strict-NFC 1-4,096 UTF-8 bytes, so a consumer
        validating `agent_skill_export` against the schema never sees a
        section Brichan itself reports as sound.
        """

        for code, _ in AGENT_SKILL_EXPORT_DETAILS:
            with self.subTest(code=code):
                self.setUp()
                with contextlib.ExitStack() as stack:
                    section = self.prepare_export_state(code, stack)()
                self.assertEqual(code, section["detail_code"], section)
                for key in ("path", "managed_path"):
                    value = section[key]
                    if value is None:
                        continue
                    encoded = value.encode("utf-8")
                    self.assertGreaterEqual(len(encoded), 1, (code, key))
                    self.assertLessEqual(
                        len(encoded), lifecycle.SKILL_OUTPUT_PATH_BYTE_LIMIT
                    )
                    self.assertEqual(
                        unicodedata.normalize("NFC", value), value, (code, key)
                    )

    def tree_snapshot(self) -> dict[str, bytes]:
        snapshot: dict[str, bytes] = {}
        for root in (self.paths.state_root, self.paths.project_root / ".agents"):
            for path in sorted(root.rglob("*")):
                key = str(path.relative_to(self.paths.project_root))
                snapshot[key] = (
                    path.read_bytes() if path.is_file() and not path.is_symlink()
                    else b"<not a regular file>"
                )
        return snapshot

    def test_a_stale_export_is_diagnosed_and_never_overwritten(self):
        self.initialize()
        drifted = b"user owned\n"
        (self.export_root / "SKILL.md").write_bytes(drifted)
        self.assert_code("EXPORT_STALE")
        # Neither a second diagnosis nor a second init touches the bytes.
        self.report()
        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertEqual(drifted, (self.export_root / "SKILL.md").read_bytes())
        self.assertNotIn("create .agents/skills/herdr-orchestration/SKILL.md", lines)
        self.assert_code("EXPORT_STALE")

    def test_user_backup_removal_and_re_export_produces_current_hashes(self):
        self.initialize()
        (self.export_root / "SKILL.md").write_bytes(b"user owned\n")
        section = self.assert_code("EXPORT_STALE")
        self.assertEqual(
            "invalid",
            section["status"],
        )
        # Exactly the two rendered commands, run by the user, in order.
        backup = self.temp_path / "backup"
        shutil.copytree(self.export_root, backup)
        shutil.rmtree(self.export_root)
        code, _ = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        section = self.assert_code("EXPORT_CURRENT")
        for row in section["files"]:
            self.assertEqual(row["managed_sha256"], row["exported_sha256"])
        self.assertEqual(b"user owned\n", (backup / "SKILL.md").read_bytes())


class DoctorExitAndOkMatrixTest(unittest.TestCase):
    """Design section 9's complete Cartesian formulas, not a sampled subset."""

    DEPENDENCY_SETS = (
        (),
        ("codex",),
        ("herdr",),
        ("git",),
        ("codex", "herdr"),
        ("codex", "git"),
        ("herdr", "git"),
        ("codex", "herdr", "git"),
    )

    def setUp(self):
        self.paths = ProjectPaths(
            tool_root=Path("/tool"),
            project_root=Path("/repo"),
            state_root=Path("/repo/.brichan"),
        )

    def export_section(self, code: str) -> dict:
        status, relation, nonnull, _ = AGENT_SKILL_EXPORT_ROWS[code]
        return {
            "status": status,
            "mode": "installed",
            "relation": relation,
            "path": "/repo/.agents/skills/herdr-orchestration" if nonnull else None,
            "managed_path": "/repo/.brichan/skills/herdr-orchestration"
            if nonnull
            else None,
            "files": [],
            "detail_code": code,
            "detail": dict(AGENT_SKILL_EXPORT_DETAILS)[code],
        }

    def run_report(self, *, state: StateKind, missing: tuple[str, ...], code: str):
        inspection = Inspection(state, "fixture")
        healthy_section = {"status": "ok", "files": {}, "detail": "ok"}

        def dependency(name, *, required):
            status = "missing" if name in missing else "ok"
            return {
                "status": status,
                "path": None if status == "missing" else f"/opt/{name}",
                "required": required,
                "detail": name,
            }

        with patch.object(
            lifecycle, "inspect_project", return_value=inspection
        ), patch.object(
            lifecycle, "_dependency_check", side_effect=dependency
        ), patch.object(
            lifecycle, "_git_section", return_value={"status": "ok", "detail": "ok"}
        ), patch.object(
            lifecycle, "_paths_section", return_value=healthy_section
        ), patch.object(
            lifecycle,
            "_routing_section",
            return_value={"status": "ok", "detail": "ok"},
        ), patch.object(
            lifecycle, "_component_problem", return_value=None
        ), patch.object(
            lifecycle,
            "agent_skill_export_section",
            return_value=self.export_section(code),
        ):
            return doctor_report(self.paths)

    def test_installed_exits_are_owned_by_state_and_codex_alone(self):
        for state in StateKind:
            for missing in self.DEPENDENCY_SETS:
                for code, _ in AGENT_SKILL_EXPORT_DETAILS:
                    with self.subTest(state=state, missing=missing, code=code):
                        exit_code, report = self.run_report(
                            state=state, missing=missing, code=code
                        )
                        if state is not StateKind.HEALTHY:
                            expected_exit = EXIT_CODES[state]
                        else:
                            expected_exit = 4 if "codex" in missing else 0
                        self.assertEqual(expected_exit, exit_code)
                        expected_ok = (
                            state is StateKind.HEALTHY
                            and not missing
                            and AGENT_SKILL_EXPORT_ROWS[code][0] == "ok"
                        )
                        self.assertEqual(expected_ok, report["ok"])

    def source_report(self, *, missing: tuple[str, ...]):
        def dependency(name, *, required):
            status = "missing" if name in missing else "ok"
            return {
                "status": status,
                "path": None,
                "required": required,
                "detail": name,
            }

        healthy_section = {"status": "ok", "files": {}, "detail": "ok"}
        with patch.object(
            lifecycle, "_dependency_check", side_effect=dependency
        ), patch.object(
            lifecycle, "_git_section", return_value={"status": "ok", "detail": "ok"}
        ), patch.object(
            lifecycle, "_paths_section", return_value=healthy_section
        ), patch.object(
            lifecycle,
            "_routing_section",
            return_value={"status": "ok", "detail": "ok"},
        ):
            return doctor_report(self.paths, checkout_root=self.paths.project_root)

    def test_source_exits_never_depend_on_the_export_section(self):
        for missing in self.DEPENDENCY_SETS:
            with self.subTest(missing=missing):
                exit_code, report = self.source_report(missing=missing)
                section = report["agent_skill_export"]
                self.assertEqual(
                    "SOURCE_CHECKOUT_NOT_APPLICABLE", section["detail_code"]
                )
                if not missing:
                    self.assertEqual(0, exit_code)
                elif missing == ("codex",):
                    self.assertEqual(4, exit_code)
                else:
                    self.assertEqual(2, exit_code)
                self.assertEqual(not missing, report["ok"])


if __name__ == "__main__":
    unittest.main()
