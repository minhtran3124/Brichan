#!/usr/bin/env python3
"""PreToolUse hook: keep secrets out of reach and guard this checkout's rules.

The permission rules in .claude/settings.json deny the file tools on secret
files and ask before edits to the Claude Code guardrail files. This hook adds
what rules cannot express: Bash commands that name a secret file, a secret
scan of what a `git commit` would record, asks for Bash writes to the
guardrail paths, and asks for edits under docs/policy/ unless the session was
launched with BRICHAN_POLICY_EDIT_TASK for a user-authorized policy task.
Reasons never echo file contents or matched values.
"""

import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))

SECRET_NAME_PATTERNS = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa*",
    ".netrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    ".git-credentials",
)
SECRET_NAME_EXCEPTIONS = (".env.example",)
SECRET_TOKEN_PATTERNS = (
    ("private key block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY( BLOCK)?-----")),
    ("GitHub personal access token", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("GitHub OAuth token", re.compile(r"gho_[A-Za-z0-9]{36}")),
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9_-]{24,}")),
    ("AWS access key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
)

POLICY_GRANT = "BRICHAN_POLICY_EDIT_TASK"
COMMAND_WRAPPERS = frozenset({"env", "exec", "command", "nohup", "nice", "time"})
SHELLS = frozenset({"sh", "bash", "zsh", "dash"})
WRITERS = frozenset(
    {"tee", "cp", "mv", "rm", "ln", "touch", "truncate", "chmod", "install"}
)
GIT_VALUE_FLAGS = frozenset(
    {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}
)
COMMIT_VALUE_SHORT = frozenset("mFCct")
COMMIT_VALUE_LONG = frozenset(
    {
        "--message",
        "--file",
        "--reuse-message",
        "--reedit-message",
        "--template",
        "--author",
        "--date",
        "--cleanup",
        "--trailer",
        "--fixup",
        "--squash",
        "--pathspec-from-file",
    }
)
COMMIT_SCOPE_SHORT = frozenset("aio")
COMMIT_SCOPE_LONG = ("--all", "--include", "--only", "--pathspec-from-file")
MAX_DEPTH = 3
GIT_TIMEOUT = 8

SECRET_REASON = (
    "Secret files are off limits in this checkout: {word!r} matches the "
    "secret-name pattern {pattern!r}. Their contents are never read or shown."
)
COMMIT_REASON = (
    "This commit would record a likely secret: {findings}. Remove it from the "
    "change before committing; the matched value is not shown."
)
SCAN_FAILED_REASON = (
    "The commit secret scan could not run ({error}), so the commit is blocked "
    "rather than allowed through unscanned."
)
GUARDRAIL_REASON = (
    "This command writes to a Claude Code guardrail path in this checkout "
    "({path}). Approve only a change the user asked for."
)
POLICY_REASON = (
    "This changes canonical policy under docs/policy/ ({path}). Approve only a "
    "policy change the user authorized; delegated policy tasks are launched "
    "with " + POLICY_GRANT + "."
)

ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
SUBSTITUTION = re.compile(r"\$\(([^()]*)\)|`([^`]*)`")
SEPARATORS = "();<>|&\n"


class Command:
    """One simple command: its words and its redirection targets."""

    def __init__(self):
        self.words: list[str] = []
        self.targets: list[tuple[str, bool]] = []  # (target, is_output)


def _commands(command: str):
    """Yield each simple command of a shell string.

    Newlines outside quotes separate commands. A punctuation run holding `<`
    or `>` is a redirection, not a separator: the next token is its target,
    never a word or a new command; after an operator ending in `&`, a digits
    or `-` token is a descriptor duplication, not a path; and a digits-only
    word just before the operator is a descriptor number, not a path.
    """
    lexer = shlex.shlex(command, posix=True, punctuation_chars=SEPARATORS)
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    current = Command()
    redirect = None
    for token in lexer:
        if redirect is not None:
            if not (redirect.endswith("&") and (token.isdigit() or token == "-")):
                current.targets.append((token, ">" in redirect))
            redirect = None
        elif token == "$" or token.strip(SEPARATORS) == "":
            if "<" in token or ">" in token:
                if token.strip("<>&") != "":
                    if current.words or current.targets:
                        yield current
                    current = Command()
                if current.words and current.words[-1].isdigit():
                    current.words.pop()
                redirect = token
            else:
                if current.words or current.targets:
                    yield current
                current = Command()
        else:
            current.words.append(token)
    if current.words or current.targets:
        yield current


