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

import getpass
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
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
#:
#: **Do not edit this constant alone.**  :data:`EXECUTABLE_SCANS`,
#: :data:`CONFIG_DISCOVERY_SOURCES`, and :data:`EXECUTION_KEYS` are all derived
#: from this release's source; the offline tests only compare them against a
#: recorded transcript, so ``make check``/``make test`` pass unchanged after a
#: bump that missed a provider-side addition.  Extract the new release and run:
#:
#: ``BRICHAN_OPENCODE_PINNED_SOURCE=<extracted tree> make test``
#:
#: Those checks skip silently when the variable is unset — an unset run is not
#: evidence.  A failure means the provider's discovery surface moved: fix the
#: derived table, not the test.  Procedure and per-failure meanings:
#: ``docs/guides/model-routing.md``, "Moving the OpenCode version pin".
#:
#: You will not get far without doing that: this constant and the three tables
#: are digested into ``tests/fixtures/opencode-pinned-surface.json``, which the
#: pinned-source run is what writes.  An always-on contract test compares the
#: digest offline, so editing this line alone fails ``make check`` with the
#: command to run.  That receipt is a forcing function, not a proof — it can be
#: hand-edited; ``tests/opencode_surface.py`` says so and says why it still
#: helps.
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

@dataclass(frozen=True)
class ExecutionKey:
    """One top-level configuration key whose value becomes a module specifier.

    ``key`` is the exact top-level name as it appears in a discovered
    ``opencode.json``/``.jsonc``.  ``config_version`` is ``v1`` or ``v2``, the
    two configuration systems v1.18.12 ships side by side.  ``specifier_path``
    records where inside the key's value the module specifier sits, so a reader
    can check the citation without re-deriving the shape.  ``merge_gated`` says
    whether the loader that consumes it reads the *merged* document (which D13
    can see, and which ``OPENCODE_DISABLE_PROJECT_CONFIG`` empties for project
    files) or the per-file documents (which neither clause can see, which is why
    D12 exists).  ``citation`` is the v1.18.12 source chain, in the same style
    :data:`EXECUTABLE_SCANS` and :data:`CONFIG_DISCOVERY_SOURCES` use.
    """

    key: str
    config_version: str
    specifier_path: str
    merge_gated: bool
    citation: str


