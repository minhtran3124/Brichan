"""Byte-exact `brichan techstacks` subprocess vectors.

Every case here runs the real launcher against a real disposable Git root and
asserts complete stdout and stderr bytes, not substrings or patterns. Access
counters for the platform predicate, the root anchor, the JSON file, the model
adapter, and the resolver are collected by running the dispatcher in-process
with named production hooks, because a subprocess cannot report them.
"""

import contextlib
import datetime
import errno
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from brichan.techstacks import cli, filesystem as fs, model
from brichan.techstacks.resolver import resolve_context

from tests.unit.test_techstack_resolver import (
    AS_OF,
    ATTEMPT_ID,
    PLAN_ID,
    PLAN_VERSION,
    TASK_ID,
    canonical_temporary_directory,
    leaf_source,
    map_source,
)


LAUNCHER = ROOT / "bin" / "brichan"
SNAPSHOT_DIRECTORY = f"projects/brida-installable-tool/handoffs/{TASK_ID}/snapshots"

#: One shell-metacharacter-bearing argument reused wherever a case must prove
#: that no untrusted token reaches a stream.
MALICIOUS = "; rm -rf / #$(whoami)`id`\n--project-root"

INPUT_OBJECT = {
    "task_id": TASK_ID,
    "plan_id": PLAN_ID,
    "plan_version": PLAN_VERSION,
    "attempt_id": ATTEMPT_ID,
    "as_of": AS_OF,
    "scope_paths": [],
    "context_chains": [],
    "exception_approvals": [],
    "declared_conflicts": [],
}


class TechstackCliTestCase(unittest.TestCase):
    """One disposable Git root and one real launcher invocation per call."""

    def setUp(self):
        fs.HELPER_CONTROLLER.reset_for_test()
        self.base = canonical_temporary_directory()
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.root = self.base / "project"
        self.root.mkdir()
        (self.root / ".git").mkdir()
        self.write("input.json", json.dumps(INPUT_OBJECT, indent=2) + "\n")

    def write(self, relative, data):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            data = data.encode("utf-8")
        target.write_bytes(data)
        return target

    def write_fixture(self, statement="Keep project context bounded."):
        self.write(
            "techstacks/README.md",
            map_source(
                [("general", "techstacks/general.md", (".",))],
                title="Base techstack map",
            ),
        )
        self.write(
            "techstacks/general.md",
            leaf_source(
                "general",
                [("GENERAL-001", statement)],
                title="General rules",
            ),
        )

    def run_cli(self, *arguments, launcher=LAUNCHER, cwd=None):
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [str(launcher), "techstacks", *arguments],
            cwd=str(ROOT if cwd is None else cwd),
            env=environment,
            check=False,
            capture_output=True,
        )

    def assert_usage(self, line, *arguments):
        result = self.run_cli(*arguments)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual(b"", result.stdout)
        self.assertEqual(line.encode("utf-8"), result.stderr)
        return result

    def resolve_arguments(self, *extra):
        return ("resolve", "--project-root", str(self.root), "--input-json", "input.json", *extra)

    def verify_arguments(self, snapshot_json, as_of=AS_OF):
        return (
            "verify",
            "--project-root",
            str(self.root),
            "--snapshot-json",
            snapshot_json,
            "--as-of",
            as_of,
        )

    def tree_digest(self):
        """Hash every regular file under the root, so a read-only claim is provable."""

        rows = []
        for path in sorted(self.root.rglob("*")):
            if path.is_file() and not path.is_symlink():
                rows.append((str(path.relative_to(self.root)), path.read_bytes()))
        return model.sha256_hex(model.canonical_json_text(
            [[name, model.sha256_hex(data)] for name, data in rows]
        ).encode("utf-8"))


# ---------------------------------------------------------------------------
# Frozen help and precedence
# ---------------------------------------------------------------------------


class HelpTest(TechstackCliTestCase):
    def test_the_three_help_documents_are_byte_exact_on_stdout(self):
        for arguments, expected in (
            (("--help",), cli.TOP_LEVEL_HELP),
            (("-h",), cli.TOP_LEVEL_HELP),
            (("resolve", "--help"), cli.RESOLVE_HELP),
            (("resolve", "-h"), cli.RESOLVE_HELP),
            (("verify", "--help"), cli.VERIFY_HELP),
            (("verify", "-h"), cli.VERIFY_HELP),
        ):
            result = self.run_cli(*arguments)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(expected.encode("utf-8"), result.stdout, arguments)
            self.assertEqual(b"", result.stderr)

    def test_the_top_level_help_bytes_are_the_frozen_design_document(self):
        self.assertEqual(
            "usage: brichan techstacks {resolve,verify} ...\n"
            "\n"
            "Resolve or verify bounded project-owned techstack context.\n"
            "\n"
            "subcommands:\n"
            "  resolve  resolve context and optionally publish a Snapshot artifact\n"
            "  verify   verify a Snapshot artifact against the project\n",
            cli.TOP_LEVEL_HELP,
        )
        self.assertEqual(
            "usage: brichan techstacks resolve --project-root ABSOLUTE --input-json "
            "PROJECT_RELATIVE [--snapshot-directory PROJECT_RELATIVE]\n"
            "\n"
            "options:\n"
            "  --project-root ABSOLUTE\n"
            "  --input-json PROJECT_RELATIVE\n"
            "  --snapshot-directory PROJECT_RELATIVE\n"
            "  -h, --help\n",
            cli.RESOLVE_HELP,
        )
        self.assertEqual(
            "usage: brichan techstacks verify --project-root ABSOLUTE --snapshot-json "
            "PROJECT_RELATIVE --as-of YYYY-MM-DD\n"
            "\n"
            "options:\n"
            "  --project-root ABSOLUTE\n"
            "  --snapshot-json PROJECT_RELATIVE\n"
            "  --as-of YYYY-MM-DD\n"
            "  -h, --help\n",
            cli.VERIFY_HELP,
        )

    def test_help_combined_with_any_other_token_loses_to_ordinary_precedence(self):
        self.assert_usage(cli.UNKNOWN_ARGUMENT_LINE, "--help", "resolve")
        self.assert_usage(cli.UNKNOWN_ARGUMENT_LINE, "--help", MALICIOUS)
        self.assert_usage(cli.UNKNOWN_FLAG_LINE, "resolve", "--help", "--project-root", "/x")
        self.assert_usage(cli.UNKNOWN_FLAG_LINE, "verify", "-h", "--as-of", AS_OF)


