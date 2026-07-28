import unittest

from target import is_terminal, transition


class TransitionTests(unittest.TestCase):
    def test_known_transitions(self):
        self.assertEqual(transition("active", "stale"), "stale")
        self.assertEqual(transition("stale", "abandon"), "abandoned")
        self.assertEqual(transition("abandoned", "replace"), "active")

    def test_terminal_states(self):
        self.assertTrue(is_terminal("complete"))
        self.assertTrue(is_terminal("abandoned"))
        self.assertFalse(is_terminal("active"))


if __name__ == "__main__":
    unittest.main()
