"""Production resolver: selection, authority, evidence, exceptions, Snapshot.

``resolve_context`` is the one importable entry point. It validates the caller
input, applies Design section 7's pre-root approval matrix, checks the platform
predicate, anchors the no-symlink Git root, and then observes only the files the
selected graph names. There is no repository-wide or unselected-branch scan.

Every finding is a closed Diagnostic registry record built by ``model``; this
module never spells a code, detail, or sort order of its own. Opaque approval
provenance stays opaque: the resolver never opens ``authorization_reference``
and never recomputes ``authorization_digest``.
"""

from __future__ import annotations

import datetime
import os
from dataclasses import dataclass, field

from . import filesystem, markdown
from .model import (
    EFFECTIVE_RULE_COUNT_LIMIT,
    EVIDENCE_AGGREGATE_BYTE_LIMIT,
    EVIDENCE_FILE_BYTE_LIMIT,
    EVIDENCE_FILE_COUNT_LIMIT,
    LEAF_FILE_BYTE_LIMIT,
    MAP_DEPTH_LIMIT,
    MAP_FILE_BYTE_LIMIT,
    ROOT_CONTEXT_ID,
    ROOT_SELECTED_FILE_APPLIES_TO,
    ROOT_SELECTED_FILE_KIND,
    ROOT_SELECTED_FILE_SELECTION_BASIS,
    SCHEMA_VERSION,
    SELECTED_AGGREGATE_BYTE_LIMIT,
    SELECTED_FILE_LIMIT,
    SELECTION_BASIS_ORDER,
    SNAPSHOT_ROOT_MAP,
    WAIVABLE_CODES,
    DIAGNOSTIC_SPECS,
    Diagnostic,
    EffectiveRule,
    EvidenceObservation,
    ExceptionApproval,
    FileIdentity,
    Resolution,
    ResolutionInput,
    SelectedFile,
    Snapshot,
    TechstackSnapshotError,
    Totals,
    apply_diagnostic_limit,
    canonical_json_text,
    diagnostic,
    effective_rule_sort_key,
    root_api_error_for_code,
    sha256_hex,
)

#: The one project-relative opt-in path. Its absence is the only not-applicable
#: observation.
ROOT_MAP_PATH = SNAPSHOT_ROOT_MAP

#: The exact ``authorized_by`` value a valid approval carries.
APPROVAL_AUTHORIZED_BY = "user"

#: The inclusive approval validity window, in days.
APPROVAL_MAX_WINDOW_DAYS = 30

#: The keys ``scope_sha256`` hashes, in Design section 7's order. Canonical JSON
#: sorts them, so this tuple names membership rather than byte order.
SCOPE_DIGEST_KEYS = (
    "task_id",
    "plan_id",
    "plan_version",
    "attempt_id",
    "scope_paths",
    "context_chains",
    "declared_conflicts",
)

#: The one approval field ``binding_sha256`` excludes: itself.
BINDING_DIGEST_EXCLUDED_KEY = "binding_sha256"


# ---------------------------------------------------------------------------
# Digests over canonical input
# ---------------------------------------------------------------------------


def scope_digest(resolution_input: ResolutionInput) -> str:
    """Hash the canonical task/plan/version/attempt/scope/chains/conflicts."""

    payload = resolution_input.to_json_object()
    scoped = {key: payload[key] for key in SCOPE_DIGEST_KEYS}
    return sha256_hex(canonical_json_text(scoped).encode("utf-8"))


def binding_digest(approval: ExceptionApproval) -> str:
    """Hash every approval field except ``binding_sha256`` itself."""

    payload = approval.to_json_object()
    del payload[BINDING_DIGEST_EXCLUDED_KEY]
    return sha256_hex(canonical_json_text(payload).encode("utf-8"))


def _date(value: str) -> datetime.date:
    return datetime.date(int(value[0:4]), int(value[5:7]), int(value[8:10]))


# ---------------------------------------------------------------------------
# Pre-root approval semantics
# ---------------------------------------------------------------------------


def _approval_diagnostic(approval: ExceptionApproval, code: str) -> Diagnostic:
    """Build one exception diagnostic located by its target Context ID."""

    return diagnostic(code, context_id=approval.target.context_id)