class ExitTwoLineTest(TechstackCliTestCase):
    """Every literal Design section 2 exit-2 line, with no echoed token."""

    def test_missing_subcommand(self):
        self.assert_usage(cli.MISSING_SUBCOMMAND_LINE)

    def test_unknown_subcommand_and_extra_positional(self):
        self.assert_usage(cli.UNKNOWN_ARGUMENT_LINE, "explode")
        self.assert_usage(cli.UNKNOWN_ARGUMENT_LINE, MALICIOUS)
        result = self.assert_usage(
            cli.UNKNOWN_ARGUMENT_LINE, "resolve", "--project-root", "/x", MALICIOUS
        )
        self.assertNotIn(b"rm -rf", result.stderr)
        self.assertNotIn(b"whoami", result.stderr)

    def test_unknown_flag(self):
        self.assert_usage(cli.UNKNOWN_FLAG_LINE, "resolve", "--not-a-flag")
        # An unknown flag consumes no value, so a token after it is an extra
        # positional and the higher-ranked positional line wins.
        self.assert_usage(cli.UNKNOWN_ARGUMENT_LINE, "resolve", "--not-a-flag", "value")
        self.assert_usage(cli.UNKNOWN_FLAG_LINE, "resolve", "--project-root=/x")
        # `--input-json` is a resolve flag, so `verify` sees it as unknown.
        self.assert_usage(cli.UNKNOWN_FLAG_LINE, "verify", "--input-json")
        result = self.assert_usage(cli.UNKNOWN_FLAG_LINE, "resolve", "-" + MALICIOUS)
        self.assertNotIn(b"whoami", result.stderr)

    def test_duplicate_flag(self):
        self.assert_usage(
            cli.DUPLICATE_FLAG_LINE,
            "resolve",
            "--project-root",
            str(self.root),
            "--project-root",
            str(self.root),
            "--input-json",
            "input.json",
        )
        self.assert_usage(
            cli.DUPLICATE_FLAG_LINE,
            "verify",
            "--as-of",
            AS_OF,
            "--as-of",
            AS_OF,
            "--project-root",
            str(self.root),
            "--snapshot-json",
            "s.json",
        )

    def test_flag_missing_value(self):
        self.assert_usage(
            cli.MISSING_VALUE_LINE, "resolve", "--input-json", "input.json", "--project-root"
        )
        self.assert_usage(cli.MISSING_VALUE_LINE, "verify", "--as-of")

    def test_required_set_failure(self):
        self.assert_usage(cli.RESOLVE_MISSING_ARGUMENT_LINE, "resolve")
        self.assert_usage(
            cli.RESOLVE_MISSING_ARGUMENT_LINE, "resolve", "--project-root", str(self.root)
        )
        self.assert_usage(cli.VERIFY_MISSING_ARGUMENT_LINE, "verify")
        self.assert_usage(
            cli.VERIFY_MISSING_ARGUMENT_LINE,
            "verify",
            "--project-root",
            str(self.root),
            "--snapshot-json",
            "s.json",
        )

    def test_positional_precedes_unknown_flag_which_precedes_duplicate_and_value(self):
        self.assert_usage(
            cli.UNKNOWN_ARGUMENT_LINE, "resolve", "stray", "--bogus", "--project-root"
        )
        self.assert_usage(
            cli.UNKNOWN_FLAG_LINE,
            "resolve",
            "--bogus",
            "--project-root",
            "/a",
            "--project-root",
            "/b",
        )
        self.assert_usage(
            cli.DUPLICATE_FLAG_LINE,
            "resolve",
            "--project-root",
            "/a",
            "--project-root",
            "/b",
            "--input-json",
        )

    def test_root_lexical_and_anchor_failures_share_one_line(self):
        for value in (
            "relative/root",
            "/tmp/../tmp",
            "/tmp/",
            "~/project",
            str(self.base / "absent"),
            MALICIOUS,
        ):
            result = self.assert_usage(
                cli.PROJECT_ROOT_INVALID_LINE,
                "resolve",
                "--project-root",
                value,
                "--input-json",
                "input.json",
            )
            self.assertNotIn(b"whoami", result.stderr)
        # An existing directory that is not a top-level Git root.
        plain = self.base / "plain"
        plain.mkdir()
        self.assert_usage(
            cli.PROJECT_ROOT_INVALID_LINE,
            "resolve",
            "--project-root",
            str(plain),
            "--input-json",
            "input.json",
        )

    def test_input_json_path_type_and_race_failures(self):
        for value in ("/etc/passwd", "../outside.json", "./input.json", "a//b.json", ""):
            self.assert_usage(
                cli.INPUT_JSON_UNAVAILABLE_LINE, *self.resolve_arguments()[:-1], value
            )
        self.assert_usage(cli.INPUT_JSON_UNAVAILABLE_LINE, *self.resolve_arguments()[:-1], "absent.json")
        (self.root / "a-directory").mkdir()
        self.assert_usage(
            cli.INPUT_JSON_UNAVAILABLE_LINE, *self.resolve_arguments()[:-1], "a-directory"
        )
        os.mkfifo(self.root / "a-fifo")
        self.assert_usage(cli.INPUT_JSON_UNAVAILABLE_LINE, *self.resolve_arguments()[:-1], "a-fifo")
        (self.root / "a-link.json").symlink_to(self.root / "input.json")
        self.assert_usage(
            cli.INPUT_JSON_UNAVAILABLE_LINE, *self.resolve_arguments()[:-1], "a-link.json"
        )

    def test_input_json_byte_limit_at_the_exact_boundary(self):
        self.write("exact.json", b"{}" + b" " * (model.CLI_JSON_BYTE_LIMIT - 2))
        self.write("over.json", b"{}" + b" " * (model.CLI_JSON_BYTE_LIMIT - 1))
        self.assertEqual(131072, (self.root / "exact.json").stat().st_size)
        self.assertEqual(131073, (self.root / "over.json").stat().st_size)
        # Exactly 131,072 is read and reaches model validation; one more byte
        # is refused without parsing.
        self.assert_usage(cli.INVALID_INPUT_LINE, *self.resolve_arguments()[:-1], "exact.json")
        self.assert_usage(
            cli.INPUT_JSON_BYTE_LIMIT_LINE, *self.resolve_arguments()[:-1], "over.json"
        )

    def test_input_json_encoding_failures(self):
        self.write("bom.json", b"\xef\xbb\xbf{}")
        self.write("nul.json", b'{"a\x00": 1}')
        self.write("latin.json", b'{"a": "\xff"}')
        for name in ("bom.json", "nul.json", "latin.json"):
            self.assert_usage(cli.INPUT_JSON_ENCODING_LINE, *self.resolve_arguments()[:-1], name)

    def test_input_json_syntax_and_duplicate_key_failures(self):
        self.write("broken.json", "{")
        self.write("array.json", "[]")
        self.write("trailing.json", '{} {"second": 1}')
        self.write("scalar.json", "1")
        for name in ("broken.json", "array.json", "trailing.json", "scalar.json"):
            self.assert_usage(cli.INPUT_JSON_SYNTAX_LINE, *self.resolve_arguments()[:-1], name)
        self.write("dup.json", '{"a": 1, "a": 2}')
        self.write("nested-dup.json", '{"a": {"b": 1, "b": 2}}')
        for name in ("dup.json", "nested-dup.json"):
            self.assert_usage(
                cli.INPUT_JSON_DUPLICATE_KEY_LINE, *self.resolve_arguments()[:-1], name
            )

    def test_invalid_input_model(self):
        self.write("bad.json", json.dumps({**INPUT_OBJECT, "plan_version": 0}) + "\n")
        self.write("extra.json", json.dumps({**INPUT_OBJECT, "extra": 1}) + "\n")
        for name in ("bad.json", "extra.json"):
            self.assert_usage(cli.INVALID_INPUT_LINE, *self.resolve_arguments()[:-1], name)

    def test_snapshot_output_refused_for_every_unauthorized_directory(self):
        for value in (
            "snapshots",
            "/absolute/snapshots",
            "projects/Bad_Slug/handoffs/TECHSTACK-001/snapshots",
            f"projects/p/handoffs/{TASK_ID}/snapshots/nested",
            ".brichan/project-memory/techstack-snapshots",
            MALICIOUS,
        ):
            result = self.assert_usage(
                cli.SNAPSHOT_OUTPUT_REFUSED_LINE,
                *self.resolve_arguments("--snapshot-directory", value),
            )
            self.assertNotIn(b"whoami", result.stderr)

    def test_every_snapshot_json_surface_line(self):
        self.assert_usage(cli.SNAPSHOT_JSON_UNAVAILABLE_LINE, *self.verify_arguments("absent.json"))
        self.assert_usage(cli.SNAPSHOT_JSON_UNAVAILABLE_LINE, *self.verify_arguments("/etc/passwd"))
        self.write("over.json", b"{}" + b" " * (model.CLI_JSON_BYTE_LIMIT - 1))
        self.assert_usage(cli.SNAPSHOT_JSON_BYTE_LIMIT_LINE, *self.verify_arguments("over.json"))
        self.write("bom.json", b"\xef\xbb\xbf{}")
        self.assert_usage(cli.SNAPSHOT_JSON_ENCODING_LINE, *self.verify_arguments("bom.json"))
        self.write("array.json", "[]")
        self.assert_usage(cli.SNAPSHOT_JSON_SYNTAX_LINE, *self.verify_arguments("array.json"))
        self.write("dup.json", '{"a": 1, "a": 2}')
        self.assert_usage(cli.SNAPSHOT_JSON_DUPLICATE_KEY_LINE, *self.verify_arguments("dup.json"))
        self.write("empty.json", "{}")
        self.assert_usage(cli.INVALID_SNAPSHOT_LINE, *self.verify_arguments("empty.json"))

    def test_an_invalid_snapshot_digest_is_the_same_invalid_snapshot_line(self):
        self.write_fixture()
        published = self.publish()
        payload = json.loads((self.root / published["selected_artifact"]).read_bytes())
        payload["snapshot_sha256"] = "0" * 64
        self.write("forged.json", model.canonical_json_document(payload))
        self.assert_usage(cli.INVALID_SNAPSHOT_LINE, *self.verify_arguments("forged.json"))

    def publish(self):
        result = self.run_cli(
            *self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY)
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Valid outcomes and byte-identical targets
# ---------------------------------------------------------------------------


