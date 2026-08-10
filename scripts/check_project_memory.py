#!/usr/bin/env python3
"""Check durable project memory against the repository's own facts.

Durable memory drifts silently: `PRODUCT.md` claimed package version 0.5.0 and
"nothing is published yet" while `VERSION` read 0.11.0 and the distribution was
live on PyPI, and four of seven projects disagreed with `projects/index.md`
about their own lifecycle state. Nothing failed, because nothing checked.

This gate checks six things and nothing else:

1. product version claims against ``VERSION``;
2. the product verification date against the matching ``CHANGELOG.md`` release;
3. index entry status and memory path;
4. overview lifecycle status and its agreement with the index;
5. the five required memory files per indexed project;
6. version-specific wheel filenames in a short explicit document list.

It is read-only, offline, standard-library only, spawns no subprocess, and exits
``0`` or ``1`` and nothing else.
"""

from __future__ import annotations

import errno as errno_module
import re
import stat
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

VERSION_FILE = "VERSION"
CHANGELOG_FILE = "CHANGELOG.md"
PRODUCT_FILE = "PRODUCT.md"
INDEX_FILE = "projects/index.md"

REQUIRED_MEMORY_FILES = (
    "overview.md",
    "current-state.md",
    "tasks.md",
    "decisions.md",
    "references.md",
)

LIFECYCLE_VALUES = (
    "active",
    "archived",
    "blocked",
    "complete",
    "paused",
    "proposed",
)

ACTIVE_PRODUCT_DOCUMENTS = (
    "PRODUCT.md",
    "README.md",
    "CONTRIBUTING.md",
    "packaging/pypi-readme.md",
    "docs/index.md",
    "docs/guides/installable-dogfood.md",
    "docs/guides/model-routing.md",
    "docs/architecture/repository-layout.md",
)

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
PACKAGE_VERSION_TOKEN = re.compile(r"\(package version (\d+\.\d+\.\d+)\)")
PUBLISHED_VERSION_TOKEN = re.compile(
    r"^Latest published version: (\d+\.\d+\.\d+)\s*$", re.MULTILINE
)
LAST_VERIFIED_TOKEN = re.compile(r"^Last verified: (?P<value>[^\s(]+)", re.MULTILINE)
WHEEL_TOKEN = re.compile(r"brichan-\d+\.\d+\.\d+-\S*\.whl")
MEMORY_VALUE = re.compile(r"^projects/(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)/$")
LIFECYCLE_LINE = re.compile(r"^- Lifecycle status: (?P<value>.+)$", re.MULTILINE)
FIELD_LINE = re.compile(r"^- (?P<label>Status|Memory):(?P<value>.*)$", re.MULTILINE)
HEADING_LINE = re.compile(r"^## (?P<title>.+?)\s*$")
FENCE_LINE = re.compile(r"^\s*(?:```|~~~)")

TEMPLATE_SECTION = "Entry template"


class UsageError(Exception):
    """The command line could not be understood."""


@dataclass(frozen=True, order=True)
class Diagnostic:
    """One consistency failure, addressed by repository-relative POSIX path."""

    path: str
    check: str
    detail: str

    def render(self) -> str:
        return f"{self.path}: {self.check}: {self.detail}"


@dataclass(frozen=True)
class Resolution:
    """What a declared relative path turned out to be.

    ``kind`` is one of ``unsafe``, ``missing``, ``symlink``, ``directory``,
    ``file``, or ``other``. ``other`` carries any remaining node type or
    ``lstat`` error with a short deterministic reason. This model exists to
    serve the checks above; it does not claim to enumerate every node type or
    every ``errno``.
    """

    kind: str
    reason: str = ""


@dataclass(frozen=True)
class IndexEntry:
    """A parsed ``projects/index.md`` entry."""

    title: str
    statuses: tuple[str, ...]
    memories: tuple[str, ...]


def _errno_reason(exc: OSError) -> str:
    """Name an ``errno`` without ever raising on an unknown numeric value."""
    if exc.errno is None:
        return "unknown-error"
    return errno_module.errorcode.get(exc.errno, f"errno-{exc.errno}")


