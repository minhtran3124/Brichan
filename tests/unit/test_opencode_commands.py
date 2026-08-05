"""Guard tests for the OpenCode adapter and its fail-closed launch shim.

No live provider is ever launched here.  Every test that needs provider output
supplies a fake runner, so the whole S3 preflight is exercised without an
`opencode` process, without touching the real OpenCode configuration, and
without reading real credentials.
"""

import contextlib
import getpass
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tests import opencode_surface

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


#: Extensions that make a glob match *executable* rather than data.  Kept
#: deliberately wider than the two OpenCode uses today: the drift test decides
#: whether a provider glob is an executable scan by intersecting its extensions
#: with this set, so a bump that starts loading ``.mjs`` or ``.tsx`` is
#: classified as an executable scan and compared, rather than skipped as data.
CODE_EXTENSIONS = frozenset({"js", "jsx", "cjs", "mjs", "ts", "tsx", "cts", "mts"})

#: Every ``Glob.scan``/``Glob.scanSync``/``fs.glob`` call site in
#: ``packages/core/src`` and ``packages/opencode/src`` at v1.18.12 (tag
#: ``v1.18.12`` = ``0dd6950d1b06958fbcdcadf0ad56258257ab7fdb``) whose pattern is
#: a per-root directory glob, transcribed verbatim as
#: ``(path, line, source line)``.
#:
#: This is the drift anchor plan version 12 requires for D8, and it is the same
#: move version 11 made for D12 — with one difference that matters: the anchor
#: is the *provider's* text, not a restatement of ours.  The executable subset
#: is computed from these lines by brace expansion, so the expected glob set is
#: derived here rather than asserted, and a line that gains a directory
#: alternative or an extension changes the derived set without anyone editing
#: an expectation.
#:
#: The non-executable entries are not decoration.  They are what makes an ADDED
#: family detectable: refreshing this transcript at a version bump transcribes
#: every per-root glob, and any one of them that turns out to carry a code
#: extension lands in the executable set and fails
#: ``test_the_table_matches_the_pinned_provider_globs``.
PINNED_PER_ROOT_GLOBS = (
    (
        "packages/opencode/src/tool/registry.ts",
        180,
        '          Glob.scanSync("{tool,tools}/*.{js,ts}", { cwd: dir, absolute:'
        " true, dot: true, symlink: true }),",
    ),
    (
        "packages/opencode/src/config/plugin.ts",
        21,
        '  for (const item of await Glob.scan("{plugin,plugins}/*.{ts,js}", {',
    ),
    (
        "packages/core/src/config/plugin/external.ts",
        60,
        '            .glob("{plugin,plugins}/*.{ts,js}", {',
    ),
    (
        "packages/opencode/src/config/agent.ts",
        13,
        '  for (const item of await Glob.scan("{agent,agents}/**/*.md", {',
    ),
    (
        "packages/opencode/src/config/agent.ts",
        36,
        '  for (const item of await Glob.scan("{mode,modes}/*.md", {',
    ),
    (
        "packages/opencode/src/config/command.ts",
        15,
        '  for (const item of await Glob.scan("{command,commands}/**/*.md", {',
    ),
    (
        "packages/core/src/config/plugin/command.ts",
        55,
        '      .glob("{command,commands}/**/*.md", { cwd: directory, absolute:'
        " true, dot: true, symlink: true })",
    ),
    (
        "packages/core/src/skill.ts",
        79,
        '          .glob("{*.md,**/SKILL.md}", { cwd: directory, absolute: true,'
        ' include: "file", symlink: true, dot: true })',
    ),
    (
        "packages/core/src/config/plugin/agent.ts",
        21,
        '  { pattern: "{agent,agents}/**/*.md", primary: false },',
    ),
    (
        "packages/core/src/config/plugin/agent.ts",
        22,
        '  { pattern: "{mode,modes}/*.md", primary: true },',
    ),
    (
        "packages/opencode/src/skill/index.ts",
        23,
        'const EXTERNAL_SKILL_PATTERN = "skills/**/SKILL.md"',
    ),
    (
        "packages/opencode/src/skill/index.ts",
        24,
        'const OPENCODE_SKILL_PATTERN = "{skill,skills}/**/SKILL.md"',
    ),
    (
        "packages/opencode/src/skill/index.ts",
        25,
        'const SKILL_PATTERN = "**/SKILL.md"',
    ),
    # Literal-pattern globs that are not per-root content discovery at all.
    # They are transcribed anyway so the completeness check can assert that
    # *every* literal glob in the two packages is accounted for: a site left out
    # of this transcript is indistinguishable from a site nobody looked at.
    (
        "packages/core/src/tool/skill.ts",
        87,
        '                    ? (yield* fs.glob("**/*", { cwd: directory,'
        ' absolute: true, include: "file", dot: true }))',
    ),
    (
        "packages/opencode/src/storage/storage.ts",
        85,
        '    const projectDirs = yield* fs.glob("*", {',
    ),
    (
        "packages/opencode/src/storage/storage.ts",
        97,
        "        for (const msgFile of yield* fs.glob"
        '("storage/session/message/*/*.json", {',
    ),
    (
        "packages/opencode/src/storage/storage.ts",
        139,
        "        for (const sessionFile of yield* fs.glob"
        '("storage/session/info/*.json", {',
    ),
    (
        "packages/opencode/src/storage/storage.ts",
        183,
        '    for (const item of yield* fs.glob("session/*/*.json", {',
    ),
    (
        "packages/opencode/src/storage/storage.ts",
        305,
        '        .glob("**/*", {',
    ),
    (
        "packages/opencode/src/project/project.ts",
        318,
        '        .glob("**/favicon.{ico,png,svg,jpg,jpeg,webp}", {',
    ),
)

#: Glob call sites at the pinned ref whose pattern is *not* a string literal, so
#: no transcript line can express them.  Each was resolved by hand to the
#: constants it can receive; the last column records that resolution.
#:
#: This list exists so the completeness check has something to assert against.
#: A provider bump that introduces a new dynamic glob call fails
#: ``test_pinned_source_contains_no_undocumented_glob_sites`` and forces a human
#: to resolve it, rather than letting an unreadable pattern pass unseen.
PINNED_DYNAMIC_GLOB_SITES = {
    ("packages/core/src/fs-util.ts", 149): "the FSUtil.glob wrapper itself",
    ("packages/core/src/config/plugin/agent.ts", 143): (
        "source.pattern from legacySources at :21-22 — both markdown"
    ),
    ("packages/core/src/filesystem/search.ts", 56): "ripgrep search tool",
    ("packages/core/src/filesystem/search.ts", 151): "ripgrep search tool",
    ("packages/core/src/filesystem/fff.bun.ts", 130): "filesystem backend shim",
    ("packages/core/src/tool/glob.ts", 77): "the agent-facing glob tool",
    ("packages/opencode/src/skill/index.ts", 150): (
        "one of the three SKILL patterns at :23-25 — all markdown"
    ),
    ("packages/opencode/src/util/filesystem.ts", 233): "generic glob helper",
    ("packages/opencode/src/cli/cmd/debug/ripgrep.ts", 37): "debug ripgrep cmd",
    ("packages/opencode/src/storage/storage.ts", 150): "storage JSON",
    ("packages/opencode/src/storage/storage.ts", 165): "storage JSON",
    ("packages/opencode/src/tool/glob.ts", 50): "the agent-facing glob tool",
    ("packages/opencode/src/session/instruction.ts", 141): "instruction files",
}

_GLOB_CALL = re.compile(r"(?:Glob\.scanSync|Glob\.scan|\.glob)\(")
_LEADING_LITERAL = re.compile(r'^\s*"([^"]*)"')
_PATTERN_LITERAL = re.compile(r'"([^"\s]*[*{][^"\s]*)"')


def expand_braces(pattern):
    """Expand ``{a,b}`` alternations into concrete patterns.

    Comparing fully expanded patterns, rather than the pattern strings, is what
    lets the drift test see three distinct kinds of change with one assertion: a
    new directory alternative, a new extension, and a change of depth
    (``tool/*.js`` becoming ``tool/**/*.js``) all alter the expanded set.
    """

    start = pattern.find("{")
    if start == -1:
        return [pattern]
    depth = 0
    for index in range(start, len(pattern)):
        if pattern[index] == "{":
            depth += 1
        elif pattern[index] == "}":
            depth -= 1
            if depth == 0:
                head, body, tail = (
                    pattern[:start],
                    pattern[start + 1 : index],
                    pattern[index + 1 :],
                )
                expanded = []
                for alternative in body.split(","):
                    for rest in expand_braces(head + alternative + tail):
                        if rest not in expanded:
                            expanded.append(rest)
                return expanded
    raise AssertionError(f"unbalanced brace in provider glob: {pattern}")


def executable_globs(transcript):
    """Concrete executable glob patterns implied by a provider transcript.

    A pattern counts as executable when any expansion of it ends in a
    :data:`CODE_EXTENSIONS` suffix; the *whole* expansion of such a pattern is
    then returned, so an extension added alongside ``js``/``ts`` widens the set
    instead of being filtered away by the very rule that selected it.
    """

    patterns = set()
    for _path, _line, text in transcript:
        for literal in _PATTERN_LITERAL.findall(text):
            expansions = expand_braces(literal)
            if any(item.rsplit(".", 1)[-1] in CODE_EXTENSIONS for item in expansions):
                patterns.update(expansions)
    return patterns


