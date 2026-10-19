"""Subprocess fault probe for owned synthetic C16 test roots; not a runner route."""

import argparse
import fcntl
import os
import time
from dataclasses import replace

from src.job_control.store import Store


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--job", required=True)
    p.add_argument("--phase", required=True)
    args = p.parse_args()
    store = Store(args.root)
    directory = store.directory(args.job)
    directory.mkdir(mode=0o700)
    if args.phase == "timeout":
        from src.job_control import registry
        from src.job_control.guardian import execute

        registry.INDEX_PROCESS = replace(registry.INDEX_PROCESS, timeout_seconds=0.01)
        execute(store.root, args.job, os.getppid())
        return 0
    store.transition(args.job, "running", "probe", "Synthetic process fault probe")
    fd = os.open(directory / "execution.lock", os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    from src.tools_rag.content_index_files import IndexFiles

    original_write, original_json = IndexFiles.write, IndexFiles.json

    def paused():
        marker = store.root / "probe-ready"
        marker.write_text(args.phase)
        marker.chmod(0o600)
        time.sleep(60)

    def write(self, relative, data, **kwargs):
        if args.phase == "staging_error" and relative.endswith(".sqlite3"):
            raise OSError(28, "synthetic ENOSPC")
        result = original_write(self, relative, data, **kwargs)
        if (
            args.phase == "before_activation"
            and relative.startswith("staging/")
            and relative.endswith("/manifest.json")
        ):
            paused()
        return result

    def json_write(self, relative, value, **kwargs):
        result = original_json(self, relative, value, **kwargs)
        if args.phase == "after_activation" and relative == "active.json":
            paused()
        return result

    IndexFiles.write, IndexFiles.json = write, json_write
    from src.job_control.adapter_worker import execute

    try:
        return execute(store, args.job)
    except Exception:
        return 3
    finally:
        os.close(fd)


if __name__ == "__main__":
    raise SystemExit(main())
