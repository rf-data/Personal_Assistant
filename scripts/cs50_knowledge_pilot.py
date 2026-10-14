"""One/two checked CS50 chunks. Offline default; explicit LLM opt-in only."""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from scripts.cs50_llm_smoke import supervise

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def worker(configuration):
    config = json.loads(configuration.read_text())
    if config["execute_llm"] and os.environ.get("CS50_KNOWLEDGE_EXECUTE_LLM") != "1":
        raise ValueError("API worker needs parent --execute-llm authorization")
    directory = configuration.parent
    started = time.monotonic()
    report = {
        "validated": False,
        "provider": config["provider"],
        "model": config["model"],
        "mode": "llm" if config["execute_llm"] else "offline",
        "requests": 0,
        "retries": 0,
        "results": [],
        "phase": "initialization",
    }
    provider = None
    try:
        if not config["execute_llm"]:
            import socket

            def forbidden(*args, **kwargs):
                raise RuntimeError("Network forbidden in offline mode")

            socket.socket.connect = forbidden
            socket.socket.connect_ex = forbidden
            socket.create_connection = forbidden
            socket.getaddrinfo = forbidden
        if config["probe_marvin"]:
            init = time.monotonic()
            save(directory / "initialization_started.json", {"phase": "marvin_import"})
            import marvin

            report.update(
                marvin_version=getattr(marvin, "__version__", "unknown"), validated=True
            )
            return 0
        from src.core.config_knowledge import KnowledgeSettings
        from src.tools_knowledge.bind_cs50_transcript import (
            CS50AdapterPlan,
            CS50KnowledgeInputManifest,
            build_cs50_knowledge_chunks,
            build_cs50_knowledge_document,
        )
        from src.tools_knowledge.consolidate_knowledge import consolidate_knowledge
        from src.tools_knowledge.cs50_extraction_provider import (
            ChunkKnowledgeResult,
            MarvinProvider,
            OpenAIHTTPProvider,
            RequestBudget,
            build_knowledge_extraction_prompt,
        )

        plan = CS50AdapterPlan.model_validate_json(Path(config["plan"]).read_bytes())
        manifest = CS50KnowledgeInputManifest.model_validate_json(
            Path(config["manifest"]).read_bytes()
        )
        if len(manifest.inputs) != 1:
            raise ValueError("Exactly one verified pilot input is required")
        input = manifest.inputs[0]
        if input.course_id != "cs50_python" or input.section_key != "0":
            raise ValueError("Only CS50 Python week 0 pilot is authorized")
        chunks = build_cs50_knowledge_chunks(
            plan, input, KnowledgeSettings(), workspace=config["workspace"]
        )[: config["max_chunks"]]
        if len(chunks) != config["max_chunks"] or any(
            len(c.text) > 6000 for c in chunks
        ):
            raise ValueError("No suitable bounded chunks (maximum 6000 characters)")
        report["prompt_version"] = "knowledge_extraction_v1"
        report["prompt_sha256"] = hashlib.sha256(
            build_knowledge_extraction_prompt().encode()
        ).hexdigest()
        save(directory / "input_manifest.json", manifest.model_dump(mode="json"))
        save(directory / "chunks.json", [c.model_dump(mode="json") for c in chunks])
        budget = RequestBudget(
            config["max_chunks"],
            config["token_budget"],
            config["input_limit"],
            config["output_limit"],
        )
        init = time.monotonic()
        if config["execute_llm"]:
            save(
                directory / "initialization_started.json", {"phase": config["provider"]}
            )
            factory = (
                MarvinProvider if config["provider"] == "marvin" else OpenAIHTTPProvider
            )
            provider = factory(
                api_key=os.environ.get("OPENAI_API_KEY"),
                model=config["model"],
                budget=budget,
            )
        report["initialization_seconds"] = time.monotonic() - init
        report["phase"] = "extraction"
        results = []
        for chunk in chunks:
            record = {"chunk_id": chunk.chunk_id, "validated": False, "usage": None}
            report["results"].append(record)
            if provider:
                result = provider.extract(chunk, record)
            else:
                result = ChunkKnowledgeResult.model_validate(
                    {
                        "analysis": {
                            "chunk_id": chunk.chunk_id,
                            "relevant": False,
                            "needs_visual_context": False,
                        },
                        "extraction": None,
                    }
                )
            # Chunk identity originates in the trusted input, not in the LLM response.
            result.analysis.chunk_id = chunk.chunk_id
            if result.extraction is not None:
                result.extraction.chunk_id = chunk.chunk_id
            document = build_cs50_knowledge_document(
                input, [chunk], [result], plan=plan, workspace=config["workspace"]
            )
            result = document.chunks[0]
            record["validated"] = True
            results.append(result)
            save(directory / f"{chunk.chunk_id}.json", result.model_dump(mode="json"))
        document = build_cs50_knowledge_document(
            input, chunks, results, plan=plan, workspace=config["workspace"]
        )
        save(directory / "extraction.json", document.model_dump(mode="json"))
        document = type(document).model_validate_json(
            (directory / "extraction.json").read_bytes()
        )
        consolidated = consolidate_knowledge(document)
        save(directory / "consolidated.json", consolidated.model_dump(mode="json"))
        assert (
            type(consolidated).model_validate_json(
                (directory / "consolidated.json").read_bytes()
            )
            == consolidated
        )
        report.update(
            validated=True,
            phase="complete",
            requests=budget.requests,
            reserved_tokens=budget.reserved,
            result_origin="LLM" if provider else "synthetic",
        )
        return 0
    except Exception as error:
        report["error"] = type(
            error
        ).__name__  # No credentials or provider response bodies.
        if "budget" in locals():
            report["requests"] = budget.requests
        return 1
    finally:
        report["runtime_seconds"] = time.monotonic() - started
        if "init" in locals() and "initialization_seconds" not in report:
            report["initialization_seconds"] = time.monotonic() - init
        save(directory / "worker_result.json", report)
        if provider:
            provider.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--provider", choices=["marvin", "openai_http"], default="marvin"
    )
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--max-chunks", type=int, choices=[1, 2], default=1)
    parser.add_argument("--timeout", type=float, default=45)
    parser.add_argument("--token-budget", type=int, default=60000)
    parser.add_argument("--input-limit", type=int, default=28000)
    parser.add_argument("--output-limit", type=int, default=1200)
    parser.add_argument("--execute-llm", action="store_true")
    parser.add_argument("--probe-marvin", action="store_true")
    args = parser.parse_args(argv)
    if (
        not 0 < args.timeout <= 120
        or not 1 <= args.token_budget <= 64000
        or not 1 <= args.input_limit <= 30000
        or not 1 <= args.output_limit <= 2000
    ):
        parser.error("Invalid bounded timeout/token configuration")
    if args.probe_marvin and args.execute_llm:
        parser.error("Initialization probe cannot execute LLM requests")
    if args.execute_llm and not os.environ.get("OPENAI_API_KEY"):
        parser.error("Explicit OPENAI_API_KEY required for --execute-llm")
    output = args.output.resolve()
    if output.is_relative_to((ROOT / "data").resolve()):
        parser.error("Pilot output must be outside production data")
    # Exclusive new run directory; never reuse or overwrite results.
    output.mkdir(parents=True, exist_ok=False)
    config = vars(args).copy()
    config.update(
        plan=str(args.plan.absolute()),
        manifest=str(args.manifest.absolute()),
        output=str(output),
        workspace=str(Path.cwd()),
    )
    save(output / "configuration.json", config)
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("MARVIN_", "CS50_KNOWLEDGE_"))
    }
    env.update(
        ROOT=str(output),
        DATA_DIR=str(output / "data"),
        CHROMA_DIR=str(output / "chroma"),
        WIKI_EN_API="https://example.invalid",
        HEADER_AGENT="cs50-pilot",
        HF_API_KEY="unused",
        OPENAI_API_KEY=os.environ["OPENAI_API_KEY"]
        if args.execute_llm
        else "offline-unused",
        MARVIN_HOME_PATH=str(output / "marvin"),
        MARVIN_DATABASE_URL=f"sqlite+aiosqlite:///{output / 'marvin.db'}",
    )
    if args.execute_llm:
        env["CS50_KNOWLEDGE_EXECUTE_LLM"] = "1"
    bootstrap = "import sys; sys.path.insert(0, sys.argv[1]); from scripts.cs50_knowledge_pilot import worker; from pathlib import Path; raise SystemExit(worker(Path(sys.argv[2])))"
    summary = supervise(
        [
            sys.executable,
            "-I",
            "-c",
            bootstrap,
            str(ROOT),
            str(output / "configuration.json"),
        ],
        output,
        env,
        args.timeout,
    )
    summary.update(
        provider=args.provider, model=args.model, execute_llm=args.execute_llm
    )
    if (output / "worker_result.json").exists():
        summary["worker"] = json.loads((output / "worker_result.json").read_text())
    save(output / "supervision.json", summary)
    print(output / "supervision.json")
    return 1 if summary["timed_out"] or summary["returncode"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
