"""Structured task-dossier record: typed loading and refusal diagnostics.

One UTF-8 JSON object describes one complete dossier. This module loads it
under exhaustive key-to-type tables, refuses every malformed, hostile, or
structurally injected value, and returns immutable dataclasses. It derives
nothing and infers nothing: a value the contract requires is either recorded
concretely or refused.

JSON ``null`` is the only null. The literal string ``"null"`` is a placeholder
and is refused wherever a null is meaningful. Types are compared with
``type(v) is ...`` rather than ``isinstance`` so that ``True`` can never be
smuggled into an integer position.

This module deliberately imports no validator and reads no routing manifest.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from .schema import (
    APPLICABILITY_STATES,
    ARTIFACTS,
    ARTIFACT_EXTRA_SECTIONS,
    AUTHORSHIP_KINDS,
    BODY_SECTIONS,
    CANONICAL_MEMORY_FILES,
    INDEX_IDENTITY_FIELDS,
    INDEX_STATUS_SECTION,
    METADATA_SECTION,
    MINIMUM_EVIDENCE_ITEMS,
    PERSONAL_PATH_PATTERNS,
    PHASE_STATES,
    PLACEHOLDER_VALUES,
    PROJECT_SLUG_PATTERN,
    RECORD_SCHEMA_VERSION,
    REMOTE_ACTION_PATTERNS,
    REVIEW_ARTIFACTS,
    REVIEW_ROUTE_STRENGTHS,
    REVIEW_VERDICTS,
    SHIP_AUTHORIZATION_STATES,
    TASK_ID_PATTERN,
    TASK_LEVELS,
)


TOP_LEVEL_KEYS = (
    "schema_version",
    "task_id",
    "level",
    "project",
    "origin",
    "index_identity",
    "artifacts",
)

# The four identity fields the generator derives from the dossier path. A
# record that supplies one of them is trying to become a second authority.
DERIVED_INDEX_FIELDS = (
    "Task ID",
    "Task level",
    "Project",
    "Canonical receipt path",
)

RECORDED_INDEX_FIELDS = tuple(
    label for label in INDEX_IDENTITY_FIELDS if label not in DERIVED_INDEX_FIELDS
)

ARTIFACT_KEYS = (
    "version",
    "origin",
    "phase_state",
    "applicability",
    "applicability_rationale",
    "authorship",
    "authoring_session",
    "effective_route",
    "effective_model",
    "effective_effort",
    "reviewing_session",
    "review_verdict",
    "fields",
    "sections",
    "claim",
    "evidence",
    "uncertainty",
)

# Every artifact key that renders as one backtick-wrapped metadata value.
NULLABLE_METADATA_KEYS = (
    "origin",
    "applicability_rationale",
    "authoring_session",
    "effective_route",
    "effective_model",
    "effective_effort",
    "reviewing_session",
    "review_verdict",
)

REQUIRED_METADATA_KEYS = ("phase_state", "applicability", "authorship")

# Provenance is recorded together or left null together.
PROVENANCE_KEYS = (
    "authoring_session",
    "effective_route",
    "effective_model",
    "effective_effort",
)

SECTION_KEYS = ("title", "body")

_FIELD_LINE = re.compile(r"^- [^:\n]+:")
_FENCE_LINE = re.compile(r"^\s*(?:```|~~~)")


class RecordFileError(Exception):
    """The record file is missing, unreadable, or not UTF-8 JSON text."""


class RecordError(Exception):
    """One or more record diagnostics. The record is refused, never repaired."""

    def __init__(self, diagnostics: Sequence[str]) -> None:
        self.diagnostics = tuple(diagnostics)
        super().__init__("; ".join(self.diagnostics))


@dataclass(frozen=True)
class SectionRecord:
    """One supplemental section: a title and its already-split rendered lines."""

    title: str
    body: tuple[str, ...]


@dataclass(frozen=True)
class ArtifactRecord:
    name: str
    version: int
    origin: str | None
    phase_state: str
    applicability: str
    applicability_rationale: str | None
    authorship: str
    authoring_session: str | None
    effective_route: str | None
    effective_model: str | None
    effective_effort: str | None
    reviewing_session: str | None
    review_verdict: str | None
    fields: Mapping[str, str]
    sections: tuple[SectionRecord, ...]
    claim: str
    evidence: tuple[str, ...]
    uncertainty: tuple[str, ...]


@dataclass(frozen=True)
class TaskRecord:
    schema_version: int
    task_id: str
    level: str
    project: str
    origin: str
    index_identity: Mapping[str, Any]
    artifacts: Mapping[str, ArtifactRecord]

    def effective_origin(self, name: str) -> str:
        """Return the origin an artifact renders, inheriting the record's own."""
        recorded = self.artifacts[name].origin
        return self.origin if recorded is None else recorded


