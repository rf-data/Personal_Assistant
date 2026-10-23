"""Read-only C26 capacity observation. Never creates directories or permits work."""

import argparse
import json
import os
import shutil
from pathlib import Path

from src.job_control.catalog import safe_path
from src.tools_materials.batch import load_batch
from src.tools_materials.capacity import MIB, CapacityLimits, estimate, free_space


def check(parent, *, purpose="zip-import", batch=None):
    if not Path(parent).is_absolute():
        raise ValueError("Explicit absolute target required")
    parent = safe_path(Path(parent))
    if not parent.is_absolute() or not parent.is_dir():
        raise ValueError("Explicit existing target parent required")
    limits = CapacityLimits(
        reserve_bytes=5 * 1024**3, archive_bytes=64 * MIB, max_materials=8
    )
    if purpose == "week-pilot":
        if batch is None:
            raise ValueError("Explicit verified batch required for week pilot estimate")
        budget = estimate(batch, limits)
        additional = (
            budget["required_free_before_new_batch_bytes"] - limits.reserve_bytes
        )
    elif purpose == "zip-import" and batch is None:
        budget = dict(
            archive_budget_bytes=limits.archive_bytes,
            report_budget_bytes=limits.report_bytes,
        )
        additional = limits.archive_bytes + limits.report_bytes
    else:
        raise ValueError("Unknown purpose or ambiguous batch selection")
    usage = shutil.disk_usage(parent)
    filesystem = os.statvfs(parent)
    inode_free = filesystem.f_favail if filesystem.f_files > 0 else None
    blockers = []
    try:
        free_space(parent, limits.reserve_bytes, additional)
    except ValueError:
        blockers.append(
            "insufficient_free_bytes_with_existing_reserve_and_output_allowance"
        )
    if inode_free == 0:
        blockers.append("no_available_inodes")
    return dict(
        schema_version=1,
        purpose=purpose,
        status="blocked" if blockers else "operator_action_required",
        execution_permitted=False,
        free_bytes=usage.free,
        reserve_bytes=limits.reserve_bytes,
        additional_allowance_bytes=additional,
        required_free_bytes=limits.reserve_bytes + additional,
        inode_free=inode_free,
        inode_status="unknown" if inode_free is None else "observed",
        blockers=blockers,
        operator_checks=[
            "correct_target_filesystem_and_mount",
            "inode_capacity"
            if inode_free is None
            else "fresh_capacity_before_each_write",
            "source_approvals_and_hash_bindings",
            "worker_and_queue_if_applicable",
        ],
        budget=budget,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-parent", type=Path, required=True)
    parser.add_argument(
        "--purpose", choices=("zip-import", "week-pilot"), default="zip-import"
    )
    parser.add_argument("--batch", type=Path)
    args = parser.parse_args(argv)
    try:
        if not args.target_parent.is_absolute():
            raise ValueError("Explicit absolute target required")
        report = check(
            args.target_parent,
            purpose=args.purpose,
            batch=load_batch(args.batch) if args.batch else None,
        )
    except (OSError, ValueError, RuntimeError) as error:
        report = dict(
            schema_version=1,
            status="blocked",
            execution_permitted=False,
            error_class=type(error).__name__,
        )
    print(json.dumps(report, indent=2))
    return 3 if report["status"] == "blocked" else 4


if __name__ == "__main__":
    raise SystemExit(main())
