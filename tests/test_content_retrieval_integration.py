"""Real local ContentStore/FTS operations with independently authored synthetic gold."""

import socket

import pytest

from src.content_store.index_models import IndexProjectionConfig
from src.content_store.index_projection import project_content_for_index
from src.content_store.models import SourceGrant, fingerprint
from src.content_store.store import ContentStore
from src.job_control.models import Principal
from src.model_evaluation.content_retrieval import (
    EvaluationConfig,
    SecurityEvidence,
    pool_scope,
)
from src.tools_evaluation.evaluate_retrieval import evaluate_retrieval
from src.tools_rag.content_index import ContentIndex
from src.tools_rag.content_index_models import SearchResultPage
from tests.content_retrieval_support import (
    REGION,
    dataset_for,
    evidence,
    gold,
    hit,
    make_evidence,
    results_for,
)
from tests.content_store_support import OTHER, OWNER, VIEWER
from tests.test_content_fts import hits, inventory, make_index


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


def evaluate(d, r):
    return evaluate_retrieval(
        d, r, evaluation_config=EvaluationConfig(schema_version=1)
    )


@pytest.mark.parametrize(
    "kind,query,region,start",
    [("code", "hello", "hello", 7), ("srt", "Hallo", "Hallo Ä", 0)],
)
def test_verified_bundle_projection_fts_gold_report_reopen(
    tmp_path, kind, query, region, start
):
    i, store, pv, _, selection, _, key = make_index(tmp_path, kind)
    before = inventory(store.root)
    projection = project_content_for_index(store, pv.parsed_version_id, actor=OWNER)
    v = evidence(store, pv.parsed_version_id, projection)
    b = v.blocks[1] if kind == "code" else v.blocks[0]
    # The constants above come from the handwritten original, never a hit excerpt.
    assert b.text[start : start + len(region)] == region
    j = gold(v, b, "independent-synthetic-original", region, start, 3)
    page = hits(i, query)
    assert page.items and page.next_cursor is None
    d = dataset_for(v, k=4, generation=page.index_generation, judgments=(j,))
    q = d.queries[0].model_copy(update={"text": query})
    d = d.model_copy(update={"queries": (q,)})
    d = d.model_copy(
        update={
            "pools": (d.pools[0].model_copy(update={"scope_sha256": pool_scope(d, q)}),)
        }
    )
    r = evaluate(d, results_for(d, page=page))
    assert r.report.precision_at_k.value == 0.25
    assert (
        r.report.recall_at_k.value
        == r.report.mrr_at_k.value
        == r.report.ndcg_at_k.value
        == 1
    )
    assert not r.report.release_blocker
    q_report = r.report.queries[0]
    if kind == "srt":
        assert q_report.locator_known == 1 and page.items[0].locators[0].start == 0.1
    else:
        assert page.items[0].locators[0].start is None
        assert q_report.locator_not_applicable + q_report.locator_unknown == 1
    reopened = ContentIndex(ContentStore(store.root), i.root, cursor_key_file=key)
    again = hits(reopened, query)
    assert evaluate(d, results_for(d, page=again)).digest == r.digest
    assert inventory(store.root) == before
    assert i.build(selection, actor=OWNER).generation_id is not None


def test_overlapping_chunks_partial_coverage_and_no_rank_compression(tmp_path):
    text = "x" * 149 + REGION + "y" * 200
    v = make_evidence(
        tmp_path,
        text=text,
        projection_config=IndexProjectionConfig(
            schema_version=1, max_codepoints=160, overlap_codepoints=128
        ),
    )
    b = next(b for b in v.blocks if b.type == "paragraph")
    d = dataset_for(v, judgments=(gold(v, b, "region", REGION, 149, 3),))
    records = [r for r in v.projection.body.records if r.body.block_id == b.block_id]
    assert (
        records[0].body.start == 0 and records[0].body.end == 160
    )  # misses the last character
    assert records[1].body.start == 32
    page = SearchResultPage(
        items=tuple(
            hit(v, r) for r in (records[0], records[1], records[2], records[3])
        ),
        next_cursor=None,
        index_generation=d.retrieval.index_generation,
    )
    report = evaluate(d, results_for(d, page=page)).report
    assert report.queries[0].gains == (0, 3, 0, 0)
    assert report.mrr_at_k.value == 0.5
    assert report.precision_at_k.value == 0.25
    assert report.ndcg_at_k.value == pytest.approx(0.6309297535714574)


