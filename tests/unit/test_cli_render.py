import contextlib
import io
import json
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
from brichan.cli import runtime
from brichan.lifecycle import documented_footprint


FOOTPRINT = [f"create .brichan/{path}" for path in documented_footprint()]
DRY_RUN = ["dry-run: zero writes", *FOOTPRINT]
APPLIED = ["initialized: /repo/.brichan", *FOOTPRINT]

FANCY = Style(color=True, unicode=True)
PLAIN = Style(color=False, unicode=False)


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
        self.assertIn("15 files", text)
        self.assertIn("zero writes", text)
        self.assertIn("brichan init --apply", text)

    def test_apply_footer_reports_creation_and_drops_the_hint(self):
        text = "\n".join(self.render(APPLIED, apply=True))
        self.assertIn("15 files created", text)
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
        self.assertIn("17 files", text)

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


if __name__ == "__main__":
    unittest.main()
