"""Explicit offline CS50 bundle inventory. Never imports or migrates content."""

import argparse
import sys
from pathlib import Path

from src.content_store.adapters import _json_bytes, _read
from src.content_store.errors import ContentStoreError
from src.content_store.inventory import (
    InventoryRequest,
    inventory,
    output_path,
    report_bytes,
)
from src.content_store.store import ContentStore
from src.job_control.models import Principal
from src.tools_materials.storage import publish_bytes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument(
        "--store", type=Path, help="Optional existing private ContentStore"
    )
    parser.add_argument("--actor", required=True)
    parser.add_argument("--course", action="append", required=True)
    parser.add_argument("--output", type=Path, help="New JSON report, otherwise stdout")
    args = parser.parse_args(argv)
    try:
        request = InventoryRequest.model_validate(_json_bytes(_read(args.selection)))
        actor = Principal(
            subject=args.actor, role="operator", courses=tuple(args.course)
        )
        store = ContentStore(args.store) if args.store else None
        target = None
        if args.output:
            target = output_path(
                args.output, request, store_root=store.root if store else None
            )
            if target == args.selection.absolute():
                raise ValueError("Report overlaps selection")
        report = inventory(request, actor=actor, store=store)
        data = report_bytes(report)
        if target:
            publish_bytes(target, data)
        else:
            sys.stdout.write(data.decode("utf-8"))
        for result in report.report.entries:
            print(
                f"{result.entry_id}: {result.validation_status} source={result.source_id} "
                f"course={result.course_id} existing={result.existing_parsed_version_id or '-'} "
                f"issues={','.join(result.issues) or '-'} approvals={','.join(result.manual_approvals) or '-'}",
                file=sys.stderr,
            )
        return int(any(r.validation_status == "blocked" for r in report.report.entries))
    except (OSError, ValueError, RecursionError, ContentStoreError):
        print("Inventory input, store or report publication rejected", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
