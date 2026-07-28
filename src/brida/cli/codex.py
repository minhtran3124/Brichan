"""Codex runtime adapter."""

from __future__ import annotations

import os
import sys

from ._root import repository_root


def command(argv: list[str]) -> list[str]:
    return [
        "codex",
        "-C",
        str(repository_root()),
        "-c",
        "agents.enabled=false",
        "--disable",
        "multi_agent",
        "--disable",
        "multi_agent_v2",
        *argv,
    ]


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    os.execvp("codex", command(arguments))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
