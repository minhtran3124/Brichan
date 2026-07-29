"""Provider-neutral Brida runtime dispatcher."""

from __future__ import annotations

import os
import sys

from ._root import repository_root
from brida.orchestration.model_routing import (
    RoutingError,
    load_settings,
)


def select_runtime(
    argv: list[str],
    environment: dict[str, str],
    default_runtime: str,
) -> tuple[str, list[str]]:
    runtime = environment.get("BRIDA_RUNTIME") or default_runtime
    remaining = list(argv)
    if remaining[:1] == ["--runtime"]:
        if len(remaining) < 2:
            raise ValueError("usage: brida [--runtime codex|claude] [arguments...]")
        runtime = remaining[1]
        remaining = remaining[2:]
    elif remaining and remaining[0].startswith("--runtime="):
        runtime = remaining[0].split("=", 1)[1]
        remaining = remaining[1:]
    if runtime not in {"codex", "claude"}:
        raise ValueError(
            f"unsupported runtime: {runtime} (expected codex or claude)"
        )
    return runtime, remaining


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    try:
        settings = load_settings(repository=repository_root(), environment=os.environ)
        runtime, remaining = select_runtime(
            arguments,
            os.environ,
            settings.default_runtime,
        )
    except (RoutingError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2

    executable = repository_root() / "bin" / f"brida-{runtime}"
    os.execv(str(executable), [str(executable), *remaining])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
