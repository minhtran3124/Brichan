import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.contracts.task_dossier import validation as task_dossier
from brichan.contracts.task_dossier.schema import (
    ARTIFACTS,
    LEVEL_REQUIRED_ARTIFACTS,
    MINIMUM_EVIDENCE_ITEMS,
    RECOGNIZED_ARTIFACTS,
    REPORT_SECTIONS,
)


OWNERS = {
    "index": "coordinator",
    "request": "coordinator",
    "requirements": "planner",
    "brief": "planner",
    "options": "planner",
    "design": "planner",
    "client-follow-up-questions": "coordinator",
    "plan": "planner",
    "report": "implementer",
    "plan-review": "reviewer",
    "code-review": "reviewer",
    "pr-desc": "generator",
}

AUTHORING_SESSIONS = {
    "report": "session-implementer",
    "plan-review": "session-plan-reviewer",
    "code-review": "session-code-reviewer",
}


def _metadata(artifact, overrides):
    values = {
        "Task ID": "TASK-001",
        "Task level": "1",
        "Artifact": artifact,
        "Artifact version": "1",
        "Origin": f"TASK-001-{artifact}@1",
        "Owner": OWNERS[artifact],
        "Phase state": "passed",
        "Applicability": "required",
        "Applicability rationale": "null",
        "Authorship": "model",
        "Authoring session": AUTHORING_SESSIONS.get(artifact, "session-planner"),
        "Effective route": "plan",
        "Effective model": "test-model",
        "Effective effort": "medium",
        "Reviewing session": "null",
        "Review verdict": "null",
    }
    if artifact == "request":
        values["Origin"] = "user-request"
    if artifact in ("plan-review", "code-review"):
        values["Reviewing session"] = AUTHORING_SESSIONS[artifact]
        values["Review verdict"] = "PASS"
    values.update(overrides.get(artifact, {}))
    return "\n".join(f"- {label}: `{value}`" for label, value in values.items())


def _body(evidence_items=2):
    evidence = "\n".join(
        f"- `src/brichan/contracts/task_dossier/validation.py` line {index}"
        for index in range(1, evidence_items + 1)
    )
    return (
        "## Claim or decision\n\n"
        "The dossier contract is implemented as specified.\n\n"
        "## Evidence\n\n"
        f"{evidence}\n\n"
        "## Uncertainty\n\n"
        "- No unresolved uncertainty remains.\n"
    )


def _extra(artifact, overrides):
    sections = {
        "index": (
            "Task identity",
            {
                "Task ID": "TASK-001",
                "Task level": "1",
                "Project": "example",
                "Canonical receipt path": (
                    "projects/example/handoffs/TASK-001/receipt.md"
                ),
                "Project memory path": "projects/example/current-state.md",
                "Accepted plan ID": "PLAN-1",
                "Accepted plan version": "1",
                "Review route strength": "routine",
                "Review route override": "null",
                "Ship authorization": "not-requested",
                "Ship authorization evidence": "null",
            },
        ),
        "request": (
            "Request provenance",
            {"Redaction applied": "yes", "Mutability": "immutable"},
        ),
        "plan": (
            "Plan status",
            {"Plan ID": "PLAN-1", "Plan status": "accepted"},
        ),
        "plan-review": (
            "Review target",
            {"Reviewed plan ID": "PLAN-1", "Reviewed plan version": "1"},
        ),
        "code-review": (
            "Review target",
            {"Reviewed plan ID": "PLAN-1", "Reviewed plan version": "1"},
        ),
        "pr-desc": (
            "Remote action",
            {"Remote action authorized": "no"},
        ),
    }
    if artifact == "report":
        bodies = overrides.get("report:sections", {})
        return "".join(
            f"## {section}\n\n"
            f"{bodies.get(section, f'- The worker report {section.lower()} entry.')}\n\n"
            for section in REPORT_SECTIONS
        )
    if artifact not in sections:
        return ""
    heading, values = sections[artifact]
    values = dict(values)
    values.update(overrides.get(f"{artifact}:extra", {}))
    fields = "\n".join(f"- {label}: `{value}`" for label, value in values.items())
    return f"## {heading}\n\n{fields}\n\n"


def _status_table(overrides, artifacts):
    rows = ["| Artifact | Applicability | Phase state | Path |", "| --- | --- | --- | --- |"]
    for artifact in artifacts:
        artifact_overrides = overrides.get(artifact, {})
        applicability = artifact_overrides.get("Applicability", "required")
        phase = artifact_overrides.get("Phase state", "passed")
        rows.append(
            f"| `{artifact}` | `{applicability}` | `{phase}` | `{artifact}.md` |"
        )
    return "## Artifact status\n\n" + "\n".join(rows) + "\n\n"


def build_dossier(
    root,
    *,
    overrides=None,
    evidence_items=2,
    receipt=True,
    memory=True,
    artifacts=ARTIFACTS,
):
    """Write a valid dossier that tests then perturb.

    The default is the complete eleven-artifact level-1 shape every dossier
    written before the worker report carries; ``artifacts`` narrows it.
    """
    overrides = overrides or {}
    dossier = root / "example" / "handoffs" / "TASK-001"
    dossier.mkdir(parents=True, exist_ok=True)
    if memory:
        (root / "example" / "current-state.md").write_text(
            "# current state\n", encoding="utf-8"
        )
    for artifact in artifacts:
        text = f"# {artifact}\n\n## Artifact metadata\n\n"
        text += _metadata(artifact, overrides) + "\n\n"
        text += _extra(artifact, overrides)
        if artifact == "index":
            text += _status_table(overrides, artifacts)
        text += _body(evidence_items)
        (dossier / f"{artifact}.md").write_text(text, encoding="utf-8")
    if receipt:
        (dossier / "receipt.md").write_text("# Handoff receipt\n", encoding="utf-8")
    return dossier


