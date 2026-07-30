"""Human-facing rendering for lifecycle command output.

`brida.lifecycle` returns plain semantic lines and stays the machine-readable
contract: `dry-run: zero writes`, `create .brida/<path>`, and the rest are
asserted on by tests and parsed by scripts. Nothing here may change them.

This module is presentation only, and applies exclusively when stdout is an
interactive terminal. Redirected or piped output keeps the plain lines
verbatim, so `brida init | grep` behaves the same as it always has.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import IO, Iterable


CREATE_PREFIX = "create .brida/"
STATE_ROOT = ".brida/"

#: One-line answer to "what is this directory?", shown above the tree. Kept in
#: step with INIT_DESCRIPTION, which answers the same question in `--help`.
INIT_SUBTITLE = "Managed state: policy, model routing, Herdr skills, and project memory."

INIT_DESCRIPTION = (
    "Create the .brida/ state directory that Brida manages in this "
    "repository: policy, model routing, Herdr skills, and project memory. "
    "Defaults to a dry run with zero writes; pass --apply to create the "
    "footprint. Existing repository files are never modified."
)

_UNICODE_GLYPHS = {"tee": "├── ", "elbow": "└── ", "pipe": "│   ", "gap": "    "}
_ASCII_GLYPHS = {"tee": "|-- ", "elbow": "`-- ", "pipe": "|   ", "gap": "    "}

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"


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
    """Render `brida init` output as a footprint tree.

    Falls back to `lines` unchanged whenever the expected shape is absent, so
    an error or already-healthy result is never reformatted into a tree.
    """
    created = [
        line[len(CREATE_PREFIX):]
        for line in lines
        if line.startswith(CREATE_PREFIX)
    ]
    if not created or not style.enabled:
        return lines

    mode = "applied" if apply else "dry run"
    separator = style.paint(" · ", _DIM)
    header = separator.join(
        [
            style.paint("brida init", _BOLD),
            mode,
            style.paint(project_root, _DIM),
        ]
    )

    subtitle = style.paint(INIT_SUBTITLE, _DIM)

    body = [style.paint(STATE_ROOT, _BOLD, _CYAN)]
    body.extend(_render_tree(_tree(created), style))

    count = f"{len(created)} file{'s' if len(created) != 1 else ''}"
    if apply:
        summary = style.paint(f"{count} created", _GREEN)
        footer = [summary]
    else:
        summary = f"{count}{separator}{style.paint('zero writes', _GREEN)}"
        hint = style.paint("Run `brida init --apply` to create them.", _DIM)
        footer = [summary, hint]

    def indent(rows: list[str]) -> list[str]:
        return [f"  {row}" for row in rows]

    return [header, *indent([subtitle]), "", *indent(body), "", *indent(footer)]
