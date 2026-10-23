"""Offline week inventory and plans. No acquisition, parser jobs or worker start."""

import argparse
import sys
from pathlib import Path

from src.job_control.catalog import read_file, safe_path
from src.model_materials.week import ProfiledWeekRequest, WeekRequest
from src.tools_materials.batch import Approvals
from src.tools_materials.quality import _json
from src.tools_materials.week import plan_week


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, help="Existing validated fixture manifest"
    )
    parser.add_argument("--week", default="0")
    parser.add_argument(
        "--request",
        type=Path,
        help="Explicit WeekRequest JSON; artifact reads require this form",
    )
    parser.add_argument(
        "--approvals", type=Path, help="Existing per-source Approvals JSON"
    )
    args = parser.parse_args(argv)
    if bool(args.manifest) == bool(args.request):
        parser.error("Supply exactly one of --manifest or --request")
    try:
        if args.request:
            data = _json(read_file(safe_path(args.request), 1048576))
            model = (
                ProfiledWeekRequest if data.get("schema_version") == 2 else WeekRequest
            )
            request = model.model_validate(data)
        else:
            request = WeekRequest(manifest=args.manifest.absolute(), week=args.week)
        approvals = (
            Approvals.model_validate(
                _json(read_file(safe_path(args.approvals), 1048576))
            )
            if args.approvals
            else Approvals()
        )
        result = plan_week(request, approvals)
        sys.stdout.write(result.model_dump_json(indent=2) + "\n")
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Week plan rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
