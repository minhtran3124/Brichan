"""OpenCode runtime adapter and its guarded launch shim.

Two console entry points live here.

``main`` is the coordinator adapter behind ``brichan-opencode`` and
``bin/brichan --runtime opencode``.  It resolves the routed coordinator model
and hands off to the shim; it never spawns a provider itself.

``exec_main`` is the shim behind ``brichan-opencode-exec``.  It owns the whole
fail-closed boundary: it scrubs every inherited ``OPENCODE_*`` key, sets exactly
six guard keys, creates and preflights per-launch isolated configuration roots,
and only then replaces itself with ``opencode --pure --agent brichan-primary``.

Every refusal names key paths only.  Resolved configuration, provider stdout,
provider stderr, and configuration values are never printed: the merged document
is provider-owned data that may carry credentials or user content, and a
diagnostic is not a place to leak it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Mapping, Sequence

from ._root import exec_runtime, repository_root
from brichan import __version__
from brichan.orchestration.model_routing import (
    ResolvedRoute,
    RoutingError,
    load_settings,
    resolve_coordinator,
    validate_effort,
    validate_model,
)


#: The exact OpenCode release this isolation contract was source-verified
#: against.  D6 gates on equality because the boundary is line-level specific;
#: any bump re-opens the isolation review before this pin moves.
OPENCODE_VERSION = "1.18.12"

GUARD_AGENT = "brichan-primary"

#: All five built-in ``mode: primary`` agents in 1.18.12.  Disabling only
#: build/plan leaves compaction/summary/title as agent-cycle targets.
BUILTIN_PRIMARY_AGENTS = ("build", "plan", "compaction", "summary", "title")

#: The one project skill the guarded agent may reach.
PROJECT_SKILL = "herdr-orchestration"

#: ``opencode debug skill`` prints raw discovery, not the agent-scoped
#: post-permission set, so this precheck is a necessary precondition only.  The
#: built-in ``customize-opencode`` is discovered-but-denied and is tolerated
#: here; acceptance authority is the in-session ``<available_skills>`` block.
DISCOVERABLE_SKILLS = frozenset({PROJECT_SKILL, "customize-opencode"})

ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {
        "$schema",
        "agent",
        "mode",
        "plugin",
        "plugin_origins",
        "command",
        "username",
        "default_agent",
        "permission",
        "share",
        "autoupdate",
        "subagent_depth",
        "instructions",
    }
)

#: Provider-normalized fields the R3B probe recorded as benign.  They are
#: accepted and never value-gated; ``plugin_origins`` in particular is a
#: discovery list, never execution evidence.
BENIGN_TOP_LEVEL_KEYS = frozenset(
    {"$schema", "mode", "plugin", "plugin_origins", "username"}
)

ALLOWED_AGENT_KEYS = frozenset(
    {"mode", "model", "variant", "options", "permission", "disable"}
)

ALLOWED_PERMISSION_KEYS = frozenset({"task", "external_directory"})

#: Keys whose presence in a discovered ``opencode.json``/``.jsonc`` would let
#: provider TUI migration rewrite config or drop a backup outside the owned
#: isolated root.
MIGRATION_KEYS = ("theme", "keybinds", "tui")

#: Byte-exact backstop written into the owned isolated config root.  Keybinds
#: are not part of the ``OPENCODE_CONFIG_CONTENT`` surface, so unbinding the
#: agent-cycle keys needs its own owned file.
TUI_BACKSTOP = '{"keybinds":{"agent_cycle":"none","agent_cycle_reverse":"none"}}'

LAUNCH_ARGV = ("opencode", "--pure", "--agent", GUARD_AGENT)

PROVIDER_TIMEOUT_SECONDS = 30

SHIM_COMMAND = "brichan-opencode-exec"

#: The authoritative S3 order.  ``preflight`` records each completed step here
#: so the ordering contract is asserted against executed behavior rather than
#: against a reading of the source.
STEP_SEQUENCE = (
    "agents-md",
    "scrub",
    "guard-environment",
    "version-gate",
    "isolated-dirs",
    "discovery-preflight",
    "tui-backstop",
    "migration-scan",
    "skill-precheck",
    "final-config-run-1",
    "final-config-run-2",
)


class GuardError(RoutingError):
    """Raised when an OpenCode launch is refused before the provider starts."""


# --------------------------------------------------------------------------
# Guard configuration and environment
# --------------------------------------------------------------------------


def guard_config(model: str, variant: str, agents_md: Path) -> dict:
    """Build the compact inline configuration pinned into the launch.

    This is an intended *input*, not the authoritative final document:
    organization, well-known, and managed sources merge after it.  D13's
    immediate final re-check is what makes a claim about the merged result.
    """

    validate_model(model, "OpenCode model")
    validate_effort("opencode", variant, "OpenCode variant")
    if not agents_md.is_absolute():
        raise GuardError("guard config instruction path must be absolute")
    agents = {name: {"disable": True} for name in BUILTIN_PRIMARY_AGENTS}
    agents[GUARD_AGENT] = {
        "mode": "primary",
        "model": model,
        "variant": variant,
        "permission": {
            "task": "deny",
            # Ordered rules: deny everything, then re-allow exactly the project
            # orchestration skill.  Global skill roots are already hidden by the
            # isolated XDG/home-dot roots.
            "skill": {"*": "deny", PROJECT_SKILL: "allow"},
        },
    }
    return {
        "agent": agents,
        "default_agent": GUARD_AGENT,
        "instructions": [str(agents_md)],
        "permission": {"task": "deny"},
        "share": "disabled",
        "autoupdate": False,
        "subagent_depth": 0,
    }


def config_content(model: str, variant: str, agents_md: Path) -> str:
    return json.dumps(
        guard_config(model, variant, agents_md),
        separators=(",", ":"),
        sort_keys=True,
    )


def scrub_environment(inherited: Mapping[str, str]) -> dict[str, str]:
    """Drop every inherited ``OPENCODE_*`` key without inspecting its value.

    ``OPENCODE_CONFIG_DIR`` is included: setting it would add a fifth
    tool-discovery root rather than replace the other four.
    """

    return {
        key: value
        for key, value in inherited.items()
        if not key.startswith("OPENCODE_")
    }


def guard_environment(
    inherited: Mapping[str, str],
    *,
    model: str,
    variant: str,
    agents_md: Path,
    xdg_config_home: Path,
    test_home: Path,
) -> dict[str, str]:
    """Return the scrubbed environment plus exactly the six guard keys.

    ``HOME``, ``XDG_DATA_HOME``, ``XDG_STATE_HOME``, and ``XDG_CACHE_HOME`` are
    deliberately untouched so real data, state, cache, and the OpenCode
    credential file keep resolving through the real home.  Isolation changes
    configuration and home-dot discovery only.
    """

    environment = scrub_environment(inherited)
    environment.update(
        {
            "OPENCODE_CONFIG_CONTENT": config_content(model, variant, agents_md),
            "OPENCODE_DISABLE_AUTOUPDATE": "1",
            "OPENCODE_DISABLE_PROJECT_CONFIG": "true",
            "OPENCODE_DISABLE_CLAUDE_CODE": "1",
            "OPENCODE_TEST_HOME": str(test_home),
            "XDG_CONFIG_HOME": str(xdg_config_home),
        }
    )
    return environment


GUARD_KEYS = (
    "OPENCODE_CONFIG_CONTENT",
    "OPENCODE_DISABLE_AUTOUPDATE",
    "OPENCODE_DISABLE_PROJECT_CONFIG",
    "OPENCODE_DISABLE_CLAUDE_CODE",
    "OPENCODE_TEST_HOME",
    "XDG_CONFIG_HOME",
)

PRESERVED_KEYS = ("HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME")


# --------------------------------------------------------------------------
# Provider invocation
# --------------------------------------------------------------------------


class ProviderResult:
    """The only part of a provider run the guard is allowed to carry around."""

    __slots__ = ("returncode", "stdout", "timed_out")

    def __init__(self, returncode: int, stdout: str, timed_out: bool = False):
        self.returncode = returncode
        self.stdout = stdout
        self.timed_out = timed_out


Runner = Callable[[Sequence[str], Mapping[str, str]], ProviderResult]


def run_provider(argv: Sequence[str], environment: Mapping[str, str]) -> ProviderResult:
    try:
        completed = subprocess.run(
            list(argv),
            env=dict(environment),
            check=False,
            capture_output=True,
            text=True,
            timeout=PROVIDER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return ProviderResult(returncode=124, stdout="", timed_out=True)
    except FileNotFoundError as exc:
        raise GuardError("cannot launch 'opencode': not installed or not on PATH") from exc
    except OSError as exc:
        raise GuardError(f"cannot launch 'opencode': {exc.strerror}") from exc
    return ProviderResult(completed.returncode, completed.stdout)


# --------------------------------------------------------------------------
# S3 preflight steps
# --------------------------------------------------------------------------


def require_agents_md(worktree: Path) -> Path:
    """First S3 step: the exact absolute instruction path must already exist."""

    agents_md = (worktree / "AGENTS.md").resolve()
    if not agents_md.is_file():
        raise GuardError(f"repository instructions are missing: {worktree / 'AGENTS.md'}")
    return agents_md


def check_version(environment: Mapping[str, str], runner: Runner) -> None:
    """D6 version gate.

    Safe in this position: ``--version`` is bound as a yargs boolean flag and
    the default command's recursive re-parse calls ``process.exit(0)`` before
    ``applyMiddlewareAndGetResult``, so no middleware, handler, ``TuiConfig``
    read, or ``migrateTuiConfig`` call is reached.  Nothing is written.
    """

    result = runner(["opencode", "--version"], environment)
    if result.timed_out:
        raise GuardError("opencode version gate timed out")
    if result.returncode != 0:
        raise GuardError("opencode version gate failed: nonzero exit")
    if result.stdout.strip() != OPENCODE_VERSION:
        raise GuardError(
            f"opencode version gate failed: this guard is pinned to {OPENCODE_VERSION}"
        )


def _prepare_isolated_dir(directory: Path, scratch_root: Path) -> None:
    """Make ``directory`` a provably fresh, empty, Brichan-owned root.

    D7 promises *a fresh empty per-launch dir*, and S3 puts the D6 version gate
    ahead of this step.  That ordering is authoritative and stays, but it has a
    consequence: ``opencode --version`` runs under the guard environment and
    materializes ``<XDG_CONFIG_HOME>/opencode/`` as a filesystem side effect, so
    this step can legitimately find the root already present.

    Accepting "it exists" would quietly downgrade the D7 guarantee to *a
    directory that exists*, which D8 does not backfill — D8 globs only the
    ``EXECUTABLE_SCANS`` directories.  So the pre-existing tree is instead *proven*
    to be nothing but empty directories under our own scratch root, then
    removed and recreated.  A file, a symlink, any other node type, or a path
    outside the owned scratch root refuses; the caller never proceeds on an
    assumption.
    """

    if os.path.islink(scratch_root):
        raise GuardError(f"owned scratch root must not be a symlink: {scratch_root}")
    if directory.parent != scratch_root:
        raise GuardError(
            f"isolated root must live directly under the owned scratch root: {directory}"
        )
    if os.path.lexists(directory):
        if os.path.islink(directory) or not directory.is_dir():
            raise GuardError(f"isolated root is not an owned directory: {directory}")
        for path in sorted(directory.rglob("*")):
            if os.path.islink(path) or not path.is_dir():
                raise GuardError(
                    "isolated root carries provider state before the guard owns it: "
                    f"{path}"
                )
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    if next(directory.iterdir(), None) is not None:  # pragma: no cover
        raise GuardError(f"isolated root is not empty: {directory}")


def create_isolated_dirs(scratch_root: Path) -> tuple[Path, Path]:
    """D7: a fresh empty XDG config root and a fresh empty home-dot root."""

    xdg_config_home = scratch_root / "xdg-config"
    test_home = scratch_root / "opencode-home"
    for directory in (xdg_config_home, test_home):
        _prepare_isolated_dir(directory, scratch_root)
    return xdg_config_home, test_home


def worktree_root(start: Path) -> Path:
    """The upward-walk stop bound: the enclosing Git worktree, or a refusal.

    D8 bounds its project-``.opencode`` walk here, so this value decides how much
    filesystem D8 actually inspects.  The provider computes the same bound at
    ``packages/core/src/project.ts:110-112`` (v1.18.12) — but where a ``.git`` is
    found it uses ``repo.worktree`` (what this walk returns), and where none is
    found it falls back to ``path.parse(input).root``, the *filesystem root*, and
    ``config.ts:178-183`` then walks from ``location.directory`` all the way up
    to it collecting ``.opencode`` directories.  Returning ``start`` here in that
    case would silently narrow D8 to ``cwd`` alone while the provider kept
    walking, so a hostile ``.opencode/plugin/evil.js`` in any ancestor above
    ``cwd`` would be loaded without D8 ever seeing it.

    Refusing rather than widening to the filesystem root is deliberate.  Widening
    would match the provider's scan surface, but it would also mean launching
    with no defined project root at all: ``require_agents_md`` would demand
    ``AGENTS.md`` in whatever ``cwd`` happened to be, D11's checkout orientation
    would have nothing to anchor on, and a root-to-``cwd`` scan of arbitrary
    ancestors is a cost paid on every launch to support a configuration this
    command does not claim to serve.  ``brichan-opencode`` is checkout-oriented:
    both supported callers — the coordinator adapter, which ``chdir``s to
    ``repository_root()``, and a Herdr-launched worker running inside the same
    checkout — always sit inside a Git worktree, so refusing costs no legitimate
    invocation and fails closed on the rest.
    """

    current = start.resolve()
    for candidate in (current, *current.parents):
        # A linked worktree carries a ``.git`` *file*, not a directory, so this
        # tests for existence of either.
        if (candidate / ".git").exists():
            return candidate
    raise GuardError(
        "refusing to launch OpenCode outside a Git worktree: no .git exists at "
        f"or above {current}"
    )


def _scan_matches(root: Path, directories: Sequence[str]) -> list[Path]:
    """Mirror one ``Glob.scan*("{a,b}/*.{js,ts}", {symlink: true})`` call.

    Both executable-load classes below go through this one function so the tool
    scan and the plugin scan cannot drift in extension set, symlink handling,
    or ordering.
    """

    matches: list[Path] = []
    for directory in directories:
        for extension in ("js", "ts"):
            try:
                candidates = sorted((root / directory).glob(f"*.{extension}"))
            except OSError:
                continue
            matches.extend(
                candidate
                for candidate in candidates
                if candidate.is_file() or os.path.lexists(candidate)
            )
    return matches


# Every directory under an OpenCode discovery root from which v1.18.12 will
# dynamically ``import()`` project-supplied code, with the guard's own label.
#
# - ``{tool,tools}/*.{js,ts}`` — ``tool/registry.ts:180``.
# - ``{plugin,plugins}/*.{ts,js}`` — ``config/plugin.ts:21``, reached through
#   ``ConfigPlugin.load(dir)`` at ``config/config.ts:462-464``.  Added in plan
#   version 9 after live probe L4 proved a project ``.opencode/plugin/evil.js``
#   executes in a real TUI session despite ``--pure``.  This scan, not
#   ``--pure`` and not config isolation, is the control for that vector.
#
# Plugin loading in 1.18.12 has three entry points, and only two of them are
# ``--pure``-gated.  Do not relax this scan on the belief that the flag covers
# the vector:
#
# - ``packages/opencode/src/plugin/index.ts:179`` — pure-gated
#   (``const plugins = flags.pure ? [] : (cfg.plugin_origins ?? [])``).
# - ``packages/opencode/src/plugin/tui/runtime.ts:1089`` — pure-gated
#   (``const records = Flag.OPENCODE_PURE ? [] : pluginOrigins``).
# - ``packages/core/src/config/plugin/external.ts`` (``ConfigExternalPlugin.Plugin``)
#   — **not gated at all**: the file contains no ``flags.pure``/``RuntimeFlags``
#   reference.  It globs the identical ``{plugin,plugins}/*.{ts,js}`` pattern
#   over every ``entry.type === "directory"`` from ``Config.Service.entries()``
#   and ``import()``s each match, and it is force-started from the boot layer in
#   ``packages/core/src/plugin/internal.ts``.  This is the best available
#   explanation for L4 — a real, unconditional import path — though it has not
#   been proven live.  D8's own scan is what closes it: the roots that path draws
#   from are ``Global.Path.config`` (the XDG root D7 owns and D8 scans first) and
#   the ``.opencode`` walk from ``location.directory`` up to
#   ``location.project.directory`` (``core/src/config.ts:178-183``), which is
#   exactly the walk ``discovery_preflight`` repeats — see ``worktree_root`` for
#   why that stop bound must be a real Git worktree.
#
# Every other per-root discovery in 1.18.12 loads markdown or config data, not
# executable modules: ``{command,commands}/**/*.md``, ``{agent,agents}/**/*.md``,
# ``{mode,modes}/*.md``, ``{skill,skills}/**/SKILL.md``.
EXECUTABLE_SCANS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("executable custom tool", ("tool", "tools")),
    ("executable plugin", ("plugin", "plugins")),
)


def _tool_matches(root: Path) -> list[Path]:
    """Mirror ``Glob.scanSync("{tool,tools}/*.{js,ts}", {symlink: true})``."""

    return _scan_matches(root, ("tool", "tools"))


def _plugin_matches(root: Path) -> list[Path]:
    """Mirror ``Glob.scan("{plugin,plugins}/*.{ts,js}", {symlink: true})``."""

    return _scan_matches(root, ("plugin", "plugins"))


def _reject_symlinks(root: Path) -> None:
    if os.path.islink(root):
        raise GuardError(f"owned isolated root must not be a symlink: {root}")
    for path in sorted(root.rglob("*")):
        if os.path.islink(path):
            raise GuardError(f"owned isolated root must not contain a symlink: {path}")


def discovery_preflight(
    *,
    cwd: Path,
    worktree: Path,
    xdg_config_home: Path,
    test_home: Path,
    environment: Mapping[str, str],
) -> list[Path]:
    """D8: resolve all four 1.18.12 discovery roots and glob them ourselves.

    This does not trust the isolation environment variables.  The project
    ``.opencode`` walk is repeated even though ``OPENCODE_DISABLE_PROJECT_CONFIG``
    removes that root, so a future release that silently changes scan semantics
    still fails closed here.

    Both ``EXECUTABLE_SCANS`` classes are checked in every root.  The plugin
    scan is the sole control for project-local plugin execution and must not be
    relaxed on the argument that ``--pure`` or config isolation already covers
    it: live probe L4 falsified both for that vector.
    """

    if "OPENCODE_CONFIG_DIR" in environment:
        raise GuardError(
            "OPENCODE_CONFIG_DIR must be unset: it adds a fifth discovery root"
        )

    roots = [xdg_config_home / "opencode"]
    current = cwd.resolve()
    stop = worktree.resolve()
    for candidate in (current, *current.parents):
        roots.append(candidate / ".opencode")
        if candidate == stop:
            break
    roots.append(test_home / ".opencode")

    for owned in (xdg_config_home, test_home):
        _reject_symlinks(owned)

    for root in roots:
        for label, directories in EXECUTABLE_SCANS:
            matches = _scan_matches(root, directories)
            if matches:
                raise GuardError(
                    f"{label} discovered in an OpenCode root: {matches[0]}"
                )
    return roots


def write_tui_backstop(xdg_config_home: Path) -> Path:
    """D10 keybind backstop, written into the owned root and re-read."""

    target = xdg_config_home / "opencode" / "tui.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(TUI_BACKSTOP, encoding="utf-8")
    if target.read_text(encoding="utf-8") != TUI_BACKSTOP:
        raise GuardError(f"owned keybind backstop does not match: {target}")
    return target


def migration_scan(cwd: Path) -> None:
    """D12: refuse if any discoverable config could trigger a TUI migration.

    Runs after the D6 version gate, which is the one source-verified provider
    spawn that cannot reach a migration path.
    """

    current = cwd.resolve()
    for candidate in (current, *current.parents):
        for name in ("opencode.json", "opencode.jsonc"):
            path = candidate / name
            if not path.is_file():
                continue
            try:
                payload = json.loads(_strip_jsonc(path.read_text(encoding="utf-8")))
            except (OSError, ValueError) as exc:
                raise GuardError(
                    f"discovered OpenCode config cannot be parsed: {path}"
                ) from exc
            if not isinstance(payload, dict):
                continue
            for key in MIGRATION_KEYS:
                if key in payload:
                    raise GuardError(
                        "discovered OpenCode config carries a migration key: "
                        f"{path}#{key}"
                    )


def _strip_jsonc(text: str) -> str:
    """Remove ``//`` and ``/* */`` comments outside strings."""

    out: list[str] = []
    index = 0
    length = len(text)
    in_string = False
    while index < length:
        character = text[index]
        if in_string:
            out.append(character)
            if character == "\\" and index + 1 < length:
                out.append(text[index + 1])
                index += 2
                continue
            if character == '"':
                in_string = False
            index += 1
            continue
        if character == '"':
            in_string = True
            out.append(character)
            index += 1
            continue
        if text.startswith("//", index):
            index = text.find("\n", index)
            if index < 0:
                break
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            index = length if end < 0 else end + 2
            continue
        out.append(character)
        index += 1
    return "".join(out)


