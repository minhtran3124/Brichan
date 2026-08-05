"""Guard tests for the OpenCode adapter and its fail-closed launch shim.

No live provider is ever launched here.  Every test that needs provider output
supplies a fake runner, so the whole S3 preflight is exercised without an
`opencode` process, without touching the real OpenCode configuration, and
without reading real credentials.
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan import __version__
from brichan.cli import opencode as oc
from brichan.cli.provider_commands import (
    opencode_command,
    secure_legacy_command,
    worker_command,
)
from brichan.orchestration.model_routing import (
    ResolvedRoute,
    RoutingError,
    parse_settings,
    resolve_coordinator,
)


MODEL = "opencode-go/gpt-5.6-luna"
VARIANT = "medium"


def route(model: str = MODEL, effort: str = VARIANT) -> ResolvedRoute:
    return ResolvedRoute(runtime="opencode", model=model, effort=effort)


def final_config(agents_md: Path, **overrides) -> dict:
    """A merged `debug config` document that satisfies every allowlist clause."""

    agents = {name: {"disable": True, "options": {}} for name in oc.BUILTIN_PRIMARY_AGENTS}
    agents[oc.GUARD_AGENT] = {
        "mode": "primary",
        "model": MODEL,
        "variant": VARIANT,
        "options": {},
        "permission": {
            "task": "deny",
            "skill": {"*": "deny", "herdr-orchestration": "allow"},
        },
    }
    document = {
        "$schema": "https://opencode.ai/config.json",
        "mode": {},
        "plugin": [],
        "plugin_origins": ["herdr-agent-state"],
        "command": {},
        "username": "someone",
        "agent": agents,
        "default_agent": oc.GUARD_AGENT,
        "instructions": [str(agents_md)],
        "permission": {"task": "deny"},
        "share": "disabled",
        "autoupdate": False,
        "subagent_depth": 0,
    }
    document.update(overrides)
    return document


class FakeProvider:
    """Records every provider invocation and replays canned output."""

    def __init__(self, agents_md: Path, **overrides):
        self.agents_md = agents_md
        self.version = overrides.pop("version", oc.OPENCODE_VERSION)
        self.skills = overrides.pop(
            "skills", [{"name": "herdr-orchestration"}, {"name": "customize-opencode"}]
        )
        self.configs = overrides.pop("configs", None)
        self.overrides = overrides
        self.calls: list[list[str]] = []
        self.environments: list[dict] = []
        self._config_reads = 0

    def __call__(self, argv, environment):
        self.calls.append(list(argv))
        self.environments.append(dict(environment))
        if argv[1:] == ["--version"]:
            return oc.ProviderResult(0, f"{self.version}\n")
        if argv[1:] == ["--pure", "debug", "skill"]:
            return oc.ProviderResult(0, json.dumps(self.skills))
        if argv[1:] == ["--pure", "debug", "config"]:
            if self.configs is not None:
                document = self.configs[min(self._config_reads, len(self.configs) - 1)]
            else:
                document = final_config(self.agents_md, **self.overrides)
            self._config_reads += 1
            return oc.ProviderResult(0, json.dumps(document))
        raise AssertionError(f"unexpected provider invocation: {argv}")


class _WorktreeTestCase(unittest.TestCase):
    """A scratch worktree with an AGENTS.md, plus an owned scratch root."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.worktree = self.root / "worktree"
        (self.worktree / ".git").mkdir(parents=True)
        (self.worktree / "AGENTS.md").write_text("# policy\n", encoding="utf-8")
        self.agents_md = (self.worktree / "AGENTS.md").resolve()
        self.scratch = self.root / "scratch"
        self.scratch.mkdir()

    def run_preflight(self, provider=None, trace=None, inherited=None, cwd=None):
        return oc.preflight(
            model=MODEL,
            variant=VARIANT,
            cwd=self.worktree if cwd is None else cwd,
            scratch_root=self.scratch,
            inherited={"PATH": "/usr/bin", "HOME": "/real/home"}
            if inherited is None
            else inherited,
            runner=FakeProvider(self.agents_md) if provider is None else provider,
            trace=trace,
        )


class GuardConfigTest(unittest.TestCase):
    def test_guard_config_pins_model_and_variant_on_the_agent_only(self):
        config = oc.guard_config(MODEL, VARIANT, Path("/repo/AGENTS.md"))
        primary = config["agent"][oc.GUARD_AGENT]
        self.assertEqual(MODEL, primary["model"])
        self.assertEqual(VARIANT, primary["variant"])
        self.assertEqual("primary", primary["mode"])
        self.assertNotIn("variant", config)
        self.assertNotIn("model", config)

    def test_all_five_builtin_primaries_are_disabled(self):
        config = oc.guard_config(MODEL, VARIANT, Path("/repo/AGENTS.md"))
        self.assertEqual(
            {"build", "plan", "compaction", "summary", "title"},
            set(oc.BUILTIN_PRIMARY_AGENTS),
        )
        for name in oc.BUILTIN_PRIMARY_AGENTS:
            self.assertTrue(config["agent"][name]["disable"], name)
        self.assertEqual(oc.GUARD_AGENT, config["default_agent"])

    def test_skill_permission_is_the_ordered_deny_then_allow_pair(self):
        config = oc.guard_config(MODEL, VARIANT, Path("/repo/AGENTS.md"))
        skill = config["agent"][oc.GUARD_AGENT]["permission"]["skill"]
        self.assertEqual([("*", "deny"), ("herdr-orchestration", "allow")], list(skill.items()))

    def test_instruction_entry_must_be_absolute(self):
        with self.assertRaisesRegex(oc.GuardError, "absolute"):
            oc.guard_config(MODEL, VARIANT, Path("AGENTS.md"))

    def test_posture_fields_are_pinned(self):
        config = oc.guard_config(MODEL, VARIANT, Path("/repo/AGENTS.md"))
        self.assertEqual("disabled", config["share"])
        self.assertIs(False, config["autoupdate"])
        self.assertEqual(0, config["subagent_depth"])
        self.assertEqual("deny", config["permission"]["task"])


