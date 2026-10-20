"""Evaluate existing formula pairs offline; no extraction or Knowledge mutations."""

import argparse
import sys
from pathlib import Path

from src.tools_evaluation.evaluate_math import evaluate_dataset
from src.tools_evaluation.math_reports import markdown_report, publish_report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        required=True,
        type=Path,
        help="Explicit versioned JSON dataset or JSONL case file",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Select exact IDs in source order",
    )
    parser.add_argument(
        "--equivalence",
        choices=("none", "sympy"),
        default="none",
        help="Optional isolated polynomial comparison; never installs a dependency",
    )
    parser.add_argument(
        "--output", type=Path, help="Explicit new report directory; never overwrite"
    )
    parser.add_argument(
        "--fail-on-failures",
        action="store_true",
        help="Exit 1 if any selected case needs review",
    )
    args = parser.parse_args(argv)
    try:
        report = evaluate_dataset(
            args.cases, case_ids=args.case_id, equivalence_backend=args.equivalence
        )
        if args.output:
            publish_report(report, args.output)
        else:
            print(report.model_dump_json(indent=2))
        print(markdown_report(report), file=sys.stderr, end="")
    except (OSError, ValueError, RecursionError) as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 2
    return 1 if args.fail_on_failures and report.failed_case_ids else 0


if __name__ == "__main__":
    raise SystemExit(main())
