#!/usr/bin/env python3
"""PreToolUse hook: deny Claude Code's native delegation tools.

Brichan workers must be independent Herdr sessions (PRODUCT.md non-goals).
The launcher already passes --disallowed-tools; this hook also covers plain
`claude` sessions in this checkout and delegation tools added under new names.
"""

import json
import re
import sys

DELEGATION_TOOLS = frozenset({"Agent", "Task", "Workflow"})
DELEGATION_PATTERN = re.compile(r"sub[-_]?agent|delegat|orchestrat", re.IGNORECASE)

REASON = (
    "Brichan forbids Claude Code native delegation ({tool}). Start an "
    "independent worker through Herdr instead: see "
    ".agents/skills/herdr-orchestration/SKILL.md."
)


def is_delegation_tool(name: str) -> bool:
    if name.startswith("mcp__"):
        return False
    return name in DELEGATION_TOOLS or bool(DELEGATION_PATTERN.search(name))


def main() -> int:
    try:
        event = json.load(sys.stdin)
        tool = event["tool_name"]
    except (ValueError, KeyError, TypeError):
        print("block_native_delegation: unreadable hook input", file=sys.stderr)
        return 2
    if not isinstance(tool, str) or not is_delegation_tool(tool):
        return 0
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": REASON.format(tool=tool),
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
