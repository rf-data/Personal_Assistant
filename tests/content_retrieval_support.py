"""Handwritten synthetic reference constants, independent of search outputs."""

import base64
import json

from src.content_store._testing import project_synthetic_for_index, publish_synthetic
from src.content_store.index_projection import _load
from src.content_store.models import ArtifactReference, fingerprint, sha256
from src.content_store.read_models import TextWindow
from src.content_store.read_views import locators, route
from src.model_evaluation.content_retrieval import (
    ContentRelevanceJudgment,
    ContentRetrievalEvaluationSet,
    EvaluationArtifact,
    EvaluationScope,
    IndependentReview,
    Query,
    QueryResults,
    RetrievalConfiguration,
    RetrievalResults,
    ReviewedBlock,
    ReviewPool,
    VersionEvidence,
    dataset_digest,
    pool_scope,
)
from src.tools_rag.content_index_models import (
    RecordAnchor,
    ScoreComponent,
    SearchHit,
    SearchResultPage,
)
from tests.content_store_support import OWNER, config, payload, seeded

TEXT = "😀 α x² + y² = z²\nprint('hello')\n"
REGION = "x² + y² = z²"
REVIEW = IndependentReview(
    status="confirmed",
    method="synthetic_reference",
    reviewer="synthetic-fixture-author",
    evidence_reference="handwritten-test-constants-not-human-real-review",
    review_date="2026-10-18",
)
GENERATION = "a" * 64


def evidence(store, pid, projection, *, synthetic=False):
    # Test-only extraction from the existing verified snapshot boundary, own store.
    with store._maintenance(), store._connection() as db:
        source, sv, pv, parser, blocks, _, _ = _load(store, db, pid, OWNER, synthetic)
        refs = {
            r.sha256: ArtifactReference(
                **r.model_dump(include={"sha256", "size_bytes", "mime_type"})
            )
            for r in (*sv.manifest.artifacts, pv.payload, pv.projection)
        }
        artifacts = tuple(
            EvaluationArtifact(
                reference=ref,
                base64_bytes=base64.b64encode(store._read_blob(ref, db)).decode(),
            )
            for ref in refs.values()
        )
    return VersionEvidence(
        source=source,
        source_version=sv,
        parsed_version=pv,
        parser=parser,
        blocks=tuple(blocks),
        projection=projection,
        artifacts=artifacts,
    )


def make_evidence(tmp_path, *, text=TEXT, projection_config=None, unknown_time=False):
    store, source, _, sv = seeded(tmp_path)
    data = payload(sv.manifest.artifacts[0].sha256, text=text)
    if unknown_time:
        parsed = json.loads(data)
        for block in parsed["blocks"]:
            for locator in block["locators"]:
                locator.update(time_status="unknown", start=None, end=None)
        data = json.dumps(parsed, ensure_ascii=False).encode()
    pv = publish_synthetic(
        store,
        sv.source_version_id,
        data,
        config(),
        actor=OWNER,
        request_key="evaluation",
    ).version
    projection = project_synthetic_for_index(
        store, pv.parsed_version_id, actor=OWNER, config=projection_config
    )
    return evidence(store, pv.parsed_version_id, projection, synthetic=True)


def gold(v, block, target, text, start, grade):
    return ContentRelevanceJudgment(
        schema_version=1,
        query_id="query-1",
        gold_target_id=target,
        source_id=v.source.source_id,
        source_version_id=v.source_version.source_version_id,
        parsed_version_id=v.parsed_version.parsed_version_id,
        block_id=block.block_id,
        start=start,
        end=start + len(text),
        original_region=text,
        text_sha256=block.text_sha256,
        region_sha256=sha256(text.encode()),
        raw_sha256=block.locators[0].raw_artifact_sha256,
        locator=block.locators[0],
        grade=grade,
        review=REVIEW,
    )


