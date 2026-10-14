"""The checkout's Claude Code hook keeps secrets out and guards its own rules."""

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".claude/hooks/protect_secrets.py"
SETTINGS = ROOT / ".claude/settings.json"
GRANT = "BRICHAN_POLICY_EDIT_TASK"
SENTINEL = "sentinel-file-contents"


def fake_token():
    # Built at runtime so no committed file holds a literal token.
    return "ghp" + "_" + 36 * "a"


def base_env(**extra):
    env = {key: value for key, value in os.environ.items() if key != GRANT}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    env.update(extra)
    return env


def run_hook(payload, env=None):
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        env=env or base_env(),
    )


def run_bash(command, cwd, env=None):
    return run_hook(
        {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)},
        env,
    )


def decision(result):
    if not result.stdout:
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


def git(repo, *arguments):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *arguments],
        cwd=repo,
        env=base_env(),
        capture_output=True,
        check=True,
    )


def make_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    (path / "tracked.txt").write_text("base\n", encoding="utf-8")
    (path / "other.txt").write_text("base\n", encoding="utf-8")
    git(path, "add", ".")
    git(path, "commit", "-q", "-m", "init")
    return path


class TempDirTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def assertDecision(self, expected, result):
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(expected, decision(result), result.stdout)


class SecretPathTest(TempDirTest):
    def setUp(self):
        super().setUp()
        for name in (".env", "deploy/server.pem", "id_rsa", ".netrc", ".pypirc"):
            path = self.tmp / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(SENTINEL, encoding="utf-8")
        (self.tmp / ".env.example").write_text("KEY=\n", encoding="utf-8")
        (self.tmp / "README.md").write_text("readme\n", encoding="utf-8")

    def test_commands_naming_secret_files_are_denied(self):
        for command in (
            "cat .env",
            "head deploy/server.pem",
            "sed -n 1p id_rsa",
            "python3 tool.py --config .netrc",
            "echo $(cat .env)",
            'echo "$(cat .env)"',
            "cat < .pypirc",
            "sh -c 'cat .env'",
        ):
            with self.subTest(command=command):
                result = run_bash(command, self.tmp)
                self.assertDecision("deny", result)
                self.assertIn("off limits", result.stdout)
                self.assertNotIn(SENTINEL, result.stdout)

    def test_other_commands_get_no_decision(self):
        for command in (
            "cat .env.example",
            "cat README.md",
            "grep -r x .",
            "python3 -m unittest",
            "echo 'cat .env'",
        ):
            with self.subTest(command=command):
                self.assertDecision(None, run_bash(command, self.tmp))


class PathShapeTest(TempDirTest):
    def test_bare_secret_words_without_such_a_file_get_no_decision(self):
        for command in (
            "git grep credentials",
            "grep -rn credentials docs/",
            "git grep .env",
            "cat .env",
        ):
            with self.subTest(command=command):
                self.assertDecision(None, run_bash(command, self.tmp))

    def test_words_with_a_separator_are_paths_even_when_absent(self):
        self.assertDecision("deny", run_bash("head deploy/server.pem", self.tmp))

    def test_bare_secret_word_naming_an_existing_file_is_denied(self):
        (self.tmp / "credentials").write_text(SENTINEL, encoding="utf-8")
        self.assertDecision("deny", run_bash("grep -rn credentials .", self.tmp))


class RedirectTest(TempDirTest):
    def test_descriptor_redirects_are_not_paths_or_commands(self):
        for command in (
            "grep x file 2>/dev/null",
            "cat foo 2>&1",
            "echo x 2> errors.log",
        ):
            with self.subTest(command=command):
                self.assertDecision(None, run_bash(command, self.tmp))

    def test_redirect_targets_are_paths_even_when_absent(self):
        for command in ("cat < .pypirc", "echo x > .env"):
            with self.subTest(command=command):
                self.assertDecision("deny", run_bash(command, self.tmp))


