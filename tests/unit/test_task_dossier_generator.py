"""Structured-record loading, rendering, publication, and generator safety.

The literal eleven-artifact record in the accepted design is the fixture: it is
extracted from `design.md` itself, so the document and the implementation
cannot drift apart silently.

Several tests here establish a *diagnostic path* only. A comment marks each
one. None of them is evidence of detection against a non-cooperating process
running under the same OS identity: that process is outside the threat model,
and the post-publication check is a point-in-time observation, never a
compare-and-swap.
"""

import contextlib
import copy
import errno
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.contracts.task_dossier import generate as generate_module
from brichan.contracts.task_dossier import record as record_module
from brichan.contracts.task_dossier.generate import (
    apply_generation,
    main as generate_main,
    plan_generation,
    render_artifact,
)
from brichan.contracts.task_dossier.record import (
    ARTIFACT_KEYS,
    RecordError,
    RecordFileError,
    TOP_LEVEL_KEYS,
    load_record,
    load_record_text,
)
from brichan.contracts.task_dossier.schema import ARTIFACTS
from brichan.contracts.task_dossier.validation import validate_dossier

DESIGN = ROOT / "projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md"
GENERATOR_SOURCES = (
    "record.py",
    "generate.py",
    "summary.py",
)


def design_record_blocks():
    """Return every fenced JSON block in the accepted design artifact."""
    text = DESIGN.read_text(encoding="utf-8")
    return re.findall(r"^```json\n(.*?)^```$", text, re.MULTILINE | re.DOTALL)


def worked_record():
    """The literal complete eleven-artifact record, parsed."""
    return json.loads(design_record_blocks()[0])


