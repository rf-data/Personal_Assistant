"""Offline visual inventory: JSON stdout and Markdown stderr unless paths supplied."""

import argparse
import sys
from pathlib import Path

from src.model_materials.visual_inventory import InventoryLimits
from src.tools_lecture.execute_cs50 import safe_path
from src.tools_materials.storage import publish_bytes
from src.tools_materials.visual_inventory import inventory, json_bytes, markdown


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normalized", type=Path, required=True)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--raw", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument(
        "--plan",
        type=Path,
        help="Optional existing MaterialPlan for graph verification",
    )
    parser.add_argument("--json-report", type=Path)
    parser.add_argument("--markdown-report", type=Path)
    parser.add_argument(
        "--limits", type=Path, help="Explicit local InventoryLimits JSON"
    )
    args = parser.parse_args(argv)
    try:
        outputs = [p.absolute() for p in (args.json_report, args.markdown_report) if p]
        if len(outputs) != len(set(outputs)):
            raise ValueError("JSON and Markdown outputs must be different paths")
        root = args.input_root.absolute()
        for path in outputs:
            safe_path(path.parent, path)
            if (
                path.is_relative_to(root)
                or path.exists()
                or (args.limits and path == args.limits.absolute())
            ):
                raise ValueError(
                    "Reports must be new paths outside the input artifact root"
                )
            if not path.parent.is_dir():
                raise ValueError("Report parent directory must already exist")
        limits = InventoryLimits()
        if args.limits:
            from src.tools_materials.visual_inventory import read_bounded, strict_json

            limits = InventoryLimits.model_validate(
                strict_json(
                    read_bounded(
                        args.limits.absolute().parent, args.limits.absolute(), 65536
                    )
                )
            )
        report = inventory(
            args.normalized,
            input_root=root,
            raw_path=args.raw,
            artifact_root=args.artifact_root,
            receipt_path=args.receipt,
            plan_path=args.plan,
            limits=limits,
        )
        encoded = json_bytes(report.model_dump(mode="json"))
        summary = markdown(report)
        if args.json_report:
            publish_bytes(args.json_report.absolute(), encoded)
        else:
            sys.stdout.write(encoded.decode())
        if args.markdown_report:
            publish_bytes(args.markdown_report.absolute(), summary.encode())
        else:
            sys.stderr.write(summary)
    except (OSError, ValueError) as error:
        print(f"Visual inventory failed: {error}", file=sys.stderr)
        return 2
    print(
        f"Visual assets={report.counts['assets']} available={report.counts['available_artifacts']} "
        f"references={report.counts['reference_only']} review={report.counts['review_candidates']} "
        f"errors={report.counts['errors']}",
        file=sys.stderr,
    )
    return 1 if report.counts["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