class CommitScanTest(TempDirTest):
    def setUp(self):
        super().setUp()
        self.repo = make_repo(self.tmp / "repo")

    def put_token(self, name="tracked.txt", stage=False):
        (self.repo / name).write_text("base\n" + fake_token() + "\n", encoding="utf-8")
        if stage:
            git(self.repo, "add", name)

    def test_staged_token_is_denied_without_echoing_it(self):
        self.put_token(stage=True)
        result = run_bash("git commit -m msg", self.repo)
        self.assertDecision("deny", result)
        self.assertIn("tracked.txt", result.stdout)
        self.assertIn("GitHub personal access token", result.stdout)
        self.assertNotIn(fake_token(), result.stdout)

    def test_clean_staged_diff_gets_no_decision(self):
        (self.repo / "tracked.txt").write_text("base\nmore\n", encoding="utf-8")
        git(self.repo, "add", "tracked.txt")
        self.assertDecision(None, run_bash("git commit -m msg", self.repo))

    def test_removing_a_token_gets_no_decision(self):
        self.put_token(stage=True)
        git(self.repo, "commit", "-q", "-m", "setup")
        (self.repo / "tracked.txt").write_text("base\n", encoding="utf-8")
        git(self.repo, "add", "tracked.txt")
        self.assertDecision(None, run_bash("git commit -m msg", self.repo))

    def test_scan_failure_blocks_the_commit(self):
        outside = self.tmp / "not-a-repo"
        outside.mkdir()
        env = base_env(GIT_CEILING_DIRECTORIES=str(self.tmp))
        result = run_bash("git commit -m msg", outside, env)
        self.assertDecision("deny", result)
        self.assertIn("could not run", result.stdout)

    def test_commits_that_can_record_unstaged_changes_scan_the_worktree(self):
        self.put_token()
        for command in (
            "git commit -a -m msg",
            "git commit -am msg",
            "git commit tracked.txt -m msg",
            "git commit --only tracked.txt -m msg",
            "git commit -om msg tracked.txt",
            "git commit other.txt -m msg",
        ):
            with self.subTest(command=command):
                self.assertDecision("deny", run_bash(command, self.repo))

    def test_plain_commit_scans_only_the_staged_diff(self):
        self.put_token()
        self.assertDecision(None, run_bash("git commit -m msg", self.repo))

    def test_shell_wrapped_commit_is_scanned(self):
        self.put_token(stage=True)
        self.assertDecision("deny", run_bash("bash -c 'git commit -m x'", self.repo))

    def test_commit_substring_triggers_a_conservative_scan(self):
        self.assertDecision(None, run_bash("echo commit", self.repo))
        self.put_token()
        self.assertDecision("deny", run_bash("echo commit", self.repo))

    def test_git_dash_c_target_is_scanned(self):
        self.put_token(stage=True)
        elsewhere = make_repo(self.tmp / "elsewhere")
        command = f"git -C {self.repo} commit -m msg"
        self.assertDecision("deny", run_bash(command, elsewhere))


class GuardrailAskTest(TempDirTest):
    def test_bash_writes_to_guardrail_paths_ask(self):
        for command in (
            "tee .claude/settings.json",
            "cp x .claude/hooks/y.py",
            "sed -i s/a/b/ .claude/settings.json",
            "echo x > .claude/settings.json",
        ):
            with self.subTest(command=command):
                self.assertDecision("ask", run_bash(command, ROOT))

    def test_relative_paths_resolve_against_the_event_cwd(self):
        self.assertDecision("ask", run_bash("tee ../.claude/settings.json", ROOT / "src"))

    def test_reading_or_running_guardrail_files_gets_no_decision(self):
        for command in (
            "cat .claude/settings.json",
            "cat < .claude/settings.json",
            "python3 .claude/hooks/protect_secrets.py --help",
        ):
            with self.subTest(command=command):
                self.assertDecision(None, run_bash(command, ROOT))


