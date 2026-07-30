import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.orchestration.model_routing import (
    RoutingError,
    load_settings,
    parse_settings,
    resolve_coordinator,
    resolve_route,
)
from brichan.cli.provider_commands import (
    codex_command,
    claude_command,
    secure_legacy_command,
    worker_command,
)


MANIFEST = ROOT / "config/model-routing.json"


def manifest_payload():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


class ModelRoutingTest(unittest.TestCase):
    def test_manifest_resolves_all_required_routes(self):
        settings = parse_settings(manifest_payload())

        self.assertEqual(
            {"plan", "implement", "review", "scan"},
            set(settings.routes),
        )
        for name in settings.routes:
            route = resolve_route(settings, name)
            self.assertIn(route.runtime, {"codex", "claude"})
            self.assertTrue(route.model)
            self.assertIn(route.effort, {"low", "medium", "high", "xhigh", "max"})

    def test_coordinator_defaults_come_from_manifest(self):
        payload = manifest_payload()
        payload["coordinator"]["default_runtime"] = "claude"
        payload["coordinator"]["runtimes"]["claude"] = {
            "model": "test-claude",
            "effort": "low",
        }

        route = resolve_coordinator(parse_settings(payload))

        self.assertEqual(("claude", "test-claude", "low"), (
            route.runtime,
            route.model,
            route.effort,
        ))

    def test_cli_route_overrides_take_precedence(self):
        settings = parse_settings(manifest_payload())

        route = resolve_route(
            settings,
            "scan",
            runtime="claude",
            model="test-model",
            effort="max",
        )

        self.assertEqual(("claude", "test-model", "max"), (
            route.runtime,
            route.model,
            route.effort,
        ))

    def test_unknown_route_and_runtime_are_rejected(self):
        settings = parse_settings(manifest_payload())
        with self.assertRaisesRegex(RoutingError, "unknown route"):
            resolve_route(settings, "unknown")
        with self.assertRaisesRegex(RoutingError, "runtime override"):
            resolve_route(settings, "plan", runtime="unknown")
        implement_runtime = settings.routes["implement"].runtime
        opposite_runtime = "claude" if implement_runtime == "codex" else "codex"
        with self.assertRaisesRegex(RoutingError, "model override is required"):
            resolve_route(settings, "implement", runtime=opposite_runtime)

    def test_codex_ultra_and_unsupported_effort_are_rejected(self):
        settings = parse_settings(manifest_payload())
        with self.assertRaisesRegex(RoutingError, "automatic delegation"):
            resolve_route(
                settings,
                "implement",
                runtime="codex",
                model="test-codex",
                effort="ultra",
            )
        with self.assertRaisesRegex(RoutingError, "unsupported"):
            resolve_route(settings, "implement", effort="impossible")

    def test_arbitrary_argv_and_permission_settings_are_rejected(self):
        for key in ("argv", "permission_mode"):
            payload = manifest_payload()
            payload["routes"]["implement"][key] = ["--unsafe"]
            with self.subTest(key=key):
                with self.assertRaisesRegex(RoutingError, "unsupported keys"):
                    parse_settings(payload)

    def test_missing_route_and_malformed_json_are_rejected(self):
        payload = manifest_payload()
        del payload["routes"]["scan"]
        with self.assertRaisesRegex(RoutingError, "missing required keys: scan"):
            parse_settings(payload)

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "routing.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(RoutingError, "malformed JSON"):
                load_settings(path)
            path.write_text('{"schema_version": 1, "schema_version": 1}', encoding="utf-8")
            with self.assertRaisesRegex(RoutingError, "duplicate key"):
                load_settings(path)

        payload = manifest_payload()
        payload["schema_version"] = True
        with self.assertRaisesRegex(RoutingError, "schema_version"):
            parse_settings(payload)

    def test_settings_changes_change_generated_commands(self):
        original = manifest_payload()
        changed = deepcopy(original)
        changed["routes"]["plan"]["model"] = "changed-planner"
        changed["routes"]["implement"]["effort"] = "xhigh"

        original_settings = parse_settings(original)
        changed_settings = parse_settings(changed)
        original_plan = worker_command(resolve_route(original_settings, "plan"))
        changed_plan = worker_command(resolve_route(changed_settings, "plan"))
        original_implement = worker_command(
            resolve_route(original_settings, "implement")
        )
        changed_implement = worker_command(
            resolve_route(changed_settings, "implement")
        )

        self.assertNotEqual(original_plan, changed_plan)
        self.assertIn("changed-planner", changed_plan)
        self.assertNotEqual(original_implement, changed_implement)
        changed_route = resolve_route(changed_settings, "implement")
        if changed_route.runtime == "codex":
            self.assertIn("model_reasoning_effort=xhigh", changed_implement)
        else:
            self.assertIn("--effort", changed_implement)
            self.assertIn("xhigh", changed_implement)

    def test_worker_commands_disable_native_delegation(self):
        settings = parse_settings(manifest_payload())
        codex = worker_command(resolve_coordinator(settings, "codex"))
        claude = worker_command(resolve_coordinator(settings, "claude"))

        self.assertIn("agents.enabled=false", codex)
        self.assertEqual(2, codex.count("--disable"))
        self.assertIn("--disallowed-tools=Task", claude)
        self.assertIn("--permission-mode", claude)
        self.assertIn("--effort", claude)

    def test_legacy_commands_are_guarded_without_losing_arguments(self):
        codex = secure_legacy_command(["codex", "-m", "legacy-model", "--help"])
        claude = secure_legacy_command(
            ["claude", "--model", "legacy-model", "--verbose"]
        )

        self.assertEqual(["-m", "legacy-model", "--help"], codex[-3:])
        self.assertIn("agents.enabled=false", codex)
        self.assertLess(claude.index("--disallowed-tools=Task"), claude.index("--verbose"))
        self.assertIn("legacy-model", claude)
        self.assertIn("--disallowed-tools=Task", claude)

    def test_legacy_permission_bypass_and_arbitrary_config_are_rejected(self):
        cases = (
            ["codex", "--dangerously-bypass-approvals-and-sandbox"],
            ["codex", "-c", "sandbox_mode=danger-full-access"],
            ["claude", "--permission-mode", "bypassPermissions"],
            ["claude", "--settings", "{}"],
            ["claude", "--agents", "{}"],
        )
        for command in cases:
            with self.subTest(command=command):
                with self.assertRaises(RoutingError):
                    secure_legacy_command(command)

    def test_legacy_scope_and_hook_overrides_are_rejected(self):
        cases = (
            ["codex", "-p", "legacy-profile"],
            ["codex", "-plegacy-profile"],
            ["codex", "--profile=legacy-profile"],
            ["codex", "--add-dir", "/tmp/extra"],
            ["codex", "--add-dir=/tmp/extra"],
            ["claude", "--bare"],
            ["claude", "--tools", "Task,Bash"],
            ["claude", "--tools=Task,Bash"],
            ["claude", "--allowedTools", "Read"],
            ["claude", "--allowed-tools=Read"],
            ["claude", "--disallowedTools", "Task"],
            ["claude", "--disallowed-tools=Task"],
        )
        for command in cases:
            with self.subTest(command=command):
                with self.assertRaises(RoutingError):
                    secure_legacy_command(command)

    def test_attached_codex_options_are_normalized_before_guards(self):
        settings = parse_settings(manifest_payload())
        codex = resolve_coordinator(settings, "codex")
        forbidden = (
            ["-c", "agents.enabled=true"],
            ["-c=agents.enabled=true"],
            ["-cagents.enabled=true"],
            ["--config", "features.multi_agent=true"],
            ["--config=features.multi_agent=true"],
            ["-s", "danger-full-access"],
            ["-s=danger-full-access"],
            ["-sdanger-full-access"],
            ["--enable", "multi_agent"],
        )
        for arguments in forbidden:
            with self.subTest(arguments=arguments):
                with self.assertRaises(RoutingError):
                    codex_command(codex, arguments)

        for arguments in (
            ["-m", "override-model"],
            ["-m=override-model"],
            ["-moverride-model"],
        ):
            with self.subTest(arguments=arguments):
                command = codex_command(codex, arguments)
                self.assertNotIn(codex.model, command)

    def test_attached_legacy_codex_config_cannot_smuggle_settings(self):
        for arguments in (
            ["-carbitrary.setting=true"],
            ["--config=arbitrary.setting=true"],
            ["-c=sandbox_mode=danger-full-access"],
            ["-s=danger-full-access"],
        ):
            with self.subTest(arguments=arguments):
                with self.assertRaises(RoutingError):
                    secure_legacy_command(["codex", *arguments])

    def test_claude_attached_deny_flag_precedes_passthrough(self):
        settings = parse_settings(manifest_payload())
        route = resolve_coordinator(settings, "claude")
        command = claude_command(route, ["--", "coordinator prompt"])
        self.assertLess(command.index("--disallowed-tools=Task"), command.index("--"))

    def test_legacy_claude_attached_deny_flag_precedes_separator(self):
        command = secure_legacy_command(["claude", "--", "legacy prompt"])
        self.assertLess(command.index("--disallowed-tools=Task"), command.index("--"))

    def test_coordinator_command_builders_reject_permission_bypass(self):
        settings = parse_settings(manifest_payload())
        codex = resolve_coordinator(settings, "codex")
        claude = resolve_coordinator(settings, "claude")

        with self.assertRaisesRegex(RoutingError, "permission-bypass"):
            codex_command(
                codex,
                ["--dangerously-bypass-approvals-and-sandbox"],
            )
        with self.assertRaisesRegex(RoutingError, "bypassPermissions"):
            claude_command(
                claude,
                ["--permission-mode", "bypassPermissions"],
            )
        with self.assertRaisesRegex(RoutingError, "automatic delegation"):
            codex_command(
                codex,
                ["-c", "model_reasoning_effort=ultra"],
            )
        with self.assertRaisesRegex(RoutingError, "unsupported"):
            claude_command(
                claude,
                ["--effort", "impossible"],
            )


if __name__ == "__main__":
    unittest.main()
