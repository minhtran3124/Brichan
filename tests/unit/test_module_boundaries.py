import sys
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.contracts.receipts.discovery import discover_receipts
from brichan.contracts.receipts.parser import parse_receipt
from brichan.contracts.receipts.schema import (
    Diagnostic,
    RECEIPT_ROLES,
    REQUIRED_SECTIONS,
)
from brichan.orchestration.layout import ResizeOp, SpawnPlan, plan_spawn
from brichan.orchestration.model_routing import (
    ResolvedRoute,
    load_settings,
    resolve_route,
)
import brichan.techstacks as techstacks
from brichan.techstacks.model import (
    DIAGNOSTIC_REGISTRY,
    INPUT_ERROR_CODES,
    SNAPSHOT_ERROR_CODES,
    Snapshot,
)


class ModuleBoundaryTest(unittest.TestCase):
    def _fresh_python(self, code: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_provider_commands_import_first_in_fresh_interpreter(self):
        result = self._fresh_python("import brichan.cli.provider_commands")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_orchestration_import_does_not_load_cli_modules(self):
        result = self._fresh_python(
            "import brichan.orchestration; import sys; "
            "assert not any(name == 'brichan.cli' or name.startswith('brichan.cli.') "
            "for name in sys.modules)"
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_receipt_schema_api_is_available(self):
        self.assertIn("standalone", RECEIPT_ROLES)
        self.assertIn("Identity", REQUIRED_SECTIONS)
        self.assertTrue(callable(parse_receipt))
        self.assertTrue(hasattr(Diagnostic, "format"))

    def test_discovery_returns_only_canonical_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            projects = Path(temporary)
            canonical = projects / "project" / "handoffs" / "TASK-1" / "receipt.md"
            historical = projects / "project" / "notes" / "receipt.md"
            canonical.parent.mkdir(parents=True)
            historical.parent.mkdir(parents=True)
            canonical.write_text("# canonical\n", encoding="utf-8")
            historical.write_text("# historical\n", encoding="utf-8")
            self.assertEqual([canonical], discover_receipts(projects))

    def test_orchestration_layout_api_is_provider_neutral(self):
        self.assertTrue(callable(plan_spawn))
        self.assertEqual("pane", ResizeOp("pane", "right", 0.5).pane_id)
        self.assertEqual("pane", SpawnPlan("pane", "right").target_pane_id)

    def test_techstacks_import_does_not_load_cli_or_project_modules(self):
        result = self._fresh_python(
            "import brichan.techstacks; import brichan.techstacks.filesystem; import sys; "
            "assert not any(name == 'brichan.cli' or name.startswith('brichan.cli.') "
            "or name in ('brichan.lifecycle', 'brichan.project') "
            "or name == 'evals' or name.startswith('evals.') "
            "for name in sys.modules)"
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_no_source_file_names_the_evals_package(self):
        """Design section 10: the dependency runs one way, eval to production.

        The fresh-interpreter guard above proves no import happens on the one
        path it walks; this proves the text is absent everywhere, so a lazy or
        conditional import cannot hide behind a branch that guard misses.
        """

        offenders = []
        for path in sorted((ROOT / "src" / "brichan").rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            content = path.read_text(encoding="utf-8")
            if re.search(r"\bevals\b", content):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders)

    def test_importing_every_source_module_never_loads_the_evals_package(self):
        """Import the whole package, not one entrypoint, then look for it."""

        result = self._fresh_python(
            "import importlib, pkgutil, sys; import brichan; "
            "[importlib.import_module(info.name) for info in "
            "pkgutil.walk_packages(brichan.__path__, 'brichan.')]; "
            "assert not any(name == 'evals' or name.startswith('evals.') "
            "for name in sys.modules), sorted(sys.modules)"
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_the_eval_package_imports_the_production_resolver(self):
        """The eval imports production; the guard above forbids the reverse."""

        result = self._fresh_python(
            "import evals.techstack_context_v1.test_cases as cases; "
            "assert cases.SCHEMA_VERSION == 2; "
            "assert len(cases.CASE_IDS) == 12"
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_the_package_import_does_not_load_the_techstacks_cli_module(self):
        """Design sections 2 and 16 put two CLI-owned names on the package.

        They are resolved lazily, so importing a record still loads no command
        surface even though the names are exported.
        """

        result = self._fresh_python(
            "import brichan.techstacks; import sys; "
            "assert 'brichan.techstacks.cli' not in sys.modules; "
            "assert 'verify_snapshot' in brichan.techstacks.__all__; "
            "assert 'publish_snapshot' in brichan.techstacks.__all__"
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_the_two_cli_owned_public_names_resolve_to_the_cli_objects(self):
        from brichan.techstacks import cli, publish_snapshot, verify_snapshot

        self.assertIs(cli.verify_snapshot, verify_snapshot)
        self.assertIs(cli.publish_snapshot, publish_snapshot)

    def test_an_unknown_package_attribute_is_still_an_attribute_error(self):
        with self.assertRaises(AttributeError):
            techstacks.no_such_public_name

    def test_the_package_dir_lists_the_defaults_and_every_public_name(self):
        """``__dir__`` widens the default listing by ``__all__``, never narrows it."""

        listed = dir(techstacks)
        self.assertEqual(sorted(listed), listed)
        self.assertEqual(len(set(listed)), len(listed))
        for name in techstacks.__all__:
            self.assertIn(name, listed)
        for name in ("model", "resolver", "__name__", "__file__", "__path__", "__doc__", "__all__"):
            self.assertIn(name, listed)
        self.assertIn("verify_snapshot", listed)
        self.assertIn("publish_snapshot", listed)

    def test_the_techstack_error_hierarchy_is_closed_at_two_subclasses(self):
        """Design section 4: only the two registry classes subclass the base."""

        result = self._fresh_python(
            "import brichan.techstacks.cli as cli; from brichan.techstacks import model; "
            "assert [c.__name__ for c in model.TechstackError.__subclasses__()] == "
            "['TechstackInputError', 'TechstackSnapshotError'], "
            "model.TechstackError.__subclasses__(); "
            "assert not isinstance(cli.SnapshotOutputRefused(), model.TechstackError)"
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_techstack_model_api_is_available(self):
        self.assertEqual(23, len(INPUT_ERROR_CODES))
        self.assertEqual(11, len(SNAPSHOT_ERROR_CODES))
        self.assertEqual(58, len(DIAGNOSTIC_REGISTRY))
        self.assertTrue(hasattr(Snapshot, "build"))

    def test_model_routing_api_is_provider_neutral(self):
        settings = load_settings(ROOT / "config/model-routing.json")
        route = resolve_route(settings, "implement")
        self.assertIsInstance(route, ResolvedRoute)
        self.assertTrue(route.model)


if __name__ == "__main__":
    unittest.main()
