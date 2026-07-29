"""Codex runtime adapter."""

from __future__ import annotations

import os
import sys

from ._root import repository_root
from brida.orchestration.model_routing import (
    RoutingError,
    load_settings,
    resolve_coordinator,
)
from .provider_commands import codex_command


def command(
    argv: list[str],
    environment: dict[str, str] | None = None,
) -> list[str]:
    env = os.environ if environment is None else environment
    root = repository_root()
    settings = load_settings(repository=root, environment=env)
    route = resolve_coordinator(settings, "codex")
    return codex_command(route, argv, cwd=root)


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    try:
        resolved_command = command(arguments, os.environ)
    except RoutingError as exc:
        print(f"brida-codex: {exc}", file=sys.stderr)
        return 2
    os.execvp("codex", resolved_command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
