"""Read-only C26 bootstrap checks. Never opens a queue or grants activation.

Run as the runtime UID with the approved runtime bind and private mount policy.
This checks the disabled staging configuration, not a live activated controller.
"""

import argparse
import json
import os
import re
import shutil
import sqlite3
from pathlib import Path

from src.job_control.models import load_settings
from src.job_control.operations import private
from src.runtime_paths import checked_path, mounts
from src.tools_materials.capacity import load_limits, tree_bytes

MIB = 1024**2
MAXIMUMS = dict(
    archive_bytes=64 * MIB,
    catalog_bytes=128 * MIB,
    job_bytes=512 * MIB,
    report_bytes=16 * MIB,
    max_materials=1,
)


def inspect(config, limits_path, runtime_mount, runtime_image, gateway_image):
    # Reuse #148's exact immutable-image contract; do not construct Gate/Store.
    from src.job_control.deployment_gate import IMAGE

    for image in (runtime_image, gateway_image):
        if not isinstance(image, str) or re.fullmatch(IMAGE, image) is None:
            raise ValueError("Reviewed immutable image references required")
    settings = load_settings(private(Path(config)))
    limits = load_limits(limits_path)
    point = checked_path(runtime_mount)
    root = checked_path(settings.root)
    if root != point / "c16" or any(
        part.startswith("cs50_pilot") for part in point.parts
    ):
        raise ValueError("Separate runtime bind and c16 subtree required")
    identity = mounts().get(point)
    if (
        not identity
        or identity["filesystem"] not in {"ext4", "xfs", "btrfs"}
        or identity["root"] == "/"
        or identity["writable"] is not True
    ):
        raise ValueError("Explicit persistent writable bind required")
    if (
        not settings.deployment_gate_required
        or settings.execution_enabled
        or settings.workflows_enabled
        or settings.pdf_enabled
        or settings.index_jobs_enabled
        or settings.import_jobs_enabled
        or settings.identities
        or settings.catalog
        or (settings.max_parallel, settings.max_queued, settings.max_jobs) != (1, 1, 1)
    ):
        raise ValueError("Disabled empty single-job staging configuration required")
    if limits.reserve_bytes < 5 * 1024**3 or any(
        getattr(limits, key) > maximum for key, maximum in MAXIMUMS.items()
    ):
        raise ValueError("Conservative bootstrap limits required")
    private(root, directory=True)
    if not os.access(root, os.W_OK | os.X_OK) or (root / "quarantine").exists():
        raise ValueError("Writable nonquarantined private root required")
    used = tree_bytes(root, limits.job_bytes)
    # Conservative full allowances, not the artifact-dependent batch estimate.
    required = limits.reserve_bytes + sum(
        getattr(limits, name)
        for name in ("archive_bytes", "catalog_bytes", "job_bytes", "report_bytes")
    )
    free = shutil.disk_usage(root).free
    if free < required:
        raise ValueError("Insufficient free space for reserve and full job allowances")
    return dict(
        schema_version=1,
        status="disabled_configuration_valid",
        root=str(root),
        root_bytes=used,
        required_free_bytes=required,
        free_bytes=free,
        queue_status="present_unverified"
        if (root / "jobs.sqlite3").exists()
        else "uninitialized",
        queue_healthy=False,
        execution_enabled=False,
        deployment_permitted=False,
        production_release="blocked",
        image_provenance_verified=False,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--limits", type=Path, required=True)
    parser.add_argument("--runtime-mount", type=Path, required=True)
    parser.add_argument("--runtime-image", required=True)
    parser.add_argument("--gateway-image", required=True)
    args = parser.parse_args(argv)
    try:
        result = inspect(
            args.config,
            args.limits,
            args.runtime_mount,
            args.runtime_image,
            args.gateway_image,
        )
    except (OSError, ValueError, RuntimeError, KeyError, sqlite3.Error):
        print(json.dumps(dict(status="blocked", deployment_permitted=False)))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
