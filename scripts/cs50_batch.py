"""C26 explicit serial downloader and existing C16/C18 batch handoff."""

import argparse
import json
import os
import sqlite3
from pathlib import Path

from src.job_control.models import fingerprint
from src.tools_materials import batch as api
from src.tools_materials.capacity import CapacityLimits, estimate, load_limits


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
    a = sub.add_parser(
        "transcripts", help="Explicit offline SRT/TXT lane; no HTTP or C18 publication"
    )
    a.add_argument("action", choices=("preview", "import", "report"))
    for name in ("batch", "archive", "approvals"):
        a.add_argument("--" + name, type=Path, required=True)
    a.add_argument("--inputs", type=Path)
    a.add_argument("--confirm", action="store_true")
    a.add_argument("--output", type=Path)
    a = sub.add_parser(
        "inventory", help="Week-0 snapshot references; no material reads or downloads"
    )
    a.add_argument("--manifest", type=Path, required=True)
    a.add_argument("--output", type=Path)
    for parser in sub.choices.values():
        parser.add_argument(
            "--limits", type=Path, default=os.environ.get("C26_LIMITS_FILE")
        )
    args = p.parse_args(argv)
    os.umask(0o077)
    try:
        limits = load_limits(args.limits) if args.limits else CapacityLimits()
        if args.command == "plan":
            batch = api.plan(
                args.manifest, args.course, args.resource, synthetic=args.synthetic
            )
            result = dict(
                batch=batch.model_dump(mode="json"),
                sha256=fingerprint(batch.model_dump(mode="json")),
                capacity_plan=estimate(batch, limits),
                capacity_limits=limits.model_dump(mode="json"),
            )
            api.output(args.output, result, limits=limits)
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
                result = api.seal(
                    batch, args.archive, args.output, approvals, limits=limits
                )
            else:
                result = api.obtain(
                    batch,
                    args.archive,
                    approvals,
                    execute=args.confirm,
                    retry_failed=args.retry_failed,
                    limits=limits,
                )
                if args.output:
                    api.output(
                        args.output,
                        result,
                        limits=limits,
                        budget=limits.archive_bytes
                        if args.output.parent == args.archive
                        else limits.report_bytes,
                    )
        elif args.command in {"transcripts", "inventory"}:
            from src.tools_materials import transcripts

            if args.command == "inventory":
                result = transcripts.week_inventory(args.manifest)
            else:
                if not args.limits or (args.action == "import" and not args.confirm):
                    raise PermissionError(
                        "Explicit limits and import confirmation required"
                    )
                if args.action != "report" and args.inputs is None:
                    raise ValueError("Explicit local source mapping required")
                result = transcripts.run(
                    api.load_batch(args.batch),
                    args.archive,
                    api.load_approvals(args.approvals),
                    transcripts.load_inputs(args.inputs) if args.inputs else {},
                    action=args.action,
                    limits=limits,
                )
            if args.output:
                api.output(args.output, result, limits=limits)
        else:
            result = api.control(
                args.config,
                args.token_file,
                args.catalog,
                args.action,
                args.source_ref,
                confirm=args.confirm,
                limits=limits,
            )
            if args.output:
                api.output(args.output, result, limits=limits)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        rows = result.get("materials", [])
        failed = any(
            r["status"] in {"blocked", "failed", "unsupported", "missing"} for r in rows
        )
        failed |= any(
            w["report"]["status"] in {"failed", "blocked", "cancelled", "interrupted"}
            for w in result.get("workflows", [])
        )
        failed |= bool(
            set(result.get("summary", {}).get("status_counts", {}))
            & {"failed", "blocked", "interrupted", "cancelled", "unsupported", "stale"}
        )
        return 1 if failed else 0
    except (ValueError, OSError, RuntimeError, KeyError, sqlite3.Error) as error:
        print(json.dumps(dict(status="rejected", error_class=type(error).__name__)))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
