"""Create one checked CS50 Knowledge input manifest; read-only artifact access."""

import argparse
from pathlib import Path

from src.tools_knowledge.bind_cs50_transcript import (
    CS50AdapterPlan,
    CS50KnowledgeInputManifest,
    bind_cs50_knowledge_input,
    save_knowledge_manifest,
    save_portable_manifest,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--course", required=True)
    parser.add_argument("--section", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--legacy-v1", action="store_true")
    args = parser.parse_args()
    plan = CS50AdapterPlan.model_validate_json(args.plan.read_bytes())
    matches = [
        binding
        for course in plan.courses
        for binding in course.bindings
        if binding.course_id == args.course and binding.section_key == args.section
    ]
    if len(matches) != 1:
        parser.error("Exactly one planned lecture must match course and section")
    input = bind_cs50_knowledge_input(plan, matches[0], workspace=args.workspace)
    # Keep manifest output separate from the validated source artifacts and receipts.
    output = args.output.absolute()
    for course in plan.courses:
        root = course.artifact_root
        root = root if root.is_absolute() else args.workspace.absolute() / root
        if output.is_relative_to(root):
            parser.error("Manifest output must be outside all source artifact roots")
    if args.legacy_v1:
        save_knowledge_manifest(CS50KnowledgeInputManifest(inputs=(input,)), output)
    else:
        save_portable_manifest((input,), output, workspace=args.workspace)
    print(f"Validated input manifest: {args.output}")


if __name__ == "__main__":
    main()
