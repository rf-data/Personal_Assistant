import pytest
from test_cs50_ingestion import context as context
from test_cs50_ingestion import index_case as index_case
from test_cs50_knowledge_input import synthetic

from src.tools_rag.cs50_knowledge_index import (
    KnowledgeCollectionDefinition,
    KnowledgeMappingContext,
    map_knowledge_document,
)
from tests.qdrant_support import qdrant_client as qdrant_client


def documents(case, context):
    from src.core.config_knowledge import KnowledgeSettings

    adapter, workspace, input, _, plan, _ = case
    binder, _, consolidation, _ = context
    chunks = binder.build_cs50_knowledge_chunks(
        adapter, input, KnowledgeSettings(), workspace=workspace
    )
    doc = binder.build_cs50_knowledge_document(
        input, chunks, [synthetic(chunks[0])], plan=adapter, workspace=workspace
    )
    return doc, consolidation.consolidate_knowledge(doc)


def test_existing_models_extract_consolidate_to_future_contract(index_case, context):
    adapter, workspace, input, engine, plan, _ = index_case
    extraction, consolidated = documents(index_case, context)
    mapping = KnowledgeMappingContext(
        extraction_provider="fake",
        extraction_model="synthetic-test",
        prompt_version="knowledge_extraction_v1",
        result_schema_version="ChunkKnowledgeResult_v1",
        quality_status="synthetic",
    )
    for doc in (extraction, consolidated):
        records = map_knowledge_document(
            doc, plan, adapter, mapping, workspace=workspace
        )
        assert {r.kind for r in records} == {"statement", "formula"}
        assert len({r.point_id for r in records}) == len(records)
        for r in records:
            assert r.source_id == input.source_id and r.lecture_id == input.lecture_id
            assert r.quality_status == "synthetic" and r.extraction_provider == "fake"
            assert r.prompt_version == "knowledge_extraction_v1"
            assert r.evidence[0]["source"] == "transcript"
            assert r.transcript_provenance["transcript_source"] == "official_subtitle"
            assert type(r).model_validate_json(r.model_dump_json()) == r
    definition = KnowledgeCollectionDefinition(embedding=engine.config)
    assert not definition.execution_supported
    assert (
        type(definition).model_validate_json(definition.model_dump_json()) == definition
    )


def test_foreign_or_missing_knowledge_source_and_quality_rejected(index_case, context):
    adapter, workspace, _, _, plan, _ = index_case
    extraction, _ = documents(index_case, context)
    metadata = KnowledgeMappingContext(quality_status="synthetic")
    for identity in (None, "foreign"):
        with pytest.raises(ValueError, match="source_id"):
            map_knowledge_document(
                extraction.model_copy(update={"source_id": identity}),
                plan,
                adapter,
                metadata,
                workspace=workspace,
            )
    with pytest.raises(ValueError, match="Synthetic"):
        map_knowledge_document(
            extraction, plan, adapter, KnowledgeMappingContext(), workspace=workspace
        )
    with pytest.raises(ValueError, match="review"):
        KnowledgeMappingContext(quality_status="reviewed")


def test_unavailable_metadata_not_invented(index_case, context):
    adapter, workspace, _, _, plan, _ = index_case
    extraction, _ = documents(index_case, context)
    result = map_knowledge_document(
        extraction,
        plan,
        adapter,
        KnowledgeMappingContext(quality_status="synthetic"),
        workspace=workspace,
    )
    assert all(r.extraction_model is None and r.prompt_version is None for r in result)


def test_nonoriginal_evidence_times_rejected(index_case, context):
    adapter, workspace, _, _, plan, _ = index_case
    extraction, _ = documents(index_case, context)
    item = extraction.chunks[0].extraction.statements[0]
    item.start, item.end = 1.125, 2.125
    with pytest.raises(ValueError, match="original cue"):
        map_knowledge_document(
            extraction,
            plan,
            adapter,
            KnowledgeMappingContext(quality_status="synthetic"),
            workspace=workspace,
        )


def test_claimed_result_hash_requires_actual_matching_artifact(
    index_case, context, tmp_path
):
    from src.tools_lecture.execute_cs50 import digest

    adapter, workspace, _, _, plan, _ = index_case
    extraction, _ = documents(index_case, context)
    path = tmp_path / "extraction.json"
    path.write_text(extraction.model_dump_json())
    metadata = KnowledgeMappingContext(
        quality_status="synthetic", result_file_sha256=digest(path)
    )
    with pytest.raises(ValueError, match="explicit"):
        map_knowledge_document(extraction, plan, adapter, metadata, workspace=workspace)
    records = map_knowledge_document(
        extraction, plan, adapter, metadata, workspace=workspace, result_file=path
    )
    assert all(
        r.context.result_file_sha256 == digest(path)
        and not r.extraction_context_verified
        for r in records
    )
    path.write_text("{}")
    with pytest.raises(ValueError, match="hash"):
        map_knowledge_document(
            extraction, plan, adapter, metadata, workspace=workspace, result_file=path
        )