class GuardEnvironmentTest(unittest.TestCase):
    def test_every_inherited_opencode_key_is_removed_unseen(self):
        inherited = {
            "PATH": "/usr/bin",
            "OPENCODE_CONFIG_DIR": "/evil/dir",
            "OPENCODE_PURE": "0",
            "OPENCODE_CONFIG_CONTENT": '{"mcp":{"evil":{}}}',
            "OPENCODE_ANYTHING": "x",
        }
        scrubbed = oc.scrub_environment(inherited)
        self.assertEqual({"PATH": "/usr/bin"}, scrubbed)

    def test_exactly_six_guard_keys_are_set_and_home_is_untouched(self):
        inherited = {
            "PATH": "/usr/bin",
            "HOME": "/real/home",
            "XDG_DATA_HOME": "/real/data",
            "XDG_STATE_HOME": "/real/state",
            "XDG_CACHE_HOME": "/real/cache",
            "OPENCODE_CONFIG_DIR": "/evil",
        }
        environment = oc.guard_environment(
            oc.scrub_environment(inherited),
            model=MODEL,
            variant=VARIANT,
            agents_md=Path("/repo/AGENTS.md"),
            xdg_config_home=Path("/scratch/xdg"),
            test_home=Path("/scratch/home"),
        )
        set_keys = {
            key
            for key, value in environment.items()
            if inherited.get(key) != value
        }
        self.assertEqual(set(oc.GUARD_KEYS), set_keys)
        self.assertEqual(6, len(oc.GUARD_KEYS))
        self.assertNotIn("OPENCODE_CONFIG_DIR", environment)
        for key in ("HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME"):
            self.assertEqual(inherited[key], environment[key], key)
        self.assertEqual("/scratch/xdg", environment["XDG_CONFIG_HOME"])

    def test_claude_compatibility_and_project_config_are_disabled(self):
        environment = oc.guard_environment(
            {"PATH": "/usr/bin"},
            model=MODEL,
            variant=VARIANT,
            agents_md=Path("/repo/AGENTS.md"),
            xdg_config_home=Path("/scratch/xdg"),
            test_home=Path("/scratch/home"),
        )
        self.assertEqual("1", environment["OPENCODE_DISABLE_CLAUDE_CODE"])
        self.assertEqual("true", environment["OPENCODE_DISABLE_PROJECT_CONFIG"])
        self.assertEqual("1", environment["OPENCODE_DISABLE_AUTOUPDATE"])
        # Global OpenCode config, AGENTS, and skill roots resolve through the
        # isolated XDG and home-dot roots, not the real ones.
        self.assertEqual("/scratch/xdg", environment["XDG_CONFIG_HOME"])
        self.assertEqual("/scratch/home", environment["OPENCODE_TEST_HOME"])

    def test_only_the_six_guard_keys_carry_the_opencode_prefix(self):
        environment = oc.guard_environment(
            {"PATH": "/usr/bin"},
            model=MODEL,
            variant=VARIANT,
            agents_md=Path("/repo/AGENTS.md"),
            xdg_config_home=Path("/scratch/xdg"),
            test_home=Path("/scratch/home"),
        )
        opencode_keys = {key for key in environment if key.startswith("OPENCODE_")}
        self.assertEqual(
            {key for key in oc.GUARD_KEYS if key.startswith("OPENCODE_")},
            opencode_keys,
        )


class VersionGateTest(unittest.TestCase):
    def test_matching_version_passes(self):
        calls = []

        def runner(argv, environment):
            calls.append(list(argv))
            return oc.ProviderResult(0, f"{oc.OPENCODE_VERSION}\n")

        oc.check_version({}, runner)
        self.assertEqual([["opencode", "--version"]], calls)

    def test_wrong_version_refuses_without_printing_provider_output(self):
        def runner(argv, environment):
            return oc.ProviderResult(0, "1.19.0\n")

        with self.assertRaises(oc.GuardError) as caught:
            oc.check_version({}, runner)
        self.assertIn(oc.OPENCODE_VERSION, str(caught.exception))
        self.assertNotIn("1.19.0", str(caught.exception))

    def test_nonzero_and_timeout_refuse(self):
        with self.assertRaisesRegex(oc.GuardError, "nonzero exit"):
            oc.check_version({}, lambda argv, env: oc.ProviderResult(3, "boom"))
        with self.assertRaisesRegex(oc.GuardError, "timed out"):
            oc.check_version(
                {}, lambda argv, env: oc.ProviderResult(124, "", timed_out=True)
            )


class DiscoveryPreflightTest(_WorktreeTestCase):
    def roots(self):
        xdg = self.scratch / "xdg-config"
        home = self.scratch / "opencode-home"
        for directory in (xdg, home):
            directory.mkdir(parents=True, exist_ok=True)
        return xdg, home

    def preflight(self, environment=None):
        xdg, home = self.roots()
        return oc.discovery_preflight(
            cwd=self.worktree,
            worktree=self.worktree,
            xdg_config_home=xdg,
            test_home=home,
            environment={} if environment is None else environment,
        )

    def test_clean_roots_pass_and_all_four_are_resolved(self):
        roots = self.preflight()
        xdg, home = self.roots()
        self.assertIn(xdg / "opencode", roots)
        self.assertIn(home / ".opencode", roots)
        self.assertIn(self.worktree / ".opencode", roots)

    def test_a_set_config_dir_refuses(self):
        with self.assertRaisesRegex(oc.GuardError, "OPENCODE_CONFIG_DIR"):
            self.preflight({"OPENCODE_CONFIG_DIR": "/somewhere"})

    def test_tool_markers_refuse_in_every_root_singular_and_plural(self):
        xdg, home = self.roots()
        cases = {
            "project-singular": self.worktree / ".opencode" / "tool" / "evil.js",
            "project-plural": self.worktree / ".opencode" / "tools" / "evil.ts",
            "xdg-singular": xdg / "opencode" / "tool" / "evil.ts",
            "xdg-plural": xdg / "opencode" / "tools" / "evil.js",
            "home-dot-singular": home / ".opencode" / "tool" / "evil.js",
            "home-dot-plural": home / ".opencode" / "tools" / "evil.ts",
        }
        for label, marker in cases.items():
            with self.subTest(label=label):
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.write_text("export default {}\n", encoding="utf-8")
                try:
                    with self.assertRaisesRegex(oc.GuardError, "executable custom tool"):
                        self.preflight()
                finally:
                    marker.unlink()

    def test_a_symlinked_tool_file_refuses(self):
        payload = self.root / "payload.js"
        payload.write_text("export default {}\n", encoding="utf-8")
        marker = self.worktree / ".opencode" / "tool" / "linked.js"
        marker.parent.mkdir(parents=True)
        marker.symlink_to(payload)
        with self.assertRaisesRegex(oc.GuardError, "executable custom tool"):
            self.preflight()

    def test_a_symlink_inside_an_owned_root_refuses(self):
        xdg, _home = self.roots()
        (xdg / "opencode").mkdir()
        (xdg / "opencode" / "escape").symlink_to(self.root)
        with self.assertRaisesRegex(oc.GuardError, "symlink"):
            self.preflight()

    def test_plugin_markers_refuse_in_every_root_singular_and_plural(self):
        # Plan version 9, D8: live probe L4 proved `--pure` does not suppress a
        # project-local `.opencode/plugin/*.js` in a real TUI session, so this
        # scan — not the provider flag — is the control.  `{plugin,plugins}` is
        # the pattern `config/plugin.ts:21` itself globs.
        xdg, home = self.roots()
        cases = {
            "project-singular": self.worktree / ".opencode" / "plugin" / "evil.js",
            "project-plural": self.worktree / ".opencode" / "plugins" / "evil.ts",
            "xdg-singular": xdg / "opencode" / "plugin" / "evil.ts",
            "xdg-plural": xdg / "opencode" / "plugins" / "evil.js",
            "home-dot-singular": home / ".opencode" / "plugin" / "evil.js",
            "home-dot-plural": home / ".opencode" / "plugins" / "evil.ts",
        }
        for label, marker in cases.items():
            with self.subTest(label=label):
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.write_text("export default {}\n", encoding="utf-8")
                try:
                    with self.assertRaisesRegex(oc.GuardError, "executable plugin"):
                        self.preflight()
                finally:
                    marker.unlink()

    def test_a_symlinked_plugin_file_refuses(self):
        payload = self.root / "payload.js"
        payload.write_text("export default {}\n", encoding="utf-8")
        marker = self.worktree / ".opencode" / "plugin" / "linked.js"
        marker.parent.mkdir(parents=True)
        marker.symlink_to(payload)
        with self.assertRaisesRegex(oc.GuardError, "executable plugin"):
            self.preflight()

    def test_a_pristine_project_carrying_only_a_plugin_refuses(self):
        # The exact L4 reproduction: no node_modules, no package.json, no
        # opencode.json, no prior provider run — a bare plugin file only.
        marker = self.worktree / ".opencode" / "plugin" / "evil.js"
        marker.parent.mkdir(parents=True)
        marker.write_text("export default {}\n", encoding="utf-8")
        self.assertEqual(
            [".git", ".opencode", "AGENTS.md"],
            sorted(entry.name for entry in self.worktree.iterdir()),
        )
        with self.assertRaisesRegex(oc.GuardError, "executable plugin"):
            self.preflight()

    def test_the_plugin_diagnostic_names_only_the_discovered_path(self):
        marker = self.worktree / ".opencode" / "plugin" / "evil.js"
        marker.parent.mkdir(parents=True)
        marker.write_text("globalThis.SECRET_PAYLOAD = 1\n", encoding="utf-8")
        with self.assertRaises(oc.GuardError) as caught:
            self.preflight()
        message = str(caught.exception)
        self.assertEqual(
            f"executable plugin discovered in an OpenCode root: {marker}", message
        )
        self.assertNotIn("SECRET_PAYLOAD", message)

    def test_the_project_walk_stops_at_the_worktree(self):
        # A marker above the worktree stop bound is out of the walk and must not
        # be reported; the redundant walk mirrors OpenCode's own stop semantics.
        marker = self.root / ".opencode" / "tool" / "evil.js"
        marker.parent.mkdir(parents=True)
        marker.write_text("export default {}\n", encoding="utf-8")
        self.preflight()


