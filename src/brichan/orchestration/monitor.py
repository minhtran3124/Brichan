#!/usr/bin/env python3
"""Read-only Herdr preflight and worker-observation surface.

This module implements the typed monitoring surface accepted as plan
``HERDR-HARDENING-PLAN-001`` version 5. Three authority classes stay strictly
separated:

* Herdr scheduling state is a *scheduling* signal only. It says when to look,
  when to wait, and when to escalate. ``done`` or ``idle`` is not proof that a
  task finished, and no type or code path here maps a scheduling state onto
  completion.
* Terminal text read through ``herdr agent read`` is a bounded observation, so
  every read carries conservative completeness metadata and a truncation-risk
  classification dominated by Herdr's native ``truncated`` flag.
* Acceptance evidence is file-based only. The evidence fallback reports
  presence metadata (existence, regular-file status, size, mtime) and never
  parses or judges content.

Every Herdr command this module may run is read-only, and no code path sends
input to an agent.
"""

from __future__ import annotations

import argparse
import errno
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence


# ---------------------------------------------------------------------------
# Frozen control-plane constants
# ---------------------------------------------------------------------------

#: Verified (server version, protocol) pairs. Widening this set requires an
#: explicitly authorized Herdr upgrade (gate AG-2) plus re-verification of the
#: command reference against the new version.
VERIFIED_SUPPORT: frozenset[tuple[str, int]] = frozenset({("0.7.3", 16)})

#: Capabilities that prove terminal-history completeness for a read source.
#: Empty on Herdr ``0.7.3``: the ``agent read`` envelope exposes no
#: alternate-screen or history-completeness signal, so truncation risk ``none``
#: is unreachable by design. Widening this set requires gates AG-2 and AG-3.
COMPLETENESS_CAPABILITIES: frozenset[str] = frozenset()

#: Hard cap on every ``herdr agent wait`` timeout, in milliseconds.
MAX_WAIT_TIMEOUT_MS = 30000

#: Runtime identifiers Herdr ``0.7.3`` reports in ``integration status``.
KNOWN_INTEGRATION_RUNTIMES: frozenset[str] = frozenset(
    {
        "pi",
        "omp",
        "claude",
        "codex",
        "copilot",
        "devin",
        "droid",
        "kimi",
        "opencode",
        "kilo",
        "hermes",
        "qodercli",
        "cursor",
        "mastracode",
    }
)

#: Status vocabulary of the ``0.7.3`` plain-text integration rows.
KNOWN_INTEGRATION_STATUSES: frozenset[str] = frozenset(
    {"current", "outdated", "not installed"}
)

#: Only ``current`` is healthy for a runtime Brichan actually launches.
HEALTHY_INTEGRATION_STATUSES: frozenset[str] = frozenset({"current"})

#: Runtimes Brichan launches workers with. Any of these not reporting
#: ``current`` is a finding. ``not installed`` for a runtime Brichan never uses
#: is the normal state and is reported as a row, not as a finding; ``outdated``
#: is control-plane drift and is a finding for every runtime.
REQUIRED_INTEGRATION_RUNTIMES: frozenset[str] = frozenset({"claude", "codex"})

DEFAULT_READ_SOURCE = "recent-unwrapped"
DEFAULT_READ_LINES = 200

TRUNCATION_NONE = "none"
TRUNCATION_POSSIBLE = "possible"
TRUNCATION_CONFIRMED = "confirmed"

SUPPORT_VERIFIED = "verified"
SUPPORT_UNVERIFIED = "unverified"
SUPPORT_UNAVAILABLE = "unavailable"

PROGRAM = "brichan-herdr-agent-observe"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class MonitorError(RuntimeError):
    """Base class for every monitor failure."""


class UsageError(MonitorError):
    """Invalid invocation. Always exit ``2``."""


class PathValidationError(MonitorError):
    """A project root or evidence path was rejected. Always exit ``2``."""


class AdapterError(MonitorError):
    """A Herdr command failed or returned an unusable payload."""


class StatusSchemaError(MonitorError):
    """``herdr status --json`` parsed but omitted or mistyped a required field."""


# ---------------------------------------------------------------------------
# Command adapters
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CommandResult:
    """The parts of a completed command this module consumes."""

    returncode: int
    stdout: str
    stderr: str = ""


Runner = Callable[[Sequence[str]], CommandResult]


def default_runner(argv: Sequence[str]) -> CommandResult:
    """Run ``argv`` without a shell and capture its output."""

    completed = subprocess.run(
        list(argv), check=False, capture_output=True, text=True
    )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


@dataclass(frozen=True)
class CommandGrammar:
    """The complete accepted shape of one read-only Herdr command.

    Prefix recognition alone is not a boundary: a command is accepted only when
    every one of its tokens is accounted for, so no extra subcommand, option, or
    trailing argument can ride along behind an allowed prefix.
    """

    adapter: str  # "json" | "text"
    positionals: int
    options: dict[str, int]  # option -> number of values it consumes
    required: frozenset[str] = frozenset()


