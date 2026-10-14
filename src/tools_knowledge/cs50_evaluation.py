"""C01: manual review contract. Valid cue bindings never imply semantic/didactic truth."""

from typing import Literal

from pydantic import Field, StrictInt, model_validator

from src.model_transcribe.data_transcribe import TranscriptSegment
from src.tools_knowledge.cs50_checkpoint import (
    CheckpointConflict,
    Contract,
    fingerprint,
)
from src.tools_knowledge.run_cs50_lecture import prepare_lecture


class ReviewAxes(Contract):
    schema_valid: bool | None = None
    source_binding_valid: bool | None = None
    semantically_supported: bool | None = None
    didactic_value: StrictInt | None = Field(default=None, ge=0, le=3)


class ManualReview(Contract):
    claim: str | None = None
    kind: Literal["statement", "formula", "negative_example"] = "statement"
    segment_ids: tuple[StrictInt, ...] = ()
    axes: ReviewAxes = Field(default_factory=ReviewAxes)
    reviewer: str | None = None
    rationale: str | None = None
    topic: str | None = None

    @model_validator(mode="after")
    def explicitly_reviewed(self):
        if len(set(self.segment_ids)) != len(self.segment_ids):
            raise ValueError("Duplicate review segment references")
        if any(v is not None for v in self.axes.model_dump().values()) and (
            not self.reviewer or not self.rationale
        ):
            raise ValueError("Human reviewer and rationale required for judgments")
        if self.claim is None and any(
            v is not None for v in self.axes.model_dump().values()
        ):
            raise ValueError("Blank template has no review judgments")
        return self


class ReviewWindow(Contract):
    chunk_index: StrictInt = Field(ge=0)
    chunk_id: str
    cue_ids: tuple[StrictInt, ...]
    cues: tuple[TranscriptSegment, ...]
    reviews: tuple[ManualReview, ...] = ()


class GoldReviewSet(Contract):
    schema_version: Literal[1] = 1
    origin: Literal["operator_declared_original", "synthetic"]
    course_id: str
    section_key: str
    lecture_id: str
    resource_id: str
    source_id: str
    raw_sha256: str
    transcript_sha256: str
    provenance_sha256: str
    chunk_plan_sha256: str
    windows: tuple[ReviewWindow, ...]


def review_template(job, *, origin, count=8, indices=None):
    if indices is None:
        if len(job.chunks) < count or count < 2:
            raise ValueError("Requested actual review windows unavailable")
        indices = [i * (len(job.chunks) - 1) // (count - 1) for i in range(count)]
    if len(set(indices)) != len(indices) or any(
        type(i) is not int or not 0 <= i < len(job.chunks) for i in indices
    ):
        raise ValueError("Invalid review window selection")
    return GoldReviewSet(
        origin=origin,
        **{
            k: getattr(job.input, k)
            for k in (
                "course_id",
                "section_key",
                "lecture_id",
                "resource_id",
                "source_id",
                "transcript_sha256",
            )
        },
        raw_sha256=job.input.raw_sha256,
        provenance_sha256=fingerprint(
            job.input.transcript_provenance.model_dump(mode="json")
        ),
        chunk_plan_sha256=job.identity.chunk_plan_sha256,
        windows=tuple(
            ReviewWindow(
                chunk_index=i,
                chunk_id=job.chunks[i].chunk_id,
                cue_ids=tuple(job.chunks[i].segment_ids),
                cues=tuple(job.segments[x] for x in job.chunks[i].segment_ids),
            )
            for i in indices
        ),
    )


def validate_review_set(review_set, job):
    # Re-read actual source artifacts, not an unchecked stale in-memory plan.
    current = prepare_lecture(
        job.plan, job.input, workspace=job.workspace, config=job.config
    )
    expected = review_template(
        current,
        origin=review_set.origin,
        indices=[w.chunk_index for w in review_set.windows],
    )
    for key in GoldReviewSet.model_fields:
        if key != "windows" and getattr(review_set, key) != getattr(expected, key):
            raise CheckpointConflict(
                "Review source/hash/provenance/plan conflict: " + key
            )
    if not review_set.windows:
        raise ValueError("Explicit review windows required")
    for window, reference in zip(review_set.windows, expected.windows, strict=True):
        if (
            window.chunk_id != reference.chunk_id
            or window.cue_ids != reference.cue_ids
            or window.cues != reference.cues
        ):
            raise CheckpointConflict("Review window contradicts original chunk")
        for review in window.reviews:
            if review.claim is not None and (
                not review.claim.strip() or not review.segment_ids
            ):
                raise ValueError(
                    "Annotated claim requires explicit nonempty cue references"
                )
            if any(
                seg not in window.cue_ids
                or seg not in current.segments
                or not current.segments[seg].text.strip()
                for seg in review.segment_ids
            ):
                raise CheckpointConflict("Unknown/empty/foreign review cue")
    return review_set


def evaluation_counts(review_set):
    """Count explicit human judgments separately; no proxy-to-gold conversion."""
    results = {}
    reviews = [r for w in review_set.windows for r in w.reviews]
    for axis in ReviewAxes.model_fields:
        values = [
            getattr(r.axes, axis) for r in reviews if getattr(r.axes, axis) is not None
        ]
        results[axis] = {
            "reviewed": len(values),
            "unknown": len(reviews) - len(values),
            "values": values,
        }
    return {
        "schema_version": 1,
        "origin": review_set.origin,
        "windows": len(review_set.windows),
        "claims": sum(r.claim is not None for r in reviews),
        "axes": results,
        "quality_established": False,
        "limits": [
            "Review judgments require human adjudication; IDs/hashes do not prove entailment"
        ],
    }
