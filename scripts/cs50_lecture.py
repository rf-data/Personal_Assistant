"""One verified CS50 lecture; offline default, isolated opt-in HTTP execution."""

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

from scripts.cs50_llm_smoke import supervise

ROOT = Path(__file__).resolve().parents[1]


def worker(path):
    from src.tools_knowledge.bind_cs50_transcript import (
        CS50AdapterPlan,
        load_knowledge_manifest,
    )
    from src.tools_knowledge.cs50_checkpoint import atomic_json
    from src.tools_knowledge.run_cs50_lecture import (
        LectureRunConfig,
        lecture_budget,
        prepare_lecture,
        run_lecture,
    )

    value = json.loads(path.read_bytes())
    if not value["config"]["execute_llm"]:
        import socket

        def forbidden(*args, **kwargs):
            raise RuntimeError("Network forbidden in offline lecture worker")

        socket.socket.connect = forbidden
        socket.create_connection = forbidden
        socket.getaddrinfo = forbidden
    report = {
        "validated": False,
        "result_origin": "LLM" if value["config"]["execute_llm"] else "synthetic",
    }
    try:
        plan = CS50AdapterPlan.model_validate_json(Path(value["plan"]).read_bytes())
        manifest = load_knowledge_manifest(value["manifest"])
        matches = [
            i
            for i in manifest.inputs
            if i.course_id == value["course"] and i.section_key == value["section"]
        ]
        if len(matches) != 1:
            raise ValueError("Exactly one explicit verified lecture input required")
        cfg = LectureRunConfig.model_validate(value["config"])
        job = prepare_lecture(
            plan, matches[0], workspace=value["workspace"], config=cfg
        )
        indices = (
            None
            if value["all_chunks"]
            else range(value["start_index"], value["start_index"] + value["max_chunks"])
        )
        budget = lecture_budget([job], Path(value["output"]) / "budget")
        report.update(
            run_lecture(job, Path(value["output"]) / "lecture", budget, indices=indices)
        )
        report["lecture_complete"] = False
        if report["status"] == "done":
            from src.tools_knowledge.complete_cs50_lecture import complete_lecture

            completion, _ = complete_lecture(
                job, Path(value["output"]) / "lecture", budget
            )
            report["lecture_complete"] = completion.phase == "done"
        report["validated"] = True
        report["budget"] = budget.snapshot().model_dump(mode="json")
        return 0
    except Exception as error:
        report["error"] = type(error).__name__
        return 1
    finally:
        atomic_json(path.parent / "worker.json", report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "manifest", "workspace", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--course", required=True)
    parser.add_argument("--section", required=True)
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument(
        "--evidence-mode", choices=["chunk", "segment_v1"], default="segment_v1"
    )
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--max-chunks", type=int, default=1)
    parser.add_argument("--all-chunks", action="store_true")
    parser.add_argument("--max-requests", type=int, default=1)
    parser.add_argument("--token-budget", type=int, default=60000)
    parser.add_argument("--output-limit", type=int, default=1200)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--execute-llm", action="store_true")
    args = parser.parse_args(argv)
    if (
        args.start_index < 0
        or args.max_chunks < 1
        or not 0 < args.max_requests <= 100000
        or not 0 < args.token_budget <= 100000000
        or not 0 < args.output_limit <= 2000
        or not 0 < args.timeout <= 3600
    ):
        parser.error("Invalid explicit window/request/token/time limits")
    if args.all_chunks and (args.start_index != 0 or args.max_chunks != 1):
        parser.error("--all-chunks cannot be combined with a custom window")
    if args.execute_llm and not os.environ.get("OPENAI_API_KEY"):
        parser.error("Explicit API key required for --execute-llm")
    output = args.output.absolute()
    if (
        any(p.is_symlink() for p in (output, *output.parents))
        or output.resolve().is_relative_to((ROOT / "data").resolve())
        or output.resolve().is_relative_to(args.workspace.resolve())
        or args.workspace.resolve().is_relative_to(output.resolve())
    ):
        parser.error(
            "Output must be separate from source workspace and production data"
        )
    run = output / "runs" / uuid.uuid4().hex
    run.mkdir(parents=True)
    from src.tools_knowledge.cs50_checkpoint import atomic_json

    value = {
        key: str(getattr(args, key).absolute())
        for key in ("plan", "manifest", "workspace", "output")
    }
    value.update(
        course=args.course,
        section=args.section,
        all_chunks=args.all_chunks,
        start_index=args.start_index,
        max_chunks=args.max_chunks,
        config={
            "model": args.model,
            "evidence_mode": args.evidence_mode,
            "execute_llm": args.execute_llm,
            "max_requests": args.max_requests,
            "token_budget": args.token_budget,
            "output_limit": args.output_limit,
            "max_seconds": args.timeout,
        },
    )
    configuration = run / "configuration.json"
    atomic_json(configuration, value)
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("MARVIN_", "CS50_LECTURE_"))
    }
    env.update(
        ROOT=str(run),
        DATA_DIR=str(run / "data"),
        CHROMA_DIR=str(run / "chroma"),
        WIKI_EN_API="https://example.invalid",
        HEADER_AGENT="cs50-lecture",
        HF_API_KEY="unused",
        OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY", "")
        if args.execute_llm
        else "offline-unused",
    )
    if args.execute_llm:
        env["CS50_LECTURE_EXECUTE_LLM"] = "1"
    bootstrap = "import sys; sys.path.insert(0,sys.argv[1]); from scripts.cs50_lecture import worker; from pathlib import Path; raise SystemExit(worker(Path(sys.argv[2])))"
    report = supervise(
        [sys.executable, "-I", "-c", bootstrap, str(ROOT), str(configuration)],
        run,
        env,
        args.timeout,
    )
    atomic_json(run / "supervision.json", report)
    print(run / "supervision.json")
    return 1 if report["timed_out"] or report["returncode"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
