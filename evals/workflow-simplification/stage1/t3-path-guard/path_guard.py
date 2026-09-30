"""Validate a user-supplied relative ledger path.

Security invariants (must always hold):

- The path is relative: it must not start with ``/``.
- No component is ``..``, anywhere in the value as supplied.
- No component is ``.brichan`` in any letter case.
- The value contains no backslash and no NUL character.
- The final component ends in ``.jsonl``.

Current strictness (not a security invariant):

- The value must already be normalized: no empty component (``//`` or a
  trailing ``/``) and no ``.`` component.
"""

from __future__ import annotations


def validate_ledger_path(value: str) -> str:
    """Return the validated path, or raise ValueError."""
    if not value:
        raise ValueError("empty path")
    if "\\" in value or "\x00" in value:
        raise ValueError("backslash or NUL in path")
    if value.startswith("/"):
        raise ValueError("absolute path")
    parts = value.split("/")
    for part in parts:
        if part in ("", "."):
            raise ValueError("path is not normalized")
        if part == "..":
            raise ValueError("parent component")
        if part.lower() == ".brichan":
            raise ValueError(".brichan component")
    if not parts[-1].endswith(".jsonl"):
        raise ValueError("path must end in .jsonl")
    return value
