"""Independent metric constants and actual offline evidence, never model quality."""

import json
import socket

import pytest
from pydantic import ValidationError

from scripts.content_retrieval_evaluation import main, publish, read_input
from src.content_store.models import canonical, sha256
from src.model_evaluation.content_retrieval import (
    ContentRetrievalEvaluationSet,
    EvaluationConfig,
    IndependentReview,
    RetrievalEvaluationReport,
    SecurityEvidence,
    dataset_digest,
)
from src.tools_evaluation.evaluate_retrieval import evaluate_retrieval
from src.tools_evaluation.retrieval_metrics import graded_ranking, recall_and_rr
from src.tools_rag.cs50_retrieval_evaluation import ranking_metrics
from tests.content_retrieval_support import dataset_for, make_evidence, results_for


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    return dataset_for(make_evidence(tmp_path_factory.mktemp("synthetic-evidence")))


def run(dataset, results=None, **kwargs):
    return evaluate_retrieval(
        dataset,
        results or results_for(dataset, **kwargs),
        evaluation_config=EvaluationConfig(schema_version=1),
    )


def replace(dataset, **changes):
    return ContentRetrievalEvaluationSet.model_validate(
        dataset.model_dump(mode="json") | changes
    )


@pytest.mark.parametrize(
    "order,expected",
    [
        (("paragraph", "heading", "code", "formula"), (0.25, 1.0, 1.0, 1.0)),
        (
            ("heading", "code", "formula", "paragraph"),
            (0.25, 1.0, 0.25, 0.43067655807339306),
        ),
        (("heading", "code", "formula"), (0.0, 0.0, 0.0, 0.0)),
        ((), (0.0, 0.0, 0.0, 0.0)),
        (("paragraph",), (0.25, 1.0, 1.0, 1.0)),
        (("paragraph", "paragraph", "paragraph", "paragraph"), (0.25, 1.0, 1.0, 1.0)),
    ],
)
def test_handwritten_metric_constants(dataset, order, expected):
    q = run(dataset, order=order).report.queries[0]
    assert q.status == "evaluated", q.technical_failures
    assert (
        q.precision_at_k.value,
        q.recall_at_k.value,
        q.reciprocal_rank_at_k.value,
        q.ndcg_at_k.value,
    ) == pytest.approx(expected)
    assert q.precision_at_k.denominator == 4


def test_no_positive_gold_has_explicit_null_denominators(dataset):
    data = dataset.model_dump(mode="json")
    data["judgments"][0]["grade"] = 0
    d = ContentRetrievalEvaluationSet.model_validate(data)
    r = run(d).report
    assert r.precision_at_k.value == 0
    for metric in (r.recall_at_k, r.mrr_at_k, r.ndcg_at_k):
        assert metric.value is None and metric.denominator == 0
        assert metric.excluded == 1
    assert r.queries[0].recall_at_k.status == "not_determinable"


@pytest.mark.parametrize(
    "change,reason",
    [
        ("pool_missing", "incomplete_review_pool"),
        ("pool_incomplete", "incomplete_review_pool"),
        ("pool_pending", "incomplete_review_pool"),
        ("pool_hash", "pool_coverage_binding"),
        ("coverage", "pool_coverage_binding"),
        ("pending", "unconfirmed_gold"),
        ("corpus", "incomplete_corpus"),
        ("review", "dataset_not_reviewed"),
    ],
)
def test_incomplete_reviews_never_become_zero_quality(dataset, change, reason):
    data = dataset.model_dump(mode="json")
    if change == "pool_missing":
        data["pools"] = []
    elif change == "pool_incomplete":
        data["pools"][0]["pool_complete"] = False
    elif change == "pool_pending":
        data["pools"][0]["review"]["status"] = "pending_review"
    elif change == "pool_hash":
        data["pools"][0]["scope_sha256"] = "0" * 64
    elif change == "coverage":
        data["pools"][0]["reviewed_blocks"] = []
    elif change == "pending":
        data["judgments"][0]["review"]["status"] = "pending_review"
    elif change == "corpus":
        data["corpus_complete"] = False
    else:
        data["review_status"] = "pending_review"
    d = ContentRetrievalEvaluationSet.model_validate(data)
    r = run(d).report
    assert reason in r.queries[0].reasons
    assert r.precision_at_k.value is None
    assert r.queries[0].precision_at_k.status == "not_evaluable"


@pytest.mark.parametrize(
    "field,value",
    [
        ("reviewer", None),
        ("evidence_reference", None),
        ("review_date", None),
        ("method", "prediction_preannotation"),
    ],
)
def test_no_self_confirming_gold(dataset, field, value):
    data = dataset.judgments[0].review.model_dump(mode="json")
    with pytest.raises(ValidationError):
        IndependentReview.model_validate(data | {field: value})


