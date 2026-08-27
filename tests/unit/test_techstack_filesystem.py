"""Platform predicate, no-symlink root anchor, and bounded reader behavior.

Every observation here is a bounded sequential observation. The tests prove
that a metadata-observed nonregular entry never reaches a content open, that
the frozen isolated launch contract is byte-exact, that a hostile ``brichan``
package cannot execute inside the bounded reader, and that the process-wide
controller never holds more than one launched or unreaped child.
"""

import ast
import errno
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from brichan.techstacks import filesystem as fs
from brichan.techstacks import model
from brichan.techstacks import safe_open_helper as helper


#: The exact Design section 16 frozen argv shape, copied literally.
FROZEN_INTERPRETER_OPTIONS = ("-I", "-S", "-B", "-X", "utf8=1")

#: The exact Design section 16 ``Popen`` keyword names, copied literally.
FROZEN_POPEN_KEYWORDS = (
    "shell",
    "stdin",
    "stdout",
    "stderr",
    "close_fds",
    "pass_fds",
    "cwd",
    "env",
)


def canonical_temporary_directory():
    """Return a temporary directory whose path contains no symlink.

    macOS places temporary directories under ``/var``, which is a symlink to
    ``/private/var``. The anchor never resolves a symlink itself, so the test
    supplies the already canonical path.
    """

    directory = tempfile.mkdtemp()
    return Path(os.path.realpath(directory))


class TemporaryRootMixin:
    def setUp(self):
        super().setUp()
        fs.HELPER_CONTROLLER.reset_for_test()
        self.base = canonical_temporary_directory()
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)

    def make_root(self, name="project", git="directory"):
        root = self.base / name
        root.mkdir()
        if git == "directory":
            (root / ".git").mkdir()
        elif git == "file":
            (root / ".git").write_text("gitdir: ../real\n", encoding="utf-8")
        elif git == "fifo":
            os.mkfifo(root / ".git")
        elif git == "symlink":
            (root / "target").mkdir()
            os.symlink(root / "target", root / ".git")
        return root


class RootAnchorTest(TemporaryRootMixin, unittest.TestCase):
    def anchor(self, path):
        handle = fs.validate_and_open_git_root(path)
        self.addCleanup(handle.close)
        return handle

    def assert_code(self, path, code):
        with self.assertRaises(model.TechstackInputError) as error:
            fs.validate_and_open_git_root(path)
        self.assertEqual(code, error.exception.code)
        self.assertEqual("project_root", error.exception.field)
        return error.exception

    def test_accepts_a_root_with_a_git_directory(self):
        root = self.make_root(git="directory")
        handle = self.anchor(root)
        info = os.stat(root)
        self.assertEqual(info.st_dev, handle.identity.device)
        self.assertEqual(info.st_ino, handle.identity.inode)
        self.assertEqual(str(root), handle.path)

    def test_accepts_a_root_with_a_regular_git_worktree_file(self):
        root = self.make_root(name="worktree", git="file")
        handle = self.anchor(root)
        self.assertGreaterEqual(handle.fd, 0)

    def test_missing_root_argument_is_a_python_type_error(self):
        with self.assertRaises(TypeError):
            fs.validate_and_open_git_root()

    def test_non_path_argument_is_a_root_type_error(self):
        root = self.make_root()
        self.assert_code(str(root), "PROJECT_ROOT_TYPE")

    def test_relative_root_is_rejected(self):
        self.assert_code(Path("project"), "PROJECT_ROOT_NOT_ABSOLUTE")

    def test_noncanonical_roots_are_rejected(self):
        root = self.make_root()
        for candidate in (
            Path(str(root) + "/.."),
            Path("/~/project"),
            Path("/tmp/" + "c" * 256),
        ):
            with self.subTest(candidate=str(candidate)):
                self.assert_code(candidate, "PROJECT_ROOT_NOT_CANONICAL")

    def test_lexical_forms_that_pathlib_normalizes_are_still_rejected(self):
        root = self.make_root(name="lexical")
        for raw in (
            str(root) + "/",
            "/tmp/./project",
            "/tmp//project",
            "/tmp/project/",
            "/tmp/pro\x00ject",
            "/tmp/" + "c" * 256 + "/project",
        ):
            with self.subTest(raw=raw):
                with mock.patch.object(fs.os, "fspath", lambda value, raw=raw: raw):
                    self.assert_code(root, "PROJECT_ROOT_NOT_CANONICAL")
        with mock.patch.object(fs.os, "fspath", lambda value: ""):
            self.assert_code(root, "PROJECT_ROOT_BYTE_LIMIT")
        with mock.patch.object(fs.os, "fspath", lambda value: b"/tmp/project"):
            self.assert_code(root, "PROJECT_ROOT_TYPE")

    def test_non_nfc_root_is_rejected(self):
        self.assert_code(Path("/tmp/café"), "PROJECT_ROOT_NOT_CANONICAL")

    def test_root_byte_bounds(self):
        self.assert_code(Path("/" + "c" * 250 + "/" + "d" * 250), "PROJECT_NOT_GIT_ROOT")
        overlong = "/" + "/".join(["c" * 250] * 13)
        self.assertGreater(len(overlong.encode("utf-8")), model.PROJECT_ROOT_BYTE_MAX)
        self.assert_code(Path(overlong), "PROJECT_ROOT_BYTE_LIMIT")

    def test_symlinked_root_ancestor_and_git_are_rejected(self):
        root = self.make_root()
        link = self.base / "link"
        os.symlink(root, link)
        self.assert_code(link, "PROJECT_ROOT_SYMLINK")
        nested = self.base / "outer"
        nested.mkdir()
        inner = nested / "inner"
        inner.mkdir()
        (inner / ".git").mkdir()
        outer_link = self.base / "outer-link"
        os.symlink(nested, outer_link)
        self.assert_code(outer_link / "inner", "PROJECT_ROOT_SYMLINK")
        symlinked_git = self.make_root(name="symlinked-git", git="symlink")
        self.assert_code(symlinked_git, "PROJECT_ROOT_SYMLINK")

    def test_non_directory_root_is_rejected(self):
        target = self.base / "file.txt"
        target.write_text("x", encoding="utf-8")
        self.assert_code(target, "PROJECT_ROOT_NOT_DIRECTORY")

    def test_root_without_git_is_rejected(self):
        plain = self.base / "plain"
        plain.mkdir()
        self.assert_code(plain, "PROJECT_NOT_GIT_ROOT")

    def test_git_of_an_unsupported_type_is_rejected(self):
        root = self.make_root(name="fifo-git", git="fifo")
        self.assert_code(root, "PROJECT_NOT_GIT_ROOT")

    def test_missing_root_path_is_not_a_git_root(self):
        self.assert_code(self.base / "absent", "PROJECT_NOT_GIT_ROOT")

    def test_no_ancestor_search_occurs(self):
        root = self.make_root()
        child = root / "package"
        child.mkdir()
        self.assert_code(child, "PROJECT_NOT_GIT_ROOT")

    @unittest.skipIf(os.geteuid() == 0, "root bypasses directory permissions")
    def test_unreadable_ancestor_is_reported(self):
        root = self.make_root(name="locked")
        os.chmod(root, 0o000)
        self.addCleanup(os.chmod, root, 0o755)
        self.assert_code(root, "PROJECT_ROOT_UNREADABLE")

    def test_root_identity_recheck_detects_a_swap(self):
        root = self.make_root(name="swap")
        handle = self.anchor(root)
        self.assertTrue(fs.root_identity_unchanged(handle))
        replacement = self.base / "replacement"
        replacement.mkdir()
        (replacement / ".git").mkdir()
        shutil.rmtree(root)
        os.rename(replacement, root)
        self.assertFalse(fs.root_identity_unchanged(handle))

    def test_errno_classes_map_to_their_exact_caller_codes(self):
        root = self.make_root(name="errno-root")
        cases = {
            errno.EACCES: "PROJECT_ROOT_UNREADABLE",
            errno.EPERM: "PROJECT_ROOT_UNREADABLE",
            errno.ESTALE: "PROJECT_ROOT_IO_ERROR",
            errno.EIO: "PROJECT_ROOT_IO_ERROR",
            errno.EMFILE: "PROJECT_ROOT_RESOURCE_LIMIT",
            errno.ENFILE: "PROJECT_ROOT_RESOURCE_LIMIT",
            errno.ENOMEM: "PROJECT_ROOT_RESOURCE_LIMIT",
            errno.EINVAL: "PROJECT_ROOT_UNSUPPORTED_SAFE_OPEN",
            errno.ENOTSUP: "PROJECT_ROOT_UNSUPPORTED_SAFE_OPEN",
            errno.ELOOP: "PROJECT_ROOT_SYMLINK",
            errno.ENOTDIR: "PROJECT_ROOT_NOT_DIRECTORY",
            errno.ENOENT: "PROJECT_NOT_GIT_ROOT",
            errno.ENXIO: "PROJECT_ROOT_FILESYSTEM_ERROR",
            # EISDIR has no Design section 3 root row, so it belongs to the
            # Design section 14 catch-all rather than to a code that would
            # assert the opposite of what the operating system reported.
            errno.EISDIR: "PROJECT_ROOT_FILESYSTEM_ERROR",
        }
        real_stat = os.stat
        for number, code in cases.items():
            with self.subTest(call="stat", errno=number):
                def failing_stat(path, *args, **keywords):
                    if path == ".git":
                        raise OSError(number, os.strerror(number))
                    return real_stat(path, *args, **keywords)

                with mock.patch.object(fs.os, "stat", failing_stat):
                    error = self.assert_code(root, code)
                if code == "PROJECT_ROOT_FILESYSTEM_ERROR":
                    self.assertEqual(
                        f"project root filesystem operation failed with errno {number}",
                        error.detail,
                    )

    def test_a_git_directory_that_cannot_be_opened_reports_its_errno_class(self):
        """The directory branch owns the same root codes as the file branch.

        The metadata call succeeds and the content-free directory ``os.open``
        fails, which is the only way a real ``.git`` directory reports an
        errno class at all.
        """

        root = self.make_root(name="open-errno-root")
        cases = {
            errno.EACCES: "PROJECT_ROOT_UNREADABLE",
            errno.EPERM: "PROJECT_ROOT_UNREADABLE",
            errno.ESTALE: "PROJECT_ROOT_IO_ERROR",
            errno.EIO: "PROJECT_ROOT_IO_ERROR",
            errno.EMFILE: "PROJECT_ROOT_RESOURCE_LIMIT",
            errno.ENFILE: "PROJECT_ROOT_RESOURCE_LIMIT",
            errno.ENOMEM: "PROJECT_ROOT_RESOURCE_LIMIT",
            errno.EINVAL: "PROJECT_ROOT_UNSUPPORTED_SAFE_OPEN",
            errno.ENOTSUP: "PROJECT_ROOT_UNSUPPORTED_SAFE_OPEN",
            errno.EOPNOTSUPP: "PROJECT_ROOT_UNSUPPORTED_SAFE_OPEN",
            errno.ELOOP: "PROJECT_ROOT_SYMLINK",
            errno.ENOENT: "PROJECT_NOT_GIT_ROOT",
        }
        details = {
            "PROJECT_ROOT_UNREADABLE": "project_root could not be read",
            "PROJECT_ROOT_IO_ERROR": "project_root filesystem I/O failed",
        }
        real_open = os.open
        for number, code in cases.items():
            with self.subTest(call="open", errno=number):
                def failing_open(path, *args, **keywords):
                    if path == fs.GIT_MARKER_NAME:
                        raise OSError(number, os.strerror(number))
                    return real_open(path, *args, **keywords)

                with mock.patch.object(fs.os, "open", failing_open):
                    error = self.assert_code(root, code)
                if code in details:
                    self.assertEqual(details[code], error.detail)

    @unittest.skipIf(os.geteuid() == 0, "root bypasses directory permissions")
    def test_an_unreadable_git_directory_is_reported_as_unreadable(self):
        root = self.make_root(name="locked-git")
        marker = root / ".git"
        os.chmod(marker, 0o000)
        self.addCleanup(os.chmod, marker, 0o755)
        error = self.assert_code(root, "PROJECT_ROOT_UNREADABLE")
        self.assertEqual("project_root could not be read", error.detail)


