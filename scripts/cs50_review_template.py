"""Generate unannotated windows from one verified input; no invented gold claims."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "manifest", "workspace", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--course", default="cs50_python")
    parser.add_argument("--section", default="0")
    parser.add_argument(
        "--origin", choices=["operator_declared_original", "synthetic"], required=True
    )
    parser.add_argument("--windows", type=int, default=8)
    args = parser.parse_args()
    from src.tools_knowledge.bind_cs50_transcript import (
        CS50AdapterPlan,
        load_knowledge_manifest,
    )
    from src.tools_knowledge.cs50_checkpoint import atomic_json
    from src.tools_knowledge.cs50_evaluation import review_template, validate_review_set
    from src.tools_knowledge.run_cs50_lecture import (
        LectureRunConfig,
        checked_output,
        prepare_lecture,
    )

    plan = CS50AdapterPlan.model_validate_json(args.plan.read_bytes())
    inputs = [
        i
        for i in load_knowledge_manifest(args.manifest).inputs
        if i.course_id == args.course and i.section_key == args.section
    ]
    if len(inputs) != 1:
        parser.error("Exactly one explicit review source required")
    job = prepare_lecture(
        plan, inputs[0], workspace=args.workspace, config=LectureRunConfig()
    )
    template = validate_review_set(
        review_template(job, origin=args.origin, count=args.windows), job
    )
    path = checked_output(job, args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(path, template.model_dump(mode="json"))
    print(path)


if __name__ == "__main__":
    main()
