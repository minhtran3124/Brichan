"""Production resolver selection, authority, evidence, exception, and Snapshot vectors.

Every observation here runs through the packet-1 production reader against real
disposable files under a real no-symlink Git root; nothing stubs the filesystem
except the named fault-injection tests, which say so. Approval provenance stays
opaque: one test proves the resolver never opens ``authorization_reference`` and
never recomputes ``authorization_digest``.
"""

import collections
import dataclasses
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.techstacks import filesystem as fs
from brichan.techstacks import markdown, model, resolver


TASK_ID = "TECHSTACK-001"
PLAN_ID = "TECHSTACK-PLAN-001"
PLAN_VERSION = 8
ATTEMPT_ID = "attempt-1"
AS_OF = "2026-08-24"


def canonical_temporary_directory():
    """Return a temporary directory whose path contains no symlink."""

    directory = tempfile.mkdtemp()
    return Path(os.path.realpath(directory))


def map_source(rows, *, context_id="root", title="Techstack map"):
    """Render one exact map-only README."""

    lines = [
        f"# {title}",
        "",
        markdown.MAP_ONLY_SENTENCE,
        "",
        markdown.MAP_METADATA_HEADING,
        "",
        f"- Context ID: `{context_id}`",
        "",
        markdown.CONTEXTS_HEADING,
        "",
    ]
    if rows:
        lines += [markdown.CONTEXTS_TABLE_HEADER, markdown.CONTEXTS_TABLE_SEPARATOR]
        for identifier, path, selectors in rows:
            rendered = "; ".join(f"`{selector}`" for selector in selectors)
            lines.append(f"| {identifier} | `{path}` | {rendered} |")
    else:
        lines.append(markdown.NONE_LINE)
    return ("\n".join(lines) + "\n").encode("utf-8")


def leaf_source(
    context_id,
    rules,
    *,
    title="Rules",
    reviewed_on="2026-08-01",
    within=365,
    deprecated="no",
    evidence=(),
    overrides=(),
    scope=("Applies to the selected task.",),
    verification=("Verify the selected Snapshot before work.",),
):
    """Render one exact leaf rule file."""

    if evidence:
        evidence_line = "- Evidence: " + "; ".join(f"`{path}`" for path in evidence)
    else:
        evidence_line = markdown.EVIDENCE_NONE_LINE
    lines = [
        f"# {title}",
        "",
        markdown.RULE_METADATA_HEADING,
        "",
        f"- Context ID: `{context_id}`",
        f"- Reviewed on: `{reviewed_on}`",
        f"- Review within days: `{within}`",
        f"- Deprecated: `{deprecated}`",
        evidence_line,
        "",
        markdown.SCOPE_HEADING,
        "",
        *[f"- {item}" for item in scope],
        "",
        markdown.RULES_HEADING,
        "",
        *[f"- `{rule_id}`: {statement}" for rule_id, statement in rules],
        "",
        markdown.OVERRIDES_HEADING,
        "",
    ]
    if overrides:
        lines += [
            f"- `{rule_id}` -> `{target}`: {reason}"
            for rule_id, target, reason in overrides
        ]
    else:
        lines.append(markdown.NONE_BULLET)
    lines += [
        "",
        markdown.VERIFICATION_HEADING,
        "",
        *[f"- {item}" for item in verification],
        "",
        markdown.EXCEPTIONS_HEADING,
        "",
        markdown.NONE_BULLET,
        "",
        markdown.EXAMPLES_HEADING,
        "",
        markdown.NONE_LINE,
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def make_input(**overrides):
    """Build one valid ResolutionInput."""

    base = {
        "task_id": TASK_ID,
        "plan_id": PLAN_ID,
        "plan_version": PLAN_VERSION,
        "attempt_id": ATTEMPT_ID,
        "as_of": AS_OF,
        "scope_paths": (),
        "context_chains": (),
        "exception_approvals": (),
        "declared_conflicts": (),
    }
    base.update(overrides)
    return model.ResolutionInput(**base)


def make_approval(reference_input, **overrides):
    """Build one coordinator-attested approval bound to ``reference_input``."""

    target = overrides.pop(
        "target",
        model.FailureTarget(
            code=overrides.pop("code", "STALE_RULE"),
            context_id=overrides.pop("context_id", "general"),
            evidence_path=overrides.pop("evidence_path", None),
        ),
    )
    fields = {
        "approval_id": "approval-1",
        "coordinator_attested": True,
        "authorized_by": "user",
        "authorization_reference": "decision recorded in the task dossier",
        "authorization_digest": "a" * 64,
        "task_id": reference_input.task_id,
        "plan_id": reference_input.plan_id,
        "plan_version": reference_input.plan_version,
        "attempt_id": reference_input.attempt_id,
        "issued_on": "2026-08-20",
        "expires_on": "2026-09-01",
        "target": target,
        "scope_sha256": resolver.scope_digest(reference_input),
        "reason": "the user approved this exception for this attempt",
        "binding_sha256": "0" * 64,
    }
    recompute = overrides.pop("recompute_binding", True)
    fields.update(overrides)
    approval = model.ExceptionApproval(**fields)
    if recompute:
        approval = dataclasses.replace(
            approval, binding_sha256=resolver.binding_digest(approval)
        )
    return approval


class ProjectMixin:
    """One real disposable Git root observed through the production reader."""

    def setUp(self):
        super().setUp()
        fs.HELPER_CONTROLLER.reset_for_test()
        self.base = canonical_temporary_directory()
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.root = self.base / "project"
        self.root.mkdir()
        (self.root / ".git").mkdir()

    def write(self, relative, data):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            data = data.encode("utf-8")
        target.write_bytes(data)
        return target

    def resolve(self, resolution_input=None, **overrides):
        if resolution_input is None:
            resolution_input = make_input(**overrides)
        return resolver.resolve_context(resolution_input, self.root)

    def codes(self, resolution):
        return tuple(item.code for item in resolution.diagnostics)

    def write_base_fixture(self):
        """Write the Design section 15 base fixture into the disposable root."""

        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("frontend", "techstacks/frontend/README.md", ("src/frontend/",)),
                    ("general", "techstacks/general.md", (".",)),
                ],
                title="Base techstack map",
            ),
        )
        self.write(
            "techstacks/general.md",
            leaf_source(
                "general",
                [("GENERAL-001", "Keep project context bounded.")],
                title="General rules",
            ),
        )
        self.write(
            "techstacks/frontend/README.md",
            map_source(
                [
                    (
                        "button",
                        "techstacks/frontend/components/Button.md",
                        ("src/frontend/components/Button.tsx",),
                    )
                ],
                context_id="frontend",
                title="Frontend techstack map",
            ),
        )
        self.write(
            "techstacks/frontend/components/Button.md",
            leaf_source(
                "button",
                [("BUTTON-001", "Preserve the public Button contract.")],
                title="Button rules",
                evidence=("evidence/button.txt",),
            ),
        )
        self.write("evidence/button.txt", "button-evidence-v1\n")


class RootPrecedenceTest(ProjectMixin, unittest.TestCase):
    def test_absent_root_map_with_empty_input_is_exact_not_applicable(self):
        resolution = self.resolve()
        self.assertEqual("not_applicable", resolution.status)
        self.assertIsNone(resolution.snapshot)
        self.assertEqual((), resolution.diagnostics)
        self.assertEqual(1, resolution.schema_version)

    def test_a_bare_directory_and_a_package_local_map_do_not_opt_in(self):
        (self.root / "techstacks").mkdir()
        self.assertEqual("not_applicable", self.resolve().status)
        self.write("src/techstacks/README.md", map_source(None))
        self.assertEqual("not_applicable", self.resolve().status)

    def test_absent_root_map_with_nonempty_input_is_unused_input_without_root(self):
        conflict = model.DeclaredConflict(
            source="techstacks/a.md", target="techstacks/b.md", detail="both claim src"
        )
        resolution = self.resolve(declared_conflicts=(conflict,))
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("UNUSED_INPUT_WITHOUT_ROOT",), self.codes(resolution))
        self.assertIsNone(resolution.diagnostics[0].path)
        self.assertIsNone(resolution.diagnostics[0].context_id)
        self.assertEqual(
            "conflict or exception input exists without root map",
            resolution.diagnostics[0].detail,
        )
        provisional = make_input()
        approval = make_approval(provisional)
        resolution = self.resolve(exception_approvals=(approval,))
        self.assertEqual(("UNUSED_INPUT_WITHOUT_ROOT",), self.codes(resolution))

    def test_a_non_enoent_root_map_observation_blocks_rather_than_opting_out(self):
        (self.root / "techstacks").mkdir()
        (self.root / "techstacks" / "README.md").mkdir()
        resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("DIRECTORY_REJECTED",), self.codes(resolution))

    def test_input_type_precedes_every_root_check(self):
        with self.assertRaises(model.TechstackInputError) as error:
            resolver.resolve_context({"task_id": TASK_ID}, Path("/nonexistent/root"))
        self.assertEqual("INPUT_TYPE", error.exception.code)
        self.assertEqual("", error.exception.field)
        self.assertEqual("input must be a ResolutionInput", error.exception.detail)

    def test_root_caller_errors_still_come_from_the_anchor(self):
        with self.assertRaises(model.TechstackInputError) as error:
            resolver.resolve_context(make_input(), self.base / "missing")
        self.assertEqual("PROJECT_NOT_GIT_ROOT", error.exception.code)

    def test_an_unsupported_platform_blocks_before_any_root_access(self):
        self.write_base_fixture()
        with mock.patch.object(fs, "is_supported_platform", return_value=False):
            with mock.patch.object(resolver, "read_project_file") as reader:
                resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("UNSUPPORTED_PLATFORM",), self.codes(resolution))
        reader.assert_not_called()


