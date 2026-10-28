#!/usr/bin/env python3
"""Download-only entrypoint. No C16/admission/processing command is exposed."""

import argparse
import fcntl
import hashlib
import json
import os
import signal
import socket
from pathlib import Path
from types import SimpleNamespace


def check(specs, data):
    from scripts.cs50p_mvp import admit
    from src.job_control.operations import private
    from src.tools_materials import batch as api
    from src.tools_materials.capacity import check_capacity, load_limits

    batch = api.load_batch(specs / "batch.json")
    if batch.source_origin != "official":
        raise PermissionError("Official reviewed snapshots required")
    limits = load_limits(specs / "limits.json")
    approvals = api.load_approvals(specs / "approvals.json")
    admit(batch, limits, approvals)
    for name, maximum in (
        ("archive", limits.archive_bytes),
        ("reports", limits.report_bytes),
    ):
        check_capacity(
            private(data / name, directory=True), maximum, limits.reserve_bytes
        )
    if any((data / "archive").rglob(".download-*")):
        raise ValueError("Partial files require investigation")
    return dict(
        status="checked", materials=len(batch.materials), processing_enabled=False
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "download"))
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args(argv)
    if os.geteuid() == 0:
        parser.error("Unprivileged service identity required")
    os.umask(0o077)
    # Resolve the one release pointer before passing paths to safe_path (no symlinks).
    release = Path(__file__).resolve().parents[2]
    specs, data = release / "specs", Path("/var/lib/cs50p-download-only")
    previous_network = socket.getaddrinfo, socket.socket.connect
    previous_signal = None
    if args.command == "preflight":
        # Defense in depth: even accidental additions to preflight cannot resolve/connect.
        def forbidden(*_a, **_k):
            raise PermissionError("Preflight network access forbidden")

        socket.getaddrinfo = forbidden
        socket.socket.connect = forbidden
    lock = None
    try:
        # Held through the entire run: package changes fail while a download is running.
        lock = os.open(
            "/opt/.cs50p-download-only-install.lock", os.O_RDONLY | os.O_NOFOLLOW
        )
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        manifest = json.loads((release / "ready.json").read_bytes())
        for name, expected in manifest["files"].items():
            path = release / name
            if (
                path.is_symlink()
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected
            ):
                raise ValueError("Sealed release integrity failed")
        result = check(specs, data)
        code = 0
        if args.command == "download":
            from scripts.cs50p_mvp import download

            def interrupted(_signum, _frame):
                raise KeyboardInterrupt

            previous_signal = signal.signal(signal.SIGTERM, interrupted)
            result, code = download(
                SimpleNamespace(
                    batch=specs / "batch.json",
                    approvals=specs / "approvals.json",
                    limits=specs / "limits.json",
                    archive=data / "archive",
                    reports=data / "reports",
                    confirm=True,
                    retry_failed=args.retry_failed,
                )
            )
        print(json.dumps(result, ensure_ascii=False))
        return code
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(json.dumps(dict(status="blocked", error_class=type(error).__name__)))
        return 2
    finally:
        socket.getaddrinfo, socket.socket.connect = previous_network
        if previous_signal is not None:
            signal.signal(signal.SIGTERM, previous_signal)
        if lock is not None:
            os.close(lock)


if __name__ == "__main__":
    raise SystemExit(main())
