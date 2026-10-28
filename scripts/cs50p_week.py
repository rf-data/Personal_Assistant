"""Explicit snapshot discovery and approved download-only acquisition; C26 HOLD."""

import argparse
import json
import os
import signal
import uuid
from pathlib import Path

from src.job_control.catalog import read_file
from src.job_control.models import fingerprint
from src.model_materials.acquisition import SourceGrant, WeekApproval, WeekInventory
from src.tools_materials import week_acquisition as api
from src.tools_materials.quality import _json
from src.tools_materials.storage import locate, publish_bytes


def output(path, value):
    path = Path(path).absolute()
    locate(path.parent, path.name)
    publish_bytes(
        path, (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
    )


def load_inventory(path):
    return WeekInventory.model_validate(
        _json(read_file(Path(path).absolute(), 8 * 1024**2))
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    discovery = sub.add_parser("discover")
    discovery.add_argument(
        "--snapshots",
        type=Path,
        required=True,
        help="Explicit JSON: course_id, week_id, source_origin, pages[{url,path,sha256}]",
    )
    discovery.add_argument("--output", type=Path, required=True)
    discovery.add_argument("--previous-inventory", type=Path)
    discovery.add_argument("--archive", type=Path)
    for name in (
        "show",
        "plan",
        "approve",
        "check-approval",
        "manual-list",
        "report",
        "acquire",
        "import-code",
    ):
        p = sub.add_parser(name)
        p.add_argument("--inventory", type=Path, required=True)
        if name != "show":
            p.add_argument("--output", type=Path)
        if name in {"report", "acquire", "import-code"}:
            p.add_argument("--archive", type=Path, required=True)
        if name == "approve":
            p.add_argument(
                "--selection",
                type=Path,
                required=True,
                help="Operator-authored list of exact SourceGrant objects",
            )
            p.add_argument("--reviewed-by", required=True)
            p.add_argument("--review-reference", required=True)
            p.add_argument("--transfer-bytes", type=int, required=True)
        if name in {"approve", "check-approval"}:
            p.add_argument(
                "--purpose", choices=("download", "discovery"), default="download"
            )
            p.add_argument("--retry-failed", action="store_true")
        if name == "check-approval":
            p.add_argument("--approval", type=Path, required=True)
        if name == "acquire":
            p.add_argument("--approval", type=Path, required=True)
            p.add_argument("--confirm", action="store_true")
            p.add_argument("--retry-failed", action="store_true")
            p.add_argument(
                "--purpose", choices=("download", "discovery"), default="download"
            )
            p.add_argument("--checkpoints", type=Path, required=True)
        if name == "import-code":
            p.add_argument("--material-id", required=True)
            p.add_argument("--file", type=Path, required=True)
            p.add_argument("--sha256", required=True)
            p.add_argument("--provenance", required=True)
    args = parser.parse_args(argv)
    os.umask(0o077)
    previous = None
    try:
        if getattr(args, "output", None):
            destination = args.output.absolute()
            locate(destination.parent, destination.name)
            if destination.exists():
                raise FileExistsError(
                    "Output already exists; choose a new report/inventory path"
                )
        if args.command == "discover":
            config = _json(read_file(args.snapshots.absolute(), 1024**2))
            if (
                set(config) != {"course_id", "week_id", "source_origin", "pages"}
                or not 1 <= len(config["pages"]) <= 64
            ):
                raise ValueError("Explicit bounded snapshot configuration required")
            pages = {}
            for entry in config["pages"]:
                if set(entry) != {"url", "path", "sha256"} or entry["url"] in pages:
                    raise ValueError("Duplicate/invalid snapshot entry")
                raw = read_file(
                    locate(args.snapshots.absolute().parent, entry["path"]), 1024**2
                )
                if api.sha(raw) != entry["sha256"]:
                    raise ValueError("Snapshot hash mismatch")
                pages[entry["url"]] = raw
            if bool(args.previous_inventory) != bool(args.archive):
                raise ValueError(
                    "Rediscovery requires both previous inventory and archive"
                )
            if args.previous_inventory:
                previous_inventory = load_inventory(args.previous_inventory)
                if (
                    previous_inventory.course_id,
                    previous_inventory.week_id,
                    previous_inventory.source_origin,
                ) != (config["course_id"], config["week_id"], config["source_origin"]):
                    raise ValueError(
                        "Rediscovery scope differs from snapshot configuration"
                    )
                for row in previous_inventory.materials:
                    if (
                        row.material_type == "page"
                        and row.acquisition_status == "VERIFIED"
                    ):
                        verified = api.verify_row(
                            row, previous_inventory, args.archive.absolute()
                        )
                        pages[row.source_url] = read_file(
                            locate(
                                args.archive.absolute(), verified.expected_local_path
                            ),
                            1024**2,
                        )
            result = api.discover(
                pages,
                course_id=config["course_id"],
                week_id=config["week_id"],
                source_origin=config["source_origin"],
            ).model_dump(mode="json")
        else:
            inventory = load_inventory(args.inventory)
            if args.command == "show":
                result = inventory.model_dump(mode="json")
            elif args.command == "plan":
                result = api.plan(inventory)
            elif args.command in {"approve", "check-approval"}:
                if args.command == "approve":
                    if args.output is None:
                        raise ValueError("New approval output required")
                    selected = _json(read_file(args.selection.absolute(), 1024**2))
                    approval = WeekApproval(
                        inventory_sha256=fingerprint(inventory.model_dump(mode="json")),
                        source_origin=inventory.source_origin,
                        reviewed_by=args.reviewed_by,
                        review_reference=args.review_reference,
                        transfer_bytes=args.transfer_bytes,
                        grants=tuple(SourceGrant.model_validate(g) for g in selected),
                    )
                else:
                    approval = WeekApproval.model_validate(
                        _json(read_file(args.approval.absolute(), 1024**2))
                    )
                if inventory.source_origin != "official":
                    raise PermissionError(
                        "Production approval commands reject synthetic inventories"
                    )
                api.validate_approval(
                    inventory,
                    approval,
                    purpose=args.purpose,
                    retry_failed=args.retry_failed,
                )
                result = (
                    approval.model_dump(mode="json")
                    if args.command == "approve"
                    else dict(status="CHECKED", processing_enabled=False)
                )
            elif args.command == "manual-list":
                result = [
                    r.model_dump(mode="json")
                    for r in inventory.materials
                    if r.material_type == "source_code"
                ]
            elif args.command == "report":
                result = api.completeness(inventory, args.archive.absolute())
            elif args.command == "import-code":
                if args.output is None:
                    raise ValueError("New --output inventory required")
                result = api.import_manual(
                    inventory,
                    args.material_id,
                    args.file.absolute(),
                    args.sha256,
                    args.archive.absolute(),
                    provenance=args.provenance,
                ).model_dump(mode="json")
            else:
                if not args.confirm or args.output is None or os.geteuid() == 0:
                    raise PermissionError(
                        "Unprivileged identity, --confirm and new --output required"
                    )
                approval = WeekApproval.model_validate(
                    _json(read_file(args.approval.absolute(), 1024**2))
                )
                checkpoint_root = args.checkpoints.absolute()
                locate(checkpoint_root.parent, checkpoint_root.name)
                checkpoint_root.mkdir(parents=True, exist_ok=True, mode=0o700)

                def checkpoint(value):
                    from src.tools_materials.capacity import check_capacity

                    check_capacity(
                        checkpoint_root,
                        inventory.limits.report_bytes,
                        inventory.limits.reserve_bytes,
                        len(value.model_dump_json().encode()) * 2 + 65536,
                    )
                    output(
                        checkpoint_root / ("inventory-" + uuid.uuid4().hex + ".json"),
                        value.model_dump(mode="json"),
                    )

                def interrupted(*_):
                    raise KeyboardInterrupt

                previous = signal.signal(signal.SIGTERM, interrupted)
                result = api.acquire(
                    inventory,
                    approval,
                    args.archive.absolute(),
                    retry_failed=args.retry_failed,
                    checkpoint=checkpoint,
                    purpose=args.purpose,
                ).model_dump(mode="json")
        if getattr(args, "output", None):
            output(args.output, result)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        if args.command == "acquire" and any(
            r["acquisition_status"] == "FAILED" for r in result["materials"]
        ):
            return 1
        return 0
    except KeyboardInterrupt:
        print(
            json.dumps(
                {
                    "status": "HOLD",
                    "reason": "Interrupted; inspect receipts and checkpoints; explicit retry and fresh approval required",
                }
            )
        )
        return 130
    except (ValueError, OSError, RuntimeError, KeyError, StopIteration) as error:
        print(
            json.dumps({"status": "HOLD", "error": f"{type(error).__name__}: {error}"})
        )
        return 2
    finally:
        if previous is not None:
            signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    raise SystemExit(main())
