"""Human-facing rendering for lifecycle command output.

`brichan.lifecycle` returns plain semantic lines and stays the machine-readable
contract: `dry-run: zero writes`, `create .brichan/<path>`, `create <root
agent entry>`, and the rest are asserted on by tests and parsed by scripts.
Nothing here may change them.

This module is presentation only, and applies exclusively when stdout is an
interactive terminal. Redirected or piped output keeps the plain lines
verbatim, so `brichan init | grep` behaves the same as it always has.
"""

from __future__ import annotations

import json
import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, Iterable


CREATE_PREFIX = "create .brichan/"
STATE_ROOT = ".brichan/"

#: One-line answer to "what is this directory?", shown above the tree. Kept in
#: step with INIT_DESCRIPTION, which answers the same question in `--help`.
INIT_SUBTITLE = "Managed state: policy, model routing, Herdr skills, and project memory."

INIT_DESCRIPTION = (
    "Create the .brichan/ state directory that Brichan manages in this "
    "repository: policy, model routing, Herdr skills, and project memory. "
    "Also creates root AGENTS.md and CLAUDE.md pointers when they are "
    "absent, and exports the Herdr skill to .agents/skills/ for direct "
    "codex sessions. Defaults to a dry run with "
    "zero writes; pass --apply to create the footprint. Existing repository "
    "files are never modified."
)

STATUS_DESCRIPTION = (
    "Report the state of this repository's .brichan/ directory as one of "
    "uninitialized, healthy, malformed, or incompatible. The exit code "
    "carries the same answer for scripts: 0 healthy, 1 uninitialized, "
    "2 malformed, 3 incompatible. Reports problems rather than repairing "
    "them; nothing is written."
)

DOCTOR_DESCRIPTION = (
    "Show a compact health summary for the resolved project root, Git, "
    ".brichan/ state, "
    "policies, model routing, project memory, and required codex/herdr "
    "dependencies. "
    "Nothing is written."
)

DOCTOR_JSON_HELP = (
    "emit the diagnostic report as one JSON document on stdout instead of "
    "the compact human-readable summary"
)


def format_doctor_json(report: dict[str, Any]) -> str:
    """Serialize a `doctor --json` report deterministically.

    Sorted keys, two-space indentation, and exactly one trailing newline, so
    the bytes are stable across runs and diffable between machines.
    """

    return json.dumps(report, indent=2, sort_keys=True) + "\n"

_UNICODE_GLYPHS = {"tee": "├── ", "elbow": "└── ", "pipe": "│   ", "gap": "    "}
_ASCII_GLYPHS = {"tee": "|-- ", "elbow": "`-- ", "pipe": "|   ", "gap": "    "}

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"


@dataclass(frozen=True)
class Style:
    """Which embellishments the destination terminal can actually take."""

    color: bool = False
    unicode: bool = False

    @property
    def enabled(self) -> bool:
        """Whether the destination takes any embellishment at all."""
        return self.color or self.unicode

    @property
    def glyphs(self) -> dict[str, str]:
        return _UNICODE_GLYPHS if self.unicode else _ASCII_GLYPHS

    def paint(self, text: str, *codes: str) -> str:
        if not self.color or not codes:
            return text
        return f"{''.join(codes)}{text}{_RESET}"


