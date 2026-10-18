"""Fixed conservative single-host limits; no retries or production auto-tuning."""

import os
import stat
from contextlib import contextmanager

from src.content_store.artifacts import _private
from src.content_store.errors import Busy, Unavailable

MAX_ACTIVE_RUNS = 32
MAX_FILES = 20000
MAX_STORE_BYTES = 2 * 1024**3
MAX_STAGING_BYTES = 512 * 1024**2
MAX_METADATA_ROWS = 200000
MIN_FREE_BYTES = 1024**2


def capacity(directory, needed):
    info = os.fstatvfs(directory)
    if info.f_bavail * info.f_frsize < needed + MIN_FREE_BYTES:
        raise Unavailable("insufficient content capacity")


@contextmanager
def staging_budget(artifacts, needed):
    import fcntl

    with artifacts.directory("locks") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Busy("staging capacity lock held") from None
        try:
            total, count = 0, 0
            pending = ["staging"]
            while pending:
                relative = pending.pop()
                with artifacts.directory(relative) as fd:
                    for name in directory_entries(fd):
                        count += 1
                        if count > MAX_FILES:
                            raise Unavailable("staging entry limit")
                        meta = os.stat(name, dir_fd=fd, follow_symlinks=False)
                        if stat.S_ISDIR(meta.st_mode):
                            pending.append(relative + "/" + name)
                        elif stat.S_ISREG(meta.st_mode) and meta.st_nlink == 1:
                            total += meta.st_size
                        else:
                            raise Unavailable("unsafe staging entry")
                if total + needed > MAX_STAGING_BYTES:
                    raise Unavailable("staging size limit")
            _private(lock, directory=True)
            capacity(lock, needed)
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def directory_entries(fd, *, limit=MAX_FILES):
    """Bound allocation before consuming an untrusted directory inventory."""
    with os.scandir(fd) as entries:
        for index, entry in enumerate(entries):
            if index >= limit:
                raise Unavailable("directory inventory limit")
            yield entry.name
