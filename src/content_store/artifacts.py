"""Private POSIX blob primitives. Internal only: SHA possession is not authority."""

import fcntl
import os
import re
import stat
from contextlib import contextmanager
from pathlib import Path

from src.content_store.errors import Busy, IntegrityError, InvalidInput, Unavailable
from src.content_store.models import MAX_BYTES, ArtifactReference

DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK


def _sync(fd):
    os.fsync(fd)


def _private(fd, *, directory=False):
    info = os.fstat(fd)
    if (
        not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
        or (not directory and info.st_nlink != 1)
    ):
        raise IntegrityError("private regular inode required")
    return info


def _open_directory(path):
    """Walk every ancestor with openat/O_NOFOLLOW, not a check-then-open path."""
    fd = os.open("/", DIR_FLAGS)
    try:
        for part in path.parts[1:]:
            child = os.open(part, DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def explicit_root(root):
    path = Path(root)
    repo = Path(__file__).resolve().parents[2]
    if (
        not path.is_absolute()
        or ".." in path.parts
        or path == Path("/")
        or path == repo
        or path.is_relative_to(repo)
        or repo.is_relative_to(path)
    ):
        raise InvalidInput("explicit external content root required")
    return path


class _Artifacts:
    def __init__(self, root):
        self.root = explicit_root(root)
        try:
            fd = _open_directory(self.root)
            try:
                _private(fd, directory=True)
                self.identity = (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
            finally:
                os.close(fd)
        except OSError:
            raise Unavailable("content root cannot be opened") from None

    @contextmanager
    def directory(self, relative="", *, create=False):
        if relative and not re.fullmatch(r"[A-Za-z0-9_./-]+", relative):
            raise InvalidInput("internal directory key")
        parts = relative.split("/") if relative else []
        if any(p in {"", ".", ".."} for p in parts):
            raise InvalidInput("internal directory key")
        fd = _open_directory(self.root)
        try:
            info = _private(fd, directory=True)
            if (info.st_dev, info.st_ino) != self.identity:
                raise IntegrityError("content root inode changed")
            for part in parts:
                if create:
                    try:
                        os.mkdir(part, 0o700, dir_fd=fd)
                        _sync(fd)
                    except FileExistsError:
                        pass
                child = os.open(part, DIR_FLAGS, dir_fd=fd)
                try:
                    child_info = _private(child, directory=True)
                    if child_info.st_dev != self.identity[0]:
                        raise IntegrityError("artifact filesystem changed")
                except BaseException:
                    os.close(child)
                    raise
                os.close(fd)
                fd = child
            yield fd
        finally:
            os.close(fd)

    @contextmanager
    def lock(self, name, *, exclusive=False):
        if not re.fullmatch(
            r"(?:\.content-[a-z-]+\.lock|locks/[a-f0-9]{32}\.lock)", name
        ):
            raise InvalidInput("lock identity")
        parent, _, leaf = name.rpartition("/")
        with self.directory(parent) as directory:
            fd = os.open(leaf, FILE_FLAGS, dir_fd=directory)
            try:
                _private(fd)
                try:
                    fcntl.flock(
                        fd,
                        (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB,
                    )
                except BlockingIOError:
                    raise Busy("content lock held") from None
                yield
            finally:
                os.close(fd)

    def create_run_lock(self, run_id):
        self._run_id(run_id)
        with self.directory("locks") as directory:
            fd = os.open(
                run_id + ".lock",
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            os.close(fd)
            _sync(directory)

    @staticmethod
    def _run_id(run_id):
        if not re.fullmatch(r"[a-f0-9]{32}", run_id):
            raise InvalidInput("run identity")

    def stage(self, run_id, stream, reference: ArtifactReference):
        self._run_id(run_id)
        with self.directory(f"staging/{run_id}", create=True) as directory:
            fd = os.open(
                reference.sha256,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            try:
                import hashlib

                digest = hashlib.sha256()
                total = 0
                with os.fdopen(fd, "wb", closefd=False) as output:
                    while True:
                        block = stream.read(
                            min(65536, reference.size_bytes - total + 1)
                        )
                        if not isinstance(block, bytes):
                            raise InvalidInput("binary stream required")
                        if not block:
                            break
                        total += len(block)
                        if total > reference.size_bytes or total > MAX_BYTES:
                            raise IntegrityError("artifact size mismatch")
                        output.write(block)
                        digest.update(block)
                    if (
                        total != reference.size_bytes
                        or digest.hexdigest() != reference.sha256
                    ):
                        raise IntegrityError("artifact hash or size mismatch")
                    output.flush()
                    _sync(fd)
                _sync(directory)
            finally:
                os.close(fd)

    def install(self, run_id, reference: ArtifactReference):
        self._run_id(run_id)
        with self.directory(f"staging/{run_id}") as staged:
            with self.directory(
                f"blobs/sha256/{reference.sha256[:2]}", create=True
            ) as target:
                # Validate the exact inode about to be linked. Never link an input file.
                self._read_at(staged, reference)
                try:
                    os.link(
                        reference.sha256,
                        reference.sha256,
                        src_dir_fd=staged,
                        dst_dir_fd=target,
                        follow_symlinks=False,
                    )
                    _sync(target)
                except FileExistsError:
                    self._read_at(target, reference)
                os.unlink(reference.sha256, dir_fd=staged)
                _sync(staged)
                self._read_at(target, reference)

    @staticmethod
    def _read_at(directory, reference):
        import hashlib

        fd = os.open(reference.sha256, FILE_FLAGS, dir_fd=directory)
        try:
            info = _private(fd)
            if info.st_size != reference.size_bytes:
                raise IntegrityError("artifact size mismatch")
            digest = hashlib.sha256()
            output = bytearray()
            while True:
                block = os.read(fd, 65536)
                if not block:
                    break
                output.extend(block)
                if len(output) > reference.size_bytes:
                    raise IntegrityError("artifact changed while reading")
                digest.update(block)
            if (
                len(output) != reference.size_bytes
                or digest.hexdigest() != reference.sha256
            ):
                raise IntegrityError("artifact hash mismatch")
            return bytes(output)
        finally:
            os.close(fd)

    def read(self, reference: ArtifactReference):
        with self.directory(f"blobs/sha256/{reference.sha256[:2]}") as directory:
            return self._read_at(directory, reference)


def create_layout(root):
    """Explicit initialization only; existing nonempty roots are never adopted."""
    root = explicit_root(root)
    parent = _open_directory(root.parent)
    try:
        try:
            os.mkdir(root.name, 0o700, dir_fd=parent)
            _sync(parent)
        except FileExistsError:
            pass
    finally:
        os.close(parent)
    artifacts = _Artifacts(root)
    with artifacts.directory() as fd:
        if os.listdir(fd):
            raise Unavailable("initialization requires an empty root")
        for name in (".content-maintenance.lock", ".content-db.lock"):
            lock = os.open(
                name,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                0o600,
                dir_fd=fd,
            )
            os.close(lock)
        _sync(fd)
    for directory in ("blobs/sha256", "staging", "locks"):
        with artifacts.directory(directory, create=True):
            pass
    return artifacts
