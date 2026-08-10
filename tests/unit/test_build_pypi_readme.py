import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_pypi_readme  # noqa: E402  (needs the path entry above)


PRIVATE = {
    "schema_version": 1,
    "source": "README.md",
    "output": "README_PYPI.md",
    "public_repository": False,
    "asset_base_url": "https://raw.githubusercontent.com/o/r/main",
    "link_base_url": "https://github.com/o/r/blob/main",
}
PUBLIC = {**PRIVATE, "public_repository": True}


class RelativeTargetTest(unittest.TestCase):
    def test_repository_relative_targets_are_detected(self):
        for target in ("assets/hero.png", "./docs/a.md", "/LICENSE", "a b.md"):
            self.assertTrue(
                build_pypi_readme.is_relative_target(target), target
            )

    def test_absolute_and_anchor_targets_are_left_alone(self):
        for target in (
            "https://example.com/a.png",
            "http://example.com",
            "mailto:a@example.com",
            "#section",
        ):
            self.assertFalse(
                build_pypi_readme.is_relative_target(target), target
            )


class PrivateRepositoryRenderTest(unittest.TestCase):
    """While the repository is private the absolute URLs would 404."""

    def test_relative_image_is_dropped_rather_than_left_broken(self):
        rendered = build_pypi_readme.render("![hero](assets/hero.png)\n", PRIVATE)
        self.assertNotIn("assets/hero.png", rendered)
        self.assertNotIn("![hero]", rendered)

    def test_relative_link_degrades_to_its_text(self):
        rendered = build_pypi_readme.render("see [guide](docs/g.md) now\n", PRIVATE)
        self.assertEqual(rendered.strip(), "see guide now")

    def test_absolute_targets_are_preserved(self):
        source = "![x](https://e.com/x.png) and [y](https://e.com)\n"
        self.assertEqual(build_pypi_readme.render(source, PRIVATE), source)

    def test_html_image_with_relative_src_is_dropped(self):
        rendered = build_pypi_readme.render('<img src="assets/h.png" alt="h">\n', PRIVATE)
        self.assertNotIn("assets/h.png", rendered)


class PublicRepositoryRenderTest(unittest.TestCase):
    """Flipping public_repository is the whole migration once the repo opens."""

    def test_relative_image_becomes_an_absolute_raw_url(self):
        rendered = build_pypi_readme.render("![hero](assets/hero.png)\n", PUBLIC)
        self.assertIn(
            "![hero](https://raw.githubusercontent.com/o/r/main/assets/hero.png)",
            rendered,
        )

    def test_relative_link_becomes_an_absolute_blob_url(self):
        rendered = build_pypi_readme.render("[g](docs/g.md)", PUBLIC)
        self.assertIn("[g](https://github.com/o/r/blob/main/docs/g.md)", rendered)

    def test_leading_dot_slash_is_not_doubled_into_the_url(self):
        rendered = build_pypi_readme.render("![h](./assets/h.png)", PUBLIC)
        self.assertIn("/main/assets/h.png)", rendered)
        self.assertNotIn("main/./assets", rendered)

    def test_root_relative_target_does_not_double_the_slash(self):
        """packaging/pypi-readme.md uses /assets/... so it resolves from ROOT."""
        rendered = build_pypi_readme.render("![h](/assets/h.png)", PUBLIC)
        self.assertIn("/main/assets/h.png)", rendered)
        self.assertNotIn("main//assets", rendered)


class ValidateTest(unittest.TestCase):
    def test_surviving_relative_target_is_reported(self):
        self.assertTrue(build_pypi_readme.validate("![a](assets/a.png)"))
        self.assertTrue(build_pypi_readme.validate('<img src="a/b.png">'))

    def test_clean_description_reports_nothing(self):
        self.assertEqual(build_pypi_readme.validate("![a](https://e.com/a.png)"), [])


class RepositoryReadmeTest(unittest.TestCase):
    def test_repository_readme_keeps_the_relative_hero_path(self):
        """README.md serves local preview and GitHub, which resolve it."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("](assets/brichan-hero.png)", readme)

    def test_hero_asset_exists_on_disk(self):
        self.assertTrue((ROOT / "assets/brichan-hero.png").is_file())

    def test_pypi_source_is_separate_from_the_repository_readme(self):
        config = build_pypi_readme.load_config()
        source = ROOT / config["source"]
        self.assertTrue(source.is_file(), config["source"])
        self.assertNotEqual(source, ROOT / "README.md")

    def test_rendering_the_real_pypi_source_leaves_no_relative_target(self):
        config = build_pypi_readme.load_config()
        source = (ROOT / config["source"]).read_text(encoding="utf-8")
        self.assertEqual(build_pypi_readme.validate(
            build_pypi_readme.render(source, config)
        ), [])

    def test_pypi_source_hero_resolves_when_the_repository_goes_public(self):
        """The one-line flip must produce a reachable raw URL, not a mangled one."""
        config = {**build_pypi_readme.load_config(), "public_repository": True}
        source = (ROOT / config["source"]).read_text(encoding="utf-8")
        rendered = build_pypi_readme.render(source, config)
        self.assertIn(
            f"{config['asset_base_url']}/assets/brichan-hero.png", rendered
        )


class ConfigTest(unittest.TestCase):
    def test_shipped_config_loads(self):
        config = build_pypi_readme.load_config()
        self.assertEqual(config["source"], "packaging/pypi-readme.md")

    def test_shipped_config_is_public_with_the_verified_base_urls(self):
        """PYPI-003: a silent revert to private mode must fail here, not ship."""
        config = build_pypi_readme.load_config()
        self.assertIs(config["public_repository"], True)
        self.assertEqual(
            config["asset_base_url"],
            "https://raw.githubusercontent.com/minhtran3124/Brichan/main",
        )
        self.assertEqual(
            config["link_base_url"],
            "https://github.com/minhtran3124/Brichan/blob/main",
        )

    def test_public_mode_requires_https_base_urls(self):
        broken = {**PUBLIC, "asset_base_url": "assets"}
        with self.assertRaises(build_pypi_readme.ReadmeConfigError):
            build_pypi_readme.load_config(_write_temp_config(self, broken))


def _write_temp_config(test, payload):
    import json
    import tempfile

    directory = tempfile.TemporaryDirectory()
    test.addCleanup(directory.cleanup)
    path = Path(directory.name) / "pypi-readme.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