def skill_precheck(environment: Mapping[str, str], runner: Runner) -> list[str]:
    """D9 clause (i): sanitized discovery precheck.

    ``debug skill`` calls ``Skill.all()`` — raw discovery with no agent and no
    permission filtering — so this is a necessary precondition, never proof of
    availability.  E1's in-session ``<available_skills>`` block is the
    acceptance authority.
    """

    result = runner(["opencode", "--pure", "debug", "skill"], environment)
    if result.timed_out:
        raise GuardError("opencode skill precheck timed out")
    if result.returncode != 0:
        raise GuardError("opencode skill precheck failed: nonzero exit")
    try:
        payload = json.loads(result.stdout)
    except ValueError as exc:
        raise GuardError("opencode skill precheck returned invalid JSON") from exc
    if not isinstance(payload, list):
        raise GuardError("opencode skill precheck did not return a skill list")
    names: list[str] = []
    for entry in payload:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise GuardError("opencode skill precheck returned an unexpected entry shape")
        names.append(entry["name"])
    # The offending name is a data value inside the provider's JSON array, not a
    # config key path, so it is counted and never echoed.  S3 groups this
    # refusal with the allowlist ones under "captured provider output never
    # reaches user output"; a caller that needs the name reads the skill roots
    # itself rather than having Brichan relay provider stdout.
    unexpected = set(names) - DISCOVERABLE_SKILLS
    if unexpected:
        raise GuardError(
            "opencode skill precheck discovered "
            f"{len(unexpected)} unexpected skill(s)"
        )
    if PROJECT_SKILL not in names:
        raise GuardError(f"required project skill was not discovered: {PROJECT_SKILL}")
    return names


