import os
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

from tests import opencode_surface  # noqa: E402  (adds src/ to sys.path)
from brichan.cli import opencode as oc  # noqa: E402


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
            "bin/brichan",
            "bin/brichan-codex",
            "bin/brichan-claude",
            "bin/brichan-opencode",
            "bin/brichan-opencode-exec",
            "bin/brichan-herdr-agent-start",
            "scripts/install-brichan",
            "CLAUDE.md",
            "docs/index.md",
            "docs/policy/identity.md",
            "docs/policy/operating-principles.md",
            "docs/policy/memory-policy.md",
            "docs/policy/model-catalog.md",
            "docs/policy/reviewer.md",
            "docs/history/setup-status.md",
            "docs/architecture/repository-layout.md",
            "src/brichan/contracts/receipts/validation.py",
            "src/brichan/orchestration/worker_launch.py",
            "src/brichan/orchestration/model_routing.py",
            "src/brichan/cli/provider_commands.py",
            "src/brichan/cli/opencode.py",
            "src/brichan/cli/runtime.py",
            "config/model-routing.json",
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
        for name in (
            "bin/brichan",
            "bin/brichan-codex",
            "bin/brichan-claude",
            "bin/brichan-opencode",
            "bin/brichan-opencode-exec",
            "scripts/install-brichan",
        ):
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
        launcher = ROOT / "bin/brichan-herdr-agent-start"
        self.assertTrue(os.access(launcher, os.X_OK))
        compile(
            launcher.read_text(encoding="utf-8"),
            str(launcher),
            "exec",
        )

    def test_launcher_disables_native_agents(self):
        providers = (
            ROOT / "src/brichan/cli/provider_commands.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"agents.enabled=false"', providers)
        self.assertIn('"multi_agent"', providers)
        self.assertIn('"multi_agent_v2"', providers)
        self.assertIn('("--disallowed-tools=Task",)', providers)
        self.assertNotIn("agents.enabled=true", providers)

    def test_runtime_dispatcher_supports_only_approved_runtimes(self):
        dispatcher = (ROOT / "src/brichan/cli/runtime.py").read_text(
            encoding="utf-8"
        )
        routing = (
            ROOT / "src/brichan/orchestration/model_routing.py"
        ).read_text(encoding="utf-8")
        self.assertIn('environment.get("BRICHAN_RUNTIME") or default_runtime', dispatcher)
        self.assertIn('{"codex", "claude", "opencode"}', routing)
        self.assertIn('{"codex", "claude"}', routing)
        self.assertIn("settings.default_runtime", dispatcher)
        self.assertIn('f"brichan-{runtime}"', dispatcher)
        self.assertIn("unsupported runtime", dispatcher)

    def test_opencode_adapter_states_its_fail_closed_boundary(self):
        adapter = (ROOT / "src/brichan/cli/opencode.py").read_text(encoding="utf-8")
        # The exact six-key guard environment, and nothing else.
        for key in (
            "OPENCODE_CONFIG_CONTENT",
            "OPENCODE_DISABLE_AUTOUPDATE",
            "OPENCODE_DISABLE_PROJECT_CONFIG",
            "OPENCODE_DISABLE_CLAUDE_CODE",
            "OPENCODE_TEST_HOME",
            "XDG_CONFIG_HOME",
        ):
            self.assertIn(key, adapter, key)
        # HOME and the data/state/cache roots are never repurposed, so the real
        # OpenCode credential file keeps resolving.
        self.assertNotIn('"HOME":', adapter)
        self.assertNotIn('"XDG_DATA_HOME":', adapter)
        self.assertIn('OPENCODE_VERSION = "1.18.12"', adapter)
        self.assertIn('LAUNCH_ARGV = ("opencode", "--pure", "--agent"', adapter)
        self.assertIn("--variant", adapter)

    def test_the_three_checkout_runtimes_have_matching_wrappers(self):
        dispatcher = (ROOT / "src/brichan/cli/runtime.py").read_text(encoding="utf-8")
        self.assertIn('{"codex", "claude", "opencode"}', dispatcher)
        for runtime in ("codex", "claude", "opencode"):
            wrapper = ROOT / "bin" / f"brichan-{runtime}"
            self.assertTrue(wrapper.is_file(), runtime)
            self.assertIn(f"brichan.cli.{runtime}", wrapper.read_text(encoding="utf-8"))

    def test_opencode_documentation_states_its_known_limitations(self):
        routing_guide = (ROOT / "docs/guides/model-routing.md").read_text(
            encoding="utf-8"
        )
        catalog = (ROOT / "docs/policy/model-catalog.md").read_text(encoding="utf-8")
        for needle in ("syntactic", "screen", "AGENTS.md"):
            self.assertIn(needle, routing_guide, needle)
        self.assertIn("opencode", catalog.lower())

    def test_claude_launcher_keeps_herdr_as_worker_control_plane(self):
        adapter = (ROOT / "src/brichan/cli/claude.py").read_text(encoding="utf-8")
        self.assertIn(
            'environment.get("BRICHAN_CLAUDE_COORDINATOR_MODEL") or None',
            adapter,
        )
        self.assertIn("claude_command", adapter)
        self.assertIn("os.chdir(repository_root())", adapter)

    def test_model_routing_manifest_has_only_model_selection_settings(self):
        import json

        manifest = json.loads(
            (ROOT / "config/model-routing.json").read_text(encoding="utf-8")
        )
        self.assertEqual(1, manifest["schema_version"])
        self.assertEqual(
            {"plan", "implement", "review", "scan"},
            set(manifest["routes"]),
        )
        serialized = json.dumps(manifest).lower()
        for forbidden in (
            "argv",
            "permission",
            "sandbox",
            "approval",
            "agents.enabled",
            "multi_agent",
        ):
            self.assertNotIn(forbidden, serialized)

        active_models = {
            defaults["model"]
            for defaults in manifest["coordinator"]["runtimes"].values()
        }
        active_models.update(
            route["model"] for route in manifest["routes"].values()
        )
        python_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "src").rglob("*.py")
        )
        runtime_instructions = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        for model in active_models:
            self.assertNotIn(model, python_source)
            self.assertNotIn(model, runtime_instructions)

    def test_claude_instructions_reference_canonical_policy(self):
        instructions = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("AGENTS.md", instructions)
        self.assertIn("docs/policy/identity.md", instructions)
        self.assertIn("docs/policy/operating-principles.md", instructions)
        self.assertIn("docs/policy/memory-policy.md", instructions)
        self.assertIn("Herdr", instructions)
        self.assertIn("brichan-", instructions)

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
        package = (ROOT / "src/brichan/__init__.py").read_text(encoding="utf-8")
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
                or ".venv" in path.parts
                or "venv" in path.parts
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
        # TDW-009 snapshots are authenticated byte-for-byte pre-task evidence,
        # not authored durable text.  Keep this exception exact so it cannot
        # become a general-purpose place to hide personal paths.
        opaque_capture_evidence = (
            ROOT
            / "projects"
            / "brida-task-dossier-workflow"
            / "handoffs"
            / "TDW-009"
            / "capture"
            / "snapshot"
        )
        offenders = []
        for directory in ("evals", "metrics", "projects"):
            for path in (ROOT / directory).rglob("*"):
                if not path.is_file() or "__pycache__" in path.parts:
                    continue
                if path.parent == opaque_capture_evidence:
                    continue
                content = path.read_text(encoding="utf-8")
                if "/Users/" in content or "/home/" in content:
                    offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders)


