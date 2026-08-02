#!/usr/bin/env python3
"""Validate checkout-mode task dossiers without mutating them.

A tracked task owns one dossier directory holding all eleven standard
artifacts plus the canonical handoff receipt. Every task level produces the
same artifact set; the level changes required evidence depth, reviewer
strength, and authorization gates. Artifact presence alone is never accepted as
evidence, and this validator never repairs what it diagnoses.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Sequence

from .parser import (
    concrete_list_items,
    has_concrete_statement,
    is_placeholder,
    parse_artifact,
    parse_table,
    plain,
    section_names,
)
from .schema import (
    APPLICABILITY_STATES,
    ARTIFACTS,
    ARTIFACT_EXTRA_SECTIONS,
    AUTHORSHIP_KINDS,
    BODY_SECTIONS,
    CANONICAL_MEMORY_FILES,
    Diagnostic,
    INDEX_IDENTITY_FIELDS,
    INDEX_IDENTITY_SECTION,
    INDEX_PROJECTION_SECTIONS,
    INDEX_STATUS_HEADER,
    INDEX_STATUS_SECTION,
    MEMORY_OWNED_SECTIONS,
    METADATA_FIELDS,
    METADATA_SECTION,
    MINIMUM_EVIDENCE_ITEMS,
    OWNERS,
    PERSONAL_PATH_PATTERNS,
    PHASE_STATES,
    PLAN_STATUSES,
    PLAN_STATUS_FIELDS,
    PLAN_STATUS_SECTION,
    PROJECT_SLUG_PATTERN,
    ParsedArtifact,
    RECEIPT_OWNED_FIELD_LABELS,
    RECEIPT_OWNED_SECTIONS,
    REMOTE_ACTION_FIELDS,
    REMOTE_ACTION_PATTERNS,
    REMOTE_ACTION_SECTION,
    REQUEST_PROVENANCE_FIELDS,
    REQUEST_PROVENANCE_SECTION,
    REVIEW_ARTIFACTS,
    REVIEW_ROUTE_STRENGTHS,
    REVIEW_TARGET_FIELDS,
    REVIEW_TARGET_SECTION,
    REVIEW_VERDICTS,
    SETTLED_PHASE_STATES,
    SHIP_AUTHORIZATION_STATES,
    TASK_ID_PATTERN,
    TASK_LEVELS,
)


EXTRA_SECTION_FIELDS = ARTIFACT_EXTRA_SECTIONS

PROVENANCE_FIELDS = (
    "Authoring session",
    "Effective route",
    "Effective model",
    "Effective effort",
)


def _diagnose(
    diagnostics: list[Diagnostic],
    artifact: ParsedArtifact,
    field: str,
    message: str,
) -> None:
    diagnostics.append(Diagnostic(artifact.path, field, message))


def _load_artifacts(
    dossier: Path, diagnostics: list[Diagnostic]
) -> dict[str, ParsedArtifact]:
    artifacts: dict[str, ParsedArtifact] = {}
    for name in ARTIFACTS:
        path = dossier / f"{name}.md"
        if path.is_symlink():
            diagnostics.append(
                Diagnostic(path, "file", "dossier artifacts must not be symlinks")
            )
            continue
        if not path.is_file():
            diagnostics.append(
                Diagnostic(
                    path,
                    "file",
                    f"required task-dossier artifact {name}.md is missing",
                )
            )
            continue
        artifacts[name] = parse_artifact(path, name, diagnostics)
    return artifacts


def _validate_personal_paths(
    artifact: ParsedArtifact, diagnostics: list[Diagnostic]
) -> None:
    for pattern in PERSONAL_PATH_PATTERNS:
        match = pattern.search(artifact.text)
        if match:
            _diagnose(
                diagnostics,
                artifact,
                "path hygiene",
                f"personal or home path is forbidden: {match.group(0)!r}",
            )
            return


def _validate_structure(
    artifact: ParsedArtifact, diagnostics: list[Diagnostic]
) -> None:
    names = section_names(artifact.text)
    expected_sections = [METADATA_SECTION]
    for section, _ in EXTRA_SECTION_FIELDS.get(artifact.name, ()):
        expected_sections.append(section)
    if artifact.name == "index":
        expected_sections.append(INDEX_STATUS_SECTION)
    expected_sections.extend(BODY_SECTIONS)

    for section in expected_sections:
        count = names.count(section)
        if count != 1:
            _diagnose(
                diagnostics,
                artifact,
                f"section.{section}",
                f"expected exactly one section, found {count}",
            )

    positions = [names.index(section) for section in expected_sections if section in names]
    if positions != sorted(positions):
        _diagnose(
            diagnostics,
            artifact,
            "sections",
            "required sections are not in canonical order",
        )

    required_fields = [(METADATA_SECTION, METADATA_FIELDS)]
    required_fields.extend(EXTRA_SECTION_FIELDS.get(artifact.name, ()))
    for section, fields in required_fields:
        for label in fields:
            if label not in artifact.fields.get(section, {}):
                _diagnose(
                    diagnostics,
                    artifact,
                    f"{section}.{label}",
                    "required field is missing",
                )


def _validate_identity(
    artifact: ParsedArtifact,
    task_id: str,
    diagnostics: list[Diagnostic],
) -> None:
    declared_id = plain(artifact.get(METADATA_SECTION, "Task ID"))
    if not TASK_ID_PATTERN.fullmatch(declared_id):
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Task ID",
            "must be a stable branch-independent task ID such as ABC-001, "
            f"found {declared_id!r}",
        )
    elif declared_id != task_id:
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Task ID",
            f"expected {task_id!r} from the canonical dossier path, "
            f"found {declared_id!r}",
        )

    declared_artifact = plain(artifact.get(METADATA_SECTION, "Artifact"))
    if declared_artifact != artifact.name:
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Artifact",
            f"expected {artifact.name!r}, found {declared_artifact!r}",
        )

    version = plain(artifact.get(METADATA_SECTION, "Artifact version"))
    try:
        valid_version = int(version) >= 1
    except ValueError:
        valid_version = False
    if not valid_version:
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Artifact version",
            "must be a positive integer",
        )

    if is_placeholder(artifact.get(METADATA_SECTION, "Origin")):
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Origin",
            "must record a concrete immutable origin marker",
        )

    owner = plain(artifact.get(METADATA_SECTION, "Owner")).lower()
    if owner not in OWNERS:
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Owner",
            f"must be one of {sorted(OWNERS)}, found {owner!r}",
        )


def _validate_state(
    artifact: ParsedArtifact,
    level: str,
    diagnostics: list[Diagnostic],
) -> None:
    phase = plain(artifact.get(METADATA_SECTION, "Phase state")).lower()
    applicability = plain(artifact.get(METADATA_SECTION, "Applicability")).lower()
    rationale = artifact.get(METADATA_SECTION, "Applicability rationale")
    evidence_items = concrete_list_items(artifact.sections.get("Evidence", ""))

    if phase not in PHASE_STATES:
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Phase state",
            f"must be one of {sorted(PHASE_STATES)}, found {phase!r}",
        )
    if applicability not in APPLICABILITY_STATES:
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Applicability",
            f"must be one of {sorted(APPLICABILITY_STATES)}, found {applicability!r}",
        )

    if (phase == "not-required") != (applicability == "not-required"):
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Phase state",
            "phase state 'not-required' and applicability 'not-required' "
            "must be declared together",
        )

    if applicability == "not-required":
        if is_placeholder(rationale):
            _diagnose(
                diagnostics,
                artifact,
                f"{METADATA_SECTION}.Applicability rationale",
                "'not-required' requires a concrete rationale",
            )
        if not evidence_items:
            _diagnose(
                diagnostics,
                artifact,
                "Evidence",
                "'not-required' requires concrete evidence; a missing or empty "
                "artifact is never evidence",
            )
        # 'not-required' is a recorded decision, not an exemption from the
        # evidence contract: it still asserts a claim and states uncertainty.
        if is_placeholder(artifact.sections.get("Claim or decision", "").strip()):
            _diagnose(
                diagnostics,
                artifact,
                "Claim or decision",
                "'not-required' requires a concrete claim or decision",
            )
        if not has_concrete_statement(artifact.sections.get("Uncertainty", "")):
            _diagnose(
                diagnostics,
                artifact,
                "Uncertainty",
                "'not-required' must concretely state unresolved uncertainty or "
                "record that none remains; a placeholder is not a statement",
            )
        return

    if not is_placeholder(rationale):
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Applicability rationale",
            "required artifacts must leave the rationale null",
        )

    if phase == "blocked" and not has_concrete_statement(
        artifact.sections.get("Uncertainty", "")
    ):
        _diagnose(
            diagnostics,
            artifact,
            "Uncertainty",
            "blocked artifacts require concrete unresolved uncertainty",
        )

    if phase != "passed":
        return

    if is_placeholder(artifact.sections.get("Claim or decision", "").strip()):
        _diagnose(
            diagnostics,
            artifact,
            "Claim or decision",
            "passed artifacts require a concrete claim or decision",
        )
    minimum = MINIMUM_EVIDENCE_ITEMS.get(level, 1)
    if len(evidence_items) < minimum:
        _diagnose(
            diagnostics,
            artifact,
            "Evidence",
            f"level {level} requires at least {minimum} concrete evidence "
            f"item(s), found {len(evidence_items)}",
        )
    if not has_concrete_statement(artifact.sections.get("Uncertainty", "")):
        _diagnose(
            diagnostics,
            artifact,
            "Uncertainty",
            "passed artifacts must concretely state unresolved uncertainty or "
            "record that none remains; a placeholder is not a statement",
        )


def _validate_provenance(
    artifact: ParsedArtifact, diagnostics: list[Diagnostic]
) -> None:
    authorship = plain(artifact.get(METADATA_SECTION, "Authorship")).lower()
    if authorship not in AUTHORSHIP_KINDS:
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Authorship",
            f"must be one of {sorted(AUTHORSHIP_KINDS)}, found {authorship!r}",
        )
        return

    for label in PROVENANCE_FIELDS:
        value = artifact.get(METADATA_SECTION, label)
        if authorship == "model" and is_placeholder(value):
            _diagnose(
                diagnostics,
                artifact,
                f"{METADATA_SECTION}.{label}",
                "model-authored artifacts must record the effective session, "
                "route, model, and effort",
            )
        if authorship == "human" and not is_placeholder(value):
            _diagnose(
                diagnostics,
                artifact,
                f"{METADATA_SECTION}.{label}",
                "human-authored artifacts must leave model provenance null",
            )

    verdict = plain(artifact.get(METADATA_SECTION, "Review verdict"))
    reviewing = artifact.get(METADATA_SECTION, "Reviewing session")
    phase = plain(artifact.get(METADATA_SECTION, "Phase state")).lower()

    if not is_placeholder(verdict) and verdict not in REVIEW_VERDICTS:
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Review verdict",
            f"must be one of {sorted(REVIEW_VERDICTS)} or null, found {verdict!r}",
        )
    if not is_placeholder(verdict) and is_placeholder(reviewing):
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Reviewing session",
            "a review verdict requires the reviewing session identity",
        )

    if artifact.name in REVIEW_ARTIFACTS and phase == "passed":
        if is_placeholder(reviewing):
            _diagnose(
                diagnostics,
                artifact,
                f"{METADATA_SECTION}.Reviewing session",
                "review artifacts require the reviewing session identity",
            )
        if verdict not in REVIEW_VERDICTS:
            _diagnose(
                diagnostics,
                artifact,
                f"{METADATA_SECTION}.Review verdict",
                f"review artifacts require one of {sorted(REVIEW_VERDICTS)}",
            )


def _validate_ownership(
    artifacts: dict[str, ParsedArtifact], diagnostics: list[Diagnostic]
) -> None:
    for name in REVIEW_ARTIFACTS:
        artifact = artifacts.get(name)
        if artifact is None:
            continue
        owner = plain(artifact.get(METADATA_SECTION, "Owner")).lower()
        if owner != "reviewer":
            _diagnose(
                diagnostics,
                artifact,
                f"{METADATA_SECTION}.Owner",
                f"review artifacts are owned by the reviewer, found {owner!r}",
            )

    for name in ("plan", "design", "requirements"):
        artifact = artifacts.get(name)
        if artifact is None:
            continue
        owner = plain(artifact.get(METADATA_SECTION, "Owner")).lower()
        if owner == "reviewer":
            _diagnose(
                diagnostics,
                artifact,
                f"{METADATA_SECTION}.Owner",
                "reviewers must not back-write planning artifacts",
            )

    plan = artifacts.get("plan")
    if plan is None:
        return
    plan_session = plain(plan.get(METADATA_SECTION, "Authoring session"))
    if is_placeholder(plan_session):
        return

    # The reviewing session is the session that performed the review; the
    # authoring session is the session that wrote the review artifact. Neither
    # may be the session that authored the plan.
    for name in REVIEW_ARTIFACTS:
        review = artifacts.get(name)
        if review is None:
            continue
        for label in ("Reviewing session", "Authoring session"):
            session = plain(review.get(METADATA_SECTION, label))
            if is_placeholder(session) or session != plan_session:
                continue
            _diagnose(
                diagnostics,
                review,
                f"{METADATA_SECTION}.{label}",
                f"{name} requires a session independent of the plan author",
            )


def _validate_request(
    artifact: ParsedArtifact, diagnostics: list[Diagnostic]
) -> None:
    origin = plain(artifact.get(METADATA_SECTION, "Origin"))
    if origin != "user-request":
        _diagnose(
            diagnostics,
            artifact,
            f"{METADATA_SECTION}.Origin",
            f"request provenance origin must be 'user-request', found {origin!r}",
        )
    redaction = plain(
        artifact.get(REQUEST_PROVENANCE_SECTION, "Redaction applied")
    ).lower()
    if redaction != "yes":
        _diagnose(
            diagnostics,
            artifact,
            f"{REQUEST_PROVENANCE_SECTION}.Redaction applied",
            "recorded request provenance must be redacted before storage",
        )
    mutability = plain(
        artifact.get(REQUEST_PROVENANCE_SECTION, "Mutability")
    ).lower()
    if mutability != "immutable":
        _diagnose(
            diagnostics,
            artifact,
            f"{REQUEST_PROVENANCE_SECTION}.Mutability",
            "request provenance is read-only; amendments are appended as new "
            "versioned artifacts",
        )


def _validate_pr_description(
    artifact: ParsedArtifact, diagnostics: list[Diagnostic]
) -> None:
    authorized = plain(
        artifact.get(REMOTE_ACTION_SECTION, "Remote action authorized")
    ).lower()
    if authorized != "no":
        _diagnose(
            diagnostics,
            artifact,
            f"{REMOTE_ACTION_SECTION}.Remote action authorized",
            "PR text never authorizes remote action",
        )
    for pattern in REMOTE_ACTION_PATTERNS:
        match = pattern.search(artifact.text)
        if match:
            _diagnose(
                diagnostics,
                artifact,
                "remote action",
                f"PR text must not instruct remote mutation: {match.group(0)!r}",
            )
            return


def _plan_version(artifact: ParsedArtifact | None) -> str:
    if artifact is None:
        return ""
    return plain(artifact.get(METADATA_SECTION, "Artifact version"))


def _validate_plan_linkage(
    artifacts: dict[str, ParsedArtifact],
    index_fields: dict[str, str],
    diagnostics: list[Diagnostic],
) -> None:
    plan = artifacts.get("plan")
    if plan is None:
        return

    plan_id = plain(plan.get(PLAN_STATUS_SECTION, "Plan ID"))
    status = plain(plan.get(PLAN_STATUS_SECTION, "Plan status")).lower()
    version = _plan_version(plan)

    if is_placeholder(plan_id):
        _diagnose(
            diagnostics,
            plan,
            f"{PLAN_STATUS_SECTION}.Plan ID",
            "plans require a concrete plan ID",
        )
    if status not in PLAN_STATUSES:
        _diagnose(
            diagnostics,
            plan,
            f"{PLAN_STATUS_SECTION}.Plan status",
            f"must be one of {sorted(PLAN_STATUSES)}, found {status!r}",
        )

    accepted_id = plain(index_fields.get("Accepted plan ID"))
    accepted_version = plain(index_fields.get("Accepted plan version"))
    index = artifacts.get("index")

    if status == "accepted" and index is not None:
        if accepted_id != plan_id:
            _diagnose(
                diagnostics,
                index,
                f"{INDEX_IDENTITY_SECTION}.Accepted plan ID",
                f"expected {plan_id!r} from plan.md, found {accepted_id!r}",
            )
        if accepted_version != version:
            _diagnose(
                diagnostics,
                index,
                f"{INDEX_IDENTITY_SECTION}.Accepted plan version",
                f"expected {version!r} from plan.md, found {accepted_version!r}",
            )

    for name in REVIEW_ARTIFACTS:
        review = artifacts.get(name)
        if review is None:
            continue
        if plain(review.get(METADATA_SECTION, "Phase state")).lower() != "passed":
            continue
        reviewed_id = plain(review.get(REVIEW_TARGET_SECTION, "Reviewed plan ID"))
        reviewed_version = plain(
            review.get(REVIEW_TARGET_SECTION, "Reviewed plan version")
        )
        if reviewed_id != plan_id:
            _diagnose(
                diagnostics,
                review,
                f"{REVIEW_TARGET_SECTION}.Reviewed plan ID",
                f"expected {plan_id!r}, found {reviewed_id!r}",
            )
        if reviewed_version != version:
            _diagnose(
                diagnostics,
                review,
                f"{REVIEW_TARGET_SECTION}.Reviewed plan version",
                "review must reference the exact accepted plan version "
                f"{version!r}, found {reviewed_version!r}",
            )


def _validate_index(
    index: ParsedArtifact,
    artifacts: dict[str, ParsedArtifact],
    dossier: Path,
    projects_root: Path,
    project: str,
    task_id: str,
    level: str,
    diagnostics: list[Diagnostic],
) -> None:
    fields = index.fields.get(INDEX_IDENTITY_SECTION, {})

    declared_project = plain(fields.get("Project"))
    if declared_project != project:
        _diagnose(
            diagnostics,
            index,
            f"{INDEX_IDENTITY_SECTION}.Project",
            f"expected {project!r} from the canonical dossier path, "
            f"found {declared_project!r}",
        )

    _validate_no_duplicated_authority(index, diagnostics)

    receipt_value = plain(fields.get("Canonical receipt path"))
    _validate_receipt_link(
        index, dossier, projects_root, project, task_id, receipt_value, diagnostics
    )
    _validate_memory_link(
        index,
        projects_root,
        project,
        plain(fields.get("Project memory path")),
        diagnostics,
    )

    strength = plain(fields.get("Review route strength")).lower()
    override = fields.get("Review route override")
    if strength not in REVIEW_ROUTE_STRENGTHS:
        _diagnose(
            diagnostics,
            index,
            f"{INDEX_IDENTITY_SECTION}.Review route strength",
            f"must be one of {sorted(REVIEW_ROUTE_STRENGTHS)}, found {strength!r}",
        )
    elif strength == "stronger" and is_placeholder(override):
        _diagnose(
            diagnostics,
            index,
            f"{INDEX_IDENTITY_SECTION}.Review route override",
            "a stronger reviewer requires the documented one-off override",
        )
    elif strength == "routine" and not is_placeholder(override):
        _diagnose(
            diagnostics,
            index,
            f"{INDEX_IDENTITY_SECTION}.Review route override",
            "routine review strength must leave the override null",
        )

    if level == "2" and strength != "stronger":
        _diagnose(
            diagnostics,
            index,
            f"{INDEX_IDENTITY_SECTION}.Review route strength",
            "level 2 requires a documented stronger reviewer",
        )

    authorization = plain(fields.get("Ship authorization")).lower()
    evidence = fields.get("Ship authorization evidence")
    if authorization not in SHIP_AUTHORIZATION_STATES:
        _diagnose(
            diagnostics,
            index,
            f"{INDEX_IDENTITY_SECTION}.Ship authorization",
            f"must be one of {sorted(SHIP_AUTHORIZATION_STATES)}, "
            f"found {authorization!r}",
        )
    elif authorization == "user-authorized" and is_placeholder(evidence):
        _diagnose(
            diagnostics,
            index,
            f"{INDEX_IDENTITY_SECTION}.Ship authorization evidence",
            "authorized ship requires recorded user authorization evidence",
        )
    elif authorization == "not-requested" and not is_placeholder(evidence):
        _diagnose(
            diagnostics,
            index,
            f"{INDEX_IDENTITY_SECTION}.Ship authorization evidence",
            "unrequested ship must leave the authorization evidence null",
        )

    if level in {"0", "1"} and authorization != "not-requested":
        _diagnose(
            diagnostics,
            index,
            f"{INDEX_IDENTITY_SECTION}.Ship authorization",
            f"level {level} does not gate a ship; authorization must be "
            "'not-requested'",
        )

    _validate_status_table(index, artifacts, diagnostics)


def _validate_no_duplicated_authority(
    index: ParsedArtifact, diagnostics: list[Diagnostic]
) -> None:
    """The receipt and project memory stay canonical; the index only links."""
    message = (
        "the receipt and project memory remain canonical; the index links "
        "instead of duplicating them"
    )
    for section in section_names(index.text):
        if section in RECEIPT_OWNED_SECTIONS:
            _diagnose(
                diagnostics,
                index,
                f"section.{section}",
                f"receipt-owned section: {message}",
            )
        elif section in MEMORY_OWNED_SECTIONS:
            _diagnose(
                diagnostics,
                index,
                f"section.{section}",
                f"project-memory-owned section: {message}",
            )
        elif section not in INDEX_PROJECTION_SECTIONS:
            _diagnose(
                diagnostics,
                index,
                f"section.{section}",
                "is not an index projection section; the index may declare "
                f"only {list(INDEX_PROJECTION_SECTIONS)}",
            )

    for label in RECEIPT_OWNED_FIELD_LABELS:
        if re.search(rf"^- {re.escape(label)}:", index.text, re.MULTILINE):
            _diagnose(diagnostics, index, f"field.{label}", message)

    status_tables = len(parse_table(index.sections.get(INDEX_STATUS_SECTION, "")))
    if len(parse_table(index.text)) > status_tables:
        _diagnose(
            diagnostics,
            index,
            f"{INDEX_STATUS_SECTION}.table",
            "the artifact status table is the only table the index may carry; "
            + message,
        )


def _is_safe_relative(value: str) -> bool:
    pure = PurePosixPath(value)
    return not (
        pure.is_absolute()
        or ".." in pure.parts
        or "\\" in value
        or (pure.parts and pure.parts[0].startswith("~"))
    )


def _symlinked_ancestor(repository_root: Path, parts: Sequence[str]) -> Path | None:
    """Return the first symlinked ancestor of a declared authority path.

    An authority path whose leaf is a real file is still untrustworthy when a
    directory above it is a symlink: the link decides which file the name
    reaches. Components are walked from the repository root and ``lstat``-ed
    without following anything, so the check answers a question about the path
    that was declared rather than about whatever it currently resolves to.
    """
    current = repository_root
    for part in parts[:-1]:
        current = current / part
        if current.is_symlink():
            return current
    return None


def _validate_receipt_link(
    index: ParsedArtifact,
    dossier: Path,
    projects_root: Path,
    project: str,
    task_id: str,
    value: str,
    diagnostics: list[Diagnostic],
) -> None:
    field = f"{INDEX_IDENTITY_SECTION}.Canonical receipt path"
    if is_placeholder(value):
        _diagnose(
            diagnostics,
            index,
            field,
            "every tracked task links its canonical handoff receipt",
        )
        return

    if not _is_safe_relative(value):
        _diagnose(diagnostics, index, field, "must be a safe repo-relative path")
        return

    expected = "/".join(
        (projects_root.name, project, "handoffs", task_id, "receipt.md")
    )
    if value != expected:
        _diagnose(
            diagnostics,
            index,
            field,
            f"must be exactly {expected!r} for this task, found {value!r}",
        )
        return

    receipt = dossier / "receipt.md"
    if receipt.is_symlink() or not receipt.is_file():
        _diagnose(
            diagnostics,
            index,
            field,
            f"canonical receipt does not exist: {value}",
        )
        return

    ancestor = _symlinked_ancestor(
        projects_root.parent.resolve(), PurePosixPath(value).parts
    )
    if ancestor is not None:
        _diagnose(
            diagnostics,
            index,
            field,
            "must not reach the canonical receipt through a symlinked "
            f"ancestor: {ancestor}",
        )


def _validate_memory_link(
    index: ParsedArtifact,
    projects_root: Path,
    project: str,
    value: str,
    diagnostics: list[Diagnostic],
) -> None:
    """Project memory stays canonical, so the index must link it safely."""
    field = f"{INDEX_IDENTITY_SECTION}.Project memory path"
    if is_placeholder(value):
        _diagnose(
            diagnostics,
            index,
            field,
            "every tracked task links its canonical project memory",
        )
        return

    if not _is_safe_relative(value):
        _diagnose(diagnostics, index, field, "must be a safe repo-relative path")
        return

    pure = PurePosixPath(value)
    if list(pure.parts[:2]) != [projects_root.name, project] or len(pure.parts) != 3:
        _diagnose(
            diagnostics,
            index,
            field,
            f"must name a file directly inside "
            f"{projects_root.name}/{project}/, found {value!r}",
        )
        return
    if pure.name not in CANONICAL_MEMORY_FILES:
        _diagnose(
            diagnostics,
            index,
            field,
            f"must be one of {sorted(CANONICAL_MEMORY_FILES)}, found {pure.name!r}",
        )
        return

    repository_root = projects_root.parent.resolve()
    candidate = repository_root.joinpath(*pure.parts)
    if candidate.is_symlink():
        _diagnose(diagnostics, index, field, "must not be a symlink")
        return
    ancestor = _symlinked_ancestor(repository_root, pure.parts)
    if ancestor is not None:
        _diagnose(
            diagnostics,
            index,
            field,
            "must not reach project memory through a symlinked ancestor: "
            f"{ancestor}",
        )
        return
    try:
        resolved = candidate.resolve()
        resolved.relative_to(repository_root)
    except (OSError, ValueError):
        _diagnose(diagnostics, index, field, "must resolve inside the repository")
        return
    if not resolved.is_file():
        _diagnose(
            diagnostics,
            index,
            field,
            f"project memory file does not exist: {value}",
        )


def _validate_status_table(
    index: ParsedArtifact,
    artifacts: dict[str, ParsedArtifact],
    diagnostics: list[Diagnostic],
) -> None:
    rows = parse_table(index.sections.get(INDEX_STATUS_SECTION, ""))
    if not rows or [plain(cell) for cell in rows[0]] != INDEX_STATUS_HEADER:
        _diagnose(
            diagnostics,
            index,
            f"{INDEX_STATUS_SECTION}.table",
            f"expected header {INDEX_STATUS_HEADER}",
        )
        return

    declared: dict[str, list[str]] = {}
    for position, row in enumerate(rows[1:], start=1):
        if len(row) != len(INDEX_STATUS_HEADER):
            _diagnose(
                diagnostics,
                index,
                f"{INDEX_STATUS_SECTION}.row[{position}]",
                f"expected {len(INDEX_STATUS_HEADER)} columns, found {len(row)}",
            )
            continue
        declared[plain(row[0])] = [plain(cell) for cell in row]

    for name in ARTIFACTS:
        row = declared.get(name)
        if row is None:
            _diagnose(
                diagnostics,
                index,
                f"{INDEX_STATUS_SECTION}.{name}",
                "every standard artifact must appear in the status table",
            )
            continue
        if row[3] != f"{name}.md":
            _diagnose(
                diagnostics,
                index,
                f"{INDEX_STATUS_SECTION}.{name}",
                f"expected path {name}.md, found {row[3]!r}",
            )
        artifact = artifacts.get(name)
        if artifact is None:
            continue
        for column, label in ((1, "Applicability"), (2, "Phase state")):
            actual = plain(artifact.get(METADATA_SECTION, label))
            if row[column] != actual:
                _diagnose(
                    diagnostics,
                    index,
                    f"{INDEX_STATUS_SECTION}.{name}.{label}",
                    f"index says {row[column]!r} but {name}.md says {actual!r}",
                )


def _validate_completion(
    artifacts: dict[str, ParsedArtifact], diagnostics: list[Diagnostic]
) -> None:
    """Gate the state a task must reach before it may be called complete."""
    for artifact in artifacts.values():
        phase = plain(artifact.get(METADATA_SECTION, "Phase state")).lower()
        if phase not in SETTLED_PHASE_STATES:
            _diagnose(
                diagnostics,
                artifact,
                f"{METADATA_SECTION}.Phase state",
                f"completed tasks require {sorted(SETTLED_PHASE_STATES)}, "
                f"found {phase!r}",
            )

    plan = artifacts.get("plan")
    if plan is not None:
        status = plain(plan.get(PLAN_STATUS_SECTION, "Plan status")).lower()
        if status != "accepted":
            _diagnose(
                diagnostics,
                plan,
                f"{PLAN_STATUS_SECTION}.Plan status",
                f"completed tasks require an accepted plan, found {status!r}",
            )

    plan_review = artifacts.get("plan-review")
    if plan_review is not None:
        applicability = plain(
            plan_review.get(METADATA_SECTION, "Applicability")
        ).lower()
        if applicability != "required":
            _diagnose(
                diagnostics,
                plan_review,
                f"{METADATA_SECTION}.Applicability",
                "plan review applies to every task and is never 'not-required'",
            )

    for name in REVIEW_ARTIFACTS:
        review = artifacts.get(name)
        if review is None:
            continue
        if plain(review.get(METADATA_SECTION, "Applicability")).lower() != "required":
            continue
        verdict = plain(review.get(METADATA_SECTION, "Review verdict"))
        if verdict != "PASS":
            _diagnose(
                diagnostics,
                review,
                f"{METADATA_SECTION}.Review verdict",
                f"completed tasks require a PASS verdict, found {verdict!r}",
            )


def _resolve_level(
    artifacts: dict[str, ParsedArtifact], diagnostics: list[Diagnostic]
) -> str:
    index = artifacts.get("index")
    level = plain(index.get(METADATA_SECTION, "Task level")) if index else ""
    if level not in TASK_LEVELS:
        if index is not None:
            _diagnose(
                diagnostics,
                index,
                f"{METADATA_SECTION}.Task level",
                f"must be one of {sorted(TASK_LEVELS)}, found {level!r}",
            )
        level = "0"

    for artifact in artifacts.values():
        declared = plain(artifact.get(METADATA_SECTION, "Task level"))
        if declared != level:
            _diagnose(
                diagnostics,
                artifact,
                f"{METADATA_SECTION}.Task level",
                f"expected {level!r} from index.md, found {declared!r}",
            )
    return level


def validate_dossier(
    dossier: Path,
    projects_root: Path,
    *,
    require_complete: bool = False,
) -> list[Diagnostic]:
    """Return every contract diagnostic for one task dossier."""
    diagnostics: list[Diagnostic] = []

    try:
        relative = dossier.relative_to(projects_root)
    except ValueError:
        diagnostics.append(
            Diagnostic(
                dossier,
                "path identity",
                f"dossier is outside supplied projects root {projects_root}",
            )
        )
        return diagnostics

    if len(relative.parts) != 3 or relative.parts[1] != "handoffs":
        diagnostics.append(
            Diagnostic(
                dossier,
                "path identity",
                "expected <project>/handoffs/<task-id>",
            )
        )
        return diagnostics

    project, task_id = relative.parts[0], relative.parts[2]
    if not TASK_ID_PATTERN.fullmatch(task_id):
        diagnostics.append(
            Diagnostic(
                dossier,
                "path identity",
                "task directory must be a stable branch-independent task ID "
                f"such as ABC-001, found {task_id!r}",
            )
        )

    artifacts = _load_artifacts(dossier, diagnostics)
    level = _resolve_level(artifacts, diagnostics)

    for artifact in artifacts.values():
        _validate_personal_paths(artifact, diagnostics)
        _validate_structure(artifact, diagnostics)
        _validate_identity(artifact, task_id, diagnostics)
        _validate_state(artifact, level, diagnostics)
        _validate_provenance(artifact, diagnostics)

    if require_complete:
        _validate_completion(artifacts, diagnostics)

    _validate_ownership(artifacts, diagnostics)
    if "request" in artifacts:
        _validate_request(artifacts["request"], diagnostics)
    if "pr-desc" in artifacts:
        _validate_pr_description(artifacts["pr-desc"], diagnostics)

    index = artifacts.get("index")
    if index is not None:
        _validate_index(
            index,
            artifacts,
            dossier,
            projects_root,
            project,
            task_id,
            level,
            diagnostics,
        )
        _validate_plan_linkage(
            artifacts,
            index.fields.get(INDEX_IDENTITY_SECTION, {}),
            diagnostics,
        )
    return diagnostics


def discover_dossiers(projects_root: Path) -> list[Path]:
    """Return every tracked task dossier directory.

    A dossier is tracked once it owns an ``index.md``. Handoff directories that
    predate the contract and hold only a task packet and receipt stay untracked,
    so the contract can be adopted one task at a time.
    """
    return sorted(path.parent for path in projects_root.glob("*/handoffs/*/index.md"))


def _declares_dossier_metadata(path: Path) -> bool:
    """Report whether a file is a dossier artifact rather than a plain document.

    A handoff may hold pre-contract planning notes named ``plan.md`` or
    ``design.md``. Only the dossier metadata block makes a file an artifact of
    this contract, so the filename alone must not revoke the historical
    receipt-only exemption.
    """
    if path.is_symlink() or not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return bool(
        re.search(rf"^## {re.escape(METADATA_SECTION)}$", text, re.MULTILINE)
    ) and bool(re.search(r"^- Artifact:", text, re.MULTILINE))


def discover_partial_dossiers(projects_root: Path) -> dict[Path, list[str]]:
    """Return handoff directories that started a dossier without an index.

    The receipt-only exemption covers historical handoffs. It does not cover a
    directory that already carries dossier artifacts, because a missing
    ``index.md`` would then silently exempt the task from the whole contract.
    """
    partial: dict[Path, list[str]] = {}
    optional = [name for name in ARTIFACTS if name != "index"]
    for handoff in sorted(projects_root.glob("*/handoffs/*")):
        if not handoff.is_dir() or (handoff / "index.md").exists():
            continue
        present = [
            name
            for name in optional
            if _declares_dossier_metadata(handoff / f"{name}.md")
        ]
        if present:
            partial[handoff] = present
    return partial


def validate_projects(
    projects_root: Path, *, require_complete: bool = False
) -> tuple[list[Path], list[Diagnostic]]:
    root = projects_root.resolve()
    dossiers = discover_dossiers(root)
    diagnostics: list[Diagnostic] = []

    for handoff, present in discover_partial_dossiers(root).items():
        diagnostics.append(
            Diagnostic(
                handoff,
                "partial adoption",
                "handoff carries dossier artifacts "
                f"({', '.join(f'{name}.md' for name in present)}) but no "
                "index.md; a tracked task owns the complete dossier",
            )
        )

    seen: dict[str, Path] = {}
    for dossier in dossiers:
        diagnostics.extend(
            validate_dossier(dossier, root, require_complete=require_complete)
        )
        task_id = dossier.name
        previous = seen.get(task_id)
        if previous is not None:
            diagnostics.append(
                Diagnostic(
                    dossier,
                    "task identity",
                    f"duplicate task ID {task_id!r} also used by {previous}",
                )
            )
        else:
            seen[task_id] = dossier
    return dossiers, diagnostics


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate checkout-mode task dossiers."
    )
    parser.add_argument(
        "projects_root",
        nargs="?",
        default="projects",
        type=Path,
        help="projects root containing <slug>/handoffs/<task-id>/index.md",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="also require every artifact to be passed or not-required",
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

    dossiers, diagnostics = validate_projects(
        projects_root, require_complete=args.require_complete
    )
    if diagnostics:
        for diagnostic in diagnostics:
            print(diagnostic.format(), file=sys.stderr)
        print(
            f"Invalid task dossiers: {len(diagnostics)} issue(s) across "
            f"{len(dossiers)} dossier(s).",
            file=sys.stderr,
        )
        return 1

    print(f"Validated {len(dossiers)} task dossier(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
