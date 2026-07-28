#!/usr/bin/env python3
"""Validate canonical project handoff receipts without mutating them."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Sequence


REQUIRED_SECTIONS = (
    "Identity",
    "Plan version",
    "Sessions",
    "Scope",
    "Non-goals",
    "Acceptance criteria",
    "Verification",
    "Implementation evidence",
    "Review verdict",
    "Risks and open decisions",
    "Cleanup status",
)

REQUIRED_FIELDS = {
    "Identity": (
        "Receipt schema version",
        "Receipt role",
        "Parent receipt path",
        "Task ID",
        "Project",
        "Handoff timestamp (UTC)",
        "Attempt",
        "Replaces session",
    ),
    "Plan version": (
        "Artifact or plan ID",
        "Version",
        "Status",
    ),
    "Scope": (
        "In scope",
        "Authorized paths",
        "Exclusive write ownership",
        "Branch",
        "Worktree",
    ),
    "Non-goals": ("Excluded work",),
    "Implementation evidence": (
        "Changed artifacts",
        "Diff evidence",
        "Test evidence",
    ),
    "Review verdict": (
        "Verdict",
        "Findings",
    ),
    "Risks and open decisions": (
        "Risks",
        "Open decisions",
    ),
    "Cleanup status": (
        "Brida-owned panes closed",
        "Project memory updated",
    ),
}

SCHEMA_V2_IDENTITY_FIELDS = (
    "Attempt origin",
    "Attempt lifecycle state",
    "Prior attempt state",
    "Replacement evidence path",
)

LIFECYCLE_STATES = {"accepted", "implemented", "reviewed"}
RECEIPT_ROLES = {"standalone", "parent", "child"}
ATTEMPT_ORIGINS = {"initial", "replacement"}
ATTEMPT_LIFECYCLE_STATES = {"active", "complete", "stale", "abandoned"}
PRIOR_ATTEMPT_STATES = {"stale", "abandoned", "null"}
CRITERION_STATES = {"pass", "fail", "pending", "null"}
VERIFICATION_STATES = {"pass", "fail", "pending", "unavailable", "null"}
PLACEHOLDER_VALUES = {
    "",
    "n/a",
    "none",
    "null",
    "pending",
    "tbd",
    "todo",
    "unavailable",
    "unknown",
}

PERSONAL_PATH_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9_])/Users/[^\s`|]+"),
    re.compile(r"(?<![A-Za-z0-9_])/home/[^\s`|]+"),
    re.compile(r"(?<![A-Za-z0-9_])~[/\\][^\s`|]*"),
    re.compile(r"(?i)\b[A-Z]:\\Users\\[^\s`|]+"),
)


@dataclass(frozen=True)
class Diagnostic:
    path: Path
    field: str
    message: str

    def format(self) -> str:
        return f"{self.path}: {self.field}: {self.message}"


@dataclass
class ParsedReceipt:
    path: Path
    text: str
    sections: dict[str, str]
    fields: dict[str, dict[str, str]]

    def get(self, section: str, field: str) -> str | None:
        return self.fields.get(section, {}).get(field)


def _plain(value: str | None) -> str:
    if value is None:
        return ""
    value = value.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return value[1:-1].strip()
    return value


def _is_placeholder(value: str | None) -> bool:
    plain = _plain(value).lower()
    return plain in PLACEHOLDER_VALUES or bool(re.fullmatch(r"<[^>]+>", plain))


def _status_token(value: str | None) -> str:
    plain = _plain(value).lower()
    return re.split(r"[\s;:,]", plain, maxsplit=1)[0]


def _parse_sections(
    path: Path, text: str, diagnostics: list[Diagnostic]
) -> dict[str, str]:
    matches = list(re.finditer(r"^## ([^\n]+)\n", text, re.MULTILINE))
    sections: dict[str, str] = {}
    seen: dict[str, int] = {}
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        seen[name] = seen.get(name, 0) + 1
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[name] = text[match.end() : end]

    for section in REQUIRED_SECTIONS:
        count = seen.get(section, 0)
        if count != 1:
            diagnostics.append(
                Diagnostic(
                    path,
                    f"section.{section}",
                    f"expected exactly one section, found {count}",
                )
            )

    required_positions = [
        next(
            (
                index
                for index, match in enumerate(matches)
                if match.group(1).strip() == section
            ),
            -1,
        )
        for section in REQUIRED_SECTIONS
    ]
    present_positions = [position for position in required_positions if position >= 0]
    if present_positions != sorted(present_positions):
        diagnostics.append(
            Diagnostic(
                path,
                "sections",
                "required sections are not in canonical order",
            )
        )
    return sections


def _parse_fields(section_text: str) -> tuple[dict[str, str], set[str]]:
    fields: dict[str, str] = {}
    duplicates: set[str] = set()
    current: str | None = None

    for line in section_text.splitlines():
        match = re.match(r"^- ([^:\n]+):\s*(.*)$", line)
        if match:
            label, value = match.groups()
            label = label.strip()
            if label in fields:
                duplicates.add(label)
            fields[label] = value.strip()
            current = label
            continue
        if current and (line.startswith("  ") or line.startswith("\t")):
            continuation = line.strip()
            if continuation and not continuation.startswith("|"):
                fields[current] = f"{fields[current]} {continuation}".strip()
        elif line.strip():
            current = None

    return fields, duplicates


def _parse_table(section_text: str) -> list[list[str]]:
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


def parse_receipt(path: Path, diagnostics: list[Diagnostic]) -> ParsedReceipt:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        diagnostics.append(Diagnostic(path, "file", f"cannot read receipt: {error}"))
        return ParsedReceipt(path, "", {}, {})

    sections = _parse_sections(path, text, diagnostics)
    fields: dict[str, dict[str, str]] = {}
    duplicates_by_section: dict[str, set[str]] = {}
    for section in REQUIRED_FIELDS:
        parsed, duplicates = _parse_fields(sections.get(section, ""))
        fields[section] = parsed
        duplicates_by_section[section] = duplicates

    receipt = ParsedReceipt(path, text, sections, fields)
    schema = _plain(receipt.get("Identity", "Receipt schema version"))

    for section, required in REQUIRED_FIELDS.items():
        duplicates = duplicates_by_section[section]
        for label in duplicates:
            diagnostics.append(
                Diagnostic(
                    path,
                    f"{section}.{label}",
                    "field appears more than once",
                )
            )
        for label in required:
            if label not in fields[section]:
                diagnostics.append(
                    Diagnostic(
                        path,
                        f"{section}.{label}",
                        "required field is missing",
                    )
                )

    if schema == "1":
        for label in SCHEMA_V2_IDENTITY_FIELDS:
            if label in fields["Identity"]:
                diagnostics.append(
                    Diagnostic(
                        path,
                        f"Identity.{label}",
                        "schema version 1 forbids schema-v2 identity fields",
                    )
                )
    elif schema == "2":
        for label in SCHEMA_V2_IDENTITY_FIELDS:
            if label not in fields["Identity"]:
                diagnostics.append(
                    Diagnostic(
                        path,
                        f"Identity.{label}",
                        "schema version 2 requires this field",
                    )
                )
    else:
        diagnostics.append(
            Diagnostic(
                path,
                "Identity.Receipt schema version",
                f"supported schema versions are 1 and 2, found {schema!r}",
            )
        )

    return receipt


def _diagnose(
    diagnostics: list[Diagnostic],
    receipt: ParsedReceipt,
    field: str,
    message: str,
) -> None:
    diagnostics.append(Diagnostic(receipt.path, field, message))


def _validate_personal_paths(
    receipt: ParsedReceipt, diagnostics: list[Diagnostic]
) -> None:
    for pattern in PERSONAL_PATH_PATTERNS:
        match = pattern.search(receipt.text)
        if match:
            _diagnose(
                diagnostics,
                receipt,
                "path hygiene",
                f"personal or home path is forbidden: {match.group(0)!r}",
            )


def _validate_path_identity(
    receipt: ParsedReceipt,
    projects_root: Path,
    diagnostics: list[Diagnostic],
) -> None:
    try:
        relative = receipt.path.relative_to(projects_root)
    except ValueError:
        _diagnose(
            diagnostics,
            receipt,
            "path identity",
            f"receipt is outside supplied projects root {projects_root}",
        )
        return

    if (
        len(relative.parts) != 4
        or relative.parts[1] != "handoffs"
        or relative.parts[3] != "receipt.md"
    ):
        _diagnose(
            diagnostics,
            receipt,
            "path identity",
            "expected <project>/handoffs/<task-id>/receipt.md",
        )
        return

    expected_project = relative.parts[0]
    expected_task = relative.parts[2]
    project = _plain(receipt.get("Identity", "Project"))
    task_id = _plain(receipt.get("Identity", "Task ID"))
    if project and project != expected_project:
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Project",
            f"expected {expected_project!r} from canonical path, found {project!r}",
        )
    if task_id and task_id != expected_task:
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Task ID",
            f"expected {expected_task!r} from canonical path, found {task_id!r}",
        )


def _validate_timestamp(
    receipt: ParsedReceipt, diagnostics: list[Diagnostic]
) -> None:
    value = _plain(receipt.get("Identity", "Handoff timestamp (UTC)"))
    if _is_placeholder(value):
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Handoff timestamp (UTC)",
            "must be a concrete UTC timestamp",
        )
        return
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if parsed is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds():
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Handoff timestamp (UTC)",
            "must be an ISO-8601 timestamp with UTC offset",
        )


def _canonical_parent_path(projects_root: Path, value: str) -> Path | None:
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or "\\" in value:
        return None
    root_name = projects_root.name
    if not pure.parts or pure.parts[0] != root_name:
        return None
    return projects_root.parent.joinpath(*pure.parts)


def _validate_role_topology(
    receipt: ParsedReceipt,
    projects_root: Path,
    diagnostics: list[Diagnostic],
) -> None:
    role = _plain(receipt.get("Identity", "Receipt role")).lower()
    parent_value = _plain(receipt.get("Identity", "Parent receipt path"))
    if role not in RECEIPT_ROLES:
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Receipt role",
            f"must be one of {sorted(RECEIPT_ROLES)}, found {role!r}",
        )
        return

    if role in {"standalone", "parent"}:
        if parent_value.lower() != "null":
            _diagnose(
                diagnostics,
                receipt,
                "Identity.Parent receipt path",
                f"{role} receipts require null",
            )
        return

    if _is_placeholder(parent_value):
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Parent receipt path",
            "child receipts require a repo-relative canonical parent path",
        )
        return

    parent_path = _canonical_parent_path(projects_root, parent_value)
    if parent_path is None:
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Parent receipt path",
            "must be repo-relative and begin with the supplied projects directory",
        )
        return
    try:
        relative = parent_path.relative_to(projects_root)
    except ValueError:
        relative = PurePosixPath()
    if (
        len(relative.parts) != 4
        or relative.parts[1] != "handoffs"
        or relative.parts[3] != "receipt.md"
    ):
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Parent receipt path",
            "must point to a canonical parent receipt",
        )
        return
    if parent_path == receipt.path:
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Parent receipt path",
            "child receipt cannot name itself as parent",
        )
        return
    if not parent_path.is_file():
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Parent receipt path",
            f"parent receipt does not exist: {parent_value}",
        )
        return

    parent_diagnostics: list[Diagnostic] = []
    parent = parse_receipt(parent_path, parent_diagnostics)
    parent_role = _plain(parent.get("Identity", "Receipt role")).lower()
    parent_project = _plain(parent.get("Identity", "Project"))
    child_project = _plain(receipt.get("Identity", "Project"))
    if parent_role != "parent":
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Parent receipt path",
            f"target receipt role must be parent, found {parent_role!r}",
        )
    if parent_project and child_project and parent_project != child_project:
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Parent receipt path",
            "parent and child receipts must name the same project",
        )


def _validate_attempt(
    receipt: ParsedReceipt,
    projects_root: Path,
    diagnostics: list[Diagnostic],
) -> None:
    schema = _plain(receipt.get("Identity", "Receipt schema version"))
    attempt_value = _plain(receipt.get("Identity", "Attempt"))
    replacement = _plain(receipt.get("Identity", "Replaces session"))
    try:
        attempt = int(attempt_value)
    except ValueError:
        attempt = 0
    if attempt < 1:
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Attempt",
            "must be a positive integer",
        )
        return
    if attempt == 1 and replacement.lower() != "null":
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Replaces session",
            "attempt 1 must not replace a prior session",
        )
    if attempt > 1 and _is_placeholder(replacement):
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Replaces session",
            "later attempts require concrete replacement provenance",
        )

    if schema != "2":
        return

    origin = _plain(receipt.get("Identity", "Attempt origin")).lower()
    attempt_lifecycle = _plain(
        receipt.get("Identity", "Attempt lifecycle state")
    ).lower()
    prior_state = _plain(receipt.get("Identity", "Prior attempt state")).lower()
    evidence_path = _plain(
        receipt.get("Identity", "Replacement evidence path")
    )

    if origin not in ATTEMPT_ORIGINS:
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Attempt origin",
            f"must be one of {sorted(ATTEMPT_ORIGINS)}, found {origin!r}",
        )
    if attempt_lifecycle not in ATTEMPT_LIFECYCLE_STATES:
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Attempt lifecycle state",
            "must be one of "
            f"{sorted(ATTEMPT_LIFECYCLE_STATES)}, found {attempt_lifecycle!r}",
        )
    if prior_state not in PRIOR_ATTEMPT_STATES:
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Prior attempt state",
            f"must be one of {sorted(PRIOR_ATTEMPT_STATES)}, found {prior_state!r}",
        )

    if attempt == 1:
        for field, value, expected in (
            ("Attempt origin", origin, "initial"),
            ("Prior attempt state", prior_state, "null"),
            ("Replacement evidence path", evidence_path.lower(), "null"),
        ):
            if value != expected:
                _diagnose(
                    diagnostics,
                    receipt,
                    f"Identity.{field}",
                    f"attempt 1 requires {expected!r}",
                )
    elif attempt > 1:
        if origin != "replacement":
            _diagnose(
                diagnostics,
                receipt,
                "Identity.Attempt origin",
                "attempts greater than 1 require 'replacement'",
            )
        if prior_state not in {"stale", "abandoned"}:
            _diagnose(
                diagnostics,
                receipt,
                "Identity.Prior attempt state",
                "attempts greater than 1 require 'stale' or 'abandoned'",
            )
        if _is_placeholder(evidence_path):
            _diagnose(
                diagnostics,
                receipt,
                "Identity.Replacement evidence path",
                "attempts greater than 1 require a concrete evidence path",
            )
        else:
            _validate_evidence_path(
                receipt,
                projects_root,
                evidence_path,
                diagnostics,
            )

    if not _is_placeholder(replacement):
        rows = _parse_table(receipt.sections.get("Sessions", ""))
        current_sessions = {
            _plain(row[4])
            for row in rows[1:]
            if len(row) == 5 and not _is_placeholder(row[4])
        }
        if replacement in current_sessions:
            _diagnose(
                diagnostics,
                receipt,
                "Identity.Replaces session",
                "cannot equal a session listed in the current receipt",
            )


def _validate_evidence_path(
    receipt: ParsedReceipt,
    projects_root: Path,
    value: str,
    diagnostics: list[Diagnostic],
) -> None:
    field = "Identity.Replacement evidence path"
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or ".." in pure.parts
        or "\\" in value
        or (pure.parts and pure.parts[0].startswith("~"))
    ):
        _diagnose(
            diagnostics,
            receipt,
            field,
            "must be a safe repo-relative path without absolute, parent, "
            "backslash, or home-path syntax",
        )
        return

    repo_root = projects_root.parent.resolve()
    candidate = repo_root.joinpath(*pure.parts)
    try:
        resolved = candidate.resolve()
        resolved.relative_to(repo_root)
    except (OSError, ValueError):
        _diagnose(
            diagnostics,
            receipt,
            field,
            "must resolve inside the repository",
        )
        return
    if not resolved.is_file():
        _diagnose(
            diagnostics,
            receipt,
            field,
            f"evidence file does not exist: {value}",
        )


def _validate_plan_and_scope(
    receipt: ParsedReceipt, diagnostics: list[Diagnostic]
) -> str:
    plan_id = receipt.get("Plan version", "Artifact or plan ID")
    if _is_placeholder(plan_id):
        _diagnose(
            diagnostics,
            receipt,
            "Plan version.Artifact or plan ID",
            "accepted plan ID must be concrete",
        )

    version = _plain(receipt.get("Plan version", "Version"))
    try:
        valid_version = int(version) >= 1
    except ValueError:
        valid_version = False
    if not valid_version:
        _diagnose(
            diagnostics,
            receipt,
            "Plan version.Version",
            "accepted plan version must be a positive integer",
        )

    lifecycle = _plain(receipt.get("Plan version", "Status")).lower()
    if lifecycle not in LIFECYCLE_STATES:
        _diagnose(
            diagnostics,
            receipt,
            "Plan version.Status",
            f"must be one of {sorted(LIFECYCLE_STATES)}, found {lifecycle!r}",
        )

    for section, field in (
        ("Identity", "Task ID"),
        ("Identity", "Project"),
        ("Scope", "In scope"),
        ("Scope", "Authorized paths"),
        ("Scope", "Exclusive write ownership"),
        ("Scope", "Branch"),
        ("Scope", "Worktree"),
        ("Non-goals", "Excluded work"),
    ):
        if _is_placeholder(receipt.get(section, field)):
            _diagnose(
                diagnostics,
                receipt,
                f"{section}.{field}",
                "must describe a concrete bounded value",
            )
    return lifecycle


def _validate_sessions(
    receipt: ParsedReceipt, diagnostics: list[Diagnostic]
) -> None:
    rows = _parse_table(receipt.sections.get("Sessions", ""))
    expected = ["Role", "Provider", "Model", "Brida-owned pane", "Session"]
    if not rows or rows[0] != expected:
        _diagnose(
            diagnostics,
            receipt,
            "Sessions.table",
            f"expected header {expected}",
        )
        return
    if len(rows) < 2:
        _diagnose(
            diagnostics,
            receipt,
            "Sessions.table",
            "must contain at least one session row",
        )
    for index, row in enumerate(rows[1:], start=1):
        if len(row) != len(expected):
            _diagnose(
                diagnostics,
                receipt,
                f"Sessions.row[{index}]",
                f"expected {len(expected)} columns, found {len(row)}",
            )


def _validate_acceptance(
    receipt: ParsedReceipt,
    lifecycle: str,
    diagnostics: list[Diagnostic],
) -> bool:
    rows = _parse_table(receipt.sections.get("Acceptance criteria", ""))
    expected = ["Criterion ID", "Status", "Evidence"]
    if not rows or rows[0] != expected:
        _diagnose(
            diagnostics,
            receipt,
            "Acceptance criteria.table",
            f"expected header {expected}",
        )
        return False
    if len(rows) < 2:
        _diagnose(
            diagnostics,
            receipt,
            "Acceptance criteria.table",
            "must contain at least one criterion row",
        )
        return False

    all_pass = True
    seen_ids: set[str] = set()
    for index, row in enumerate(rows[1:], start=1):
        field = f"Acceptance criteria.row[{index}]"
        if len(row) != 3:
            _diagnose(
                diagnostics,
                receipt,
                field,
                f"expected 3 columns, found {len(row)}",
            )
            all_pass = False
            continue
        criterion_id = _plain(row[0])
        status = _status_token(row[1])
        evidence = row[2]
        if _is_placeholder(criterion_id):
            _diagnose(
                diagnostics,
                receipt,
                f"{field}.Criterion ID",
                "must be concrete",
            )
        elif criterion_id in seen_ids:
            _diagnose(
                diagnostics,
                receipt,
                f"{field}.Criterion ID",
                f"duplicate criterion ID {criterion_id!r}",
            )
        seen_ids.add(criterion_id)
        if status not in CRITERION_STATES:
            _diagnose(
                diagnostics,
                receipt,
                f"{field}.Status",
                f"must be one of {sorted(CRITERION_STATES)}, found {status!r}",
            )
        if status != "pass":
            all_pass = False
        if status == "pass" and _is_placeholder(evidence):
            _diagnose(
                diagnostics,
                receipt,
                f"{field}.Evidence",
                "passing criteria require concrete evidence",
            )
    if lifecycle == "implemented" and not all_pass:
        _diagnose(
            diagnostics,
            receipt,
            "Acceptance criteria",
            "implemented receipts require every criterion to pass",
        )
    return all_pass


def _validate_verification(
    receipt: ParsedReceipt,
    lifecycle: str,
    diagnostics: list[Diagnostic],
) -> bool:
    rows = _parse_table(receipt.sections.get("Verification", ""))
    expected = ["Command", "Result"]
    if not rows or rows[0] != expected:
        _diagnose(
            diagnostics,
            receipt,
            "Verification.table",
            f"expected header {expected}",
        )
        return False
    if len(rows) < 2:
        _diagnose(
            diagnostics,
            receipt,
            "Verification.table",
            "must contain at least one verification row",
        )
        return False

    all_pass = True
    for index, row in enumerate(rows[1:], start=1):
        field = f"Verification.row[{index}]"
        if len(row) != 2:
            _diagnose(
                diagnostics,
                receipt,
                field,
                f"expected 2 columns, found {len(row)}",
            )
            all_pass = False
            continue
        command = row[0]
        result = _status_token(row[1])
        if _is_placeholder(command):
            _diagnose(
                diagnostics,
                receipt,
                f"{field}.Command",
                "must be concrete",
            )
        if result not in VERIFICATION_STATES:
            _diagnose(
                diagnostics,
                receipt,
                f"{field}.Result",
                f"must start with one of {sorted(VERIFICATION_STATES)}",
            )
        if result != "pass":
            all_pass = False
    if lifecycle == "implemented" and not all_pass:
        _diagnose(
            diagnostics,
            receipt,
            "Verification",
            "implemented receipts require every verification row to pass",
        )
    return all_pass


def _validate_implementation_evidence(
    receipt: ParsedReceipt,
    lifecycle: str,
    diagnostics: list[Diagnostic],
) -> bool:
    complete = True
    for field in REQUIRED_FIELDS["Implementation evidence"]:
        if _is_placeholder(receipt.get("Implementation evidence", field)):
            complete = False
            if lifecycle in {"implemented", "reviewed"}:
                _diagnose(
                    diagnostics,
                    receipt,
                    f"Implementation evidence.{field}",
                    "must be concrete after implementation",
                )
    return complete


def _validate_attempt_lifecycle(
    receipt: ParsedReceipt,
    plan_lifecycle: str,
    implementation_complete: bool,
    diagnostics: list[Diagnostic],
) -> None:
    if _plain(receipt.get("Identity", "Receipt schema version")) != "2":
        return

    lifecycle = _plain(
        receipt.get("Identity", "Attempt lifecycle state")
    ).lower()
    prior_state = _plain(receipt.get("Identity", "Prior attempt state")).lower()
    attempt_value = _plain(receipt.get("Identity", "Attempt"))
    try:
        attempt = int(attempt_value)
    except ValueError:
        attempt = 0

    if plan_lifecycle in {"implemented", "reviewed"} and lifecycle != "complete":
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Attempt lifecycle state",
            f"{plan_lifecycle} receipts require 'complete'",
        )
    if (
        lifecycle in {"active", "stale", "abandoned"}
        and plan_lifecycle != "accepted"
    ):
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Attempt lifecycle state",
            f"{lifecycle!r} is valid only while plan status is 'accepted'",
        )
    if lifecycle in {"stale", "abandoned"} and not implementation_complete:
        _diagnose(
            diagnostics,
            receipt,
            "Implementation evidence",
            f"{lifecycle!r} lifecycle requires concrete evidence",
        )
    if (
        plan_lifecycle in {"implemented", "reviewed"}
        and attempt > 1
        and prior_state != "abandoned"
    ):
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Prior attempt state",
            f"{plan_lifecycle} replacement receipts require 'abandoned'",
        )


def _validate_review_and_cleanup(
    receipt: ParsedReceipt,
    lifecycle: str,
    criteria_pass: bool,
    verification_pass: bool,
    implementation_complete: bool,
    diagnostics: list[Diagnostic],
) -> None:
    verdict = _plain(receipt.get("Review verdict", "Verdict"))
    findings = receipt.get("Review verdict", "Findings")
    panes_closed = _plain(
        receipt.get("Cleanup status", "Brida-owned panes closed")
    ).lower()
    memory_updated = _plain(
        receipt.get("Cleanup status", "Project memory updated")
    ).lower()
    attempt_lifecycle = _plain(
        receipt.get("Identity", "Attempt lifecycle state")
    ).lower()
    schema = _plain(receipt.get("Identity", "Receipt schema version"))

    for field, value in (
        ("Cleanup status.Brida-owned panes closed", panes_closed),
        ("Cleanup status.Project memory updated", memory_updated),
    ):
        if value not in {"yes", "no", "null"}:
            _diagnose(
                diagnostics,
                receipt,
                field,
                "must be yes, no, or null",
            )

    if lifecycle in {"accepted", "implemented"}:
        if verdict.lower() not in {"null", "pending", ""}:
            _diagnose(
                diagnostics,
                receipt,
                "Review verdict.Verdict",
                f"{lifecycle} receipts must not claim a review verdict",
            )
        return

    if verdict not in {"PASS", "CHANGES REQUIRED"}:
        _diagnose(
            diagnostics,
            receipt,
            "Review verdict.Verdict",
            "reviewed receipts require PASS or CHANGES REQUIRED",
        )
        return

    if verdict == "CHANGES REQUIRED":
        if _is_placeholder(findings):
            _diagnose(
                diagnostics,
                receipt,
                "Review verdict.Findings",
                "CHANGES REQUIRED requires actionable findings",
            )
        return

    if schema == "2" and attempt_lifecycle != "complete":
        _diagnose(
            diagnostics,
            receipt,
            "Identity.Attempt lifecycle state",
            "reviewed PASS requires 'complete'",
        )
    if not criteria_pass:
        _diagnose(
            diagnostics,
            receipt,
            "Acceptance criteria",
            "reviewed PASS requires every criterion to pass",
        )
    if not verification_pass:
        _diagnose(
            diagnostics,
            receipt,
            "Verification",
            "reviewed PASS requires every verification row to pass",
        )
    if not implementation_complete:
        _diagnose(
            diagnostics,
            receipt,
            "Implementation evidence",
            "reviewed PASS requires complete implementation evidence",
        )
    if panes_closed != "yes":
        _diagnose(
            diagnostics,
            receipt,
            "Cleanup status.Brida-owned panes closed",
            "reviewed PASS requires yes",
        )
    if memory_updated != "yes":
        _diagnose(
            diagnostics,
            receipt,
            "Cleanup status.Project memory updated",
            "reviewed PASS requires yes",
        )


def validate_receipt(
    path: Path, projects_root: Path
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    receipt = parse_receipt(path, diagnostics)
    _validate_personal_paths(receipt, diagnostics)
    _validate_path_identity(receipt, projects_root, diagnostics)
    _validate_timestamp(receipt, diagnostics)
    _validate_role_topology(receipt, projects_root, diagnostics)
    _validate_attempt(receipt, projects_root, diagnostics)
    lifecycle = _validate_plan_and_scope(receipt, diagnostics)
    _validate_sessions(receipt, diagnostics)
    criteria_pass = _validate_acceptance(receipt, lifecycle, diagnostics)
    verification_pass = _validate_verification(receipt, lifecycle, diagnostics)
    implementation_complete = _validate_implementation_evidence(
        receipt, lifecycle, diagnostics
    )
    _validate_attempt_lifecycle(
        receipt,
        lifecycle,
        implementation_complete,
        diagnostics,
    )
    _validate_review_and_cleanup(
        receipt,
        lifecycle,
        criteria_pass,
        verification_pass,
        implementation_complete,
        diagnostics,
    )
    return diagnostics


def discover_receipts(projects_root: Path) -> list[Path]:
    """Return only canonical project handoff receipts."""
    return sorted(projects_root.glob("*/handoffs/*/receipt.md"))


def validate_projects(projects_root: Path) -> tuple[list[Path], list[Diagnostic]]:
    root = projects_root.resolve()
    receipts = discover_receipts(root)
    diagnostics: list[Diagnostic] = []
    for receipt in receipts:
        diagnostics.extend(validate_receipt(receipt, root))
    return receipts, diagnostics


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate canonical project handoff receipts."
    )
    parser.add_argument(
        "projects_root",
        nargs="?",
        default="projects",
        type=Path,
        help="projects root containing <slug>/handoffs/<task-id>/receipt.md",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    projects_root = args.projects_root
    if not projects_root.is_dir():
        print(
            f"{projects_root}: projects root: directory does not exist",
            file=sys.stderr,
        )
        return 2

    receipts, diagnostics = validate_projects(projects_root)
    if diagnostics:
        for diagnostic in diagnostics:
            print(diagnostic.format(), file=sys.stderr)
        print(
            f"Invalid canonical handoff receipts: {len(diagnostics)} "
            f"issue(s) across {len(receipts)} receipt(s).",
            file=sys.stderr,
        )
        return 1

    print(f"Validated {len(receipts)} canonical handoff receipt(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
