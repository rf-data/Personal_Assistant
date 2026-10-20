"""Explicit offline material audit. JSON on stdout, summary on stderr by default."""

import argparse
import json
import sys
from pathlib import Path

from src.tools_lecture.execute_cs50 import safe_path
from src.tools_lecture.material_handoff import prepare_material_handoff
from src.tools_materials.storage import publish_bytes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    for name in ("normalized", "receipt", "raw"):
        parser.add_argument(
            f"--{name}",
            required=True,
            type=Path,
            action="append",
            help="Repeat in matching order for multiple materials",
        )
    parser.add_argument(
        "--output", type=Path, help="Explicit new JSON report path; never overwrite"
    )
    args = parser.parse_args(argv)
    if not len(args.normalized) == len(args.receipt) == len(args.raw):
        parser.error("--normalized, --receipt and --raw must occur equally often")
    reviews = [
        prepare_material_handoff(
            normalized_path=normalized,
            receipt_path=receipt,
            raw_path=raw,
            plan_path=args.plan,
            workspace=args.workspace,
        )
        for normalized, receipt, raw in zip(
            args.normalized, args.receipt, args.raw, strict=True
        )
    ]
    # Repeating a material is an input error, never permission to double its text.
    identities = [r.report.material_id for r in reviews if r.report.material_id]
    if len(identities) != len(set(identities)):
        parser.error("Duplicate material inputs; supply each material once")
    payload = {
        "schema_version": 1,
        "reviews": [r.model_dump(mode="json") for r in reviews],
    }
    contents = (
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode()
    if args.output:
        try:
            output = args.output.absolute()
            safe_path(output.parent, output)
            workspace = args.workspace.absolute()
            sources = [*args.normalized, *args.receipt, *args.raw, args.plan]
            if output.is_relative_to(workspace) or any(
                output == p.absolute() for p in sources
            ):
                raise ValueError(
                    "Report output must be outside the input artifact workspace and input paths"
                )
            # Shared exclusive atomic publisher refuses existing files, including symlinks.
            publish_bytes(output, contents)
        except (OSError, ValueError) as exc:
            print(f"Report publication failed: {exc}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(contents.decode())
    for review in reviews:
        report = review.report
        errors = sum(f.severity == "error" for f in report.findings)
        warnings = sum(f.severity == "warning" for f in report.findings)
        print(
            f"{report.status}: {report.material_id or report.inputs['normalized']} -> course={report.course_id} sections={','.join(report.section_keys)} lectures={','.join(report.lecture_ids)} errors={errors} warnings={warnings}",
            file=sys.stderr,
        )
        for finding in report.findings:
            if finding.severity == "info":
                continue
            where = report.inputs.get(finding.input, report.inputs["normalized"])
            location = (
                finding.location.model_dump(exclude_none=True)
                if finding.location
                else {}
            )
            print(
                f"  {finding.severity} [{finding.category}/{finding.code}] {where} block={finding.block_id or '-'} image={finding.image_id or '-'} location={location} field={finding.field or '-'}: {finding.message}",
                file=sys.stderr,
            )
    return 1 if any(not r.report.passed for r in reviews) else 0


if __name__ == "__main__":
    raise SystemExit(main())
