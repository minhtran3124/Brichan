"""Unit matrix for the read-only Herdr monitoring surface.

Every payload below was captured from a live read-only Herdr probe before any
parser was written, exactly as plan ``HERDR-HARDENING-PLAN-001`` version 5 Step
2.1 requires. Two control-plane versions are frozen here:

* ``0.7.3`` (protocol ``16``), probed 2026-08-14.
* ``0.9.1`` (protocol ``22``), probed 2026-09-18 for task ``HERDR-091`` and
  recorded in ``herdr-0.9.1-probe.md``.

No test in this file needs a live Herdr, Codex, or Claude session.

Probes captured:

* ``herdr status --json`` on both versions
* ``herdr integration status`` on both versions (the ``--json`` flag exits
  ``2`` on both), including the ``0.9.1`` ``outdated (vN < vM)`` and
  ``<runtime> (experimental)`` row shapes
* ``herdr agent get`` JSON envelopes, including the ``agent_not_found`` error
  shape, and the ``0.9.1`` ``herdr agent read`` plain-text output
* ``herdr agent explain --json``, including the ``trust_directory`` failure
"""

from __future__ import annotations

import copy
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.orchestration import monitor


# ---------------------------------------------------------------------------
# Fixtures frozen from live Herdr 0.7.3 read-only probes (2026-08-14)
# ---------------------------------------------------------------------------

STATUS_JSON = {
    "client": {
        "version": "0.7.3",
        "channel": "stable",
        "protocol": 16,
        "binary": "/Users/example/.local/bin/herdr",
        "session": None,
    },
    "server": {
        "status": "running",
        "running": True,
        "version": "0.7.3",
        "protocol": 16,
        "capabilities": {"live_handoff": True, "detached_server_daemon": True},
        "compatible": True,
        "socket": "/Users/example/.config/herdr/herdr.sock",
        "session": None,
        "restart_needed": False,
    },
    "update": {"restart_needed": False},
}

INTEGRATION_TEXT = (
    "pi: not installed (/Users/example/.pi/agent/extensions/herdr-agent-state.ts)\n"
    "omp: not installed (/Users/example/.omp/agent/extensions/herdr-omp-agent-state.ts)\n"
    "claude: current (v7) (/Users/example/.claude/hooks/herdr-agent-state.sh)\n"
    "codex: current (v6) (/Users/example/.codex/herdr-agent-state.sh)\n"
    "copilot: not installed (/Users/example/.copilot/hooks/herdr-agent-state.sh)\n"
    "devin: not installed (/Users/example/.config/devin/herdr-agent-state.sh)\n"
    "droid: current (v2) (/Users/example/.factory/hooks/herdr-agent-state.sh)\n"
    "kimi: not installed (/Users/example/.kimi-code/hooks/herdr-agent-state.sh)\n"
    "opencode: current (v8) (/Users/example/.config/opencode/plugins/herdr-agent-state.js)\n"
    "kilo: not installed (/Users/example/.config/kilo/plugin/herdr-agent-state.js)\n"
    "hermes: not installed (/Users/example/.hermes/plugins/herdr-agent-state/__init__.py)\n"
    "qodercli: not installed (/Users/example/.qoder/hooks/herdr-agent-state.sh)\n"
    "cursor: current (v1) (/Users/example/.cursor/herdr-agent-state.sh)\n"
    "mastracode: not installed (/Users/example/.mastracode/hooks/herdr-agent-state.sh)\n"
)

# ---------------------------------------------------------------------------
# Fixtures frozen from the live Herdr 0.9.1 read-only probe (2026-09-18)
# ---------------------------------------------------------------------------

#: ``herdr status --json`` on ``0.9.1``. Keys were added, none removed; every
#: field ``parse_status_payload`` requires is still present in the same place.
STATUS_JSON_091 = {
    "client": {
        "version": "0.9.1",
        "channel": "stable",
        "protocol": 22,
        "endpoint_protocol_generation": 1,
        "endpoint_capabilities": ["surface_interest", "health_check"],
        "remote_host_bridge": True,
        "binary": "/Users/example/.local/bin/herdr",
        "session": None,
    },
    "server": {
        "status": "running",
        "running": True,
        "version": "0.9.1",
        "protocol": 22,
        "capabilities": {
            "live_handoff": True,
            "detached_server_daemon": True,
            "surface_interest": True,
            "health_check": True,
        },
        "compatible": True,
        "endpoint_compatible": True,
        "socket": "/Users/example/.config/herdr/herdr.sock",
        "session": None,
        "restart_needed": False,
        "server_binary_stale": False,
    },
    "update": {"restart_needed": False, "server_binary_stale": False},
}

#: ``herdr integration status`` on ``0.9.1``, verbatim row shapes with the
#: probe's home paths replaced by an example home. Four runtimes are new
#: (``qwen``, ``antigravity-cli``, ``grok``, ``letta``), two rows carry the new
#: ``outdated (vN < vM)`` comparison, and one carries the ``(experimental)``
#: runtime qualifier.
INTEGRATION_TEXT_091 = (
    "pi: not installed (/Users/example/.pi/agent/extensions/herdr-agent-state.ts)\n"
    "omp: not installed (/Users/example/.omp/agent/extensions/herdr-omp-agent-state.ts)\n"
    "claude: current (v10) (/Users/example/.claude/hooks/herdr-agent-state.sh)\n"
    "codex: current (v8) (/Users/example/.codex/herdr-agent-state.sh)\n"
    "copilot: not installed (/Users/example/.copilot/hooks/herdr-agent-state.sh)\n"
    "devin: not installed (/Users/example/.config/devin/herdr-agent-state.sh)\n"
    "droid: outdated (v2 < v3) (/Users/example/.factory/hooks/herdr-agent-state.sh)\n"
    "kimi: not installed (/Users/example/.kimi-code/hooks/herdr-agent-state.sh)\n"
    "opencode: outdated (v8 < v12) "
    "(/Users/example/.config/opencode/plugins/herdr-agent-state.js)\n"
    "kilo: not installed (/Users/example/.config/kilo/plugin/herdr-agent-state.js)\n"
    "hermes: not installed (/Users/example/.hermes/plugins/herdr-agent-state/__init__.py)\n"
    "qodercli: not installed (/Users/example/.qoder/hooks/herdr-agent-state.sh)\n"
    "qwen: not installed (/Users/example/.qwen/hooks/herdr-agent-session.sh)\n"
    "cursor: current (v1) (/Users/example/.cursor/herdr-agent-state.sh)\n"
    "mastracode: not installed (/Users/example/.mastracode/hooks/herdr-agent-state.sh)\n"
    "antigravity-cli: not installed "
    "(/Users/example/.gemini/config/hooks/herdr-agent-state.sh)\n"
    "grok: not installed (/Users/example/.grok/hooks/herdr-agent-state.sh)\n"
    "letta (experimental): not installed "
    "(/Users/example/.letta/hooks/herdr-agent-session.sh)\n"
)


AGENT_GET_JSON = {
    "id": "cli:agent:get",
    "result": {
        "agent": {
            "agent": "claude",
            "agent_status": "working",
            "cwd": "/Users/example/project",
            "focused": False,
            "name": "brichan-worker",
            "pane_id": "w37:p8",
            "revision": 0,
            "tab_id": "w37:t1",
            "terminal_id": "term_658ff2c318b64a",
            "workspace_id": "w37",
        },
        "type": "agent_info",
    },
}

#: ``herdr agent read <target> --source recent-unwrapped --lines N`` on
#: ``0.9.1``. There is no envelope: the terminal snapshot itself is stdout, and
#: nothing in it reports a source, a line count, or a ``truncated`` flag.
AGENT_READ_TEXT = "line one\nline two\nline three"

AGENT_NOT_FOUND_JSON = {
    "error": {
        "code": "agent_not_found",
        "message": "agent target brichan-missing not found",
    },
    "id": "cli:agent:get",
}

EXPLAIN_TRUST_DIRECTORY_JSON = {
    "agent": "codex",
    "cached_remote_version": "2026.07.18.1",
    "fallback_reason": None,
    "local_override_shadowing_remote": False,
    "manifest_source": "remote:/Users/example/.local/state/herdr/codex.toml",
    "manifest_version": "2026.07.18.1",
    "matched_rule": {"id": "osc_title_working", "priority": 1050, "state": "working"},
    "remote_update_error": (
        "rule trust_directory uses invalid region: top_non_empty_lines(20)"
    ),
    "remote_update_status": "failed",
    "screen_detection_skipped": False,
    "skip_state_update": False,
    "skipped_update_reason": None,
    "state": "working",
    "visible_blocker": False,
    "visible_idle": False,
    "visible_working": True,
    "warning": None,
}