#: **The D12 execution-key set, derived from an enumeration of every module
#: specifier the pinned provider can import rather than hand-listed.**
#:
#: Plan version 13 applies to the key surface the discipline version 11 applied
#: to the config-file surface and version 12 to the directory-glob surface.
#: Until this round the set was the literal tuple ``("plugin", "plugins")``, and
#: every hand-written set in this guard has eventually produced a vector.
#:
#: **The derivation, and its result: the hand-listed pair was not complete.**
#: The closure argument is over ``import()`` call sites, not over config keys —
#: a key can only execute code by reaching an import.  At v1.18.12 (tag
#: ``v1.18.12`` = ``0dd6950d1b06958fbcdcadf0ad56258257ab7fdb``) exactly seven
#: ``import()`` call sites in ``packages/{core,opencode}/src`` take a
#: non-literal specifier; every other import in those packages names a bundled
#: module literally and no configuration can redirect it.  Each of the seven was
#: traced back to where its specifier comes from:
#:
#: - ``core/config/plugin/external.ts:80`` — ``entry.info.plugins[].package``
#:   (**v2 key ``plugins``**) and the D8 ``{plugin,plugins}`` glob.
#: - ``opencode/plugin/loader.ts:139`` — ``plugin_origins``, built from the
#:   **v1 key ``plugin``** (``opencode/config/config.ts:344-348,432``) and the
#:   same D8 glob (``ConfigPlugin.load`` at ``config/plugin.ts:18-30``).
#: - ``core/plugin/provider/dynamic.ts:20`` and
#:   ``core/plugin/provider/sap-ai-core.ts:25`` — ``evt.package``, which
#:   ``core/aisdk.ts:208,215`` sets from ``model.api.package``
#:   (**v2 key ``providers``**).
#: - ``opencode/provider/provider.ts:1793`` — ``model.api.npm``, resolved at
#:   ``:1440-1443`` from **v1 key ``provider``**.
#: - ``opencode/tool/registry.ts:187`` — the D8 ``{tool,tools}`` glob only; no
#:   configuration key reaches it.
#: - ``opencode/config/config.ts:265`` — the legacy global TOML config *file*
#:   itself, which :data:`CONFIG_DISCOVERY_SOURCES` already refuses on existence
#:   because the guard cannot parse it.  No key names it.
#:
#: So the enumeration yields four top-level keys, not two.  ``provider`` and
#: ``providers`` are **new in plan version 13** and were not previously refused
#: by any clause.  Their reachability argument is the same one that makes
#: ``plugin`` the fourth vector, and it is recorded here rather than smoothed
#: over, because the two spellings differ in evidential status exactly as
#: ``plugin`` and ``plugins`` do:
#:
#: * **``providers`` (v2) bypasses the merge, like ``plugins``.**
#:   ``ConfigProviderPlugin`` (``core/config/plugin/provider.ts:15,43-44``) reads
#:   ``Config.Service.entries()`` — the same per-file API ``ConfigExternalPlugin``
#:   uses — and writes each file's ``providers.<id>.api`` and
#:   ``providers.<id>.models.<id>.api`` straight into the catalog at ``:55,65``.
#:   ``ProviderV2.AISDK`` carries ``package: Schema.String``
#:   (``packages/schema/src/provider.ts:27-32``), which ``core/aisdk.ts:208,215``
#:   hands to the SDK hook and ``dynamic.ts:14-24`` installs and ``import()``s.
#:   Both that plugin and ``DynamicProviderPlugin`` are added unconditionally at
#:   boot (``core/plugin/internal.ts:119-120``, ``core/plugin/provider.ts:70``)
#:   and neither file contains a ``pure``/``RuntimeFlags`` reference — the same
#:   ungated shape as ``ConfigExternalPlugin``.
#: * **``provider`` (v1) reaches that same per-file reader by migration.**
#:   ``ConfigMigrateV1.isV1`` lists ``provider`` as a v1 marker
#:   (``core/v1/config/migrate.ts:10-27``), and ``migrate()`` rewrites
#:   ``provider.<id>.npm`` into ``providers.<id>.api.package`` and
#:   ``provider.<id>.models.<id>.provider.npm`` into
#:   ``providers.<id>.models.<id>.api.package`` (``:165-233``); ``loadFile``
#:   applies that migration to every discovered file
#:   (``core/config.ts:147-162``).  Its *other* consumer,
#:   ``opencode/provider/provider.ts:1336-1346``, reads the merged document and
#:   so is gated by D13's top-level allowlist and by
#:   ``OPENCODE_DISABLE_PROJECT_CONFIG``; the per-file consumer is not.
#:
#: ``merge_gated`` records that split.  It is documentation, not a switch: every
#: entry is refused regardless, because D12's whole reason for existing is that a
#: merge-gated conclusion has been wrong here before.
#:
#: The status of the two new keys is **fail-closed on a source argument that
#: live testing has not exercised**, which is exactly the status the plan
#: records for ``plugins``.  A coordinator probe found ``plugins`` alone did not
#: execute on 1.18.12 while ``plugin`` did, so the v2 per-file reader may not be
#: active in the probed configuration; if so ``providers`` inherits the same
#: uncertainty.  Refusing costs two key names and fails closed either way.
EXECUTION_KEYS: tuple[ExecutionKey, ...] = (
    ExecutionKey(
        key="plugin",
        config_version="v1",
        specifier_path="plugin[] (string, or [string, options] tuple)",
        merge_gated=False,
        citation=(
            "schema packages/core/src/v1/config/config.ts:56 "
            "(plugin: Array(ConfigPluginV1.Spec)); collected into plugin_origins "
            "at packages/opencode/src/config/config.ts:344-348,432 and "
            "import()ed at packages/opencode/src/plugin/loader.ts:139; also "
            "migrated in memory to the v2 plugins field by "
            "packages/core/src/v1/config/migrate.ts:10-27 and reaches "
            "packages/core/src/config/plugin/external.ts:80.  Live-confirmed "
            "vector: a project opencode.json carrying it executed the file "
            "under the otherwise complete guard on 1.18.12."
        ),
    ),
    ExecutionKey(
        key="plugins",
        config_version="v2",
        specifier_path="plugins[].package (or plugins[] as a bare string)",
        merge_gated=False,
        citation=(
            "schema packages/core/src/config.ts:102-104 (plugins: "
            "ConfigPlugin.Plugins) with packages/core/src/config/plugin.ts:5-13 "
            "(Entry.package: Schema.String); read per file from "
            "Config.Service.entries() at "
            "packages/core/src/config/plugin/external.ts:42-56 and import()ed "
            "at :80 with no pure gate."
        ),
    ),
    ExecutionKey(
        key="provider",
        config_version="v1",
        specifier_path=(
            "provider.<id>.npm and provider.<id>.models.<id>.provider.npm"
        ),
        merge_gated=False,
        citation=(
            "schema packages/core/src/v1/config/provider.ts:87 (Info.npm) and "
            ":65 (Model.provider.npm), top-level at "
            "packages/core/src/v1/config/config.ts:110; merged-document "
            "consumer packages/opencode/src/provider/provider.ts:1440-1443 "
            "resolves model.api.npm and import()s it at :1785-1793.  The "
            "per-file consumer is the migration: "
            "packages/core/src/v1/config/migrate.ts:10-27 treats a top-level "
            "provider as a v1 marker and :165-233 rewrites npm into the v2 "
            "providers.<id>.api.package field, applied to every discovered file "
            "by packages/core/src/config.ts:147-162."
        ),
    ),
    ExecutionKey(
        key="providers",
        config_version="v2",
        specifier_path=(
            "providers.<id>.api.package and "
            "providers.<id>.models.<id>.api.package (api.type == \"aisdk\")"
        ),
        merge_gated=False,
        citation=(
            "schema packages/core/src/config.ts:106 (providers: "
            "Record(ConfigProvider.Info)) with "
            "packages/core/src/config/provider.ts:33-45,65-71 and "
            "packages/schema/src/provider.ts:27-32 (AISDK.package: "
            "Schema.String); read per file from Config.Service.entries() at "
            "packages/core/src/config/plugin/provider.ts:15,43-44 and written "
            "into the catalog at :55,65; packages/core/src/aisdk.ts:208,215 "
            "passes model.api.package to the SDK hook, which "
            "packages/core/src/plugin/provider/dynamic.ts:14-24 (and "
            "sap-ai-core.ts:19-25) installs and import()s.  Both plugins boot "
            "unconditionally at packages/core/src/plugin/internal.ts:119-120 "
            "and packages/core/src/plugin/provider.ts:70, with no pure gate."
        ),
    ),
)

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


