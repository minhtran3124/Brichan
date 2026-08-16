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
from brichan.cli._root import checkout_root, exec_runtime
from brichan.cli import claude as claude_cli
from brichan.cli import codex as codex_cli
from brichan.cli import runtime as runtime_cli
from brichan.lifecycle import initialize_project
from brichan.project import project_paths


_NOT_A_CHECKOUT = RuntimeError(
    "cannot locate the Brichan repository root; run inside the repository "
    "or set BRICHAN_ROOT"
)


class CheckoutRootTest(unittest.TestCase):
    """DOGFOOD-007 M1: a malformed root is an owned error, never a traceback.

    `checkout_root` normalizes a wrapper-supplied path and is deliberately
    strict; each `checkout_main` converts its failures into exit code 2.
    """

    def test_a_relative_claim_is_normalized(self):
        self.assertEqual(ROOT.resolve(), checkout_root(str(ROOT / "tests" / "..")))

    def test_a_symlinked_checkout_is_accepted(self):
        # Editable and symlinked checkouts are legitimate; only the launch
        # decides mode, so following the link here is safe.
        with tempfile.TemporaryDirectory() as temporary:
            link = Path(temporary) / "checkout"
            link.symlink_to(ROOT)
            self.assertEqual(ROOT.resolve(), checkout_root(link))

    def test_missing_and_looping_claims_raise_owned_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(OSError):
                checkout_root(root / "absent")
            loop = root / "loop"
            loop.symlink_to(loop)
            with self.assertRaises((OSError, RuntimeError)):
                checkout_root(loop)

    def test_every_checkout_main_reports_a_bad_root_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as temporary:
            absent = str(Path(temporary) / "absent")
            for main, owner in (
                (runtime_cli.checkout_main, "brichan:"),
                (codex_cli.checkout_main, "brichan-codex:"),
                (claude_cli.checkout_main, "brichan-claude:"),
            ):
                out = io.StringIO()
                err = io.StringIO()
                with (
                    contextlib.redirect_stdout(out),
                    contextlib.redirect_stderr(err),
                ):
                    code = main(absent, ["--version"])
                self.assertEqual(2, code, owner)
                self.assertIn(owner, err.getvalue())
                self.assertNotIn("Traceback", err.getvalue())


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


class ForgedCheckoutClaimTest(_OutsideCheckoutTestCase):
    """DOGFOOD-007 H1: no target shape can switch an installed command.

    The original defect let a claimed root whose `src/brichan` symlinked to the
    imported package prove "checkout", which selected the unguarded checkout
    `codex_command()` instead of the managed `codex_project_command()`. Mode is
    now decided by the invoked entrypoint, so the forged claim must be inert.
    """

    def _forged_root(self, wrapper):
        root = self.outside / f"forged-{wrapper}"
        (root / "bin").mkdir(parents=True)
        (root / "bin" / wrapper).write_text("#!/bin/sh\n", encoding="utf-8")
        (root / "src").mkdir()
        # The exact reproduction from the review: point the claimed source
        # package at the package this process actually imported.
        (root / "src" / "brichan").symlink_to(Path(codex_cli.__file__).parents[1])
        os.environ["BRICHAN_ROOT"] = str(root)
        return root

    def test_forged_claim_cannot_give_installed_codex_checkout_dispatch(self):
        self._forged_root("brichan-codex")
        with (
            mock.patch.object(codex_cli, "run_project") as run_project,
            mock.patch.object(codex_cli, "codex_command") as codex_command,
        ):
            code, out, err = self._run(codex_cli.main, ["do something"])
        run_project.assert_not_called()
        codex_command.assert_not_called()
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("brichan-codex:", err)
        self.assertNotIn("Traceback", err)

    def test_forged_claim_cannot_give_installed_brichan_checkout_dispatch(self):
        root = self._forged_root("brichan")
        with mock.patch.object(runtime_cli, "exec_runtime") as exec_wrapper:
            code, _, err = self._run(runtime_cli.main, ["do something"])
        # Checkout dispatch would have exec'd the claimed root's wrapper.
        exec_wrapper.assert_not_called()
        self.assertEqual(2, code)
        self.assertNotIn(str(root), err)

    def test_forged_claim_cannot_give_installed_claude_checkout_dispatch(self):
        self._forged_root("brichan-claude")
        with mock.patch.object(claude_cli, "claude_command") as claude_command:
            code, _, err = self._run(claude_cli.main, ["do something"])
        claude_command.assert_not_called()
        self.assertEqual(2, code)
        self.assertIn("brichan-claude:", err)

    def test_a_malformed_claim_is_ignored_rather_than_raised(self):
        # DOGFOOD-007 M1 reproduction: the self-referential source-package
        # symlink that previously escaped as a RuntimeError traceback.
        root = self.outside / "malformed"
        (root / "bin").mkdir(parents=True)
        (root / "bin" / "brichan-codex").write_text("", encoding="utf-8")
        (root / "src").mkdir()
        (root / "src" / "brichan").symlink_to(root / "src" / "brichan")
        os.environ["BRICHAN_ROOT"] = str(root)
        code, out, err = self._run(codex_cli.main, ["--version"])
        self.assertEqual(0, code)
        self.assertEqual(f"brichan-codex {__version__}\n", out)
        self.assertEqual("", err)


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