class SelectionTest(ProjectMixin, unittest.TestCase):
    def test_the_base_fixture_selects_the_dot_row_only_without_scope(self):
        self.write_base_fixture()
        resolution = self.resolve()
        self.assertEqual("applicable", resolution.status)
        snapshot = resolution.snapshot
        self.assertEqual(
            ("techstacks/README.md", "techstacks/general.md"),
            tuple(item.path for item in snapshot.selected_files),
        )
        root, general = snapshot.selected_files
        self.assertEqual("root", root.context_id)
        self.assertEqual("map", root.kind)
        self.assertIsNone(root.referrer_map)
        self.assertEqual((), root.map_chain)
        self.assertEqual((".",), root.applies_to)
        self.assertEqual(("root",), root.selection_basis)
        self.assertIsNone(root.reviewed_on)
        self.assertIsNone(root.review_within_days)
        self.assertIsNone(root.deprecated)
        self.assertEqual((), root.evidence)
        self.assertEqual("techstacks/README.md", snapshot.root_map)
        self.assertEqual(("dot",), general.selection_basis)
        self.assertEqual(("general",), general.map_chain)
        self.assertEqual("techstacks/README.md", general.referrer_map)
        self.assertEqual((".",), general.applies_to)
        self.assertEqual(365, general.review_within_days)
        self.assertFalse(general.deprecated)

    def test_a_scope_path_selects_the_prefix_row_and_its_descendants(self):
        self.write_base_fixture()
        resolution = self.resolve(scope_paths=("src/frontend/components/Button.tsx",))
        self.assertEqual("applicable", resolution.status)
        snapshot = resolution.snapshot
        self.assertEqual(
            (
                "techstacks/README.md",
                "techstacks/frontend/README.md",
                "techstacks/frontend/components/Button.md",
                "techstacks/general.md",
            ),
            tuple(item.path for item in snapshot.selected_files),
        )
        frontend = snapshot.selected_files[1]
        self.assertEqual(("src/frontend/",), frontend.applies_to)
        self.assertEqual(("scope",), frontend.selection_basis)
        self.assertEqual(("frontend",), frontend.map_chain)
        button = snapshot.selected_files[2]
        self.assertEqual(("frontend", "button"), button.map_chain)
        self.assertEqual("techstacks/frontend/README.md", button.referrer_map)
        self.assertEqual(("scope",), button.selection_basis)

    def test_selection_basis_lists_every_cause_in_registry_order(self):
        self.write(
            "techstacks/README.md",
            map_source([("general", "techstacks/general.md", (".",))]),
        )
        self.write(
            "techstacks/general.md",
            leaf_source("general", [("GENERAL-001", "Keep context bounded.")]),
        )
        resolution = self.resolve(
            scope_paths=("src/app.ts",), context_chains=(("general",),)
        )
        basis = resolution.snapshot.selected_files[1].selection_basis
        self.assertEqual(("dot", "scope", "context_chain"), basis)
        self.assertEqual(
            list(basis),
            [item for item in model.SELECTION_BASIS_ORDER if item in set(basis)],
        )

    def test_input_order_never_changes_the_canonical_snapshot_digest(self):
        self.write_base_fixture()
        forward = self.resolve(
            scope_paths=("src/app.ts", "src/frontend/components/Button.tsx"),
            context_chains=(("general",), ("frontend", "button")),
        )
        backward = self.resolve(
            scope_paths=("src/frontend/components/Button.tsx", "src/app.ts", "src/app.ts"),
            context_chains=(("frontend", "button"), ("general",)),
        )
        self.assertEqual("applicable", forward.status)
        self.assertEqual(
            forward.snapshot.snapshot_sha256, backward.snapshot.snapshot_sha256
        )
        self.assertEqual(
            (("frontend", "button"), ("general",)), forward.snapshot.context_chains
        )

    def test_a_dot_row_with_empty_scope_has_basis_dot_only(self):
        self.write_base_fixture()
        resolution = self.resolve()
        self.assertEqual(("dot",), resolution.snapshot.selected_files[1].selection_basis)

    def test_no_unselected_branch_is_read(self):
        self.write_base_fixture()
        self.write("techstacks/unselected.md", b"not even valid leaf bytes\n")
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("general", "techstacks/general.md", (".",)),
                    ("unselected", "techstacks/unselected.md", ("src/other",)),
                ]
            ),
        )
        original = resolver.read_project_file
        observed = []

        def spy(root_fd, relative_path, limit):
            observed.append(relative_path)
            return original(root_fd, relative_path, limit)

        with mock.patch.object(resolver, "read_project_file", spy):
            resolution = self.resolve()
        self.assertEqual("applicable", resolution.status)
        self.assertNotIn("techstacks/unselected.md", observed)
        self.assertEqual(
            ["techstacks/README.md", "techstacks/general.md"], observed
        )


