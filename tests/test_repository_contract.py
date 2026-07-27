import os
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTest(unittest.TestCase):
    def test_required_repository_files_exist(self):
        required = (
            "README.md",
            "AGENTS.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CHANGELOG.md",
            "LICENSE",
            "VERSION",
            "bin/brida",
            "bin/brida-codex",
            "bin/brida-claude",
            "bin/brida-herdr-agent-start",
            "CLAUDE.md",
            ".codex/config.toml",
            "projects/_template/overview.md",
            "metrics/runs.jsonl",
        )
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual([], missing)

    def test_launcher_is_executable_and_valid_shell(self):
        for name in ("bin/brida", "bin/brida-codex", "bin/brida-claude"):
            launcher = ROOT / name
            self.assertTrue(os.access(launcher, os.X_OK))
            result = subprocess.run(
                ["sh", "-n", str(launcher)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual("", result.stderr)
            self.assertEqual(0, result.returncode)

    def test_balanced_herdr_launcher_is_executable_python(self):
        launcher = ROOT / "bin/brida-herdr-agent-start"
        self.assertTrue(os.access(launcher, os.X_OK))
        compile(
            launcher.read_text(encoding="utf-8"),
            str(launcher),
            "exec",
        )

    def test_launcher_disables_native_agents(self):
        launcher = (ROOT / "bin/brida-codex").read_text(encoding="utf-8")
        self.assertIn("-c agents.enabled=false", launcher)
        self.assertIn("--disable multi_agent", launcher)
        self.assertIn("--disable multi_agent_v2", launcher)
        self.assertNotIn("agents.enabled=true", launcher)

    def test_runtime_dispatcher_supports_only_approved_runtimes(self):
        launcher = (ROOT / "bin/brida").read_text(encoding="utf-8")
        self.assertIn('runtime=${BRIDA_RUNTIME:-codex}', launcher)
        self.assertIn('exec "$BRIDA_ROOT/bin/brida-codex"', launcher)
        self.assertIn('exec "$BRIDA_ROOT/bin/brida-claude"', launcher)
        self.assertIn("unsupported runtime", launcher)

    def test_claude_launcher_keeps_herdr_as_worker_control_plane(self):
        launcher = (ROOT / "bin/brida-claude").read_text(encoding="utf-8")
        self.assertIn("--disallowed-tools Task", launcher)
        self.assertIn("cd \"$BRIDA_ROOT\"", launcher)
        self.assertIn("coordinator_model=${BRIDA_CLAUDE_COORDINATOR_MODEL:-opus}", launcher)
        self.assertIn('--model "$coordinator_model"', launcher)

    def test_claude_instructions_reference_canonical_policy(self):
        instructions = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("AGENTS.md", instructions)
        self.assertIn("Herdr", instructions)
        self.assertIn("brida-", instructions)

    def test_project_config_disables_native_agents(self):
        config = (ROOT / ".codex/config.toml").read_text(encoding="utf-8")
        self.assertIn("[agents]", config)
        self.assertIn("enabled = false", config)
        self.assertIn("multi_agent = false", config)
        self.assertIn("multi_agent_v2 = false", config)

    def test_version_matches_changelog(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertIn(f"## [{version}]", changelog)

    def test_mit_license_is_declared(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(license_text.startswith("MIT License\n"))
        self.assertIn("Copyright (c) 2026 Minh Tran", license_text)
        self.assertIn("[MIT License](LICENSE)", readme)

    def test_legacy_brand_is_absent(self):
        legacy_brand = "mi" + "na"
        legacy_pattern = re.compile(
            rf"(?<![a-z]){legacy_brand}(?![a-z])",
            re.IGNORECASE,
        )
        offenders = []
        for path in ROOT.rglob("*"):
            if (
                not path.is_file()
                or ".git" in path.parts
                or "__pycache__" in path.parts
                or "internal-docs" in path.parts
                or "assets" in path.parts
                or path.name == ".DS_Store"
            ):
                continue
            content = path.read_text(encoding="utf-8")
            if legacy_pattern.search(content):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders)

    def test_durable_artifacts_do_not_embed_home_paths(self):
        offenders = []
        for directory in ("evals", "metrics", "projects"):
            for path in (ROOT / directory).rglob("*"):
                if not path.is_file() or "__pycache__" in path.parts:
                    continue
                content = path.read_text(encoding="utf-8")
                if "/Users/" in content or "/home/" in content:
                    offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
