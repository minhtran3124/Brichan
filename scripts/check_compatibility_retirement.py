#!/usr/bin/env python3
"""Validate and report the documentation-pointer retirement gate."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/compatibility-retirement.json"
REQUIRED_GATES = {
    "release_window",
    "external_links",
    "codex_startup",
    "claude_startup",
    "full_ci",
    "repository_search",
}
STATUSES = {"pass", "pending", "fail", "unavailable"}
EXPECTED_POINTERS = {
    "identity.md": "docs/policy/identity.md",
    "operating-principles.md": "docs/policy/operating-principles.md",
    "memory-policy.md": "docs/policy/memory-policy.md",
    "model-catalog.md": "docs/policy/model-catalog.md",
    "reviewer.md": "docs/policy/reviewer.md",
    "setup-status.md": "docs/history/setup-status.md",
}
VERSIONED_CHANGELOG_EVIDENCE = re.compile(
    r"^CHANGELOG\.md#\[(\d+)\.(\d+)\.(\d+)\]$"
)


def _repo_path(value: str) -> Path:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe repository-relative path: {value!r}")
    return ROOT / path


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    return config


def _parse_checked_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _validate_evidence(label: str, value: object) -> list[str]:
    if not isinstance(value, str) or "#" not in value:
        return [f"{label} must be a repository file plus #fragment"]
    path_value, fragment = value.split("#", 1)
    if not fragment:
        return [f"{label} requires a non-empty #fragment"]
    try:
        path = _repo_path(path_value)
    except (TypeError, ValueError) as exc:
        return [f"{label}: {exc}"]
    if not path.is_file():
        return [f"{label} file missing: {path_value}"]
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{label} cannot be read: {exc}"]
    if fragment not in content:
        return [f"{label} fragment not found in {path_value}: {fragment!r}"]
    return []


def _all_gates_pass(config: dict) -> bool:
    gates = config.get("gates", {})
    return (
        isinstance(gates, dict)
        and set(gates) == REQUIRED_GATES
        and all(
            isinstance(gates[name], dict)
            and gates[name].get("status") == "pass"
            for name in REQUIRED_GATES
        )
    )


def validate_config(config: dict) -> list[str]:
    errors: list[str] = []
    if config.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not config.get("migration_id"):
        errors.append("migration_id is required")
    if not isinstance(config.get("retired"), bool):
        errors.append("retired must be a boolean")

    temporary_paths = config.get("temporary_paths")
    if not isinstance(temporary_paths, list) or not temporary_paths:
        errors.append("temporary_paths must be a non-empty list")
        temporary_paths = []

    seen: set[str] = set()
    mappings: dict[str, str] = {}
    retired = config.get("retired") is True
    for index, mapping in enumerate(temporary_paths):
        label = f"temporary_paths[{index}]"
        if not isinstance(mapping, dict):
            errors.append(f"{label} must be an object")
            continue
        if set(mapping) != {"path", "canonical"}:
            errors.append(f"{label} must contain only path and canonical")
            continue
        try:
            temporary = _repo_path(mapping["path"])
            canonical = _repo_path(mapping["canonical"])
        except (TypeError, ValueError) as exc:
            errors.append(f"{label}: {exc}")
            continue
        if mapping["path"] in seen:
            errors.append(f"{label}: duplicate path {mapping['path']}")
        seen.add(mapping["path"])
        mappings[mapping["path"]] = mapping["canonical"]
        if not canonical.is_file():
            errors.append(f"{label}: canonical file missing: {mapping['canonical']}")
        if retired and (temporary.exists() or temporary.is_symlink()):
            errors.append(f"{label}: retired pointer still exists: {mapping['path']}")
        if not retired and not temporary.is_file():
            errors.append(f"{label}: active pointer missing: {mapping['path']}")
    if mappings != EXPECTED_POINTERS:
        errors.append(
            "temporary_paths must exactly match the protected policy-docs-v1 "
            "pointer mapping"
        )

    gates = config.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
        gates = {}
    missing_gates = sorted(REQUIRED_GATES - set(gates))
    extra_gates = sorted(set(gates) - REQUIRED_GATES)
    if missing_gates:
        errors.append("missing gates: " + ", ".join(missing_gates))
    if extra_gates:
        errors.append("unsupported gates: " + ", ".join(extra_gates))

    checked_at_by_gate: dict[str, datetime] = {}
    for name in sorted(REQUIRED_GATES & set(gates)):
        gate = gates[name]
        if not isinstance(gate, dict):
            errors.append(f"gates.{name} must be an object")
            continue
        status = gate.get("status")
        if status not in STATUSES:
            errors.append(f"gates.{name}.status must be one of {sorted(STATUSES)}")
        checked_at = gate.get("checked_at")
        evidence = gate.get("evidence")
        parsed_checked_at = _parse_checked_at(checked_at)
        if status == "pass":
            if parsed_checked_at is None:
                errors.append(
                    f"gates.{name}: pass requires a timezone-aware "
                    "ISO-8601 checked_at"
                )
            else:
                checked_at_by_gate[name] = parsed_checked_at
            errors.extend(
                _validate_evidence(f"gates.{name}.evidence", evidence)
            )
            if name == "release_window" and isinstance(evidence, str):
                if VERSIONED_CHANGELOG_EVIDENCE.fullmatch(evidence) is None:
                    errors.append(
                        "gates.release_window.evidence must reference a "
                        "versioned CHANGELOG section"
                    )

    release_checked_at = checked_at_by_gate.get("release_window")
    if release_checked_at is not None:
        for name in sorted(REQUIRED_GATES - {"release_window"}):
            gate_checked_at = checked_at_by_gate.get(name)
            if gate_checked_at is not None and gate_checked_at < release_checked_at:
                errors.append(
                    f"gates.{name}: evidence predates the completed release window"
                )

    retirement_evidence = config.get("retirement_evidence")
    changelog = (
        retirement_evidence.get("changelog")
        if isinstance(retirement_evidence, dict)
        else None
    )
    if not isinstance(changelog, dict):
        errors.append("retirement_evidence.changelog must be an object")
    elif retired:
        if changelog.get("status") != "pass":
            errors.append(
                "retired migration requires passing changelog evidence"
            )
        if _parse_checked_at(changelog.get("checked_at")) is None:
            errors.append(
                "retired migration requires dated changelog evidence"
            )
        errors.extend(
            _validate_evidence(
                "retirement_evidence.changelog.evidence",
                changelog.get("evidence"),
            )
        )

    if retired and not _all_gates_pass(config):
        errors.append("retired migration requires every compatibility gate to pass")
    return errors


def is_eligible(config: dict) -> bool:
    return _all_gates_pass(config) and not validate_config(config)


def status_lines(config: dict) -> list[str]:
    gates = config["gates"]
    lines = [
        f"{name}: {gates[name]['status']}"
        for name in sorted(REQUIRED_GATES)
    ]
    lines.append(f"eligible: {'yes' if is_eligible(config) else 'no'}")
    lines.append(f"retired: {'yes' if config['retired'] else 'no'}")
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the compatibility-pointer retirement gate."
    )
    parser.add_argument(
        "config",
        nargs="?",
        type=Path,
        default=DEFAULT_CONFIG,
        help="retirement config path",
    )
    parser.add_argument(
        "--require-eligible",
        action="store_true",
        help="fail unless every retirement gate has passing evidence",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
        errors = validate_config(config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"compatibility retirement check failed: {exc}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("\n".join(status_lines(config)))
    if args.require_eligible and not is_eligible(config):
        print(
            "compatibility retirement is not eligible",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
