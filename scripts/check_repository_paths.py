#!/usr/bin/env python3
"""Validate Brichan's repository path and local Markdown-link contracts."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config/repository-paths.json"
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
EXTERNAL_SCHEMES = {"http", "https", "mailto"}
SKIPPED_PARTS = {".git", "__pycache__"}


def _repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe repository-relative path: {value}")
    return ROOT / path


def load_manifest(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if not isinstance(manifest.get("entries"), list):
        raise ValueError("entries must be a list")
    if not isinstance(manifest.get("references"), list):
        raise ValueError("references must be a list")
    return manifest


def validate_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []
    known_paths: set[str] = set()

    for index, entry in enumerate(manifest["entries"]):
        label = f"entries[{index}]"
        required = {"path", "kind", "category", "policy"}
        missing = sorted(required - entry.keys())
        if missing:
            errors.append(f"{label}: missing {', '.join(missing)}")
            continue

        value = entry["path"]
        if value in known_paths:
            errors.append(f"{label}: duplicate path {value}")
            continue
        known_paths.add(value)

        try:
            path = _repo_path(value)
        except ValueError as exc:
            errors.append(f"{label}: {exc}")
            continue

        kind = entry["kind"]
        if kind == "file" and not path.is_file():
            errors.append(f"{label}: required file missing: {value}")
        elif kind == "directory" and not path.is_dir():
            errors.append(f"{label}: required directory missing: {value}")
        elif kind not in {"file", "directory"}:
            errors.append(f"{label}: unsupported kind {kind}")

    ignored_root_files = set(manifest.get("ignored_root_files", []))
    inventoried_root_files = {
        value for value in known_paths if len(Path(value).parts) == 1
    }
    actual_root_files = {
        path.name
        for path in ROOT.iterdir()
        if path.is_file() and path.name not in ignored_root_files
    }
    unclassified = sorted(actual_root_files - inventoried_root_files)
    if unclassified:
        errors.append(
            "unclassified root files: " + ", ".join(unclassified)
        )

    for index, reference in enumerate(manifest["references"]):
        label = f"references[{index}]"
        if "source" not in reference or "target" not in reference:
            errors.append(f"{label}: source and target are required")
            continue

        source_value = reference["source"]
        target_value = reference["target"]
        try:
            source = _repo_path(source_value)
            target = _repo_path(target_value)
        except ValueError as exc:
            errors.append(f"{label}: {exc}")
            continue

        if not source.is_file():
            errors.append(f"{label}: source file missing: {source_value}")
            continue
        if not target.exists():
            errors.append(f"{label}: target missing: {target_value}")
        if target_value not in known_paths:
            errors.append(f"{label}: target is not inventoried: {target_value}")

        needle = reference.get("needle", target_value)
        if needle not in source.read_text(encoding="utf-8"):
            errors.append(
                f"{label}: {source_value} does not contain reference {needle!r}"
            )

    return errors


def _local_link_target(source: Path, raw_target: str) -> Path | None:
    target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
    parsed = urlsplit(target)
    if parsed.scheme.lower() in EXTERNAL_SCHEMES or target.startswith("#"):
        return None
    if parsed.scheme or parsed.netloc:
        return None

    decoded = unquote(parsed.path)
    if not decoded:
        return None
    if decoded.startswith("/"):
        return ROOT / decoded.removeprefix("/")
    return source.parent / decoded


def markdown_sources() -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "*.md",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(
            "cannot inventory tracked and non-ignored Markdown files: "
            + result.stderr.strip()
        )
    return [ROOT / value for value in result.stdout.splitlines() if value]


def validate_markdown_links() -> list[str]:
    errors: list[str] = []
    for source in markdown_sources():
        if (
            any(part in SKIPPED_PARTS for part in source.parts)
            or not source.is_file()
        ):
            continue
        content = source.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK.findall(content):
            target = _local_link_target(source, raw_target)
            if target is not None and not target.exists():
                relative_source = source.relative_to(ROOT)
                errors.append(
                    f"{relative_source}: broken local link {raw_target!r}"
                )
    return errors


def main() -> int:
    manifest_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MANIFEST
    try:
        manifest = load_manifest(manifest_path)
        errors = validate_manifest(manifest)
        errors.extend(validate_markdown_links())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"repository path check failed: {exc}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "repository paths valid: "
        f"{len(manifest['entries'])} entries, "
        f"{len(manifest['references'])} references"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