#: Exact read-only Herdr command grammars. Nothing here mutates control-plane
#: state, and the table contains no ``pane run``, ``agent send``,
#: ``pane send-keys``, ``pane close``, ``pane resize``, ``pane focus``, or
#: ``agent start``. Each command is bound to the single adapter allowed to run
#: it, so a text-only command can never be driven through the JSON adapter.
COMMAND_GRAMMARS: dict[tuple[str, ...], CommandGrammar] = {
    ("status",): CommandGrammar(
        adapter="json",
        positionals=0,
        options={"--json": 0},
        required=frozenset({"--json"}),
    ),
    ("integration", "status"): CommandGrammar(
        adapter="text", positionals=0, options={}
    ),
    ("agent", "list"): CommandGrammar(adapter="json", positionals=0, options={}),
    ("agent", "get"): CommandGrammar(adapter="json", positionals=1, options={}),
    ("agent", "read"): CommandGrammar(
        adapter="json",
        positionals=1,
        options={"--source": 1, "--lines": 1},
        required=frozenset({"--source", "--lines"}),
    ),
    ("agent", "explain"): CommandGrammar(
        adapter="json",
        positionals=1,
        options={"--json": 0},
        required=frozenset({"--json"}),
    ),
    ("agent", "wait"): CommandGrammar(
        adapter="json",
        positionals=1,
        options={"--status": 1, "--timeout": 1},
        required=frozenset({"--status", "--timeout"}),
    ),
}


#: The read-only command allowlist, derived from the grammar table so the two
#: can never drift apart.
READ_ONLY_COMMANDS: frozenset[tuple[str, ...]] = frozenset(COMMAND_GRAMMARS)


def validate_argv(argv: Sequence[str]) -> tuple[tuple[str, ...], CommandGrammar]:
    """Validate one argv against its complete command grammar.

    Returns the matched command prefix and its grammar. Raises
    :class:`MonitorError` for anything else: a non-``herdr`` program, a command
    outside the allowlist, an unknown or duplicated option, a missing option
    value, wrong positional arity, trailing tokens smuggled behind an allowed
    prefix, or an unbounded ``herdr agent wait`` timeout.
    """

    parts = list(argv)
    if not parts or parts[0] != "herdr":
        raise MonitorError(f"refusing non-herdr command: {' '.join(parts)!r}")

    prefix: tuple[str, ...] | None = None
    for length in (2, 1):
        candidate = tuple(parts[1 : 1 + length])
        if candidate in COMMAND_GRAMMARS:
            prefix = candidate
            break
    if prefix is None:
        raise MonitorError(
            f"refusing command outside the read-only allowlist: {' '.join(parts)!r}"
        )
    grammar = COMMAND_GRAMMARS[prefix]
    rest = parts[1 + len(prefix) :]

    # Every wait timeout occurrence is bounded before the duplicate rule can
    # short-circuit, so no occurrence can slip past unchecked.
    if prefix == ("agent", "wait"):
        _assert_every_timeout_is_bounded(rest)

    seen: set[str] = set()
    positionals = 0
    index = 0
    while index < len(rest):
        token = rest[index]
        if token.startswith("-"):
            if token not in grammar.options:
                raise MonitorError(
                    f"refusing unknown option {token!r} for "
                    f"{'herdr ' + ' '.join(prefix)!r}"
                )
            if token in seen:
                raise MonitorError(
                    f"refusing duplicate option {token!r} for "
                    f"{'herdr ' + ' '.join(prefix)!r}"
                )
            seen.add(token)
            arity = grammar.options[token]
            if index + arity > len(rest) - 1:
                raise MonitorError(f"option {token!r} is missing its value")
            for offset in range(1, arity + 1):
                value = rest[index + offset]
                if value.startswith("-"):
                    raise MonitorError(f"option {token!r} is missing its value")
            index += arity + 1
            continue
        positionals += 1
        index += 1

    if positionals != grammar.positionals:
        raise MonitorError(
            f"{'herdr ' + ' '.join(prefix)!r} takes exactly "
            f"{grammar.positionals} argument(s), got {positionals}: "
            f"{' '.join(parts)!r}"
        )
    missing = sorted(grammar.required - seen)
    if missing:
        raise MonitorError(
            f"{'herdr ' + ' '.join(prefix)!r} is missing required option(s): "
            f"{', '.join(missing)}"
        )
    return prefix, grammar


def assert_read_only(argv: Sequence[str]) -> None:
    """Reject any argv outside the read-only allowlist.

    Also enforces the hard ``herdr agent wait`` timeout cap, so no caller can
    reach a longer wait by assembling argv by hand.
    """

    validate_argv(argv)


