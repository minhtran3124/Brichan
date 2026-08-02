import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.contracts.task_dossier import scaffold as scaffold_module
from brichan.contracts.task_dossier.schema import ARTIFACTS
from brichan.contracts.task_dossier.scaffold import (
    apply_scaffold,
    dossier_path,
    plan_scaffold,
)


class TaskDossierWorkflowIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.checkout = Path(self.temporary_directory.name)
        self.projects = self.checkout / "projects"
        self.dossier = self.projects / "example" / "handoffs" / "TASK-001"
        self.dossier.mkdir(parents=True)

    def run_script(self, script, *arguments):
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), *arguments],
            cwd=self.checkout,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_scaffold_dry_run_writes_nothing(self):
        actions = plan_scaffold(
            self.dossier, "TASK-001", "1", "example", repository_root=ROOT
        )
        self.assertEqual(
            len(ARTIFACTS),
            sum(1 for action in actions if action.action == "create"),
        )
        self.assertEqual([], sorted(self.dossier.iterdir()))

    def test_scaffold_apply_creates_the_complete_dossier(self):
        apply_scaffold(self.dossier, "TASK-001", "1", "example", repository_root=ROOT)
        written = sorted(path.name for path in self.dossier.glob("*.md"))
        self.assertEqual(sorted(f"{name}.md" for name in ARTIFACTS), written)
        index = (self.dossier / "index.md").read_text(encoding="utf-8")
        self.assertIn("- Task ID: `TASK-001`", index)
        self.assertIn("- Task level: `1`", index)
        self.assertIn("- Project: `example`", index)
        self.assertFalse((self.dossier / "receipt.md").exists())

    def test_scaffold_preserves_existing_artifacts(self):
        existing = self.dossier / "design.md"
        existing.write_text("# my design\n", encoding="utf-8")
        actions = apply_scaffold(
            self.dossier, "TASK-001", "1", "example", repository_root=ROOT
        )
        self.assertEqual("# my design\n", existing.read_text(encoding="utf-8"))
        preserved = [
            action for action in actions if action.path == existing
        ]
        self.assertEqual(["preserve"], [action.action for action in preserved])

    def test_scaffolded_placeholders_fail_validation(self):
        apply_scaffold(self.dossier, "TASK-001", "1", "example", repository_root=ROOT)
        result = self.run_script("validate_task_dossiers.py", "projects")
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("Invalid task dossiers", result.stderr)
        self.assertIn("canonical receipt does not exist", result.stderr)

    def test_validator_wrapper_accepts_a_checkout_without_dossiers(self):
        result = self.run_script("validate_task_dossiers.py", "projects")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Validated 0 task dossier(s)", result.stdout)

    def test_scaffold_wrapper_defaults_to_a_dry_run(self):
        result = self.run_script(
            "scaffold_task_dossier.py",
            "TASK-002",
            "--level",
            "0",
            "--project",
            "example",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("planned 11 task-dossier artifact(s)", result.stdout)
        self.assertFalse(
            (self.projects / "example" / "handoffs" / "TASK-002").exists()
        )

    def test_scaffold_wrapper_rejects_an_unstable_task_id(self):
        result = self.run_script(
            "scaffold_task_dossier.py",
            "feature-branch",
            "--level",
            "0",
            "--project",
            "example",
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("branch-independent", result.stderr)

    # --- review remediation: finding 1, scaffold containment and symlinks ---

    def test_scaffold_rejects_a_project_slug_that_escapes_the_root(self):
        for slug in ("../escaped", "..", "Example", "a/b", "example/../.."):
            with self.subTest(slug=slug):
                with self.assertRaises(ValueError) as error:
                    dossier_path(self.projects, slug, "TASK-001")
                self.assertIn("lowercase hyphenated slug", str(error.exception))

    def test_scaffold_path_stays_inside_the_projects_root(self):
        resolved = dossier_path(self.projects, "example", "TASK-001")
        self.assertEqual(self.dossier.resolve(), resolved.resolve())

    def test_scaffold_wrapper_rejects_an_escaping_project_and_writes_nothing(self):
        outside = self.checkout / "escaped"
        outside.mkdir()
        result = self.run_script(
            "scaffold_task_dossier.py",
            "TASK-003",
            "--level",
            "0",
            "--project",
            "../escaped",
            "--apply",
        )
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("lowercase hyphenated slug", result.stderr)
        self.assertEqual([], sorted(outside.iterdir()))

    def test_scaffold_refuses_to_write_through_a_dangling_symlink(self):
        escape_target = self.checkout / "outside.md"
        (self.dossier / "design.md").symlink_to(escape_target)
        self.assertFalse(escape_target.exists())

        with self.assertRaises(ValueError) as error:
            plan_scaffold(
                self.dossier, "TASK-001", "1", "example", repository_root=ROOT
            )
        self.assertIn("symlinked artifact", str(error.exception))

        with self.assertRaises(ValueError):
            apply_scaffold(
                self.dossier, "TASK-001", "1", "example", repository_root=ROOT
            )
        self.assertFalse(escape_target.exists())
        # The rejection happens before any write, so no other artifact appears.
        self.assertEqual(["design.md"], sorted(p.name for p in self.dossier.iterdir()))

    def test_scaffold_refuses_to_write_through_a_resolving_symlink(self):
        escape_target = self.checkout / "outside.md"
        escape_target.write_text("original\n", encoding="utf-8")
        (self.dossier / "brief.md").symlink_to(escape_target)

        with self.assertRaises(ValueError):
            apply_scaffold(
                self.dossier, "TASK-001", "1", "example", repository_root=ROOT
            )
        self.assertEqual("original\n", escape_target.read_text(encoding="utf-8"))
        self.assertEqual(["brief.md"], sorted(p.name for p in self.dossier.iterdir()))

    def test_scaffold_rejects_a_symlinked_dossier_directory(self):
        linked = self.projects / "example" / "handoffs" / "TASK-004"
        linked.symlink_to(self.dossier, target_is_directory=True)
        with self.assertRaises(ValueError) as error:
            plan_scaffold(linked, "TASK-004", "0", "example", repository_root=ROOT)
        self.assertIn("must not be a symlink", str(error.exception))

    def test_scaffolded_index_links_the_canonical_authorities(self):
        apply_scaffold(self.dossier, "TASK-001", "1", "example", repository_root=ROOT)
        index = (self.dossier / "index.md").read_text(encoding="utf-8")
        self.assertIn(
            "- Canonical receipt path: `projects/example/handoffs/TASK-001/receipt.md`",
            index,
        )
        self.assertIn(
            "- Project memory path: `projects/example/current-state.md`", index
        )

    # --- second re-review: residual 2, write-after-plan race ---

    def _race(self, create):
        """Run the real renderer, but let a writer land between plan and write.

        ``_render`` is called only in the write loop, once per planned create,
        in ARTIFACTS order. Creating the collision on the first call reproduces
        a file appearing after planning but before its own write.
        """
        original = scaffold_module._render
        state = {"fired": False}

        def racing_render(*arguments, **keywords):
            if not state["fired"]:
                state["fired"] = True
                create()
            return original(*arguments, **keywords)

        return mock.patch.object(
            scaffold_module, "_render", side_effect=racing_render
        )

    def test_apply_never_overwrites_a_file_created_after_planning(self):
        target = self.dossier / "brief.md"

        def concurrent_writer():
            target.write_text("written by another writer\n", encoding="utf-8")

        with self._race(concurrent_writer):
            actions = apply_scaffold(
                self.dossier, "TASK-001", "1", "example", repository_root=ROOT
            )

        self.assertEqual(
            "written by another writer\n", target.read_text(encoding="utf-8")
        )
        collided = [action for action in actions if action.path == target]
        self.assertEqual(["preserve"], [action.action for action in collided])
        self.assertIn("appeared after planning", collided[0].reason)
        # Every other artifact is still scaffolded; the collision is contained.
        self.assertEqual(
            sorted(f"{name}.md" for name in ARTIFACTS),
            sorted(path.name for path in self.dossier.glob("*.md")),
        )

    def test_apply_never_follows_a_symlink_created_after_planning(self):
        escape_target = self.checkout / "outside.md"
        escape_target.write_text("original\n", encoding="utf-8")
        link = self.dossier / "brief.md"

        def concurrent_symlink():
            link.symlink_to(escape_target)

        with self._race(concurrent_symlink):
            with self.assertRaises(ValueError) as error:
                apply_scaffold(
                    self.dossier, "TASK-001", "1", "example", repository_root=ROOT
                )

        self.assertIn("symlinked artifact", str(error.exception))
        self.assertEqual("original\n", escape_target.read_text(encoding="utf-8"))
        self.assertTrue(link.is_symlink())

    def test_apply_is_idempotent_and_never_rewrites_its_own_output(self):
        apply_scaffold(self.dossier, "TASK-001", "1", "example", repository_root=ROOT)
        stamped = {
            path.name: path.read_text(encoding="utf-8")
            for path in self.dossier.glob("*.md")
        }
        actions = apply_scaffold(
            self.dossier, "TASK-001", "1", "example", repository_root=ROOT
        )
        self.assertEqual(
            [], [action for action in actions if action.action == "create"]
        )
        for name, text in stamped.items():
            self.assertEqual(
                text, (self.dossier / name).read_text(encoding="utf-8"), name
            )

    def test_repository_checkout_validates_clean(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_task_dossiers.py"), "projects"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)


# --------------------------------------------------------------------------
# Implementation-start capture map: build, preflight, delta.
#
# The literal block in the accepted design is the sole reviewed implementation
# of the capture contract. These tests extract that exact block and run it, so
# the tests and the procedure the implementer runs cannot drift apart.
# --------------------------------------------------------------------------

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import re
import shutil
import stat

DESIGN = ROOT / "projects/brida-task-dossier-workflow/handoffs/TDW-009/design.md"


def load_capture_module(directory):
    """Extract the one fenced python block that defines the capture map."""
    text = DESIGN.read_text(encoding="utf-8")
    blocks = re.findall(r"^```python\n(.*?)^```$", text, re.MULTILINE | re.DOTALL)
    sources = [block for block in blocks if "capture_map_version" in block]
    if len(sources) != 1:
        raise AssertionError(f"expected one capture block, found {len(sources)}")
    path = Path(directory) / "capture.py"
    path.write_text(sources[0], encoding="utf-8")
    spec = importlib.util.spec_from_file_location("tdw009_capture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaptureMapIntegrationTest(unittest.TestCase):
    """Fail-closed behaviour of the exact executable, on a fixture tree."""

    @classmethod
    def setUpClass(cls):
        cls.extraction_directory = tempfile.TemporaryDirectory()
        cls.capture = load_capture_module(cls.extraction_directory.name)

    @classmethod
    def tearDownClass(cls):
        cls.extraction_directory.cleanup()

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name) / "checkout"
        self.root.mkdir()
        self.manifest_path = self.root.parent / "capture-manifest.json"
        self.build_fixture_tree()
        self.pristine = self.build()
        self.write_manifest(self.pristine)

    # -- fixture ---------------------------------------------------------

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def build_fixture_tree(self):
        """Every accepted modified path present; every new path absent."""
        for index, relative in enumerate(self.capture.ALLOWLIST_MODIFIED):
            self.write(relative, f"fixture content {index}\n")
        # A pre-existing tracked file and a pre-existing untracked leaf that
        # are both outside the allowlist and must therefore never move.
        self.write("README.md", "outside the allowlist\n")
        self.write("notes/scratch.txt", "untracked leaf\n")
        # Excluded entries must stay invisible to the map.
        self.write(".git/config", "[core]\n")
        self.write("src/__pycache__/stale.pyc", "ignored\n")
        self.write(".DS_Store", "platform noise\n")
        self.write(".env", "SECRET=1\n")

        snapshot = self.root / self.capture.SNAPSHOT_DIR
        snapshot.mkdir(parents=True)
        for relative in self.capture.ALLOWLIST_MODIFIED:
            (snapshot / self.capture.snapshot_name(relative)).write_bytes(
                (self.root / relative).read_bytes()
            )

    def build(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = self.capture.main(["build", "--root", str(self.root)])
        self.assertEqual(0, code)
        return json.loads(stdout.getvalue())

    def write_manifest(self, manifest):
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def read_manifest(self):
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def fresh_manifest(self):
        """Each mutation starts from the pristine capture, never a mutated one."""
        self.write_manifest(self.pristine)
        return copy.deepcopy(self.pristine)

    def run_mode(self, mode):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.capture.main(
                [mode, "--root", str(self.root), "--manifest", str(self.manifest_path)]
            )
        return code, stdout.getvalue() + stderr.getvalue()

    def touch_all_authorized(self):
        for relative in self.capture.ALLOWLIST_ALL:
            path = self.root / relative
            if path.exists():
                path.write_text(
                    path.read_text(encoding="utf-8") + "implemented\n",
                    encoding="utf-8",
                )
            else:
                self.write(relative, "implemented\n")

    def assert_refused(self, mode, needle=None):
        code, output = self.run_mode(mode)
        self.assertEqual(1, code, output)
        if needle is not None:
            self.assertIn(needle, output)
        return output

    # -- canonical round trip --------------------------------------------

    def test_the_frozen_tuples_match_the_accepted_plan(self):
        self.assertEqual(8, len(self.capture.ALLOWLIST_MODIFIED))
        self.assertEqual(36, len(self.capture.ALLOWLIST_NEW))
        self.assertEqual(44, len(self.capture.ALLOWLIST_ALL))
        self.assertEqual(
            (), tuple(set(self.capture.ALLOWLIST_MODIFIED) & set(self.capture.ALLOWLIST_NEW))
        )
        # The union is derived from the constants, never from a manifest.
        self.assertEqual(
            self.capture.ALLOWLIST_ALL,
            tuple(sorted(set(self.capture.ALLOWLIST_MODIFIED) | set(self.capture.ALLOWLIST_NEW))),
        )

    def test_build_output_is_accepted_by_the_strict_loader_and_preflight(self):
        manifest = self.read_manifest()
        self.assertEqual(1, manifest["capture_map_version"])
        self.assertEqual(list(self.capture.ALLOWLIST_MODIFIED), manifest["allowlist_modified"])
        self.assertEqual(list(self.capture.ALLOWLIST_NEW), manifest["allowlist_new"])
        code, output = self.run_mode("preflight")
        self.assertEqual(0, code, output)
        self.assertIn("preflight OK", output)

    def test_excluded_entries_never_become_rows(self):
        rows = {row["path"] for row in self.read_manifest()["rows"]}
        for excluded in (
            ".git/config",
            "src/__pycache__/stale.pyc",
            ".DS_Store",
            ".env",
        ):
            with self.subTest(path=excluded):
                self.assertNotIn(excluded, rows)
        self.assertIn("README.md", rows)
        self.assertIn("notes/scratch.txt", rows)

    # -- set equality -----------------------------------------------------

    def test_touching_all_forty_four_passes_the_delta(self):
        self.touch_all_authorized()
        code, output = self.run_mode("delta")
        self.assertEqual(0, code, output)
        self.assertIn("touched set equals all 44 authorized paths", output)

    def test_touching_forty_three_fails_and_names_the_untouched_path(self):
        self.touch_all_authorized()
        skipped = self.capture.ALLOWLIST_NEW[0]
        (self.root / skipped).unlink()
        output = self.assert_refused("delta", "UNTOUCHED")
        self.assertIn(skipped, output)

    def test_touching_an_extra_path_fails_and_names_it(self):
        self.touch_all_authorized()
        self.write("unauthorized.md", "not mine\n")
        output = self.assert_refused("delta", "UNEXPECTED")
        self.assertIn("unauthorized.md", output)

    def test_a_removal_fails_the_delta(self):
        self.touch_all_authorized()
        (self.root / "README.md").unlink()
        self.assert_refused("delta", "REMOVED")

    def test_outside_allowlist_changes_fail_preflight_and_delta(self):
        for relative in ("README.md", "notes/scratch.txt"):
            with self.subTest(path=relative):
                original = (self.root / relative).read_text(encoding="utf-8")
                (self.root / relative).write_text("mutated\n", encoding="utf-8")
                self.assert_refused("preflight", "DRIFT")
                self.touch_all_authorized()
                output = self.assert_refused("delta", "UNEXPECTED")
                self.assertIn(relative, output)
                (self.root / relative).write_text(original, encoding="utf-8")
                for new in self.capture.ALLOWLIST_NEW:
                    if (self.root / new).exists():
                        (self.root / new).unlink()
                for modified in self.capture.ALLOWLIST_MODIFIED:
                    index = self.capture.ALLOWLIST_MODIFIED.index(modified)
                    (self.root / modified).write_text(
                        f"fixture content {index}\n", encoding="utf-8"
                    )

    # -- frozen allowlist equality ---------------------------------------

    def test_a_same_count_substitution_is_refused_with_the_path_named(self):
        cases = {
            "modified": ("allowlist_modified", 0, "forged/modified.py"),
            "new": ("allowlist_new", 0, "forged/new.py"),
        }
        for label, (key, index, replacement) in cases.items():
            with self.subTest(case=label):
                manifest = self.fresh_manifest()
                original = manifest[key][index]
                manifest[key][index] = replacement
                manifest[key].sort()
                self.write_manifest(manifest)
                output = self.assert_refused(
                    "preflight", "must equal the accepted plan's frozen set"
                )
                self.assertIn(replacement, output)
                self.assertIn(original, output)

    def test_substituting_in_both_lists_at_once_is_refused(self):
        manifest = self.fresh_manifest()
        manifest["allowlist_modified"][0] = "forged/one.py"
        manifest["allowlist_modified"].sort()
        manifest["allowlist_new"][0] = "forged/two.py"
        manifest["allowlist_new"].sort()
        self.write_manifest(manifest)
        self.assert_refused("preflight", "must equal the accepted plan's frozen set")

    def test_misclassifying_one_path_between_the_lists_is_refused(self):
        manifest = self.fresh_manifest()
        moved = manifest["allowlist_new"].pop(0)
        promoted = manifest["allowlist_modified"].pop(0)
        manifest["allowlist_modified"].append(moved)
        manifest["allowlist_modified"].sort()
        manifest["allowlist_new"].append(promoted)
        manifest["allowlist_new"].sort()
        self.write_manifest(manifest)
        self.assert_refused("preflight", "must equal the accepted plan's frozen set")

    def test_a_forged_full_forty_four_delta_is_refused(self):
        """The manifest's own 44 paths are all touched, and it still fails."""
        manifest = self.fresh_manifest()
        substitute = "forged/substitute.py"
        replaced = manifest["allowlist_modified"][0]
        manifest["allowlist_modified"][0] = substitute
        manifest["allowlist_modified"].sort()
        self.write_manifest(manifest)

        for relative in manifest["allowlist_modified"] + manifest["allowlist_new"]:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("forged touch\n", encoding="utf-8")
        output = self.assert_refused("delta")
        self.assertIn(substitute, output)

    # -- snapshot_dir containment ----------------------------------------

    def test_snapshot_dir_values_are_refused_before_any_filesystem_access(self):
        for label, value in (
            ("absolute", "/etc"),
            ("traversing", "../outside/snapshot"),
            ("embedded traversal", (
                "projects/brida-task-dossier-workflow/handoffs/TDW-009/../../snapshot"
            )),
            ("backslash", "projects\\snapshot"),
            ("non-excluded", "src/snapshot"),
            ("alternate", (
                "projects/brida-task-dossier-workflow/handoffs/TDW-009/capture/other"
            )),
        ):
            with self.subTest(case=label):
                manifest = self.fresh_manifest()
                manifest["snapshot_dir"] = value
                self.write_manifest(manifest)
                self.assert_refused("preflight", "snapshot_dir")

    def test_a_symlinked_snapshot_component_is_refused_by_the_descriptor_walk(self):
        decoy = self.root / "decoy"
        decoy.mkdir()
        snapshot = self.root / self.capture.SNAPSHOT_DIR
        for label, target in (
            ("final component", snapshot),
            ("intermediate ancestor", snapshot.parent),
        ):
            with self.subTest(case=label):
                moved = target.parent / f"{target.name}-real"
                target.rename(moved)
                target.symlink_to(decoy)
                self.assert_refused("preflight", "is not a ")
                target.unlink()
                moved.rename(target)
        code, output = self.run_mode("preflight")
        self.assertEqual(0, code, "restoring real directories restores a clean run")

    def test_snapshot_faults_are_refused(self):
        snapshot = self.root / self.capture.SNAPSHOT_DIR
        first = self.capture.snapshot_name(self.capture.ALLOWLIST_MODIFIED[0])

        stray = snapshot / "stray.bin"
        stray.write_text("stray\n", encoding="utf-8")
        self.assert_refused("preflight", "SNAPSHOTDIR")
        stray.unlink()

        original = (snapshot / first).read_bytes()
        (snapshot / first).write_bytes(b"corrupted\n")
        self.assert_refused("preflight", "does not match its capture row")
        (snapshot / first).write_bytes(original)

        (snapshot / first).unlink()
        self.assert_refused("preflight", "SNAPSHOT")
        (snapshot / first).write_bytes(original)

        target = self.root / "elsewhere.bin"
        target.write_bytes(original)
        (snapshot / first).unlink()
        (snapshot / first).symlink_to(target)
        self.assert_refused("preflight", "is a symlink")

    # -- manifest strictness ---------------------------------------------

    def test_structural_manifest_faults_are_refused(self):
        def mutate(name, change):
            manifest = self.fresh_manifest()
            change(manifest)
            self.write_manifest(manifest)
            with self.subTest(case=name):
                self.assert_refused("preflight")

        mutate("wrong version", lambda m: m.__setitem__("capture_map_version", 2))
        mutate(
            "altered exclusions",
            lambda m: m["exclusions"]["names"].append("extra"),
        )
        mutate("unknown top-level key", lambda m: m.__setitem__("extra", 1))
        mutate("missing top-level key", lambda m: m.pop("rows"))
        mutate("seven modified", lambda m: m["allowlist_modified"].pop())
        mutate("thirty-five new", lambda m: m["allowlist_new"].pop())
        mutate(
            "duplicate inside a list",
            lambda m: m["allowlist_modified"].__setitem__(
                1, m["allowlist_modified"][0]
            ),
        )
        mutate(
            "new path also present in rows",
            lambda m: m["rows"].append(
                {
                    "path": self.capture.ALLOWLIST_NEW[0],
                    "type": "f",
                    "length": 1,
                    "sha256": hashlib.sha256(b"x").hexdigest(),
                }
            ),
        )
        mutate("duplicate row path", lambda m: m["rows"].append(copy.deepcopy(m["rows"][0])))
        mutate("unsorted rows", lambda m: m["rows"].reverse())
        mutate("row missing a key", lambda m: m["rows"][0].pop("length"))
        mutate("row type outside f/l/o", lambda m: m["rows"][0].__setitem__("type", "x"))

    def test_a_duplicate_json_key_is_refused(self):
        text = self.manifest_path.read_text(encoding="utf-8")
        injected = text.replace(
            '"capture_map_version": 1,', '"capture_map_version": 1,\n  "capture_map_version": 1,', 1
        )
        self.manifest_path.write_text(injected, encoding="utf-8")
        self.assert_refused("preflight", "duplicate JSON key")

    def test_invalid_json_and_a_non_object_root_are_refused(self):
        self.manifest_path.write_text("{", encoding="utf-8")
        self.assert_refused("preflight", "not valid JSON")
        self.manifest_path.write_text("[]", encoding="utf-8")
        self.assert_refused("preflight", "must be a JSON object")

    # -- strict value rules ----------------------------------------------

    def test_strict_value_rules_are_enforced(self):
        cases = (
            ("boolean version", lambda m: m.__setitem__("capture_map_version", True)),
            ("float version", lambda m: m.__setitem__("capture_map_version", 1.0)),
            ("negative length", lambda m: m["rows"][0].__setitem__("length", -1)),
            ("boolean length", lambda m: m["rows"][0].__setitem__("length", True)),
            (
                "uppercase digest",
                lambda m: m["rows"][0].__setitem__(
                    "sha256", m["rows"][0]["sha256"].upper()
                ),
            ),
            (
                "short digest",
                lambda m: m["rows"][0].__setitem__(
                    "sha256", m["rows"][0]["sha256"][:63]
                ),
            ),
            (
                "non-hex digest",
                lambda m: m["rows"][0].__setitem__("sha256", "z" * 64),
            ),
        )
        for name, change in cases:
            with self.subTest(case=name):
                manifest = self.fresh_manifest()
                change(manifest)
                self.write_manifest(manifest)
                self.assert_refused("preflight")

    def test_a_non_file_row_must_record_the_zero_pair(self):
        fifo = self.root / "queue.fifo"
        os.mkfifo(fifo)
        self.pristine = self.build()
        self.write_manifest(self.pristine)
        rows = {row["path"]: row for row in self.read_manifest()["rows"]}
        self.assertEqual("o", rows["queue.fifo"]["type"])
        self.assertEqual(0, rows["queue.fifo"]["length"])
        self.assertEqual("0" * 64, rows["queue.fifo"]["sha256"])

        for name, change in (
            ("non-zero length", lambda row: row.__setitem__("length", 1)),
            (
                "non-zero digest",
                lambda row: row.__setitem__("sha256", hashlib.sha256(b"x").hexdigest()),
            ),
        ):
            with self.subTest(case=name):
                manifest = self.fresh_manifest()
                for row in manifest["rows"]:
                    if row["path"] == "queue.fifo":
                        change(row)
                self.write_manifest(manifest)
                self.assert_refused("preflight", "must record length 0")

    # -- symlink completeness ---------------------------------------------

    def test_a_symlink_to_a_directory_is_recorded_and_never_traversed(self):
        hidden = self.root / "hidden"
        hidden.mkdir()
        (hidden / "secret.txt").write_text("not traversed\n", encoding="utf-8")
        link = self.root / "link-to-directory"
        link.symlink_to(hidden)
        self.pristine = self.build()
        self.write_manifest(self.pristine)

        rows = {row["path"]: row for row in self.read_manifest()["rows"]}
        self.assertEqual("l", rows["link-to-directory"]["type"])
        self.assertNotIn("link-to-directory/secret.txt", rows)
        self.assertIn("hidden/secret.txt", rows)
        code, output = self.run_mode("preflight")
        self.assertEqual(0, code, output)

    def test_retargeting_or_replacing_a_directory_symlink_is_caught(self):
        hidden = self.root / "hidden"
        hidden.mkdir()
        (hidden / "secret.txt").write_text("not traversed\n", encoding="utf-8")
        other = self.root / "other"
        other.mkdir()
        link = self.root / "link-to-directory"
        link.symlink_to(hidden)
        self.pristine = self.build()
        self.write_manifest(self.pristine)

        with self.subTest(case="retarget"):
            link.unlink()
            link.symlink_to(other)
            self.assert_refused("preflight", "DRIFT")
            self.touch_all_authorized()
            self.assert_refused("delta")
            for new in self.capture.ALLOWLIST_NEW:
                if (self.root / new).exists():
                    (self.root / new).unlink()
            for index, modified in enumerate(self.capture.ALLOWLIST_MODIFIED):
                (self.root / modified).write_text(
                    f"fixture content {index}\n", encoding="utf-8"
                )
            link.unlink()
            link.symlink_to(hidden)
            code, _ = self.run_mode("preflight")
            self.assertEqual(0, code)

        with self.subTest(case="replaced by a real directory"):
            link.unlink()
            link.mkdir()
            self.assert_refused("preflight", "DRIFT")
            link.rmdir()
            link.symlink_to(hidden)

        with self.subTest(case="replaced by a regular file"):
            link.unlink()
            link.write_text("now a file\n", encoding="utf-8")
            self.assert_refused("preflight", "DRIFT")

    def test_a_symlink_inside_an_excluded_prefix_is_not_recorded(self):
        link = self.root / ".git" / "link"
        link.symlink_to(self.root / "README.md")
        self.write_manifest(self.build())  # excluded entries never reach rows
        rows = {row["path"] for row in self.read_manifest()["rows"]}
        self.assertNotIn(".git/link", rows)


class ConciseGeneratorWrapperIntegrationTest(unittest.TestCase):
    """The thin wrappers stay bootstrap shims over the importable modules."""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.checkout = Path(self.temporary_directory.name)
        self.projects = self.checkout / "projects"
        (self.projects / "synthetic-level0").mkdir(parents=True)
        (self.projects / "synthetic-level0" / "current-state.md").write_text(
            "# Current state\n", encoding="utf-8"
        )
        text = DESIGN.read_text(encoding="utf-8")
        block = re.findall(
            r"^```json\n(.*?)^```$", text, re.MULTILINE | re.DOTALL
        )[0]
        self.record = self.checkout / "record.json"
        self.record.write_text(block, encoding="utf-8")

    def run_script(self, script, *arguments):
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), *arguments],
            cwd=self.checkout,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def generate(self, *extra):
        return self.run_script(
            "generate_task_dossier.py",
            "SYNTH-010",
            "--level",
            "0",
            "--project",
            "synthetic-level0",
            "--record",
            str(self.record),
            "--projects-root",
            str(self.projects),
            *extra,
        )

    def test_the_wrappers_are_thin_bootstrap_shims(self):
        for script in ("generate_task_dossier.py", "summarize_task_dossier.py"):
            with self.subTest(script=script):
                source = (ROOT / "scripts" / script).read_text(encoding="utf-8")
                self.assertIn("sys.path.insert(0, str(SRC))", source)
                self.assertIn("raise SystemExit(main())", source)
                self.assertLess(len(source.splitlines()), 25)

    def test_dry_run_then_apply_then_summarize(self):
        dry = self.generate()
        self.assertEqual(0, dry.returncode, dry.stderr)
        self.assertIn("planned 11 task-dossier artifact(s)", dry.stdout)
        dossier = self.projects / "synthetic-level0" / "handoffs" / "SYNTH-010"
        self.assertFalse(dossier.exists())

        applied = self.generate("--apply")
        self.assertEqual(0, applied.returncode, applied.stderr)
        self.assertIn("wrote 11 task-dossier artifact(s)", applied.stdout)
        self.assertEqual(
            sorted(f"{name}.md" for name in ARTIFACTS),
            sorted(path.name for path in dossier.glob("*.md")),
        )

        (dossier / "receipt.md").write_text("# Handoff receipt\n", encoding="utf-8")
        validated = self.run_script(
            "validate_task_dossiers.py", str(self.projects), "--require-complete"
        )
        self.assertEqual(0, validated.returncode, validated.stderr)

        summarized = self.run_script("summarize_task_dossier.py", str(self.projects))
        self.assertEqual(0, summarized.returncode, summarized.stderr)
        self.assertIn("## Root verdict", summarized.stdout)

    def test_reapplying_preserves_every_artifact_and_exits_nonzero(self):
        self.generate("--apply")
        dossier = self.projects / "synthetic-level0" / "handoffs" / "SYNTH-010"
        stamped = {
            path.name: path.read_text(encoding="utf-8")
            for path in dossier.glob("*.md")
        }
        again = self.generate("--apply")
        self.assertEqual(1, again.returncode)
        self.assertIn("partial adoption", again.stderr)
        for name, text in stamped.items():
            self.assertEqual(
                text, (dossier / name).read_text(encoding="utf-8"), name
            )


if __name__ == "__main__":
    unittest.main()
