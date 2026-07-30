import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import release_pypi  # noqa: E402  (needs the path entry above)


TOKEN = "pypi-AgEAAAApretend0token0value"


def _write(directory: Path, text: str) -> Path:
    path = directory / ".env"
    path.write_text(text, encoding="utf-8")
    return path


class EnvFileTest(unittest.TestCase):
    def parse(self, text: str) -> dict:
        with tempfile.TemporaryDirectory() as temporary:
            return release_pypi.read_env_file(_write(Path(temporary), text))

    def test_plain_assignment(self):
        self.assertEqual({"PYPI_TOKEN": TOKEN}, self.parse(f"PYPI_TOKEN={TOKEN}\n"))

    def test_export_prefix_and_surrounding_space(self):
        self.assertEqual(
            {"PYPI_TOKEN": TOKEN}, self.parse(f"  export PYPI_TOKEN = {TOKEN}  \n")
        )

    def test_quotes_are_stripped(self):
        for quoted in (f'PYPI_TOKEN="{TOKEN}"', f"PYPI_TOKEN='{TOKEN}'"):
            self.assertEqual({"PYPI_TOKEN": TOKEN}, self.parse(quoted))

    def test_comments_and_blank_lines_are_ignored(self):
        self.assertEqual(
            {"PYPI_TOKEN": TOKEN},
            self.parse(f"# a comment\n\nPYPI_TOKEN={TOKEN}\n"),
        )

    def test_value_containing_equals_is_kept_whole(self):
        self.assertEqual({"K": "a=b=c"}, self.parse("K=a=b=c\n"))

    def test_missing_file_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual({}, release_pypi.read_env_file(Path(temporary) / ".env"))


class TokenTest(unittest.TestCase):
    """The token is a secret: it must never reach stdout, stderr, or argv."""

    def test_environment_variable_is_used(self):
        self.assertEqual(TOKEN, release_pypi.resolve_token({"PYPI_TOKEN": TOKEN}))

    def test_malformed_token_is_rejected_without_echoing_it(self):
        secret = "definitely-not-a-pypi-token"
        with self.assertRaises(release_pypi.ReleaseError) as caught:
            release_pypi.resolve_token({"PYPI_TOKEN": secret})
        self.assertNotIn(secret, str(caught.exception))

    def test_missing_token_is_reported_by_name_only(self):
        with mock.patch.object(release_pypi, "read_env_file", return_value={}):
            with self.assertRaises(release_pypi.ReleaseError) as caught:
                release_pypi.resolve_token({})
        self.assertIn("PYPI_TOKEN", str(caught.exception))

    def test_upload_passes_credentials_through_the_environment_not_argv(self):
        """argv is readable by any user on the machine via ps."""
        with mock.patch.object(release_pypi, "run") as run:
            release_pypi.upload([Path("dist/x.whl")], "pypi", TOKEN)
        command = run.call_args.args[0]
        self.assertNotIn(TOKEN, command)
        for argument in command:
            self.assertNotIn(TOKEN, argument)
        environment = run.call_args.kwargs["env"]
        self.assertEqual("__token__", environment["TWINE_USERNAME"])
        self.assertEqual(TOKEN, environment["TWINE_PASSWORD"])

    def test_upload_targets_the_requested_index(self):
        for repository, url in release_pypi.REPOSITORIES.items():
            with mock.patch.object(release_pypi, "run") as run:
                release_pypi.upload([Path("dist/x.whl")], repository, TOKEN)
            self.assertEqual(url, run.call_args.kwargs["env"]["TWINE_REPOSITORY_URL"])


class VersionSourceTest(unittest.TestCase):
    def test_every_declared_source_exists_and_parses(self):
        versions = release_pypi.current_versions()
        self.assertEqual(set(release_pypi.VERSION_SOURCES), set(versions))
        for name, value in versions.items():
            self.assertRegex(value, r"^\d+\.\d+\.\d+", name)

    def test_repository_versions_agree_right_now(self):
        """The checked-in tree must always be releasable as one version."""
        self.assertEqual(
            (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
            release_pypi.require_consistent_version(),
        )

    def test_accepted_and_rejected_version_strings(self):
        for good in ("0.6.0", "1.0.0", "0.6.0rc1", "1.2.3.post1"):
            self.assertTrue(release_pypi.SEMVER.match(good), good)
        for bad in ("", "1.0", "v1.0.0", "latest", "1.0.0 "):
            self.assertFalse(release_pypi.SEMVER.match(bad), repr(bad))


class GuardTest(unittest.TestCase):
    def test_publishing_an_existing_version_is_refused(self):
        with mock.patch.object(
            release_pypi, "released_versions", return_value={"0.5.0"}
        ):
            with self.assertRaises(release_pypi.ReleaseError) as caught:
                release_pypi.require_unpublished("0.5.0", "pypi")
        self.assertIn("already on pypi", str(caught.exception))

    def test_publishing_a_new_version_is_allowed(self):
        with mock.patch.object(
            release_pypi, "released_versions", return_value={"0.5.0"}
        ):
            release_pypi.require_unpublished("0.6.0", "pypi")

    def test_an_unreachable_index_never_reads_as_unpublished(self):
        """Assuming "not published" on a network error risks a doomed upload."""
        with mock.patch.object(
            release_pypi,
            "released_versions",
            side_effect=release_pypi.ReleaseError("cannot query pypi.org"),
        ):
            with self.assertRaises(release_pypi.ReleaseError):
                release_pypi.require_unpublished("0.6.0", "pypi")

    def test_missing_changelog_section_is_refused(self):
        with self.assertRaises(release_pypi.ReleaseError):
            release_pypi.require_changelog_entry("99.99.99")

    def test_current_version_has_a_changelog_section(self):
        release_pypi.require_changelog_entry(
            release_pypi.require_consistent_version()
        )


class DefaultsTest(unittest.TestCase):
    def test_preview_is_the_default_and_publishing_is_opt_in(self):
        self.assertFalse(release_pypi.parse_arguments([]).publish)
        self.assertTrue(release_pypi.parse_arguments(["--publish"]).publish)

    def test_default_index_is_pypi(self):
        self.assertEqual("pypi", release_pypi.parse_arguments([]).repository)

    def test_confirmation_is_required_unless_waived(self):
        self.assertFalse(release_pypi.parse_arguments([]).yes)


if __name__ == "__main__":
    unittest.main()
