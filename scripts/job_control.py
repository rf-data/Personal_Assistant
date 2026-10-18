"""Explicit local controller/worker startup. No productive defaults or deployments."""

import argparse
import sqlite3
import sys

from src.job_control.models import load_settings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["api", "worker", "check"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--port", type=int, default=8016)
    parser.add_argument(
        "--content-config",
        help="Explicit private content-read-v1 configuration (API only)",
    )
    parser.add_argument(
        "--review-config",
        help="Explicit private evaluation-review-v1 configuration (API only)",
    )
    args = parser.parse_args(argv)
    if args.content_config and args.command != "api":
        parser.error("--content-config is API-only")
    if args.review_config and args.command != "api":
        parser.error("--review-config is API-only")
    settings = load_settings(args.config)
    if not 1024 <= args.port <= 65535:
        parser.error("Nonprivileged local port required")
    if args.command == "api":
        from src.content_store.reader import load_content_settings
        from src.job_control.controller import Controller
        from src.job_control.http import serve

        content = (
            load_content_settings(args.content_config) if args.content_config else None
        )
        from src.evaluation_store.http import load_review_settings

        review = (
            load_review_settings(args.review_config) if args.review_config else None
        )
        serve(
            Controller(settings),
            args.port,
            content_settings=content,
            review_settings=review,
        )
    elif args.command == "worker":
        from src.job_control.executor import Executor

        Executor(settings).serve()
    else:
        from src.job_control.catalog import verified_files

        for entry in settings.catalog.values():
            verified_files(entry)
        print("Configuration and declared input hashes valid; no job created")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError, ImportError, sqlite3.Error) as error:
        print(
            "Job control stopped ("
            + type(error).__name__
            + "); check private configuration and state",
            file=sys.stderr,
        )
        raise SystemExit(2) from None
