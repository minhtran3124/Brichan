import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class PackagingMetadataTest(unittest.TestCase):
    def test_pyproject_declares_brichan_distribution_and_wheel_build_requirement(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('name = "brichan"', pyproject)
        self.assertIn("wheel", pyproject.split("requires = ", 1)[1].splitlines()[0])

    def test_console_scripts_are_unchanged(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        for entry_point in (
            'brida = "brida.cli.runtime:main"',
            'brida-codex = "brida.cli.codex:main"',
            'brida-claude = "brida.cli.claude:main"',
            'brida-herdr-agent-start = "brida.orchestration.worker_launch:main"',
            'brida-validate-receipts = "brida.contracts.receipts.validation:main"',
        ):
            self.assertIn(entry_point, pyproject)

    def test_import_package_remains_brida(self):
        self.assertTrue((ROOT / "src/brida/__init__.py").is_file())
        self.assertFalse((ROOT / "src/brichan").exists())


class SdistBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidates = (
            sys.executable,
            *(shutil.which(name) for name in ("python3.13", "python3.12", "python3.11")),
        )
        build_python = None
        for candidate in candidates:
            if candidate is None:
                continue
            result = subprocess.run(
                [candidate, "-c", "import setuptools"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                build_python = candidate
                break
        if build_python is None:
            raise unittest.SkipTest("no offline Python setuptools backend is installed")

        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.source_root = Path(cls.temporary.name) / "source"
        cls.source_root.mkdir()
        for name in ("pyproject.toml", "README.md", "LICENSE"):
            shutil.copy2(ROOT / name, cls.source_root / name)
        shutil.copytree(ROOT / "src", cls.source_root / "src")
        cls.sdist_dir = Path(cls.temporary.name) / "sdist"
        cls.sdist_dir.mkdir()

        # Build directly through the setuptools.build_meta backend so this
        # test only depends on setuptools, not the separate "build" frontend
        # package used by CI and the release checklist.
        result = subprocess.run(
            [
                build_python,
                "-c",
                "from setuptools import build_meta as backend\n"
                f"backend.build_sdist({str(cls.sdist_dir)!r})\n",
            ],
            cwd=cls.source_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AssertionError(f"sdist build failed:\n{result.stdout}\n{result.stderr}")
        archives = list(cls.sdist_dir.glob("*.tar.gz"))
        if len(archives) != 1:
            raise AssertionError(f"expected one sdist, found: {archives}")
        cls.sdist = archives[0]

    def test_sdist_is_named_brichan_and_contains_the_brida_package(self):
        self.assertTrue(self.sdist.name.startswith("brichan-"), self.sdist.name)
        with tarfile.open(self.sdist) as archive:
            names = archive.getnames()
        self.assertTrue(any(name.endswith("src/brida/__init__.py") for name in names))
        self.assertTrue(
            any(name.endswith("PKG-INFO") for name in names), "sdist has no PKG-INFO"
        )


if __name__ == "__main__":
    unittest.main()