def _reject_duplicate_keys(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    """Refuse a repeated key at any depth.

    ``json.loads`` keeps the last duplicate silently, so a crafted record could
    show a reviewer one verdict and hand the loader another.
    """
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r} in the record")
        result[key] = value
    return result


def _is_placeholder(value: str) -> bool:
    text = value.strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        text = text[1:-1].strip()
    return text.lower() in PLACEHOLDER_VALUES or bool(re.fullmatch(r"<[^>]+>", text))


def _has_control(value: str, *, allow_line_feed: bool = False) -> str | None:
    for character in value:
        if character == "\n" and allow_line_feed:
            continue
        if ord(character) < 32 or ord(character) == 127:
            return character
    return None


class _Loader:
    """Accumulate every diagnostic instead of stopping at the first one."""

    def __init__(self, task_id: str, level: str, project: str) -> None:
        self.task_id = task_id
        self.level = level
        self.project = project
        self.diagnostics: list[str] = []

    # -- diagnostics ---------------------------------------------------

    def fail(self, locator: str, message: str) -> None:
        self.diagnostics.append(f"{locator}: {message}")

    def exact_type(self, locator: str, value: Any, expected: type) -> bool:
        if type(value) is not expected:
            self.fail(
                locator,
                f"must be exactly {expected.__name__}, found "
                f"{type(value).__name__}",
            )
            return False
        return True

    def exact_keys(self, locator: str, value: Any, expected: Sequence[str]) -> bool:
        if not self.exact_type(locator, value, dict):
            return False
        unknown = sorted(set(value) - set(expected))
        missing = sorted(set(expected) - set(value))
        if unknown:
            self.fail(locator, f"unknown key(s): {unknown}")
        if missing:
            self.fail(locator, f"missing key(s): {missing}")
        return not unknown and not missing

    # -- position classes ----------------------------------------------

    def backtick_value(self, locator: str, value: Any) -> str | None:
        """A value the renderer wraps in a code span."""
        if not self.exact_type(locator, value, str):
            return None
        for forbidden, label in (("`", "backtick"), ("|", "pipe"), ("\n", "newline")):
            if forbidden in value:
                self.fail(locator, f"backtick-wrapped values must not contain a {label}")
                return None
        control = _has_control(value)
        if control is not None:
            self.fail(locator, f"control character {control!r} is forbidden")
            return None
        self.personal_paths(locator, value)
        return value

    def free_text(self, locator: str, value: Any) -> str | None:
        """A value the renderer emits as one line of free text."""
        if not self.exact_type(locator, value, str):
            return None
        if "\n" in value:
            self.fail(locator, "must be a single line; a line feed is forbidden")
            return None
        control = _has_control(value)
        if control is not None:
            self.fail(locator, f"control character {control!r} is forbidden")
            return None
        if not self._safe_line(locator, value):
            return None
        self.personal_paths(locator, value)
        return value

    def body_line(self, locator: str, value: Any) -> str | None:
        """A `sections[].body[]` element: exactly one rendered line."""
        if not self.exact_type(locator, value, str):
            return None
        if "\n" in value:
            self.fail(
                locator,
                "a body element is exactly one rendered line; an embedded line "
                "feed is forbidden",
            )
            return None
        control = _has_control(value)
        if control is not None:
            self.fail(locator, f"control character {control!r} is forbidden")
            return None
        if not self._safe_line(locator, value):
            return None
        if _FIELD_LINE.match(value):
            self.fail(locator, "must not render as a '- <label>:' field line")
            return None
        self.personal_paths(locator, value)
        return value

    def multi_line(self, locator: str, value: Any) -> str | None:
        """`claim` is the only multi-line class; every line is checked."""
        if not self.exact_type(locator, value, str):
            return None
        control = _has_control(value, allow_line_feed=True)
        if control is not None:
            self.fail(locator, f"control character {control!r} is forbidden")
            return None
        for number, line in enumerate(value.split("\n"), start=1):
            where = f"{locator}[line {number}]"
            if not self._safe_line(where, line):
                return None
            if _FIELD_LINE.match(line):
                self.fail(where, "must not render as a '- <label>:' field line")
                return None
            if _FENCE_LINE.match(line):
                self.fail(where, "must not open or close a fenced block")
                return None
        self.personal_paths(locator, value)
        return value

    def _safe_line(self, locator: str, line: str) -> bool:
        if line.startswith("#"):
            self.fail(locator, "must not start with '#'; it would render a heading")
            return False
        stripped = line.strip()
        if len(stripped) >= 2 and stripped.startswith("|") and stripped.endswith("|"):
            self.fail(locator, "must not render as a table row")
            return False
        return True

    def personal_paths(self, locator: str, value: str) -> None:
        for pattern in PERSONAL_PATH_PATTERNS:
            match = pattern.search(value)
            if match:
                self.fail(
                    locator,
                    f"personal or home path is forbidden: {match.group(0)!r}",
                )
                return

    def concrete(self, locator: str, value: str | None) -> None:
        if value is not None and _is_placeholder(value):
            self.fail(
                locator,
                "must record a concrete value; a placeholder is not a value",
            )

    # -- structure -----------------------------------------------------

    def load(self, payload: Any) -> TaskRecord | None:
        if not self.exact_keys("record", payload, TOP_LEVEL_KEYS):
            return None

        if self.exact_type("schema_version", payload["schema_version"], int):
            if payload["schema_version"] != RECORD_SCHEMA_VERSION:
                self.fail(
                    "schema_version",
                    f"must be {RECORD_SCHEMA_VERSION}, found "
                    f"{payload['schema_version']}",
                )

        task_id = self.backtick_value("task_id", payload["task_id"])
        if task_id is not None:
            if not TASK_ID_PATTERN.fullmatch(task_id):
                self.fail("task_id", f"must be a stable task ID, found {task_id!r}")
            elif task_id != self.task_id:
                self.fail(
                    "task_id",
                    f"must equal the requested {self.task_id!r}, found {task_id!r}",
                )

        level = self.backtick_value("level", payload["level"])
        if level is not None:
            if level not in TASK_LEVELS:
                self.fail("level", f"must be one of {sorted(TASK_LEVELS)}")
            elif level != self.level:
                self.fail(
                    "level",
                    f"must equal the requested {self.level!r}, found {level!r}",
                )

        project = self.backtick_value("project", payload["project"])
        if project is not None:
            if not PROJECT_SLUG_PATTERN.fullmatch(project):
                self.fail("project", "must be a lowercase hyphenated slug")
            elif project != self.project:
                self.fail(
                    "project",
                    f"must equal the requested {self.project!r}, found {project!r}",
                )

        origin = self.backtick_value("origin", payload["origin"])
        self.concrete("origin", origin)

        identity = self._load_identity(payload["index_identity"])
        artifacts = self._load_artifacts(payload["artifacts"])

        if self.diagnostics:
            return None

        record = TaskRecord(
            schema_version=payload["schema_version"],
            task_id=task_id,  # type: ignore[arg-type]
            level=level,  # type: ignore[arg-type]
            project=project,  # type: ignore[arg-type]
            origin=origin,  # type: ignore[arg-type]
            index_identity=identity,  # type: ignore[arg-type]
            artifacts=artifacts,  # type: ignore[arg-type]
        )
        self._cross_record(record)
        self._level_gates(record)
        return None if self.diagnostics else record

    def _load_identity(self, value: Any) -> dict[str, Any] | None:
        locator = "index_identity"
        if type(value) is not dict:
            self.exact_type(locator, value, dict)
            return None
        supplied = sorted(set(value) & set(DERIVED_INDEX_FIELDS))
        if supplied:
            self.fail(
                locator,
                f"the generator derives {supplied}; a record must not supply them",
            )
        if not self.exact_keys(locator, value, RECORDED_INDEX_FIELDS):
            return None

        identity: dict[str, Any] = {}
        for label in RECORDED_INDEX_FIELDS:
            where = f"{locator}.{label}"
            item = value[label]
            if item is None:
                identity[label] = None
                continue
            if label == "Accepted plan version":
                if self.exact_type(where, item, int):
                    if item < 1:
                        self.fail(where, "must be a positive integer")
                    identity[label] = item
                continue
            text = self.backtick_value(where, item)
            self.concrete(where, text)
            identity[label] = text

        memory = identity.get("Project memory path")
        if type(memory) is not str:
            self.fail(f"{locator}.Project memory path", "must be a recorded string")
        else:
            pure = PurePosixPath(memory)
            unsafe = (
                pure.is_absolute()
                or ".." in pure.parts
                or "\\" in memory
                or (pure.parts and pure.parts[0].startswith("~"))
            )
            if unsafe:
                self.fail(
                    f"{locator}.Project memory path",
                    "must be a safe repository-relative path",
                )
            elif pure.name not in CANONICAL_MEMORY_FILES:
                self.fail(
                    f"{locator}.Project memory path",
                    f"must be one of {sorted(CANONICAL_MEMORY_FILES)}, found "
                    f"{pure.name!r}",
                )

        strength = identity.get("Review route strength")
        if strength not in REVIEW_ROUTE_STRENGTHS:
            self.fail(
                f"{locator}.Review route strength",
                f"must be one of {sorted(REVIEW_ROUTE_STRENGTHS)}, found "
                f"{strength!r}",
            )
        else:
            override = identity.get("Review route override")
            if strength == "stronger" and override is None:
                self.fail(
                    f"{locator}.Review route override",
                    "a stronger reviewer requires the documented one-off override",
                )
            if strength == "routine" and override is not None:
                self.fail(
                    f"{locator}.Review route override",
                    "routine review strength must leave the override null",
                )

        authorization = identity.get("Ship authorization")
        if authorization not in SHIP_AUTHORIZATION_STATES:
            self.fail(
                f"{locator}.Ship authorization",
                f"must be one of {sorted(SHIP_AUTHORIZATION_STATES)}, found "
                f"{authorization!r}",
            )
        else:
            evidence = identity.get("Ship authorization evidence")
            if authorization == "user-authorized" and evidence is None:
                self.fail(
                    f"{locator}.Ship authorization evidence",
                    "authorized ship requires recorded user authorization evidence",
                )
            if authorization == "not-requested" and evidence is not None:
                self.fail(
                    f"{locator}.Ship authorization evidence",
                    "unrequested ship must leave the authorization evidence null",
                )
        return identity

    def _load_artifacts(self, value: Any) -> dict[str, ArtifactRecord] | None:
        if not self.exact_keys("artifacts", value, ARTIFACTS):
            return None
        artifacts: dict[str, ArtifactRecord] = {}
        for name in ARTIFACTS:
            artifact = self._load_artifact(name, value[name])
            if artifact is not None:
                artifacts[name] = artifact
        return artifacts

    def _load_artifact(self, name: str, value: Any) -> ArtifactRecord | None:
        locator = f"artifacts.{name}"
        if not self.exact_keys(locator, value, ARTIFACT_KEYS):
            return None

        version = None
        if self.exact_type(f"{locator}.version", value["version"], int):
            version = value["version"]
            if version < 1:
                self.fail(f"{locator}.version", "must be a positive integer")

        metadata: dict[str, str | None] = {}
        for key in NULLABLE_METADATA_KEYS:
            where = f"{locator}.{key}"
            item = value[key]
            if item is None:
                metadata[key] = None
                continue
            text = self.backtick_value(where, item)
            self.concrete(where, text)
            metadata[key] = text
        for key in REQUIRED_METADATA_KEYS:
            where = f"{locator}.{key}"
            text = self.backtick_value(where, value[key])
            self.concrete(where, text)
            metadata[key] = text

        phase = metadata.get("phase_state")
        if phase not in PHASE_STATES:
            self.fail(
                f"{locator}.phase_state",
                f"must be one of {sorted(PHASE_STATES)}, found {phase!r}",
            )
        applicability = metadata.get("applicability")
        if applicability not in APPLICABILITY_STATES:
            self.fail(
                f"{locator}.applicability",
                f"must be one of {sorted(APPLICABILITY_STATES)}, found "
                f"{applicability!r}",
            )
        if (phase == "not-required") != (applicability == "not-required"):
            self.fail(
                f"{locator}.phase_state",
                "phase state 'not-required' and applicability 'not-required' "
                "must be declared together",
            )
        rationale = metadata.get("applicability_rationale")
        if applicability == "not-required" and rationale is None:
            self.fail(
                f"{locator}.applicability_rationale",
                "'not-required' requires a concrete rationale",
            )
        if applicability == "required" and rationale is not None:
            self.fail(
                f"{locator}.applicability_rationale",
                "required artifacts must leave the rationale null",
            )

        authorship = metadata.get("authorship")
        if authorship not in AUTHORSHIP_KINDS:
            self.fail(
                f"{locator}.authorship",
                f"must be one of {sorted(AUTHORSHIP_KINDS)}, found {authorship!r}",
            )
        else:
            for key in PROVENANCE_KEYS:
                recorded = metadata.get(key)
                if authorship == "model" and recorded is None:
                    self.fail(
                        f"{locator}.{key}",
                        "model-authored artifacts must record the effective "
                        "session, route, model, and effort",
                    )
                if authorship == "human" and recorded is not None:
                    self.fail(
                        f"{locator}.{key}",
                        "human-authored artifacts must leave model provenance null",
                    )

        verdict = metadata.get("review_verdict")
        if verdict is not None and verdict not in REVIEW_VERDICTS:
            self.fail(
                f"{locator}.review_verdict",
                f"must be one of {sorted(REVIEW_VERDICTS)} or null, found "
                f"{verdict!r}",
            )
        if verdict is not None and metadata.get("reviewing_session") is None:
            self.fail(
                f"{locator}.reviewing_session",
                "a review verdict requires the reviewing session identity",
            )
        if name in REVIEW_ARTIFACTS and phase == "passed":
            if verdict is None:
                self.fail(
                    f"{locator}.review_verdict",
                    f"a passed review requires one of {sorted(REVIEW_VERDICTS)}",
                )
            if metadata.get("reviewing_session") is None:
                self.fail(
                    f"{locator}.reviewing_session",
                    "review artifacts require the reviewing session identity",
                )

        origin = metadata.get("origin")
        if name == "request":
            effective = origin
            if effective is not None and effective != "user-request":
                self.fail(
                    f"{locator}.origin",
                    "request provenance origin must render 'user-request', found "
                    f"{effective!r}",
                )

        fields = self._load_fields(name, locator, value["fields"])
        sections = self._load_sections(name, locator, value["sections"])

        claim = self.multi_line(f"{locator}.claim", value["claim"])
        self.concrete(f"{locator}.claim", claim)
        evidence = self._load_items(f"{locator}.evidence", value["evidence"])
        uncertainty = self._load_items(f"{locator}.uncertainty", value["uncertainty"])

        self._evidence_depth(locator, phase, applicability, evidence)
        if name == "pr-desc":
            self._pr_description(locator, fields, claim, evidence, uncertainty, sections)
        if name == "request":
            self._request_provenance(locator, fields)

        if self.diagnostics:
            return None
        return ArtifactRecord(
            name=name,
            version=version,  # type: ignore[arg-type]
            origin=origin,
            phase_state=metadata["phase_state"],  # type: ignore[index]
            applicability=metadata["applicability"],  # type: ignore[index]
            applicability_rationale=rationale,
            authorship=metadata["authorship"],  # type: ignore[index]
            authoring_session=metadata["authoring_session"],
            effective_route=metadata["effective_route"],
            effective_model=metadata["effective_model"],
            effective_effort=metadata["effective_effort"],
            reviewing_session=metadata["reviewing_session"],
            review_verdict=verdict,
            fields=fields or {},
            sections=sections or (),
            claim=claim,  # type: ignore[arg-type]
            evidence=evidence or (),
            uncertainty=uncertainty or (),
        )

    def _load_fields(
        self, name: str, locator: str, value: Any
    ) -> dict[str, str] | None:
        where = f"{locator}.fields"
        # The index projects its identity from `index_identity`, so its own
        # `fields` map stays empty; a record must not open a second channel.
        expected: tuple[str, ...] = ()
        if name != "index":
            for _, labels in ARTIFACT_EXTRA_SECTIONS.get(name, ()):
                expected += tuple(labels)
        if not self.exact_keys(where, value, expected):
            return None
        fields: dict[str, str] = {}
        for label in expected:
            text = self.backtick_value(f"{where}.{label}", value[label])
            self.concrete(f"{where}.{label}", text)
            if text is not None:
                fields[label] = text
        return fields

    def _load_sections(
        self, name: str, locator: str, value: Any
    ) -> tuple[SectionRecord, ...] | None:
        where = f"{locator}.sections"
        if not self.exact_type(where, value, list):
            return None
        if name == "index" and value:
            self.fail(
                where,
                "the index is a projection and may not declare supplemental "
                "sections",
            )
            return None

        reserved = {METADATA_SECTION, INDEX_STATUS_SECTION, *BODY_SECTIONS}
        for section, _ in ARTIFACT_EXTRA_SECTIONS.get(name, ()):
            reserved.add(section)

        sections: list[SectionRecord] = []
        seen: set[str] = set()
        for position, item in enumerate(value):
            item_where = f"{where}[{position}]"
            if not self.exact_keys(item_where, item, SECTION_KEYS):
                continue
            title = self.free_text(f"{item_where}.title", item["title"])
            self.concrete(f"{item_where}.title", title)
            if title is not None:
                if title in reserved:
                    self.fail(
                        f"{item_where}.title",
                        f"collides with the required section {title!r}",
                    )
                elif title in seen:
                    self.fail(f"{item_where}.title", "section titles must be unique")
                seen.add(title)
            body_value = item["body"]
            if not self.exact_type(f"{item_where}.body", body_value, list):
                continue
            body: list[str] = []
            for index, line in enumerate(body_value):
                rendered = self.body_line(f"{item_where}.body[{index}]", line)
                if rendered is not None:
                    body.append(rendered)
            if title is not None:
                sections.append(SectionRecord(title=title, body=tuple(body)))
        return tuple(sections)

    def _load_items(self, locator: str, value: Any) -> tuple[str, ...] | None:
        if not self.exact_type(locator, value, list):
            return None
        if not value:
            self.fail(locator, "must record at least one concrete item")
            return None
        items: list[str] = []
        for position, item in enumerate(value):
            where = f"{locator}[{position}]"
            text = self.free_text(where, item)
            self.concrete(where, text)
            if text is not None:
                items.append(text)
        return tuple(items)

    def _evidence_depth(
        self,
        locator: str,
        phase: str | None,
        applicability: str | None,
        evidence: tuple[str, ...] | None,
    ) -> None:
        """Mirror the validator's evidence-depth rule exactly.

        'not-required' is a recorded decision, not an exemption: it still needs
        one concrete evidence item. A passed artifact meets its level floor.
        """
        count = len(evidence or ())
        if applicability == "not-required":
            if count < 1:
                self.fail(
                    f"{locator}.evidence",
                    "'not-required' requires concrete evidence; a missing "
                    "artifact is never evidence",
                )
            return
        if phase != "passed":
            return
        minimum = MINIMUM_EVIDENCE_ITEMS.get(self.level, 1)
        if count < minimum:
            self.fail(
                f"{locator}.evidence",
                f"level {self.level} requires at least {minimum} concrete "
                f"evidence item(s), found {count}",
            )

    def _request_provenance(self, locator: str, fields: Mapping[str, str] | None) -> None:
        recorded = fields or {}
        if recorded.get("Redaction applied", "").lower() != "yes":
            self.fail(
                f"{locator}.fields.Redaction applied",
                "recorded request provenance must be redacted before storage",
            )
        if recorded.get("Mutability", "").lower() != "immutable":
            self.fail(
                f"{locator}.fields.Mutability",
                "request provenance is read-only; amendments are appended as "
                "new versioned artifacts",
            )

    def _pr_description(
        self,
        locator: str,
        fields: Mapping[str, str] | None,
        claim: str | None,
        evidence: tuple[str, ...] | None,
        uncertainty: tuple[str, ...] | None,
        sections: tuple[SectionRecord, ...] | None,
    ) -> None:
        recorded = fields or {}
        if recorded.get("Remote action authorized", "").lower() != "no":
            self.fail(
                f"{locator}.fields.Remote action authorized",
                "PR text never authorizes remote action",
            )
        texts = [claim or ""]
        texts.extend(evidence or ())
        texts.extend(uncertainty or ())
        texts.extend(recorded.values())
        for section in sections or ():
            texts.append(section.title)
            texts.extend(section.body)
        for text in texts:
            for pattern in REMOTE_ACTION_PATTERNS:
                match = pattern.search(text)
                if match:
                    self.fail(
                        f"{locator}",
                        "PR text must not instruct remote mutation: "
                        f"{match.group(0)!r}",
                    )
                    return

    def _cross_record(self, record: TaskRecord) -> None:
        """Four consistency refusals. None of them derives a value."""
        plan = record.artifacts["plan"]
        plan_id = plan.fields.get("Plan ID")
        plan_status = plan.fields.get("Plan status", "").lower()

        if plan_status == "accepted":
            accepted_id = record.index_identity.get("Accepted plan ID")
            accepted_version = record.index_identity.get("Accepted plan version")
            if accepted_id != plan_id:
                self.fail(
                    "index_identity.Accepted plan ID",
                    f"must equal artifacts.plan.fields['Plan ID'] {plan_id!r}, "
                    f"found {accepted_id!r}",
                )
            if accepted_version != plan.version:
                self.fail(
                    "index_identity.Accepted plan version",
                    f"must equal artifacts.plan.version {plan.version!r}, found "
                    f"{accepted_version!r}",
                )

        for name in REVIEW_ARTIFACTS:
            review = record.artifacts[name]
            reviewed_version = review.fields.get("Reviewed plan version")
            if reviewed_version != str(plan.version):
                self.fail(
                    f"artifacts.{name}.fields.Reviewed plan version",
                    f"must equal the decimal string {str(plan.version)!r} of "
                    f"artifacts.plan.version, found {reviewed_version!r}",
                )
            reviewed_id = review.fields.get("Reviewed plan ID")
            if reviewed_id != plan_id:
                self.fail(
                    f"artifacts.{name}.fields.Reviewed plan ID",
                    f"must equal artifacts.plan.fields['Plan ID'] {plan_id!r}, "
                    f"found {reviewed_id!r}",
                )
            for label, session in (
                ("reviewing_session", review.reviewing_session),
                ("authoring_session", review.authoring_session),
            ):
                if session is not None and session == plan.authoring_session:
                    self.fail(
                        f"artifacts.{name}.{label}",
                        f"{name} requires a session independent of the plan author",
                    )

    def _level_gates(self, record: TaskRecord) -> None:
        """Level changes gates, never artifact presence."""
        strength = record.index_identity.get("Review route strength")
        if self.level == "2" and strength != "stronger":
            self.fail(
                "index_identity.Review route strength",
                "level 2 requires a documented stronger reviewer",
            )
        authorization = record.index_identity.get("Ship authorization")
        if self.level in {"0", "1"} and authorization != "not-requested":
            self.fail(
                "index_identity.Ship authorization",
                f"level {self.level} does not gate a ship; authorization must "
                "be 'not-requested'",
            )


def load_record_text(
    text: str, *, task_id: str, level: str, project: str
) -> TaskRecord:
    """Load and fully validate a record already read into memory."""
    try:
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except ValueError as error:
        raise RecordError((f"record: {error}",)) from None

    loader = _Loader(task_id, level, project)
    record = loader.load(payload)
    if record is None:
        raise RecordError(loader.diagnostics or ("record: refused",))
    return record


def load_record(path, *, task_id: str, level: str, project: str) -> TaskRecord:
    """Read one UTF-8 JSON record file and return it fully validated.

    A missing or unreadable file raises ``RecordFileError``; malformed or
    refused content raises ``RecordError`` carrying every diagnostic.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise RecordFileError(f"cannot read record {path}: {error}") from None
    return load_record_text(text, task_id=task_id, level=level, project=project)


__all__ = [
    "ARTIFACT_KEYS",
    "ArtifactRecord",
    "DERIVED_INDEX_FIELDS",
    "RECORDED_INDEX_FIELDS",
    "RecordError",
    "RecordFileError",
    "SectionRecord",
    "TOP_LEVEL_KEYS",
    "TaskRecord",
    "load_record",
    "load_record_text",
]
