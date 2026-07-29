"""Translate resolved routes into guarded provider-native commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from brida.orchestration.model_routing import (
    ResolvedRoute,
    RoutingError,
    validate_effort,
    validate_model,
)


CODEX_NATIVE_AGENT_FLAGS = (
    "-c",
    "agents.enabled=false",
    "--disable",
    "multi_agent",
    "--disable",
    "multi_agent_v2",
)
CLAUDE_NATIVE_AGENT_FLAGS = ("--disallowed-tools=Task",)
PROJECT_SAFE_CONFIG_KEYS = frozenset({"model", "model_reasoning_effort"})
PROJECT_SAFE_FLAGS = frozenset(
    {"-h", "--help", "-V", "--version", "--no-alt-screen", "--strict-config"}
)
PROJECT_FORBIDDEN_COMMANDS = frozenset(
    {
        "app",
        "app-server",
        "apply",
        "archive",
        "cloud",
        "completion",
        "debug",
        "delete",
        "doctor",
        "exec",
        "exec-server",
        "features",
        "fork",
        "login",
        "logout",
        "mcp",
        "mcp-server",
        "plugin",
        "remote-control",
        "resume",
        "review",
        "sandbox",
        "unarchive",
        "update",
    }
)


def _option_value(item: str, name: str) -> str | None:
    """Return a value for one supported option spelling, if present."""

    if item.startswith(f"{name}="):
        return item.split("=", 1)[1]
    if len(name) == 2 and item.startswith(name) and len(item) > len(name):
        return item[len(name) :]
    return None


def _option_prefix(argv: list[str]) -> list[str]:
    return argv[: argv.index("--")] if "--" in argv else argv


def _has_option(argv: list[str], names: set[str]) -> bool:
    return any(
        item == name or _option_value(item, name) is not None
        for item in _option_prefix(argv)
        for name in names
    )


def _value_after(argv: list[str], names: set[str]) -> Iterable[tuple[str, str]]:
    index = 0
    while index < len(argv):
        item = argv[index]
        if item == "--":
            break
        if item in names:
            if index + 1 >= len(argv):
                raise RoutingError(f"{item} requires a value")
            yield item, argv[index + 1]
            index += 2
            continue
        for name in names:
            value = _option_value(item, name)
            if value is not None:
                if not value:
                    raise RoutingError(f"{name} requires a value")
                yield name, value
                break
        index += 1


def _config_assignments(argv: list[str]) -> list[str]:
    return [value for _, value in _value_after(argv, {"-c", "--config"})]


def _assignment_key_value(assignment: str) -> tuple[str, str]:
    if "=" not in assignment:
        raise RoutingError("Codex configuration overrides must use key=value")
    key, value = assignment.split("=", 1)
    return key.strip(), value.strip().strip("\"'")


def _namespace_matches(key: str, namespace: str) -> bool:
    return (
        key == namespace
        or key.startswith(f"{namespace}.")
        or key.startswith(f"{namespace}[")
    )


def _project_config_assignments(argv: list[str]) -> list[tuple[str, str]]:
    assignments = [
        _assignment_key_value(item) for item in _config_assignments(argv)
    ]
    for key, _ in assignments:
        if _namespace_matches(key, "developer_instructions") or _namespace_matches(
            key, "skills.config"
        ):
            raise RoutingError(
                f"Brida project launch owns the Codex setting namespace: {key}"
            )
        if key not in PROJECT_SAFE_CONFIG_KEYS:
            raise RoutingError(
                f"Codex setting is forbidden in installed project mode: {key}"
            )
    return assignments


def _validate_project_passthrough(argv: list[str]) -> None:
    """Allow only bounded interactive-project arguments before `--`."""

    index = 0
    saw_positional = False
    while index < len(argv):
        item = argv[index]
        if item == "--":
            return
        if item in PROJECT_SAFE_FLAGS:
            index += 1
            continue
        if item in {"-m", "--model", "-c", "--config"}:
            if index + 1 >= len(argv):
                raise RoutingError(f"{item} requires a value")
            index += 2
            continue
        if any(
            _option_value(item, name) is not None
            for name in ("-m", "--model", "-c", "--config")
        ):
            index += 1
            continue
        if item.startswith("-"):
            raise RoutingError(
                f"Codex option is forbidden in installed project mode: {item}"
            )
        if not saw_positional and item in PROJECT_FORBIDDEN_COMMANDS:
            raise RoutingError(
                f"Codex subcommand is forbidden in installed project mode: {item}"
            )
        saw_positional = True
        index += 1


def _reject_codex_native_delegation(argv: list[str]) -> None:
    for _, feature in _value_after(argv, {"--enable"}):
        if feature in {"multi_agent", "multi_agent_v2", "agents"}:
            raise RoutingError(f"Codex native delegation cannot be enabled: {feature}")
    for assignment in _config_assignments(argv):
        key, value = _assignment_key_value(assignment)
        if key in {
            "agents.enabled",
            "features.multi_agent",
            "features.multi_agent_v2",
        } and value.lower() != "false":
            raise RoutingError(f"Codex native delegation setting is forbidden: {key}")


def _reject_codex_permission_bypass(argv: list[str]) -> None:
    forbidden = {
        "--dangerously-bypass-approvals-and-sandbox",
        "--dangerously-bypass-hook-trust",
    }
    if any(
        item.split("=", 1)[0] in forbidden for item in _option_prefix(argv)
    ):
        raise RoutingError("Codex permission-bypass options are forbidden")
    for _, value in _value_after(argv, {"-s", "--sandbox"}):
        if value == "danger-full-access":
            raise RoutingError("Codex danger-full-access sandbox is forbidden")
    for assignment in _config_assignments(argv):
        key, value = _assignment_key_value(assignment)
        if key == "sandbox_mode" and value == "danger-full-access":
            raise RoutingError("Codex danger-full-access sandbox is forbidden")


def _reject_legacy_codex_scope_widening(argv: list[str]) -> None:
    if _has_option(argv, {"-p", "--profile"}):
        raise RoutingError("Codex profile options are forbidden in legacy commands")
    if _has_option(argv, {"--add-dir"}):
        raise RoutingError("Codex extra directory options are forbidden in legacy commands")


def _reject_claude_native_delegation(argv: list[str]) -> None:
    forbidden = {
        "--agent",
        "--agents",
        "--bg",
        "--background",
        "--forward-subagent-text",
    }
    prefix = _option_prefix(argv)
    for item in prefix:
        name = item.split("=", 1)[0]
        if name in forbidden:
            raise RoutingError(f"Claude native delegation option is forbidden: {name}")
    if prefix[:1] == ["agents"]:
        raise RoutingError("Claude native agent commands are forbidden")


def _reject_claude_permission_bypass(argv: list[str]) -> None:
    forbidden = {
        "--allow-dangerously-skip-permissions",
        "--dangerously-skip-permissions",
    }
    if any(
        item.split("=", 1)[0] in forbidden for item in _option_prefix(argv)
    ):
        raise RoutingError("Claude permission-bypass options are forbidden")
    for _, mode in _value_after(argv, {"--permission-mode"}):
        if mode == "bypassPermissions":
            raise RoutingError("Claude bypassPermissions mode is forbidden")


def _reject_legacy_claude_hook_overrides(argv: list[str]) -> None:
    if _has_option(argv, {"--bare"}):
        raise RoutingError("Claude bare mode is forbidden in legacy commands")
    if _has_option(argv, {"--tools"}):
        raise RoutingError("Claude tool-list overrides are forbidden in legacy commands")
    if _has_option(argv, {"--allowedTools", "--allowed-tools"}):
        raise RoutingError("Claude allowed-tool overrides are forbidden in legacy commands")
    if _has_option(argv, {"--disallowedTools", "--disallowed-tools"}):
        raise RoutingError("Claude disallowed-tool overrides are forbidden in legacy commands")


def _validate_codex_overrides(argv: list[str], label: str) -> list[tuple[str, str]]:
    assignments = [_assignment_key_value(item) for item in _config_assignments(argv)]
    for key, value in assignments:
        if key == "model":
            validate_model(value, f"{label} model")
        if key == "model_reasoning_effort":
            validate_effort("codex", value, f"{label} effort")
    for _, model in _value_after(argv, {"-m", "--model"}):
        validate_model(model, f"{label} model")
    return assignments


def codex_command(
    route: ResolvedRoute,
    argv: list[str] | None = None,
    *,
    cwd: Path | None = None,
) -> list[str]:
    if route.runtime != "codex":
        raise RoutingError("Codex command requires a codex route")
    passthrough = [] if argv is None else list(argv)
    _reject_codex_native_delegation(passthrough)
    _reject_codex_permission_bypass(passthrough)
    assignments = _validate_codex_overrides(passthrough, "Codex override")
    command = ["codex"]
    if cwd is not None:
        command.extend(["-C", str(cwd)])
    command.extend(CODEX_NATIVE_AGENT_FLAGS)
    if not _has_option(passthrough, {"-m", "--model"}) and not any(
        key == "model" for key, _ in assignments
    ):
        command.extend(["--model", route.model])
    if not any(key == "model_reasoning_effort" for key, _ in assignments):
        command.extend(["-c", f"model_reasoning_effort={route.effort}"])
    command.extend(passthrough)
    return command


def codex_project_command(
    route: ResolvedRoute,
    argv: list[str],
    *,
    cwd: Path,
    developer_instructions: str,
    skill_path: Path,
) -> list[str]:
    """Build a guarded Codex command for an initialized target project."""

    _validate_project_passthrough(argv)
    _project_config_assignments(argv)
    command = codex_command(route, argv, cwd=cwd)
    passthrough_count = len(argv)
    insertion = len(command) - passthrough_count if passthrough_count else len(command)
    bootstrap = (
        f"developer_instructions={json.dumps(developer_instructions)}"
    )
    skill = (
        "skills.config=[{path="
        f"{json.dumps(str(skill_path.resolve()))},enabled=true"
        "}]"
    )
    command[insertion:insertion] = ["-c", bootstrap, "-c", skill]
    return command


def claude_command(
    route: ResolvedRoute,
    argv: list[str] | None = None,
    *,
    worker: bool = False,
) -> list[str]:
    if route.runtime != "claude":
        raise RoutingError("Claude command requires a claude route")
    passthrough = [] if argv is None else list(argv)
    _reject_claude_native_delegation(passthrough)
    _reject_claude_permission_bypass(passthrough)
    for _, model in _value_after(passthrough, {"--model"}):
        validate_model(model, "Claude model override")
    for _, effort in _value_after(passthrough, {"--effort"}):
        validate_effort("claude", effort, "Claude effort override")
    command = ["claude"]
    if worker and not _has_option(passthrough, {"--permission-mode"}):
        command.extend(["--permission-mode", "auto"])
    if not _has_option(passthrough, {"--model"}):
        command.extend(["--model", route.model])
    if not _has_option(passthrough, {"--effort"}):
        command.extend(["--effort", route.effort])
    command.extend(CLAUDE_NATIVE_AGENT_FLAGS)
    command.extend(passthrough)
    return command


def worker_command(route: ResolvedRoute) -> list[str]:
    if route.runtime == "codex":
        return codex_command(route)
    if route.runtime == "claude":
        return claude_command(route, worker=True)
    raise RoutingError(f"unsupported worker runtime: {route.runtime}")


def secure_legacy_command(argv: list[str]) -> list[str]:
    """Validate and guard the documented explicit-command compatibility path."""

    if not argv:
        raise RoutingError("legacy agent command is empty")
    runtime, arguments = argv[0], list(argv[1:])
    if runtime == "codex":
        _reject_legacy_codex_scope_widening(arguments)
        _reject_codex_permission_bypass(arguments)
        assignments = _validate_codex_overrides(arguments, "legacy Codex")
        allowed_keys = {
            "model",
            "model_reasoning_effort",
            "agents.enabled",
            "features.multi_agent",
            "features.multi_agent_v2",
        }
        for key, _ in assignments:
            if key not in allowed_keys:
                raise RoutingError(
                    f"arbitrary Codex setting is forbidden in legacy commands: {key}"
                )
        _reject_codex_native_delegation(arguments)
        return ["codex", *CODEX_NATIVE_AGENT_FLAGS, *arguments]

    if runtime == "claude":
        if any(
            item.split("=", 1)[0] == "--settings"
            for item in _option_prefix(arguments)
        ):
            raise RoutingError("Claude settings options are forbidden in legacy commands")
        _reject_legacy_claude_hook_overrides(arguments)
        _reject_claude_permission_bypass(arguments)
        for _, model in _value_after(arguments, {"--model"}):
            validate_model(model, "legacy Claude model")
        for _, effort in _value_after(arguments, {"--effort"}):
            validate_effort("claude", effort, "legacy Claude effort")
        _reject_claude_native_delegation(arguments)
        command = ["claude"]
        if not _has_option(arguments, {"--permission-mode"}):
            command.extend(["--permission-mode", "auto"])
        command.extend(CLAUDE_NATIVE_AGENT_FLAGS)
        command.extend(arguments)
        return command

    raise RoutingError(
        f"unsupported legacy worker runtime {runtime!r}; expected codex or claude"
    )