def format_doctor_text(report: dict[str, Any], style: Style) -> list[str]:
    """Render the compact operator-facing doctor summary."""

    def state(status: str) -> str:
        if status == "ok":
            return style.paint("OK", _BOLD, _GREEN)
        if status in {"missing", "unavailable"}:
            return style.paint(status.upper(), _BOLD, _YELLOW)
        return style.paint(status.upper(), _BOLD, _RED)

    def mark(status: str) -> str:
        if style.unicode:
            return style.paint("✓" if status == "ok" else "!", _BOLD)
        return "[ok]" if status == "ok" else "[!]"

    rows = [*_doctor_callout(report, style), ""]
    checks = [
        ("repository", "repository"),
        ("git", "git"),
        ("policies", "policies"),
        ("model_routing", "model routing"),
        ("project_memory", "project memory"),
        ("agent_skill_export", "agent skill export"),
        ("dependencies", "dependencies"),
    ]
    for key, label in checks:
        section = report[key]
        status = section["status"]
        if key == "agent_skill_export":
            rows.append(f"{mark(status)} {label}: {state(status)}")
            rows.append(f"    detail: {section['detail']}")
            rows.append(f"    managed: {_path_or_null(section['managed_path'])}")
            rows.append(f"    exported: {_path_or_null(section['path'])}")
            rows.extend(_export_commands(report, section))
            continue
        suffix = ""
        if key == "repository" and status == "ok":
            kind = section.get("kind", "repository").replace("_", " ")
            suffix = f" · {kind}"
        elif key == "git" and status == "ok":
            suffix = f" · {'dirty' if section.get('dirty') else 'clean'} worktree"
            if section.get("branch"):
                suffix += f" · {section['branch']}"
            if section.get("commit"):
                suffix += f" · commit {section['commit'][:7]}"
            suffix += " · untracked" if section.get("untracked") else " · no untracked"
        rows.append(f"{mark(status)} {label}: {state(status)}{suffix}")
        if status != "ok":
            rows.append(f"    {section.get('detail', 'check failed')}")

        if key == "policies" and section.get("files"):
            bullet = "•" if style.unicode else "-"
            for path, check in section["files"].items():
                if check.get("status") == "ok":
                    rows.append(f"    {bullet} {path}")

        if key == "model_routing" and status == "ok":
            rows.extend(_format_route_summary(section, style))

        if key == "dependencies":
            rows.extend(_format_dependency_summary(section, style))

    overall_status = "ok" if report["ok"] else "invalid"
    rows.extend(["", f"overall: {state(overall_status)} · {'healthy' if report['ok'] else 'needs attention'}"])
    return rows


#: The three relations a user can act on. Doctor renders no backup or removal
#: command, because both targets are user choices.
EXPORT_COMMAND_CODES = ("EXPORT_EXTRA", "EXPORT_STALE", "EXPORT_MISSING")


def _path_or_null(value: str | None) -> str:
    return "null" if value is None else value


def _export_commands(report: dict[str, Any], section: dict[str, Any]) -> list[str]:
    """The two shell-quoted commands, or nothing at all.

    The root is quoted with `shlex.quote`, so a space, a single quote, or a
    leading dash is pasteable rather than a second argument.
    """

    if section.get("detail_code") not in EXPORT_COMMAND_CODES:
        return []
    root = shlex.quote(str(report["repository"]["root"]))
    return [
        f"    re-export: brichan init --apply --project {root}",
        f"    verify: brichan doctor --json --project {root}",
    ]


def _doctor_callout(report: dict[str, Any], style: Style) -> list[str]:
    """Highlight the command title and target root in a dotted callout."""

    title = "BRICHAN DOCTOR"
    root = f"project root: {report['repository']['root']}"
    inner_width = max(len(title), len(root)) + 2
    if style.unicode:
        left, right = "┌", "┐"
        vertical = "│"
        bottom_left, bottom_right = "└", "┘"
    else:
        left, right = "+", "+"
        vertical = "|"
        bottom_left, bottom_right = "+", "+"
    dots = "·" * inner_width if style.unicode else "." * inner_width

    def content(value: str, *codes: str) -> str:
        return (
            style.paint(vertical, _DIM)
            + " "
            + style.paint(value, *codes)
            + " " * (inner_width - len(value) - 1)
            + style.paint(vertical, _DIM)
        )

    return [
        style.paint(left + dots + right, _BOLD, _CYAN),
        content(title, _BOLD, _CYAN),
        content(root, _DIM),
        style.paint(bottom_left + dots + bottom_right, _BOLD, _CYAN),
    ]


_ROUTE_PURPOSES = {
    "plan": "planning",
    "implement": "implementation",
    "review": "review",
    "scan": "repository scan",
}


def _format_route_summary(section: dict[str, Any], style: Style) -> list[str]:
    """Show configured route models without expanding the JSON contract."""

    try:
        path = section.get("path")
        if not path:
            return []
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        routes = payload.get("routes", {})
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return []
    if not isinstance(routes, dict):
        return []

    bullet = "•" if style.unicode else "-"
    lines = []
    for name, route in routes.items():
        if not isinstance(route, dict) or not route.get("model"):
            continue
        purpose = _ROUTE_PURPOSES.get(name, name)
        lines.append(
            f"    {bullet} {route['model']} — {purpose} ({name})"
        )
    return lines


