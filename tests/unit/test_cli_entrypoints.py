import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan import __version__
from brichan.cli._root import exec_runtime
from brichan.cli import claude as claude_cli
from brichan.cli import codex as codex_cli
from brichan.cli import opencode as opencode_cli
from brichan.cli import runtime as runtime_cli
from brichan.lifecycle import initialize_project
from brichan.project import project_paths


_NOT_A_CHECKOUT = RuntimeError(
    "cannot locate the Brichan repository root; run inside the repository "
    "or set BRICHAN_ROOT"
)


class _OutsideCheckoutTestCase(unittest.TestCase):
    """Runs each test with cwd in a directory that is neither a Git
    repository nor the Brichan checkout, and without BRICHAN_ROOT set.

    ``repository_root`` is also patched to fail the way it does when the
    package is installed outside any checkout (e.g. into site-packages):
    unit tests otherwise run with this repository's own ``src/`` on
    ``sys.path``, so the real fallback in ``_root.repository_root`` would
    find this checkout's ``AGENTS.md`` and mask the installed-elsewhere
    behavior under test — and, for brichan-claude/brichan-codex, would exec the
    real ``claude``/``codex`` binaries as a side effect.
    """

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.outside = Path(self.temporary.name) / "outside"
        self.outside.mkdir()
        self.previous_cwd = Path.cwd()
        os.chdir(self.outside)
        self.addCleanup(os.chdir, self.previous_cwd)
        self.previous_root = os.environ.pop("BRICHAN_ROOT", None)
        self.addCleanup(self._restore_root)

    def _restore_root(self):
        if self.previous_root is not None:
            os.environ["BRICHAN_ROOT"] = self.previous_root

    def _run(self, main, argv):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()


class RuntimeInstalledDefaultTest(_OutsideCheckoutTestCase):
    def test_help_works_before_initialization(self):
        code, out, err = self._run(runtime_cli.main, ["--help"])
        self.assertEqual(0, code)
        self.assertIn("usage: brichan", out)
        self.assertEqual("", err)

    def test_short_help_flag_works_before_initialization(self):
        code, out, _ = self._run(runtime_cli.main, ["-h"])
        self.assertEqual(0, code)
        self.assertIn("usage: brichan", out)

    def test_version_works_before_initialization(self):
        code, out, err = self._run(runtime_cli.main, ["--version"])
        self.assertEqual(0, code)
        self.assertEqual(f"brichan {__version__}\n", out)
        self.assertEqual("", err)

    def test_other_arguments_still_report_owned_uninitialized_error(self):
        code, out, err = self._run(runtime_cli.main, ["do something"])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("brichan:", err)

    def test_help_works_inside_a_git_repo_that_is_not_yet_initialized(self):
        # A Git repository without a .brichan directory takes a different
        # internal path (RoutingError via inspect_project) than a directory
        # that is not a Git repository at all (ProjectError); both must
        # short-circuit --help/--version before touching that error.
        target = self.outside / "uninitialized-project"
        target.mkdir()
        (target / ".git").mkdir()
        os.chdir(target)
        code, out, err = self._run(runtime_cli.main, ["--help"])
        self.assertEqual(0, code)
        self.assertIn("usage: brichan", out)
        self.assertEqual("", err)

    def test_version_works_inside_a_git_repo_that_is_not_yet_initialized(self):
        target = self.outside / "uninitialized-project"
        target.mkdir()
        (target / ".git").mkdir()
        os.chdir(target)
        code, out, err = self._run(runtime_cli.main, ["--version"])
        self.assertEqual(0, code)
        self.assertEqual(f"brichan {__version__}\n", out)
        self.assertEqual("", err)

    def test_other_arguments_inside_uninitialized_git_repo_still_error(self):
        target = self.outside / "uninitialized-project"
        target.mkdir()
        (target / ".git").mkdir()
        os.chdir(target)
        code, out, err = self._run(runtime_cli.main, ["do something"])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("brichan: project state is uninitialized", err)

    def test_help_and_version_pass_through_to_codex_inside_healthy_project(self):
        target = self.outside / "project"
        target.mkdir()
        (target / ".git").mkdir()
        paths = project_paths(explicit=target)
        initialize_project(paths, apply=True)
        os.chdir(target)
        with mock.patch.object(runtime_cli, "run_project") as run_project:
            run_project.return_value = 0
            code, out, err = self._run(runtime_cli.main, ["--help"])
        self.assertEqual(0, code)
        self.assertEqual("", out)
        self.assertEqual("", err)
        run_project.assert_called_once()
        self.assertEqual(["--help"], run_project.call_args.args[1])

    def test_bare_launch_inside_healthy_project_is_unaffected(self):
        target = self.outside / "project"
        target.mkdir()
        (target / ".git").mkdir()
        paths = project_paths(explicit=target)
        initialize_project(paths, apply=True)
        os.chdir(target)
        # A healthy project attempts to launch codex rather than short-circuit
        # into the pre-initialization help path; RoutingError/ValueError paths
        # are exercised elsewhere, so only assert we did not take the
        # uninitialized branch (which would name "brichan init").
        code, _, err = self._run(runtime_cli.main, ["--runtime", "claude"])
        self.assertEqual(2, code)
        self.assertIn("installed-project dogfood supports only the codex runtime", err)


