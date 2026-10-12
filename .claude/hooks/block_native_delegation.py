#!/usr/bin/env python3
"""PreToolUse hook: keep agent work on the Herdr worker lifecycle.

Brichan workers must be independent Herdr sessions (PRODUCT.md non-goals).
The launcher already passes --disallowed-tools; this hook also covers plain
`claude` sessions in this checkout, delegation tools added under new names,
and agent sessions started from Bash, which it sends to the user to approve.
"""

import json
import os
import re
import shlex
import sys

DELEGATION_TOOLS = frozenset(
    {"Agent", "Task", "Workflow", "CronCreate", "RemoteTrigger"}
)
DELEGATION_PATTERN = re.compile(r"sub[-_]?agent|delegat|orchestrat", re.IGNORECASE)

AGENT_COMMANDS = frozenset({"claude", "codex"})
INFO_ARGUMENTS = frozenset({"--version", "-v", "--help", "-h"})
COMMAND_WRAPPERS = frozenset({"env", "exec", "command", "nohup", "nice", "time"})

DENY_REASON = (
    "Brichan forbids Claude Code native delegation ({tool}). Start an "
    "independent worker through Herdr instead: see "
    ".agents/skills/herdr-orchestration/SKILL.md."
)
ASK_REASON = (
    "This command starts a {agent} agent session outside Herdr. Brichan "
    "workers run through bin/brichan-herdr-agent-start; approve only a "
    "one-off probe, not delegated project work."
)


def is_delegation_tool(name: str) -> bool:
    if name.startswith("mcp__"):
        return False
    return name in DELEGATION_TOOLS or bool(DELEGATION_PATTERN.search(name))


ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")


def _commands(command: str):
    """Yield the words of each simple command in a shell string.

    Backticks become separators so `...` substitutions are inspected too; a
    literal backtick inside single quotes can then cause a spurious prompt,
    never a missed one.
    """
    lexer = shlex.shlex(command.replace("`", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    current: list[str] = []
    for token in lexer:
        if token == "$" or token.strip("();&|<>") == "":
            if current:
                yield current
            current = []
        else:
            current.append(token)
    if current:
        yield current


def _executable(words: list[str]):
    """Skip variable assignments and simple wrappers; return (name, arguments)."""
    index = 0
    while index < len(words):
        name = os.path.basename(words[index])
        if ASSIGNMENT.match(words[index]):
            index += 1
        elif name in COMMAND_WRAPPERS or name == "timeout":
            index += 1
            while index < len(words) and words[index].startswith("-"):
                index += 1
            if name == "timeout":
                index += 1
        else:
            return name, words[index + 1 :]
    return None, []


def agent_launch(command: str):
    """Return the agent CLI a Bash command starts, or None.

    Only --version or --help on its own is exempt; anything else, including a
    bare interactive start, counts as starting an agent session.
    """
    try:
        commands = list(_commands(command))
    except ValueError:
        return None
    for words in commands:
        name, arguments = _executable(words)
        if name in AGENT_COMMANDS and not (
            arguments and set(arguments) <= INFO_ARGUMENTS
        ):
            return name
    return None


def _decision(kind: str, reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": kind,
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    try:
        event = json.load(sys.stdin)
        tool = event["tool_name"]
    except (ValueError, KeyError, TypeError):
        print("block_native_delegation: unreadable hook input", file=sys.stderr)
        return 2
    if not isinstance(tool, str):
        return 0
    if is_delegation_tool(tool):
        json.dump(_decision("deny", DENY_REASON.format(tool=tool)), sys.stdout)
        return 0
    if tool == "Bash":
        command = (event.get("tool_input") or {}).get("command")
        agent = agent_launch(command) if isinstance(command, str) else None
        if agent is not None:
            json.dump(_decision("ask", ASK_REASON.format(agent=agent)), sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