class ValidOutcomeTest(TechstackCliTestCase):
    def test_resolve_emits_the_api_canonical_bytes_with_one_terminal_lf(self):
        self.write_fixture()
        before = self.tree_digest()
        result = self.run_cli(*self.resolve_arguments())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(b"", result.stderr)
        expected = resolve_context(
            model.resolution_input_from_json_object(INPUT_OBJECT), self.root
        )
        document = model.canonical_json_document(expected.to_json_object())
        self.assertEqual(document.encode("utf-8"), result.stdout)
        self.assertTrue(result.stdout.endswith(b"}\n"))
        self.assertEqual(1, result.stdout.count(b"\n}\n"))
        self.assertEqual(before, self.tree_digest())

    def test_a_not_applicable_project_is_exit_zero_and_a_blocked_one_is_exit_five(self):
        result = self.run_cli(*self.resolve_arguments())
        self.assertEqual(0, result.returncode)
        self.assertEqual("not_applicable", json.loads(result.stdout)["status"])
        self.assertEqual(b"", result.stderr)
        self.write_fixture()
        self.write("techstacks/general.md", "# Not a leaf\n")
        result = self.run_cli(*self.resolve_arguments())
        self.assertEqual(5, result.returncode)
        self.assertEqual("blocked", json.loads(result.stdout)["status"])
        self.assertEqual(b"", result.stderr)

    def test_verify_is_exit_zero_for_match_and_five_for_drift_and_blocked(self):
        self.write_fixture()
        publication = json.loads(
            self.run_cli(
                *self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY)
            ).stdout
        )
        artifact = publication["selected_artifact"]
        before = self.tree_digest()
        result = self.run_cli(*self.verify_arguments(artifact))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(b"", result.stderr)
        self.assertEqual("match", json.loads(result.stdout)["status"])
        self.assertEqual(before, self.tree_digest())

        self.write_fixture(statement="Keep project context tightly bounded.")
        result = self.run_cli(*self.verify_arguments(artifact))
        self.assertEqual(5, result.returncode)
        self.assertEqual("drift", json.loads(result.stdout)["status"])
        self.assertEqual(b"", result.stderr)

        self.write("techstacks/general.md", "# Not a leaf\n")
        result = self.run_cli(*self.verify_arguments(artifact))
        self.assertEqual(5, result.returncode)
        self.assertEqual("blocked", json.loads(result.stdout)["status"])
        self.assertEqual(b"", result.stderr)

    def test_verify_output_is_exactly_the_api_document(self):
        self.write_fixture()
        publication = json.loads(
            self.run_cli(
                *self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY)
            ).stdout
        )
        artifact = publication["selected_artifact"]
        snapshot = model.snapshot_from_json_object(
            json.loads((self.root / artifact).read_bytes())
        )
        expected = cli.verify_snapshot(
            snapshot, self.root, datetime.date.fromisoformat(AS_OF)
        )
        result = self.run_cli(*self.verify_arguments(artifact))
        self.assertEqual(
            model.canonical_json_document(expected.to_json_object()).encode("utf-8"),
            result.stdout,
        )