def merge_overrides(*layers):
    merged = {}
    for layer in layers:
        for key, values in layer.items():
            merged[key] = {**merged.get(key, {}), **values}
    return merged


def level_overrides(level):
    """Overrides that declare ``level`` consistently across every artifact."""
    overrides = {name: {"Task level": level} for name in RECOGNIZED_ARTIFACTS}
    overrides["index:extra"] = {
        "Task level": level,
        "Review route strength": "stronger" if level == "2" else "routine",
        "Review route override": (
            "one-off stronger review route" if level == "2" else "null"
        ),
    }
    return overrides


def build_reduced_dossier(root, level, *, overrides=None, **kwargs):
    """Write a valid reduced level-0/1 dossier: no plan, a worker report."""
    unplanned = {
        "index:extra": {"Accepted plan ID": "null", "Accepted plan version": "null"},
        "code-review:extra": {
            "Reviewed plan ID": "null",
            "Reviewed plan version": "null",
        },
    }
    kwargs.setdefault("evidence_items", MINIMUM_EVIDENCE_ITEMS[level])
    kwargs.setdefault("artifacts", LEVEL_REQUIRED_ARTIFACTS[level])
    return build_dossier(
        root,
        overrides=merge_overrides(level_overrides(level), unplanned, overrides or {}),
        **kwargs,
    )


WAIVED_CODE_REVIEW = {
    "code-review": {
        "Phase state": "not-required",
        "Applicability": "not-required",
        "Applicability rationale": "diff touches no contract path",
        "Reviewing session": "null",
        "Review verdict": "null",
    }
}


class DossierValidatorBase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.projects = Path(self.temporary_directory.name) / "projects"
        self.projects.mkdir(parents=True)

    def validate(self, dossier, **kwargs):
        return task_dossier.validate_dossier(dossier, self.projects, **kwargs)

    def messages(self, diagnostics):
        return " | ".join(diagnostic.format() for diagnostic in diagnostics)

    def assert_valid(self, dossier, **kwargs):
        diagnostics = self.validate(dossier, **kwargs)
        self.assertEqual([], diagnostics, self.messages(diagnostics))

    def assert_reports(self, dossier, needle, **kwargs):
        diagnostics = self.validate(dossier, **kwargs)
        self.assertTrue(
            any(needle in diagnostic.format() for diagnostic in diagnostics),
            f"expected {needle!r} in: {self.messages(diagnostics)}",
        )
        return diagnostics