def _executable(words: list[str]):
    """Skip variable assignments and simple wrappers; return (name, arguments)."""
    index = 0
    while index < len(words):
        name = os.path.basename(words[index])
        if ASSIGNMENT.match(words[index]):
            index += 1
        elif name in COMMAND_WRAPPERS or name == "timeout":
            index += 1
            while index < len(words) and words[index].startswith("-"):
                index += 1
            if name == "timeout":
                index += 1
        else:
            return name, words[index + 1 :]
    return None, []


def _shell_strings(name, arguments):
    """Return the -c command strings of an sh/bash/zsh/dash invocation."""
    if name not in SHELLS:
        return []
    for index, word in enumerate(arguments):
        if word.startswith("-") and not word.startswith("--") and "c" in word[1:]:
            return arguments[index + 1 : index + 2]
    return []


def simple_commands(command: str, depth: int = 0):
    """Return every simple command, including substitution bodies and -c strings.

    Substitution bodies and -c strings share one depth budget. A string shlex
    cannot tokenize contributes nothing.
    """
    found: list[Command] = []
    if depth < MAX_DEPTH:
        for match in SUBSTITUTION.finditer(command):
            body = match.group(1) if match.group(1) is not None else match.group(2)
            found.extend(simple_commands(body, depth + 1))
    try:
        commands = list(_commands(command))
    except ValueError:
        return found
    found.extend(commands)
    if depth < MAX_DEPTH:
        for item in commands:
            for inner in _shell_strings(*_executable(item.words)):
                found.extend(simple_commands(inner, depth + 1))
    return found


def secret_pattern(path: str):
    """Return the secret-name pattern a path's file name matches, or None."""
    name = os.path.basename(path.rstrip("/"))
    if name in SECRET_NAME_EXCEPTIONS:
        return None
    for pattern in SECRET_NAME_PATTERNS:
        if fnmatch.fnmatchcase(name, pattern):
            return pattern
    return None


def check_secret_paths(commands, cwd: str):
    for item in commands:
        candidates = [target for target, _ in item.targets]
        candidates += [
            word
            for word in item.words
            if "/" in word or os.path.lexists(os.path.join(cwd, word))
        ]
        for word in candidates:
            pattern = secret_pattern(word)
            if pattern is not None:
                return SECRET_REASON.format(word=word, pattern=pattern)
    return None


def _git_globals(arguments: list[str]):
    """Split git's global options; return (pass-through flags, rest) or None."""
    passed: list[str] = []
    index = 0
    while index < len(arguments):
        word = arguments[index]
        if word in GIT_VALUE_FLAGS:
            if word in ("-C", "-c"):
                passed += arguments[index : index + 2]
            index += 2
        elif word.startswith("-"):
            index += 1
        else:
            return passed, arguments[index:]
    return None


def _extended_scope(arguments: list[str]) -> bool:
    """Whether a commit's scope can exceed the index.

    Any word not recognized as a flag or a flag value counts as a pathspec,
    so a misclassification only ever widens the scan.
    """
    index = 0
    while index < len(arguments):
        word = arguments[index]
        index += 1
        if word == "--":
            return True
        if word.startswith("--"):
            name, attached, _ = word.partition("=")
            if any(option.startswith(name) for option in COMMIT_SCOPE_LONG):
                return True
            if name in COMMIT_VALUE_LONG and not attached:
                index += 1
        elif word.startswith("-") and len(word) > 1:
            for position, flag in enumerate(word[1:], start=1):
                if flag in COMMIT_SCOPE_SHORT:
                    return True
                if flag in COMMIT_VALUE_SHORT:
                    if position == len(word) - 1:
                        index += 1
                    break
        else:
            return True
    return False


def commit_scans(commands, command: str):
    """Return (git global flags, scan worktree too) for each commit to scan."""
    scans = []
    for item in commands:
        name, arguments = _executable(item.words)
        if name != "git":
            continue
        split = _git_globals(arguments)
        if split is not None and split[1][0] == "commit":
            scans.append((split[0], _extended_scope(split[1][1:])))
    if not scans and "commit" in command:
        scans.append(([], True))
    return scans


def _added_lines(diff: str):
    """Yield (file, line) for each added line of a unified diff."""
    path = None
    in_header = False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            in_header = True
            path = line.rsplit(" b/", 1)[-1]
        elif in_header and line.startswith("+++ "):
            target = line[4:]
            if target != "/dev/null":
                path = target[2:] if target.startswith("b/") else target
        elif line.startswith("@@"):
            in_header = False
        elif not in_header and line.startswith("+"):
            yield path, line[1:]


