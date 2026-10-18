"""Bounded offline evaluation of supplied evidence and actual C24 result DTOs."""

import base64
import binascii
from collections import Counter

from src.content_store.errors import ContentStoreError
from src.content_store.models import canonical, fingerprint, sha256, snapshot
from src.content_store.read_views import locators, route
from src.model_discovery.cs50 import deterministic_id
from src.model_evaluation.content_retrieval import (
    SCENARIOS,
    ContentRetrievalEvaluationSet,
    EvaluationConfig,
    MacroMetric,
    Metric,
    QueryEvaluation,
    RetrievalEvaluationReport,
    RetrievalReportBody,
    RetrievalResults,
    SecurityEvidence,
    dataset_digest,
    pool_scope,
)
from src.tools_evaluation.retrieval_metrics import graded_ranking, recall_and_rr
from src.tools_materials.quality import _json


def _version_errors(v, config):
    """Hash original bytes and connect supplied typed identities; no parsing/recovery."""
    errors = set()
    s, sv, pv, parser, p = (
        v.source,
        v.source_version,
        v.parsed_version,
        v.parser,
        v.projection.body,
    )
    if (s.source_id, sv.source_id, pv.source_id, p.source_id) != (s.source_id,) * 4:
        errors.add("source_binding")
    if (pv.source_version_id, p.source_version_id) != (sv.source_version_id,) * 2:
        errors.add("source_version_binding")
    if p.parsed_version_id != pv.parsed_version_id:
        errors.add("parsed_version_binding")
    if (pv.parser_config_id, p.parser_config_id) != (
        parser.config_id,
    ) * 2 or pv.payload_schema != parser.payload_schema:
        errors.add("parser_binding")
    if (p.payload_sha256, p.projection_sha256, p.config) != (
        pv.payload.sha256,
        pv.projection.sha256,
        config,
    ):
        errors.add("projection_binding")
    if s.state != "registered" or sv.state != "verified" or pv.state != "published":
        errors.add("unavailable_version")
    blobs = {}
    for a in v.artifacts:
        try:
            data = base64.b64decode(a.base64_bytes, validate=True)
        except (ValueError, binascii.Error):
            errors.add("artifact_encoding")
            continue
        if len(data) != a.reference.size_bytes or sha256(data) != a.reference.sha256:
            errors.add("artifact_hash")
        if a.reference.sha256 in blobs:
            errors.add("duplicate_artifact")
        blobs[a.reference.sha256] = data
    required = {a.sha256 for a in (*sv.manifest.artifacts, pv.payload, pv.projection)}
    if set(blobs) != required:
        errors.add("artifact_closure")
    for ref in (*sv.manifest.artifacts, pv.payload, pv.projection):
        if ref.sha256 in blobs and len(blobs[ref.sha256]) != ref.size_bytes:
            errors.add("artifact_size_binding")
    if len({b.block_id for b in v.blocks}) != len(v.blocks) or [
        b.order for b in v.blocks
    ] != list(range(len(v.blocks))):
        errors.add("block_identity")
    try:
        projection = _json(blobs[pv.projection.sha256])
        canonical(projection)
        actual = projection["blocks"]
        if parser.adapter_version == "cs50_srt_content_v1":
            actual = [
                dict(
                    b,
                    block_id=deterministic_id(
                        "content_cue_v1",
                        pv.parsed_version_id,
                        str(b["locators"][0]["original_segment_id"]),
                    ),
                )
                for b in actual
            ]
        if (
            projection.get("schema_version") != 1
            or projection["slot_id"] != pv.slot_id
            or actual != [b.model_dump(mode="json") for b in v.blocks]
        ):
            errors.add("original_projection_binding")
    except (
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        UnicodeError,
        RecursionError,
        ContentStoreError,
    ):
        errors.add("original_projection_binding")
    blocks = {b.block_id: b for b in v.blocks}
    raw = {a.sha256 for a in sv.manifest.artifacts}
    for b in v.blocks:
        if any(
            loc.raw_artifact_sha256 not in raw
            or loc.origin_pointer != b.payload_pointer
            for loc in b.locators
        ):
            errors.add("raw_locator_binding")
    for r in p.records:
        rb = r.body
        b = blocks.get(rb.block_id)
        if b is None or (
            rb.text_sha256 != b.text_sha256
            or rb.text_length != len(b.text)
            or rb.search_text != b.text[rb.start : rb.end]
            or rb.locators != b.locators
            or rb.origin_pointer != b.payload_pointer
            or rb.block_order != b.order
            or rb.original_type != b.original_type
            or rb.course_id != s.registration.course_id
            or rb.parser_fingerprint != fingerprint(parser.model_dump(mode="json"))
        ):
            errors.add("record_block_binding")
    return errors