class PolicyAskTest(TempDirTest):
    POLICY_FILE = str(ROOT / "docs/policy/reviewer.md")

    def file_event(self, tool, path):
        key = "notebook_path" if tool == "NotebookEdit" else "file_path"
        return {"tool_name": tool, "tool_input": {key: path}, "cwd": str(ROOT)}

    def test_policy_edits_ask_without_the_grant(self):
        for tool in ("Edit", "Write", "NotebookEdit"):
            for env in (base_env(), base_env(**{GRANT: ""})):
                with self.subTest(tool=tool, grant=env.get(GRANT)):
                    result = run_hook(self.file_event(tool, self.POLICY_FILE), env)
                    self.assertDecision("ask", result)

    def test_policy_edits_with_the_grant_get_no_decision(self):
        env = base_env(**{GRANT: "CLAUDE-010"})
        for tool in ("Edit", "Write", "NotebookEdit"):
            with self.subTest(tool=tool):
                result = run_hook(self.file_event(tool, self.POLICY_FILE), env)
                self.assertDecision(None, result)

    def test_other_docs_edits_get_no_decision(self):
        path = str(ROOT / "docs/guides/example.md")
        self.assertDecision(None, run_hook(self.file_event("Edit", path)))

    def test_bash_policy_writes_follow_the_grant(self):
        command = "tee docs/policy/reviewer.md"
        self.assertDecision("ask", run_bash(command, ROOT))
        granted = base_env(**{GRANT: "CLAUDE-010"})
        self.assertDecision(None, run_bash(command, ROOT, granted))

    def test_grant_does_not_cover_guardrail_writes(self):
        command = "tee docs/policy/reviewer.md; tee .claude/settings.json"
        granted = base_env(**{GRANT: "CLAUDE-010"})
        self.assertDecision("ask", run_bash(command, ROOT, granted))


class HookContractTest(unittest.TestCase):
    def test_unreadable_input_blocks(self):
        for payload in ("not json", "{}", "[]"):
            with self.subTest(payload=payload):
                self.assertEqual(2, run_hook(payload).returncode)

    def test_ordinary_tools_get_no_decision(self):
        for tool in ("Read", "Grep"):
            with self.subTest(tool=tool):
                result = run_hook(
                    {"tool_name": tool, "tool_input": {"file_path": ".env"}}
                )
                self.assertEqual(0, result.returncode)
                self.assertEqual("", result.stdout)


def hook_constant(name):
    tree = ast.parse(HOOK.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found in {HOOK}")


class TestSettingsWiring(unittest.TestCase):
    """Passes only once .claude/settings.json activates the hook (plan step 6)."""

    PATTERNS = (
        ".env",
        ".env.*",
        "!.env.example",
        "*.pem",
        "*.key",
        "id_rsa*",
        ".netrc",
        ".pypirc",
        "credentials",
        "credentials.json",
        ".git-credentials",
    )

    def setUp(self):
        self.settings = json.loads(SETTINGS.read_text(encoding="utf-8"))

    def test_hook_is_registered_fail_closed(self):
        hooks = [
            (entry["matcher"], hook)
            for entry in self.settings["hooks"]["PreToolUse"]
            for hook in entry["hooks"]
            if hook["command"] == "${CLAUDE_PROJECT_DIR}/.claude/hooks/protect_secrets.py"
        ]
        self.assertEqual(1, len(hooks))
        matcher, hook = hooks[0]
        self.assertEqual("Bash|Edit|Write|NotebookEdit", matcher)
        self.assertEqual(10, hook["timeout"])
        self.assertEqual("block", hook["onFailure"])
        self.assertTrue(os.access(HOOK, os.X_OK))

    def test_permission_rules_cover_secret_and_guardrail_paths(self):
        deny = self.settings["permissions"]["deny"]
        for tool in ("Read", "Edit"):
            rules = [f"{tool}({pattern})" for pattern in self.PATTERNS]
            with self.subTest(tool=tool):
                for rule in rules:
                    self.assertIn(rule, deny)
                carve_out = deny.index(f"{tool}(!.env.example)")
                self.assertLess(deny.index(f"{tool}(.env)"), carve_out)
                self.assertLess(deny.index(f"{tool}(.env.*)"), carve_out)
        self.assertEqual(
            {
                "Edit(.claude/settings.json)",
                "Edit(.claude/settings.local.json)",
                "Edit(.claude/hooks/**)",
            },
            set(self.settings["permissions"]["ask"]),
        )

    def test_settings_and_hook_share_one_pattern_list(self):
        deny = self.settings["permissions"]["deny"]
        for tool in ("Read", "Edit"):
            prefix = f"{tool}("
            patterns = [rule[len(prefix) : -1] for rule in deny if rule.startswith(prefix)]
            with self.subTest(tool=tool):
                self.assertEqual(
                    set(hook_constant("SECRET_NAME_PATTERNS")),
                    {p for p in patterns if not p.startswith("!")},
                )
                self.assertEqual(
                    set(hook_constant("SECRET_NAME_EXCEPTIONS")),
                    {p[1:] for p in patterns if p.startswith("!")},
                )


if __name__ == "__main__":
    unittest.main()