class ReachabilityTest(ProjectMixin, unittest.TestCase):
    def write_chain(self, depth):
        """Write ``depth`` nested maps below root plus one terminal leaf."""

        rows = [(f"c{1:02d}", "techstacks/m01/README.md", (".",))]
        self.write("techstacks/README.md", map_source(rows))
        for index in range(1, depth + 1):
            identifier = f"c{index:02d}"
            if index == depth:
                child = (f"c{index + 1:02d}", f"techstacks/m{index:02d}/leaf.md", (".",))
            else:
                child = (
                    f"c{index + 1:02d}",
                    f"techstacks/m{index + 1:02d}/README.md",
                    (".",),
                )
            self.write(
                f"techstacks/m{index:02d}/README.md",
                map_source([child], context_id=identifier),
            )
        self.write(
            f"techstacks/m{depth:02d}/leaf.md",
            leaf_source(f"c{depth + 1:02d}", [("DEEP-001", "Keep the deep rule.")]),
        )

    def test_one_id_chain_selects_exactly_that_row(self):
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("general", "techstacks/general.md", ("src/general",)),
                    ("other", "techstacks/other.md", ("src/other",)),
                ]
            ),
        )
        self.write(
            "techstacks/general.md",
            leaf_source("general", [("GENERAL-001", "Keep context bounded.")]),
        )
        self.write(
            "techstacks/other.md",
            leaf_source("other", [("OTHER-001", "Keep the other rule.")]),
        )
        resolution = self.resolve(context_chains=(("general",),))
        self.assertEqual("applicable", resolution.status)
        self.assertEqual(
            ("techstacks/README.md", "techstacks/general.md"),
            tuple(item.path for item in resolution.snapshot.selected_files),
        )
        self.assertEqual(
            ("context_chain",), resolution.snapshot.selected_files[1].selection_basis
        )

    def test_a_six_id_chain_is_reachable_and_a_seventh_is_a_caller_error(self):
        self.write_chain(5)
        chain = tuple(f"c{index:02d}" for index in range(1, 7))
        resolution = self.resolve(context_chains=(chain,))
        self.assertEqual("applicable", resolution.status)
        self.assertEqual(7, len(resolution.snapshot.selected_files))
        self.assertEqual(
            chain, resolution.snapshot.selected_files[-1].map_chain
        )
        with self.assertRaises(model.TechstackInputError) as error:
            make_input(context_chains=(chain + ("c07",),))
        self.assertEqual("INPUT_COUNT_LIMIT", error.exception.code)

    def test_a_seventh_map_level_exceeds_the_depth_limit(self):
        self.write_chain(6)
        chain = tuple(f"c{index:02d}" for index in range(1, 8))
        with self.assertRaises(model.TechstackInputError):
            make_input(context_chains=(chain,))
        resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("MAP_DEPTH_LIMIT",), self.codes(resolution))

    def assert_unreachable(self, chain):
        resolution = self.resolve(context_chains=(chain,))
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("UNREACHABLE_CONTEXT",), self.codes(resolution))
        return resolution

    def test_skipped_shortened_extra_and_reordered_chains_are_unreachable(self):
        self.write_chain(2)
        self.assertEqual(
            "applicable", self.resolve(context_chains=(("c01", "c02", "c03"),)).status
        )
        self.assert_unreachable(("c01", "c03"))
        self.assert_unreachable(("c02",))
        self.assert_unreachable(("c01", "c02", "c03", "c04"))
        self.assert_unreachable(("c02", "c01", "c03"))
        self.assert_unreachable(("root", "c01"))

    def test_reachability_reads_rows_but_a_broken_intermediate_map_has_none(self):
        # A one-ID chain whose target leaf failed the grammar reports only the
        # load failure, because the row that names it is still there to walk.
        # An intermediate map that failed the grammar has no rows at all, so
        # the same walk cannot confirm the chain and both codes are reported.
        self.write(
            "techstacks/README.md",
            map_source([("general", "techstacks/general.md", (".",))]),
        )
        self.write("techstacks/general.md", b"# Not a leaf\n")
        resolution = self.resolve(context_chains=(("general",),))
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("INVALID_LEAF",), self.codes(resolution))
        # The resolver carries the parser's line and violated rule into the
        # diagnostic detail: this one-line leaf runs out of lines where the
        # first section boundary was required.
        self.assertEqual(
            "leaf bytes do not match the leaf grammar at line 2: SECTION_BOUNDARY",
            resolution.diagnostics[0].detail,
        )
        self.write_chain(2)
        self.write("techstacks/m01/README.md", b"# Not a map\n")
        resolution = self.resolve(context_chains=(("c01", "c02", "c03"),))
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(
            ("INVALID_MAP", "UNREACHABLE_CONTEXT"), self.codes(resolution)
        )

    def test_a_duplicate_row_id_across_selected_maps_blocks(self):
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("shared", "techstacks/one/README.md", (".",)),
                    ("other", "techstacks/other.md", (".",)),
                ]
            ),
        )
        self.write(
            "techstacks/one/README.md",
            map_source(
                [("other", "techstacks/one/leaf.md", (".",))], context_id="shared"
            ),
        )
        self.write(
            "techstacks/one/leaf.md",
            leaf_source("other", [("ONE-001", "Keep the one rule.")]),
        )
        self.write(
            "techstacks/other.md",
            leaf_source("other", [("OTHER-001", "Keep the other rule.")]),
        )
        resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("DUPLICATE_CONTEXT_ID",), self.codes(resolution))
        duplicate = next(
            item for item in resolution.diagnostics if item.code == "DUPLICATE_CONTEXT_ID"
        )
        self.assertEqual("techstacks/one/README.md", duplicate.path)
        self.assertEqual("other", duplicate.context_id)

    def test_a_row_child_id_mismatch_blocks(self):
        self.write(
            "techstacks/README.md",
            map_source([("general", "techstacks/general.md", (".",))]),
        )
        self.write(
            "techstacks/general.md",
            leaf_source("different", [("GENERAL-001", "Keep context bounded.")]),
        )
        resolution = self.resolve()
        self.assertEqual(("ROW_CHILD_ID_MISMATCH",), self.codes(resolution))
        self.assertEqual("techstacks/general.md", resolution.diagnostics[0].path)
        self.assertEqual("general", resolution.diagnostics[0].context_id)

    def test_a_duplicate_selected_path_blocks(self):
        self.write(
            "techstacks/README.md",
            map_source([("alpha", "techstacks/one/README.md", (".",))]),
        )
        self.write(
            "techstacks/one/README.md",
            map_source([("beta", "techstacks/shared.md", (".",))], context_id="alpha"),
        )
        self.write(
            "techstacks/shared.md",
            leaf_source("beta", [("SHARED-001", "Keep the shared rule.")]),
        )
        # The second selected reference to the same path is the duplicate.
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("alpha", "techstacks/one/README.md", (".",)),
                    ("gamma", "techstacks/shared.md", (".",)),
                ]
            ),
        )
        resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("ROW_CHILD_ID_MISMATCH", "DUPLICATE_RULE_PATH"), self.codes(resolution))

    def test_a_cycle_between_selected_maps_blocks(self):
        self.write(
            "techstacks/README.md",
            map_source([("alpha", "techstacks/one/README.md", (".",))]),
        )
        self.write(
            "techstacks/one/README.md",
            map_source(
                [("beta", "techstacks/two/README.md", (".",))], context_id="alpha"
            ),
        )
        self.write(
            "techstacks/two/README.md",
            map_source(
                [("gamma", "techstacks/one/README.md", (".",))], context_id="beta"
            ),
        )
        resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("CONTEXT_CYCLE",), self.codes(resolution))
        cycle = next(item for item in resolution.diagnostics if item.code == "CONTEXT_CYCLE")
        self.assertEqual("techstacks/one/README.md", cycle.path)
        self.assertEqual("gamma", cycle.context_id)

    def test_a_row_path_that_escapes_the_root_is_an_invalid_map(self):
        self.write(
            "techstacks/README.md",
            map_source([("alpha", "techstacks/../outside.md", (".",))]),
        )
        resolution = self.resolve()
        self.assertEqual(("INVALID_MAP",), self.codes(resolution))
        self.assertEqual("techstacks/README.md", resolution.diagnostics[0].path)

    def test_a_missing_selected_rule_file_blocks(self):
        self.write(
            "techstacks/README.md",
            map_source([("general", "techstacks/general.md", (".",))]),
        )
        resolution = self.resolve()
        self.assertEqual(("MISSING_RULE_FILE",), self.codes(resolution))
        self.assertEqual("techstacks/general.md", resolution.diagnostics[0].path)


