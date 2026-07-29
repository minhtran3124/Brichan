"""Claude Code runtime adapter."""

from __future__ import annotations

import os
import sys

from ._root import repository_root
from brida.orchestration.model_routing import (
    RoutingError,
    load_settings,
    resolve_coordinator,
)
from .provider_commands import claude_command


def command(argv: list[str], environment: dict[str, str]) -> list[str]:
    root = repository_root()
    settings = load_settings(repository=root, environment=environment)
    compatibility_model = environment.get("BRIDA_CLAUDE_COORDINATOR_MODEL") or None
    route = resolve_coordinator(
        settings,
        "claude",
        model=compatibility_model,
    )
    return claude_command(route, argv)


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    os.chdir(repository_root())
    try:
        resolved_command = command(arguments, os.environ)
    except RoutingError as exc:
        print(f"brida-claude: {exc}", file=sys.stderr)
        return 2
    os.execvp("claude", resolved_command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
