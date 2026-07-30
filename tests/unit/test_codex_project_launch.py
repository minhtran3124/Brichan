import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.cli.codex import project_command
from brichan.lifecycle import initialize_project
from brichan.orchestration.model_routing import RoutingError
from brichan.project import project_paths


class CodexProjectLaunchTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "target"
        self.root.mkdir()
        (self.root / ".git").mkdir()
        self.paths = project_paths(explicit=self.root)
        initialize_project(self.paths, apply=True)

    def test_command_injects_owned_policy_skill_and_safety_guards(self):
        command = project_command(self.paths, ["--help"], {})

        self.assertEqual("codex", command[0])
        self.assertEqual(
            str(self.paths.project_root), command[command.index("-C") + 1]
        )
        self.assertIn("agents.enabled=false", command)
        self.assertIn("multi_agent", command)
        self.assertIn("multi_agent_v2", command)
        assignments = [
            command[index + 1]
            for index, item in enumerate(command[:-1])
            if item == "-c"
        ]
        developer = next(
            item for item in assignments if item.startswith("developer_instructions=")
        )
        instructions = json.loads(developer.split("=", 1)[1])
        self.assertIn("You are Brichan", instructions)
        self.assertIn(str(self.paths.project_root), instructions)
        skill = next(item for item in assignments if item.startswith("skills.config="))
        self.assertIn(str(self.paths.state_root / "skills/herdr-orchestration"), skill)
        self.assertEqual("--help", command[-1])

    def test_owned_config_namespaces_and_attached_forms_are_rejected(self):
        cases = (
            ["-c", "developer_instructions='replace'"],
            ["-cdeveloper_instructions.extra='replace'"],
            ["-c=developer_instructions[0]='replace'"],
            ["--config=skills.config=[]"],
            ["--config", "skills.config.0.enabled=false"],
            ["-cskills.config.0.enabled=false"],
            ["-c=skills.config[0].enabled=false"],
            ["--config=skills.config.0.path='/tmp/hostile'"],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(RoutingError, "owns"):
                    project_command(self.paths, arguments, {})

    def test_scope_profile_remote_and_permission_options_are_rejected(self):
        cases = (
            ["-C", "/tmp/elsewhere"],
            ["-C/tmp/elsewhere"],
            ["-C=/tmp/elsewhere"],
            ["--cd", "/tmp/elsewhere"],
            ["--cd=/tmp/elsewhere"],
            ["--add-dir", "/tmp/extra"],
            ["--add-dir=/tmp/extra"],
            ["-p", "hostile"],
            ["-phostile"],
            ["-p=hostile"],
            ["--profile", "hostile"],
            ["--profile=hostile"],
            ["-a", "never"],
            ["-anever"],
            ["-a=never"],
            ["--ask-for-approval", "never"],
            ["--ask-for-approval=never"],
            ["--remote", "ws://example.test"],
            ["--remote=ws://example.test"],
            ["--remote-auth-token-env", "TOKEN"],
            ["--remote-auth-token-env=TOKEN"],
            ["--oss"],
            ["--local-provider", "ollama"],
            ["cloud"],
            ["remote-control"],
            ["--dangerously-bypass-approvals-and-sandbox"],
            ["--dangerously-bypass-hook-trust"],
            ["--sandbox", "read-only"],
            ["--sandbox=workspace-write"],
            ["-sread-only"],
            ["-c", "agents.enabled=true"],
            ["--enable", "multi_agent"],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaises(RoutingError):
                    project_command(self.paths, arguments, {})

    def test_approval_permission_and_writable_root_config_are_rejected(self):
        cases = (
            ["-c", "approval_policy='never'"],
            ["-capproval_policy='never'"],
            ["-c=approval_policy='never'"],
            ["--config", "approval_policy.granular.rules=false"],
            ["--config=default_permissions=':danger-full-access'"],
            [
                "-c",
                "sandbox_workspace_write.writable_roots=['/tmp/elsewhere']",
            ],
            [
                "--config=sandbox_workspace_write.writable_roots.0='/tmp/elsewhere'"
            ],
            ["-c", "permissions.hostile.extends=':workspace'"],
            ["-c", "sandbox_mode='danger-full-access'"],
            ["-c", "model_provider='hostile'"],
            ["-c", "model_providers.hostile.base_url='https://example.test'"],
            ["-c", "shell_environment_policy.inherit='all'"],
            ["-c", "mcp_servers.hostile.url='https://example.test'"],
            ["-c", "model_instructions_file='/tmp/replace.md'"],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(RoutingError, "forbidden"):
                    project_command(self.paths, arguments, {})

    def test_explicit_safe_project_passthrough_remains_supported(self):
        command = project_command(
            self.paths,
            [
                "--model",
                "safe-model",
                "-cmodel_reasoning_effort=high",
                "--no-alt-screen",
                "work on the target",
            ],
            {},
        )
        self.assertIn("safe-model", command)
        self.assertIn("-cmodel_reasoning_effort=high", command)
        self.assertEqual("work on the target", command[-1])

        literal = project_command(
            self.paths,
            [
                "--",
                "--remote=ws://literal-prompt",
                "--config=skills.config.0.enabled=false",
                "--dangerously-bypass-approvals-and-sandbox",
                "--dangerously-bypass-hook-trust",
            ],
            {},
        )
        self.assertEqual(
            [
                "--",
                "--remote=ws://literal-prompt",
                "--config=skills.config.0.enabled=false",
                "--dangerously-bypass-approvals-and-sandbox",
                "--dangerously-bypass-hook-trust",
            ],
            literal[-5:],
        )


if __name__ == "__main__":
    unittest.main()
