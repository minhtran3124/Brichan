import unittest

from ledger_summary import summarize


class VisibleTest(unittest.TestCase):
    def test_one_launch_finished(self):
        data = (
            b'{"event": "launched", "launch_id": "a"}\n'
            b'{"event": "finished", "launch_id": "a"}\n'
        )
        self.assertEqual(
            {
                "finished": ["a"],
                "unknown": [],
                "orphans": [],
                "undecodable": 0,
                "duplicate_finished": 0,
                "duplicate_launched": 0,
            },
            summarize(data),
        )


if __name__ == "__main__":
    unittest.main()
