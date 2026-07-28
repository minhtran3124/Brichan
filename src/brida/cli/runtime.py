"""Provider-neutral Brida runtime dispatcher."""

from __future__ import annotations

import os
import sys

from ._root import repository_root


def select_runtime(argv: list[str], environment: dict[str, str]) -> tuple[str, list[str]]:
    runtime = environment.get("BRIDA_RUNTIME") or "codex"
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
        runtime, remaining = select_runtime(arguments, os.environ)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    executable = repository_root() / "bin" / f"brida-{runtime}"
    os.execv(str(executable), [str(executable), *remaining])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
