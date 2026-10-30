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


# C27: optional registered locations extend the existing storage boundary.
# No roots are implicitly registered and no existing worker configuration changes.
class RegisteredStorage:
    """Read snapshots through registered roots; writes retain runtime_paths grants.

    Root descriptors and O_NOFOLLOW protect each component, including replacement
    races. Kernel mount boundaries are checked even for same-device bind mounts.
    Callers configure trusted roots; lecture/model text cannot register a root.
    """

    def __init__(self, roots):
        import re

        from src.runtime_paths import checked_path

        if not isinstance(roots, dict) or not 1 <= len(roots) <= 16:
            raise ValueError("One to sixteen explicit storage roots required")
        self.roots = {}
        for key, grant in roots.items():
            if not isinstance(key, str) or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", key
            ):
                raise ValueError("Invalid storage ID")
            if not isinstance(grant, dict) or not isinstance(
                grant.get("path"), (str, Path)
            ):
                raise ValueError("Storage root requires an explicit physical path")
            if set(grant) - {"path", "readonly"}:
                raise ValueError("Unknown storage root setting")
            path = checked_path(grant["path"])
            if path == Path("/") or not isinstance(grant.get("readonly", True), bool):
                raise ValueError("Invalid storage root")
            self.roots[key] = (path, grant.get("readonly", True))

    def path(self, storage_id, relative, *, write=False):
        from pathlib import PurePosixPath

        from src.runtime_paths import mounts, output_path

        if storage_id not in self.roots:
            raise ValueError("Unregistered storage root")
        root, readonly = self.roots[storage_id]
        rel = PurePosixPath(relative)
        if (
            not relative
            or rel.is_absolute()
            or ".." in rel.parts
            or rel.as_posix() != relative
            or "\\" in relative
            or any(ord(c) < 32 for c in relative)
            or relative == "."
        ):
            raise ValueError("Portable nontraversing artifact path required")
        if not root.is_dir():
            raise FileNotFoundError("Storage root/mount unavailable: " + storage_id)
        target = locate(root, root / relative)
        if any(
            m != root and m.is_relative_to(root) and target.is_relative_to(m)
            for m in mounts(subtree=root)
        ):
            raise ValueError("Nested storage mount forbidden")
        if write:
            if readonly:
                raise PermissionError("Storage root is read-only")
            # In particular, a root inside the checkout still needs C16/C26 policy.
            output_path(target, "material_artifacts")
        return target

    @contextmanager
    def parent(self, storage_id, relative, *, write=False):
        """Yield an anchored parent descriptor, never create directories."""
        import stat

        target = self.path(storage_id, relative, write=write)
        # Walk from / to avoid following a root ancestor swapped after validation.
        descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        root = self.roots[storage_id][0]
        root_device = None
        try:
            current = Path("/")
            for part in target.parent.parts[1:]:
                next_fd = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=descriptor,
                )
                os.close(descriptor)
                descriptor = next_fd
                current = current / part
                info = os.fstat(descriptor)
                if current == root:
                    root_device = info.st_dev
                if root_device is not None and info.st_dev != root_device:
                    raise ValueError("Storage device boundary changed")
                if not stat.S_ISDIR(info.st_mode):
                    raise ValueError("Storage parent is not a directory")
            yield descriptor, target.name
        finally:
            os.close(descriptor)

    def read(self, storage_id, relative, *, maximum=2 * 1024 * 1024):
        import stat

        with self.parent(storage_id, relative) as (parent, name):
            fd = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
            )
            with os.fdopen(fd, "rb") as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
                    raise ValueError("Source must be a bounded regular file")
                if before.st_dev != os.fstat(parent).st_dev:
                    raise ValueError("Source crosses storage device boundary")
                data = stream.read(maximum + 1)
                after = os.fstat(stream.fileno())

                def identity(s):
                    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)

                if len(data) > maximum or identity(before) != identity(after):
                    raise ValueError("Source changed during bounded read")
        return data

    def create(self, storage_id, relative, data):
        """Exclusive publication only, never overwrite; explicit write permission."""
        with self.parent(storage_id, relative, write=True) as (parent, name):
            fd = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent,
            )
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.fsync(parent)
