"""Exact map and leaf grammars, including the Examples line-state machine.

The parser is authority-neutral. It converts raw file bytes into the exact
records Design section 5 describes and never decides selection, freshness, or
rule authority; the resolver owns every one of those. Raw bytes are hashed by
the caller, so this module reports the normalized payload accounting only.

Every grammar token below is copied literally from the design. A document that
deviates in any byte raises :class:`MarkdownError` carrying one closed
Diagnostic registry code, so the resolver never invents a code of its own.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .model import (
    EVIDENCE_DECLARATION_MAX,
    FREE_TEXT_BYTE_MAX,
    MAP_ROW_LIMIT,
    MAP_ROW_SELECTOR_LIMIT,
    is_context_id,
    is_date,
    is_nfc,
    is_normalized_relative_path,
    is_rule_id,
    is_selector,
)

# ---------------------------------------------------------------------------
# Literal grammar tokens, copied byte for byte from Design section 5
# ---------------------------------------------------------------------------

#: The one map-only sentence every README carries after its title.
MAP_ONLY_SENTENCE = "Map only. This README contains no normative rules."

MAP_METADATA_HEADING = "## Map metadata"
CONTEXTS_HEADING = "## Contexts"
CONTEXTS_TABLE_HEADER = "| Context ID | Rule path | Applies to |"
CONTEXTS_TABLE_SEPARATOR = "| --- | --- | --- |"

RULE_METADATA_HEADING = "## Rule metadata"
SCOPE_HEADING = "## Scope"
RULES_HEADING = "## Rules"
OVERRIDES_HEADING = "## Overrides"
VERIFICATION_HEADING = "## Verification"
EXCEPTIONS_HEADING = "## Exceptions"
EXAMPLES_HEADING = "## Examples"

#: The exact bare sentinel that replaces a whole Contexts table or the whole
#: Examples section, and the exact bullet sentinel of Overrides/Exceptions.
NONE_LINE = "None."
NONE_BULLET = "- None."
EVIDENCE_NONE_LINE = "- Evidence: None."
EXAMPLES_LABEL = "Example only."

#: Exactly three backticks. This line always closes a payload and therefore can
#: never be represented as payload data.
FENCE = "```"

#: The literal separator between backtick-wrapped selectors or evidence paths.
LIST_SEPARATOR = "; "

#: The project-relative prefix every map row path begins with.
ROW_PATH_PREFIX = "techstacks/"

#: The exact nested-map basename; every other row path names a leaf.
MAP_BASENAME = "README.md"

#: The dot selector contains every other selector.
DOT_SELECTOR = "."


# ---------------------------------------------------------------------------
# Numeric grammar bounds
# ---------------------------------------------------------------------------

TITLE_BYTE_MAX = 128
SCOPE_BULLET_MAX = 16
RULE_BULLET_MAX = 32
OVERRIDE_BULLET_MAX = 32
VERIFICATION_BULLET_MAX = 16
EXCEPTION_BULLET_MAX = 16
REVIEW_WITHIN_DAYS_MIN = 1
REVIEW_WITHIN_DAYS_MAX = 3650
EXAMPLE_FENCE_MAX = 8
PAYLOAD_LINE_BYTE_MAX = 4096
PAYLOAD_AGGREGATE_BYTE_MAX = 8192

#: The five Examples line states of Design section 5.
STATE_EXPECT_LABEL = "EXPECT_LABEL"
STATE_EXPECT_OPEN = "EXPECT_OPEN"
STATE_PAYLOAD = "PAYLOAD"
STATE_AFTER_CLOSE = "AFTER_CLOSE"
STATE_DONE = "DONE"

EXAMPLES_STATES = (
    STATE_EXPECT_LABEL,
    STATE_EXPECT_OPEN,
    STATE_PAYLOAD,
    STATE_AFTER_CLOSE,
    STATE_DONE,
)


# ---------------------------------------------------------------------------
# Failure surface
# ---------------------------------------------------------------------------


class MarkdownError(Exception):
    """One grammar failure carrying its exact Diagnostic registry code.

    ``code`` is ``INVALID_MAP``, ``MAP_ROW_LIMIT``, ``SELECTOR_LIMIT``, or
    ``INVALID_LEAF``. ``context_id`` is present only for ``SELECTOR_LIMIT``,
    whose registry field class requires both a path and a Context ID; the
    caller supplies the path because only it knows which file it read.
    """

    def __init__(self, code: str, *, context_id: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.context_id = context_id


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MapRow:
    """One Contexts-table row and its normalized selector union."""

    context_id: str
    rule_path: str
    selectors: tuple[str, ...]
    applies_to: tuple[str, ...]

    @property
    def is_map(self) -> bool:
        """Return True when the row names a nested map rather than a leaf."""

        return self.rule_path.endswith("/" + MAP_BASENAME)


@dataclass(frozen=True)
class ParsedMap:
    """One map-only README: its title, metadata Context ID, and sorted rows."""

    title: str
    context_id: str
    rows: tuple[MapRow, ...]


@dataclass(frozen=True)
class RuleRecord:
    """One normative rule bullet and its exact normalized prose."""

    rule_id: str
    statement: str


@dataclass(frozen=True)
class OverrideRecord:
    """One declared override edge from this leaf to a dominating context."""

    rule_id: str
    target_context_id: str
    reason: str


@dataclass(frozen=True)
class ExampleFence:
    """One Examples fence and its normalized payload byte count."""

    language: str
    payload_bytes: int


@dataclass(frozen=True)
class ParsedLeaf:
    """One leaf rule file, parsed into its exact ordered sections."""

    title: str
    context_id: str
    reviewed_on: str
    review_within_days: int
    deprecated: bool
    deprecated_on: str | None
    deprecated_reason: str | None
    evidence: tuple[str, ...]
    scope: tuple[str, ...]
    rules: tuple[RuleRecord, ...]
    overrides: tuple[OverrideRecord, ...]
    verification: tuple[str, ...]
    exceptions: tuple[str, ...]
    examples: tuple[ExampleFence, ...]
    example_payload_bytes: int


# ---------------------------------------------------------------------------
# Selector algebra
# ---------------------------------------------------------------------------


def is_prefix_selector(value: str) -> bool:
    """Return True for a prefix selector: a normalized path plus one slash."""

    return isinstance(value, str) and value.endswith("/") and is_selector(value)


def selector_contains(container: str, member: str) -> bool:
    """Return True when ``container`` wholly contains ``member``.

    Dot contains every selector; an exact selector contains only itself; a
    prefix contains exact paths beneath it and prefixes equal to or below it.
    """

    if container == DOT_SELECTOR:
        return True
    if member == DOT_SELECTOR:
        return False
    if container.endswith("/"):
        return member == container or member.startswith(container)
    return member == container


def selectors_overlap(first: str, second: str) -> bool:
    """Return True when two selectors share at least one covered path."""

    return selector_contains(first, second) or selector_contains(second, first)


def unions_overlap(first: tuple[str, ...], second: tuple[str, ...]) -> bool:
    """Return True when any selector of one union overlaps the other union."""

    return any(
        selectors_overlap(left, right) for left in first for right in second
    )


def union_is_subset(inner: tuple[str, ...], outer: tuple[str, ...]) -> bool:
    """Return True when every selector of ``inner`` is contained by ``outer``."""

    return all(
        any(selector_contains(container, member) for container in outer)
        for member in inner
    )


def normalize_selectors(selectors: tuple[str, ...]) -> tuple[str, ...]:
    """Remove every selector wholly contained by another, then sort by bytes.

    Duplicates are rejected by the grammar before normalization, so a selector
    is dropped only when a strictly different selector of the same row covers
    it.
    """

    kept = [
        member
        for member in selectors
        if not any(
            container != member and selector_contains(container, member)
            for container in selectors
        )
    ]
    return tuple(sorted(set(kept), key=lambda value: value.encode("utf-8")))


# ---------------------------------------------------------------------------
# Shared normalization
# ---------------------------------------------------------------------------

_UTF8_BOM = b"\xef\xbb\xbf"

_TITLE_PREFIX = "# "
_ORDINARY_BULLET_PREFIX = "- "

_CONTEXT_ID_LINE = re.compile(r"^- Context ID: `(?P<value>[^`]*)`$")
_REVIEWED_ON_LINE = re.compile(r"^- Reviewed on: `(?P<value>[^`]*)`$")
_REVIEW_WITHIN_LINE = re.compile(r"^- Review within days: `(?P<value>[^`]*)`$")
_DEPRECATED_LINE = re.compile(r"^- Deprecated: `(?P<value>[^`]*)`$")
_EVIDENCE_LINE = re.compile(r"^- Evidence: (?P<value>.*)$")
_DEPRECATED_YES = re.compile(r"^yes: (?P<date>\d{4}-\d{2}-\d{2}): (?P<reason>.+)$")

#: A Contexts row. Cells may contain no pipe, backslash, or backtick.
_MAP_ROW = re.compile(
    r"^\| (?P<context_id>[^|\\`]+) \| `(?P<rule_path>[^|\\`]+)` \| (?P<selectors>[^|\\]+) \|$"
)
_BACKTICKED = re.compile(r"^`(?P<value>[^`|\\]+)`$")
_RULE_BULLET = re.compile(r"^- `(?P<rule_id>[^`|\\]+)`: (?P<statement>.+)$")
_OVERRIDE_BULLET = re.compile(
    r"^- `(?P<rule_id>[^`|\\]+)` -> `(?P<target>[^`|\\]+)`: (?P<reason>.+)$"
)
_FENCE_OPEN = re.compile(r"^```(?P<language>[a-z][a-z0-9-]{0,31})$")


def _byte_length(value: str) -> int:
    return len(value.encode("utf-8"))


def _is_prose(value: str) -> bool:
    """Return True for one ordinary NFC prose token on one physical line."""

    if not value or not 1 <= _byte_length(value) <= FREE_TEXT_BYTE_MAX:
        return False
    if value != value.strip():
        return False
    if not is_nfc(value):
        return False
    for character in value:
        if character in "`|<>":
            return False
        if unicodedata.category(character)[0] == "C":
            return False
    return True


def _is_title(value: str) -> bool:
    if not value or not 1 <= _byte_length(value) <= TITLE_BYTE_MAX:
        return False
    if value != value.strip() or not is_nfc(value):
        return False
    return all(unicodedata.category(character)[0] != "C" for character in value)


def normalize_document(raw: bytes, code: str) -> tuple[str, ...]:
    """Decode one raw file and return its normalized line array.

    Strict UTF-8, no BOM, and no NUL are required. Every CRLF pair becomes one
    LF and any remaining bare CR is rejected. The document ends with exactly
    one terminal LF. These four rules precede line-state parsing and therefore
    apply inside an Examples payload as well as outside one.
    """

    if raw.startswith(_UTF8_BOM):
        raise MarkdownError(code)
    if b"\x00" in raw:
        raise MarkdownError(code)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise MarkdownError(code) from None
    text = text.replace("\r\n", "\n")
    if "\r" in text:
        raise MarkdownError(code)
    if not text.endswith("\n") or text.endswith("\n\n"):
        raise MarkdownError(code)
    return tuple(text[:-1].split("\n"))


def _check_outside_line(line: str, code: str) -> None:
    """Reject tabs, trailing whitespace, and indentation outside a payload."""

    if "\t" in line:
        raise MarkdownError(code)
    if line != line.rstrip():
        raise MarkdownError(code)
    if line.startswith(" "):
        raise MarkdownError(code)


class _Cursor:
    """A line cursor that rejects every unconsumed or unexpected line."""

    def __init__(self, lines: tuple[str, ...], code: str) -> None:
        self._lines = lines
        self._code = code
        self._index = 0

    @property
    def code(self) -> str:
        return self._code

    def fail(self) -> MarkdownError:
        return MarkdownError(self._code)

    def exhausted(self) -> bool:
        return self._index >= len(self._lines)

    def peek(self) -> str:
        if self.exhausted():
            raise self.fail()
        return self._lines[self._index]

    def take(self) -> str:
        """Return the next line after the outside-payload line-shape check."""

        line = self.peek()
        _check_outside_line(line, self._code)
        self._index += 1
        return line

    def take_raw(self) -> str:
        """Return the next line verbatim; only PAYLOAD uses this."""

        line = self.peek()
        self._index += 1
        return line

    def expect(self, literal: str) -> None:
        if self.take() != literal:
            raise self.fail()

    def expect_blank(self) -> None:
        if self.take() != "":
            raise self.fail()

    def require_end(self) -> None:
        if not self.exhausted():
            raise self.fail()


# ---------------------------------------------------------------------------
# Map grammar
# ---------------------------------------------------------------------------


def _parse_row(line: str, code: str) -> MapRow:
    match = _MAP_ROW.match(line)
    if match is None:
        raise MarkdownError(code)
    context_id = match.group("context_id")
    rule_path = match.group("rule_path")
    if not is_context_id(context_id):
        raise MarkdownError(code)
    if not is_normalized_relative_path(rule_path):
        raise MarkdownError(code)
    if not rule_path.startswith(ROW_PATH_PREFIX) or not rule_path.endswith(".md"):
        raise MarkdownError(code)
    basename = rule_path.rsplit("/", 1)[-1]
    if basename == MAP_BASENAME:
        # A row names a nested map, never the root README it lives beside.
        if rule_path.count("/") < 2:
            raise MarkdownError(code)
    selectors = []
    for token in match.group("selectors").split(LIST_SEPARATOR):
        selector_match = _BACKTICKED.match(token)
        if selector_match is None:
            raise MarkdownError(code)
        selectors.append(selector_match.group("value"))
    if len(selectors) > MAP_ROW_SELECTOR_LIMIT:
        raise MarkdownError("SELECTOR_LIMIT", context_id=context_id)
    if len(set(selectors)) != len(selectors):
        raise MarkdownError(code)
    for selector in selectors:
        if not is_selector(selector):
            raise MarkdownError(code)
    return MapRow(
        context_id=context_id,
        rule_path=rule_path,
        selectors=tuple(selectors),
        applies_to=normalize_selectors(tuple(selectors)),
    )


def _row_sort_key(row: MapRow) -> tuple[bytes, bytes, tuple[bytes, ...]]:
    return (
        row.context_id.encode("utf-8"),
        row.rule_path.encode("utf-8"),
        tuple(selector.encode("utf-8") for selector in row.applies_to),
    )


def parse_map(raw: bytes) -> ParsedMap:
    """Parse one map-only README. Rows are data, never precedence."""

    code = "INVALID_MAP"
    cursor = _Cursor(normalize_document(raw, code), code)
    title = cursor.take()
    if not title.startswith(_TITLE_PREFIX) or not _is_title(title[len(_TITLE_PREFIX) :]):
        raise cursor.fail()
    cursor.expect_blank()
    cursor.expect(MAP_ONLY_SENTENCE)
    cursor.expect_blank()
    cursor.expect(MAP_METADATA_HEADING)
    cursor.expect_blank()
    metadata = _CONTEXT_ID_LINE.match(cursor.take())
    if metadata is None or not is_context_id(metadata.group("value"), allow_root=True):
        raise cursor.fail()
    cursor.expect_blank()
    cursor.expect(CONTEXTS_HEADING)
    cursor.expect_blank()
    if cursor.peek() == NONE_LINE:
        cursor.take()
        cursor.require_end()
        return ParsedMap(
            title=title[len(_TITLE_PREFIX) :],
            context_id=metadata.group("value"),
            rows=(),
        )
    cursor.expect(CONTEXTS_TABLE_HEADER)
    cursor.expect(CONTEXTS_TABLE_SEPARATOR)
    rows: list[MapRow] = []
    while not cursor.exhausted():
        rows.append(_parse_row(cursor.take(), code))
        if len(rows) > MAP_ROW_LIMIT:
            raise MarkdownError("MAP_ROW_LIMIT")
    if not rows:
        raise cursor.fail()
    identifiers = [row.context_id for row in rows]
    paths = [row.rule_path for row in rows]
    if len(set(identifiers)) != len(identifiers) or len(set(paths)) != len(paths):
        raise cursor.fail()
    return ParsedMap(
        title=title[len(_TITLE_PREFIX) :],
        context_id=metadata.group("value"),
        rows=tuple(sorted(rows, key=_row_sort_key)),
    )


# ---------------------------------------------------------------------------
# Leaf grammar
# ---------------------------------------------------------------------------


def _take_section(cursor: _Cursor, heading: str) -> None:
    cursor.expect_blank()
    cursor.expect(heading)
    cursor.expect_blank()


def _parse_metadata(cursor: _Cursor) -> dict[str, object]:
    context_match = _CONTEXT_ID_LINE.match(cursor.take())
    if context_match is None or not is_context_id(context_match.group("value")):
        raise cursor.fail()
    reviewed_match = _REVIEWED_ON_LINE.match(cursor.take())
    if reviewed_match is None or not is_date(reviewed_match.group("value")):
        raise cursor.fail()
    within_match = _REVIEW_WITHIN_LINE.match(cursor.take())
    if within_match is None:
        raise cursor.fail()
    digits = within_match.group("value")
    if not digits.isdigit() or (len(digits) > 1 and digits.startswith("0")):
        raise cursor.fail()
    within = int(digits)
    if not REVIEW_WITHIN_DAYS_MIN <= within <= REVIEW_WITHIN_DAYS_MAX:
        raise cursor.fail()
    deprecated_match = _DEPRECATED_LINE.match(cursor.take())
    if deprecated_match is None:
        raise cursor.fail()
    declared = deprecated_match.group("value")
    deprecated_on: str | None = None
    deprecated_reason: str | None = None
    if declared == "no":
        deprecated = False
    else:
        yes_match = _DEPRECATED_YES.match(declared)
        if yes_match is None or not is_date(yes_match.group("date")):
            raise cursor.fail()
        if not _is_prose(yes_match.group("reason")):
            raise cursor.fail()
        deprecated = True
        deprecated_on = yes_match.group("date")
        deprecated_reason = yes_match.group("reason")
    evidence_line = cursor.take()
    evidence: tuple[str, ...] = ()
    if evidence_line != EVIDENCE_NONE_LINE:
        evidence_match = _EVIDENCE_LINE.match(evidence_line)
        if evidence_match is None:
            raise cursor.fail()
        paths: list[str] = []
        for token in evidence_match.group("value").split(LIST_SEPARATOR):
            path_match = _BACKTICKED.match(token)
            if path_match is None:
                raise cursor.fail()
            paths.append(path_match.group("value"))
        if not 1 <= len(paths) <= EVIDENCE_DECLARATION_MAX:
            raise cursor.fail()
        if len(set(paths)) != len(paths):
            raise cursor.fail()
        for path in paths:
            if not is_normalized_relative_path(path):
                raise cursor.fail()
        evidence = tuple(paths)
    return {
        "context_id": context_match.group("value"),
        "reviewed_on": reviewed_match.group("value"),
        "review_within_days": within,
        "deprecated": deprecated,
        "deprecated_on": deprecated_on,
        "deprecated_reason": deprecated_reason,
        "evidence": evidence,
    }


def _parse_ordinary_bullets(cursor: _Cursor, maximum: int) -> tuple[str, ...]:
    bullets: list[str] = []
    while not cursor.exhausted() and cursor.peek() != "":
        line = cursor.take()
        if not line.startswith(_ORDINARY_BULLET_PREFIX):
            raise cursor.fail()
        prose = line[len(_ORDINARY_BULLET_PREFIX) :]
        if prose == NONE_LINE or not _is_prose(prose):
            raise cursor.fail()
        bullets.append(prose)
        if len(bullets) > maximum:
            raise cursor.fail()
    if not bullets:
        raise cursor.fail()
    return tuple(bullets)


def _parse_rules(cursor: _Cursor) -> tuple[RuleRecord, ...]:
    rules: list[RuleRecord] = []
    while not cursor.exhausted() and cursor.peek() != "":
        match = _RULE_BULLET.match(cursor.take())
        if match is None:
            raise cursor.fail()
        rule_id = match.group("rule_id")
        statement = match.group("statement")
        if not is_rule_id(rule_id) or not _is_prose(statement):
            raise cursor.fail()
        rules.append(RuleRecord(rule_id=rule_id, statement=statement))
        if len(rules) > RULE_BULLET_MAX:
            raise cursor.fail()
    if not rules:
        raise cursor.fail()
    identifiers = [rule.rule_id for rule in rules]
    if len(set(identifiers)) != len(identifiers):
        raise cursor.fail()
    return tuple(rules)


def _parse_overrides(
    cursor: _Cursor, context_id: str, rules: tuple[RuleRecord, ...]
) -> tuple[OverrideRecord, ...]:
    if cursor.peek() == NONE_BULLET:
        cursor.take()
        return ()
    overrides: list[OverrideRecord] = []
    known = {rule.rule_id for rule in rules}
    while not cursor.exhausted() and cursor.peek() != "":
        match = _OVERRIDE_BULLET.match(cursor.take())
        if match is None:
            raise cursor.fail()
        rule_id = match.group("rule_id")
        target = match.group("target")
        reason = match.group("reason")
        if not is_rule_id(rule_id) or rule_id not in known:
            raise cursor.fail()
        if not is_context_id(target) or target == context_id:
            raise cursor.fail()
        if not _is_prose(reason):
            raise cursor.fail()
        overrides.append(
            OverrideRecord(rule_id=rule_id, target_context_id=target, reason=reason)
        )
        if len(overrides) > OVERRIDE_BULLET_MAX:
            raise cursor.fail()
    if not overrides:
        raise cursor.fail()
    pairs = [(item.rule_id, item.target_context_id) for item in overrides]
    if len(set(pairs)) != len(pairs):
        raise cursor.fail()
    return tuple(overrides)


def _parse_exceptions(cursor: _Cursor) -> tuple[str, ...]:
    if cursor.peek() == NONE_BULLET:
        cursor.take()
        return ()
    return _parse_ordinary_bullets(cursor, EXCEPTION_BULLET_MAX)


def _parse_examples(cursor: _Cursor) -> tuple[tuple[ExampleFence, ...], int]:
    """Run Design section 5's Examples line-state machine to DONE.

    Only a normalized line exactly equal to three backticks closes a payload,
    so every other line inside PAYLOAD is data and no outside-payload Markdown
    rejection applies to it.
    """

    state = STATE_EXPECT_LABEL
    fences: list[ExampleFence] = []
    aggregate = 0
    label = cursor.take()
    if label == NONE_LINE:
        cursor.require_end()
        return (), 0
    if label != EXAMPLES_LABEL:
        raise cursor.fail()
    cursor.expect_blank()
    state = STATE_EXPECT_OPEN
    while state != STATE_DONE:
        opening = _FENCE_OPEN.match(cursor.take())
        if opening is None:
            raise cursor.fail()
        state = STATE_PAYLOAD
        payload_bytes = 0
        closed = False
        while not cursor.exhausted():
            line = cursor.take_raw()
            if line == FENCE:
                closed = True
                break
            if _byte_length(line) > PAYLOAD_LINE_BYTE_MAX:
                raise cursor.fail()
            payload_bytes += _byte_length(line) + 1
            aggregate += _byte_length(line) + 1
            if aggregate > PAYLOAD_AGGREGATE_BYTE_MAX:
                raise cursor.fail()
        if not closed:
            raise cursor.fail()
        fences.append(
            ExampleFence(language=opening.group("language"), payload_bytes=payload_bytes)
        )
        if len(fences) > EXAMPLE_FENCE_MAX:
            raise cursor.fail()
        state = STATE_AFTER_CLOSE
        if cursor.exhausted():
            state = STATE_DONE
            continue
        cursor.expect_blank()
        state = STATE_EXPECT_OPEN
    return tuple(fences), aggregate


def parse_leaf(raw: bytes) -> ParsedLeaf:
    """Parse one leaf rule file in its exact ordered sections."""

    code = "INVALID_LEAF"
    cursor = _Cursor(normalize_document(raw, code), code)
    title = cursor.take()
    if not title.startswith(_TITLE_PREFIX) or not _is_title(title[len(_TITLE_PREFIX) :]):
        raise cursor.fail()
    _take_section(cursor, RULE_METADATA_HEADING)
    metadata = _parse_metadata(cursor)
    _take_section(cursor, SCOPE_HEADING)
    scope = _parse_ordinary_bullets(cursor, SCOPE_BULLET_MAX)
    _take_section(cursor, RULES_HEADING)
    rules = _parse_rules(cursor)
    _take_section(cursor, OVERRIDES_HEADING)
    overrides = _parse_overrides(cursor, str(metadata["context_id"]), rules)
    _take_section(cursor, VERIFICATION_HEADING)
    verification = _parse_ordinary_bullets(cursor, VERIFICATION_BULLET_MAX)
    _take_section(cursor, EXCEPTIONS_HEADING)
    exceptions = _parse_exceptions(cursor)
    _take_section(cursor, EXAMPLES_HEADING)
    examples, payload_bytes = _parse_examples(cursor)
    cursor.require_end()
    return ParsedLeaf(
        title=title[len(_TITLE_PREFIX) :],
        context_id=str(metadata["context_id"]),
        reviewed_on=str(metadata["reviewed_on"]),
        review_within_days=int(metadata["review_within_days"]),  # type: ignore[arg-type]
        deprecated=bool(metadata["deprecated"]),
        deprecated_on=metadata["deprecated_on"],  # type: ignore[arg-type]
        deprecated_reason=metadata["deprecated_reason"],  # type: ignore[arg-type]
        evidence=metadata["evidence"],  # type: ignore[arg-type]
        scope=scope,
        rules=rules,
        overrides=overrides,
        verification=verification,
        exceptions=exceptions,
        examples=examples,
        example_payload_bytes=payload_bytes,
    )
