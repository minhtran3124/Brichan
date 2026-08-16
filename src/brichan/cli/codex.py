"""Codex runtime adapter."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ._root import checkout_root, exec_runtime, repository_root
from brichan import __version__
from brichan.lifecycle import StateKind, inspect_project
from brichan.orchestration.model_routing import (
    RoutingError,
    load_settings,
    resolve_coordinator,
)
from brichan.project import ProjectPaths, ProjectError, project_paths
from .provider_commands import codex_command, codex_project_command


def command(
    argv: list[str],
    environment: dict[str, str] | None = None,
    *,
    root: Path | None = None,
) -> list[str]:
    env = os.environ if environment is None else environment
    root = repository_root() if root is None else root
    settings = load_settings(repository=root, environment=env)
    route = resolve_coordinator(settings, "codex")
    return codex_command(route, argv, cwd=root)


def project_command(
    paths: ProjectPaths,
    argv: list[str],
    environment: dict[str, str] | None = None,
) -> list[str]:
    """Resolve a package-owned command for one initialized Git project."""

    env = os.environ if environment is None else environment
    inspection = inspect_project(paths)
    if inspection.kind is not StateKind.HEALTHY:
        raise RoutingError(
            f"project state is {inspection.kind.value}: {inspection.detail}"
        )
    settings = load_settings(
        paths.state_root / "config" / "model-routing.json",
        environment=env,
    )
    route = resolve_coordinator(settings, "codex")
    bootstrap_path = paths.state_root / "policy" / "bootstrap.md"
    try:
        bootstrap = bootstrap_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RoutingError(f"cannot read Brichan bootstrap policy: {exc}") from exc
    developer_instructions = (
        f"{bootstrap.rstrip()}\n\n"
        f"Target project root: {paths.project_root}\n"
        f"Mutable Brichan state root: {paths.state_root}\n"
        "Use only package-owned Brichan launchers; never execute target-repository "
        "bin/brichan-* wrappers."
    )
    return codex_project_command(
        route,
        argv,
        cwd=paths.project_root,
        developer_instructions=developer_instructions,
        skill_path=paths.state_root / "skills" / "herdr-orchestration",
    )


def run_project(
    paths: ProjectPaths,
    argv: list[str],
    environment: dict[str, str] | None = None,
) -> int:
    resolved_command = project_command(paths, argv, environment)
    os.chdir(paths.project_root)
    return exec_runtime("codex", resolved_command, owner="brichan")


def main(argv: list[str] | None = None) -> int:
    """Installed console-script entrypoint; never enters checkout mode.

    Only an initialized project discovered from the working directory can be
    launched, and it is always launched through the managed `project_command`
    path, which keeps the bootstrap policy, skill injection, and the
    installed-project option allowlist.
    """

    arguments = sys.argv[1:] if argv is None else argv
    try:
        paths = project_paths()
    except ProjectError:
        paths = None
    if paths is not None and paths.state_root.exists():
        try:
            return run_project(paths, arguments, os.environ)
        except RoutingError as exc:
            print(f"brichan-codex: {exc}", file=sys.stderr)
            return 2
    if arguments[:1] in (["--help"], ["-h"]):
        print("usage: brichan-codex [codex arguments...]")
        print()
        print(
            "brichan-codex is checkout-oriented: run the checkout's own "
            "bin/brichan-codex wrapper, or run this installed command inside a "
            "Git project initialized with 'brichan init --apply'."
        )
        return 0
    if arguments[:1] in (["--version"], ["-V"]):
        print(f"brichan-codex {__version__}")
        return 0
    print(
        "brichan-codex: no initialized project here; run "
        "'brichan init --apply --project PATH' first",
        file=sys.stderr,
    )
    return 2


def checkout_main(root: Path | str, argv: list[str] | None = None) -> int:
    """Source-checkout entrypoint, reached only from `bin/brichan-codex`."""

    arguments = sys.argv[1:] if argv is None else argv
    try:
        resolved_command = command(
            arguments, os.environ, root=checkout_root(root)
        )
    except (OSError, RuntimeError, RoutingError) as exc:
        print(f"brichan-codex: {exc}", file=sys.stderr)
        return 2
    return exec_runtime("codex", resolved_command, owner="brichan-codex")


if __name__ == "__main__":
    raise SystemExit(main())