class AuthorityTest(ProjectMixin, unittest.TestCase):
    """The retained version-3 authority cases, independent of author order."""

    def write_general_and_component(self, *, order="general-first", override=("root",)):
        general_row = ("general", "techstacks/general.md", (".",))
        domain_row = ("domain", "techstacks/domain/README.md", ("src/",))
        rows = (
            [general_row, domain_row]
            if order == "general-first"
            else [domain_row, general_row]
        )
        self.write("techstacks/README.md", map_source(rows))
        self.write(
            "techstacks/general.md",
            leaf_source("general", [("SHARED-001", "Keep the general rule.")]),
        )
        self.write(
            "techstacks/domain/README.md",
            map_source(
                [("component", "techstacks/domain/component.md", ("src/a",))],
                context_id="domain",
            ),
        )
        self.write(
            "techstacks/domain/component.md",
            leaf_source(
                "component",
                [("SHARED-001", "Keep the component rule.")],
                overrides=[
                    ("SHARED-001", target, "the nearer context owns this rule")
                    for target in override
                ],
            ),
        )

    def test_general_before_map_equals_map_before_general(self):
        self.write_general_and_component(override=("general",))
        first = self.resolve(scope_paths=("src/a",))
        self.assertEqual("applicable", first.status)
        self.setUp()
        self.write_general_and_component(order="domain-first", override=("general",))
        second = self.resolve(scope_paths=("src/a",))
        self.assertEqual("applicable", second.status)
        self.assertEqual(first.snapshot.effective_rules, second.snapshot.effective_rules)

    def test_the_component_names_the_nearest_dominating_context(self):
        self.write_general_and_component(override=("general",))
        resolution = self.resolve(scope_paths=("src/a",))
        rules = resolution.snapshot.effective_rules
        self.assertEqual(2, len(rules))
        by_source = {rule.source_path: rule for rule in rules}
        component = by_source["techstacks/domain/component.md"]
        self.assertEqual("general", component.overrides_context_id)
        self.assertEqual("techstacks/domain/README.md", component.authority_map)
        self.assertEqual(("src/a",), component.applies_to)
        general = by_source["techstacks/general.md"]
        self.assertIsNone(general.overrides_context_id)
        self.assertEqual("techstacks/README.md", general.authority_map)

    def test_naming_a_farther_ancestor_is_non_nearest(self):
        # root/general -> domain/general -> component: the component must name
        # the domain, not the root.
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("general", "techstacks/general.md", (".",)),
                    ("domain", "techstacks/domain/README.md", ("src/",)),
                ]
            ),
        )
        self.write(
            "techstacks/general.md",
            leaf_source("general", [("SHARED-001", "Keep the root rule.")]),
        )
        self.write(
            "techstacks/domain/README.md",
            map_source(
                [
                    ("domaingeneral", "techstacks/domain/general.md", ("src/",)),
                    ("component", "techstacks/domain/component.md", ("src/a",)),
                ],
                context_id="domain",
            ),
        )
        self.write(
            "techstacks/domain/general.md",
            leaf_source(
                "domaingeneral",
                [("SHARED-001", "Keep the domain rule.")],
                overrides=[("SHARED-001", "general", "the root rule is nearest")],
            ),
        )
        self.write(
            "techstacks/domain/component.md",
            leaf_source(
                "component",
                [("SHARED-001", "Keep the component rule.")],
                overrides=[("SHARED-001", "general", "wrongly names the root")],
            ),
        )
        resolution = self.resolve(scope_paths=("src/a",))
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("NON_NEAREST_OVERRIDE",), self.codes(resolution))
        finding = next(
            item for item in resolution.diagnostics if item.code == "NON_NEAREST_OVERRIDE"
        )
        self.assertEqual("techstacks/domain/component.md", finding.path)
        self.assertEqual("component", finding.context_id)
        # Naming the domain instead resolves.
        self.write(
            "techstacks/domain/component.md",
            leaf_source(
                "component",
                [("SHARED-001", "Keep the component rule.")],
                overrides=[("SHARED-001", "domaingeneral", "the domain is nearest")],
            ),
        )
        resolution = self.resolve(scope_paths=("src/a",))
        self.assertEqual("applicable", resolution.status)

    def test_same_map_narrower_row_overrides_the_same_map_general_row(self):
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("wide", "techstacks/wide.md", ("src/",)),
                    ("narrow", "techstacks/narrow.md", ("src/a",)),
                ]
            ),
        )
        self.write(
            "techstacks/wide.md",
            leaf_source("wide", [("SHARED-001", "Keep the wide rule.")]),
        )
        self.write(
            "techstacks/narrow.md",
            leaf_source(
                "narrow",
                [("SHARED-001", "Keep the narrow rule.")],
                overrides=[("SHARED-001", "wide", "the wide row is nearest")],
            ),
        )
        resolution = self.resolve(scope_paths=("src/a",))
        self.assertEqual("applicable", resolution.status)
        narrow = next(
            rule
            for rule in resolution.snapshot.effective_rules
            if rule.source_path == "techstacks/narrow.md"
        )
        self.assertEqual("wide", narrow.overrides_context_id)

    def test_disjoint_siblings_coexist_and_overlapping_siblings_conflict(self):
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("left", "techstacks/left.md", ("src/left/",)),
                    ("right", "techstacks/right.md", ("src/right/",)),
                ]
            ),
        )
        self.write(
            "techstacks/left.md",
            leaf_source("left", [("SHARED-001", "Keep the left rule.")]),
        )
        self.write(
            "techstacks/right.md",
            leaf_source("right", [("SHARED-001", "Keep the right rule.")]),
        )
        resolution = self.resolve(scope_paths=("src/left/a", "src/right/b"))
        self.assertEqual("applicable", resolution.status)
        self.assertEqual(2, len(resolution.snapshot.effective_rules))
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("left", "techstacks/left.md", ("src/shared/",)),
                    ("right", "techstacks/right.md", ("src/shared/b",)),
                ]
            ),
        )
        self.write(
            "techstacks/right.md",
            leaf_source(
                "right",
                [("SHARED-001", "Keep the right rule.")],
                overrides=[("SHARED-001", "left", "the left row is nearest")],
            ),
        )
        resolution = self.resolve(scope_paths=("src/shared/b",))
        self.assertEqual("applicable", resolution.status)

    def test_two_overlapping_incomparable_descendants_conflict(self):
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("ancestor", "techstacks/ancestor.md", (".",)),
                    ("first", "techstacks/first/README.md", ("src/a/",)),
                    ("second", "techstacks/second/README.md", ("src/a/b/",)),
                ]
            ),
        )
        self.write(
            "techstacks/ancestor.md",
            leaf_source("ancestor", [("SHARED-001", "Keep the ancestor rule.")]),
        )
        for name, identifier, selector in (
            ("first", "firstleaf", "src/a/"),
            ("second", "secondleaf", "src/a/b/"),
        ):
            self.write(
                f"techstacks/{name}/README.md",
                map_source(
                    [(identifier, f"techstacks/{name}/leaf.md", (selector,))],
                    context_id=name,
                ),
            )
            self.write(
                f"techstacks/{name}/leaf.md",
                leaf_source(
                    identifier,
                    [("SHARED-001", f"Keep the {name} rule.")],
                    overrides=[("SHARED-001", "ancestor", "the ancestor is nearest")],
                ),
            )
        resolution = self.resolve(scope_paths=("src/a/b/c",))
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("PEER_RULE_CONFLICT", "PEER_RULE_CONFLICT"), self.codes(resolution))

    def test_two_disjoint_descendants_each_name_the_shared_nearest_ancestor(self):
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("ancestor", "techstacks/ancestor.md", (".",)),
                    ("left", "techstacks/left.md", ("src/left/",)),
                    ("right", "techstacks/right.md", ("src/right/",)),
                ]
            ),
        )
        self.write(
            "techstacks/ancestor.md",
            leaf_source("ancestor", [("SHARED-001", "Keep the ancestor rule.")]),
        )
        for name in ("left", "right"):
            self.write(
                f"techstacks/{name}.md",
                leaf_source(
                    name,
                    [("SHARED-001", f"Keep the {name} rule.")],
                    overrides=[("SHARED-001", "ancestor", "the ancestor is nearest")],
                ),
            )
        resolution = self.resolve(scope_paths=("src/left/a", "src/right/b"))
        self.assertEqual("applicable", resolution.status)
        targets = {
            rule.source_path: rule.overrides_context_id
            for rule in resolution.snapshot.effective_rules
        }
        self.assertEqual("ancestor", targets["techstacks/left.md"])
        self.assertEqual("ancestor", targets["techstacks/right.md"])
        self.assertIsNone(targets["techstacks/ancestor.md"])

    def test_a_skipped_ancestor_without_the_rule_is_not_the_nearest(self):
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("ancestor", "techstacks/ancestor.md", (".",)),
                    ("middle", "techstacks/middle/README.md", ("src/",)),
                ]
            ),
        )
        self.write(
            "techstacks/ancestor.md",
            leaf_source("ancestor", [("SHARED-001", "Keep the ancestor rule.")]),
        )
        self.write(
            "techstacks/middle/README.md",
            map_source(
                [
                    ("middleleaf", "techstacks/middle/leaf.md", ("src/",)),
                    ("deep", "techstacks/middle/deep.md", ("src/a",)),
                ],
                context_id="middle",
            ),
        )
        # The middle leaf carries a different Rule ID, so it is skipped.
        self.write(
            "techstacks/middle/leaf.md",
            leaf_source("middleleaf", [("OTHER-001", "Keep the middle rule.")]),
        )
        self.write(
            "techstacks/middle/deep.md",
            leaf_source(
                "deep",
                [("SHARED-001", "Keep the deep rule.")],
                overrides=[("SHARED-001", "ancestor", "the ancestor is nearest")],
            ),
        )
        resolution = self.resolve(scope_paths=("src/a",))
        self.assertEqual("applicable", resolution.status)
        deep = next(
            rule
            for rule in resolution.snapshot.effective_rules
            if rule.source_path == "techstacks/middle/deep.md"
        )
        self.assertEqual("ancestor", deep.overrides_context_id)

    def test_a_missing_or_unknown_override_is_invalid(self):
        self.write_general_and_component(override=())
        resolution = self.resolve(scope_paths=("src/a",))
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("INVALID_OVERRIDE",), self.codes(resolution))
        self.write_general_and_component(override=("unknowncontext",))
        resolution = self.resolve(scope_paths=("src/a",))
        self.assertEqual(("INVALID_OVERRIDE",), self.codes(resolution))

    def test_an_override_without_any_dominating_occurrence_is_invalid(self):
        self.write(
            "techstacks/README.md",
            map_source([("only", "techstacks/only.md", (".",))]),
        )
        self.write(
            "techstacks/only.md",
            leaf_source(
                "only",
                [("SHARED-001", "Keep the only rule.")],
                overrides=[("SHARED-001", "absent", "there is nothing to override")],
            ),
        )
        resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("INVALID_OVERRIDE",), self.codes(resolution))

    def test_effective_rule_fields_equal_their_leaf_and_referring_row(self):
        self.write_base_fixture()
        resolution = self.resolve(scope_paths=("src/frontend/components/Button.tsx",))
        rules = {rule.rule_id: rule for rule in resolution.snapshot.effective_rules}
        button = rules["BUTTON-001"]
        self.assertEqual("techstacks/frontend/components/Button.md", button.source_path)
        self.assertEqual("button", button.context_id)
        self.assertEqual("techstacks/frontend/README.md", button.authority_map)
        self.assertEqual(("src/frontend/components/Button.tsx",), button.applies_to)
        self.assertEqual(
            model.sha256_hex(b"Preserve the public Button contract."),
            button.statement_sha256,
        )


