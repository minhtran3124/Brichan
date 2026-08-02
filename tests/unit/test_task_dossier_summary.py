"""Deterministic read-only dossier summary.

The summary reports; it never decides validity. Every test here that asserts a
nonzero outcome asserts it against the validator's verdict, and the
authority-link rows are checked as *health* detail beside that verdict, never
as a second authority.
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "unit"))

from brichan.contracts.task_dossier import summary as summary_module
from brichan.contracts.task_dossier import validation as validation_module
from brichan.contracts.task_dossier.schema import ARTIFACTS
from brichan.contracts.task_dossier.summary import (
    INDEPENDENCE_CAVEAT,
    main as summary_main,
    render_summary_json,
    render_summary_text,
    summarize_dossier,
)

from test_task_dossier_validator import build_dossier

SECTIONS = (
    "## Identity",
    "## Artifact state",
    "## Evidence depth",
    "## Provenance",
    "## Plan and review identity",
    "## Authority links",
    "## Review independence",
    "## Unreadable artifacts",
    "## Diagnostics",
    "## Root verdict",
)


class SummaryBase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.checkout = Path(self.temporary_directory.name)
        self.projects = self.checkout / "projects"
        self.projects.mkdir(parents=True)

    def run_main(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = summary_main([str(self.projects), *arguments])
        return code, stdout.getvalue(), stderr.getvalue()


class SummaryReportTest(SummaryBase):
    def test_every_section_is_present_and_the_clean_case_exits_zero(self):
        build_dossier(self.projects)
        code, stdout, _ = self.run_main()
        self.assertEqual(0, code, stdout)
        for section in SECTIONS:
            with self.subTest(section=section):
                self.assertIn(section, stdout)
        for name in ARTIFACTS:
            self.assertIn(f"- {name}: applicability=", stdout)

    def test_the_independence_caveat_is_always_rendered(self):
        build_dossier(self.projects)
        _, stdout, _ = self.run_main()
        self.assertIn(INDEPENDENCE_CAVEAT, stdout)
        _, machine, _ = self.run_main("--json")
        self.assertEqual(INDEPENDENCE_CAVEAT, json.loads(machine)["independence_caveat"])

    def test_both_independence_arms_are_reported_separately(self):
        dossier = build_dossier(self.projects)
        report = summarize_dossier(dossier, self.projects)
        arms = {arm.review: arm for arm in report.independence}
        self.assertEqual("independent", arms["plan-review"].reviewing_session_arm)
        self.assertEqual("independent", arms["plan-review"].authoring_session_arm)

        shutil.rmtree(dossier)
        build_dossier(
            self.projects,
            overrides={"plan-review": {"Reviewing session": "session-planner"}},
        )
        report = summarize_dossier(dossier, self.projects)
        arms = {arm.review: arm for arm in report.independence}
        self.assertEqual("not-independent", arms["plan-review"].reviewing_session_arm)
        self.assertEqual("independent", arms["plan-review"].authoring_session_arm)

    def test_effective_provenance_is_read_from_the_artifacts(self):
        dossier = build_dossier(self.projects)
        report = summarize_dossier(dossier, self.projects)
        states = {state.name: state for state in report.artifacts}
        self.assertEqual("test-model", states["brief"].effective_model)
        self.assertEqual("plan", states["brief"].effective_route)
        self.assertEqual("medium", states["brief"].effective_effort)

    def test_no_routing_manifest_is_opened(self):
        build_dossier(self.projects)
        opened = []
        real_open = io.open

        def spy(path, *args, **kwargs):
            opened.append(str(path))
            return real_open(path, *args, **kwargs)

        with mock.patch("io.open", spy):
            self.run_main()
        self.assertEqual(
            [], [path for path in opened if path.endswith("model-routing.json")]
        )

    def test_text_and_json_carry_the_same_facts_and_exit_code(self):
        build_dossier(self.projects)
        text_code, text, _ = self.run_main()
        json_code, machine, _ = self.run_main("--json")
        self.assertEqual(text_code, json_code)
        payload = json.loads(machine)
        self.assertEqual(text_code, payload["exit_code"])
        dossier = payload["dossiers"][0]
        self.assertEqual("TASK-001", dossier["task_id"])
        self.assertIn(f"- Task ID: {dossier['task_id']}", text)
        self.assertEqual(len(ARTIFACTS), len(dossier["artifacts"]))
        self.assertEqual(
            "validate_projects(root, require_complete=True)",
            payload["verdict_source"],
        )

    def test_output_is_deterministic(self):
        build_dossier(self.projects)
        first = self.run_main()[1]
        second = self.run_main()[1]
        self.assertEqual(first, second)


class EvidenceDepthTest(SummaryBase):
    def test_the_passed_floor_and_the_not_required_rule_are_distinguished(self):
        for level, floor in (("0", 1), ("1", 2), ("2", 3)):
            with self.subTest(level=level):
                projects = self.checkout / f"projects-{level}"
                projects.mkdir()
                overrides = {
                    artifact: {"Task level": level} for artifact in ARTIFACTS
                }
                overrides["client-follow-up-questions"] = {
                    "Task level": level,
                    "Applicability": "not-required",
                    "Phase state": "not-required",
                    "Applicability rationale": "no client question applies",
                }
                if level == "2":
                    overrides["index"] = dict(overrides["index"])
                    overrides["index:extra"] = {
                        "Review route strength": "stronger",
                        "Review route override": "documented one-off override",
                    }
                dossier = build_dossier(
                    projects, overrides=overrides, evidence_items=floor
                )
                report = summarize_dossier(dossier, projects)
                states = {state.name: state for state in report.artifacts}

                self.assertEqual("level-floor", states["brief"].evidence_rule)
                self.assertEqual(floor, states["brief"].evidence_required)
                self.assertTrue(states["brief"].meets_evidence_rule)

                optional = states["client-follow-up-questions"]
                self.assertEqual("one-item", optional.evidence_rule)
                self.assertEqual(1, optional.evidence_required)
                self.assertTrue(
                    optional.meets_evidence_rule,
                    "a 'not-required' artifact meets a one-item rule, not the "
                    "level floor",
                )

    def test_a_pending_artifact_reports_no_floor_but_still_exits_nonzero(self):
        dossier = build_dossier(
            self.projects, overrides={"pr-desc": {"Phase state": "pending"}}
        )
        report = summarize_dossier(dossier, self.projects)
        states = {state.name: state for state in report.artifacts}
        self.assertEqual("not-applicable", states["pr-desc"].evidence_rule)
        code, _, _ = self.run_main()
        self.assertEqual(1, code, "the complete gate is the default semantics")


class AuthorityLinkHealthTest(SummaryBase):
    def links(self, dossier):
        report = summarize_dossier(dossier, self.projects)
        return {link.label: link for link in report.authority_links}

    def test_healthy_links_are_reported_healthy(self):
        dossier = build_dossier(self.projects)
        links = self.links(dossier)
        for label in ("Canonical receipt path", "Project memory path"):
            with self.subTest(label=label):
                link = links[label]
                self.assertTrue(link.matches_expected)
                self.assertTrue(link.exists)
                self.assertTrue(link.not_a_symlink)
                self.assertTrue(link.no_symlinked_ancestor)
                self.assertTrue(link.contained)

    def test_a_missing_target_is_reported(self):
        dossier = build_dossier(self.projects, receipt=False)
        self.assertFalse(self.links(dossier)["Canonical receipt path"].exists)

    def test_a_symlinked_target_is_reported(self):
        dossier = build_dossier(self.projects)
        memory = self.projects / "example" / "current-state.md"
        real = self.projects / "example" / "real-state.md"
        memory.rename(real)
        memory.symlink_to(real)
        link = self.links(dossier)["Project memory path"]
        self.assertFalse(link.not_a_symlink)

    def test_a_symlinked_ancestor_verdict_comes_from_the_validator(self):
        dossier = build_dossier(self.projects)
        example = self.projects / "example"
        real = self.projects / "real-example"
        example.rename(real)
        example.symlink_to(real)
        dossier = self.projects / "example" / "handoffs" / "TASK-001"

        link = self.links(dossier)["Project memory path"]
        self.assertFalse(link.no_symlinked_ancestor)

        # The summary reports health; the validator owns invalidity.
        diagnostics = validation_module.validate_dossier(dossier, self.projects)
        messages = " | ".join(item.format() for item in diagnostics)
        self.assertIn("symlinked ancestor", messages)
        code, _, _ = self.run_main()
        self.assertEqual(1, code)


class ExitBoundaryTest(SummaryBase):
    def test_an_existing_but_unreadable_index_exits_one(self):
        dossier = build_dossier(self.projects)
        (dossier / "index.md").chmod(0o000)
        self.addCleanup((dossier / "index.md").chmod, 0o644)
        code, stdout, _ = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("cannot read artifact", stdout)

    def test_an_unreadable_non_index_artifact_is_reported_not_omitted(self):
        dossier = build_dossier(self.projects)
        (dossier / "brief.md").chmod(0o000)
        self.addCleanup((dossier / "brief.md").chmod, 0o644)
        code, stdout, _ = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("## Unreadable artifacts", stdout)
        self.assertIn("brief.md", stdout)

    def test_root_level_partial_adoption_exits_one(self):
        dossier = build_dossier(self.projects)
        partial = self.projects / "example" / "handoffs" / "TASK-002"
        partial.mkdir(parents=True)
        shutil.copy(dossier / "plan.md", partial / "plan.md")
        code, stdout, _ = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("partial adoption", stdout)

    def test_a_receipt_only_handoff_contributes_no_diagnostic(self):
        build_dossier(self.projects)
        historical = self.projects / "example" / "handoffs" / "TASK-000"
        historical.mkdir(parents=True)
        (historical / "receipt.md").write_text("# Handoff receipt\n", encoding="utf-8")
        code, stdout, _ = self.run_main()
        self.assertEqual(0, code, stdout)

    def test_duplicate_task_ids_exit_one(self):
        build_dossier(self.projects)
        shutil.copytree(
            self.projects / "example", self.projects / "twin"
        )
        code, stdout, _ = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("duplicate task ID", stdout)

    def test_an_absent_projects_root_exits_two(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = summary_main([str(self.checkout / "absent")])
        self.assertEqual(2, code)

    def test_an_unmatched_task_exits_two_and_still_prints_root_diagnostics(self):
        dossier = build_dossier(self.projects)
        partial = self.projects / "example" / "handoffs" / "TASK-002"
        partial.mkdir(parents=True)
        shutil.copy(dossier / "plan.md", partial / "plan.md")
        code, _, stderr = self.run_main("--task", "TASK-404")
        self.assertEqual(2, code)
        self.assertIn("matches no discovered dossier", stderr)
        self.assertIn(
            "partial adoption",
            stderr,
            "an unmatched selection must never hide a root-level finding",
        )

    def test_an_unlistable_requested_dossier_exits_two(self):
        dossier = build_dossier(self.projects)
        dossier.chmod(0o000)
        self.addCleanup(dossier.chmod, 0o755)
        code, _, stderr = self.run_main("--task", "TASK-001")
        self.assertEqual(2, code)
        # Python 3.10 raises while globbing an unreadable directory; 3.11+
        # skips it. Either way the requested scope cannot be evaluated.
        self.assertTrue(
            "cannot be listed" in stderr
            or "matches no discovered dossier" in stderr,
            stderr,
        )

    def test_a_task_matching_more_than_one_dossier_exits_two(self):
        build_dossier(self.projects)
        shutil.copytree(self.projects / "example", self.projects / "twin")
        code, _, stderr = self.run_main("--task", "TASK-001")
        self.assertEqual(2, code)
        self.assertIn("matches more than one dossier", stderr)

    def test_selecting_one_task_never_suppresses_the_root_verdict(self):
        dossier = build_dossier(self.projects)
        other = self.projects / "second"
        shutil.copytree(self.projects / "example", other)
        broken = other / "handoffs" / "TASK-001"
        broken.rename(other / "handoffs" / "TASK-003")
        for path in (other / "handoffs" / "TASK-003").glob("*.md"):
            path.write_text(
                path.read_text(encoding="utf-8").replace("TASK-001", "TASK-003"),
                encoding="utf-8",
            )
        (other / "handoffs" / "TASK-003" / "brief.md").write_text(
            "# broken\n", encoding="utf-8"
        )
        code, stdout, _ = self.run_main("--task", "TASK-001")
        self.assertEqual(1, code)
        self.assertIn("TASK-003", stdout, "root diagnostics are always printed")
        self.assertEqual(
            1,
            sum(1 for line in stdout.splitlines() if line.startswith("# Task dossier")),
            "only the selected dossier is detailed",
        )


class PackageExportTest(unittest.TestCase):
    """The validator keeps the `main` binding; the CLIs are separate names."""

    def test_main_still_names_the_validator_and_the_clis_are_distinct(self):
        from brichan.contracts import task_dossier as package
        from brichan.contracts.task_dossier import generate as generate_module

        self.assertIs(validation_module.main, package.main)
        self.assertIs(generate_module.main, package.generate_main)
        self.assertIs(summary_module.main, package.summary_main)
        self.assertEqual(
            3,
            len({package.main, package.generate_main, package.summary_main}),
        )

    def test_the_public_surface_is_exported(self):
        from brichan.contracts import task_dossier as package

        for name in (
            "ArtifactRecord",
            "DossierSummary",
            "TaskRecord",
            "apply_generation",
            "generate_main",
            "load_record",
            "plan_generation",
            "render_artifact",
            "render_summary_json",
            "render_summary_text",
            "summarize_dossier",
            "summary_main",
        ):
            with self.subTest(name=name):
                self.assertIn(name, package.__all__)
                self.assertTrue(hasattr(package, name))


class ReadOnlyTest(SummaryBase):
    def test_the_summary_mutates_nothing(self):
        build_dossier(self.projects)
        before = {
            path: path.stat().st_mtime_ns
            for path in sorted(self.projects.rglob("*"))
        }
        self.run_main()
        self.run_main("--json")
        after = {
            path: path.stat().st_mtime_ns
            for path in sorted(self.projects.rglob("*"))
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
