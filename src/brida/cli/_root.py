"""Repository-root resolution shared by source and installed CLI adapters."""

import os
import sys
from pathlib import Path


def exec_runtime(program: str, command: list[str], *, owner: str) -> int:
    """Replace this process with `program`, or report why it cannot.

    os.exec* raises FileNotFoundError when the runtime is not installed. The
    provider binaries are external and genuinely absent on plain machines and
    in CI, so surface an owned, actionable message instead of a traceback.
    Returns only on failure; a successful exec never comes back.
    """
    try:
        os.execvp(program, command)
    except FileNotFoundError:
        print(
            f"{owner}: cannot launch {program!r}: not installed or not on PATH",
            file=sys.stderr,
        )
        return 2
    except OSError as exc:
        print(f"{owner}: cannot launch {program!r}: {exc}", file=sys.stderr)
        return 2
    return 0


def repository_root() -> Path:
    override = os.environ.get("BRIDA_ROOT")
    if override:
        return Path(override).resolve()

    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / "bin").is_dir():
            return candidate

    source_root = Path(__file__).resolve().parents[3]
    if (source_root / "AGENTS.md").is_file():
        return source_root
    raise RuntimeError(
        "cannot locate the Brida repository root; run inside the repository "
        "or set BRIDA_ROOT"
    )
