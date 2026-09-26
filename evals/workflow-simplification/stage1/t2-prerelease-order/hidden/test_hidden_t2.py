import itertools
import random
import unittest

from semver_order import compare, sort_versions

CHAIN = [
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-alpha.beta",
    "1.0.0-beta",
    "1.0.0-beta.2",
    "1.0.0-beta.11",
    "1.0.0-rc.1",
    "1.0.0",
]


class HiddenT2(unittest.TestCase):
    def test_reported_example(self):
        self.assertEqual(
            ["1.0.0-rc.2", "1.0.0-rc.10", "1.0.0"],
            sort_versions(["1.0.0-rc.10", "1.0.0-rc.2", "1.0.0"]),
        )

    def test_spec_chain_all_pairs(self):
        for i, j in itertools.combinations(range(len(CHAIN)), 2):
            self.assertEqual(-1, compare(CHAIN[i], CHAIN[j]), (CHAIN[i], CHAIN[j]))
            self.assertEqual(1, compare(CHAIN[j], CHAIN[i]), (CHAIN[j], CHAIN[i]))

    def test_spec_chain_sort_from_shuffles(self):
        rng = random.Random(7)
        for _ in range(20):
            shuffled = CHAIN[:]
            rng.shuffle(shuffled)
            self.assertEqual(CHAIN, sort_versions(shuffled))

    def test_numeric_lower_than_alphanumeric(self):
        self.assertEqual(-1, compare("1.0.0-1", "1.0.0-a"))
        self.assertEqual(-1, compare("1.0.0-alpha.1", "1.0.0-alpha.a"))
        self.assertEqual(1, compare("1.0.0-a", "1.0.0-999"))

    def test_digit_leading_alphanumeric_is_not_numeric(self):
        self.assertEqual(-1, compare("1.0.0-1", "1.0.0-0a"))
        self.assertEqual(-1, compare("1.0.0-10a", "1.0.0-9a"))  # ASCII lexical

    def test_ascii_lexical_case(self):
        self.assertEqual(-1, compare("1.0.0-B", "1.0.0-a"))

    def test_hyphenated_identifier(self):
        self.assertEqual(-1, compare("1.0.0-alpha-1", "1.0.0-alpha-2"))

    def test_longer_prerelease_wins_when_prefix_equal(self):
        self.assertEqual(-1, compare("1.0.0-alpha", "1.0.0-alpha.0"))
        self.assertEqual(-1, compare("1.0.0-1.2", "1.0.0-1.2.a"))

    def test_large_numeric(self):
        self.assertEqual(-1, compare("1.0.0-99999999999999999999", "1.0.0-100000000000000000000"))

    def test_build_metadata_ignored(self):
        self.assertEqual(0, compare("1.0.0+a", "1.0.0+b"))
        self.assertEqual(0, compare("1.0.0-rc.1+x.1", "1.0.0-rc.1"))
        self.assertEqual(["1.0.0+b", "1.0.0+a"], sort_versions(["1.0.0+b", "1.0.0+a"]))

    def test_core_numeric(self):
        self.assertEqual(-1, compare("1.9.0", "1.10.0"))

    def test_invalid_still_rejected(self):
        for bad in ["1.0.0-01", "1.0", "01.0.0", "1.0.0-", "1.0.0+", "1.0.0-a..b", "v1.0.0"]:
            with self.assertRaises(ValueError, msg=bad):
                compare(bad, "1.0.0")


if __name__ == "__main__":
    unittest.main()
