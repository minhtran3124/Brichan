import contextlib
import io
import json
import shlex
import re
import tempfile
import unittest
from pathlib import Path

from brichan.cli.render import (
    DOCTOR_DESCRIPTION,
    DOCTOR_JSON_HELP,
    INIT_DESCRIPTION,
    INIT_SUBTITLE,
    STATUS_DESCRIPTION,
    Style,
    format_doctor_json,
    format_doctor_text,
    format_init,
    resolve_style,
)
from brichan.cli import render
from brichan.cli import runtime
from brichan.lifecycle import (
    AGENT_SKILL_EXPORT_DETAILS,
    AGENT_SKILL_EXPORT_ROWS,
    documented_footprint,
)


#: Design section 16 freezes all 27 complete unstyled outputs literally.
FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "doctor_v2_text.json"
)
DOCTOR_V2_TEXT = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

EXPORT_ROOT = "/repo"
MANAGED_SKILL_PATH = "/repo/.brichan/skills/herdr-orchestration"
EXPORTED_SKILL_PATH = "/repo/.agents/skills/herdr-orchestration"

FOOTPRINT = [f"create .brichan/{path}" for path in documented_footprint()]
DRY_RUN = ["dry-run: zero writes", *FOOTPRINT]
APPLIED = ["initialized: /repo/.brichan", *FOOTPRINT]

FANCY = Style(color=True, unicode=True)
PLAIN = Style(color=False, unicode=False)


#: The design's frozen blocks, committed beside the doctor fixture so the
#: registry tests compare the module to the authority on every checkout rather
#: than only where the gitignored dossier is. Each fixture's SHA-256 is frozen,
#: and its bytes are checked against the design wherever the dossier is on
#: disk, by `tests.contract.test_techstack_policy_contract`.
DESIGN_FIXTURES = FIXTURE_PATH.parent
SECTION_9_REGISTRY = DESIGN_FIXTURES / "doctor_section_9_registry.md"
SECTION_14_BLOCK = DESIGN_FIXTURES / "doctor_section_14_block.md"
SECTION_16_ROWS = DESIGN_FIXTURES / "doctor_section_16_rows.md"
SECTION_16_VERSION_9_BLOCKS = (
    DESIGN_FIXTURES / "doctor_section_16_version_9_blocks.md"
)

#: The three authoritative surfaces: section 9's closed detail_code registry,
#: section 14's frozen literal block, and section 16's sole authoritative
#: cross-product.
SECTION_9_HEADER = "| Code | Exact detail |"
SECTION_14_HEADING = "### Exact doctor `agent_skill_export` details"
SECTION_16_HEADER = (
    "| detail_code in precedence order | status/relation | path | managed_path "
    "| files |"
)


def design_table(text: str, header: str) -> list[list[str]]:
    """The body rows of the one markdown table introduced by `header`."""

    lines = text.split("\n")
    start = lines.index(header) + 2
    rows = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def design_detail_block(text: str, heading: str) -> list[tuple[str, str]]:
    """The `CODE=detail` lines of the first fenced block under `heading`.

    Anchored on the heading, because section 14 states three fenced literal
    blocks in the same shape and only one of them is the doctor registry.
    """

    lines = text.split("\n")
    start = lines.index(heading)
    opened = lines.index("```text", start) + 1
    end = lines.index("```", opened)
    return [tuple(line.split("=", 1)) for line in lines[opened:end]]


class FakeStream:
    def __init__(self, *, tty: bool, encoding: str = "utf-8"):
        self._tty = tty
        self.encoding = encoding

    def isatty(self) -> bool:
        return self._tty