class MalformedLeafAttributionTest(TechstackCliTestCase):
    """The attributed INVALID_LEAF detail, proven through the real launcher."""

    def test_resolve_on_a_malformed_leaf_freezes_its_exact_stdout_bytes(self):
        # The leaf is the valid fixture plus one trailing line, so the whole
        # document parses and the failure is the first unconsumed line -- 34,
        # not the 33 the last valid line carries. Every byte of stdout is
        # frozen here because the detail is the one resolve-document field
        # the line and rule attribution changes.
        self.write_fixture()
        leaf = (self.root / "techstacks" / "general.md").read_bytes()
        self.write("techstacks/general.md", leaf + b"trailing\n")
        before = self.tree_digest()
        result = self.run_cli(*self.resolve_arguments())
        self.assertEqual(5, result.returncode)
        self.assertEqual(b"", result.stderr)
        self.assertEqual(
            b'{\n'
            b'  "diagnostics": [\n'
            b'    {\n'
            b'      "code": "INVALID_LEAF",\n'
            b'      "context_id": null,\n'
            b'      "detail": "leaf bytes do not match the leaf grammar at line 34: '
            b'TRAILING_CONTENT",\n'
            b'      "path": "techstacks/general.md",\n'
            b'      "severity": "error",\n'
            b'      "waivable": false,\n'
            b'      "waived_by": null\n'
            b'    }\n'
            b'  ],\n'
            b'  "schema_version": 1,\n'
            b'  "snapshot": null,\n'
            b'  "status": "blocked"\n'
            b'}\n',
            result.stdout,
        )
        self.assertEqual(before, self.tree_digest())


