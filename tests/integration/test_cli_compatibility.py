import json
import os
import stat
import subprocess
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
                cwd=ROOT,
                env=process_environment,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def test_codex_wrapper_preserves_flags_and_arguments(self):
        result = self.run_launcher("brida-codex", "--model", "test")
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
            "brida-claude",
            "--verbose",
            environment={"BRIDA_CLAUDE_COORDINATOR_MODEL": "sonnet"},
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
        codex = self.run_launcher(
            "brida",
            "--help",
            environment={"BRIDA_RUNTIME": ""},
        )
        claude = self.run_launcher(
            "brida-claude",
            "--help",
            environment={"BRIDA_CLAUDE_COORDINATOR_MODEL": ""},
        )
        self.assertIn("agents.enabled=false", codex["argv"])
        self.assertEqual(
            CLAUDE_COORDINATOR["model"],
            claude["argv"][claude["argv"].index("--model") + 1],
        )

    def test_explicit_cli_model_and_effort_override_manifest_defaults(self):
        codex = self.run_launcher(
            "brida-codex",
            "--model",
            "explicit-codex",
            "-c",
            "model_reasoning_effort=xhigh",
        )
        claude = self.run_launcher(
            "brida-claude",
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
            "brida-claude",
            "--model",
            "explicit-claude",
            environment={"BRIDA_CLAUDE_COORDINATOR_MODEL": "environment-claude"},
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
                "brida-codex",
                environment={"BRIDA_MODEL_ROUTING_FILE": str(manifest)},
            )

        self.assertIn("changed-coordinator", result["argv"])
        self.assertIn("model_reasoning_effort=xhigh", result["argv"])

    def test_invalid_coordinator_environment_override_fails(self):
        result = subprocess.run(
            [str(ROOT / "bin" / "brida-codex"), "--help"],
            cwd=ROOT,
            env={**os.environ, "BRIDA_MODEL_ROUTING_FILE": "/not/a/manifest.json"},
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
                [str(ROOT / "bin" / "brida-claude"), "--help"],
                cwd=ROOT,
                env={**os.environ, "BRIDA_MODEL_ROUTING_FILE": str(manifest)},
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(2, result.returncode)
        self.assertIn("malformed JSON", result.stderr)

    def test_dispatcher_routes_both_supported_runtimes(self):
        codex = self.run_launcher("brida", "--runtime", "codex", "--help")
        claude = self.run_launcher("brida", "--runtime=claude", "--help")
        self.assertIn("agents.enabled=false", codex["argv"])
        self.assertIn("--disallowed-tools=Task", claude["argv"])

    def test_dispatcher_rejects_unknown_runtime(self):
        result = subprocess.run(
            [str(ROOT / "bin" / "brida"), "--runtime", "unknown"],
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


if __name__ == "__main__":
    unittest.main()
