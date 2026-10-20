"""Reuse the CS50 executor's hash, path, directory sync and receipt primitives."""

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
    root = Path(root).absolute()
    repo = Path(__file__).resolve().parents[2]
    if root == repo or root.is_relative_to(repo) or repo.is_relative_to(root):
        raise ExecutionConflict(
            "Material artifact workspace must be outside the repository"
        )
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
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".material-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, path)
        sync_directory(path.parent)
    finally:
        Path(name).unlink(missing_ok=True)


def save_model(path, model):
    publish_bytes(path, (model.model_dump_json(indent=2) + "\n").encode())
