"""Claude Code runtime adapter."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ._root import checkout_root, exec_runtime, repository_root
from brichan import __version__
from brichan.orchestration.model_routing import (
    RoutingError,
    load_settings,
    resolve_coordinator,
)
from .provider_commands import claude_command


def command(
    argv: list[str], environment: dict[str, str], *, root: Path | None = None
) -> list[str]:
    root = repository_root() if root is None else root
    settings = load_settings(repository=root, environment=environment)
    compatibility_model = environment.get("BRICHAN_CLAUDE_COORDINATOR_MODEL") or None
    route = resolve_coordinator(
        settings,
        "claude",
        model=compatibility_model,
    )
    return claude_command(route, argv)


def main(argv: list[str] | None = None) -> int:
    """Installed console-script entrypoint; never enters checkout mode.

    Claude is a checkout-only coordinator runtime: the Codex-first
    installed-project workflow has nothing for this command to launch, so the
    installed console script answers help/version and otherwise refuses.
    """

    arguments = sys.argv[1:] if argv is None else argv
    if arguments[:1] in (["--help"], ["-h"]):
        print("usage: brichan-claude [claude arguments...]")
        print()
        print(
            "brichan-claude is checkout-oriented: run the checkout's own "
            "bin/brichan-claude wrapper. It is not part of the Codex-first "
            "installed-project workflow."
        )
        return 0
    if arguments[:1] in (["--version"], ["-V"]):
        print(f"brichan-claude {__version__}")
        return 0
    print(
        "brichan-claude: checkout-only command; run the checkout's own "
        "bin/brichan-claude wrapper",
        file=sys.stderr,
    )
    return 2


def checkout_main(root: Path | str, argv: list[str] | None = None) -> int:
    """Source-checkout entrypoint, reached only from `bin/brichan-claude`."""

    arguments = sys.argv[1:] if argv is None else argv
    try:
        resolved = checkout_root(root)
        os.chdir(resolved)
        resolved_command = command(arguments, os.environ, root=resolved)
    except (OSError, RuntimeError, RoutingError) as exc:
        print(f"brichan-claude: {exc}", file=sys.stderr)
        return 2
    return exec_runtime("claude", resolved_command, owner="brichan-claude")


if __name__ == "__main__":
    raise SystemExit(main())