class WorktreeBoundTest(_WorktreeTestCase):
    """D8's stop bound must be a real Git worktree, never a silent cwd fallback.

    ``packages/core/src/project.ts:110-112`` (v1.18.12) resolves the project
    directory to the *filesystem root* when no ``.git`` is found, and
    ``core/src/config.ts:178-183`` then walks every ancestor from
    ``location.directory`` up to it collecting ``.opencode`` directories.  A
    fallback to ``cwd`` on this side would leave that whole ancestor chain
    unscanned while the provider still imported from it.
    """

    def setUp(self):
        super().setUp()
        self.outside = self.root / "outside"
        self.outside.mkdir()
        self.assertFalse(
            any(
                (candidate / ".git").exists()
                for candidate in (self.outside, *self.outside.parents)
            ),
            "the system temporary root unexpectedly sits inside a Git worktree",
        )

    def test_a_cwd_outside_any_git_worktree_refuses(self):
        with self.assertRaisesRegex(oc.GuardError, "outside a Git worktree"):
            oc.worktree_root(self.outside)

    def test_a_linked_worktree_is_still_a_worktree(self):
        # A linked worktree carries a `.git` *file*; refusing on it would break a
        # legitimate checkout-oriented invocation.
        linked = self.root / "linked"
        linked.mkdir()
        (linked / ".git").write_text(
            "gitdir: /elsewhere/.git/worktrees/linked\n", encoding="utf-8"
        )
        self.assertEqual(linked, oc.worktree_root(linked))

    def test_a_plugin_marker_in_an_ancestor_above_cwd_cannot_escape_d8(self):
        # Everything the pre-refusal code needed to sail through preflight: a
        # non-git cwd with its own AGENTS.md, a provider that agrees with it, and
        # the hostile marker one directory *above* cwd rather than inside it.
        marker = self.outside / ".opencode" / "plugin" / "evil.js"
        marker.parent.mkdir(parents=True)
        marker.write_text("export default {}\n", encoding="utf-8")
        nested = self.outside / "project"
        nested.mkdir()
        (nested / "AGENTS.md").write_text("# policy\n", encoding="utf-8")
        provider = FakeProvider((nested / "AGENTS.md").resolve())
        with self.assertRaisesRegex(oc.GuardError, "outside a Git worktree"):
            oc.preflight(
                model=MODEL,
                variant=VARIANT,
                cwd=nested,
                scratch_root=self.scratch,
                inherited={"PATH": "/usr/bin", "HOME": "/real/home"},
                runner=provider,
            )
        # The bound is checked first, so nothing is spawned and nothing is written.
        self.assertEqual([], provider.calls)
        self.assertEqual([], sorted(self.scratch.iterdir()))


class TuiBackstopTest(_WorktreeTestCase):
    def test_backstop_is_written_byte_exactly_into_the_owned_root(self):
        xdg = self.scratch / "xdg-config"
        xdg.mkdir()
        target = oc.write_tui_backstop(xdg)
        self.assertEqual(xdg / "opencode" / "tui.json", target)
        self.assertEqual(
            '{"keybinds":{"agent_cycle":"none","agent_cycle_reverse":"none"}}',
            target.read_text(encoding="utf-8"),
        )

    def test_a_tampered_backstop_refuses(self):
        xdg = self.scratch / "xdg-config"
        xdg.mkdir()
        real_write = Path.write_text

        def tamper(self_path, *args, **kwargs):
            real_write(self_path, "{}", encoding="utf-8")

        with mock.patch.object(Path, "write_text", tamper):
            with self.assertRaisesRegex(oc.GuardError, "backstop"):
                oc.write_tui_backstop(xdg)


class MigrationScanTest(_WorktreeTestCase):
    def test_a_clean_tree_passes(self):
        oc.migration_scan(self.worktree)

    def test_each_migration_key_refuses_by_key_path(self):
        for name in ("opencode.json", "opencode.jsonc"):
            for key in oc.MIGRATION_KEYS:
                with self.subTest(name=name, key=key):
                    path = self.worktree / name
                    path.write_text(json.dumps({key: {}}), encoding="utf-8")
                    try:
                        with self.assertRaises(oc.GuardError) as caught:
                            oc.migration_scan(self.worktree)
                        self.assertIn(f"#{key}", str(caught.exception))
                    finally:
                        path.unlink()

    def test_a_benign_config_above_the_worktree_is_still_scanned(self):
        path = self.root / "opencode.json"
        path.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
        with self.assertRaisesRegex(oc.GuardError, "migration key"):
            oc.migration_scan(self.worktree)

    def test_comments_are_stripped_before_parsing_jsonc(self):
        path = self.worktree / "opencode.jsonc"
        path.write_text(
            '// leading\n{"tui": {} /* trailing */}\n', encoding="utf-8"
        )
        with self.assertRaisesRegex(oc.GuardError, "migration key"):
            oc.migration_scan(self.worktree)

    def test_unparseable_config_refuses(self):
        (self.worktree / "opencode.json").write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(oc.GuardError, "cannot be parsed"):
            oc.migration_scan(self.worktree)


