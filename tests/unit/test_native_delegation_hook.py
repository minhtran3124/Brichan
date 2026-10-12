"""The checkout's Claude Code hook denies native delegation tools."""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".claude/hooks/block_native_delegation.py"
SETTINGS = ROOT / ".claude/settings.json"


def run_hook(payload):
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def decision(result):
    if not result.stdout:
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


class NativeDelegationHookTest(unittest.TestCase):
    def test_known_delegation_tools_are_denied(self):
        for tool in ("Agent", "Task", "Workflow", "CronCreate", "RemoteTrigger"):
            with self.subTest(tool=tool):
                result = run_hook({"hook_event_name": "PreToolUse", "tool_name": tool})
                self.assertEqual(0, result.returncode)
                self.assertEqual("deny", decision(result))
                self.assertIn("Herdr", result.stdout)

    def test_renamed_delegation_tools_are_denied(self):
        for tool in ("SubAgent", "spawn_subagent", "DelegateTask", "Orchestrate"):
            with self.subTest(tool=tool):
                self.assertEqual("deny", decision(run_hook({"tool_name": tool})))

    def test_ordinary_tools_get_no_decision(self):
        for tool in (
            "Bash",
            "Edit",
            "TaskStop",
            "TaskCreate",
            "CronList",
            "CronDelete",
            "ListAgents",
            "SendMessage",
            "mcp__server__orchestrate_deploy",
        ):
            with self.subTest(tool=tool):
                result = run_hook({"tool_name": tool})
                self.assertEqual(0, result.returncode)
                self.assertEqual("", result.stdout)

    def test_bash_agent_sessions_ask_for_approval(self):
        for command, agent in (
            ('claude -p "summarize"', "claude"),
            ("cd /tmp && timeout 120 claude -p --model haiku -- hi", "claude"),
            ("claude", "claude"),
            ('codex exec "fix it"', "codex"),
            ("FOO=1 env BAR=2 /usr/bin/claude -p x", "claude"),
            ("echo $(claude -p x)", "claude"),
            ("echo `codex exec y`", "codex"),
            ("nohup claude -p x &", "claude"),
        ):
            with self.subTest(command=command):
                result = run_hook(
                    {"tool_name": "Bash", "tool_input": {"command": command}}
                )
                self.assertEqual(0, result.returncode)
                self.assertEqual("ask", decision(result))
                self.assertIn(agent, result.stdout)

    def test_bash_without_agent_session_gets_no_decision(self):
        for command in (
            "claude --version",
            "ls; codex --help",
            "bin/brichan --runtime claude",
            'herdr pane run wP:p4 "probe with claude -p first"',
            "grep -rn claude docs | wc -l",
            'git commit -m "fix(cli): block claude"',
            "echo 'unbalanced",
        ):
            with self.subTest(command=command):
                result = run_hook(
                    {"tool_name": "Bash", "tool_input": {"command": command}}
                )
                self.assertEqual(0, result.returncode)
                self.assertEqual("", result.stdout)

    def test_unreadable_input_blocks(self):
        for payload in ("not json", "{}", "[]"):
            with self.subTest(payload=payload):
                self.assertEqual(2, run_hook(payload).returncode)

    def test_non_string_tool_name_gets_no_decision(self):
        result = run_hook({"tool_name": 7})
        self.assertEqual(0, result.returncode)
        self.assertEqual("", result.stdout)

    def test_settings_wire_the_hook_and_deny_rules(self):
        settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        self.assertEqual(
            {"Agent", "Task", "Workflow", "CronCreate", "RemoteTrigger"},
            set(settings["permissions"]["deny"]),
        )
        entries = settings["hooks"]["PreToolUse"]
        commands = [hook["command"] for entry in entries for hook in entry["hooks"]]
        self.assertIn(
            "${CLAUDE_PROJECT_DIR}/.claude/hooks/block_native_delegation.py", commands
        )
        self.assertTrue(os.access(HOOK, os.X_OK))


if __name__ == "__main__":
    unittest.main()
