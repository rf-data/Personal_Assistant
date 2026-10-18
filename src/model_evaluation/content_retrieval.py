"""Independent region review and offline evidence; no replacement for live ACLs."""

from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from src.content_store.index_models import IndexProjectionConfig, IndexProjectionResult
from src.content_store.models import (
    ArtifactReference,
    ContentBlock,
    ContentLocator,
    Name,
    ParsedDocumentVersion,
    ParserConfiguration,
    Source,
    SourceVersion,
    fingerprint,
)
from src.job_control.models import Contract, Principal, Sha
from src.model_discovery.cs50 import CourseId
from src.tools_rag.content_index_models import SearchResultPage

Origin = Literal["synthetic", "real", "unknown"]
ReviewStatus = Literal["pending_review", "confirmed", "rejected"]
Backend = Literal["lexical", "vector", "hybrid"]


class Versioned(Contract):
    schema_version: Literal[1]

    @model_validator(mode="before")
    @classmethod
    def explicit_schema(cls, value):
        if isinstance(value, dict) and type(value.get("schema_version")) is not int:
            raise ValueError("explicit integer schema_version required")
        return value


class IndependentReview(Contract):
    status: ReviewStatus
    method: Literal[
        "independent_source_annotation",
        "synthetic_reference",
        "prediction_preannotation",
    ]
    reviewer: Name | None = None
    evidence_reference: Name | None = None
    review_date: date | None = None

    @model_validator(mode="after")
    def confirmed(self):
        if self.status == "confirmed" and (
            self.method == "prediction_preannotation"
            or not all((self.reviewer, self.evidence_reference, self.review_date))
        ):
            raise ValueError("confirmation requires independent reviewer/date/evidence")
        return self


class EvaluationArtifact(Contract):
    reference: ArtifactReference
    base64_bytes: str = Field(max_length=8 * 1024**2)


class VersionEvidence(Contract):
    source: Source
    source_version: SourceVersion
    parsed_version: ParsedDocumentVersion
    parser: ParserConfiguration
    blocks: tuple[ContentBlock, ...] = Field(max_length=2000)
    projection: IndexProjectionResult
    artifacts: tuple[EvaluationArtifact, ...] = Field(max_length=504)


