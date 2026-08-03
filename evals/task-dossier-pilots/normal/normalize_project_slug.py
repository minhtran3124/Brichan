"""Pilot fixture for TDW-007: dependency-free project-slug normalization.

This module is an isolated evaluation fixture. It is not part of the shipped
`brichan` package, is not imported by any repository test layer, and has no
enforcement authority. It uses the standard library only and performs no I/O.
"""

import re

# Every maximal run of characters outside the ASCII slug alphabet collapses to a
# single hyphen. The output alphabet is therefore the complement of this class,
# which is what makes conformance to the project slug grammar structural rather
# than merely tested (see options.md, Option A).
_SEPARATOR_RUN = re.compile(r"[^a-z0-9]+")


def normalize_project_slug(value: str) -> str:
    """Return the normalized project slug for ``value``.

    The input is trimmed and lowercased, each run of non-ASCII-alphanumeric
    characters becomes one hyphen, and edge hyphens are stripped. Non-ASCII
    letters are separators, so ``"Café"`` normalizes to ``"caf"``.

    Raises:
        ValueError: if no ASCII alphanumeric content remains after
            normalization. An empty slug is never returned.
    """
    text = value.strip().lower()
    slug = _SEPARATOR_RUN.sub("-", text).strip("-")
    if not slug:
        raise ValueError(
            f"no alphanumeric content remains after normalizing {value!r}"
        )
    return slug
