"""Explicit offline-first material catalog/plan/import/download/parse/status CLI."""

import argparse
import json
from pathlib import Path

from src.tools_materials.download import MaterialDownloader
from src.tools_materials.inventory import catalog
from src.tools_materials.processing import (
    MaterialPlan,
    MaterialProcessor,
    make_plan,
    plan_steps,
)
from src.tools_materials.storage import publish_bytes, save_model


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command",
        choices=[
            "inventory",
            "plan",
            "download",
            "import-local",
            "parse",
            "resume",
            "status",
            "demo",
        ],
    )
    p.add_argument(
        "--manifest", type=Path, default=Path("docs/course_sources/cs50/manifest.json")
    )
    p.add_argument("--plan", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--workspace", type=Path)
    p.add_argument("--course")
    p.add_argument("--section")
    p.add_argument("--lecture")
    p.add_argument("--resource")
    p.add_argument("--all-courses", action="store_true")
    p.add_argument("--max-resources", type=int, default=1)
    p.add_argument("--local-file", type=Path)
    p.add_argument("--license-reviewed", action="store_true")
    p.add_argument("--execute-download", action="store_true")
    p.add_argument("--execute-import", action="store_true")
    p.add_argument("--execute-parse", action="store_true")
    return p


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    for flag, command in [
        (args.execute_download, "download"),
        (args.execute_import, "import-local"),
        (args.execute_parse, "parse"),
    ]:
        if flag and args.command not in (
            {"parse", "resume"} if command == "parse" else {command}
        ):
            p.error("Execution approval belongs to a separate command")
    if args.all_courses and any(
        (args.course, args.section, args.lecture, args.resource)
    ):
        p.error("--all-courses cannot be combined with a narrower scope")
    if args.section and not args.course:
        p.error("--section requires --course")
    if not 1 <= args.max_resources <= 2000:
        p.error("--max-resources must be 1..2000")
    if args.command == "inventory":
        result = catalog(args.manifest)
    elif args.command == "demo":
        if not args.output:
            p.error("demo requires a new external --output directory")
        from scripts.cs50_materials_demo import demo

        result = demo(
            args.manifest, args.output, course=args.course, all_courses=args.all_courses
        )
    elif args.command == "plan":
        plan = make_plan(args.manifest)
        if not any(
            (args.course, args.section, args.lecture, args.resource, args.all_courses)
        ):
            p.error(
                "Choose explicit --course/--section/--lecture/--resource/--all-courses scope"
            )
        selected = plan.select(
            course=args.course,
            section=args.section,
            lecture=args.lecture,
            resource=args.resource,
        )
        if args.license_reviewed:
            selected = tuple(
                b.model_copy(update={"license_status": "reviewed"}) for b in selected
            )
        plan = MaterialPlan(courses=plan.courses, materials=selected)
        if args.output:
            save_model(args.output, plan)
        result = {
            "schema_version": 1,
            "coverage": "local_snapshot_only",
            "materials": len(selected),
            "states": [plan_steps(b) for b in selected],
            "output": str(args.output) if args.output else None,
        }
    else:
        if not args.plan or not args.workspace:
            p.error("--plan and external --workspace required")
        if not any(
            (args.course, args.section, args.lecture, args.resource, args.all_courses)
        ):
            p.error("Explicit scope required")
        if args.section and not args.course:
            p.error("--section requires --course")
        plan = MaterialPlan.model_validate_json(args.plan.read_bytes())
        rows = plan.select(
            course=args.course,
            section=args.section,
            lecture=args.lecture,
            resource=args.resource,
        )
        if args.command == "import-local" and (not args.local_file or len(rows) != 1):
            p.error(
                "Local import requires --local-file and exactly one selected resource"
            )
        rows = rows[: args.max_resources]
        worker = MaterialDownloader(args.workspace)
        processor = MaterialProcessor(args.workspace)
        results = []
        for b in rows:
            if not plan_steps(b)["tasks"]:
                result = plan_steps(b)
            elif args.command in {"parse", "resume"}:
                result = processor.parse(b, execute=args.execute_parse)
            elif args.command == "status":
                try:
                    result = processor.inspect(b)
                except (ValueError, OSError) as exc:
                    result = {
                        "status": "blocked",
                        "material_id": b.material_id,
                        "reason": str(exc),
                    }
            else:
                result = worker.obtain(
                    b,
                    execute=args.execute_download or args.execute_import,
                    license_reviewed=args.license_reviewed,
                    local_file=args.local_file
                    if args.command == "import-local"
                    else None,
                )
            results.append(
                result.model_dump(mode="json")
                if hasattr(result, "model_dump")
                else result
            )
        result = {
            "schema_version": 1,
            "results": results,
            "remaining_unattempted": len(
                plan.select(
                    course=args.course,
                    section=args.section,
                    lecture=args.lecture,
                    resource=args.resource,
                )
            )
            - len(rows),
        }
    if args.command == "inventory" and args.output:
        publish_bytes(
            args.output,
            (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode(),
        )
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "reference_occurrences": len(result["references"]),
                }
            )
        )
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
