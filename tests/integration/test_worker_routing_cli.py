import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "bin/brichan-herdr-agent-start"


class FakeHerdrTestCase(unittest.TestCase):
    """Fake-Herdr harness shared by the routing and ledger launcher suites."""

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
    #: the rollback path. ``FAKE_HERDR_SPLIT_NO_PANE`` and
    #: ``FAKE_HERDR_START_PANE`` cover the envelopes a zero exit can still
    #: carry: a split that names no pane, and a start that landed elsewhere.
    #: ``pane process-info`` reports an idle shell unless
    #: ``FAKE_HERDR_SHELL_BUSY_POLLS`` asks for that many busy reads first,
    #: the way a slow ``.zshrc`` looks while it is still running.
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
    if os.environ.get('FAKE_HERDR_SPLIT_NO_PANE'):
        payload = {'id': 'cli:pane:split', 'result': {'type': 'pane_info'}}
    else:
        payload = {'id': 'cli:pane:split', 'result': {
            'pane': {'pane_id': 'p2', 'tab_id': 't1', 'workspace_id': 'w1'},
            'type': 'pane_info'}}
elif args[:2] == ['pane', 'process-info']:
    with open(os.environ['FAKE_HERDR_LOG'], encoding='utf-8') as log:
        polls = sum(1 for line in log if '"process-info"' in line)
    busy = polls <= int(os.environ.get('FAKE_HERDR_SHELL_BUSY_POLLS', '0'))
    shell = {'pid': 500, 'name': 'zsh', 'argv0': 'zsh'}
    init = {'pid': 501, 'name': 'node', 'argv0': 'nvm'}
    payload = {'id': 'cli:pane:process_info', 'result': {'process_info': {
        'pane_id': args[args.index('--pane') + 1], 'shell_pid': 500,
        'foreground_process_group_id': 500,
        'foreground_processes': [shell, init] if busy else [shell]},
        'type': 'pane_process_info'}}
