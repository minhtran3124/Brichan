#!/usr/bin/env python3
"""Render the PyPI long description from Brichan's repository README.

PyPI serves the long description as a standalone page with no repository
behind it, so repository-relative targets never resolve there: images render
broken and links resolve against pypi.org. The repository README must keep
relative targets, because those are the ones that work in local Markdown
previews and in the GitHub web UI.

The two audiences therefore need two documents. This module derives the PyPI
one from the repository one so they cannot drift.

Relative targets are rewritten to absolute URLs when the repository is
publicly readable. While it is private those URLs would 404 for PyPI's
anonymous fetch, so images are dropped and links are flattened to their text
instead. Either way the published description contains no relative target,
which is the property `validate` enforces.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/pypi-readme.json"

# ![alt](target) and [text](target), captured separately so images can be
# dropped while links keep their text.
MARKDOWN_TARGET = re.compile(r"(!?)\[([^\]]*)\]\(([^)]+)\)")
HTML_IMG_SRC = re.compile(r"""(<img\b[^>]*?\bsrc\s*=\s*)(["'])(.*?)\2""", re.IGNORECASE)
EXTERNAL_SCHEMES = {"http", "https", "mailto"}


class ReadmeConfigError(ValueError):
    """Raised when the PyPI README configuration is unusable."""


def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)

    if config.get("schema_version") != 1:
        raise ReadmeConfigError("schema_version must be 1")

    required = {"source", "output", "public_repository"}
    missing = sorted(required - config.keys())
    if missing:
        raise ReadmeConfigError(f"missing keys: {', '.join(missing)}")

    if not isinstance(config["public_repository"], bool):
        raise ReadmeConfigError("public_repository must be a boolean")

    if config["public_repository"]:
        for key in ("asset_base_url", "link_base_url"):
            value = config.get(key)
            if not isinstance(value, str) or not value.startswith("https://"):
                raise ReadmeConfigError(f"{key} must be an https URL when public")

    return config


def is_relative_target(target: str) -> bool:
    """Report whether a Markdown target needs rewriting for PyPI.

    Anchors and absolute URLs already resolve on the project page; everything
    else is repository-relative and does not.
    """
    candidate = target.strip().split(maxsplit=1)[0].strip("<>")
    if not candidate or candidate.startswith("#"):
        return False
    parsed = urlsplit(candidate)
    if parsed.scheme.lower() in EXTERNAL_SCHEMES:
        return False
    return not (parsed.scheme or parsed.netloc)


def _absolute(base_url: str, target: str) -> str:
    candidate = target.strip().split(maxsplit=1)[0].strip("<>")
    return f"{base_url.rstrip('/')}/{candidate.lstrip('./').lstrip('/')}"


def render(readme: str, config: dict) -> str:
    """Return `readme` with every relative target made PyPI-safe."""
    public = config["public_repository"]

    def replace_markdown(match: re.Match[str]) -> str:
        bang, text, target = match.group(1), match.group(2), match.group(3)
        if not is_relative_target(target):
            return match.group(0)
        if not public:
            # An image has no meaningful text fallback; a link does.
            return "" if bang else text
        base = config["asset_base_url"] if bang else config["link_base_url"]
        return f"{bang}[{text}]({_absolute(base, target)})"

    def replace_html_img(match: re.Match[str]) -> str:
        prefix, quote, src = match.group(1), match.group(2), match.group(3)
        if not is_relative_target(src):
            return match.group(0)
        if not public:
            return ""
        absolute = _absolute(config["asset_base_url"], src)
        return f"{prefix}{quote}{absolute}{quote}"

    rendered = MARKDOWN_TARGET.sub(replace_markdown, readme)
    rendered = HTML_IMG_SRC.sub(replace_html_img, rendered)

    # Dropping a standalone image leaves the blank line it occupied, which
    # would collapse into a stray paragraph gap.
    rendered = re.sub(r"\n[ \t]*\n[ \t]*\n+", "\n\n", rendered)
    return rendered


def validate(rendered: str) -> list[str]:
    """Return the relative targets still present in a rendered description."""
    errors: list[str] = []
    for bang, _text, target in MARKDOWN_TARGET.findall(rendered):
        if is_relative_target(target):
            kind = "image" if bang else "link"
            errors.append(f"unresolved relative {kind} target: {target!r}")
    for _prefix, _quote, src in HTML_IMG_SRC.findall(rendered):
        if is_relative_target(src):
            errors.append(f"unresolved relative image src: {src!r}")
    return errors


def expected(config: dict | None = None, root: Path = ROOT) -> str:
    """Return the description `config` should produce from the README."""
    config = load_config() if config is None else config
    rendered = render(
        (root / config["source"]).read_text(encoding="utf-8"), config
    )
    errors = validate(rendered)
    if errors:
        raise ReadmeConfigError("; ".join(errors))
    return rendered


def build(config: dict | None = None, root: Path = ROOT) -> Path:
    """Regenerate the PyPI description and return the path written."""
    config = load_config() if config is None else config
    output = root / config["output"]
    output.write_text(expected(config, root), encoding="utf-8")
    return output


def main() -> int:
    check_only = "--check" in sys.argv[1:]
    try:
        config = load_config()
        if check_only:
            output = ROOT / config["output"]
            current = (
                output.read_text(encoding="utf-8") if output.is_file() else None
            )
            if current != expected(config):
                print(
                    f"{config['output']} is out of date with {config['source']}; "
                    "run `make readme-check`",
                    file=sys.stderr,
                )
                return 1
            print(f"{config['output']} is in sync with {config['source']}")
            return 0
        output = build(config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"PyPI README build failed: {exc}", file=sys.stderr)
        return 1

    mode = "absolute URLs" if config["public_repository"] else "stripped targets"
    print(f"wrote {output.relative_to(ROOT)} ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
