"""Provider-neutral Brida runtime dispatcher."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from ._root import exec_runtime
from .codex import run_project
from .render import (
    DOCTOR_DESCRIPTION,
    INIT_DESCRIPTION,
    STATUS_DESCRIPTION,
    format_init,
    resolve_style,
)
from brida import __version__
from brida.lifecycle import (
    StateKind,
    doctor_lines,
    initialize_project,
    inspect_project,
    status_lines,
)
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


LIFECYCLE_DESCRIPTIONS = {
    "init": INIT_DESCRIPTION,
    "status": STATUS_DESCRIPTION,
    "doctor": DOCTOR_DESCRIPTION,
}


def _print_lines(lines: list[str]) -> None:
    for line in lines:
        print(line)


def _lifecycle_command(command_name: str, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog=f"brida {command_name}",
        description=LIFECYCLE_DESCRIPTIONS.get(command_name),
    )
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
        lines = format_init(
            lines,
            project_root=str(paths.project_root),
            apply=args.apply,
            style=resolve_style(sys.stdout, os.environ),
        )
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


def _global_help_lines() -> list[str]:
    return [
        "usage: brida [--runtime codex|claude] [prompt...]",
        "       brida init|status|doctor [--project PATH] [--apply|--dry-run]",
        "       brida run --project PATH -- <codex arguments>",
        "",
        "Installed-project mode launches Codex inside an initialized Git",
        "repository. Run 'brida init --apply --project PATH' first.",
        "",
        "Inside a healthy initialized project, --help/--version are instead",
        "forwarded to codex as documented CLI overrides. From a source",
        "checkout they report Brida; use bin/brida-codex --help for codex.",
    ]


def _installed_default(argv: list[str]) -> int:
    try:
        paths = project_paths()
    except ProjectError as exc:
        return _unavailable_response(argv, str(exc))

    if inspect_project(paths).kind != StateKind.HEALTHY:
        response = _unavailable_response(argv, None)
        if response is not None:
            return response

    try:
        runtime, remaining = select_runtime(argv, os.environ, "codex")
        if runtime != "codex":
            raise ValueError(
                "installed-project dogfood supports only the codex runtime"
            )
        return run_project(paths, remaining, os.environ)
    except (RoutingError, ValueError) as exc:
        print(f"brida: {exc}", file=sys.stderr)
        return 2


def _brida_help_or_version(argv: list[str]) -> int | None:
    """Answer a request for Brida's own help/version; None if it is not one.

    Shared by both dispatch modes so `brida --help` cannot mean one thing in
    a source checkout and another outside it.
    """
    if argv[:1] in (["--help"], ["-h"]):
        _print_lines(_global_help_lines())
        return 0
    if argv[:1] in (["--version"], ["-V"]):
        print(f"brida {__version__}")
        return 0
    return None


def _unavailable_response(argv: list[str], error: str | None) -> int | None:
    """Handle --help/--version pre-launch; return None to fall through."""

    response = _brida_help_or_version(argv)
    if response is not None:
        return response
    if error is None:
        return None
    print(f"brida: {error}", file=sys.stderr)
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

    # A checkout has no project state to launch into, so `brida --help` here
    # is a question about Brida. `bin/brida-<runtime> --help` still reaches
    # the runtime's own help.
    response = _brida_help_or_version(arguments)
    if response is not None:
        return response

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

    # _checkout_root only guarantees bin/brida, so the per-runtime wrapper may
    # be absent in a partial checkout.
    executable = root / "bin" / f"brida-{runtime}"
    return exec_runtime(
        str(executable), [str(executable), *remaining], owner="brida"
    )


if __name__ == "__main__":
    raise SystemExit(main())