class ExecutableScanEnumerationTest(unittest.TestCase):
    """D8's glob set must equal the pinned provider's own per-root scan set.

    ``EXECUTABLE_SCANS`` was the last hand-listed executable surface after plan
    version 11 derived D12's config set.  The round-6 implementer flagged it
    rather than leaving it buried, and version 12 closes it here.
    """

    def guard_globs(self):
        return {
            f"{directory}/*.{extension}"
            for scan in oc.EXECUTABLE_SCANS
            for directory in scan.directories
            for extension in scan.extensions
        }

    def test_the_table_matches_the_pinned_provider_globs(self):
        self.assertEqual(
            executable_globs(PINNED_PER_ROOT_GLOBS), self.guard_globs()
        )

    def test_every_entry_carries_a_pinned_source_citation(self):
        for scan in oc.EXECUTABLE_SCANS:
            with self.subTest(label=scan.label):
                self.assertRegex(scan.citation, r"packages/\S+\.ts:\d")

    def test_an_added_provider_directory_family_fails(self):
        """The ADDED direction, demonstrated rather than asserted.

        A provider release that starts globbing a third family — here a
        hypothetical ``{extension,extensions}/*.js`` — enters the transcript
        when it is refreshed at the version bump, widens the derived set, and
        fails the equality assertion while ``EXECUTABLE_SCANS`` is untouched.
        """

        widened = PINNED_PER_ROOT_GLOBS + (
            (
                "packages/opencode/src/config/extension.ts",
                9,
                '  for (const item of await Glob.scan("{extension,extensions}/*.js", {',
            ),
        )
        derived = executable_globs(widened)
        self.assertIn("extension/*.js", derived)
        self.assertNotEqual(derived, self.guard_globs())
        with mock.patch.dict(globals(), {"PINNED_PER_ROOT_GLOBS": widened}):
            with self.assertRaises(AssertionError):
                self.test_the_table_matches_the_pinned_provider_globs()

    def test_an_added_provider_extension_fails(self):
        """The other ADDED shape: same families, one more extension."""

        widened = tuple(
            (path, line, text.replace("*.{ts,js}", "*.{ts,js,mjs}"))
            for path, line, text in PINNED_PER_ROOT_GLOBS
        )
        derived = executable_globs(widened)
        self.assertIn("plugin/*.mjs", derived)
        with mock.patch.dict(globals(), {"PINNED_PER_ROOT_GLOBS": widened}):
            with self.assertRaises(AssertionError):
                self.test_the_table_matches_the_pinned_provider_globs()

    def test_a_deeper_provider_glob_fails(self):
        """Depth counts too: ``tool/*.js`` widening to ``tool/**/*.js``."""

        widened = tuple(
            (path, line, text.replace("{tool,tools}/*.", "{tool,tools}/**/*."))
            for path, line, text in PINNED_PER_ROOT_GLOBS
        )
        self.assertIn("tool/**/*.js", executable_globs(widened))
        with mock.patch.dict(globals(), {"PINNED_PER_ROOT_GLOBS": widened}):
            with self.assertRaises(AssertionError):
                self.test_the_table_matches_the_pinned_provider_globs()

    def test_dropping_a_family_from_the_guard_fails(self):
        """The deletion direction, for symmetry with round 6's demonstration."""

        trimmed = tuple(
            scan for scan in oc.EXECUTABLE_SCANS if scan.label != "executable plugin"
        )
        with mock.patch.object(oc, "EXECUTABLE_SCANS", trimmed):
            with self.assertRaises(AssertionError):
                self.test_the_table_matches_the_pinned_provider_globs()

    def test_markdown_scans_are_classified_as_data(self):
        """The classifier must not sweep every provider glob into the guard."""

        derived = executable_globs(PINNED_PER_ROOT_GLOBS)
        for pattern in derived:
            self.assertNotIn(".md", pattern)
        self.assertTrue(
            any("SKILL.md" in text for _p, _l, text in PINNED_PER_ROOT_GLOBS)
        )


#: Set this to an extracted v1.18.12 source tree to run the completeness check
#: below, e.g.::
#:
#:     gh api repos/anomalyco/opencode/tarball/v1.18.12 > oc.tgz
#:     tar -xzf oc.tgz -C /some/dir
#:     BRICHAN_OPENCODE_PINNED_SOURCE=/some/dir/anomalyco-opencode-0dd6950 \
#:         python3 -m unittest tests.unit.test_opencode_commands
#:
#: It is opt-in because the default suite must stay hermetic and offline.  What
#: it buys is the one thing the transcript above cannot prove on its own: that
#: the transcript is *complete*.
PINNED_SOURCE_ENV = "BRICHAN_OPENCODE_PINNED_SOURCE"


