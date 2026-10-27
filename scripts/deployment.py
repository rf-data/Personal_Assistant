"""Explicit C22 local operations and managed C16 role entrypoint."""

import argparse
import json
import os
import signal
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

from src.job_control.operations import (
    backup,
    fence,
    health,
    preflight,
    restore,
    volume_probe,
)


def api_configuration(args, settings):
    """Load explicit private bindings; validate without opening/creating stores."""
    if not any((args.content_config, args.review_config, args.search_config)) and not (
        settings.index_jobs_enabled or settings.import_jobs_enabled
    ):
        return {}

    from src.content_store.reader import load_content_settings
    from src.content_store.search_http import load_search_settings
    from src.evaluation_store.http import load_review_settings
    from src.job_control.http import Application

    content = (
        load_content_settings(args.content_config) if args.content_config else None
    )
    review = load_review_settings(args.review_config) if args.review_config else None
    search = load_search_settings(args.search_config) if args.search_config else None
    if review is not None and (content is None or review.content != content):
        raise ValueError("Review and API require the same content configuration")
    # Application already owns root separation and import/index dependencies.
    # Only its constructor is used here; no Controller/Store initialization.
    options = dict(
        content_settings=content, review_settings=review, search_settings=search
    )
    Application(SimpleNamespace(settings=settings), **options)
    return options


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "probe", "api", "worker", "health", "backup"):
        p = sub.add_parser(command)
        p.add_argument("--config", type=Path, required=True)
        if command in {"api", "health"}:
            p.add_argument("--port", type=int, default=8016)
        if command == "health":
            p.add_argument("--role", choices=("api", "worker"), required=True)
        if command == "backup":
            p.add_argument("--output", type=Path, required=True)
        if command in {"api", "check", "health"}:
            for name in ("content", "review", "search"):
                p.add_argument(
                    "--" + name + "-config",
                    type=Path,
                    help="Explicit private " + name + " settings (API/check only)",
                )
    p = sub.add_parser("restore")
    p.add_argument("--snapshot", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if hasattr(args, "port") and not 1024 <= args.port <= 65535:
        parser.error("Nonprivileged loopback port required")
    if (
        args.command == "health"
        and args.role != "api"
        and any((args.content_config, args.review_config, args.search_config))
    ):
        parser.error("Content/review/search configuration requires the API role")
    os.umask(0o077)
    if args.command == "restore":
        result = restore(args.snapshot, args.output)
    elif args.command == "backup":
        manifest = backup(args.config, args.output)
        result = {
            "schema_version": 1,
            "files": len(manifest["files"]),
            "status": "backed_up",
        }
    else:
        settings = preflight(args.config)
        options = (
            api_configuration(args, settings)
            if args.command in {"api", "check"}
            or (args.command == "health" and args.role == "api")
            else {}
        )
        if args.command == "probe":
            result = volume_probe(settings.root)
        elif args.command == "check":
            result = {
                "schema_version": 1,
                "status": "ready",
                "catalogs": len(settings.catalog),
            }
        elif args.command == "health":
            health(settings, args.role, port=args.port)
            result = {"schema_version": 1, "status": "healthy", "role": args.role}
        else:
            with fence(settings.root):
                if args.command == "api":
                    from src.job_control.controller import Controller
                    from src.job_control.http import serve

                    def stop(_signum, _frame):
                        raise SystemExit(0)

                    signal.signal(signal.SIGTERM, stop)
                    serve(Controller(settings), args.port, **options)
                else:
                    from src.job_control.executor import Executor

                    Executor(settings).serve()
            return 0
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
        print(
            "Deployment operation refused (" + type(error).__name__ + ")",
            file=sys.stderr,
        )
        raise SystemExit(2) from None