def _approval_failure(
    approval: ExceptionApproval, resolution_input: ResolutionInput, expected_scope: str
) -> str | None:
    """Return the first failing closed check for one approval, or None.

    Only one code is reported per approval, so a single forged record cannot
    multiply into a cascade of derived findings.
    """

    if approval.coordinator_attested is not True:
        return "UNATTESTED_EXCEPTION"
    if approval.authorized_by != APPROVAL_AUTHORIZED_BY:
        return "INVALID_EXCEPTION_PROVENANCE"
    if not approval.authorization_reference:
        # The shape layer permits an empty opaque reference precisely so a
        # well-typed forged claim reaches this closed blocked diagnostic.
        return "INVALID_EXCEPTION_PROVENANCE"
    if (
        approval.task_id != resolution_input.task_id
        or approval.plan_id != resolution_input.plan_id
        or approval.plan_version != resolution_input.plan_version
        or approval.attempt_id != resolution_input.attempt_id
    ):
        return "EXCEPTION_BINDING_MISMATCH"
    if approval.scope_sha256 != expected_scope:
        return "EXCEPTION_DIGEST_MISMATCH"
    if approval.binding_sha256 != binding_digest(approval):
        return "EXCEPTION_DIGEST_MISMATCH"
    issued = _date(approval.issued_on)
    expires = _date(approval.expires_on)
    as_of = _date(resolution_input.as_of)
    if not issued <= as_of <= expires:
        return "EXCEPTION_EXPIRED"
    if expires > issued + datetime.timedelta(days=APPROVAL_MAX_WINDOW_DAYS):
        return "EXCEPTION_EXPIRED"
    return None


def validate_approvals(resolution_input: ResolutionInput) -> list[Diagnostic]:
    """Return the independent pre-root approval diagnostics, in input order."""

    expected_scope = scope_digest(resolution_input)
    findings: list[Diagnostic] = []
    for approval in resolution_input.exception_approvals:
        code = _approval_failure(approval, resolution_input, expected_scope)
        if code is not None:
            findings.append(_approval_diagnostic(approval, code))
    return findings


# ---------------------------------------------------------------------------
# Bounded project reads
# ---------------------------------------------------------------------------


def read_project_file(root_fd: int, relative_path: str, limit: int):
    """Read one project-relative path through the packet-1 production reader.

    Every intermediate component is metadata-classified and opened no-follow
    relative to the held root descriptor; only the final metadata-regular
    candidate reaches the bounded helper.
    """

    components = relative_path.split("/")
    opened: list[int] = []
    parent = root_fd
    try:
        for component in components[:-1]:
            descriptor, observed = filesystem.open_directory(parent, component)
            if descriptor is None:
                return observed
            opened.append(descriptor)
            parent = descriptor
        return filesystem.read_bounded_regular(parent, components[-1], limit)
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)


# ---------------------------------------------------------------------------
# Selected graph
# ---------------------------------------------------------------------------


@dataclass
class _Node:
    """One selected map or leaf with its complete selection provenance."""

    path: str
    context_id: str
    kind: str
    referrer_map: str | None
    map_chain: tuple[str, ...]
    applies_to: tuple[str, ...]
    selection_basis: tuple[str, ...]
    identity: FileIdentity
    raw: bytes
    ancestor_paths: tuple[str, ...]
    parsed_map: markdown.ParsedMap | None = None
    parsed_leaf: markdown.ParsedLeaf | None = None
    evidence: tuple[EvidenceObservation, ...] = ()

    @property
    def is_map(self) -> bool:
        return self.kind == "map"


@dataclass
class _Occurrence:
    """One rule occurrence and the anchor that carries its authority."""

    leaf: _Node
    map_node: _Node
    rule: markdown.RuleRecord


@dataclass
class _Findings:
    """The accumulated diagnostics of one resolution."""

    records: list[Diagnostic] = field(default_factory=list)

    def add(self, code: str, **location) -> None:
        self.records.append(diagnostic(code, **location))

    def codes(self) -> tuple[str, ...]:
        return tuple(record.code for record in self.records)


