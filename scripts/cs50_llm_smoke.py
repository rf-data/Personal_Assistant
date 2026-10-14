"""Bounded, opt-in smoke test. No production runner, cache or retry wrapper."""

import argparse
import faulthandler
import hashlib
import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def supervise(command, directory, env, timeout):
    """POSIX process group includes grandchildren; kill it even if leader exits."""
    started = time.monotonic()
    with (
        (directory / "stdout.log").open("w") as stdout,
        (directory / "stderr.log").open("w") as stderr,
    ):
        child = subprocess.Popen(
            command,
            cwd=directory,
            env=env,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        timed_out = False
        try:
            child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                child.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
            finally:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait(timeout=3)
    return dict(
        timed_out=timed_out,
        returncode=child.returncode,
        runtime_seconds=time.monotonic() - started,
    )


class RequestBudget:
    """One attempt per chunk, including failed requests; never reset global count."""

    def __init__(self, maximum):
        self.maximum = maximum
        self.requests = 0
        self.chunk_requests = 0
        self.failed = False

    def begin_chunk(self):
        self.chunk_requests = 0

    def claim(self):
        if self.failed or self.requests >= self.maximum or self.chunk_requests:
            raise RuntimeError("API attempt budget exhausted; retries are disabled")
        self.requests += 1
        self.chunk_requests += 1


def worker(plan_path):
    plan = json.loads(plan_path.read_text())
    if plan["enable_api"] and os.environ.get("CS50_SMOKE_ENABLE_API") != "1":
        raise ValueError("API worker requires explicit --enable-api authorization")
    directory = plan_path.parent
    report = dict(
        mode="api" if plan["enable_api"] else "offline",
        model=plan["model"],
        api_requests=0,
        token_usage=[],
        results=[],
        phase="preparing",
        validated=False,
    )
    started = time.monotonic()

    def checkpoint():
        report["worker_seconds"] = time.monotonic() - started
        write_json(directory / "worker.json", report)

    checkpoint()
    if not plan["enable_api"]:
        import socket

        def forbidden(*args, **kwargs):
            raise RuntimeError("Network forbidden in offline smoke test")

        socket.socket.connect = forbidden
        socket.socket.connect_ex = forbidden
        socket.create_connection = forbidden
        socket.getaddrinfo = forbidden
    sys.path.insert(0, str(ROOT))
    budget = RequestBudget(plan["max_chunks"])
    try:
        from src.core.config_knowledge import KnowledgeSettings
        from src.core.memory import app_session
        from src.model_knowledge.data_knowledge import ChunkKnowledgeResult
        from src.model_transcribe.data_transcribe import TranscriptDocument
        from src.tools_knowledge.find_knowledge import (
            _get_knowledge_extractor as _get_extract_knowledge,
        )
        from src.tools_knowledge.find_knowledge import (
            attach_chunk_provenance,
            build_transcript_chunks,
            extract_knowledge,
            validate_extraction,
        )

        app_session.logger = logging.getLogger("cs50-smoke")
        source = Path(plan["transcript"])
        raw = source.read_bytes()
        transcript = TranscriptDocument.model_validate_json(raw)
        report["transcript_sha256"] = hashlib.sha256(raw).hexdigest()
        report["language"] = transcript.language
        report["transcript_provenance"] = (
            transcript.provenance.model_dump(mode="json")
            if transcript.provenance
            else None
        )
        # Bound the input window before invoking the unchanged chunking function.
        # Stop at the first cue crossing 45/90 seconds, at most 64 segments.
        segments = []
        for segment in transcript.segments[:64]:
            if segment.start is None or segment.end is None:
                raise ValueError("Smoke test requires timed segments")
            segments.append(segment)
            if segment.end - segments[0].start >= 45 * plan["max_chunks"]:
                break
        bounded = transcript.model_copy(
            update={
                "segments": segments,
                "text": "\n".join(s.text for s in segments),
            }
        )
        chunks = build_transcript_chunks(KnowledgeSettings(), bounded)[
            : plan["max_chunks"]
        ]
        if not chunks or any(not c.text.strip() or len(c.text) > 6000 for c in chunks):
            raise ValueError("No suitable small timed chunk (maximum 6000 characters)")
        write_json(
            directory / "chunks.json", [c.model_dump(mode="json") for c in chunks]
        )
        report["selected_chunks"] = [c.chunk_id for c in chunks]
        report["input_segments"] = len(segments)
        contract = ChunkKnowledgeResult.model_validate(
            {
                "analysis": {
                    "chunk_id": chunks[0].chunk_id,
                    "relevant": False,
                    "needs_visual_context": False,
                },
                "extraction": None,
            }
        )
        write_json(
            directory / "offline_contract.json", contract.model_dump(mode="json")
        )
        report["offline_contract_validated"] = True
        report["preparation_seconds"] = time.monotonic() - started
        report["phase"] = "marvin_initialization"
        checkpoint()
        init_start = time.monotonic()
        faulthandler.dump_traceback_later(max(1, plan["timeout"] * 0.6))
        import marvin

        report["initialization_seconds"] = time.monotonic() - init_start
        faulthandler.cancel_dump_traceback_later()
        report["marvin_version"] = getattr(marvin, "__version__", "unknown")
        # The actual lazy decorator and existing return schema, without calling it.
        decorated = _get_extract_knowledge()
        task = decorated.as_task(
            target_chunk=chunks[0].text, previous_context=None, next_context=None
        )
        report["task_schema"] = task.result_type.__name__
        if not plan["enable_api"]:
            result = ChunkKnowledgeResult.model_validate(
                {
                    "analysis": {
                        "chunk_id": chunks[0].chunk_id,
                        "relevant": False,
                        "needs_visual_context": False,
                    },
                    "extraction": None,
                }
            )
            write_json(
                directory / "offline_contract.json", result.model_dump(mode="json")
            )
            report.update(
                phase="offline_ready",
                validated=True,
                result_origin="synthetic contract, no generation",
            )
            checkpoint()
            return 0

        import httpx
        from openai import AsyncOpenAI
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        from src.utils.llm_helper import configure_marvin

        configure_marvin(SimpleNamespace(llm_model=plan["model"], llm_context=None))

        class BoundedTransport(httpx.AsyncBaseTransport):
            def __init__(self):
                self.inner = httpx.AsyncHTTPTransport(retries=0)

            async def handle_async_request(self, request):
                if request.url.host != "api.openai.com" or request.method != "POST":
                    raise RuntimeError("Unexpected API endpoint/method")
                budget.claim()
                report["api_requests"] = budget.requests
                checkpoint()
                try:
                    response = await self.inner.handle_async_request(request)
                    await response.aread()
                    if response.is_error:
                        budget.failed = True
                    body = response.json()
                    report["token_usage"].append(body.get("usage"))
                    checkpoint()
                    return response
                except Exception:
                    budget.failed = True
                    raise

            async def aclose(self):
                await self.inner.aclose()

        client = AsyncOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            max_retries=0,
            timeout=20,
            http_client=httpx.AsyncClient(
                transport=BoundedTransport(),
                timeout=20,
                trust_env=False,
            ),
        )
        marvin.defaults.model = OpenAIChatModel(
            plan["model"].removeprefix("openai:"),
            provider=OpenAIProvider(openai_client=client),
        )
        marvin.defaults.agent.model_settings = {"max_tokens": 1200}
        report["phase"] = "extraction"
        checkpoint()
        for chunk in chunks:
            budget.begin_chunk()
            call_start = time.monotonic()
            result = extract_knowledge(chunk.text, None, None)
            result = ChunkKnowledgeResult.model_validate(result)
            result = validate_extraction(attach_chunk_provenance(result, chunk))
            result = ChunkKnowledgeResult.model_validate_json(result.model_dump_json())
            write_json(
                directory / f"{chunk.chunk_id}.json", result.model_dump(mode="json")
            )
            report["results"].append(
                dict(
                    chunk_id=chunk.chunk_id,
                    validated=True,
                    runtime_seconds=time.monotonic() - call_start,
                )
            )
            checkpoint()
        report.update(phase="complete", validated=True, result_origin="LLM")
        checkpoint()
        return 0
    except Exception as exc:
        # Avoid SDK error bodies which can include submitted text or credentials.
        report.update(
            error_stage=report["phase"],
            phase="failed",
            error_type=type(exc).__name__,
            error="Initialization/extraction failed; no automatic retry",
        )
        if report.get("preparation_seconds") is not None:
            report["initialization_seconds"] = report.get(
                "initialization_seconds", time.monotonic() - init_start
            )
        if report["api_requests"] == 0:
            message = str(exc)[:500]
            key = os.environ.get("OPENAI_API_KEY")
            report["error_detail"] = (
                message.replace(key, "[redacted]") if key else message
            )
        report["http_status"] = getattr(exc, "status_code", None)
        faulthandler.cancel_dump_traceback_later()
        checkpoint()
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New dedicated directory; must not exist",
    )
    parser.add_argument("--max-chunks", type=int, choices=(1, 2), default=1)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--model", default="openai:gpt-4o-mini")
    parser.add_argument("--enable-api", action="store_true")
    args = parser.parse_args(argv)
    if os.name != "posix":
        parser.error("Process-group termination requires POSIX")
    if not 1 <= args.timeout <= 120:
        parser.error("timeout must be between 1 and 120 seconds")
    if not args.model.startswith("openai:"):
        parser.error("Only explicit openai:<model> names are supported")
    if not args.transcript.is_file():
        parser.error("Normalized TranscriptDocument JSON not found")
    if args.enable_api and not os.environ.get("OPENAI_API_KEY"):
        parser.error("--enable-api requires an explicitly exported OPENAI_API_KEY")
    directory = args.output.resolve()
    # Keep logs/database/results outside all production data directories.
    if directory.is_relative_to(ROOT / "data"):
        parser.error("Output must be outside the production data directory")
    directory.mkdir(parents=True, exist_ok=False)
    plan = dict(
        transcript=str(args.transcript.resolve()),
        max_chunks=args.max_chunks,
        model=args.model,
        enable_api=args.enable_api,
        timeout=args.timeout,
    )
    write_json(directory / "plan.json", plan)
    env = {
        key: os.environ[key]
        for key in ("PATH", "LANG", "LD_LIBRARY_PATH")
        if key in os.environ
    }
    env.update(
        ROOT=str(directory),
        DATA_DIR=str(directory / "data"),
        CHROMA_DIR=str(directory / "chroma"),
        WIKI_EN_API="https://example.invalid",
        HEADER_AGENT="cs50-smoke",
        HF_API_KEY="offline-placeholder",
        OPENAI_API_KEY=os.environ["OPENAI_API_KEY"]
        if args.enable_api
        else "offline-placeholder",
        MARVIN_HOME_PATH=str(directory / "marvin"),
        MARVIN_DATABASE_URL=f"sqlite+aiosqlite:///{directory / 'marvin.db'}",
    )
    if args.enable_api:
        env["CS50_SMOKE_ENABLE_API"] = "1"
    command = [
        sys.executable,
        "-I",
        str(Path(__file__).resolve()),
        "--worker",
        str(directory / "plan.json"),
    ]
    summary = supervise(command, directory, env, args.timeout)
    summary.update(enable_api=args.enable_api, timeout_seconds=args.timeout)
    if (directory / "worker.json").exists():
        summary["worker"] = json.loads((directory / "worker.json").read_text())
    if summary["timed_out"]:
        summary["error"] = (
            "Subprocess deadline exceeded; complete process group terminated"
        )
        if summary.get("worker", {}).get("phase") == "marvin_initialization":
            summary["initialization_incomplete_after_seconds"] = max(
                0, summary["runtime_seconds"] - summary["worker"]["preparation_seconds"]
            )
    write_json(directory / "report.json", summary)
    print(directory / "report.json")
    return 1 if summary["timed_out"] or summary["returncode"] else 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        raise SystemExit(worker(Path(sys.argv[2])))
    raise SystemExit(main())
