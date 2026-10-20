"""Separate-process fault injection on owned synthetic import test roots only."""

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
    a = p.parse_args()
    store = Store(a.root)
    directory = store.directory(a.job)
    directory.mkdir(mode=0o700)
    if a.phase == "timeout":
        from src.job_control import registry
        from src.job_control.guardian import execute

        registry.IMPORT_PROCESS = replace(registry.IMPORT_PROCESS, timeout_seconds=0.2)
        execute(store.root, a.job, os.getppid())
        return 0
    store.transition(a.job, "running", "probe", "Synthetic fault probe")
    fd = os.open(directory / "execution.lock", os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def paused():
        (store.root / "probe-ready").write_text(a.phase)
        time.sleep(60)

    from src.content_store import publication

    original = publication.finish_publication

    def finish(*args, **kw):
        if a.phase == "before_publication":
            paused()
        result = original(*args, **kw)
        return result

    publication.finish_publication = finish
    from src.job_control import import_jobs

    original_import = import_jobs.import_verified_bundle

    def imported(*args, **kwargs):
        result = original_import(*args, **kwargs)
        if a.phase == "after_publication":
            paused()
        return result

    import_jobs.import_verified_bundle = imported
    from src.job_control.adapter_worker import execute

    try:
        return execute(store, a.job)
    finally:
        os.close(fd)


if __name__ == "__main__":
    raise SystemExit(main())
