import contextlib
import io
import shlex
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.contracts.receipts import validation as validate_handoff_receipts


class ReceiptFixtureMixin:
    """Receipt fixtures and validator plumbing shared by both test classes.

    Extracted so the techstack round trips can reuse the fixtures without
    inheriting — and re-running — the existing validator cases.
    """

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.projects = self.root / "projects"
        self.projects.mkdir()

    def receipt(
        self,
        *,
        task_id="TASK-001",
        project="example",
        role="standalone",
        parent="null",
        schema_version="1",
        include_v2=None,
        attempt="1",
        replaces="null",
        origin="initial",
        attempt_lifecycle="active",
        prior_state="null",
        replacement_evidence="null",
        status="accepted",
        criterion_status="pending",
        verification_result="pending",
        changed_artifacts="pending",
        diff_evidence="pending",
        test_evidence="pending",
        verdict="null",
        findings="null",
        panes_closed="no",
        memory_updated="yes",
        scope="bounded validator implementation",
        verification_command="python3 -m unittest",
    ):
        content = textwrap.dedent(
            f"""\
            # Handoff receipt

            Fixture receipt.

            ## Identity

            - Receipt schema version: `{schema_version}`
            - Receipt role: `{role}`
            - Parent receipt path: `{parent}`
            - Task ID: `{task_id}`
            - Project: `{project}`
            - Handoff timestamp (UTC): `2026-07-28T05:23:11Z`
            - Attempt: `{attempt}`
            - Replaces session: `{replaces}`

            ## Plan version

            - Artifact or plan ID: `{task_id}-P1`
            - Version: `1`
            - Status: `{status}`

            ## Sessions

            | Role | Provider | Model | Brida-owned pane | Session |
            | --- | --- | --- | --- | --- |
            | Implementer | `Codex` | `test-model` | `pane-1` | `session-1` |

            ## Scope

            - In scope: {scope}
            - Authorized paths: `scripts/example.py`
            - Exclusive write ownership: `single writer`
            - Branch: `test-branch`
            - Worktree: `test-worktree`

            ## Non-goals

            - Excluded work: deployment and remote actions

            ## Acceptance criteria

            | Criterion ID | Status | Evidence |
            | --- | --- | --- |
            | `C1` | `{criterion_status}` | `fixture criterion evidence` |

            ## Verification

            | Command | Result |
            | --- | --- |
            | `{verification_command}` | `{verification_result}` |

            ## Implementation evidence

            - Changed artifacts: `{changed_artifacts}`
            - Diff evidence: `{diff_evidence}`
            - Test evidence: `{test_evidence}`

            ## Review verdict

            - Verdict: `{verdict}`
            - Findings: `{findings}`

            ## Risks and open decisions

            - Risks: `fixture risk`
            - Open decisions: `null`

            ## Cleanup status

            - Brida-owned panes closed: `{panes_closed}`
            - Project memory updated: `{memory_updated}`
            """
        )
        if include_v2 is None:
            include_v2 = schema_version == "2"
        if include_v2:
            v2_fields = textwrap.dedent(
                f"""\
                - Attempt origin: `{origin}`
                - Attempt lifecycle state: `{attempt_lifecycle}`
                - Prior attempt state: `{prior_state}`
                - Replacement evidence path: `{replacement_evidence}`
                """
            )
            content = content.replace(
                f"- Replaces session: `{replaces}`\n",
                f"- Replaces session: `{replaces}`\n{v2_fields}",
            )
        return content

    def write_receipt(self, content, project="example", task_id="TASK-001"):
        path = self.projects / project / "handoffs" / task_id / "receipt.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_validator(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = validate_handoff_receipts.main([str(self.projects)])
        return result, stdout.getvalue(), stderr.getvalue()

    def write_evidence(self, path="evidence/replacement.md", content="evidence"):
        evidence = self.root / path
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(content, encoding="utf-8")
        return evidence

    def assert_invalid(self, diagnostic):
        result, _, stderr = self.run_validator()
        self.assertNotEqual(0, result)
        self.assertIn("receipt.md", stderr)
        self.assertIn(diagnostic, stderr)

    def implemented_receipt(self, **overrides):
        values = {
            "status": "implemented",
            "criterion_status": "pass",
            "verification_result": "pass; fixture tests",
            "changed_artifacts": "scripts/example.py",
            "diff_evidence": "commit abc123",
            "test_evidence": "fixture tests pass",
            "panes_closed": "no",
            "memory_updated": "no",
            "attempt_lifecycle": "complete",
        }
        values.update(overrides)
        return self.receipt(**values)

    def reviewed_receipt(self, **overrides):
        values = {
            "status": "reviewed",
            "criterion_status": "pass",
            "verification_result": "pass; fixture tests",
            "changed_artifacts": "scripts/example.py",
            "diff_evidence": "commit abc123",
            "test_evidence": "fixture tests pass",
            "verdict": "PASS",
            "findings": "null",
            "panes_closed": "yes",
            "memory_updated": "yes",
            "attempt_lifecycle": "complete",
        }
        values.update(overrides)
        return self.receipt(**values)