class ResolveStyleTest(unittest.TestCase):
    def test_non_interactive_stream_gets_nothing(self):
        """Piped output must stay byte-identical to the lifecycle lines."""
        style = resolve_style(FakeStream(tty=False), {})
        self.assertFalse(style.enabled)

    def test_interactive_stream_gets_colour_and_unicode(self):
        style = resolve_style(FakeStream(tty=True), {})
        self.assertTrue(style.color)
        self.assertTrue(style.unicode)

    def test_no_color_suppresses_colour_but_keeps_the_tree(self):
        style = resolve_style(FakeStream(tty=True), {"NO_COLOR": "1"})
        self.assertFalse(style.color)
        self.assertTrue(style.unicode)

    def test_empty_no_color_value_still_counts(self):
        """no-color.org specifies presence, not truthiness."""
        style = resolve_style(FakeStream(tty=True), {"NO_COLOR": ""})
        self.assertFalse(style.color)

    def test_dumb_terminal_gets_nothing(self):
        style = resolve_style(FakeStream(tty=True), {"TERM": "dumb"})
        self.assertFalse(style.enabled)

    def test_ascii_terminal_keeps_colour_but_drops_box_drawing(self):
        style = resolve_style(FakeStream(tty=True, encoding="ascii"), {})
        self.assertTrue(style.color)
        self.assertFalse(style.unicode)

    def test_stream_without_isatty_is_treated_as_non_interactive(self):
        class Bare:
            encoding = "utf-8"

        self.assertFalse(resolve_style(Bare(), {}).enabled)


class PlainOutputContractTest(unittest.TestCase):
    """The machine-readable lines are a contract; rendering must not touch them."""

    def test_plain_style_returns_the_lines_untouched(self):
        self.assertEqual(
            DRY_RUN, format_init(DRY_RUN, project_root="/repo", apply=False, style=PLAIN)
        )

    def test_first_line_stays_the_documented_dry_run_marker(self):
        rendered = format_init(DRY_RUN, project_root="/repo", apply=False, style=PLAIN)
        self.assertEqual("dry-run: zero writes", rendered[0])

    def test_results_without_create_lines_are_never_reformatted(self):
        for lines in (
            ["no changes: /repo/.brichan is already healthy"],
            ["malformed: /repo/.brichan: manifest contains malformed JSON"],
        ):
            self.assertEqual(
                lines,
                format_init(lines, project_root="/repo", apply=False, style=FANCY),
                lines,
            )