class PlatformPredicateTest(unittest.TestCase):
    def setUp(self):
        fs.HELPER_CONTROLLER.reset_for_test()

    def test_this_host_satisfies_every_predicate(self):
        self.assertEqual((), fs.failing_platform_predicates())
        self.assertTrue(fs.is_supported_platform())
        self.assertEqual(8, len(fs.PLATFORM_PREDICATES))

    def test_predicate_one_and_two_reject_other_platforms(self):
        with mock.patch.object(fs.os, "name", "nt"):
            self.assertIn(1, fs.failing_platform_predicates())
        with mock.patch.object(fs.sys, "platform", "win32"):
            self.assertIn(2, fs.failing_platform_predicates())
        with mock.patch.object(fs.sys, "platform", "darwin23"):
            self.assertNotIn(2, fs.failing_platform_predicates())

    def test_predicate_three_rejects_absent_or_zero_flags(self):
        for flag in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK"):
            with self.subTest(flag=flag):
                with mock.patch.object(fs.os, flag, 0):
                    self.assertIn(3, fs.failing_platform_predicates())

    def test_predicate_four_requires_descriptor_relative_capabilities(self):
        with mock.patch.object(fs.os, "supports_dir_fd", set()):
            self.assertIn(4, fs.failing_platform_predicates())
        with mock.patch.object(fs.os, "supports_follow_symlinks", set()):
            self.assertIn(4, fs.failing_platform_predicates())

    def test_predicate_five_requires_the_exact_callables(self):
        with mock.patch.object(fs.os, "read", None):
            self.assertIn(5, fs.failing_platform_predicates())
        with mock.patch.object(fs.subprocess, "TimeoutExpired", None):
            with mock.patch.object(fs, "hasattr", lambda *a: False, create=True):
                pass
        with mock.patch.object(fs.subprocess.Popen, "terminate", None):
            self.assertIn(5, fs.failing_platform_predicates())

    def test_predicate_six_requires_python_3_10(self):
        with mock.patch.object(fs.sys, "version_info", (3, 9, 18)):
            self.assertIn(6, fs.failing_platform_predicates())
        with mock.patch.object(fs.sys, "version_info", (3, 10, 0)):
            self.assertNotIn(6, fs.failing_platform_predicates())

    def test_predicate_seven_requires_a_regular_absolute_interpreter(self):
        with mock.patch.object(fs.sys, "executable", ""):
            self.assertIn(7, fs.failing_platform_predicates())
        with mock.patch.object(fs.sys, "executable", "python3"):
            self.assertIn(7, fs.failing_platform_predicates())
        with mock.patch.object(fs.sys, "executable", os.path.dirname(sys.executable)):
            self.assertIn(7, fs.failing_platform_predicates())

    def test_predicate_eight_fails_closed_for_a_missing_or_unsafe_helper(self):
        with mock.patch.object(fs.sys, "getfilesystemencoding", lambda: "ascii"):
            self.assertIn(8, fs.failing_platform_predicates())
        with mock.patch.object(fs, "_HELPER_PATH", "techstacks/safe_open_helper.py"):
            self.assertIn(8, fs.failing_platform_predicates())
        with tempfile.TemporaryDirectory() as temporary:
            missing = os.path.join(temporary, "safe_open_helper.py")
            with mock.patch.object(fs, "_HELPER_PATH", missing):
                self.assertIn(8, fs.failing_platform_predicates())
            directory = os.path.join(temporary, "as_directory")
            os.mkdir(directory)
            with mock.patch.object(fs, "_HELPER_PATH", directory):
                self.assertIn(8, fs.failing_platform_predicates())
            link = os.path.join(temporary, "linked_helper.py")
            os.symlink(fs._HELPER_PATH, link)
            with mock.patch.object(fs, "_HELPER_PATH", link):
                self.assertIn(8, fs.failing_platform_predicates())

    def test_no_predicate_probes_the_filesystem_beyond_owned_metadata(self):
        opened = []
        real_open = os.open

        def counting_open(path, *args, **keywords):
            opened.append(path)
            return real_open(path, *args, **keywords)

        with mock.patch.object(fs.os, "open", counting_open):
            fs.failing_platform_predicates()
        self.assertEqual([], opened)