class SkillPrecheckTest(unittest.TestCase):
    def payload(self, names):
        return lambda argv, env: oc.ProviderResult(
            0, json.dumps([{"name": name} for name in names])
        )

    def test_the_expected_discovery_set_passes(self):
        names = oc.skill_precheck({}, self.payload(["herdr-orchestration", "customize-opencode"]))
        self.assertIn("herdr-orchestration", names)

    def test_the_project_skill_alone_passes(self):
        oc.skill_precheck({}, self.payload(["herdr-orchestration"]))

    def test_any_other_discovered_skill_refuses_before_spawn(self):
        with self.assertRaisesRegex(oc.GuardError, "unexpected skill"):
            oc.skill_precheck(
                {},
                self.payload(
                    ["herdr-orchestration", "customize-opencode", "test-driven-development"]
                ),
            )

    def test_the_refusal_never_echoes_the_discovered_skill_name(self):
        """S3 groups this refusal under "captured provider output never reaches
        user output".  A skill name is a value in the provider's JSON array, not
        a config key path, so it must not be relayed."""

        leaked = "sk-secret-looking-skill-name"
        with self.assertRaises(oc.GuardError) as caught:
            oc.skill_precheck(
                {}, self.payload(["herdr-orchestration", leaked])
            )
        message = str(caught.exception)
        self.assertIn("unexpected skill", message)
        self.assertNotIn(leaked, message)
        # Nor any other provider-supplied name from the same payload.
        with self.assertRaises(oc.GuardError) as caught:
            oc.skill_precheck(
                {},
                self.payload(
                    [
                        "herdr-orchestration",
                        "customize-opencode",
                        "test-driven-development",
                        "mcp-agent-mail-verification",
                    ]
                ),
            )
        message = str(caught.exception)
        for name in ("test-driven-development", "mcp-agent-mail-verification"):
            self.assertNotIn(name, message)

    def test_a_missing_project_skill_refuses(self):
        with self.assertRaisesRegex(oc.GuardError, "required project skill"):
            oc.skill_precheck({}, self.payload(["customize-opencode"]))

    def test_invalid_json_nonzero_and_timeout_refuse(self):
        with self.assertRaisesRegex(oc.GuardError, "invalid JSON"):
            oc.skill_precheck({}, lambda argv, env: oc.ProviderResult(0, "not json"))
        with self.assertRaisesRegex(oc.GuardError, "nonzero exit"):
            oc.skill_precheck({}, lambda argv, env: oc.ProviderResult(1, "[]"))
        with self.assertRaisesRegex(oc.GuardError, "timed out"):
            oc.skill_precheck(
                {}, lambda argv, env: oc.ProviderResult(124, "", timed_out=True)
            )


class FinalConfigAllowlistTest(_WorktreeTestCase):
    def check(self, document):
        oc.check_final_config(
            document, model=MODEL, variant=VARIANT, agents_md=self.agents_md
        )

    def test_the_guarded_document_passes(self):
        self.check(final_config(self.agents_md))

    def test_every_disallowed_top_level_key_refuses(self):
        for key in ("mcp", "tools", "experimental", "keybinds", "future_field"):
            with self.subTest(key=key):
                document = final_config(self.agents_md)
                document[key] = {"anything": True}
                with self.assertRaises(oc.GuardError) as caught:
                    self.check(document)
                self.assertIn(key, str(caught.exception))
                self.assertNotIn("anything", str(caught.exception))

    def test_local_and_remote_mcp_markers_both_refuse(self):
        cases = {
            "local": {"evil": {"type": "local", "command": ["/bin/echo", "hi"]}},
            "remote": {"evil": {"type": "remote", "url": "https://example.invalid"}},
            "mixed": {
                "a": {"type": "local", "command": ["/bin/echo"]},
                "b": {"type": "remote", "url": "https://example.invalid"},
            },
        }
        for label, mcp in cases.items():
            with self.subTest(label=label):
                document = final_config(self.agents_md)
                document["mcp"] = mcp
                with self.assertRaises(oc.GuardError) as caught:
                    self.check(document)
                self.assertIn("mcp", str(caught.exception))
                self.assertNotIn("example.invalid", str(caught.exception))
                self.assertNotIn("/bin/echo", str(caught.exception))

    def test_skills_and_remote_config_fields_refuse(self):
        for key, value in (
            ("skills", {"anything": True}),
            ("skill", {"anything": True}),
            ("remote", {"url": "https://example.invalid"}),
            ("well_known", {"url": "https://example.invalid"}),
            ("managed", {"policy": "x"}),
            ("provider", {"anthropic": {}}),
            ("model", "someone-elses-model"),
            ("variant", "max"),
        ):
            with self.subTest(key=key):
                document = final_config(self.agents_md)
                document[key] = value
                with self.assertRaises(oc.GuardError) as caught:
                    self.check(document)
                self.assertIn(key, str(caught.exception))

    def test_instruction_shape_is_enforced_exactly(self):
        cases = {
            "extra": [str(self.agents_md), "/other/AGENTS.md"],
            "relative": ["AGENTS.md"],
            "home": ["~/AGENTS.md"],
            "url": ["https://example.invalid/AGENTS.md"],
            "empty": [],
            "wrong-absolute": ["/elsewhere/AGENTS.md"],
        }
        for label, value in cases.items():
            with self.subTest(label=label):
                document = final_config(self.agents_md, instructions=value)
                with self.assertRaises(oc.GuardError) as caught:
                    self.check(document)
                self.assertIn("instructions", str(caught.exception))

    def test_command_and_mcp_must_be_empty(self):
        with self.assertRaisesRegex(oc.GuardError, "command"):
            self.check(final_config(self.agents_md, command={"evil": {}}))
        document = final_config(self.agents_md)
        document["mcp"] = {}
        with self.assertRaisesRegex(oc.GuardError, "mcp"):
            # An empty object is tolerated only if the schema forces the key;
            # the top-level allowlist rejects it first either way.
            self.check(document)

    def test_posture_values_are_gated(self):
        for key, value in (
            ("share", "enabled"),
            ("autoupdate", True),
            ("subagent_depth", 1),
        ):
            with self.subTest(key=key):
                with self.assertRaises(oc.GuardError) as caught:
                    self.check(final_config(self.agents_md, **{key: value}))
                self.assertIn(key, str(caught.exception))

    def test_permission_widening_refuses(self):
        cases = {
            "external-allow": {"task": "deny", "external_directory": "allow"},
            "external-ask": {"task": "deny", "external_directory": "ask"},
            "task-allow": {"task": "allow"},
            "unknown-grant": {"task": "deny", "bash": "allow"},
        }
        for label, permission in cases.items():
            with self.subTest(label=label):
                with self.assertRaises(oc.GuardError) as caught:
                    self.check(final_config(self.agents_md, permission=permission))
                self.assertIn("permission", str(caught.exception))

    def test_an_extra_agent_or_extra_primary_refuses(self):
        document = final_config(self.agents_md)
        document["agent"]["evil-primary"] = {"mode": "primary", "options": {}}
        with self.assertRaisesRegex(oc.GuardError, "unexpected agent"):
            self.check(document)

        document = final_config(self.agents_md)
        document["agent"]["plan"] = {"mode": "primary", "options": {}}
        with self.assertRaises(oc.GuardError):
            self.check(document)

    def test_unknown_agent_options_and_keys_refuse(self):
        document = final_config(self.agents_md)
        document["agent"][oc.GUARD_AGENT]["options"] = {"temperature": 1}
        with self.assertRaisesRegex(oc.GuardError, "options"):
            self.check(document)

        document = final_config(self.agents_md)
        document["agent"][oc.GUARD_AGENT]["tools"] = {"skill": True}
        with self.assertRaisesRegex(oc.GuardError, "unexpected agent keys"):
            self.check(document)

        document = final_config(self.agents_md)
        document["agent"]["build"]["options"] = {"reasoning": "high"}
        with self.assertRaisesRegex(oc.GuardError, "options"):
            self.check(document)

    def test_wrong_model_or_variant_refuses(self):
        document = final_config(self.agents_md)
        document["agent"][oc.GUARD_AGENT]["model"] = "someone-elses-model"
        with self.assertRaises(oc.GuardError) as caught:
            self.check(document)
        self.assertIn("model", str(caught.exception))
        self.assertNotIn("someone-elses-model", str(caught.exception))

        document = final_config(self.agents_md)
        document["agent"][oc.GUARD_AGENT]["variant"] = "max"
        with self.assertRaisesRegex(oc.GuardError, "variant"):
            self.check(document)

    def test_additional_or_reordered_skill_grants_refuse(self):
        cases = {
            "extra-grant": {"*": "deny", "herdr-orchestration": "allow", "other": "allow"},
            "reordered": {"herdr-orchestration": "allow", "*": "deny"},
            "wildcard-allow": {"*": "allow", "herdr-orchestration": "allow"},
        }
        for label, skill in cases.items():
            with self.subTest(label=label):
                document = final_config(self.agents_md)
                document["agent"][oc.GUARD_AGENT]["permission"]["skill"] = skill
                with self.assertRaisesRegex(oc.GuardError, "skill"):
                    self.check(document)

    def test_an_ordered_rule_list_is_accepted_as_the_same_semantics(self):
        document = final_config(self.agents_md)
        document["agent"][oc.GUARD_AGENT]["permission"]["skill"] = [
            {"pattern": "*", "action": "deny"},
            {"pattern": "herdr-orchestration", "action": "allow"},
        ]
        self.check(document)

    def test_a_disabled_builtin_that_is_not_disabled_refuses(self):
        document = final_config(self.agents_md)
        document["agent"]["title"] = {"mode": "primary", "options": {}}
        with self.assertRaisesRegex(oc.GuardError, "agent.title"):
            self.check(document)

    def test_default_agent_and_task_denial_are_gated(self):
        with self.assertRaisesRegex(oc.GuardError, "default_agent"):
            self.check(final_config(self.agents_md, default_agent="build"))
        document = final_config(self.agents_md)
        document["agent"][oc.GUARD_AGENT]["permission"]["task"] = "allow"
        with self.assertRaisesRegex(oc.GuardError, "permission.task"):
            self.check(document)

    def test_benign_provider_fields_are_never_value_gated(self):
        document = final_config(
            self.agents_md,
            username="anyone",
            plugin=["a", "b"],
            plugin_origins=["npm:whatever"],
            mode={"anything": {}},
        )
        document["$schema"] = "https://example.invalid/other.json"
        self.check(document)