class PublicationOutputTest(TechstackCliTestCase):
    """Frozen canonical publication outputs and immutable drift leftovers."""

    def publish(self, expect=0):
        result = self.run_cli(
            *self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY)
        )
        self.assertEqual(expect, result.returncode, result.stderr)
        self.assertEqual(b"", result.stderr)
        return json.loads(result.stdout), result.stdout

    def test_first_publish_then_identical_reuse_are_frozen_documents(self):
        self.write_fixture()
        first, first_bytes = self.publish()
        artifact = first["selected_artifact"]
        digest = first["selected_snapshot_sha256"]
        self.assertEqual(
            f"{SNAPSHOT_DIRECTORY}/{ATTEMPT_ID}-{digest}.snapshot.json", artifact
        )
        self.assertEqual(
            [
                {
                    "ordinal": 1,
                    "artifact_path": artifact,
                    "snapshot_sha256": digest,
                    "publication": "created",
                    "verification_status": "match",
                }
            ],
            first["attempts"],
        )
        self.assertEqual("published", first["status"])
        self.assertEqual(1, first["schema_version"])
        self.assertTrue(first_bytes.endswith(b"\n"))

        target = self.root / artifact
        identity = (target.stat().st_ino, target.stat().st_mtime_ns)
        second, second_bytes = self.publish()
        self.assertEqual("identical_existing", second["attempts"][0]["publication"])
        self.assertEqual(first_bytes.replace(b'"created"', b'"identical_existing"'), second_bytes)
        self.assertEqual(identity, (target.stat().st_ino, target.stat().st_mtime_ns))
        self.assertEqual(0o600, stat.S_IMODE(target.stat().st_mode))

    def test_a_not_applicable_publication_writes_nothing(self):
        publication, document = self.publish()
        self.assertEqual(
            {
                "schema_version": 1,
                "status": "not_applicable",
                "resolution": {
                    "schema_version": 1,
                    "status": "not_applicable",
                    "snapshot": None,
                    "diagnostics": [],
                },
                "attempts": [],
                "selected_artifact": None,
                "selected_snapshot_sha256": None,
            },
            publication,
        )
        self.assertEqual(
            model.canonical_json_document(publication).encode("utf-8"), document
        )
        self.assertFalse((self.root / "projects").exists())

    def test_a_blocked_publication_exits_five_and_writes_nothing(self):
        self.write_fixture()
        self.write("techstacks/general.md", "# Not a leaf\n")
        publication, _ = self.publish(expect=5)
        self.assertEqual("blocked", publication["status"])
        self.assertEqual([], publication["attempts"])
        self.assertFalse((self.root / "projects").exists())

    def test_observation_drift_exits_five_and_leaves_every_artifact_intact(self):
        self.write_fixture()
        # A CLI subprocess cannot be raced deterministically, so the three
        # drifting attempts are driven in-process against the same production
        # dispatcher; only the moment of the project change is scheduled.
        real = cli.verify_snapshot
        seen = []

        def spy(snapshot, project_root, as_of):
            seen.append(snapshot.snapshot_sha256)
            self.write_fixture(statement=f"Revision {len(seen)}.")
            return real(snapshot, project_root, as_of)

        out = io.StringIO()
        err = io.StringIO()
        with mock.patch.object(cli, "verify_snapshot", spy):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = cli.main(
                    list(self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY))
                )
        self.assertEqual(5, code)
        self.assertEqual("", err.getvalue())
        publication = json.loads(out.getvalue())
        self.assertEqual("observation_drift", publication["status"])
        self.assertIsNone(publication["selected_artifact"])
        self.assertIsNone(publication["selected_snapshot_sha256"])
        self.assertEqual(3, len(publication["attempts"]))
        for attempt in publication["attempts"]:
            target = self.root / attempt["artifact_path"]
            self.assertTrue(target.is_file(), attempt["artifact_path"])
            snapshot = model.snapshot_from_json_object(json.loads(target.read_bytes()))
            self.assertEqual(attempt["snapshot_sha256"], snapshot.snapshot_sha256)
            self.assertEqual(
                model.snapshot_document(snapshot).encode("utf-8"), target.read_bytes()
            )

    def test_the_published_artifact_is_the_only_packetable_pointer(self):
        self.write_fixture()
        publication, _ = self.publish()
        directory = self.root / SNAPSHOT_DIRECTORY
        self.assertEqual(
            [publication["selected_artifact"].rsplit("/", 1)[1]],
            sorted(item.name for item in directory.iterdir()),
        )
        self.assertLessEqual(
            (self.root / publication["selected_artifact"]).stat().st_size,
            model.SNAPSHOT_DOCUMENT_BYTE_LIMIT,
        )


# ---------------------------------------------------------------------------
# Precedence with access counters
# ---------------------------------------------------------------------------