class HandoffReceiptValidatorTest(ReceiptFixtureMixin, unittest.TestCase):
    def test_valid_accepted_receipt_is_not_mutated(self):
        content = self.receipt()
        path = self.write_receipt(content)

        result, stdout, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)
        self.assertIn("Validated 1 canonical handoff receipt", stdout)
        self.assertEqual(content, path.read_text(encoding="utf-8"))

    def test_valid_implemented_receipt(self):
        self.write_receipt(self.implemented_receipt())

        result, _, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)

    def test_valid_reviewed_pass_receipt(self):
        self.write_receipt(self.reviewed_receipt())

        result, _, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)

    def test_valid_v2_initial_receipt(self):
        self.write_receipt(self.receipt(schema_version="2"))

        result, _, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)

    def test_valid_v2_replacement_complete_pass_is_not_mutated(self):
        evidence = self.write_evidence(content="original recovery observations")
        content = self.reviewed_receipt(
            schema_version="2",
            attempt="2",
            replaces="opaque:prior/session@provider",
            origin="replacement",
            prior_state="abandoned",
            replacement_evidence="evidence/replacement.md",
        )
        path = self.write_receipt(content)

        result, _, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)
        self.assertEqual(content, path.read_text(encoding="utf-8"))
        self.assertEqual(
            "original recovery observations",
            evidence.read_text(encoding="utf-8"),
        )

    def test_valid_v2_stale_accepted_receipt_has_concrete_evidence(self):
        content = self.receipt(
            schema_version="2",
            attempt_lifecycle="stale",
            changed_artifacts="none; read-only attempt",
            diff_evidence="three no-progress observations",
            test_evidence="no task output after three observations",
        )
        self.write_receipt(content)

        result, _, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)

    def test_valid_changes_required_receipt_during_remediation(self):
        content = self.reviewed_receipt(
            criterion_status="fail",
            verification_result="fail; reviewer mutation",
            verdict="CHANGES REQUIRED",
            findings="C1 must reject the reviewer mutation",
            panes_closed="no",
            memory_updated="no",
        )
        self.write_receipt(content)

        result, _, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)

    def test_valid_parent_and_child_topology(self):
        parent = self.receipt(task_id="PARENT", role="parent")
        child = self.receipt(
            task_id="CHILD",
            role="child",
            parent="projects/example/handoffs/PARENT/receipt.md",
        )
        self.write_receipt(parent, task_id="PARENT")
        self.write_receipt(child, task_id="CHILD")

        result, stdout, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)
        self.assertIn("Validated 2 canonical handoff receipt", stdout)

    def test_valid_v2_parent_and_child_topology(self):
        parent = self.receipt(
            task_id="PARENT",
            role="parent",
            schema_version="2",
        )
        child = self.receipt(
            task_id="CHILD",
            role="child",
            parent="projects/example/handoffs/PARENT/receipt.md",
            schema_version="2",
        )
        self.write_receipt(parent, task_id="PARENT")
        self.write_receipt(child, task_id="CHILD")

        result, stdout, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)
        self.assertIn("Validated 2 canonical handoff receipt", stdout)

    def test_missing_required_field_reports_file_and_field(self):
        content = self.receipt().replace("- Project: `example`\n", "")
        self.write_receipt(content)

        self.assert_invalid("Identity.Project")

    def test_bad_path_identity_reports_expected_task(self):
        self.write_receipt(self.receipt(task_id="OTHER"))

        self.assert_invalid("expected 'TASK-001' from canonical path")

    def test_bad_role_parent_topology_is_rejected(self):
        content = self.receipt(role="child", parent="null")
        self.write_receipt(content)

        self.assert_invalid("child receipts require a repo-relative canonical")

    def test_incomplete_reviewed_pass_is_rejected(self):
        content = self.reviewed_receipt(criterion_status="pending")
        self.write_receipt(content)

        self.assert_invalid("reviewed PASS requires every criterion to pass")

    def test_reviewed_pass_requires_implementation_evidence(self):
        content = self.reviewed_receipt(changed_artifacts="TBD")
        self.write_receipt(content)

        self.assert_invalid("Implementation evidence.Changed artifacts")

    def test_reviewed_pass_cleanup_failure_is_rejected(self):
        content = self.reviewed_receipt(panes_closed="no")
        self.write_receipt(content)

        self.assert_invalid("Cleanup status.Brida-owned panes closed")

    def test_replacement_attempt_requires_provenance(self):
        content = self.receipt(attempt="2", replaces="null")
        self.write_receipt(content)

        self.assert_invalid("later attempts require concrete replacement")

    def test_attempt_one_cannot_claim_replacement(self):
        content = self.receipt(attempt="1", replaces="prior-session")
        self.write_receipt(content)

        self.assert_invalid("attempt 1 must not replace a prior session")

    def test_v2_requires_all_four_fields(self):
        for field in (
            "Attempt origin",
            "Attempt lifecycle state",
            "Prior attempt state",
            "Replacement evidence path",
        ):
            with self.subTest(field=field):
                content = self.receipt(schema_version="2")
                content = content.replace(
                    next(
                        line
                        for line in content.splitlines(keepends=True)
                        if line.startswith(f"- {field}:")
                    ),
                    "",
                )
                self.write_receipt(content)
                self.assert_invalid(f"Identity.{field}")

    def test_v2_enum_fields_reject_invalid_values(self):
        mutations = (
            ("Attempt origin", "`initial`", "`complete`"),
            ("Attempt lifecycle state", "`active`", "`replacement`"),
            ("Prior attempt state", "`null`", "`active`"),
        )
        for field, old, new in mutations:
            with self.subTest(field=field):
                content = self.receipt(schema_version="2").replace(
                    f"- {field}: {old}",
                    f"- {field}: {new}",
                )
                self.write_receipt(content)
                self.assert_invalid(f"Identity.{field}")

    def test_v2_origin_inversion_is_rejected(self):
        self.write_evidence()
        cases = (
            self.receipt(schema_version="2", origin="replacement"),
            self.receipt(
                schema_version="2",
                attempt="2",
                replaces="prior-session",
                origin="initial",
                prior_state="stale",
                replacement_evidence="evidence/replacement.md",
            ),
        )
        for content in cases:
            with self.subTest(origin=content.split("Attempt origin:")[1].splitlines()[0]):
                self.write_receipt(content)
                self.assert_invalid("Identity.Attempt origin")

    def test_v2_self_replacement_is_rejected(self):
        self.write_evidence()
        content = self.receipt(
            schema_version="2",
            attempt="2",
            replaces="session-1",
            origin="replacement",
            prior_state="stale",
            replacement_evidence="evidence/replacement.md",
        )
        self.write_receipt(content)

        self.assert_invalid("cannot equal a session listed in the current receipt")

    def test_v2_unsafe_and_missing_evidence_paths_are_rejected(self):
        cases = (
            ("/tmp/evidence.md", "safe repo-relative path"),
            ("../evidence.md", "safe repo-relative path"),
            ("~/evidence.md", "safe repo-relative path"),
            ("evidence/missing.md", "evidence file does not exist"),
        )
        for evidence_path, diagnostic in cases:
            with self.subTest(evidence_path=evidence_path):
                content = self.receipt(
                    schema_version="2",
                    attempt="2",
                    replaces="prior-session",
                    origin="replacement",
                    prior_state="stale",
                    replacement_evidence=evidence_path,
                )
                self.write_receipt(content)
                self.assert_invalid(diagnostic)

    def test_v2_lifecycle_and_plan_status_must_be_compatible(self):
        cases = (
            (
                self.implemented_receipt(
                    schema_version="2",
                    attempt_lifecycle="active",
                ),
                "implemented receipts require 'complete'",
            ),
            (
                self.receipt(
                    schema_version="2",
                    attempt_lifecycle="abandoned",
                ),
                "'abandoned' lifecycle requires concrete evidence",
            ),
            (
                self.reviewed_receipt(
                    schema_version="2",
                    attempt_lifecycle="stale",
                ),
                "reviewed PASS requires 'complete'",
            ),
        )
        for content, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                self.write_receipt(content)
                self.assert_invalid(diagnostic)

    def test_v2_complete_replacement_requires_abandoned_prior_at_review(self):
        self.write_evidence()
        content = self.reviewed_receipt(
            schema_version="2",
            attempt="2",
            replaces="prior-session",
            origin="replacement",
            prior_state="stale",
            replacement_evidence="evidence/replacement.md",
        )
        self.write_receipt(content)

        self.assert_invalid("reviewed replacement receipts require 'abandoned'")

    def test_schema_v1_rejects_v2_only_fields(self):
        content = self.receipt(schema_version="1", include_v2=True)
        self.write_receipt(content)

        self.assert_invalid("schema version 1 forbids schema-v2 identity fields")

    def test_unsupported_or_blank_schema_version_is_rejected(self):
        for schema_version in ("3", "", "   "):
            with self.subTest(schema_version=repr(schema_version)):
                content = self.receipt(
                    schema_version=schema_version,
                    include_v2=False,
                )
                self.write_receipt(content)
                self.assert_invalid("supported schema versions are 1 and 2")

    def test_v2_has_no_attempt_cap_or_provider_session_format_guessing(self):
        self.write_evidence()
        content = self.receipt(
            schema_version="2",
            attempt="1000000",
            replaces="opaque:provider/session@identifier",
            origin="replacement",
            prior_state="stale",
            replacement_evidence="evidence/replacement.md",
        )
        self.write_receipt(content)

        result, _, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)

    def test_personal_and_home_paths_are_rejected(self):
        for index, unsafe_path in enumerate(
            ("/Users/alice/repo", "/home/alice/repo", "~/repo"),
            start=1,
        ):
            with self.subTest(unsafe_path=unsafe_path):
                task_id = f"TASK-{index:03d}"
                content = self.receipt(task_id=task_id, scope=unsafe_path)
                self.write_receipt(content, task_id=task_id)

        result, _, stderr = self.run_validator()

        self.assertNotEqual(0, result)
        self.assertEqual(3, stderr.count("path hygiene"))

    def test_historical_evaluation_receipts_are_not_discovered(self):
        historical = (
            self.root / "evals" / "mixed-provider-coding" / "receipt.md"
        )
        historical.parent.mkdir(parents=True)
        historical.write_text("not a canonical receipt", encoding="utf-8")

        result, stdout, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)
        self.assertIn("Validated 0 canonical handoff receipt", stdout)