def _assert_every_timeout_is_bounded(rest: Sequence[str]) -> None:
    occurrences = [index for index, token in enumerate(rest) if token == "--timeout"]
    if not occurrences:
        raise MonitorError("herdr agent wait requires an explicit --timeout")
    for position in occurrences:
        if position + 1 >= len(rest):
            raise MonitorError("herdr agent wait --timeout is missing its value")
        raw = rest[position + 1]
        try:
            timeout = int(raw)
        except ValueError:
            raise MonitorError(
                f"herdr agent wait --timeout must be an integer: {raw!r}"
            ) from None
        if timeout <= 0 or timeout > MAX_WAIT_TIMEOUT_MS:
            raise MonitorError(
                f"herdr agent wait --timeout must be 1..{MAX_WAIT_TIMEOUT_MS} ms, "
                f"got {timeout}"
            )


def wait_argv(name: str, status: str, timeout_ms: int = MAX_WAIT_TIMEOUT_MS) -> list[str]:
    """Build a bounded ``herdr agent wait`` argv.

    The timeout is capped in code, never merely documented.
    """

    if not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool):
        raise MonitorError("wait timeout must be an integer number of milliseconds")
    if timeout_ms <= 0 or timeout_ms > MAX_WAIT_TIMEOUT_MS:
        raise MonitorError(
            f"wait timeout must be 1..{MAX_WAIT_TIMEOUT_MS} ms, got {timeout_ms}"
        )
    argv = ["herdr", "agent", "wait", name, "--status", status, "--timeout", str(timeout_ms)]
    assert_read_only(argv)
    return argv


def run_json(argv: Sequence[str], runner: Runner | None = None) -> dict[str, Any]:
    """Strict JSON adapter: nonzero exit or non-JSON stdout is a hard error.

    Bound to the commands whose grammar declares the ``json`` adapter. A
    text-only command such as ``herdr integration status`` is refused here.
    """

    prefix, grammar = validate_argv(argv)
    if grammar.adapter != "json":
        raise MonitorError(
            f"{'herdr ' + ' '.join(prefix)!r} is a {grammar.adapter} command and "
            "must not be run through the JSON adapter"
        )
    result = (runner or default_runner)(list(argv))
    joined = " ".join(argv)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise AdapterError(f"{joined} failed: {detail}" if detail else f"{joined} failed")
    try:
        payload = json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        raise AdapterError(f"{joined} returned invalid JSON") from None
    if not isinstance(payload, dict):
        raise AdapterError(f"{joined} returned a non-object JSON payload")
    if "error" in payload:
        raise AdapterError(f"{joined} returned an error payload")
    return payload


def run_text(argv: Sequence[str], runner: Runner | None = None) -> str:
    """Plain-text adapter for commands whose supported output is not JSON.

    Used only for ``herdr integration status``, whose ``--json`` flag exits
    ``2`` on Herdr ``0.7.3``. A JSON command is refused here.
    """

    prefix, grammar = validate_argv(argv)
    if grammar.adapter != "text":
        raise MonitorError(
            f"{'herdr ' + ' '.join(prefix)!r} is a {grammar.adapter} command and "
            "must not be run through the text adapter"
        )
    result = (runner or default_runner)(list(argv))
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        joined = " ".join(argv)
        raise AdapterError(f"{joined} failed: {detail}" if detail else f"{joined} failed")
    return result.stdout


# ---------------------------------------------------------------------------
# Typed surface
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IntegrationRow:
    """One parsed ``herdr integration status`` row.

    Carries a runtime identifier and a status token only. Everything else in
    the raw row — in particular the absolute home or configuration path Herdr
    prints — is discarded at the parser and can never reach output.
    """

    runtime: str
    status: str
    classification: str  # "valid" | "unknown-row" | "malformed-row"
    index: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "index": self.index,
            "runtime": self.runtime,
            "status": self.status,
        }


@dataclass(frozen=True)
class CapabilityFinding:
    """A Herdr capability defect the tooling reports and never repairs."""

    agent: str
    code: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {"agent": self.agent, "code": self.code, "detail": self.detail}


@dataclass(frozen=True)
class EvidenceFileReport:
    """Presence metadata for one declared evidence path.

    Collected from a final ``fstat`` on a held descriptor. Content judgment
    stays with the coordinator and reviewers; presence never substitutes for
    reading the evidence.
    """

    path: str
    exists: bool
    is_regular_file: bool
    size_bytes: int | None
    mtime: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "exists": self.exists,
            "is_regular_file": self.is_regular_file,
            "mtime": self.mtime,
            "path": self.path,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class HerdrPreflight:
    """Read-only control-plane report. ``unverified`` never blocks or updates."""

    herdr_found: bool
    client_version: str | None
    server_version: str | None
    protocol: int | None
    compatible: bool | None
    server_restart_needed: bool | None
    update_restart_needed: bool | None
    support: str
    integrations: tuple[IntegrationRow, ...]
    capabilities: tuple[CapabilityFinding, ...]
    findings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "capabilities": [item.as_dict() for item in self.capabilities],
            "client_version": self.client_version,
            "compatible": self.compatible,
            "findings": list(self.findings),
            "herdr_found": self.herdr_found,
            "integrations": [item.as_dict() for item in self.integrations],
            "protocol": self.protocol,
            "report": "preflight",
            "server_restart_needed": self.server_restart_needed,
            "server_version": self.server_version,
            "support": self.support,
            "update_restart_needed": self.update_restart_needed,
        }