class EvidenceTest(ProjectMixin, unittest.TestCase):
    def test_evidence_observations_hash_the_exact_raw_bytes(self):
        self.write_base_fixture()
        resolution = self.resolve(scope_paths=("src/frontend/components/Button.tsx",))
        button = next(
            item
            for item in resolution.snapshot.selected_files
            if item.path.endswith("Button.md")
        )
        self.assertEqual(1, len(button.evidence))
        observation = button.evidence[0]
        self.assertEqual("evidence/button.txt", observation.path)
        self.assertEqual(19, observation.bytes)
        self.assertEqual(
            model.sha256_hex(b"button-evidence-v1\n"), observation.sha256
        )

    def test_totals_recompute_from_the_selected_arrays(self):
        self.write_base_fixture()
        resolution = self.resolve(scope_paths=("src/frontend/components/Button.tsx",))
        snapshot = resolution.snapshot
        totals = snapshot.totals
        self.assertEqual(len(snapshot.selected_files), totals.file_count)
        self.assertEqual(
            sum(item.bytes for item in snapshot.selected_files), totals.bytes
        )
        self.assertEqual(1, totals.evidence_file_count)
        self.assertEqual(19, totals.evidence_bytes)
        self.assertEqual(len(snapshot.effective_rules), totals.rule_count)
        for item in snapshot.selected_files:
            self.assertEqual(item.identity.size, item.bytes)
            self.assertEqual(
                len((self.root / item.path).read_bytes()), item.bytes
            )
            self.assertEqual(
                model.sha256_hex((self.root / item.path).read_bytes()), item.sha256
            )

    def test_missing_evidence_is_a_waivable_finding_with_path_and_context(self):
        self.write_base_fixture()
        (self.root / "evidence/button.txt").unlink()
        resolution = self.resolve(scope_paths=("src/frontend/components/Button.tsx",))
        self.assertEqual("blocked", resolution.status)
        finding = next(
            item for item in resolution.diagnostics if item.code == "MISSING_EVIDENCE"
        )
        self.assertEqual("evidence/button.txt", finding.path)
        self.assertEqual("button", finding.context_id)
        self.assertTrue(finding.waivable)
        self.assertIsNone(finding.waived_by)

    def test_an_over_limit_evidence_file_blocks(self):
        self.write_base_fixture()
        self.write("evidence/button.txt", b"x" * (model.EVIDENCE_FILE_BYTE_LIMIT + 1))
        resolution = self.resolve(scope_paths=("src/frontend/components/Button.tsx",))
        self.assertEqual("blocked", resolution.status)
        finding = next(
            item for item in resolution.diagnostics if item.code == "EVIDENCE_BYTE_LIMIT"
        )
        self.assertEqual("evidence/button.txt", finding.path)
        self.assertEqual("button", finding.context_id)

    def test_an_exact_limit_evidence_file_is_accepted(self):
        self.write_base_fixture()
        self.write("evidence/button.txt", b"x" * model.EVIDENCE_FILE_BYTE_LIMIT)
        resolution = self.resolve(scope_paths=("src/frontend/components/Button.tsx",))
        self.assertEqual("applicable", resolution.status)
        self.assertEqual(
            model.EVIDENCE_FILE_BYTE_LIMIT, resolution.snapshot.totals.evidence_bytes
        )

    def test_the_evidence_file_count_limit_blocks(self):
        rows = []
        for index in range(9):
            identifier = f"leaf{index:02d}"
            path = f"techstacks/{identifier}.md"
            rows.append((identifier, path, (".",)))
            declared = [f"evidence/e{index:02d}-{slot}.txt" for slot in range(8)]
            for name in declared:
                self.write(name, b"x")
            self.write(
                path,
                leaf_source(
                    identifier,
                    [(f"L{index:02d}-001", "Keep the rule.")],
                    evidence=declared,
                ),
            )
        self.write("techstacks/README.md", map_source(rows))
        resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("EVIDENCE_FILE_LIMIT",), self.codes(resolution))

    def test_the_evidence_aggregate_byte_limit_blocks_at_the_boundary(self):
        # Eleven leaves declare one 1 MiB evidence file each, so the 8 MiB
        # aggregate is exceeded on the ninth read. The cap is enforced as the
        # reads accumulate, so the last two declared paths are never read.
        rows = []
        block = b"x" * model.EVIDENCE_FILE_BYTE_LIMIT
        for index in range(11):
            identifier = f"leaf{index:02d}"
            path = f"techstacks/{identifier}.md"
            declared = f"evidence/e{index:02d}.txt"
            rows.append((identifier, path, (".",)))
            self.write(declared, block)
            self.write(
                path,
                leaf_source(
                    identifier,
                    [(f"L{index:02d}-001", "Keep the rule.")],
                    evidence=(declared,),
                ),
            )
        self.write("techstacks/README.md", map_source(rows))
        original = resolver.read_project_file
        observed = []

        def spy(root_fd, relative_path, limit):
            observed.append(relative_path)
            return original(root_fd, relative_path, limit)

        with mock.patch.object(resolver, "read_project_file", spy):
            resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("EVIDENCE_AGGREGATE_BYTE_LIMIT",), self.codes(resolution))
        self.assertEqual(
            [f"evidence/e{index:02d}.txt" for index in range(9)],
            [path for path in observed if path.startswith("evidence/")],
        )

    def test_evidence_exceeding_both_caps_reports_both_codes_in_rank_order(self):
        # Eleven leaves declare eight 128 KiB evidence files each: 88 files
        # and 11 MiB against the 64-file and 8 MiB caps, in twelve selected
        # files. 8 MiB / 128 KiB is exactly 64, so the 65th read is the first
        # to cross the aggregate cap, and the count cap is already exceeded
        # at that point. Both frozen codes must be reported, in registry rank
        # order, while the read bound stays at the boundary.
        rows = []
        block = b"x" * (128 * 1024)
        for index in range(11):
            identifier = f"leaf{index:02d}"
            path = f"techstacks/{identifier}.md"
            rows.append((identifier, path, (".",)))
            declared = [f"evidence/{identifier}-{slot}.bin" for slot in range(8)]
            for name in declared:
                self.write(name, block)
            self.write(
                path,
                leaf_source(
                    identifier,
                    [(f"L{index:02d}-001", "Keep the rule.")],
                    evidence=declared,
                ),
            )
        self.write("techstacks/README.md", map_source(rows))
        original = resolver.read_project_file
        observed = []

        def spy(root_fd, relative_path, limit):
            observed.append(relative_path)
            return original(root_fd, relative_path, limit)

        with mock.patch.object(resolver, "read_project_file", spy):
            resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(
            ("EVIDENCE_FILE_LIMIT", "EVIDENCE_AGGREGATE_BYTE_LIMIT"),
            self.codes(resolution),
        )
        evidence_reads = [path for path in observed if path.startswith("evidence/")]
        self.assertEqual(65, len(evidence_reads))
        self.assertEqual("evidence/leaf08-0.bin", evidence_reads[-1])

    def test_evidence_drift_during_observation_blocks(self):
        self.write_base_fixture()
        original = fs.read_bounded_regular

        def drifting(parent_fd, name, limit):
            if name == "button.txt":
                return fs.Observation(code="FILE_CHANGED")
            return original(parent_fd, name, limit)

        with mock.patch.object(fs, "read_bounded_regular", drifting):
            resolution = self.resolve(
                scope_paths=("src/frontend/components/Button.tsx",)
            )
        self.assertEqual("blocked", resolution.status)
        finding = next(
            item for item in resolution.diagnostics if item.code == "FILE_CHANGED"
        )
        self.assertEqual("evidence/button.txt", finding.path)


