import unittest

from path_guard import validate_ledger_path as v


class HiddenT3(unittest.TestCase):
    def test_requested_normalization(self):
        self.assertEqual("ledger/workers.jsonl", v("ledger/./workers.jsonl"))
        self.assertEqual("ledger/workers.jsonl", v("ledger//workers.jsonl"))
        self.assertEqual("ledger/workers.jsonl", v("./ledger/workers.jsonl"))
        self.assertEqual("a/b/w.jsonl", v("a/.//./b///w.jsonl"))
        self.assertEqual("w.jsonl", v("w.jsonl"))

    def test_parent_rejected_even_if_it_resolves_inside(self):
        for bad in ["a/../w.jsonl", "a/b/../../w.jsonl", "./../w.jsonl", "a//..//w.jsonl", "../w.jsonl", "a/.."]:
            with self.assertRaises(ValueError, msg=bad):
                v(bad)

    def test_absolute_rejected_including_repeated_leading_slashes(self):
        for bad in ["/w.jsonl", "//w.jsonl", "///etc/w.jsonl"]:
            with self.assertRaises(ValueError, msg=bad):
                v(bad)

    def test_brichan_component_any_case_after_normalization(self):
        for bad in [".brichan/w.jsonl", "./.brichan/w.jsonl", "a//.BRICHAN/w.jsonl", "a/./.Brichan/./w.jsonl", "a/.brichan"]:
            with self.assertRaises(ValueError, msg=bad):
                v(bad)

    def test_brichan_substring_is_allowed(self):
        self.assertEqual("x.brichan/w.jsonl", v("x.brichan/w.jsonl"))

    def test_backslash_and_nul(self):
        for bad in ["a\\w.jsonl", "a/w.jsonl\x00", "a\\..\\w.jsonl"]:
            with self.assertRaises(ValueError, msg=bad):
                v(bad)

    def test_suffix_checked_on_normalized_final_component(self):
        for bad in ["a/w.json", "w.jsonl/x"]:
            with self.assertRaises(ValueError, msg=bad):
                v(bad)

    def test_empty_results_rejected(self):
        for bad in ["", ".", "./", "//", "./."]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                v(bad)

    def test_value_error_type(self):
        with self.assertRaises(ValueError):
            v("../x.jsonl")


if __name__ == "__main__":
    unittest.main()