class FrozenLaunchContractTest(TemporaryRootMixin, unittest.TestCase):
    def test_helper_path_is_the_file_beside_the_imported_module(self):
        self.assertEqual(os.path.dirname(fs.__file__), fs._HELPER_DIR)
        self.assertEqual(
            os.path.join(os.path.dirname(fs.__file__), "safe_open_helper.py"),
            fs._HELPER_PATH,
        )
        self.assertTrue(os.path.isabs(fs._HELPER_PATH))
        self.assertTrue(stat.S_ISREG(os.stat(fs._HELPER_PATH, follow_symlinks=False).st_mode))

    def test_frozen_argv_element_by_element(self):
        argv = fs.helper_argv(9, "README.md", "read", 65536)
        self.assertEqual(15, len(argv))
        self.assertEqual(sys.executable, argv[0])
        self.assertEqual(list(FROZEN_INTERPRETER_OPTIONS), argv[1:6])
        self.assertEqual(fs._HELPER_PATH, argv[6])
        self.assertEqual("--dir-fd", argv[7])
        self.assertEqual("9", argv[8])
        self.assertEqual("--name", argv[9])
        self.assertEqual("README.md", argv[10])
        self.assertEqual("--mode", argv[11])
        self.assertEqual("read", argv[12])
        self.assertEqual("--limit", argv[13])
        self.assertEqual("65536", argv[14])
        self.assertNotIn("-m", argv)
        validate = fs.helper_argv(9, ".git", "validate", 0)
        self.assertEqual(["--mode", "validate", "--limit", "0"], validate[11:])

    def test_frozen_popen_keyword_mapping(self):
        keywords = fs.helper_popen_keywords(9)
        self.assertEqual(set(FROZEN_POPEN_KEYWORDS), set(keywords))
        self.assertFalse(keywords["shell"])
        self.assertEqual(subprocess.DEVNULL, keywords["stdin"])
        self.assertEqual(subprocess.PIPE, keywords["stdout"])
        self.assertEqual(subprocess.PIPE, keywords["stderr"])
        self.assertTrue(keywords["close_fds"])
        self.assertEqual((9,), keywords["pass_fds"])
        self.assertEqual(fs._HELPER_DIR, keywords["cwd"])
        self.assertEqual({}, keywords["env"])

    def test_the_production_launch_uses_exactly_that_argv_and_keywords(self):
        root = self.make_root()
        (root / "note.md").write_text("hello\n", encoding="utf-8")
        handle = fs.validate_and_open_git_root(root)
        self.addCleanup(handle.close)
        real_popen = fs.subprocess.Popen
        captured = {}

        def recording_popen(argv, **keywords):
            captured["argv"] = list(argv)
            captured["keywords"] = dict(keywords)
            return real_popen(argv, **keywords)

        with mock.patch.object(fs.subprocess, "Popen", recording_popen):
            observation = fs.read_bounded_regular(handle.fd, "note.md", 100)
        self.assertTrue(observation.ok)
        self.assertEqual(fs.helper_argv(handle.fd, "note.md", "read", 100), captured["argv"])
        self.assertEqual(fs.helper_popen_keywords(handle.fd), captured["keywords"])

    def test_a_name_beginning_with_a_dash_is_a_value(self):
        root = self.make_root(name="dashes")
        (root / "--name").write_text("dash content\n", encoding="utf-8")
        handle = fs.validate_and_open_git_root(root)
        self.addCleanup(handle.close)
        observation = fs.read_bounded_regular(handle.fd, "--name", 100)
        self.assertTrue(observation.ok)
        self.assertEqual(b"dash content\n", observation.data)

    def test_the_helper_module_imports_only_the_standard_library(self):
        source = Path(fs._HELPER_PATH).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        dynamic = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module is not None:
                    imported.add(node.module.split(".")[0])
                else:
                    dynamic.append(f"relative import at line {node.lineno}")
            elif isinstance(node, ast.Call):
                target = node.func
                if isinstance(target, ast.Name) and target.id in (
                    "__import__",
                    "import_module",
                ):
                    dynamic.append(f"{target.id} at line {node.lineno}")
                if (
                    isinstance(target, ast.Attribute)
                    and target.attr == "import_module"
                ):
                    dynamic.append(f"importlib.import_module at line {node.lineno}")
        self.assertEqual([], dynamic)
        self.assertTrue(imported)
        self.assertEqual(set(), imported - set(sys.stdlib_module_names))
        self.assertNotIn("brichan", imported)
        self.assertIn('if __name__ == "__main__":', source)


class FakeStat:
    """A stat-shaped object for metadata-range and race injection."""

    def __init__(self, mode=stat.S_IFREG | 0o644, **fields):
        self.st_mode = mode
        self.st_dev = fields.get("st_dev", 1)
        self.st_ino = fields.get("st_ino", 2)
        self.st_size = fields.get("st_size", 3)
        self.st_mtime_ns = fields.get("st_mtime_ns", 4)
        self.st_ctime_ns = fields.get("st_ctime_ns", 5)