class AccessCounterTest(TechstackCliTestCase):
    """Design section 16's two `--as-of` positions and the platform position."""

    def counted(self, arguments):
        """Run the production dispatcher in process, counting each surface."""

        counters = {"platform": 0, "root": 0, "file": 0, "model": 0, "resolver": 0}
        real_platform = fs.is_supported_platform
        real_root = fs.validate_and_open_git_root
        real_file = cli.read_project_file
        real_model = cli.snapshot_from_json_object
        real_resolver = cli.resolve_context

        def wrap(name, function):
            def wrapped(*arguments_, **keywords):
                counters[name] += 1
                return function(*arguments_, **keywords)

            return wrapped

        out = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch.object(fs, "is_supported_platform", wrap("platform", real_platform)),
            mock.patch.object(fs, "validate_and_open_git_root", wrap("root", real_root)),
            mock.patch.object(cli, "read_project_file", wrap("file", real_file)),
            mock.patch.object(cli, "snapshot_from_json_object", wrap("model", real_model)),
            mock.patch.object(cli, "resolve_context", wrap("resolver", real_resolver)),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = cli.main(list(arguments))
        return code, out.getvalue(), err.getvalue(), counters

    def published_artifact(self):
        self.write_fixture()
        result = self.run_cli(
            *self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY)
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)["selected_artifact"]

    def test_a_lexically_invalid_date_touches_no_platform_root_file_or_resolver(self):
        artifact = self.published_artifact()
        for value in ("2026-8-24", "2026-02-30", "not-a-date", "", "2026-08-24 ", "٢٠٢٦-٠٨-٢٤"):
            code, out, err, counters = self.counted(self.verify_arguments(artifact, value))
            self.assertEqual(2, code, value)
            self.assertEqual("", out)
            self.assertEqual(cli.INVALID_AS_OF_LINE, err)
            self.assertEqual(
                {"platform": 0, "root": 0, "file": 0, "model": 0, "resolver": 0},
                counters,
                value,
            )

    def test_lexical_root_and_snapshot_path_precede_the_lexical_date(self):
        code, out, err, counters = self.counted(
            (
                "verify",
                "--project-root",
                "relative",
                "--snapshot-json",
                "s.json",
                "--as-of",
                "nope",
            )
        )
        self.assertEqual(cli.PROJECT_ROOT_INVALID_LINE, err)
        self.assertEqual({"platform": 0, "root": 0, "file": 0, "model": 0, "resolver": 0}, counters)
        code, out, err, counters = self.counted(
            (
                "verify",
                "--project-root",
                str(self.root),
                "--snapshot-json",
                "/absolute.json",
                "--as-of",
                "nope",
            )
        )
        self.assertEqual(cli.SNAPSHOT_JSON_UNAVAILABLE_LINE, err)
        self.assertEqual({"platform": 0, "root": 0, "file": 0, "model": 0, "resolver": 0}, counters)

    def test_a_valid_but_unequal_date_is_compared_only_after_a_valid_snapshot(self):
        artifact = self.published_artifact()
        code, out, err, counters = self.counted(
            self.verify_arguments(artifact, "2026-08-25")
        )
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertEqual(cli.INVALID_AS_OF_LINE, err)
        # The Snapshot has been read and validated, and nothing has been
        # observed in the project.
        self.assertEqual(
            {"platform": 1, "root": 1, "file": 1, "model": 1, "resolver": 0}, counters
        )

    def test_every_earlier_snapshot_failure_precedes_the_date_mismatch(self):
        self.write_fixture()
        for name, contents, line, expected in (
            ("absent.json", None, cli.SNAPSHOT_JSON_UNAVAILABLE_LINE,
             {"platform": 1, "root": 1, "file": 1, "model": 0, "resolver": 0}),
            ("bom.json", b"\xef\xbb\xbf{}", cli.SNAPSHOT_JSON_ENCODING_LINE,
             {"platform": 1, "root": 1, "file": 1, "model": 0, "resolver": 0}),
            ("array.json", b"[]", cli.SNAPSHOT_JSON_SYNTAX_LINE,
             {"platform": 1, "root": 1, "file": 1, "model": 0, "resolver": 0}),
            ("dup.json", b'{"a": 1, "a": 2}', cli.SNAPSHOT_JSON_DUPLICATE_KEY_LINE,
             {"platform": 1, "root": 1, "file": 1, "model": 0, "resolver": 0}),
            ("empty.json", b"{}", cli.INVALID_SNAPSHOT_LINE,
             {"platform": 1, "root": 1, "file": 1, "model": 1, "resolver": 0}),
        ):
            if contents is not None:
                self.write(name, contents)
            code, out, err, counters = self.counted(
                self.verify_arguments(name, "2026-08-25")
            )
            self.assertEqual(2, code, name)
            self.assertEqual("", out, name)
            self.assertEqual(line, err, name)
            self.assertEqual(expected, counters, name)

    def test_a_bad_root_precedes_every_snapshot_and_date_state(self):
        code, out, err, counters = self.counted(
            (
                "verify",
                "--project-root",
                str(self.base / "absent"),
                "--snapshot-json",
                "s.json",
                "--as-of",
                "2026-08-25",
            )
        )
        self.assertEqual(cli.PROJECT_ROOT_INVALID_LINE, err)
        self.assertEqual(
            {"platform": 1, "root": 1, "file": 0, "model": 0, "resolver": 0}, counters
        )


class PlatformOrderingTest(TechstackCliTestCase):
    def test_the_platform_gate_sits_after_lexical_arguments_and_before_any_open(self):
        out = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch.object(fs, "is_supported_platform", return_value=False),
            mock.patch.object(fs, "validate_and_open_git_root") as anchor,
            mock.patch.object(cli, "read_project_file") as reader,
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = cli.main(list(self.resolve_arguments()))
        self.assertEqual(2, code)
        self.assertEqual("", out.getvalue())
        self.assertEqual(cli.UNSUPPORTED_PLATFORM_LINE, err.getvalue())
        anchor.assert_not_called()
        reader.assert_not_called()

    def test_a_lexical_failure_still_precedes_the_platform_gate(self):
        out = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch.object(fs, "is_supported_platform", return_value=False) as platform,
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = cli.main(["resolve", "--project-root", "relative", "--input-json", "i.json"])
        self.assertEqual(2, code)
        self.assertEqual(cli.PROJECT_ROOT_INVALID_LINE, err.getvalue())
        platform.assert_not_called()


