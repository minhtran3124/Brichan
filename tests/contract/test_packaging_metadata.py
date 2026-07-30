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

    def test_packaged_description_is_the_generated_one(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('readme = "README_PYPI.md"', pyproject)

    def test_generated_description_is_in_sync_with_the_readme(self):
        """A stale committed description would re-ship the broken image."""
        sys.path.insert(0, str(ROOT / "scripts"))
        import build_pypi_readme

        committed = (ROOT / "README_PYPI.md").read_text(encoding="utf-8")
        self.assertEqual(
            committed,
            build_pypi_readme.expected(),
            "README_PYPI.md is stale; run `make readme-check`",
        )


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
        for name in ("pyproject.toml", "README.md", "README_PYPI.md", "LICENSE"):
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

    def _pkg_info(self):
        with tarfile.open(self.sdist) as archive:
            name = next(
                item
                for item in archive.getnames()
                if item.count("/") == 1 and item.endswith("PKG-INFO")
            )
            handle = archive.extractfile(name)
            self.assertIsNotNone(handle, name)
            return handle.read().decode("utf-8")

    def test_published_description_carries_no_repository_relative_target(self):
        """The 0.5.0 page shipped `assets/brida-hero.png` and rendered broken.

        PyPI resolves relative targets against pypi.org, so any that survive
        into PKG-INFO are a broken image or a dead link on the project page.
        """
        pkg_info = self._pkg_info()
        self.assertIn("Brichan", pkg_info)
        self.assertNotIn("(assets/", pkg_info)
        self.assertNotIn("(docs/", pkg_info)
        self.assertNotIn("(CONTRIBUTING.md)", pkg_info)
        self.assertNotIn("(LICENSE)", pkg_info)

    def test_published_description_keeps_the_pypi_prose(self):
        """Stripping targets must not cost the description its content."""
        pkg_info = self._pkg_info()
        self.assertIn("AI Chief of Staff", pkg_info)
        self.assertIn("pip install brichan", pkg_info)
        for heading in ("## Installation", "## Usage", "## Contributing"):
            self.assertIn(heading, pkg_info, heading)

    def test_published_description_states_the_package_is_installable(self):
        """README.md still says Brida is unpublished; the PyPI page must not."""
        pkg_info = self._pkg_info()
        self.assertNotIn("not published to a package registry", pkg_info)


if __name__ == "__main__":
    unittest.main()