def _gold_errors(j, versions, scope):
    v = versions.get(j.parsed_version_id)
    if v is None:
        return {"gold_version_binding"}
    b = next((b for b in v.blocks if b.block_id == j.block_id), None)
    if (
        j.source_id not in scope.source_ids
        or j.parsed_version_id not in scope.parsed_version_ids
        or j.source_id != v.source.source_id
        or j.source_version_id != v.source_version.source_version_id
        or b is None
    ):
        return {"gold_identity_binding"}
    if (
        j.end > len(b.text)
        or b.text[j.start : j.end] != j.original_region
        or j.text_sha256 != b.text_sha256
        or j.region_sha256 != sha256(j.original_region.encode())
        or j.locator not in b.locators
        or j.locator.raw_artifact_sha256 != j.raw_sha256
    ):
        return {"gold_region_binding"}
    return set()


def _hit_errors(h, dataset, versions, scope):
    v = versions.get(h.parsed_version_id)
    if v is None:
        return {"hit_version_binding"}, None
    if (
        h.source_id not in scope.source_ids
        or h.parsed_version_id not in scope.parsed_version_ids
        or v.source.registration.course_id not in scope.courses
        or h.source_id != v.source.source_id
        or h.source_version_id != v.source_version.source_version_id
    ):
        return {"hit_scope_binding"}, None
    record = next(
        (
            r
            for r in v.projection.body.records
            if r.index_record_id == h.index_record_id
        ),
        None,
    )
    b = next((b for b in v.blocks if b.block_id == h.block_id), None)
    if record is None or b is None:
        return {"hit_record_binding"}, None
    r, a, e = record.body, h.anchor, h.excerpt
    errors = set()
    if (
        h.block_id != r.block_id
        or h.parsed_version_id != a.parsed_version_id
        or h.block_id != a.block_id
        or (a.start, a.end, a.text_sha256) != (r.start, r.end, r.text_sha256)
        or h.content_type != r.content_type
        or h.projection_fingerprint != r.projection_sha256
        or (
            e.parsed_version_id,
            e.block_id,
            e.start,
            e.end,
            e.text_length,
            e.text_sha256,
            e.text,
        )
        != (
            h.parsed_version_id,
            b.block_id,
            r.start,
            min(r.end, r.start + 512),
            len(b.text),
            b.text_sha256,
            b.text[r.start : min(r.end, r.start + 512)],
        )
    ):
        errors.add("hit_text_anchor")
    if h.locators_in_structure or h.locators is None:
        # No implicit network hydration. A later adapter must supply explicit evidence.
        errors.add("external_locators_not_checked")
    elif h.locators != locators(b, v.source_version):
        errors.add("hit_locator_binding")
    if (h.text_route, h.structure_route) != (
        route("parsed", h.parsed_version_id, "blocks", b.block_id, "text"),
        route("parsed", h.parsed_version_id, "blocks", b.block_id, "structure"),
    ):
        errors.add("hit_route_binding")
    if h.index_generation != dataset.retrieval.index_generation:
        errors.add("stale_generation")
    if any(c.source_id != h.source_id for c in h.components):
        errors.add("foreign_score_component")
    if dataset.retrieval.adapter == "c24_search_result_page_v1" and (
        h.method != dataset.retrieval.method
        or h.ranking_schema != dataset.retrieval.ranking_schema
    ):
        errors.add("backend_contract")
    return errors, b


