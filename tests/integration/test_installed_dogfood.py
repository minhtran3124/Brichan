import hashlib
import json
import os
import stat
import subprocess
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class InstalledDogfoodTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build_temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.build_temp.cleanup)
        cls.build_root = Path(cls.build_temp.name)
        wheel_dir = cls.build_root / "wheel"
        wheel_dir.mkdir()
        source_root = cls.build_root / "source"
        source_root.mkdir()
        # README_PYPI.md is the packaged long description named by
        # pyproject.toml, so the copied tree is not buildable without it.
        for name in ("pyproject.toml", "README.md", "README_PYPI.md", "LICENSE"):
            shutil.copy2(ROOT / name, source_root / name)
        shutil.copytree(ROOT / "src", source_root / "src")
        candidates = (
            sys.executable,
            *(shutil.which(name) for name in ("python3.13", "python3.12", "python3.11")),
        )
        build_python = None
        for candidate in candidates:
            if candidate is None:
                continue
            result = subprocess.run(
                [candidate, "-c", "import setuptools, wheel"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                build_python = candidate
                break
        if build_python is None:
            raise unittest.SkipTest("no offline Python wheel backend is installed")
        cls.build_python = build_python

        result = subprocess.run(
            [
                build_python,
                "-m",
                "pip",
                "wheel",
                ".",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir",
                str(wheel_dir),
            ],
            cwd=source_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AssertionError(f"wheel build failed:\n{result.stdout}\n{result.stderr}")
        wheels = list(wheel_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise AssertionError(f"expected one wheel, found: {wheels}")
        cls.wheel = wheels[0]

        cls.venv = cls.build_root / "venv"
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(cls.venv)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AssertionError(f"venv creation failed: {result.stderr}")
        cls.python = cls.venv / "bin" / "python"
        cls.brichan = cls.venv / "bin" / "brichan"
        cls.herdr_launcher = cls.venv / "bin" / "brichan-herdr-agent-start"
        result = subprocess.run(
            [
                str(cls.python),
                "-m",
                "pip",
                "install",
                "--no-deps",
                str(cls.wheel),
            ],
            cwd=cls.build_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AssertionError(f"wheel install failed:\n{result.stdout}\n{result.stderr}")

        cls.venv_without_pip = cls.build_root / "venv-without-pip"
        result = subprocess.run(
            [sys.executable, "-m", "venv", "--without-pip", str(cls.venv_without_pip)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AssertionError(f"pip-less venv creation failed: {result.stderr}")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.temp_path = Path(self.temporary.name)
        self.target = self.temp_path / "target"
        self.target.mkdir()
        self.resolved_target = self.target.resolve()
        (self.target / ".git").mkdir()
        (self.target / "AGENTS.md").write_bytes(b"target agents\n")
        (self.target / "CLAUDE.md").write_bytes(b"target claude\n")
        (self.target / "provider.json").write_bytes(b'{"provider":"user"}\n')
        self.original_root_files = {
            name: (self.target / name).read_bytes()
            for name in ("AGENTS.md", "CLAUDE.md", "provider.json")
        }

        self.fake_bin = self.temp_path / "fake-bin"
        self.fake_bin.mkdir()
        self.capture = self.temp_path / "codex-capture.json"
        fake_codex = self.fake_bin / "codex"
        fake_codex.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "with open(os.environ['FAKE_CODEX_CAPTURE'], 'w', encoding='utf-8') as out:\n"
            "    json.dump({'argv': sys.argv[1:], 'cwd': os.getcwd()}, out)\n",
            encoding="utf-8",
        )
        fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IXUSR)

        # `doctor` only resolves herdr on PATH; it never executes it.
        fake_herdr = self.fake_bin / "herdr"
        fake_herdr.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        fake_herdr.chmod(fake_herdr.stat().st_mode | stat.S_IXUSR)

        hostile_bin = self.target / "bin"
        hostile_bin.mkdir()
        self.hostile_marker = self.temp_path / "hostile-ran"
        hostile = hostile_bin / "brichan-codex"
        hostile.write_text(
            f"#!/bin/sh\nprintf TARGET_WRAPPER_EXECUTED > "
            f"'{self.hostile_marker}'\nexit 91\n",
            encoding="utf-8",
        )
        hostile.chmod(hostile.stat().st_mode | stat.S_IXUSR)

    def environment(self):
        environment = os.environ.copy()
        for name in (
            "BRICHAN_ROOT",
            "BRICHAN_RUNTIME",
            "BRICHAN_MODEL_ROUTING_FILE",
            "BRICHAN_CLAUDE_COORDINATOR_MODEL",
            "PYTHONPATH",
        ):
            environment.pop(name, None)
        environment["PATH"] = (
            f"{self.fake_bin}{os.pathsep}{self.venv / 'bin'}"
            f"{os.pathsep}{environment['PATH']}"
        )
        environment["FAKE_CODEX_CAPTURE"] = str(self.capture)
        return environment

    def run_brichan(self, *arguments):
        return subprocess.run(
            [str(self.brichan), *arguments],
            cwd=self.temp_path,
            env=self.environment(),
            check=False,
            capture_output=True,
            text=True,
        )

    def state_snapshot(self):
        state = self.target / ".brichan"
        return {
            path.relative_to(state).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in state.rglob("*")
            if path.is_file()
        }

    def test_wheel_contains_every_runtime_resource(self):
        with zipfile.ZipFile(self.wheel) as archive:
            names = set(archive.namelist())
        required_suffixes = (
            "brichan/resources/dogfood_v1/config/model-routing.json",
            "brichan/resources/dogfood_v1/policy/bootstrap.md",
            "brichan/resources/dogfood_v1/policy/identity.md",
            "brichan/resources/dogfood_v1/policy/operating-principles.md",
            "brichan/resources/dogfood_v1/policy/memory-policy.md",
            "brichan/resources/dogfood_v1/skills/herdr-orchestration/SKILL.md",
            "brichan/resources/dogfood_v1/project-memory/main/overview.md",
            "brichan/resources/dogfood_v1/agent-entry/AGENTS.md",
            "brichan/resources/dogfood_v1/agent-entry/CLAUDE.md",
        )
        for suffix in required_suffixes:
            self.assertTrue(any(name.endswith(suffix) for name in names), suffix)

    def test_installer_runs_outside_checkout_without_activation(self):
        install_root = self.temp_path / "installed-tool"
        command_dir = self.temp_path / "commands"
        environment = self.environment()
        environment.pop("VIRTUAL_ENV", None)
        environment["PATH"] = (
            f"{command_dir}{os.pathsep}{self.fake_bin}"
            f"{os.pathsep}{environment['PATH']}"
        )

        result = subprocess.run(
            [
                str(ROOT / "scripts/install-brichan"),
                "--install-root",
                str(install_root),
                "--bin-dir",
                str(command_dir),
                "--python",
                str(self.build_python),
            ],
            cwd=self.target,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("No virtualenv activation is required.", result.stdout)
        self.assertFalse((self.target / ".brichan").exists())

        commands = (
            "brichan",
            "brichan-codex",
            "brichan-claude",
            "brichan-herdr-agent-start",
            "brichan-validate-receipts",
        )
        for command_name in commands:
            command_link = command_dir / command_name
            self.assertTrue(command_link.is_symlink(), command_name)
            self.assertEqual(
                (install_root / "venv/bin" / command_name).resolve(),
                command_link.resolve(),
            )

        result = subprocess.run(
            [
                "brichan",
                "init",
                "--apply",
                "--project",
                str(self.target),
            ],
            cwd=self.target,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue((self.target / ".brichan/manifest.json").is_file())
        self.assertNotIn("VIRTUAL_ENV", environment)
        self.assertFalse((ROOT / "build").exists())
        self.assertFalse(any((ROOT / "src").glob("*.egg-info")))

    def test_installer_rejects_build_python_without_pip(self):
        install_root = self.temp_path / "installed-tool"
        command_dir = self.temp_path / "commands"
        environment = self.environment()
        environment.pop("VIRTUAL_ENV", None)
        environment["PATH"] = (
            f"{command_dir}{os.pathsep}{self.fake_bin}"
            f"{os.pathsep}{environment['PATH']}"
        )

        # self.build_python genuinely has pip, setuptools, venv, and wheel.
        # Hide only pip from importlib.util.find_spec so this regression is
        # specific to the pip requirement, not to setuptools/venv/wheel.
        site_dir = self.temp_path / "hide-pip-site"
        site_dir.mkdir()
        (site_dir / "sitecustomize.py").write_text(
            "import importlib.util\n"
            "_find_spec = importlib.util.find_spec\n"
            "def find_spec(name, *args, **kwargs):\n"
            "    if name == 'pip':\n"
            "        return None\n"
            "    return _find_spec(name, *args, **kwargs)\n"
            "importlib.util.find_spec = find_spec\n",
            encoding="utf-8",
        )
        environment["PYTHONPATH"] = str(site_dir)

        result = subprocess.run(
            [
                str(ROOT / "scripts/install-brichan"),
                "--install-root",
                str(install_root),
                "--bin-dir",
                str(command_dir),
                "--python",
                str(self.build_python),
            ],
            cwd=self.target,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("pip", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((install_root / "venv").exists())

    def test_installer_rejects_existing_venv_without_pip(self):
        install_root = self.temp_path / "installed-tool"
        command_dir = self.temp_path / "commands"
        environment = self.environment()
        environment.pop("VIRTUAL_ENV", None)
        environment["PATH"] = (
            f"{command_dir}{os.pathsep}{self.fake_bin}"
            f"{os.pathsep}{environment['PATH']}"
        )

        venv_dir = install_root / "venv"
        shutil.copytree(self.venv_without_pip, venv_dir, symlinks=True)

        result = subprocess.run(
            [
                str(ROOT / "scripts/install-brichan"),
                "--install-root",
                str(install_root),
                "--bin-dir",
                str(command_dir),
                "--python",
                str(self.build_python),
            ],
            cwd=self.target,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("pip", result.stderr)
        self.assertIn(str(venv_dir), result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_installed_init_status_doctor_and_direct_launch(self):
        result = self.run_brichan("status", "--project", str(self.target))
        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stdout.startswith("uninitialized:"))

        result = self.run_brichan(
            "init", "--dry-run", "--project", str(self.target)
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("dry-run: zero writes", result.stdout)
        self.assertFalse((self.target / ".brichan").exists())

        result = self.run_brichan("init", "--apply", "--project", str(self.target))
        self.assertEqual(0, result.returncode, result.stderr)
        before = self.state_snapshot()
        self.assertTrue(before)
        manifest = json.loads(
            (self.target / ".brichan/manifest.json").read_text(encoding="utf-8")
        )
        expected_footprint = {
            "manifest.json",
            *manifest["resources"],
            *manifest["mutable_paths"],
        }
        self.assertEqual(expected_footprint, set(before))
        for name, content in self.original_root_files.items():
            self.assertEqual(content, (self.target / name).read_bytes())

        result = self.run_brichan("init", "--apply", "--project", str(self.target))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("no changes:", result.stdout)
        self.assertEqual(before, self.state_snapshot())

        result = self.run_brichan("status", "--project", str(self.target))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("healthy:"))
        result = self.run_brichan("doctor", "--project", str(self.target))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("dependencies: OK", result.stdout)

        result = self.run_brichan(
            "run", "--project", str(self.target), "--", "--help"
        )
        self.assertEqual(0, result.returncode, result.stderr)
        capture = json.loads(self.capture.read_text(encoding="utf-8"))
        self.assertEqual(str(self.resolved_target), capture["cwd"])
        self.assertEqual(str(self.resolved_target), capture["argv"][1])
        self.assertIn("agents.enabled=false", capture["argv"])
        self.assertIn("multi_agent", capture["argv"])
        self.assertIn("multi_agent_v2", capture["argv"])
        self.assertTrue(
            any(
                item.startswith("developer_instructions=")
                and "You are Brichan" in item
                for item in capture["argv"]
            )
        )
        self.assertTrue(
            any(
                item.startswith("skills.config=")
                and str(
                    self.resolved_target / ".brichan/skills/herdr-orchestration"
                )
                in item
                for item in capture["argv"]
            )
        )
        self.assertFalse(self.hostile_marker.exists())

        result = self.run_brichan(
            "run",
            "--project",
            str(self.target),
            "--",
            "--dangerously-bypass-approvals-and-sandbox",
            "--dangerously-bypass-hook-trust",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        literal_capture = json.loads(self.capture.read_text(encoding="utf-8"))
        self.assertEqual(
            [
                "--",
                "--dangerously-bypass-approvals-and-sandbox",
                "--dangerously-bypass-hook-trust",
            ],
            literal_capture["argv"][-3:],
        )

        marker_config = self.target / "config"
        marker_config.mkdir()
        shutil.copy2(
            self.target / ".brichan/config/model-routing.json",
            marker_config / "model-routing.json",
        )
        (self.target / "src/brichan").mkdir(parents=True)
        root_wrapper = self.target / "bin/brichan"
        root_wrapper.write_text(
            f"#!/bin/sh\nprintf TARGET_WRAPPER_EXECUTED > '{self.hostile_marker}'\n"
            "exit 92\n",
            encoding="utf-8",
        )
        root_wrapper.chmod(root_wrapper.stat().st_mode | stat.S_IXUSR)

        spoof_environment = self.environment()
        spoof_environment["BRICHAN_ROOT"] = str(self.target)
        result = subprocess.run(
            [str(self.brichan), "--help"],
            cwd=self.target,
            env=spoof_environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(self.hostile_marker.exists())
        spoof_capture = json.loads(self.capture.read_text(encoding="utf-8"))
        self.assertEqual(str(self.resolved_target), spoof_capture["cwd"])

        external_routing = self.temp_path / "external-routing.json"
        external_payload = json.loads(
            (
                self.target / ".brichan/config/model-routing.json"
            ).read_text(encoding="utf-8")
        )
        external_payload["routes"]["scan"]["model"] = "external-checkout-model"
        external_routing.write_text(json.dumps(external_payload), encoding="utf-8")
        herdr_environment = self.environment()
        herdr_environment["BRICHAN_MODEL_ROUTING_FILE"] = str(external_routing)
        result = subprocess.run(
            [
                str(self.herdr_launcher),
                "brichan-installed-dry-run",
                "--cwd",
                str(self.target),
                "--route",
                "scan",
                "--json",
            ],
            cwd=self.temp_path,
            env=herdr_environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        route = json.loads(result.stdout)
        self.assertTrue(route["dry_run"])
        self.assertEqual("codex", route["resolved"]["runtime"])
        self.assertEqual("gpt-5.6-luna", route["resolved"]["model"])
        self.assertNotIn("external-checkout-model", route["command"])

    def test_installed_status_reports_malformed_and_incompatible(self):
        result = self.run_brichan("init", "--apply", "--project", str(self.target))
        self.assertEqual(0, result.returncode, result.stderr)
        manifest_path = self.target / ".brichan" / "manifest.json"
        original = manifest_path.read_text(encoding="utf-8")

        manifest_path.write_text("{", encoding="utf-8")
        result = self.run_brichan("status", "--project", str(self.target))
        self.assertEqual(2, result.returncode)
        self.assertTrue(result.stdout.startswith("malformed:"))

        payload = json.loads(original)
        payload["schema_version"] = 2
        manifest_path.write_text(json.dumps(payload), encoding="utf-8")
        result = self.run_brichan("doctor", "--project", str(self.target))
        self.assertEqual(3, result.returncode)
        self.assertIn("repository: INVALID", result.stdout)
        self.assertIn("schema_version 2 is not supported", result.stdout)

    def test_installed_dangling_state_and_apply_failure_have_no_traceback(self):
        missing_state = self.temp_path / "missing-state"
        (self.target / ".brichan").symlink_to(
            missing_state, target_is_directory=True
        )
        result = self.run_brichan("status", "--project", str(self.target))
        self.assertEqual(2, result.returncode)
        self.assertIn(".brichan must not be a symlink", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

        result = self.run_brichan("init", "--apply", "--project", str(self.target))
        self.assertEqual(2, result.returncode)
        self.assertIn(".brichan must not be a symlink", result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(missing_state.exists())

        (self.target / ".brichan").unlink()
        original_mode = stat.S_IMODE(self.target.stat().st_mode)
        self.target.chmod(0o500)
        try:
            result = self.run_brichan(
                "init", "--apply", "--project", str(self.target)
            )
        finally:
            self.target.chmod(original_mode)
        self.assertEqual(2, result.returncode)
        self.assertIn("initialization failed:", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_installed_inaccessible_state_is_malformed_without_traceback(self):
        result = self.run_brichan("init", "--apply", "--project", str(self.target))
        self.assertEqual(0, result.returncode, result.stderr)
        state = self.target / ".brichan"
        original_mode = stat.S_IMODE(state.stat().st_mode)
        state.chmod(0)
        try:
            probes = (
                ("status",),
                ("doctor",),
                ("init", "--apply"),
            )
            results = [
                self.run_brichan(*probe, "--project", str(self.target))
                for probe in probes
            ]
        finally:
            state.chmod(original_mode)

        for result in results:
            self.assertEqual(2, result.returncode)
            self.assertIn("cannot inspect project state", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

    def doctor_json(self, *arguments, codex=True):
        environment = self.environment()
        if not codex:
            # Drop the fake codex without losing the interpreter or git.
            environment["PATH"] = os.pathsep.join(
                [str(self.venv / "bin"), "/usr/bin", "/bin"]
            )
        result = subprocess.run(
            [str(self.brichan), "doctor", "--json", *arguments],
            cwd=self.temp_path,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual("", result.stderr)
        self.assertTrue(result.stdout.endswith("}\n"), repr(result.stdout[-20:]))
        return result.returncode, json.loads(result.stdout)

    def test_installed_doctor_json_reports_the_managed_footprint(self):
        code, report = self.doctor_json("--project", str(self.target))
        self.assertEqual(1, code)
        self.assertEqual(
            {
                "schema_version",
                "ok",
                "repository",
                "git",
                "policies",
                "model_routing",
                "project_memory",
                "dependencies",
            },
            set(report),
        )
        self.assertEqual(1, report["schema_version"])
        self.assertEqual("installed_project", report["repository"]["kind"])
        self.assertEqual(str(self.resolved_target), report["repository"]["root"])
        self.assertEqual("missing", report["repository"]["status"])
        self.assertFalse(report["ok"])
        self.assertFalse(self.target.joinpath(".brichan").exists())

        result = self.run_brichan("init", "--apply", "--project", str(self.target))
        self.assertEqual(0, result.returncode, result.stderr)
        before = self.state_snapshot()
        root_files_before = {
            name: (self.target / name).read_bytes()
            for name in self.original_root_files
        }

        code, report = self.doctor_json("--project", str(self.target))
        self.assertEqual(0, code)
        self.assertEqual("ok", report["repository"]["status"])
        self.assertIn("policy/identity.md", report["policies"]["files"])
        self.assertIn("project-memory/index.md", report["project_memory"]["files"])
        self.assertEqual("ok", report["policies"]["status"])
        self.assertEqual("ok", report["project_memory"]["status"])
        self.assertEqual(1, report["model_routing"]["schema_version"])
        self.assertEqual(
            str(self.resolved_target / ".brichan" / "config" / "model-routing.json"),
            report["model_routing"]["path"],
        )
        self.assertTrue(report["dependencies"]["codex"]["required"])
        self.assertTrue(report["dependencies"]["herdr"]["required"])
        # Read-only: neither managed state nor untouched root files change.
        self.assertEqual(before, self.state_snapshot())
        self.assertEqual(root_files_before, self.original_root_files)

    def test_installed_doctor_json_preserves_every_exit_class(self):
        self.run_brichan("init", "--apply", "--project", str(self.target))
        manifest = self.target / ".brichan" / "manifest.json"
        healthy = manifest.read_bytes()

        code, report = self.doctor_json("--project", str(self.target), codex=False)
        self.assertEqual(4, code)
        self.assertEqual("missing", report["dependencies"]["codex"]["status"])
        self.assertEqual("ok", report["repository"]["status"])
        self.assertFalse(report["ok"])

        manifest.write_text("{", encoding="utf-8")
        code, report = self.doctor_json("--project", str(self.target))
        self.assertEqual(2, code)
        self.assertEqual("invalid", report["repository"]["status"])

        payload = json.loads(healthy)
        payload["schema_version"] = 99
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        code, report = self.doctor_json("--project", str(self.target))
        self.assertEqual(3, code)
        self.assertEqual("invalid", report["repository"]["status"])
        self.assertIn("incompatible", report["repository"]["detail"])


if __name__ == "__main__":
    unittest.main()