def scan_commit(flags: list[str], worktree: bool, cwd: str):
    """Return a deny reason when the commit's diffs add a secret token."""
    diffs = [["diff", "--cached", "-U0", "--no-color"]]
    if worktree:
        diffs.append(["diff", "-U0", "--no-color"])
    findings: list[str] = []
    for diff in diffs:
        try:
            result = subprocess.run(
                ["git", *flags, *diff],
                cwd=cwd,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=GIT_TIMEOUT,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return SCAN_FAILED_REASON.format(error=type(error).__name__)
        if result.returncode != 0:
            lines = result.stderr.strip().splitlines()
            summary = lines[0][:200] if lines else f"git exit {result.returncode}"
            return SCAN_FAILED_REASON.format(error=summary)
        for path, line in _added_lines(result.stdout):
            for kind, pattern in SECRET_TOKEN_PATTERNS:
                finding = f"{path} adds a {kind}"
                if pattern.search(line) and finding not in findings:
                    findings.append(finding)
    if findings:
        return COMMIT_REASON.format(findings="; ".join(findings))
    return None


def _relative(path: str, cwd: str):
    """Return path relative to the checkout root, or None when outside it."""
    resolved = os.path.realpath(os.path.join(cwd, os.path.expanduser(path)))
    relative = os.path.relpath(resolved, ROOT)
    if relative == ".." or relative.startswith(".." + os.sep):
        return None
    return relative.replace(os.sep, "/")


def is_guardrail(relative: str) -> bool:
    return (
        fnmatch.fnmatchcase(relative, ".claude/settings*.json")
        or relative == ".claude/hooks"
        or relative.startswith(".claude/hooks/")
    )


def is_policy(relative: str) -> bool:
    return relative == "docs/policy" or relative.startswith("docs/policy/")


def _write_targets(item: Command):
    targets = [target for target, is_output in item.targets if is_output]
    name, arguments = _executable(item.words)
    in_place = name == "sed" and any(
        word.startswith("--in-place")
        or (word.startswith("-") and not word.startswith("--") and "i" in word)
        for word in arguments
    )
    if name in WRITERS or in_place:
        targets += arguments
    return targets


def check_writes(commands, cwd: str):
    """Return (guardrail paths, policy paths) the commands write to."""
    guardrail: list[str] = []
    policy: list[str] = []
    for item in commands:
        for target in _write_targets(item):
            relative = _relative(target, cwd)
            if relative is None:
                continue
            if is_guardrail(relative):
                guardrail.append(relative)
            elif is_policy(relative):
                policy.append(relative)
    return guardrail, policy


def policy_granted() -> bool:
    return bool(os.environ.get(POLICY_GRANT))


def bash_decision(command: str, cwd: str):
    commands = simple_commands(command)
    reason = check_secret_paths(commands, cwd)
    if reason is not None:
        return "deny", reason
    for flags, worktree in commit_scans(commands, command):
        reason = scan_commit(flags, worktree, cwd)
        if reason is not None:
            return "deny", reason
    guardrail, policy = check_writes(commands, cwd)
    if guardrail:
        return "ask", GUARDRAIL_REASON.format(path=guardrail[0])
    if policy and not policy_granted():
        return "ask", POLICY_REASON.format(path=policy[0])
    return None


def file_decision(tool_input: dict, cwd: str):
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(path, str):
        return None
    relative = _relative(path, cwd)
    if relative is not None and is_policy(relative) and not policy_granted():
        return "ask", POLICY_REASON.format(path=relative)
    return None


def _decision(kind: str, reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": kind,
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    try:
        event = json.load(sys.stdin)
        tool = event["tool_name"]
    except (ValueError, KeyError, TypeError):
        print("protect_secrets: unreadable hook input", file=sys.stderr)
        return 2
    tool_input = event.get("tool_input") or {}
    cwd = event.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        cwd = os.getcwd()
    if not isinstance(tool_input, dict):
        return 0
    result = None
    if tool == "Bash":
        command = tool_input.get("command")
        if isinstance(command, str):
            result = bash_decision(command, cwd)
    elif tool in ("Edit", "Write", "NotebookEdit"):
        result = file_decision(tool_input, cwd)
    if result is not None:
        json.dump(_decision(*result), sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