elif args[:2] == ['agent', 'start']:
    if os.environ.get('FAKE_HERDR_FAIL_START'):
        sys.stderr.write('agent_start_timeout\\n')
        raise SystemExit(1)
    kind = args[args.index('--kind') + 1]
    forwarded = args[args.index('--') + 1:] if '--' in args else []
    started_pane = os.environ.get('FAKE_HERDR_START_PANE', 'p2')
    payload = {'id': 'cli:agent:start', 'result': {
        'agent': {'agent': kind, 'name': args[2], 'pane_id': started_pane},
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

    def run_launcher(
        self, *arguments, fail_start=False, split_without_pane=False,
        start_pane=None, shell_busy_polls=0,
    ):
        environment = self.environment()
        if fail_start:
            environment["FAKE_HERDR_FAIL_START"] = "1"
        if split_without_pane:
            environment["FAKE_HERDR_SPLIT_NO_PANE"] = "1"
        if start_pane is not None:
            environment["FAKE_HERDR_START_PANE"] = start_pane
        if shell_busy_polls:
            environment["FAKE_HERDR_SHELL_BUSY_POLLS"] = str(shell_busy_polls)
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


class WorkerRoutingCliTest(FakeHerdrTestCase):
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

    def test_a_split_envelope_without_a_pane_id_is_a_clean_failure(self):
        """A zero exit is not a pane: the missing key must not escape.

        Reading the ID with a bare subscript raised ``KeyError`` here, which
        the rollback handler does not catch, so the launch died with the
        layout half-applied instead of failing cleanly.
        """

        result = self.run_launcher(
            *self.common_arguments(), "--route", "review", split_without_pane=True
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("returned no pane id", result.stderr)
        # No agent may be started against a pane that was never identified.
        self.assertEqual(
            [], [call for call in self.calls() if call[:2] == ["agent", "start"]]
        )

    def test_a_start_in_another_pane_closes_the_pane_the_launcher_created(self):
        """The mismatch check must unwind, not just exit.

        The agent is live somewhere Brichan does not own, so the empty pane
        the launcher made is closed and the stray pane is named for the
        caller.
        """

        result = self.run_launcher(
            *self.common_arguments(), "--route", "review", start_pane="p9"
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("p9", result.stderr)
        closes = [call for call in self.calls() if call[:2] == ["pane", "close"]]
        self.assertEqual([["pane", "close", "p2"]], closes)
        self.assertNotIn(["pane", "close", "p1"], self.calls())

    def test_the_start_waits_for_the_new_shell_to_reach_its_prompt(self):
        """``agent start`` needs an idle shell; a slow startup is waited out."""

        result = self.run_launcher(
            *self.common_arguments(), "--route", "review", shell_busy_polls=2
        )

        self.assertEqual(0, result.returncode, result.stderr)
        verbs = [call[:2] for call in self.calls()]
        polls = [i for i, verb in enumerate(verbs) if verb == ["pane", "process-info"]]
        start = verbs.index(["agent", "start"])
        self.assertEqual(3, len(polls))
        self.assertTrue(all(poll < start for poll in polls))
        self.assertEqual(
            ["pane", "process-info", "--pane", "p2"], self.calls()[polls[0]]
        )

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


class WorkerLedgerLaunchTest(FakeHerdrTestCase):
    """The launcher is the one point where resolution data becomes durable.

    Every case runs the committed wrappers against a throwaway checkout root,
    so the record, its null rules, and the never-fails-a-launch policy are
    exercised end to end without touching this repository's own tree.
    """

    def setUp(self):
        super().setUp()
        self.checkout = self.temp_path / "checkout"
        (self.checkout / "bin").mkdir(parents=True)
        (self.checkout / "projects" / "slug").mkdir(parents=True)
        # The committed wrapper is copied byte for byte and finds its root from
        # its own location, so the launcher under test is the real one; only
        # the root it derives is a throwaway.
        self.launcher = self.checkout / "bin/brichan-herdr-agent-start"
        shutil.copy2(LAUNCHER, self.launcher)
        os.symlink(ROOT / "src", self.checkout / "src")
        self.ledger_value = "projects/slug/ledger/workers.jsonl"
        self.ledger_path = self.checkout / self.ledger_value
        self.installed_launcher = self.temp_path / "installed-agent-start"
        self.installed_launcher.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
            "from brichan.orchestration.worker_launch import main\n"
            "raise SystemExit(main())\n",
            encoding="utf-8",
        )
        self.installed_launcher.chmod(
            self.installed_launcher.stat().st_mode | stat.S_IXUSR
        )

    def run_checkout_launcher(self, *arguments, launcher=None, **kwargs):
        environment = self.environment()
        if kwargs.pop("fail_start", False):
            environment["FAKE_HERDR_FAIL_START"] = "1"
        self.assertEqual({}, kwargs)
        return subprocess.run(
            [str(launcher or self.launcher), *arguments],
            cwd=self.checkout,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def checkout_arguments(self, *extra):
        return [
            "brichan-test-worker",
            "--anchor-pane",
            "p1",
            "--cwd",
            str(self.checkout),
            *extra,
        ]

    def records(self, path=None):
        target = self.ledger_path if path is None else path
        return [
            json.loads(line)
            for line in target.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def printed_launch_id(self, result):
        prefix = "ledger: launch_id="
        lines = [
            line for line in result.stderr.splitlines() if line.startswith(prefix)
        ]
        self.assertEqual(1, len(lines), result.stderr)
        return lines[0][len(prefix) :]

    def test_a_routed_launch_records_the_resolution_and_the_split_envelope(self):
        """R1, R4, M7: the launch data exists in-process and nowhere else.

        Without this the resolved route, runtime, model, effort, and the pane
        Herdr actually returned are lost the moment the launcher exits.
        """

        result = self.run_checkout_launcher(
            *self.checkout_arguments(
                "--route", "review", "--ledger-file", self.ledger_value
            )
        )
        self.assertEqual(0, result.returncode, result.stderr)

        (record,) = self.records()
        route = self.manifest["routes"]["review"]
        self.assertEqual("launched", record["event"])
        self.assertEqual(1, record["schema_version"])
        self.assertEqual("review", record["route"])
        self.assertEqual(route["runtime"], record["runtime"])
        self.assertEqual(route["model"], record["model"])
        self.assertEqual(route["effort"], record["effort"])
        self.assertEqual("p2", record["pane_id"])
        self.assertEqual("w1", record["workspace_id"])
        self.assertEqual("t1", record["tab_id"])
        self.assertEqual("brichan-herdr-agent-start", record["source"])
        self.assertEqual(self.printed_launch_id(result), record["launch_id"])
        # stdout stays the verbatim envelope.
        self.assertEqual("p2", json.loads(result.stdout)["result"]["agent"]["pane_id"])

    def test_a_legacy_launch_nulls_route_model_and_effort(self):
        """R4: the compatibility path must never invent what it cannot know."""

        result = self.run_checkout_launcher(
            *self.checkout_arguments("--ledger-file", self.ledger_value),
            "--",
            "codex",
            "--model",
            "legacy-model",
        )
        self.assertEqual(0, result.returncode, result.stderr)

        (record,) = self.records()
        self.assertIsNone(record["route"])
        self.assertIsNone(record["model"])
        self.assertIsNone(record["effort"])
        self.assertEqual("codex", record["runtime"])

    def test_a_task_identifier_is_recorded_verbatim_and_never_inferred(self):
        """R5: `task_id` comes only from the flag."""

        result = self.run_checkout_launcher(
            *self.checkout_arguments(
                "--route",
                "review",
                "--task",
                "WLG-X",
                "--ledger-file",
                self.ledger_value,
            )
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("WLG-X", self.records()[0]["task_id"])

        self.ledger_path.unlink()
        result = self.run_checkout_launcher(
            *self.checkout_arguments(
                "--route", "review", "--ledger-file", self.ledger_value
            )
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIsNone(self.records()[0]["task_id"])

    def test_a_dry_run_and_a_json_run_leave_no_ledger_behind(self):
        """R3: both return before any Herdr call and before the write site."""

        for flag in ("--dry-run", "--json"):
            with self.subTest(flag=flag):
                result = self.run_checkout_launcher(
                    "brichan-dry-run",
                    "--cwd",
                    str(self.checkout),
                    "--route",
                    "implement",
                    "--ledger-file",
                    self.ledger_value,
                    flag,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertFalse(self.ledger_path.exists())
                self.assertEqual([], self.calls())

    def test_a_rolled_back_launch_appends_nothing(self):
        """R1: the ledger must never name a worker that is not running."""

        result = self.run_checkout_launcher(
            *self.checkout_arguments(
                "--route", "review", "--ledger-file", self.ledger_value
            ),
            fail_start=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertFalse(self.ledger_path.exists())

    def test_a_checkout_launch_without_the_flag_notes_it_and_writes_nothing(self):
        """A ledger location is explicit in checkout mode, never guessed."""

        result = self.run_checkout_launcher(
            *self.checkout_arguments("--route", "review")
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            "ledger: no ledger location for this launch; not recorded",
            result.stderr,
        )
        self.assertFalse((self.checkout / "projects/slug/ledger").exists())

    def test_a_refused_ledger_file_value_fails_before_any_herdr_call(self):
        """PR2-M2: one mistaken flag must never reach managed state.

        Validating at parse time also means the refusal can never affect a
        launch that has already started.
        """

        for value in (
            ".brichan/manifest.json",
            ".BRICHAN/ledger/workers.jsonl",
            "../outside/workers.jsonl",
            "/absolute/workers.jsonl",
            "projects/slug/ledger/notes.txt",
        ):
            with self.subTest(value=value):
                result = self.run_checkout_launcher(
                    *self.checkout_arguments(
                        "--route", "review", "--ledger-file", value
                    )
                )
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertEqual([], self.calls())
        self.assertFalse((self.checkout / ".brichan").exists())

    def test_an_empty_ledger_file_value_is_refused_like_any_other(self):
        """WLG-001-CR-L1: an empty value is a value, not an absent flag.

        The resolver refuses `""` explicitly, but a truthiness guard skipped
        the resolver for it, so the launch proceeded with only the
        not-recorded note while `finish` exited 2 for the same input — a
        coordinator would read that as "no ledger configured" rather than as
        the typo it is. Per `TEST-003` this must fail if the guard reverts to
        testing truthiness.
        """

        result = self.run_checkout_launcher(
            *self.checkout_arguments("--route", "review", "--ledger-file", "")
        )

        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("--ledger-file must not be empty", result.stderr)
        self.assertNotIn(
            "ledger: no ledger location for this launch; not recorded",
            result.stderr,
        )
        self.assertEqual([], self.calls())
        self.assertFalse((self.checkout / "projects/slug/ledger").exists())

    def test_the_installed_launcher_rejects_a_ledger_file_flag(self):
        """Installed mode has exactly one ledger path, so the flag cannot exist."""

        result = self.run_checkout_launcher(
            *self.checkout_arguments(
                "--route", "review", "--ledger-file", self.ledger_value
            ),
            launcher=self.installed_launcher,
        )
        self.assertEqual(2, result.returncode)
        self.assertEqual([], self.calls())

    def test_an_unwritable_ledger_path_still_reports_a_successful_launch(self):
        """R7: a filesystem failure after a start never changes the outcome."""

        result = self.run_checkout_launcher(
            *self.checkout_arguments(
                "--route",
                "review",
                "--ledger-file",
                "projects/absent/ledger/workers.jsonl",
            )
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "p2", json.loads(result.stdout)["result"]["agent"]["pane_id"]
        )
        warnings = [
            line
            for line in result.stderr.splitlines()
            if line.startswith("warning: worker started but ledger write failed:")
        ]
        self.assertEqual(1, len(warnings), result.stderr)
        self.assertFalse((self.checkout / "projects/absent").exists())

    def test_a_non_oserror_ledger_defect_still_reports_a_successful_launch(self):
        """M3: the v2 guard covered only `OSError`.

        Any other class escaping ledger code would reach the launcher's outer
        handler and turn a live worker into exit 1, which is the failure R7
        forbids. The fault is injected in a throwaway wrapper because no
        production code carries a test hook.
        """

        faulty = self.checkout / "bin/faulty-agent-start"
        faulty.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "from pathlib import Path\n"
            "ROOT = Path(__file__).resolve().parents[1]\n"
            "sys.path.insert(0, str(ROOT / 'src'))\n"
            "from brichan.orchestration import worker_ledger\n"
            "def broken(*args, **kwargs):\n"
            "    raise TypeError('malformed envelope value')\n"
            "worker_ledger.append_record = broken\n"
            "from brichan.orchestration.worker_launch import checkout_main\n"
            "raise SystemExit(checkout_main(ROOT, sys.argv[1:]))\n",
            encoding="utf-8",
        )
        faulty.chmod(faulty.stat().st_mode | stat.S_IXUSR)

        result = self.run_checkout_launcher(
            *self.checkout_arguments(
                "--route", "review", "--ledger-file", self.ledger_value
            ),
            launcher=faulty,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "p2", json.loads(result.stdout)["result"]["agent"]["pane_id"]
        )
        warnings = [
            line
            for line in result.stderr.splitlines()
            if line.startswith("warning: worker started but ledger write failed:")
        ]
        self.assertEqual(1, len(warnings), result.stderr)
        self.assertIn("TypeError", warnings[0])
        self.assertFalse(self.ledger_path.exists())


class LegacyInstalledLedgerTest(FakeHerdrTestCase):
    """M4: legacy ledger resolution must never fail a working launch.

    `project_paths` raises for any `--cwd` that is not itself a Git root, and
    the launcher's outer handler turns that into exit 1 — the regression the
    reviewer reproduced against plan version 2.
    """

    def setUp(self):
        super().setUp()
        self.project = self.temp_path / "target"
        (self.project / "subdirectory").mkdir(parents=True)
        (self.project / ".git").mkdir()
        self.launcher = self.temp_path / "installed-agent-start"
        self.launcher.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
            "from brichan.orchestration.worker_launch import main\n"
            "raise SystemExit(main())\n",
            encoding="utf-8",
        )
        self.launcher.chmod(self.launcher.stat().st_mode | stat.S_IXUSR)

    def run_legacy(self, cwd):
        return subprocess.run(
            [
                str(self.launcher),
                "brichan-test-worker",
                "--anchor-pane",
                "p1",
                "--cwd",
                str(cwd),
                "--",
                "codex",
                "--model",
                "legacy-model",
            ],
            cwd=self.temp_path,
            env=self.environment(),
            check=False,
            capture_output=True,
            text=True,
        )

    def test_a_subdirectory_cwd_launch_still_starts_and_notes_the_gap(self):
        result = self.run_legacy(self.project / "subdirectory")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            "ledger: no ledger location for this launch; not recorded",
            result.stderr,
        )
        self.assertFalse((self.project / ".brichan").exists())

    def test_a_non_git_cwd_launch_still_starts_and_notes_the_gap(self):
        outside = self.temp_path / "not-a-repository"
        outside.mkdir()

        result = self.run_legacy(outside)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            "ledger: no ledger location for this launch; not recorded",
            result.stderr,
        )
        self.assertFalse((outside / ".brichan").exists())

    def test_a_subdirectory_cwd_records_into_the_git_roots_fixed_ledger(self):
        """R15: the upward walk is the same discovery `finish` uses."""

        (self.project / ".brichan").mkdir()
        (self.project / ".brichan/manifest.json").write_text("{}", encoding="utf-8")

        result = self.run_legacy(self.project / "subdirectory")

        self.assertEqual(0, result.returncode, result.stderr)
        ledger = self.project / ".brichan/ledger/workers.jsonl"
        self.assertTrue(ledger.is_file())
        (record,) = [
            json.loads(line)
            for line in ledger.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual("codex", record["runtime"])
        self.assertIsNone(record["route"])
        self.assertIn(f"ledger: launch_id={record['launch_id']}", result.stderr)


if __name__ == "__main__":
    unittest.main()