def _scan_matches(
    root: Path, directories: Sequence[str], extensions: Sequence[str]
) -> list[Path]:
    """Mirror one ``Glob.scan*("{a,b}/*.{js,ts}", {symlink: true})`` call.

    Both executable-load classes below go through this one function so the tool
    scan and the plugin scan cannot drift in symlink handling or ordering.  The
    directory family and the extension set are supplied by the caller from
    :data:`EXECUTABLE_SCANS` rather than written here, so the only place either
    is stated is the source-cited table.

    Extensions are iterated in sorted order, not in the order the provider
    happens to spell them (``{js,ts}`` at ``tool/registry.ts:180`` versus
    ``{ts,js}`` at ``config/plugin.ts:21``).  The provider's spelling has no
    semantics — a brace alternation is a set — and sorting keeps the *first*
    reported match stable across both families, which is what refusal
    diagnostics name.
    """

    matches: list[Path] = []
    for directory in directories:
        for extension in sorted(extensions):
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


@dataclass(frozen=True)
class ExecutableScan:
    """One per-root directory family the pinned provider imports code from.

    ``directories`` are the brace alternatives of the provider's own glob and
    ``extensions`` its extension alternatives, both carried as sets rather than
    as the pattern string so a test can compare them against the provider's
    spelling without re-parsing ours.  ``citation`` is the v1.18.12 source line
    that establishes the scan, in the same style :data:`CONFIG_DISCOVERY_SOURCES`
    uses for D12's config files.
    """

    label: str
    directories: tuple[str, ...]
    extensions: tuple[str, ...]
    citation: str


