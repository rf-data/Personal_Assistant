"""C26 explicit serial downloader and existing C16/C18 batch handoff."""

import argparse
import json
import os
import sqlite3
from pathlib import Path

from src.job_control.models import fingerprint
from src.tools_materials import batch as api


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("plan")
    a.add_argument("--manifest", type=Path, required=True)
    a.add_argument("--course", action="append", required=True)
    a.add_argument("--resource", action="append", default=[])
    a.add_argument("--synthetic", action="store_true")
    a.add_argument("--output", type=Path, required=True)
    for command in ("download", "seal"):
        a = sub.add_parser(command)
        a.add_argument("--batch", type=Path, required=True)
        a.add_argument("--archive", type=Path, required=True)
        a.add_argument("--approvals", type=Path)
        a.add_argument("--confirm", action="store_true")
        if command == "download":
            a.add_argument("--retry-failed", action="store_true")
        a.add_argument("--output", type=Path, required=command == "seal")
    a = sub.add_parser("workflow")
    a.add_argument(
        "action", choices=("preview", "execute", "resume", "cancel", "report")
    )
    for name in ("config", "token-file", "catalog"):
        a.add_argument("--" + name, type=Path, required=True)
    a.add_argument("--source-ref", action="append", default=[])
    a.add_argument("--confirm", action="store_true")
    a.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    os.umask(0o077)
    try:
        if args.command == "plan":
            batch = api.plan(
                args.manifest, args.course, args.resource, synthetic=args.synthetic
            )
            result = dict(
                batch=batch.model_dump(mode="json"),
                sha256=fingerprint(batch.model_dump(mode="json")),
            )
            api.output(args.output, result)
        elif args.command in {"download", "seal"}:
            batch = api.load_batch(args.batch)
            approvals = (
                api.load_approvals(args.approvals)
                if args.approvals
                else api.Approvals()
            )
            if args.command == "seal":
                if not args.confirm:
                    raise PermissionError(
                        "Explicit catalog publication confirmation required"
                    )
                result = api.seal(batch, args.archive, args.output, approvals)
            else:
                result = api.obtain(
                    batch,
                    args.archive,
                    approvals,
                    execute=args.confirm,
                    retry_failed=args.retry_failed,
                )
                if args.output:
                    api.output(args.output, result)
        else:
            result = api.control(
                args.config,
                args.token_file,
                args.catalog,
                args.action,
                args.source_ref,
                confirm=args.confirm,
            )
            if args.output:
                api.output(args.output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        rows = result.get("materials", [])
        failed = any(r["status"] in {"blocked", "failed", "unsupported"} for r in rows)
        failed |= any(
            w["report"]["status"] in {"failed", "blocked", "cancelled", "interrupted"}
            for w in result.get("workflows", [])
        )
        return 1 if failed else 0
    except (ValueError, OSError, RuntimeError, KeyError, sqlite3.Error) as error:
        print(json.dumps(dict(status="rejected", error_class=type(error).__name__)))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
