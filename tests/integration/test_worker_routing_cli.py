import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "bin/brichan-herdr-agent-start"


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

    #: Stubbed Herdr ``0.9.1``. ``pane split`` returns the ``pane_info``
    #: envelope carrying the new pane ID, and ``agent start`` returns the
    #: ``agent_started`` envelope for that same pane. Setting
    #: ``FAKE_HERDR_FAIL_START`` makes ``agent start`` fail the way the real
    #: client does when readiness is never observed, which is what exercises
    #: the rollback path.
    FAKE_HERDR = """#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
with open(os.environ['FAKE_HERDR_LOG'], 'a', encoding='utf-8') as log:
    log.write(json.dumps(args) + '\\n')
if args[:2] == ['pane', 'layout']:
    payload = {'result': {'layout': {'focused_pane_id': 'p1',
        'panes': [{'pane_id': 'p1', 'rect': {'x': 0, 'y': 0,
        'width': 120, 'height': 80}}], 'splits': []}}}
elif args[:2] == ['pane', 'split']:
    payload = {'id': 'cli:pane:split', 'result': {
        'pane': {'pane_id': 'p2', 'tab_id': 't1', 'workspace_id': 'w1'},
        'type': 'pane_info'}}
elif args[:2] == ['agent', 'start']:
    if os.environ.get('FAKE_HERDR_FAIL_START'):
        sys.stderr.write('agent_start_timeout\\n')
        raise SystemExit(1)
    kind = args[args.index('--kind') + 1]
    forwarded = args[args.index('--') + 1:] if '--' in args else []
    payload = {'id': 'cli:agent:start', 'result': {
        'agent': {'agent': kind, 'name': args[2], 'pane_id': 'p2'},
        'argv': [kind, *forwarded], 'type': 'agent_started'}}
else:
    payload = {'result': {}}
print(json.dumps(payload))
"""

    def _write_fake_herdr(self):
        executable = self.temp_path / "herdr"
        executable.write_text(self.FAKE_HERDR, encoding="utf-8")
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)

    def environment(self):
        environment = os.environ.copy()
        environment["PATH"] = (
            f"{self.temp_path}{os.pathsep}{environment['PATH']}"
        )
        environment["FAKE_HERDR_LOG"] = str(self.log_path)
        environment["BRICHAN_MODEL_ROUTING_FILE"] = str(self.manifest_path)
        return environment

    def run_launcher(self, *arguments, fail_start=False):
        environment = self.environment()
        if fail_start:
            environment["FAKE_HERDR_FAIL_START"] = "1"
        return subprocess.run(
            [str(LAUNCHER), *arguments],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def start_call(self):
        return next(call for call in self.calls() if call[:2] == ["agent", "start"])

    def split_call(self):
        return next(call for call in self.calls() if call[:2] == ["pane", "split"])

    def forwarded_agent_argv(self):
        """The argv Herdr passes to the agent, after ``--kind`` and ``--``."""

        start = self.start_call()
        return start[start.index("--") + 1 :] if "--" in start else []

    def calls(self):
        if not self.log_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.log_path.read_text(encoding="utf-8").splitlines()
        ]

    def common_arguments(self):
        return [
            "brichan-test-worker",
            "--anchor-pane",
            "p1",
            "--cwd",
            str(ROOT),
        ]

    def test_the_launch_is_a_split_then_a_start_in_that_pane(self):
        """The 0.9.1 two-step launch, including the pane-ID handoff.

        The ``0.7.3`` single ``agent start --workspace/--tab/--split`` call is
        rejected by the 0.9.1 client, so the removed options must not reappear
        and the started pane must be the one ``pane split`` returned.
        """

        result = self.run_launcher(*self.common_arguments(), "--route", "review")
        self.assertEqual(0, result.returncode, result.stderr)

        calls = self.calls()
        split, start = self.split_call(), self.start_call()
        self.assertLess(calls.index(split), calls.index(start))

        self.assertEqual("p1", split[2])
        self.assertEqual("right", split[split.index("--direction") + 1])
        self.assertEqual(str(ROOT), split[split.index("--cwd") + 1])

        # The pane ID comes from the split envelope, never from the anchor.
        self.assertEqual("p2", start[start.index("--pane") + 1])
        self.assertEqual(
            self.manifest["routes"]["review"]["runtime"],
            start[start.index("--kind") + 1],
        )
        self.assertEqual("30000", start[start.index("--timeout") + 1])
        for removed in ("--workspace", "--tab", "--split", "--no-focus", "--cwd"):
            self.assertNotIn(removed, start, removed)
        # A successful launch closes nothing.
        self.assertEqual([], [call for call in calls if call[:2] == ["pane", "close"]])

    def test_the_kind_supplies_the_executable_so_it_is_not_forwarded(self):
        """``--kind claude`` runs the executable; only its arguments follow."""

        result = self.run_launcher(*self.common_arguments(), "--route", "review")
        self.assertEqual(0, result.returncode, result.stderr)

        runtime = self.manifest["routes"]["review"]["runtime"]
        forwarded = self.forwarded_agent_argv()
        self.assertTrue(forwarded)
        self.assertNotEqual(runtime, forwarded[0])
        self.assertNotIn(runtime, forwarded)
        # Herdr echoes the reassembled argv with the executable back in front.
        self.assertEqual(
            [runtime, *forwarded], json.loads(result.stdout)["result"]["argv"]
        )

    def test_a_failed_start_closes_only_the_pane_the_launcher_created(self):
        result = self.run_launcher(
            *self.common_arguments(), "--route", "review", fail_start=True
        )

        self.assertNotEqual(0, result.returncode)
        closes = [call for call in self.calls() if call[:2] == ["pane", "close"]]
        self.assertEqual([["pane", "close", "p2"]], closes)
        # The anchor is never closed, whatever else fails.
        self.assertNotIn(["pane", "close", "p1"], self.calls())

    def test_the_started_envelope_carries_the_new_pane_id(self):
        result = self.run_launcher(*self.common_arguments(), "--route", "review")

        self.assertEqual(0, result.returncode, result.stderr)
        started = json.loads(result.stdout)["result"]["agent"]
        self.assertEqual("p2", started["pane_id"])
        self.assertNotEqual("p1", started["pane_id"])

    def test_named_route_builds_guarded_provider_command(self):
        result = self.run_launcher(*self.common_arguments(), "--route", "review")

        self.assertEqual(0, result.returncode, result.stderr)
        command = self.forwarded_agent_argv()
        runtime = self.manifest["routes"]["review"]["runtime"]
        self.assertEqual(runtime, self.start_call()[self.start_call().index("--kind") + 1])
        if runtime == "codex":
            self.assertIn("agents.enabled=false", command)
            self.assertIn("multi_agent_v2", command)
        else:
            self.assertIn("--disallowed-tools=Task", command)
            self.assertIn("--permission-mode", command)
        self.assertIn("--model", command)
        if runtime == "claude":
            self.assertIn("--effort", command)
        else:
            self.assertTrue(
                any(item.startswith("model_reasoning_effort=") for item in command)
            )

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
        command = self.forwarded_agent_argv()
        self.assertEqual("claude", self.start_call()[self.start_call().index("--kind") + 1])
        self.assertIn("override-model", command)
        self.assertIn("max", command)
        self.assertNotIn(self.manifest["routes"]["scan"]["model"], command)

    def test_json_dry_run_has_no_herdr_mutation(self):
        result = self.run_launcher(
            "brichan-dry-run",
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
        self.assertEqual(
            self.manifest["routes"]["implement"]["runtime"],
            payload["resolved"]["runtime"],
        )
        self.assertEqual([], self.calls())

    def test_human_readable_dry_run_has_no_herdr_mutation(self):
        result = self.run_launcher(
            "brichan-dry-run",
            "--cwd",
            str(ROOT),
            "--route",
            "implement",
            "--dry-run",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        expected_runtime = self.manifest["routes"]["implement"]["runtime"]
        self.assertTrue(result.stdout.startswith(f"{expected_runtime} "))
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
        implement_runtime = self.manifest["routes"]["implement"]["runtime"]
        opposite_runtime = "claude" if implement_runtime == "codex" else "codex"
        cases = (
            ("--runtime", "unknown"),
            ("--runtime", opposite_runtime),
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
        command = self.forwarded_agent_argv()
        self.assertEqual("codex", self.start_call()[self.start_call().index("--kind") + 1])
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
        self.assertIn("legacy-model", self.forwarded_agent_argv())

    def test_legacy_claude_deny_flag_precedes_argument_separator(self):
        result = self.run_launcher(
            *self.common_arguments(),
            "--",
            "claude",
            "--",
            "legacy prompt",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        command = self.forwarded_agent_argv()
        self.assertLess(command.index("--disallowed-tools=Task"), command.index("--"))


if __name__ == "__main__":
    unittest.main()