@dataclass(frozen=True)
class AgentObservation:
    """One bounded observation of a worker.

    Deliberately has no ``done``, ``success``, or ``complete`` field: the
    status-versus-completion invariant is structural, not instructional.
    ``scheduling_state`` is Herdr's verbatim string and is passed through
    uninterpreted.
    """

    name: str
    pane_id: str | None
    scheduling_state: str | None
    text: str
    source: str
    source_reported: str | None
    lines_requested: int
    lines_counted: int
    native_truncated: bool | None
    truncation_risk: str
    read_error: str | None
    evidence: tuple[EvidenceFileReport, ...]
    findings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence": [item.as_dict() for item in self.evidence],
            "findings": list(self.findings),
            "lines_counted": self.lines_counted,
            "lines_requested": self.lines_requested,
            "name": self.name,
            "native_truncated": self.native_truncated,
            "pane_id": self.pane_id,
            "read_error": self.read_error,
            "report": "observe",
            "scheduling_state": self.scheduling_state,
            "source": self.source,
            "source_reported": self.source_reported,
            "text": self.text,
            "truncation_risk": self.truncation_risk,
        }


# ---------------------------------------------------------------------------
# Integration-status text parser
# ---------------------------------------------------------------------------


#: Anchored grammar for one ``herdr integration status`` row, frozen from a
#: live read-only Herdr ``0.7.3`` probe on 2026-08-14::
#:
#:     <runtime>: <status token>[ (v<N>)] (<absolute path>)
#:
#: The whole row must match. The trailing absolute-path group is required, and
#: the runtime and status captures are bounded character classes that cannot
#: hold a path separator, a parenthesis, or a tilde. A row is therefore either
#: fully understood — in which case only the two bounded tokens are kept — or
#: rejected as ``malformed-row`` with nothing retained from it at all.
INTEGRATION_ROW = re.compile(
    r"^(?P<runtime>[a-z0-9][a-z0-9_-]{0,31})"
    r": "
    r"(?P<status>[a-z][a-z-]{0,31}(?: [a-z][a-z-]{0,31}){0,3})"
    r"(?: \(v(?P<version>[0-9][0-9a-z.+-]{0,31})\))?"
    r" \((?P<path>/[^()]{1,512})\)$"
)


def parse_integration_rows(stdout: str) -> tuple[IntegrationRow, ...]:
    """Parse the plain-text ``herdr integration status`` output.

    The full row is matched against :data:`INTEGRATION_ROW` before any value is
    stored, so a row with a missing path group, a naked absolute path, trailing
    content after the path, or an unbalanced group is ``malformed-row`` and
    contributes no raw remainder to the report. A row that matches the grammar
    but carries an unrecognized runtime or status token is ``unknown-row``, and
    even then only the two bounded tokens are retained. The captured path is
    never stored, so no home or configuration path can reach output.
    """

    rows: list[IntegrationRow] = []
    index = 0
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        index += 1
        match = INTEGRATION_ROW.fullmatch(line)
        if match is None:
            rows.append(IntegrationRow("", "", "malformed-row", index))
            continue
        runtime = match.group("runtime")
        status = match.group("status")
        known = (
            runtime in KNOWN_INTEGRATION_RUNTIMES
            and status in KNOWN_INTEGRATION_STATUSES
        )
        rows.append(
            IntegrationRow(
                runtime=runtime,
                status=status,
                classification="valid" if known else "unknown-row",
                index=index,
            )
        )
    return tuple(rows)


def _integration_findings(rows: Iterable[IntegrationRow]) -> list[str]:
    findings: list[str] = []
    observed_valid_runtimes: set[str] = set()
    for row in rows:
        if row.classification == "malformed-row":
            findings.append(f"malformed-row({row.index})")
        elif row.classification == "unknown-row":
            findings.append(f"unknown-row({row.index})")
        else:
            observed_valid_runtimes.add(row.runtime)
            if (
                row.runtime in REQUIRED_INTEGRATION_RUNTIMES
                and row.status not in HEALTHY_INTEGRATION_STATUSES
            ) or row.status == "outdated":
                findings.append(f"integration-unhealthy({row.runtime}={row.status})")
    for runtime in sorted(REQUIRED_INTEGRATION_RUNTIMES - observed_valid_runtimes):
        findings.append(f"integration-unhealthy({runtime}=missing)")
    return findings


# ---------------------------------------------------------------------------
# Truncation classification
# ---------------------------------------------------------------------------


def completeness_token(source: str) -> str:
    """The capability token that would prove history completeness for ``source``."""

    return f"normal-screen-history-complete:{source}"


