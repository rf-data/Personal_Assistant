"""Existing consolidation entry points with explicit offline, read-only defaults."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.tools_knowledge.consolidation_run import (
    RunConfig,
    hash_bytes,
    inspect_input,
    make_result,
    publication_lock,
    run_course,
)
from src.tools_knowledge.consolidation_validation import require_valid
from src.tools_knowledge.cs50_checkpoint import atomic_json
from src.tools_lecture.execute_cs50 import safe_path


def run_knowledge_consolidation():
    """Compatibility entry for a configured course; now a read-only audit."""
    from src.core.config import folder_env_vars
    from src.core.memory_lecture import LectureContext
    from src.utils.dict_helper import load_dict

    context = load_dict(
        path=folder_env_vars.config_dir / "context_lecture_compile.json",
        cls=LectureContext,
    )
    folder = (
        folder_env_vars.data_lectures
        / context.provider
        / context.course_id
        / "knowledge"
    )
    return process_course_knowledge(
        list(folder.rglob("*_know_extract.json")),
        folder,
        context.cfg_knowledge.llm_model,
        input_root=folder,
        course_id=context.course_id,
    )


def process_course_knowledge(
    input_paths: list[Path],
    output_folder: Path,
    model_name: str,
    *,
    input_root=None,
    write=False,
    course_id=None,
    lecture_ids=(),
    semantic_stage=None,
    semantic_contract=None,
):
    """Preserve the runner boundary; return a versioned audit instead of None.

    semantic_stage is an explicit existing-stage adapter or offline test double.
    This runner never imports/configures an SDK or chooses a live provider.
    """
    if input_root is None:
        input_root = (
            Path(
                os.path.commonpath(
                    [str(Path(p).absolute().parent) for p in input_paths]
                )
            )
            if input_paths
            else Path.cwd()
        )
    config = RunConfig(
        model_name=model_name,
        stage="semantic" if semantic_stage else "deterministic",
        semantic_contract=semantic_contract,
    )
    return run_course(
        input_paths,
        output_folder,
        input_root=input_root,
        config=config,
        write=write,
        course_id=course_id,
        lecture_ids=lecture_ids,
        semantic_stage=semantic_stage,
    )


def process_knowledge_file(
    input_path: Path,
    output_path: Path,
    model_name: str,
    *,
    write=False,
    semantic_stage=None,
):
    """Single-file compatibility boundary, validated and exclusive on publication.

    For receipt-backed resume use process_course_knowledge. This helper never skips
    or adopts an output and does not call the semantic stage unless supplied.
    """
    document, digest = inspect_input(
        input_path, Path(input_path).absolute().parent, RunConfig()
    )
    require_valid(document, strict=True)
    _, result = make_result(
        document, model_name=model_name, semantic_stage=semantic_stage
    )
    if write:
        output_path = Path(output_path).absolute()
        safe_path(output_path.parent, output_path)
        with publication_lock(output_path.parent):
            if hash_bytes(Path(input_path).read_bytes()) != digest:
                raise ValueError("Input changed during consolidation")
            atomic_json(output_path, result.model_dump(mode="json"))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", action="append", type=Path, required=True, dest="inputs"
    )
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--course")
    parser.add_argument("--lecture", action="append", default=[])
    parser.add_argument(
        "--write",
        action="store_true",
        help="Publish NEW deterministic outputs and immutable receipts",
    )
    parser.add_argument(
        "--report", type=Path, help="Explicit new JSON report path (never overwrite)"
    )
    args = parser.parse_args(argv)
    try:
        # Refuse report conflicts before processing/publishing anything.
        if args.report:
            report_path = Path(args.report).absolute()
            safe_path(report_path.parent, report_path)
            if report_path.exists() or not report_path.parent.is_dir():
                raise ValueError(
                    "Report already exists or its parent directory is missing"
                )
            for root in (args.input_root.absolute(), args.output_root.absolute()):
                if report_path.is_relative_to(root):
                    raise ValueError("Report must be outside input/output roots")
        report = process_course_knowledge(
            args.inputs,
            args.output_root,
            "offline",
            input_root=args.input_root,
            write=args.write,
            course_id=args.course,
            lecture_ids=tuple(args.lecture),
        )
        if args.report:
            atomic_json(report_path, report.model_dump(mode="json"))
    except (OSError, ValueError) as error:
        parser.exit(2, f"consolidation: {error}\n")
    print(
        f"Lectures={report.counts['lectures_examined']} inputs={report.counts['inputs_selected']} "
        f"objects={report.counts['objects_processed']} merged={report.counts['objects_merged']} "
        f"errors={report.counts['errors']} warnings={report.counts['warnings']}"
    )
    for item in report.inputs:
        print(
            f"{item.status}: {item.input_path} -> {item.course_id}/{item.lecture_id}/{item.source_id} ({item.decision})"
        )
        for finding in item.findings:
            print(
                f"  {finding.severity} {finding.code} chunk={finding.chunk_id} item={finding.item_id}: {finding.message}"
            )
    return (
        1
        if any(report.counts[status] for status in ("failed", "invalid", "stale"))
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
