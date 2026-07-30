"""Claude Code runtime adapter."""

from __future__ import annotations

import os
import sys

from ._root import exec_runtime, repository_root
from brida import __version__
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
    try:
        os.chdir(repository_root())
        resolved_command = command(arguments, os.environ)
    except RoutingError as exc:
        print(f"brida-claude: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        if arguments[:1] in (["--help"], ["-h"]):
            print("usage: brida-claude [claude arguments...]")
            print()
            print(
                "brida-claude is checkout-oriented: run it from within the "
                "Brida source checkout, or with BRIDA_ROOT set. It is not "
                "part of the Codex-first installed-project workflow."
            )
            return 0
        if arguments[:1] in (["--version"], ["-V"]):
            print(f"brida-claude {__version__}")
            return 0
        print(f"brida-claude: {exc}", file=sys.stderr)
        return 2
    return exec_runtime("claude", resolved_command, owner="brida-claude")


if __name__ == "__main__":
    raise SystemExit(main())