def _lexical_reason(value: str) -> str | None:
    """Reject a declared path on its text alone, before touching the disk."""
    if not value:
        return "empty path"
    if "\\" in value:
        return "backslash in path"
    if value.startswith("/"):
        return "absolute path"
    for component in value.split("/"):
        if component == "":
            return "empty path component"
        if component == ".":
            return "current-directory component"
        if component == "..":
            return "parent-directory component"
        if component.startswith("~"):
            return "home-directory reference"
    return None


def resolve(root: Path, value: str) -> Resolution:
    """Resolve ``value`` under ``root`` component-wise, never following a link.

    A symlink anywhere in the path — including the final component and
    including a dangling one — decides which file the name reaches, so it is
    reported as a symlink rather than followed. ``Path.exists``,
    ``Path.resolve``, ``Path.is_dir``, and ``Path.is_file`` are deliberately
    not used on an unvalidated relative value.
    """
    reason = _lexical_reason(value)
    if reason is not None:
        return Resolution("unsafe", reason)

    components = value.split("/")
    current = root
    info = None
    for position, component in enumerate(components):
        current = current / component
        prefix = "/".join(components[: position + 1])
        try:
            info = current.lstat()
        except FileNotFoundError:
            return Resolution("missing", f"missing at {prefix}")
        except OSError as exc:
            return Resolution("other", f"cannot stat {prefix} ({_errno_reason(exc)})")
        if stat.S_ISLNK(info.st_mode):
            return Resolution("symlink", f"symlink at {prefix}")
        if position < len(components) - 1 and not stat.S_ISDIR(info.st_mode):
            return Resolution("other", f"not a directory at {prefix}")

    assert info is not None  # a non-empty component list always lstats once
    if stat.S_ISDIR(info.st_mode):
        return Resolution("directory")
    if stat.S_ISREG(info.st_mode):
        return Resolution("file")
    return Resolution("other", "not a regular file or directory")


def _unavailable_reason(outcome: Resolution) -> str:
    if outcome.kind == "missing":
        return "is missing"
    if outcome.kind == "symlink":
        return f"is a symlink ({outcome.reason})"
    if outcome.kind == "directory":
        return "is a directory, not a regular file"
    if outcome.kind == "unsafe":
        return f"is not a safe repository path ({outcome.reason})"
    return f"is not readable ({outcome.reason})"


class Reader:
    """Read each checker input at most once, diagnosing it at most once."""

    def __init__(self, root: Path, diagnostics: list[Diagnostic]) -> None:
        self._root = root
        self._diagnostics = diagnostics
        self._texts: dict[str, str | None] = {}

    def text(self, relative: str) -> str | None:
        """Return the file's text, or ``None`` after recording one diagnostic."""
        if relative in self._texts:
            return self._texts[relative]
        content = self._read(relative)
        self._texts[relative] = content
        return content

    def failed(self, relative: str) -> bool:
        return relative in self._texts and self._texts[relative] is None

    def _read(self, relative: str) -> str | None:
        outcome = resolve(self._root, relative)
        if outcome.kind != "file":
            self._diagnostics.append(
                Diagnostic(relative, "input", _unavailable_reason(outcome))
            )
            return None
        try:
            return (self._root / relative).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            self._diagnostics.append(
                Diagnostic(relative, "input", "is not valid UTF-8")
            )
        except OSError as exc:
            self._diagnostics.append(
                Diagnostic(
                    relative, "input", f"cannot be read ({_errno_reason(exc)})"
                )
            )
        return None


def _strip_fences(text: str) -> list[str]:
    """Drop fenced blocks so a template inside one is never read as content."""
    kept: list[str] = []
    inside = False
    for line in text.splitlines():
        if FENCE_LINE.match(line):
            inside = not inside
            continue
        if not inside:
            kept.append(line)
    return kept


