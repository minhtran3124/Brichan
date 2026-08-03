"""Task-dossier schema constants and parsed diagnostic types.

This module is the stable import boundary for the checkout-mode full-document
task-dossier contract. It records artifact identity, phase state, applicability,
evidence, provenance, and review vocabulary. It deliberately holds no routing
manifest keys: the workflow is routing-neutral and records only the effective
route that a session actually used.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ARTIFACTS = (
    "index",
    "request",
    "requirements",
    "brief",
    "options",
    "design",
    "client-follow-up-questions",
    "plan",
    "plan-review",
    "code-review",
    "pr-desc",
)

REVIEW_ARTIFACTS = ("plan-review", "code-review")

METADATA_SECTION = "Artifact metadata"

METADATA_FIELDS = (
    "Task ID",
    "Task level",
    "Artifact",
    "Artifact version",
    "Origin",
    "Owner",
    "Phase state",
    "Applicability",
    "Applicability rationale",
    "Authorship",
    "Authoring session",
    "Effective route",
    "Effective model",
    "Effective effort",
    "Reviewing session",
    "Review verdict",
)

BODY_SECTIONS = (
    "Claim or decision",
    "Evidence",
    "Uncertainty",
)

INDEX_IDENTITY_SECTION = "Task identity"
INDEX_STATUS_SECTION = "Artifact status"
INDEX_IDENTITY_FIELDS = (
    "Task ID",
    "Task level",
    "Project",
    "Canonical receipt path",
    "Project memory path",
    "Accepted plan ID",
    "Accepted plan version",
    "Review route strength",
    "Review route override",
    "Ship authorization",
    "Ship authorization evidence",
)
INDEX_STATUS_HEADER = ["Artifact", "Applicability", "Phase state", "Path"]

REQUEST_PROVENANCE_SECTION = "Request provenance"
REQUEST_PROVENANCE_FIELDS = ("Redaction applied", "Mutability")

PLAN_STATUS_SECTION = "Plan status"
PLAN_STATUS_FIELDS = ("Plan ID", "Plan status")

REVIEW_TARGET_SECTION = "Review target"
REVIEW_TARGET_FIELDS = ("Reviewed plan ID", "Reviewed plan version")

REMOTE_ACTION_SECTION = "Remote action"
REMOTE_ACTION_FIELDS = ("Remote action authorized",)

TASK_LEVELS = {"0", "1", "2"}
PHASE_STATES = {"pending", "active", "passed", "not-required", "blocked"}
SETTLED_PHASE_STATES = {"passed", "not-required"}
APPLICABILITY_STATES = {"required", "not-required"}
OWNERS = {"coordinator", "planner", "implementer", "reviewer", "generator"}
AUTHORSHIP_KINDS = {"model", "human"}
REVIEW_VERDICTS = {"PASS", "CHANGES REQUIRED"}
PLAN_STATUSES = {"draft", "accepted", "superseded"}
REVIEW_ROUTE_STRENGTHS = {"routine", "stronger"}
SHIP_AUTHORIZATION_STATES = {"not-requested", "user-authorized"}

# Level changes evidence depth, reviewer strength, and authorization gates.
# It never changes which artifacts must exist.
MINIMUM_EVIDENCE_ITEMS = {"0": 1, "1": 2, "2": 3}

# Receipt and project memory stay canonical; the index links instead of copying.
RECEIPT_OWNED_SECTIONS = (
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

RECEIPT_OWNED_FIELD_LABELS = (
    "Receipt schema version",
    "Receipt role",
    "Parent receipt path",
    "Handoff timestamp (UTC)",
    "Attempt",
    "Attempt origin",
    "Attempt lifecycle state",
    "Prior attempt state",
    "Replaces session",
    "Replacement evidence path",
    "Authorized paths",
    "Exclusive write ownership",
    "Excluded work",
    "Changed artifacts",
    "Diff evidence",
    "Test evidence",
    "Verdict",
    "Findings",
    "Brida-owned panes closed",
    "Project memory updated",
)

CANONICAL_MEMORY_FILES = (
    "current-state.md",
    "overview.md",
    "tasks.md",
    "decisions.md",
    "references.md",
)

# Project memory owns these; the index links to a memory file and copies none.
MEMORY_OWNED_SECTIONS = (
    "Current state",
    "Overview",
    "Tasks",
    "Decisions",
    "References",
    "Active tasks",
    "Project memory",
)

# The index is a projection. These are the only sections it may declare.
INDEX_PROJECTION_SECTIONS = (
    METADATA_SECTION,
    INDEX_IDENTITY_SECTION,
    INDEX_STATUS_SECTION,
) + BODY_SECTIONS

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

TASK_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3,}$")
PROJECT_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

PERSONAL_PATH_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9_])/Users/[^\s`|]+"),
    re.compile(r"(?<![A-Za-z0-9_])/home/[^\s`|]+"),
    re.compile(r"(?<![A-Za-z0-9_])~[/\\][^\s`|]*"),
    re.compile(r"(?i)\b[A-Z]:\\Users\\[^\s`|]+"),
)

# PR text describes a change. It never authorizes or instructs remote mutation.
REMOTE_ACTION_PATTERNS = (
    re.compile(r"(?i)\bgit\s+push\b"),
    re.compile(r"(?i)\bgh\s+pr\s+create\b"),
    re.compile(r"(?i)\bgh\s+pr\s+merge\b"),
    re.compile(r"(?i)\bgh\s+release\s+create\b"),
    re.compile(r"(?i)\btwine\s+upload\b"),
    re.compile(r"(?i)\bnpm\s+publish\b"),
    re.compile(r"(?i)\bmake\s+release\b"),
)


@dataclass(frozen=True)
class Diagnostic:
    path: Path
    field: str
    message: str

    def format(self) -> str:
        return f"{self.path}: {self.field}: {self.message}"


@dataclass
class ParsedArtifact:
    path: Path
    name: str
    text: str
    sections: dict[str, str]
    fields: dict[str, dict[str, str]]

    def get(self, section: str, field: str) -> str | None:
        return self.fields.get(section, {}).get(field)


__all__ = [
    "APPLICABILITY_STATES",
    "ARTIFACTS",
    "AUTHORSHIP_KINDS",
    "BODY_SECTIONS",
    "CANONICAL_MEMORY_FILES",
    "Diagnostic",
    "INDEX_IDENTITY_FIELDS",
    "INDEX_IDENTITY_SECTION",
    "INDEX_PROJECTION_SECTIONS",
    "INDEX_STATUS_HEADER",
    "INDEX_STATUS_SECTION",
    "MEMORY_OWNED_SECTIONS",
    "METADATA_FIELDS",
    "METADATA_SECTION",
    "MINIMUM_EVIDENCE_ITEMS",
    "OWNERS",
    "PERSONAL_PATH_PATTERNS",
    "PHASE_STATES",
    "PLACEHOLDER_VALUES",
    "PLAN_STATUSES",
    "PLAN_STATUS_FIELDS",
    "PLAN_STATUS_SECTION",
    "PROJECT_SLUG_PATTERN",
    "ParsedArtifact",
    "RECEIPT_OWNED_FIELD_LABELS",
    "RECEIPT_OWNED_SECTIONS",
    "REMOTE_ACTION_FIELDS",
    "REMOTE_ACTION_PATTERNS",
    "REMOTE_ACTION_SECTION",
    "REQUEST_PROVENANCE_FIELDS",
    "REQUEST_PROVENANCE_SECTION",
    "REVIEW_ARTIFACTS",
    "REVIEW_ROUTE_STRENGTHS",
    "REVIEW_TARGET_FIELDS",
    "REVIEW_TARGET_SECTION",
    "REVIEW_VERDICTS",
    "SETTLED_PHASE_STATES",
    "SHIP_AUTHORIZATION_STATES",
    "TASK_ID_PATTERN",
    "TASK_LEVELS",
]
