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

from brida import __version__
from brida.cli import claude as claude_cli
from brida.cli import codex as codex_cli
from brida.cli import runtime as runtime_cli
from brida.lifecycle import initialize_project
from brida.project import project_paths


_NOT_A_CHECKOUT = RuntimeError(
    "cannot locate the Brida repository root; run inside the repository "
    "or set BRIDA_ROOT"
)


class _OutsideCheckoutTestCase(unittest.TestCase):
    """Runs each test with cwd in a directory that is neither a Git
    repository nor the Brida checkout, and without BRIDA_ROOT set.

    ``repository_root`` is also patched to fail the way it does when the
    package is installed outside any checkout (e.g. into site-packages):
    unit tests otherwise run with this repository's own ``src/`` on
    ``sys.path``, so the real fallback in ``_root.repository_root`` would
    find this checkout's ``AGENTS.md`` and mask the installed-elsewhere
    behavior under test — and, for brida-claude/brida-codex, would exec the
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
        self.previous_root = os.environ.pop("BRIDA_ROOT", None)
        self.addCleanup(self._restore_root)

    def _restore_root(self):
        if self.previous_root is not None:
            os.environ["BRIDA_ROOT"] = self.previous_root

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
        self.assertIn("usage: brida", out)
        self.assertEqual("", err)

    def test_short_help_flag_works_before_initialization(self):
        code, out, _ = self._run(runtime_cli.main, ["-h"])
        self.assertEqual(0, code)
        self.assertIn("usage: brida", out)

    def test_version_works_before_initialization(self):
        code, out, err = self._run(runtime_cli.main, ["--version"])
        self.assertEqual(0, code)
        self.assertEqual(f"brida {__version__}\n", out)
        self.assertEqual("", err)

    def test_other_arguments_still_report_owned_uninitialized_error(self):
        code, out, err = self._run(runtime_cli.main, ["do something"])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("brida:", err)

    def test_help_works_inside_a_git_repo_that_is_not_yet_initialized(self):
        # A Git repository without a .brida directory takes a different
        # internal path (RoutingError via inspect_project) than a directory
        # that is not a Git repository at all (ProjectError); both must
        # short-circuit --help/--version before touching that error.
        target = self.outside / "uninitialized-project"
        target.mkdir()
        (target / ".git").mkdir()
        os.chdir(target)
        code, out, err = self._run(runtime_cli.main, ["--help"])
        self.assertEqual(0, code)
        self.assertIn("usage: brida", out)
        self.assertEqual("", err)

    def test_version_works_inside_a_git_repo_that_is_not_yet_initialized(self):
        target = self.outside / "uninitialized-project"
        target.mkdir()
        (target / ".git").mkdir()
        os.chdir(target)
        code, out, err = self._run(runtime_cli.main, ["--version"])
        self.assertEqual(0, code)
        self.assertEqual(f"brida {__version__}\n", out)
        self.assertEqual("", err)

    def test_other_arguments_inside_uninitialized_git_repo_still_error(self):
        target = self.outside / "uninitialized-project"
        target.mkdir()
        (target / ".git").mkdir()
        os.chdir(target)
        code, out, err = self._run(runtime_cli.main, ["do something"])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("brida: project state is uninitialized", err)

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
        # uninitialized branch (which would name "brida init").
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
        self.assertIn("usage: brida-codex", out)
        self.assertEqual("", err)

    def test_version_has_no_traceback_and_exits_zero(self):
        code, out, err = self._run(codex_cli.main, ["--version"])
        self.assertEqual(0, code)
        self.assertEqual(f"brida-codex {__version__}\n", out)
        self.assertEqual("", err)

    def test_unsupported_invocation_is_an_owned_error_not_a_traceback(self):
        code, out, err = self._run(codex_cli.main, ["do something"])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("brida-codex:", err)
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
        self.assertIn("usage: brida-claude", out)
        self.assertIn("checkout-oriented", out)
        self.assertEqual("", err)

    def test_version_has_no_traceback_and_exits_zero(self):
        code, out, err = self._run(claude_cli.main, ["--version"])
        self.assertEqual(0, code)
        self.assertEqual(f"brida-claude {__version__}\n", out)
        self.assertEqual("", err)

    def test_unsupported_invocation_is_an_owned_error_not_a_traceback(self):
        code, out, err = self._run(claude_cli.main, ["do something"])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("brida-claude:", err)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