#: **The D8 directory-glob set, derived from the provider's own per-root
#: executable-scan implementation at the pinned v1.18.12 rather than
#: hand-listed.**
#:
#: Plan version 12 applies to D8 the discipline version 11 applied to D12.  The
#: two families below were previously a hand-maintained tuple with no drift
#: test, which is the exact shape that produced four separate plugin-execution
#: vectors on the config surface.  ``tests/unit/test_opencode_commands.py``
#: now asserts this table equals a documented enumeration transcribed verbatim
#: from the pinned provider source, so a bump that adds a scanned directory
#: family or a new executable extension fails a test.
#:
#: The enumeration is closed: at v1.18.12 (tag ``v1.18.12`` =
#: ``0dd6950d1b06958fbcdcadf0ad56258257ab7fdb``) exactly three call sites glob a
#: per-root directory for code and ``import()`` the matches, and they cover two
#: families:
#:
#: - ``{tool,tools}/*.{js,ts}`` — ``packages/opencode/src/tool/registry.ts:180``,
#:   imported at ``:187``.
#: - ``{plugin,plugins}/*.{ts,js}`` — ``packages/opencode/src/config/plugin.ts:21``
#:   (via ``ConfigPlugin.load(dir)`` at ``config/config.ts:462-464``) and
#:   ``packages/core/src/config/plugin/external.ts:60``, imported at ``:80``.
#:   Added in plan version 9 after live probe L4 proved a project
#:   ``.opencode/plugin/evil.js`` executes in a real TUI session despite
#:   ``--pure``.  This scan, not ``--pure`` and not config isolation, is the
#:   control for that vector.
#:
#: Every other per-root glob in ``packages/*/src`` at that ref matches markdown,
#: never code: ``{command,commands}/**/*.md``
#: (``packages/opencode/src/config/command.ts:15``,
#: ``packages/core/src/config/plugin/command.ts:55``), ``{agent,agents}/**/*.md``
#: and ``{mode,modes}/*.md`` (``packages/opencode/src/config/agent.ts:13,36``;
#: ``packages/core/src/config/plugin/agent.ts:21-22,143``), and the skill
#: patterns ``skills/**/SKILL.md`` / ``{skill,skills}/**/SKILL.md`` /
#: ``**/SKILL.md`` (``packages/opencode/src/skill/index.ts:23-25,150``,
#: ``packages/core/src/skill.ts:79``).  The two variable-pattern call sites were
#: resolved to their literals rather than assumed: ``config/plugin/agent.ts:143``
#: takes ``source.pattern`` from ``legacySources`` at ``:21-22``, and
#: ``skill/index.ts:150`` takes one of the three constants at ``:23-25``.
#:
#: Plugin loading in 1.18.12 has three entry points, and only two of them are
#: ``--pure``-gated.  Do not relax this scan on the belief that the flag covers
#: the vector:
#:
#: - ``packages/opencode/src/plugin/index.ts:179`` — pure-gated
#:   (``const plugins = flags.pure ? [] : (cfg.plugin_origins ?? [])``).
#: - ``packages/opencode/src/plugin/tui/runtime.ts:1089`` — pure-gated
#:   (``const records = Flag.OPENCODE_PURE ? [] : pluginOrigins``).
#: - ``packages/core/src/config/plugin/external.ts`` (``ConfigExternalPlugin.Plugin``)
#:   — **not gated at all**: the file contains no ``flags.pure``/``RuntimeFlags``
#:   reference.  It globs the identical ``{plugin,plugins}/*.{ts,js}`` pattern
#:   over every ``entry.type === "directory"`` from ``Config.Service.entries()``
#:   and ``import()``s each match, and it is force-started from the boot layer in
#:   ``packages/core/src/plugin/internal.ts``.  This is the best available
#:   explanation for L4 — a real, unconditional import path — though it has not
#:   been proven live.  D8's own scan is what closes it: the roots that path draws
#:   from are ``Global.Path.config`` (the XDG root D7 owns and D8 scans first) and
#:   the ``.opencode`` walk from ``location.directory`` up to
#:   ``location.project.directory`` (``core/src/config.ts:178-183``), which is
#:   exactly the walk ``discovery_preflight`` repeats — see ``worktree_root`` for
#:   why that stop bound must be a real Git worktree.
EXECUTABLE_SCANS: tuple[ExecutableScan, ...] = (
    ExecutableScan(
        label="executable custom tool",
        directories=("tool", "tools"),
        extensions=("js", "ts"),
        citation=(
            'packages/opencode/src/tool/registry.ts:180 — Glob.scanSync("{tool,'
            'tools}/*.{js,ts}", { cwd: dir, absolute: true, dot: true, symlink: '
            "true }) over config.directories(); each match is import()ed at "
            ":187."
        ),
    ),
    ExecutableScan(
        label="executable plugin",
        directories=("plugin", "plugins"),
        extensions=("ts", "js"),
        citation=(
            'packages/opencode/src/config/plugin.ts:21 — Glob.scan("{plugin,'
            'plugins}/*.{ts,js}", { cwd: dir, dot: true, symlink: true }) via '
            "ConfigPlugin.load(dir) at config/config.ts:462-464; and "
            'packages/core/src/config/plugin/external.ts:60 — fs.glob("{plugin,'
            'plugins}/*.{ts,js}", ...) over every entry.type === "directory", '
            "import()ed at :80 with no pure gate."
        ),
    ),
)


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
        for scan in EXECUTABLE_SCANS:
            matches = _scan_matches(root, scan.directories, scan.extensions)
            if matches:
                raise GuardError(
                    f"{scan.label} discovered in an OpenCode root: {matches[0]}"
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


#: Environment keys that would relocate or add a configuration source the
#: enumeration below cannot express as a path.  ``OPENCODE_CONFIG`` names an
#: arbitrary config file (``packages/opencode/src/config/config.ts:401-403``);
#: ``OPENCODE_CONFIG_DIR`` replaces the global config root and adds a fifth
#: discovery root (``packages/core/src/global.ts:64``,
#: ``packages/opencode/src/config/paths.ts:39``);
#: ``OPENCODE_TEST_MANAGED_CONFIG_DIR`` relocates the managed root
#: (``packages/opencode/src/config/managed.ts:32``).  The shim scrubs every
#: inherited ``OPENCODE_*`` key, so none of these can legitimately be present;
#: seeing one means the scrub did not hold and the scan set is wrong.
CONFIG_SOURCE_FORBIDDEN_ENV = (
    "OPENCODE_CONFIG",
    "OPENCODE_CONFIG_DIR",
    "OPENCODE_TEST_MANAGED_CONFIG_DIR",
)


@dataclass(frozen=True)
class ConfigSource:
    """One configuration-file family the pinned provider can read.

    ``root`` names a directory family expanded by :func:`_config_source_roots`;
    ``filenames`` are the exact basenames read inside it; ``parse`` is ``jsonc``
    when the guard can read the file and gate its keys, or ``opaque`` when it
    cannot and mere existence must refuse.  ``citation`` is the v1.18.12 source
    line that establishes the read.

    ``document`` names *which* configuration document the file decodes into,
    and it changes which key sets apply.  The provider ships two side by side:

    * ``"main"`` — the ``Config.Info`` document.  Both :data:`MIGRATION_KEYS`
      and :data:`EXECUTION_KEYS` apply.
    * ``"tui"`` — the ``TuiConfig.Info`` document (``tui.json``/``tui.jsonc``,
      schema at ``packages/tui/src/config/index.tsx:44-66``).  Only
      :data:`EXECUTION_KEYS` apply.  ``theme`` and ``keybinds`` are this
      document's *legitimate content*, not migration residue — D10 writes a
      keybind backstop into the owned root on purpose — so applying
      :data:`MIGRATION_KEYS` here would refuse the guard's own file and every
      launch with it.  The migration-key refusal exists to stop provider TUI
      migration from rewriting the **main** config and dropping backups outside
      the owned root, which is a statement about ``opencode.json``, not about
      ``tui.json``.
    """

    label: str
    root: str
    filenames: tuple[str, ...]
    parse: str
    citation: str
    document: str = "main"


#: **The D12 scan set, derived from the provider's own configuration-discovery
#: implementation at the pinned v1.18.12 rather than hand-listed.**
#:
#: Plan version 11 restructured D12 after a fourth vector of one shape: versions
#: 9 and 10 each patched whichever location had just been found, and a further
#: one surfaced each time.  The table below is the enumeration; anything that
#: scans must expand from it, and ``tests/unit/test_opencode_commands.py``
#: asserts both that this table matches its documented contents and that the
#: concrete paths scanned expand from exactly these entries.  A provider bump
#: that adds a discovery path therefore fails a test instead of silently opening
#: a hole.
#:
#: v1.18.12 ships two config systems and both were traced:
#:
#: * v1 — ``packages/opencode/src/config/config.ts``, whose discovery roots come
#:   from ``packages/opencode/src/config/paths.ts``.
#: * v2 — ``packages/core/src/config.ts``, whose walk and per-directory load are
#:   at ``:177-200``.
#:
#: Both resolve to the same file families, so the union below is the scan set.
#: The ancestor walk itself is ``FSUtil.up`` at
#: ``packages/core/src/fs-util.ts:168-182`` — a plain parent walk that stops at
#: ``stop`` if given and at the filesystem root otherwise.  D12 walks to the
#: filesystem root unconditionally, which is a superset of both callers'
#: bounds (v1 stops at ``ctx.worktree``, v2 at ``location.project.directory``),
#: so no bound mismatch can narrow the scan.
#:
#: Sources deliberately **not** in this table, with the reason:
#:
#: * ``OPENCODE_CONFIG_CONTENT`` (``config.ts:468-475``) — Brichan authors it.
#: * Authenticated org / well-known and remote account config
#:   (``config.ts:505-514``) — fetched over the network, not a filesystem path.
#:   D13's second ``debug config`` read against freshly merged provider output
#:   is the control for those, as the plan records.
CONFIG_DISCOVERY_SOURCES: tuple[ConfigSource, ...] = (
    ConfigSource(
        label="global config root",
        root="global-config",
        filenames=("config.json", "opencode.json", "opencode.jsonc"),
        parse="jsonc",
        citation=(
            "v1 packages/opencode/src/config/config.ts:258-260 "
            "(loadFile over Global.Path.config); "
            "v2 packages/core/src/config.ts:142,173,186-187,200 "
            "(loadDirectory over directories[0] = global.config, names = "
            '["opencode.json", "opencode.jsonc"]). '
            "Global.Path.config is <XDG_CONFIG_HOME>/opencode "
            "(packages/core/src/global.ts:13,26)."
        ),
    ),
    ConfigSource(
        label="global legacy toml config",
        root="global-config",
        filenames=("config",),
        parse="opaque",
        citation=(
            "v1 packages/opencode/src/config/config.ts:262-268 — "
            "import(pathToFileURL(<Global.Path.config>/config), "
            '{ with: { type: "toml" } }). Not JSON, so the guard cannot gate '
            "its keys; presence alone refuses."
        ),
    ),
    ConfigSource(
        label="ancestor project config",
        root="ancestor",
        filenames=("opencode.json", "opencode.jsonc"),
        parse="jsonc",
        citation=(
            "v1 packages/opencode/src/config/config.ts:406-409 via "
            "ConfigPaths.files at packages/opencode/src/config/paths.ts:16-20 "
            '(up targets ["opencode.jsonc", "opencode.json"]); '
            "v2 packages/core/src/config.ts:179-185,195-196 "
            "(up targets include names.toReversed(), loaded via loadFile)."
        ),
    ),
    ConfigSource(
        label="ancestor .opencode config",
        root="ancestor-opencode",
        filenames=("opencode.json", "opencode.jsonc"),
        parse="jsonc",
        citation=(
            "v1 packages/opencode/src/config/config.ts:416,425-430 — for each "
            'directory ending in ".opencode", loadFile of "opencode.json" and '
            '"opencode.jsonc"; directories from '
            "packages/opencode/src/config/paths.ts:28-33; "
            "v2 packages/core/src/config.ts:164-171,186-192,200 "
            "(loadDirectory over every discovered .opencode). "
            "This is the fourth vector: D8 globs only this root's "
            "{tool,tools}/{plugin,plugins} subdirectories, and D12 before "
            "plan version 11 never appended the .opencode segment."
        ),
    ),
    ConfigSource(
        label="home-dot .opencode config",
        root="home-opencode",
        filenames=("opencode.json", "opencode.jsonc"),
        parse="jsonc",
        citation=(
            "v1 packages/opencode/src/config/paths.ts:34-38 — up targets "
            '[".opencode"] from Global.Path.home with stop = Global.Path.home, '
            "so exactly <home>/.opencode; consumed by config.ts:425-430. "
            "Global.Path.home honours OPENCODE_TEST_HOME "
            "(packages/core/src/global.ts:18-20), which D7 owns."
        ),
    ),
    ConfigSource(
        label="system managed config",
        root="managed",
        filenames=("opencode.json", "opencode.jsonc"),
        parse="jsonc",
        citation=(
            "v1 packages/opencode/src/config/config.ts:516-521 over "
            "ConfigManaged.managedConfigDir() "
            "(packages/opencode/src/config/managed.ts:20-33)."
        ),
    ),
    ConfigSource(
        label="macOS managed preferences",
        root="managed-preferences",
        filenames=("ai.opencode.managed.plist",),
        parse="opaque",
        citation=(
            "v1 packages/opencode/src/config/config.ts:523-530 via "
            "ConfigManaged.readManagedPreferences "
            "(packages/opencode/src/config/managed.ts:8,43-68) — an MDM plist "
            "that overrides everything.  It is a plist, not JSON, so the guard "
            "cannot gate its keys; presence alone refuses."
        ),
    ),
    # ---- The TUI document, added in round 12. -----------------------------
    # Round 11 derived this surface from the tree instead of a transcript and
    # found a config-file family the transcript had never named.  Round 12
    # established it is an executable surface of the same class as the other
    # four: ``plugin`` is a ``PluginSpec`` (``packages/tui/src/config/
    # index.tsx:19,57``) — the same string-or-[string, options] shape the main
    # config's ``plugin`` key uses — and it reaches the same importer.  The
    # chain: ``config/tui.ts:157-168`` turns the array into
    # ``ConfigPlugin.Origin`` records, ``tui.ts:223,253,274`` exposes them as
    # ``TuiConfig.pluginOrigins()``, ``plugin/tui/runtime.ts:1088,1106`` passes
    # them to ``resolveExternalPlugins``, ``:677`` hands them to
    # ``PluginLoader.loadExternal``, and ``plugin/loader.ts:139`` runs
    # ``await import(row.entry)``.  That is the identical import site
    # ``EXECUTION_KEYS`` already refuses ``plugin`` for on the main document.
    #
    # ``Flag.OPENCODE_PURE`` gates that consumer at ``runtime.ts:1089``, and
    # the guard sets ``--pure``.  That gate is not the control: live probe L4
    # falsified exactly this argument for the main config's ``plugin`` key,
    # which is why D8 and D12 scan project roots redundantly despite D7.  A
    # second consumer has no pure gate at all — ``config/tui.ts:224,236-247``
    # runs ``npm.install`` in every discovered ``.opencode`` directory whenever
    # the array is non-empty.
    ConfigSource(
        label="global tui config",
        root="global-config",
        filenames=("tui.json", "tui.jsonc"),
        parse="jsonc",
        document="tui",
        citation=(
            "v1 packages/opencode/src/config/tui.ts:184 — "
            'ConfigPaths.fileInDirectory(Global.Path.config, "tui"), expanded '
            "by packages/opencode/src/config/paths.ts:43-45 into "
            "<dir>/tui.json and <dir>/tui.jsonc.  This is the root D10 writes "
            "its own keybind backstop into."
        ),
    ),
    ConfigSource(
        label="ancestor tui config",
        root="ancestor",
        filenames=("tui.json", "tui.jsonc"),
        parse="jsonc",
        document="tui",
        citation=(
            "v1 packages/opencode/src/config/tui.ts:175 — "
            'ConfigPaths.files("tui", ctx.directory) via paths.ts:10-21, whose '
            "targets are [`${name}.jsonc`, `${name}.json`].  Called without a "
            "worktree argument, so stop is undefined and the walk reaches the "
            "filesystem root.  Gated by OPENCODE_DISABLE_PROJECT_CONFIG, which "
            "the guard sets and which D12 scans past on principle."
        ),
    ),
    ConfigSource(
        label="ancestor .opencode tui config",
        root="ancestor-opencode",
        filenames=("tui.json", "tui.jsonc"),
        parse="jsonc",
        document="tui",
        citation=(
            "v1 packages/opencode/src/config/tui.ts:203-209 — "
            'ConfigPaths.fileInDirectory(dir, "tui") for every directory from '
            "ConfigPaths.directories (paths.ts:23-41) ending in .opencode."
        ),
    ),
    ConfigSource(
        label="home-dot .opencode tui config",
        root="home-opencode",
        filenames=("tui.json", "tui.jsonc"),
        parse="jsonc",
        document="tui",
        citation=(
            "v1 packages/opencode/src/config/tui.ts:203-209 over the same "
            "ConfigPaths.directories list, whose home-dot entry comes from "
            "paths.ts:34-38 (up targets [\".opencode\"] bounded to "
            "Global.Path.home)."
        ),
    ),
)


def managed_config_dir() -> Path:
    """Mirror ``ConfigManaged.managedConfigDir`` (``managed.ts:20-33``).

    ``OPENCODE_TEST_MANAGED_CONFIG_DIR`` is refused outright rather than
    honoured, so only the platform default is expanded here.
    """

    if sys.platform == "darwin":
        return Path("/Library/Application Support/opencode")
    if os.name == "nt":  # pragma: no cover - the guard does not target Windows
        return Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "opencode"
    return Path("/etc/opencode")


def _managed_preferences_dirs() -> list[Path]:
    """Mirror ``readManagedPreferences``' path list (``managed.ts:43-56``)."""

    if sys.platform != "darwin":
        return []
    try:
        user = getpass.getuser() or "user"
    except Exception:  # pragma: no cover - matches the provider's own fallback
        user = "user"
    base = Path("/Library/Managed Preferences")
    return [base / user, base]


def _config_source_roots(
    source: ConfigSource,
    *,
    cwd: Path,
    xdg_config_home: Path,
    test_home: Path,
) -> list[Path]:
    """Expand one :class:`ConfigSource` root family into directories.

    An unrecognised ``root`` raises rather than being skipped: adding a source
    to :data:`CONFIG_DISCOVERY_SOURCES` without teaching the expansion about it
    must fail loudly, never scan nothing.
    """

    if source.root == "global-config":
        return [xdg_config_home / "opencode"]
    if source.root == "home-opencode":
        return [test_home / ".opencode"]
    if source.root == "managed":
        return [managed_config_dir()]
    if source.root == "managed-preferences":
        return _managed_preferences_dirs()
    if source.root in ("ancestor", "ancestor-opencode"):
        current = cwd.resolve()
        ancestors = [current, *current.parents]
        if source.root == "ancestor":
            return ancestors
        return [ancestor / ".opencode" for ancestor in ancestors]
    raise GuardError(  # pragma: no cover - guarded by the drift test
        f"unknown OpenCode config discovery root: {source.root}"
    )


def config_scan_paths(
    *,
    cwd: Path,
    xdg_config_home: Path,
    test_home: Path,
    environment: Mapping[str, str],
) -> list[tuple[Path, ConfigSource]]:
    """Expand :data:`CONFIG_DISCOVERY_SOURCES` into the concrete D12 scan set.

    Order follows the table, then root order, then filename order, so the set is
    deterministic and a test can assert it exactly.  Duplicates are collapsed on
    first appearance.
    """

    for key in CONFIG_SOURCE_FORBIDDEN_ENV:
        if key in environment:
            raise GuardError(
                f"{key} must be unset: it moves OpenCode configuration outside "
                "the derived scan set"
            )

    paths: list[tuple[Path, ConfigSource]] = []
    seen: set[Path] = set()
    for source in CONFIG_DISCOVERY_SOURCES:
        for root in _config_source_roots(
            source, cwd=cwd, xdg_config_home=xdg_config_home, test_home=test_home
        ):
            for name in source.filenames:
                path = root / name
                if path in seen:
                    continue
                seen.add(path)
                paths.append((path, source))
    return paths


def migration_scan(
    cwd: Path,
    *,
    xdg_config_home: Path,
    test_home: Path,
    environment: Mapping[str, str],
) -> list[Path]:
    """D12: scan every config file the provider itself can read.

    The scan set is not hand-listed.  It expands from
    :data:`CONFIG_DISCOVERY_SOURCES`, which is derived from the pinned
    provider's own discovery implementation and carries a source citation per
    entry.  Neither is the key set: it expands from :data:`EXECUTION_KEYS`,
    derived from every non-literal ``import()`` site at the pinned version.
    Refuses if any discovered config could trigger a TUI migration and — for the
    reason recorded on :data:`EXECUTION_KEYS` — if one names a module the
    provider would load; refuses on the mere existence of a source the guard
    cannot parse.
    Runs after the D6 version gate, which is the one source-verified provider
    spawn that cannot reach a migration path.

    Returns the scanned paths so callers and tests can bind against the actual
    set rather than a restatement of it.
    """

    scanned = config_scan_paths(
        cwd=cwd,
        xdg_config_home=xdg_config_home,
        test_home=test_home,
        environment=environment,
    )
    for path, source in scanned:
        if source.parse == "opaque":
            if path.exists() or os.path.lexists(path):
                raise GuardError(
                    "discovered OpenCode config source cannot be inspected and "
                    f"must not exist: {path}"
                )
            continue
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
        # Migration keys are a statement about the *main* document only.  On
        # the TUI document ``theme`` and ``keybinds`` are its declared schema
        # (``packages/tui/src/config/index.tsx:54-56``) and its expected
        # content — D10 writes a keybind backstop into the owned root two steps
        # before this scan runs.  Gating them here would refuse the guard's own
        # file and take every launch down with it.  Execution keys still apply
        # to both documents, which is the entire reason the TUI family is in
        # the table at all.
        if source.document == "main":
            for key in MIGRATION_KEYS:
                if key in payload:
                    raise GuardError(
                        "discovered OpenCode config carries a migration key: "
                        f"{path}#{key}"
                    )
        for execution in EXECUTION_KEYS:
            if execution.key in payload:
                raise GuardError(
                    "discovered OpenCode config carries an execution key: "
                    f"{path}#{execution.key}"
                )
    return [path for path, _ in scanned]


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

    migration_scan(
        cwd,
        xdg_config_home=xdg_config_home,
        test_home=test_home,
        environment=environment,
    )
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