def _format_dependency_summary(section: dict[str, Any], style: Style) -> list[str]:
    bullet = "•" if style.unicode else "-"
    lines = []
    for name in ("python", "git", "codex", "herdr"):
        dependency = section.get(name)
        if not isinstance(dependency, dict):
            continue
        required = "required" if dependency.get("required") else "optional"
        lines.append(
            f"    {bullet} {name}: {state_for_dependency(dependency['status'], style)} · {required}"
        )
    return lines


def state_for_dependency(status: str, style: Style) -> str:
    if status == "ok":
        return style.paint("OK", _BOLD, _GREEN)
    if status in {"missing", "unavailable"}:
        return style.paint(status.upper(), _BOLD, _YELLOW)
    return style.paint(status.upper(), _BOLD, _RED)


def _supports_unicode(stream: IO[str]) -> bool:
    encoding = getattr(stream, "encoding", None)
    if not encoding:
        return False
    try:
        "├──".encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return False
    return True


def resolve_style(stream: IO[str], environment: dict[str, str]) -> Style:
    """Return the style `stream` can render.

    A non-interactive stream gets nothing, which is what keeps piped output
    identical to the plain lifecycle lines. NO_COLOR suppresses colour only;
    the tree itself is still worth drawing.
    """
    if not callable(getattr(stream, "isatty", None)) or not stream.isatty():
        return Style()
    if environment.get("TERM") == "dumb":
        return Style()
    unicode_ok = _supports_unicode(stream)
    return Style(color="NO_COLOR" not in environment, unicode=unicode_ok)


def _tree(paths: Iterable[str]) -> dict:
    """Nest `a/b/c` paths into dicts, preserving footprint order."""
    root: dict = {}
    for path in paths:
        node = root
        for part in path.split("/"):
            node = node.setdefault(part, {})
    return root


def _render_tree(node: dict, style: Style, prefix: str = "") -> list[str]:
    lines: list[str] = []
    glyphs = style.glyphs
    items = list(node.items())
    for index, (name, children) in enumerate(items):
        last = index == len(items) - 1
        connector = glyphs["elbow"] if last else glyphs["tee"]
        if children:
            label = style.paint(f"{name}/", _BOLD, _CYAN)
        else:
            label = name
        lines.append(f"{style.paint(prefix + connector, _DIM)}{label}")
        if children:
            extension = glyphs["gap"] if last else glyphs["pipe"]
            lines.extend(_render_tree(children, style, prefix + extension))
    return lines


def format_init(
    lines: list[str],
    *,
    project_root: str,
    apply: bool,
    style: Style,
) -> list[str]:
    """Render `brichan init` output as a footprint tree.

    Falls back to `lines` unchanged whenever the expected shape is absent, so
    an error or already-healthy result is never reformatted into a tree.
    """
    created = [
        line[len(CREATE_PREFIX):]
        for line in lines
        if line.startswith(CREATE_PREFIX)
    ]
    root_created = [
        line[len("create "):]
        for line in lines
        if line.startswith("create ") and not line.startswith(CREATE_PREFIX)
    ]
    if (not created and not root_created) or not style.enabled:
        return lines

    mode = "applied" if apply else "dry run"
    separator = style.paint(" · ", _DIM)
    header = separator.join(
        [
            style.paint("brichan init", _BOLD),
            mode,
            style.paint(project_root, _DIM),
        ]
    )

    subtitle = style.paint(INIT_SUBTITLE, _DIM)

    body = []
    if created:
        body.append(style.paint(STATE_ROOT, _BOLD, _CYAN))
        body.extend(_render_tree(_tree(created), style))
    body.extend(style.paint(name, _BOLD, _CYAN) for name in root_created)

    total = len(created) + len(root_created)
    count = f"{total} file{'s' if total != 1 else ''}"
    if apply:
        summary = style.paint(f"{count} created", _GREEN)
        footer = [summary]
    else:
        summary = f"{count}{separator}{style.paint('zero writes', _GREEN)}"
        hint = style.paint("Run `brichan init --apply` to create them.", _DIM)
        footer = [summary, hint]

    def indent(rows: list[str]) -> list[str]:
        return [f"  {row}" for row in rows]

    return [header, *indent([subtitle]), "", *indent(body), "", *indent(footer)]