class InternalErrorTest(TechstackCliTestCase):
    def test_an_unexpected_failure_is_exact_sanitized_exit_seventy(self):
        self.write_fixture()
        out = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch.object(
                cli, "resolve_context", side_effect=RuntimeError(MALICIOUS)
            ),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = cli.main(list(self.resolve_arguments()))
        self.assertEqual(70, code)
        self.assertEqual("", out.getvalue())
        self.assertEqual(
            "brichan techstacks: INTERNAL_ERROR: resolution failed\n", err.getvalue()
        )
        self.assertEqual(cli.INTERNAL_ERROR_LINE, err.getvalue())

    def test_an_interrupt_and_an_explicit_exit_are_neither_sanitized_nor_seventy(self):
        """Design section 2 reserves exit 70 for an unexpected internal failure."""

        self.write_fixture()
        for interrupt in (KeyboardInterrupt, SystemExit):
            out = io.StringIO()
            err = io.StringIO()
            with (
                mock.patch.object(cli, "resolve_context", side_effect=interrupt),
                contextlib.redirect_stdout(out),
                contextlib.redirect_stderr(err),
            ):
                with self.assertRaises(interrupt):
                    cli.main(list(self.resolve_arguments()))
            self.assertEqual("", out.getvalue(), interrupt)
            self.assertEqual("", err.getvalue(), interrupt)

    def test_an_over_cap_publication_emits_nothing_and_publishes_no_artifact(self):
        self.write_fixture()
        out = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch.object(model, "PUBLICATION_DOCUMENT_BYTE_LIMIT", 1),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = cli.main(
                list(self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY))
            )
        self.assertEqual(70, code)
        self.assertEqual("", out.getvalue())
        self.assertEqual(cli.INTERNAL_ERROR_LINE, err.getvalue())
        self.assertFalse((self.root / "projects").exists())


class RootReanchorTest(TechstackCliTestCase):
    """Design section 14 maps the root table at every anchor, not only the first.

    Each importable API anchors the root for itself, so a root defeated after
    the CLI's own anchor fails inside the API. A real writer removes the `.git`
    marker at exactly that point, which is what a racing writer, a permission
    change, or descriptor exhaustion would do; nothing is injected.
    """

    def defeat_root_before(self, name):
        """Patch one production hook to remove `.git` and then delegate."""

        real = getattr(cli, name)

        def hook(*arguments, **keywords):
            shutil.rmtree(self.root / ".git")
            return real(*arguments, **keywords)

        return mock.patch.object(cli, name, hook)

    def assert_root_invalid(self, arguments, hook):
        out = io.StringIO()
        err = io.StringIO()
        with hook, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(arguments))
        self.assertEqual(2, code)
        self.assertEqual("", out.getvalue())
        self.assertEqual(cli.PROJECT_ROOT_INVALID_LINE, err.getvalue())

    def test_a_root_defeated_before_the_resolver_anchor_is_the_frozen_line(self):
        self.write_fixture()
        self.assert_root_invalid(
            self.resolve_arguments(), self.defeat_root_before("resolve_context")
        )

    def test_a_root_defeated_before_a_publication_attempt_is_the_frozen_line(self):
        self.write_fixture()
        self.assert_root_invalid(
            self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY),
            self.defeat_root_before("resolve_context"),
        )
        self.assertFalse((self.root / "projects").exists())

    def test_a_root_defeated_before_the_artifact_anchor_is_the_frozen_line(self):
        self.write_fixture()
        self.assert_root_invalid(
            self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY),
            self.defeat_root_before("snapshot_document"),
        )
        self.assertFalse((self.root / "projects").exists())

    def test_a_root_defeated_before_the_verify_anchor_is_the_frozen_line(self):
        self.write_fixture()
        result = self.run_cli(
            *self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY)
        )
        self.assertEqual(0, result.returncode, result.stderr)
        artifact = json.loads(result.stdout)["selected_artifact"]
        self.assert_root_invalid(
            self.verify_arguments(artifact), self.defeat_root_before("resolve_context")
        )


