"""Exact map, leaf, selector, and Examples grammar vectors.

Every fixture below is copyable: it is assembled from the literal Design
section 5 tokens and the frozen Design section 15 fixture bytes, never from a
regenerated approximation. LF and CRLF documents are asserted to parse to equal
semantic models while retaining different raw byte counts and hashes.
"""

import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.techstacks import markdown


#: The exact Design section 15 base map bytes.
BASE_MAP_LINES = (
    "# Base techstack map",
    "",
    "Map only. This README contains no normative rules.",
    "",
    "## Map metadata",
    "",
    "- Context ID: `root`",
    "",
    "## Contexts",
    "",
    "| Context ID | Rule path | Applies to |",
    "| --- | --- | --- |",
    "| frontend | `techstacks/frontend/README.md` | `src/frontend/` |",
    "| general | `techstacks/general.md` | `.` |",
)

#: The exact Design section 15 base leaf bytes.
BASE_LEAF_LINES = (
    "# General rules",
    "",
    "## Rule metadata",
    "",
    "- Context ID: `general`",
    "- Reviewed on: `2026-08-01`",
    "- Review within days: `365`",
    "- Deprecated: `no`",
    "- Evidence: None.",
    "",
    "## Scope",
    "",
    "- Applies to every task.",
    "",
    "## Rules",
    "",
    "- `GENERAL-001`: Keep project context bounded.",
    "",
    "## Overrides",
    "",
    "- None.",
    "",
    "## Verification",
    "",
    "- Verify the selected Snapshot before work.",
    "",
    "## Exceptions",
    "",
    "- None.",
    "",
    "## Examples",
    "",
    "None.",
)

def document(lines, newline="\n"):
    """Render one line array as raw bytes with exactly one terminal newline."""

    return newline.join(list(lines) + [""]).encode("utf-8")


def leaf_lines(*, examples=("None.",)):
    """Return the base leaf lines with the Examples section body replaced."""

    return list(BASE_LEAF_LINES[:-1]) + list(examples)


def with_section_body(heading, body):
    """Return the base leaf lines with one section body replaced."""

    lines = list(BASE_LEAF_LINES)
    start = lines.index(heading) + 2
    end = start
    while end < len(lines) and lines[end] != "":
        end += 1
    lines[start:end] = list(body)
    return lines


def map_lines(rows, *, context_id="root", title="# Base techstack map"):
    """Return one map document's lines for the given row tuples."""

    lines = [
        title,
        "",
        markdown.MAP_ONLY_SENTENCE,
        "",
        markdown.MAP_METADATA_HEADING,
        "",
        f"- Context ID: `{context_id}`",
        "",
        markdown.CONTEXTS_HEADING,
        "",
    ]
    if rows is None:
        return lines + [markdown.NONE_LINE]
    lines += [markdown.CONTEXTS_TABLE_HEADER, markdown.CONTEXTS_TABLE_SEPARATOR]
    for identifier, path, selectors in rows:
        rendered = "; ".join(f"`{selector}`" for selector in selectors)
        lines.append(f"| {identifier} | `{path}` | {rendered} |")
    return lines


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class SelectorAlgebraTest(unittest.TestCase):
    def test_containment_follows_the_closed_selector_rules(self):
        self.assertTrue(markdown.selector_contains(".", "src/a"))
        self.assertTrue(markdown.selector_contains(".", "src/"))
        self.assertFalse(markdown.selector_contains("src/a", "."))
        self.assertTrue(markdown.selector_contains("src/a", "src/a"))
        self.assertFalse(markdown.selector_contains("src/a", "src/ab"))
        self.assertTrue(markdown.selector_contains("src/", "src/a"))
        self.assertTrue(markdown.selector_contains("src/", "src/"))
        self.assertTrue(markdown.selector_contains("src/", "src/deep/"))
        self.assertFalse(markdown.selector_contains("src/a/", "src/"))

    def test_overlap_is_symmetric_and_disjoint_peers_do_not_overlap(self):
        self.assertTrue(markdown.selectors_overlap("src/", "src/a"))
        self.assertTrue(markdown.selectors_overlap("src/a", "src/"))
        self.assertFalse(markdown.selectors_overlap("src/a", "src/b"))
        self.assertFalse(markdown.selectors_overlap("src/a/", "src/b/"))
        self.assertTrue(markdown.selectors_overlap(".", "src/b/"))

    def test_normalization_removes_contained_selectors_and_sorts(self):
        self.assertEqual(
            ("src/",), markdown.normalize_selectors(("src/a", "src/", "src/b/"))
        )
        self.assertEqual(
            ("docs/", "src/a"), markdown.normalize_selectors(("src/a", "docs/"))
        )
        self.assertEqual((".",), markdown.normalize_selectors((".", "src/a")))

    def test_union_subset_and_overlap_use_containment(self):
        self.assertTrue(markdown.union_is_subset(("src/a",), ("src/",)))
        self.assertFalse(markdown.union_is_subset(("src/",), ("src/a",)))
        self.assertTrue(markdown.unions_overlap(("src/a",), ("src/",)))
        self.assertFalse(markdown.unions_overlap(("src/a",), ("docs/",)))

    def test_prefix_selector_predicate_matches_the_model(self):
        self.assertTrue(markdown.is_prefix_selector("src/frontend/"))
        self.assertFalse(markdown.is_prefix_selector("src/frontend"))
        self.assertFalse(markdown.is_prefix_selector("src//"))