class OpencodePinnedSurfaceReceiptTest(unittest.TestCase):
    """The one always-on check that a version bump re-ran its derivations.

    ``EXECUTABLE_SCANS``, ``CONFIG_DISCOVERY_SOURCES``, and ``EXECUTION_KEYS``
    are derived from the pinned provider's own source.  Their drift tests are
    offline and compare against a hand-written transcript, so they agree with
    themselves after a bump and prove nothing about the new release; the checks
    that read a real extracted tree are opt-in and skip when
    ``BRICHAN_OPENCODE_PINNED_SOURCE`` is unset.  Before this test, editing
    ``OPENCODE_VERSION`` alone left the whole suite green.

    This runs in ``make check``, offline, with no network and no local tree: it
    compares a digest of the live tables against the receipt the pinned-source
    run wrote.  It is a forcing function, not a proof — the receipt can be
    hand-edited, and ``tests/opencode_surface.py`` says so at length.
    """

    def test_the_receipt_matches_the_current_derived_surface(self):
        recorded = opencode_surface.load_fixture()
        if recorded.get("surface_digest") != opencode_surface.surface_digest() or (
            recorded.get("opencode_version") != oc.OPENCODE_VERSION
        ):
            self.fail(opencode_surface.mismatch_message(recorded))

    def test_the_receipt_records_the_entry_counts_a_reader_can_check(self):
        """Cheap redundancy: a digest is opaque, a count is reviewable."""

        recorded = opencode_surface.load_fixture()
        self.assertEqual(
            {
                name: len(getattr(oc, name))
                for name in opencode_surface.DERIVED_TABLES
            },
            recorded["entry_counts"],
        )

    def test_the_receipt_states_that_hand_editing_defeats_it(self):
        """The honesty is part of the artifact, not only of the commit message."""

        recorded = opencode_surface.load_fixture()
        self.assertIn("Hand-editing", recorded["_comment"])

    def test_the_failure_message_names_the_command_to_run(self):
        message = opencode_surface.mismatch_message(
            {"opencode_version": "0.0.0", "surface_digest": "sha256:stale"}
        )
        self.assertIn("BRICHAN_OPENCODE_PINNED_SOURCE=", message)
        self.assertIn(f"tarball/v{oc.OPENCODE_VERSION}", message)
        self.assertIn("docs/guides/model-routing.md", message)
        self.assertIn("fix the derived table", message)
        # And it must not imply the receipt is a proof.
        self.assertIn("without verifying anything", message)


if __name__ == "__main__":
    unittest.main()
