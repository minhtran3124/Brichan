"""Load and resolve Brichan's provider-neutral model-routing settings."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
SUPPORTED_RUNTIMES = frozenset({"codex", "claude"})
SUPPORTED_EFFORTS = {
    "codex": frozenset({"low", "medium", "high", "xhigh", "max"}),
    "claude": frozenset({"low", "medium", "high", "xhigh", "max"}),
}
REQUIRED_ROUTES = frozenset({"plan", "implement", "review", "scan"})
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")


class RoutingError(ValueError):
    """Raised when routing settings or overrides are invalid."""


@dataclass(frozen=True)
class ResolvedRoute:
    runtime: str
    model: str
    effort: str

    def as_dict(self) -> dict[str, str]:
        return {
            "runtime": self.runtime,
            "model": self.model,
            "effort": self.effort,
        }


@dataclass(frozen=True)
class RoutingSettings:
    default_runtime: str
    coordinators: Mapping[str, ResolvedRoute]
    routes: Mapping[str, ResolvedRoute]


def _expect_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RoutingError(f"{location} must be a JSON object")
    return value


def _expect_exact_keys(
    value: Mapping[str, Any],
    expected: set[str] | frozenset[str],
    location: str,
) -> None:
    actual = set(value)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        raise RoutingError(f"{location} is missing required keys: {', '.join(missing)}")
    if unexpected:
        raise RoutingError(
            f"{location} contains unsupported keys: {', '.join(unexpected)}"
        )


def validate_runtime(runtime: Any, location: str = "runtime") -> str:
    if not isinstance(runtime, str) or runtime not in SUPPORTED_RUNTIMES:
        choices = ", ".join(sorted(SUPPORTED_RUNTIMES))
        raise RoutingError(f"{location} must be one of: {choices}")
    return runtime


def validate_model(model: Any, location: str = "model") -> str:
    if not isinstance(model, str) or not MODEL_PATTERN.fullmatch(model):
        raise RoutingError(
            f"{location} must be a non-empty model identifier without whitespace"
        )
    return model


def validate_effort(
    runtime: str,
    effort: Any,
    location: str = "effort",
) -> str:
    validate_runtime(runtime, f"{location} runtime")
    if not isinstance(effort, str) or effort not in SUPPORTED_EFFORTS[runtime]:
        choices = ", ".join(sorted(SUPPORTED_EFFORTS[runtime]))
        if runtime == "codex" and effort == "ultra":
            raise RoutingError(
                f"{location} cannot be ultra for a Codex worker because it can "
                "enable automatic delegation"
            )
        raise RoutingError(
            f"{location} is unsupported for {runtime}; expected one of: {choices}"
        )
    return effort


def _parse_route(value: Any, location: str) -> ResolvedRoute:
    route = _expect_object(value, location)
    _expect_exact_keys(route, {"runtime", "model", "effort"}, location)
    runtime = validate_runtime(route["runtime"], f"{location}.runtime")
    return ResolvedRoute(
        runtime=runtime,
        model=validate_model(route["model"], f"{location}.model"),
        effort=validate_effort(runtime, route["effort"], f"{location}.effort"),
    )


def parse_settings(payload: Any) -> RoutingSettings:
    root = _expect_object(payload, "settings")
    _expect_exact_keys(root, {"schema_version", "coordinator", "routes"}, "settings")
    if (
        type(root["schema_version"]) is not int
        or root["schema_version"] != SCHEMA_VERSION
    ):
        raise RoutingError(
            f"settings.schema_version must be {SCHEMA_VERSION}, "
            f"got {root['schema_version']!r}"
        )

    coordinator = _expect_object(root["coordinator"], "settings.coordinator")
    _expect_exact_keys(
        coordinator,
        {"default_runtime", "runtimes"},
        "settings.coordinator",
    )
    default_runtime = validate_runtime(
        coordinator["default_runtime"],
        "settings.coordinator.default_runtime",
    )
    runtime_values = _expect_object(
        coordinator["runtimes"],
        "settings.coordinator.runtimes",
    )
    _expect_exact_keys(
        runtime_values,
        SUPPORTED_RUNTIMES,
        "settings.coordinator.runtimes",
    )
    coordinators: dict[str, ResolvedRoute] = {}
    for runtime, value in runtime_values.items():
        location = f"settings.coordinator.runtimes.{runtime}"
        defaults = _expect_object(value, location)
        _expect_exact_keys(defaults, {"model", "effort"}, location)
        coordinators[runtime] = ResolvedRoute(
            runtime=runtime,
            model=validate_model(defaults["model"], f"{location}.model"),
            effort=validate_effort(runtime, defaults["effort"], f"{location}.effort"),
        )

    route_values = _expect_object(root["routes"], "settings.routes")
    _expect_exact_keys(route_values, REQUIRED_ROUTES, "settings.routes")
    routes = {
        name: _parse_route(value, f"settings.routes.{name}")
        for name, value in route_values.items()
    }
    return RoutingSettings(
        default_runtime=default_runtime,
        coordinators=coordinators,
        routes=routes,
    )


def settings_path(
    repository: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> Path:
    env = os.environ if environment is None else environment
    override = env.get("BRICHAN_MODEL_ROUTING_FILE")
    if override:
        return Path(override).expanduser().resolve()
    if repository is not None:
        root = repository
    elif env.get("BRICHAN_ROOT"):
        root = Path(env["BRICHAN_ROOT"])
    else:
        root = Path(__file__).resolve().parents[3]
    resolved_root = root.resolve()
    installed_project_settings = (
        resolved_root / ".brichan" / "config" / "model-routing.json"
    )
    if installed_project_settings.is_file():
        return installed_project_settings
    return resolved_root / "config" / "model-routing.json"


def load_settings(
    path: Path | None = None,
    *,
    repository: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> RoutingSettings:
    source = path or settings_path(repository, environment)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise RoutingError(f"cannot read routing settings {source}: {exc}") from exc
    try:
        payload = json.loads(text, object_pairs_hook=_unique_object)
    except json.JSONDecodeError as exc:
        raise RoutingError(
            f"routing settings {source} contain malformed JSON: "
            f"line {exc.lineno}, column {exc.colno}"
        ) from exc
    return parse_settings(payload)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RoutingError(f"routing settings contain duplicate key: {key}")
        value[key] = item
    return value


def _apply_overrides(
    route: ResolvedRoute,
    *,
    runtime: str | None,
    model: str | None,
    effort: str | None,
) -> ResolvedRoute:
    resolved_runtime = (
        route.runtime if runtime is None else validate_runtime(runtime, "runtime override")
    )
    if runtime is not None and runtime != route.runtime and model is None:
        raise RoutingError(
            "model override is required when changing a route's runtime"
        )
    resolved_model = (
        route.model if model is None else validate_model(model, "model override")
    )
    resolved_effort = (
        route.effort
        if effort is None
        else validate_effort(resolved_runtime, effort, "effort override")
    )
    if runtime is not None and effort is None:
        validate_effort(resolved_runtime, resolved_effort, "resolved effort")
    return ResolvedRoute(resolved_runtime, resolved_model, resolved_effort)


def resolve_route(
    settings: RoutingSettings,
    name: str,
    *,
    runtime: str | None = None,
    model: str | None = None,
    effort: str | None = None,
) -> ResolvedRoute:
    if name not in settings.routes:
        choices = ", ".join(sorted(settings.routes))
        raise RoutingError(f"unknown route {name!r}; expected one of: {choices}")
    return _apply_overrides(
        settings.routes[name],
        runtime=runtime,
        model=model,
        effort=effort,
    )


def resolve_coordinator(
    settings: RoutingSettings,
    runtime: str | None = None,
    *,
    model: str | None = None,
    effort: str | None = None,
) -> ResolvedRoute:
    resolved_runtime = settings.default_runtime if runtime is None else runtime
    validate_runtime(resolved_runtime, "coordinator runtime")
    return _apply_overrides(
        settings.coordinators[resolved_runtime],
        runtime=resolved_runtime,
        model=model,
        effort=effort,
    )