class MapGrammarTest(unittest.TestCase):
    def test_the_frozen_base_map_parses_to_its_exact_rows(self):
        parsed = markdown.parse_map(document(BASE_MAP_LINES))
        self.assertEqual("Base techstack map", parsed.title)
        self.assertEqual("root", parsed.context_id)
        self.assertEqual(
            ("frontend", "general"), tuple(row.context_id for row in parsed.rows)
        )
        frontend, general = parsed.rows
        self.assertEqual("techstacks/frontend/README.md", frontend.rule_path)
        self.assertEqual(("src/frontend/",), frontend.applies_to)
        self.assertTrue(frontend.is_map)
        self.assertEqual("techstacks/general.md", general.rule_path)
        self.assertEqual((".",), general.applies_to)
        self.assertFalse(general.is_map)

    def test_lf_and_crlf_maps_are_semantically_equal_with_different_bytes(self):
        lf_bytes = document(BASE_MAP_LINES)
        crlf_bytes = document(BASE_MAP_LINES, newline="\r\n")
        self.assertNotEqual(len(lf_bytes), len(crlf_bytes))
        self.assertNotEqual(sha256(lf_bytes), sha256(crlf_bytes))
        self.assertEqual(markdown.parse_map(lf_bytes), markdown.parse_map(crlf_bytes))

    def test_rows_sort_by_context_then_path_then_selectors(self):
        rows = [
            ("zebra", "techstacks/zebra.md", ("src/z",)),
            ("alpha", "techstacks/alpha.md", ("src/a",)),
        ]
        parsed = markdown.parse_map(document(map_lines(rows)))
        self.assertEqual(("alpha", "zebra"), tuple(row.context_id for row in parsed.rows))

    def test_a_none_table_replaces_the_whole_table(self):
        parsed = markdown.parse_map(document(map_lines(None)))
        self.assertEqual((), parsed.rows)

    def test_selectors_normalize_per_row(self):
        rows = [("alpha", "techstacks/alpha.md", ("src/a", "src/"))]
        parsed = markdown.parse_map(document(map_lines(rows)))
        self.assertEqual(("src/a", "src/"), parsed.rows[0].selectors)
        self.assertEqual(("src/",), parsed.rows[0].applies_to)

    def assert_invalid_map(self, lines, code="INVALID_MAP", newline="\n"):
        with self.assertRaises(markdown.MarkdownError) as error:
            markdown.parse_map(document(lines, newline=newline))
        self.assertEqual(code, error.exception.code)
        return error.exception

    def test_every_prohibited_outside_form_is_rejected(self):
        base = list(BASE_MAP_LINES)
        cases = {
            "heading": lambda lines: lines.insert(1, "### Extra"),
            "list": lambda lines: lines.insert(1, "- stray bullet"),
            "html": lambda lines: lines.insert(1, "<div>"),
            "reference": lambda lines: lines.insert(1, "[ref]: https://example.test"),
            "setext": lambda lines: lines.insert(1, "==="),
            "thematic": lambda lines: lines.insert(1, "---"),
            "indentation": lambda lines: lines.__setitem__(2, "  " + lines[2]),
            "tab": lambda lines: lines.__setitem__(2, lines[2] + "\t"),
            "trailing_space": lambda lines: lines.__setitem__(2, lines[2] + " "),
            "extra_blank": lambda lines: lines.insert(3, ""),
            "missing_blank": lambda lines: lines.pop(1),
            "reordered": lambda lines: lines.insert(4, lines.pop(8)),
            "unknown_section": lambda lines: lines.__setitem__(4, "## Unknown"),
            "unknown_sentence": lambda lines: lines.__setitem__(2, "Map only."),
            "trailing_line": lambda lines: lines.append("trailing"),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                lines = list(base)
                mutate(lines)
                self.assert_invalid_map(lines)

    def test_byte_level_prohibitions_are_rejected(self):
        raw = document(BASE_MAP_LINES)
        for name, payload in (
            ("bom", b"\xef\xbb\xbf" + raw),
            ("nul", raw.replace(b"map", b"m\x00p", 1)),
            ("bare_cr", raw.replace(b"\n", b"\r", 1)),
            ("invalid_utf8", raw.replace(b"Base", b"\xff\xfe", 1)),
            ("missing_terminal_lf", raw[:-1]),
            ("double_terminal_lf", raw + b"\n"),
        ):
            with self.subTest(case=name):
                with self.assertRaises(markdown.MarkdownError) as error:
                    markdown.parse_map(payload)
                self.assertEqual("INVALID_MAP", error.exception.code)

    def test_row_cells_reject_pipe_backslash_and_bad_paths(self):
        for name, rows in (
            ("absolute", [("alpha", "/techstacks/alpha.md", ("src/a",))]),
            ("outside", [("alpha", "docs/alpha.md", ("src/a",))]),
            ("dotdot", [("alpha", "techstacks/../alpha.md", ("src/a",))]),
            ("root_readme", [("alpha", "techstacks/README.md", ("src/a",))]),
            ("not_markdown", [("alpha", "techstacks/alpha.txt", ("src/a",))]),
            ("reserved_id", [("root", "techstacks/alpha.md", ("src/a",))]),
            ("upper_id", [("Alpha", "techstacks/alpha.md", ("src/a",))]),
            ("duplicate_selector", [("alpha", "techstacks/alpha.md", ("src/a", "src/a"))]),
            ("bad_selector", [("alpha", "techstacks/alpha.md", ("/src/a",))]),
            ("duplicate_row_id", [
                ("alpha", "techstacks/alpha.md", ("src/a",)),
                ("alpha", "techstacks/beta.md", ("src/b",)),
            ]),
            ("duplicate_row_path", [
                ("alpha", "techstacks/alpha.md", ("src/a",)),
                ("beta", "techstacks/alpha.md", ("src/b",)),
            ]),
        ):
            with self.subTest(case=name):
                self.assert_invalid_map(map_lines(rows))
        self.assert_invalid_map(
            map_lines([("alpha", "techstacks/alpha.md", ("src/a",))])[:-1]
            + ["| alpha | `techstacks/alpha.md` | `src/a` | extra |"]
        )

    def test_map_rows_thirty_two_pass_and_thirty_three_overflow(self):
        rows = [
            (f"c{index:02d}", f"techstacks/c{index:02d}.md", (f"src/c{index:02d}",))
            for index in range(32)
        ]
        self.assertEqual(32, len(markdown.parse_map(document(map_lines(rows))).rows))
        rows.append(("c32", "techstacks/c32.md", ("src/c32",)))
        self.assert_invalid_map(map_lines(rows), code="MAP_ROW_LIMIT")

    def test_selectors_sixteen_pass_and_seventeen_overflow_with_context(self):
        selectors = tuple(f"src/s{index:02d}" for index in range(16))
        rows = [("alpha", "techstacks/alpha.md", selectors)]
        parsed = markdown.parse_map(document(map_lines(rows)))
        self.assertEqual(16, len(parsed.rows[0].applies_to))
        rows = [("alpha", "techstacks/alpha.md", selectors + ("src/s16",))]
        error = self.assert_invalid_map(map_lines(rows), code="SELECTOR_LIMIT")
        self.assertEqual("alpha", error.context_id)

    def test_map_metadata_identity_is_reported_for_child_equality(self):
        lines = map_lines(
            [("alpha", "techstacks/alpha.md", ("src/a",))], context_id="frontend"
        )
        self.assertEqual("frontend", markdown.parse_map(document(lines)).context_id)

    def test_a_readme_never_emits_a_rule_section(self):
        parsed = markdown.parse_map(document(BASE_MAP_LINES))
        self.assertFalse(hasattr(parsed, "rules"))
        for heading in ("## Rules", "## Scope", "## Verification", "## Exceptions"):
            with self.subTest(heading=heading):
                lines = list(BASE_MAP_LINES) + ["", heading, "", "- prose."]
                self.assert_invalid_map(lines)

    def test_title_bounds(self):
        self.assertEqual(
            "t" * 128,
            markdown.parse_map(document(map_lines(None, title="# " + "t" * 128))).title,
        )
        self.assert_invalid_map(map_lines(None, title="# " + "t" * 129))
        self.assert_invalid_map(map_lines(None, title="#"))
        self.assert_invalid_map(map_lines(None, title="# "))

    def test_the_title_class_is_wider_than_the_prose_class(self):
        # The retained version-3 title rule constrains one line, 1-128 UTF-8
        # bytes, NFC, and no surrounding whitespace; it does not name the
        # prose class, so a title may carry the markup characters a Scope or
        # Verification bullet may not. The title reaches no Snapshot field.
        for title in ("<b>Title</b>", "Title `t`", "Title | t"):
            with self.subTest(title=title):
                self.assertEqual(
                    title,
                    markdown.parse_map(
                        document(map_lines(None, title=f"# {title}"))
                    ).title,
                )


class LeafGrammarTest(unittest.TestCase):
    def assert_invalid_leaf(self, lines, code="INVALID_LEAF", newline="\n"):
        with self.assertRaises(markdown.MarkdownError) as error:
            markdown.parse_leaf(document(lines, newline=newline))
        self.assertEqual(code, error.exception.code)
        return error.exception

    def test_the_frozen_base_leaf_parses_to_its_exact_sections(self):
        parsed = markdown.parse_leaf(document(BASE_LEAF_LINES))
        self.assertEqual("General rules", parsed.title)
        self.assertEqual("general", parsed.context_id)
        self.assertEqual("2026-08-01", parsed.reviewed_on)
        self.assertEqual(365, parsed.review_within_days)
        self.assertFalse(parsed.deprecated)
        self.assertIsNone(parsed.deprecated_on)
        self.assertEqual((), parsed.evidence)
        self.assertEqual(("Applies to every task.",), parsed.scope)
        self.assertEqual(("GENERAL-001",), tuple(rule.rule_id for rule in parsed.rules))
        self.assertEqual(
            "Keep project context bounded.", parsed.rules[0].statement
        )
        self.assertEqual((), parsed.overrides)
        self.assertEqual((), parsed.exceptions)
        self.assertEqual((), parsed.examples)
        self.assertEqual(0, parsed.example_payload_bytes)

    def test_lf_and_crlf_leaves_are_semantically_equal_with_different_bytes(self):
        lf_bytes = document(BASE_LEAF_LINES)
        crlf_bytes = document(BASE_LEAF_LINES, newline="\r\n")
        self.assertNotEqual(len(lf_bytes), len(crlf_bytes))
        self.assertNotEqual(sha256(lf_bytes), sha256(crlf_bytes))
        self.assertEqual(markdown.parse_leaf(lf_bytes), markdown.parse_leaf(crlf_bytes))

    def test_evidence_deprecation_and_override_forms(self):
        lines = list(BASE_LEAF_LINES)
        lines[8] = "- Evidence: `evidence/one.txt`; `evidence/two.txt`"
        lines[7] = "- Deprecated: `yes: 2026-07-01: the component moved`"
        parsed = markdown.parse_leaf(document(lines))
        self.assertEqual(("evidence/one.txt", "evidence/two.txt"), parsed.evidence)
        self.assertTrue(parsed.deprecated)
        self.assertEqual("2026-07-01", parsed.deprecated_on)
        self.assertEqual("the component moved", parsed.deprecated_reason)
        override = list(BASE_LEAF_LINES)
        override[20] = "- `GENERAL-001` -> `root-domain`: the domain rule is nearer"
        parsed = markdown.parse_leaf(document(override))
        self.assertEqual(1, len(parsed.overrides))
        self.assertEqual("root-domain", parsed.overrides[0].target_context_id)
        self.assertEqual("GENERAL-001", parsed.overrides[0].rule_id)

    def test_every_prohibited_outside_form_is_rejected(self):
        cases = {
            "heading": lambda lines: lines.insert(12, "#### Deep"),
            "list": lambda lines: lines.insert(12, "* star bullet"),
            "nested_list": lambda lines: lines.insert(13, "  - nested"),
            "html": lambda lines: lines.insert(12, "<span>x</span>"),
            "reference": lambda lines: lines.insert(12, "[ref]: https://example.test"),
            "block_quote": lambda lines: lines.insert(12, "> quoted"),
            "setext": lambda lines: lines.insert(12, "==="),
            "thematic": lambda lines: lines.insert(12, "***"),
            "indentation": lambda lines: lines.__setitem__(12, "  " + lines[12]),
            "lazy_continuation": lambda lines: lines.insert(13, "continued prose"),
            "tab": lambda lines: lines.__setitem__(12, lines[12] + "\ta"),
            "trailing_space": lambda lines: lines.__setitem__(12, lines[12] + " "),
            "extra_blank": lambda lines: lines.insert(13, ""),
            "missing_blank": lambda lines: lines.pop(11),
            "reordered_sections": lambda lines: lines.insert(10, lines.pop(14)),
            "unknown_section": lambda lines: lines.__setitem__(10, "## Unknown"),
            "unconsumed_line": lambda lines: lines.append("trailing"),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                lines = list(BASE_LEAF_LINES)
                mutate(lines)
                self.assert_invalid_leaf(lines)

    def test_byte_level_prohibitions_are_rejected(self):
        raw = document(BASE_LEAF_LINES)
        for name, payload in (
            ("bom", b"\xef\xbb\xbf" + raw),
            ("nul", raw.replace(b"General", b"Gene\x00al", 1)),
            ("bare_cr", raw.replace(b"\n", b"\r", 1)),
            ("invalid_utf8", raw.replace(b"General", b"\xff\xfeneral", 1)),
            ("missing_terminal_lf", raw[:-1]),
            ("double_terminal_lf", raw + b"\n"),
        ):
            with self.subTest(case=name):
                with self.assertRaises(markdown.MarkdownError) as error:
                    markdown.parse_leaf(payload)
                self.assertEqual("INVALID_LEAF", error.exception.code)

    def test_metadata_token_rules(self):
        for index, replacement in (
            (4, "- Context ID: `Root`"),
            (4, "- Context ID: `root`"),
            (5, "- Reviewed on: `2026-02-30`"),
            (5, "- Reviewed on: `2026-8-01`"),
            (6, "- Review within days: `0`"),
            (6, "- Review within days: `3651`"),
            (6, "- Review within days: `0365`"),
            (6, "- Review within days: `+365`"),
            (7, "- Deprecated: `maybe`"),
            (7, "- Deprecated: `yes: 2026-13-01: reason`"),
            (8, "- Evidence: None"),
            (8, "- Evidence: `a.txt`; `a.txt`"),
            (8, "- Evidence: `/a.txt`"),
        ):
            with self.subTest(line=replacement):
                lines = list(BASE_LEAF_LINES)
                lines[index] = replacement
                self.assert_invalid_leaf(lines)

    def test_bullet_count_bounds(self):
        with_body = with_section_body
        scope = [f"- Scope bullet {index:02d}." for index in range(16)]
        markdown.parse_leaf(document(with_body("## Scope", scope)))
        self.assert_invalid_leaf(with_body("## Scope", scope + ["- Scope bullet 16."]))
        rules = [
            f"- `RULE-{index:02d}`: Rule statement {index:02d}." for index in range(32)
        ]
        markdown.parse_leaf(document(with_body("## Rules", rules)))
        self.assert_invalid_leaf(
            with_body("## Rules", rules + ["- `RULE-32`: Rule statement 32."])
        )
        verification = [f"- Verification bullet {index:02d}." for index in range(16)]
        markdown.parse_leaf(document(with_body("## Verification", verification)))
        self.assert_invalid_leaf(
            with_body("## Verification", verification + ["- Verification bullet 16."])
        )
        exceptions = [f"- Exception bullet {index:02d}." for index in range(16)]
        markdown.parse_leaf(document(with_body("## Exceptions", exceptions)))
        self.assert_invalid_leaf(
            with_body("## Exceptions", exceptions + ["- Exception bullet 16."])
        )
        # Overrides may name at most 32 records, and every Rule ID must occur
        # in this leaf's own Rules section.
        lines = with_body("## Rules", rules)
        start = lines.index("## Overrides") + 2
        overrides = [
            f"- `RULE-{index:02d}` -> `target-{index:02d}`: reason {index:02d}"
            for index in range(32)
        ]
        lines[start:start + 1] = overrides
        markdown.parse_leaf(document(lines))
        lines[start:start + 32] = overrides + [
            "- `RULE-00` -> `target-33`: one record too many"
        ]
        self.assert_invalid_leaf(lines)
        self.assert_invalid_leaf(with_body("## Scope", ["- None."]))
        self.assert_invalid_leaf(with_body("## Verification", ["- None."]))
        self.assert_invalid_leaf(with_body("## Rules", ["- None."]))
        self.assert_invalid_leaf(with_body("## Overrides", []))

    def test_override_records_bind_to_this_leaf(self):
        lines = list(BASE_LEAF_LINES)
        lines[20] = "- `MISSING-001` -> `other`: unknown rule"
        self.assert_invalid_leaf(lines)
        lines[20] = "- `GENERAL-001` -> `general`: self target"
        self.assert_invalid_leaf(lines)
        lines[20] = "- `GENERAL-001` -> `other`: fine"
        markdown.parse_leaf(document(lines))
        duplicate = list(BASE_LEAF_LINES)
        duplicate[20:21] = [
            "- `GENERAL-001` -> `other`: fine",
            "- `GENERAL-001` -> `other`: repeated",
        ]
        self.assert_invalid_leaf(duplicate)

    def test_duplicate_rule_ids_in_one_leaf_are_invalid(self):
        lines = list(BASE_LEAF_LINES)
        lines[16:17] = [
            "- `GENERAL-001`: Keep project context bounded.",
            "- `GENERAL-001`: Keep it bounded twice.",
        ]
        self.assert_invalid_leaf(lines)

    def test_prose_rejects_control_and_markup_characters(self):
        for prose in ("- Applies to `code`.", "- Applies to <b>.", "- Applies to a|b."):
            with self.subTest(prose=prose):
                lines = list(BASE_LEAF_LINES)
                lines[12] = prose
                self.assert_invalid_leaf(lines)


class ExamplesStateMachineTest(unittest.TestCase):
    def parse(self, examples, newline="\n"):
        return markdown.parse_leaf(
            document(leaf_lines(examples=examples), newline=newline)
        )

    def assert_invalid(self, examples, newline="\n"):
        with self.assertRaises(markdown.MarkdownError) as error:
            self.parse(examples, newline=newline)
        self.assertEqual("INVALID_LEAF", error.exception.code)

    def test_none_reaches_done_immediately(self):
        parsed = self.parse(("None.",))
        self.assertEqual((), parsed.examples)

    def test_label_requires_one_blank_line_then_an_opening(self):
        parsed = self.parse(("Example only.", "", "```text", "payload", "```"))
        self.assertEqual(("text",), tuple(fence.language for fence in parsed.examples))
        self.assertEqual(8, parsed.example_payload_bytes)
        self.assert_invalid(("Example only.", "```text", "payload", "```"))
        self.assert_invalid(("Example only.", "", "", "```text", "payload", "```"))
        self.assert_invalid(("Example only",))
        self.assert_invalid(("none.",))

    def test_opening_requires_a_language(self):
        self.assert_invalid(("Example only.", "", "```", "payload", "```"))
        self.assert_invalid(("Example only.", "", "```Text", "payload", "```"))
        self.assert_invalid(("Example only.", "", "```1text", "payload", "```"))
        self.assert_invalid(("Example only.", "", "~~~text", "payload", "~~~"))
        self.assert_invalid(
            ("Example only.", "", "```" + "t" * 33, "payload", "```")
        )
        self.parse(("Example only.", "", "```" + "t" * 32, "payload", "```"))

    def test_every_accepted_inside_payload_form(self):
        payload = [
            "\tindented with a tab",
            "trailing space   ",
            "<div>html</div>",
            "# heading",
            "- list marker",
            "> block quote",
            "***",
            "===",
            "~~~",
            "    ```indented fence",
            "````",
            "```text",
            "``` trailing text",
            "|pipe| and \\backslash",
        ]
        parsed = self.parse(("Example only.", "", "```text", *payload, "```"))
        expected = sum(len(line.encode("utf-8")) + 1 for line in payload)
        self.assertEqual(expected, parsed.example_payload_bytes)
        self.assertEqual(expected, parsed.examples[0].payload_bytes)

    def test_exact_three_backticks_always_closes_and_is_never_payload(self):
        # A payload line equal to three backticks closes the fence, so the
        # following line becomes text outside a fence and rejects.
        self.assert_invalid(("Example only.", "", "```text", "```", "still payload", "```"))

    def test_adjacent_open_close_is_the_unique_zero_byte_payload(self):
        empty = self.parse(("Example only.", "", "```text", "```"))
        self.assertEqual(0, empty.example_payload_bytes)
        blank = self.parse(("Example only.", "", "```text", "", "```"))
        self.assertEqual(1, blank.example_payload_bytes)

    def test_payload_line_bytes_4096_pass_and_4097_reject(self):
        self.parse(("Example only.", "", "```text", "x" * 4096, "```"))
        self.assert_invalid(("Example only.", "", "```text", "x" * 4097, "```"))

    def test_aggregate_payload_8192_passes_and_8193_rejects(self):
        two_lines = ["x" * 4095, "y" * 4095]
        parsed = self.parse(("Example only.", "", "```text", *two_lines, "```"))
        self.assertEqual(8192, parsed.example_payload_bytes)
        self.assert_invalid(("Example only.", "", "```text", "x" * 4095, "y" * 4096, "```"))

    def test_lf_and_crlf_payload_counts_are_equal(self):
        examples = ("Example only.", "", "```text", "alpha", "beta", "```")
        lf_parsed = self.parse(examples)
        crlf_parsed = self.parse(examples, newline="\r\n")
        self.assertEqual(
            lf_parsed.example_payload_bytes, crlf_parsed.example_payload_bytes
        )
        self.assertEqual(lf_parsed, crlf_parsed)
        self.assertNotEqual(
            len(document(leaf_lines(examples=examples))),
            len(document(leaf_lines(examples=examples), newline="\r\n")),
        )

    def test_eight_fences_pass_and_nine_reject(self):
        def fences(count):
            lines = ["Example only.", ""]
            for index in range(count):
                if index:
                    lines.append("")
                lines += ["```text", f"payload {index}", "```"]
            return tuple(lines)

        self.assertEqual(8, len(self.parse(fences(8)).examples))
        self.assert_invalid(fences(9))

    def test_missing_close_and_extra_inter_fence_blank_reject(self):
        self.assert_invalid(("Example only.", "", "```text", "payload"))
        self.assert_invalid(
            ("Example only.", "", "```text", "a", "```", "", "", "```text", "b", "```")
        )
        self.assert_invalid(
            ("Example only.", "", "```text", "a", "```", "```text", "b", "```")
        )
        self.assert_invalid(("Example only.", "", "```text", "a", "```", "", "outside"))

    def test_payload_bytes_are_normalized_even_for_multibyte_text(self):
        parsed = self.parse(("Example only.", "", "```text", "é" * 10, "```"))
        self.assertEqual(21, parsed.example_payload_bytes)


if __name__ == "__main__":  # pragma: no cover - exercised by the test runner
    unittest.main()
