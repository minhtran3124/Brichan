#!/usr/bin/env python3
"""Decide whether a diff touches a contract path.

A Level 0 task needs an independent code review if and only if its diff
touches a contract path (docs/workflows/task-dossier.md). The input is the
changed repository-relative path names, one per line, exactly as
``git diff --name-only --no-renames <dispatch-base>`` prints them, so an add, a
modify, a delete, and both sides of a rename all appear.

This module reads names only. It never runs git, opens no repository file, and
fails closed on input it cannot decode.

Exit codes: ``0`` no contract path, ``3`` at least one contract path, ``2``
invalid invocation, undecodable input, or input with no path name. A failed
upstream ``git diff`` prints nothing, so empty input is refused rather than
read as "no contract path".
"""

from __future__ import annotations

import argparse
import sys
from typing import BinaryIO, Iterable, Sequence

from .schema import CONTRACT_PATH_FILES, CONTRACT_PATH_PREFIXES


def _unquote(name: str) -> str:
    """Drop git's C-style quotes; every contract entry is plain ASCII.

    git quotes a name holding unusual bytes. The escapes only ever encode those
    bytes, so the unquoted text still starts with any ASCII prefix it matches.
    """
    if len(name) >= 2 and name.startswith('"') and name.endswith('"'):
        return name[1:-1]
    return name


def is_contract_path(name: str) -> bool:
    path = _unquote(name)
    return path in CONTRACT_PATH_FILES or path.startswith(CONTRACT_PATH_PREFIXES)


def contract_path_matches(names: Iterable[str]) -> list[str]:
    """Return every changed name that is a contract path, in input order."""
    return [name for name in names if is_contract_path(name)]


def _build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description=(
            "Read changed path names from stdin (git diff --name-only "
            "--no-renames <base>) and report whether any is a contract path."
        )
    )


def main(argv: Sequence[str] | None = None, stdin: BinaryIO | None = None) -> int:
    _build_parser().parse_args(argv)
    stream = sys.stdin.buffer if stdin is None else stdin
    try:
        text = stream.read().decode("utf-8")
    except UnicodeDecodeError:
        print(
            "contract-path: input is not UTF-8 path names; refusing to decide",
            file=sys.stderr,
        )
        return 2

    names = [line.rstrip("\r") for line in text.split("\n")]
    names = [name for name in names if name.strip()]
    if not names:
        print(
            "contract-path: no path names on input; refusing to decide",
            file=sys.stderr,
        )
        return 2
    matches = contract_path_matches(names)
    if matches:
        print("contract-path: yes")
        for name in matches:
            print(name)
        return 3
    print("contract-path: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