def classify_truncation(
    *,
    read_failed: bool,
    native_truncated: bool | None,
    lines_counted: int,
    lines_requested: int,
    source: str,
    capabilities: Iterable[str] = COMPLETENESS_CAPABILITIES,
) -> str:
    """Classify truncation risk in strict precedence order.

    1. ``confirmed`` — the read failed or was partial, or Herdr's native
       ``truncated`` flag is set. The native flag dominates.
    2. ``possible`` — no verified completeness capability proves history
       completeness for this source. This holds even below budget.
    3. ``possible`` — the counted lines equal the requested budget.
    4. ``none`` — only with a proven capability, native ``truncated`` false,
       and a below-budget read.
    """

    if read_failed or native_truncated is None or native_truncated:
        return TRUNCATION_CONFIRMED
    if completeness_token(source) not in set(capabilities):
        return TRUNCATION_POSSIBLE
    if lines_counted >= lines_requested:
        return TRUNCATION_POSSIBLE
    return TRUNCATION_NONE


def count_lines(text: str) -> int:
    """Count the lines the adapter itself sees; Herdr ``0.7.3`` reports none."""

    if not text:
        return 0
    return len(text.splitlines())


# ---------------------------------------------------------------------------
# Descriptor-anchored path validation
# ---------------------------------------------------------------------------

Opener = Callable[..., int]

_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_LEAF_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)


def open_project_root(root: str, *, opener: Opener = os.open) -> int:
    """Validate ``--project-root`` and return a held descriptor.

    Rejects a relative root, a symlinked root, a non-directory root, and a root
    whose device/inode identity changes between the initial ``lstat`` and the
    ``fstat`` of the opened descriptor.

    Threat-model boundary, stated not implied: a non-cooperating process
    running under the same OS identity is outside this tooling's threat model.
    Neither prevention nor detection is claimed against it. This is the same
    stated limit as the task-dossier generator's.
    """

    if not root:
        raise PathValidationError("project root must not be empty")
    if not os.path.isabs(root):
        raise PathValidationError(f"project root must be absolute: {root!r}")

    try:
        before = os.lstat(root)
    except OSError as error:
        raise PathValidationError(f"cannot stat project root {root!r}: {error}") from None
    if stat.S_ISLNK(before.st_mode):
        raise PathValidationError(f"project root is a symlink: {root!r}")
    if not stat.S_ISDIR(before.st_mode):
        raise PathValidationError(f"project root is not a directory: {root!r}")

    try:
        descriptor = opener(root, _DIRECTORY_FLAGS)
    except OSError as error:
        raise PathValidationError(f"cannot open project root {root!r}: {error}") from None

    after = os.fstat(descriptor)
    if (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino):
        os.close(descriptor)
        raise PathValidationError(
            f"project root changed identity during validation: {root!r}"
        )
    return descriptor


def _split_evidence_path(value: str) -> list[str]:
    if not value or not value.strip():
        raise PathValidationError("evidence path must not be empty")
    if value.startswith("~"):
        raise PathValidationError(f"evidence path must not be home-relative: {value!r}")
    if os.path.isabs(value) or value.startswith("\\"):
        raise PathValidationError(f"evidence path must be relative: {value!r}")
    components = [part for part in value.split("/") if part not in ("", ".")]
    if not components:
        raise PathValidationError(f"evidence path resolves to nothing: {value!r}")
    if any(part == ".." for part in components):
        raise PathValidationError(
            f"evidence path must not contain a '..' segment: {value!r}"
        )
    return components


def collect_evidence(
    root_fd: int,
    paths: Sequence[str],
    *,
    opener: Opener = os.open,
) -> tuple[EvidenceFileReport, ...]:
    """Report presence metadata for each declared evidence path.

    The walk is descriptor-relative from the held root descriptor: every
    intermediate component is opened with ``O_DIRECTORY | O_NOFOLLOW`` relative
    to its parent descriptor, the final component with ``O_NOFOLLOW``, and all
    reported metadata comes from ``fstat`` on the final held descriptor. There
    is no pathname re-lookup after validation, so an ancestor swapped after the
    root open cannot redirect the walk outside the held descriptor chain.

    Access is read-only metadata: nothing is created, written, or deleted.
    """

    reports: list[EvidenceFileReport] = []
    for declared in paths:
        components = _split_evidence_path(declared)
        reports.append(_walk_one(root_fd, declared, components, opener=opener))
    return tuple(reports)