class PreflightOrderingTest(_WorktreeTestCase):
    def test_the_s3_sequence_executes_exactly_as_listed(self):
        trace: list[str] = []
        launch, environment = self.run_preflight(trace=trace)
        self.assertEqual(list(oc.STEP_SEQUENCE), trace)
        self.assertEqual(
            ["agents-md", "scrub", "guard-environment", "version-gate",
             "isolated-dirs", "discovery-preflight", "tui-backstop",
             "migration-scan", "skill-precheck",
             "final-config-run-1", "final-config-run-2"],
            trace,
        )
        self.assertEqual(list(oc.LAUNCH_ARGV), launch)
        self.assertEqual(["opencode", "--pure", "--agent", "brichan-primary"], launch)

    def test_both_final_config_runs_happen_and_the_version_gate_is_first(self):
        provider = FakeProvider(self.agents_md)
        self.run_preflight(provider=provider)
        self.assertEqual(["opencode", "--version"], provider.calls[0])
        config_calls = [
            call for call in provider.calls if call[1:] == ["--pure", "debug", "config"]
        ]
        self.assertEqual(2, len(config_calls))
        skill_index = provider.calls.index(["opencode", "--pure", "debug", "skill"])
        first_config = provider.calls.index(["opencode", "--pure", "debug", "config"])
        self.assertLess(skill_index, first_config)

    def test_run_two_refuses_when_the_second_read_differs(self):
        drifted = final_config(self.agents_md)
        drifted["username"] = "someone-else"
        provider = FakeProvider(
            self.agents_md, configs=[final_config(self.agents_md), drifted]
        )
        with self.assertRaisesRegex(oc.GuardError, "changed between the two"):
            self.run_preflight(provider=provider)

    def test_run_two_refuses_when_a_later_merge_widens_the_document(self):
        widened = final_config(self.agents_md)
        widened["mcp"] = {"evil": {"type": "local"}}
        provider = FakeProvider(
            self.agents_md, configs=[final_config(self.agents_md), widened]
        )
        with self.assertRaisesRegex(oc.GuardError, "mcp"):
            self.run_preflight(provider=provider)

    def test_a_missing_agents_md_refuses_before_any_provider_call(self):
        (self.worktree / "AGENTS.md").unlink()
        provider = FakeProvider(self.agents_md)
        with self.assertRaisesRegex(oc.GuardError, "instructions are missing"):
            self.run_preflight(provider=provider)
        self.assertEqual([], provider.calls)

    def test_the_launch_environment_is_the_guard_environment(self):
        _launch, environment = self.run_preflight()
        self.assertEqual(
            {key for key in environment if key.startswith("OPENCODE_")},
            {key for key in oc.GUARD_KEYS if key.startswith("OPENCODE_")},
        )
        self.assertEqual(str(self.scratch / "xdg-config"), environment["XDG_CONFIG_HOME"])
        self.assertEqual("/real/home", environment["HOME"])
        pinned = json.loads(environment["OPENCODE_CONFIG_CONTENT"])
        self.assertEqual(MODEL, pinned["agent"][oc.GUARD_AGENT]["model"])
        self.assertEqual([str(self.agents_md)], pinned["instructions"])

    def test_a_discovered_tool_marker_refuses_before_the_config_reads(self):
        marker = self.worktree / ".opencode" / "tool" / "evil.js"
        marker.parent.mkdir(parents=True)
        marker.write_text("export default {}\n", encoding="utf-8")
        provider = FakeProvider(self.agents_md)
        with self.assertRaisesRegex(oc.GuardError, "executable custom tool"):
            self.run_preflight(provider=provider)
        self.assertEqual([["opencode", "--version"]], provider.calls)

    def test_a_discovered_plugin_marker_refuses_before_the_config_reads(self):
        marker = self.worktree / ".opencode" / "plugin" / "evil.js"
        marker.parent.mkdir(parents=True)
        marker.write_text("export default {}\n", encoding="utf-8")
        provider = FakeProvider(self.agents_md)
        with self.assertRaisesRegex(oc.GuardError, "executable plugin"):
            self.run_preflight(provider=provider)
        # Only the D6 version gate ran, and `--version` cannot load a plugin:
        # it exits inside yargs before any middleware or handler, so no config
        # merge, no `ConfigPlugin.load`, and no `PluginLoader` are reached.
        self.assertEqual([["opencode", "--version"]], provider.calls)

    def test_a_migration_key_refuses_before_the_skill_precheck(self):
        (self.worktree / "opencode.json").write_text(
            json.dumps({"keybinds": {}}), encoding="utf-8"
        )
        provider = FakeProvider(self.agents_md)
        with self.assertRaisesRegex(oc.GuardError, "migration key"):
            self.run_preflight(provider=provider)
        self.assertNotIn(["opencode", "--pure", "debug", "skill"], provider.calls)

    def test_the_wrong_provider_version_refuses_before_any_isolated_write(self):
        provider = FakeProvider(self.agents_md, version="1.19.0")
        with self.assertRaisesRegex(oc.GuardError, oc.OPENCODE_VERSION):
            self.run_preflight(provider=provider)
        self.assertFalse((self.scratch / "xdg-config").exists())


class VersionGateSideEffect(FakeProvider):
    """A fake whose version gate writes where the real 1.18.12 binary writes.

    `opencode --version` creates `$XDG_CONFIG_HOME/opencode/` as a filesystem
    side effect before printing.  Every other fake in this file is side-effect
    free, which is exactly why the whole suite passed while the real binary
    crashed the shim: S3 runs the D6 version gate under the guard environment
    *before* D7 creates the isolated roots, so the provider gets there first.
    """

    def __init__(self, agents_md, *, side_effect=None, **overrides):
        super().__init__(agents_md, **overrides)
        self._side_effect = side_effect

    def __call__(self, argv, environment):
        if argv[1:] == ["--version"]:
            created = Path(environment["XDG_CONFIG_HOME"]) / "opencode"
            created.mkdir(parents=True, exist_ok=True)
            if self._side_effect is not None:
                self._side_effect(created)
        return super().__call__(argv, environment)