class CodexEntrypointOutsideCheckoutTest(_OutsideCheckoutTestCase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(
            codex_cli, "repository_root", side_effect=_NOT_A_CHECKOUT
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_help_has_no_traceback_and_exits_zero(self):
        code, out, err = self._run(codex_cli.main, ["--help"])
        self.assertEqual(0, code)
        self.assertIn("usage: brichan-codex", out)
        self.assertEqual("", err)

    def test_version_has_no_traceback_and_exits_zero(self):
        code, out, err = self._run(codex_cli.main, ["--version"])
        self.assertEqual(0, code)
        self.assertEqual(f"brichan-codex {__version__}\n", out)
        self.assertEqual("", err)

    def test_unsupported_invocation_is_an_owned_error_not_a_traceback(self):
        code, out, err = self._run(codex_cli.main, ["do something"])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("brichan-codex:", err)
        self.assertNotIn("Traceback", err)


class ClaudeEntrypointOutsideCheckoutTest(_OutsideCheckoutTestCase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(
            claude_cli, "repository_root", side_effect=_NOT_A_CHECKOUT
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_help_has_no_traceback_and_exits_zero(self):
        code, out, err = self._run(claude_cli.main, ["--help"])
        self.assertEqual(0, code)
        self.assertIn("usage: brichan-claude", out)
        self.assertIn("checkout-oriented", out)
        self.assertEqual("", err)

    def test_version_has_no_traceback_and_exits_zero(self):
        code, out, err = self._run(claude_cli.main, ["--version"])
        self.assertEqual(0, code)
        self.assertEqual(f"brichan-claude {__version__}\n", out)
        self.assertEqual("", err)

    def test_unsupported_invocation_is_an_owned_error_not_a_traceback(self):
        code, out, err = self._run(claude_cli.main, ["do something"])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("brichan-claude:", err)
        self.assertNotIn("Traceback", err)


class OpencodeEntrypointOutsideCheckoutTest(_OutsideCheckoutTestCase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(
            opencode_cli, "repository_root", side_effect=_NOT_A_CHECKOUT
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_help_has_no_traceback_and_exits_zero(self):
        code, out, err = self._run(opencode_cli.main, ["--help"])
        self.assertEqual(0, code)
        self.assertIn("usage: brichan-opencode", out)
        self.assertIn("checkout-oriented", out)
        self.assertEqual("", err)

    def test_version_has_no_traceback_and_exits_zero(self):
        code, out, err = self._run(opencode_cli.main, ["--version"])
        self.assertEqual(0, code)
        self.assertEqual(f"brichan-opencode {__version__}\n", out)
        self.assertEqual("", err)

    def test_unsupported_invocation_is_an_owned_error_not_a_traceback(self):
        code, out, err = self._run(opencode_cli.main, ["do something"])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("brichan-opencode:", err)
        self.assertNotIn("Traceback", err)


class RuntimeDispatchTest(unittest.TestCase):
    """--runtime opencode reaches one guarded adapter, and only in a checkout."""

    def test_select_runtime_accepts_all_three_runtimes(self):
        for source in (
            (["--runtime", "opencode"], {}),
            (["--runtime=opencode"], {}),
            ([], {"BRICHAN_RUNTIME": "opencode"}),
        ):
            argv, environment = source
            with self.subTest(argv=argv, environment=environment):
                runtime, remaining = runtime_cli.select_runtime(
                    argv, environment, "codex"
                )
                self.assertEqual("opencode", runtime)
                self.assertEqual([], remaining)

    def test_an_unsupported_runtime_still_names_the_three_it_knows(self):
        with self.assertRaisesRegex(ValueError, "codex, claude, or opencode"):
            runtime_cli.select_runtime(["--runtime", "gemini"], {}, "codex")


class ExecRuntimeTest(unittest.TestCase):
    """A missing provider binary is an ordinary condition, not a crash.

    CI installs no providers, and plain machines often have neither codex nor
    claude, so the handoff has to fail like a CLI rather than like Python.
    """

    def _run(self, program):
        err = io.StringIO()
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = exec_runtime(program, [program, "--help"], owner="brichan-codex")
        return code, out.getvalue(), err.getvalue()

    def test_missing_binary_is_an_owned_error_not_a_traceback(self):
        code, out, err = self._run("brichan-no-such-runtime-binary")
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("brichan-codex:", err)
        self.assertIn("not installed or not on PATH", err)
        self.assertNotIn("Traceback", err)

    def test_missing_absolute_path_is_handled_the_same_way(self):
        code, _out, err = self._run("/nonexistent/bin/brichan-claude")
        self.assertEqual(2, code)
        self.assertNotIn("Traceback", err)

    def test_other_os_errors_are_owned_too(self):
        """A present-but-unexecutable target must not surface as a traceback."""
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "not-executable"
            target.write_text("#!/bin/sh\n", encoding="utf-8")
            code, _out, err = self._run(str(target))
        self.assertEqual(2, code)
        self.assertIn("brichan-codex:", err)
        self.assertNotIn("Traceback", err)

    def test_successful_exec_replaces_the_process(self):
        with mock.patch.object(os, "execvp") as execvp:
            code = exec_runtime("codex", ["codex", "--help"], owner="brichan")
        execvp.assert_called_once_with("codex", ["codex", "--help"])
        self.assertEqual(0, code)


if __name__ == "__main__":
    unittest.main()
