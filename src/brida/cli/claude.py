"""Claude Code runtime adapter."""

from __future__ import annotations

import os
import sys

from ._root import repository_root


def command(argv: list[str], environment: dict[str, str]) -> list[str]:
    model = environment.get("BRIDA_CLAUDE_COORDINATOR_MODEL") or "opus"
    return [
        "claude",
        "--model",
        model,
        "--disallowed-tools",
        "Task",
        *argv,
    ]


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    os.chdir(repository_root())
    os.execvp("claude", command(arguments, os.environ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
