"""Provider-neutral Brida runtime dispatcher."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .codex import run_project
from brida.lifecycle import doctor_lines, initialize_project, status_lines
from brida.orchestration.model_routing import (
    RoutingError,
    load_settings,
)
from brida.project import ProjectError, package_root, project_paths


def select_runtime(
    argv: list[str],
    environment: dict[str, str],
    default_runtime: str,
) -> tuple[str, list[str]]:
    runtime = environment.get("BRIDA_RUNTIME") or default_runtime
    remaining = list(argv)
    if remaining[:1] == ["--runtime"]:
        if len(remaining) < 2:
            raise ValueError("usage: brida [--runtime codex|claude] [arguments...]")
        runtime = remaining[1]
        remaining = remaining[2:]
    elif remaining and remaining[0].startswith("--runtime="):
        runtime = remaining[0].split("=", 1)[1]
        remaining = remaining[1:]
    if runtime not in {"codex", "claude"}:
        raise ValueError(
            f"unsupported runtime: {runtime} (expected codex or claude)"
        )
    return runtime, remaining


def _print_lines(lines: list[str]) -> None:
    for line in lines:
        print(line)


def _lifecycle_command(command_name: str, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog=f"brida {command_name}")
    parser.add_argument(
        "--project",
        type=Path,
        help="explicit top-level Git repository (defaults to discovery from cwd)",
    )
    if command_name == "init":
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument(
            "--apply",
            action="store_true",
            help="create the documented .brida footprint",
        )
        mode.add_argument(
            "--dry-run",
            action="store_true",
            help="preview the footprint with zero writes (default)",
        )
    args = parser.parse_args(argv)
    try:
        paths = project_paths(explicit=args.project)
    except ProjectError as exc:
        print(f"brida {command_name}: {exc}", file=sys.stderr)
        return 2

    if command_name == "init":
        code, lines = initialize_project(paths, apply=args.apply)
    elif command_name == "status":
        code, lines = status_lines(paths)
    else:
        code, lines = doctor_lines(paths)
    _print_lines(lines)
    return code


def _run_command(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="brida run", add_help=True)
    parser.add_argument(
        "--project",
        type=Path,
        help="explicit top-level Git repository (defaults to discovery from cwd)",
    )
    args, passthrough = parser.parse_known_args(argv)
    try:
        paths = project_paths(explicit=args.project)
        return run_project(paths, passthrough, os.environ)
    except (ProjectError, RoutingError) as exc:
        print(f"brida run: {exc}", file=sys.stderr)
        return 2


def _checkout_root() -> Path | None:
    override = os.environ.get("BRIDA_ROOT")
    if not override:
        return None
    root = Path(override).expanduser().resolve()
    source_package = root / "src" / "brida"
    if not (root / "bin" / "brida").is_file():
        return None
    if source_package != package_root():
        return None
    return root


def _installed_default(argv: list[str]) -> int:
    try:
        paths = project_paths()
        runtime, remaining = select_runtime(argv, os.environ, "codex")
        if runtime != "codex":
            raise ValueError(
                "installed-project dogfood supports only the codex runtime"
            )
        return run_project(paths, remaining, os.environ)
    except (ProjectError, RoutingError, ValueError) as exc:
        print(f"brida: {exc}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments[:1] and arguments[0] in {"init", "status", "doctor"}:
        return _lifecycle_command(arguments[0], arguments[1:])
    if arguments[:1] == ["run"]:
        return _run_command(arguments[1:])
    root = _checkout_root()
    if root is None:
        return _installed_default(arguments)

    try:
        settings = load_settings(repository=root, environment=os.environ)
        runtime, remaining = select_runtime(
            arguments,
            os.environ,
            settings.default_runtime,
        )
    except (RoutingError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2

    executable = root / "bin" / f"brida-{runtime}"
    os.execv(str(executable), [str(executable), *remaining])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