class IsolatedRootSideEffectTest(_WorktreeTestCase):
    """D7 against a provider that materializes the root before Brichan does."""

    def test_the_version_gate_side_effect_does_not_break_the_launch(self):
        trace = []
        launch, _environment = self.run_preflight(
            provider=VersionGateSideEffect(self.agents_md), trace=trace
        )
        self.assertEqual(list(oc.LAUNCH_ARGV), launch)
        self.assertEqual(list(oc.STEP_SEQUENCE), trace)

    def test_preflight_hands_discovery_two_provably_empty_roots(self):
        """The D7 guarantee is *fresh and empty*, not merely *present*."""

        observed = {}
        real = oc.discovery_preflight

        def spy(**kwargs):
            observed["xdg"] = sorted(p.name for p in kwargs["xdg_config_home"].iterdir())
            observed["home"] = sorted(p.name for p in kwargs["test_home"].iterdir())
            return real(**kwargs)

        with mock.patch.object(oc, "discovery_preflight", side_effect=spy):
            self.run_preflight(provider=VersionGateSideEffect(self.agents_md))
        self.assertEqual({"xdg": [], "home": []}, observed)

    def test_a_pre_existing_empty_root_is_reset_rather_than_accepted(self):
        (self.scratch / "xdg-config" / "opencode").mkdir(parents=True)
        xdg, home = oc.create_isolated_dirs(self.scratch)
        self.assertEqual([], list(xdg.iterdir()))
        self.assertEqual([], list(home.iterdir()))

    def test_a_file_left_in_an_isolated_root_refuses(self):
        provider = VersionGateSideEffect(
            self.agents_md,
            side_effect=lambda root: (root / "tui.json").write_text("{}", encoding="utf-8"),
        )
        with self.assertRaisesRegex(oc.GuardError, "provider state"):
            self.run_preflight(provider=provider)

    def test_a_symlink_left_in_an_isolated_root_refuses(self):
        outside = self.root / "outside"
        outside.mkdir()

        def link(root: Path) -> None:
            (root / "escape").symlink_to(outside)

        provider = VersionGateSideEffect(self.agents_md, side_effect=link)
        with self.assertRaisesRegex(oc.GuardError, "provider state"):
            self.run_preflight(provider=provider)

    def test_an_isolated_root_that_is_a_symlink_refuses(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        (self.scratch / "xdg-config").symlink_to(elsewhere)
        with self.assertRaisesRegex(oc.GuardError, "not an owned directory"):
            oc.create_isolated_dirs(self.scratch)

    def test_a_root_outside_the_owned_scratch_root_refuses(self):
        with self.assertRaisesRegex(oc.GuardError, "owned scratch root"):
            oc._prepare_isolated_dir(self.root / "loose", self.scratch)


class ProviderOutputCaptureTest(_WorktreeTestCase):
    """No refusal may echo resolved config, provider stdout, or values."""

    def test_refusal_diagnostics_name_key_paths_only(self):
        secret = "sk-do-not-print-this"
        document = final_config(self.agents_md)
        document["mcp"] = {"evil": {"command": [secret]}}
        document["username"] = secret
        provider = FakeProvider(self.agents_md, configs=[document])
        with self.assertRaises(oc.GuardError) as caught:
            self.run_preflight(provider=provider)
        message = str(caught.exception)
        self.assertIn("mcp", message)
        self.assertNotIn(secret, message)
        self.assertNotIn("{", message)

    def test_invalid_and_nonzero_provider_output_never_reaches_the_message(self):
        def invalid(argv, environment):
            if argv[1:] == ["--version"]:
                return oc.ProviderResult(0, f"{oc.OPENCODE_VERSION}\n")
            if argv[1:] == ["--pure", "debug", "skill"]:
                return oc.ProviderResult(0, json.dumps([{"name": "herdr-orchestration"}]))
            return oc.ProviderResult(0, "<<<secret provider stdout>>>")

        with self.assertRaises(oc.GuardError) as caught:
            self.run_preflight(provider=invalid)
        self.assertIn("invalid JSON", str(caught.exception))
        self.assertNotIn("secret provider stdout", str(caught.exception))


class ShimArgumentTest(unittest.TestCase):
    def test_the_only_accepted_shape_is_model_plus_variant(self):
        self.assertEqual(
            (MODEL, VARIANT), oc.parse_shim_arguments(["--model", MODEL, "--variant", VARIANT])
        )

    def test_every_other_argument_is_forbidden(self):
        cases = (
            ["--model", MODEL, "--variant", VARIANT, "run"],
            ["--model", MODEL, "--variant", VARIANT, "--pure"],
            ["--model", MODEL, "--variant", VARIANT, "--agent", "general"],
            ["--model", MODEL, "--variant", VARIANT, "prompt text"],
            [f"--model={MODEL}", "--variant", VARIANT],
            ["debug", "config"],
            ["--env", "OPENCODE_CONFIG_DIR=/evil"],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaises(oc.GuardError):
                    oc.parse_shim_arguments(arguments)

    def test_missing_values_and_duplicates_are_rejected(self):
        for arguments in (
            ["--model"],
            ["--model", MODEL],
            ["--variant", VARIANT],
            ["--model", MODEL, "--model", MODEL, "--variant", VARIANT],
            ["--model", MODEL, "--variant", VARIANT, "--variant", VARIANT],
        ):
            with self.subTest(arguments=arguments):
                with self.assertRaises(oc.GuardError):
                    oc.parse_shim_arguments(arguments)

    def test_an_unsupported_variant_is_rejected(self):
        with self.assertRaises(RoutingError):
            oc.parse_shim_arguments(["--model", MODEL, "--variant", "ultra"])


class DirectConsoleGateTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def initialized_target(self) -> Path:
        target = self.root / "target"
        (target / ".brichan").mkdir(parents=True)
        (target / "bin").mkdir()
        (target / "AGENTS.md").write_text("# policy\n", encoding="utf-8")
        return target

    def test_an_initialized_target_refuses(self):
        with self.assertRaisesRegex(oc.GuardError, "initialized Brichan project"):
            oc.require_direct_console_target(self.initialized_target())

    def test_a_lookalike_target_with_a_routing_entry_still_refuses(self):
        target = self.initialized_target()
        config = target / ".brichan" / "config"
        config.mkdir()
        (config / "model-routing.json").write_text(
            json.dumps({"coordinator": {"runtimes": {"opencode": {}}}}), encoding="utf-8"
        )
        with self.assertRaisesRegex(oc.GuardError, "initialized Brichan project"):
            oc.require_direct_console_target(target)

    def test_a_target_without_state_passes(self):
        target = self.root / "plain"
        target.mkdir()
        oc.require_direct_console_target(target)

    def test_a_source_checkout_that_initialized_itself_is_allowed(self):
        """D11's permissive branch: `.brichan` present AND genuine package markers.

        This is `brichan init --apply` run inside the Brichan checkout itself.
        Every other case here is a refusal, so without this the allow path is
        unexercised and a regression would silently over-refuse.
        """

        checkout = self.root / "checkout"
        (checkout / ".brichan" / "config").mkdir(parents=True)
        (checkout / "src" / "brichan").mkdir(parents=True)
        (checkout / "src" / "brichan" / "__init__.py").write_text(
            '__version__ = "0.0.0"\n', encoding="utf-8"
        )
        (checkout / "pyproject.toml").write_text(
            '[project]\nname = "brichan"\nversion = "0.0.0"\n', encoding="utf-8"
        )
        # Same lookalike surface the refusal cases carry, so the only thing that
        # distinguishes this target is the package marker.
        (checkout / "bin").mkdir()
        (checkout / "AGENTS.md").write_text("# policy\n", encoding="utf-8")

        self.assertTrue(oc.is_source_checkout(checkout))
        oc.require_direct_console_target(checkout)

        # Remove only the marker; the same directory must now refuse.
        (checkout / "pyproject.toml").write_text(
            '[project]\nname = "not-brichan"\n', encoding="utf-8"
        )
        self.assertFalse(oc.is_source_checkout(checkout))
        with self.assertRaisesRegex(oc.GuardError, "initialized Brichan project"):
            oc.require_direct_console_target(checkout)

    def test_the_real_source_checkout_is_positively_identified(self):
        self.assertTrue(oc.is_source_checkout(ROOT))
        oc.require_direct_console_target(ROOT)

    def test_the_agents_md_plus_bin_heuristic_is_not_the_marker(self):
        target = self.initialized_target()
        self.assertFalse(oc.is_source_checkout(target))
        (target / "pyproject.toml").write_text('name = "something-else"\n', encoding="utf-8")
        self.assertFalse(oc.is_source_checkout(target))


class CoordinatorEntrypointTest(unittest.TestCase):
    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = oc.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_help_and_version_work_outside_a_checkout(self):
        with mock.patch.object(
            oc, "repository_root", side_effect=RuntimeError("not a checkout")
        ):
            code, out, err = self._run(["--help"])
            self.assertEqual(0, code)
            self.assertIn("usage: brichan-opencode", out)
            self.assertEqual("", err)
            code, out, err = self._run(["--version"])
            self.assertEqual(0, code)
            self.assertEqual(f"brichan-opencode {__version__}\n", out)

    def test_provider_arguments_are_refused(self):
        code, _out, err = self._run(["--agent", "general"])
        self.assertEqual(2, code)
        self.assertIn("takes no provider arguments", err)
        self.assertNotIn("Traceback", err)

    def test_a_missing_manifest_entry_is_an_owned_error(self):
        payload = json.loads((ROOT / "config/model-routing.json").read_text("utf-8"))
        del payload["coordinator"]["runtimes"]["opencode"]
        settings = parse_settings(payload)
        with self.assertRaisesRegex(RoutingError, "no opencode coordinator entry"):
            resolve_coordinator(settings, "opencode")

    def test_the_resolved_command_is_the_shim_and_carries_no_provider_argv(self):
        command = oc.shim_command(route())
        self.assertTrue(command[0].endswith("brichan-opencode-exec"))
        self.assertEqual(["--model", MODEL, "--variant", VARIANT], command[1:])
        self.assertNotIn("opencode", command[1:])
        self.assertNotIn("--pure", command)


class WorkerCommandTest(unittest.TestCase):
    def test_a_named_opencode_route_launches_through_the_shim(self):
        command = worker_command(route())
        self.assertTrue(command[0].endswith("brichan-opencode-exec"))
        self.assertEqual(["--model", MODEL, "--variant", VARIANT], command[1:])

    def test_the_legacy_shape_consumes_dash_m_into_the_agent_config(self):
        for arguments in (
            ["-m", MODEL, "--variant", VARIANT],
            ["--model", MODEL, "--variant", VARIANT],
            [f"-m{MODEL}", f"--variant={VARIANT}"],
        ):
            with self.subTest(arguments=arguments):
                command = secure_legacy_command(["opencode", *arguments])
                self.assertTrue(command[0].endswith("brichan-opencode-exec"))
                self.assertEqual(["--model", MODEL, "--variant", VARIANT], command[1:])

    def test_every_other_legacy_opencode_argument_is_forbidden(self):
        cases = (
            ["run", "do the thing"],
            ["--pure"],
            ["--agent", "general"],
            ["-m", MODEL, "--variant", VARIANT, "--print-logs"],
            ["-m", MODEL, "--variant", VARIANT, "serve"],
            ["-c", "mcp.evil=true", "--variant", VARIANT],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaises(RoutingError):
                    secure_legacy_command(["opencode", *arguments])

    def test_an_incomplete_legacy_shape_is_rejected(self):
        for arguments in ([], ["-m", MODEL], ["--variant", VARIANT]):
            with self.subTest(arguments=arguments):
                with self.assertRaises(RoutingError):
                    opencode_command(list(arguments))

    def test_codex_and_claude_worker_commands_are_untouched(self):
        settings = parse_settings(
            json.loads((ROOT / "config/model-routing.json").read_text("utf-8"))
        )
        codex = worker_command(resolve_coordinator(settings, "codex"))
        claude = worker_command(resolve_coordinator(settings, "claude"))
        self.assertEqual("codex", codex[0])
        self.assertEqual("claude", claude[0])
        self.assertNotIn("opencode", codex)
        self.assertNotIn("opencode", claude)


class WorkerGateManifestBranchTest(unittest.TestCase):
    """D4's gate when the runtime comes from the manifest, not from `--runtime`.

    `_reject_opencode_installed_target` has two call sites in the named-route
    path: one for an explicit `--runtime opencode` (checked before the project
    state is inspected) and one for `route.runtime == "opencode"` after
    resolution.  The refusal tests elsewhere all take the first.  These take the
    second, so the manifest-driven path is a tested fact rather than a reading.
    """

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.target = self.root / "target"
        (self.target / ".git").mkdir(parents=True)
        self.manifest = self.root / "model-routing.json"
        payload = json.loads((ROOT / "config/model-routing.json").read_text("utf-8"))
        payload["routes"]["implement"] = {
            "runtime": "opencode",
            "model": MODEL,
            "effort": VARIANT,
        }
        self.manifest.write_text(json.dumps(payload), encoding="utf-8")

    def arguments(self, **overrides):
        import argparse

        values = {
            "name": "brichan-test-worker",
            "cwd": str(self.target),
            "env": [],
            "route": "implement",
            "runtime": None,
            "model": None,
            "effort": None,
            "argv": [],
            "anchor_pane": "p1",
            "dry_run": False,
            "json_output": False,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def resolve(self, args):
        from brichan.orchestration import worker_launch

        with mock.patch.dict(
            os.environ, {"BRICHAN_MODEL_ROUTING_FILE": str(self.manifest)}
        ):
            return worker_launch._resolve_launch(args)

    def test_a_manifest_routed_opencode_worker_resolves_without_an_explicit_runtime(self):
        """The precondition: no --runtime is passed, yet the route is OpenCode."""

        resolution = self.resolve(self.arguments())
        self.assertIsNotNone(resolution.route)
        self.assertEqual("opencode", resolution.route.runtime)
        self.assertTrue(resolution.command[0].endswith("brichan-opencode-exec"))

    def test_the_gate_refuses_a_manifest_routed_opencode_worker_on_a_state_target(self):
        from brichan.lifecycle import Inspection, StateKind
        from brichan.orchestration.model_routing import RoutingError

        state = self.target / ".brichan" / "config"
        state.mkdir(parents=True)
        (state / "model-routing.json").write_text(
            self.manifest.read_text(encoding="utf-8"), encoding="utf-8"
        )

        # Only the state-health inspection is stubbed, and only to HEALTHY. The
        # managed routing file is hash-checked in real life, so a real target
        # cannot both be healthy and route to OpenCode; stubbing that one check
        # is what makes the guard under test reachable at all. The routing
        # resolution and the gate itself both run for real.
        healthy = Inspection(StateKind.HEALTHY, "healthy")
        with mock.patch("brichan.lifecycle.inspect_project", return_value=healthy):
            with self.assertRaises(RoutingError) as caught:
                self.resolve(self.arguments())
        self.assertIn("OpenCode workers are not supported", str(caught.exception))

    def test_the_gate_also_refuses_a_manifest_routed_env_override(self):
        from brichan.lifecycle import Inspection, StateKind
        from brichan.orchestration.model_routing import RoutingError

        state = self.target / ".brichan" / "config"
        state.mkdir(parents=True)
        (state / "model-routing.json").write_text(
            self.manifest.read_text(encoding="utf-8"), encoding="utf-8"
        )
        healthy = Inspection(StateKind.HEALTHY, "healthy")
        with mock.patch("brichan.lifecycle.inspect_project", return_value=healthy):
            with self.assertRaises(RoutingError):
                self.resolve(self.arguments(env=["OPENCODE_CONFIG_DIR=/evil"]))

    def test_a_manifest_routed_opencode_worker_is_allowed_without_state(self):
        """The permissive side of the same branch: no `.brichan`, no refusal."""

        resolution = self.resolve(self.arguments())
        self.assertEqual(
            ["--model", MODEL, "--variant", VARIANT], list(resolution.command[1:])
        )


class ShimEntrypointTest(_WorktreeTestCase):
    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = oc.exec_main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_help_and_version_do_not_preflight(self):
        code, out, _err = self._run(["--help"])
        self.assertEqual(0, code)
        self.assertIn("usage: brichan-opencode-exec", out)
        code, out, _err = self._run(["--version"])
        self.assertEqual(0, code)
        self.assertEqual(f"brichan-opencode-exec {__version__}\n", out)

    def test_a_forbidden_argument_exits_nonzero_without_preflight(self):
        with mock.patch.object(oc, "preflight") as preflight:
            code, _out, err = self._run(["--model", MODEL, "--variant", VARIANT, "run"])
        self.assertEqual(2, code)
        self.assertIn("forbidden", err)
        self.assertNotIn("Traceback", err)
        preflight.assert_not_called()

    def test_a_cwd_outside_a_git_worktree_is_an_owned_nonzero_refusal(self):
        # End-to-end through the real preflight: no fake runner and no mocked
        # step, because the bound check precedes every provider call.
        outside = self.root / "outside"
        outside.mkdir()
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(outside)
        code, out, err = self._run(["--model", MODEL, "--variant", VARIANT])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertTrue(err.startswith(f"{oc.SHIM_COMMAND}: "), err)
        self.assertIn("outside a Git worktree", err)
        self.assertNotIn("Traceback", err)

    def test_a_refused_preflight_removes_the_owned_scratch_root(self):
        removed = []

        def refuse(**kwargs):
            removed.append(kwargs["scratch_root"])
            kwargs["scratch_root"].mkdir(parents=True, exist_ok=True)
            raise oc.GuardError("refused for the test")

        with mock.patch.object(oc, "preflight", side_effect=refuse):
            code, _out, err = self._run(["--model", MODEL, "--variant", VARIANT])
        self.assertEqual(2, code)
        self.assertIn("refused for the test", err)
        self.assertFalse(removed[0].exists())

    def test_a_successful_preflight_execs_the_pinned_argv(self):
        def succeed(**kwargs):
            # The real success path never returns, so the owned scratch root is
            # handed to the provider and outlives the process.  execvpe is
            # mocked here, so this test has to remove it itself or it leaks one
            # empty directory into the system temporary root per suite run.
            self.addCleanup(shutil.rmtree, kwargs["scratch_root"], True)
            return list(oc.LAUNCH_ARGV), {"PATH": "/usr/bin"}

        with mock.patch.object(oc, "preflight", side_effect=succeed):
            with mock.patch.object(os, "execvpe") as execvpe:
                code, _out, _err = self._run(["--model", MODEL, "--variant", VARIANT])
        execvpe.assert_called_once_with(
            "opencode",
            ["opencode", "--pure", "--agent", "brichan-primary"],
            {"PATH": "/usr/bin"},
        )
        self.assertEqual(0, code)

    def test_a_missing_provider_binary_is_an_owned_error(self):
        def succeed(**kwargs):
            return list(oc.LAUNCH_ARGV), {"PATH": "/usr/bin"}

        with mock.patch.object(oc, "preflight", side_effect=succeed):
            with mock.patch.object(os, "execvpe", side_effect=FileNotFoundError()):
                code, _out, err = self._run(["--model", MODEL, "--variant", VARIANT])
        self.assertEqual(2, code)
        self.assertIn("not installed or not on PATH", err)
        self.assertNotIn("Traceback", err)

    def test_no_exception_type_escapes_the_shim_as_a_traceback(self):
        """A traceback is not an owned refusal: it prints paths and frames."""

        for error in (
            FileExistsError(17, "File exists"),
            PermissionError(13, "Permission denied"),
            RecursionError("depth"),
            ValueError("unhandled"),
        ):
            with self.subTest(error=type(error).__name__):
                roots = []

                def explode(**kwargs):
                    roots.append(kwargs["scratch_root"])
                    raise error

                with mock.patch.object(oc, "preflight", side_effect=explode):
                    code, _out, err = self._run(["--model", MODEL, "--variant", VARIANT])
                self.assertEqual(2, code)
                self.assertTrue(err.startswith("brichan-opencode-exec: "), err)
                self.assertIn(type(error).__name__, err)
                self.assertNotIn("Traceback", err)
                self.assertFalse(roots[0].exists())

    def test_an_unexpected_failure_before_the_scratch_root_is_still_owned(self):
        with mock.patch.object(oc.tempfile, "mkdtemp", side_effect=RuntimeError("boom")):
            code, _out, err = self._run(["--model", MODEL, "--variant", VARIANT])
        self.assertEqual(2, code)
        self.assertTrue(err.startswith("brichan-opencode-exec: "), err)
        self.assertNotIn("Traceback", err)

    def test_an_unwritable_temporary_root_is_an_owned_error(self):
        failure = OSError(13, "Permission denied")
        with mock.patch.object(oc.tempfile, "mkdtemp", side_effect=failure):
            code, _out, err = self._run(["--model", MODEL, "--variant", VARIANT])
        self.assertEqual(2, code)
        self.assertIn("cannot create the owned scratch root", err)
        self.assertNotIn("Traceback", err)


class CoordinatorFailureTest(unittest.TestCase):
    """The coordinator entry point owns its failures too."""

    def test_no_exception_type_escapes_the_coordinator_as_a_traceback(self):
        for error in (RuntimeError("no root"), ValueError("odd"), OSError(2, "gone")):
            with self.subTest(error=type(error).__name__):
                out, stderr = io.StringIO(), io.StringIO()
                with mock.patch.object(oc, "command", side_effect=error):
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(stderr):
                        code = oc.main([])
                err = stderr.getvalue()
                self.assertEqual(2, code)
                self.assertTrue(err.startswith("brichan-opencode: "), err)
                self.assertNotIn("Traceback", err)

    def test_a_failing_chdir_is_an_owned_error(self):
        with mock.patch.object(oc, "command", return_value=["/bin/true"]):
            with mock.patch.object(os, "chdir", side_effect=OSError(2, "No such file")):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    code = oc.main([])
        self.assertEqual(2, code)
        self.assertIn("cannot enter the repository root", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())


if __name__ == "__main__":
    unittest.main()