def parse_index(text: str) -> list[IndexEntry]:
    """Parse real index entries, skipping the documented entry template."""
    entries: list[IndexEntry] = []
    title: str | None = None
    body: list[str] = []

    def flush() -> None:
        if title is None or title == TEMPLATE_SECTION:
            return
        fields = FIELD_LINE.findall("\n".join(body))
        entries.append(
            IndexEntry(
                title=title,
                statuses=tuple(
                    value.strip() for label, value in fields if label == "Status"
                ),
                memories=tuple(
                    value.strip() for label, value in fields if label == "Memory"
                ),
            )
        )

    for line in _strip_fences(text):
        heading = HEADING_LINE.match(line)
        if heading is None:
            body.append(line)
            continue
        flush()
        title = heading.group("title")
        body = []
    flush()
    return entries


def _strip_backticks(value: str) -> str:
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return value[1:-1].strip()
    return value


def check_product_version(product: str, version: str) -> list[Diagnostic]:
    """Anchored version tokens in ``PRODUCT.md`` must equal ``VERSION``."""
    diagnostics = []
    for claimed in PACKAGE_VERSION_TOKEN.findall(product):
        if claimed != version:
            diagnostics.append(
                Diagnostic(
                    PRODUCT_FILE,
                    "version-claim",
                    f"claims package version {claimed}, {VERSION_FILE} is {version}",
                )
            )
    for claimed in PUBLISHED_VERSION_TOKEN.findall(product):
        if claimed != version:
            diagnostics.append(
                Diagnostic(
                    PRODUCT_FILE,
                    "version-claim",
                    "claims latest published version "
                    f"{claimed}, {VERSION_FILE} is {version}",
                )
            )
    return diagnostics


def find_release_date(changelog: str, version: str) -> tuple[date | None, str | None]:
    """Return the matching release date, or a reason there is no valid one."""
    heading = re.compile(
        rf"^## \[{re.escape(version)}\] - (?P<date>\d{{4}}-\d{{2}}-\d{{2}})$",
        re.MULTILINE,
    )
    match = heading.search(changelog)
    if match is None:
        return None, f"no dated release heading for version {version}"
    raw = match.group("date")
    try:
        return date.fromisoformat(raw), None
    except ValueError:
        return None, (
            f"release heading for version {version} carries {raw}, "
            "which is not a real calendar date"
        )


def check_product_date(
    product: str, release_date: date | None
) -> list[Diagnostic]:
    """The declared verification date must parse and not predate the release."""
    diagnostics = []
    values = LAST_VERIFIED_TOKEN.findall(product)
    if not values:
        return [
            Diagnostic(
                PRODUCT_FILE, "date-claim", "declares no `Last verified:` date"
            )
        ]
    for raw in values:
        try:
            verified = date.fromisoformat(raw)
        except ValueError:
            diagnostics.append(
                Diagnostic(
                    PRODUCT_FILE,
                    "date-claim",
                    f"`Last verified:` value {raw} is not an ISO date",
                )
            )
            continue
        if release_date is not None and verified < release_date:
            diagnostics.append(
                Diagnostic(
                    PRODUCT_FILE,
                    "date-claim",
                    f"`Last verified:` {verified.isoformat()} predates the "
                    f"matching release date {release_date.isoformat()}",
                )
            )
    return diagnostics


def check_wheel_filenames(relative: str, text: str) -> list[Diagnostic]:
    """A literal wheel filename goes stale on the next release; derive it."""
    return [
        Diagnostic(
            relative,
            "wheel-version",
            f"embeds the version-specific wheel filename {match}; "
            f"derive it from {VERSION_FILE}",
        )
        for match in WHEEL_TOKEN.findall(text)
    ]


def check_entry_status(entry: IndexEntry) -> Diagnostic | None:
    """Each entry declares exactly one status drawn from the lifecycle enum."""
    if not entry.statuses:
        return Diagnostic(
            INDEX_FILE, "index-status", f"{entry.title!r} declares no `- Status:`"
        )
    if len(entry.statuses) > 1:
        return Diagnostic(
            INDEX_FILE,
            "index-status",
            f"{entry.title!r} declares {len(entry.statuses)} `- Status:` lines",
        )
    value = entry.statuses[0]
    if not value:
        return Diagnostic(
            INDEX_FILE, "index-status", f"{entry.title!r} declares an empty status"
        )
    if value not in LIFECYCLE_VALUES:
        return Diagnostic(
            INDEX_FILE,
            "index-status",
            f"{entry.title!r} declares status {value!r}, "
            f"not one of {', '.join(LIFECYCLE_VALUES)}",
        )
    return None