class EvaluationScope(Contract):
    actor: Principal
    courses: tuple[CourseId, ...] = Field(min_length=1, max_length=3)
    source_ids: tuple[Name, ...] = Field(min_length=1, max_length=32)
    parsed_version_ids: tuple[Name, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def unique(self):
        for values in (self.courses, self.source_ids, self.parsed_version_ids):
            if len(values) != len(set(values)):
                raise ValueError("scope identities must be unique")
        if not set(self.courses).issubset(self.actor.courses):
            raise ValueError("evaluation course outside actor scope")
        return self


class Query(Contract):
    query_id: Name
    text: str = Field(min_length=1, max_length=512)
    scope: EvaluationScope


class ReviewedBlock(Contract):
    parsed_version_id: Name
    block_id: Name
    text_sha256: Sha


class ReviewPool(Contract):
    query_id: Name
    pool_complete: bool = Field(strict=True)
    scope_sha256: Sha
    reviewed_blocks: tuple[ReviewedBlock, ...] = Field(max_length=2000)
    coverage_note: Name
    review: IndependentReview


class ContentRelevanceJudgment(Versioned):
    query_id: Name
    gold_target_id: Name
    source_id: Name
    source_version_id: Name
    parsed_version_id: Name
    block_id: Name
    start: int = Field(strict=True, ge=0)
    end: int = Field(strict=True, ge=1)
    offset_unit: Literal["unicode_codepoint"] = "unicode_codepoint"
    original_region: str = Field(min_length=1, max_length=2000)
    text_sha256: Sha
    region_sha256: Sha
    raw_sha256: Sha
    locator: ContentLocator
    grade: int = Field(strict=True, ge=0, le=3)
    review: IndependentReview
    ambiguous: bool = Field(default=False, strict=True)
    ambiguity_note: Name | None = None

    @model_validator(mode="after")
    def region(self):
        if not self.start < self.end or self.end - self.start != len(
            self.original_region
        ):
            raise ValueError(
                "complete original region requires exact codepoint offsets"
            )
        if self.ambiguous and (
            not self.ambiguity_note or self.review.status == "confirmed"
        ):
            raise ValueError("ambiguous sources need a note and cannot be confirmed")
        return self


class RetrievalConfiguration(Contract):
    method: Backend
    ranking_schema: Name
    backend_fingerprint: Sha
    configuration_fingerprint: Sha
    index_generation: Sha
    adapter: Literal["c24_search_result_page_v1", "synthetic_ranking_list_v1"]
    k: int = Field(strict=True, ge=1, le=100)

    @model_validator(mode="after")
    def configuration_hash(self):
        if self.configuration_fingerprint != fingerprint(
            self.model_dump(mode="json", exclude={"configuration_fingerprint"})
        ):
            raise ValueError("retrieval configuration fingerprint mismatch")
        return self


class ContentRetrievalEvaluationSet(Versioned):
    dataset_version: Name
    origin: Origin
    review_status: ReviewStatus
    corpus_complete: bool = Field(strict=True)
    corpus_reference: Name
    projection_config: IndexProjectionConfig
    retrieval: RetrievalConfiguration
    queries: tuple[Query, ...] = Field(min_length=1, max_length=100)
    versions: tuple[VersionEvidence, ...] = Field(min_length=1, max_length=128)
    judgments: tuple[ContentRelevanceJudgment, ...] = Field(max_length=2000)
    pools: tuple[ReviewPool, ...] = Field(max_length=100)

    @model_validator(mode="after")
    def identities(self):
        groups = (
            [q.query_id for q in self.queries],
            [v.parsed_version.parsed_version_id for v in self.versions],
            [j.gold_target_id for j in self.judgments],
            [p.query_id for p in self.pools],
        )
        if any(len(values) != len(set(values)) for values in groups):
            raise ValueError("duplicate dataset identity")
        ids = set(groups[0])
        if any(j.query_id not in ids for j in self.judgments) or any(
            p.query_id not in ids for p in self.pools
        ):
            raise ValueError("foreign query in gold/pool")
        for review in [
            *(j.review for j in self.judgments),
            *(p.review for p in self.pools),
        ]:
            if review.status == "confirmed" and (
                self.origin != "synthetic"
                and review.method != "independent_source_annotation"
                or self.origin == "synthetic"
                and review.method != "synthetic_reference"
            ):
                raise ValueError("review method contradicts dataset origin")
        if (
            self.retrieval.adapter == "synthetic_ranking_list_v1"
            and self.origin != "synthetic"
        ):
            raise ValueError("unintegrated backend adapters are synthetic only")
        grouped = {}
        for j in self.judgments:
            if j.review.status == "confirmed":
                grouped.setdefault(
                    (j.query_id, j.parsed_version_id, j.block_id), []
                ).append(j)
        for group in grouped.values():
            ordered = sorted(group, key=lambda j: (j.start, j.end))
            if any(a.end > b.start for a, b in zip(ordered, ordered[1:], strict=False)):
                raise ValueError(
                    "overlapping gold: split or explicitly merge before review"
                )
        return self


SecurityScenario = Literal[
    "unauthorized_source",
    "missing_course",
    "revoked_grant",
    "quarantine",
    "tombstone",
    "stale_generation",
    "bad_anchor",
    "foreign_score_influence",
    "cursor_pagination",
    "existence_leak",
    "text_leak",
    "locator_leak",
]
SCENARIOS = (
    "unauthorized_source",
    "missing_course",
    "revoked_grant",
    "quarantine",
    "tombstone",
    "stale_generation",
    "bad_anchor",
    "foreign_score_influence",
    "cursor_pagination",
    "existence_leak",
    "text_leak",
    "locator_leak",
)


class SecurityEvidence(Contract):
    scenario: SecurityScenario
    status: Literal["passed", "failed", "not_checked"]
    reason: Name
    evidence_sha256: Sha | None = None
    confirmed_leak: bool = Field(default=False, strict=True)

    @model_validator(mode="after")
    def evidence(self):
        if self.status != "not_checked" and self.evidence_sha256 is None:
            raise ValueError("executed security scenario requires evidence digest")
        if self.confirmed_leak and self.status != "failed":
            raise ValueError("confirmed leaks must fail")
        return self


class QueryResults(Contract):
    query_id: Name
    query_sha256: Sha
    scope_sha256: Sha
    configuration: RetrievalConfiguration
    page: SearchResultPage
    starts_at_rank: Literal[1] = 1


class RetrievalResults(Versioned):
    dataset_sha256: Sha
    queries: tuple[QueryResults, ...] = Field(max_length=100)
    security: tuple[SecurityEvidence, ...] = Field(default=(), max_length=12)

    @model_validator(mode="after")
    def unique(self):
        if len({q.query_id for q in self.queries}) != len(self.queries) or len(
            {s.scenario for s in self.security}
        ) != len(self.security):
            raise ValueError("duplicate results/security scenario")
        return self


class EvaluationConfig(Versioned):
    evaluator: Literal["content_retrieval_evaluation_v1"] = (
        "content_retrieval_evaluation_v1"
    )
    matching: Literal["full_region_one_target_v1"] = "full_region_one_target_v1"
    max_input_bytes: Literal[33554432] = 33554432


class Metric(Contract):
    status: Literal["evaluated", "not_evaluable", "not_determinable"]
    numerator: float | None
    denominator: float | None
    value: float | None
    reason: Name | None = None


class QueryEvaluation(Contract):
    query_key: Sha
    status: Literal["evaluated", "not_evaluable"]
    reasons: tuple[Name, ...]
    precision_at_k: Metric
    recall_at_k: Metric
    reciprocal_rank_at_k: Metric
    ndcg_at_k: Metric
    credited_targets: int
    gains: tuple[int, ...]
    technical_checks: int
    technical_failures: tuple[Name, ...]
    locator_known: int
    locator_unknown: int
    locator_not_applicable: int
    # Counts for each coordinate; absent non-time coordinates remain unknown.
    locator_coordinates: dict[
        Literal[
            "page", "line", "dom", "time", "geometry", "block", "text", "unicode_offset"
        ],
        dict[Literal["known", "unknown", "not_applicable"], int],
    ]
    independent_original_review: ReviewStatus


class MacroMetric(Contract):
    value: float | None
    numerator: float
    denominator: int
    excluded: int
    exclusion_reasons: dict[str, int]


class RetrievalReportBody(Versioned):
    evaluator: Literal["content_retrieval_evaluation_v1"]
    dataset_version: Name
    dataset_sha256: Sha
    results_sha256: Sha
    origin: Origin
    review_status: ReviewStatus
    corpus_complete: bool
    config: EvaluationConfig
    retrieval: RetrievalConfiguration
    projection_fingerprint: Sha
    queries: tuple[QueryEvaluation, ...]
    query_count: int
    evaluable_queries: int
    excluded_queries: int
    precision_at_k: MacroMetric
    recall_at_k: MacroMetric
    mrr_at_k: MacroMetric
    ndcg_at_k: MacroMetric
    security: tuple[SecurityEvidence, ...]
    release_blocker: bool
    live_authorization: Literal["not_checked"] = "not_checked"
    real_acceptance: Literal["blocked"] = "blocked"


class RetrievalEvaluationReport(Versioned):
    report: RetrievalReportBody
    digest: Sha

    @model_validator(mode="after")
    def checksum(self):
        if self.digest != fingerprint(self.report.model_dump(mode="json")):
            raise ValueError("report digest mismatch")
        return self


def dataset_digest(dataset):
    return fingerprint(dataset.model_dump(mode="json"))


def pool_scope(dataset, query):
    return fingerprint(
        dict(
            query=query.model_dump(mode="json"),
            versions=[
                v.parsed_version.model_dump(mode="json")
                for v in dataset.versions
                if v.parsed_version.parsed_version_id in query.scope.parsed_version_ids
            ],
            projection=dataset.projection_config.model_dump(mode="json"),
        )
    )
