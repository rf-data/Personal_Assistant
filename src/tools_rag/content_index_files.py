"""Private bounded derivative files using existing ContentStore inode primitives."""

import os
import re

from src.content_store.artifacts import (
    FILE_FLAGS,
    _Artifacts,
    _private,
    _sync,
    explicit_root,
)
from src.content_store.errors import IntegrityError, InvalidInput, Unavailable
from src.content_store.limits import directory_entries
from src.content_store.models import canonical

MAX_FILE = 64 * 1024**2


class IndexFiles(_Artifacts):
    def _parts(self, relative):
        if (
            not isinstance(relative, str)
            or not re.fullmatch(r"[A-Za-z0-9_. /-]+", relative)
            or " " in relative
        ):
            raise InvalidInput("index internal path")
        parent, _, leaf = relative.rpartition("/")
        if not leaf or any(p in {".", "..", ""} for p in relative.split("/")):
            raise InvalidInput("index internal path")
        return parent, leaf

    def read(self, relative, *, maximum=MAX_FILE, missing=False):
        parent, leaf = self._parts(relative)
        try:
            with self.directory(parent) as directory:
                fd = os.open(leaf, FILE_FLAGS, dir_fd=directory)
                with os.fdopen(fd, "rb") as f:
                    before = _private(f.fileno())
                    if before.st_size > maximum:
                        raise Unavailable("index file size")
                    data = f.read(maximum + 1)
                    after = _private(f.fileno())
                    if len(data) != before.st_size or (
                        before.st_mtime_ns,
                        before.st_ctime_ns,
                    ) != (after.st_mtime_ns, after.st_ctime_ns):
                        raise IntegrityError("index file changed")
                    return data
        except FileNotFoundError:
            if missing:
                return None
            raise Unavailable("index file missing") from None
        except OSError:
            raise Unavailable("index file unavailable") from None

    def write(self, relative, data, *, replace=False):
        parent, leaf = self._parts(relative)
        if len(data) > MAX_FILE:
            raise Unavailable("index file size")
        with self.directory(parent, create=True) as directory:
            temporary = leaf
            if replace:
                import uuid

                temporary = "pending-" + uuid.uuid4().hex + ".json"
            fd = os.open(
                temporary,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            if replace:
                os.replace(temporary, leaf, src_dir_fd=directory, dst_dir_fd=directory)
            _sync(directory)

    def json(self, relative, value, *, replace=False):
        self.write(relative, canonical(value), replace=replace)

    def publish(self, build_id, generation_id):
        with (
            self.directory("staging") as src,
            self.directory(
                "generations/" + generation_id.split(":")[1], create=True
            ) as dst,
        ):
            try:
                os.stat(build_id, dir_fd=dst, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise IntegrityError("generation already exists")
            os.rename(build_id, build_id, src_dir_fd=src, dst_dir_fd=dst)
            _sync(src)
            _sync(dst)

    def remove_directory(self, relative, expected_files):
        with self.directory(relative) as directory:
            actual = set(directory_entries(directory, limit=129))
            if actual != set(expected_files):
                raise IntegrityError("index inventory mismatch")
            for name in sorted(actual):
                fd = os.open(name, FILE_FLAGS, dir_fd=directory)
                try:
                    _private(fd)
                finally:
                    os.close(fd)
            for name in sorted(actual):
                os.unlink(name, dir_fd=directory)
            _sync(directory)
        parent, leaf = self._parts(relative)
        with self.directory(parent) as directory:
            os.rmdir(leaf, dir_fd=directory)
            _sync(directory)


def initialize_root(root, store_root, purpose):
    root = explicit_root(root)
    if root.is_relative_to(store_root) or store_root.is_relative_to(root):
        raise InvalidInput("index and content roots must be separate")
    # No adoption of a foreign/partially initialized root.
    from src.content_store.artifacts import _open_directory

    parent = _open_directory(root.parent)
    try:
        os.mkdir(root.name, 0o700, dir_fd=parent)
        _sync(parent)
    finally:
        os.close(parent)
    files = IndexFiles(root)
    for name in (".content-index-catalog.lock", ".content-index-build.lock"):
        files.write(name, b"")
    files.json(
        "identity.json",
        dict(schema_version=1, identity="content-fts5-v1", purpose=purpose),
    )
    return files