class TaskDossierValidatorTest(DossierValidatorBase):
    def test_complete_level_1_dossier_is_valid(self):
        dossier = build_dossier(self.projects)
        self.assert_valid(dossier)
        self.assert_valid(dossier, require_complete=True)

    def test_level_2_requires_every_standard_artifact(self):
        for artifact in ARTIFACTS:
            with self.subTest(artifact=artifact):
                dossier = build_dossier(
                    self.projects,
                    evidence_items=3,
                    overrides=level_overrides("2"),
                )
                self.assert_valid(dossier)
                (dossier / f"{artifact}.md").unlink()
                self.assert_reports(dossier, f"required task-dossier artifact {artifact}.md")

    def test_missing_canonical_receipt_fails(self):
        dossier = build_dossier(self.projects, receipt=False)
        self.assert_reports(dossier, "canonical receipt does not exist")

    def test_index_must_link_the_canonical_receipt(self):
        dossier = build_dossier(
            self.projects,
            overrides={"index:extra": {"Canonical receipt path": "null"}},
        )
        self.assert_reports(dossier, "links its canonical handoff receipt")

    def test_index_must_not_duplicate_receipt_authority(self):
        dossier = build_dossier(self.projects)
        index = dossier / "index.md"
        index.write_text(
            index.read_text(encoding="utf-8") + "\n## Review verdict\n\n- PASS\n",
            encoding="utf-8",
        )
        self.assert_reports(dossier, "the receipt and project memory remain canonical")

    def test_empty_artifact_fails(self):
        dossier = build_dossier(self.projects)
        (dossier / "brief.md").write_text("", encoding="utf-8")
        self.assert_reports(dossier, "artifact is empty")

    def test_placeholder_evidence_fails(self):
        dossier = build_dossier(self.projects)
        design = dossier / "design.md"
        text = design.read_text(encoding="utf-8")
        text = text.split("## Evidence")[0] + (
            "## Evidence\n\n- `<repository or source evidence>`\n\n"
            "## Uncertainty\n\n- none\n"
        )
        design.write_text(text, encoding="utf-8")
        self.assert_reports(dossier, "concrete evidence item")

    def test_not_required_needs_rationale_and_evidence(self):
        dossier = build_dossier(
            self.projects,
            overrides={
                "options": {
                    "Phase state": "not-required",
                    "Applicability": "not-required",
                    "Applicability rationale": "null",
                }
            },
        )
        self.assert_reports(dossier, "requires a concrete rationale")

        dossier = build_dossier(
            self.projects,
            overrides={
                "options": {
                    "Phase state": "not-required",
                    "Applicability": "not-required",
                    "Applicability rationale": "one credible option only",
                }
            },
        )
        self.assert_valid(dossier)

    def test_not_required_without_evidence_fails(self):
        dossier = build_dossier(
            self.projects,
            evidence_items=0,
            overrides={
                "options": {
                    "Phase state": "not-required",
                    "Applicability": "not-required",
                    "Applicability rationale": "one credible option only",
                }
            },
        )
        self.assert_reports(dossier, "is never evidence")

    def test_unsupported_phase_state_fails(self):
        dossier = build_dossier(
            self.projects, overrides={"brief": {"Phase state": "done"}}
        )
        self.assert_reports(dossier, "Phase state")

    def test_model_authored_artifact_records_effective_route(self):
        dossier = build_dossier(
            self.projects, overrides={"design": {"Effective model": "null"}}
        )
        self.assert_reports(dossier, "effective session, route, model, and effort")

    def test_human_authored_artifact_records_no_model_provenance(self):
        dossier = build_dossier(
            self.projects,
            overrides={"request": {"Authorship": "human"}},
        )
        self.assert_reports(dossier, "must leave model provenance null")

    def test_stale_reviewed_plan_version_fails(self):
        dossier = build_dossier(
            self.projects,
            overrides={"plan-review:extra": {"Reviewed plan version": "2"}},
        )
        self.assert_reports(dossier, "exact accepted plan version")

    def test_index_accepted_plan_version_must_match_plan(self):
        dossier = build_dossier(
            self.projects,
            overrides={"index:extra": {"Accepted plan version": "3"}},
        )
        self.assert_reports(dossier, "Accepted plan version")

    def test_missing_review_verdict_fails(self):
        dossier = build_dossier(
            self.projects, overrides={"code-review": {"Review verdict": "null"}}
        )
        self.assert_reports(dossier, "review artifacts require")

    def test_reviewer_must_not_author_the_plan(self):
        dossier = build_dossier(
            self.projects, overrides={"plan": {"Owner": "reviewer"}}
        )
        self.assert_reports(dossier, "must not back-write planning artifacts")

    def test_plan_review_requires_an_independent_session(self):
        dossier = build_dossier(
            self.projects,
            overrides={"plan-review": {"Authoring session": "session-planner"}},
        )
        self.assert_reports(dossier, "independent of the plan author")

    def test_unsafe_request_provenance_fails(self):
        dossier = build_dossier(
            self.projects,
            overrides={"request:extra": {"Redaction applied": "no"}},
        )
        self.assert_reports(dossier, "must be redacted before storage")

    def test_mutable_request_provenance_fails(self):
        dossier = build_dossier(
            self.projects,
            overrides={"request:extra": {"Mutability": "mutable"}},
        )
        self.assert_reports(dossier, "request provenance is read-only")

    def test_personal_paths_are_rejected(self):
        dossier = build_dossier(self.projects)
        brief = dossier / "brief.md"
        brief.write_text(
            brief.read_text(encoding="utf-8") + "\n- /Users/example/notes.md\n",
            encoding="utf-8",
        )
        self.assert_reports(dossier, "personal or home path is forbidden")

    def test_pr_text_never_authorizes_remote_action(self):
        dossier = build_dossier(
            self.projects,
            overrides={"pr-desc:extra": {"Remote action authorized": "yes"}},
        )
        self.assert_reports(dossier, "never authorizes remote action")

    def test_pr_text_must_not_instruct_remote_mutation(self):
        dossier = build_dossier(self.projects)
        pr_desc = dossier / "pr-desc.md"
        pr_desc.write_text(
            pr_desc.read_text(encoding="utf-8") + "\nThen run git push origin main.\n",
            encoding="utf-8",
        )
        self.assert_reports(dossier, "must not instruct remote mutation")

    def test_unauthorized_ship_state_fails(self):
        dossier = build_dossier(
            self.projects,
            overrides={"index:extra": {"Ship authorization": "user-authorized"}},
        )
        self.assert_reports(dossier, "requires recorded user authorization evidence")

    def test_level_2_requires_a_stronger_reviewer(self):
        overrides = {
            artifact: {"Task level": "2"} for artifact in ARTIFACTS
        }
        dossier = build_dossier(
            self.projects,
            evidence_items=3,
            overrides={**overrides, "index:extra": {"Task level": "2"}},
        )
        self.assert_reports(dossier, "level 2 requires a documented stronger reviewer")

    def test_full_legacy_dossier_stays_valid_at_every_level(self):
        """The eleven-artifact shape every existing dossier carries (no report).

        A dossier that carries plan.md satisfies levels 0 and 1 without a
        worker report, and its status table lists exactly its eleven rows.
        """
        for level, items in MINIMUM_EVIDENCE_ITEMS.items():
            with self.subTest(level=level):
                enough = build_dossier(
                    self.projects,
                    evidence_items=items,
                    overrides=level_overrides(level),
                )
                self.assertFalse((enough / "report.md").exists())
                self.assert_valid(enough)
                self.assert_valid(enough, require_complete=True)

                if items > 1:
                    too_thin = build_dossier(
                        self.projects,
                        evidence_items=items - 1,
                        overrides=level_overrides(level),
                    )
                    self.assert_reports(too_thin, f"level {level} requires at least")

    def test_task_level_must_agree_with_the_index(self):
        dossier = build_dossier(
            self.projects, overrides={"design": {"Task level": "2"}}
        )
        self.assert_reports(dossier, "expected '1' from index.md")

    def test_task_identity_is_branch_independent_and_path_derived(self):
        dossier = build_dossier(
            self.projects, overrides={"brief": {"Task ID": "TASK-002"}}
        )
        self.assert_reports(dossier, "from the canonical dossier path")

    def test_unstable_task_directory_is_rejected(self):
        dossier = self.projects / "example" / "handoffs" / "feature-branch"
        dossier.mkdir(parents=True)
        (dossier / "index.md").write_text("# index\n", encoding="utf-8")
        self.assert_reports(dossier, "branch-independent task ID")

    def test_symlinked_artifact_is_rejected(self):
        dossier = build_dossier(self.projects)
        target = dossier / "design.md"
        target.unlink()
        target.symlink_to(dossier / "brief.md")
        self.assert_reports(dossier, "must not be symlinks")

    def test_require_complete_rejects_unsettled_phases(self):
        dossier = build_dossier(
            self.projects, overrides={"code-review": {"Phase state": "active"}}
        )
        self.assert_reports(dossier, "completed tasks require", require_complete=True)

    def test_status_table_must_match_artifact_state(self):
        dossier = build_dossier(self.projects)
        index = dossier / "index.md"
        index.write_text(
            index.read_text(encoding="utf-8").replace(
                "| `brief` | `required` | `passed` | `brief.md` |",
                "| `brief` | `required` | `not-required` | `brief.md` |",
            ),
            encoding="utf-8",
        )
        self.assert_reports(dossier, "index says 'not-required' but brief.md says")

    def test_duplicate_task_ids_are_reported(self):
        build_dossier(self.projects)
        duplicate = self.projects / "other" / "handoffs" / "TASK-001"
        duplicate.mkdir(parents=True)
        (duplicate / "index.md").write_text("# index\n", encoding="utf-8")
        _, diagnostics = task_dossier.validate_projects(self.projects)
        self.assertTrue(
            any("duplicate task ID" in item.format() for item in diagnostics),
            self.messages(diagnostics),
        )

    def test_discovery_only_tracks_dossiers_with_an_index(self):
        untracked = self.projects / "example" / "handoffs" / "TASK-009"
        untracked.mkdir(parents=True)
        (untracked / "receipt.md").write_text("# receipt\n", encoding="utf-8")
        self.assertEqual([], task_dossier.discover_dossiers(self.projects))

    # --- review remediation: finding 5, 'not-required' keeps the contract ---

    def test_not_required_still_requires_a_claim(self):
        dossier = build_dossier(
            self.projects,
            overrides={
                "options": {
                    "Phase state": "not-required",
                    "Applicability": "not-required",
                    "Applicability rationale": "one credible option only",
                }
            },
        )
        options = dossier / "options.md"
        options.write_text(
            options.read_text(encoding="utf-8").replace(
                "The dossier contract is implemented as specified.",
                "`<claim or decision>`",
            ),
            encoding="utf-8",
        )
        self.assert_reports(
            dossier, "'not-required' requires a concrete claim or decision"
        )

    def test_not_required_still_requires_stated_uncertainty(self):
        dossier = build_dossier(
            self.projects,
            overrides={
                "options": {
                    "Phase state": "not-required",
                    "Applicability": "not-required",
                    "Applicability rationale": "one credible option only",
                }
            },
        )
        options = dossier / "options.md"
        text = options.read_text(encoding="utf-8")
        options.write_text(
            text.split("## Uncertainty")[0] + "## Uncertainty\n\n", encoding="utf-8"
        )
        self.assert_reports(
            dossier, "'not-required' must concretely state unresolved uncertainty"
        )

    # --- review remediation: finding 2, completion gates ---

    def test_require_complete_rejects_an_unaccepted_plan(self):
        dossier = build_dossier(
            self.projects, overrides={"plan:extra": {"Plan status": "draft"}}
        )
        self.assert_reports(
            dossier, "require an accepted plan", require_complete=True
        )

    def test_require_complete_rejects_a_not_required_plan_review_at_level_2(self):
        waived = {
            "plan-review": {
                "Phase state": "not-required",
                "Applicability": "not-required",
                "Applicability rationale": "skipped",
            }
        }
        dossier = build_dossier(
            self.projects,
            evidence_items=3,
            overrides=merge_overrides(level_overrides("2"), waived),
        )
        self.assert_reports(
            dossier,
            "plan review applies to every level 2 task",
            require_complete=True,
        )

        # Levels 0 and 1 have no plan review, so a present one may be waived.
        dossier = build_dossier(
            self.projects, overrides=merge_overrides(level_overrides("1"), waived)
        )
        self.assert_valid(dossier, require_complete=True)

    def test_require_complete_rejects_a_changes_required_review(self):
        for artifact in ("plan-review", "code-review"):
            with self.subTest(artifact=artifact):
                dossier = build_dossier(
                    self.projects,
                    overrides={artifact: {"Review verdict": "CHANGES REQUIRED"}},
                )
                self.assert_valid(dossier)
                self.assert_reports(
                    dossier, "require a PASS verdict", require_complete=True
                )

    def test_level_0_code_review_may_be_not_required_with_evidence(self):
        dossier = build_dossier(
            self.projects,
            evidence_items=1,
            overrides=merge_overrides(level_overrides("0"), WAIVED_CODE_REVIEW),
        )
        self.assert_valid(dossier)
        self.assert_valid(dossier, require_complete=True)

    def test_reviewing_session_must_be_independent_of_the_plan_author(self):
        for artifact in ("plan-review", "code-review"):
            with self.subTest(artifact=artifact):
                dossier = build_dossier(
                    self.projects,
                    overrides={artifact: {"Reviewing session": "session-planner"}},
                )
                self.assert_reports(
                    dossier,
                    f"Reviewing session: {artifact} requires a session independent",
                )

    def test_levels_0_and_1_must_not_gate_a_ship(self):
        for level, items in (("0", 1), ("1", 2)):
            with self.subTest(level=level):
                overrides = {artifact: {"Task level": level} for artifact in ARTIFACTS}
                dossier = build_dossier(
                    self.projects,
                    evidence_items=items,
                    overrides={
                        **overrides,
                        "index:extra": {
                            "Task level": level,
                            "Ship authorization": "user-authorized",
                            "Ship authorization evidence": "user said ship it",
                        },
                    },
                )
                self.assert_reports(dossier, f"level {level} does not gate a ship")

    def test_level_2_may_ship_only_with_recorded_evidence(self):
        overrides = {artifact: {"Task level": "2"} for artifact in ARTIFACTS}
        extra = {
            "Task level": "2",
            "Review route strength": "stronger",
            "Review route override": "one-off stronger review route",
        }
        authorized = build_dossier(
            self.projects,
            evidence_items=3,
            overrides={
                **overrides,
                "index:extra": {
                    **extra,
                    "Ship authorization": "user-authorized",
                    "Ship authorization evidence": "recorded user decision 2026-08-02",
                },
            },
        )
        self.assert_valid(authorized)
        self.assert_valid(authorized, require_complete=True)

        unevidenced = build_dossier(
            self.projects,
            evidence_items=3,
            overrides={
                **overrides,
                "index:extra": {**extra, "Ship authorization": "user-authorized"},
            },
        )
        self.assert_reports(
            unevidenced, "requires recorded user authorization evidence"
        )

    # --- review remediation: finding 4, canonical authority links ---

    def test_canonical_receipt_path_must_match_this_task_exactly(self):
        for wrong in (
            "projects/example/handoffs/TASK-002/receipt.md",
            "projects/other/handoffs/TASK-001/receipt.md",
            "receipt.md",
        ):
            with self.subTest(path=wrong):
                dossier = build_dossier(
                    self.projects,
                    overrides={"index:extra": {"Canonical receipt path": wrong}},
                )
                self.assert_reports(dossier, "must be exactly")

    def test_unsafe_canonical_receipt_path_is_rejected(self):
        dossier = build_dossier(
            self.projects,
            overrides={
                "index:extra": {
                    "Canonical receipt path": "../../../etc/receipt.md"
                }
            },
        )
        self.assert_reports(dossier, "must be a safe repo-relative path")

    def test_index_must_link_project_memory(self):
        dossier = build_dossier(
            self.projects,
            overrides={"index:extra": {"Project memory path": "null"}},
        )
        self.assert_reports(dossier, "links its canonical project memory")

    def test_project_memory_link_must_be_safe_and_in_project(self):
        cases = {
            "../../../../etc/passwd": "must be a safe repo-relative path",
            "projects/other/current-state.md": "must name a file directly inside",
            "projects/example/handoffs/TASK-001/index.md": (
                "must name a file directly inside"
            ),
            "projects/example/secrets.md": "must be one of",
        }
        for value, needle in cases.items():
            with self.subTest(path=value):
                dossier = build_dossier(
                    self.projects,
                    overrides={"index:extra": {"Project memory path": value}},
                )
                self.assert_reports(dossier, needle)

    def test_missing_project_memory_file_is_reported(self):
        dossier = build_dossier(self.projects, memory=False)
        self.assert_reports(dossier, "project memory file does not exist")

    def test_symlinked_project_memory_is_rejected(self):
        dossier = build_dossier(self.projects)
        memory = self.projects / "example" / "current-state.md"
        memory.unlink()
        memory.symlink_to(dossier / "index.md")
        self.assert_reports(
            dossier, "Project memory path: must not be a symlink"
        )

    def test_index_must_not_repeat_receipt_owned_fields(self):
        for label in ("Verdict", "Diff evidence", "Brida-owned panes closed"):
            with self.subTest(label=label):
                dossier = build_dossier(self.projects)
                index = dossier / "index.md"
                index.write_text(
                    index.read_text(encoding="utf-8") + f"\n- {label}: `PASS`\n",
                    encoding="utf-8",
                )
                self.assert_reports(dossier, f"field.{label}")

    def test_index_must_carry_only_the_artifact_status_table(self):
        dossier = build_dossier(self.projects)
        index = dossier / "index.md"
        index.write_text(
            index.read_text(encoding="utf-8")
            + "\n| Command | Result |\n| --- | --- |\n| `make check` | `pass` |\n",
            encoding="utf-8",
        )
        self.assert_reports(dossier, "only table the index may carry")

    # --- review remediation: finding 3, partial adoption ---

    def test_receipt_only_handoffs_stay_exempt(self):
        historical = self.projects / "example" / "handoffs" / "TASK-900"
        historical.mkdir(parents=True)
        (historical / "receipt.md").write_text("# receipt\n", encoding="utf-8")
        (historical / "task-packet.md").write_text("# packet\n", encoding="utf-8")
        dossiers, diagnostics = task_dossier.validate_projects(self.projects)
        self.assertEqual([], dossiers)
        self.assertEqual([], diagnostics, self.messages(diagnostics))

    def test_pre_contract_planning_notes_keep_the_exemption(self):
        historical = self.projects / "example" / "handoffs" / "TASK-902"
        historical.mkdir(parents=True)
        (historical / "receipt.md").write_text("# receipt\n", encoding="utf-8")
        (historical / "plan.md").write_text(
            "# TASK-902 plan\n\n## Objective\n\nDo the work.\n", encoding="utf-8"
        )
        self.assertEqual({}, task_dossier.discover_partial_dossiers(self.projects))
        _, diagnostics = task_dossier.validate_projects(self.projects)
        self.assertEqual([], diagnostics, self.messages(diagnostics))

    def test_scaffolded_dossier_missing_its_index_is_reported(self):
        partial = self.projects / "example" / "handoffs" / "TASK-903"
        build_dossier(self.projects)
        partial.mkdir(parents=True)
        source = self.projects / "example" / "handoffs" / "TASK-001"
        for name in ("plan", "design"):
            (partial / f"{name}.md").write_text(
                (source / f"{name}.md").read_text(encoding="utf-8"), encoding="utf-8"
            )
        self.assertEqual(
            {partial: ["design", "plan"]},
            task_dossier.discover_partial_dossiers(self.projects),
        )

    def test_partial_adoption_without_an_index_is_reported(self):
        partial = self.projects / "example" / "handoffs" / "TASK-901"
        partial.mkdir(parents=True)
        (partial / "receipt.md").write_text("# receipt\n", encoding="utf-8")
        (partial / "plan.md").write_text(
            "# plan\n\n## Artifact metadata\n\n- Artifact: `plan`\n",
            encoding="utf-8",
        )
        self.assertEqual(
            {partial: ["plan"]},
            task_dossier.discover_partial_dossiers(self.projects),
        )
        _, diagnostics = task_dossier.validate_projects(self.projects)
        self.assertTrue(
            any("partial adoption" in item.format() for item in diagnostics),
            self.messages(diagnostics),
        )
        self.assertTrue(
            any("plan.md" in item.format() for item in diagnostics),
            self.messages(diagnostics),
        )

    # --- second re-review: residual 1, placeholder uncertainty ---

    def _replace_uncertainty(self, dossier, artifact, body):
        path = dossier / f"{artifact}.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.split("## Uncertainty")[0] + f"## Uncertainty\n\n{body}",
            encoding="utf-8",
        )

    def test_passed_artifact_rejects_template_uncertainty(self):
        template_items = (
            "- `<unresolved uncertainty, or a recorded statement that none remains>`\n",
            "- `<unresolved uncertainty>`\n",
            "- TBD\n",
            "- null\n",
            "`<unresolved uncertainty>`\n",
            "pending\n",
        )
        for body in template_items:
            with self.subTest(body=body.strip()):
                dossier = build_dossier(self.projects)
                self._replace_uncertainty(dossier, "design", body)
                self.assert_reports(
                    dossier,
                    "passed artifacts must concretely state unresolved uncertainty",
                )

    def test_not_required_rejects_template_uncertainty(self):
        dossier = build_dossier(
            self.projects,
            overrides={
                "options": {
                    "Phase state": "not-required",
                    "Applicability": "not-required",
                    "Applicability rationale": "one credible option only",
                }
            },
        )
        self._replace_uncertainty(
            dossier,
            "options",
            "- `<unresolved uncertainty, or a recorded statement that none remains>`\n",
        )
        self.assert_reports(
            dossier, "'not-required' must concretely state unresolved uncertainty"
        )

    def test_blocked_artifact_rejects_template_uncertainty(self):
        dossier = build_dossier(
            self.projects, overrides={"design": {"Phase state": "blocked"}}
        )
        self._replace_uncertainty(dossier, "design", "- `<unresolved uncertainty>`\n")
        self.assert_reports(dossier, "blocked artifacts require concrete")

    def test_concrete_uncertainty_is_accepted_as_prose_or_items(self):
        for body in (
            "- No unresolved uncertainty remains.\n",
            "No unresolved uncertainty remains.\n",
            "- Level thresholds are unproven until the pilot runs.\n",
        ):
            with self.subTest(body=body.strip()):
                dossier = build_dossier(self.projects)
                self._replace_uncertainty(dossier, "design", body)
                self.assert_valid(dossier)

    # --- second re-review: residual 3, index projection sections only ---

    def test_index_must_not_copy_project_memory_sections(self):
        for section in (
            "Current state",
            "Overview",
            "Tasks",
            "Decisions",
            "References",
        ):
            with self.subTest(section=section):
                dossier = build_dossier(self.projects)
                index = dossier / "index.md"
                index.write_text(
                    index.read_text(encoding="utf-8")
                    + f"\n## {section}\n\nCopied from project memory.\n",
                    encoding="utf-8",
                )
                self.assert_reports(
                    dossier, f"section.{section}: project-memory-owned section"
                )

    def test_index_rejects_any_section_outside_the_projection(self):
        dossier = build_dossier(self.projects)
        index = dossier / "index.md"
        index.write_text(
            index.read_text(encoding="utf-8") + "\n## Notes\n\nSide commentary.\n",
            encoding="utf-8",
        )
        self.assert_reports(dossier, "is not an index projection section")

    def test_index_projection_sections_stay_valid(self):
        dossier = build_dossier(self.projects)
        self.assert_valid(dossier)
        from brichan.contracts.task_dossier.schema import INDEX_PROJECTION_SECTIONS

        text = (dossier / "index.md").read_text(encoding="utf-8")
        for section in INDEX_PROJECTION_SECTIONS:
            self.assertIn(f"## {section}", text)

    def test_cli_reports_success_and_failure(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = task_dossier.main([str(self.projects)])
        self.assertEqual(0, code)
        self.assertIn("Validated 0 task dossier(s)", stdout.getvalue())

        build_dossier(self.projects, overrides={"brief": {"Owner": "wizard"}})
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = task_dossier.main([str(self.projects)])
        self.assertEqual(1, code)
        self.assertIn("Invalid task dossiers", stderr.getvalue())

    def test_a_symlinked_ancestor_above_the_receipt_is_diagnosed(self):
        """A real receipt reached through a symlinked directory is invalid.

        The leaf being a genuine file is not enough: a link above it decides
        which file the declared path reaches.
        """
        dossier = build_dossier(self.projects)
        handoffs = self.projects / "example" / "handoffs"
        real = self.projects / "example" / "handoffs-real"
        handoffs.rename(real)
        handoffs.symlink_to(real)
        dossier = self.projects / "example" / "handoffs" / "TASK-001"

        diagnostics = self.assert_reports(
            dossier,
            "must not reach the canonical receipt through a symlinked ancestor",
        )
        named = [
            diagnostic
            for diagnostic in diagnostics
            if "symlinked ancestor" in diagnostic.message
        ]
        self.assertEqual(1, len(named), self.messages(diagnostics))
        self.assertEqual("index.md", named[0].path.name)
        self.assertEqual(
            "Task identity.Canonical receipt path", named[0].field
        )

    def test_a_symlinked_ancestor_above_project_memory_is_diagnosed(self):
        dossier = build_dossier(self.projects)
        example = self.projects / "example"
        real = self.projects / "example-real"
        example.rename(real)
        example.symlink_to(real)
        dossier = self.projects / "example" / "handoffs" / "TASK-001"

        diagnostics = self.assert_reports(
            dossier, "must not reach project memory through a symlinked ancestor"
        )
        named = [
            diagnostic
            for diagnostic in diagnostics
            if diagnostic.field.endswith("Project memory path")
        ]
        self.assertEqual(1, len(named), self.messages(diagnostics))
        self.assertEqual("index.md", named[0].path.name)

    def test_the_clean_authority_case_is_unchanged(self):
        """Neither new diagnostic fires on a dossier with real directories."""
        dossier = build_dossier(self.projects)
        diagnostics = self.validate(dossier)
        self.assertEqual([], diagnostics, self.messages(diagnostics))
        self.assertNotIn("symlinked ancestor", self.messages(diagnostics))

    def test_exactly_two_ancestor_diagnostics_are_added(self):
        source = (
            ROOT / "src/brichan/contracts/task_dossier/validation.py"
        ).read_text(encoding="utf-8")
        # one definition plus exactly two call sites: the receipt link and the
        # project-memory link, and nothing else.
        self.assertEqual(3, source.count("_symlinked_ancestor("))
        self.assertEqual(1, source.count("def _symlinked_ancestor("))

    def test_cli_reports_missing_projects_root(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = task_dossier.main([str(self.projects / "absent")])
        self.assertEqual(2, code)


class ReducedDossierValidatorTest(DossierValidatorBase):
    """Levels 0 and 1: a worker report carries the plan; no plan artifacts."""

    def test_reduced_level_0_dossier_with_a_waived_code_review_is_valid(self):
        dossier = build_reduced_dossier(
            self.projects, "0", overrides=WAIVED_CODE_REVIEW
        )
        self.assertEqual(
            sorted(
                ["index.md", "request.md", "report.md", "code-review.md", "receipt.md"]
            ),
            sorted(path.name for path in dossier.glob("*.md")),
        )
        self.assert_valid(dossier)
        self.assert_valid(dossier, require_complete=True)

    def test_reduced_level_1_dossier_with_an_independent_review_is_valid(self):
        dossier = build_reduced_dossier(self.projects, "1")
        self.assert_valid(dossier)
        self.assert_valid(dossier, require_complete=True)

    def test_reduced_dossier_without_a_report_is_rejected(self):
        for level in ("0", "1"):
            with self.subTest(level=level):
                dossier = build_reduced_dossier(self.projects, level)
                (dossier / "report.md").unlink()
                self.assert_reports(
                    dossier, "required task-dossier artifact report.md is missing"
                )

    def test_a_symlinked_plan_does_not_excuse_the_report(self):
        dossier = build_dossier(self.projects)
        self.assert_valid(dossier)
        plan = dossier / "plan.md"
        plan.unlink()
        plan.symlink_to(dossier / "design.md")
        self.assert_reports(
            dossier, "required task-dossier artifact report.md is missing"
        )

    def test_an_unreadable_plan_does_not_excuse_the_report(self):
        dossier = build_dossier(self.projects)
        self.assert_valid(dossier)
        (dossier / "plan.md").write_bytes(b"\xff\xfe not utf-8\n")
        diagnostics = self.assert_reports(
            dossier, "required task-dossier artifact report.md is missing"
        )
        self.assertIn(
            "plan.md: file: cannot read artifact", self.messages(diagnostics)
        )

    def test_a_symlinked_required_artifact_is_not_also_reported_missing(self):
        dossier = build_reduced_dossier(self.projects, "1")
        report = dossier / "report.md"
        report.unlink()
        report.symlink_to(dossier / "request.md")
        diagnostics = self.assert_reports(dossier, "must not be symlinks")
        self.assertNotIn("report.md is missing", self.messages(diagnostics))

    def test_an_unreadable_plan_is_absent_for_every_review_target_rule(self):
        dossier = build_dossier(self.projects)
        self.assert_valid(dossier)
        (dossier / "plan.md").write_bytes(b"\xff\xfe not utf-8\n")
        diagnostics = self.assert_reports(
            dossier, "required task-dossier artifact report.md is missing"
        )
        messages = self.messages(diagnostics)
        for review in ("plan-review", "code-review"):
            self.assertIn(
                f"{review}.md: Review target.Reviewed plan ID: a dossier without "
                "plan.md has no plan to review",
                messages,
            )
        self.assertNotIn("Reviewed plan ID: expected ''", messages)

    def test_an_unknown_level_gets_the_deepest_evidence_floor(self):
        dossier = build_reduced_dossier(self.projects, "1")
        diagnostics = []
        artifact = task_dossier.parse_artifact(
            dossier / "request.md", "request", diagnostics
        )
        self.assertEqual([], diagnostics)
        task_dossier._validate_state(artifact, "bogus", diagnostics)
        self.assertIn(
            f"requires at least {MINIMUM_EVIDENCE_ITEMS['2']} concrete evidence "
            "item(s), found 2",
            self.messages(diagnostics),
        )

    def test_levels_1_and_2_may_not_waive_code_review(self):
        dossier = build_reduced_dossier(
            self.projects, "1", overrides=WAIVED_CODE_REVIEW
        )
        self.assert_reports(dossier, "level 1 requires an independent code review")

        dossier = build_dossier(
            self.projects,
            evidence_items=3,
            overrides=merge_overrides(level_overrides("2"), WAIVED_CODE_REVIEW),
        )
        self.assert_reports(dossier, "level 2 requires an independent code review")

    def test_a_passed_report_requires_concrete_report_sections(self):
        for section in ("Plan", "Verification"):
            with self.subTest(section=section):
                dossier = build_reduced_dossier(
                    self.projects,
                    "1",
                    overrides={
                        "report:sections": {section: "- `<placeholder>`"}
                    },
                )
                diagnostics = self.assert_reports(
                    dossier, "a passed worker report requires a concrete statement"
                )
                self.assertIn(
                    f"report.md: {section}:", self.messages(diagnostics)
                )

    def test_the_report_sections_are_structurally_required(self):
        dossier = build_reduced_dossier(self.projects, "1")
        report = dossier / "report.md"
        text = report.read_text(encoding="utf-8")
        report.write_text(
            text.replace("## Changes\n", "## Notes\n"), encoding="utf-8"
        )
        self.assert_reports(dossier, "section.Changes: expected exactly one section")

    def test_code_review_must_be_independent_of_the_report_author(self):
        for label in ("Reviewing session", "Authoring session"):
            with self.subTest(label=label):
                dossier = build_reduced_dossier(
                    self.projects,
                    "1",
                    overrides={"code-review": {label: "session-implementer"}},
                )
                self.assert_reports(
                    dossier,
                    f"{label}: code-review requires a session independent of "
                    "the report author",
                )

    def test_reviewer_must_not_author_the_report(self):
        dossier = build_reduced_dossier(
            self.projects, "1", overrides={"report": {"Owner": "reviewer"}}
        )
        self.assert_reports(dossier, "must not back-write planning artifacts")

    def test_review_targets_stay_null_without_a_plan(self):
        dossier = build_reduced_dossier(
            self.projects,
            "1",
            overrides={"code-review:extra": {"Reviewed plan ID": "PLAN-1"}},
        )
        self.assert_reports(
            dossier, "Review target.Reviewed plan ID: a dossier without plan.md"
        )

    def test_status_table_lists_exactly_required_and_present_artifacts(self):
        dossier = build_reduced_dossier(self.projects, "1")
        index = dossier / "index.md"
        original = index.read_text(encoding="utf-8")
        report_row = "| `report` | `required` | `passed` | `report.md` |\n"
        self.assertIn(report_row, original)

        index.write_text(original.replace(report_row, ""), encoding="utf-8")
        self.assert_reports(
            dossier, "Artifact status.report: every required or present artifact"
        )

        index.write_text(
            original.replace(
                report_row,
                report_row + "| `design` | `required` | `passed` | `design.md` |\n",
            ),
            encoding="utf-8",
        )
        self.assert_reports(
            dossier,
            "Artifact status.design: design.md is neither required at this "
            "level nor present",
        )

    def test_require_complete_rejects_a_changes_required_reduced_review(self):
        dossier = build_reduced_dossier(
            self.projects,
            "1",
            overrides={"code-review": {"Review verdict": "CHANGES REQUIRED"}},
        )
        self.assert_valid(dossier)
        self.assert_reports(dossier, "require a PASS verdict", require_complete=True)

    def test_an_invalid_level_fails_closed_to_level_2(self):
        dossier = build_reduced_dossier(
            self.projects,
            "1",
            overrides={
                name: {"Task level": "two"} for name in RECOGNIZED_ARTIFACTS
            },
        )
        diagnostics = self.assert_reports(dossier, "found 'two'")
        joined = self.messages(diagnostics)
        for name in ARTIFACTS:
            if name in LEVEL_REQUIRED_ARTIFACTS["1"]:
                continue
            self.assertIn(f"required task-dossier artifact {name}.md", joined)
        self.assertIn("level 2 requires at least 3", joined)

    def test_a_missing_index_fails_closed_to_level_2(self):
        dossier = build_reduced_dossier(self.projects, "0")
        (dossier / "index.md").unlink()
        joined = self.messages(self.validate(dossier))
        for name in ARTIFACTS:
            if name == "request" or name == "code-review":
                continue
            self.assertIn(f"required task-dossier artifact {name}.md", joined)

    def test_a_report_alone_without_an_index_is_partial_adoption(self):
        source = build_reduced_dossier(self.projects, "1")
        partial = self.projects / "example" / "handoffs" / "TASK-904"
        partial.mkdir(parents=True)
        (partial / "report.md").write_text(
            (source / "report.md").read_text(encoding="utf-8"), encoding="utf-8"
        )
        self.assertEqual(
            {partial: ["report"]},
            task_dossier.discover_partial_dossiers(self.projects),
        )


if __name__ == "__main__":
    unittest.main()