class ArtifactWriteFaultTest(TechstackCliTestCase):
    """Design section 2's row is path/authority/collision, never disk failure."""

    def test_an_unwritable_artifact_directory_is_still_the_refusal_line(self):
        self.write_fixture()
        directory = self.root / SNAPSHOT_DIRECTORY
        directory.mkdir(parents=True)
        directory.chmod(0o500)
        self.addCleanup(directory.chmod, 0o700)
        result = self.run_cli(
            *self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY)
        )
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual(b"", result.stdout)
        self.assertEqual(cli.SNAPSHOT_OUTPUT_REFUSED_LINE.encode("utf-8"), result.stderr)

    def test_a_full_volume_is_an_internal_failure_not_an_unauthorized_directory(self):
        self.write_fixture()
        real_write = os.write

        def failing_write(descriptor, data):
            # Only the artifact document faults; every other write is real.
            if data.startswith(b"{"):
                raise OSError(errno.ENOSPC, "no space left on device")
            return real_write(descriptor, data)

        out = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch.object(os, "write", failing_write),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = cli.main(
                list(self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY))
            )
        self.assertEqual(70, code)
        self.assertEqual("", out.getvalue())
        self.assertEqual(cli.INTERNAL_ERROR_LINE, err.getvalue())

    def run_in_process_with_open_directory_seam(self, seam):
        """Run a publish in-process with ``filesystem.open_directory`` replaced."""

        out = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch.object(fs, "open_directory", seam),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = cli.main(
                list(self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY))
            )
        return code, out.getvalue(), err.getvalue()

    def assert_existing_ancestor_outcome_is_internal(self, outcome, errno_value):
        # Every ancestor already exists, so the fault reaches the first
        # ancestor-walk arm: an observation that is not NOT_FOUND.
        self.write_fixture()
        (self.root / SNAPSHOT_DIRECTORY).mkdir(parents=True)
        real_open = fs.open_directory

        def faulting_open(parent_fd, name):
            if name == "snapshots":
                return None, fs.Observation(code=outcome, errno_value=errno_value)
            return real_open(parent_fd, name)

        code, out, err = self.run_in_process_with_open_directory_seam(faulting_open)
        self.assertEqual(70, code)
        self.assertEqual("", out)
        self.assertEqual(cli.INTERNAL_ERROR_LINE, err)

    def assert_reopen_after_mkdir_outcome_is_internal(self, outcome, errno_value):
        # The leaf is missing, so the walk creates it and then re-opens it; the
        # fault is injected only on that re-open, the second ancestor-walk arm.
        self.write_fixture()
        real_open = fs.open_directory

        def faulting_reopen(parent_fd, name):
            descriptor, observed = real_open(parent_fd, name)
            if name == "snapshots" and descriptor is not None:
                os.close(descriptor)
                return None, fs.Observation(code=outcome, errno_value=errno_value)
            return descriptor, observed

        code, out, err = self.run_in_process_with_open_directory_seam(faulting_reopen)
        self.assertEqual(70, code)
        self.assertEqual("", out)
        self.assertEqual(cli.INTERNAL_ERROR_LINE, err)
        self.assertTrue((self.root / SNAPSHOT_DIRECTORY).is_dir())

    def test_an_io_error_on_an_existing_ancestor_is_an_internal_failure(self):
        self.assert_existing_ancestor_outcome_is_internal("FILESYSTEM_IO_ERROR", errno.EIO)

    def test_a_resource_limit_on_an_existing_ancestor_is_an_internal_failure(self):
        self.assert_existing_ancestor_outcome_is_internal("RESOURCE_LIMIT", errno.EMFILE)

    def test_an_io_error_reopening_a_created_ancestor_is_an_internal_failure(self):
        self.assert_reopen_after_mkdir_outcome_is_internal("FILESYSTEM_IO_ERROR", errno.ESTALE)

    def test_a_resource_limit_reopening_a_created_ancestor_is_an_internal_failure(self):
        self.assert_reopen_after_mkdir_outcome_is_internal("RESOURCE_LIMIT", errno.ENFILE)

    def test_an_authority_outcome_on_an_existing_ancestor_is_still_the_refusal(self):
        # A symlink ancestor is a genuine authority failure and keeps its line.
        self.write_fixture()
        (self.root / SNAPSHOT_DIRECTORY).mkdir(parents=True)
        real_open = fs.open_directory

        def rejecting_open(parent_fd, name):
            if name == "snapshots":
                return None, fs.Observation(code="SYMLINK_REJECTED", errno_value=errno.ELOOP)
            return real_open(parent_fd, name)

        code, out, err = self.run_in_process_with_open_directory_seam(rejecting_open)
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertEqual(cli.SNAPSHOT_OUTPUT_REFUSED_LINE, err)


class NonAsciiDateInputTest(TechstackCliTestCase):
    """A schema-invalid date is refused at the model on both resolve surfaces."""

    ARABIC_INDIC_AS_OF = "\u0662\u0660\u0662\u0666-\u0660\u0668-\u0660\u0661"

    def setUp(self):
        super().setUp()
        self.write_fixture()
        payload = dict(INPUT_OBJECT)
        payload["as_of"] = self.ARABIC_INDIC_AS_OF
        self.write("input.json", json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    def test_the_read_only_surface_refuses_a_non_ascii_as_of(self):
        self.assert_usage(cli.INVALID_INPUT_LINE, *self.resolve_arguments())

    def test_the_publish_surface_refuses_the_same_input_with_the_same_line(self):
        self.assert_usage(
            cli.INVALID_INPUT_LINE,
            *self.resolve_arguments("--snapshot-directory", SNAPSHOT_DIRECTORY),
        )
        self.assertFalse((self.root / "projects").exists())


class LauncherDispatchTest(TechstackCliTestCase):
    """Checkout and installed launcher dispatch stay mode-correct."""

    def test_the_checkout_launcher_reaches_the_techstacks_surface(self):
        result = self.run_cli("--help")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(cli.TOP_LEVEL_HELP.encode("utf-8"), result.stdout)

    def test_the_installed_console_entrypoint_reaches_the_same_surface(self):
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT / "src")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        outside = self.base / "outside"
        outside.mkdir()
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; from brichan.cli.runtime import main; "
                "raise SystemExit(main(sys.argv[1:]))",
                "techstacks",
                "--help",
            ],
            cwd=str(outside),
            env=environment,
            check=False,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(cli.TOP_LEVEL_HELP.encode("utf-8"), result.stdout)
        self.assertEqual(b"", result.stderr)

    def test_neither_mode_forwards_techstacks_to_a_provider_runtime(self):
        # `brichan techstacks ...` must never reach codex/claude, in either
        # mode, whatever the working directory.
        result = self.run_cli("resolve", cwd=self.root)
        self.assertEqual(2, result.returncode)
        self.assertEqual(cli.RESOLVE_MISSING_ARGUMENT_LINE.encode("utf-8"), result.stderr)


if __name__ == "__main__":
    unittest.main()
