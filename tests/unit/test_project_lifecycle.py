import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.lifecycle import (
    AGENT_ENTRY_PATHS,
    AGENT_SKILLS_DIR,
    CHECKOUT_MEMORY_PATHS,
    CHECKOUT_POLICY_PATHS,
    DOCTOR_SCHEMA_VERSION,
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
from brichan.project import ProjectError, find_git_root, project_paths


REPORT_KEYS = {
    "schema_version",
    "ok",
    "repository",
    "git",
    "policies",
    "model_routing",
    "project_memory",
    "dependencies",
}
STATUSES = {"ok", "missing", "invalid", "unavailable"}


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
    """`init --init-agents` exports the Herdr skill for direct codex runs."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "target"
        self.root.mkdir()
        (self.root / ".git").mkdir()
        self.paths = project_paths(explicit=self.root)

    def test_skill_export_contract_names_the_codex_discovery_dir(self):
        self.assertEqual(".agents/skills/herdr-orchestration", AGENT_SKILLS_DIR)

    def test_default_init_never_creates_or_lists_the_agents_dir(self):
        code, lines = initialize_project(self.paths, apply=False)
        self.assertEqual(0, code)
        self.assertNotIn(
            "create .agents/skills/herdr-orchestration/SKILL.md", lines
        )
        code, lines = initialize_project(self.paths, apply=True)
        self.assertEqual(0, code)
        self.assertNotIn(
            "create .agents/skills/herdr-orchestration/SKILL.md", lines
        )
        self.assertFalse((self.root / ".agents").exists())

    def test_dry_run_lists_missing_skill_export_without_writing(self):
        code, lines = initialize_project(
            self.paths, apply=False, include_agents=True
        )
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
        code, lines = initialize_project(
            self.paths, apply=True, include_agents=True
        )
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

        code, lines = initialize_project(
            self.paths, apply=True, include_agents=True
        )
        self.assertEqual(0, code)
        self.assertNotIn(
            "create .agents/skills/herdr-orchestration/SKILL.md", lines
        )
        self.assertEqual(b"user skill\n", marker.read_bytes())

    def test_healthy_project_gains_missing_skill_export_on_reinit(self):
        initialize_project(self.paths, apply=True)

        code, lines = initialize_project(
            self.paths, apply=True, include_agents=True
        )
        self.assertEqual(0, code)
        self.assertIn("create .agents/skills/herdr-orchestration/SKILL.md", lines)
        self.assertTrue((self.root / AGENT_SKILLS_DIR / "SKILL.md").is_file())

        code, lines = initialize_project(
            self.paths, apply=True, include_agents=True
        )
        self.assertEqual(0, code)
        self.assertTrue(lines[0].startswith("no changes:"))

    def test_cli_flag_plumbs_through_to_the_export(self):
        from brichan.cli import runtime as cli_runtime

        with contextlib.redirect_stdout(io.StringIO()):
            code = cli_runtime.main(
                ["init", "--apply", "--init-agents", "--project", str(self.root)]
            )
        self.assertEqual(0, code)
        self.assertTrue((self.root / AGENT_SKILLS_DIR / "SKILL.md").is_file())

    def test_cli_default_leaves_agents_dir_absent(self):
        from brichan.cli import runtime as cli_runtime

        with contextlib.redirect_stdout(io.StringIO()):
            code = cli_runtime.main(
                ["init", "--apply", "--project", str(self.root)]
            )
        self.assertEqual(0, code)
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


if __name__ == "__main__":
    unittest.main()