class FreshnessTest(ProjectMixin, unittest.TestCase):
    def write_single_leaf(self, **leaf_overrides):
        self.write(
            "techstacks/README.md",
            map_source([("general", "techstacks/general.md", (".",))]),
        )
        self.write(
            "techstacks/general.md",
            leaf_source(
                "general", [("GENERAL-001", "Keep context bounded.")], **leaf_overrides
            ),
        )

    def test_an_expired_review_interval_is_a_waivable_stale_rule(self):
        self.write_single_leaf(reviewed_on="2025-01-01", within=30)
        resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        finding = next(
            item for item in resolution.diagnostics if item.code == "STALE_RULE"
        )
        self.assertEqual("techstacks/general.md", finding.path)
        self.assertEqual("general", finding.context_id)
        self.assertTrue(finding.waivable)

    def test_the_freshness_boundary_is_inclusive(self):
        self.write_single_leaf(reviewed_on="2026-08-01", within=23)
        self.assertEqual("applicable", self.resolve().status)
        self.write_single_leaf(reviewed_on="2026-08-01", within=22)
        self.assertEqual("blocked", self.resolve().status)

    def test_a_future_review_date_is_not_waivable(self):
        self.write_single_leaf(reviewed_on="2026-09-01")
        resolution = self.resolve()
        finding = next(
            item for item in resolution.diagnostics if item.code == "FUTURE_REVIEW_DATE"
        )
        self.assertFalse(finding.waivable)

    def test_deprecation_on_or_before_as_of_blocks_and_a_future_date_does_not(self):
        self.write_single_leaf(deprecated="yes: 2026-08-24: the rule moved")
        resolution = self.resolve()
        self.assertEqual(("DEPRECATED_RULE",), self.codes(resolution))
        self.write_single_leaf(deprecated="yes: 2026-08-25: the rule moves soon")
        resolution = self.resolve()
        self.assertEqual("applicable", resolution.status)
        self.assertTrue(resolution.snapshot.selected_files[1].deprecated)


class DeclaredConflictTest(ProjectMixin, unittest.TestCase):
    def test_a_declared_conflict_always_blocks(self):
        self.write_base_fixture()
        conflict = model.DeclaredConflict(
            source="techstacks/general.md",
            target="techstacks/frontend/README.md",
            detail="both claim the same selector",
        )
        resolution = self.resolve(declared_conflicts=(conflict,))
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("DECLARED_AUTHORITY_CONFLICT",), self.codes(resolution))
        finding = next(
            item
            for item in resolution.diagnostics
            if item.code == "DECLARED_AUTHORITY_CONFLICT"
        )
        self.assertIsNone(finding.path)
        self.assertIsNone(finding.context_id)
        self.assertFalse(finding.waivable)


