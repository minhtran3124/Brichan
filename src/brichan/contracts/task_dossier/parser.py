"""Dependency-free Markdown parsing for task-dossier artifacts."""

from __future__ import annotations

import re
from pathlib import Path

from .schema import (
    Diagnostic,
    METADATA_SECTION,
    PLACEHOLDER_VALUES,
    ParsedArtifact,
)


FIELD_SECTIONS = (
    METADATA_SECTION,
    "Task identity",
    "Request provenance",
    "Plan status",
    "Review target",
    "Remote action",
)


def plain(value: str | None) -> str:
    if value is None:
        return ""
    value = value.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return value[1:-1].strip()
    return value


def is_placeholder(value: str | None) -> bool:
    text = plain(value).lower()
    return text in PLACEHOLDER_VALUES or bool(re.fullmatch(r"<[^>]+>", text))


def parse_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^## ([^\n]+)\n", text, re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.setdefault(name, text[match.end() : end])
    return sections


def section_names(text: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"^## ([^\n]+)\n", text, re.MULTILINE)
    ]


def parse_fields(section_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    current: str | None = None
    for line in section_text.splitlines():
        match = re.match(r"^- ([^:\n]+):\s*(.*)$", line)
        if match:
            label, value = match.groups()
            label = label.strip()
            fields[label] = value.strip()
            current = label
            continue
        if current and (line.startswith("  ") or line.startswith("\t")):
            continuation = line.strip()
            if continuation and not continuation.startswith("|"):
                fields[current] = f"{fields[current]} {continuation}".strip()
        elif line.strip():
            current = None
    return fields


def parse_table(section_text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped[1:-1].split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def list_items(section_text: str) -> list[str]:
    return [
        line.strip()[2:].strip()
        for line in section_text.splitlines()
        if line.strip().startswith("- ")
    ]


def concrete_list_items(section_text: str) -> list[str]:
    return [item for item in list_items(section_text) if not is_placeholder(item)]


def has_concrete_statement(section_text: str) -> bool:
    """Report whether a section states something rather than merely existing.

    A template bullet is text, so a non-empty check accepts an unfilled
    placeholder. Bulleted sections must carry at least one concrete item; prose
    sections must not be a bare placeholder.
    """
    items = list_items(section_text)
    if items:
        return bool(concrete_list_items(section_text))
    stripped = section_text.strip()
    return bool(stripped) and not is_placeholder(stripped)


def parse_artifact(
    path: Path, name: str, diagnostics: list[Diagnostic]
) -> ParsedArtifact:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        diagnostics.append(Diagnostic(path, "file", f"cannot read artifact: {error}"))
        return ParsedArtifact(path, name, "", {}, {})

    if not text.strip():
        diagnostics.append(
            Diagnostic(path, "file", "artifact is empty; placeholders are not evidence")
        )

    sections = parse_sections(text)
    fields = {
        section: parse_fields(sections.get(section, "")) for section in FIELD_SECTIONS
    }
    return ParsedArtifact(path, name, text, sections, fields)


__all__ = [
    "concrete_list_items",
    "has_concrete_statement",
    "is_placeholder",
    "list_items",
    "parse_artifact",
    "parse_fields",
    "parse_sections",
    "parse_table",
    "plain",
    "section_names",
]
