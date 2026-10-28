"""Local processing plan/verification CLI; production execution is HOLD."""

import argparse
from pathlib import Path

from scripts.cs50p_week import load_inventory, output
from src.tools_materials.week_acquisition import completeness
from src.tools_materials.week_processing import plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "report"))
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--processing-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    inventory = load_inventory(args.inventory)
    if args.command == "report" and (
        args.archive is None or args.processing_root is None
    ):
        parser.error("report requires --archive and --processing-root")
    result = (
        plan(inventory)
        if args.command == "plan"
        else completeness(inventory, args.archive, args.processing_root)
    )
    output(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