# --------------------------------------------------------------------------
# D13 positive final-config allowlist
# --------------------------------------------------------------------------


def _skill_rules(value: object, location: str) -> list[tuple[str, str]]:
    """Normalize the skill permission into an ordered (pattern, action) list."""

    if isinstance(value, dict):
        rules = []
        for pattern, action in value.items():
            if not isinstance(pattern, str) or not isinstance(action, str):
                raise GuardError(f"unexpected skill permission rule shape: {location}")
            rules.append((pattern, action))
        return rules
    if isinstance(value, list):
        rules = []
        for item in value:
            if isinstance(item, dict) and len(item) == 1:
                pattern, action = next(iter(item.items()))
            elif isinstance(item, dict):
                pattern = item.get("pattern") or item.get("skill")
                action = item.get("action") or item.get("permission")
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                pattern, action = item
            else:
                raise GuardError(f"unexpected skill permission rule shape: {location}")
            if not isinstance(pattern, str) or not isinstance(action, str):
                raise GuardError(f"unexpected skill permission rule shape: {location}")
            rules.append((pattern, action))
        return rules
    raise GuardError(f"unexpected skill permission rule shape: {location}")


def _check_agent_entry(name: str, entry: object, expected: dict) -> None:
    location = f"agent.{name}"
    if not isinstance(entry, dict):
        raise GuardError(f"final config entry must be an object: {location}")
    unexpected = sorted(set(entry) - ALLOWED_AGENT_KEYS)
    if unexpected:
        raise GuardError(f"final config has unexpected agent keys: {location}.{unexpected[0]}")
    options = entry.get("options", {})
    if options != {}:
        raise GuardError(f"final config agent carries options: {location}.options")
    for key, value in expected.items():
        if entry.get(key) != value:
            raise GuardError(f"final config value is not the guarded one: {location}.{key}")


