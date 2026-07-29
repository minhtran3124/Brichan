import sys
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brida.contracts.receipts.discovery import discover_receipts
from brida.contracts.receipts.parser import parse_receipt
from brida.contracts.receipts.schema import (
    Diagnostic,
    RECEIPT_ROLES,
    REQUIRED_SECTIONS,
)
from brida.orchestration.layout import ResizeOp, SpawnPlan, plan_spawn
from brida.orchestration.model_routing import (
    ResolvedRoute,
    load_settings,
    resolve_route,
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
        result = self._fresh_python("import brida.cli.provider_commands")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_orchestration_import_does_not_load_cli_modules(self):
        result = self._fresh_python(
            "import brida.orchestration; import sys; "
            "assert not any(name == 'brida.cli' or name.startswith('brida.cli.') "
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

    def test_model_routing_api_is_provider_neutral(self):
        settings = load_settings(ROOT / "config/model-routing.json")
        route = resolve_route(settings, "implement")
        self.assertIsInstance(route, ResolvedRoute)
        self.assertTrue(route.model)


if __name__ == "__main__":
    unittest.main()