class _Resolver:
    """One bounded resolution against one anchored root."""

    def __init__(self, resolution_input: ResolutionInput, handle) -> None:
        self.input = resolution_input
        self.handle = handle
        self.findings = _Findings()
        self.nodes: dict[str, _Node] = {}
        self.row_ids: set[str] = set()
        self.exhausted = False

    # -- reading ----------------------------------------------------------

    def _read(self, relative_path: str, limit: int):
        return read_project_file(self.handle.fd, relative_path, limit)

    def _add_located(self, code: str, relative_path: str, errno_value=None) -> None:
        """Add one observation diagnostic under its registry field class.

        ``UNSUPPORTED_SAFE_OPEN`` and ``RESOURCE_LIMIT`` are class ``G`` and
        therefore carry no path, even though the observation that produced them
        named one.
        """

        if DIAGNOSTIC_SPECS[code].fields == "G":
            self.findings.add(code, errno_value=errno_value)
            return
        self.findings.add(code, path=relative_path, errno_value=errno_value)

    def _observation_diagnostic(
        self, observation, relative_path: str, *, byte_limit_code: str
    ) -> None:
        """Map one failed observation to its exact registry diagnostic."""

        if observation.code == filesystem.OUTCOME_BYTE_LIMIT:
            self.findings.add(byte_limit_code, path=relative_path)
            return
        if observation.code == filesystem.OUTCOME_NOT_FOUND:
            self.findings.add("MISSING_RULE_FILE", path=relative_path)
            return
        self._add_located(observation.code, relative_path, observation.errno_value)

    # -- selection --------------------------------------------------------

    def _chain_basis(self, map_node: _Node, row: markdown.MapRow) -> bool:
        depth = len(map_node.map_chain)
        for chain in self.input.context_chains:
            if len(chain) > depth and chain[:depth] == map_node.map_chain:
                if chain[depth] == row.context_id:
                    return True
        return False

    def _selection_basis(self, map_node: _Node, row: markdown.MapRow) -> tuple[str, ...]:
        values: set[str] = set()
        if markdown.DOT_SELECTOR in row.applies_to:
            values.add("dot")
        if any(
            markdown.selector_contains(selector, scope_path)
            for selector in row.applies_to
            for scope_path in self.input.scope_paths
        ):
            values.add("scope")
        if self._chain_basis(map_node, row):
            values.add("context_chain")
        return tuple(item for item in SELECTION_BASIS_ORDER if item in values)

    def _within_selected_bounds(self) -> bool:
        """Emit and stop once the selected file or byte cap is exceeded."""

        if self.exhausted:
            return False
        if len(self.nodes) > SELECTED_FILE_LIMIT:
            self.findings.add("SELECTED_FILE_LIMIT")
            self.exhausted = True
            return False
        if sum(len(node.raw) for node in self.nodes.values()) > SELECTED_AGGREGATE_BYTE_LIMIT:
            self.findings.add("SELECTED_BYTE_LIMIT")
            self.exhausted = True
            return False
        return True

    def _parse(self, node: _Node) -> bool:
        """Parse one selected file and record its grammar failure exactly."""

        try:
            if node.is_map:
                node.parsed_map = markdown.parse_map(node.raw)
            else:
                node.parsed_leaf = markdown.parse_leaf(node.raw)
        except markdown.MarkdownError as error:
            self.findings.add(
                error.code,
                path=node.path,
                context_id=error.context_id,
                line=error.line,
                rule=error.rule,
            )
            return False
        return True

    def _register_row_ids(self, node: _Node) -> None:
        """All row IDs of every parsed selected map are globally unique."""

        assert node.parsed_map is not None
        for row in node.parsed_map.rows:
            if row.context_id in self.row_ids:
                self.findings.add(
                    "DUPLICATE_CONTEXT_ID", path=node.path, context_id=row.context_id
                )
                continue
            self.row_ids.add(row.context_id)

    def _load_root_map(self):
        observation = self._read(ROOT_MAP_PATH, MAP_FILE_BYTE_LIMIT)
        if observation.code == filesystem.OUTCOME_NOT_FOUND:
            return None
        if not observation.ok:
            self._observation_diagnostic(
                observation, ROOT_MAP_PATH, byte_limit_code="MAP_BYTE_LIMIT"
            )
            return False
        node = _Node(
            path=ROOT_MAP_PATH,
            context_id=ROOT_CONTEXT_ID,
            kind=ROOT_SELECTED_FILE_KIND,
            referrer_map=None,
            map_chain=(),
            applies_to=ROOT_SELECTED_FILE_APPLIES_TO,
            selection_basis=ROOT_SELECTED_FILE_SELECTION_BASIS,
            identity=observation.identity,
            raw=observation.data or b"",
            ancestor_paths=(ROOT_MAP_PATH,),
        )
        self.nodes[node.path] = node
        if not self._parse(node):
            return False
        if node.parsed_map.context_id != ROOT_CONTEXT_ID:
            # Root metadata is exactly ``root``; anything else is not a root map.
            self.findings.add("INVALID_MAP", path=node.path)
            return False
        self._register_row_ids(node)
        return node

    def _load_child(self, map_node: _Node, row: markdown.MapRow, basis: tuple[str, ...]):
        chain = map_node.map_chain + (row.context_id,)
        is_map = row.is_map
        if row.rule_path in map_node.ancestor_paths:
            self.findings.add(
                "CONTEXT_CYCLE", path=row.rule_path, context_id=row.context_id
            )
            return None
        if row.rule_path in self.nodes:
            self.findings.add(
                "DUPLICATE_RULE_PATH", path=row.rule_path, context_id=row.context_id
            )
            return None
        if is_map and len(chain) + 1 > MAP_DEPTH_LIMIT:
            self.findings.add("MAP_DEPTH_LIMIT")
            return None
        limit = MAP_FILE_BYTE_LIMIT if is_map else LEAF_FILE_BYTE_LIMIT
        observation = self._read(row.rule_path, limit)
        if not observation.ok:
            self._observation_diagnostic(
                observation,
                row.rule_path,
                byte_limit_code="MAP_BYTE_LIMIT" if is_map else "LEAF_BYTE_LIMIT",
            )
            return None
        node = _Node(
            path=row.rule_path,
            context_id=row.context_id,
            kind="map" if is_map else "leaf",
            referrer_map=map_node.path,
            map_chain=chain,
            applies_to=row.applies_to,
            selection_basis=basis,
            identity=observation.identity,
            raw=observation.data or b"",
            ancestor_paths=map_node.ancestor_paths + (row.rule_path,),
        )
        self.nodes[node.path] = node
        if not self._parse(node):
            return None
        declared = (
            node.parsed_map.context_id if is_map else node.parsed_leaf.context_id
        )
        if declared != row.context_id:
            self.findings.add(
                "ROW_CHILD_ID_MISMATCH", path=node.path, context_id=row.context_id
            )
            return None
        if is_map:
            self._register_row_ids(node)
        return node

    def _build_graph(self, root_node: _Node) -> None:
        queue = [root_node]
        while queue:
            map_node = queue.pop(0)
            assert map_node.parsed_map is not None
            for row in map_node.parsed_map.rows:
                if not self._within_selected_bounds():
                    return
                basis = self._selection_basis(map_node, row)
                if not basis:
                    continue
                child = self._load_child(map_node, row, basis)
                if child is not None and child.is_map:
                    queue.append(child)
        self._within_selected_bounds()

    def _check_chains(self, root_node: _Node) -> None:
        for chain in self.input.context_chains:
            if not self._chain_reachable(root_node, chain):
                self.findings.add("UNREACHABLE_CONTEXT")
                return

    def _chain_reachable(self, root_node: _Node, chain: tuple[str, ...]) -> bool:
        """A chain names every row ID from the root map to its target row."""

        current: _Node | None = root_node
        for index, context_id in enumerate(chain):
            if current is None or current.parsed_map is None:
                return False
            row = next(
                (item for item in current.parsed_map.rows if item.context_id == context_id),
                None,
            )
            if row is None:
                return False
            if index == len(chain) - 1:
                return True
            if not row.is_map:
                return False
            current = self.nodes.get(row.rule_path)
        return False

    # -- evidence ---------------------------------------------------------

    def _observe_evidence(self) -> None:
        total_count = 0
        total_bytes = 0
        exhausted = False
        for node in self._leaves():
            assert node.parsed_leaf is not None
            observations: list[EvidenceObservation] = []
            for path in sorted(node.parsed_leaf.evidence, key=lambda item: item.encode("utf-8")):
                observation = self._read(path, EVIDENCE_FILE_BYTE_LIMIT)
                if observation.code == filesystem.OUTCOME_NOT_FOUND:
                    self.findings.add(
                        "MISSING_EVIDENCE", path=path, context_id=node.context_id
                    )
                    continue
                if observation.code == filesystem.OUTCOME_BYTE_LIMIT:
                    self.findings.add(
                        "EVIDENCE_BYTE_LIMIT", path=path, context_id=node.context_id
                    )
                    continue
                if not observation.ok:
                    self._add_located(observation.code, path, observation.errno_value)
                    continue
                data = observation.data or b""
                observations.append(
                    EvidenceObservation(
                        path=path, bytes=len(data), sha256=sha256_hex(data)
                    )
                )
                total_count += 1
                total_bytes += len(data)
                if total_bytes > EVIDENCE_AGGREGATE_BYTE_LIMIT:
                    # The aggregate cap is enforced as the reads accumulate, so
                    # an oversized tree stops at the boundary instead of
                    # reading every remaining declared path first.
                    exhausted = True
                    break
            node.evidence = tuple(observations)
            if exhausted:
                break
        if total_count > EVIDENCE_FILE_COUNT_LIMIT:
            self.findings.add("EVIDENCE_FILE_LIMIT")
        if exhausted:
            self.findings.add("EVIDENCE_AGGREGATE_BYTE_LIMIT")

    # -- freshness --------------------------------------------------------

    def _check_freshness(self) -> None:
        as_of = _date(self.input.as_of)
        for node in self._leaves():
            leaf = node.parsed_leaf
            assert leaf is not None
            reviewed = _date(leaf.reviewed_on)
            if reviewed > as_of:
                self.findings.add(
                    "FUTURE_REVIEW_DATE", path=node.path, context_id=node.context_id
                )
            elif (as_of - reviewed).days > leaf.review_within_days:
                self.findings.add(
                    "STALE_RULE", path=node.path, context_id=node.context_id
                )
            if leaf.deprecated and leaf.deprecated_on is not None:
                # A future deprecation date is retained but never fails.
                if _date(leaf.deprecated_on) <= as_of:
                    self.findings.add(
                        "DEPRECATED_RULE", path=node.path, context_id=node.context_id
                    )

    # -- authority --------------------------------------------------------

    def _leaves(self) -> list[_Node]:
        """Return every parsed selected leaf in path order.

        A leaf whose bytes failed the grammar stays in ``nodes`` so a second
        reference to it is still a duplicate path, but it carries no parsed
        sections and therefore never reaches evidence, freshness, or authority.
        """

        return [
            node
            for path, node in sorted(self.nodes.items(), key=lambda item: item[0].encode("utf-8"))
            if not node.is_map and node.parsed_leaf is not None
        ]

    def _more_specific(self, dominant: _Occurrence, candidate: _Occurrence) -> bool:
        """Return True when ``candidate`` is strictly more specific."""

        descends = dominant.map_node.path in candidate.map_node.ancestor_paths
        if not descends:
            return False
        if not markdown.union_is_subset(
            candidate.leaf.applies_to, dominant.leaf.applies_to
        ):
            return False
        strict_map = dominant.map_node.path != candidate.map_node.path
        strict_union = candidate.leaf.applies_to != dominant.leaf.applies_to
        return strict_map or strict_union

    def _effective_rules(self) -> tuple[EffectiveRule, ...]:
        occurrences: dict[str, list[_Occurrence]] = {}
        for node in self._leaves():
            leaf = node.parsed_leaf
            assert leaf is not None
            map_node = self.nodes[node.referrer_map]
            for rule in leaf.rules:
                occurrences.setdefault(rule.rule_id, []).append(
                    _Occurrence(leaf=node, map_node=map_node, rule=rule)
                )
        rules: list[EffectiveRule] = []
        for rule_id in sorted(occurrences, key=lambda value: value.encode("utf-8")):
            group = occurrences[rule_id]
            for occurrence in group:
                target = self._authority_target(rule_id, occurrence, group)
                rules.append(
                    EffectiveRule(
                        rule_id=rule_id,
                        statement_sha256=sha256_hex(
                            occurrence.rule.statement.encode("utf-8")
                        ),
                        source_path=occurrence.leaf.path,
                        context_id=occurrence.leaf.context_id,
                        authority_map=occurrence.map_node.path,
                        applies_to=occurrence.leaf.applies_to,
                        overrides_context_id=target,
                    )
                )
        self._check_unmatched_overrides(occurrences)
        if len(rules) > EFFECTIVE_RULE_COUNT_LIMIT:
            self.findings.add("EFFECTIVE_RULE_LIMIT")
        return tuple(sorted(rules, key=lambda item: effective_rule_sort_key(item.to_json_object())))

    def _authority_target(
        self, rule_id: str, occurrence: _Occurrence, group: list[_Occurrence]
    ) -> str | None:
        """Return the validated nearest override target, or None."""

        dominating = [
            other
            for other in group
            if other is not occurrence and self._more_specific(other, occurrence)
        ]
        overlapping_peers = [
            other
            for other in group
            if other is not occurrence
            and markdown.unions_overlap(other.leaf.applies_to, occurrence.leaf.applies_to)
            and not self._more_specific(other, occurrence)
            and not self._more_specific(occurrence, other)
        ]
        if overlapping_peers:
            self.findings.add(
                "PEER_RULE_CONFLICT",
                path=occurrence.leaf.path,
                context_id=occurrence.leaf.context_id,
            )
            return None
        if not dominating:
            return None
        nearest = self._nearest(dominating)
        declared = [
            record
            for record in occurrence.leaf.parsed_leaf.overrides
            if record.rule_id == rule_id
        ]
        if nearest is None or len(declared) != 1:
            self.findings.add(
                "INVALID_OVERRIDE",
                path=occurrence.leaf.path,
                context_id=occurrence.leaf.context_id,
            )
            return None
        target = declared[0].target_context_id
        if target == nearest.leaf.context_id:
            return target
        if any(other.leaf.context_id == target for other in dominating):
            self.findings.add(
                "NON_NEAREST_OVERRIDE",
                path=occurrence.leaf.path,
                context_id=occurrence.leaf.context_id,
            )
            return None
        self.findings.add(
            "INVALID_OVERRIDE",
            path=occurrence.leaf.path,
            context_id=occurrence.leaf.context_id,
        )
        return None

    def _nearest(self, dominating: list[_Occurrence]) -> _Occurrence | None:
        """Return the unique occurrence every other dominating one dominates."""

        candidates = [
            candidate
            for candidate in dominating
            if all(
                other is candidate or self._more_specific(other, candidate)
                for other in dominating
            )
        ]
        return candidates[0] if len(candidates) == 1 else None

    def _check_unmatched_overrides(
        self, occurrences: dict[str, list[_Occurrence]]
    ) -> None:
        """An override with no dominating occurrence to name is invalid."""

        for node in self._leaves():
            leaf = node.parsed_leaf
            assert leaf is not None
            for record in leaf.overrides:
                group = occurrences.get(record.rule_id, [])
                mine = next(
                    (item for item in group if item.leaf.path == node.path), None
                )
                if mine is None:
                    continue
                if not any(
                    other is not mine and self._more_specific(other, mine)
                    for other in group
                ):
                    self.findings.add(
                        "INVALID_OVERRIDE",
                        path=node.path,
                        context_id=node.context_id,
                    )

    # -- exceptions -------------------------------------------------------

    def _consume_approvals(self) -> None:
        """Consume each approval against exactly one waivable finding."""

        for approval in self.input.exception_approvals:
            target = approval.target
            matches = [
                record
                for record in self.findings.records
                if record.code == target.code
                and record.code in WAIVABLE_CODES
                and record.waived_by is None
                and record.context_id == target.context_id
                and (target.evidence_path is None or record.path == target.evidence_path)
            ]
            if not matches:
                self.findings.records.append(
                    _approval_diagnostic(approval, "UNUSED_EXCEPTION")
                )
                continue
            if len(matches) > 1:
                self.findings.records.append(
                    _approval_diagnostic(approval, "AMBIGUOUS_EXCEPTION")
                )
                continue
            consumed = matches[0]
            index = self.findings.records.index(consumed)
            self.findings.records[index] = diagnostic(
                consumed.code,
                path=consumed.path,
                context_id=consumed.context_id,
                waived_by=approval.approval_id,
            )

    # -- assembly ---------------------------------------------------------

    def _selected_files(self) -> tuple[SelectedFile, ...]:
        root = self.nodes[ROOT_MAP_PATH]
        others = sorted(
            (node for path, node in self.nodes.items() if path != ROOT_MAP_PATH),
            key=lambda node: node.path.encode("utf-8"),
        )
        return tuple(self._selected_file(node) for node in [root] + others)

    def _selected_file(self, node: _Node) -> SelectedFile:
        leaf = node.parsed_leaf
        return SelectedFile(
            path=node.path,
            context_id=node.context_id,
            kind=node.kind,
            referrer_map=node.referrer_map,
            map_chain=node.map_chain,
            applies_to=node.applies_to,
            selection_basis=node.selection_basis,
            identity=node.identity,
            bytes=len(node.raw),
            sha256=sha256_hex(node.raw),
            reviewed_on=None if leaf is None else leaf.reviewed_on,
            review_within_days=None if leaf is None else leaf.review_within_days,
            deprecated=None if leaf is None else leaf.deprecated,
            evidence=node.evidence,
        )

    def _snapshot(self, rules: tuple[EffectiveRule, ...]) -> Snapshot | None:
        selected = self._selected_files()
        totals = Totals(
            file_count=len(selected),
            bytes=sum(item.bytes for item in selected),
            evidence_file_count=sum(len(item.evidence) for item in selected),
            evidence_bytes=sum(
                observation.bytes for item in selected for observation in item.evidence
            ),
            rule_count=len(rules),
        )
        try:
            return Snapshot.build(
                schema_version=SCHEMA_VERSION,
                task_id=self.input.task_id,
                plan_id=self.input.plan_id,
                plan_version=self.input.plan_version,
                attempt_id=self.input.attempt_id,
                as_of=self.input.as_of,
                root_identity=self.handle.identity,
                root_map=ROOT_MAP_PATH,
                scope_paths=self.input.scope_paths,
                context_chains=self.input.context_chains,
                exception_approvals=self.input.exception_approvals,
                declared_conflicts=self.input.declared_conflicts,
                selected_files=selected,
                effective_rules=rules,
                totals=totals,
            )
        except TechstackSnapshotError as error:
            if error.code != "SNAPSHOT_BYTE_LIMIT":
                raise
            self.findings.add("SNAPSHOT_BYTE_LIMIT")
            return None

    def run(self) -> Resolution:
        root_node = self._load_root_map()
        if root_node is None:
            # Root-map absence is the one not-applicable observation, and only
            # when no approval or declared conflict would go unused.
            if self.input.exception_approvals or self.input.declared_conflicts:
                return _blocked([diagnostic("UNUSED_INPUT_WITHOUT_ROOT")])
            return Resolution(
                schema_version=SCHEMA_VERSION,
                status="not_applicable",
                snapshot=None,
                diagnostics=(),
            )
        if root_node is False:
            return _blocked(self.findings.records)
        self._build_graph(root_node)
        self._check_chains(root_node)
        self._observe_evidence()
        self._check_freshness()
        rules = self._effective_rules()
        if self.input.declared_conflicts:
            self.findings.add("DECLARED_AUTHORITY_CONFLICT")
        self._consume_approvals()
        if not filesystem.root_identity_unchanged(self.handle):
            self.findings.add("ROOT_CHANGED")
        if any(record.severity == "error" for record in self.findings.records):
            return _blocked(self.findings.records)
        snapshot = self._snapshot(rules)
        if snapshot is None:
            return _blocked(self.findings.records)
        return Resolution(
            schema_version=SCHEMA_VERSION,
            status="applicable",
            snapshot=snapshot,
            diagnostics=apply_diagnostic_limit(self.findings.records),
        )


def _blocked(diagnostics) -> Resolution:
    """Return one complete blocked Resolution with its bounded diagnostics."""

    bounded = apply_diagnostic_limit(diagnostics)
    return Resolution(
        schema_version=SCHEMA_VERSION,
        status="blocked",
        snapshot=None,
        diagnostics=bounded,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_context(input, project_root) -> Resolution:  # noqa: A002 - frozen name
    """Resolve one bounded techstack context for one attempt.

    Precedence is exactly Design section 14: input type and schema, then the
    pre-root approval matrix, then the platform predicate, then the root. Each
    earlier failure proves zero access to every later surface.
    """

    if not isinstance(input, ResolutionInput):
        raise root_api_error_for_code("INPUT_TYPE")
    approval_findings = validate_approvals(input)
    if approval_findings:
        return _blocked(approval_findings)
    if not filesystem.is_supported_platform():
        return _blocked([diagnostic("UNSUPPORTED_PLATFORM")])
    handle = filesystem.validate_and_open_git_root(project_root)
    try:
        return _Resolver(input, handle).run()
    finally:
        handle.close()
