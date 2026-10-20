"""Read-only bounded file inventory for operator-approved copy verification.

Only explicitly supplied roots are read. No SSH, copying, cloud API or deletion.
Output contains relative filenames and belongs in a private operator evidence root.
This stdlib-only script can also be supplied on stdin to an authorized remote Python.
"""

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path


def inventory(root, *, max_entries=20000, max_bytes=2 * 1024**3):
    root = Path(root)
    if not root.is_absolute() or ".." in root.parts:
        raise ValueError("Explicit absolute root required")
    for path in (root, *root.parents):
        if not stat.S_ISDIR(path.lstat().st_mode):
            raise ValueError("Only real directory components allowed")
    files, directories, observed = [], [], []
    total, entries = 0, 0
    device = root.stat().st_dev

    def signature(info):
        return (
            info.st_dev,
            info.st_ino,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
        )

    def failed(error):
        raise error

    for base, dirs, names in os.walk(root, followlinks=False, onerror=failed):
        base = Path(base)
        current = base.lstat()
        if not stat.S_ISDIR(current.st_mode):
            raise ValueError("Directory changed or unsafe")
        observed.append((base, signature(current)))
        for name in sorted(dirs + names):
            entries += 1
            if entries > max_entries:
                raise ValueError("Entry limit exceeded")
            path = base / name
            before = path.lstat()
            relative = path.relative_to(root).as_posix()
            if before.st_dev != device:
                raise ValueError("Cross-filesystem input forbidden")
            if stat.S_ISDIR(before.st_mode):
                directories.append(relative)
                continue
            if not stat.S_ISREG(before.st_mode):
                raise ValueError("Only regular files/directories allowed")
            total += before.st_size
            if total > max_bytes:
                raise ValueError("Byte limit exceeded")
            digest, size = hashlib.sha256(), 0
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor, "rb") as stream:
                opened = os.fstat(stream.fileno())
                if not stat.S_ISREG(opened.st_mode) or signature(opened) != signature(
                    before
                ):
                    raise ValueError("File changed before reading")
                while chunk := stream.read(65536):
                    size += len(chunk)
                    if size > before.st_size:
                        raise ValueError("File grew while reading")
                    digest.update(chunk)
                if (
                    size != before.st_size
                    or signature(os.fstat(stream.fileno())) != signature(before)
                    or signature(path.lstat()) != signature(before)
                ):
                    raise ValueError("File changed while reading")
            files.append(
                dict(path=relative, size_bytes=size, sha256=digest.hexdigest())
            )
    for path, before in observed:
        if signature(path.lstat()) != before or path.stat().st_dev != device:
            raise ValueError("Directory changed or crossed filesystem")
    return dict(
        schema_version=1,
        kind="c26-copy-inventory",
        directories=sorted(directories),
        files=sorted(files, key=lambda f: f["path"]),
        total_bytes=total,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    try:
        result = inventory(args.root)
    except (OSError, ValueError) as error:
        print(json.dumps(dict(status="blocked", error_class=type(error).__name__)))
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
