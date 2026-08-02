#!/usr/bin/env python3
"""Deterministic read-only summary of checkout-mode task dossiers.

The summary answers "is this dossier sound?" without opening eleven files by
eye. It reports artifact state, evidence depth against the rule that actually
applies, effective model provenance, plan and review identity, authority-link
health, and review independence.

It is not a second validity authority. The verdict is always
``validate_projects(root, require_complete=True)``; selecting one task never
suppresses a root-level diagnostic. Authority-link rows report *health*;
invalidity is the validator's diagnostic, reported here and never decided here.

Exit codes compose a scope code with a verdict code: ``2`` means the requested
scope could not be evaluated at all, ``1`` means it was evaluated and the sole
validator produced a diagnostic, ``0`` means neither.

Effective route, model, and effort are read from the artifacts. The routing
manifest is never opened.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

from .parser import concrete_list_items, parse_artifact, plain
from .schema import (
    ARTIFACTS,
    CANONICAL_MEMORY_FILES,
    Diagnostic,
    INDEX_IDENTITY_SECTION,
    METADATA_SECTION,
    MINIMUM_EVIDENCE_ITEMS,
    PLAN_STATUS_SECTION,
    REVIEW_ARTIFACTS,
    REVIEW_TARGET_SECTION,
)
from .validation import validate_dossier, validate_projects


# Fixed wording. Two identifiers differing is a deterministic consistency
# signal that can be checked; it is not proof that two independent sessions
# existed, and no rendered form may imply that it is.
INDEPENDENCE_CAVEAT = (
    "Session-identifier inequality is a deterministic consistency signal, not "
    "proof that two independent sessions existed."
)

EVIDENCE_RULES = {
    "level-floor": "level floor for a passed artifact",
    "one-item": "one concrete item for a 'not-required' artifact",
    "not-applicable": "no floor applies in this phase state",
}


class ScopeError(Exception):
    """The requested scope cannot be evaluated at all. Exit code 2."""


@dataclass(frozen=True)
class ArtifactState:
    name: str
    present: bool
    applicability: str
    phase_state: str
    evidence_items: int
    evidence_rule: str
    evidence_required: int
    meets_evidence_rule: bool
    authorship: str
    authoring_session: str
    effective_route: str
    effective_model: str
    effective_effort: str


@dataclass(frozen=True)
class AuthorityLink:
    label: str
    declared: str
    expected: str
    matches_expected: bool
    exists: bool
    not_a_symlink: bool
    no_symlinked_ancestor: bool
    contained: bool


@dataclass(frozen=True)
class ReviewIndependence:
    review: str
    reviewing_session_arm: str
    authoring_session_arm: str


@dataclass(frozen=True)
class PlanIdentity:
    plan_id: str
    plan_status: str
    plan_artifact_version: str
    index_accepted_plan_id: str
    index_accepted_plan_version: str
    accepted_id_state: str
    accepted_version_state: str
    reviews: tuple[tuple[str, str, str, str, str], ...]


@dataclass(frozen=True)
class DossierSummary:
    task_id: str
    level: str
    project: str
    path: str
    artifacts: tuple[ArtifactState, ...]
    plan_identity: PlanIdentity
    authority_links: tuple[AuthorityLink, ...]
    independence: tuple[ReviewIndependence, ...]
    unreadable: tuple[tuple[str, str], ...]
    diagnostics: tuple[str, ...]


def _is_safe_relative(value: str) -> bool:
    pure = PurePosixPath(value)
    return not (
        pure.is_absolute()
        or ".." in pure.parts
        or "\\" in value
        or (pure.parts and pure.parts[0].startswith("~"))
    )


def _symlinked_ancestor(repository_root: Path, parts: Sequence[str]) -> Path | None:
    current = repository_root
    for part in parts[:-1]:
        current = current / part
        if current.is_symlink():
            return current
    return None


def _evidence_rule(applicability: str, phase_state: str, level: str) -> tuple[str, int]:
    """Report the rule that applies, not a single universal floor.

    A Level 2 'not-required' artifact holding one item is compliant, not
    below-floor: the level floor governs passed artifacts only.
    """
    if applicability == "not-required":
        return "one-item", 1
    if phase_state == "passed":
        return "level-floor", MINIMUM_EVIDENCE_ITEMS.get(level, 1)
    return "not-applicable", 0


def _authority_link(
    label: str,
    declared: str,
    expected: str,
    repository_root: Path,
    *,
    matches: bool | None = None,
) -> AuthorityLink:
    contained = bool(declared) and _is_safe_relative(declared)
    exists = False
    not_a_symlink = False
    no_ancestor = False
    if contained:
        parts = PurePosixPath(declared).parts
        candidate = repository_root.joinpath(*parts)
        not_a_symlink = not candidate.is_symlink()
        exists = candidate.is_file() and not_a_symlink
        no_ancestor = _symlinked_ancestor(repository_root, parts) is None
    return AuthorityLink(
        label=label,
        declared=declared or "(not declared)",
        expected=expected,
        matches_expected=(declared == expected) if matches is None else matches,
        exists=exists,
        not_a_symlink=not_a_symlink,
        no_symlinked_ancestor=no_ancestor,
        contained=contained,
    )


def _independence_arm(session: str, plan_session: str) -> str:
    if not session or not plan_session:
        return "unknown"
    return "not-independent" if session == plan_session else "independent"


def summarize_dossier(dossier: Path, projects_root: Path) -> DossierSummary:
    """Return one deterministic read-only summary. Nothing is mutated."""
    root = projects_root.resolve()
    repository_root = root.parent
    try:
        relative = dossier.relative_to(root)
    except ValueError:
        # A caller may pass an unresolved path (a temporary directory reached
        # through a platform symlink such as darwin's /tmp). Comparing the
        # resolved form keeps the declared path intact for reporting.
        relative = Path(os.path.realpath(dossier)).relative_to(root)
    project, task_id = relative.parts[0], relative.parts[2]

    unreadable: list[tuple[str, str]] = []
    parsed: dict[str, Any] = {}
    for name in ARTIFACTS:
        path = dossier / f"{name}.md"
        if path.is_symlink():
            unreadable.append((f"{name}.md", "artifact is a symlink"))
            continue
        if not path.is_file():
            unreadable.append((f"{name}.md", "artifact is missing"))
            continue
        collected: list[Diagnostic] = []
        artifact = parse_artifact(path, name, collected)
        for diagnostic in collected:
            if diagnostic.message.startswith("cannot read artifact"):
                unreadable.append((f"{name}.md", diagnostic.message))
        parsed[name] = artifact

    index = parsed.get("index")
    level = plain(index.get(METADATA_SECTION, "Task level")) if index else ""

    states: list[ArtifactState] = []
    for name in ARTIFACTS:
        artifact = parsed.get(name)
        if artifact is None:
            states.append(
                ArtifactState(
                    name=name,
                    present=False,
                    applicability="(absent)",
                    phase_state="(absent)",
                    evidence_items=0,
                    evidence_rule="not-applicable",
                    evidence_required=0,
                    meets_evidence_rule=False,
                    authorship="(absent)",
                    authoring_session="(absent)",
                    effective_route="(absent)",
                    effective_model="(absent)",
                    effective_effort="(absent)",
                )
            )
            continue
        applicability = plain(artifact.get(METADATA_SECTION, "Applicability"))
        phase_state = plain(artifact.get(METADATA_SECTION, "Phase state"))
        items = len(concrete_list_items(artifact.sections.get("Evidence", "")))
        rule, required = _evidence_rule(applicability, phase_state, level)
        states.append(
            ArtifactState(
                name=name,
                present=True,
                applicability=applicability,
                phase_state=phase_state,
                evidence_items=items,
                evidence_rule=rule,
                evidence_required=required,
                meets_evidence_rule=items >= required,
                authorship=plain(artifact.get(METADATA_SECTION, "Authorship")),
                authoring_session=plain(
                    artifact.get(METADATA_SECTION, "Authoring session")
                ),
                effective_route=plain(
                    artifact.get(METADATA_SECTION, "Effective route")
                ),
                effective_model=plain(
                    artifact.get(METADATA_SECTION, "Effective model")
                ),
                effective_effort=plain(
                    artifact.get(METADATA_SECTION, "Effective effort")
                ),
            )
        )

    plan = parsed.get("plan")
    plan_id = plain(plan.get(PLAN_STATUS_SECTION, "Plan ID")) if plan else ""
    plan_status = plain(plan.get(PLAN_STATUS_SECTION, "Plan status")) if plan else ""
    plan_version = plain(plan.get(METADATA_SECTION, "Artifact version")) if plan else ""
    index_fields = index.fields.get(INDEX_IDENTITY_SECTION, {}) if index else {}
    accepted_id = plain(index_fields.get("Accepted plan ID", ""))
    accepted_version = plain(index_fields.get("Accepted plan version", ""))

    reviews: list[tuple[str, str, str, str, str]] = []
    independence: list[ReviewIndependence] = []
    plan_session = plain(plan.get(METADATA_SECTION, "Authoring session")) if plan else ""
    for name in REVIEW_ARTIFACTS:
        review = parsed.get(name)
        if review is None:
            reviews.append((name, "(absent)", "(absent)", "unknown", "unknown"))
            independence.append(ReviewIndependence(name, "unknown", "unknown"))
            continue
        reviewed_id = plain(review.get(REVIEW_TARGET_SECTION, "Reviewed plan ID"))
        reviewed_version = plain(
            review.get(REVIEW_TARGET_SECTION, "Reviewed plan version")
        )
        reviews.append(
            (
                name,
                reviewed_id,
                reviewed_version,
                "matches" if reviewed_id == plan_id else "differs",
                "matches" if reviewed_version == plan_version else "differs",
            )
        )
        independence.append(
            ReviewIndependence(
                review=name,
                reviewing_session_arm=_independence_arm(
                    plain(review.get(METADATA_SECTION, "Reviewing session")),
                    plan_session,
                ),
                authoring_session_arm=_independence_arm(
                    plain(review.get(METADATA_SECTION, "Authoring session")),
                    plan_session,
                ),
            )
        )

    plan_identity = PlanIdentity(
        plan_id=plan_id or "(absent)",
        plan_status=plan_status or "(absent)",
        plan_artifact_version=plan_version or "(absent)",
        index_accepted_plan_id=accepted_id or "(absent)",
        index_accepted_plan_version=accepted_version or "(absent)",
        accepted_id_state=(
            "matches" if accepted_id == plan_id else "differs"
        ),
        accepted_version_state=(
            "matches" if accepted_version == plan_version else "differs"
        ),
        reviews=tuple(reviews),
    )

    declared_memory = plain(index_fields.get("Project memory path", ""))
    memory_parts = PurePosixPath(declared_memory).parts if declared_memory else ()
    authority = (
        _authority_link(
            "Canonical receipt path",
            plain(index_fields.get("Canonical receipt path", "")),
            "/".join((root.name, project, "handoffs", task_id, "receipt.md")),
            repository_root,
        ),
        _authority_link(
            "Project memory path",
            declared_memory,
            "/".join(
                (root.name, project, f"<one of {sorted(CANONICAL_MEMORY_FILES)}>")
            ),
            repository_root,
            matches=(
                len(memory_parts) == 3
                and list(memory_parts[:2]) == [root.name, project]
                and memory_parts[2] in CANONICAL_MEMORY_FILES
            ),
        ),
    )

    detail = validate_dossier(dossier, root, require_complete=True)
    return DossierSummary(
        task_id=task_id,
        level=level or "(absent)",
        project=project,
        path=str(relative),
        artifacts=tuple(states),
        plan_identity=plan_identity,
        authority_links=authority,
        independence=tuple(independence),
        unreadable=tuple(unreadable),
        diagnostics=tuple(diagnostic.format() for diagnostic in detail),
    )


def _select(
    projects_root: Path, task: str | None
) -> tuple[list[Path], list[Diagnostic]]:
    if not projects_root.is_dir():
        raise ScopeError(f"projects root cannot be evaluated: {projects_root}")
    try:
        dossiers, diagnostics = validate_projects(
            projects_root, require_complete=True
        )
    except OSError as error:
        raise ScopeError(f"projects root cannot be listed: {error}") from None

    if task is None:
        return dossiers, diagnostics

    matched = [dossier for dossier in dossiers if dossier.name == task]
    if not matched:
        raise ScopeError(f"--task {task!r} matches no discovered dossier")
    if len(matched) > 1:
        raise ScopeError(f"--task {task!r} matches more than one dossier")
    return matched, diagnostics


def render_summary_text(
    summaries: Sequence[DossierSummary], diagnostics: Sequence[Diagnostic]
) -> str:
    lines: list[str] = []
    for summary in summaries:
        lines.append(f"# Task dossier summary: {summary.task_id}")
        lines.append("")
        lines.append("## Identity")
        lines.append(f"- Task ID: {summary.task_id}")
        lines.append(f"- Task level: {summary.level}")
        lines.append(f"- Project: {summary.project}")
        lines.append(f"- Dossier path: {summary.path}")
        lines.append("")
        lines.append("## Artifact state")
        for state in summary.artifacts:
            lines.append(
                f"- {state.name}: applicability={state.applicability} "
                f"phase={state.phase_state}"
            )
        lines.append("")
        lines.append("## Evidence depth")
        for state in summary.artifacts:
            verdict = "meets" if state.meets_evidence_rule else "below"
            lines.append(
                f"- {state.name}: {state.evidence_items} item(s); rule="
                f"{EVIDENCE_RULES[state.evidence_rule]}; required="
                f"{state.evidence_required}; {verdict}"
            )
        lines.append("")
        lines.append("## Provenance")
        for state in summary.artifacts:
            lines.append(
                f"- {state.name}: authorship={state.authorship} "
                f"session={state.authoring_session} route={state.effective_route} "
                f"model={state.effective_model} effort={state.effective_effort}"
            )
        lines.append("")
        lines.append("## Plan and review identity")
        identity = summary.plan_identity
        lines.append(f"- Plan ID: {identity.plan_id}")
        lines.append(f"- Plan status: {identity.plan_status}")
        lines.append(f"- Plan artifact version: {identity.plan_artifact_version}")
        lines.append(
            f"- Index accepted plan ID: {identity.index_accepted_plan_id} "
            f"({identity.accepted_id_state})"
        )
        lines.append(
            f"- Index accepted plan version: {identity.index_accepted_plan_version} "
            f"({identity.accepted_version_state})"
        )
        for name, reviewed_id, reviewed_version, id_state, version_state in (
            identity.reviews
        ):
            lines.append(
                f"- {name}: reviewed plan ID={reviewed_id} ({id_state}); "
                f"reviewed plan version={reviewed_version} ({version_state})"
            )
        lines.append("")
        lines.append("## Authority links")
        for link in summary.authority_links:
            lines.append(
                f"- {link.label}: declared={link.declared}; expected="
                f"{link.expected}; matches={link.matches_expected}; "
                f"exists={link.exists}; not-a-symlink={link.not_a_symlink}; "
                f"no-symlinked-ancestor={link.no_symlinked_ancestor}; "
                f"contained={link.contained}"
            )
        lines.append(
            "- Health only. Invalidity is the validator's verdict, reported "
            "under Diagnostics."
        )
        lines.append("")
        lines.append("## Review independence")
        for arm in summary.independence:
            lines.append(
                f"- {arm.review}: reviewing session arm="
                f"{arm.reviewing_session_arm}; authoring session arm="
                f"{arm.authoring_session_arm}"
            )
        lines.append(f"- {INDEPENDENCE_CAVEAT}")
        lines.append("")
        lines.append("## Unreadable artifacts")
        if summary.unreadable:
            for name, reason in summary.unreadable:
                lines.append(f"- {name}: {reason}")
        else:
            lines.append("- none")
        lines.append("")
        lines.append("## Diagnostics")
        if summary.diagnostics:
            for diagnostic in summary.diagnostics:
                lines.append(f"- {diagnostic}")
        else:
            lines.append("- none for this dossier")
        lines.append("")

    lines.append("## Root verdict")
    lines.append(
        "- Source: validate_projects(root, require_complete=True); task "
        "selection never suppresses a root-level diagnostic."
    )
    if diagnostics:
        for diagnostic in diagnostics:
            lines.append(f"- {diagnostic.format()}")
        lines.append(f"- {len(diagnostics)} root-level diagnostic(s).")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def render_summary_json(
    summaries: Sequence[DossierSummary],
    diagnostics: Sequence[Diagnostic],
    exit_code: int,
) -> str:
    payload = {
        "independence_caveat": INDEPENDENCE_CAVEAT,
        "verdict_source": "validate_projects(root, require_complete=True)",
        "root_diagnostics": [diagnostic.format() for diagnostic in diagnostics],
        "dossiers": [asdict(summary) for summary in summaries],
        "exit_code": exit_code,
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize checkout-mode task dossiers (read-only)."
    )
    parser.add_argument(
        "projects_root",
        nargs="?",
        default="projects",
        type=Path,
        help="projects root containing <slug>/handoffs/<task-id>/index.md",
    )
    parser.add_argument(
        "--task", default=None, help="report only the dossier with this task ID"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit the machine-readable form"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        dossiers, diagnostics = _select(args.projects_root, args.task)
    except ScopeError as error:
        # A scope failure still prints whatever the root verdict found, so an
        # unmatched --task can never hide a partial-adoption or duplicate-ID
        # finding.
        print(f"task-dossier summary: {error}", file=sys.stderr)
        if args.projects_root.is_dir():
            try:
                _, root_diagnostics = validate_projects(
                    args.projects_root, require_complete=True
                )
            except OSError as listing_error:
                # The scope is already unevaluable; report why and keep exit 2
                # rather than turning a scope failure into a traceback.
                print(
                    f"task-dossier summary: root diagnostics unavailable: "
                    f"{listing_error}",
                    file=sys.stderr,
                )
            else:
                for diagnostic in root_diagnostics:
                    print(diagnostic.format(), file=sys.stderr)
        return 2

    summaries = [
        summarize_dossier(dossier, args.projects_root) for dossier in dossiers
    ]
    verdict = 1 if diagnostics else 0
    if args.json:
        sys.stdout.write(render_summary_json(summaries, diagnostics, verdict))
    else:
        sys.stdout.write(render_summary_text(summaries, diagnostics))
    return verdict


if __name__ == "__main__":
    raise SystemExit(main())
