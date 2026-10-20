"""One/two checked CS50 chunks. Offline default; explicit LLM opt-in only."""

import argparse
import hashlib
import json
import os
import sys
import time
from contextlib import ExitStack
from pathlib import Path

from scripts.cs50_llm_smoke import supervise

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    from src.tools_knowledge.cs50_checkpoint import atomic_json

    atomic_json(path, value)


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
    checkpoint = None
    current_chunk = None
    resources = ExitStack()
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
            messages_for,
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
        settings = KnowledgeSettings()
        available_chunks = build_cs50_knowledge_chunks(
            plan, input, settings, workspace=config["workspace"]
        )
        start_index = config.get("chunk_index", 0)
        if not isinstance(start_index, int) or start_index < 0:
            raise ValueError("chunk_index must be a non-negative integer")
        chunks = available_chunks[start_index : start_index + config["max_chunks"]]
        report["chunk_index"] = start_index
        report["available_chunks"] = len(available_chunks)
        if len(chunks) != config["max_chunks"]:
            report["selection_error"] = (
                "Requested chunk window exceeds available chunks"
            )
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
        evidence_mode = config.get("evidence_mode", "chunk")
        evidence_audit = []
        segment_map = None
        if evidence_mode == "segment_v1":
            from src.tools_knowledge.bind_cs50_transcript import (
                load_knowledge_transcript,
            )

            transcript = load_knowledge_transcript(
                plan, input, workspace=config["workspace"]
            )
            segment_map = {s.seg_id: s for s in transcript.segments}
        elif evidence_mode != "chunk":
            raise ValueError("Unknown evidence mode")
        if (
            evidence_mode == "segment_v1"
            and config["execute_llm"]
            and config["provider"] != "openai_http"
        ):
            raise ValueError(
                "segment_v1 currently requires explicit openai_http provider"
            )
        report["evidence_mode"] = evidence_mode
        report["evidence_input_version"] = (
            "cs50_segment_evidence_v1" if segment_map is not None else None
        )
        if config.get("checkpoint_dir"):
            from src.tools_knowledge.cs50_checkpoint import (
                CheckpointStore,
                JobIdentity,
                fingerprint,
            )

            checkpoint_path = Path(config["checkpoint_dir"]).absolute()
            course = next(
                c for c in plan.courses if c.lecture_course.course_id == input.course_id
            )
            source_root = course.artifact_root
            if not source_root.is_absolute():
                source_root = Path(config["workspace"]) / source_root
            if (
                checkpoint_path.resolve().is_relative_to(source_root.resolve())
                or checkpoint_path.resolve().is_relative_to((ROOT / "data").resolve())
                or checkpoint_path.resolve().is_relative_to(directory.resolve())
                or directory.resolve().is_relative_to(checkpoint_path.resolve())
            ):
                raise ValueError(
                    "Checkpoint must be separate from source artifacts and run output"
                )
            identity = JobIdentity(
                **{
                    key: getattr(input, key)
                    for key in (
                        "course_id",
                        "section_key",
                        "lecture_id",
                        "resource_id",
                        "source_id",
                        "transcript_sha256",
                    )
                },
                raw_sha256=input.raw_sha256,
                input_binding_sha256=fingerprint(input.model_dump(mode="json")),
                chunking=settings.model_dump(mode="json"),
                chunk_plan_sha256=fingerprint(
                    [c.model_dump(mode="json") for c in available_chunks]
                ),
                selected_chunks=tuple(c.chunk_id for c in chunks),
                prompt_version=report["prompt_version"],
                prompt_sha256=fingerprint(
                    [messages_for(c, segments=segment_map) for c in chunks]
                ),
                result_schema_sha256=fingerprint(
                    ChunkKnowledgeResult.model_json_schema()
                ),
                evidence_mode=evidence_mode,
                evidence_version="cs50_segment_evidence_v1"
                if segment_map is not None
                else "chunk_v1",
                provider=config["provider"],
                model=config["model"],
                execution_mode="llm" if config["execute_llm"] else "offline",
                request_limits={
                    k: config[k]
                    for k in (
                        "token_budget",
                        "input_limit",
                        "output_limit",
                        "max_chunks",
                    )
                },
            )
            checkpoint = resources.enter_context(
                CheckpointStore(config["checkpoint_dir"], identity, chunks).locked()
            )
            report["checkpoint_job_id"] = identity.job_id
        init = time.monotonic()
        report["initialization_seconds"] = time.monotonic() - init
        report["phase"] = "extraction"
        results = []

        def validate_checkpoint(values, chunk):
            result = ChunkKnowledgeResult.model_validate(values["result"])
            fresh_audit = []
            checked = build_cs50_knowledge_document(
                input,
                [chunk],
                [result],
                plan=plan,
                workspace=config["workspace"],
                evidence_mode=evidence_mode,
                evidence_audit=fresh_audit,
            ).chunks[0]
            expected = {
                "schema_version": 1,
                "source_id": input.source_id,
                "chunk_id": chunk.chunk_id,
                "evidence_mode": evidence_mode,
                "items": fresh_audit,
            }
            if (
                checked != result
                or values["evidence"] != expected
                or not isinstance(values["provider"], dict)
            ):
                raise ValueError("Checkpoint result/evidence/source conflict")
            return checked

        # Validate the entire selected window before initializing a provider.
        cached = {}
        if checkpoint:
            for selected in chunks:
                current_chunk = selected.chunk_id
                cached[selected.chunk_id] = checkpoint.reuse(
                    selected.chunk_id,
                    lambda values, selected=selected: validate_checkpoint(
                        values, selected
                    ),
                )
        for chunk in chunks:
            current_chunk = chunk.chunk_id
            chunk_audit = []
            reused = cached.get(chunk.chunk_id)
            if reused is not None:
                result, values, metadata = reused
                results.append(result)
                evidence_audit.extend(values["evidence"]["items"])
                report["results"].append({**metadata, "reused": True})
                save(directory / f"{chunk.chunk_id}.provider.json", values["provider"])
                save(directory / f"{chunk.chunk_id}.json", values["result"])
                continue
            if checkpoint:
                budget.before_dispatch = lambda reservation, cid=chunk.chunk_id: (
                    checkpoint.reserve(cid, reservation)
                )
            if config["execute_llm"] and provider is None:
                init = time.monotonic()
                save(
                    directory / "initialization_started.json",
                    {"phase": config["provider"]},
                )
                factory = (
                    MarvinProvider
                    if config["provider"] == "marvin"
                    else OpenAIHTTPProvider
                )
                extra = {"segments": segment_map} if segment_map is not None else {}
                provider = factory(
                    api_key=os.environ.get("OPENAI_API_KEY"),
                    model=config["model"],
                    budget=budget,
                    **extra,
                )
                report["initialization_seconds"] = time.monotonic() - init
            record = {"chunk_id": chunk.chunk_id, "validated": False, "usage": None}
            report["results"].append(record)
            if provider:
                try:
                    result = provider.extract(chunk, record)
                except Exception as error:
                    if "provider_fields" in record:
                        save(
                            directory / f"{chunk.chunk_id}.provider.json",
                            record.pop("provider_fields"),
                        )
                    from src.tools_knowledge.cs50_precise_evidence import (
                        EvidenceValidationError,
                    )

                    if isinstance(error, EvidenceValidationError):
                        save(
                            directory / "quality_report.json",
                            {
                                "quality_version": "cs50_quality_v2",
                                "evidence_mode": evidence_mode,
                                "evidence_scopes": error.audit,
                                "validation": {"precise_binding": False},
                            },
                        )
                    raise
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
            # Keep explicitly provided model fields before evidence/identity overwrites.
            provider_fields = record.pop("provider_fields", None) or result.model_dump(
                mode="json", exclude_unset=True
            )
            save(directory / f"{chunk.chunk_id}.provider.json", provider_fields)
            # Chunk identity originates in the trusted input, not in the LLM response.
            if evidence_mode == "chunk":
                result.analysis.chunk_id = chunk.chunk_id
                if result.extraction is not None:
                    result.extraction.chunk_id = chunk.chunk_id
            document = build_cs50_knowledge_document(
                input,
                [chunk],
                [result],
                plan=plan,
                workspace=config["workspace"],
                evidence_mode=evidence_mode,
                evidence_audit=chunk_audit,
            )
            evidence_audit.extend(chunk_audit)
            result = document.chunks[0]
            record["validated"] = True
            results.append(result)
            if checkpoint:
                checkpoint.complete(
                    chunk.chunk_id,
                    {
                        "provider": provider_fields,
                        "result": result.model_dump(mode="json"),
                        "evidence": {
                            "schema_version": 1,
                            "source_id": input.source_id,
                            "chunk_id": chunk.chunk_id,
                            "evidence_mode": evidence_mode,
                            "items": chunk_audit,
                        },
                    },
                    record,
                    lambda values, chunk=chunk: validate_checkpoint(values, chunk),
                )
            save(directory / f"{chunk.chunk_id}.json", result.model_dump(mode="json"))
        document = build_cs50_knowledge_document(
            input,
            chunks,
            results,
            plan=plan,
            workspace=config["workspace"],
            evidence_mode=evidence_mode,
        )
        save(
            directory / "evidence_bindings.v1.json",
            {
                "schema_version": 1,
                "evidence_mode": evidence_mode,
                "course_id": input.course_id,
                "lecture_id": input.lecture_id,
                "resource_id": input.resource_id,
                "source_id": input.source_id,
                "transcript_sha256": input.transcript_sha256,
                "items": evidence_audit,
            },
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
        from src.tools_knowledge.cs50_quality import quality_report

        save(
            directory / "quality_report.json",
            quality_report(
                document,
                chunks,
                evidence_audit=evidence_audit,
                worker_report={
                    "validated": True,
                    "result_origin": "LLM" if config["execute_llm"] else "synthetic",
                },
            ),
        )
        report.update(
            validated=True,
            phase="complete",
            requests=budget.requests,
            reserved_tokens=budget.reserved,
            result_origin="LLM" if config["execute_llm"] else "synthetic",
        )
        return 0
    except Exception as error:
        if checkpoint is not None and current_chunk is not None:
            checkpoint.interrupted(current_chunk)
            report["checkpoint_status"] = checkpoint.state.chunks[current_chunk].status
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
        try:
            save(directory / "worker_result.json", report)
        finally:
            resources.close()
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
    parser.add_argument(
        "--chunk-index",
        type=int,
        default=0,
        help="Zero-based starting index; selects max-chunks consecutive chunks",
    )
    parser.add_argument("--timeout", type=float, default=45)
    parser.add_argument("--token-budget", type=int, default=60000)
    parser.add_argument("--input-limit", type=int, default=28000)
    parser.add_argument("--output-limit", type=int, default=1200)
    parser.add_argument(
        "--evidence-mode", choices=["chunk", "segment_v1"], default="chunk"
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        help="Explicit durable job directory; verified done chunks may be reused",
    )
    parser.add_argument("--execute-llm", action="store_true")
    parser.add_argument("--probe-marvin", action="store_true")
    args = parser.parse_args(argv)
    if (
        args.chunk_index < 0
        or not 0 < args.timeout <= 120
        or not 1 <= args.token_budget <= 64000
        or not 1 <= args.input_limit <= 30000
        or not 1 <= args.output_limit <= 2000
    ):
        parser.error("Invalid bounded chunk-index/timeout/token configuration")
    if (
        args.execute_llm
        and args.evidence_mode == "segment_v1"
        and args.provider != "openai_http"
    ):
        parser.error("segment_v1 requires explicit --provider openai_http")
    if args.probe_marvin and args.execute_llm:
        parser.error("Initialization probe cannot execute LLM requests")
    if args.execute_llm and not os.environ.get("OPENAI_API_KEY"):
        parser.error("Explicit OPENAI_API_KEY required for --execute-llm")
    output = args.output.resolve()
    if output.is_relative_to((ROOT / "data").resolve()):
        parser.error("Pilot output must be outside production data")
    if args.checkpoint_dir:
        checkpoint_path = args.checkpoint_dir.absolute()
        if (
            checkpoint_path.resolve().is_relative_to((ROOT / "data").resolve())
            or checkpoint_path == output
            or checkpoint_path.is_relative_to(output)
            or output.is_relative_to(checkpoint_path)
        ):
            parser.error(
                "Checkpoint must be outside production data and separate from output"
            )
    # Exclusive new run directory; never reuse or overwrite results.
    output.mkdir(parents=True, exist_ok=False)
    config = vars(args).copy()
    config.update(
        plan=str(args.plan.absolute()),
        manifest=str(args.manifest.absolute()),
        output=str(output),
        workspace=str(Path.cwd()),
        checkpoint_dir=str(args.checkpoint_dir.absolute())
        if args.checkpoint_dir
        else None,
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
