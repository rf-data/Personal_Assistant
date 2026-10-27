"""Reuse the CS50 executor's hash, path, directory sync and receipt primitives."""

import ctypes
import errno
import fcntl
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from src.tools_lecture.execute_cs50 import (
    ExecutionConflict,
    safe_path,
    sync_directory,
)


def artifact_root(root):
    from src.runtime_paths import output_path

    root = Path(root).absolute()
    try:
        output_path(root, "material_artifacts")
    except ValueError as error:
        raise ExecutionConflict(
            "Material artifact workspace is not authorized"
        ) from error
    safe_path(root.parent, root)
    return root


def locate(root, relative):
    return safe_path(root, Path(root) / relative)


@contextmanager
def locked(root):
    root = artifact_root(root)
    root.mkdir(parents=True, exist_ok=True)
    path = locate(root, ".materials.lock")
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield root


def publish_bytes(path, contents):
    """Exclusive atomic publication; an existing file is never replaced."""
    destination = os.fsencode(path)
    if b"\0" in destination:
        raise ValueError("Invalid publication path")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".material-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        # One atomic namespace operation: cancellation after link() previously
        # left two names for the published inode until the finally block ran.
        # SIGKILL cannot run finally; stopped-workspace inspection then correctly
        # rejected that hardlink. Linux C16 requires no-replace rename semantics.
        rename = getattr(ctypes.CDLL(None, use_errno=True), "renameat2", None)
        if rename is None:
            raise OSError(errno.ENOSYS, "Atomic no-replace publication unavailable")
        rename.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        rename.restype = ctypes.c_int
        if rename(-100, os.fsencode(name), -100, destination, 1) != 0:
            code = ctypes.get_errno()
            raise OSError(code, "Atomic no-replace publication failed")
        sync_directory(path.parent)
    finally:
        Path(name).unlink(missing_ok=True)


def save_model(path, model):
    publish_bytes(path, (model.model_dump_json(indent=2) + "\n").encode())