@pytest.mark.parametrize("origin", ["real", "unknown"])
def test_synthetic_review_is_never_promoted(dataset, origin):
    with pytest.raises(ValidationError, match="origin"):
        replace(dataset, origin=origin)
    data = dataset.model_dump(mode="json")
    data["origin"] = origin
    for j in data["judgments"]:
        j["review"]["status"] = "pending_review"
    data["pools"][0]["review"]["status"] = "pending_review"
    r = run(ContentRetrievalEvaluationSet.model_validate(data)).report
    assert r.origin == origin and r.precision_at_k.value is None


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("parsed", "hit_version_binding"),
        ("block", "hit_record_binding"),
        ("hash", "hit_text_anchor"),
        ("excerpt", "hit_text_anchor"),
        ("generation", "stale_generation"),
        ("scope", "hit_scope_binding"),
        ("locator", "hit_locator_binding"),
        ("route", "hit_route_binding"),
        ("score", "foreign_score_component"),
        ("external", "external_locators_not_checked"),
    ],
)
def test_bad_hits_fail_closed(dataset, mutation, code):
    result = results_for(dataset)
    data = result.model_dump(mode="json")
    h = data["queries"][0]["page"]["items"][0]
    if mutation == "parsed":
        h["parsed_version_id"] = "foreign-parsed"
    elif mutation == "block":
        h["block_id"] = "foreign-block"
    elif mutation == "hash":
        h["anchor"]["text_sha256"] = "0" * 64
    elif mutation == "excerpt":
        h["excerpt"]["text"] = "forged text"
    elif mutation == "generation":
        h["index_generation"] = "0" * 64
    elif mutation == "scope":
        h["source_id"] = "foreign-source"
    elif mutation == "locator":
        h["locators"][0]["page"] = 99
    elif mutation == "route":
        h["text_route"] = "/foreign"
    elif mutation == "score":
        h["components"][0]["source_id"] = "foreign-source"
    else:
        h["locators_in_structure"], h["locators"] = True, None
    r = run(dataset, type(result).model_validate(data)).report
    assert code in r.queries[0].technical_failures
    assert r.release_blocker and r.precision_at_k.value is None


@pytest.mark.parametrize("field", ["raw_sha256", "region_sha256", "text_sha256"])
def test_gold_hashes_are_checked(dataset, field):
    data = dataset.model_dump(mode="json")
    data["judgments"][0][field] = "0" * 64
    r = run(ContentRetrievalEvaluationSet.model_validate(data)).report
    assert "gold_region_binding" in r.queries[0].technical_failures


def test_original_artifact_bytes_are_hashed(dataset):
    data = dataset.model_dump(mode="json")
    data["versions"][0]["artifacts"][0]["base64_bytes"] = "YQ=="
    r = run(ContentRetrievalEvaluationSet.model_validate(data)).report
    assert "artifact_hash" in r.queries[0].technical_failures
    assert r.release_blocker


def test_reviewed_negative_distinct_from_unjudged(dataset):
    data = dataset.model_dump(mode="json")
    data["judgments"] = [
        j for j in data["judgments"] if j["gold_target_id"] != "negative-heading"
    ]
    d = ContentRetrievalEvaluationSet.model_validate(data)
    r = run(d).report
    assert "unjudged_hit" in r.queries[0].reasons
    assert r.precision_at_k.value is None


def test_overlap_gold_is_rejected_and_large_regions_require_manual_split(dataset):
    data = dataset.model_dump(mode="json")
    data["judgments"].append(data["judgments"][0] | {"gold_target_id": "overlap"})
    with pytest.raises(ValidationError, match="overlapping"):
        ContentRetrievalEvaluationSet.model_validate(data)
    data = dataset.judgments[0].model_dump(mode="json")
    with pytest.raises(ValidationError):
        type(dataset.judgments[0]).model_validate(
            data | {"original_region": "x" * 2001, "start": 0, "end": 2001}
        )


def test_unicode_formula_and_code_are_exact_original_anchors(dataset):
    j = dataset.judgments[0]
    assert j.start == 4 and j.original_region == "x² + y² = z²"
    assert dataset.versions[0].blocks[1].text.startswith("😀 α ")
    data = dataset.model_dump(mode="json")
    data["judgments"][0]["start"] = 5
    data["judgments"][0]["end"] += 1
    r = run(ContentRetrievalEvaluationSet.model_validate(data)).report
    assert "gold_region_binding" in r.queries[0].technical_failures
    assert not r.queries[0].gains


@pytest.mark.parametrize("method", ["lexical", "vector", "hybrid"])
def test_one_arithmetic_contract_for_all_ranking_lists(dataset, method):
    d = dataset_for(dataset.versions[0], method=method)
    r = run(d, order=("heading", "code", "formula", "paragraph")).report
    assert r.mrr_at_k.value == 0.25
    assert r.ndcg_at_k.value == pytest.approx(0.43067655807339306)
    assert r.retrieval.method == method