class ExceptionMatrixTest(ProjectMixin, unittest.TestCase):
    def write_stale_fixture(self):
        self.write(
            "techstacks/README.md",
            map_source([("general", "techstacks/general.md", (".",))], title="Stale map"),
        )
        self.write(
            "techstacks/general.md",
            leaf_source(
                "general",
                [("STALE-001", "Require an explicit freshness decision.")],
                reviewed_on="2025-01-01",
                within=30,
            ),
        )

    def resolve_with(self, approval, **overrides):
        provisional = make_input(**overrides)
        return self.resolve(
            make_input(exception_approvals=(approval,), **overrides)
        ), provisional

    def test_caller_shape_defects_raise_before_any_root_examination(self):
        self.write_stale_fixture()
        provisional = make_input()
        approval = make_approval(provisional)
        payload = provisional.to_json_object()
        payload["exception_approvals"] = [
            approval.to_json_object(),
            approval.to_json_object(),
        ]
        with self.assertRaises(model.TechstackInputError) as error:
            model.resolution_input_from_json_object(payload)
        self.assertEqual("INPUT_DUPLICATE", error.exception.code)
        payload["exception_approvals"] = [approval.to_json_object()]
        payload["exception_approvals"][0]["unknown"] = 1
        with self.assertRaises(model.TechstackInputError) as error:
            model.resolution_input_from_json_object(payload)
        self.assertEqual("INPUT_UNKNOWN_KEY", error.exception.code)

    def assert_blocked_before_root(self, approval, code):
        self.write_stale_fixture()
        with mock.patch.object(resolver, "read_project_file") as reader:
            resolution = self.resolve(exception_approvals=(approval,))
        reader.assert_not_called()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual((code,), self.codes(resolution))
        self.assertEqual("general", resolution.diagnostics[0].context_id)
        self.assertIsNone(resolution.diagnostics[0].path)
        return resolution

    def test_every_blocked_pre_root_row(self):
        provisional = make_input()
        self.assert_blocked_before_root(
            make_approval(provisional, coordinator_attested=False),
            "UNATTESTED_EXCEPTION",
        )
        self.assert_blocked_before_root(
            make_approval(provisional, authorized_by="coordinator"),
            "INVALID_EXCEPTION_PROVENANCE",
        )
        self.assert_blocked_before_root(
            make_approval(provisional, authorization_reference=""),
            "INVALID_EXCEPTION_PROVENANCE",
        )
        self.assert_blocked_before_root(
            make_approval(provisional, plan_version=7), "EXCEPTION_BINDING_MISMATCH"
        )
        self.assert_blocked_before_root(
            make_approval(provisional, attempt_id="attempt-0"),
            "EXCEPTION_BINDING_MISMATCH",
        )
        self.assert_blocked_before_root(
            make_approval(provisional, scope_sha256="b" * 64),
            "EXCEPTION_DIGEST_MISMATCH",
        )
        self.assert_blocked_before_root(
            make_approval(provisional, binding_sha256="c" * 64, recompute_binding=False),
            "EXCEPTION_DIGEST_MISMATCH",
        )
        self.assert_blocked_before_root(
            make_approval(provisional, issued_on="2026-08-25", expires_on="2026-09-01"),
            "EXCEPTION_EXPIRED",
        )
        self.assert_blocked_before_root(
            make_approval(provisional, issued_on="2026-07-01", expires_on="2026-07-31"),
            "EXCEPTION_EXPIRED",
        )
        self.assert_blocked_before_root(
            make_approval(provisional, issued_on="2026-08-20", expires_on="2026-09-20"),
            "EXCEPTION_EXPIRED",
        )
        # Exactly thirty days is inside the window.
        self.write_stale_fixture()
        inside = make_approval(
            provisional, issued_on="2026-08-20", expires_on="2026-09-19"
        )
        resolution = self.resolve(exception_approvals=(inside,))
        self.assertEqual("applicable", resolution.status)

    def test_a_prior_plan_scope_fails_the_scope_digest(self):
        self.write_stale_fixture()
        other = make_input(scope_paths=("src/other",))
        approval = make_approval(other)
        resolution = self.resolve(exception_approvals=(approval,))
        self.assertEqual(("EXCEPTION_DIGEST_MISMATCH",), self.codes(resolution))

    def test_exact_consumption_turns_the_finding_into_a_warning(self):
        self.write_stale_fixture()
        provisional = make_input()
        approval = make_approval(provisional)
        resolution = self.resolve(exception_approvals=(approval,))
        self.assertEqual("applicable", resolution.status)
        self.assertEqual(1, len(resolution.diagnostics))
        finding = resolution.diagnostics[0]
        self.assertEqual("STALE_RULE", finding.code)
        self.assertEqual("warning", finding.severity)
        self.assertEqual("approval-1", finding.waived_by)
        self.assertTrue(finding.waivable)
        self.assertEqual(
            (approval,), resolution.snapshot.exception_approvals
        )

    def test_all_three_waivable_classes_can_be_consumed(self):
        provisional = make_input()
        self.write(
            "techstacks/README.md",
            map_source([("general", "techstacks/general.md", (".",))]),
        )
        cases = (
            (
                {"reviewed_on": "2025-01-01", "within": 30},
                make_approval(provisional, code="STALE_RULE"),
            ),
            (
                {"deprecated": "yes: 2026-08-01: the rule moved"},
                make_approval(provisional, code="DEPRECATED_RULE"),
            ),
            (
                {"evidence": ("evidence/missing.txt",)},
                make_approval(
                    provisional,
                    code="MISSING_EVIDENCE",
                    evidence_path="evidence/missing.txt",
                ),
            ),
        )
        for leaf_overrides, approval in cases:
            with self.subTest(code=approval.target.code):
                self.write(
                    "techstacks/general.md",
                    leaf_source(
                        "general",
                        [("GENERAL-001", "Keep context bounded.")],
                        **leaf_overrides,
                    ),
                )
                resolution = self.resolve(exception_approvals=(approval,))
                self.assertEqual("applicable", resolution.status)
                self.assertEqual(
                    approval.target.code, resolution.diagnostics[0].code
                )
                self.assertEqual("approval-1", resolution.diagnostics[0].waived_by)

    def test_a_non_waivable_target_code_is_a_caller_error(self):
        provisional = make_input()
        payload = provisional.to_json_object()
        approval = make_approval(provisional).to_json_object()
        approval["target"]["code"] = "INVALID_MAP"
        payload["exception_approvals"] = [approval]
        with self.assertRaises(model.TechstackInputError) as error:
            model.resolution_input_from_json_object(payload)
        self.assertEqual("INPUT_VALUE", error.exception.code)
        self.assertEqual(
            "/exception_approvals/0/target/code", error.exception.field
        )
        self.assertEqual(
            model.WAIVABLE_CODES,
            ("STALE_RULE", "DEPRECATED_RULE", "MISSING_EVIDENCE"),
        )

    def test_a_non_waivable_finding_is_never_consumed(self):
        self.write(
            "techstacks/README.md",
            map_source([("general", "techstacks/general.md", (".",))]),
        )
        self.write(
            "techstacks/general.md",
            leaf_source(
                "general",
                [("GENERAL-001", "Keep context bounded.")],
                reviewed_on="2026-09-01",
            ),
        )
        approval = make_approval(make_input())
        resolution = self.resolve(exception_approvals=(approval,))
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(
            ("FUTURE_REVIEW_DATE", "UNUSED_EXCEPTION"), self.codes(resolution)
        )

    def test_an_unused_approval_blocks(self):
        self.write_base_fixture()
        approval = make_approval(make_input())
        resolution = self.resolve(exception_approvals=(approval,))
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("UNUSED_EXCEPTION",), self.codes(resolution))

    def test_an_ambiguous_approval_matches_multiple_findings(self):
        # Two stale leaves share Context ID ``stale`` because a map rejects a
        # duplicate row ID only within itself: DUPLICATE_CONTEXT_ID records the
        # repeat but does not stop the traversal, so both findings survive and
        # one approval matches both.
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("dom", "techstacks/dom/README.md", (".",)),
                    ("stale", "techstacks/stale.md", (".",)),
                ]
            ),
        )
        self.write(
            "techstacks/dom/README.md",
            map_source(
                [("stale", "techstacks/dom/stale.md", (".",))], context_id="dom"
            ),
        )
        for path in ("techstacks/stale.md", "techstacks/dom/stale.md"):
            self.write(
                path,
                leaf_source(
                    "stale",
                    [("SHARED-001", "Keep context bounded.")],
                    reviewed_on="2025-01-01",
                    within=30,
                ),
            )
        approval = make_approval(make_input(), context_id="stale")
        resolution = self.resolve(exception_approvals=(approval,))
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(
            (
                ("DUPLICATE_CONTEXT_ID", "techstacks/dom/README.md", "stale"),
                ("INVALID_OVERRIDE", "techstacks/dom/stale.md", "stale"),
                ("STALE_RULE", "techstacks/dom/stale.md", "stale"),
                ("STALE_RULE", "techstacks/stale.md", "stale"),
                ("AMBIGUOUS_EXCEPTION", None, "stale"),
            ),
            tuple(
                (item.code, item.path, item.context_id)
                for item in resolution.diagnostics
            ),
        )
        self.assertTrue(
            all(item.waived_by is None for item in resolution.diagnostics)
        )

    def test_reordered_approvals_canonicalize_to_the_same_snapshot(self):
        self.write(
            "techstacks/README.md",
            map_source(
                [
                    ("general", "techstacks/general.md", (".",)),
                    ("other", "techstacks/other.md", (".",)),
                ]
            ),
        )
        self.write(
            "techstacks/general.md",
            leaf_source(
                "general",
                [("GENERAL-001", "Keep context bounded.")],
                reviewed_on="2025-01-01",
                within=30,
            ),
        )
        self.write(
            "techstacks/other.md",
            leaf_source(
                "other",
                [("OTHER-001", "Keep the other rule.")],
                reviewed_on="2025-01-01",
                within=30,
            ),
        )
        provisional = make_input()
        first = make_approval(provisional, approval_id="approval-1", context_id="general")
        second = make_approval(provisional, approval_id="approval-2", context_id="other")
        forward = self.resolve(exception_approvals=(first, second))
        backward = self.resolve(exception_approvals=(second, first))
        self.assertEqual("applicable", forward.status)
        self.assertEqual(
            forward.snapshot.snapshot_sha256, backward.snapshot.snapshot_sha256
        )

    def test_the_resolver_never_opens_or_recomputes_the_opaque_provenance(self):
        self.write_stale_fixture()
        self.write("evidence/decision.txt", b"the durable decision evidence\n")
        provisional = make_input()
        approval = make_approval(
            provisional,
            authorization_reference="evidence/decision.txt",
            authorization_digest="f" * 64,
        )
        original = resolver.read_project_file
        observed = []

        def spy(root_fd, relative_path, limit):
            observed.append(relative_path)
            return original(root_fd, relative_path, limit)

        with mock.patch.object(resolver, "read_project_file", spy):
            resolution = self.resolve(exception_approvals=(approval,))
        self.assertEqual("applicable", resolution.status)
        self.assertNotIn("evidence/decision.txt", observed)
        self.assertEqual(
            "f" * 64,
            resolution.snapshot.exception_approvals[0].authorization_digest,
        )
        source = (ROOT / "src/brichan/techstacks/resolver.py").read_text("utf-8")
        self.assertNotIn("authorization_reference)", source)