def check_final_config(
    document: object,
    *,
    model: str,
    variant: str,
    agents_md: Path,
) -> None:
    """The seven-clause positive allowlist over the merged document."""

    if not isinstance(document, dict):
        raise GuardError("final config is not a JSON object")

    # Clause 1 — top-level allowlist, not a blocklist, so unknown and future
    # fields (mcp, tools, experimental, keybinds) refuse by construction.
    unexpected = sorted(set(document) - ALLOWED_TOP_LEVEL_KEYS)
    if unexpected:
        raise GuardError(f"final config has a disallowed top-level key: {unexpected[0]}")

    # Clause 2 — capability surfaces.
    mcp = document.get("mcp", {})
    if mcp != {}:
        raise GuardError("final config declares MCP servers: mcp")
    if document.get("command", {}) != {}:
        raise GuardError("final config declares custom commands: command")
    instructions = document.get("instructions")
    if not isinstance(instructions, list) or len(instructions) != 1:
        raise GuardError("final config must carry exactly one instruction: instructions")
    entry = instructions[0]
    if not isinstance(entry, str):
        raise GuardError("final config instruction must be a string: instructions[0]")
    if "://" in entry:
        raise GuardError("final config instruction must not be a URL: instructions[0]")
    if entry.startswith("~") or not entry.startswith("/"):
        raise GuardError("final config instruction must be absolute: instructions[0]")
    if entry != str(agents_md):
        raise GuardError("final config instruction is not the guarded path: instructions[0]")

    # Clause 3 — global posture.
    for key, value in (
        ("share", "disabled"),
        ("autoupdate", False),
        ("subagent_depth", 0),
    ):
        if document.get(key) != value:
            raise GuardError(f"final config value is not the guarded one: {key}")
    permission = document.get("permission")
    if not isinstance(permission, dict):
        raise GuardError("final config permission must be an object: permission")
    widened = sorted(set(permission) - ALLOWED_PERMISSION_KEYS)
    if widened:
        raise GuardError(f"final config widens permissions: permission.{widened[0]}")
    if permission.get("task") != "deny":
        raise GuardError("final config does not deny delegation: permission.task")
    for key, value in permission.items():
        if value != "deny":
            raise GuardError(f"final config widens permissions: permission.{key}")

    # Clause 4 — the agent set.
    agents = document.get("agent")
    if not isinstance(agents, dict):
        raise GuardError("final config agent must be an object: agent")
    expected_names = set(BUILTIN_PRIMARY_AGENTS) | {GUARD_AGENT}
    extra = sorted(set(agents) - expected_names)
    if extra:
        raise GuardError(f"final config declares an unexpected agent: agent.{extra[0]}")
    missing = sorted(expected_names - set(agents))
    if missing:
        raise GuardError(f"final config is missing a guarded agent: agent.{missing[0]}")
    for name in BUILTIN_PRIMARY_AGENTS:
        _check_agent_entry(name, agents[name], {"disable": True})
    _check_agent_entry(
        GUARD_AGENT,
        agents[GUARD_AGENT],
        {"mode": "primary", "model": model, "variant": variant},
    )
    primary = agents[GUARD_AGENT]
    if primary.get("disable") is True:
        raise GuardError(f"final config disables the guarded agent: agent.{GUARD_AGENT}.disable")
    primary_permission = primary.get("permission")
    if not isinstance(primary_permission, dict):
        raise GuardError(f"final config agent permission must be an object: agent.{GUARD_AGENT}.permission")
    if primary_permission.get("task") != "deny":
        raise GuardError(f"final config does not deny delegation: agent.{GUARD_AGENT}.permission.task")
    rules = _skill_rules(
        primary_permission.get("skill"),
        f"agent.{GUARD_AGENT}.permission.skill",
    )
    if rules != [("*", "deny"), (PROJECT_SKILL, "allow")]:
        raise GuardError(
            f"final config skill rules are not the guarded ordered pair: "
            f"agent.{GUARD_AGENT}.permission.skill"
        )
    live_primaries = sorted(
        name
        for name, entry in agents.items()
        if isinstance(entry, dict)
        and entry.get("mode") == "primary"
        and entry.get("disable") is not True
    )
    if live_primaries != [GUARD_AGENT]:
        raise GuardError("final config does not leave exactly one primary agent: agent")

    # Clause 5 — the pinned default.
    if document.get("default_agent") != GUARD_AGENT:
        raise GuardError("final config default agent is not the guarded one: default_agent")

    # Clause 6 — keybinds never travel on this surface; the owned tui.json is
    # checked separately by write_tui_backstop.  Clause 1 already rejects the
    # key, so this is only a named restatement for diagnostics.
    if "keybinds" in document:
        raise GuardError("final config must not carry keybinds: keybinds")

    # Clause 7 — benign provider-normalized fields are accepted as-is and are
    # never value-gated; plugin_origins is never read as execution evidence.


