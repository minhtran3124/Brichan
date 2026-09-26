"""Semantic Versioning 2.0.0 precedence (https://semver.org/#spec-item-11)."""

from __future__ import annotations

import functools
import re

_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def parse(version: str) -> tuple[tuple[int, int, int], tuple[str, ...]]:
    """Return ((major, minor, patch), prerelease identifiers).

    Build metadata is dropped: it never affects precedence.
    Raises ValueError for anything that is not a valid SemVer 2.0.0 string.
    """
    match = _SEMVER.match(version)
    if not match:
        raise ValueError(f"invalid semantic version: {version!r}")
    core = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    pre = tuple(match.group(4).split(".")) if match.group(4) else ()
    return core, pre


def compare(a: str, b: str) -> int:
    """Return -1, 0, or 1 as a has lower, equal, or higher precedence than b."""
    core_a, pre_a = parse(a)
    core_b, pre_b = parse(b)
    if core_a != core_b:
        return -1 if core_a < core_b else 1
    if pre_a == pre_b:
        return 0
    # A version without a prerelease has higher precedence.
    if not pre_a:
        return 1
    if not pre_b:
        return -1
    return -1 if pre_a < pre_b else 1


def sort_versions(versions: list[str]) -> list[str]:
    """Return versions sorted by ascending precedence (stable for equal ones)."""
    return sorted(versions, key=functools.cmp_to_key(compare))
