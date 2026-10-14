"""Real source/index core, exclusively synthetic HTTP and hash embeddings."""

import socket
from contextlib import closing
from pathlib import Path
from unittest.mock import patch


def demonstrate(adapter, directory, *, course=None, section=None, all_six=False):
    import httpx
    from qdrant_client import QdrantClient

    from src.core.config_knowledge import KnowledgeSettings
    from src.model_discovery.cs50_index import EmbeddingConfig
    from src.tools_knowledge.bind_cs50_transcript import save_portable_manifest
    from src.tools_knowledge.cs50_checkpoint import atomic_json
    from src.tools_rag.cs50_embeddings import FakeEmbedder
    from src.tools_rag.cs50_ingestion import (
        build_ingestion_plan,
        embed_plan,
        upsert_plan,
    )
    from src.tools_rag.cs50_orchestration import index_status, prepare_sources
    from src.tools_rag.cs50_retrieval import search_cs50_transcripts

    directory = Path(directory).absolute()
    repository = Path(__file__).resolve().parents[1]
    if directory.exists():
        raise FileExistsError("Demo requires an exclusive new directory")
    if directory.is_relative_to(repository) or any(
        p.is_symlink() for p in (directory, *directory.parents)
    ):
        raise ValueError("Demo must use an external nonsymlink scratch directory")
    directory.mkdir(parents=True)
    workspace = directory / "synthetic-sources"
    workspace.mkdir()
    requests = []
    body = b"1\n00:00:00,000 --> 00:00:20,000\nSynthetic Python input accepts a value.\n\n2\n00:00:20,000 --> 00:00:25,000\n\n3\n00:00:25,000 --> 00:00:50,000\nSynthetic Python print displays a value.\n\n4\n00:00:50,000 --> 00:01:20,000\nSynthetic Python function returns a value.\n"

    def http(request):
        requests.append(str(request.url))
        return httpx.Response(200, content=body)

    def forbidden(*args, **kwargs):
        raise AssertionError("Demo forbids real network")

    with (
        patch.object(socket.socket, "connect", forbidden),
        patch.object(socket, "getaddrinfo", forbidden),
    ):
        report, inputs = prepare_sources(
            adapter,
            workspace=workspace,
            course=course,
            section=section,
            all_six=all_six,
            execute_download=True,
            license_reviewed=True,
            transport=httpx.MockTransport(http),
        )
        save_portable_manifest(
            inputs, directory / "inputs.v2.json", workspace=workspace
        )
        config = EmbeddingConfig.fake(max_tokens=256).model_copy(
            update={"batch_size": 128}
        )
        engine = FakeEmbedder(config)
        plan = build_ingestion_plan(
            adapter,
            inputs,
            KnowledgeSettings(),
            engine,
            workspace=workspace,
            course=course,
            section=section,
            all_six=all_six,
            source_origin="synthetic",
        )
        atomic_json(directory / "ingestion-plan.v1.json", plan.model_dump(mode="json"))
        artifact = embed_plan(
            plan,
            adapter,
            engine,
            workspace=workspace,
            destination=directory / "vectors.v1.json",
        )
        with closing(QdrantClient(path=str(directory / "qdrant"))) as client:
            done = upsert_plan(
                client,
                plan,
                artifact,
                adapter,
                workspace=workspace,
                state_root=directory / "status",
                execute=True,
                allow_create=True,
            )
        # Reopen the actual persisted local DB for resume/readback, not only memory.
        with closing(QdrantClient(path=str(directory / "qdrant"))) as client:
            resumed = upsert_plan(
                client,
                plan,
                artifact,
                adapter,
                workspace=workspace,
                state_root=directory / "status",
                execute=True,
            )
            status = index_status(
                client,
                plan,
                artifact,
                adapter,
                workspace=workspace,
                state_root=directory / "status",
            )
            first = inputs[0]
            hits = search_cs50_transcripts(
                "Python input function",
                client,
                plan,
                engine,
                course_id=first.course_id,
                source_id=first.source_id,
                adapter=adapter,
                workspace=workspace,
            )
        report = {
            "schema_version": 1,
            "source_origin": "synthetic",
            "embedding_provider": "fake",
            "sources": len(inputs),
            "planned_source_tasks": report["tasks"],
            "fake_http_requests": len(requests),
            "units": len(plan.units),
            "unique_points": len({p.point_id for p in plan.units}),
            "complete": status["complete"],
            "resume_equal": done == resumed,
            "hits_original_checked": all(h.original_source_checked for h in hits),
            "recall_at_k": None,
            "mrr": None,
        }
        atomic_json(directory / "demo-report.v1.json", report)
        return report
