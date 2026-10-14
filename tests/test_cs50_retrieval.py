from contextlib import closing

import pytest
from qdrant_client import QdrantClient
from test_cs50_ingestion import context as context
from test_cs50_ingestion import index_case as index_case

from src.model_discovery.cs50_index import EmbeddingConfig
from src.tools_rag.cs50_embeddings import FakeEmbedder
from src.tools_rag.cs50_ingestion import upsert_plan
from src.tools_rag.cs50_retrieval import TranscriptHit, search_cs50_transcripts


def test_real_local_retrieval_filters_and_original_validation(index_case, tmp_path):
    adapter, workspace, input, engine, plan, vectors = index_case
    with closing(QdrantClient(":memory:")) as client:
        upsert_plan(
            client,
            plan,
            vectors,
            adapter,
            workspace=workspace,
            state_root=tmp_path / "state",
            execute=True,
            allow_create=True,
        )
        hits = search_cs50_transcripts(
            "Python function argument",
            client,
            plan,
            engine,
            course_id=input.course_id,
            lecture_id=input.lecture_id,
            source_id=input.source_id,
            adapter=adapter,
            workspace=workspace,
            top_k=2,
            score_threshold=-1,
        )
        assert len(hits) == 2
        for hit in hits:
            assert hit.original_source_checked
            assert hit.payload.source_id == input.source_id
            assert hit.payload.text in hit.payload.original_chunk_text
            assert TranscriptHit.model_validate_json(hit.model_dump_json()) == hit
        assert not search_cs50_transcripts(
            "Python", client, plan, engine, course_id="cs50_sql"
        )
        assert not search_cs50_transcripts(
            "Python", client, plan, engine, language="de"
        )
        raw = search_cs50_transcripts("Python", client, plan, engine)
        assert not raw[0].original_source_checked


def test_foreign_retrieval_payload_rejected(index_case, tmp_path):
    adapter, workspace, _, engine, plan, vectors = index_case
    with closing(QdrantClient(":memory:")) as client:
        upsert_plan(
            client,
            plan,
            vectors,
            adapter,
            workspace=workspace,
            state_root=tmp_path / "state",
            execute=True,
            allow_create=True,
        )
        client.set_payload(
            plan.collection.name,
            {"text": "invented"},
            points=[p.point_id for p in plan.units],
        )
        with pytest.raises(ValueError):
            search_cs50_transcripts("Python", client, plan, engine)


def test_query_contract_and_original_hash_conflict(index_case, tmp_path):
    adapter, workspace, input, engine, plan, vectors = index_case
    with closing(QdrantClient(":memory:")) as client:
        upsert_plan(
            client,
            plan,
            vectors,
            adapter,
            workspace=workspace,
            state_root=tmp_path / "state",
            execute=True,
            allow_create=True,
        )
        with pytest.raises(ValueError, match="configuration"):
            search_cs50_transcripts(
                "Python",
                client,
                plan,
                FakeEmbedder(EmbeddingConfig.fake(max_tokens=128)),
            )
        with pytest.raises(ValueError):
            search_cs50_transcripts(" ", client, plan, engine)
        input.raw_srt_path.write_text("changed")
        with pytest.raises(ValueError, match="hash conflict"):
            search_cs50_transcripts(
                "Python", client, plan, engine, adapter=adapter, workspace=workspace
            )