EXPLAIN_HEALTHY_JSON = dict(
    EXPLAIN_TRUST_DIRECTORY_JSON,
    agent="claude",
    remote_update_error=None,
    remote_update_status="current",
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakeRunner:
    """Injected command runner. Records every executed argv."""

    def __init__(self, responses=None):
        self.responses = dict(responses or {})
        self.calls: list[list[str]] = []

    @staticmethod
    def key(argv):
        words = [part for part in argv[1:] if not part.startswith("-")]
        return " ".join(words[:2])

    def __call__(self, argv):
        argv = list(argv)
        self.calls.append(argv)
        response = self.responses.get(self.key(argv))
        if response is None:
            return monitor.CommandResult(1, "", "unexpected command")
        if callable(response):
            return response(argv)
        return response


def ok_json(payload):
    return monitor.CommandResult(0, json.dumps(payload), "")


def ok_text(text):
    return monitor.CommandResult(0, text, "")


def fail(message="boom", code=1):
    return monitor.CommandResult(code, "", message)


def healthy_responses(**overrides):
    """The supported control plane. Since plan v3 that is Herdr ``0.9.1``.

    A 0.7.3 status payload is no longer "healthy": it reports
    ``unverified-version``, which ``PreflightGateTest`` asserts explicitly.
    """

    responses = {
        "status": ok_json(STATUS_JSON_091),
        "integration status": ok_text(INTEGRATION_TEXT),
        "agent get": ok_json(AGENT_GET_JSON),
        "agent read": ok_text(AGENT_READ_TEXT),
        "agent explain": ok_json(EXPLAIN_HEALTHY_JSON),
    }
    responses.update(overrides)
    return responses


def status_with(**changes):
    payload = copy.deepcopy(STATUS_JSON_091)
    for dotted, value in changes.items():
        section, _, field = dotted.partition("__")
        payload[section][field] = value
    return payload


def run_main(argv, runner, herdr_on_path=True):
    """Drive ``main`` and capture exit code, stdout, and stderr."""

    out, err = io.StringIO(), io.StringIO()
    which = "/usr/bin/herdr" if herdr_on_path else None
    with mock.patch.object(monitor.shutil, "which", return_value=which):
        with redirect_stdout(out), redirect_stderr(err):
            code = monitor.main(argv, runner=runner)
    return code, out.getvalue(), err.getvalue()


class RecordingOpener:
    """Wraps ``os.open`` and records how every descriptor was obtained."""

    def __init__(self):
        self.opens: list[dict] = []

    def __call__(self, name, flags, dir_fd=None, **kwargs):
        self.opens.append({"name": name, "flags": flags, "dir_fd": dir_fd})
        if dir_fd is None:
            return os.open(name, flags, **kwargs)
        return os.open(name, flags, dir_fd=dir_fd, **kwargs)


# ---------------------------------------------------------------------------
# Adapters and the read-only allowlist
# ---------------------------------------------------------------------------


class ReadOnlyAllowlistTest(unittest.TestCase):
    def test_allowlist_admits_only_the_declared_read_only_commands(self):
        for argv in (
            ["herdr", "status", "--json"],
            ["herdr", "integration", "status"],
            ["herdr", "agent", "list"],
            ["herdr", "agent", "get", "brichan-worker"],
            [
                "herdr",
                "agent",
                "read",
                "brichan-worker",
                "--source",
                "recent-unwrapped",
                "--lines",
                "200",
            ],
            ["herdr", "agent", "explain", "brichan-worker", "--json"],
            ["herdr", "agent", "wait", "w", "--until", "idle", "--timeout", "30000"],
        ):
            monitor.assert_read_only(argv)

    def test_the_allowlist_is_derived_from_the_grammar_table(self):
        self.assertEqual(
            monitor.READ_ONLY_COMMANDS, frozenset(monitor.COMMAND_GRAMMARS)
        )
        for prefix in monitor.COMMAND_GRAMMARS:
            self.assertNotIn(
                prefix,
                {
                    ("pane", "run"),
                    ("agent", "send"),
                    ("pane", "send-keys"),
                    ("pane", "close"),
                    ("pane", "resize"),
                    ("pane", "focus"),
                    ("agent", "start"),
                },
            )

    def test_allowlist_refuses_every_mutating_command(self):
        for argv in (
            ["herdr", "pane", "run", "w37:p8", "text"],
            ["herdr", "agent", "send", "brichan-worker", "text"],
            ["herdr", "pane", "send-keys", "w37:p8", "Enter"],
            ["herdr", "pane", "close", "w37:p8"],
            ["herdr", "pane", "resize", "w37:p8"],
            ["herdr", "pane", "focus", "w37:p8"],
            ["herdr", "agent", "start", "brichan-worker"],
            ["herdr", "agent", "rename", "brichan-worker", "other"],
            ["herdr", "integration", "install", "claude"],
            ["rm", "-rf", "/"],
        ):
            with self.assertRaises(monitor.MonitorError, msg=argv):
                monitor.assert_read_only(argv)

    def test_every_executed_argv_stays_inside_the_allowlist(self):
        runner = FakeRunner(healthy_responses())
        monitor.run_preflight(runner=runner, agent="brichan-worker")
        monitor.observe_agent("brichan-worker", runner=runner)
        self.assertTrue(runner.calls)
        for argv in runner.calls:
            monitor.assert_read_only(argv)
            self.assertEqual("herdr", argv[0])

    def test_suffix_smuggling_behind_an_allowed_prefix_is_refused(self):
        """Code review v2, finding M2: prefix recognition is not a boundary."""

        for argv in (
            ["herdr", "status", "--json", "pane", "close", "w37:p9"],
            ["herdr", "status", "pane", "close", "w37:p9"],
            ["herdr", "agent", "list", "pane", "run", "w37:p9", "rm -rf /"],
            ["herdr", "agent", "get", "brichan-worker", "agent", "send", "text"],
            ["herdr", "integration", "status", "install", "claude"],
            [
                "herdr",
                "agent",
                "explain",
                "brichan-worker",
                "--json",
                "pane",
                "send-keys",
                "Enter",
            ],
        ):
            with self.assertRaises(monitor.MonitorError, msg=argv):
                monitor.assert_read_only(argv)

    def test_unknown_and_duplicate_options_are_refused(self):
        for argv in (
            ["herdr", "status", "--json", "--verbose"],
            ["herdr", "status", "--json", "--json"],
            ["herdr", "agent", "get", "brichan-worker", "--json"],
            ["herdr", "integration", "status", "--json"],
            ["herdr", "agent", "list", "--all"],
            [
                "herdr",
                "agent",
                "read",
                "brichan-worker",
                "--source",
                "recent-unwrapped",
                "--source",
                "visible",
                "--lines",
                "200",
            ],
            [
                "herdr",
                "agent",
                "wait",
                "w",
                "--until",
                "idle",
                "--until",
                "blocked",
                "--timeout",
                "100",
            ],
        ):
            with self.assertRaises(monitor.MonitorError, msg=argv):
                monitor.assert_read_only(argv)

    def test_malformed_arity_is_refused(self):
        for argv in (
            ["herdr", "agent", "get"],
            ["herdr", "agent", "get", "one", "two"],
            ["herdr", "agent", "list", "extra"],
            ["herdr", "status", "--json", "extra"],
            ["herdr", "integration", "status", "extra"],
            ["herdr", "agent", "explain", "--json"],
            ["herdr", "agent", "read", "--source", "recent-unwrapped", "--lines", "5"],
        ):
            with self.assertRaises(monitor.MonitorError, msg=argv):
                monitor.assert_read_only(argv)

    def test_missing_required_options_are_refused(self):
        for argv in (
            ["herdr", "status"],
            ["herdr", "agent", "explain", "brichan-worker"],
            ["herdr", "agent", "read", "brichan-worker", "--lines", "200"],
            ["herdr", "agent", "read", "brichan-worker", "--source", "recent-unwrapped"],
            ["herdr", "agent", "wait", "w", "--until", "idle"],
            ["herdr", "agent", "wait", "w", "--timeout", "100"],
        ):
            with self.assertRaises(monitor.MonitorError, msg=argv):
                monitor.assert_read_only(argv)

    def test_options_missing_their_value_are_refused(self):
        for argv in (
            ["herdr", "agent", "wait", "w", "--until", "idle", "--timeout"],
            ["herdr", "agent", "wait", "w", "--timeout", "--until", "idle"],
            ["herdr", "agent", "read", "brichan-worker", "--source", "--lines", "200"],
            ["herdr", "agent", "read", "brichan-worker", "--source", "recent", "--lines"],
        ):
            with self.assertRaises(monitor.MonitorError, msg=argv):
                monitor.assert_read_only(argv)

    def test_the_removed_status_wait_option_is_refused(self):
        """Herdr 0.9.1 removed ``--status``; the client exits 2 on it.

        Emitting it would turn every bounded wait into an immediate usage
        error, so the grammar must reject it here rather than let it reach the
        client.
        """

        for argv in (
            ["herdr", "agent", "wait", "w", "--status", "idle", "--timeout", "30000"],
            ["herdr", "agent", "wait", "w", "--until", "idle",
             "--status", "blocked", "--timeout", "30000"],
        ):
            with self.assertRaises(monitor.MonitorError, msg=argv):
                monitor.assert_read_only(argv)
        self.assertNotIn(
            "--status", monitor.COMMAND_GRAMMARS[("agent", "wait")].options
        )
        self.assertIn("--until", monitor.COMMAND_GRAMMARS[("agent", "wait")].required)

    def test_wait_argv_spells_the_state_option_as_until(self):
        argv = monitor.wait_argv("brichan-worker", "idle")
        self.assertIn("--until", argv)
        self.assertNotIn("--status", argv)
        self.assertEqual("idle", argv[argv.index("--until") + 1])

    def test_each_command_is_bound_to_its_required_adapter(self):
        runner = FakeRunner(healthy_responses())
        with self.assertRaises(monitor.MonitorError):
            # integration status is text-only; the JSON adapter must refuse it.
            monitor.run_json(["herdr", "integration", "status"], runner)
        with self.assertRaises(monitor.MonitorError):
            # status --json is a JSON command; the text adapter must refuse it.
            monitor.run_text(["herdr", "status", "--json"], runner)
        with self.assertRaises(monitor.MonitorError):
            monitor.run_text(["herdr", "agent", "get", "brichan-worker"], runner)
        self.assertEqual([], runner.calls, "no wrong-adapter command may execute")

    def test_no_executed_argv_can_send_input_to_an_agent(self):
        runner = FakeRunner(healthy_responses())
        monitor.run_preflight(runner=runner, agent="brichan-worker")
        monitor.observe_agent("brichan-worker", runner=runner)
        forbidden = {"send", "send-keys", "run", "close", "start", "resize", "focus"}
        for argv in runner.calls:
            self.assertFalse(forbidden.intersection(argv), argv)


class BoundedWaitTest(unittest.TestCase):
    def test_wait_argv_caps_the_timeout_at_30000_ms(self):
        argv = monitor.wait_argv("brichan-worker", "idle")
        self.assertIn("--timeout", argv)
        self.assertEqual("30000", argv[argv.index("--timeout") + 1])

    def test_every_executed_wait_argv_carries_a_bounded_timeout(self):
        for timeout in (1, 500, 15000, monitor.MAX_WAIT_TIMEOUT_MS):
            argv = monitor.wait_argv("brichan-worker", "idle", timeout)
            monitor.assert_read_only(argv)
            value = int(argv[argv.index("--timeout") + 1])
            self.assertGreater(value, 0)
            self.assertLessEqual(value, monitor.MAX_WAIT_TIMEOUT_MS)

    def test_wait_above_the_cap_is_rejected_in_code(self):
        for timeout in (30001, 60000, 10**9):
            with self.assertRaises(monitor.MonitorError):
                monitor.wait_argv("brichan-worker", "idle", timeout)

    def test_hand_assembled_wait_argv_cannot_exceed_the_cap(self):
        argv = ["herdr", "agent", "wait", "w", "--until", "idle", "--timeout", "45000"]
        with self.assertRaises(monitor.MonitorError):
            monitor.assert_read_only(argv)

    def test_wait_without_a_timeout_is_rejected(self):
        argv = ["herdr", "agent", "wait", "w", "--until", "idle"]
        with self.assertRaises(monitor.MonitorError):
            monitor.assert_read_only(argv)

    def test_a_duplicate_timeout_cannot_smuggle_an_over_cap_value(self):
        """Code review v2, finding M2: first-occurrence checking is not a cap."""

        for second in ("30001", "60000", "999999999"):
            for argv in (
                # An in-cap decoy first, the real over-cap value second.
                ["herdr", "agent", "wait", "w", "--until", "idle",
                 "--timeout", "100", "--timeout", second],
                # And the reverse order.
                ["herdr", "agent", "wait", "w", "--until", "idle",
                 "--timeout", second, "--timeout", "100"],
            ):
                with self.assertRaises(monitor.MonitorError, msg=argv):
                    monitor.assert_read_only(argv)

    def test_a_duplicate_in_cap_timeout_is_still_refused(self):
        argv = [
            "herdr", "agent", "wait", "w", "--until", "idle",
            "--timeout", "100", "--timeout", "200",
        ]
        with self.assertRaises(monitor.MonitorError):
            monitor.assert_read_only(argv)

    def test_a_non_integer_or_non_positive_timeout_is_refused(self):
        for value in ("abc", "", "-1", "0", "1e9", "30000.0"):
            argv = [
                "herdr", "agent", "wait", "w", "--until", "idle", "--timeout", value,
            ]
            with self.assertRaises(monitor.MonitorError, msg=value):
                monitor.assert_read_only(argv)


class AdapterTest(unittest.TestCase):
    def test_json_adapter_rejects_nonzero_exit(self):
        runner = FakeRunner({"status": fail("herdr server down")})
        with self.assertRaises(monitor.AdapterError):
            monitor.run_json(["herdr", "status", "--json"], runner)

    def test_json_adapter_rejects_non_json_stdout(self):
        runner = FakeRunner({"status": ok_text("usage: herdr status")})
        with self.assertRaises(monitor.AdapterError):
            monitor.run_json(["herdr", "status", "--json"], runner)

    def test_json_adapter_rejects_an_error_payload(self):
        runner = FakeRunner({"agent get": ok_json(AGENT_NOT_FOUND_JSON)})
        with self.assertRaises(monitor.AdapterError):
            monitor.run_json(["herdr", "agent", "get", "brichan-missing"], runner)

    def test_text_adapter_returns_raw_stdout_and_rejects_nonzero(self):
        runner = FakeRunner({"integration status": ok_text(INTEGRATION_TEXT)})
        self.assertEqual(
            INTEGRATION_TEXT,
            monitor.run_text(["herdr", "integration", "status"], runner),
        )
        runner = FakeRunner({"integration status": fail("usage:", code=2)})
        with self.assertRaises(monitor.AdapterError):
            monitor.run_text(["herdr", "integration", "status"], runner)


# ---------------------------------------------------------------------------
# Integration-status text parser
# ---------------------------------------------------------------------------


class IntegrationParserTest(unittest.TestCase):
    def test_valid_rows_yield_runtime_and_status_only(self):
        rows = monitor.parse_integration_rows(INTEGRATION_TEXT)
        self.assertEqual(14, len(rows))
        by_runtime = {row.runtime: row for row in rows}
        self.assertEqual("current", by_runtime["claude"].status)
        self.assertEqual("current", by_runtime["codex"].status)
        self.assertEqual("not installed", by_runtime["pi"].status)
        for row in rows:
            self.assertEqual("valid", row.classification)

    def test_mixed_installed_current_and_outdated_states(self):
        text = (
            "claude: current (v7) (/Users/example/.claude/hooks/herdr-agent-state.sh)\n"
            "codex: outdated (v5) (/Users/example/.codex/herdr-agent-state.sh)\n"
            "kimi: not installed (/Users/example/.kimi-code/hooks/herdr-agent-state.sh)\n"
        )
        rows = monitor.parse_integration_rows(text)
        self.assertEqual(
            [("claude", "current"), ("codex", "outdated"), ("kimi", "not installed")],
            [(row.runtime, row.status) for row in rows],
        )
        findings = monitor._integration_findings(rows)
        self.assertIn("integration-unhealthy(codex=outdated)", findings)
        self.assertNotIn("integration-unhealthy(kimi=not installed)", findings)

    def test_unknown_runtime_or_status_token_is_an_unknown_row(self):
        text = (
            "quokka: current (v1) (/Users/example/.quokka/hook.sh)\n"
            "claude: quantum-entangled (/Users/example/.claude/hooks/hook.sh)\n"
        )
        rows = monitor.parse_integration_rows(text)
        self.assertEqual(["unknown-row", "unknown-row"], [r.classification for r in rows])
        self.assertEqual(
            [
                "unknown-row(1)",
                "unknown-row(2)",
                "integration-unhealthy(claude=missing)",
                "integration-unhealthy(codex=missing)",
            ],
            monitor._integration_findings(rows),
        )
        # Even an unknown row retains only the two bounded tokens.
        self.assertEqual(("quokka", "current"), (rows[0].runtime, rows[0].status))
        self.assertEqual(
            ("claude", "quantum-entangled"), (rows[1].runtime, rows[1].status)
        )

    def test_rows_outside_the_grammar_are_malformed_rows(self):
        text = "this row has no separator at all\nclaude\n: leading colon\n"
        rows = monitor.parse_integration_rows(text)
        self.assertEqual(
            ["malformed-row", "malformed-row", "malformed-row"],
            [row.classification for row in rows],
        )
        self.assertEqual(
            [
                "malformed-row(1)",
                "malformed-row(2)",
                "malformed-row(3)",
                "integration-unhealthy(claude=missing)",
                "integration-unhealthy(codex=missing)",
            ],
            monitor._integration_findings(rows),
        )

    def test_missing_required_runtime_rows_are_unhealthy(self):
        cases = (
            (
                "",
                {
                    "integration-unhealthy(claude=missing)",
                    "integration-unhealthy(codex=missing)",
                },
            ),
            (
                "claude: current (v7) (/Users/example/.claude/hook.sh)\n",
                {"integration-unhealthy(codex=missing)"},
            ),
            (
                "codex: current (v5) (/Users/example/.codex/hook.sh)\n",
                {"integration-unhealthy(claude=missing)"},
            ),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                findings = set(
                    monitor._integration_findings(monitor.parse_integration_rows(text))
                )
                self.assertEqual(expected, findings)

    # -- code review v2, finding M1: anchored grammar and strict redaction ----

    #: Rows that must all be ``malformed-row`` and must contribute no raw
    #: remainder. Each carries path material in a shape the previous permissive
    #: parser would have copied into ``IntegrationRow.status``.
    PATH_BEARING_MALFORMED_ROWS = (
        # Missing trailing path group entirely.
        "claude: current",
        "claude: current (v7)",
        # Naked absolute path, unparenthesized.
        "claude: current /Users/example/.claude/hooks/herdr-agent-state.sh",
        "claude: current (v7) /Users/example/.claude/hooks/hook.sh",
        # Trailing content after an otherwise valid path group.
        "claude: current (v7) (/Users/example/.claude/hook.sh) extra",
        "claude: current (/Users/example/.claude/hook.sh) /home/other/hook.sh",
        # Path group not at the end, or unbalanced.
        "claude: (/Users/example/.claude/hook.sh) current",
        "claude: current (/Users/example/.claude/hook.sh",
        "claude: current /Users/example/.claude/hook.sh)",
        # Home-relative and nested-parenthesis shapes.
        "claude: current (~/.claude/hooks/hook.sh)",
        "claude: current ((/Users/example/.claude/hook.sh))",
        # Path material smuggled into the runtime or status position.
        "/Users/example/.claude: current (/Users/example/.claude/hook.sh)",
        "claude: /Users/example/.claude/hook.sh (/Users/example/.claude/hook.sh)",
    )

    def test_path_bearing_rows_outside_the_grammar_are_malformed_and_bare(self):
        text = "\n".join(self.PATH_BEARING_MALFORMED_ROWS) + "\n"
        rows = monitor.parse_integration_rows(text)
        self.assertEqual(len(self.PATH_BEARING_MALFORMED_ROWS), len(rows))
        for row, raw in zip(rows, self.PATH_BEARING_MALFORMED_ROWS):
            self.assertEqual("malformed-row", row.classification, raw)
            self.assertEqual("", row.runtime, raw)
            self.assertEqual("", row.status, raw)

    def test_no_malformed_row_leaks_path_material_into_the_report(self):
        runner = FakeRunner(
            healthy_responses(
                **{
                    "integration status": ok_text(
                        "\n".join(self.PATH_BEARING_MALFORMED_ROWS) + "\n"
                    )
                }
            )
        )
        report = monitor.run_preflight(runner=runner)
        rendered = monitor.render_report(report.as_dict())
        for leaked in ("/Users/", "/home/", "~/", "hook.sh", "herdr-agent-state", ".claude"):
            self.assertNotIn(leaked, rendered, leaked)
        self.assertEqual(
            {
                *(f"malformed-row({index})" for index in range(1, len(report.integrations) + 1)),
                "integration-unhealthy(claude=missing)",
                "integration-unhealthy(codex=missing)",
            },
            set(report.findings),
        )

    def test_a_path_like_unknown_row_still_cannot_carry_a_path(self):
        rows = monitor.parse_integration_rows(
            "quokka: not installed (/Users/example/.quokka/plugins/state.js)\n"
        )
        self.assertEqual("unknown-row", rows[0].classification)
        for value in (rows[0].runtime, rows[0].status):
            self.assertNotIn("/", value)
            self.assertNotIn("~", value)
            self.assertNotIn("(", value)

    def test_the_trailing_path_group_is_required_by_the_grammar(self):
        valid = "claude: current (v7) (/Users/example/.claude/hook.sh)"
        self.assertEqual(
            "valid", monitor.parse_integration_rows(valid)[0].classification
        )
        without_path = "claude: current (v7)"
        self.assertEqual(
            "malformed-row",
            monitor.parse_integration_rows(without_path)[0].classification,
        )

    def test_the_version_group_is_optional_but_bounded(self):
        rows = monitor.parse_integration_rows(
            "claude: current (v7) (/Users/example/a.sh)\n"
            "codex: current (/Users/example/b.sh)\n"
            "droid: current (v2.1.0) (/Users/example/c.sh)\n"
        )
        self.assertEqual(["valid", "valid", "valid"], [r.classification for r in rows])
        for row in rows:
            self.assertEqual("current", row.status)

    def test_every_live_0_9_1_row_parses_as_valid(self):
        rows = monitor.parse_integration_rows(INTEGRATION_TEXT_091)
        self.assertEqual(18, len(rows))
        for row in rows:
            self.assertEqual("valid", row.classification, row.index)
        by_runtime = {row.runtime: row.status for row in rows}
        self.assertEqual("outdated", by_runtime["droid"])
        self.assertEqual("outdated", by_runtime["opencode"])
        self.assertEqual("current", by_runtime["claude"])
        self.assertEqual("current", by_runtime["codex"])

    def test_the_experimental_qualifier_is_matched_but_never_recorded(self):
        rows = monitor.parse_integration_rows(
            "letta (experimental): not installed (/Users/example/.letta/hook.sh)\n"
        )
        self.assertEqual(1, len(rows))
        self.assertEqual("valid", rows[0].classification)
        self.assertEqual("letta", rows[0].runtime)
        self.assertEqual("not installed", rows[0].status)
        self.assertNotIn("experimental", json.dumps(rows[0].as_dict()))

    def test_the_upgrade_comparison_version_group_is_bounded_and_dropped(self):
        rows = monitor.parse_integration_rows(
            "droid: outdated (v2 < v3) (/Users/example/.factory/hook.sh)\n"
        )
        self.assertEqual("valid", rows[0].classification)
        self.assertEqual("droid", rows[0].runtime)
        self.assertEqual("outdated", rows[0].status)
        self.assertNotIn("v2", json.dumps(rows[0].as_dict()))

    def test_the_four_new_0_9_1_runtimes_are_known(self):
        for runtime in ("qwen", "antigravity-cli", "grok", "letta"):
            self.assertIn(runtime, monitor.KNOWN_INTEGRATION_RUNTIMES, runtime)

    def test_the_widened_grammar_still_rejects_genuinely_malformed_rows(self):
        """The qualifier and comparison are literal, not an escape hatch."""

        for line in (
            "letta (experimental): not installed",
            "letta (experimental) (/Users/example/.letta/hook.sh)",
            "letta (unstable): not installed (/Users/example/.letta/hook.sh)",
            "letta (experimental) (experimental): not installed "
            "(/Users/example/.letta/hook.sh)",
            "droid: outdated (v2 < v3) /Users/example/.factory/hook.sh",
            "droid: outdated (v2 < ) (/Users/example/.factory/hook.sh)",
            "droid: outdated (v2 < v3 < v4) (/Users/example/.factory/hook.sh)",
            "droid: outdated (v2 > v3) (/Users/example/.factory/hook.sh)",
            "droid: outdated (v2 < v3) (~/.factory/hook.sh)",
            "droid: outdated (v2 < v3) (/Users/example/.factory/hook.sh) extra",
        ):
            rows = monitor.parse_integration_rows(line + "\n")
            self.assertEqual("malformed-row", rows[0].classification, line)
            self.assertEqual("", rows[0].runtime, line)
            self.assertEqual("", rows[0].status, line)
            self.assertNotIn("/Users/", json.dumps(rows[0].as_dict()), line)

    def test_nonzero_integration_exit_is_a_collected_finding(self):
        runner = FakeRunner(
            healthy_responses(**{"integration status": fail("usage:", code=2)})
        )
        report = monitor.run_preflight(runner=runner)
        self.assertIn("integration-unhealthy", report.findings)
        self.assertEqual((), report.integrations)

    def test_no_home_or_configuration_path_reaches_the_report(self):
        runner = FakeRunner(healthy_responses())
        report = monitor.run_preflight(runner=runner, agent="brichan-worker")
        rendered = monitor.render_report(report.as_dict())
        for leaked in ("/Users/", "/home/", ".claude/hooks", "herdr-agent-state", "~/"):
            self.assertNotIn(leaked, rendered, leaked)
        # The parser must discard the path before any value is stored.
        for row in report.integrations:
            self.assertNotIn("/", row.status)
            self.assertNotIn("/", row.runtime)


# ---------------------------------------------------------------------------
# Preflight gating and status schema
# ---------------------------------------------------------------------------


class PreflightGateTest(unittest.TestCase):
    def test_verified_version_and_protocol(self):
        report = monitor.run_preflight(runner=FakeRunner(healthy_responses()))
        self.assertEqual(monitor.SUPPORT_VERIFIED, report.support)
        self.assertEqual("0.9.1", report.server_version)
        self.assertEqual(22, report.protocol)
        self.assertNotIn("unverified-version", report.findings)

    def test_0_9_1_is_the_only_verified_pair(self):
        """Plan v3: 0.9.1 is the minimum supported Herdr.

        The text-only read adapter cannot parse a 0.7.3 JSON read envelope, so
        claiming 0.7.3 as verified would be a promise the adapter cannot keep.
        """

        self.assertEqual(frozenset({("0.9.1", 22)}), monitor.VERIFIED_SUPPORT)
        report = monitor.run_preflight(
            runner=FakeRunner(healthy_responses(status=ok_json(STATUS_JSON_091)))
        )
        self.assertEqual(monitor.SUPPORT_VERIFIED, report.support)
        self.assertEqual("0.9.1", report.server_version)
        self.assertEqual(22, report.protocol)
        self.assertNotIn("unverified-version", report.findings)

    def test_0_7_3_now_reports_unverified_and_is_not_blocked(self):
        """Dropping 0.7.3 reports a state; it never refuses to report.

        The whole preflight still runs against a 0.7.3 payload — integration
        rows are still parsed, nothing is updated or installed — so an operator
        on an old server gets a report plus a finding, not a hard failure.
        """

        self.assertNotIn(("0.7.3", 16), monitor.VERIFIED_SUPPORT)
        runner = FakeRunner(healthy_responses(status=ok_json(STATUS_JSON)))
        report = monitor.run_preflight(runner=runner)
        self.assertEqual(monitor.SUPPORT_UNVERIFIED, report.support)
        self.assertIn("unverified-version", report.findings)
        self.assertEqual("0.7.3", report.server_version)
        self.assertEqual(16, report.protocol)
        self.assertEqual(14, len(report.integrations))
        for argv in runner.calls:
            self.assertNotIn("install", argv)
            self.assertNotIn("update", argv)

    def test_the_live_0_9_1_control_plane_reports_no_row_findings(self):
        """AC3 at the unit layer: no malformed-row, no unknown-row."""

        report = monitor.run_preflight(
            runner=FakeRunner(
                healthy_responses(
                    status=ok_json(STATUS_JSON_091),
                    **{"integration status": ok_text(INTEGRATION_TEXT_091)},
                )
            )
        )
        self.assertEqual(monitor.SUPPORT_VERIFIED, report.support)
        for finding in report.findings:
            self.assertFalse(finding.startswith("malformed-row"), finding)
            self.assertFalse(finding.startswith("unknown-row"), finding)
        # droid and opencode are genuinely outdated on the probed machine, and
        # outdated stays a finding for every runtime.
        self.assertIn("integration-unhealthy(droid=outdated)", report.findings)
        self.assertIn("integration-unhealthy(opencode=outdated)", report.findings)

    def test_version_outside_the_verified_set_is_unverified_not_a_block(self):
        runner = FakeRunner(
            healthy_responses(status=ok_json(status_with(server__version="0.9.0")))
        )
        report = monitor.run_preflight(runner=runner)
        self.assertEqual(monitor.SUPPORT_UNVERIFIED, report.support)
        self.assertIn("unverified-version", report.findings)
        # Read-only probing still happened; nothing updated or installed.
        self.assertTrue(any("integration" in " ".join(c) for c in runner.calls))
        for argv in runner.calls:
            self.assertNotIn("install", argv)
            self.assertNotIn("update", argv)

    def test_protocol_outside_the_verified_set_is_unverified(self):
        runner = FakeRunner(
            healthy_responses(status=ok_json(status_with(server__protocol=17)))
        )
        report = monitor.run_preflight(runner=runner)
        self.assertEqual(monitor.SUPPORT_UNVERIFIED, report.support)

    def test_status_probe_failure_makes_the_report_impossible(self):
        for response in (fail("connection refused"), ok_text("not json at all")):
            runner = FakeRunner(healthy_responses(status=response))
            with self.assertRaises(monitor.AdapterError):
                monitor.run_preflight(runner=runner)

    def test_incompatible_control_plane_is_a_collected_finding(self):
        runner = FakeRunner(
            healthy_responses(status=ok_json(status_with(server__compatible=False)))
        )
        report = monitor.run_preflight(runner=runner)
        self.assertIn("incompatible-control-plane", report.findings)
        self.assertIs(False, report.compatible)

    def test_server_restart_need_is_a_collected_finding(self):
        runner = FakeRunner(
            healthy_responses(status=ok_json(status_with(server__restart_needed=True)))
        )
        report = monitor.run_preflight(runner=runner)
        self.assertIn("restart-needed(server)", report.findings)

    def test_update_restart_need_is_a_collected_finding(self):
        runner = FakeRunner(
            healthy_responses(status=ok_json(status_with(update__restart_needed=True)))
        )
        report = monitor.run_preflight(runner=runner)
        self.assertIn("restart-needed(update)", report.findings)

    def test_findings_are_a_union_and_never_mask_one_another(self):
        payload = status_with(
            server__version="0.9.0",
            server__compatible=False,
            server__restart_needed=True,
        )
        payload["update"]["restart_needed"] = True
        runner = FakeRunner(
            healthy_responses(
                status=ok_json(payload),
                **{
                    "integration status": ok_text(
                        "codex: outdated (v5) (/Users/example/.codex/hook.sh)\n"
                        "bogus row without a separator\n"
                    )
                },
                **{"agent explain": ok_json(EXPLAIN_TRUST_DIRECTORY_JSON)},
            )
        )
        report = monitor.run_preflight(runner=runner, agent="brichan-worker")
        for finding in (
            "unverified-version",
            "incompatible-control-plane",
            "restart-needed(server)",
            "restart-needed(update)",
            "integration-unhealthy(codex=outdated)",
            "malformed-row(2)",
            "capability-drift",
        ):
            self.assertIn(finding, report.findings, finding)


class StatusSchemaTest(unittest.TestCase):
    REQUIRED = (
        ("client", "version"),
        ("server", "version"),
        ("server", "protocol"),
        ("server", "compatible"),
        ("server", "restart_needed"),
        ("update", "restart_needed"),
    )

    def test_each_required_field_absent_is_status_schema_invalid(self):
        for section, field in self.REQUIRED:
            payload = copy.deepcopy(STATUS_JSON)
            del payload[section][field]
            with self.assertRaises(monitor.StatusSchemaError, msg=f"{section}.{field}"):
                monitor.parse_status_payload(payload)

    def test_each_required_field_mistyped_is_status_schema_invalid(self):
        mistypes = {
            ("client", "version"): 7,
            ("server", "version"): None,
            ("server", "protocol"): "16",
            ("server", "compatible"): "true",
            ("server", "restart_needed"): 1,
            ("update", "restart_needed"): "no",
        }
        for (section, field), value in mistypes.items():
            payload = copy.deepcopy(STATUS_JSON)
            payload[section][field] = value
            with self.assertRaises(monitor.StatusSchemaError, msg=f"{section}.{field}"):
                monitor.parse_status_payload(payload)

    def test_a_missing_section_is_status_schema_invalid(self):
        payload = copy.deepcopy(STATUS_JSON)
        del payload["update"]
        with self.assertRaises(monitor.StatusSchemaError):
            monitor.parse_status_payload(payload)

    def test_the_frozen_live_payload_validates(self):
        fields = monitor.parse_status_payload(STATUS_JSON)
        self.assertEqual("0.7.3", fields["server_version"])
        self.assertEqual(16, fields["protocol"])
        self.assertIs(True, fields["compatible"])
        self.assertIs(False, fields["server_restart_needed"])
        self.assertIs(False, fields["update_restart_needed"])

    def test_the_frozen_live_0_9_1_payload_validates_unchanged(self):
        """0.9.1 added keys and removed none, so the schema still holds."""

        fields = monitor.parse_status_payload(STATUS_JSON_091)
        self.assertEqual("0.9.1", fields["server_version"])
        self.assertEqual("0.9.1", fields["client_version"])
        self.assertEqual(22, fields["protocol"])
        self.assertIs(True, fields["compatible"])
        self.assertIs(False, fields["server_restart_needed"])
        self.assertIs(False, fields["update_restart_needed"])

    def test_each_required_field_absent_from_the_0_9_1_payload_is_invalid(self):
        for section, field in (
            ("client", "version"),
            ("server", "version"),
            ("server", "protocol"),
            ("server", "compatible"),
            ("server", "restart_needed"),
            ("update", "restart_needed"),
        ):
            payload = copy.deepcopy(STATUS_JSON_091)
            del payload[section][field]
            with self.assertRaises(
                monitor.StatusSchemaError, msg=f"{section}.{field}"
            ):
                monitor.parse_status_payload(payload)


class CapabilityFindingTest(unittest.TestCase):
    def test_trust_directory_explain_failure_is_reported_not_repaired(self):
        runner = FakeRunner(
            healthy_responses(**{"agent explain": ok_json(EXPLAIN_TRUST_DIRECTORY_JSON)})
        )
        report = monitor.run_preflight(runner=runner, agent="brichan-worker")
        self.assertEqual(1, len(report.capabilities))
        finding = report.capabilities[0]
        self.assertEqual("remote-update-failed", finding.code)
        self.assertEqual(
            "rule trust_directory uses invalid region: top_non_empty_lines(20)",
            finding.detail,
        )
        self.assertIn("capability-drift", report.findings)
        # Reporting drift never repairs it: no manifest or rule command ran.
        for argv in runner.calls:
            self.assertNotIn("install", argv)
            self.assertNotIn("manifest", argv)

    def test_healthy_explain_yields_no_capability_finding(self):
        runner = FakeRunner(healthy_responses())
        report = monitor.run_preflight(runner=runner, agent="brichan-worker")
        self.assertEqual((), report.capabilities)
        self.assertNotIn("capability-drift", report.findings)

    def test_explain_is_probed_only_when_an_agent_is_named(self):
        runner = FakeRunner(healthy_responses())
        monitor.run_preflight(runner=runner)
        self.assertFalse(
            [argv for argv in runner.calls if "explain" in argv], runner.calls
        )


# ---------------------------------------------------------------------------
# Truncation classification
# ---------------------------------------------------------------------------


class TruncationTest(unittest.TestCase):
    def test_native_truncated_true_dominates_and_yields_confirmed(self):
        self.assertEqual(
            monitor.TRUNCATION_CONFIRMED,
            monitor.classify_truncation(
                read_failed=False,
                native_truncated=True,
                lines_counted=3,
                lines_requested=200,
                source="recent-unwrapped",
                capabilities={monitor.completeness_token("recent-unwrapped")},
            ),
        )

    def test_read_failure_yields_confirmed(self):
        self.assertEqual(
            monitor.TRUNCATION_CONFIRMED,
            monitor.classify_truncation(
                read_failed=True,
                native_truncated=None,
                lines_counted=0,
                lines_requested=200,
                source="recent-unwrapped",
            ),
        )

    def test_an_absent_native_flag_on_a_successful_read_yields_possible(self):
        """Herdr 0.9.1 reports no native flag; a successful read is bounded.

        It must not be reported as ``confirmed`` — that would make every
        healthy worker look truncated — and it must not be able to reach
        ``none``, which the next test pins.
        """

        self.assertEqual(
            monitor.TRUNCATION_POSSIBLE,
            monitor.classify_truncation(
                read_failed=False,
                native_truncated=None,
                lines_counted=5,
                lines_requested=200,
                source="recent-unwrapped",
            ),
        )

    def test_an_absent_native_flag_can_never_reach_none(self):
        """Even a stubbed completeness capability cannot promise completeness.

        Without a native flag nothing distinguishes a full screen from a
        clipped one, so rule 2 has to win over the capability rule. If this
        ordering were reversed, a 0.9.1 read would claim ``none``.
        """

        capability = {monitor.completeness_token("recent-unwrapped")}
        for counted in (0, 1, 3, 199, 200, 500):
            self.assertEqual(
                monitor.TRUNCATION_POSSIBLE,
                monitor.classify_truncation(
                    read_failed=False,
                    native_truncated=None,
                    lines_counted=counted,
                    lines_requested=200,
                    source="recent-unwrapped",
                    capabilities=capability,
                ),
                counted,
            )

    def test_a_failed_read_without_a_native_flag_is_still_confirmed(self):
        """Rule 1 keeps precedence over the new absent-flag rule."""

        capability = {monitor.completeness_token("recent-unwrapped")}
        self.assertEqual(
            monitor.TRUNCATION_CONFIRMED,
            monitor.classify_truncation(
                read_failed=True,
                native_truncated=None,
                lines_counted=0,
                lines_requested=200,
                source="recent-unwrapped",
                capabilities=capability,
            ),
        )

    def test_exact_budget_read_yields_possible(self):
        self.assertEqual(
            monitor.TRUNCATION_POSSIBLE,
            monitor.classify_truncation(
                read_failed=False,
                native_truncated=False,
                lines_counted=200,
                lines_requested=200,
                source="recent-unwrapped",
                capabilities={monitor.completeness_token("recent-unwrapped")},
            ),
        )

    def test_below_budget_with_the_empty_capability_set_is_still_possible(self):
        self.assertEqual(
            monitor.TRUNCATION_POSSIBLE,
            monitor.classify_truncation(
                read_failed=False,
                native_truncated=False,
                lines_counted=3,
                lines_requested=200,
                source="recent-unwrapped",
            ),
        )

    def test_below_budget_with_a_stubbed_completeness_capability_is_none(self):
        self.assertEqual(
            monitor.TRUNCATION_NONE,
            monitor.classify_truncation(
                read_failed=False,
                native_truncated=False,
                lines_counted=3,
                lines_requested=200,
                source="recent-unwrapped",
                capabilities={monitor.completeness_token("recent-unwrapped")},
            ),
        )

    def test_none_is_unreachable_on_the_shipped_capability_set(self):
        self.assertEqual(frozenset(), monitor.COMPLETENESS_CAPABILITIES)
        for counted in (0, 1, 199, 200, 500):
            self.assertNotEqual(
                monitor.TRUNCATION_NONE,
                monitor.classify_truncation(
                    read_failed=False,
                    native_truncated=False,
                    lines_counted=counted,
                    lines_requested=200,
                    source="recent-unwrapped",
                ),
            )

    def test_line_counting_is_done_by_the_adapter(self):
        self.assertEqual(0, monitor.count_lines(""))
        self.assertEqual(1, monitor.count_lines("one"))
        self.assertEqual(3, monitor.count_lines("a\nb\nc"))
        self.assertEqual(3, monitor.count_lines("a\nb\nc\n"))
        # Herdr 0.9.1 writes bare terminal text, so the count can come from
        # nowhere but the adapter itself.
        self.assertEqual(
            monitor.count_lines(AGENT_READ_TEXT),
            len(AGENT_READ_TEXT.splitlines()),
        )


# ---------------------------------------------------------------------------
# Observation
# ---------------------------------------------------------------------------


class ObservationTest(unittest.TestCase):
    def test_observation_has_no_completion_field(self):
        observation = monitor.observe_agent(
            "brichan-worker", runner=FakeRunner(healthy_responses())
        )
        rendered = json.loads(monitor.render_report(observation.as_dict()))
        for forbidden in ("done", "success", "complete", "completed", "finished", "ok"):
            self.assertNotIn(forbidden, rendered, forbidden)
            self.assertFalse(hasattr(observation, forbidden), forbidden)

    def test_scheduling_state_passes_through_uninterpreted(self):
        for state in ("idle", "working", "blocked", "done", "unknown", "future-state"):
            payload = copy.deepcopy(AGENT_GET_JSON)
            payload["result"]["agent"]["agent_status"] = state
            observation = monitor.observe_agent(
                "brichan-worker",
                runner=FakeRunner(healthy_responses(**{"agent get": ok_json(payload)})),
            )
            self.assertEqual(state, observation.scheduling_state)

    def test_a_healthy_text_read_is_possible_not_none_on_0_9_1(self):
        observation = monitor.observe_agent(
            "brichan-worker", runner=FakeRunner(healthy_responses()), lines=200
        )
        self.assertEqual(monitor.TRUNCATION_POSSIBLE, observation.truncation_risk)
        self.assertIsNone(observation.native_truncated)
        self.assertIsNone(observation.source_reported)
        self.assertEqual(AGENT_READ_TEXT, observation.text)
        self.assertEqual(3, observation.lines_counted)
        self.assertEqual(200, observation.lines_requested)
        self.assertEqual("recent-unwrapped", observation.source)
        self.assertIsNone(observation.read_error)
        self.assertNotIn("read-failed", observation.findings)

    def test_the_read_argv_pins_the_text_format(self):
        """Nothing may inherit a changed client default and parse ANSI bytes."""

        runner = FakeRunner(healthy_responses())
        monitor.observe_agent("brichan-worker", runner=runner)
        read = next(
            argv for argv in runner.calls if argv[1:3] == ["agent", "read"]
        )
        self.assertEqual("text", read[read.index("--format") + 1])
        monitor.assert_read_only(read)

    def test_read_failure_is_a_collected_finding_not_a_failed_report(self):
        for response in (
            fail("read failed"),
            fail("unknown option: --format", code=2),
            ok_text(""),
            ok_text("   \n\n"),
        ):
            observation = monitor.observe_agent(
                "brichan-worker",
                runner=FakeRunner(healthy_responses(**{"agent read": response})),
            )
            self.assertIn("read-failed", observation.findings)
            self.assertIsNotNone(observation.read_error)
            self.assertEqual(monitor.TRUNCATION_CONFIRMED, observation.truncation_risk)
            self.assertEqual("", observation.text)
            self.assertIsNone(observation.native_truncated)
            # The scheduling probe still succeeded, so the report exists.
            self.assertEqual("working", observation.scheduling_state)

    def test_a_failed_read_cannot_reach_none_even_with_a_stubbed_capability(self):
        """The H1 invariant, carried over to the plain-text read path."""

        capability = {monitor.completeness_token("recent-unwrapped")}
        for response in (fail("read failed"), ok_text(""), ok_text("  \n")):
            observation = monitor.observe_agent(
                "brichan-worker",
                runner=FakeRunner(healthy_responses(**{"agent read": response})),
                lines=200,
                capabilities=capability,
            )
            self.assertEqual(
                monitor.TRUNCATION_CONFIRMED, observation.truncation_risk
            )

    def test_agent_get_failure_makes_the_report_impossible(self):
        for response in (
            fail("agent target not found"),
            ok_json(AGENT_NOT_FOUND_JSON),
            ok_text("not json"),
            ok_json({"result": {}}),
        ):
            with self.assertRaises(monitor.AdapterError):
                monitor.observe_agent(
                    "brichan-missing",
                    runner=FakeRunner(healthy_responses(**{"agent get": response})),
                )

    # -- code review v2, finding H1, on the 0.9.1 plain-text read path -------

    #: Every entry is a command that exited ``0`` and is nonetheless not a
    #: usable read. On ``0.7.3`` these were partial JSON envelopes; on ``0.9.1``
    #: stdout *is* the read, so the equivalent defect is stdout that carries no
    #: screen at all. A live pane always shows at least a shell prompt, so each
    #: of these must be treated as failed rather than as a zero-line
    #: observation.
    EMPTY_READ_STDOUTS = {
        "empty stdout": "",
        "single newline": "\n",
        "blank lines": "\n\n\n",
        "spaces only": "    ",
        "tabs and newlines": "\t\n \n",
    }

    def test_canonical_source_normalizes_the_live_spelling_pair(self):
        self.assertEqual(
            monitor.canonical_source("recent-unwrapped"),
            monitor.canonical_source("recent_unwrapped"),
        )
        self.assertEqual("recent-unwrapped", monitor.canonical_source("Recent_Unwrapped"))
        self.assertNotEqual(
            monitor.canonical_source("visible"),
            monitor.canonical_source("recent-unwrapped"),
        )

    def test_the_read_reports_no_source_because_0_9_1_reports_none(self):
        """The adapter states what it does not know instead of echoing input.

        Reporting ``source_reported`` as the source that was *requested* would
        manufacture a confirmation the control plane never gave.
        """

        observation = monitor.observe_agent(
            "brichan-worker", runner=FakeRunner(healthy_responses())
        )
        self.assertIsNone(observation.read_error)
        self.assertIsNone(observation.source_reported)
        self.assertEqual("recent-unwrapped", observation.source)

    def test_every_empty_read_is_treated_as_failed(self):
        for label, stdout in self.EMPTY_READ_STDOUTS.items():
            observation = monitor.observe_agent(
                "brichan-worker",
                runner=FakeRunner(healthy_responses(**{"agent read": ok_text(stdout)})),
            )
            self.assertIn("read-failed", observation.findings, label)
            self.assertIsNotNone(observation.read_error, label)
            self.assertEqual(
                monitor.TRUNCATION_CONFIRMED, observation.truncation_risk, label
            )
            self.assertEqual("", observation.text, label)
            self.assertIsNone(observation.native_truncated, label)
            self.assertIsNone(observation.source_reported, label)

    def test_no_empty_read_can_reach_none_even_with_a_stubbed_capability(self):
        """The H1 regression: a contentless read must never look complete."""

        capability = {monitor.completeness_token("recent-unwrapped")}
        for label, stdout in self.EMPTY_READ_STDOUTS.items():
            observation = monitor.observe_agent(
                "brichan-worker",
                runner=FakeRunner(healthy_responses(**{"agent read": ok_text(stdout)})),
                lines=200,
                capabilities=capability,
            )
            self.assertEqual(
                monitor.TRUNCATION_CONFIRMED, observation.truncation_risk, label
            )

    def test_not_even_a_healthy_short_read_reaches_none_with_a_capability(self):
        """On 0.9.1 ``none`` is unreachable through the CLI at all.

        ``classify_truncation`` can still return ``none`` when it is handed an
        explicit ``native_truncated=False`` — ``TruncationTest`` pins that, so
        this assertion is not passing because the rule is inert. The adapter
        simply never has such a flag to hand it.
        """

        capability = {monitor.completeness_token("recent-unwrapped")}
        observation = monitor.observe_agent(
            "brichan-worker",
            runner=FakeRunner(healthy_responses()),
            lines=200,
            capabilities=capability,
        )
        self.assertEqual(monitor.TRUNCATION_POSSIBLE, observation.truncation_risk)
        self.assertIsNone(observation.read_error)

    def test_parse_read_payload_rejects_each_contentless_read_directly(self):
        for label, stdout in self.EMPTY_READ_STDOUTS.items():
            with self.assertRaises(monitor.AdapterError, msg=label):
                monitor.parse_read_payload(stdout, "brichan-worker", 200)

    def test_parse_read_payload_accepts_the_frozen_live_text(self):
        parsed = monitor.parse_read_payload(AGENT_READ_TEXT, "brichan-worker", 200)
        self.assertEqual(AGENT_READ_TEXT, parsed["text"])
        self.assertIsNone(parsed["truncated"])
        self.assertIsNone(parsed["source"])

    def test_the_read_adapter_refuses_the_json_path(self):
        """0.9.1 has no JSON read form, so the JSON adapter must not run one."""

        runner = FakeRunner(healthy_responses())
        with self.assertRaises(monitor.MonitorError):
            monitor.run_json(
                [
                    "herdr",
                    "agent",
                    "read",
                    "brichan-worker",
                    "--source",
                    "recent-unwrapped",
                    "--lines",
                    "200",
                ],
                runner,
            )
        self.assertEqual([], runner.calls)

    # -- code review v3, finding M1-v3: malformed outer envelopes ------------

    #: Syntactically valid JSON whose ``result`` container is not an object.
    #: A chained ``.get`` over these raises an unowned ``AttributeError``; the
    #: exit table requires an owned failure instead.
    MALFORMED_RESULT_ENVELOPES = {
        "result null": {"id": "cli:agent:x", "result": None},
        "result list": {"id": "cli:agent:x", "result": []},
        "result populated list": {"id": "cli:agent:x", "result": [{"read": {}}]},
        "result string": {"id": "cli:agent:x", "result": "ok"},
        "result integer": {"id": "cli:agent:x", "result": 3},
        "result boolean": {"id": "cli:agent:x", "result": True},
        "result absent": {"id": "cli:agent:x"},
    }

    def test_envelope_result_owns_every_malformed_container(self):
        for label, payload in self.MALFORMED_RESULT_ENVELOPES.items():
            with self.assertRaises(monitor.AdapterError, msg=label):
                monitor.envelope_result(payload, "herdr agent read w")

    def test_envelope_result_returns_the_object_when_well_formed(self):
        self.assertEqual(
            AGENT_GET_JSON["result"],
            monitor.envelope_result(AGENT_GET_JSON, "herdr agent get w"),
        )

    def test_a_malformed_result_on_the_get_path_is_an_owned_adapter_error(self):
        for label, payload in self.MALFORMED_RESULT_ENVELOPES.items():
            runner = FakeRunner(healthy_responses(**{"agent get": ok_json(payload)}))
            with self.assertRaises(monitor.AdapterError, msg=label):
                monitor.observe_agent("brichan-worker", runner=runner)

    def test_no_malformed_envelope_raises_an_unowned_exception(self):
        """Anything not derived from MonitorError would escape as a traceback."""

        for label, payload in self.MALFORMED_RESULT_ENVELOPES.items():
            for command in ("agent get",):
                runner = FakeRunner(
                    healthy_responses(**{command: ok_json(payload)})
                )
                try:
                    monitor.observe_agent("brichan-worker", runner=runner)
                except monitor.MonitorError:
                    pass
                except Exception as error:  # pragma: no cover - the defect
                    self.fail(
                        f"{label} via {command} raised unowned "
                        f"{type(error).__name__}: {error}"
                    )

    def test_observe_never_sends_input_to_a_blocked_agent(self):
        payload = copy.deepcopy(AGENT_GET_JSON)
        payload["result"]["agent"]["agent_status"] = "blocked"
        runner = FakeRunner(healthy_responses(**{"agent get": ok_json(payload)}))
        observation = monitor.observe_agent("brichan-worker", runner=runner)
        self.assertEqual("blocked", observation.scheduling_state)
        for argv in runner.calls:
            monitor.assert_read_only(argv)


# ---------------------------------------------------------------------------
# Descriptor-anchored path validation
# ---------------------------------------------------------------------------


class ProjectRootValidationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def test_a_valid_absolute_directory_root_is_accepted(self):
        descriptor = monitor.open_project_root(str(self.root))
        try:
            self.assertTrue(stat.S_ISDIR(os.fstat(descriptor).st_mode))
        finally:
            os.close(descriptor)

    def test_a_relative_root_is_rejected_before_any_filesystem_access(self):
        with self.assertRaises(monitor.PathValidationError):
            monitor.open_project_root("relative/project")

    def test_a_symlinked_root_is_rejected(self):
        target = self.root / "real"
        target.mkdir()
        link = self.root / "link"
        link.symlink_to(target, target_is_directory=True)
        with self.assertRaises(monitor.PathValidationError):
            monitor.open_project_root(str(link))

    def test_a_non_directory_root_is_rejected(self):
        regular = self.root / "file.txt"
        regular.write_text("x", encoding="utf-8")
        with self.assertRaises(monitor.PathValidationError):
            monitor.open_project_root(str(regular))

    def test_a_root_that_changes_identity_during_validation_is_rejected(self):
        other = self.root / "other"
        other.mkdir()
        target = self.root / "target"
        target.mkdir()

        def swapping_opener(name, flags, **kwargs):
            # Simulate the root being replaced between lstat and open.
            return os.open(str(other), flags, **kwargs)

        with self.assertRaises(monitor.PathValidationError) as caught:
            monitor.open_project_root(str(target), opener=swapping_opener)
        self.assertIn("changed identity", str(caught.exception))

    def test_a_missing_root_is_rejected(self):
        with self.assertRaises(monitor.PathValidationError):
            monitor.open_project_root(str(self.root / "absent"))


class EvidencePathValidationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        (self.root / "docs").mkdir()
        (self.root / "docs" / "evidence.md").write_text("hello\n", encoding="utf-8")
        self.fd = monitor.open_project_root(str(self.root))
        self.addCleanup(os.close, self.fd)

    def collect(self, *paths, opener=os.open):
        return monitor.collect_evidence(self.fd, list(paths), opener=opener)

    def test_a_declared_relative_file_reports_presence_metadata(self):
        (report,) = self.collect("docs/evidence.md")
        self.assertTrue(report.exists)
        self.assertTrue(report.is_regular_file)
        self.assertEqual(6, report.size_bytes)
        self.assertIsNotNone(report.mtime)

    def test_a_validated_but_absent_path_is_evidence_missing_not_a_rejection(self):
        (report,) = self.collect("docs/absent.md")
        self.assertFalse(report.exists)
        self.assertIsNone(report.size_bytes)
        (report,) = self.collect("absent-dir/absent.md")
        self.assertFalse(report.exists)

    def test_absolute_paths_are_rejected(self):
        with self.assertRaises(monitor.PathValidationError):
            self.collect("/etc/passwd")

    def test_home_relative_paths_are_rejected(self):
        for path in ("~/secrets.md", "~"):
            with self.assertRaises(monitor.PathValidationError, msg=path):
                self.collect(path)

    def test_dot_dot_segments_are_rejected(self):
        for path in ("../escape.md", "docs/../../escape.md", "docs/.."):
            with self.assertRaises(monitor.PathValidationError, msg=path):
                self.collect(path)

    def test_empty_paths_are_rejected(self):
        for path in ("", "   ", "/", "./"):
            with self.assertRaises(monitor.PathValidationError, msg=repr(path)):
                self.collect(path)

    def test_a_symlinked_intermediate_component_is_rejected(self):
        (self.root / "outside").mkdir()
        (self.root / "outside" / "leak.md").write_text("x", encoding="utf-8")
        (self.root / "link").symlink_to(self.root / "outside", target_is_directory=True)
        with self.assertRaises(monitor.PathValidationError) as caught:
            self.collect("link/leak.md")
        self.assertIn("symlink", str(caught.exception))

    def test_a_symlinked_final_component_is_rejected(self):
        (self.root / "docs" / "alias.md").symlink_to(self.root / "docs" / "evidence.md")
        with self.assertRaises(monitor.PathValidationError) as caught:
            self.collect("docs/alias.md")
        self.assertIn("symlink", str(caught.exception))

    def test_a_non_directory_intermediate_component_is_rejected(self):
        with self.assertRaises(monitor.PathValidationError):
            self.collect("docs/evidence.md/nested.md")

    def test_a_directory_evidence_path_is_reported_as_not_a_regular_file(self):
        (report,) = self.collect("docs")
        self.assertTrue(report.exists)
        self.assertFalse(report.is_regular_file)
        self.assertIsNone(report.size_bytes)

    def test_every_open_is_descriptor_relative_and_no_follow(self):
        opener = RecordingOpener()
        self.collect("docs/evidence.md", opener=opener)
        self.assertEqual(2, len(opener.opens))
        for record in opener.opens:
            self.assertIsNotNone(record["dir_fd"], record)
            self.assertTrue(record["flags"] & os.O_NOFOLLOW, record)
            self.assertNotIn("/", record["name"], record)
        self.assertTrue(opener.opens[0]["flags"] & os.O_DIRECTORY)
        self.assertFalse(opener.opens[1]["flags"] & os.O_DIRECTORY)

    def test_metadata_comes_from_the_held_descriptor_not_a_pathname_relookup(self):
        """Replacing the file after the walk cannot change the reported size."""

        captured: dict[str, int] = {}
        real_fstat = os.fstat

        def swapping_fstat(descriptor):
            info = real_fstat(descriptor)
            if stat.S_ISREG(info.st_mode) and "swapped" not in captured:
                captured["swapped"] = 1
                # Replace the pathname's target after the descriptor is held.
                (self.root / "docs" / "evidence.md").unlink()
                (self.root / "docs" / "evidence.md").write_text(
                    "a much longer replacement body\n", encoding="utf-8"
                )
            return info

        with mock.patch.object(monitor.os, "fstat", swapping_fstat):
            (report,) = self.collect("docs/evidence.md")
        self.assertEqual(1, captured.get("swapped"))
        self.assertEqual(6, report.size_bytes)

    def test_the_walk_never_creates_writes_or_deletes_anything(self):
        opener = RecordingOpener()
        before = sorted(path.name for path in self.root.rglob("*"))
        self.collect("docs/evidence.md", "docs/absent.md", opener=opener)
        after = sorted(path.name for path in self.root.rglob("*"))
        self.assertEqual(before, after)
        self.assertTrue(opener.opens)
        for record in opener.opens:
            for write_flag in (os.O_CREAT, os.O_WRONLY, os.O_RDWR, os.O_TRUNC):
                self.assertFalse(record["flags"] & write_flag, record)


# ---------------------------------------------------------------------------
# Exit-code table (design.md v5, "CLI and exit semantics")
# ---------------------------------------------------------------------------


class ExitTableTest(unittest.TestCase):
    """Table-driven over every row of the design's subcommand-by-state table."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        (self.root / "docs").mkdir()
        (self.root / "docs" / "evidence.md").write_text("ok\n", encoding="utf-8")

    def assert_exit(self, code, argv, runner=None, herdr_on_path=True):
        actual, out, err = run_main(
            argv, runner or FakeRunner(healthy_responses()), herdr_on_path
        )
        self.assertEqual(code, actual, f"{argv} -> {err or out}")
        if code == 0:
            self.assertEqual("", err)
            payload = json.loads(out)
            self.assertEqual(out, monitor.render_report(payload))
            self.assertTrue(out.endswith("\n"))
        else:
            self.assertEqual("", out)
            self.assertTrue(err.strip())
        return out, err

    # -- exit 2: invalid argv ------------------------------------------------

    def test_invalid_argv_exits_2(self):
        for argv in (
            [],
            ["nonsense"],
            ["preflight", "--nope"],
            ["observe"],
            ["observe", "w", "--lines", "0"],
            ["observe", "w", "--lines", "-1"],
            ["observe", "w", "--lines", "abc"],
            ["observe", "w", "--lines", "1.5"],
            ["observe", "w", "--evidence", "docs/evidence.md"],
        ):
            self.assert_exit(2, argv)

    # -- exit 2: rejected project roots -------------------------------------

    def test_rejected_project_roots_exit_2(self):
        link = self.root / "link"
        link.symlink_to(self.root / "docs", target_is_directory=True)
        regular = self.root / "docs" / "evidence.md"
        for root in ("relative/path", str(link), str(regular), str(self.root / "gone")):
            self.assert_exit(2, ["observe", "brichan-worker", "--project-root", root])

    def test_a_changed_identity_root_exits_2(self):
        other = self.root / "other"
        other.mkdir()
        real_open_project_root = monitor.open_project_root

        def swapping_opener(name, flags, **kwargs):
            # Simulate the root being replaced between lstat and open.
            return os.open(str(other), flags, **kwargs)

        def patched(root, **_kwargs):
            return real_open_project_root(root, opener=swapping_opener)

        runner = FakeRunner(healthy_responses())
        with mock.patch.object(monitor, "open_project_root", patched):
            code, out, err = run_main(
                ["observe", "brichan-worker", "--project-root", str(self.root)],
                runner,
            )
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("changed identity", err)
        self.assertEqual([], runner.calls)

    # -- exit 2: rejected evidence paths -------------------------------------

    def test_rejected_evidence_paths_exit_2(self):
        (self.root / "outside").mkdir()
        (self.root / "outside" / "leak.md").write_text("x", encoding="utf-8")
        (self.root / "link").symlink_to(self.root / "outside", target_is_directory=True)
        (self.root / "docs" / "alias.md").symlink_to(self.root / "docs" / "evidence.md")
        for evidence in (
            "/etc/passwd",
            "~/secrets.md",
            "../escape.md",
            "docs/../../escape.md",
            "",
            "link/leak.md",
            "docs/alias.md",
        ):
            self.assert_exit(
                2,
                [
                    "observe",
                    "brichan-worker",
                    "--project-root",
                    str(self.root),
                    "--evidence",
                    evidence,
                ],
            )

    def test_a_rejected_path_wins_over_a_healthy_agent(self):
        """Combined-outcome precedence: class 2 always beats class 0."""

        runner = FakeRunner(healthy_responses())
        self.assert_exit(
            2,
            [
                "observe",
                "brichan-worker",
                "--project-root",
                str(self.root),
                "--evidence",
                "../escape.md",
            ],
            runner,
        )
        # Validation happened before any subprocess.
        self.assertEqual([], runner.calls)

    # -- exit 1: report impossible -------------------------------------------

    def test_missing_herdr_exits_1_for_both_subcommands(self):
        self.assert_exit(1, ["preflight"], herdr_on_path=False)
        self.assert_exit(1, ["observe", "brichan-worker"], herdr_on_path=False)

    def test_status_probe_failure_exits_1(self):
        for response in (fail("connection refused"), ok_text("usage: herdr status")):
            self.assert_exit(
                1, ["preflight"], FakeRunner(healthy_responses(status=response))
            )

    def test_status_schema_invalid_exits_1(self):
        for section, field in StatusSchemaTest.REQUIRED:
            payload = copy.deepcopy(STATUS_JSON)
            del payload[section][field]
            _, err = self.assert_exit(
                1, ["preflight"], FakeRunner(healthy_responses(status=ok_json(payload)))
            )
            self.assertIn("status-schema-invalid", err)
            payload = copy.deepcopy(STATUS_JSON)
            payload[section][field] = ["mistyped"]
            _, err = self.assert_exit(
                1, ["preflight"], FakeRunner(healthy_responses(status=ok_json(payload)))
            )
            self.assertIn("status-schema-invalid", err)

    def test_agent_get_failure_and_not_found_exit_1(self):
        for response in (
            fail("agent target brichan-missing not found"),
            ok_json(AGENT_NOT_FOUND_JSON),
            ok_text("not json"),
        ):
            self.assert_exit(
                1,
                ["observe", "brichan-missing"],
                FakeRunner(healthy_responses(**{"agent get": response})),
            )

    # -- exit 0: collected preflight reports ---------------------------------

    def test_verified_and_healthy_preflight_exits_0(self):
        out, _ = self.assert_exit(0, ["preflight"])
        payload = json.loads(out)
        self.assertEqual("verified", payload["support"])
        self.assertEqual([], payload["findings"])

    def test_unverified_version_exits_0(self):
        runner = FakeRunner(
            healthy_responses(status=ok_json(status_with(server__version="0.9.9")))
        )
        out, _ = self.assert_exit(0, ["preflight"], runner)
        self.assertEqual("unverified", json.loads(out)["support"])

    def test_incompatible_and_restart_findings_survive_json_rendering_at_0(self):
        cases = {
            "incompatible-control-plane": status_with(server__compatible=False),
            "restart-needed(server)": status_with(server__restart_needed=True),
            "restart-needed(update)": status_with(update__restart_needed=True),
        }
        for finding, payload in cases.items():
            runner = FakeRunner(healthy_responses(status=ok_json(payload)))
            out, _ = self.assert_exit(0, ["preflight"], runner)
            self.assertIn(finding, json.loads(out)["findings"], finding)

    def test_the_combined_finding_case_exits_0_with_a_union(self):
        payload = status_with(
            server__version="0.9.0",
            server__compatible=False,
            server__restart_needed=True,
        )
        payload["update"]["restart_needed"] = True
        runner = FakeRunner(
            healthy_responses(
                status=ok_json(payload),
                **{
                    "integration status": ok_text(
                        "codex: outdated (v5) (/Users/example/.codex/hook.sh)\n"
                        "quokka: current (v1) (/Users/example/.quokka/hook.sh)\n"
                        "garbage row\n"
                    ),
                    "agent explain": ok_json(EXPLAIN_TRUST_DIRECTORY_JSON),
                },
            )
        )
        out, _ = self.assert_exit(0, ["preflight", "--agent", "brichan-worker"], runner)
        report = json.loads(out)
        self.assertEqual("unverified", report["support"])
        for finding in (
            "unverified-version",
            "incompatible-control-plane",
            "restart-needed(server)",
            "restart-needed(update)",
            "integration-unhealthy(codex=outdated)",
            "unknown-row(2)",
            "malformed-row(3)",
            "capability-drift",
        ):
            self.assertIn(finding, report["findings"], finding)
        self.assertEqual(
            "rule trust_directory uses invalid region: top_non_empty_lines(20)",
            report["capabilities"][0]["detail"],
        )

    def test_integration_probe_states_exit_0(self):
        cases = {
            "integration-unhealthy": fail("usage:", code=2),
            "unknown-row(1)": ok_text("quokka: current (v1) (/Users/example/hook.sh)\n"),
            "malformed-row(1)": ok_text("no separator here\n"),
            "integration-unhealthy(claude=not installed)": ok_text(
                "claude: not installed (/Users/example/.claude/hooks/hook.sh)\n"
            ),
        }
        for finding, response in cases.items():
            runner = FakeRunner(
                healthy_responses(**{"integration status": response})
            )
            out, _ = self.assert_exit(0, ["preflight"], runner)
            self.assertIn(finding, json.loads(out)["findings"], finding)

    def test_capability_finding_exits_0(self):
        runner = FakeRunner(
            healthy_responses(**{"agent explain": ok_json(EXPLAIN_TRUST_DIRECTORY_JSON)})
        )
        out, _ = self.assert_exit(0, ["preflight", "--agent", "brichan-worker"], runner)
        self.assertIn("capability-drift", json.loads(out)["findings"])

    # -- exit 0: collected observations --------------------------------------

    def test_read_failure_is_collected_at_0(self):
        runner = FakeRunner(healthy_responses(**{"agent read": fail("read failed")}))
        out, _ = self.assert_exit(0, ["observe", "brichan-worker"], runner)
        report = json.loads(out)
        self.assertIn("read-failed", report["findings"])
        self.assertEqual("confirmed", report["truncation_risk"])
        self.assertIsNotNone(report["read_error"])

    def test_an_empty_read_is_collected_at_0(self):
        """The 0.9.1 analogue of the M1-v3 row, through the exit table."""

        for label, stdout in ObservationTest.EMPTY_READ_STDOUTS.items():
            runner = FakeRunner(healthy_responses(**{"agent read": ok_text(stdout)}))
            out, _ = self.assert_exit(0, ["observe", "brichan-worker"], runner)
            report = json.loads(out)
            self.assertIn("read-failed", report["findings"], label)
            self.assertIsNotNone(report["read_error"], label)
            self.assertEqual("confirmed", report["truncation_risk"], label)

    def test_a_malformed_result_envelope_get_exits_1(self):
        for label, payload in ObservationTest.MALFORMED_RESULT_ENVELOPES.items():
            runner = FakeRunner(healthy_responses(**{"agent get": ok_json(payload)}))
            _, err = self.assert_exit(1, ["observe", "brichan-worker"], runner)
            self.assertIn("brichan-herdr-agent-observe:", err, label)
            self.assertNotIn("Traceback", err, label)

    def test_truncation_risk_states_are_collected_at_0(self):
        out, _ = self.assert_exit(0, ["observe", "brichan-worker"])
        report = json.loads(out)
        self.assertEqual("possible", report["truncation_risk"])
        self.assertIsNone(report["native_truncated"])

        runner = FakeRunner(healthy_responses(**{"agent read": fail("read failed")}))
        out, _ = self.assert_exit(0, ["observe", "brichan-worker"], runner)
        self.assertEqual("confirmed", json.loads(out)["truncation_risk"])

    def test_missing_evidence_is_collected_at_0(self):
        out, _ = self.assert_exit(
            0,
            [
                "observe",
                "brichan-worker",
                "--project-root",
                str(self.root),
                "--evidence",
                "docs/evidence.md",
                "--evidence",
                "docs/absent.md",
            ],
        )
        report = json.loads(out)
        self.assertIn("evidence-missing(docs/absent.md)", report["findings"])
        self.assertTrue(report["evidence"][0]["exists"])
        self.assertFalse(report["evidence"][1]["exists"])

    def test_read_failure_with_missing_evidence_is_one_collected_report_at_0(self):
        """Combined-outcome precedence: both findings present, exit 0."""

        runner = FakeRunner(healthy_responses(**{"agent read": fail("read failed")}))
        out, _ = self.assert_exit(
            0,
            [
                "observe",
                "brichan-worker",
                "--project-root",
                str(self.root),
                "--evidence",
                "docs/absent.md",
            ],
            runner,
        )
        report = json.loads(out)
        self.assertIn("read-failed", report["findings"])
        self.assertIn("evidence-missing(docs/absent.md)", report["findings"])
        self.assertEqual("confirmed", report["truncation_risk"])

    def test_blocked_and_other_scheduling_states_pass_through_at_0(self):
        for state in ("idle", "working", "blocked", "done", "unknown", "future-state"):
            payload = copy.deepcopy(AGENT_GET_JSON)
            payload["result"]["agent"]["agent_status"] = state
            runner = FakeRunner(healthy_responses(**{"agent get": ok_json(payload)}))
            out, _ = self.assert_exit(0, ["observe", "brichan-worker"], runner)
            report = json.loads(out)
            self.assertEqual(state, report["scheduling_state"])
            for forbidden in ("done", "success", "complete"):
                self.assertNotIn(forbidden, report)

    def test_reports_are_deterministic_json(self):
        out, _ = self.assert_exit(0, ["preflight"])
        self.assertEqual(out, monitor.render_report(json.loads(out)))
        top_level = [
            line.strip().split('"')[1]
            for line in out.splitlines()
            if line.startswith('  "')
        ]
        self.assertEqual(sorted(top_level), top_level)
        self.assertEqual(sorted(json.loads(out).keys()), top_level)
        self.assertTrue(out.endswith("\n"))
        self.assertFalse(out.endswith("\n\n"))
        repeated, _ = self.assert_exit(0, ["preflight"])
        self.assertEqual(out, repeated)


if __name__ == "__main__":
    unittest.main()
