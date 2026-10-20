"""Write a separate versioned CS50 metadata plan; never execute ResourceTasks."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, default=ROOT / "docs/course_sources/cs50/manifest.json"
    )
    parser.add_argument("--artifact-root", type=Path, default=Path("data/lectures"))
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/course_sources/cs50/cs50_lecture_plan.v1.json",
    )
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from src.model_discovery.cs50_selection import SelectionPolicy
    from src.tools_lecture.adapt_cs50 import CS50AdapterPlan, build_cs50_course_plan
    from src.tools_lecture.prepare_cs50 import discover_fixture_courses
    from src.tools_lecture.select_cs50 import preview_course

    if args.output.absolute().is_relative_to(args.artifact_root.absolute()):
        parser.error("Keep the report separate from the transcript artifact directory")
    policy = SelectionPolicy(text_strategy="timed_knowledge")
    plan = CS50AdapterPlan(
        courses=tuple(
            build_cs50_course_plan(
                preview_course(course, policy), artifact_root=args.artifact_root
            )
            for course in discover_fixture_courses(args.manifest)
        )
    )
    text = plan.model_dump_json(indent=2) + "\n"
    if CS50AdapterPlan.model_validate_json(text) != plan:
        raise ValueError("Generated plan failed its complete JSON roundtrip")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(text)
    print(
        json.dumps(
            {
                "courses": len(plan.courses),
                "bindings": sum(len(c.bindings) for c in plan.courses),
                "tasks": sum(len(c.tasks) for c in plan.courses),
                "planned_only": plan.planned_only,
                "execution_supported": plan.execution_supported,
            }
        )
    )


if __name__ == "__main__":
    main()
