"""Codex runtime adapter."""

from __future__ import annotations

import os
import sys

from ._root import repository_root
from brida import __version__
from brida.lifecycle import StateKind, inspect_project
from brida.orchestration.model_routing import (
    RoutingError,
    load_settings,
    resolve_coordinator,
)
from brida.project import ProjectPaths, ProjectError, project_paths
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
        raise RoutingError(f"cannot read Brida bootstrap policy: {exc}") from exc
    developer_instructions = (
        f"{bootstrap.rstrip()}\n\n"
        f"Target project root: {paths.project_root}\n"
        f"Mutable Brida state root: {paths.state_root}\n"
        "Use only package-owned Brida launchers; never execute target-repository "
        "bin/brida-* wrappers."
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
    os.execvp("codex", resolved_command)
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    try:
        paths = project_paths()
        if paths.state_root.exists():
            return run_project(paths, arguments, os.environ)
    except (ProjectError, RoutingError) as exc:
        if not isinstance(exc, ProjectError):
            print(f"brida-codex: {exc}", file=sys.stderr)
            return 2
        pass
    try:
        resolved_command = command(arguments, os.environ)
    except RoutingError as exc:
        print(f"brida-codex: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        if arguments[:1] in (["--help"], ["-h"]):
            print("usage: brida-codex [codex arguments...]")
            print()
            print(
                "brida-codex is checkout-oriented: run it from within the "
                "Brida source checkout (or with BRIDA_ROOT set), or inside a "
                "Git project initialized with 'brida init --apply' for the "
                "installed-project workflow."
            )
            return 0
        if arguments[:1] in (["--version"], ["-V"]):
            print(f"brida-codex {__version__}")
            return 0
        print(f"brida-codex: {exc}", file=sys.stderr)
        return 2
    os.execvp("codex", resolved_command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