def dataset_for(v, *, k=4, method="lexical", generation=GENERATION, judgments=None):
    query = Query(
        query_id="query-1",
        text="mathematical identity",
        scope=EvaluationScope(
            actor=OWNER,
            courses=("cs50_python",),
            source_ids=(v.source.source_id,),
            parsed_version_ids=(v.parsed_version.parsed_version_id,),
        ),
    )
    if judgments is None:
        paragraph = next(b for b in v.blocks if b.type == "paragraph")
        judgments = [gold(v, paragraph, "positive", REGION, 4, 3)]
        for b in v.blocks:
            if b.type in {"heading", "code", "formula"}:
                judgments.append(gold(v, b, "negative-" + b.type, b.type, 0, 0))
    retrieval_data = dict(
        method=method,
        ranking_schema="source_rrf_v1" if method == "lexical" else "synthetic_order_v1",
        backend_fingerprint="b" * 64,
        index_generation=generation,
        k=k,
        adapter="c24_search_result_page_v1"
        if method == "lexical"
        else "synthetic_ranking_list_v1",
    )
    dataset = ContentRetrievalEvaluationSet(
        schema_version=1,
        dataset_version="synthetic-v1",
        origin="synthetic",
        review_status="confirmed",
        corpus_complete=True,
        corpus_reference="bounded hand-authored synthetic originals",
        projection_config=v.projection.body.config,
        retrieval=RetrievalConfiguration(
            **retrieval_data, configuration_fingerprint=fingerprint(retrieval_data)
        ),
        queries=(query,),
        versions=(v,),
        judgments=tuple(judgments),
        pools=(),
    )
    blocks = tuple(
        ReviewedBlock(
            parsed_version_id=v.parsed_version.parsed_version_id,
            block_id=b.block_id,
            text_sha256=b.text_sha256,
        )
        for b in v.blocks
        if any(r.body.block_id == b.block_id for r in v.projection.body.records)
    )
    pool = ReviewPool(
        query_id=query.query_id,
        pool_complete=True,
        scope_sha256=pool_scope(dataset, query),
        reviewed_blocks=blocks,
        coverage_note="All listed original blocks reviewed for this synthetic query",
        review=REVIEW,
    )
    return dataset.model_copy(update={"pools": (pool,)})


def hit(v, record, *, generation=GENERATION):
    r = record.body
    b = next(b for b in v.blocks if b.block_id == r.block_id)
    end = min(r.end, r.start + 512)
    return SearchHit(
        index_record_id=record.index_record_id,
        source_id=r.source_id,
        source_version_id=r.source_version_id,
        parsed_version_id=r.parsed_version_id,
        block_id=r.block_id,
        content_type=r.content_type,
        anchor=RecordAnchor(
            parsed_version_id=r.parsed_version_id,
            block_id=r.block_id,
            text_sha256=r.text_sha256,
            start=r.start,
            end=r.end,
        ),
        excerpt=TextWindow(
            parsed_version_id=r.parsed_version_id,
            block_id=r.block_id,
            start=r.start,
            end=end,
            text_length=r.text_length,
            text_sha256=r.text_sha256,
            text=b.text[r.start : end],
        ),
        locators=locators(b, v.source_version),
        locators_in_structure=False,
        structure_route=route(
            "parsed", r.parsed_version_id, "blocks", r.block_id, "structure"
        ),
        text_route=route("parsed", r.parsed_version_id, "blocks", r.block_id, "text"),
        components=(ScoreComponent(source_id=r.source_id, raw_score=-1),),
        ranking_score=1 / 61,
        index_generation=generation,
        projection_fingerprint=r.projection_sha256,
    )


def results_for(
    dataset,
    *,
    order=("paragraph", "heading", "code", "formula"),
    page=None,
    security=(),
):
    if page is None:
        v = dataset.versions[0]
        records = {r.body.content_type: r for r in v.projection.body.records}
        page = SearchResultPage(
            items=tuple(
                hit(v, records[name], generation=dataset.retrieval.index_generation)
                for name in order
            ),
            next_cursor=None,
            index_generation=dataset.retrieval.index_generation,
        )
    q = dataset.queries[0]
    result = QueryResults(
        query_id=q.query_id,
        query_sha256=sha256(q.text.encode()),
        scope_sha256=fingerprint(q.scope.model_dump(mode="json")),
        configuration=dataset.retrieval,
        page=page,
    )
    return RetrievalResults(
        schema_version=1,
        dataset_sha256=dataset_digest(dataset),
        queries=(result,),
        security=security,
    )
