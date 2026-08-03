"""Provider-neutral Brichan runtime dispatcher."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from ._root import exec_runtime
from .codex import run_project
from .render import (
    DOCTOR_DESCRIPTION,
    DOCTOR_JSON_HELP,
    INIT_DESCRIPTION,
    STATUS_DESCRIPTION,
    format_doctor_json,
    format_doctor_text,
    format_init,
    resolve_style,
)
from brichan import __version__
from brichan.lifecycle import (
    StateKind,
    doctor_report,
    initialize_project,
    inspect_project,
    status_lines,
)
from brichan.orchestration.model_routing import (
    RoutingError,
    load_settings,
)
from brichan.project import ProjectError, package_root, project_paths


def select_runtime(
    argv: list[str],
    environment: dict[str, str],
    default_runtime: str,
) -> tuple[str, list[str]]:
    runtime = environment.get("BRICHAN_RUNTIME") or default_runtime
    remaining = list(argv)
    if remaining[:1] == ["--runtime"]:
        if len(remaining) < 2:
            raise ValueError("usage: brichan [--runtime codex|claude] [arguments...]")
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
        prog=f"brichan {command_name}",
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
            help="create the documented .brichan footprint",
        )
        mode.add_argument(
            "--dry-run",
            action="store_true",
            help="preview the footprint with zero writes (default)",
        )
    if command_name == "doctor":
        parser.add_argument("--json", action="store_true", help=DOCTOR_JSON_HELP)
    args = parser.parse_args(argv)
    try:
        paths = project_paths(explicit=args.project)
    except ProjectError as exc:
        print(f"brichan {command_name}: {exc}", file=sys.stderr)
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
    elif args.json:
        code, report = doctor_report(paths, checkout_root=_checkout_root())
        # Written rather than printed so the document ends in exactly one
        # newline, whatever the platform.
        sys.stdout.write(format_doctor_json(report))
        return code
    else:
        code, report = doctor_report(paths, checkout_root=_checkout_root())
        lines = format_doctor_text(
            report,
            style=resolve_style(sys.stdout, os.environ),
        )
    _print_lines(lines)
    return code


def _run_command(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="brichan run", add_help=True)
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
        print(f"brichan run: {exc}", file=sys.stderr)
        return 2


def _checkout_root() -> Path | None:
    override = os.environ.get("BRICHAN_ROOT")
    if not override:
        return None
    root = Path(override).expanduser().resolve()
    source_package = root / "src" / "brichan"
    if not (root / "bin" / "brichan").is_file():
        return None
    if source_package != package_root():
        return None
    return root


def _global_help_lines() -> list[str]:
    return [
        "usage: brichan [--runtime codex|claude] [prompt...]",
        "       brichan init|status|doctor [--project PATH] [--apply|--dry-run]",
        "       brichan run --project PATH -- <codex arguments>",
        "",
        "Installed-project mode launches Codex inside an initialized Git",
        "repository. Run 'brichan init --apply --project PATH' first.",
        "",
        "Inside a healthy initialized project, --help/--version are instead",
        "forwarded to codex as documented CLI overrides. From a source",
        "checkout they report Brichan; use bin/brichan-codex --help for codex.",
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
        print(f"brichan: {exc}", file=sys.stderr)
        return 2


def _brichan_help_or_version(argv: list[str]) -> int | None:
    """Answer a request for Brichan's own help/version; None if it is not one.

    Shared by both dispatch modes so `brichan --help` cannot mean one thing in
    a source checkout and another outside it.
    """
    if argv[:1] in (["--help"], ["-h"]):
        _print_lines(_global_help_lines())
        return 0
    if argv[:1] in (["--version"], ["-V"]):
        print(f"brichan {__version__}")
        return 0
    return None


def _unavailable_response(argv: list[str], error: str | None) -> int | None:
    """Handle --help/--version pre-launch; return None to fall through."""

    response = _brichan_help_or_version(argv)
    if response is not None:
        return response
    if error is None:
        return None
    print(f"brichan: {error}", file=sys.stderr)
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

    # A checkout has no project state to launch into, so `brichan --help` here
    # is a question about Brichan. `bin/brichan-<runtime> --help` still reaches
    # the runtime's own help.
    response = _brichan_help_or_version(arguments)
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

    # _checkout_root only guarantees bin/brichan, so the per-runtime wrapper may
    # be absent in a partial checkout.
    executable = root / "bin" / f"brichan-{runtime}"
    return exec_runtime(
        str(executable), [str(executable), *remaining], owner="brichan"
    )


if __name__ == "__main__":
    raise SystemExit(main())