def _walk_one(
    root_fd: int,
    declared: str,
    components: Sequence[str],
    *,
    opener: Opener,
) -> EvidenceFileReport:
    parent = root_fd
    opened: list[int] = []
    try:
        for component in components[:-1]:
            try:
                child = opener(component, _DIRECTORY_FLAGS, dir_fd=parent)
            except FileNotFoundError:
                return EvidenceFileReport(declared, False, False, None, None)
            except OSError as error:
                raise _path_rejection(declared, component, error) from None
            opened.append(child)
            parent = child

        leaf = components[-1]
        try:
            descriptor = opener(leaf, _LEAF_FLAGS, dir_fd=parent)
        except FileNotFoundError:
            return EvidenceFileReport(declared, False, False, None, None)
        except OSError as error:
            raise _path_rejection(declared, leaf, error) from None
        try:
            info = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        regular = stat.S_ISREG(info.st_mode)
        return EvidenceFileReport(
            path=declared,
            exists=True,
            is_regular_file=regular,
            size_bytes=info.st_size if regular else None,
            mtime=info.st_mtime,
        )
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)


def _path_rejection(declared: str, component: str, error: OSError) -> PathValidationError:
    if error.errno in {errno.ELOOP, errno.EMLINK, errno.ENOTDIR}:
        # O_NOFOLLOW reports a symlinked directory component as ENOTDIR on
        # macOS and ELOOP on Linux. Both are the same refusal.
        return PathValidationError(
            f"evidence path component {component!r} is a symlink or not a "
            f"directory; refusing to follow it: {declared!r}"
        )
    return PathValidationError(
        f"cannot open evidence path component {component!r}: {error}"
    )


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------


def _require(payload: dict[str, Any], keys: Sequence[str], kind: type) -> Any:
    node: Any = payload
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            raise StatusSchemaError(
                "status-schema-invalid: missing " + ".".join(keys)
            )
        node = node[key]
    if kind is bool:
        if not isinstance(node, bool):
            raise StatusSchemaError(
                "status-schema-invalid: " + ".".join(keys) + " must be a boolean"
            )
    elif kind is int:
        if not isinstance(node, int) or isinstance(node, bool):
            raise StatusSchemaError(
                "status-schema-invalid: " + ".".join(keys) + " must be an integer"
            )
    elif kind is str:
        if not isinstance(node, str) or not node:
            raise StatusSchemaError(
                "status-schema-invalid: " + ".".join(keys) + " must be a string"
            )
    return node


