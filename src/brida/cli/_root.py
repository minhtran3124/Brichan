"""Repository-root resolution shared by source and installed CLI adapters."""

import os
from pathlib import Path


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
