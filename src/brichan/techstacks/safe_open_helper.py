#!/usr/bin/env python3
"""Bounded standard-library safe-open child for techstack reads.

This file is executed as ``__main__`` from its absolute package file path by
``filesystem.py``'s frozen isolated launch contract. It imports only the
standard library and contains no ``brichan`` import of any kind, so the child
never resolves a module through ``sys.path``, ``PYTHONPATH``, the working
directory, the user site directory, or ``sitecustomize``/``usercustomize``.

The child receives one already held directory descriptor, reclassifies the
named entry with a descriptor-relative no-follow ``stat``, opens it no-follow
and nonblocking only when that metadata says regular, verifies identity and
type through ``fstat``, reads at most the surface limit plus one byte, rechecks
identity and exact size, performs one same-name reopen identity check, and
writes exactly one length-prefixed frame to stdout with stderr empty. It never
opens a metadata-observed nonregular entry and never writes project state.
"""

import errno as errno_module
import os
import stat
import sys


#: Frame protocol marker. The parent rejects any other first token.
FRAME_MARKER = "brichan-safe-open-1"

#: Fixed argv option names; positions are frozen, so a ``--name`` value that
#: begins with a dash is a value and never an option. ``argparse`` is not used.
ARGV_OPTIONS = ("--dir-fd", "--name", "--mode", "--limit")

#: The only two accepted modes. ``validate`` always pairs with limit 0 and
#: performs no read.
MODES = ("read", "validate")

#: Supported metadata integer ranges, inlined because the child imports no
#: package module.
INTEGER_MAX = 9223372036854775807
MODE_MAX = 4294967295

#: Exit codes. A protocol violation writes no frame.
EXIT_OK = 0
EXIT_USAGE = 2

_ERRNO_STATUS = {
    errno_module.ENOENT: "not_found",
    errno_module.ELOOP: "symlink",
    errno_module.EMLINK: "symlink",
    errno_module.ENOTDIR: "path_component_not_directory",
    errno_module.EISDIR: "directory",
    errno_module.EACCES: "unreadable",
    errno_module.EPERM: "unreadable",
    errno_module.ENXIO: "special_unavailable",
    errno_module.ENODEV: "special_unavailable",
    errno_module.EINVAL: "unsupported_safe_open",
    errno_module.ENOTSUP: "unsupported_safe_open",
    errno_module.EOPNOTSUPP: "unsupported_safe_open",
    errno_module.ESTALE: "io_error",
    errno_module.EIO: "io_error",
    errno_module.EMFILE: "resource_limit",
    errno_module.ENFILE: "resource_limit",
    errno_module.ENOMEM: "resource_limit",
}


def errno_status(value):
    """Map one errno to its closed status token."""

    return _ERRNO_STATUS.get(value, "filesystem_error")


def type_status(mode):
    """Map one nonregular st_mode to its closed status token."""

    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISFIFO(mode):
        return "fifo"
    if stat.S_ISSOCK(mode):
        return "socket"
    if stat.S_ISCHR(mode) or stat.S_ISBLK(mode):
        return "device"
    if stat.S_ISLNK(mode):
        return "symlink"
    return "non_regular"


def identity_tuple(info):
    """Return the six-field identity tuple of one stat result."""

    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def identity_in_range(identity):
    """Return True when every metadata field fits the supported ranges."""

    device, inode, mode, size, mtime_ns, ctime_ns = identity
    for value in (device, inode, size, mtime_ns, ctime_ns):
        if not isinstance(value, int) or not 0 <= value <= INTEGER_MAX:
            return False
    return isinstance(mode, int) and 0 <= mode <= MODE_MAX


def write_frame(status, errno_value=-1, identity=(0, 0, 0, 0, 0, 0), payload=b""):
    """Write exactly one frame to stdout and return the process exit code."""

    header = "{} {} {} {} {} {} {} {} {} {}\n".format(
        FRAME_MARKER,
        status,
        errno_value,
        identity[0],
        identity[1],
        identity[2],
        identity[3],
        identity[4],
        identity[5],
        len(payload),
    )
    stream = sys.stdout.buffer
    stream.write(header.encode("utf-8"))
    stream.write(payload)
    stream.flush()
    return EXIT_OK


def _close(descriptor):
    try:
        os.close(descriptor)
    except OSError:
        pass


def run(dir_fd, name, mode, limit):
    """Perform the bounded observation and write its single result frame."""

    try:
        before = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except OSError as error:
        return write_frame(errno_status(error.errno), _decimal(error.errno))
    # Metadata type is the authority and precedes the range check, so a
    # nonregular entry reports its exact type outcome and is never opened.
    if not stat.S_ISREG(before.st_mode):
        return write_frame(type_status(before.st_mode))
    identity = identity_tuple(before)
    if not identity_in_range(identity):
        return write_frame("metadata_range")

    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=dir_fd,
        )
    except OSError as error:
        return write_frame(errno_status(error.errno), _decimal(error.errno))

    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or identity_tuple(opened) != identity:
            return write_frame("file_changed", identity=identity)
        payload = b""
        if mode == "read":
            payload = _read_bounded(descriptor, limit)
            if payload is None:
                return write_frame("io_error")
            if len(payload) > limit:
                return write_frame("byte_limit", identity=identity)
            if len(payload) != before.st_size:
                return write_frame("file_changed", identity=identity)
        try:
            after = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
        except OSError as error:
            return write_frame(errno_status(error.errno), _decimal(error.errno))
        if identity_tuple(after) != identity:
            return write_frame("file_changed", identity=identity)
        try:
            reopened = os.open(
                name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=dir_fd,
            )
        except OSError as error:
            return write_frame(errno_status(error.errno), _decimal(error.errno))
        try:
            if identity_tuple(os.fstat(reopened)) != identity:
                return write_frame("file_changed", identity=identity)
        finally:
            _close(reopened)
        return write_frame("ok", identity=identity, payload=payload)
    finally:
        _close(descriptor)


def _decimal(value):
    """Return a decimal errno, or -1 when the OSError carries none."""

    return -1 if value is None else int(value)


def _read_bounded(descriptor, limit):
    """Read at most ``limit`` plus one byte, or None on an unreadable stream."""

    chunks = []
    remaining = limit + 1
    while remaining > 0:
        try:
            chunk = os.read(descriptor, remaining)
        except BlockingIOError:
            return None
        except OSError:
            return None
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def main(argv):
    """Parse the frozen fixed-position argv and run one bounded observation."""

    if len(argv) != 9:
        return EXIT_USAGE
    for index, option in enumerate(ARGV_OPTIONS):
        if argv[1 + index * 2] != option:
            return EXIT_USAGE
    try:
        dir_fd = int(argv[2])
        limit = int(argv[8])
    except ValueError:
        return EXIT_USAGE
    name = argv[4]
    mode = argv[6]
    if mode not in MODES or dir_fd < 0 or limit < 0:
        return EXIT_USAGE
    if mode == "validate" and limit != 0:
        return EXIT_USAGE
    if not name or "/" in name:
        return EXIT_USAGE
    return run(dir_fd, name, mode, limit)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