class SnapshotTest(ProjectMixin, unittest.TestCase):
    def test_the_maximum_valid_fixture_yields_a_deterministic_snapshot(self):
        rows = []
        for index in range(11):
            identifier = f"leaf{index:02d}"
            path = f"techstacks/{identifier}.md"
            rows.append((identifier, path, (".",)))
            self.write(
                path,
                leaf_source(identifier, [(f"L{index:02d}-001", "Keep the rule.")]),
            )
        self.write("techstacks/README.md", map_source(rows))
        first = self.resolve()
        second = self.resolve()
        self.assertEqual("applicable", first.status)
        self.assertEqual(12, first.snapshot.totals.file_count)
        self.assertEqual(11, first.snapshot.totals.rule_count)
        self.assertEqual(
            first.snapshot.snapshot_sha256, second.snapshot.snapshot_sha256
        )
        document = model.snapshot_document(first.snapshot)
        self.assertTrue(document.endswith("\n"))
        self.assertLessEqual(
            len(document.encode("utf-8")), model.SNAPSHOT_DOCUMENT_BYTE_LIMIT
        )
        self.assertEqual(
            first.snapshot.snapshot_sha256,
            model.snapshot_digest(first.snapshot.to_json_object()),
        )

    def test_a_thirteenth_selected_file_overflows(self):
        rows = []
        for index in range(12):
            identifier = f"leaf{index:02d}"
            path = f"techstacks/{identifier}.md"
            rows.append((identifier, path, (".",)))
            self.write(
                path,
                leaf_source(identifier, [(f"L{index:02d}-001", "Keep the rule.")]),
            )
        self.write("techstacks/README.md", map_source(rows))
        resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("SELECTED_FILE_LIMIT",), self.codes(resolution))
        self.assertIsNone(resolution.snapshot)

    def test_the_selected_aggregate_byte_limit_overflows(self):
        padding = tuple(f"Scope bullet {index:02d} " + "p" * 900 for index in range(16))
        rows = []
        for index in range(3):
            identifier = f"big{index:02d}"
            path = f"techstacks/{identifier}.md"
            rows.append((identifier, path, (".",)))
            self.write(
                path,
                leaf_source(
                    identifier,
                    [(f"BIG{index:02d}-001", "s" * 900)],
                    scope=padding,
                    verification=padding,
                ),
            )
        self.write("techstacks/README.md", map_source(rows))
        resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("SELECTED_BYTE_LIMIT",), self.codes(resolution))

    def test_the_leaf_byte_limit_overflows(self):
        self.write(
            "techstacks/README.md",
            map_source([("general", "techstacks/general.md", (".",))]),
        )
        oversized = leaf_source(
            "general", [("GENERAL-001", "Keep context bounded.")]
        )
        oversized += b"x" * (model.LEAF_FILE_BYTE_LIMIT + 1 - len(oversized))
        self.write("techstacks/general.md", oversized)
        resolution = self.resolve()
        self.assertEqual(("LEAF_BYTE_LIMIT",), self.codes(resolution))
        self.assertEqual("techstacks/general.md", resolution.diagnostics[0].path)

    def test_the_map_byte_limit_and_grammar_codes_reach_the_registry(self):
        oversized = map_source([("general", "techstacks/general.md", (".",))])
        oversized += b"x" * (model.MAP_FILE_BYTE_LIMIT + 1 - len(oversized))
        self.write("techstacks/README.md", oversized)
        resolution = self.resolve()
        self.assertEqual(("MAP_BYTE_LIMIT",), self.codes(resolution))
        self.assertEqual("techstacks/README.md", resolution.diagnostics[0].path)
        rows = [
            (f"c{index:02d}", f"techstacks/c{index:02d}.md", (f"src/c{index:02d}",))
            for index in range(33)
        ]
        self.write("techstacks/README.md", map_source(rows))
        resolution = self.resolve()
        self.assertEqual(("MAP_ROW_LIMIT",), self.codes(resolution))
        self.assertEqual("techstacks/README.md", resolution.diagnostics[0].path)
        self.assertIsNone(resolution.diagnostics[0].context_id)
        selectors = tuple(f"src/s{index:02d}" for index in range(17))
        self.write(
            "techstacks/README.md",
            map_source([("general", "techstacks/general.md", selectors)]),
        )
        resolution = self.resolve()
        self.assertEqual(("SELECTOR_LIMIT",), self.codes(resolution))
        self.assertEqual("techstacks/README.md", resolution.diagnostics[0].path)
        self.assertEqual("general", resolution.diagnostics[0].context_id)
        self.write(
            "techstacks/README.md",
            map_source([("general", "techstacks/general.md", (".",))]),
        )
        self.write("techstacks/general.md", b"# Not a leaf\n")
        resolution = self.resolve()
        self.assertEqual(("INVALID_LEAF",), self.codes(resolution))
        self.assertEqual("techstacks/general.md", resolution.diagnostics[0].path)
        self.assertEqual(
            "leaf bytes do not match the leaf grammar at line 2: SECTION_BOUNDARY",
            resolution.diagnostics[0].detail,
        )

    def test_the_effective_rule_count_stays_inside_its_structural_bound(self):
        # Eleven leaves of 32 rules is the most a twelve-file selection can
        # carry, so 352 is the reachable maximum under the 384-rule cap.
        rows = []
        for index in range(11):
            identifier = f"leaf{index:02d}"
            path = f"techstacks/{identifier}.md"
            rows.append((identifier, path, (".",)))
            self.write(
                path,
                leaf_source(
                    identifier,
                    [
                        (f"L{index:02d}-{slot:03d}", f"Keep rule {slot:03d}.")
                        for slot in range(32)
                    ],
                ),
            )
        self.write("techstacks/README.md", map_source(rows))
        resolution = self.resolve()
        self.assertEqual("applicable", resolution.status)
        self.assertEqual(352, resolution.snapshot.totals.rule_count)
        self.assertLessEqual(352, model.EFFECTIVE_RULE_COUNT_LIMIT)

    def write_overflow_fixture(self, unused_approvals):
        """Write eleven stale, deprecated leaves declaring absent evidence.

        Each leaf yields ``STALE_RULE`` and ``DEPRECATED_RULE`` and eight
        ``MISSING_EVIDENCE`` records, so 110 findings plus one
        ``UNUSED_EXCEPTION`` per approval walk the array up to its cap.
        """

        rows = []
        for index in range(11):
            identifier = f"leaf{index:02d}"
            path = f"techstacks/{identifier}.md"
            rows.append((identifier, path, (".",)))
            self.write(
                path,
                leaf_source(
                    identifier,
                    [(f"L{index:02d}-001", "Keep context bounded.")],
                    reviewed_on="2025-01-01",
                    within=30,
                    deprecated="yes: 2026-08-01: the rule moved",
                    evidence=tuple(
                        f"evidence/{identifier}-{slot}.txt" for slot in range(8)
                    ),
                ),
            )
        self.write("techstacks/README.md", map_source(rows))
        approvals = tuple(
            make_approval(
                make_input(),
                approval_id=f"approval-{slot:03d}",
                context_id=f"absent{slot:03d}",
            )
            for slot in range(unused_approvals)
        )
        return self.resolve(exception_approvals=approvals)

    def test_the_diagnostic_overflow_sentinel_replaces_the_array(self):
        # Both results come from production code on a legal fixture: 128
        # accumulated records are returned complete, and the 129th discards
        # the whole array for the single rank-54 sentinel.
        resolution = self.write_overflow_fixture(18)
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(128, len(resolution.diagnostics))
        self.assertEqual(
            {
                "STALE_RULE": 11,
                "DEPRECATED_RULE": 11,
                "MISSING_EVIDENCE": 88,
                "UNUSED_EXCEPTION": 18,
            },
            collections.Counter(self.codes(resolution)),
        )
        resolution = self.write_overflow_fixture(19)
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("DIAGNOSTIC_LIMIT",), self.codes(resolution))
        self.assertIsNone(resolution.snapshot)
        self.assertEqual(
            "diagnostic count exceeded 128; individual diagnostics suppressed",
            resolution.diagnostics[0].detail,
        )

    def test_byte_identical_repeats_reach_the_overflow_sentinel(self):
        # Root -> m1 -> m2 -> m3 -> m4, then seven map-level-6 maps of 32 rows
        # each: 224 byte-identical MAP_DEPTH_LIMIT records accumulate, and
        # section 4 counts emitted records, not distinct ones.
        self.write(
            "techstacks/README.md",
            map_source([("m1", "techstacks/m1/README.md", (".",))]),
        )
        for level in range(1, 5):
            rows = (
                [(f"m{level + 1}", f"techstacks/m{level + 1}/README.md", (".",))]
                if level < 4
                else [
                    (f"d{index}", f"techstacks/d{index}/README.md", (".",))
                    for index in range(7)
                ]
            )
            self.write(
                f"techstacks/m{level}/README.md",
                map_source(rows, context_id=f"m{level}"),
            )
        for index in range(7):
            self.write(
                f"techstacks/d{index}/README.md",
                map_source(
                    [
                        (
                            f"d{index}x{slot:02d}",
                            f"techstacks/d{index}/x{slot:02d}/README.md",
                            (".",),
                        )
                        for slot in range(32)
                    ],
                    context_id=f"d{index}",
                ),
            )
        resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("DIAGNOSTIC_LIMIT",), self.codes(resolution))
        self.assertIsNone(resolution.snapshot)

    def test_root_identity_change_during_resolution_blocks(self):
        self.write_base_fixture()
        with mock.patch.object(fs, "root_identity_unchanged", return_value=False):
            resolution = self.resolve()
        self.assertEqual("blocked", resolution.status)
        self.assertEqual(("ROOT_CHANGED",), self.codes(resolution))

    def test_the_snapshot_repeats_the_canonical_input_without_a_root_path(self):
        self.write_base_fixture()
        resolution = self.resolve(
            scope_paths=("src/frontend/components/Button.tsx", "src/app.ts")
        )
        snapshot = resolution.snapshot
        self.assertEqual(
            ("src/app.ts", "src/frontend/components/Button.tsx"), snapshot.scope_paths
        )
        self.assertEqual(TASK_ID, snapshot.task_id)
        self.assertEqual(AS_OF, snapshot.as_of)
        self.assertEqual((), snapshot.context_chains)
        self.assertEqual((), snapshot.declared_conflicts)
        document = model.snapshot_document(snapshot)
        self.assertNotIn(str(self.root), document)
        self.assertNotIn("Preserve the public Button contract.", document)
        self.assertGreater(snapshot.root_identity.device, 0)
        self.assertGreater(snapshot.root_identity.inode, 0)


if __name__ == "__main__":  # pragma: no cover - exercised by the test runner
    unittest.main()