class RecordLoadingTest(unittest.TestCase):
    """One named refusal per malformed class. Nothing is repaired."""

    def setUp(self):
        self.payload = worked_record()

    def load(self, payload=None, **overrides):
        arguments = {
            "task_id": "SYNTH-010",
            "level": "0",
            "project": "synthetic-level0",
        }
        arguments.update(overrides)
        text = payload if isinstance(payload, str) else json.dumps(
            self.payload if payload is None else payload
        )
        return load_record_text(text, **arguments)

    def assert_refused(self, needle, payload=None, **overrides):
        with self.assertRaises(RecordError) as caught:
            self.load(payload, **overrides)
        joined = " | ".join(caught.exception.diagnostics)
        self.assertIn(needle, joined, joined)
        return joined

    # -- the record the design promises ---------------------------------

    def test_worked_record_loads(self):
        record = self.load()
        self.assertEqual("SYNTH-010", record.task_id)
        self.assertEqual(set(ARTIFACTS), set(record.artifacts))

    # -- malformed input ------------------------------------------------

    def test_malformed_json_is_refused(self):
        self.assert_refused("record", "{")

    def test_non_object_root_is_refused(self):
        self.assert_refused("must be exactly dict", "[]")

    def test_non_utf8_record_file_is_a_scope_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            path.write_bytes(b"\xff\xfe{")
            with self.assertRaises(RecordFileError):
                load_record(
                    path,
                    task_id="SYNTH-010",
                    level="0",
                    project="synthetic-level0",
                )

    def test_duplicate_top_level_key_is_refused(self):
        text = json.dumps(self.payload)
        injected = text.replace('{"schema_version": 1', '{"schema_version": 1, "schema_version": 1', 1)
        self.assert_refused("duplicate key", injected)

    def test_duplicate_key_inside_an_artifact_is_refused(self):
        text = json.dumps(self.payload)
        injected = text.replace(
            '"index": {"version": 1', '"index": {"version": 1, "version": 1', 1
        )
        self.assert_refused("duplicate key", injected)

    def test_boolean_in_an_integer_position_is_refused(self):
        self.payload["artifacts"]["index"]["version"] = True
        self.assert_refused("must be exactly int")

    def test_wrong_exact_types_are_refused(self):
        cases = {
            "schema_version": "1",
            "task_id": 10,
            "index_identity": [],
            "artifacts": [],
        }
        for key, value in cases.items():
            with self.subTest(key=key):
                payload = copy.deepcopy(self.payload)
                payload[key] = value
                self.assert_refused("must be exactly", payload)

    def test_list_and_dict_positions_require_their_exact_type(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["index"]["evidence"] = "one item"
        self.assert_refused("must be exactly list", payload)
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["index"]["fields"] = []
        self.assert_refused("must be exactly dict", payload)

    def test_the_null_string_is_not_a_null(self):
        self.payload["artifacts"]["index"]["review_verdict"] = "null"
        self.assert_refused("placeholder is not a value")

    def test_unknown_and_missing_top_level_keys_are_refused(self):
        payload = copy.deepcopy(self.payload)
        payload["extra"] = 1
        self.assert_refused("unknown key", payload)
        for key in TOP_LEVEL_KEYS:
            with self.subTest(key=key):
                payload = copy.deepcopy(self.payload)
                del payload[key]
                self.assert_refused("missing key", payload)

    def test_unknown_missing_and_misspelled_artifacts_are_refused(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["invented"] = payload["artifacts"]["index"]
        self.assert_refused("unknown key", payload)

        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["pr_desc"] = payload["artifacts"].pop("pr-desc")
        joined = self.assert_refused("unknown key", payload)
        self.assertIn("missing key", joined)

        payload = copy.deepcopy(self.payload)
        del payload["artifacts"]["design"]
        self.assert_refused("missing key", payload)

    def test_unknown_and_missing_artifact_keys_are_refused(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["brief"]["extra"] = 1
        self.assert_refused("unknown key", payload)
        for key in ARTIFACT_KEYS:
            with self.subTest(key=key):
                payload = copy.deepcopy(self.payload)
                del payload["artifacts"]["brief"][key]
                self.assert_refused("missing key", payload)

    # -- identity and cross-record consistency --------------------------

    def test_identity_must_equal_the_command_line(self):
        self.assert_refused("must equal the requested", task_id="SYNTH-999")
        self.assert_refused("must equal the requested", level="1")
        self.assert_refused("must equal the requested", project="other-project")

    def test_accepted_plan_identity_must_match_the_plan(self):
        payload = copy.deepcopy(self.payload)
        payload["index_identity"]["Accepted plan ID"] = "SYNTH-010-P2"
        self.assert_refused("must equal artifacts.plan.fields", payload)

        payload = copy.deepcopy(self.payload)
        payload["index_identity"]["Accepted plan version"] = 2
        self.assert_refused("must equal artifacts.plan.version", payload)

    def test_reviews_must_name_the_exact_plan_version_and_id(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["plan-review"]["fields"]["Reviewed plan version"] = "2"
        self.assert_refused("must equal the decimal string", payload)

        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["code-review"]["fields"]["Reviewed plan ID"] = "OTHER-1"
        self.assert_refused("must equal artifacts.plan.fields", payload)

    def test_a_review_may_not_reuse_the_plan_authoring_session(self):
        for label in ("reviewing_session", "authoring_session"):
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payload)
                payload["artifacts"]["plan-review"][label] = payload["artifacts"][
                    "plan"
                ]["authoring_session"]
                self.assert_refused("independent of the plan author", payload)

    # -- judgment-bearing values ----------------------------------------

    def test_placeholders_are_refused_in_concrete_positions(self):
        for locator, mutate in (
            ("claim", lambda p: p["artifacts"]["brief"].__setitem__("claim", "TBD")),
            (
                "evidence",
                lambda p: p["artifacts"]["brief"].__setitem__("evidence", ["pending"]),
            ),
            (
                "uncertainty",
                lambda p: p["artifacts"]["brief"].__setitem__(
                    "uncertainty", ["unknown"]
                ),
            ),
        ):
            with self.subTest(locator=locator):
                payload = copy.deepcopy(self.payload)
                mutate(payload)
                self.assert_refused("placeholder is not a value", payload)

    def test_evidence_below_the_applicable_rule_is_refused(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["brief"]["evidence"] = []
        self.assert_refused("at least one concrete item", payload)

        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["client-follow-up-questions"]["evidence"] = []
        self.assert_refused("at least one concrete item", payload)

    def test_level_floor_is_enforced_against_the_requested_level(self):
        payload = copy.deepcopy(self.payload)
        payload["level"] = "1"
        with self.assertRaises(RecordError) as caught:
            self.load(payload, level="1")
        joined = " | ".join(caught.exception.diagnostics)
        self.assertIn("level 1 requires at least 2 concrete evidence item(s)", joined)

    def test_missing_and_invalid_review_verdicts_are_refused(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["plan-review"]["review_verdict"] = None
        payload["artifacts"]["plan-review"]["reviewing_session"] = None
        self.assert_refused("a passed review requires", payload)

        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["plan-review"]["review_verdict"] = "LGTM"
        self.assert_refused("must be one of ['CHANGES REQUIRED', 'PASS']", payload)

    def test_unpaired_not_required_state_is_refused(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["client-follow-up-questions"]["applicability"] = "required"
        self.assert_refused("must be declared together", payload)

    def test_non_null_rationale_on_a_required_artifact_is_refused(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["brief"]["applicability_rationale"] = "because"
        self.assert_refused("must leave the rationale null", payload)

    def test_provenance_is_recorded_or_null_together(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["brief"]["effective_model"] = None
        self.assert_refused("must record the effective", payload)

        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["brief"]["authorship"] = "human"
        self.assert_refused("must leave model provenance null", payload)

    def test_personal_paths_are_refused(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["brief"]["evidence"] = ["/Users/someone/notes.md"]
        self.assert_refused("personal or home path is forbidden", payload)

    def test_unsafe_memory_path_is_refused(self):
        payload = copy.deepcopy(self.payload)
        payload["index_identity"]["Project memory path"] = "../escape.md"
        self.assert_refused("safe repository-relative path", payload)

        payload = copy.deepcopy(self.payload)
        payload["index_identity"]["Project memory path"] = (
            "projects/synthetic-level0/notes.md"
        )
        self.assert_refused("must be one of", payload)

    def test_derived_index_fields_may_not_be_supplied(self):
        for label in ("Task ID", "Task level", "Project", "Canonical receipt path"):
            with self.subTest(label=label):
                payload = copy.deepcopy(self.payload)
                payload["index_identity"][label] = "anything"
                self.assert_refused("the generator derives", payload)

    def test_index_may_not_declare_supplemental_sections(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["index"]["sections"] = [
            {"title": "Extra", "body": ["text"]}
        ]
        self.assert_refused("may not declare supplemental sections", payload)

    # -- structural injection, one case per position class --------------

    def test_backtick_wrapped_positions_refuse_structure(self):
        for value, needle in (
            ("has `backtick", "backtick"),
            ("has | pipe", "pipe"),
            ("has\nnewline", "newline"),
        ):
            with self.subTest(value=value):
                payload = copy.deepcopy(self.payload)
                payload["artifacts"]["brief"]["effective_model"] = value
                self.assert_refused(needle, payload)

    def test_free_text_positions_refuse_structure(self):
        for value, needle in (
            ("# heading", "must not start with '#'"),
            ("| a | b |", "must not render as a table row"),
            ("line\nfeed", "single line"),
        ):
            with self.subTest(value=value):
                payload = copy.deepcopy(self.payload)
                payload["artifacts"]["brief"]["evidence"] = [value]
                self.assert_refused(needle, payload)

    def test_body_elements_are_exactly_one_rendered_line(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["plan"]["sections"] = [
            {"title": "Steps", "body": ["first\nsecond"]}
        ]
        self.assert_refused("an embedded line feed is forbidden", payload)

        for value, needle in (
            ("# heading", "must not start with '#'"),
            ("| a | b |", "must not render as a table row"),
            ("- Label: value", "'- <label>:' field line"),
        ):
            with self.subTest(value=value):
                payload = copy.deepcopy(self.payload)
                payload["artifacts"]["plan"]["sections"] = [
                    {"title": "Steps", "body": [value]}
                ]
                self.assert_refused(needle, payload)

    def test_a_safe_multi_line_claim_is_accepted(self):
        """The required pair: body refuses line feeds, claim permits them."""
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["brief"]["claim"] = (
            "Synthetic non-authoritative fixture data; it proves no real review.\n"
            "A second line states the same thing without structure."
        )
        record = self.load(payload)
        rendered = render_artifact(record, "brief")
        self.assertIn("A second line states the same thing", rendered)

    def test_claim_refuses_structural_lines_per_line(self):
        for value, needle in (
            ("fine\n# heading", "must not start with '#'"),
            ("fine\n| a | b |", "must not render as a table row"),
            ("fine\n- Label: value", "'- <label>:' field line"),
            ("fine\n```python", "must not open or close a fenced block"),
        ):
            with self.subTest(value=value):
                payload = copy.deepcopy(self.payload)
                payload["artifacts"]["brief"]["claim"] = value
                self.assert_refused(needle, payload)

    def test_a_backticked_path_line_evidence_item_is_accepted(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["brief"]["evidence"] = [
            "`src/brichan/contracts/task_dossier/schema.py:17-29` names the artifacts."
        ]
        record = self.load(payload)
        self.assertIn(
            "- `src/brichan/contracts/task_dossier/schema.py:17-29`",
            render_artifact(record, "brief"),
        )

    def test_section_titles_are_unique_and_do_not_collide(self):
        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["plan"]["sections"] = [
            {"title": "Steps", "body": ["one"]},
            {"title": "Steps", "body": ["two"]},
        ]
        self.assert_refused("section titles must be unique", payload)

        payload = copy.deepcopy(self.payload)
        payload["artifacts"]["plan"]["sections"] = [
            {"title": "Evidence", "body": ["one"]}
        ]
        self.assert_refused("collides with the required section", payload)


class DesignExtractionTest(unittest.TestCase):
    """The design artifact is the fixture, so the two cannot drift apart."""

    def test_design_carries_exactly_one_complete_record(self):
        blocks = design_record_blocks()
        self.assertEqual(1, len(blocks))
        payload = json.loads(blocks[0])
        self.assertEqual(list(ARTIFACTS), list(payload["artifacts"]))
        for name, artifact in payload["artifacts"].items():
            with self.subTest(artifact=name):
                self.assertEqual(17, len(artifact))
                self.assertEqual(set(ARTIFACT_KEYS), set(artifact))

    def test_the_four_cross_record_rules_hold_in_the_literal_record(self):
        payload = worked_record()
        plan = payload["artifacts"]["plan"]
        self.assertEqual("accepted", plan["fields"]["Plan status"])
        self.assertEqual(
            plan["fields"]["Plan ID"], payload["index_identity"]["Accepted plan ID"]
        )
        self.assertEqual(
            plan["version"], payload["index_identity"]["Accepted plan version"]
        )
        for name in ("plan-review", "code-review"):
            review = payload["artifacts"][name]
            self.assertEqual(
                str(plan["version"]), review["fields"]["Reviewed plan version"]
            )
            self.assertEqual(
                plan["fields"]["Plan ID"], review["fields"]["Reviewed plan ID"]
            )
            self.assertNotEqual(
                plan["authoring_session"], review["reviewing_session"]
            )
            self.assertNotEqual(
                plan["authoring_session"], review["authoring_session"]
            )

    def test_the_literal_record_renders_and_validates_clean(self):
        with tempfile.TemporaryDirectory() as directory:
            projects = Path(directory) / "projects"
            (projects / "synthetic-level0").mkdir(parents=True)
            (projects / "synthetic-level0" / "current-state.md").write_text(
                "# Current state\n", encoding="utf-8"
            )
            record_path = Path(directory) / "record.json"
            record_path.write_text(
                json.dumps(worked_record()), encoding="utf-8"
            )
            record = load_record(
                record_path,
                task_id="SYNTH-010",
                level="0",
                project="synthetic-level0",
            )
            apply_generation(record, projects)
            dossier = projects / "synthetic-level0" / "handoffs" / "SYNTH-010"
            (dossier / "receipt.md").write_text(
                "# Handoff receipt\n", encoding="utf-8"
            )
            for gate in (False, True):
                with self.subTest(require_complete=gate):
                    diagnostics = validate_dossier(
                        dossier, projects, require_complete=gate
                    )
                    self.assertEqual(
                        [],
                        diagnostics,
                        " | ".join(item.format() for item in diagnostics),
                    )


class GeneratorRoutingNeutralityTest(unittest.TestCase):
    """Two arms. Neither one alone discharges the requirement."""

    def test_static_arm_no_forbidden_spelling_in_the_generator_sources(self):
        package = ROOT / "src/brichan/contracts/task_dossier"
        for name in GENERATOR_SOURCES:
            with self.subTest(module=name):
                source = (package / name).read_text(encoding="utf-8")
                self.assertNotIn("model-routing.json", source)
                self.assertNotIn("model_routing", source)

    def test_import_arm_a_real_dry_run_opens_no_routing_manifest(self):
        """Import, generate for real, and inspect every opened path.

        This runs in a fresh interpreter on purpose: the `sys.modules`
        assertion is only meaningful when no unrelated test in the same
        process has already imported the routing module.
        """
        program = textwrap.dedent(
            """
            import io, json, os, sys, tempfile
            from pathlib import Path

            sys.path.insert(0, sys.argv[1])
            opened = []

            real_os_open, real_io_open = os.open, io.open

            def spy_os_open(path, *args, **kwargs):
                opened.append(str(path))
                return real_os_open(path, *args, **kwargs)

            def spy_io_open(path, *args, **kwargs):
                opened.append(str(path))
                return real_io_open(path, *args, **kwargs)

            os.open, io.open = spy_os_open, spy_io_open
            try:
                from brichan.contracts.task_dossier.generate import (
                    main as generate_main,
                )

                with tempfile.TemporaryDirectory() as directory:
                    projects = Path(directory) / "projects"
                    (projects / "synthetic-level0").mkdir(parents=True)
                    record = Path(directory) / "record.json"
                    record.write_text(sys.argv[2], encoding="utf-8")
                    code = generate_main([
                        "SYNTH-010", "--level", "0",
                        "--project", "synthetic-level0",
                        "--record", str(record),
                        "--projects-root", str(projects),
                    ])
            finally:
                os.open, io.open = real_os_open, real_io_open

            routing_opens = [p for p in opened if p.endswith("model-routing.json")]
            routing_modules = [m for m in sys.modules if "model_routing" in m]
            print(json.dumps({
                "code": code,
                "opened": len(opened),
                "routing_opens": routing_opens,
                "routing_modules": routing_modules,
            }))
            """
        )
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                program,
                str(ROOT / "src"),
                json.dumps(worked_record()),
            ],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(0, report["code"])
        self.assertGreater(report["opened"], 0, "the spy recorded nothing")
        self.assertEqual([], report["routing_opens"])
        self.assertEqual([], report["routing_modules"])


class GenerationBase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.checkout = Path(self.temporary_directory.name)
        self.projects = self.checkout / "projects"
        (self.projects / "synthetic-level0").mkdir(parents=True)
        (self.projects / "synthetic-level0" / "current-state.md").write_text(
            "# Current state\n", encoding="utf-8"
        )
        self.record_path = self.checkout / "record.json"
        self.record_path.write_text(json.dumps(worked_record()), encoding="utf-8")
        self.record = load_record(
            self.record_path,
            task_id="SYNTH-010",
            level="0",
            project="synthetic-level0",
        )
        self.dossier = self.projects / "synthetic-level0" / "handoffs" / "SYNTH-010"

    def artifacts_present(self):
        if not self.dossier.is_dir():
            return []
        return sorted(path.name for path in self.dossier.glob("*.md"))

    def leaves(self):
        if not self.dossier.is_dir():
            return []
        return sorted(path.name for path in self.dossier.iterdir())


class GenerationTest(GenerationBase):
    def test_dry_run_writes_nothing(self):
        actions = plan_generation(self.record, self.projects)
        self.assertFalse(self.dossier.exists())
        self.assertEqual(
            len(ARTIFACTS),
            sum(1 for action in actions if action.action == "create"),
        )

    def test_apply_publishes_every_artifact_and_no_temporary_leaf(self):
        apply_generation(self.record, self.projects)
        self.assertEqual(
            sorted(f"{name}.md" for name in ARTIFACTS), self.artifacts_present()
        )
        self.assertEqual(self.artifacts_present(), self.leaves())

    def test_rendering_is_deterministic(self):
        first = render_artifact(self.record, "index")
        second = render_artifact(self.record, "index")
        self.assertEqual(first, second)
        for forbidden in (str(ROOT), str(os.getpid()), "/Users/", "/home/"):
            self.assertNotIn(forbidden, first)

    def test_only_mechanically_derivable_values_are_derived(self):
        index = render_artifact(self.record, "index")
        self.assertIn("- Task ID: `SYNTH-010`", index)
        self.assertIn("- Task level: `0`", index)
        self.assertIn("- Artifact: `index`", index)
        self.assertIn("- Owner: `coordinator`", index)
        self.assertIn("- Project: `synthetic-level0`", index)
        self.assertIn(
            "- Canonical receipt path: "
            "`projects/synthetic-level0/handoffs/SYNTH-010/receipt.md`",
            index,
        )
        self.assertIn("| `index` | `required` | `passed` | `index.md` |", index)
        # A judgment-bearing value is copied, never inferred.
        self.assertIn("- Review verdict: `null`", index)
        self.assertIn(
            "- Review verdict: `PASS`", render_artifact(self.record, "plan-review")
        )

    def test_an_existing_artifact_is_never_overwritten(self):
        self.dossier.mkdir(parents=True)
        (self.dossier / "brief.md").write_text("hand written\n", encoding="utf-8")
        with self.assertRaises(generate_module.GenerationError) as caught:
            apply_generation(self.record, self.projects)
        self.assertIn("partial adoption", str(caught.exception))
        self.assertEqual(
            "hand written\n",
            (self.dossier / "brief.md").read_text(encoding="utf-8"),
        )
        # Every other artifact is complete; nothing is published half-written.
        self.assertEqual(
            sorted(f"{name}.md" for name in ARTIFACTS), self.artifacts_present()
        )

    def cli(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = generate_main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cli_exit_codes(self):
        code, _, _ = self.cli(
            [
                "SYNTH-010", "--level", "0", "--project", "synthetic-level0",
                "--record", str(self.record_path),
                "--projects-root", str(self.projects),
            ]
        )
        self.assertEqual(0, code)

        code, _, stderr = self.cli(
            [
                "SYNTH-010", "--level", "0", "--project", "synthetic-level0",
                "--record", str(self.checkout / "absent.json"),
                "--projects-root", str(self.projects),
            ]
        )
        self.assertEqual(2, code)
        self.assertIn("cannot read record", stderr)

        code, _, _ = self.cli(
            [
                "SYNTH-010", "--level", "0", "--project", "synthetic-level0",
                "--record", str(self.record_path),
                "--projects-root", str(self.checkout / "absent"),
            ]
        )
        self.assertEqual(2, code)

        code, _, stderr = self.cli(
            [
                "SYNTH-999", "--level", "0", "--project", "synthetic-level0",
                "--record", str(self.record_path),
                "--projects-root", str(self.projects),
            ]
        )
        self.assertEqual(1, code)
        self.assertIn("must equal the requested", stderr)


class NamespaceSafetyTest(GenerationBase):
    """Symlinks, lock ordering, and namespace drift."""

    def assert_symlinked_component_refused(self, link):
        """A symlinked component inside the root is refused by the walk.

        The decoy stays inside the projects root so that containment passes
        and the refusal is demonstrably the ``O_NOFOLLOW`` walk rather than the
        earlier identity check.
        """
        decoy = self.projects / "decoy"
        decoy.mkdir(exist_ok=True)
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(decoy)
        with self.assertRaises(generate_module.GenerationError) as caught:
            apply_generation(self.record, self.projects)
        self.assertIn("symlink or not a directory", str(caught.exception))
        self.assertEqual([], sorted(decoy.iterdir()))

    def test_a_component_symlinked_outside_the_root_is_refused(self):
        escape = self.checkout / "escape"
        escape.mkdir()
        (self.projects / "synthetic-level0").rename(self.projects / "real")
        (self.projects / "synthetic-level0").symlink_to(escape)
        with self.assertRaises(ValueError) as caught:
            apply_generation(self.record, self.projects)
        self.assertIn("must stay inside", str(caught.exception))
        self.assertEqual([], sorted(escape.iterdir()))

    def test_a_symlinked_project_directory_is_refused(self):
        (self.projects / "synthetic-level0").rename(self.projects / "real")
        self.assert_symlinked_component_refused(self.projects / "synthetic-level0")

    def test_a_symlinked_handoffs_directory_is_refused(self):
        self.assert_symlinked_component_refused(
            self.projects / "synthetic-level0" / "handoffs"
        )

    def test_a_symlinked_dossier_directory_is_refused(self):
        self.assert_symlinked_component_refused(self.dossier)

    def test_a_non_directory_component_is_refused(self):
        handoffs = self.projects / "synthetic-level0" / "handoffs"
        handoffs.write_text("not a directory\n", encoding="utf-8")
        with self.assertRaises(generate_module.GenerationError) as caught:
            apply_generation(self.record, self.projects)
        self.assertIn("symlink or not a directory", str(caught.exception))

    def test_a_swapped_ancestor_cannot_redirect_a_held_descriptor(self):
        """Diagnostic path only.

        This proves the descriptor keeps writing into the inode it opened and
        that the final re-walk refuses to report success. It is NOT evidence of
        detection against the excluded non-cooperating same-identity process.
        """
        self.dossier.mkdir(parents=True)
        decoy = self.checkout / "decoy"
        decoy.mkdir()
        real_inode = self.dossier.stat().st_ino

        original_flock = generate_module.fcntl.flock

        def swap_then_lock(descriptor, operation):
            result = original_flock(descriptor, operation)
            handoffs = self.projects / "synthetic-level0" / "handoffs"
            target = handoffs / "SYNTH-010"
            if not target.is_symlink():
                target.rename(handoffs / "moved")
                target.symlink_to(decoy)
            return result

        with mock.patch.object(generate_module.fcntl, "flock", swap_then_lock):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)
        self.assertIn("namespace drift", str(caught.exception))
        self.assertEqual([], sorted(decoy.iterdir()))
        moved = self.projects / "synthetic-level0" / "handoffs" / "moved"
        self.assertEqual(real_inode, moved.stat().st_ino)
        self.assertEqual(
            sorted(f"{name}.md" for name in ARTIFACTS),
            sorted(path.name for path in moved.glob("*.md")),
        )

    def test_a_namespace_swap_between_two_publications_is_refused(self):
        """Diagnostic path only.

        The swap is injected *between* two artifact publications, so the
        descriptor is already in use when the name it came from is replaced.
        Every artifact must still land in the inode the run opened. This
        establishes the diagnostic path only and is NOT evidence of detection
        against the excluded non-cooperating same-identity process.
        """
        self.dossier.mkdir(parents=True)
        decoy = self.checkout / "decoy"
        decoy.mkdir()
        real_inode = self.dossier.stat().st_ino
        handoffs = self.projects / "synthetic-level0" / "handoffs"

        real_link = os.link
        published = []

        def swap_after_first_publication(source, target, **kwargs):
            result = real_link(source, target, **kwargs)
            published.append(target)
            already_swapped = (handoffs / "SYNTH-010").is_symlink()
            if len(published) == 1 and not already_swapped:
                (handoffs / "SYNTH-010").rename(handoffs / "moved")
                (handoffs / "SYNTH-010").symlink_to(decoy)
            return result

        with mock.patch.object(
            generate_module.os, "link", swap_after_first_publication
        ):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)

        self.assertIn("namespace drift", str(caught.exception))
        self.assertEqual([], sorted(decoy.iterdir()), "no write reached the decoy")
        moved = handoffs / "moved"
        self.assertEqual(real_inode, moved.stat().st_ino)
        self.assertEqual(
            sorted(f"{name}.md" for name in ARTIFACTS),
            sorted(path.name for path in moved.glob("*.md")),
            "every artifact landed in the inode the run opened",
        )
        self.assertEqual(
            [], sorted(path.name for path in moved.glob(".tdgen.*")),
            "no private temporary survived",
        )

    RACE_PROGRAM = textwrap.dedent(
        """
        '''One invocation of a deterministic two-process first-creation race.

        Both processes start against a genuinely missing dossier and meet at a
        barrier *inside* the mkdir of the final component, so the mkdir/EEXIST
        convergence is really exercised rather than assumed. Ordering is
        enforced by blocking waits, not by timing.
        '''
        import json, os, sys, time
        from pathlib import Path

        role, source, barrier, projects_root, record_path = sys.argv[1:6]
        sys.path.insert(0, source)

        from brichan.contracts.task_dossier import generate as generator
        from brichan.contracts.task_dossier.generate import (
            GenerationError, apply_generation,
        )
        from brichan.contracts.task_dossier.record import load_record

        barrier = Path(barrier)
        projects = Path(projects_root)
        dossier = projects / "synthetic-level0" / "handoffs" / "SYNTH-010"

        def signal(name):
            (barrier / name).write_text("1", encoding="utf-8")

        def wait(name, timeout=60.0):
            deadline = time.monotonic() + timeout
            while not (barrier / name).exists():
                if time.monotonic() > deadline:
                    raise SystemExit(f"{role}: timed out waiting for {name}")
                time.sleep(0.002)

        report = {
            "role": role,
            "dossier_missing_at_start": not dossier.exists(),
            "mkdir_eexist": False,
            "mkdir_created": False,
        }

        real_mkdir = os.mkdir

        def barriered_mkdir(name, *arguments, **keywords):
            if name != "SYNTH-010":
                return real_mkdir(name, *arguments, **keywords)
            # Both processes are now inside the same mkdir call.
            signal(f"{role}_at_mkdir")
            wait("winner_at_mkdir")
            wait("loser_at_mkdir")
            if role == "loser":
                wait("winner_mkdir_done")
            try:
                real_mkdir(name, *arguments, **keywords)
            except FileExistsError:
                report["mkdir_eexist"] = True
                raise
            report["mkdir_created"] = True
            if role == "winner":
                signal("winner_mkdir_done")
            return None

        real_flock = generator.fcntl.flock

        def barriered_flock(descriptor, operation):
            if role == "winner":
                result = real_flock(descriptor, operation)
                # Held, with nothing published yet: the loser observes now.
                signal("winner_locked")
                wait("loser_done")
                return result
            wait("winner_locked")
            return real_flock(descriptor, operation)

        os.mkdir = barriered_mkdir
        generator.os.mkdir = barriered_mkdir
        generator.fcntl.flock = barriered_flock

        record = load_record(
            Path(record_path),
            task_id="SYNTH-010", level="0", project="synthetic-level0",
        )
        try:
            apply_generation(record, projects)
            report["outcome"] = "published"
        except GenerationError as error:
            report["outcome"] = str(error)
        finally:
            report["inode"] = dossier.stat().st_ino if dossier.is_dir() else None
            report["leaves"] = (
                sorted(path.name for path in dossier.iterdir())
                if dossier.is_dir() else []
            )
            if role == "loser":
                signal("loser_done")

        print(json.dumps(report))
        """
    )

    def run_first_creation_race(self):
        """Start both invocations against a genuinely missing dossier."""
        self.assertFalse(self.dossier.exists())
        barrier = self.checkout / "barrier"
        barrier.mkdir()

        processes = {
            role: subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    self.RACE_PROGRAM,
                    role,
                    str(ROOT / "src"),
                    str(barrier),
                    str(self.projects),
                    str(self.record_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            for role in ("winner", "loser")
        }
        reports = {}
        for role, process in processes.items():
            stdout, stderr = process.communicate(timeout=120)
            self.assertEqual(0, process.returncode, f"{role}: {stderr}")
            reports[role] = json.loads(stdout.strip().splitlines()[-1])
        return reports

    def test_a_genuine_two_invocation_first_creation_race(self):
        """Two processes race the first creation of a missing dossier.

        Both start with the dossier absent and meet at a barrier inside the
        mkdir of the final component, so one really does observe `EEXIST` and
        reopen the directory the other created. Exactly one publishes; the
        loser is refused by the nonblocking lock before it can create any
        artifact or temporary.

        Diagnostic and cooperating-writer behaviour only. This says nothing
        about a non-cooperating process running under the same OS identity:
        that process is outside the threat model, and nothing here is a
        compare-and-swap.
        """
        reports = self.run_first_creation_race()
        winner, loser = reports["winner"], reports["loser"]

        # Both genuinely started before the dossier existed.
        self.assertTrue(winner["dossier_missing_at_start"])
        self.assertTrue(loser["dossier_missing_at_start"])

        # The mkdir race really happened: one created, the other saw EEXIST.
        self.assertTrue(winner["mkdir_created"], "the winner created the dossier")
        self.assertFalse(winner["mkdir_eexist"])
        self.assertTrue(
            loser["mkdir_eexist"],
            "the loser must observe EEXIST and reopen the same directory",
        )
        self.assertFalse(loser["mkdir_created"])

        # Both converged on one inode.
        self.assertIsNotNone(winner["inode"])
        self.assertEqual(winner["inode"], loser["inode"])
        self.assertEqual(winner["inode"], self.dossier.stat().st_ino)

        # Exactly one published; the other was refused by the lock.
        self.assertEqual("published", winner["outcome"])
        self.assertIn("holds the dossier lock", loser["outcome"])

        # Observed while the winner held the lock and had published nothing.
        self.assertEqual(
            [],
            loser["leaves"],
            "the loser created no artifact and no temporary leaf",
        )

        # The winner's output is complete and carries no temporary.
        self.assertEqual(
            sorted(f"{name}.md" for name in ARTIFACTS), self.artifacts_present()
        )
        self.assertEqual(self.artifacts_present(), self.leaves())

    def test_the_first_creation_race_is_deterministic(self):
        """The same race, repeated, must reach the same outcome every time."""
        for attempt in range(3):
            with self.subTest(attempt=attempt):
                if attempt:
                    self.setUp()
                reports = self.run_first_creation_race()
                self.assertTrue(reports["loser"]["mkdir_eexist"])
                self.assertEqual("published", reports["winner"]["outcome"])
                self.assertIn(
                    "holds the dossier lock", reports["loser"]["outcome"]
                )
                self.assertEqual([], reports["loser"]["leaves"])
                self.assertEqual(
                    reports["winner"]["inode"], reports["loser"]["inode"]
                )

    def test_publication_never_uses_rename_or_replace(self):
        source = (
            ROOT / "src/brichan/contracts/task_dossier/generate.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("os.rename(", source)
        self.assertNotIn("os.replace(", source)


class PublicationFaultTest(GenerationBase):
    """Every specified fault leaves no partial artifact and exits nonzero."""

    def assert_no_partial(self):
        """No artifact is half-written and no private temporary survives."""
        if not self.dossier.is_dir():
            return
        for path in sorted(self.dossier.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.endswith("\n"), path.name)
            self.assertIn("## Artifact metadata", text)
            self.assertIn("## Uncertainty", text)
        leftovers = sorted(path.name for path in self.dossier.glob(".tdgen.*"))
        self.assertEqual([], leftovers, "a private temporary survived")

    def assert_fault_is_refused(self, attribute, side_effect, *, only_regular=False):
        """Inject one fault, assert a refusal, and leave nothing partial.

        ``only_regular`` narrows the patch to descriptors that name regular
        files, so patching ``close`` or ``fsync`` does not also break the
        directory descriptors the walk depends on.
        """
        real = getattr(generate_module.os, attribute)

        def faulty(descriptor, *args, **kwargs):
            if only_regular:
                try:
                    if not generate_module.stat.S_ISREG(
                        os.fstat(descriptor).st_mode
                    ):
                        return real(descriptor, *args, **kwargs)
                except OSError:
                    return real(descriptor, *args, **kwargs)
            raise side_effect

        with mock.patch.object(generate_module.os, attribute, faulty):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)
        self.assert_no_partial()
        return caught.exception

    def test_a_stalled_write_never_publishes_a_truncated_artifact(self):
        def stalled(descriptor, data):
            return 0

        with mock.patch.object(generate_module.os, "write", stalled):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)
        self.assertIn("short write", str(caught.exception))
        self.assert_no_partial()
        self.assertEqual([], self.artifacts_present())

    def test_a_write_reporting_progress_it_did_not_make_is_refused(self):
        """The size check, not the return value, decides completeness."""

        def lying(descriptor, data):
            return len(data)

        with mock.patch.object(generate_module.os, "write", lying):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)
        self.assertIn("rendered artifact is", str(caught.exception))
        self.assert_no_partial()
        self.assertEqual([], self.artifacts_present())

    def test_a_progressing_short_write_still_publishes_complete_artifacts(self):
        real_write = os.write

        def one_byte(descriptor, data):
            return real_write(descriptor, data[:1])

        with mock.patch.object(generate_module.os, "write", one_byte):
            apply_generation(self.record, self.projects)
        self.assert_no_partial()
        self.assertEqual(
            sorted(f"{name}.md" for name in ARTIFACTS), self.artifacts_present()
        )

    def test_a_write_error_is_refused(self):
        self.assert_fault_is_refused("write", OSError(errno.EIO, "boom"))
        self.assertEqual([], self.artifacts_present())

    def test_a_file_fsync_failure_is_refused(self):
        self.assert_fault_is_refused(
            "fsync", OSError(errno.EIO, "fsync failed"), only_regular=True
        )
        self.assertEqual([], self.artifacts_present())

    def test_a_directory_fsync_failure_is_refused(self):
        real_fsync = os.fsync

        def directory_only(descriptor):
            if generate_module.stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise OSError(errno.EIO, "directory fsync failed")
            return real_fsync(descriptor)

        with mock.patch.object(generate_module.os, "fsync", directory_only):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)
        self.assertIn("fsync the dossier directory", str(caught.exception))

    def test_a_close_failure_is_refused(self):
        self.assert_fault_is_refused(
            "close", OSError(errno.EIO, "close failed"), only_regular=True
        )
        self.assertEqual([], self.artifacts_present())

    def test_a_link_failure_is_refused(self):
        error = self.assert_fault_is_refused(
            "link", OSError(errno.ENOSPC, "no space")
        )
        self.assertIn("partial adoption", str(error))
        self.assertEqual([], self.artifacts_present())

    def test_a_cleanup_failure_forces_a_nonzero_outcome(self):
        real_unlink = os.unlink

        def refuse(path, *args, **kwargs):
            if str(path).startswith(".tdgen."):
                raise OSError(errno.EPERM, "cleanup refused")
            return real_unlink(path, *args, **kwargs)

        with mock.patch.object(generate_module.os, "unlink", refuse):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)
        self.assertIn("private temporary", str(caught.exception))

    def test_temporary_name_exhaustion_is_a_refusal(self):
        with mock.patch.object(generate_module, "TEMPORARY_ATTEMPTS", 0):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)
        self.assertIn("exhausted", str(caught.exception))
        self.assertEqual([], self.artifacts_present())

    def test_a_permission_denied_dossier_is_refused(self):
        self.dossier.mkdir(parents=True)
        self.dossier.chmod(0o500)
        self.addCleanup(self.dossier.chmod, 0o755)
        with self.assertRaises(generate_module.GenerationError):
            apply_generation(self.record, self.projects)

    def test_a_retry_republishes_only_the_missing_artifacts(self):
        apply_generation(self.record, self.projects)
        stamped = {
            path.name: path.read_text(encoding="utf-8")
            for path in self.dossier.glob("*.md")
        }
        (self.dossier / "brief.md").unlink()
        with self.assertRaises(generate_module.GenerationError) as caught:
            apply_generation(self.record, self.projects)
        self.assertIn("partial adoption", str(caught.exception))
        for name, text in stamped.items():
            self.assertEqual(
                text, (self.dossier / name).read_text(encoding="utf-8"), name
            )

    def test_an_injected_eexist_preserves_the_existing_file(self):
        """A collision never overwrites and always forces a nonzero outcome."""
        self.dossier.mkdir(parents=True)
        real_link = os.link
        injected = {"count": 0}

        def collide_on_the_third(source, target, **kwargs):
            injected["count"] += 1
            if injected["count"] == 3:
                raise FileExistsError(errno.EEXIST, "injected collision")
            return real_link(source, target, **kwargs)

        with mock.patch.object(generate_module.os, "link", collide_on_the_third):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)

        message = str(caught.exception)
        self.assertIn("partial adoption", message)
        self.assert_no_partial()
        # The collided artifact is absent because the injection stood in for an
        # existing file; every other artifact published completely.
        self.assertEqual(len(ARTIFACTS) - 1, len(self.artifacts_present()))

    def test_a_temporary_inode_mismatch_is_refused_before_the_link(self):
        """The staged name must still be the file this run wrote."""
        self.dossier.mkdir(parents=True)
        decoy = self.dossier / "decoy.bin"
        decoy.write_text("a different inode\n", encoding="utf-8")
        real_lstat = os.lstat
        injected = {"done": False}

        def mismatch_once(path, *args, **kwargs):
            if (
                not injected["done"]
                and isinstance(path, str)
                and path.startswith(".tdgen.")
            ):
                injected["done"] = True
                return real_lstat(decoy)
            return real_lstat(path, *args, **kwargs)

        with mock.patch.object(generate_module.os, "lstat", mismatch_once):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)

        self.assertIn("no longer names the file this run wrote", str(caught.exception))
        self.assertEqual([], self.artifacts_present(), "nothing was published")
        self.assertTrue(decoy.is_file(), "the foreign file was not unlinked")
        self.assertEqual(
            [], sorted(path.name for path in self.dossier.glob(".tdgen.*"))
        )

    def test_a_foreign_file_is_never_unlinked_during_cleanup(self):
        """Diagnostic path only; not evidence of detection."""
        self.dossier.mkdir(parents=True)
        foreign = self.dossier / "foreign.txt"
        foreign.write_text("not ours\n", encoding="utf-8")
        apply_generation(self.record, self.projects)
        self.assertTrue(foreign.is_file())
        self.assertEqual("not ours\n", foreign.read_text(encoding="utf-8"))


class PublicationSubstitutionTest(GenerationBase):
    """Stable injected substitutions around the hard link.

    Every test in this class establishes a *reachable diagnostic path* only.
    None of them is evidence of prevention or of guaranteed detection against
    the excluded non-cooperating process running under the same OS identity:
    that process is outside the threat model, and the post-publication check is
    a point-in-time observation, never a compare-and-swap. What they do
    establish is what happens when the observation *does* fire: the run never
    reports success, the final entry is never unlinked, a foreign replacement
    is never removed, and this run's own private temporary does not survive.
    """

    def setUp(self):
        super().setUp()
        self.dossier.mkdir(parents=True)
        self.decoy = self.checkout / "decoy.md"
        self.decoy.write_text("decoy content\n", encoding="utf-8")

    def temporaries(self):
        return sorted(path.name for path in self.dossier.glob(".tdgen.*"))

    def substitute_before_link(self, replace):
        """Run one generation, replacing the staged source just before link."""
        real_link = os.link
        injected = {}

        def substituting_link(source, target, **kwargs):
            if not injected:
                injected["source"] = self.dossier / source
                injected["target"] = target
                replace(self.dossier / source)
            return real_link(source, target, **kwargs)

        with mock.patch.object(generate_module.os, "link", substituting_link):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)
        return injected, caught.exception

    def test_a_regular_file_substituted_for_the_source_is_refused(self):
        def replace(path):
            # Substitute via rename rather than unlink-then-create: an
            # in-place unlink/recreate can hand the new file the same inode
            # the old one held (observed on Linux tmpfs), which would make
            # this an accidental no-op instead of an actual substitution.
            decoy = path.with_name(path.name + ".decoy")
            decoy.write_text("substituted regular file\n", encoding="utf-8")
            os.replace(decoy, path)

        injected, error = self.substitute_before_link(replace)

        self.assertIn("publication integrity", str(error))
        self.assertIn("partial adoption", str(error))
        # The foreign replacement is never unlinked: its identity is not ours.
        self.assertTrue(injected["source"].is_file())
        self.assertEqual(
            "substituted regular file\n",
            injected["source"].read_text(encoding="utf-8"),
        )
        # The final entry is left in place for inspection, never removed.
        self.assertTrue((self.dossier / injected["target"]).exists())

    def test_a_symlink_substituted_for_the_source_is_refused(self):
        def replace(path):
            # See the note in the regular-file variant above: substitute via
            # rename so the identity actually changes on every filesystem.
            decoy_link = path.with_name(path.name + ".decoy")
            decoy_link.symlink_to(self.decoy)
            os.replace(decoy_link, path)

        injected, error = self.substitute_before_link(replace)

        self.assertIn("publication integrity", str(error))
        self.assertTrue(injected["source"].is_symlink())
        final = self.dossier / injected["target"]
        self.assertTrue(
            final.is_symlink(),
            "follow_symlinks=False links the link itself, never its target",
        )
        self.assertEqual(
            "decoy content\n",
            self.decoy.read_text(encoding="utf-8"),
            "no write reached the symlink target",
        )

    def test_the_final_name_replaced_after_the_link_is_refused(self):
        """M1: the run-owned temporary must not survive this branch."""
        real_link = os.link
        injected = {}

        def replace_final_after_link(source, target, **kwargs):
            result = real_link(source, target, **kwargs)
            if not injected:
                injected["source"] = self.dossier / source
                injected["target"] = self.dossier / target
                injected["target"].unlink()
                injected["target"].write_text("foreign entry\n", encoding="utf-8")
            return result

        with mock.patch.object(
            generate_module.os, "link", replace_final_after_link
        ):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)

        self.assertIn("publication integrity", str(caught.exception))
        self.assertIn("partial adoption", str(caught.exception))
        self.assertEqual(
            "foreign entry\n",
            injected["target"].read_text(encoding="utf-8"),
            "the replacement final entry is left untouched",
        )
        self.assertFalse(
            injected["source"].exists(),
            "this run's own private temporary was cleaned up",
        )
        self.assertEqual([], self.temporaries())

    def test_an_observation_error_still_cleans_up_the_run_owned_temporary(self):
        """M1: an OSError from the post-link lstat is not a licence to litter."""
        real_lstat = os.lstat
        injected = {"done": False}

        def fail_the_observation(path, *args, **kwargs):
            if (
                not injected["done"]
                and isinstance(path, str)
                and path.endswith(".md")
            ):
                injected["done"] = True
                raise OSError(errno.EIO, "injected observation failure")
            return real_lstat(path, *args, **kwargs)

        with mock.patch.object(generate_module.os, "lstat", fail_the_observation):
            with self.assertRaises(generate_module.GenerationError) as caught:
                apply_generation(self.record, self.projects)

        message = str(caught.exception)
        self.assertIn("cannot observe published", message)
        self.assertIn("partial adoption", message)
        self.assertEqual([], self.temporaries(), "no private temporary survived")
        # The artifact it did publish stays complete and in place.
        self.assertIn("index.md", self.artifacts_present())

    def test_a_foreign_temporary_is_preserved_while_ours_is_removed(self):
        """The cleanup helper distinguishes the two by identity, not by name."""
        foreign = self.dossier / ".tdgen.SYNTH-010.foreign.0.0.tmp"
        foreign.write_text("not ours\n", encoding="utf-8")
        apply_generation(self.record, self.projects)
        self.assertTrue(foreign.is_file())
        self.assertEqual("not ours\n", foreign.read_text(encoding="utf-8"))
        self.assertEqual(
            [foreign.name],
            self.temporaries(),
            "only the foreign temporary remains; every run-owned one is gone",
        )


if __name__ == "__main__":
    unittest.main()