def test_deterministic_digest_redacted_report_and_changed_rank(dataset):
    one, two = run(dataset), run(dataset)
    assert one.digest == two.digest
    assert RetrievalEvaluationReport.model_validate_json(one.model_dump_json()) == one
    changed = run(dataset, order=("heading", "code", "formula", "paragraph"))
    assert changed.digest != one.digest
    public = one.model_dump_json()
    for value in (
        dataset.queries[0].text,
        dataset.queries[0].scope.actor.subject,
        dataset.versions[0].source.source_id,
        "/tmp/",
        "x²",
        "hello",
    ):
        assert value not in public
    with pytest.raises(ValidationError):
        RetrievalEvaluationReport.model_validate(
            one.model_dump(mode="json") | {"digest": "0" * 64}
        )


def test_missing_results_and_short_page_with_cursor(dataset):
    results = results_for(dataset)
    missing = results.model_copy(update={"queries": ()})
    assert "missing_results" in run(dataset, missing).report.queries[0].reasons
    q = results.queries[0]
    short = q.page.model_copy(
        update={"items": q.page.items[:1], "next_cursor": "opaque-never-replayed"}
    )
    result = results.model_copy(
        update={"queries": (q.model_copy(update={"page": short}),)}
    )
    assert (
        "insufficient_ranking_window" in run(dataset, result).report.queries[0].reasons
    )


def test_security_findings_never_averaged_away(dataset):
    leak = SecurityEvidence(
        scenario="text_leak",
        status="failed",
        reason="synthetic injected leak detected",
        confirmed_leak=True,
        evidence_sha256="d" * 64,
    )
    r = run(dataset, security=(leak,)).report
    assert r.release_blocker and r.precision_at_k.value == 0.25
    assert len([s for s in r.security if s.status == "not_checked"]) == 11
    assert r.live_authorization == "not_checked" and r.real_acceptance == "blocked"
    with pytest.raises(ValidationError):
        SecurityEvidence(scenario="text_leak", status="passed", reason="unbacked claim")


def test_legacy_arithmetic_and_review_gates_still_strict():
    assert ranking_metrics([{1, 2}, {3}], [[2, 4], [0, 3]], k=2) == {
        "recall_at_k": 0.75,
        "mrr_at_k": 0.75,
    }
    with pytest.raises(ValueError):
        ranking_metrics([set()], [[]], k=5)
    assert recall_and_rr({"a"}, ["b", "b", "b", "a"], k=4) == (1, 0.25)
    assert graded_ranking([0, 0, 0, 3], [3], k=4) == pytest.approx(
        (3.0147359065137516, 7)
    )


def test_cli_hashes_no_overwrite_and_malformed_inputs(tmp_path, dataset, capsys):
    d, rs = tmp_path / "dataset.json", tmp_path / "results.json"
    d.write_bytes(canonical(dataset.model_dump(mode="json")))
    rs.write_bytes(canonical(results_for(dataset).model_dump(mode="json")))
    output = tmp_path / "reports"
    argv = ["--dataset", str(d), "--results", str(rs), "--output", str(output)]
    assert main(argv) == 0
    manifest = json.loads((output / "manifest.json").read_bytes())
    for name, digest in manifest["files"].items():
        assert sha256((output / name).read_bytes()) == digest
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    assert main(argv) == 2
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}
    report = read_input(output / "report.v1.json", RetrievalEvaluationReport)
    publish(report, tmp_path / "again")
    assert (tmp_path / "again" / "report.v1.json").read_bytes() == before[
        "report.v1.json"
    ]
    d.write_text('{"schema_version":1,"schema_version":1}')
    assert main(argv) == 2
    assert "rejected" in capsys.readouterr().err


@pytest.mark.parametrize(
    "change", ["version", "bool_version", "duplicate", "scope", "unknown_field"]
)
def test_schema_errors(dataset, change):
    data = dataset.model_dump(mode="json")
    if change == "version":
        data.pop("schema_version")
    elif change == "bool_version":
        data["schema_version"] = True
    elif change == "duplicate":
        data["queries"].append(data["queries"][0])
    elif change == "scope":
        data["queries"][0]["scope"]["actor"]["courses"] = []
    else:
        data["magic_verified"] = True
    with pytest.raises(ValidationError):
        ContentRetrievalEvaluationSet.model_validate(data)