def _metric(num=None, den=None, *, reason=None, status="not_evaluable"):
    if reason:
        return Metric(
            status=status, numerator=num, denominator=den, value=None, reason=reason
        )
    return Metric(status="evaluated", numerator=num, denominator=den, value=num / den)


def _query(dataset, q, result, versions, errors):
    reasons, technical = set(), set()
    if dataset.origin == "unknown":
        reasons.add("unknown_origin")
    if dataset.review_status != "confirmed":
        reasons.add("dataset_not_reviewed")
    if not dataset.corpus_complete:
        reasons.add("incomplete_corpus")
    selected = set(q.scope.parsed_version_ids)
    known = set(versions)
    if not selected.issubset(known):
        technical.add("scope_version_binding")
    for pid in selected.intersection(known):
        v = versions[pid]
        technical.update(errors[pid])
        if (
            dataset.origin == "real"
            and v.source.registration.source_origin != "official"
        ) or (
            dataset.origin == "synthetic"
            and v.source.registration.source_origin != "synthetic"
        ):
            technical.add("origin_source_conflict")
        if (
            v.source.source_id not in q.scope.source_ids
            or v.source.registration.course_id not in q.scope.courses
        ):
            technical.add("scope_source_binding")
    pool = next((p for p in dataset.pools if p.query_id == q.query_id), None)
    expected_blocks = {
        (v.parsed_version.parsed_version_id, b.block_id, b.text_sha256)
        for v in versions.values()
        if v.parsed_version.parsed_version_id in selected
        for b in v.blocks
        if any(r.body.block_id == b.block_id for r in v.projection.body.records)
    }
    if pool is None or not pool.pool_complete or pool.review.status != "confirmed":
        reasons.add("incomplete_review_pool")
    elif (
        pool.scope_sha256 != pool_scope(dataset, q)
        or len(pool.reviewed_blocks) != len(expected_blocks)
        or {
            (b.parsed_version_id, b.block_id, b.text_sha256)
            for b in pool.reviewed_blocks
        }
        != expected_blocks
    ):
        reasons.add("pool_coverage_binding")
    judgments = [j for j in dataset.judgments if j.query_id == q.query_id]
    if any(j.review.status == "pending_review" for j in judgments):
        reasons.add("unconfirmed_gold")
    confirmed = [j for j in judgments if j.review.status == "confirmed"]
    for j in confirmed:
        technical.update(_gold_errors(j, versions, q.scope))
    if result is None:
        reasons.add("missing_results")
        hits = ()
    else:
        if (
            result.query_sha256 != sha256(q.text.encode())
            or result.scope_sha256 != fingerprint(q.scope.model_dump(mode="json"))
            or result.configuration != dataset.retrieval
        ):
            technical.add("result_request_binding")
        if result.page.index_generation != dataset.retrieval.index_generation:
            technical.add("stale_generation")
        if (
            dataset.retrieval.adapter == "c24_search_result_page_v1"
            and result.page.ranking_schema != dataset.retrieval.ranking_schema
        ):
            technical.add("backend_contract")
        if len(result.page.items) > 100:
            raise ValueError("result page limit")
        if len(result.page.items) < dataset.retrieval.k and result.page.next_cursor:
            reasons.add("insufficient_ranking_window")
        hits = result.page.items[: dataset.retrieval.k]
        # Returned data beyond k also crosses the confidentiality boundary.
        for h in result.page.items[dataset.retrieval.k :]:
            hit_errors, _ = _hit_errors(h, dataset, versions, q.scope)
            technical.update(hit_errors)
    credited, ranked, gains = set(), [], []
    location_counts = Counter()
    coordinates = {
        axis: Counter()
        for axis in (
            "page",
            "line",
            "dom",
            "time",
            "geometry",
            "block",
            "text",
            "unicode_offset",
        )
    }
    for h in hits:
        hit_errors, b = _hit_errors(h, dataset, versions, q.scope)
        technical.update(hit_errors)
        if not hit_errors and b:
            for loc in b.locators:
                location_counts[loc.time_status] += 1
                for axis, value in (
                    ("page", loc.page),
                    ("line", loc.line_start),
                    ("dom", loc.dom),
                    ("geometry", loc.bbox),
                ):
                    coordinates[axis]["known" if value is not None else "unknown"] += 1
                coordinates["time"][loc.time_status] += 1
                for axis in ("block", "text", "unicode_offset"):
                    coordinates[axis]["known"] += 1
        candidates = sorted(
            (
                j
                for j in confirmed
                if (
                    j.source_id == h.source_id
                    and j.source_version_id == h.source_version_id
                    and j.parsed_version_id == h.parsed_version_id
                    and j.block_id == h.block_id
                    and j.text_sha256 == h.anchor.text_sha256
                    and h.anchor.start <= j.start
                    and h.anchor.end >= j.end
                )
            ),
            key=lambda j: (j.start, j.end, j.gold_target_id),
        )
        # One deterministic target per hit, even if a large chunk spans several.
        target = candidates[0] if candidates and not hit_errors else None
        if not hit_errors and target is None:
            # Partial overlap is known to miss the complete reviewed target. An
            # unrelated unjudged hit is unknown, never an inferred negative.
            partial = any(
                j.parsed_version_id == h.parsed_version_id
                and j.block_id == h.block_id
                and j.start < h.anchor.end
                and h.anchor.start < j.end
                for j in confirmed
            )
            if not partial:
                reasons.add("unjudged_hit")
        new = (
            target is not None
            and target.grade > 0
            and target.gold_target_id not in credited
        )
        gains.append(target.grade if new else 0)
        ranked.append(target.gold_target_id if new else None)
        if new:
            credited.add(target.gold_target_id)
    if technical:
        reasons.add("technical_integrity_failure")
    relevant = {j.gold_target_id for j in confirmed if j.grade > 0}
    if reasons:
        precision = recall = rr = ndcg = _metric(reason=sorted(reasons)[0])
    else:
        precision = _metric(len(credited), dataset.retrieval.k)
        if relevant:
            rec, reciprocal = recall_and_rr(relevant, ranked, k=dataset.retrieval.k)
            recall = _metric(len(credited), len(relevant))
            assert recall.value == rec
            first = next((r for r, g in enumerate(gains, 1) if g), None)
            rr = _metric(1 if first else 0, first or 1)
            assert rr.value == reciprocal
        else:
            recall = _metric(0, 0, reason="no_relevant_gold", status="not_determinable")
            rr = _metric(reason="no_relevant_gold", status="not_determinable")
        dcg, idcg = graded_ranking(
            gains, [j.grade for j in confirmed], k=dataset.retrieval.k
        )
        ndcg = (
            _metric(dcg, idcg)
            if idcg
            else _metric(dcg, 0, reason="zero_idcg", status="not_determinable")
        )
    return QueryEvaluation(
        query_key=fingerprint(q.query_id),
        status="not_evaluable" if reasons else "evaluated",
        reasons=tuple(sorted(reasons)),
        precision_at_k=precision,
        recall_at_k=recall,
        reciprocal_rank_at_k=rr,
        ndcg_at_k=ndcg,
        credited_targets=len(credited) if not reasons else 0,
        gains=tuple(gains) if not reasons else (),
        technical_checks=len(result.page.items) if result is not None else 0,
        technical_failures=tuple(sorted(technical)),
        locator_known=location_counts["known"],
        locator_unknown=location_counts["unknown"],
        locator_not_applicable=location_counts["not_applicable"],
        locator_coordinates={
            axis: {
                status: counts[status]
                for status in ("known", "unknown", "not_applicable")
            }
            for axis, counts in coordinates.items()
        },
        independent_original_review="confirmed" if not reasons else "pending_review",
    )


