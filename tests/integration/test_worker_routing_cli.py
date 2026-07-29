import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "bin/brida-herdr-agent-start"


class WorkerRoutingCliTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.temp_path = Path(self.temporary.name)
        self.log_path = self.temp_path / "herdr-calls.jsonl"
        self.manifest_path = self.temp_path / "model-routing.json"
        self.manifest = json.loads(
            (ROOT / "config/model-routing.json").read_text(encoding="utf-8")
        )
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self._write_fake_herdr()

    def _write_fake_herdr(self):
        executable = self.temp_path / "herdr"
        executable.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "args = sys.argv[1:]\n"
            "with open(os.environ['FAKE_HERDR_LOG'], 'a', encoding='utf-8') as log:\n"
            "    log.write(json.dumps(args) + '\\n')\n"
            "if args[:2] == ['pane', 'get']:\n"
            "    payload = {'result': {'pane': {'workspace_id': 'w1', "
            "'tab_id': 't1'}}}\n"
            "elif args[:2] == ['pane', 'layout']:\n"
            "    payload = {'result': {'layout': {'focused_pane_id': 'p1', "
            "'panes': [{'pane_id': 'p1', 'rect': {'x': 0, 'y': 0, "
            "'width': 120, 'height': 80}}], 'splits': []}}}\n"
            "elif args[:2] == ['agent', 'start']:\n"
            "    payload = {'result': {'agent': {'pane_id': 'p2'}}}\n"
            "else:\n"
            "    payload = {'result': {}}\n"
            "print(json.dumps(payload))\n",
            encoding="utf-8",
        )
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)

    def environment(self):
        environment = os.environ.copy()
        environment["PATH"] = (
            f"{self.temp_path}{os.pathsep}{environment['PATH']}"
        )
        environment["FAKE_HERDR_LOG"] = str(self.log_path)
        environment["BRIDA_MODEL_ROUTING_FILE"] = str(self.manifest_path)
        return environment

    def run_launcher(self, *arguments):
        return subprocess.run(
            [str(LAUNCHER), *arguments],
            cwd=ROOT,
            env=self.environment(),
            check=False,
            capture_output=True,
            text=True,
        )

    def calls(self):
        if not self.log_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.log_path.read_text(encoding="utf-8").splitlines()
        ]

    def common_arguments(self):
        return [
            "brida-test-worker",
            "--anchor-pane",
            "p1",
            "--cwd",
            str(ROOT),
        ]

    def test_named_route_builds_guarded_provider_command(self):
        result = self.run_launcher(*self.common_arguments(), "--route", "review")

        self.assertEqual(0, result.returncode, result.stderr)
        start = next(call for call in self.calls() if call[:2] == ["agent", "start"])
        command = start[start.index("--") + 1 :]
        self.assertEqual("claude", command[0])
        self.assertIn("--disallowed-tools=Task", command)
        self.assertIn("--permission-mode", command)
        self.assertIn("--model", command)
        self.assertIn("--effort", command)

    def test_named_route_cli_overrides_manifest(self):
        result = self.run_launcher(
            *self.common_arguments(),
            "--route",
            "scan",
            "--runtime",
            "claude",
            "--model",
            "override-model",
            "--effort",
            "max",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        start = next(call for call in self.calls() if call[:2] == ["agent", "start"])
        command = start[start.index("--") + 1 :]
        self.assertIn("override-model", command)
        self.assertIn("max", command)
        self.assertNotIn(self.manifest["routes"]["scan"]["model"], command)

    def test_json_dry_run_has_no_herdr_mutation(self):
        result = self.run_launcher(
            "brida-dry-run",
            "--cwd",
            str(ROOT),
            "--route",
            "implement",
            "--json",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["dry_run"])
        self.assertEqual("implement", payload["route"])
        self.assertEqual("codex", payload["resolved"]["runtime"])
        self.assertEqual([], self.calls())

    def test_human_readable_dry_run_has_no_herdr_mutation(self):
        result = self.run_launcher(
            "brida-dry-run",
            "--cwd",
            str(ROOT),
            "--route",
            "implement",
            "--dry-run",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("codex "))
        self.assertEqual([], self.calls())

    def test_invalid_route_fails_before_herdr(self):
        result = self.run_launcher(
            *self.common_arguments(),
            "--route",
            "unknown",
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("unknown route", result.stderr)
        self.assertEqual([], self.calls())

    def test_invalid_runtime_and_effort_fail_before_herdr(self):
        cases = (
            ("--runtime", "unknown"),
            ("--runtime", "claude"),
            ("--effort", "ultra"),
            ("--effort", "impossible"),
        )
        for option, value in cases:
            with self.subTest(option=option, value=value):
                result = self.run_launcher(
                    *self.common_arguments(),
                    "--route",
                    "implement",
                    option,
                    value,
                )
                self.assertNotEqual(0, result.returncode)
                self.assertEqual([], self.calls())

    def test_malformed_settings_fail_before_herdr(self):
        self.manifest_path.write_text("{", encoding="utf-8")

        result = self.run_launcher(
            *self.common_arguments(),
            "--route",
            "implement",
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("malformed JSON", result.stderr)
        self.assertEqual([], self.calls())

    def test_permission_bypass_fails_before_herdr(self):
        result = self.run_launcher(
            *self.common_arguments(),
            "--",
            "claude",
            "--dangerously-skip-permissions",
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("forbidden", result.stderr)
        self.assertEqual([], self.calls())

    def test_legacy_scope_and_hook_overrides_fail_before_herdr(self):
        cases = (
            ("codex", "-p", "legacy-profile"),
            ("codex", "-plegacy-profile"),
            ("codex", "--profile=legacy-profile"),
            ("codex", "--add-dir", "/tmp/extra"),
            ("codex", "--add-dir=/tmp/extra"),
            ("claude", "--bare"),
            ("claude", "--tools", "Task,Bash"),
            ("claude", "--tools=Task,Bash"),
            ("claude", "--allowedTools", "Read"),
            ("claude", "--allowed-tools=Read"),
            ("claude", "--disallowedTools", "Task"),
            ("claude", "--disallowed-tools=Task"),
        )
        for command in cases:
            with self.subTest(command=command):
                result = self.run_launcher(*self.common_arguments(), "--", *command)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("forbidden", result.stderr)
                self.assertEqual([], self.calls())

    def test_legacy_explicit_command_remains_compatible_and_guarded(self):
        result = self.run_launcher(
            *self.common_arguments(),
            "--",
            "codex",
            "--model",
            "legacy-model",
            "--help",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        start = next(call for call in self.calls() if call[:2] == ["agent", "start"])
        command = start[start.index("--") + 1 :]
        self.assertEqual(["--model", "legacy-model", "--help"], command[-3:])
        self.assertIn("agents.enabled=false", command)
        self.assertIn("multi_agent_v2", command)

    def test_legacy_explicit_command_does_not_depend_on_manifest(self):
        self.manifest_path.write_text("{", encoding="utf-8")

        result = self.run_launcher(
            *self.common_arguments(),
            "--",
            "codex",
            "--model",
            "legacy-model",
            "--help",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        start = next(call for call in self.calls() if call[:2] == ["agent", "start"])
        command = start[start.index("--") + 1 :]
        self.assertIn("legacy-model", command)

    def test_legacy_claude_deny_flag_precedes_argument_separator(self):
        result = self.run_launcher(
            *self.common_arguments(),
            "--",
            "claude",
            "--",
            "legacy prompt",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        start = next(call for call in self.calls() if call[:2] == ["agent", "start"])
        command = start[start.index("--") + 1 :]
        self.assertLess(command.index("--disallowed-tools=Task"), command.index("--"))


if __name__ == "__main__":
    unittest.main()