def test_request_and_dataset_digests(dataset):
    result = results_for(dataset)
    with pytest.raises(ValueError, match="digest"):
        run(dataset, result.model_copy(update={"dataset_sha256": "0" * 64}))
    q = result.queries[0].model_copy(update={"query_sha256": "0" * 64})
    r = run(dataset, result.model_copy(update={"queries": (q,)})).report
    assert "result_request_binding" in r.queries[0].technical_failures
    assert result.dataset_sha256 == dataset_digest(dataset)


def test_macro_excludes_missing_query_instead_of_adding_zero(dataset):
    from src.model_evaluation.content_retrieval import pool_scope

    first = dataset.queries[0]
    second = first.model_copy(update={"query_id": "missing-query"})
    d = dataset.model_copy(update={"queries": (first, second)})
    pool = d.pools[0].model_copy(
        update={"query_id": second.query_id, "scope_sha256": pool_scope(d, second)}
    )
    judgments = tuple(
        j.model_copy(
            update={
                "query_id": second.query_id,
                "gold_target_id": "second-" + j.gold_target_id,
            }
        )
        for j in dataset.judgments
    )
    d = d.model_copy(
        update={"pools": (*d.pools, pool), "judgments": (*d.judgments, *judgments)}
    )
    report = run(d).report
    assert (report.query_count, report.evaluable_queries, report.excluded_queries) == (
        2,
        1,
        1,
    )
    assert report.mrr_at_k.numerator == report.mrr_at_k.denominator == 1
    assert report.mrr_at_k.value == 1 and report.mrr_at_k.exclusion_reasons == {
        "missing_results": 1
    }


def test_unknown_txt_time_remains_unknown(tmp_path):
    from src.tools_transcribe.import_transcript import import_txt
    from tests.content_retrieval_support import TEXT

    path = tmp_path / "synthetic.txt"
    path.write_text(TEXT)
    doc = import_txt(
        path, language="en", original_url="https://example.invalid/synthetic.txt"
    )
    assert all(s.start is None and s.end is None for s in doc.segments)
    # Synthetic Content contract projection, not a claimed TXT B-adapter import.
    d = dataset_for(make_evidence(tmp_path, unknown_time=True))
    q = run(d).report.queries[0]
    assert q.locator_known == 0 and q.locator_unknown == 4
    assert q.locator_coordinates["time"] == {
        "known": 0,
        "unknown": 4,
        "not_applicable": 0,
    }


def test_unreviewed_or_foreign_hits_beyond_k_are_not_ignored(dataset):
    d = dataset_for(dataset.versions[0], k=1)
    result = results_for(d)
    data = result.model_dump(mode="json")
    data["queries"][0]["page"]["items"][1]["source_id"] = "foreign"
    report = run(d, type(result).model_validate(data)).report
    assert "hit_scope_binding" in report.queries[0].technical_failures
    assert report.release_blocker


def test_retrieval_configuration_fingerprint_cannot_be_declared_arbitrarily(dataset):
    from src.model_evaluation.content_retrieval import RetrievalConfiguration

    data = dataset.retrieval.model_dump(mode="json")
    with pytest.raises(ValidationError, match="fingerprint"):
        RetrievalConfiguration.model_validate(data | {"k": 3})


def test_legacy_transcript_review_rejects_synthetic_and_missing_review():
    from types import SimpleNamespace

    from src.tools_rag.cs50_retrieval_evaluation import reviewed_metrics

    plan = SimpleNamespace(
        collection=SimpleNamespace(embedding=SimpleNamespace(provider="fake"))
    )
    with pytest.raises(ValueError, match="Fake"):
        reviewed_metrics(SimpleNamespace(source_origin="synthetic"), [], {}, plan)
    plan.collection.embedding.provider = "local"
    plan.units = ()
    with pytest.raises(ValueError, match="Every real question"):
        reviewed_metrics(SimpleNamespace(source_origin="official"), [], {}, plan)


def test_target_identity_cannot_collide_with_uncredited_rank_marker(dataset):
    data = dataset.model_dump(mode="json")
    data["judgments"][0]["gold_target_id"] = "uncredited-rank-1"
    d = ContentRetrievalEvaluationSet.model_validate(data)
    report = run(d, order=("heading", "code", "formula", "paragraph")).report
    assert report.mrr_at_k.value == 0.25 and report.recall_at_k.value == 1


def test_rejected_gold_is_excluded_without_becoming_negative(dataset):
    data = dataset.model_dump(mode="json")
    data["judgments"][0]["review"]["status"] = "rejected"
    d = ContentRetrievalEvaluationSet.model_validate(data)
    assert "unjudged_hit" in run(d).report.queries[0].reasons


def test_unknown_format_coords_are_not_invented(dataset):
    q = run(dataset).report.queries[0]
    assert q.locator_coordinates["line"]["unknown"] == 4
    assert q.locator_coordinates["dom"]["unknown"] == 4
    assert q.locator_coordinates["page"]["known"] == 4