def _macro(queries, name):
    ms = [getattr(q, name) for q in queries]
    values = [m.value for m in ms if m.status == "evaluated"]
    total = sum(values)
    return MacroMetric(
        value=total / len(values) if values else None,
        numerator=total,
        denominator=len(values),
        excluded=len(ms) - len(values),
        exclusion_reasons=dict(
            sorted(Counter(m.reason for m in ms if m.status != "evaluated").items())
        ),
    )


def evaluate_retrieval(dataset, results, *, evaluation_config):
    """Pure function. Revalidate nested inputs; no store, environment or network I/O."""
    if (
        not isinstance(dataset, ContentRetrievalEvaluationSet)
        or not isinstance(results, RetrievalResults)
        or not isinstance(evaluation_config, EvaluationConfig)
    ):
        raise ValueError("typed evaluation inputs required")
    dataset, results, config = (
        snapshot(dataset),
        snapshot(results),
        snapshot(evaluation_config),
    )
    if (
        len(canonical(dataset.model_dump(mode="json")))
        + len(canonical(results.model_dump(mode="json")))
        > config.max_input_bytes
    ):
        raise ValueError("evaluation input byte limit")
    if results.dataset_sha256 != dataset_digest(dataset):
        raise ValueError("results dataset digest mismatch")
    if (
        dataset.retrieval.adapter == "c24_search_result_page_v1"
        and dataset.retrieval.method not in {"lexical", "vector"}
    ):
        raise ValueError("hybrid not integrated; use synthetic ranking adapter")
    versions = {v.parsed_version.parsed_version_id: v for v in dataset.versions}
    errors = {
        pid: _version_errors(v, dataset.projection_config)
        for pid, v in versions.items()
    }
    by_query = {q.query_id: q for q in results.queries}
    if set(by_query) - {q.query_id for q in dataset.queries}:
        raise ValueError("foreign result query")
    queries = tuple(
        _query(dataset, q, by_query.get(q.query_id), versions, errors)
        for q in dataset.queries
    )
    supplied = {s.scenario: s for s in results.security}
    security = tuple(
        supplied.get(
            s,
            SecurityEvidence(
                scenario=s, status="not_checked", reason="no_executed_scenario_evidence"
            ),
        )
        for s in SCENARIOS
    )
    body = RetrievalReportBody(
        schema_version=1,
        evaluator=config.evaluator,
        dataset_version=dataset.dataset_version,
        dataset_sha256=dataset_digest(dataset),
        results_sha256=fingerprint(results.model_dump(mode="json")),
        origin=dataset.origin,
        review_status=dataset.review_status,
        corpus_complete=dataset.corpus_complete,
        config=config,
        retrieval=dataset.retrieval,
        projection_fingerprint=fingerprint(
            dataset.projection_config.model_dump(mode="json")
        ),
        queries=queries,
        query_count=len(queries),
        evaluable_queries=sum(q.status == "evaluated" for q in queries),
        excluded_queries=sum(q.status != "evaluated" for q in queries),
        precision_at_k=_macro(queries, "precision_at_k"),
        recall_at_k=_macro(queries, "recall_at_k"),
        mrr_at_k=_macro(queries, "reciprocal_rank_at_k"),
        ndcg_at_k=_macro(queries, "ndcg_at_k"),
        security=security,
        release_blocker=any(s.status == "failed" or s.confirmed_leak for s in security)
        or any(q.technical_failures for q in queries),
    )
    return RetrievalEvaluationReport(
        schema_version=1, report=body, digest=fingerprint(body.model_dump(mode="json"))
    )