def parse_status_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the required ``herdr status --json`` fields.

    Key spellings frozen from a live read-only Herdr ``0.7.3`` probe.
    """

    return {
        "client_version": _require(payload, ("client", "version"), str),
        "server_version": _require(payload, ("server", "version"), str),
        "protocol": _require(payload, ("server", "protocol"), int),
        "compatible": _require(payload, ("server", "compatible"), bool),
        "server_restart_needed": _require(payload, ("server", "restart_needed"), bool),
        "update_restart_needed": _require(payload, ("update", "restart_needed"), bool),
    }


def explain_capability_findings(
    agent: str, payload: dict[str, Any]
) -> tuple[CapabilityFinding, ...]:
    """Surface Herdr capability drift; never repair it.

    Reproduced on Herdr ``0.7.3``: ``remote_update_status: failed`` with
    ``remote_update_error: rule trust_directory uses invalid region:
    top_non_empty_lines(20)``.
    """

    findings: list[CapabilityFinding] = []
    status = payload.get("remote_update_status")
    if isinstance(status, str) and status == "failed":
        detail = payload.get("remote_update_error")
        findings.append(
            CapabilityFinding(
                agent=agent,
                code="remote-update-failed",
                detail=detail if isinstance(detail, str) else "",
            )
        )
    warning = payload.get("warning")
    if isinstance(warning, str) and warning:
        findings.append(
            CapabilityFinding(agent=agent, code="manifest-warning", detail=warning)
        )
    fallback = payload.get("fallback_reason")
    if isinstance(fallback, str) and fallback:
        findings.append(
            CapabilityFinding(agent=agent, code="manifest-fallback", detail=fallback)
        )
    return tuple(findings)


def run_preflight(
    *,
    runner: Runner | None = None,
    agent: str | None = None,
    verified_support: Iterable[tuple[str, int]] = VERIFIED_SUPPORT,
) -> HerdrPreflight:
    """Collect the read-only control-plane report.

    Raises :class:`AdapterError` or :class:`StatusSchemaError` when the primary
    status probe fails; every other declared state is a finding inside the
    collected report.
    """

    payload = run_json(["herdr", "status", "--json"], runner)
    fields = parse_status_payload(payload)

    findings: list[str] = []
    support = (
        SUPPORT_VERIFIED
        if (fields["server_version"], fields["protocol"]) in set(verified_support)
        else SUPPORT_UNVERIFIED
    )
    if support == SUPPORT_UNVERIFIED:
        findings.append("unverified-version")
    if fields["compatible"] is False:
        findings.append("incompatible-control-plane")
    if fields["server_restart_needed"]:
        findings.append("restart-needed(server)")
    if fields["update_restart_needed"]:
        findings.append("restart-needed(update)")

    rows: tuple[IntegrationRow, ...] = ()
    try:
        stdout = run_text(["herdr", "integration", "status"], runner)
    except AdapterError:
        findings.append("integration-unhealthy")
    else:
        rows = parse_integration_rows(stdout)
        findings.extend(_integration_findings(rows))

    capabilities: tuple[CapabilityFinding, ...] = ()
    if agent:
        try:
            explain = run_json(["herdr", "agent", "explain", agent, "--json"], runner)
        except AdapterError as error:
            capabilities = (
                CapabilityFinding(agent=agent, code="explain-failed", detail=str(error)),
            )
            findings.append("capability-probe-failed")
        else:
            capabilities = explain_capability_findings(agent, explain)
    if capabilities and any(item.code != "explain-failed" for item in capabilities):
        findings.append("capability-drift")

    return HerdrPreflight(
        herdr_found=True,
        client_version=fields["client_version"],
        server_version=fields["server_version"],
        protocol=fields["protocol"],
        compatible=fields["compatible"],
        server_restart_needed=fields["server_restart_needed"],
        update_restart_needed=fields["update_restart_needed"],
        support=support,
        integrations=rows,
        capabilities=capabilities,
        findings=tuple(findings),
    )


# ---------------------------------------------------------------------------
# Observation
# ---------------------------------------------------------------------------


def envelope_result(payload: dict[str, Any], prefix: str) -> dict[str, Any]:
    """Return the envelope's ``result`` object, type-checked before any access.

    A syntactically valid JSON payload can still carry ``"result": null`` or
    ``"result": []``. Dereferencing those with a chained ``.get`` raises an
    unowned ``AttributeError`` that escapes the adapter boundary as a traceback
    instead of the owned failure the exit table requires (code review v3,
    finding M1-v3). Every malformed container becomes an
    :class:`AdapterError` here, so the read path collects it as a
    ``read-failed`` observation at exit ``0`` and the ``agent get`` path
    surfaces it as an owned exit-``1`` diagnostic.
    """

    if "result" not in payload:
        raise AdapterError(f"{prefix} returned an envelope without a result")
    result = payload["result"]
    if not isinstance(result, dict):
        raise AdapterError(
            f"{prefix} returned a malformed result container: expected an "
            f"object, got {type(result).__name__}"
        )
    return result


def canonical_source(value: str) -> str:
    """Normalize a read-source spelling.

    Herdr ``0.7.3`` accepts ``recent-unwrapped`` on the command line and
    reports ``recent_unwrapped`` in the envelope. Both spell the same source.
    """

    return value.strip().lower().replace("_", "-")


def parse_read_payload(
    payload: dict[str, Any], name: str, requested_source: str
) -> dict[str, Any]:
    """Validate the complete successful ``herdr agent read`` schema.

    Every field the truncation contract depends on is required *before*
    classification: a string ``text``, a boolean native ``truncated``, and a
    string ``source`` that canonically matches the source actually requested.
    A payload that omits, mistypes, or mismatches any of them is a partial
    read, not a successful one — it raises here, so
    :func:`classify_truncation` sees ``read_failed`` and yields ``confirmed``.
    Without this gate a short partial payload could reach the ``none`` rule and
    report false completeness (code review v2, finding H1).
    """

    prefix = f"herdr agent read {name}"
    read_node = envelope_result(payload, prefix).get("read")
    if not isinstance(read_node, dict):
        raise AdapterError(f"{prefix} returned no read record")

    text = read_node.get("text")
    if not isinstance(text, str):
        raise AdapterError(f"{prefix} returned a partial read: text is missing or not a string")

    truncated = read_node.get("truncated")
    if not isinstance(truncated, bool):
        raise AdapterError(
            f"{prefix} returned a partial read: native truncated flag is "
            "missing or not a boolean"
        )

    reported = read_node.get("source")
    if not isinstance(reported, str) or not reported.strip():
        raise AdapterError(
            f"{prefix} returned a partial read: source is missing or not a string"
        )
    if canonical_source(reported) != canonical_source(requested_source):
        raise AdapterError(
            f"{prefix} returned a mismatched source: requested "
            f"{canonical_source(requested_source)!r}, reported "
            f"{canonical_source(reported)!r}"
        )
    return {"text": text, "truncated": truncated, "source": reported}


def observe_agent(
    name: str,
    *,
    runner: Runner | None = None,
    lines: int = DEFAULT_READ_LINES,
    source: str = DEFAULT_READ_SOURCE,
    evidence: tuple[EvidenceFileReport, ...] = (),
    capabilities: Iterable[str] = COMPLETENESS_CAPABILITIES,
) -> AgentObservation:
    """Observe one worker read-only.

    ``herdr agent get`` is the primary probe: its failure makes the report
    impossible. A failed ``herdr agent read`` is a collected finding with
    ``truncation_risk`` ``confirmed``, not a failure of the report.

    No code path here sends keys, prompts, or any other input to the agent.
    """

    info = run_json(["herdr", "agent", "get", name], runner)
    get_prefix = f"herdr agent get {name}"
    agent_node = envelope_result(info, get_prefix).get("agent")
    if not isinstance(agent_node, dict):
        raise AdapterError(f"{get_prefix} returned no agent record")

    scheduling_state = agent_node.get("agent_status")
    pane_id = agent_node.get("pane_id")

    findings: list[str] = []
    read_error: str | None = None
    text = ""
    source_reported: str | None = None
    native_truncated: bool | None = None

    try:
        payload = run_json(
            [
                "herdr",
                "agent",
                "read",
                name,
                "--source",
                source,
                "--lines",
                str(lines),
            ],
            runner,
        )
        read_node = parse_read_payload(payload, name, source)
    except AdapterError as error:
        read_error = str(error)
        findings.append("read-failed")
    else:
        text = read_node["text"]
        source_reported = read_node["source"]
        native_truncated = read_node["truncated"]

    lines_counted = count_lines(text)
    risk = classify_truncation(
        read_failed=read_error is not None,
        native_truncated=native_truncated,
        lines_counted=lines_counted,
        lines_requested=lines,
        source=source,
        capabilities=capabilities,
    )

    for report in evidence:
        if not report.exists:
            findings.append(f"evidence-missing({report.path})")
        elif not report.is_regular_file:
            findings.append(f"evidence-not-regular-file({report.path})")

    return AgentObservation(
        name=name,
        pane_id=pane_id if isinstance(pane_id, str) else None,
        scheduling_state=scheduling_state if isinstance(scheduling_state, str) else None,
        text=text,
        source=source,
        source_reported=source_reported,
        lines_requested=lines,
        lines_counted=lines_counted,
        native_truncated=native_truncated,
        truncation_risk=risk,
        read_error=read_error,
        evidence=tuple(evidence),
        findings=tuple(findings),
    )


# ---------------------------------------------------------------------------
# Deterministic rendering and CLI
# ---------------------------------------------------------------------------


def render_report(payload: dict[str, Any]) -> str:
    """One JSON document: sorted keys, two-space indent, one trailing newline."""

    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> Any:  # pragma: no cover - trivial
        raise UsageError(message)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"must be an integer: {value!r}") from None
    if parsed <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive integer: {value!r}")
    return parsed


def build_parser() -> _Parser:
    parser = _Parser(
        prog=PROGRAM,
        description=(
            "Read-only Herdr preflight and worker observation. Scheduling state "
            "is a scheduling signal only; it is not proof that a task finished."
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, parser_class=_Parser
    )

    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--agent", default=None)

    observe = subparsers.add_parser("observe")
    observe.add_argument("name")
    observe.add_argument("--lines", type=_positive_int, default=DEFAULT_READ_LINES)
    observe.add_argument("--source", default=DEFAULT_READ_SOURCE)
    observe.add_argument("--project-root", dest="project_root", default=None)
    observe.add_argument("--evidence", action="append", default=[])
    return parser


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "observe":
        if args.evidence and not args.project_root:
            raise UsageError("--evidence requires --project-root")
    return args


def _herdr_available() -> bool:
    return shutil.which("herdr") is not None


def _preflight_command(args: argparse.Namespace, runner: Runner | None) -> int:
    if not _herdr_available():
        print(f"{PROGRAM}: herdr is not on PATH", file=sys.stderr)
        return 1
    try:
        report = run_preflight(runner=runner, agent=args.agent)
    except (AdapterError, StatusSchemaError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return 1
    sys.stdout.write(render_report(report.as_dict()))
    return 0


def _observe_command(args: argparse.Namespace, runner: Runner | None) -> int:
    # Every argument and path check happens before any subprocess, so a
    # class-2 condition always wins over a class-1 or class-0 outcome.
    evidence: tuple[EvidenceFileReport, ...] = ()
    root_fd: int | None = None
    if args.project_root is not None:
        root_fd = open_project_root(args.project_root)
    try:
        if root_fd is not None and args.evidence:
            evidence = collect_evidence(root_fd, args.evidence)
    finally:
        if root_fd is not None:
            os.close(root_fd)

    if not _herdr_available():
        print(f"{PROGRAM}: herdr is not on PATH", file=sys.stderr)
        return 1
    try:
        observation = observe_agent(
            args.name,
            runner=runner,
            lines=args.lines,
            source=args.source,
            evidence=evidence,
        )
    except AdapterError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return 1
    sys.stdout.write(render_report(observation.as_dict()))
    return 0


def main(argv: Sequence[str] | None = None, *, runner: Runner | None = None) -> int:
    """Entry point. Exit ``0`` collected, ``1`` impossible, ``2`` invalid."""

    try:
        args = _parse_args(argv)
    except UsageError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return 2
    except SystemExit as error:  # argparse --help and friends
        return int(error.code or 0)

    try:
        if args.command == "preflight":
            return _preflight_command(args, runner)
        return _observe_command(args, runner)
    except PathValidationError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return 2
    except MonitorError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
