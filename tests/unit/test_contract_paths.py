"""The Level 0 contract-path decision is a command, not a judgment."""

import contextlib
import io
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.contracts.task_dossier.contract_paths import (
    contract_path_matches,
    is_contract_path,
    main,
)


def run(text=None, data=None, argv=()):
    stdout, stderr = io.StringIO(), io.StringIO()
    stream = io.BytesIO(text.encode("utf-8") if data is None else data)
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(list(argv), stream)
    return code, stdout.getvalue(), stderr.getvalue()


class ContractPathClassificationTest(unittest.TestCase):
    def test_contract_paths_match_and_other_paths_do_not(self):
        for path, expected in (
            ("docs/policy/x.md", True),
            ("docs/workflows/task-dossier.md", True),
            (".agents/skills/herdr-orchestration/SKILL.md", True),
            ("bin/brichan", True),
            ("src/brichan/project.py", True),
            ("scripts/validate_task_dossiers.py", True),
            ("config/model-routing.json", True),
            ("packaging/pypi-readme.md", True),
            ("techstacks/general.md", True),
            ("Makefile", True),
            ("pyproject.toml", True),
            ("PRODUCT.md", True),
            ("tests/unit/x.py", False),
            ("docs/index.md", False),
            ("README.md", False),
            ("CHANGELOG.md", False),
            ("docs/Makefile", False),
            ("src/brichanx/x.py", False),
            ('"docs/policy/caf\\303\\251.md"', True),
        ):
            with self.subTest(path=path):
                self.assertEqual(expected, is_contract_path(path))

    def test_both_sides_of_a_rename_are_honored(self):
        # --no-renames prints a rename as a delete and an add, so moving a
        # contract file out of a contract directory still matches.
        names = ["docs/policy/old.md", "notes/new.md"]
        self.assertEqual(["docs/policy/old.md"], contract_path_matches(names))
        names = ["notes/old.md", "scripts/new.py"]
        self.assertEqual(["scripts/new.py"], contract_path_matches(names))


class ContractPathCommandTest(unittest.TestCase):
    def test_no_contract_path_exits_zero(self):
        code, stdout, _ = run("tests/unit/x.py\nREADME.md\n")
        self.assertEqual(0, code)
        self.assertEqual("contract-path: no\n", stdout)

    def test_a_contract_path_exits_three_and_names_every_match(self):
        code, stdout, _ = run("tests/unit/x.py\ndocs/policy/x.md\r\nbin/brichan\n")
        self.assertEqual(3, code)
        self.assertEqual(
            "contract-path: yes\ndocs/policy/x.md\nbin/brichan\n", stdout
        )

    def test_undecodable_input_fails_closed(self):
        code, stdout, stderr = run(data=b"docs/policy/\xff.md\n")
        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertIn("not UTF-8", stderr)

    def test_empty_or_blank_input_is_refused_not_answered_no(self):
        # A failed upstream git diff prints nothing; silence is not evidence.
        for text in ("", "\n", "  \n\t\r\n"):
            with self.subTest(text=text):
                code, stdout, stderr = run(text)
                self.assertEqual(2, code)
                self.assertEqual("", stdout)
                self.assertIn("no path names on input; refusing to decide", stderr)

    def test_the_wrapper_refuses_empty_input(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_contract_paths.py")],
            input="",
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("refusing to decide", result.stderr)

    def test_an_invalid_invocation_exits_two(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                run("", argv=["--unknown"])
        self.assertEqual(2, caught.exception.code)

    def test_the_wrapper_runs_the_checker_from_stdin(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_contract_paths.py")],
            input="src/brichan/lifecycle.py\n",
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(3, result.returncode, result.stderr)
        self.assertEqual(
            "contract-path: yes\nsrc/brichan/lifecycle.py\n", result.stdout
        )


if __name__ == "__main__":
    unittest.main()