def check_entry_memory(
    root: Path, entry: IndexEntry
) -> tuple[str | None, Diagnostic | None]:
    """Return the entry's slug, or the reason its memory path is unusable."""
    if not entry.memories:
        return None, Diagnostic(
            INDEX_FILE, "index-path", f"{entry.title!r} declares no `- Memory:`"
        )
    if len(entry.memories) > 1:
        return None, Diagnostic(
            INDEX_FILE,
            "index-path",
            f"{entry.title!r} declares {len(entry.memories)} `- Memory:` lines",
        )
    value = entry.memories[0]
    match = MEMORY_VALUE.match(value)
    if match is None:
        return None, Diagnostic(
            INDEX_FILE,
            "index-path",
            f"{entry.title!r} declares memory path {value!r}, which is not "
            "`projects/<slug>/`",
        )
    slug = match.group("slug")
    directory = f"projects/{slug}"
    outcome = resolve(root, directory)
    if outcome.kind == "directory":
        return slug, None
    if outcome.kind == "symlink":
        detail = f"is a symlink ({outcome.reason})"
    elif outcome.kind == "missing":
        detail = f"does not exist ({outcome.reason})"
    elif outcome.kind == "unsafe":
        detail = f"is not a safe repository path ({outcome.reason})"
    else:
        detail = f"is not a directory ({outcome.reason})"
    return None, Diagnostic(
        INDEX_FILE,
        "index-path",
        f"{entry.title!r} memory directory {directory} {detail}",
    )


def check_memory_files(root: Path, slug: str) -> list[Diagnostic]:
    """Every indexed project carries the five policy-required memory files."""
    diagnostics = []
    for name in REQUIRED_MEMORY_FILES:
        relative = f"projects/{slug}/{name}"
        outcome = resolve(root, relative)
        if outcome.kind == "file":
            continue
        if outcome.kind == "missing":
            detail = "is missing"
        elif outcome.kind == "symlink":
            detail = f"is a symlink ({outcome.reason})"
        elif outcome.kind == "directory":
            detail = "is a directory, not a regular file"
        elif outcome.kind == "unsafe":
            detail = f"is not a safe repository path ({outcome.reason})"
        else:
            detail = f"is not a regular file ({outcome.reason})"
        diagnostics.append(
            Diagnostic(relative, "memory-completeness", f"required memory file {detail}")
        )
    return diagnostics


def check_lifecycle(
    relative: str, overview: str, status: str
) -> list[Diagnostic]:
    """The overview declares one lifecycle value and the index agrees with it."""
    raw_values = LIFECYCLE_LINE.findall(overview)
    values = [_strip_backticks(value.strip()) for value in raw_values]
    if not values:
        return [
            Diagnostic(
                relative,
                "overview-lifecycle",
                "declares no `- Lifecycle status:` value",
            )
        ]
    if len(values) > 1:
        return [
            Diagnostic(
                relative,
                "overview-lifecycle",
                f"declares {len(values)} `- Lifecycle status:` lines",
            )
        ]
    value = values[0]
    if not value:
        return [
            Diagnostic(
                relative,
                "overview-lifecycle",
                "declares an empty `- Lifecycle status:` value",
            )
        ]
    if value not in LIFECYCLE_VALUES:
        return [
            Diagnostic(
                relative,
                "overview-lifecycle",
                f"declares lifecycle status {value!r}, "
                f"not one of {', '.join(LIFECYCLE_VALUES)}",
            )
        ]
    if value != status:
        return [
            Diagnostic(
                relative,
                "lifecycle-agreement",
                f"declares lifecycle status {value!r} while {INDEX_FILE} "
                f"declares {status!r}",
            )
        ]
    return []