def test_one_hit_cannot_credit_two_disjoint_targets(tmp_path):
    v = make_evidence(tmp_path)
    b = next(b for b in v.blocks if b.type == "paragraph")
    d = dataset_for(
        v,
        judgments=(
            gold(v, b, "first", REGION, 4, 3),
            gold(v, b, "second", "print('hello')", 17, 2),
        ),
    )
    report = evaluate(d, results_for(d, order=("paragraph", "paragraph"))).report
    assert report.queries[0].gains == (3, 0)
    assert report.recall_at_k.value == 0.5
    assert report.precision_at_k.value == 0.25


def test_executed_acl_scenarios_reported_separately(tmp_path):
    i, store, pv, *_ = make_index(tmp_path)
    v = evidence(
        store,
        pv.parsed_version_id,
        project_content_for_index(store, pv.parsed_version_id, actor=OWNER),
    )
    b = v.blocks[1]
    positive = gold(v, b, "hello", "hello", 7, 3)
    page = hits(i)
    d = dataset_for(v, generation=page.index_generation, judgments=(positive,))
    observed = {}
    denied = hits(i, actor=OTHER)
    assert denied.items == ()
    observed["unauthorized_source"] = denied.model_dump(mode="json")
    no_course = hits(
        i, actor=Principal(subject=OWNER.subject, role="operator", courses=())
    )
    assert no_course.items == ()
    observed["missing_course"] = no_course.model_dump(mode="json")
    store.set_source_grants(
        pv.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    assert hits(i, actor=VIEWER).items
    store.set_source_grants(pv.source_id, (), expected_acl_revision=1, actor=OWNER)
    revoked = hits(i, actor=VIEWER)
    assert revoked.items == ()
    observed["revoked_grant"] = revoked.model_dump(mode="json")
    for scenario in ("existence_leak", "text_leak", "locator_leak"):
        assert denied.model_dump(mode="json") == hits(
            i, actor=OTHER, source_ids=("nonexistent",)
        ).model_dump(mode="json")
        observed[scenario] = denied.model_dump(mode="json")
    security = tuple(
        SecurityEvidence(
            scenario=name,
            status="passed",
            reason="executed synthetic FTS integration assertions",
            evidence_sha256=fingerprint(value),
        )
        for name, value in observed.items()
    )
    report = evaluate(d, results_for(d, page=page, security=security)).report
    assert sum(s.status == "passed" for s in report.security) == 6
    assert sum(s.status == "not_checked" for s in report.security) == 6
    assert not report.release_blocker


def test_integrated_vector_dto_uses_same_evaluator_without_new_backend(tmp_path):
    from src.model_evaluation.content_retrieval import RetrievalConfiguration
    from tests.test_content_vectors import case, search

    _, vector, pv, _, _ = case(tmp_path, "code")
    page = search(vector, "hello")
    assert page.items and all(h.method == "vector" for h in page.items)
    v = evidence(
        vector.store,
        pv.parsed_version_id,
        project_content_for_index(vector.store, pv.parsed_version_id, actor=OWNER),
    )
    judgments = (
        gold(v, v.blocks[1], "hello", "hello", 7, 3),
        gold(v, v.blocks[0], "negative-header", "# Ä", 0, 0),
    )
    d = dataset_for(
        v, method="vector", generation=page.index_generation, judgments=judgments
    )
    c = d.retrieval.model_dump(mode="json", exclude={"configuration_fingerprint"})
    c.update(adapter="c24_search_result_page_v1", ranking_schema="cosine_l2_v1")
    q = d.queries[0].model_copy(update={"text": "hello"})
    d = d.model_copy(
        update={
            "retrieval": RetrievalConfiguration(
                **c, configuration_fingerprint=fingerprint(c)
            ),
            "queries": (q,),
        }
    )
    d = d.model_copy(
        update={
            "pools": (d.pools[0].model_copy(update={"scope_sha256": pool_scope(d, q)}),)
        }
    )
    report = evaluate(d, results_for(d, page=page)).report
    assert report.evaluable_queries == 1 and not report.release_blocker
    assert report.retrieval.ranking_schema == "cosine_l2_v1"
    assert report.live_authorization == "not_checked"