class TreeRenderTest(unittest.TestCase):
    def render(self, lines=DRY_RUN, apply=False, style=Style(unicode=True)):
        return format_init(
            lines, project_root="/repo", apply=apply, style=style
        )

    def test_every_footprint_file_appears_exactly_once(self):
        text = "\n".join(self.render())
        for path in documented_footprint():
            leaf = path.rsplit("/", 1)[-1]
            self.assertEqual(text.count(leaf), 1, leaf)

    def test_directories_are_rendered_once_not_repeated_per_file(self):
        text = "\n".join(self.render())
        self.assertEqual(text.count("policy/"), 1)
        self.assertEqual(text.count("herdr-orchestration/"), 1)

    def test_last_child_uses_an_elbow_and_others_use_a_tee(self):
        text = "\n".join(self.render())
        self.assertIn("└── tasks.md", text)
        self.assertIn("├── manifest.json", text)

    def test_nesting_is_indented_under_its_parent(self):
        rendered = self.render()
        line = next(l for l in rendered if "model-routing.json" in l)
        self.assertIn("│   └── ", line)

    def test_subtitle_explains_the_directory_directly_under_the_header(self):
        rendered = self.render()
        self.assertEqual(f"  {INIT_SUBTITLE}", rendered[1])

    def test_subtitle_is_present_for_apply_too(self):
        self.assertIn(INIT_SUBTITLE, "\n".join(self.render(APPLIED, apply=True)))

    def test_subtitle_and_help_description_name_the_same_contents(self):
        """Two surfaces answering one question must not drift apart."""
        for topic in ("policy", "model routing", "Herdr skills", "project memory"):
            self.assertIn(topic, INIT_SUBTITLE, topic)
            self.assertIn(topic, INIT_DESCRIPTION, topic)

    def test_subtitle_stays_one_line(self):
        self.assertNotIn("\n", INIT_SUBTITLE)
        self.assertLessEqual(len(INIT_SUBTITLE), 79)

    def test_header_states_the_mode_and_the_target(self):
        self.assertIn("dry run", self.render()[0])
        self.assertIn("/repo", self.render()[0])
        self.assertIn("applied", self.render(APPLIED, apply=True)[0])

    def test_dry_run_footer_promises_no_writes_and_offers_the_next_step(self):
        text = "\n".join(self.render())
        self.assertIn("17 files", text)
        self.assertIn("zero writes", text)
        self.assertIn("brichan init --apply", text)

    def test_apply_footer_reports_creation_and_drops_the_hint(self):
        text = "\n".join(self.render(APPLIED, apply=True))
        self.assertIn("17 files created", text)
        self.assertNotIn("--apply", text)

    def test_single_file_is_not_pluralised(self):
        text = "\n".join(
            self.render(["dry-run: zero writes", "create .brichan/manifest.json"])
        )
        self.assertIn("1 file ", text + " ")
        self.assertNotIn("1 files", text)

    def test_ascii_style_avoids_box_drawing_characters(self):
        text = "\n".join(self.render(style=Style(color=True, unicode=False)))
        self.assertIn("|-- ", text)
        for glyph in ("├", "└", "│"):
            self.assertNotIn(glyph, text)

    def test_uncoloured_tree_emits_no_escape_sequences(self):
        text = "\n".join(self.render(style=Style(color=False, unicode=True)))
        self.assertNotIn("\033", text)

    def test_colour_changes_only_appearance_never_layout(self):
        """Stripping the escapes must reproduce the uncoloured tree exactly."""
        coloured = "\n".join(self.render(style=FANCY))
        stripped = re.sub(r"\033\[[0-9;]*m", "", coloured)
        self.assertEqual(
            "\n".join(self.render(style=Style(color=False, unicode=True))),
            stripped,
        )

    def test_every_opened_sequence_is_closed(self):
        text = "\n".join(self.render(style=FANCY))
        self.assertTrue(text.endswith("\033[0m"))
        # No reset may be emitted while nothing is open.
        depth = 0
        for code in re.findall(r"\033\[([0-9;]*)m", text):
            if code == "0":
                self.assertGreater(depth, 0, "reset with nothing open")
                depth = 0
            else:
                depth += 1
        self.assertEqual(0, depth, "unclosed escape sequence")


class RootEntryRenderTest(unittest.TestCase):
    """Root AGENTS.md/CLAUDE.md create lines must survive both render modes."""

    LINES = [
        "dry-run: zero writes",
        *FOOTPRINT,
        "create AGENTS.md",
        "create CLAUDE.md",
    ]

    def test_plain_style_returns_root_entry_lines_untouched(self):
        self.assertEqual(
            self.LINES,
            format_init(
                self.LINES, project_root="/repo", apply=False, style=PLAIN
            ),
        )

    def test_fancy_render_shows_root_entries_and_counts_them(self):
        text = "\n".join(
            format_init(
                self.LINES,
                project_root="/repo",
                apply=False,
                style=Style(unicode=True),
            )
        )
        self.assertIn("AGENTS.md", text)
        self.assertIn("CLAUDE.md", text)
        self.assertIn("19 files", text)

    def test_root_entries_alone_still_render_as_a_tree(self):
        lines = ["dry-run: zero writes", "create CLAUDE.md"]
        rendered = format_init(
            lines, project_root="/repo", apply=False, style=Style(unicode=True)
        )
        text = "\n".join(rendered)
        self.assertIn("CLAUDE.md", text)
        self.assertIn("1 file ", text + " ")


