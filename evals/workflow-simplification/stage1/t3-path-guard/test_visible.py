import unittest

from path_guard import validate_ledger_path


class VisibleTest(unittest.TestCase):
    def test_plain(self):
        self.assertEqual("ledger/workers.jsonl", validate_ledger_path("ledger/workers.jsonl"))

    def test_parent_rejected(self):
        with self.assertRaises(ValueError):
            validate_ledger_path("../workers.jsonl")


if __name__ == "__main__":
    unittest.main()
