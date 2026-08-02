#!/usr/bin/env python3
"""Compatibility wrapper for Brichan's dry-run-first task-dossier scaffold."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brichan.contracts.task_dossier.scaffold import main


if __name__ == "__main__":
    raise SystemExit(main())
