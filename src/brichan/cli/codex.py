"""Codex runtime adapter."""

from __future__ import annotations

import os
import sys

from ._root import exec_runtime, repository_root
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
) -> list[str]:
    env = os.environ if environment is None else environment
    root = repository_root()
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
    arguments = sys.argv[1:] if argv is None else argv
    try:
        paths = project_paths()
        if paths.state_root.exists():
            return run_project(paths, arguments, os.environ)
    except (ProjectError, RoutingError) as exc:
        if not isinstance(exc, ProjectError):
            print(f"brichan-codex: {exc}", file=sys.stderr)
            return 2
        pass
    try:
        resolved_command = command(arguments, os.environ)
    except RoutingError as exc:
        print(f"brichan-codex: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        if arguments[:1] in (["--help"], ["-h"]):
            print("usage: brichan-codex [codex arguments...]")
            print()
            print(
                "brichan-codex is checkout-oriented: run it from within the "
                "Brichan source checkout (or with BRICHAN_ROOT set), or inside a "
                "Git project initialized with 'brichan init --apply' for the "
                "installed-project workflow."
            )
            return 0
        if arguments[:1] in (["--version"], ["-V"]):
            print(f"brichan-codex {__version__}")
            return 0
        print(f"brichan-codex: {exc}", file=sys.stderr)
        return 2
    return exec_runtime("codex", resolved_command, owner="brichan-codex")


if __name__ == "__main__":
    raise SystemExit(main())
