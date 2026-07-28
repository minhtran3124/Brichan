import os
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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
            "pyproject.toml",
            "bin/brida",
            "bin/brida-codex",
            "bin/brida-claude",
            "bin/brida-herdr-agent-start",
            "CLAUDE.md",
            "docs/index.md",
            "docs/policy/identity.md",
            "docs/policy/operating-principles.md",
            "docs/policy/memory-policy.md",
            "docs/policy/model-catalog.md",
            "docs/policy/reviewer.md",
            "docs/history/setup-status.md",
            "docs/architecture/repository-layout.md",
            "src/brida/contracts/receipts/validation.py",
            "src/brida/orchestration/worker_launch.py",
            "src/brida/cli/runtime.py",
            ".codex/config.toml",
            ".agents/skills/herdr-orchestration/references/handoff-receipt.md",
            ".agents/skills/herdr-orchestration/references/task-packet.md",
            "projects/_template/overview.md",
            "metrics/runs.jsonl",
        )
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual([], missing)

    def test_handoff_receipt_template_contract(self):
        template = (
            ROOT
            / ".agents/skills/herdr-orchestration/references/handoff-receipt.md"
        ).read_text(encoding="utf-8")
        headings = (
            "Identity",
            "Plan version",
            "Sessions",
            "Scope",
            "Non-goals",
            "Acceptance criteria",
            "Verification",
            "Implementation evidence",
            "Review verdict",
            "Risks and open decisions",
            "Cleanup status",
        )
        positions = []
        for heading in headings:
            matches = list(
                re.finditer(rf"^## {re.escape(heading)}$", template, re.MULTILINE)
            )
            self.assertEqual(1, len(matches), heading)
            positions.append(matches[0].start())
        self.assertEqual(positions, sorted(positions))

        required_labels = (
            "Receipt schema version:",
            "Attempt origin:",
            "Attempt lifecycle state:",
            "Prior attempt state:",
            "Replacement evidence path:",
            "Task ID:",
            "Project:",
            "Handoff timestamp (UTC):",
            "Artifact or plan ID:",
            "Version:",
            "Status:",
            "In scope:",
            "Authorized paths:",
            "Excluded work:",
            "Criterion ID",
            "Evidence",
            "Result",
            "Changed artifacts:",
            "Diff evidence:",
            "Test evidence:",
            "Verdict:",
            "Findings:",
            "Risks:",
            "Open decisions:",
            "Brida-owned panes closed:",
            "Project memory updated:",
        )
        for label in required_labels:
            self.assertIn(label, template)

        for role in ("Planner", "Implementer", "Reviewer"):
            self.assertIn(f"| {role} |", template)

        code_spans = re.findall(r"`([^`\n]*)`", template)
        self.assertFalse(any("|" in span for span in code_spans))
        self.assertNotIn("/Users/", template)
        self.assertNotIn("/home/", template)

        skill = (ROOT / ".agents/skills/herdr-orchestration/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("references/handoff-receipt.md", skill)

    def test_task_packet_optional_plan_receipt_linkage(self):
        template = (
            ROOT
            / ".agents/skills/herdr-orchestration/references/task-packet.md"
        ).read_text(encoding="utf-8")
        required_labels = (
            "Upstream plan and receipt (optional):",
            "Accepted plan ID:",
            "Plan version:",
            "Plan status:",
            "Handoff receipt path:",
        )
        for label in required_labels:
            self.assertIn(label, template)
        self.assertIn("omit the block or use `null` for every value", template)
        self.assertIn("repo-relative", template)
        self.assertNotIn("/Users/", template)
        self.assertNotIn("/home/", template)

        code_spans = re.findall(r"`([^`\n]*)`", template)
        self.assertFalse(any("|" in span for span in code_spans))

        skill = (ROOT / ".agents/skills/herdr-orchestration/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("references/task-packet.md", skill)
        self.assertIn("omit the block or use `null` values", skill)

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
        adapter = (ROOT / "src/brida/cli/codex.py").read_text(encoding="utf-8")
        self.assertIn('"agents.enabled=false"', adapter)
        self.assertIn('"multi_agent"', adapter)
        self.assertIn('"multi_agent_v2"', adapter)
        self.assertNotIn("agents.enabled=true", adapter)

    def test_runtime_dispatcher_supports_only_approved_runtimes(self):
        dispatcher = (ROOT / "src/brida/cli/runtime.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('environment.get("BRIDA_RUNTIME") or "codex"', dispatcher)
        self.assertIn('{"codex", "claude"}', dispatcher)
        self.assertIn('f"brida-{runtime}"', dispatcher)
        self.assertIn("unsupported runtime", dispatcher)

    def test_claude_launcher_keeps_herdr_as_worker_control_plane(self):
        adapter = (ROOT / "src/brida/cli/claude.py").read_text(encoding="utf-8")
        self.assertIn(
            'environment.get("BRIDA_CLAUDE_COORDINATOR_MODEL") or "opus"',
            adapter,
        )
        self.assertIn('"--disallowed-tools"', adapter)
        self.assertIn('"Task"', adapter)
        self.assertIn("os.chdir(repository_root())", adapter)

    def test_claude_instructions_reference_canonical_policy(self):
        instructions = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("AGENTS.md", instructions)
        self.assertIn("docs/policy/identity.md", instructions)
        self.assertIn("docs/policy/operating-principles.md", instructions)
        self.assertIn("docs/policy/memory-policy.md", instructions)
        self.assertIn("Herdr", instructions)
        self.assertIn("brida-", instructions)

    def test_retired_root_policy_pointers_are_absent(self):
        canonical_paths = {
            "identity.md": "docs/policy/identity.md",
            "operating-principles.md": "docs/policy/operating-principles.md",
            "memory-policy.md": "docs/policy/memory-policy.md",
            "model-catalog.md": "docs/policy/model-catalog.md",
            "reviewer.md": "docs/policy/reviewer.md",
            "setup-status.md": "docs/history/setup-status.md",
        }
        for stub, canonical in canonical_paths.items():
            self.assertFalse((ROOT / stub).exists())
            self.assertTrue((ROOT / canonical).is_file())

    def test_project_config_disables_native_agents(self):
        config = (ROOT / ".codex/config.toml").read_text(encoding="utf-8")
        self.assertIn("[agents]", config)
        self.assertIn("enabled = false", config)
        self.assertIn("multi_agent = false", config)
        self.assertIn("multi_agent_v2 = false", config)

    def test_version_matches_changelog(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        package = (ROOT / "src/brida/__init__.py").read_text(encoding="utf-8")
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertIn(f"## [{version}]", changelog)
        self.assertIn(f'version = "{version}"', pyproject)
        self.assertIn(f'__version__ = "{version}"', package)

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
