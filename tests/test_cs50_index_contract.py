import subprocess
import sys
from contextlib import closing
from uuid import UUID

import pytest
from pydantic import ValidationError
from qdrant_client import QdrantClient, models

from src.model_discovery.cs50_index import (
    CollectionContract,
    EmbeddingConfig,
    TranscriptPayload,
)
from src.tools_rag.cs50_collection import check_collection, ensure_collection


def payload():
    config = CollectionContract(embedding=EmbeddingConfig.fake())
    return TranscriptPayload(
        course_id="cs50x",
        section_key="ai",
        lecture_id="lecture",
        resource_id="srt",
        source_id="source",
        chunk_id="chunk_0000",
        original_url="https://cdn.cs50.net/python/2022/lectures/0/lang/en/lecture0.srt",
        raw_sha256="a" * 64,
        transcript_sha256="b" * 64,
        receipt_sha256="c" * 64,
        input_binding_sha256="d" * 64,
        chunk_plan_sha256="e" * 64,
        chunking={"overlap_segments": 2},
        transcript_provenance={
            "source_url": "https://cdn.cs50.net/python/2022/lectures/0/lang/en/lecture0.srt",
            "language": "en",
            "transcript_source": "official_subtitle",
            "media_format": "srt",
            "media_id": None,
        },
        provenance_sha256="f" * 64,
        discovery_provenance=(),
        original_chunk_text="Python input",
        original_chunk_segment_ids=(0, 2),
        original_chunk_start=1,
        original_chunk_end=5,
        text="Python",
        segment_ids=(0,),
        start=1,
        end=2,
        char_start=0,
        char_end=6,
        unit_index=0,
        unit_count=2,
        embedding_model=config.embedding.model,
        embedding_version=config.embedding.version,
        collection_contract_id=config.contract_id,
        source_origin="synthetic",
    )


def test_identity_roundtrip_and_original_keys():
    p = payload()
    assert UUID(p.point_id).version == 5
    assert TranscriptPayload.model_validate_json(p.model_dump_json()) == p
    assert p.point_id == TranscriptPayload.model_validate(p.model_dump()).point_id
    assert p.section_key == "ai" and p.media_id is None
    assert p.point_id != p.model_copy(update={"transcript_sha256": "0" * 64}).point_id
    config = CollectionContract(embedding=EmbeddingConfig.fake())
    assert CollectionContract.model_validate_json(config.model_dump_json()) == config
    p.check_collection(config)


@pytest.mark.parametrize(
    "update",
    [
        {"text": "invented"},
        {"segment_ids": (9,)},
        {"segment_ids": (0, 0)},
        {"start": 999},
        {"char_end": 100},
        {"unit_count": 0},
        {"original_url": "https://secret:password@cdn.cs50.net/a.srt"},
        {"transcript_provenance": {"source_file": "/personal/source.srt"}},
    ],
)
def test_invalid_payload(update):
    with pytest.raises(ValidationError):
        TranscriptPayload.model_validate(payload().model_dump() | update)


def test_real_collection_creation_and_version_checks():
    with closing(QdrantClient(":memory:")) as client:
        contract = CollectionContract(embedding=EmbeddingConfig.fake())
        with pytest.raises(ValueError, match="authorization"):
            ensure_collection(client, contract)
        ensure_collection(client, contract, allow_create=True)
        check_collection(client, contract)
        with pytest.raises(ValueError, match="dimension"):
            check_collection(
                client,
                contract.model_copy(
                    update={"embedding": EmbeddingConfig.fake(dimension=8)}
                ),
            )
        other = EmbeddingConfig.fake(max_tokens=64)
        with pytest.raises(ValueError, match="metadata"):
            ensure_collection(
                client,
                contract.model_copy(update={"embedding": other}),
                allow_create=True,
            )


def test_existing_unknown_collection_not_adopted():
    with closing(QdrantClient(":memory:")) as client:
        contract = CollectionContract(embedding=EmbeddingConfig.fake())
        client.create_collection(
            contract.name,
            vectors_config=models.VectorParams(
                size=16, distance=models.Distance.COSINE
            ),
        )
        with pytest.raises(ValueError, match="never adopt"):
            ensure_collection(client, contract, allow_create=True)


def test_unresolved_revision_and_fake_impersonation():
    with pytest.raises(ValidationError, match="immutable"):
        EmbeddingConfig(revision="main")
    with pytest.raises(ValidationError, match="never claim"):
        EmbeddingConfig(provider="fake", revision="fake-v1")


def test_contract_imports_need_no_optional_sdk():
    source = """
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in {'qdrant_client','sentence_transformers','torch','marvin','openai','pydantic_ai'}:
            raise AssertionError(fullname)
sys.meta_path.insert(0, Block())
import src.model_discovery.cs50_index
import src.tools_rag.cs50_collection
"""
    subprocess.run([sys.executable, "-c", source], check=True, timeout=15)
