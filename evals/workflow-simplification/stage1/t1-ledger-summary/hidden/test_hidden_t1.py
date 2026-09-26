import unittest

from ledger_summary import summarize

L = lambda i: ('{"event": "launched", "launch_id": "%s"}' % i).encode()
F = lambda i: ('{"event": "finished", "launch_id": "%s"}' % i).encode()


def s(*lines, end=b"\n"):
    return b"\n".join(lines) + end


class HiddenT1(unittest.TestCase):
    def test_keys_exact(self):
        self.assertEqual(
            {"finished", "unknown", "orphans", "undecodable", "duplicate_finished", "duplicate_launched"},
            set(summarize(b"")),
        )

    def test_empty(self):
        r = summarize(b"")
        self.assertEqual(([], [], [], 0, 0, 0), (r["finished"], r["unknown"], r["orphans"], r["undecodable"], r["duplicate_finished"], r["duplicate_launched"]))

    def test_blank_and_whitespace_lines_not_counted(self):
        r = summarize(b"\n   \n\t\n" + s(L("a")) + b"\n\n")
        self.assertEqual(0, r["undecodable"])
        self.assertEqual(["a"], r["unknown"])

    def test_undecodable_kinds(self):
        lines = [
            b"not json",
            b"[1, 2]",
            b'"str"',
            b'{"event": "launched"}',
            b'{"launch_id": "x"}',
            b'{"event": "launched", "launch_id": 5}',
            b'{"event": 1, "launch_id": "x"}',
            b'{"event": "started", "launch_id": "x"}',
            b"\xff\xfe{}",
            b'{"event": "launched", "launch_id": "ok"}',
        ]
        r = summarize(s(*lines))
        self.assertEqual(9, r["undecodable"])
        self.assertEqual(["ok"], r["unknown"])

    def test_invalid_utf8_inside_otherwise_valid_line(self):
        r = summarize(b'{"event": "launched", "launch_id": "\xc3\x28"}\n')
        self.assertEqual(1, r["undecodable"])

    def test_pairs_by_launch_id_not_worker(self):
        data = s(
            b'{"event": "launched", "launch_id": "a", "worker": "brichan-w"}',
            b'{"event": "launched", "launch_id": "b", "worker": "brichan-w"}',
            b'{"event": "finished", "launch_id": "b", "worker": "brichan-other"}',
        )
        r = summarize(data)
        self.assertEqual(["b"], r["finished"])
        self.assertEqual(["a"], r["unknown"])

    def test_duplicate_finished(self):
        r = summarize(s(L("a"), F("a"), F("a"), F("a")))
        self.assertEqual(["a"], r["finished"])
        self.assertEqual(2, r["duplicate_finished"])

    def test_finished_before_launched_is_not_orphan(self):
        r = summarize(s(F("a"), L("a")))
        self.assertEqual(["a"], r["finished"])
        self.assertEqual([], r["orphans"])

    def test_orphans_unique_first_order(self):
        r = summarize(s(F("z"), F("y"), F("z")))
        self.assertEqual(["z", "y"], r["orphans"])
        self.assertEqual([], r["finished"])

    def test_orphan_repeat_counts_duplicate_finished(self):
        # The first finished for a launch_id wins even without a launched record.
        r = summarize(s(F("z"), F("z")))
        self.assertEqual(1, r["duplicate_finished"])

    def test_duplicate_launched(self):
        r = summarize(s(L("a"), L("b"), L("a"), F("a")))
        self.assertEqual(1, r["duplicate_launched"])
        self.assertEqual(["a"], r["finished"])
        self.assertEqual(["b"], r["unknown"])

    def test_order_follows_launched_records(self):
        r = summarize(s(L("c"), L("a"), L("b"), F("b"), F("c"), F("a")))
        self.assertEqual(["c", "a", "b"], r["finished"])

    def test_last_line_without_newline(self):
        r = summarize(s(L("a"), F("a"), end=b""))
        self.assertEqual(["a"], r["finished"])

    def test_crlf(self):
        r = summarize(L("a") + b"\r\n" + F("a") + b"\r\n")
        self.assertEqual(["a"], r["finished"])
        self.assertEqual(0, r["undecodable"])

    def test_unknown_keys_ignored(self):
        r = summarize(s(b'{"event": "launched", "launch_id": "a", "extra": {"x": [1]}}'))
        self.assertEqual(["a"], r["unknown"])


if __name__ == "__main__":
    unittest.main()
