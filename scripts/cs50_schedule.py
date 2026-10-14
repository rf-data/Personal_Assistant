"""Explicit one-course or six-course scope; isolated offline by default."""

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

from scripts.cs50_llm_smoke import supervise

ROOT = Path(__file__).resolve().parents[1]


def worker(path):
    from src.tools_knowledge.batch_cs50 import prepare_batch, run_batch
    from src.tools_knowledge.bind_cs50_transcript import (
        CS50AdapterPlan,
        load_knowledge_manifest,
    )
    from src.tools_knowledge.cs50_checkpoint import atomic_json
    from src.tools_knowledge.run_cs50_lecture import LectureRunConfig
    from src.tools_knowledge.schedule_cs50 import PreflightFailure, prepare_schedule

    data = json.loads(path.read_bytes())
    report = {"validated": False}
    if not data["config"]["execute_llm"]:
        import socket

        def forbidden(*args, **kwargs):
            raise RuntimeError("Offline schedule network forbidden")

        socket.socket.connect = forbidden
        socket.create_connection = forbidden
        socket.getaddrinfo = forbidden
    try:
        plan = CS50AdapterPlan.model_validate_json(Path(data["plan"]).read_bytes())
        inputs = load_knowledge_manifest(data["manifest"]).inputs
        cfg = LectureRunConfig.model_validate(data["config"])
        factory = prepare_batch if data["six_course_batch"] else prepare_schedule
        scope = factory(
            plan,
            inputs,
            course_ids=data["course"],
            workspace=data["workspace"],
            config=cfg,
        )
        report = run_batch(
            scope,
            Path(data["output"]) / "scope",
            max_lectures=data["max_lectures"],
            audit_only=data["audit_only"],
        )
        report["validated"] = True
        atomic_json(path.parent / "report.json", report)
        return (
            1
            if any(row["status"] in ("failed", "unknown") for row in report["sources"])
            else 0
        )
    except Exception as error:
        report["error"] = type(error).__name__
        if isinstance(error, PreflightFailure):
            report["source_failures"] = error.failures
        atomic_json(path.parent / "report.json", report)
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "manifest", "workspace", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--course", action="append", required=True)
    parser.add_argument("--six-course-batch", action="store_true")
    parser.add_argument("--max-lectures", type=int)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument(
        "--evidence-mode", choices=["chunk", "segment_v1"], default="segment_v1"
    )
    parser.add_argument("--max-requests", type=int, default=1)
    parser.add_argument("--token-budget", type=int, default=60000)
    parser.add_argument("--output-limit", type=int, default=1200)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--execute-llm", action="store_true")
    args = parser.parse_args(argv)
    if not args.six_course_batch and len(args.course) != 1:
        parser.error(
            "One explicit course or --six-course-batch with all six IDs required"
        )
    if args.execute_llm and (args.audit_only or not os.environ.get("OPENAI_API_KEY")):
        parser.error("Explicit key and non-audit mode required for --execute-llm")
    if (
        not 1 <= args.timeout <= 3600
        or not 1 <= args.max_requests <= 100000
        or not 1 <= args.token_budget <= 100000000
        or not 1 <= args.output_limit <= 2000
        or args.max_lectures is not None
        and args.max_lectures < 1
    ):
        parser.error("Invalid bounded scope limits")
    output = args.output.absolute()
    if (
        any(p.is_symlink() for p in (output, *output.parents))
        or output.resolve().is_relative_to((ROOT / "data").resolve())
        or output.resolve().is_relative_to(args.workspace.resolve())
        or args.workspace.resolve().is_relative_to(output.resolve())
    ):
        parser.error("Output must be outside source workspace and production data")
    run = output / "runs" / uuid.uuid4().hex
    run.mkdir(parents=True)
    from src.tools_knowledge.cs50_checkpoint import atomic_json

    configuration = {
        k: str(getattr(args, k).absolute())
        for k in ("plan", "manifest", "workspace", "output")
    }
    configuration.update(
        course=args.course,
        six_course_batch=args.six_course_batch,
        max_lectures=args.max_lectures,
        audit_only=args.audit_only,
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
    path = run / "configuration.json"
    atomic_json(path, configuration)
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
        HEADER_AGENT="cs50-schedule",
        HF_API_KEY="unused",
        OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY", "")
        if args.execute_llm
        else "offline-unused",
    )
    if args.execute_llm:
        env["CS50_LECTURE_EXECUTE_LLM"] = "1"
    bootstrap = "import sys;sys.path.insert(0,sys.argv[1]);from scripts.cs50_schedule import worker;from pathlib import Path;raise SystemExit(worker(Path(sys.argv[2])))"
    supervision = supervise(
        [sys.executable, "-I", "-c", bootstrap, str(ROOT), str(path)],
        run,
        env,
        args.timeout,
    )
    atomic_json(run / "supervision.json", supervision)
    print(run / "report.json")
    return 1 if supervision["timed_out"] or supervision["returncode"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
