import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ACTIVE_ROUTING = json.loads(
    (ROOT / "config/model-routing.json").read_text(encoding="utf-8")
)
CODEX_COORDINATOR = ACTIVE_ROUTING["coordinator"]["runtimes"]["codex"]
CLAUDE_COORDINATOR = ACTIVE_ROUTING["coordinator"]["runtimes"]["claude"]


class CliCompatibilityTest(unittest.TestCase):
    def fake_runtime(self, directory: Path, name: str) -> None:
        executable = directory / name
        executable.write_text(
            "#!/bin/sh\n"
            "python3 -c 'import json, os, sys; "
            "print(json.dumps({\"argv\": sys.argv[1:], \"cwd\": os.getcwd()}))' "
            "\"$@\"\n",
            encoding="utf-8",
        )
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)

    def run_launcher(
        self,
        launcher: str,
        *arguments: str,
        environment: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> dict:
        with tempfile.TemporaryDirectory() as temporary:
            runtime_directory = Path(temporary)
            self.fake_runtime(runtime_directory, "codex")
            self.fake_runtime(runtime_directory, "claude")
            process_environment = os.environ.copy()
            process_environment["PATH"] = (
                f"{runtime_directory}{os.pathsep}{process_environment['PATH']}"
            )
            process_environment.update(environment or {})
            result = subprocess.run(
                [str(ROOT / "bin" / launcher), *arguments],
                cwd=ROOT if cwd is None else cwd,
                env=process_environment,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def test_codex_wrapper_preserves_flags_and_arguments(self):
        result = self.run_launcher("brichan-codex", "--model", "test")
        self.assertEqual(
            [
                "-C",
                str(ROOT),
                "-c",
                "agents.enabled=false",
                "--disable",
                "multi_agent",
                "--disable",
                "multi_agent_v2",
                "-c",
                f"model_reasoning_effort={CODEX_COORDINATOR['effort']}",
                "--model",
                "test",
            ],
            result["argv"],
        )

    def test_claude_wrapper_preserves_model_control_and_root_cwd(self):
        result = self.run_launcher(
            "brichan-claude",
            "--verbose",
            environment={"BRICHAN_CLAUDE_COORDINATOR_MODEL": "sonnet"},
        )
        self.assertEqual(
            [
                "--model",
                "sonnet",
                "--effort",
                CLAUDE_COORDINATOR["effort"],
                "--disallowed-tools=Task",
                "--verbose",
            ],
            result["argv"],
        )
        self.assertEqual(str(ROOT), result["cwd"])

    def test_empty_environment_values_preserve_defaults(self):
        # A bare prompt, not --help: from a checkout `brichan --help` reports
        # Brichan and never reaches the runtime, so it cannot carry this probe.
        codex = self.run_launcher(
            "brichan",
            "probe",
            environment={"BRICHAN_RUNTIME": ""},
        )
        claude = self.run_launcher(
            "brichan-claude",
            "--help",
            environment={"BRICHAN_CLAUDE_COORDINATOR_MODEL": ""},
        )
        self.assertIn("agents.enabled=false", codex["argv"])
        self.assertEqual(
            CLAUDE_COORDINATOR["model"],
            claude["argv"][claude["argv"].index("--model") + 1],
        )

    def test_explicit_cli_model_and_effort_override_manifest_defaults(self):
        codex = self.run_launcher(
            "brichan-codex",
            "--model",
            "explicit-codex",
            "-c",
            "model_reasoning_effort=xhigh",
        )
        claude = self.run_launcher(
            "brichan-claude",
            "--model",
            "explicit-claude",
            "--effort",
            "low",
        )

        self.assertEqual(1, codex["argv"].count("--model"))
        self.assertIn("explicit-codex", codex["argv"])
        self.assertNotIn(
            f"model_reasoning_effort={CODEX_COORDINATOR['effort']}",
            codex["argv"],
        )
        self.assertIn("model_reasoning_effort=xhigh", codex["argv"])
        self.assertEqual(1, claude["argv"].count("--model"))
        self.assertEqual(1, claude["argv"].count("--effort"))
        self.assertIn("explicit-claude", claude["argv"])
        self.assertIn("low", claude["argv"])

    def test_claude_cli_model_beats_environment_and_manifest(self):
        claude = self.run_launcher(
            "brichan-claude",
            "--model",
            "explicit-claude",
            environment={"BRICHAN_CLAUDE_COORDINATOR_MODEL": "environment-claude"},
        )

        self.assertEqual(1, claude["argv"].count("--model"))
        self.assertIn("explicit-claude", claude["argv"])
        self.assertNotIn("environment-claude", claude["argv"])
        self.assertNotIn(CLAUDE_COORDINATOR["model"], claude["argv"])

    def test_changed_manifest_changes_coordinator_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "routing.json"
            payload = json.loads(
                (ROOT / "config/model-routing.json").read_text(encoding="utf-8")
            )
            payload["coordinator"]["runtimes"]["codex"] = {
                "model": "changed-coordinator",
                "effort": "xhigh",
            }
            manifest.write_text(json.dumps(payload), encoding="utf-8")

            result = self.run_launcher(
                "brichan-codex",
                environment={"BRICHAN_MODEL_ROUTING_FILE": str(manifest)},
            )

        self.assertIn("changed-coordinator", result["argv"])
        self.assertIn("model_reasoning_effort=xhigh", result["argv"])

    def test_invalid_coordinator_environment_override_fails(self):
        result = subprocess.run(
            [str(ROOT / "bin" / "brichan-codex"), "--help"],
            cwd=ROOT,
            env={**os.environ, "BRICHAN_MODEL_ROUTING_FILE": "/not/a/manifest.json"},
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("cannot read routing settings", result.stderr)

    def test_malformed_coordinator_manifest_fails_at_startup(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "routing.json"
            manifest.write_text("{", encoding="utf-8")
            result = subprocess.run(
                [str(ROOT / "bin" / "brichan-claude"), "--help"],
                cwd=ROOT,
                env={**os.environ, "BRICHAN_MODEL_ROUTING_FILE": str(manifest)},
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(2, result.returncode)
        self.assertIn("malformed JSON", result.stderr)

    def test_dispatcher_routes_both_supported_runtimes(self):
        codex = self.run_launcher("brichan", "--runtime", "codex", "--help")
        claude = self.run_launcher("brichan", "--runtime=claude", "--help")
        self.assertIn("agents.enabled=false", codex["argv"])
        self.assertIn("--disallowed-tools=Task", claude["argv"])

    def test_checkout_dispatch_works_from_descendant_directory(self):
        result = self.run_launcher(
            "brichan",
            "--runtime",
            "codex",
            "--help",
            cwd=ROOT / "tests" / "integration",
        )
        self.assertIn("agents.enabled=false", result["argv"])
        self.assertEqual(str(ROOT / "tests" / "integration"), result["cwd"])

    def _brichan(self, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(ROOT / "bin" / "brichan"), *arguments],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_checkout_help_reports_brichan_not_the_runtime(self):
        """A checkout has no project to launch into, so --help is about Brichan."""
        for flag in ("--help", "-h"):
            result = self._brichan(flag)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("usage: brichan", result.stdout)
            self.assertNotIn("Codex CLI", result.stdout)

    def test_checkout_version_reports_brichan_not_the_runtime(self):
        for flag in ("--version", "-V"):
            result = self._brichan(flag)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(result.stdout.startswith("brichan "), result.stdout)

    def test_explicit_runtime_still_forwards_help_to_that_runtime(self):
        """`--runtime codex --help` names a runtime, so it wants its help."""
        result = self.run_launcher("brichan", "--runtime", "codex", "--help")
        self.assertIn("--help", result["argv"])

    def test_dispatcher_rejects_unknown_runtime(self):
        result = subprocess.run(
            [str(ROOT / "bin" / "brichan"), "--runtime", "unknown"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("unsupported runtime", result.stderr)

    def test_receipt_validator_wrapper_uses_importable_core(self):
        result = subprocess.run(
            [
                "python3",
                "scripts/validate_handoff_receipts.py",
                "projects",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Validated", result.stdout)


class DoctorJsonCheckoutTest(unittest.TestCase):
    """`bin/brichan doctor --json` over the real checkout and a real project."""

    @classmethod
    def setUpClass(cls):
        cls.git = shutil.which("git")
        if cls.git is None:
            raise unittest.SkipTest("git executable is not available")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.temp_path = Path(self.temporary.name)
        self.tool_bin = self.temp_path / "bin"
        self.tool_bin.mkdir()

    def fake_executable(self, name: str) -> None:
        executable = self.tool_bin / name
        executable.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)

    def doctor_json(
        self,
        *arguments: str,
        available: tuple[str, ...] = ("codex", "herdr"),
    ) -> tuple[int, dict, str]:
        # Rebuilt per call: fakes must not leak from an earlier invocation
        # into one that declares the same executable missing.
        shutil.rmtree(self.tool_bin)
        self.tool_bin.mkdir()
        for name in available:
            self.fake_executable(name)
        # A narrow PATH keeps the dependency section deterministic: only the
        # fakes plus what bin/brichan itself needs (a shell, python3, git).
        # Anything the test declares missing must be genuinely absent, which
        # the assertions below check rather than assume.
        path = os.pathsep.join(
            [
                str(self.tool_bin),
                str(Path(self.git).parent),
                str(Path(sys.executable).parent),
                "/usr/bin",
                "/bin",
            ]
        )
        result = subprocess.run(
            [str(ROOT / "bin" / "brichan"), "doctor", "--json", *arguments],
            cwd=ROOT,
            env={**os.environ, "PATH": path},
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual("", result.stderr)
        return result.returncode, json.loads(result.stdout), result.stdout

    def git_state(self, root: Path) -> tuple[str, bytes | None]:
        """Worktree and index snapshot, taken without writing either."""
        porcelain = subprocess.run(
            [self.git, "--no-optional-locks", "-C", str(root), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        )
        index = root / ".git" / "index"
        return porcelain.stdout, index.read_bytes() if index.exists() else None

    def test_source_checkout_reports_the_checkout_contract(self):
        before = self.git_state(ROOT)
        code, report, text = self.doctor_json()
        self.assertEqual(before, self.git_state(ROOT))

        self.assertEqual(0, code, text)
        self.assertTrue(report["ok"])
        self.assertEqual(1, report["schema_version"])
        self.assertEqual("source_checkout", report["repository"]["kind"])
        self.assertEqual(str(ROOT), report["repository"]["root"])
        self.assertEqual("ok", report["git"]["status"])
        self.assertIs(bool, type(report["git"]["dirty"]))
        self.assertEqual(1, report["model_routing"]["schema_version"])
        self.assertIn("docs/policy/identity.md", report["policies"]["files"])
        self.assertIn("projects/index.md", report["project_memory"]["files"])

    def test_stdout_is_exactly_one_stable_json_document(self):
        _, _, first = self.doctor_json()
        _, _, second = self.doctor_json()
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("}\n"))
        self.assertFalse(first.endswith("}\n\n"))
        self.assertEqual(1, first.count("\n}\n"))
        lines = first.splitlines()
        # Sorted keys put "dependencies" first; two-space indent throughout.
        self.assertEqual('  "dependencies": {', lines[1])
        for line in lines:
            indent = len(line) - len(line.lstrip(" "))
            self.assertEqual(0, indent % 2, repr(line))

    def test_missing_herdr_invalidates_the_checkout(self):
        code, report, text = self.doctor_json(available=("codex",))
        self.assertEqual(2, code, text)
        self.assertFalse(report["ok"])
        self.assertEqual("missing", report["dependencies"]["herdr"]["status"])
        self.assertTrue(report["dependencies"]["herdr"]["required"])

    def test_missing_codex_exits_four_without_failing_the_checkout(self):
        code, report, text = self.doctor_json(available=("herdr",))
        self.assertEqual(4, code, text)
        self.assertFalse(report["ok"])
        self.assertEqual("missing", report["dependencies"]["codex"]["status"])
        self.assertEqual("ok", report["repository"]["status"])

    def test_installed_project_json_preserves_the_state_exit_matrix(self):
        target = self.temp_path / "target"
        subprocess.run(
            [self.git, "init", "--quiet", str(target)],
            check=True,
            capture_output=True,
            text=True,
        )

        code, report, text = self.doctor_json("--project", str(target))
        self.assertEqual(1, code, text)
        self.assertEqual("installed_project", report["repository"]["kind"])
        self.assertEqual(str(target.resolve()), report["repository"]["root"])
        self.assertFalse(report["ok"])

        subprocess.run(
            [
                str(ROOT / "bin" / "brichan"),
                "init",
                "--apply",
                "--project",
                str(target),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        before = self.git_state(target)
        code, report, text = self.doctor_json("--project", str(target))
        self.assertEqual(0, code, text)
        self.assertTrue(report["ok"])
        self.assertEqual("ok", report["repository"]["status"])
        self.assertIn("policy/identity.md", report["policies"]["files"])
        self.assertIn("project-memory/index.md", report["project_memory"]["files"])
        self.assertEqual(before, self.git_state(target))

        code, report, text = self.doctor_json(
            "--project", str(target), available=("herdr",)
        )
        self.assertEqual(4, code, text)

        manifest = target / ".brichan" / "manifest.json"
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        manifest.write_text("{", encoding="utf-8")
        code, report, text = self.doctor_json("--project", str(target))
        self.assertEqual(2, code, text)
        self.assertEqual("invalid", report["repository"]["status"])

        payload["schema_version"] = 99
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        code, report, text = self.doctor_json("--project", str(target))
        self.assertEqual(3, code, text)

    def test_undecodable_routing_config_yields_one_json_document(self):
        """An unreadable byte sequence is a report, not a traceback."""
        target = self.temp_path / "undecodable"
        subprocess.run(
            [self.git, "init", "--quiet", str(target)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                str(ROOT / "bin" / "brichan"),
                "init",
                "--apply",
                "--project",
                str(target),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        routing = target / ".brichan" / "config" / "model-routing.json"
        routing.write_bytes(b'{"schema_version": "\xff\xfe"}')

        path = os.pathsep.join(
            [
                str(self.tool_bin),
                str(Path(self.git).parent),
                str(Path(sys.executable).parent),
                "/usr/bin",
                "/bin",
            ]
        )
        self.fake_executable("codex")
        result = subprocess.run(
            [
                str(ROOT / "bin" / "brichan"),
                "doctor",
                "--json",
                "--project",
                str(target),
            ],
            cwd=ROOT,
            env={**os.environ, "PATH": path},
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual("", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(2, result.returncode, result.stdout)
        report = json.loads(result.stdout)
        self.assertTrue(result.stdout.endswith("}\n"))
        self.assertFalse(result.stdout.endswith("}\n\n"))
        self.assertEqual("invalid", report["model_routing"]["status"])
        self.assertIsNone(report["model_routing"]["schema_version"])
        self.assertIn("utf-8", report["model_routing"]["detail"])
        self.assertFalse(report["ok"])

    def test_state_symlink_is_reported_without_traversing_it(self):
        target = self.temp_path / "linked"
        subprocess.run(
            [self.git, "init", "--quiet", str(target)],
            check=True,
            capture_output=True,
            text=True,
        )
        outside = self.temp_path / "outside-state"
        outside.mkdir()
        (outside / "config").mkdir()
        (outside / "config" / "model-routing.json").write_text(
            "{\"schema_version\": 1}", encoding="utf-8"
        )
        (target / ".brichan").symlink_to(outside, target_is_directory=True)

        code, report, text = self.doctor_json("--project", str(target))
        self.assertEqual(2, code, text)
        self.assertEqual("invalid", report["repository"]["status"])
        self.assertEqual("invalid", report["model_routing"]["status"])
        # The linked-to routing file was never parsed.
        self.assertIsNone(report["model_routing"]["schema_version"])
        self.assertIn("symbolic link", report["model_routing"]["detail"])
        for section in ("policies", "project_memory"):
            self.assertEqual("invalid", report[section]["status"], section)

    def test_default_doctor_output_is_compact_human_readable_text(self):
        # Deterministic PATH: codex/herdr availability is exercised by the
        # dedicated dependency tests above, not this formatting check.
        self.fake_executable("codex")
        self.fake_executable("herdr")
        path = os.pathsep.join(
            [
                str(self.tool_bin),
                str(Path(self.git).parent),
                str(Path(sys.executable).parent),
                "/usr/bin",
                "/bin",
            ]
        )
        result = subprocess.run(
            [str(ROOT / "bin" / "brichan"), "doctor"],
            cwd=ROOT,
            env={**os.environ, "PATH": path},
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("BRICHAN DOCTOR", result.stdout)
        self.assertIn(f"project root: {ROOT}", result.stdout)
        self.assertIn("overall:", result.stdout)
        self.assertNotIn("manifest.json", result.stdout)

    def test_json_flag_is_rejected_for_the_other_lifecycle_commands(self):
        for command in ("init", "status"):
            result = subprocess.run(
                [str(ROOT / "bin" / "brichan"), command, "--json"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, result.returncode, command)
            self.assertIn("unrecognized arguments: --json", result.stderr, command)


if __name__ == "__main__":
    unittest.main()
