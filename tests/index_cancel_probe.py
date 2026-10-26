"""Owned synthetic index build paused under the unchanged C16 guardian."""

import argparse
import os
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--payload", action="store_true")
    args = parser.parse_args()
    if args.payload:
        from src.job_control.adapter_worker import execute
        from src.job_control.store import Store
        from src.tools_rag.content_index_files import IndexFiles

        store = Store(args.root)
        original = IndexFiles.write

        def pause(self, relative, data, **kwargs):
            result = original(self, relative, data, **kwargs)
            if relative.startswith("staging/") and relative.endswith("/manifest.json"):
                marker = store.root / "cancel-ready.tmp"
                marker.write_text(str(os.getpid()))
                marker.chmod(0o600)
                marker.replace(store.root / "cancel-ready")
                time.sleep(30)
            return result

        IndexFiles.write = pause
        return execute(store, args.job)
    from src.job_control import guardian
    from src.job_control.store import Store

    store = Store(args.root)
    store.directory(args.job).mkdir(mode=0o700)
    original = guardian.supervise

    def supervise(command, **kwargs):
        return original(
            [
                sys.executable,
                "-m",
                "tests.index_cancel_probe",
                "--root",
                args.root,
                "--job",
                args.job,
                "--payload",
            ],
            **kwargs,
        )

    guardian.supervise = supervise
    guardian.execute(store.root, args.job, os.getppid())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