@unittest.skipUnless(
    os.environ.get(PINNED_SOURCE_ENV),
    f"set {PINNED_SOURCE_ENV} to an extracted v1.18.12 tree",
)
class PinnedSourceCompletenessTest(unittest.TestCase):
    """Check the transcript against the real pinned tree, when one is supplied.

    Without this, ``PINNED_PER_ROOT_GLOBS`` is trusted text.  With it, the
    transcript is verified line for line and, more importantly, verified to omit
    nothing: every glob call site in the two packages that can load per-root
    content is either transcribed or listed as a resolved dynamic site.
    """

    def setUp(self):
        self.tree = Path(os.environ[PINNED_SOURCE_ENV])
        if not (self.tree / "packages/opencode/src").is_dir():
            self.skipTest(f"{self.tree} is not an opencode source tree")

    def source_files(self):
        for package in ("core", "opencode"):
            yield from sorted((self.tree / "packages" / package / "src").rglob("*.ts"))

    def test_every_transcribed_line_matches_the_pinned_source(self):
        for path, line, text in PINNED_PER_ROOT_GLOBS:
            with self.subTest(path=path, line=line):
                actual = (self.tree / path).read_text(encoding="utf-8").splitlines()
                self.assertEqual(text, actual[line - 1])

    def test_pinned_source_contains_no_undocumented_glob_sites(self):
        transcribed = {(path, line) for path, line, _text in PINNED_PER_ROOT_GLOBS}
        literal_sites = set()
        dynamic_sites = set()
        for source in self.source_files():
            relative = str(source.relative_to(self.tree))
            for number, text in enumerate(
                source.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if text.lstrip().startswith("//"):
                    continue
                call = _GLOB_CALL.search(text)
                if not call:
                    continue
                site = (relative, number)
                if _LEADING_LITERAL.match(text[call.end() :]):
                    literal_sites.add(site)
                else:
                    dynamic_sites.add(site)

        # Every literal-pattern glob call must be transcribed above, or the
        # transcript is not the complete per-root picture it claims to be.
        self.assertEqual(set(), literal_sites - transcribed)
        # And every pattern the transcript cannot express must be a site a human
        # has already resolved.
        self.assertEqual(set(), dynamic_sites - set(PINNED_DYNAMIC_GLOB_SITES))

    def test_the_guard_glob_set_matches_the_pinned_tree_directly(self):
        """Derive the executable set from the tree itself, ignoring the transcript."""

        patterns = set()
        for source in self.source_files():
            for text in source.read_text(encoding="utf-8").splitlines():
                if text.lstrip().startswith("//"):
                    continue
                call = _GLOB_CALL.search(text)
                if not call:
                    continue
                literal = _LEADING_LITERAL.match(text[call.end() :])
                if not literal:
                    continue
                expansions = expand_braces(literal.group(1))
                if any(
                    item.rsplit(".", 1)[-1] in CODE_EXTENSIONS for item in expansions
                ):
                    patterns.update(expansions)
        self.assertEqual(
            {
                f"{directory}/*.{extension}"
                for scan in oc.EXECUTABLE_SCANS
                for directory in scan.directories
                for extension in scan.extensions
            },
            patterns,
        )


# ---------------------------------------------------------------------------
# D12 execution keys — the third derivation, of the same shape as the two above
# ---------------------------------------------------------------------------


#: Every ``import()`` call site in ``packages/{core,opencode}/src`` at the pinned
#: ref whose specifier is **not** a string literal, transcribed verbatim, with
#: the origin of that specifier resolved.
#:
#: The closure argument runs over imports, not over configuration keys, and that
#: direction is what makes it complete: a configuration key can only execute code
#: by reaching an ``import()``.  Enumerate every import a configuration value can
#: reach, resolve where each one's specifier comes from, and the set of
#: configuration keys falls out — with nothing left over to have been forgotten.
#: Enumerating keys directly would have no such closure, which is how
#: ``plugin``/``plugins`` came to be believed complete when it was not.
#:
#: ``origins`` is a tuple of resolutions, because one site can be fed from more
#: than one place.  Each entry is either:
#:
#: * ``"key:<name>"`` — a top-level configuration key.  These are the guard's
#:   :data:`oc.EXECUTION_KEYS`.
#: * ``"glob:<pattern>"`` — a per-root directory scan, which is D8's surface and
#:   already covered by :data:`oc.EXECUTABLE_SCANS`.
#: * ``"file:<label>"`` — a discovered configuration *file* named by its path
#:   rather than by any key, which is D12's :data:`oc.CONFIG_DISCOVERY_SOURCES`
#:   surface.
#: * ``"none"`` — no configuration input reaches this specifier.
PINNED_DYNAMIC_IMPORT_SITES = (
    (
        "packages/core/src/config/plugin/external.ts",
        80,
        "          const mod = yield* Effect.promise(() => import(entrypoint))",
        ("key:plugins", "glob:{plugin,plugins}/*.{ts,js}"),
        "entry.info.plugins[].package at :42-56, or the directory glob at :60",
    ),
    (
        "packages/core/src/plugin/provider/dynamic.ts",
        20,
        "          return (await import(",
        ("key:providers",),
        "evt.package, set from model.api.package by core/src/aisdk.ts:208,215",
    ),
    (
        "packages/core/src/plugin/provider/sap-ai-core.ts",
        25,
        "          return (await import(",
        ("key:providers",),
        "the same evt.package, for the sap-ai-core provider id",
    ),
    (
        "packages/opencode/src/config/config.ts",
        265,
        "          import(pathToFileURL(legacy).href, "
        '{ with: { type: "toml" } })',
        ("file:global legacy toml config",),
        "the <Global.Path.config>/config file path itself; no key names it",
    ),
    (
        "packages/opencode/src/plugin/loader.ts",
        139,
        "      mod = await import(row.entry)",
        ("key:plugin", "glob:{plugin,plugins}/*.{ts,js}"),
        "plugin_origins, built from the v1 plugin array at "
        "opencode/src/config/config.ts:344-348,432 and from ConfigPlugin.load "
        "— and, established in round 12, from the TUI document's own plugin "
        "array via config/tui.ts:157-168 and plugin/tui/runtime.ts:1088,1106. "
        "Same key name, second document; both are in CONFIG_DISCOVERY_SOURCES",
    ),
    (
        "packages/opencode/src/provider/provider.ts",
        1793,
        "        const mod = await import(importSpec)",
        ("key:provider",),
        "model.api.npm, resolved from the v1 provider record at :1440-1443",
    ),
    (
        "packages/opencode/src/tool/registry.ts",
        187,
        "          const mod = yield* Effect.promise(() => "
        "import(pathToFileURL(match).href))",
        ("glob:{tool,tools}/*.{js,ts}",),
        "a match from the {tool,tools} scan at :180; no key reaches it",
    ),
)

#: Where each derived key must appear as a top-level field in the pinned schemas.
#: This is the second half of the derivation: the import trace says *which*
#: values are imported, and this says what a config author has to spell to supply
#: one.  A provider bump that renames a key breaks this even if the import site
#: is untouched.
PINNED_EXECUTION_KEY_SCHEMA = {
    "plugin": ("packages/core/src/v1/config/config.ts", 56),
    "provider": ("packages/core/src/v1/config/config.ts", 110),
    "plugins": ("packages/core/src/config.ts", 102),
    "providers": ("packages/core/src/config.ts", 106),
}

_IMPORT_CALL = re.compile(r"(?<![\w$.])import\s*\(")
_IMPORT_LITERAL = re.compile(r"^\s*[\"'`]")


def module_specifier_keys(transcript):
    """Configuration keys implied by an import-site transcript."""

    return {
        origin[len("key:") :]
        for _path, _line, _text, origins, _note in transcript
        for origin in origins
        if origin.startswith("key:")
    }


class ExecutionKeyEnumerationTest(unittest.TestCase):
    """D12's key set must equal the pinned provider's module-specifier keys.

    ``EXECUTION_KEYS`` was the last hand-listed executable surface after plan
    versions 11 and 12 derived the config-file and directory-glob sets.  The
    round-7 implementer flagged it; version 13 closes it here — and the
    derivation immediately showed the hand-listed pair was not complete, adding
    ``provider`` and ``providers``.
    """

    def guard_keys(self):
        return {execution.key for execution in oc.EXECUTION_KEYS}

    def test_the_table_matches_the_pinned_provider_keys(self):
        self.assertEqual(
            module_specifier_keys(PINNED_DYNAMIC_IMPORT_SITES), self.guard_keys()
        )

    def test_every_entry_carries_a_pinned_source_citation(self):
        for execution in oc.EXECUTION_KEYS:
            with self.subTest(key=execution.key):
                self.assertRegex(execution.citation, r"packages/\S+\.ts:\d")
                self.assertIn(execution.config_version, ("v1", "v2"))
                self.assertTrue(execution.specifier_path)

    def test_no_key_is_trusted_to_the_merged_document(self):
        """``merge_gated`` is documentation; every key is refused regardless.

        D12 exists because a merge-gated conclusion has been wrong here before,
        so a future entry that sets this flag must still be scanned.
        """

        for execution in oc.EXECUTION_KEYS:
            with self.subTest(key=execution.key):
                self.assertFalse(execution.merge_gated)

    def test_an_added_provider_module_specifier_key_fails(self):
        """The ADDED direction, demonstrated rather than asserted.

        A provider release that starts importing a specifier taken from a new
        configuration key enters the transcript when it is refreshed at the
        version bump, widens the derived set, and fails the equality assertion
        while ``EXECUTION_KEYS`` is untouched.
        """

        widened = PINNED_DYNAMIC_IMPORT_SITES + (
            (
                "packages/core/src/config/plugin/extension.ts",
                44,
                "          const mod = yield* Effect.promise(() => import(spec))",
                ("key:extensions",),
                "entry.info.extensions[].package",
            ),
        )
        derived = module_specifier_keys(widened)
        self.assertIn("extensions", derived)
        self.assertNotEqual(derived, self.guard_keys())
        with mock.patch.dict(
            globals(), {"PINNED_DYNAMIC_IMPORT_SITES": widened}
        ):
            with self.assertRaises(AssertionError):
                self.test_the_table_matches_the_pinned_provider_keys()

    def test_an_existing_site_gaining_a_second_key_fails(self):
        """The other ADDED shape: an import already traced grows a new source.

        This is how ``providers`` would have arrived had ``dynamic.ts`` not
        already existed — a site whose specifier starts being fed from one more
        place.  Resolving origins per site, rather than counting sites, is what
        makes that visible.
        """

        widened = tuple(
            (path, line, text, origins + ("key:tools",), note)
            if path.endswith("tool/registry.ts")
            else (path, line, text, origins, note)
            for path, line, text, origins, note in PINNED_DYNAMIC_IMPORT_SITES
        )
        self.assertIn("tools", module_specifier_keys(widened))
        with mock.patch.dict(
            globals(), {"PINNED_DYNAMIC_IMPORT_SITES": widened}
        ):
            with self.assertRaises(AssertionError):
                self.test_the_table_matches_the_pinned_provider_keys()

    def test_dropping_a_key_from_the_guard_fails(self):
        """The deletion direction, for symmetry with rounds 6 and 7."""

        trimmed = tuple(
            execution
            for execution in oc.EXECUTION_KEYS
            if execution.key != "providers"
        )
        with mock.patch.object(oc, "EXECUTION_KEYS", trimmed):
            with self.assertRaises(AssertionError):
                self.test_the_table_matches_the_pinned_provider_keys()

    def test_glob_and_file_origins_are_not_swept_into_the_key_set(self):
        """The classifier must not turn D8's and D12's surfaces into keys."""

        derived = module_specifier_keys(PINNED_DYNAMIC_IMPORT_SITES)
        self.assertEqual({"plugin", "plugins", "provider", "providers"}, derived)
        origins = {
            origin
            for _p, _l, _t, items, _n in PINNED_DYNAMIC_IMPORT_SITES
            for origin in items
        }
        self.assertIn("glob:{tool,tools}/*.{js,ts}", origins)
        self.assertIn("file:global legacy toml config", origins)

    def test_every_derived_key_is_refused_by_the_scan(self):
        """The derivation is load-bearing: each key must actually refuse.

        A key that is enumerated but not applied would pass the equality
        assertion above while leaving the hole open, so the two are bound
        together here rather than trusted to stay in step.
        """

        realistic = {
            "plugin": ["./declared.js"],
            "plugins": [{"package": "./declared.js"}],
            "provider": {"rogue": {"npm": "file:///tmp/declared.js"}},
            "providers": {
                "rogue": {"api": {"type": "aisdk", "package": "file:///x.js"}}
            },
        }
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        for execution in oc.EXECUTION_KEYS:
            with self.subTest(key=execution.key):
                self.assertIn(
                    execution.key,
                    realistic,
                    "a newly derived key needs a realistic payload here",
                )
                payload = {execution.key: realistic[execution.key]}
                target = root / "opencode.json"
                target.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(oc.GuardError) as caught:
                    oc.migration_scan(
                        root,
                        xdg_config_home=root / "xdg",
                        test_home=root / "home",
                        environment={},
                    )
                message = str(caught.exception)
                self.assertIn("execution key", message)
                self.assertIn(f"#{execution.key}", message)
                self.assertNotIn("declared.js", message)
                target.unlink()


@unittest.skipUnless(
    os.environ.get(PINNED_SOURCE_ENV),
    f"set {PINNED_SOURCE_ENV} to an extracted v1.18.12 tree",
)
class PinnedSourceExecutionKeyTest(unittest.TestCase):
    """Check the import transcript against the real pinned tree, when supplied.

    Same opt-in switch as :class:`PinnedSourceCompletenessTest`, so one command
    at a version bump re-runs all three derivations — config files, directory
    globs, and execution keys — against a real extracted tree.  See
    ``docs/guides/model-routing.md`` for the procedure that names it.
    """

    def setUp(self):
        self.tree = Path(os.environ[PINNED_SOURCE_ENV])
        if not (self.tree / "packages/opencode/src").is_dir():
            self.skipTest(f"{self.tree} is not an opencode source tree")

    def source_files(self):
        for package in ("core", "opencode"):
            yield from sorted((self.tree / "packages" / package / "src").rglob("*.ts"))

    def test_every_transcribed_line_matches_the_pinned_source(self):
        for path, line, text, _origins, _note in PINNED_DYNAMIC_IMPORT_SITES:
            with self.subTest(path=path, line=line):
                actual = (self.tree / path).read_text(encoding="utf-8").splitlines()
                self.assertEqual(text, actual[line - 1])

    def test_pinned_source_contains_no_undocumented_dynamic_import_sites(self):
        """The ADDED direction against the tree itself.

        Every ``import()`` whose specifier is not a string literal is a place a
        configuration value could reach.  A provider release that adds one fails
        here and forces a human to resolve where its specifier comes from,
        rather than letting an unreadable specifier pass unseen.  Literal
        specifiers are excluded because no configuration can redirect them.
        """

        transcribed = {
            (path, line) for path, line, _t, _o, _n in PINNED_DYNAMIC_IMPORT_SITES
        }
        found = set()
        for source in self.source_files():
            relative = str(source.relative_to(self.tree))
            for number, text in enumerate(
                source.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if text.lstrip().startswith("//"):
                    continue
                call = _IMPORT_CALL.search(text)
                if not call:
                    continue
                if _IMPORT_LITERAL.match(text[call.end() :]):
                    continue
                found.add((relative, number))
        self.assertEqual(set(), found - transcribed)
        self.assertEqual(set(), transcribed - found)

    def test_every_execution_key_is_a_top_level_schema_field(self):
        """A key nobody can spell is not a key; a renamed one must fail here."""

        self.assertEqual(
            {execution.key for execution in oc.EXECUTION_KEYS},
            set(PINNED_EXECUTION_KEY_SCHEMA),
        )
        for key, (path, line) in sorted(PINNED_EXECUTION_KEY_SCHEMA.items()):
            with self.subTest(key=key):
                actual = (self.tree / path).read_text(encoding="utf-8").splitlines()
                self.assertTrue(
                    actual[line - 1].startswith(f"  {key}:"),
                    f"{path}:{line} no longer declares a top-level {key!r}",
                )


# ---------------------------------------------------------------------------
# D12 config discovery against the pinned tree — the third derivation's own
# tree check, added in round 11 to close the asymmetry round 10 disclosed
# ---------------------------------------------------------------------------


#: Every call site in ``packages/{core,opencode}/src`` at the pinned ref that
#: reads a configuration document off disk, transcribed verbatim, with what it
#: reads resolved.
#:
#: **The closure argument.** A configuration document can only influence the
#: provider by being read, and at v1.18.12 every such read goes through one of
#: five named helpers: ``loadFile`` (the v1 reader at
#: ``opencode/src/config/config.ts:238-244`` and the v2 reader at
#: ``core/src/config.ts:147-163``), ``readConfigFile`` (the text layer under
#: it), ``loadDirectory`` (the v2 expansion of ``names`` over a directory),
#: ``fileInDirectory`` (the ``<dir>/<name>.{json,jsonc}`` pair builder), and
#: ``readManagedPreferences`` (the MDM plist, which bypasses ``loadFile``
#: entirely and is why an enumeration of ``loadFile`` alone would be short).
#: Enumerate the call sites and the discovery set falls out, the same way the
#: ``import()`` enumeration made the execution-key set fall out.  The one read
#: that is *not* a call to those helpers — the legacy TOML ``import()`` — is
#: enumerated by :data:`PINNED_DYNAMIC_IMPORT_SITES` instead and cross-checked
#: by :meth:`PinnedSourceConfigDiscoveryTest.test_the_legacy_toml_source_is_derived_from_the_tree`.
#:
#: ``resolutions`` is a tuple, because one site can serve more than one family
#: — ``config.ts:429`` alone covers the project ``.opencode`` walk, the home-dot
#: ``.opencode``, and ``OPENCODE_CONFIG_DIR``.  Each entry is one of:
#:
#: * ``"source:<label>"`` — this read is a :data:`oc.CONFIG_DISCOVERY_SOURCES`
#:   entry, named by its label.  These are D12's surface.
#: * ``"helper"`` — the definition of one of the readers, not a read site.
#: * ``"env:<FLAG>"`` — the path comes from an environment flag, so it is not
#:   expressible as a derived path.  Every flag named here is in
#:   :data:`oc.CONFIG_SOURCE_FORBIDDEN_ENV` and refuses on presence.
#: * ``"write"`` — the ``Config.update`` path, which reads a file this table
#:   already covers in order to rewrite it.
#: * ``"subcommand"`` — reachable only from an ``opencode`` subcommand the
#:   guard's fixed ``LAUNCH_ARGV`` never invokes.
#: * ``"unrelated"`` — the same identifier in a different subsystem.
#:
#: There is no ``"document:tui"`` resolution any more.  Round 11 used one to
#: record the TUI document as found-but-unscanned; round 12 established it is
#: an executable surface and put its four families in
#: :data:`oc.CONFIG_DISCOVERY_SOURCES`, so those sites now resolve to
#: ``source:`` labels like every other read.
PINNED_CONFIG_READ_SITES = (
    (
        "packages/core/src/config/plugin/command.ts",
        24,
        "          return loadDirectory(fs, entry.path).pipe(",
        ("unrelated",),
        "loads command markdown from a command directory, not a config document",
    ),
    (
        "packages/core/src/config/plugin/command.ts",
        52,
        "function loadDirectory(fs: FSUtil.Interface, directory: string) {",
        ("unrelated",),
        "the definition of that same command-directory reader",
    ),
    (
        "packages/core/src/config.ts",
        166,
        "        ...(yield* Effect.forEach(names, (file) => "
        "loadFile(path.join(directory, file))).pipe(",
        (
            "source:global config root",
            "source:ancestor project config",
            "source:ancestor .opencode config",
        ),
        "v2 loadDirectory over names = [\"opencode.json\", \"opencode.jsonc\"] "
        "at :140, applied to global.config, to the ancestor walk's direct "
        "files, and to every discovered .opencode (:173-190)",
    ),
    (
        "packages/opencode/src/cli/cmd/plug.ts",
        60,
        "  files: (dir, name) => ConfigPaths.fileInDirectory(dir, name),",
        ("subcommand",),
        "the `opencode plug` subcommand; LAUNCH_ARGV is fixed and the argument "
        "guards refuse any other subcommand before spawn",
    ),
    (
        "packages/opencode/src/config/config.ts",
        241,
        "      const text = yield* readConfigFile(filepath)",
        ("helper",),
        "the text layer inside the v1 loadFile",
    ),
    (
        "packages/opencode/src/config/config.ts",
        258,
        "      result = mergeConfig(result, yield* "
        'loadFile(path.join(Global.Path.config, "config.json"), env))',
        ("source:global config root",),
        "the first of the three global basenames",
    ),
    (
        "packages/opencode/src/config/config.ts",
        259,
        "      result = mergeConfig(result, yield* "
        'loadFile(path.join(Global.Path.config, "opencode.json"), env))',
        ("source:global config root",),
        "the second",
    ),
    (
        "packages/opencode/src/config/config.ts",
        260,
        "      result = mergeConfig(result, yield* "
        'loadFile(path.join(Global.Path.config, "opencode.jsonc"), env))',
        ("source:global config root",),
        "the third",
    ),
    (
        "packages/opencode/src/config/config.ts",
        402,
        "          yield* merge(Flag.OPENCODE_CONFIG, yield* "
        "loadFile(Flag.OPENCODE_CONFIG, authEnv))",
        ("env:OPENCODE_CONFIG",),
        "an arbitrary absolute path; no derivation can express it, so the guard "
        "refuses the variable's presence instead",
    ),
    (
        "packages/opencode/src/config/config.ts",
        408,
        "            yield* merge(file, yield* loadFile(file, authEnv), "
        '"local")',
        ("source:ancestor project config",),
        "ConfigPaths.files(\"opencode\", ...) — the cwd-to-worktree walk",
    ),
    (
        "packages/opencode/src/config/config.ts",
        429,
        "              yield* merge(source, yield* loadFile(source, authEnv))",
        (
            "source:ancestor .opencode config",
            "source:home-dot .opencode config",
            "env:OPENCODE_CONFIG_DIR",
        ),
        "one site, three families: ConfigPaths.directories yields the project "
        ".opencode walk, the home-dot .opencode, and OPENCODE_CONFIG_DIR, and "
        ":425 keeps whichever end in .opencode or equal that flag",
    ),
    (
        "packages/opencode/src/config/config.ts",
        520,
        '            yield* merge(source, yield* loadFile(source), "global")',
        ("source:system managed config",),
        "over ConfigManaged.managedConfigDir()",
    ),
    (
        "packages/opencode/src/config/config.ts",
        525,
        "        const managed = yield* Effect.promise(() => "
        "ConfigManaged.readManagedPreferences())",
        ("source:macOS managed preferences",),
        "the MDM plist; read through plutil, never through loadFile",
    ),
    (
        "packages/opencode/src/config/config.ts",
        627,
        "      const existing = yield* loadFile(file)",
        ("write",),
        "Config.update reading before rewriting a file already in the table",
    ),
    (
        "packages/opencode/src/config/config.ts",
        639,
        '      const before = (yield* readConfigFile(file)) ?? "{}"',
        ("write",),
        "the same update path, at the text layer",
    ),
    (
        "packages/opencode/src/config/managed.ts",
        43,
        "export async function readManagedPreferences() {",
        ("helper",),
        "the definition of the plist reader",
    ),
    (
        "packages/opencode/src/config/paths.ts",
        43,
        "export function fileInDirectory(dir: string, name: string) {",
        ("helper",),
        "the definition of the <dir>/<name>.{json,jsonc} pair builder",
    ),
    (
        "packages/opencode/src/config/tui-migrate.ts",
        117,
        '    ...ConfigPaths.fileInDirectory(Global.Path.config, "opencode"),',
        ("source:global config root",),
        "TUI migration reads the main config to strip its tui keys; the read "
        "target is already scanned and D12's migration-key refusal is what "
        "keeps this from running at all",
    ),
    (
        "packages/opencode/src/config/tui-migrate.ts",
        121,
        '    files.push(...ConfigPaths.fileInDirectory(dir, "opencode"))',
        ("source:ancestor .opencode config",),
        "the same migration read over the .opencode directories",
    ),
    (
        "packages/opencode/src/config/tui.ts",
        151,
        "      const data = yield* loadFile(file)",
        (
            "source:global tui config",
            "source:ancestor tui config",
            "source:ancestor .opencode tui config",
            "source:home-dot .opencode tui config",
        ),
        "the TUI document's own reader, shared by all four of its roots",
    ),
    (
        "packages/opencode/src/config/tui.ts",
        184,
        "  for (const file of "
        'ConfigPaths.fileInDirectory(Global.Path.config, "tui")) {',
        ("source:global tui config",),
        "tui.json/tui.jsonc in the global config root — the root D10 writes "
        "its own keybind backstop into",
    ),
    (
        "packages/opencode/src/config/tui.ts",
        207,
        '    for (const file of ConfigPaths.fileInDirectory(dir, "tui")) {',
        (
            "source:ancestor .opencode tui config",
            "source:home-dot .opencode tui config",
            "env:OPENCODE_CONFIG_DIR",
        ),
        "tui.json/tui.jsonc in every discovered .opencode directory, plus "
        "OPENCODE_CONFIG_DIR, exactly as config.ts:429 does for the main "
        "document",
    ),
    (
        "packages/opencode/src/plugin/install.ts",
        88,
        "  files: (dir, name) => ConfigPaths.fileInDirectory(dir, name),",
        ("subcommand",),
        "plugin installation, reachable from `opencode plug`, not from launch",
    ),
)

#: **The round-12 determination, pinned to the tree.**
#:
#: Round 11 derived D12's surface from the tree instead of a transcript and
#: found a config-file family the transcript had never named: ``tui.json`` and
#: ``tui.jsonc``.  Round 12 settled the only question that mattered about it —
#: can that document carry a value that becomes a module specifier the provider
#: loads?  It can, and the chain below is why.  The four families are now in
#: :data:`oc.CONFIG_DISCOVERY_SOURCES` with ``document="tui"``.
#:
#: Each entry is ``(citation, must_appear)``.  These are the load-bearing lines
#: of the determination; if a later release drops any of them the finding needs
#: re-deriving, and this fails rather than decaying into a stale comment.
PINNED_TUI_EXECUTION_CHAIN = (
    (
        "packages/tui/src/config/index.tsx",
        "export const PluginSpec = Schema.Union([Schema.String, "
        "Schema.mutable(Schema.Tuple([Schema.String, PluginOptions]))])",
    ),
    (
        "packages/tui/src/config/index.tsx",
        "plugin: Schema.optional(Schema.Array(PluginSpec)),",
    ),
    (
        "packages/opencode/src/config/tui.ts",
        "if (!data.plugin?.length) return",
    ),
    (
        "packages/opencode/src/config/tui.ts",
        "acc.plugin_origins = plugins",
    ),
    (
        "packages/opencode/src/plugin/tui/runtime.ts",
        "const pluginOrigins = config.plugin_origins ?? "
        "(await TuiConfig.pluginOrigins())",
    ),
    (
        "packages/opencode/src/plugin/tui/runtime.ts",
        "const ready = await resolveExternalPlugins(records, () => "
        "TuiConfig.waitForDependencies())",
    ),
    (
        "packages/opencode/src/plugin/tui/runtime.ts",
        "return PluginLoader.loadExternal({",
    ),
    (
        "packages/opencode/src/plugin/loader.ts",
        "mod = await import(row.entry)",
    ),
)

#: The two gates that stand between the TUI document and that importer, carried
#: so nobody re-derives the finding and concludes the guard was already safe.
#:
#: ``runtime.ts:1089`` reduces the origins to ``[]`` under
#: ``Flag.OPENCODE_PURE``, and ``tui.ts:175`` skips the project-ancestor read
#: under ``Flag.OPENCODE_DISABLE_PROJECT_CONFIG``.  The guard sets both.  That
#: is exactly the argument live probe L4 falsified for the main config's
#: ``plugin`` key — which is why D8 and D12 scan project roots redundantly
#: despite D7, and why a provider-honoured flag is never accepted as the
#: control.  A third consumer has no pure gate at all: ``tui.ts:224,236-247``
#: runs ``npm.install`` in every discovered ``.opencode`` directory whenever the
#: array is non-empty.  Exploitability under the shipped guard was neither
#: established nor refuted — no live probe was run, scope forbade it — and the
#: refusal is retained as fail-closed regardless, exactly as the plan records
#: for ``provider``/``providers``.
PINNED_TUI_GATES = (
    ("packages/opencode/src/plugin/tui/runtime.ts", "Flag.OPENCODE_PURE ? [] : pluginOrigins"),
    (
        "packages/opencode/src/config/tui.ts",
        "Flag.OPENCODE_DISABLE_PROJECT_CONFIG ? [] : yield* ConfigPaths.files",
    ),
)

_CONFIG_READ_CALL = re.compile(
    r"(?<![\w$])(?:\w+\.)?"
    r"(loadFile|readConfigFile|loadDirectory|fileInDirectory"
    r"|readManagedPreferences)\s*\("
)


def derived_document_stems(tree):
    """Every ``name`` the provider passes to the ``<name>.{json,jsonc}`` builders.

    ``ConfigPaths.fileInDirectory(dir, name)`` and ``ConfigPaths.files(name,
    ...)`` are parameterised on the document stem, so the *set of documents*
    the provider discovers is exactly the set of literals reaching them.  At
    v1.18.12 that is ``opencode`` and ``tui`` — and it was reading this from
    the tree in round 11, rather than trusting a transcript, that surfaced the
    TUI document at all.  A release that adds a third document changes this set
    with nobody editing this file.
    """

    stems = set()
    for package in ("core", "opencode"):
        base = tree / "packages" / package / "src"
        for source in [*base.rglob("*.ts"), *base.rglob("*.tsx")]:
            text = source.read_text(encoding="utf-8")
            stems.update(
                re.findall(r'fileInDirectory\([^,]+,\s*"([^"]+)"\)', text)
            )
            stems.update(re.findall(r'ConfigPaths\.files\(\s*"([^"]+)"', text))
    return stems


def derived_config_basenames(tree):
    """Re-derive the discovered basenames from the pinned tree's own literals.

    Not a transcript comparison: every name below is pulled out of the provider
    source at read time, so a release that renames or adds one changes this set
    without anybody editing this file.
    """

    names = set()

    paths_source = (tree / "packages/opencode/src/config/paths.ts").read_text(
        encoding="utf-8"
    )
    builder = re.search(
        r"export function fileInDirectory\(.*?\n}", paths_source, re.DOTALL
    )
    assert builder, "the <dir>/<name>.{json,jsonc} builder moved"
    extensions = set(re.findall(r"\$\{name\}\.(\w+)", builder.group(0)))
    assert extensions, "fileInDirectory no longer interpolates literal extensions"
    for stem in derived_document_stems(tree):
        names.update(f"{stem}.{extension}" for extension in extensions)

    core = (tree / "packages/core/src/config.ts").read_text(encoding="utf-8")
    v2 = re.search(r"const names = \[([^\]]*)\]", core)
    assert v2, "core/src/config.ts no longer declares a literal names array"
    names.update(re.findall(r'"([^"]+)"', v2.group(1)))

    v1 = (tree / "packages/opencode/src/config/config.ts").read_text(
        encoding="utf-8"
    )
    names.update(
        re.findall(r'loadFile\(path\.join\(Global\.Path\.config, "([^"]+)"\)', v1)
    )
    legacy = re.search(r'const legacy = path\.join\(Global\.Path\.config, "([^"]+)"\)', v1)
    assert legacy, "the legacy TOML config path is no longer a literal join"
    names.add(legacy.group(1))
    for literal in re.findall(r'for \(const file of \[([^\]]*)\]\)', v1):
        names.update(re.findall(r'"([^"]+)"', literal))

    targets = re.search(r"targets: \[([^\]]*)\]", paths_source)
    assert targets, "ConfigPaths.files no longer declares a literal target list"
    walk_extensions = re.findall(r"\$\{name\}\.(\w+)", targets.group(1))
    assert walk_extensions, "the ancestor walk no longer targets literal extensions"
    for stem in derived_document_stems(tree):
        names.update(f"{stem}.{extension}" for extension in walk_extensions)

    managed = (tree / "packages/opencode/src/config/managed.ts").read_text(
        encoding="utf-8"
    )
    domain = re.search(r'MANAGED_PLIST_DOMAIN = "([^"]+)"', managed)
    assert domain, "the managed plist domain is no longer a literal"
    assert "${MANAGED_PLIST_DOMAIN}.plist" in managed
    names.add(f"{domain.group(1)}.plist")

    return names


@unittest.skipUnless(
    os.environ.get(PINNED_SOURCE_ENV),
    f"set {PINNED_SOURCE_ENV} to an extracted v{oc.OPENCODE_VERSION} tree",
)
class PinnedSourceConfigDiscoveryTest(unittest.TestCase):
    """Check D12's config-discovery set against the real pinned tree.

    Round 10 shipped a receipt digesting all three derived tables and disclosed
    that only two of them had a class of this shape: ``EXECUTABLE_SCANS`` and
    ``EXECUTION_KEYS`` each read the tree, while ``CONFIG_DISCOVERY_SOURCES``
    was verified against a hand-written transcript only.  A receipt asserting
    uniform verification over a non-uniform verification is a control implying
    more than it delivers, which is the failure this project keeps paying for.
    This class closes it, and the disclosure is what created the round.
    """

    def setUp(self):
        self.tree = Path(os.environ[PINNED_SOURCE_ENV])
        if not (self.tree / "packages/opencode/src").is_dir():
            self.skipTest(f"{self.tree} is not an opencode source tree")

    def source_files(self):
        for package in ("core", "opencode"):
            base = self.tree / "packages" / package / "src"
            yield from sorted(
                [*base.rglob("*.ts"), *base.rglob("*.tsx")]
            )

    def read_sites(self):
        found = set()
        for source in self.source_files():
            relative = str(source.relative_to(self.tree))
            for number, text in enumerate(
                source.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if text.lstrip().startswith("//"):
                    continue
                if _CONFIG_READ_CALL.search(text):
                    found.add((relative, number))
        return found

    def test_every_transcribed_line_matches_the_pinned_source(self):
        for path, line, text, _resolutions, _note in PINNED_CONFIG_READ_SITES:
            with self.subTest(path=path, line=line):
                actual = (self.tree / path).read_text(encoding="utf-8").splitlines()
                self.assertEqual(text, actual[line - 1])

    def test_pinned_source_contains_no_undocumented_config_read_sites(self):
        """The ADDED direction, against the tree itself.

        A release that gains a configuration read — a new file family, a new
        root, a new document — gains a call site, and the site fails here until
        a human resolves what it reads.  This is the check whose absence let
        the TUI document go unnamed through five rounds.
        """

        transcribed = {
            (path, line) for path, line, _t, _r, _n in PINNED_CONFIG_READ_SITES
        }
        found = self.read_sites()
        self.assertEqual(set(), found - transcribed)
        self.assertEqual(set(), transcribed - found)

    def test_every_documented_source_is_reached_by_a_transcribed_site(self):
        """No entry in the guard's table may be unsupported by a real read."""

        resolved = {
            resolution[len("source:") :]
            for _p, _l, _t, resolutions, _n in PINNED_CONFIG_READ_SITES
            for resolution in resolutions
            if resolution.startswith("source:")
        }
        labels = {source.label for source in oc.CONFIG_DISCOVERY_SOURCES}
        # The legacy TOML source is read by import(), not by these helpers, and
        # is carried by PINNED_DYNAMIC_IMPORT_SITES instead.
        self.assertEqual(set(), resolved - labels)
        self.assertEqual({"global legacy toml config"}, labels - resolved)

    def test_every_env_resolution_names_a_key_the_guard_refuses(self):
        for _p, _l, _t, resolutions, _n in PINNED_CONFIG_READ_SITES:
            for resolution in resolutions:
                if not resolution.startswith("env:"):
                    continue
                with self.subTest(resolution=resolution):
                    self.assertIn(
                        resolution[len("env:") :], oc.CONFIG_SOURCE_FORBIDDEN_ENV
                    )

    def test_the_discovered_basenames_match_the_pinned_tree_directly(self):
        """Derive the filenames from the tree, ignoring the transcript."""

        self.assertEqual(
            {
                name
                for source in oc.CONFIG_DISCOVERY_SOURCES
                for name in source.filenames
            },
            derived_config_basenames(self.tree),
        )

    def test_the_managed_roots_match_the_pinned_tree_directly(self):
        """The two roots a unit test cannot reach, re-derived from source."""

        managed = (self.tree / "packages/opencode/src/config/managed.ts").read_text(
            encoding="utf-8"
        )
        system = re.search(
            r"function systemManagedConfigDir\(\).*?\n}", managed, re.DOTALL
        )
        self.assertIsNotNone(system, "systemManagedConfigDir no longer exists")
        body = system.group(0)

        with mock.patch.object(sys, "platform", "darwin"):
            self.assertIn(f'"{oc.managed_config_dir()}"', body)
        with mock.patch.object(sys, "platform", "linux"):
            self.assertIn(f'"{oc.managed_config_dir()}"', body)

        preferences = re.search(
            r"const paths = \[(.*?)\]", managed, re.DOTALL
        )
        self.assertIsNotNone(preferences, "the managed-preferences list moved")
        with mock.patch.object(sys, "platform", "darwin"):
            for directory in oc._managed_preferences_dirs():
                with self.subTest(directory=directory):
                    self.assertIn('"/Library/Managed Preferences"', preferences.group(1))
                    self.assertTrue(str(directory).startswith("/Library/Managed Preferences"))

    def test_the_legacy_toml_source_is_derived_from_the_tree(self):
        """The one read that is an import(), cross-checked against its own table."""

        v1 = (self.tree / "packages/opencode/src/config/config.ts").read_text(
            encoding="utf-8"
        )
        self.assertIn("import(pathToFileURL(legacy).href", v1)
        self.assertIn(
            "file:global legacy toml config",
            {
                origin
                for _p, _l, _t, origins, _n in PINNED_DYNAMIC_IMPORT_SITES
                for origin in origins
            },
        )

    def test_the_tui_execution_chain_still_holds_on_this_tree(self):
        """Round 12's determination, re-checked line by line against the tree.

        The TUI families are in the guard's table because this chain exists.
        If a release breaks a link, the finding needs re-deriving and possibly
        retiring — so it fails here rather than decaying into a stale comment
        that keeps four sources in the scan set for a reason that stopped being
        true.
        """

        for relative, expected in PINNED_TUI_EXECUTION_CHAIN:
            with self.subTest(path=relative, line=expected[:48]):
                text = (self.tree / relative).read_text(encoding="utf-8")
                self.assertIn(expected, text)

    def test_the_tui_gates_are_the_ones_the_determination_names(self):
        """The gates exist; they are recorded as gates, not as the control."""

        for relative, expected in PINNED_TUI_GATES:
            with self.subTest(path=relative):
                text = (self.tree / relative).read_text(encoding="utf-8")
                self.assertIn(expected, text)

    def test_the_tui_npm_install_path_has_no_pure_gate(self):
        """The consumer `--pure` does not reach, pinned so it stays visible."""

        tui = (self.tree / "packages/opencode/src/config/tui.ts").read_text(
            encoding="utf-8"
        )
        self.assertIn("dirs: result.plugin?.length ? dirs : []", tui)
        install = re.search(r"const deps = yield\* Effect\.forEach\(\s*data\.dirs.*?\)", tui, re.DOTALL)
        self.assertIsNotNone(install, "the tui npm.install fan-out moved")
        self.assertNotIn("OPENCODE_PURE", install.group(0))

    def test_every_tui_source_is_gated_on_execution_keys_only(self):
        """The trap, asserted on the table rather than only on behaviour."""

        tui_sources = [
            source
            for source in oc.CONFIG_DISCOVERY_SOURCES
            if source.document == "tui"
        ]
        self.assertEqual(4, len(tui_sources))
        for source in tui_sources:
            with self.subTest(label=source.label):
                self.assertEqual(("tui.json", "tui.jsonc"), source.filenames)
                self.assertEqual("jsonc", source.parse)


@unittest.skipUnless(
    os.environ.get(PINNED_SOURCE_ENV),
    f"set {PINNED_SOURCE_ENV} to an extracted v{oc.OPENCODE_VERSION} tree",
)
class PinnedSourceReceiptTest(unittest.TestCase):
    """Write the receipt that binds ``OPENCODE_VERSION`` to its derived tables.

    The two classes above are the actual verification; this one records that it
    happened, so an always-on contract test can refuse a bump that skipped it.
    The receipt is `tests/fixtures/opencode-pinned-surface.json` and
    ``tests/opencode_surface.py`` states plainly what it does and does not
    guarantee — chiefly that a maintainer can hand-edit it, which makes this a
    forcing function rather than a proof.

    Writing is conditional: the verification classes are re-run against this
    tree first and the receipt is not written if any of them fails.  Otherwise a
    red pinned-source run would still leave a green-looking receipt behind,
    which is the exact shape of failure this whole mechanism exists to prevent.
    """

    def setUp(self):
        self.tree = Path(os.environ[PINNED_SOURCE_ENV])
        if not (self.tree / "packages/opencode/src").is_dir():
            self.skipTest(f"{self.tree} is not an opencode source tree")

    def test_the_supplied_tree_self_identifies_as_the_pinned_version(self):
        """A receipt written from the wrong tree would be worse than none."""

        manifest = json.loads(
            (self.tree / "packages/opencode/package.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            oc.OPENCODE_VERSION,
            manifest.get("version"),
            f"{self.tree} is not a v{oc.OPENCODE_VERSION} tree; the receipt "
            "must be written from the release the pin names",
        )

    def test_the_receipt_is_regenerated_from_a_verified_tree(self):
        loader = unittest.TestLoader()
        suite = unittest.TestSuite(
            loader.loadTestsFromTestCase(case)
            for case in (
                PinnedSourceCompletenessTest,
                PinnedSourceConfigDiscoveryTest,
                PinnedSourceExecutionKeyTest,
            )
        )
        buffer = io.StringIO()
        result = unittest.TextTestRunner(stream=buffer, verbosity=0).run(suite)
        self.assertTrue(
            result.wasSuccessful(),
            "refusing to write the pinned-surface receipt: the derivations do "
            "not match this tree, so the guard is what has to change. See the "
            "failures reported by PinnedSourceCompletenessTest and "
            "PinnedSourceExecutionKeyTest.",
        )

        self.test_the_supplied_tree_self_identifies_as_the_pinned_version()
        document = opencode_surface.write_fixture()
        self.assertEqual(oc.OPENCODE_VERSION, document["opencode_version"])
        self.assertEqual(opencode_surface.surface_digest(), document["surface_digest"])


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


#: The documented, source-derived D12 enumeration, restated independently of
#: :data:`oc.CONFIG_DISCOVERY_SOURCES` as
#: ``(label, root, filenames, parse, document)``.
#: This is the drift anchor plan version 11 requires: the module's table is
#: asserted to equal this literal, and the concrete scan set is asserted to
#: expand from exactly these entries.  A provider bump that adds, moves, or
#: renames a discovery path fails here rather than silently opening a hole.
DOCUMENTED_CONFIG_SOURCES = (
    (
        "global config root",
        "global-config",
        ("config.json", "opencode.json", "opencode.jsonc"),
        "jsonc",
        "main",
    ),
    ("global legacy toml config", "global-config", ("config",), "opaque", "main"),
    (
        "ancestor project config",
        "ancestor",
        ("opencode.json", "opencode.jsonc"),
        "jsonc",
        "main",
    ),
    (
        "ancestor .opencode config",
        "ancestor-opencode",
        ("opencode.json", "opencode.jsonc"),
        "jsonc",
        "main",
    ),
    (
        "home-dot .opencode config",
        "home-opencode",
        ("opencode.json", "opencode.jsonc"),
        "jsonc",
        "main",
    ),
    (
        "system managed config",
        "managed",
        ("opencode.json", "opencode.jsonc"),
        "jsonc",
        "main",
    ),
    (
        "macOS managed preferences",
        "managed-preferences",
        ("ai.opencode.managed.plist",),
        "opaque",
        "main",
    ),
    # The TUI document, established as an executable surface in round 12.
    # ``document`` is "tui", which is what keeps MIGRATION_KEYS off it and so
    # keeps D10's own keybind backstop from refusing every launch.
    ("global tui config", "global-config", ("tui.json", "tui.jsonc"), "jsonc", "tui"),
    ("ancestor tui config", "ancestor", ("tui.json", "tui.jsonc"), "jsonc", "tui"),
    (
        "ancestor .opencode tui config",
        "ancestor-opencode",
        ("tui.json", "tui.jsonc"),
        "jsonc",
        "tui",
    ),
    (
        "home-dot .opencode tui config",
        "home-opencode",
        ("tui.json", "tui.jsonc"),
        "jsonc",
        "tui",
    ),
)


class ConfigDiscoveryEnumerationTest(_WorktreeTestCase):
    """D12's scan set must equal the documented source-derived enumeration."""

    def roots(self):
        xdg = self.scratch / "xdg-config"
        home = self.scratch / "opencode-home"
        for directory in (xdg, home):
            directory.mkdir(parents=True, exist_ok=True)
        return xdg, home

    def scan_paths(self, cwd=None):
        xdg, home = self.roots()
        return oc.config_scan_paths(
            cwd=self.worktree if cwd is None else cwd,
            xdg_config_home=xdg,
            test_home=home,
            environment={},
        )

    def test_the_table_matches_the_documented_enumeration(self):
        actual = tuple(
            (
                source.label,
                source.root,
                source.filenames,
                source.parse,
                source.document,
            )
            for source in oc.CONFIG_DISCOVERY_SOURCES
        )
        self.assertEqual(DOCUMENTED_CONFIG_SOURCES, actual)

    def test_every_entry_carries_a_pinned_source_citation(self):
        for source in oc.CONFIG_DISCOVERY_SOURCES:
            with self.subTest(label=source.label):
                self.assertRegex(source.citation, r"packages/\S+\.ts:\d")

    def test_the_scanned_set_equals_the_expansion_of_the_documented_set(self):
        xdg, home = self.roots()
        current = self.worktree.resolve()
        ancestors = [current, *current.parents]
        expected: list[Path] = []
        for _label, root, filenames, _parse, _document in DOCUMENTED_CONFIG_SOURCES:
            if root == "global-config":
                directories = [xdg / "opencode"]
            elif root == "home-opencode":
                directories = [home / ".opencode"]
            elif root == "managed":
                directories = [oc.managed_config_dir()]
            elif root == "managed-preferences":
                base = Path("/Library/Managed Preferences")
                directories = (
                    [base / getpass.getuser(), base] if sys.platform == "darwin" else []
                )
            elif root == "ancestor":
                directories = list(ancestors)
            elif root == "ancestor-opencode":
                directories = [ancestor / ".opencode" for ancestor in ancestors]
            else:  # pragma: no cover - the table above is closed
                self.fail(f"undocumented root family: {root}")
            for directory in directories:
                for name in filenames:
                    candidate = directory / name
                    if candidate not in expected:
                        expected.append(candidate)
        self.assertEqual(expected, [path for path, _ in self.scan_paths()])

    def test_dropping_a_documented_path_is_detectable(self):
        """The drift test bites: remove an entry and the scan set shrinks.

        This is the property that makes the next vector impossible to introduce
        silently.  Patching the table to omit the nested ``.opencode`` family
        must both change the scanned set and make the equality assertion fail.
        """

        full = {path for path, _ in self.scan_paths()}
        nested = self.worktree / ".opencode" / "opencode.json"
        self.assertIn(nested, full)

        trimmed = tuple(
            source
            for source in oc.CONFIG_DISCOVERY_SOURCES
            if source.root != "ancestor-opencode"
        )
        with mock.patch.object(oc, "CONFIG_DISCOVERY_SOURCES", trimmed):
            reduced = {path for path, _ in self.scan_paths()}
            self.assertNotIn(nested, reduced)
            with self.assertRaises(AssertionError):
                self.test_the_table_matches_the_documented_enumeration()

    def test_an_unknown_root_family_raises_rather_than_scanning_nothing(self):
        rogue = oc.ConfigSource(
            label="rogue",
            root="not-a-root",
            filenames=("opencode.json",),
            parse="jsonc",
            citation="packages/core/src/config.ts:1",
        )
        with mock.patch.object(oc, "CONFIG_DISCOVERY_SOURCES", (rogue,)):
            with self.assertRaisesRegex(oc.GuardError, "unknown OpenCode config"):
                self.scan_paths()

    def test_each_forbidden_config_env_key_refuses(self):
        xdg, home = self.roots()
        for key in oc.CONFIG_SOURCE_FORBIDDEN_ENV:
            with self.subTest(key=key):
                with self.assertRaisesRegex(oc.GuardError, key):
                    oc.config_scan_paths(
                        cwd=self.worktree,
                        xdg_config_home=xdg,
                        test_home=home,
                        environment={key: "/somewhere"},
                    )


class MigrationScanTest(_WorktreeTestCase):
    def roots(self):
        xdg = self.scratch / "xdg-config"
        home = self.scratch / "opencode-home"
        for directory in (xdg, home):
            directory.mkdir(parents=True, exist_ok=True)
        return xdg, home

    def scan(self, cwd=None):
        xdg, home = self.roots()
        return oc.migration_scan(
            self.worktree if cwd is None else cwd,
            xdg_config_home=xdg,
            test_home=home,
            environment={},
        )

    def test_a_clean_tree_passes(self):
        self.scan()

    def test_each_migration_key_refuses_by_key_path(self):
        for name in ("opencode.json", "opencode.jsonc"):
            for key in oc.MIGRATION_KEYS:
                with self.subTest(name=name, key=key):
                    path = self.worktree / name
                    path.write_text(json.dumps({key: {}}), encoding="utf-8")
                    try:
                        with self.assertRaises(oc.GuardError) as caught:
                            self.scan()
                        self.assertIn(f"#{key}", str(caught.exception))
                    finally:
                        path.unlink()

    def test_a_benign_config_above_the_worktree_is_still_scanned(self):
        path = self.root / "opencode.json"
        path.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
        with self.assertRaisesRegex(oc.GuardError, "migration key"):
            self.scan()

    def test_comments_are_stripped_before_parsing_jsonc(self):
        path = self.worktree / "opencode.jsonc"
        path.write_text(
            '// leading\n{"tui": {} /* trailing */}\n', encoding="utf-8"
        )
        with self.assertRaisesRegex(oc.GuardError, "migration key"):
            self.scan()

    def test_unparseable_config_refuses(self):
        (self.worktree / "opencode.json").write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(oc.GuardError, "cannot be parsed"):
            self.scan()

    def test_a_declared_plugin_at_cwd_refuses_by_key_path(self):
        for name in ("opencode.json", "opencode.jsonc"):
            for execution in oc.EXECUTION_KEYS:
                key = execution.key
                with self.subTest(name=name, key=key):
                    path = self.worktree / name
                    path.write_text(
                        json.dumps({key: ["./declared.js"]}), encoding="utf-8"
                    )
                    try:
                        with self.assertRaises(oc.GuardError) as caught:
                            self.scan()
                        message = str(caught.exception)
                        self.assertIn("execution key", message)
                        self.assertIn(f"#{key}", message)
                        # Key-path only: the declared target never leaks.
                        self.assertNotIn("declared.js", message)
                    finally:
                        path.unlink()

    def test_a_declared_plugin_above_the_worktree_refuses(self):
        path = self.root / "opencode.json"
        path.write_text(json.dumps({"plugin": ["./declared.js"]}), encoding="utf-8")
        with self.assertRaisesRegex(oc.GuardError, "execution key"):
            self.scan()

    def test_a_nested_opencode_config_refuses_at_cwd_and_at_an_ancestor(self):
        """The fourth vector: ``.opencode/opencode.json`` declaring a plugin.

        Both filenames, both spellings, at the worktree and above it.  Plugin
        paths declared in a nested config resolve relative to that config's own
        directory, which is why this location is reachable at all and why the
        earlier ancestor-only walk never saw it.
        """

        for directory in (self.worktree, self.root):
            for name in ("opencode.json", "opencode.jsonc"):
                for execution in oc.EXECUTION_KEYS:
                    key = execution.key
                    with self.subTest(directory=directory, name=name, key=key):
                        nested = directory / ".opencode"
                        nested.mkdir(parents=True, exist_ok=True)
                        path = nested / name
                        path.write_text(
                            json.dumps({key: ["./declared.js"]}), encoding="utf-8"
                        )
                        try:
                            with self.assertRaises(oc.GuardError) as caught:
                                self.scan()
                            message = str(caught.exception)
                            self.assertIn("execution key", message)
                            self.assertIn(f"#{key}", message)
                            self.assertIn(str(path), message)
                            self.assertNotIn("declared.js", message)
                        finally:
                            path.unlink()

    def test_a_nested_opencode_migration_key_refuses(self):
        nested = self.worktree / ".opencode"
        nested.mkdir(parents=True, exist_ok=True)
        path = nested / "opencode.jsonc"
        path.write_text('{"keybinds": {}}', encoding="utf-8")
        with self.assertRaisesRegex(oc.GuardError, "migration key"):
            self.scan()

    def test_the_owned_global_root_is_scanned(self):
        xdg, _home = self.roots()
        target = xdg / "opencode"
        target.mkdir(parents=True, exist_ok=True)
        (target / "config.json").write_text(
            json.dumps({"plugin": ["./declared.js"]}), encoding="utf-8"
        )
        with self.assertRaisesRegex(oc.GuardError, "execution key"):
            self.scan()

    def test_the_home_dot_root_is_scanned(self):
        _xdg, home = self.roots()
        target = home / ".opencode"
        target.mkdir(parents=True, exist_ok=True)
        (target / "opencode.json").write_text(
            json.dumps({"tui": {}}), encoding="utf-8"
        )
        with self.assertRaisesRegex(oc.GuardError, "migration key"):
            self.scan()

    def test_an_uninspectable_source_refuses_on_mere_existence(self):
        xdg, _home = self.roots()
        target = xdg / "opencode"
        target.mkdir(parents=True, exist_ok=True)
        (target / "config").write_text("model = 'x'\n", encoding="utf-8")
        with self.assertRaisesRegex(oc.GuardError, "cannot be inspected"):
            self.scan()

    def test_the_system_managed_root_is_scanned(self):
        """The `managed` root is a real system path, so a fixture stands in.

        `/Library/Application Support/opencode` (or `/etc/opencode`) is neither
        owned nor writable by a unit test, so `managed_config_dir` is injected
        the way `xdg_config_home`/`test_home` already are for the owned roots.
        This source parses as JSONC, so its refusal is by key rather than by
        mere existence; what is pinned here is that the root is scanned at all
        and that both its filenames reach the key gates.
        """

        managed = self.scratch / "managed"
        managed.mkdir(parents=True, exist_ok=True)
        with mock.patch.object(oc, "managed_config_dir", lambda: managed):
            for name in ("opencode.json", "opencode.jsonc"):
                for payload, expected in (
                    ({"tui": {}}, "migration key"),
                    ({"plugin": ["./declared.js"]}, "execution key"),
                ):
                    with self.subTest(name=name, expected=expected):
                        path = managed / name
                        path.write_text(json.dumps(payload), encoding="utf-8")
                        try:
                            with self.assertRaises(oc.GuardError) as caught:
                                self.scan()
                            message = str(caught.exception)
                            self.assertIn(expected, message)
                            self.assertIn(str(path), message)
                            self.assertNotIn("declared.js", message)
                        finally:
                            path.unlink()

    def test_the_managed_preferences_source_refuses_on_mere_existence(self):
        """The MDM plist is opaque, so presence alone must refuse.

        `/Library/Managed Preferences` cannot be populated by a unit test, so
        `_managed_preferences_dirs` is injected and a fixture directory carries
        the planted plist.  This is the third opaque source; the other two are
        covered by `test_an_uninspectable_source_refuses_on_mere_existence`.
        """

        preferences = self.scratch / "managed-preferences"
        preferences.mkdir(parents=True, exist_ok=True)
        with mock.patch.object(oc, "_managed_preferences_dirs", lambda: [preferences]):
            self.scan()  # the fixture root alone is benign
            planted = preferences / "ai.opencode.managed.plist"
            planted.write_bytes(b"bplist00")
            with self.assertRaises(oc.GuardError) as caught:
                self.scan()
        message = str(caught.exception)
        self.assertIn("cannot be inspected", message)
        self.assertIn(str(planted), message)

    def test_a_tui_document_execution_key_refuses_at_every_root(self):
        """Round 12's vector: `plugin` in tui.json reaches the same import().

        `packages/tui/src/config/index.tsx:19,57` gives the TUI document a
        `plugin` array of the same PluginSpec shape the main config uses, and
        it lands at `plugin/loader.ts:139 await import(row.entry)` by way of
        TuiConfig.pluginOrigins -> resolveExternalPlugins -> loadExternal.
        """

        xdg, home = self.roots()
        roots = {
            "global": xdg / "opencode",
            "ancestor-cwd": self.worktree,
            "ancestor-above": self.root,
            "nested-opencode": self.worktree / ".opencode",
            "home-dot": home / ".opencode",
        }
        for label, directory in roots.items():
            directory.mkdir(parents=True, exist_ok=True)
            for name in ("tui.json", "tui.jsonc"):
                for execution in oc.EXECUTION_KEYS:
                    key = execution.key
                    with self.subTest(root=label, name=name, key=key):
                        path = directory / name
                        path.write_text(
                            json.dumps({key: ["./declared.js"]}), encoding="utf-8"
                        )
                        try:
                            with self.assertRaises(oc.GuardError) as caught:
                                self.scan()
                            message = str(caught.exception)
                            self.assertIn("execution key", message)
                            self.assertIn(f"#{key}", message)
                            self.assertNotIn("declared.js", message)
                        finally:
                            path.unlink()

    def test_the_owned_d10_keybind_backstop_survives_the_scan(self):
        """The trap: D10 writes this file two steps before D12 reads it.

        `write_tui_backstop` puts `{"keybinds": ...}` into the owned global
        root, and `keybinds` is a MIGRATION_KEYS member.  Gating migration keys
        on the TUI document would refuse the guard's own file and take every
        launch with it, so migration keys apply to the main document only.
        """

        xdg, _home = self.roots()
        backstop = oc.write_tui_backstop(xdg)
        self.assertTrue(backstop.is_file())
        self.assertIn(backstop, self.scan())

    def test_presentation_state_on_a_tui_document_does_not_refuse(self):
        """theme/keybinds are the TUI document's declared schema, not residue."""

        xdg, _home = self.roots()
        target = xdg / "opencode"
        target.mkdir(parents=True, exist_ok=True)
        for name in ("tui.json", "tui.jsonc"):
            for key in oc.MIGRATION_KEYS:
                with self.subTest(name=name, key=key):
                    path = target / name
                    path.write_text(json.dumps({key: {}}), encoding="utf-8")
                    try:
                        self.scan()
                    finally:
                        path.unlink()

    def test_the_same_keys_still_refuse_on_the_main_document(self):
        """The exemption is scoped to the TUI document and nothing else."""

        xdg, _home = self.roots()
        target = xdg / "opencode"
        target.mkdir(parents=True, exist_ok=True)
        for key in oc.MIGRATION_KEYS:
            with self.subTest(key=key):
                path = target / "opencode.json"
                path.write_text(json.dumps({key: {}}), encoding="utf-8")
                try:
                    with self.assertRaisesRegex(oc.GuardError, "migration key"):
                        self.scan()
                finally:
                    path.unlink()

    def test_the_plugin_refusal_does_not_depend_on_the_merged_document(self):
        """D12 sees what the loader sees, not what `debug config` reports.

        `OPENCODE_DISABLE_PROJECT_CONFIG=true` keeps the project array out of the
        merge, so the merged document reads `plugin: []` and passes D13's
        allowlist unchanged.  The plugin loader reads the project file directly,
        so D12's filesystem scan must still refuse.
        """

        (self.worktree / "opencode.json").write_text(
            json.dumps({"plugin": ["./declared.js"]}), encoding="utf-8"
        )
        merged = final_config(self.agents_md)
        self.assertEqual([], merged["plugin"])
        oc.check_final_config(
            merged, model=MODEL, variant=VARIANT, agents_md=self.agents_md
        )
        with self.assertRaisesRegex(oc.GuardError, "execution key"):
            self.scan()


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

    def test_a_normal_launch_survives_the_tui_document_being_scanned(self):
        """Round 12's lockout check, at the full-preflight level.

        D10 writes `<XDG>/opencode/tui.json` at step `tui-backstop`, and D12
        scans that exact path one step later now that the TUI family is in the
        table.  A clean worktree must still reach launch, and the owned
        backstop must still be on disk and intact afterwards.
        """

        trace: list[str] = []
        launch, environment = self.run_preflight(trace=trace)
        self.assertEqual(list(oc.LAUNCH_ARGV), launch)
        self.assertIn("tui-backstop", trace)
        self.assertIn("migration-scan", trace)
        self.assertLess(trace.index("tui-backstop"), trace.index("migration-scan"))

        backstop = Path(environment["XDG_CONFIG_HOME"]) / "opencode" / "tui.json"
        self.assertTrue(backstop.is_file())
        self.assertEqual(oc.TUI_BACKSTOP, backstop.read_text(encoding="utf-8"))

    def test_a_launch_refuses_when_a_tui_document_declares_a_plugin(self):
        """The same launch, with the round-12 vector planted at the worktree."""

        (self.worktree / "tui.json").write_text(
            json.dumps({"plugin": ["./declared.js"]}), encoding="utf-8"
        )
        with self.assertRaises(oc.GuardError) as caught:
            self.run_preflight()
        message = str(caught.exception)
        self.assertIn("execution key", message)
        self.assertIn("#plugin", message)
        self.assertNotIn("declared.js", message)

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

    def test_a_config_declared_plugin_refuses_before_any_config_read(self):
        (self.worktree / "opencode.json").write_text(
            json.dumps({"plugin": ["./declared.js"]}), encoding="utf-8"
        )
        provider = FakeProvider(self.agents_md)
        with self.assertRaisesRegex(oc.GuardError, "execution key"):
            self.run_preflight(provider=provider)
        # Only the D6 version gate ran; it exits inside yargs before any config
        # merge, so no `Config.entries()` and no `ConfigExternalPlugin` import.
        self.assertEqual([["opencode", "--version"]], provider.calls)

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
