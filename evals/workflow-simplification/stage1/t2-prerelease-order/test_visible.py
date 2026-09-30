import unittest

from semver_order import compare, sort_versions


class VisibleTest(unittest.TestCase):
    def test_core_order(self):
        self.assertEqual(
            ["1.0.0", "1.2.0", "2.0.0"], sort_versions(["2.0.0", "1.0.0", "1.2.0"])
        )

    def test_release_beats_prerelease(self):
        self.assertEqual(1, compare("1.0.0", "1.0.0-rc.1"))

    def test_invalid(self):
        with self.assertRaises(ValueError):
            compare("1.0", "1.0.0")


if __name__ == "__main__":
    unittest.main()