class LifecycleHelpTest(unittest.TestCase):
    """Each lifecycle command must say what it does, not just list its flags."""

    def _help(self, command: str) -> str:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as caught:
                runtime.main([command, "--help"])
        self.assertEqual(0, caught.exception.code)
        return " ".join(buffer.getvalue().split())

    def test_every_lifecycle_command_carries_its_description(self):
        for command, description in runtime.LIFECYCLE_DESCRIPTIONS.items():
            with self.subTest(command=command):
                self.assertIn(" ".join(description.split()), self._help(command))

    def test_no_lifecycle_command_is_left_undescribed(self):
        self.assertEqual({"init", "status", "doctor"}, set(runtime.LIFECYCLE_DESCRIPTIONS))

    def test_init_help_still_documents_every_flag(self):
        text = self._help("init")
        for flag in ("--project", "--apply", "--dry-run"):
            self.assertIn(flag, text, flag)
        self.assertNotIn("--init-agents", text)

    def test_status_description_names_every_state_and_exit_code(self):
        for state in ("uninitialized", "healthy", "malformed", "incompatible"):
            self.assertIn(state, STATUS_DESCRIPTION, state)
        for code in ("0", "1", "2", "3"):
            self.assertIn(code, STATUS_DESCRIPTION, code)

    def test_doctor_description_names_what_it_probes(self):
        for probe in ("codex", "herdr", ".brichan/"):
            self.assertIn(probe, DOCTOR_DESCRIPTION, probe)

    def test_read_only_commands_promise_not_to_write(self):
        for description in (STATUS_DESCRIPTION, DOCTOR_DESCRIPTION):
            self.assertIn("nothing is written", description.lower())


class DoctorJsonSerializationTest(unittest.TestCase):
    REPORT = {
        "schema_version": 1,
        "ok": True,
        "repository": {"kind": "source_checkout", "status": "ok"},
        "git": {"branch": "main", "dirty": False, "commit": None},
    }

    def test_serialization_is_sorted_indented_and_newline_terminated(self):
        text = format_doctor_json(self.REPORT)
        self.assertEqual(
            "{\n"
            '  "git": {\n'
            '    "branch": "main",\n'
            '    "commit": null,\n'
            '    "dirty": false\n'
            "  },\n"
            '  "ok": true,\n'
            '  "repository": {\n'
            '    "kind": "source_checkout",\n'
            '    "status": "ok"\n'
            "  },\n"
            '  "schema_version": 1\n'
            "}\n",
            text,
        )
        self.assertTrue(text.endswith("}\n"))
        self.assertFalse(text.endswith("}\n\n"))
        self.assertEqual(self.REPORT, json.loads(text))

    def test_serialization_is_byte_stable_across_key_insertion_order(self):
        shuffled = dict(reversed(list(self.REPORT.items())))
        self.assertEqual(
            format_doctor_json(self.REPORT).encode("utf-8"),
            format_doctor_json(shuffled).encode("utf-8"),
        )

    def test_doctor_json_flag_is_documented_as_a_single_stdout_document(self):
        self.assertIn("JSON", DOCTOR_JSON_HELP)
        self.assertIn("stdout", DOCTOR_JSON_HELP)