class MetadataClassificationTest(TemporaryRootMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.root = self.make_root(name="entries")
        self.handle = fs.validate_and_open_git_root(self.root)
        self.addCleanup(self.handle.close)

    def assert_no_content_open(self, name, code):
        launches = []
        real_open = os.open

        def counting_open(path, *args, **keywords):
            if path == name:
                launches.append(path)
            return real_open(path, *args, **keywords)

        with mock.patch.object(fs, "_launch_bounded_helper", lambda *a, **k: self.fail(
            "a metadata-observed nonregular entry reached a content open"
        )):
            with mock.patch.object(fs.os, "open", counting_open):
                observation = fs.read_bounded_regular(self.handle.fd, name, 4096)
        self.assertEqual(code, observation.code)
        self.assertEqual([], launches)

    def test_directory_is_classified_without_a_content_open(self):
        (self.root / "package").mkdir()
        self.assert_no_content_open("package", "DIRECTORY_REJECTED")

    def test_fifo_without_a_writer_is_classified_without_a_content_open(self):
        os.mkfifo(self.root / "pipe")
        self.assert_no_content_open("pipe", "FIFO_REJECTED")

    def test_unix_socket_is_classified_without_a_content_open(self):
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(server.close)
        server.bind(str(self.root / "endpoint"))
        self.assert_no_content_open("endpoint", "SOCKET_REJECTED")

    def test_symlink_is_classified_without_a_content_open(self):
        (self.root / "target.md").write_text("x\n", encoding="utf-8")
        os.symlink(self.root / "target.md", self.root / "link.md")
        self.assert_no_content_open("link.md", "SYMLINK_REJECTED")

    def test_character_device_is_classified_without_a_content_open(self):
        descriptor = os.open("/dev", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.addCleanup(os.close, descriptor)
        with mock.patch.object(
            fs, "_launch_bounded_helper", lambda *a, **k: self.fail("content open")
        ):
            observation = fs.read_bounded_regular(descriptor, "null", 4096)
        self.assertEqual("DEVICE_REJECTED", observation.code)

    def test_block_device_is_classified_without_a_content_open(self):
        name = None
        with os.scandir("/dev") as entries:
            for entry in entries:
                try:
                    if stat.S_ISBLK(entry.stat(follow_symlinks=False).st_mode):
                        name = entry.name
                        break
                except OSError:
                    continue
        if name is None:
            self.skipTest("no block device available")
        descriptor = os.open("/dev", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.addCleanup(os.close, descriptor)
        with mock.patch.object(
            fs, "_launch_bounded_helper", lambda *a, **k: self.fail("content open")
        ):
            observation = fs.read_bounded_regular(descriptor, name, 4096)
        self.assertEqual("DEVICE_REJECTED", observation.code)

    def test_unknown_nonregular_mode_maps_to_its_exact_code(self):
        self.assertEqual("NON_REGULAR_REJECTED", fs._nonregular_outcome(0o160000))
        self.assertEqual("DIRECTORY_REJECTED", fs._nonregular_outcome(stat.S_IFDIR))
        self.assertEqual("FIFO_REJECTED", fs._nonregular_outcome(stat.S_IFIFO))
        self.assertEqual("SOCKET_REJECTED", fs._nonregular_outcome(stat.S_IFSOCK))
        self.assertEqual("DEVICE_REJECTED", fs._nonregular_outcome(stat.S_IFCHR))
        self.assertEqual("DEVICE_REJECTED", fs._nonregular_outcome(stat.S_IFBLK))
        self.assertEqual("SYMLINK_REJECTED", fs._nonregular_outcome(stat.S_IFLNK))

    def test_missing_entry_is_not_found_without_a_content_open(self):
        self.assert_no_content_open("absent.md", "NOT_FOUND")

    def test_out_of_range_metadata_is_reported_before_any_open(self):
        with mock.patch.object(
            fs.os, "stat", lambda *a, **k: FakeStat(st_dev=model.INTEGER_MAX + 1)
        ):
            observation = fs.classify_entry(self.handle.fd, "anything")
        self.assertEqual("OS_METADATA_RANGE", observation.code)

    def test_errno_classes_map_to_their_exact_outcome_codes(self):
        cases = {
            errno.EACCES: "UNREADABLE_FILE",
            errno.EPERM: "UNREADABLE_FILE",
            errno.ELOOP: "SYMLINK_REJECTED",
            errno.EMLINK: "SYMLINK_REJECTED",
            errno.ENOTDIR: "PATH_COMPONENT_NOT_DIRECTORY",
            errno.EISDIR: "DIRECTORY_REJECTED",
            errno.ENXIO: "SPECIAL_FILE_UNAVAILABLE",
            errno.ENODEV: "SPECIAL_FILE_UNAVAILABLE",
            errno.EINVAL: "UNSUPPORTED_SAFE_OPEN",
            errno.ENOTSUP: "UNSUPPORTED_SAFE_OPEN",
            errno.ESTALE: "FILESYSTEM_IO_ERROR",
            errno.EIO: "FILESYSTEM_IO_ERROR",
            errno.EMFILE: "RESOURCE_LIMIT",
            errno.ENFILE: "RESOURCE_LIMIT",
            errno.ENOMEM: "RESOURCE_LIMIT",
            errno.ENOENT: "NOT_FOUND",
            errno.EXDEV: "FILESYSTEM_ERROR",
        }
        for number, code in cases.items():
            with self.subTest(errno=number):
                def failing(*args, **keywords):
                    raise OSError(number, os.strerror(number))

                with mock.patch.object(fs.os, "stat", failing):
                    observation = fs.classify_entry(self.handle.fd, "entry")
                self.assertEqual(code, observation.code)
                if code == "FILESYSTEM_ERROR":
                    self.assertEqual(number, observation.errno_value)


class BoundedReadTest(TemporaryRootMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.root = self.make_root(name="reads")
        self.handle = fs.validate_and_open_git_root(self.root)
        self.addCleanup(self.handle.close)

    def write(self, name, size):
        payload = b"x" * size
        (self.root / name).write_bytes(payload)
        return payload

    def test_exact_and_over_limit_reads(self):
        for limit in (
            model.MAP_FILE_BYTE_LIMIT,
            model.EVIDENCE_FILE_BYTE_LIMIT,
            model.MANAGED_SKILL_FILE_BYTE_LIMIT,
            model.CLI_JSON_BYTE_LIMIT,
        ):
            with self.subTest(limit=limit):
                payload = self.write("exact.bin", limit)
                observation = fs.read_bounded_regular(self.handle.fd, "exact.bin", limit)
                self.assertTrue(observation.ok)
                self.assertEqual(payload, observation.data)
                self.assertEqual(limit, observation.identity.size)
                self.write("over.bin", limit + 1)
                overflow = fs.read_bounded_regular(self.handle.fd, "over.bin", limit)
                self.assertEqual("BYTE_LIMIT", overflow.code)
                self.assertIsNone(overflow.data)

    def test_empty_and_single_byte_reads(self):
        self.write("empty.md", 0)
        observation = fs.read_bounded_regular(self.handle.fd, "empty.md", 10)
        self.assertTrue(observation.ok)
        self.assertEqual(b"", observation.data)
        self.write("one.md", 1)
        self.assertTrue(fs.read_bounded_regular(self.handle.fd, "one.md", 1).ok)

    def test_validate_mode_returns_an_empty_successful_frame(self):
        self.write("marker", 32)
        observation = fs.validate_bounded_regular(self.handle.fd, "marker")
        self.assertTrue(observation.ok)
        self.assertEqual(b"", observation.data)
        self.assertEqual(32, observation.identity.size)

    @unittest.skipIf(os.geteuid() == 0, "root bypasses file permissions")
    def test_unreadable_regular_file_is_reported(self):
        self.write("secret.md", 8)
        os.chmod(self.root / "secret.md", 0o000)
        self.addCleanup(os.chmod, self.root / "secret.md", 0o644)
        observation = fs.read_bounded_regular(self.handle.fd, "secret.md", 100)
        self.assertEqual("UNREADABLE_FILE", observation.code)

    def test_identity_mismatch_between_parent_and_child_is_file_changed(self):
        self.write("racing.md", 16)
        real_classify = fs.classify_entry

        def stale_classify(parent_fd, name):
            observation = real_classify(parent_fd, name)
            identity = observation.identity
            return fs.Observation(
                code=observation.code,
                identity=model.FileIdentity(
                    device=identity.device,
                    inode=identity.inode,
                    mode=identity.mode,
                    size=identity.size + 1,
                    mtime_ns=identity.mtime_ns,
                    ctime_ns=identity.ctime_ns,
                ),
            )

        with mock.patch.object(fs, "classify_entry", stale_classify):
            observation = fs.read_bounded_regular(self.handle.fd, "racing.md", 100)
        self.assertEqual("FILE_CHANGED", observation.code)

    def test_same_inode_metadata_change_is_file_changed(self):
        self.write("touched.md", 16)
        real_classify = fs.classify_entry

        def stale_classify(parent_fd, name):
            observation = real_classify(parent_fd, name)
            identity = observation.identity
            return fs.Observation(
                code=observation.code,
                identity=model.FileIdentity(
                    device=identity.device,
                    inode=identity.inode,
                    mode=identity.mode,
                    size=identity.size,
                    mtime_ns=identity.mtime_ns + 1,
                    ctime_ns=identity.ctime_ns,
                ),
            )

        with mock.patch.object(fs, "classify_entry", stale_classify):
            observation = fs.read_bounded_regular(self.handle.fd, "touched.md", 100)
        self.assertEqual("FILE_CHANGED", observation.code)

    def test_helper_frame_validation_rejects_malformed_and_oversize_output(self):
        for stdout, stderr, returncode in (
            (b"", b"", 0),
            (b"not-a-frame\n", b"", 0),
            (b"brichan-safe-open-1 ok 0 1 2 3 4 5 6 7\n", b"", 0),
            (b"brichan-safe-open-1 nonsense 0 1 2 3 4 5 6 0\n", b"", 0),
            (b"brichan-safe-open-1 ok 0 1 2 3 4 5 6 4\nxx", b"", 0),
            (b"brichan-safe-open-1 ok 0 1 2 3 4 5 6 0\n", b"noise", 0),
            (b"brichan-safe-open-1 ok 0 1 2 3 4 5 6 0\n", b"", 3),
            (b"x" * (10 + 4096 + 1), b"", 0),
        ):
            with self.subTest(stdout=stdout[:32]):
                observation = fs._parse_frame(stdout, stderr, returncode, 10)
                self.assertEqual("SAFE_OPEN_HELPER_FAILED", observation.code)

    def test_every_child_status_token_maps_to_one_parent_outcome(self):
        child_tokens = set(helper._ERRNO_STATUS.values()) | {
            "filesystem_error",
            "ok",
            "byte_limit",
            "file_changed",
            "metadata_range",
            "directory",
            "fifo",
            "socket",
            "device",
            "symlink",
            "non_regular",
        }
        self.assertEqual(child_tokens, set(fs._CHILD_STATUS_OUTCOMES))
        self.assertEqual(helper.FRAME_MARKER, fs.FRAME_MARKER)
        registry = set(model.DIAGNOSTIC_CODES) | {
            fs.OUTCOME_OK,
            fs.OUTCOME_NOT_FOUND,
            fs.OUTCOME_BYTE_LIMIT,
        }
        for outcome in fs._CHILD_STATUS_OUTCOMES.values():
            self.assertIn(outcome, registry)


class HelperChildTest(TemporaryRootMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.root = self.make_root(name="child")
        self.fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.addCleanup(os.close, self.fd)
        self.frames = []

    def record_frame(self, status, errno_value=-1, identity=(0, 0, 0, 0, 0, 0), payload=b""):
        self.frames.append((status, errno_value, identity, payload))
        return 0

    def run_child(self, name, mode="read", limit=100, stat_side_effect=None):
        with mock.patch.object(helper, "write_frame", self.record_frame):
            if stat_side_effect is None:
                helper.run(self.fd, name, mode, limit)
            else:
                with mock.patch.object(helper.os, "stat", stat_side_effect):
                    helper.run(self.fd, name, mode, limit)
        return self.frames[-1]

    def test_child_argv_contract_is_fixed_position(self):
        self.assertEqual(("--dir-fd", "--name", "--mode", "--limit"), helper.ARGV_OPTIONS)
        self.assertEqual(2, helper.main(["helper"]))
        self.assertEqual(
            2, helper.main(["helper", "--dirfd", "3", "--name", "x", "--mode", "read", "--limit", "1"])
        )
        self.assertEqual(
            2, helper.main(["helper", "--dir-fd", "3", "--name", "x", "--mode", "write", "--limit", "1"])
        )
        self.assertEqual(
            2,
            helper.main(
                ["helper", "--dir-fd", "3", "--name", "x", "--mode", "validate", "--limit", "1"]
            ),
        )
        self.assertEqual(
            2,
            helper.main(
                ["helper", "--dir-fd", "3", "--name", "a/b", "--mode", "read", "--limit", "1"]
            ),
        )

    def test_child_reads_a_regular_file(self):
        (self.root / "note.md").write_bytes(b"hello\n")
        status, _errno, identity, payload = self.run_child("note.md")
        self.assertEqual("ok", status)
        self.assertEqual(b"hello\n", payload)
        self.assertEqual(6, identity[3])

    def test_child_reports_final_reopen_mismatch_as_file_changed(self):
        (self.root / "swap.md").write_bytes(b"abc")
        real_stat = helper.os.stat
        calls = {"count": 0}

        def mutating_stat(name, *args, **keywords):
            calls["count"] += 1
            info = real_stat(name, *args, **keywords)
            if calls["count"] == 2:
                return FakeStat(
                    mode=info.st_mode,
                    st_dev=info.st_dev,
                    st_ino=info.st_ino + 1,
                    st_size=info.st_size,
                )
            return info

        status, _errno, _identity, _payload = self.run_child(
            "swap.md", stat_side_effect=mutating_stat
        )
        self.assertEqual("file_changed", status)

    def test_child_reports_byte_limit_and_type_codes(self):
        (self.root / "big.md").write_bytes(b"y" * 20)
        status, _errno, _identity, _payload = self.run_child("big.md", limit=10)
        self.assertEqual("byte_limit", status)
        (self.root / "package").mkdir()
        status, _errno, _identity, _payload = self.run_child("package")
        self.assertEqual("directory", status)
        os.mkfifo(self.root / "pipe")
        status, _errno, _identity, _payload = self.run_child("pipe")
        self.assertEqual("fifo", status)

    def test_child_validate_mode_reads_nothing(self):
        (self.root / "marker").write_bytes(b"z" * 5)
        status, _errno, identity, payload = self.run_child("marker", mode="validate", limit=0)
        self.assertEqual("ok", status)
        self.assertEqual(b"", payload)
        self.assertEqual(5, identity[3])

    def test_child_maps_errno_and_out_of_range_metadata(self):
        self.assertEqual("not_found", helper.errno_status(errno.ENOENT))
        self.assertEqual("unreadable", helper.errno_status(errno.EACCES))
        self.assertEqual("filesystem_error", helper.errno_status(errno.EXDEV))
        self.assertFalse(helper.identity_in_range((1, 2, 3, 4, 5, 2 ** 63)))
        self.assertFalse(helper.identity_in_range((1, 2, 2 ** 32, 4, 5, 6)))
        self.assertTrue(helper.identity_in_range((1, 2, 3, 4, 5, 6)))


HOSTILE_MODULE_TEMPLATE = (
    "import os\n"
    "open({marker!r}, 'a').write('{name}\\n')\n"
    "print('HOSTILE-{name}')\n"
)

RUNNER_SOURCE = (
    "import json, os, sys\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "from brichan.techstacks import filesystem as fs\n"
    "descriptor = os.open(sys.argv[2], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)\n"
    "observation = fs.read_bounded_regular(descriptor, 'target.md', 4096)\n"
    "print(json.dumps({'code': observation.code,"
    " 'data': (observation.data or b'').decode('utf-8')}))\n"
)


class ShadowPackageTest(TemporaryRootMixin, unittest.TestCase):
    """A target repository's own ``brichan`` package must never execute."""

    def plant(self, directory):
        marker = str(directory / "hostile-marker")
        package = directory / "brichan" / "techstacks"
        package.mkdir(parents=True)
        for name, path in (
            ("init", directory / "brichan" / "__init__.py"),
            ("techstacks-init", package / "__init__.py"),
            ("helper", package / "safe_open_helper.py"),
        ):
            path.write_text(
                HOSTILE_MODULE_TEMPLATE.format(marker=marker, name=name), encoding="utf-8"
            )
        for name in ("sitecustomize", "usercustomize"):
            (directory / f"{name}.py").write_text(
                HOSTILE_MODULE_TEMPLATE.format(marker=marker, name=name), encoding="utf-8"
            )
        return marker

    def installed_package_root(self):
        install = self.base / "site-packages"
        target = install / "brichan" / "techstacks"
        target.mkdir(parents=True)
        shutil.copy(ROOT / "src" / "brichan" / "__init__.py", install / "brichan")
        # Copy the complete package, exactly as a wheel installs it; a
        # hardcoded module list would silently diverge from the real package
        # the moment a module is added.
        for source in sorted((ROOT / "src" / "brichan" / "techstacks").glob("*.py")):
            shutil.copy(source, target)
        return install

    def run_case(self, package_root, plant_on_pythonpath):
        data = self.base / f"data-{plant_on_pythonpath}-{package_root.name}"
        data.mkdir()
        (data / "target.md").write_text("real content\n", encoding="utf-8")
        hostile = self.base / f"hostile-{plant_on_pythonpath}-{package_root.name}"
        hostile.mkdir()
        marker = self.plant(hostile)
        environment = {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PATH": os.environ.get("PATH", ""),
        }
        if plant_on_pythonpath:
            environment["PYTHONPATH"] = f"{package_root}{os.pathsep}{hostile}"
        else:
            environment["PYTHONPATH"] = str(package_root)
        result = subprocess.run(
            [sys.executable, "-S", "-c", RUNNER_SOURCE, str(package_root), str(data)],
            cwd=hostile,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = result.stdout.strip().splitlines()[-1]
        self.assertIn('"code": "OK"', payload)
        self.assertIn("real content", payload)
        self.assertFalse(os.path.exists(marker), "the planted package executed")
        self.assertNotIn("HOSTILE-", result.stdout)
        self.assertNotIn("HOSTILE-", result.stderr)

    def test_checkout_mode_with_the_plant_in_the_working_directory(self):
        self.run_case(ROOT / "src", plant_on_pythonpath=False)

    def test_checkout_mode_with_the_plant_on_pythonpath(self):
        self.run_case(ROOT / "src", plant_on_pythonpath=True)

    def test_installed_mode_with_the_plant_in_the_working_directory(self):
        self.run_case(self.installed_package_root(), plant_on_pythonpath=False)

    def test_installed_mode_with_the_plant_on_pythonpath(self):
        self.run_case(self.installed_package_root(), plant_on_pythonpath=True)

    def test_isolated_options_exclude_the_working_and_package_directories(self):
        hostile = self.base / "hostile-path"
        hostile.mkdir()
        self.plant(hostile)
        script = self.base / "print_path.py"
        script.write_text("import sys; print('\\n'.join(sys.path))\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-I", "-S", "-B", "-X", "utf8=1", str(script)],
            cwd=hostile,
            env={},
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        entries = [entry for entry in result.stdout.splitlines() if entry]
        for entry in entries:
            self.assertNotEqual(str(hostile), entry)
            self.assertFalse(entry.startswith(str(self.base)))


class FakePipe:
    def __init__(self, raise_on_close=False):
        self.closed = 0
        self.raise_on_close = raise_on_close

    def close(self):
        self.closed += 1
        if self.raise_on_close:
            raise OSError("pipe close failed")


class FakePopen:
    """A configurable stand-in for the retained child object."""

    def __init__(
        self,
        script,
        *,
        pid=4242,
        pipe_close_raises=False,
        terminate_effect=None,
        kill_effect=None,
        entered=None,
        release=None,
    ):
        self.script = list(script)
        self.returncode = None
        self.stdout = FakePipe(pipe_close_raises)
        self.stderr = FakePipe(pipe_close_raises)
        self.pid = pid
        self.calls = []
        self.terminate_effect = terminate_effect
        self.kill_effect = kill_effect
        self.entered = entered
        self.release = release

    def communicate(self, timeout=None):
        self.calls.append(("communicate", timeout))
        if self.entered is not None:
            self.entered.set()
        if self.release is not None:
            self.release.wait(5)
        action = self.script.pop(0) if self.script else ("return", (b"", b""), 0)
        if action[0] == "timeout":
            raise subprocess.TimeoutExpired("helper", timeout)
        if action[0] == "raise":
            raise action[1]
        self.returncode = action[2]
        return action[1]

    def terminate(self):
        self.calls.append(("terminate",))
        if self.terminate_effect == "raise":
            raise OSError("terminate failed")
        if isinstance(self.terminate_effect, BaseException):
            raise self.terminate_effect

    def kill(self):
        self.calls.append(("kill",))
        if self.kill_effect == "raise":
            raise OSError("kill failed")

    def poll(self):
        return self.returncode


def ok_frame(payload=b"data"):
    header = "brichan-safe-open-1 ok -1 1 2 33188 {size} 4 5 {size}\n".format(
        size=len(payload)
    )
    return header.encode("utf-8") + payload


class HelperControllerTest(unittest.TestCase):
    def setUp(self):
        fs.HELPER_CONTROLLER.reset_for_test()
        self.addCleanup(fs.HELPER_CONTROLLER.reset_for_test)

    def launch(self, factory, limit=100):
        with mock.patch.object(fs.subprocess, "Popen", factory):
            return fs._launch_bounded_helper(3, "target.md", "read", limit)

    def test_normal_result_reaps_closes_and_returns_to_idle(self):
        payload = b"data"
        process = FakePopen([("return", (ok_frame(payload), b""), 0)])
        observation = self.launch(lambda *a, **k: process)
        self.assertTrue(observation.ok)
        self.assertEqual(payload, observation.data)
        self.assertEqual(fs.STATE_IDLE, fs.HELPER_CONTROLLER.state)
        self.assertIsNone(fs.HELPER_CONTROLLER.retained_process)
        self.assertEqual(1, process.stdout.closed)
        self.assertEqual(1, process.stderr.closed)
        self.assertEqual(["reserved:1", "active:1", "idle:1"], fs.HELPER_CONTROLLER.transitions)

    def test_constructor_failure_retains_no_object(self):
        def failing(*args, **keywords):
            raise OSError(errno.ENOENT, "helper missing")

        observation = self.launch(failing)
        self.assertEqual("SAFE_OPEN_HELPER_FAILED", observation.code)
        self.assertEqual(fs.STATE_IDLE, fs.HELPER_CONTROLLER.state)
        self.assertIsNone(fs.HELPER_CONTROLLER.retained_process)
        self.assertEqual(
            ["reserved:1", "launch-failed:1"], fs.HELPER_CONTROLLER.transitions
        )

    def test_first_timeout_then_term_completion_is_a_timeout(self):
        process = FakePopen([("timeout",), ("return", (b"", b""), -15)])
        observation = self.launch(lambda *a, **k: process)
        self.assertEqual("SAFE_OPEN_HELPER_TIMEOUT", observation.code)
        self.assertEqual(fs.STATE_IDLE, fs.HELPER_CONTROLLER.state)
        self.assertIn(("terminate",), process.calls)
        self.assertNotIn(("kill",), process.calls)
        self.assertEqual(
            ["reserved:1", "active:1", "terminating:1", "idle:1"],
            fs.HELPER_CONTROLLER.transitions,
        )

    def test_second_timeout_then_kill_completion_is_a_timeout(self):
        process = FakePopen([("timeout",), ("timeout",), ("return", (b"", b""), -9)])
        observation = self.launch(lambda *a, **k: process)
        self.assertEqual("SAFE_OPEN_HELPER_TIMEOUT", observation.code)
        self.assertIn(("kill",), process.calls)
        self.assertEqual(
            ["reserved:1", "active:1", "terminating:1", "killing:1", "idle:1"],
            fs.HELPER_CONTROLLER.transitions,
        )

    def test_kill_window_timeout_retains_the_object_as_unreaped(self):
        process = FakePopen([("timeout",), ("timeout",), ("timeout",)])
        observation = self.launch(lambda *a, **k: process)
        self.assertEqual("SAFE_OPEN_HELPER_LEAK", observation.code)
        self.assertEqual(fs.STATE_UNREAPED, fs.HELPER_CONTROLLER.state)
        self.assertIs(process, fs.HELPER_CONTROLLER.retained_process)
        self.assertEqual(1, process.stdout.closed)
        self.assertEqual(1, process.stderr.closed)

    def test_a_later_call_is_refused_until_the_retained_child_reaps(self):
        process = FakePopen([("timeout",), ("timeout",), ("timeout",)])
        self.launch(lambda *a, **k: process)
        launched = []

        def counting(*args, **keywords):
            launched.append(args)
            return FakePopen([("return", (ok_frame(), b""), 0)])

        refused = self.launch(counting)
        self.assertEqual("SAFE_OPEN_HELPER_LEAK", refused.code)
        self.assertEqual([], launched)
        process.returncode = -9
        accepted = self.launch(counting)
        self.assertTrue(accepted.ok)
        self.assertEqual(1, len(launched))
        self.assertEqual(fs.STATE_IDLE, fs.HELPER_CONTROLLER.state)
        # The two booleans guard the retained slot, so the abandoned child's
        # pipes are closed exactly once across abandon and later reap.
        self.assertEqual(1, process.stdout.closed)
        self.assertEqual(1, process.stderr.closed)

    def test_a_raising_poll_keeps_the_leak(self):
        process = FakePopen([("timeout",), ("timeout",), ("timeout",)])
        self.launch(lambda *a, **k: process)

        def raising_poll():
            raise OSError("poll failed")

        process.poll = raising_poll
        refused = self.launch(lambda *a, **k: self.fail("a second child was launched"))
        self.assertEqual("SAFE_OPEN_HELPER_LEAK", refused.code)
        self.assertEqual(fs.STATE_UNREAPED, fs.HELPER_CONTROLLER.state)

    def assert_closed_outcome(self, observation):
        """Assert one closed Design section 3 outcome code, never an escape."""

        self.assertIn(
            observation.code,
            set(model.DIAGNOSTIC_CODES)
            | set(model.HELPER_DIAGNOSTIC_CODES)
            | {fs.OUTCOME_OK, fs.OUTCOME_NOT_FOUND, fs.OUTCOME_BYTE_LIMIT},
        )

    def test_a_raising_poll_during_the_term_and_kill_windows_never_escapes(self):
        process = FakePopen([("timeout",), ("timeout",), ("timeout",)])

        def raising_poll():
            raise OSError("poll exploded")

        process.poll = raising_poll
        observation = self.launch(lambda *a, **k: process)
        self.assert_closed_outcome(observation)
        self.assertEqual("SAFE_OPEN_HELPER_LEAK", observation.code)
        self.assertIn(("terminate",), process.calls)
        self.assertIn(("kill",), process.calls)
        # The controller never stays in a cleanup state: every Design section
        # 16 row resolves to idle or unreaped.
        self.assertNotIn(
            fs.HELPER_CONTROLLER.state, (fs.STATE_TERMINATING, fs.STATE_KILLING)
        )
        self.assertEqual(fs.STATE_UNREAPED, fs.HELPER_CONTROLLER.state)
        # Once the retained child does reap, the slot recovers and a later
        # healthy call succeeds.
        process.poll = lambda: -9
        process.returncode = -9
        healthy = self.launch(lambda *a, **k: FakePopen([("return", (ok_frame(), b""), 0)]))
        self.assertTrue(healthy.ok)
        self.assertEqual(fs.STATE_IDLE, fs.HELPER_CONTROLLER.state)

    def test_a_raising_poll_after_a_completed_communicate_never_escapes(self):
        process = FakePopen([("return", (ok_frame(), b""), 0)])

        def raising_poll():
            raise OSError("poll exploded")

        process.poll = raising_poll
        observation = self.launch(lambda *a, **k: process)
        self.assert_closed_outcome(observation)
        self.assertEqual("SAFE_OPEN_HELPER_LEAK", observation.code)
        self.assertNotIn(
            fs.HELPER_CONTROLLER.state, (fs.STATE_TERMINATING, fs.STATE_KILLING)
        )

    def test_a_keyboard_interrupt_from_popen_propagates_and_releases(self):
        def interrupting(*args, **keywords):
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            self.launch(interrupting)
        self.assertEqual(fs.STATE_IDLE, fs.HELPER_CONTROLLER.state)
        self.assertIsNone(fs.HELPER_CONTROLLER.retained_process)
        self.assertEqual(
            ["reserved:1", "launch-failed:1"], fs.HELPER_CONTROLLER.transitions
        )
        healthy = self.launch(lambda *a, **k: FakePopen([("return", (ok_frame(), b""), 0)]))
        self.assertTrue(healthy.ok)

    def test_a_keyboard_interrupt_in_the_term_window_propagates_and_abandons(self):
        # L1-i1v2-1: the interrupt keeps propagating (L2-i1-4), but the slot
        # resolves to ``unreaped`` retaining the object instead of stranding in
        # ``terminating``, so the normal recovery path applies afterwards.
        process = FakePopen([("timeout",)], terminate_effect=KeyboardInterrupt())
        with self.assertRaises(KeyboardInterrupt):
            self.launch(lambda *a, **k: process)
        self.assertEqual(fs.STATE_UNREAPED, fs.HELPER_CONTROLLER.state)
        self.assertIs(process, fs.HELPER_CONTROLLER.retained_process)
        self.assertEqual(
            ["reserved:1", "active:1", "terminating:1", "unreaped:1"],
            fs.HELPER_CONTROLLER.transitions,
        )
        self.assertEqual(1, process.stdout.closed)
        self.assertEqual(1, process.stderr.closed)
        launched = []

        def counting(*args, **keywords):
            launched.append(args)
            return FakePopen([("return", (ok_frame(), b""), 0)])

        process.returncode = -15
        healthy = self.launch(counting)
        self.assertTrue(healthy.ok)
        self.assertEqual(1, len(launched))
        self.assertEqual(fs.STATE_IDLE, fs.HELPER_CONTROLLER.state)
        self.assertIsNone(fs.HELPER_CONTROLLER.retained_process)
        self.assertEqual(1, process.stdout.closed)
        self.assertEqual(1, process.stderr.closed)

    def test_raising_terminate_still_runs_the_remaining_stages(self):
        process = FakePopen(
            [("timeout",), ("return", (b"", b""), -15)], terminate_effect="raise"
        )
        observation = self.launch(lambda *a, **k: process)
        self.assertEqual("SAFE_OPEN_HELPER_FAILED", observation.code)
        self.assertEqual(fs.STATE_IDLE, fs.HELPER_CONTROLLER.state)

    def test_a_raising_communicate_is_a_helper_failure(self):
        process = FakePopen([("raise", OSError("broken pipe")), ("return", (b"", b""), 1)])
        observation = self.launch(lambda *a, **k: process)
        self.assertEqual("SAFE_OPEN_HELPER_FAILED", observation.code)
        self.assertEqual(fs.STATE_IDLE, fs.HELPER_CONTROLLER.state)

    def test_pipe_close_exceptions_are_contained_and_close_once(self):
        process = FakePopen([("return", (ok_frame(), b""), 0)], pipe_close_raises=True)
        observation = self.launch(lambda *a, **k: process)
        self.assertTrue(observation.ok)
        self.assertEqual(1, process.stdout.closed)
        self.assertEqual(1, process.stderr.closed)
        self.assertIn("stdout-close-raised", fs.HELPER_CONTROLLER.transitions)
        self.assertEqual(fs.STATE_IDLE, fs.HELPER_CONTROLLER.state)

    def test_a_stale_generation_cannot_clear_a_newer_reservation(self):
        status, generation = fs.HELPER_CONTROLLER.reserve()
        self.assertEqual("reserved", status)
        fs.HELPER_CONTROLLER.launch_failed(generation)
        with self.assertRaises(RuntimeError):
            fs.HELPER_CONTROLLER.launch_failed(generation)
        status, second = fs.HELPER_CONTROLLER.reserve()
        self.assertEqual(generation + 1, second)
        with self.assertRaises(RuntimeError):
            fs.HELPER_CONTROLLER.attach(generation, FakePopen([]))
        fs.HELPER_CONTROLLER.launch_failed(second)

    def test_pid_reuse_never_grants_ownership(self):
        first = FakePopen([("timeout",), ("timeout",), ("timeout",)], pid=777)
        self.launch(lambda *a, **k: first)
        self.assertIs(first, fs.HELPER_CONTROLLER.retained_process)
        second = FakePopen([("return", (ok_frame(), b""), 0)], pid=777)
        refused = self.launch(lambda *a, **k: second)
        self.assertEqual("SAFE_OPEN_HELPER_LEAK", refused.code)
        self.assertIs(first, fs.HELPER_CONTROLLER.retained_process)
        self.assertEqual([], second.calls)

    def test_concurrent_callers_launch_exactly_one_child(self):
        for caller_count in (2, 8, 32):
            with self.subTest(callers=caller_count):
                fs.HELPER_CONTROLLER.reset_for_test()
                entered = threading.Event()
                release = threading.Event()
                constructed = []
                winner = FakePopen(
                    [("return", (ok_frame(), b""), 0)], entered=entered, release=release
                )

                def factory(*args, **keywords):
                    constructed.append(args)
                    return winner

                results = [None] * caller_count

                def call(index):
                    results[index] = fs._launch_bounded_helper(3, "target.md", "read", 100)

                with mock.patch.object(fs.subprocess, "Popen", factory):
                    threads = [
                        threading.Thread(target=call, args=(index,))
                        for index in range(caller_count)
                    ]
                    for thread in threads:
                        thread.start()
                    self.assertTrue(entered.wait(5))
                    for thread in threads[1:]:
                        thread.join(0.2)
                    release.set()
                    for thread in threads:
                        thread.join(5)
                self.assertEqual(1, len(constructed))
                codes = [result.code for result in results]
                self.assertEqual(1, codes.count(fs.OUTCOME_OK))
                self.assertEqual(
                    caller_count - 1, codes.count("SAFE_OPEN_HELPER_BUSY")
                )
                self.assertEqual(fs.STATE_IDLE, fs.HELPER_CONTROLLER.state)


class RootHelperBusyTest(TemporaryRootMixin, unittest.TestCase):
    def test_a_concurrent_caller_during_git_validation_is_refused(self):
        root = self.make_root(name="busy", git="file")
        status, generation = fs.HELPER_CONTROLLER.reserve()
        self.assertEqual("reserved", status)
        self.addCleanup(fs.HELPER_CONTROLLER.reset_for_test)
        launched = []

        def counting(*args, **keywords):
            launched.append(args)
            raise AssertionError("a child was launched while the controller was busy")

        with mock.patch.object(fs.subprocess, "Popen", counting):
            with self.assertRaises(model.TechstackInputError) as error:
                fs.validate_and_open_git_root(root)
        self.assertEqual("PROJECT_ROOT_HELPER_BUSY", error.exception.code)
        self.assertEqual("project_root", error.exception.field)
        self.assertEqual(
            "project_root safe-open helper is busy", error.exception.detail
        )
        self.assertEqual([], launched)
        fs.HELPER_CONTROLLER.launch_failed(generation)

    def record_root_descriptor(self):
        """Record the root descriptor handed to the marker validation, and the
        descriptors closed from that point on.

        Only closes after the marker call are recorded, because the walk
        releases and reuses ancestor descriptor numbers before it.
        """

        held = []
        closed = []
        recording = []
        real_marker = fs._validate_git_marker
        real_close = os.close

        def recording_marker(root_fd):
            held.append(root_fd)
            recording.append(True)
            return real_marker(root_fd)

        def recording_close(descriptor, *args, **keywords):
            if recording:
                closed.append(descriptor)
            return real_close(descriptor, *args, **keywords)

        marker_patcher = mock.patch.object(fs, "_validate_git_marker", recording_marker)
        close_patcher = mock.patch.object(fs.os, "close", recording_close)
        marker_patcher.start()
        self.addCleanup(marker_patcher.stop)
        close_patcher.start()
        self.addCleanup(close_patcher.stop)
        return held, closed

    def test_a_raising_poll_during_root_validation_closes_the_root_descriptor(self):
        root = self.make_root(name="root-poll", git="file")
        process = FakePopen([("timeout",), ("timeout",), ("timeout",)])

        def raising_poll():
            raise OSError("poll exploded")

        process.poll = raising_poll
        held, closed = self.record_root_descriptor()
        with mock.patch.object(fs.subprocess, "Popen", lambda *a, **k: process):
            with self.assertRaises(model.TechstackInputError) as error:
                fs.validate_and_open_git_root(root)
        self.assertEqual("PROJECT_ROOT_HELPER_LEAK", error.exception.code)
        self.assertEqual([held[0]], closed)
        self.assertNotIn(
            fs.HELPER_CONTROLLER.state, (fs.STATE_TERMINATING, fs.STATE_KILLING)
        )

    def test_any_exception_during_marker_validation_closes_the_root_descriptor(self):
        root = self.make_root(name="root-raise", git="file")
        held, closed = self.record_root_descriptor()

        def exploding(*args, **keywords):
            raise RuntimeError("marker validation exploded")

        with mock.patch.object(fs, "validate_bounded_regular", exploding):
            with self.assertRaises(RuntimeError):
                fs.validate_and_open_git_root(root)
        self.assertIn(held[0], closed)

    def test_helper_outcomes_map_to_their_root_caller_codes(self):
        root = self.make_root(name="root-helper", git="file")
        for outcome, code in (
            ("SAFE_OPEN_HELPER_TIMEOUT", "PROJECT_ROOT_HELPER_TIMEOUT"),
            ("SAFE_OPEN_HELPER_FAILED", "PROJECT_ROOT_HELPER_FAILED"),
            ("SAFE_OPEN_HELPER_LEAK", "PROJECT_ROOT_HELPER_LEAK"),
            ("SAFE_OPEN_HELPER_BUSY", "PROJECT_ROOT_HELPER_BUSY"),
        ):
            with self.subTest(outcome=outcome):
                with mock.patch.object(
                    fs,
                    "_launch_bounded_helper",
                    lambda *a, **k: fs.Observation(code=outcome),
                ):
                    with self.assertRaises(model.TechstackInputError) as error:
                        fs.validate_and_open_git_root(root)
                self.assertEqual(code, error.exception.code)


if __name__ == "__main__":
    unittest.main()
