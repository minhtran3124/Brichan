"""Focused behavior tests for the read-only project-memory consistency gate."""

from __future__ import annotations

import ast
import contextlib
import io
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import check_project_memory as checker


VERSION = "1.2.3"
RELEASE_DATE = "2026-08-03"
VERIFIED_DATE = "2026-08-09"


class ProjectMemoryCheckerTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self._build_valid_tree()

    def _write(self, relative: str, text: str) -> None:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def _product(
        self,
        *,
        package_version: str = VERSION,
        published_version: str = VERSION,
        verified: str = VERIFIED_DATE,
        extra: str = "",
    ) -> str:
        return (
            "# Product\n\n"
            f"Last verified: {verified} (package version {package_version}).\n\n"
            f"Latest published version: {published_version}\n"
            f"{extra}"
        )

    def _index(self, entries: list[tuple[str, str, str]]) -> str:
        rendered = ["# Project index", ""]
        for title, status_line, memory_line in entries:
            rendered.extend(
                (
                    f"## {title}",
                    status_line,
                    "- Summary: fixture",
                    memory_line,
                    "",
                )
            )
        rendered.extend(
            (
                "## Entry template",
                "",
                "```text",
                "## <project-name>",
                "- Status: proposed | active | blocked | paused | complete | archived",
                "- Memory: projects/<slug>/",
                "```",
                "",
            )
        )
        return "\n".join(rendered)

    def _build_valid_tree(self) -> None:
        self._write("VERSION", f"{VERSION}\n")
        self._write(
            "CHANGELOG.md",
            f"# Changelog\n\n## [{VERSION}] - {RELEASE_DATE}\n",
        )
        for relative in checker.ACTIVE_PRODUCT_DOCUMENTS:
            self._write(relative, f"# {relative}\n")
        self._write("PRODUCT.md", self._product())
        self._write(
            "projects/index.md",
            self._index(
                [("Demo", "- Status: active", "- Memory: projects/demo/")]
            ),
        )
        for name in checker.REQUIRED_MEMORY_FILES:
            content = "- Lifecycle status: active\n" if name == "overview.md" else ""
            self._write(f"projects/demo/{name}", content)

    def _diagnostics(self) -> list[checker.Diagnostic]:
        first = checker.collect(self.root)
        second = checker.collect(self.root)
        first_bytes = "\n".join(item.render() for item in first).encode("utf-8")
        second_bytes = "\n".join(item.render() for item in second).encode("utf-8")
        self.assertEqual(first_bytes, second_bytes)
        return first

    def _assert_checks(self, expected: list[tuple[str, str]]) -> None:
        actual = [(item.path, item.check) for item in self._diagnostics()]
        self.assertEqual(expected, actual)

    def test_valid_fixture_is_clean_and_main_exits_zero(self):
        self._assert_checks([])
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = checker.main(["--root", str(self.root)])
        self.assertEqual(0, result)
        self.assertEqual("", stderr.getvalue())
        self.assertEqual(
            "project memory consistent: 1 indexed projects, 8 active documents\n",
            stdout.getvalue(),
        )

    def test_missing_memory_files_are_an_exact_golden_fixture(self):
        for name in checker.REQUIRED_MEMORY_FILES:
            (self.root / "projects/demo" / name).unlink()
        expected = [
            (
                f"projects/demo/{name}",
                "memory-completeness",
                "required memory file is missing",
            )
            for name in (
                "current-state.md",
                "decisions.md",
                "overview.md",
                "references.md",
                "tasks.md",
            )
        ]
        actual = [
            (item.path, item.check, item.detail) for item in self._diagnostics()
        ]
        self.assertEqual(expected, actual)

    def test_unsafe_index_paths_are_an_exact_golden_fixture(self):
        link = self.root / "projects/link"
        link.symlink_to("missing-target", target_is_directory=True)
        self._write(
            "projects/index.md",
            self._index(
                [
                    ("Absolute", "- Status: active", "- Memory: /tmp/absolute/"),
                    (
                        "Traversal",
                        "- Status: active",
                        "- Memory: projects/../escape/",
                    ),
                    (
                        "Malformed",
                        "- Status: active",
                        "- Memory: projects/Bad_Name/",
                    ),
                    ("Symlinked", "- Status: active", "- Memory: projects/link/"),
                ]
            ),
        )
        expected = sorted(
            [
                (
                    "projects/index.md",
                    "index-path",
                    "'Absolute' declares memory path '/tmp/absolute/', which is not `projects/<slug>/`",
                ),
                (
                    "projects/index.md",
                    "index-path",
                    "'Traversal' declares memory path 'projects/../escape/', which is not `projects/<slug>/`",
                ),
                (
                    "projects/index.md",
                    "index-path",
                    "'Malformed' declares memory path 'projects/Bad_Name/', which is not `projects/<slug>/`",
                ),
                (
                    "projects/index.md",
                    "index-path",
                    "'Symlinked' memory directory projects/link is a symlink (symlink at projects/link)",
                ),
            ]
        )
        actual = [
            (item.path, item.check, item.detail) for item in self._diagnostics()
        ]
        self.assertEqual(expected, actual)

    def test_combined_drift_is_an_exact_golden_fixture(self):
        self._write(
            "PRODUCT.md",
            self._product(
                package_version="1.2.2",
                verified="2026-08-02",
                extra="Install brichan-1.2.3-py3-none-any.whl here.\n",
            ),
        )
        self._write("projects/demo/overview.md", "- Lifecycle status: complete\n")
        self._write(
            "projects/index.md",
            self._index(
                [
                    ("Demo", "- Status: active", "- Memory: projects/demo/"),
                    (
                        "Traversal",
                        "- Status: active",
                        "- Memory: projects/../escape/",
                    ),
                ]
            ),
        )
        expected = [
            (
                "PRODUCT.md",
                "date-claim",
                "`Last verified:` 2026-08-02 predates the matching release date 2026-08-03",
            ),
            (
                "PRODUCT.md",
                "version-claim",
                "claims package version 1.2.2, VERSION is 1.2.3",
            ),
            (
                "PRODUCT.md",
                "wheel-version",
                "embeds the version-specific wheel filename brichan-1.2.3-py3-none-any.whl; derive it from VERSION",
            ),
            (
                "projects/demo/overview.md",
                "lifecycle-agreement",
                "declares lifecycle status 'complete' while projects/index.md declares 'active'",
            ),
            (
                "projects/index.md",
                "index-path",
                "'Traversal' declares memory path 'projects/../escape/', which is not `projects/<slug>/`",
            ),
        ]
        actual = [
            (item.path, item.check, item.detail) for item in self._diagnostics()
        ]
        self.assertEqual(expected, actual)

    def test_version_and_date_drift_are_reported(self):
        self._write(
            "PRODUCT.md",
            self._product(
                package_version="1.2.2",
                published_version="1.2.1",
                verified="2026-08-02",
            ),
        )
        self._assert_checks(
            [
                ("PRODUCT.md", "date-claim"),
                ("PRODUCT.md", "version-claim"),
                ("PRODUCT.md", "version-claim"),
            ]
        )

    def test_invalid_product_verification_date_is_reported(self):
        self._write("PRODUCT.md", self._product(verified="2026-02-30"))
        self._assert_checks([("PRODUCT.md", "date-claim")])

    def test_one_missing_required_memory_file_is_reported(self):
        (self.root / "projects/demo/tasks.md").unlink()
        self._assert_checks(
            [("projects/demo/tasks.md", "memory-completeness")]
        )

    def test_overview_lifecycle_failures_are_reported(self):
        cases = (
            "# no lifecycle\n",
            "- Lifecycle status: active\n- Lifecycle status: complete\n",
            "- Lifecycle status active\n",
            "- Lifecycle status: \n",
            "- Lifecycle status: unknown\n",
        )
        for content in cases:
            with self.subTest(content=content):
                self._write("projects/demo/overview.md", content)
                self._assert_checks(
                    [("projects/demo/overview.md", "overview-lifecycle")]
                )

    def test_index_status_failures_are_reported(self):
        for status_line in ("- Status active", "- Status: unknown"):
            with self.subTest(status_line=status_line):
                self._write(
                    "projects/index.md",
                    self._index(
                        [("Demo", status_line, "- Memory: projects/demo/")]
                    ),
                )
                self._assert_checks([("projects/index.md", "index-status")])

    def test_lifecycle_disagreement_is_reported(self):
        self._write("projects/demo/overview.md", "- Lifecycle status: complete\n")
        self._assert_checks(
            [("projects/demo/overview.md", "lifecycle-agreement")]
        )

    def test_missing_and_non_directory_index_targets_are_reported(self):
        cases = ("missing", "not-directory")
        for slug in cases:
            with self.subTest(slug=slug):
                if slug == "not-directory":
                    self._write("projects/not-directory", "not a directory\n")
                self._write(
                    "projects/index.md",
                    self._index(
                        [
                            (
                                "Broken",
                                "- Status: active",
                                f"- Memory: projects/{slug}/",
                            )
                        ]
                    ),
                )
                self._assert_checks([("projects/index.md", "index-path")])

    def test_wheel_literals_are_reported_even_when_version_matches(self):
        self._write(
            "README.md",
            "brichan-1.2.3-py3-none-any.whl\n"
            "brichan-9.8.7-py3-none-any.whl\n",
        )
        self._assert_checks(
            [
                ("README.md", "wheel-version"),
                ("README.md", "wheel-version"),
            ]
        )

    def test_version_derived_wheel_flow_has_no_literal(self):
        command = (
            'BRICHAN_SRC=/absolute/path/to/brichan\n'
            '"/tmp/brichan-wheel/brichan-$(cat "$BRICHAN_SRC/VERSION")-'
            'py3-none-any.whl"\n'
        )
        self._write("docs/guides/installable-dogfood.md", command)

        substitution = re.search(
            r'\$\(cat "\$BRICHAN_SRC/(?P<relative>[^\"]+)"\)', command
        )
        self.assertIsNotNone(substitution)
        assert substitution is not None
        self.assertEqual("VERSION", substitution.group("relative"))
        resolved_version = (
            self.root / substitution.group("relative")
        ).read_text(encoding="utf-8").strip()
        resolved_command = command.replace(substitution.group(0), resolved_version)
        resolved_wheel = re.search(
            r"(?P<filename>brichan-[^/\s\"]+\.whl)", resolved_command
        )
        self.assertIsNotNone(resolved_wheel)
        assert resolved_wheel is not None
        self.assertEqual(
            f"brichan-{VERSION}-py3-none-any.whl",
            resolved_wheel.group("filename"),
        )
        self._assert_checks([])

    def test_missing_invalid_and_older_only_matching_release_states(self):
        cases = (
            "# Changelog\n",
            f"# Changelog\n\n## [{VERSION}] - 2026-02-30\n",
            "# Changelog\n\n## [1.2.2] - 2026-08-03\n",
        )
        for changelog in cases:
            with self.subTest(changelog=changelog):
                self._write("CHANGELOG.md", changelog)
                self._assert_checks([("CHANGELOG.md", "changelog-release")])

    def test_invalid_version_does_not_suppress_missing_changelog_input(self):
        self._write("VERSION", "not-a-version\n")
        (self.root / "CHANGELOG.md").unlink()
        self._assert_checks(
            [
                ("CHANGELOG.md", "input"),
                ("VERSION", "input"),
            ]
        )

    def test_unknown_errno_read_failure_is_stable_and_has_no_traceback(self):
        original = Path.read_text
        failing = self.root / "README.md"

        def read_text(path: Path, *args, **kwargs):
            if path == failing:
                raise OSError(9876, "fixture error")
            return original(path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", read_text):
            diagnostics = self._diagnostics()
        self.assertEqual(
            [("README.md", "input")],
            [(item.path, item.check) for item in diagnostics],
        )
        self.assertIn("errno-9876", diagnostics[0].detail)
        self.assertNotIn("Traceback", diagnostics[0].render())

    def test_failure_exit_is_one_with_sorted_stderr(self):
        self._write("PRODUCT.md", self._product(package_version="1.2.2"))

        def invoke() -> tuple[int, bytes, bytes]:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = checker.main([f"--root={self.root}"])
            return (
                result,
                stdout.getvalue().encode("utf-8"),
                stderr.getvalue().encode("utf-8"),
            )

        first = invoke()
        second = invoke()
        self.assertEqual(first, second)
        result, stdout, stderr = first
        self.assertEqual(1, result)
        self.assertEqual(b"", stdout)
        lines = stderr.decode("utf-8").splitlines()
        self.assertEqual(1, len(lines))
        path, check, detail = lines[0].split(": ", 2)
        self.assertEqual(
            ("PRODUCT.md", "version-claim"),
            (path, check),
        )
        self.assertTrue(detail)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(1, checker.main(["--unknown"]))

    def test_checker_has_no_write_or_subprocess_side_effects(self):
        source = Path(checker.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported.update(
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        self.assertNotIn("subprocess", imported)

        mutating_methods = {
            "chmod",
            "hardlink_to",
            "mkdir",
            "rename",
            "replace",
            "rmdir",
            "symlink_to",
            "touch",
            "unlink",
            "write_bytes",
            "write_text",
        }
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue(mutating_methods.isdisjoint(calls))

        patched = {
            name: mock.patch.object(subprocess, name, side_effect=AssertionError(name))
            for name in ("Popen", "call", "check_call", "check_output", "run")
        }
        with contextlib.ExitStack() as stack:
            for patcher in patched.values():
                stack.enter_context(patcher)
            self._assert_checks([])


if __name__ == "__main__":
    unittest.main()
