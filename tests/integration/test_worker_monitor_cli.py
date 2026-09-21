"""Stubbed-CLI matrix for ``bin/brichan-herdr-agent-observe``.

Table-driven over every row of the ``design.md`` version 5 exit table. Each
case invokes the real wrapper as a subprocess against a stubbed ``herdr``
executable placed first on ``PATH``, and asserts both the exit code and the
stdout/stderr shape: a deterministic JSON report on stdout for exit ``0``,
diagnostics on stderr for exits ``1`` and ``2``.

The stub payloads mirror the fixtures frozen from live read-only Herdr probes:
``0.7.3`` on 2026-08-14 and ``0.9.1`` on 2026-09-18 (task ``HERDR-091``). No
case requires a live Herdr, Codex, or Claude session.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OBSERVE = ROOT / "bin/brichan-herdr-agent-observe"

STATUS_JSON = {
    "client": {"version": "0.7.3", "channel": "stable", "protocol": 16},
    "server": {
        "status": "running",
        "running": True,
        "version": "0.7.3",
        "protocol": 16,
        "compatible": True,
        "restart_needed": False,
    },
    "update": {"restart_needed": False},
}

INTEGRATION_TEXT = (
    "claude: current (v7) (/Users/example/.claude/hooks/herdr-agent-state.sh)\n"
    "codex: current (v6) (/Users/example/.codex/herdr-agent-state.sh)\n"
    "kimi: not installed (/Users/example/.kimi-code/hooks/herdr-agent-state.sh)\n"
)

AGENT_GET_JSON = {
    "id": "cli:agent:get",
    "result": {
        "agent": {
            "agent": "claude",
            "agent_status": "working",
            "name": "brichan-worker",
            "pane_id": "w37:p8",
            "tab_id": "w37:t1",
            "workspace_id": "w37",
        },
        "type": "agent_info",
    },
}

#: ``herdr agent read`` on ``0.9.1`` writes the terminal snapshot itself to
#: stdout: no envelope, no source echo, no native ``truncated`` flag.
AGENT_READ_TEXT = "line one\nline two\nline three"

#: ``herdr status --json`` on ``0.9.1``: keys added, none removed.
STATUS_JSON_091 = {
    "client": {"version": "0.9.1", "channel": "stable", "protocol": 22},
    "server": {
        "status": "running",
        "running": True,
        "version": "0.9.1",
        "protocol": 22,
        "compatible": True,
        "endpoint_compatible": True,
        "restart_needed": False,
        "server_binary_stale": False,
    },
    "update": {"restart_needed": False, "server_binary_stale": False},
}

#: The ``0.9.1`` row shapes the widened grammar has to accept: the
#: ``outdated (vN < vM)`` comparison, the ``(experimental)`` runtime
#: qualifier, and the four runtimes ``0.9.1`` added.
INTEGRATION_TEXT_091 = (
    "claude: current (v10) (/Users/example/.claude/hooks/herdr-agent-state.sh)\n"
    "codex: current (v8) (/Users/example/.codex/herdr-agent-state.sh)\n"
    "droid: outdated (v2 < v3) (/Users/example/.factory/hooks/herdr-agent-state.sh)\n"
    "qwen: not installed (/Users/example/.qwen/hooks/herdr-agent-session.sh)\n"
    "antigravity-cli: not installed "
    "(/Users/example/.gemini/config/hooks/herdr-agent-state.sh)\n"
    "grok: not installed (/Users/example/.grok/hooks/herdr-agent-state.sh)\n"
    "letta (experimental): not installed "
    "(/Users/example/.letta/hooks/herdr-agent-session.sh)\n"
)

AGENT_NOT_FOUND_JSON = {
    "error": {
        "code": "agent_not_found",
        "message": "agent target brichan-missing not found",
    },
    "id": "cli:agent:get",
}

EXPLAIN_TRUST_DIRECTORY_JSON = {
    "agent": "codex",
    "remote_update_error": (
        "rule trust_directory uses invalid region: top_non_empty_lines(20)"
    ),
    "remote_update_status": "failed",
    "state": "working",
    "warning": None,
    "fallback_reason": None,
}

EXPLAIN_HEALTHY_JSON = {
    "agent": "claude",
    "remote_update_error": None,
    "remote_update_status": "current",
    "state": "working",
    "warning": None,
    "fallback_reason": None,
}

STUB_SOURCE = '''#!/usr/bin/env python3
"""Stubbed read-only Herdr. Serves canned payloads and logs every argv."""
import json, os, sys

argv = sys.argv[1:]
with open(os.environ["STUB_HERDR_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(argv) + "\\n")

responses = json.loads(os.environ["STUB_HERDR_RESPONSES"])
words = [part for part in argv if not part.startswith("-")]
key = " ".join(words[:2])
for candidate in (key, " ".join(words[:1])):
    if candidate in responses:
        entry = responses[candidate]
        break
else:
    sys.stderr.write("stub: unexpected command %s\\n" % " ".join(argv))
    raise SystemExit(97)

if entry.get("stdout") is not None:
    sys.stdout.write(entry["stdout"])
if entry.get("stderr"):
    sys.stderr.write(entry["stderr"])
raise SystemExit(entry.get("exit", 0))
'''


#: Test-only harness injected into the wrapper subprocess through
#: ``PYTHONPATH``. It runs at interpreter startup, before ``brichan`` is
#: imported, which is what makes the seams below deterministic. Nothing here
#: exists in or is reachable from production code: the wrapper behaves normally
#: unless a test sets the environment variables.
#:
#: ``MONITOR_TEST_SWAP_ROOT`` / ``MONITOR_TEST_SWAP_TO`` reproduce the
#: changed-identity project root: the ``lstat`` sees the declared root, while
#: the subsequent ``O_DIRECTORY`` open lands on a different directory, so the
#: device/inode comparison must reject it (code review v2, finding M3).
#:
#: ``MONITOR_TEST_COMPLETENESS_SOURCE`` stubs a completeness capability so the
#: stubbed-CLI layer can prove that no read — failed, empty, or healthy — can
#: reach truncation risk ``none`` on Herdr ``0.9.1`` (code review v2, finding
#: H1, carried onto the plain-text read path).
SITECUSTOMIZE_SOURCE = '''
import os
import sys

_swap_from = os.environ.get("MONITOR_TEST_SWAP_ROOT")
_swap_to = os.environ.get("MONITOR_TEST_SWAP_TO")
if _swap_from and _swap_to:
    _real_open = os.open

    def _redirecting_open(path, flags, *args, **kwargs):
        if (
            kwargs.get("dir_fd") is None
            and isinstance(path, str)
            and path == _swap_from
            and flags & os.O_DIRECTORY
        ):
            return _real_open(_swap_to, flags, *args, **kwargs)
        return _real_open(path, flags, *args, **kwargs)

    os.open = _redirecting_open

_capability_source = os.environ.get("MONITOR_TEST_COMPLETENESS_SOURCE")
if _capability_source:
    sys.path.insert(0, os.environ["MONITOR_TEST_SRC"])
    from brichan.orchestration import monitor

    _capabilities = frozenset({monitor.completeness_token(_capability_source)})
    monitor.COMPLETENESS_CAPABILITIES = _capabilities
    monitor.observe_agent.__kwdefaults__["capabilities"] = _capabilities
'''


def payload(value):
    return {"stdout": json.dumps(value), "exit": 0}


def text(value):
    return {"stdout": value, "exit": 0}


def failure(message="stub failure", code=1):
    return {"stdout": "", "stderr": message, "exit": code}


def healthy(**overrides):
    """The supported control plane. Since plan v3 that is Herdr ``0.9.1``."""

    responses = {
        "status": payload(STATUS_JSON_091),
        "integration status": text(INTEGRATION_TEXT),
        "agent get": payload(AGENT_GET_JSON),
        "agent read": text(AGENT_READ_TEXT),
        "agent explain": payload(EXPLAIN_HEALTHY_JSON),
    }
    responses.update(overrides)
    return responses


def status_with(**changes):
    document = json.loads(json.dumps(STATUS_JSON_091))
    for dotted, value in changes.items():
        section, _, field = dotted.partition("__")
        document[section][field] = value
    return document


def status_without(section, field):
    document = json.loads(json.dumps(STATUS_JSON_091))
    del document[section][field]
    return document


def status_mistyping(section, field):
    document = json.loads(json.dumps(STATUS_JSON_091))
    document[section][field] = ["mistyped"]
    return document


class WorkerMonitorCliTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.temp_path = Path(self.temporary.name)
        self.log_path = self.temp_path / "herdr-calls.jsonl"
        self.stub_dir = self.temp_path / "bin"
        self.stub_dir.mkdir()
        stub = self.stub_dir / "herdr"
        stub.write_text(STUB_SOURCE, encoding="utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)

        self.project = self.temp_path / "project"
        (self.project / "docs").mkdir(parents=True)
        (self.project / "docs" / "evidence.md").write_text("ok\n", encoding="utf-8")

    # -- harness -----------------------------------------------------------

    def run_observe(self, *arguments, responses=None, herdr_on_path=True, seams=None):
        environment = os.environ.copy()
        base = environment.get("PATH", "")
        if herdr_on_path:
            environment["PATH"] = f"{self.stub_dir}{os.pathsep}{base}"
        else:
            # An empty PATH keeps the stub — and any real herdr — unreachable.
            environment["PATH"] = str(self.temp_path / "empty")
        environment["STUB_HERDR_LOG"] = str(self.log_path)
        environment["STUB_HERDR_RESPONSES"] = json.dumps(
            healthy() if responses is None else responses
        )
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        if seams:
            harness = self.temp_path / "harness"
            harness.mkdir(exist_ok=True)
            (harness / "sitecustomize.py").write_text(
                SITECUSTOMIZE_SOURCE, encoding="utf-8"
            )
            environment["PYTHONPATH"] = os.pathsep.join(
                filter(None, [str(harness), environment.get("PYTHONPATH", "")])
            )
            environment["MONITOR_TEST_SRC"] = str(ROOT / "src")
            environment.update(seams)
        return subprocess.run(
            [sys.executable, str(OBSERVE), *arguments],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def stub_calls(self):
        if not self.log_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.log_path.read_text(encoding="utf-8").splitlines()
            if line
        ]

    def assert_row(
        self, exit_code, arguments, responses=None, herdr_on_path=True, seams=None
    ):
        """Assert one exit-table row: exit code plus stdout/stderr shape."""

        result = self.run_observe(
            *arguments,
            responses=responses,
            herdr_on_path=herdr_on_path,
            seams=seams,
        )
        self.assertEqual(
            exit_code,
            result.returncode,
            f"{arguments}\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        if exit_code == 0:
            self.assertEqual("", result.stderr, arguments)
            report = json.loads(result.stdout)
            expected = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False)
            self.assertEqual(expected + "\n", result.stdout, arguments)
            return report
        self.assertEqual("", result.stdout, arguments)
        self.assertTrue(result.stderr.strip(), arguments)
        return result.stderr

    # -- exit 2: invalid argv (both subcommands) ----------------------------

    def test_invalid_argv_exits_2_on_stderr(self):
        for arguments in (
            [],
            ["nonsense"],
            ["preflight", "--unknown-flag"],
            ["observe"],
            ["observe", "brichan-worker", "--unknown-flag"],
            ["observe", "brichan-worker", "--lines", "0"],
            ["observe", "brichan-worker", "--lines", "-3"],
            ["observe", "brichan-worker", "--lines", "many"],
            ["observe", "brichan-worker", "--lines", "2.5"],
            ["observe", "brichan-worker", "--evidence", "docs/evidence.md"],
        ):
            self.assert_row(2, arguments)
        self.assertEqual([], self.stub_calls())

    # -- exit 2: rejected project roots -------------------------------------

    def test_rejected_project_roots_exit_2_on_stderr(self):
        link = self.temp_path / "root-link"
        link.symlink_to(self.project, target_is_directory=True)
        for root in (
            "relative/project",
            str(link),
            str(self.project / "docs" / "evidence.md"),
            str(self.temp_path / "absent-root"),
        ):
            self.assert_row(2, ["observe", "brichan-worker", "--project-root", root])
        self.assertEqual([], self.stub_calls())

    def test_a_changed_identity_project_root_exits_2_at_the_wrapper(self):
        """Code review v2, finding M3: the exit table's changed-identity row.

        The seam makes the condition deterministic: ``lstat`` observes the
        declared root while the ``O_DIRECTORY`` open lands on a different
        directory, exactly as a root replaced between the two calls would.
        """

        other = self.temp_path / "swapped-root"
        other.mkdir()
        result = self.run_observe(
            "observe",
            "brichan-worker",
            "--project-root",
            str(self.project),
            "--evidence",
            "docs/evidence.md",
            seams={
                "MONITOR_TEST_SWAP_ROOT": str(self.project),
                "MONITOR_TEST_SWAP_TO": str(other),
            },
        )
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)
        self.assertIn("changed identity", result.stderr)
        self.assertEqual([], self.stub_calls())

    def test_the_identity_seam_does_not_reject_an_untouched_root(self):
        """The seam only fires for the swapped root, so the row is real."""

        other = self.temp_path / "swapped-root"
        other.mkdir()
        result = self.run_observe(
            "observe",
            "brichan-worker",
            "--project-root",
            str(self.project),
            "--evidence",
            "docs/evidence.md",
            seams={
                "MONITOR_TEST_SWAP_ROOT": str(self.temp_path / "unrelated"),
                "MONITOR_TEST_SWAP_TO": str(other),
            },
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(json.loads(result.stdout)["evidence"][0]["exists"])

    # -- exit 2: rejected evidence paths -------------------------------------

    def test_rejected_evidence_paths_exit_2_on_stderr(self):
        (self.temp_path / "outside").mkdir()
        (self.temp_path / "outside" / "leak.md").write_text("x", encoding="utf-8")
        (self.project / "link").symlink_to(
            self.temp_path / "outside", target_is_directory=True
        )
        (self.project / "docs" / "alias.md").symlink_to(
            self.project / "docs" / "evidence.md"
        )
        for evidence in (
            "/etc/passwd",
            "~/secrets.md",
            "../escape.md",
            "docs/../../escape.md",
            "",
            "link/leak.md",
            "docs/alias.md",
        ):
            self.assert_row(
                2,
                [
                    "observe",
                    "brichan-worker",
                    "--project-root",
                    str(self.project),
                    "--evidence",
                    evidence,
                ],
            )
        # Class-2 conditions win before any subprocess runs.
        self.assertEqual([], self.stub_calls())

    # -- exit 1: report impossible -------------------------------------------

    def test_missing_herdr_exits_1_for_both_subcommands(self):
        for arguments in (["preflight"], ["observe", "brichan-worker"]):
            stderr = self.assert_row(1, arguments, herdr_on_path=False)
            self.assertIn("herdr", stderr)

    def test_status_probe_failures_exit_1(self):
        for response in (
            failure("connection refused"),
            text("usage: herdr status"),
            text(""),
            text("{not json"),
        ):
            self.assert_row(1, ["preflight"], healthy(status=response))

    def test_status_schema_invalid_exits_1(self):
        required = (
            ("client", "version"),
            ("server", "version"),
            ("server", "protocol"),
            ("server", "compatible"),
            ("server", "restart_needed"),
            ("update", "restart_needed"),
        )
        for section, field in required:
            for document in (
                status_without(section, field),
                status_mistyping(section, field),
            ):
                stderr = self.assert_row(
                    1, ["preflight"], healthy(status=payload(document))
                )
                self.assertIn("status-schema-invalid", stderr)

    def test_agent_get_failure_and_agent_not_found_exit_1(self):
        for response in (
            failure("agent target brichan-missing not found"),
            payload(AGENT_NOT_FOUND_JSON),
            text("not json"),
            payload({"result": {}}),
        ):
            self.assert_row(
                1, ["observe", "brichan-missing"], healthy(**{"agent get": response})
            )

    # -- exit 0: collected preflight reports ---------------------------------

    def test_verified_and_healthy_preflight_exits_0(self):
        report = self.assert_row(0, ["preflight"])
        self.assertEqual("verified", report["support"])
        self.assertEqual([], report["findings"])
        self.assertEqual("0.9.1", report["server_version"])
        self.assertEqual(22, report["protocol"])

    def test_0_7_3_is_no_longer_verified_but_still_reports(self):
        """Plan v3: 0.9.1 is the minimum supported Herdr.

        The old control plane is a reported state, never a refusal: the rest of
        the preflight is still collected at exit 0.
        """

        report = self.assert_row(
            0, ["preflight"], healthy(status=payload(STATUS_JSON))
        )
        self.assertEqual("unverified", report["support"])
        self.assertIn("unverified-version", report["findings"])
        self.assertEqual("0.7.3", report["server_version"])
        self.assertEqual(16, report["protocol"])
        self.assertEqual(3, len(report["integrations"]))

    def test_the_0_9_1_control_plane_preflights_cleanly(self):
        """AC2 and AC3 at the stubbed-CLI layer.

        The widened verified set and the widened row grammar have to hold
        together: a 0.9.1 server reports ``verified``, and every row shape the
        0.9.1 client prints parses without a ``malformed-row`` or
        ``unknown-row`` finding.
        """

        report = self.assert_row(
            0,
            ["preflight"],
            healthy(**{"integration status": text(INTEGRATION_TEXT_091)}),
        )
        self.assertEqual("verified", report["support"])
        self.assertEqual("0.9.1", report["server_version"])
        self.assertEqual(22, report["protocol"])
        for finding in report["findings"]:
            self.assertFalse(finding.startswith("malformed-row"), finding)
            self.assertFalse(finding.startswith("unknown-row"), finding)
        self.assertNotIn("unverified-version", report["findings"])
        self.assertIn("integration-unhealthy(droid=outdated)", report["findings"])
        for row in report["integrations"]:
            self.assertEqual("valid", row["classification"], row)
        self.assertNotIn("/Users/", json.dumps(report))
        self.assertNotIn("experimental", json.dumps(report))
        self.assertIn(
            "letta", [row["runtime"] for row in report["integrations"]]
        )

    def test_a_genuinely_malformed_row_is_still_rejected_on_0_9_1(self):
        """AC3's negative half: the widened grammar is not an escape hatch."""

        rows = (
            "letta (unstable): not installed (/Users/example/.letta/hook.sh)\n"
            "droid: outdated (v2 < v3) /Users/example/.factory/hook.sh\n"
        )
        report = self.assert_row(
            0, ["preflight"], healthy(**{"integration status": text(rows)})
        )
        self.assertIn("malformed-row(1)", report["findings"])
        self.assertIn("malformed-row(2)", report["findings"])
        self.assertNotIn("/Users/", json.dumps(report))

    def test_unverified_version_exits_0(self):
        for document in (
            status_with(server__version="0.9.9"),
            status_with(server__protocol=17),
        ):
            report = self.assert_row(0, ["preflight"], healthy(status=payload(document)))
            self.assertEqual("unverified", report["support"])
            self.assertIn("unverified-version", report["findings"])

    def test_compatibility_and_restart_findings_render_at_exit_0(self):
        cases = {
            "incompatible-control-plane": status_with(server__compatible=False),
            "restart-needed(server)": status_with(server__restart_needed=True),
            "restart-needed(update)": status_with(update__restart_needed=True),
        }
        for finding, document in cases.items():
            report = self.assert_row(0, ["preflight"], healthy(status=payload(document)))
            self.assertIn(finding, report["findings"], finding)

    def test_integration_probe_rows_and_failures_exit_0(self):
        cases = {
            "integration-unhealthy": failure("usage:", code=2),
            "unknown-row(1)": text("quokka: current (v1) (/Users/example/hook.sh)\n"),
            "malformed-row(1)": text("a row with no separator\n"),
            "integration-unhealthy(codex=outdated)": text(
                "codex: outdated (v5) (/Users/example/.codex/herdr-agent-state.sh)\n"
            ),
            "integration-unhealthy(claude=not installed)": text(
                "claude: not installed (/Users/example/.claude/hooks/hook.sh)\n"
            ),
        }
        for finding, response in cases.items():
            report = self.assert_row(
                0, ["preflight"], healthy(**{"integration status": response})
            )
            self.assertIn(finding, report["findings"], finding)

    def test_missing_required_integration_rows_are_unhealthy(self):
        cases = (
            (
                "empty",
                "",
                {
                    "integration-unhealthy(claude=missing)",
                    "integration-unhealthy(codex=missing)",
                },
            ),
            (
                "claude-only",
                "claude: current (v7) (/Users/example/.claude/hook.sh)\n",
                {"integration-unhealthy(codex=missing)"},
            ),
            (
                "codex-only",
                "codex: current (v5) (/Users/example/.codex/hook.sh)\n",
                {"integration-unhealthy(claude=missing)"},
            ),
        )
        for label, rows, expected in cases:
            with self.subTest(label=label):
                report = self.assert_row(
                    0,
                    ["preflight"],
                    healthy(**{"integration status": text(rows)}),
                )
                self.assertEqual(expected, set(report["findings"]))

    def test_capability_finding_exits_0_and_is_never_repaired(self):
        report = self.assert_row(
            0,
            ["preflight", "--agent", "brichan-worker"],
            healthy(**{"agent explain": payload(EXPLAIN_TRUST_DIRECTORY_JSON)}),
        )
        self.assertIn("capability-drift", report["findings"])
        self.assertEqual(
            "rule trust_directory uses invalid region: top_non_empty_lines(20)",
            report["capabilities"][0]["detail"],
        )
        for argv in self.stub_calls():
            self.assertNotIn("install", argv)

    def test_the_combined_finding_case_exits_0_with_a_union(self):
        document = status_with(
            server__version="0.9.0",
            server__compatible=False,
            server__restart_needed=True,
        )
        document["update"]["restart_needed"] = True
        report = self.assert_row(
            0,
            ["preflight", "--agent", "brichan-worker"],
            healthy(
                status=payload(document),
                **{
                    "integration status": text(
                        "codex: outdated (v5) (/Users/example/.codex/hook.sh)\n"
                        "quokka: current (v1) (/Users/example/.quokka/hook.sh)\n"
                        "garbage row\n"
                    ),
                    "agent explain": payload(EXPLAIN_TRUST_DIRECTORY_JSON),
                },
            ),
        )
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

    def test_no_home_or_configuration_path_reaches_stdout(self):
        result = self.run_observe("preflight", "--agent", "brichan-worker")
        self.assertEqual(0, result.returncode, result.stderr)
        for leaked in ("/Users/example", "/home/", "herdr-agent-state", ".claude/hooks"):
            self.assertNotIn(leaked, result.stdout, leaked)

    # -- code review v2, finding M1: anchored grammar and strict redaction ----

    #: Colon-bearing rows carrying path material in shapes the previous
    #: permissive parser copied into the rendered report.
    PATH_BEARING_MALFORMED_ROWS = (
        "claude: current",
        "claude: current (v7)",
        "claude: current /Users/example/.claude/hooks/herdr-agent-state.sh",
        "claude: current (v7) /Users/example/.claude/hooks/hook.sh",
        "claude: current (v7) (/Users/example/.claude/hook.sh) extra",
        "claude: current (/Users/example/.claude/hook.sh) /home/other/hook.sh",
        "claude: (/Users/example/.claude/hook.sh) current",
        "claude: current (/Users/example/.claude/hook.sh",
        "claude: current (~/.claude/hooks/hook.sh)",
        "/Users/example/.claude: current (/Users/example/.claude/hook.sh)",
        "claude: /Users/example/.claude/hook.sh (/Users/example/.claude/hook.sh)",
    )

    def test_path_bearing_malformed_rows_leak_nothing_into_stdout(self):
        rows = "\n".join(self.PATH_BEARING_MALFORMED_ROWS) + "\n"
        result = self.run_observe(
            "preflight", responses=healthy(**{"integration status": text(rows)})
        )
        self.assertEqual(0, result.returncode, result.stderr)
        for leaked in (
            "/Users/",
            "/home/",
            "~/",
            "hook.sh",
            "herdr-agent-state",
            ".claude",
        ):
            self.assertNotIn(leaked, result.stdout, leaked)
        report = json.loads(result.stdout)
        self.assertEqual(
            len(self.PATH_BEARING_MALFORMED_ROWS), len(report["integrations"])
        )
        for row in report["integrations"]:
            self.assertEqual("malformed-row", row["classification"])
            self.assertEqual("", row["runtime"])
            self.assertEqual("", row["status"])
        self.assertEqual(
            {
                *(f"malformed-row({index})" for index in range(1, len(report["integrations"]) + 1)),
                "integration-unhealthy(claude=missing)",
                "integration-unhealthy(codex=missing)",
            },
            set(report["findings"]),
        )

    def test_a_missing_trailing_path_group_is_malformed_not_valid(self):
        report = self.assert_row(
            0,
            ["preflight"],
            healthy(**{"integration status": text("claude: current\n")}),
        )
        self.assertEqual("malformed-row", report["integrations"][0]["classification"])
        self.assertIn("malformed-row(1)", report["findings"])

    def test_a_path_like_unknown_row_carries_only_bounded_tokens(self):
        report = self.assert_row(
            0,
            ["preflight"],
            healthy(
                **{
                    "integration status": text(
                        "quokka: not installed "
                        "(/Users/example/.quokka/plugins/state.js)\n"
                    )
                }
            ),
        )
        row = report["integrations"][0]
        self.assertEqual("unknown-row", row["classification"])
        self.assertEqual("quokka", row["runtime"])
        self.assertEqual("not installed", row["status"])
        self.assertNotIn("/Users/", json.dumps(report))

    # -- exit 0: collected observations --------------------------------------

    def test_healthy_observation_exits_0_with_possible_truncation_risk(self):
        report = self.assert_row(0, ["observe", "brichan-worker", "--lines", "200"])
        self.assertEqual("possible", report["truncation_risk"])
        self.assertEqual("working", report["scheduling_state"])
        self.assertEqual(3, report["lines_counted"])
        self.assertEqual(200, report["lines_requested"])
        self.assertIsNone(report["native_truncated"])
        self.assertIsNone(report["read_error"])
        self.assertNotIn("read-failed", report["findings"])
        for forbidden in ("done", "success", "complete", "completed"):
            self.assertNotIn(forbidden, report, forbidden)

    def test_the_0_9_1_control_plane_observes_cleanly(self):
        """AC4 at the stubbed-CLI layer, against the 0.9.1 status fixture."""

        report = self.assert_row(
            0,
            ["observe", "brichan-worker", "--lines", "50"],
            healthy(**{"integration status": text(INTEGRATION_TEXT_091)}),
        )
        self.assertEqual("possible", report["truncation_risk"])
        self.assertGreater(report["lines_counted"], 0)
        self.assertEqual([], report["findings"])
        self.assertIsNone(report["read_error"])

    def test_the_read_argv_asks_for_the_text_format(self):
        self.run_observe("observe", "brichan-worker")
        read = next(
            argv for argv in self.stub_calls() if argv[:2] == ["agent", "read"]
        )
        self.assertEqual("text", read[read.index("--format") + 1])

    def test_read_failure_and_contentless_reads_exit_0(self):
        for response in (
            failure("read failed"),
            failure("unknown option: --format", code=2),
            text(""),
            text("\n\n"),
            text("   "),
        ):
            report = self.assert_row(
                0, ["observe", "brichan-worker"], healthy(**{"agent read": response})
            )
            self.assertIn("read-failed", report["findings"])
            self.assertEqual("confirmed", report["truncation_risk"])
            self.assertIsNotNone(report["read_error"])
            self.assertEqual("", report["text"])
            self.assertIsNone(report["native_truncated"])

    # -- code review v2, finding H1, on the 0.9.1 plain-text read path -------

    #: Reads that exit ``0`` but carry no screen. A live pane always shows at
    #: least a shell prompt, so each of these is a failed read, not a zero-line
    #: observation.
    EMPTY_READ_STDOUTS = {
        "empty stdout": "",
        "single newline": "\n",
        "blank lines": "\n\n\n",
        "spaces only": "    ",
        "tabs and newlines": "\t\n \n",
    }

    def test_contentless_reads_exit_0_as_confirmed_read_failures(self):
        for label, stdout in self.EMPTY_READ_STDOUTS.items():
            report = self.assert_row(
                0,
                ["observe", "brichan-worker"],
                healthy(**{"agent read": text(stdout)}),
            )
            self.assertIn("read-failed", report["findings"], label)
            self.assertEqual("confirmed", report["truncation_risk"], label)
            self.assertIsNotNone(report["read_error"], label)
            self.assertEqual("", report["text"], label)
            self.assertIsNone(report["native_truncated"], label)
            self.assertIsNone(report["source_reported"], label)

    def test_no_contentless_read_reaches_none_even_with_a_stubbed_capability(self):
        seams = {"MONITOR_TEST_COMPLETENESS_SOURCE": "recent-unwrapped"}
        for label, stdout in self.EMPTY_READ_STDOUTS.items():
            report = self.assert_row(
                0,
                ["observe", "brichan-worker", "--lines", "200"],
                healthy(**{"agent read": text(stdout)}),
                seams=seams,
            )
            self.assertNotEqual("none", report["truncation_risk"], label)
            self.assertEqual("confirmed", report["truncation_risk"], label)

    def test_not_even_a_healthy_read_reaches_none_with_a_stubbed_capability(self):
        """AC4: on 0.9.1 ``none`` is unreachable through the CLI at all.

        The seam is not inert — ``tests/unit/test_herdr_monitor.py`` pins that
        ``classify_truncation`` still returns ``none`` when it is handed an
        explicit ``native_truncated=False``. The 0.9.1 adapter simply never has
        such a flag to hand it, so a short healthy read stays ``possible``.
        """

        report = self.assert_row(
            0,
            ["observe", "brichan-worker", "--lines", "200"],
            seams={"MONITOR_TEST_COMPLETENESS_SOURCE": "recent-unwrapped"},
        )
        self.assertEqual("possible", report["truncation_risk"])
        self.assertIsNone(report["read_error"])

    # -- code review v3, finding M1-v3: malformed outer envelopes ------------

    #: Syntactically valid JSON whose ``result`` container is not an object.
    #: Before the fix these reached a chained ``.get`` and the real wrapper
    #: printed an ``AttributeError`` traceback instead of an owned failure.
    MALFORMED_RESULT_ENVELOPES = {
        "result null": {"id": "cli:agent:x", "result": None},
        "result list": {"id": "cli:agent:x", "result": []},
        "result populated list": {"id": "cli:agent:x", "result": [{"read": {}}]},
        "result string": {"id": "cli:agent:x", "result": "ok"},
        "result integer": {"id": "cli:agent:x", "result": 3},
        "result boolean": {"id": "cli:agent:x", "result": True},
        "result absent": {"id": "cli:agent:x"},
    }

    def test_a_malformed_result_envelope_get_exits_1_without_a_traceback(self):
        for label, document in self.MALFORMED_RESULT_ENVELOPES.items():
            result = self.run_observe(
                "observe",
                "brichan-worker",
                responses=healthy(**{"agent get": payload(document)}),
            )
            self.assertEqual(1, result.returncode, f"{label}: {result.stderr}")
            self.assertEqual("", result.stdout, label)
            self.assertTrue(result.stderr.strip(), label)
            self.assertNotIn("Traceback", result.stderr, label)
            self.assertNotIn("AttributeError", result.stderr, label)
            self.assertTrue(
                result.stderr.startswith("brichan-herdr-agent-observe:"),
                f"{label}: {result.stderr}",
            )

    def test_the_wrapper_reports_no_source_because_0_9_1_reports_none(self):
        """Echoing the requested source back would manufacture a confirmation."""

        report = self.assert_row(0, ["observe", "brichan-worker"])
        self.assertIsNone(report["source_reported"])
        self.assertEqual("recent-unwrapped", report["source"])
        self.assertIsNone(report["read_error"])

    def test_missing_evidence_exits_0(self):
        report = self.assert_row(
            0,
            [
                "observe",
                "brichan-worker",
                "--project-root",
                str(self.project),
                "--evidence",
                "docs/evidence.md",
                "--evidence",
                "docs/absent.md",
            ],
        )
        self.assertIn("evidence-missing(docs/absent.md)", report["findings"])
        self.assertTrue(report["evidence"][0]["exists"])
        self.assertTrue(report["evidence"][0]["is_regular_file"])
        self.assertEqual(3, report["evidence"][0]["size_bytes"])
        self.assertFalse(report["evidence"][1]["exists"])

    def test_read_failure_with_missing_evidence_is_one_report_at_exit_0(self):
        report = self.assert_row(
            0,
            [
                "observe",
                "brichan-worker",
                "--project-root",
                str(self.project),
                "--evidence",
                "docs/absent.md",
            ],
            healthy(**{"agent read": failure("read failed")}),
        )
        self.assertIn("read-failed", report["findings"])
        self.assertIn("evidence-missing(docs/absent.md)", report["findings"])

    def test_blocked_and_other_scheduling_states_pass_through_at_exit_0(self):
        for state in ("idle", "working", "blocked", "done", "unknown", "future-state"):
            document = json.loads(json.dumps(AGENT_GET_JSON))
            document["result"]["agent"]["agent_status"] = state
            report = self.assert_row(
                0,
                ["observe", "brichan-worker"],
                healthy(**{"agent get": payload(document)}),
            )
            self.assertEqual(state, report["scheduling_state"])

    # -- cross-cutting -------------------------------------------------------

    def test_the_stub_log_shows_read_only_commands_only(self):
        self.run_observe("preflight", "--agent", "brichan-worker")
        self.run_observe(
            "observe",
            "brichan-worker",
            "--project-root",
            str(self.project),
            "--evidence",
            "docs/evidence.md",
        )
        calls = self.stub_calls()
        self.assertTrue(calls)
        allowed = {
            ("status",),
            ("integration", "status"),
            ("agent", "list"),
            ("agent", "get"),
            ("agent", "read"),
            ("agent", "explain"),
            ("agent", "wait"),
        }
        forbidden = {"send", "send-keys", "run", "close", "start", "resize", "focus"}
        for argv in calls:
            words = [part for part in argv if not part.startswith("-")]
            self.assertTrue(
                tuple(words[:2]) in allowed or tuple(words[:1]) in allowed, argv
            )
            self.assertFalse(forbidden.intersection(argv), argv)

    def test_every_executed_argv_satisfies_its_full_command_grammar(self):
        """Not just an allowed prefix: every token must be accounted for."""

        sys.path.insert(0, str(ROOT / "src"))
        from brichan.orchestration import monitor

        self.run_observe("preflight", "--agent", "brichan-worker")
        self.run_observe(
            "observe",
            "brichan-worker",
            "--project-root",
            str(self.project),
            "--evidence",
            "docs/evidence.md",
        )
        calls = self.stub_calls()
        self.assertTrue(calls)
        for argv in calls:
            monitor.validate_argv(["herdr", *argv])

    def test_every_wait_argv_the_tool_could_emit_is_bounded(self):
        sys.path.insert(0, str(ROOT / "src"))
        from brichan.orchestration.monitor import (
            MAX_WAIT_TIMEOUT_MS,
            MonitorError,
            assert_read_only,
            wait_argv,
        )

        argv = wait_argv("brichan-worker", "idle")
        self.assertEqual(30000, MAX_WAIT_TIMEOUT_MS)
        self.assertLessEqual(int(argv[argv.index("--timeout") + 1]), MAX_WAIT_TIMEOUT_MS)
        # A duplicated or over-cap timeout cannot be smuggled past the cap.
        self.assertIn("--until", argv)
        self.assertNotIn("--status", argv)
        for hostile in (
            ["herdr", "agent", "wait", "w", "--until", "idle", "--timeout", "60000"],
            ["herdr", "agent", "wait", "w", "--until", "idle",
             "--timeout", "100", "--timeout", "60000"],
            ["herdr", "agent", "wait", "w", "--until", "idle", "--timeout"],
            # The option Herdr 0.9.1 removed is refused before it can be run.
            ["herdr", "agent", "wait", "w", "--status", "idle", "--timeout", "100"],
        ):
            with self.assertRaises(MonitorError, msg=hostile):
                assert_read_only(hostile)


if __name__ == "__main__":
    unittest.main()