class TechstackReceiptRoundTripTest(ReceiptFixtureMixin, unittest.TestCase):
    """Techstack pointers must fit the receipt that already exists.

    Design section 16 places the Snapshot pointer inside the existing `Scope`
    value and the verify result inside the existing `Verification` table. That
    claim is only credible if a complete receipt carrying those exact bytes
    parses with the production parser and validates with zero diagnostics, so
    these fixtures freeze the fully substituted commands rather than
    placeholders. No parser, validator, schema, section, field, generator, or
    template is touched by this module.
    """

    #: Three roots that exercise quoting without breaking the two-column
    #: table: a space, a single quote, and a leading-dash final component. No
    #: `/Users/`, `/home/`, or `~` appears, so receipt path hygiene stays
    #: satisfied. The fixtures below are the real `shlex.quote` output for
    #: each, which `test_the_frozen_roots_are_the_real_shlex_quote_output`
    #: pins — a hand-written approximation would prove nothing.
    ROOTS = (
        "/srv/work space/repo",
        "/srv/it's/repo",
        "/srv/-dashed",
    )
    QUOTED_ROOTS = tuple(shlex.quote(root) for root in ROOTS)
    DIGEST = "a" * 64
    ARTIFACT = (
        "projects/example/handoffs/TASK-001/snapshots/"
        "attempt-1-" + "a" * 64 + ".snapshot.json"
    )

    def applicable_scope(self):
        return (
            "bounded validator implementation; "
            f"Techstack snapshot pointer: {self.ARTIFACT}; "
            f"Techstack snapshot SHA-256: {self.DIGEST}"
        )

    def verify_command(self, quoted_root):
        return (
            "brichan techstacks verify "
            f"--project-root {quoted_root} "
            f"--snapshot-json '{self.ARTIFACT}' "
            "--as-of 2026-08-24"
        )

    def publication_command(self, quoted_root):
        return (
            "brichan techstacks resolve "
            f"--project-root {quoted_root} "
            "--input-json 'techstack-input.json' "
            "--snapshot-directory "
            "'projects/example/handoffs/TASK-001/snapshots'"
        )

    def test_the_frozen_roots_are_the_real_shlex_quote_output(self):
        self.assertEqual(
            ("'/srv/work space/repo'", "'/srv/it'\"'\"'s/repo'", "/srv/-dashed"),
            self.QUOTED_ROOTS,
        )
        # A leading-dash component needs no quoting, so the command carries it
        # bare; that is the case the receipt row must still survive.
        self.assertEqual("/srv/-dashed", shlex.quote("/srv/-dashed"))

    def test_an_applicable_techstack_receipt_validates_with_zero_diagnostics(self):
        for index, quoted_root in enumerate(self.QUOTED_ROOTS, start=1):
            with self.subTest(quoted_root=quoted_root):
                task_id = f"TASK-{index:03d}"
                content = self.implemented_receipt(
                    task_id=task_id,
                    scope=self.applicable_scope(),
                    verification_command=self.verify_command(quoted_root),
                    verification_result=f"pass; snapshot_sha256={self.DIGEST}",
                )
                path = self.write_receipt(content, task_id=task_id)

                # The frozen bytes really are in the file the parser reads.
                self.assertIn(self.verify_command(quoted_root), content)
                self.assertIn(
                    f"Techstack snapshot SHA-256: {self.DIGEST}", content
                )

                parse_diagnostics = []
                validate_handoff_receipts.parse_receipt(path, parse_diagnostics)
                self.assertEqual([], parse_diagnostics, parse_diagnostics)
                diagnostics = validate_handoff_receipts.validate_receipt(
                    path, self.projects
                )
                self.assertEqual(
                    [],
                    [diagnostic.format() for diagnostic in diagnostics],
                )
                # Parsing and validating leave the receipt byte-identical.
                self.assertEqual(content, path.read_text(encoding="utf-8"))

    def test_a_not_applicable_techstack_receipt_validates_with_zero_diagnostics(self):
        for index, quoted_root in enumerate(self.QUOTED_ROOTS, start=1):
            with self.subTest(quoted_root=quoted_root):
                task_id = f"TASK-1{index:02d}"
                scope = (
                    "bounded validator implementation; "
                    "Techstack snapshot pointer: none; "
                    "Techstack snapshot SHA-256: null"
                )
                content = self.implemented_receipt(
                    task_id=task_id,
                    scope=scope,
                    verification_command=self.publication_command(quoted_root),
                    verification_result=(
                        "pass; snapshot_sha256=null; status=not_applicable"
                    ),
                )
                path = self.write_receipt(content, task_id=task_id)
                self.assertIn(
                    "Techstack snapshot pointer: none; "
                    "Techstack snapshot SHA-256: null",
                    content,
                )

                parse_diagnostics = []
                validate_handoff_receipts.parse_receipt(path, parse_diagnostics)
                self.assertEqual([], parse_diagnostics, parse_diagnostics)
                diagnostics = validate_handoff_receipts.validate_receipt(
                    path, self.projects
                )
                self.assertEqual(
                    [],
                    [diagnostic.format() for diagnostic in diagnostics],
                )
                self.assertEqual(content, path.read_text(encoding="utf-8"))

    def test_both_techstack_forms_pass_the_whole_validator_run(self):
        """End to end through `main`, not only the two callables."""

        self.write_receipt(
            self.implemented_receipt(
                task_id="TASK-201",
                scope=self.applicable_scope(),
                verification_command=self.verify_command(self.QUOTED_ROOTS[0]),
                verification_result=f"pass; snapshot_sha256={self.DIGEST}",
            ),
            task_id="TASK-201",
        )
        self.write_receipt(
            self.implemented_receipt(
                task_id="TASK-202",
                scope=(
                    "bounded validator implementation; "
                    "Techstack snapshot pointer: none; "
                    "Techstack snapshot SHA-256: null"
                ),
                verification_command=self.publication_command(
                    self.QUOTED_ROOTS[2]
                ),
                verification_result=(
                    "pass; snapshot_sha256=null; status=not_applicable"
                ),
            ),
            task_id="TASK-202",
        )

        result, stdout, stderr = self.run_validator()

        self.assertEqual(0, result, stderr)
        self.assertIn("Validated 2 canonical handoff receipt", stdout)

    def test_a_root_containing_a_pipe_is_out_of_contract(self):
        """The stated boundary, frozen as observed behavior.

        `src/brichan/contracts/receipts/validation.py:223` splits every table
        line on `|` with no unescape step, so a root carrying one produces a
        three-column row. `shlex.quote` only wraps the value in single quotes
        and a `\|` escape is never unescaped, so neither rescues the row. This
        is why coordinator policy forbids a techstacks receipt for such a root.
        """

        expected = "Verification.row[1]: expected 2 columns, found 3"
        for index, quoted_root in enumerate(
            ("'/srv/a|b'", "'/srv/a\\|b'"), start=1
        ):
            with self.subTest(quoted_root=quoted_root):
                task_id = f"TASK-3{index:02d}"
                content = self.implemented_receipt(
                    task_id=task_id,
                    scope=self.applicable_scope(),
                    verification_command=self.verify_command(quoted_root),
                    verification_result=f"pass; snapshot_sha256={self.DIGEST}",
                )
                path = self.write_receipt(content, task_id=task_id)

                diagnostics = validate_handoff_receipts.validate_receipt(
                    path, self.projects
                )
                messages = [
                    f"{diagnostic.field}: {diagnostic.message}"
                    for diagnostic in diagnostics
                ]
                self.assertIn(expected, messages, messages)

    def test_the_pipe_boundary_is_the_parser_and_not_the_quoting(self):
        """Both escape attempts fail for the same reason: no unescape step."""

        rows = validate_handoff_receipts._parse_table(
            "| Command | Result |\n"
            "| --- | --- |\n"
            "| `brichan techstacks verify --project-root '/srv/a|b'` | `pass` |\n"
        )
        self.assertEqual(3, len(rows[1]))
        escaped = validate_handoff_receipts._parse_table(
            "| Command | Result |\n"
            "| --- | --- |\n"
            "| `brichan techstacks verify --project-root '/srv/a\\|b'` | `pass` |\n"
        )
        self.assertEqual(3, len(escaped[1]))


if __name__ == "__main__":
    unittest.main()
