"""Verified source windows and manual judgments; fake scores are never quality metrics."""

from typing import Literal

from pydantic import Field, model_validator

from src.model_discovery.cs50_index import Hash, Name
from src.tools_knowledge.cs50_checkpoint import Contract


class RetrievalQuestion(Contract):
    question_id: Name
    question: Name
    expected_lecture_id: Name
    source_id: Name
    proposed_segment_ids: tuple[int, ...] = Field(min_length=1)
    start: float
    end: float
    content_topic: Name
    # Proposals are grounded windows, not fabricated gold relevance judgments.
    relevance_reviewed: Literal[False] = False


class RetrievalEvaluationSet(Contract):
    schema_version: Literal[1] = 1
    source_origin: Literal["official", "synthetic"] = "official"
    course_id: Name
    lecture_id: Name
    source_id: Name
    transcript_sha256: Hash
    raw_sha256: Hash
    original_url: Name
    provenance_sha256: Hash
    questions: tuple[RetrievalQuestion, ...] = Field(min_length=10)

    @model_validator(mode="after")
    def identities(self):
        if len({q.question_id for q in self.questions}) != len(self.questions):
            raise ValueError("Duplicate evaluation question")
        if any(
            q.source_id != self.source_id or q.expected_lecture_id != self.lecture_id
            for q in self.questions
        ):
            raise ValueError("Foreign evaluation source/lecture")
        return self


def create_evaluation_template(
    adapter, input, *, workspace, specifications, source_origin="official"
):
    from src.tools_knowledge.bind_cs50_transcript import load_knowledge_transcript
    from src.tools_knowledge.cs50_checkpoint import fingerprint

    transcript = load_knowledge_transcript(adapter, input, workspace=workspace)
    segments = {s.seg_id: s for s in transcript.segments if s.text.strip()}
    questions = []
    for index, spec in enumerate(specifications):
        ids = tuple(spec["segment_ids"])
        if (
            not ids
            or len(set(ids)) != len(ids)
            or any(sid not in segments for sid in ids)
        ):
            raise ValueError(
                "Evaluation window must reference actual nonempty unique original cues"
            )
        cues = [segments[sid] for sid in ids]
        questions.append(
            RetrievalQuestion(
                question_id=f"python0-{index + 1:02d}",
                question=spec["question"],
                expected_lecture_id=input.lecture_id,
                source_id=input.source_id,
                proposed_segment_ids=ids,
                start=min(s.start for s in cues),
                end=max(s.end for s in cues),
                content_topic=spec["topic"],
            )
        )
    return RetrievalEvaluationSet(
        source_origin=source_origin,
        course_id=input.course_id,
        lecture_id=input.lecture_id,
        source_id=input.source_id,
        transcript_sha256=input.transcript_sha256,
        raw_sha256=input.raw_sha256,
        original_url=input.transcript_url,
        provenance_sha256=fingerprint(transcript.provenance.model_dump(mode="json")),
        questions=tuple(questions),
    )


class ManualRetrievalJudgment(Contract):
    question_id: Name
    transcript_sha256: Hash
    reviewer: Name
    relevant_point_ids: tuple[str, ...] = Field(min_length=1)
    relevant_segment_ids: tuple[int, ...] = Field(min_length=1)
    semantic_source_correct: Literal[True]
    usefulness_note: Name


def ranking_metrics(relevant, rankings, *, k):
    """Pure arithmetic; callers must first establish reviewed real relevance."""
    if (
        k < 1
        or not relevant
        or len(relevant) != len(rankings)
        or any(not ids for ids in relevant)
    ):
        raise ValueError("Complete nonempty relevance sets and positive k required")
    recall, rr = [], []
    for gold, ranked in zip(relevant, rankings, strict=True):
        top = ranked[:k]
        recall.append(len(set(gold).intersection(top)) / len(set(gold)))
        rr.append(
            next((1 / (i + 1) for i, point in enumerate(top) if point in gold), 0.0)
        )
    return {"recall_at_k": sum(recall) / len(recall), "mrr_at_k": sum(rr) / len(rr)}


def reviewed_metrics(template, judgments, results, plan, *, k=5):
    if (
        template.source_origin != "official"
        or plan.collection.embedding.provider != "local"
        or any(p.source_origin != "official" for p in plan.units)
    ):
        raise ValueError(
            "Fake embeddings/synthetic sources cannot establish semantic retrieval quality"
        )
    if (
        len(judgments) < 10
        or {j.question_id for j in judgments}
        != {q.question_id for q in template.questions}
        or len(judgments) != len(template.questions)
    ):
        raise ValueError(
            "Every real question needs an explicit human relevance judgment"
        )
    expected = {p.point_id: p for p in plan.units}
    questions = {q.question_id: q for q in template.questions}
    relevant, rankings = [], []
    for judgment in judgments:
        q = questions[judgment.question_id]
        if judgment.transcript_sha256 != template.transcript_sha256:
            raise ValueError("Review source hash conflict")
        for point in judgment.relevant_point_ids:
            p = expected.get(point)
            if (
                p is None
                or p.source_id != template.source_id
                or p.lecture_id != q.expected_lecture_id
                or p.transcript_sha256 != template.transcript_sha256
                or not set(p.segment_ids).intersection(judgment.relevant_segment_ids)
            ):
                raise ValueError(
                    "Relevance judgment is not grounded in the reviewed original source"
                )
        hits = results.get(q.question_id)
        if hits is None or any(
            not h.original_source_checked or h.payload != expected.get(h.point_id)
            for h in hits
        ):
            raise ValueError(
                "Executed retrieval with original-source verification required"
            )
        relevant.append(set(judgment.relevant_point_ids))
        rankings.append([h.point_id for h in hits])
    return ranking_metrics(relevant, rankings, k=k)
