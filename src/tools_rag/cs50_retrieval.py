"""Text retrieval only; no answer generation, downloads or implicit index writes."""

import math

from pydantic import Field

from src.model_discovery.cs50_index import TranscriptPayload
from src.tools_knowledge.cs50_checkpoint import Contract
from src.tools_rag.cs50_collection import check_collection
from src.tools_rag.cs50_ingestion import IngestionPlan, revalidate_plan


class TranscriptHit(Contract):
    point_id: str
    score: float = Field(allow_inf_nan=False)
    payload: TranscriptPayload
    original_source_checked: bool


def verify_hit(hit, plan, adapter, *, workspace):
    expected = {p.point_id: p for p in plan.units}
    if hit.point_id not in expected or hit.payload != expected[hit.point_id]:
        raise ValueError("Retrieval hit does not match the explicit source plan")
    revalidate_plan(
        plan, adapter, workspace=workspace, source_ids={hit.payload.source_id}
    )
    return True


def search_cs50_transcripts(
    query,
    client,
    plan,
    embedder,
    *,
    top_k=5,
    course_id=None,
    lecture_id=None,
    source_id=None,
    language="en",
    score_threshold=None,
    adapter=None,
    workspace=None,
):
    plan = IngestionPlan.model_validate_json(plan.model_dump_json())
    if not 1 <= top_k <= 100 or not query.strip():
        raise ValueError("Nonempty query and top_k between 1 and 100 required")
    if score_threshold is not None and (
        not math.isfinite(score_threshold) or not -1 <= score_threshold <= 1
    ):
        raise ValueError("Cosine score threshold must be finite and within [-1,1]")
    if embedder.config != plan.collection.embedding:
        raise ValueError("Query and document embedding configuration mismatch")
    if (adapter is None) != (workspace is None):
        raise ValueError(
            "Original verification requires adapter and workspace together"
        )
    check_collection(client, plan.collection)
    from qdrant_client import models

    must = [
        models.FieldCondition(
            key="source_id",
            match=models.MatchAny(any=[s.input["source_id"] for s in plan.sources]),
        )
    ]
    for key, value in (
        ("course_id", course_id),
        ("lecture_id", lecture_id),
        ("source_id", source_id),
        ("language", language),
    ):
        if value is not None:
            if not value.strip():
                raise ValueError("Empty filter value")
            must.append(
                models.FieldCondition(key=key, match=models.MatchValue(value=value))
            )
    vector = embedder.encode([query], query=True)[0]
    response = client.query_points(
        plan.collection.name,
        query=vector,
        query_filter=models.Filter(must=must),
        limit=top_k,
        score_threshold=score_threshold,
        with_payload=True,
    )
    expected = {p.point_id: p for p in plan.units}
    hits = []
    for record in response.points:
        if record.payload is None or any(
            key not in record.payload for key in plan.collection.required_payload_fields
        ):
            raise ValueError("Missing explicit retrieval payload/version fields")
        payload = TranscriptPayload.model_validate(record.payload)
        payload.check_collection(plan.collection)
        if str(record.id) != payload.point_id or payload != expected.get(
            str(record.id)
        ):
            raise ValueError(
                "Retrieved foreign/corrupted point; cannot adopt as source evidence"
            )
        hit = TranscriptHit(
            point_id=str(record.id),
            score=record.score,
            payload=payload,
            original_source_checked=False,
        )
        if adapter is not None:
            verify_hit(hit, plan, adapter, workspace=workspace)
            hit = hit.model_copy(update={"original_source_checked": True})
        hits.append(hit)
    return tuple(hits)