def read_final_config(environment: Mapping[str, str], runner: Runner) -> tuple[dict, str]:
    result = runner(["opencode", "--pure", "debug", "config"], environment)
    if result.timed_out:
        raise GuardError("opencode final-config preflight timed out")
    if result.returncode != 0:
        raise GuardError("opencode final-config preflight failed: nonzero exit")
    try:
        document = json.loads(result.stdout)
    except ValueError as exc:
        raise GuardError("opencode final-config preflight returned invalid JSON") from exc
    return document, json.dumps(document, sort_keys=True)


# --------------------------------------------------------------------------
# S3 orchestration
# --------------------------------------------------------------------------


def preflight(
    *,
    model: str,
    variant: str,
    cwd: Path,
    scratch_root: Path,
    inherited: Mapping[str, str],
    runner: Runner | None = None,
    trace: list[str] | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Run every S3 step in the authoritative order and return the launch.

    ``trace`` receives one entry per completed step so the ordering contract can
    be asserted against executed behavior.
    """

    execute = run_provider if runner is None else runner
    record = trace if trace is not None else []

    worktree = worktree_root(cwd)

    agents_md = require_agents_md(worktree)
    record.append("agents-md")

    scrubbed = scrub_environment(inherited)
    record.append("scrub")

    xdg_config_home = scratch_root / "xdg-config"
    test_home = scratch_root / "opencode-home"
    environment = guard_environment(
        scrubbed,
        model=model,
        variant=variant,
        agents_md=agents_md,
        xdg_config_home=xdg_config_home,
        test_home=test_home,
    )
    record.append("guard-environment")

    check_version(environment, execute)
    record.append("version-gate")

    created_xdg, created_home = create_isolated_dirs(scratch_root)
    if (created_xdg, created_home) != (xdg_config_home, test_home):  # pragma: no cover
        raise GuardError("isolated directory layout does not match the guard environment")
    record.append("isolated-dirs")

    discovery_preflight(
        cwd=cwd,
        worktree=worktree,
        xdg_config_home=xdg_config_home,
        test_home=test_home,
        environment=environment,
    )
    record.append("discovery-preflight")

    write_tui_backstop(xdg_config_home)
    record.append("tui-backstop")

    migration_scan(cwd)
    record.append("migration-scan")

    skill_precheck(environment, execute)
    record.append("skill-precheck")

    _, first = read_final_config(environment, execute)
    check_final_config(json.loads(first), model=model, variant=variant, agents_md=agents_md)
    record.append("final-config-run-1")

    # Run 2 is not redundant despite its adjacency: authenticated organization,
    # well-known, and managed sources merge after the inline config and may be
    # fetched over the network, so the merged document can legitimately differ
    # between the two reads.  A residual provider-owned race remains after this
    # check and is documented rather than claimed away.
    _, second = read_final_config(environment, execute)
    check_final_config(json.loads(second), model=model, variant=variant, agents_md=agents_md)
    if second != first:
        raise GuardError("final config changed between the two preflight reads")
    record.append("final-config-run-2")

    return list(LAUNCH_ARGV), environment


# --------------------------------------------------------------------------
# Coordinator adapter (brichan-opencode)
# --------------------------------------------------------------------------


def is_source_checkout(root: Path) -> bool:
    """D11's positive package-marker check.

    Deliberately not the ``AGENTS.md`` + ``bin/`` heuristic: an initialized
    target project has both, which is exactly the lookalike this must reject.
    """

    pyproject = root / "pyproject.toml"
    if not pyproject.is_file() or not (root / "src" / "brichan" / "__init__.py").is_file():
        return False
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return False
    return 'name = "brichan"' in text


def require_direct_console_target(root: Path) -> None:
    """D11: refuse a direct console launch against an initialized target."""

    if not os.path.lexists(root / ".brichan"):
        return
    if is_source_checkout(root):
        return
    raise GuardError(
        "refusing to launch OpenCode against an initialized Brichan project; "
        "brichan-opencode is checkout-oriented and installed OpenCode is out of scope"
    )


def shim_executable() -> str:
    checkout = Path(__file__).resolve().parents[3] / "bin" / SHIM_COMMAND
    if checkout.is_file():
        return str(checkout)
    return SHIM_COMMAND


def shim_command(route: ResolvedRoute) -> list[str]:
    """The only argv shape that reaches the guarded shim.

    The routed model and effort travel as shim options and become
    ``agent.brichan-primary.model``/``.variant``; they are never forwarded as
    provider argv, and no top-level ``--variant`` is ever emitted.
    """

    if route.runtime != "opencode":
        raise GuardError("OpenCode command requires an opencode route")
    validate_model(route.model, "OpenCode model")
    validate_effort("opencode", route.effort, "OpenCode variant")
    return [shim_executable(), "--model", route.model, "--variant", route.effort]


def _help_lines() -> list[str]:
    return [
        "usage: brichan-opencode",
        "",
        "brichan-opencode is checkout-oriented: run it from within the Brichan",
        "source checkout, or with BRICHAN_ROOT set. It takes no provider",
        "arguments; the routed model and effort come from",
        "config/model-routing.json and are pinned into a guarded agent.",
        "Installed OpenCode targets are out of scope.",
    ]


def command(argv: list[str], environment: Mapping[str, str]) -> list[str]:
    if argv:
        raise GuardError(f"brichan-opencode takes no provider arguments: {argv[0]}")
    root = repository_root()
    require_direct_console_target(root)
    settings = load_settings(repository=root, environment=environment)
    route = resolve_coordinator(settings, "opencode")
    return shim_command(route)


CONSOLE_COMMAND = "brichan-opencode"


def _unexpected(exc: BaseException) -> str:
    """The owned wording for a failure with no dedicated diagnostic.

    Only the exception *type* is named.  Its ``str`` can carry filesystem paths
    and provider data, and a traceback carries both plus stack frames, which the
    diagnostics rule forbids.
    """

    return f"refusing to launch after an unexpected {type(exc).__name__}"


def _main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments[:1] in (["--help"], ["-h"]):
        for line in _help_lines():
            print(line)
        return 0
    if arguments[:1] in (["--version"], ["-V"]):
        print(f"brichan-opencode {__version__}")
        return 0
    try:
        resolved_command = command(arguments, os.environ)
    except RoutingError as exc:
        print(f"{CONSOLE_COMMAND}: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"{CONSOLE_COMMAND}: {exc}", file=sys.stderr)
        return 2
    try:
        # repository_root() resolves a directory that os.chdir may still fail on
        # (removed, unreadable, not a directory); load_settings's own OSError
        # wrapping does not cover that.
        os.chdir(repository_root())
    except RuntimeError as exc:
        print(f"{CONSOLE_COMMAND}: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(
            f"{CONSOLE_COMMAND}: cannot enter the repository root: {exc.strerror}",
            file=sys.stderr,
        )
        return 2
    return exec_runtime(
        resolved_command[0], resolved_command, owner=CONSOLE_COMMAND
    )


def main(argv: list[str] | None = None) -> int:
    """Backstop so no exception type can escape this entry point as a traceback.

    ``_main`` names every failure it can foresee.  This wrapper exists for the
    ones it cannot: a traceback is not an owned diagnostic, and it prints
    internal paths and stack frames.
    """

    try:
        return _main(argv)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print(f"{CONSOLE_COMMAND}: interrupted", file=sys.stderr)
        return 130
    except BaseException as exc:
        print(f"{CONSOLE_COMMAND}: {_unexpected(exc)}", file=sys.stderr)
        return 2


# --------------------------------------------------------------------------
# Guarded shim (brichan-opencode-exec)
# --------------------------------------------------------------------------


def parse_shim_arguments(argv: list[str]) -> tuple[str, str]:
    """Strict shim parsing: exactly ``--model`` and ``--variant``, nothing else.

    No positional argument, no attached spelling, and no subcommand is
    accepted, so nothing a caller supplies can reach provider argv.
    """

    model: str | None = None
    variant: str | None = None
    index = 0
    while index < len(argv):
        item = argv[index]
        if item in ("--model", "--variant"):
            if index + 1 >= len(argv):
                raise GuardError(f"{item} requires a value")
            value = argv[index + 1]
            if item == "--model":
                if model is not None:
                    raise GuardError("--model may be given only once")
                model = validate_model(value, "OpenCode model")
            else:
                if variant is not None:
                    raise GuardError("--variant may be given only once")
                variant = validate_effort("opencode", value, "OpenCode variant")
            index += 2
            continue
        raise GuardError(f"brichan-opencode-exec argument is forbidden: {item}")
    if model is None or variant is None:
        raise GuardError("brichan-opencode-exec requires --model and --variant")
    return model, variant


def _refuse(scratch_root: Path, message: str, code: int = 2) -> int:
    """Drop the owned scratch root and report an owned, launch-free refusal."""

    shutil.rmtree(scratch_root, ignore_errors=True)
    print(f"{SHIM_COMMAND}: {message}", file=sys.stderr)
    return code


def _exec_main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments[:1] in (["--help"], ["-h"]):
        print(f"usage: {SHIM_COMMAND} --model MODEL --variant VARIANT")
        return 0
    if arguments[:1] in (["--version"], ["-V"]):
        print(f"{SHIM_COMMAND} {__version__}")
        return 0
    try:
        model, variant = parse_shim_arguments(arguments)
    except RoutingError as exc:
        print(f"{SHIM_COMMAND}: {exc}", file=sys.stderr)
        return 2

    try:
        scratch_root = Path(tempfile.mkdtemp(prefix="brichan-opencode-"))
    except OSError as exc:
        print(
            f"{SHIM_COMMAND}: cannot create the owned scratch root: {exc.strerror}",
            file=sys.stderr,
        )
        return 2

    try:
        launch, environment = preflight(
            model=model,
            variant=variant,
            cwd=Path.cwd(),
            scratch_root=scratch_root,
            inherited=os.environ,
        )
    except RoutingError as exc:
        return _refuse(scratch_root, str(exc))
    except SystemExit:
        shutil.rmtree(scratch_root, ignore_errors=True)
        raise
    except KeyboardInterrupt:
        return _refuse(scratch_root, "interrupted", 130)
    except BaseException as exc:
        # Preflight touches the filesystem, the provider, and JSON it does not
        # own, so it can raise types no clause above names.  Refusing with an
        # owned diagnostic is the fail-closed answer; a traceback would both
        # escape the diagnostics rule and leave the launch state unstated.
        return _refuse(scratch_root, _unexpected(exc))

    # The isolated roots must outlive this process: execvpe replaces it, and the
    # provider reads them for the whole session.  They stay Brichan-owned scratch
    # under the system temporary root; every path that refuses instead of
    # launching removes them above.
    try:
        os.execvpe(launch[0], launch, environment)
    except FileNotFoundError:
        return _refuse(
            scratch_root, "cannot launch 'opencode': not installed or not on PATH"
        )
    except OSError as exc:
        return _refuse(scratch_root, f"cannot launch 'opencode': {exc.strerror}")
    except SystemExit:
        shutil.rmtree(scratch_root, ignore_errors=True)
        raise
    except KeyboardInterrupt:
        return _refuse(scratch_root, "interrupted", 130)
    except BaseException as exc:
        return _refuse(scratch_root, _unexpected(exc))
    return 0


def exec_main(argv: list[str] | None = None) -> int:
    """Backstop so no exception type can escape this entry point as a traceback.

    ``_exec_main`` names every failure it can foresee and always removes the
    owned scratch root first.  This wrapper covers what it cannot foresee —
    including a failure in argument parsing or in the help/version paths, which
    run before there is a scratch root to remove.
    """

    try:
        return _exec_main(argv)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print(f"{SHIM_COMMAND}: interrupted", file=sys.stderr)
        return 130
    except BaseException as exc:
        print(f"{SHIM_COMMAND}: {_unexpected(exc)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
