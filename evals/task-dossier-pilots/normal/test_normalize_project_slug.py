"""Focused unit tests for the TDW-007 pilot fixture."""

import re
import unittest

from normalize_project_slug import normalize_project_slug

# Literal copy of the repository's project slug grammar, defined at
# src/brichan/contracts/task_dossier/schema.py:181. It is restated here rather
# than imported because this fixture is deliberately isolated from the
# `brichan` package and is discovered with its own directory as the test root.
PROJECT_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class NormalizeProjectSlugTests(unittest.TestCase):
    def test_normal_input_is_trimmed_lowercased_and_hyphenated(self):
        self.assertEqual(
            normalize_project_slug("  Brida Task  Dossier "), "brida-task-dossier"
        )

    def test_repeated_separators_collapse_to_one_hyphen(self):
        self.assertEqual(normalize_project_slug("a___b---c"), "a-b-c")

    def test_edge_separators_are_stripped(self):
        self.assertEqual(normalize_project_slug("--alpha beta--"), "alpha-beta")

    def test_digits_are_preserved(self):
        self.assertEqual(normalize_project_slug("Project 42 v2"), "project-42-v2")

    def test_empty_normalized_input_raises_value_error(self):
        for value in ("!!!", "", "   "):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_project_slug(value)

    def test_non_ascii_letters_are_treated_as_separators(self):
        self.assertEqual(normalize_project_slug("Café"), "caf")

    def test_every_returned_slug_matches_the_project_slug_grammar(self):
        for value in (
            "  Brida Task  Dossier ",
            "a___b---c",
            "--alpha beta--",
            "Project 42 v2",
            "Café",
        ):
            with self.subTest(value=value):
                self.assertRegex(normalize_project_slug(value), PROJECT_SLUG_PATTERN)


if __name__ == "__main__":
    unittest.main()