def check_projects(
    root: Path, reader: Reader, index_text: str
) -> tuple[list[Diagnostic], int]:
    """Run every per-project check, honouring the documented precedence."""
    diagnostics: list[Diagnostic] = []
    entries = parse_index(index_text)
    for entry in entries:
        status_problem = check_entry_status(entry)
        if status_problem is not None:
            diagnostics.append(status_problem)
        slug, path_problem = check_entry_memory(root, entry)
        if path_problem is not None:
            diagnostics.append(path_problem)
        if status_problem is not None or path_problem is not None or slug is None:
            # A broken entry makes every downstream answer about it noise.
            continue

        file_problems = check_memory_files(root, slug)
        diagnostics.extend(file_problems)
        overview = f"projects/{slug}/overview.md"
        if any(problem.path == overview for problem in file_problems):
            continue
        overview_text = reader.text(overview)
        if overview_text is None:
            continue
        diagnostics.extend(
            check_lifecycle(overview, overview_text, entry.statuses[0])
        )
    return diagnostics, len(entries)


def collect(root: Path) -> list[Diagnostic]:
    """Return every diagnostic for ``root``, sorted deterministically."""
    diagnostics: list[Diagnostic] = []
    reader = Reader(root, diagnostics)

    raw_version = reader.text(VERSION_FILE)
    version: str | None = None
    if raw_version is not None:
        candidate = raw_version.strip()
        if VERSION_PATTERN.match(candidate):
            version = candidate
        else:
            diagnostics.append(
                Diagnostic(
                    VERSION_FILE,
                    "input",
                    f"holds {candidate!r}, which is not an X.Y.Z version",
                )
            )

    changelog = reader.text(CHANGELOG_FILE)
    release_date: date | None = None
    if version is not None and changelog is not None:
        release_date, reason = find_release_date(changelog, version)
        if reason is not None:
            diagnostics.append(
                Diagnostic(CHANGELOG_FILE, "changelog-release", reason)
            )

    product = reader.text(PRODUCT_FILE)
    if product is not None:
        if version is not None:
            diagnostics.extend(check_product_version(product, version))
        diagnostics.extend(check_product_date(product, release_date))

    for relative in ACTIVE_PRODUCT_DOCUMENTS:
        text = reader.text(relative)
        if text is not None:
            diagnostics.extend(check_wheel_filenames(relative, text))

    index_text = reader.text(INDEX_FILE)
    if index_text is not None:
        project_diagnostics, _ = check_projects(root, reader, index_text)
        diagnostics.extend(project_diagnostics)

    return sorted(diagnostics)


def summary(root: Path) -> str:
    index_text = None
    try:
        index_text = (root / INDEX_FILE).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):  # pragma: no cover - unreachable at exit 0
        index_text = None
    projects = len(parse_index(index_text)) if index_text is not None else 0
    return (
        "project memory consistent: "
        f"{projects} indexed projects, "
        f"{len(ACTIVE_PRODUCT_DOCUMENTS)} active documents"
    )


def parse_args(argv: list[str]) -> str | None:
    root: str | None = None
    position = 0
    while position < len(argv):
        argument = argv[position]
        if argument == "--root":
            position += 1
            if position >= len(argv):
                raise UsageError("--root requires a PATH")
            root = argv[position]
        elif argument.startswith("--root="):
            root = argument[len("--root=") :]
        else:
            raise UsageError(f"unknown argument: {argument!r}")
        position += 1
    return root


def main(argv: list[str] | None = None) -> int:
    try:
        requested = parse_args(list(sys.argv[1:] if argv is None else argv))
    except UsageError as exc:
        print(f"usage: check_project_memory.py [--root PATH]\n{exc}", file=sys.stderr)
        return 1

    root = Path(requested) if requested is not None else Path(__file__).resolve().parents[1]
    diagnostics = collect(root)
    if diagnostics:
        for diagnostic in diagnostics:
            print(diagnostic.render(), file=sys.stderr)
        return 1
    print(summary(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