class DoctorTextRenderingTest(unittest.TestCase):
    REPORT = {
        "ok": True,
        "repository": {"root": "/repo", "status": "ok", "kind": "source_checkout"},
        "git": {
            "status": "ok",
            "dirty": False,
            "branch": "main",
            "commit": "1234567890abcdef",
            "untracked": False,
        },
        "policies": {
            "status": "ok",
            "detail": "all policy files present",
            "files": {
                "docs/policy/identity.md": {"status": "ok"},
                "docs/policy/operating-principles.md": {"status": "ok"},
            },
        },
        "model_routing": {"status": "ok", "detail": "valid"},
        "project_memory": {"status": "ok", "detail": "valid"},
        "agent_skill_export": {
            "status": "ok",
            "mode": "installed",
            "relation": "current",
            "path": EXPORTED_SKILL_PATH,
            "managed_path": MANAGED_SKILL_PATH,
            "files": [],
            "detail_code": "EXPORT_CURRENT",
            "detail": "managed and exported skill files are current",
        },
        "dependencies": {
            "status": "ok",
            "python": {"status": "ok", "required": True},
            "git": {"status": "ok", "required": True},
            "codex": {"status": "ok", "required": True},
            "herdr": {"status": "missing", "required": True},
        },
    }

    def test_text_is_a_compact_operator_summary(self):
        text = "\n".join(format_doctor_text(self.REPORT, PLAIN))
        self.assertIn("BRICHAN DOCTOR", text)
        self.assertIn("+", text)
        self.assertIn(".", text)
        self.assertIn("repository: OK", text)
        self.assertIn("source checkout", text)
        self.assertIn("git: OK · clean worktree · main", text)
        self.assertIn("commit 1234567", text)
        self.assertIn("no untracked", text)
        self.assertIn("- python: OK · required", text)
        self.assertIn("- herdr: MISSING · required", text)
        self.assertNotIn("all policy files present", text)
        self.assertIn("- docs/policy/identity.md", text)
        self.assertIn("overall: OK · healthy", text)

    def test_text_lists_configured_route_models(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model-routing.json"
            path.write_text(
                json.dumps(
                    {
                        "routes": {
                            "plan": {"model": "claude-fable-5"},
                            "implement": {"model": "claude-opus-5"},
                        }
                    }
                ),
                encoding="utf-8",
            )
            report = dict(self.REPORT)
            report["model_routing"] = {"status": "ok", "path": str(path)}
            text = "\n".join(format_doctor_text(report, PLAIN))
        self.assertIn("- claude-fable-5 — planning (plan)", text)
        self.assertIn("- claude-opus-5 — implementation (implement)", text)

    def test_failed_checks_show_only_the_actionable_detail(self):
        report = dict(self.REPORT)
        report["policies"] = {
            "status": "missing",
            "detail": "unhealthy policy paths: docs/policy/identity.md",
        }
        report["ok"] = False
        text = "\n".join(format_doctor_text(report, PLAIN))
        self.assertIn("policies: MISSING", text)
        self.assertIn("identity.md", text)
        self.assertIn("overall: INVALID · needs attention", text)

    def test_interactive_text_uses_colour_and_unicode(self):
        text = "\n".join(format_doctor_text(self.REPORT, FANCY))
        self.assertIn("\033[", text)
        self.assertIn("✓", text)
        self.assertIn("┌", text)
        self.assertIn("·", text)


class AgentSkillExportTextTest(unittest.TestCase):
    """Design section 16's export block is one frozen byte contract."""

    def base(self, export: dict, root: str = EXPORT_ROOT) -> dict:
        """The section-16 fixture base: everything but the export is healthy."""

        return {
            "ok": export["status"] == "ok",
            "repository": {
                "root": root,
                "status": "ok",
                "kind": "source_checkout",
            },
            "git": {
                "status": "ok",
                "dirty": False,
                "branch": "main",
                "commit": "1234567890abcdef",
                "untracked": False,
            },
            "policies": {
                "status": "ok",
                "detail": "all policy files present",
                "files": {
                    "docs/policy/identity.md": {"status": "ok"},
                    "docs/policy/operating-principles.md": {"status": "ok"},
                },
            },
            "model_routing": {"status": "ok", "detail": "valid"},
            "project_memory": {"status": "ok", "detail": "valid"},
            "agent_skill_export": export,
            "dependencies": {
                "status": "ok",
                "python": {"status": "ok", "required": True},
                "git": {"status": "ok", "required": True},
                "codex": {"status": "ok", "required": True},
                "herdr": {"status": "ok", "required": True},
            },
        }

    def section(self, code: str, root: str = EXPORT_ROOT) -> dict:
        detail = dict(AGENT_SKILL_EXPORT_DETAILS)[code]
        status, relation, nonnull, _ = AGENT_SKILL_EXPORT_ROWS[code]
        managed = f"{root}/.brichan/skills/herdr-orchestration"
        exported = f"{root}/.agents/skills/herdr-orchestration"
        return {
            "status": status,
            "mode": (
                "source_checkout"
                if code == "SOURCE_CHECKOUT_NOT_APPLICABLE"
                else "installed"
            ),
            "relation": relation,
            "path": exported if nonnull else None,
            "managed_path": managed if nonnull else None,
            "files": [],
            "detail_code": code,
            "detail": detail,
        }

    def render(self, code: str, root: str = EXPORT_ROOT) -> str:
        rows = format_doctor_text(self.base(self.section(code, root), root), PLAIN)
        return "\n".join(rows) + "\n"

    # -- registries -------------------------------------------------------

    def test_both_registries_list_the_same_27_codes_in_the_same_order(self):
        """Sections 9, 14, and 16 and the module are one registry.

        All three tables are the design's own blocks, committed as fixtures, so
        this compares the module to the authority rather than to a second copy
        of itself.
        """

        codes = [code for code, _ in AGENT_SKILL_EXPORT_DETAILS]
        self.assertEqual(27, len(codes))
        self.assertEqual(27, len(set(codes)))
        self.assertEqual(codes, list(AGENT_SKILL_EXPORT_ROWS))
        self.assertEqual(sorted(codes), sorted(DOCTOR_V2_TEXT))
        self.assertEqual("SOURCE_CHECKOUT_NOT_APPLICABLE", codes[0])
        self.assertEqual("OUTPUT_PATH_BYTE_LIMIT", codes[1])
        # The three version-9 rows, at the positions section 9 forces.
        self.assertEqual("OUTPUT_PATH_NOT_CANONICAL", codes[2])
        self.assertEqual("RESOURCE_LIMIT", codes[7])
        self.assertEqual("SKILL_ENTRY_NAME_BYTE_LIMIT", codes[12])
        self.assertEqual("SKILL_ENTRY_NAME_INVALID", codes[13])
        self.assertEqual("EXPORT_CURRENT", codes[-1])

        registry = [
            (code.strip("`"), detail.strip("`"))
            for code, detail in design_table(
                SECTION_9_REGISTRY.read_text(encoding="utf-8"), SECTION_9_HEADER
            )
        ]
        frozen = design_detail_block(
            SECTION_14_BLOCK.read_text(encoding="utf-8"), SECTION_14_HEADING
        )
        cross_product = design_table(
            SECTION_16_ROWS.read_text(encoding="utf-8"), SECTION_16_HEADER
        )
        self.assertEqual(27, len(registry))
        self.assertEqual(27, len(frozen))
        self.assertEqual(27, len(cross_product))
        # Section 9's order, section 14's order, section 16's order, and the
        # module's order.
        self.assertEqual(
            [code for code, _ in registry],
            [row[0].strip("`") for row in cross_product],
        )
        self.assertEqual(
            [code for code, _ in registry], [code for code, _ in frozen]
        )
        self.assertEqual(codes, [code for code, _ in registry])
        # Section 9's exact sentences, section 14's exact sentences, and the
        # module's: byte-equal across all three, not only the codes and order.
        self.assertEqual(list(AGENT_SKILL_EXPORT_DETAILS), registry)
        self.assertEqual(registry, frozen)
        self.assertEqual(list(AGENT_SKILL_EXPORT_DETAILS), frozen)
        # Section 16's status, relation, path nullability, and files rule.
        expected = {}
        for code, status_relation, path, managed_path, files in cross_product:
            self.assertEqual(path, managed_path, code)
            status, relation = status_relation.strip("`").split("/", 1)
            expected[code.strip("`")] = (
                status,
                relation,
                path == "nonnull",
                files.startswith("complete"),
            )
        self.assertEqual(expected, dict(AGENT_SKILL_EXPORT_ROWS))

    def test_every_detail_is_one_to_128_utf8_bytes(self):
        for code, detail in AGENT_SKILL_EXPORT_DETAILS:
            with self.subTest(code=code):
                self.assertTrue(1 <= len(code.encode("utf-8")) <= 64)
                self.assertTrue(code.isascii())
                self.assertTrue(1 <= len(detail.encode("utf-8")) <= 128)

    # -- frozen bytes -----------------------------------------------------

    def test_every_detail_code_renders_its_frozen_fixture_bytes(self):
        for code, _ in AGENT_SKILL_EXPORT_DETAILS:
            with self.subTest(code=code):
                self.assertEqual(DOCTOR_V2_TEXT[code], self.render(code))

    def test_the_three_version_9_blocks_reproduce_design_section_16(self):
        """Their four rendered lines are copied from the design, not derived."""

        lines = SECTION_16_VERSION_9_BLOCKS.read_text(encoding="utf-8").split("\n")
        for code in (
            "OUTPUT_PATH_NOT_CANONICAL",
            "RESOURCE_LIMIT",
            "SKILL_ENTRY_NAME_BYTE_LIMIT",
        ):
            with self.subTest(code=code):
                start = lines.index(f"`{code}`:")
                opened = lines.index("```text", start) + 1
                end = lines.index("```", opened)
                block = "\n".join(lines[opened:end])
                self.assertEqual(4, end - opened)
                self.assertIn(f"{block}\n", DOCTOR_V2_TEXT[code])
                self.assertIn(f"{block}\n", self.render(code))

    def test_the_callout_border_and_padding_stay_invariant(self):
        for code, text in DOCTOR_V2_TEXT.items():
            with self.subTest(code=code):
                lines = text.split("\n")
                self.assertEqual("+" + "." * 21 + "+", lines[0])
                self.assertEqual("+" + "." * 21 + "+", lines[3])
                self.assertEqual("| BRICHAN DOCTOR      |", lines[1])
                self.assertEqual("| project root: /repo |", lines[2])
                self.assertTrue(text.endswith("\n"))
                self.assertFalse(text.endswith("\n\n"))

    def test_only_the_export_block_and_overall_line_vary(self):
        """Every other byte of the section-16 template is invariant."""

        def stripped(text: str) -> list[str]:
            return [
                line
                for line in text.rstrip("\n").split("\n")
                if "agent skill export" not in line
                and not line.startswith("    detail: ")
                and not line.startswith("    managed: ")
                and not line.startswith("    exported: ")
                and not line.startswith("    re-export: ")
                and not line.startswith("    verify: ")
                and not line.startswith("overall: ")
            ]

        invariant = stripped(DOCTOR_V2_TEXT["EXPORT_CURRENT"])
        # The pre-export template is 19 rows; only `overall:` is dropped here.
        self.assertEqual(18, len(invariant))
        for code, text in DOCTOR_V2_TEXT.items():
            with self.subTest(code=code):
                self.assertEqual(invariant, stripped(text))

    def test_no_fixture_encodes_the_superseded_one_line_form(self):
        """Version 6's `agent skill export: <STATUS> — <detail>` is dead."""

        for code, text in DOCTOR_V2_TEXT.items():
            with self.subTest(code=code):
                label = next(
                    line for line in text.split("\n") if "agent skill export" in line
                )
                self.assertNotIn("—", label)
                self.assertNotIn(" · ", label)
                self.assertRegex(label, r"^\[(ok|!)\] agent skill export: [A-Z]+$")
                self.assertIn("\n    detail: ", text)

    def test_no_fixture_leaves_an_angle_bracket_or_placeholder(self):
        for code, text in DOCTOR_V2_TEXT.items():
            with self.subTest(code=code):
                self.assertNotIn("<", text)
                self.assertNotIn(">", text)
                self.assertNotIn("PATH", text)

    def test_the_block_sits_between_project_memory_and_dependencies(self):
        for code, text in DOCTOR_V2_TEXT.items():
            with self.subTest(code=code):
                lines = text.split("\n")
                memory = lines.index("[ok] project memory: OK")
                label = next(
                    index
                    for index, line in enumerate(lines)
                    if "agent skill export" in line
                )
                dependencies = lines.index("[ok] dependencies: OK")
                self.assertEqual(memory + 1, label)
                self.assertLess(label, dependencies)
                self.assertNotIn("", lines[memory + 1 : dependencies])

    def test_the_mark_and_overall_line_follow_the_export_status(self):
        for code, _ in AGENT_SKILL_EXPORT_DETAILS:
            with self.subTest(code=code):
                status = AGENT_SKILL_EXPORT_ROWS[code][0]
                text = DOCTOR_V2_TEXT[code]
                if status == "ok":
                    self.assertIn("[ok] agent skill export: OK\n", text)
                    self.assertTrue(text.endswith("overall: OK · healthy\n"))
                else:
                    self.assertIn(
                        f"[!] agent skill export: {status.upper()}\n", text
                    )
                    self.assertTrue(
                        text.endswith("overall: INVALID · needs attention\n")
                    )

    def test_null_paths_belong_to_exactly_three_rows(self):
        null_rows = {
            code
            for code, text in DOCTOR_V2_TEXT.items()
            if "    managed: null\n" in text
        }
        self.assertEqual(
            {
                "SOURCE_CHECKOUT_NOT_APPLICABLE",
                "OUTPUT_PATH_BYTE_LIMIT",
                "OUTPUT_PATH_NOT_CANONICAL",
            },
            null_rows,
        )
        for code in null_rows:
            self.assertIn("    exported: null\n", DOCTOR_V2_TEXT[code])
        for code, text in DOCTOR_V2_TEXT.items():
            if code in null_rows:
                continue
            with self.subTest(code=code):
                self.assertIn(f"    managed: {MANAGED_SKILL_PATH}\n", text)
                self.assertIn(f"    exported: {EXPORTED_SKILL_PATH}\n", text)

    # -- commands ---------------------------------------------------------

    def test_only_the_three_actionable_relations_render_commands(self):
        with_commands = {
            code
            for code, text in DOCTOR_V2_TEXT.items()
            if "    re-export: " in text
        }
        self.assertEqual(
            {"EXPORT_EXTRA", "EXPORT_STALE", "EXPORT_MISSING"}, with_commands
        )
        self.assertEqual(
            set(render.EXPORT_COMMAND_CODES),
            with_commands,
        )
        for code in with_commands:
            text = DOCTOR_V2_TEXT[code]
            self.assertIn(
                "    re-export: brichan init --apply --project /repo\n"
                "    verify: brichan doctor --json --project /repo\n",
                text,
            )

    def test_doctor_renders_no_backup_or_removal_command(self):
        for code, text in DOCTOR_V2_TEXT.items():
            with self.subTest(code=code):
                for forbidden in ("backup", "rm ", "remove", "mv ", "cp "):
                    self.assertNotIn(forbidden, text, forbidden)

    def test_roots_with_spaces_quotes_and_leading_dashes_are_shell_quoted(self):
        for root, quoted in (
            ("/tmp/a repo", "'/tmp/a repo'"),
            ("/tmp/it's", "'/tmp/it'\"'\"'s'"),
            # `shlex.quote` leaves a leading-dash component unquoted because it
            # carries no shell metacharacter; `--project` still takes it as the
            # value of the preceding flag.
            ("/tmp/-dash", "/tmp/-dash"),
        ):
            with self.subTest(root=root):
                text = self.render("EXPORT_STALE", root)
                self.assertIn(
                    f"    re-export: brichan init --apply --project {quoted}\n", text
                )
                self.assertIn(
                    f"    verify: brichan doctor --json --project {quoted}\n", text
                )
                if quoted != root:
                    self.assertNotIn(f"--project {root}\n", text)
                self.assertEqual(quoted, shlex.quote(root))

    def test_a_plain_root_is_never_gratuitously_quoted(self):
        self.assertIn(
            "    re-export: brichan init --apply --project /repo\n",
            self.render("EXPORT_MISSING"),
        )

    # -- styling ----------------------------------------------------------

    def test_colour_wraps_only_the_status_token(self):
        for code, _ in AGENT_SKILL_EXPORT_DETAILS:
            with self.subTest(code=code):
                report = self.base(self.section(code))
                coloured = "\n".join(
                    format_doctor_text(report, Style(color=True, unicode=False))
                )
                stripped = re.sub(r"\033\[[0-9;]*m", "", coloured)
                self.assertEqual(
                    "\n".join(format_doctor_text(report, PLAIN)), stripped
                )


if __name__ == "__main__":
    unittest.main()
